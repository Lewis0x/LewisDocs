# Copyright 2026

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path
from shutil import which
from subprocess import run
from tempfile import TemporaryDirectory
from types import ModuleType
from typing import TypeAlias, cast
from unittest.mock import patch

from typer.testing import CliRunner

from scripts.ai import cli as ai_cli


class _FakeSyncModule(ModuleType):
    def __init__(self, name: str, *, exit_code: int) -> None:
        super().__init__(name)
        self._exit_code: int = exit_code

    def main(self) -> int:
        return self._exit_code


ROOT = Path(__file__).resolve().parents[2]
PACKAGE_JSON = ROOT / "package.json"
PYPROJECT = ROOT / "pyproject.toml"
LOCKFILE = ROOT / "requirements-uv-bootstrap.lock"
UV_LOCK = ROOT / "uv.lock"
THEME_CSS = ROOT / "docs/.vitepress/theme/custom.css"
VITEPRESS_CONFIG = ROOT / "docs/.vitepress/config.ts"
AI_SYNC_WORKFLOW = ROOT / ".github/workflows/ai-handbook-sync.yml"
BUILD_SCRIPT = (
    "vitepress build docs && python scripts/watermark.py && "
    "node scripts/ai_content_gate.mjs verify-dist"
)
PREPARE_SCRIPT = (
    "npm run import && npm run rewrite && npm run link-citations && "
    "node scripts/ai_content_gate.mjs prepare"
)
LINT_TS_SCRIPT = (
    "biome check docs/.vitepress/config.ts docs/.vitepress/search-render.mjs "
    "docs/.vitepress/theme/index.ts docs/.vitepress/theme/components/AiLanguageSwitch.vue "
    "tests/ai/node/search-render.test.mjs"
)


JSONScalar: TypeAlias = str | int | float | bool | None
JSONValue: TypeAlias = JSONScalar | list["JSONValue"] | dict[str, "JSONValue"]
JSONDict: TypeAlias = dict[str, JSONValue]


def _as_dict(payload: JSONValue) -> JSONDict:
    if not isinstance(payload, dict):
        message = "Expected mapping payload"
        raise TypeError(message)
    return cast("JSONDict", payload)


def _as_str_mapping(payload: JSONValue) -> dict[str, str]:
    mapping = _as_dict(payload)
    values: dict[str, str] = {}
    for key, value in mapping.items():
        if not isinstance(value, str):
            continue
        values[key] = value
    return values


def _as_str_list(payload: JSONValue) -> list[str]:
    if not isinstance(payload, list):
        message = "Expected list payload"
        raise TypeError(message)
    payload_list = cast("list[JSONValue]", payload)
    values: list[str] = []
    for item in payload_list:
        if not isinstance(item, str):
            message = "Expected list of strings"
            raise TypeError(message)
        values.append(item)
    return values


def _key_as_dict(payload: JSONDict, key: str) -> JSONDict:
    return _as_dict(payload[key])


def test_legacy_dependency_locks_removed() -> None:
    assert not (ROOT / "requirements-ai.in").exists()
    assert not (ROOT / "requirements-ai.lock").exists()


def test_package_contract() -> None:
    package_json = _as_dict(cast("JSONDict", json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))))
    scripts = _as_str_mapping(package_json["scripts"])
    dev_deps = _as_str_mapping(package_json["devDependencies"])
    assert scripts["import"] == "python scripts/import_docs.py"
    assert scripts["rewrite"] == "python scripts/rewrite_links.py"
    assert scripts["link-citations"] == "python scripts/link_citations.py"
    assert scripts["build"] == BUILD_SCRIPT
    assert (
        scripts["build:no-watermark"]
        == "vitepress build docs && node scripts/ai_content_gate.mjs verify-dist"
    )
    assert scripts["prepare-content"] == PREPARE_SCRIPT
    assert scripts["ai:sync"] == "node scripts/run_ai_python.mjs --ai -- -m scripts.ai.cli sync"
    assert "ai:validate" not in scripts
    assert "ai:check" not in scripts
    assert scripts["typecheck"] == "tsc -p tsconfig.json"
    assert scripts["lint:ts"] == LINT_TS_SCRIPT

    assert dev_deps["@biomejs/biome"] == "2.5.5"
    assert dev_deps["typescript"] == "7.0.2"
    assert dev_deps["@types/node"] == "20.19.43"
    assert "tsx" not in dev_deps
    assert "@cloudflare/workers-types" not in dev_deps
    assert "playwright-core" not in dev_deps


def test_public_handbook_is_unconditional_and_sync_workflow_is_manual() -> None:
    config = VITEPRESS_CONFIG.read_text(encoding="utf-8")
    assert "INCLUDE_AI_HANDBOOK" not in config
    assert "createSearchRenderer(true)" in config

    workflow = AI_SYNC_WORKFLOW.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in workflow
    assert "schedule:" not in workflow
    assert "contents: write" in workflow
    assert "timeout-minutes: 240" in workflow
    assert "MOONSHOT_API_KEY: ${{ secrets.MOONSHOT_API_KEY }}" in workflow
    assert "AI_SYNC_RESUME: '1'" in workflow
    assert "delays=(0 60 300 900)" in workflow
    assert "npm run ai:sync" in workflow
    assert "git add -- source-ai/content" in workflow
    add_index = workflow.index("git add -- source-ai/content")
    diff_index = workflow.index("git diff --cached --quiet")
    assert add_index < diff_index


def test_tablet_navigation_uses_mobile_controls() -> None:
    css = THEME_CSS.read_text(encoding="utf-8")
    assert "@media (min-width: 768px) and (max-width: 959px)" in css
    assert ".VPNavBarMenu" in css
    assert ".VPNavBarExtra" in css
    assert ".VPNavBarHamburger" in css
    assert ".VPNavScreen" in css


def test_pyproject_contract() -> None:
    project = _as_dict(cast("JSONDict", tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))))
    project_root = _key_as_dict(project, "project")
    assert project_root["requires-python"] == ">=3.11"
    assert "optional-dependencies" not in project_root

    deps = _as_str_list(project_root["dependencies"])
    assert "pydantic==2.13.4" in deps
    assert "typer==0.27.0" in deps
    assert "rich==15.0.0" in deps
    assert "httpx2[http2,brotli,zstd]==2.9.1" in deps
    dependency_groups_root = _key_as_dict(project, "dependency-groups")
    assert "dev" in dependency_groups_root

    dependency_groups = _as_str_list(dependency_groups_root["dev"])
    assert "pytest==9.1.1" in dependency_groups
    assert "basedpyright==1.39.9" in dependency_groups
    assert "ruff==0.16.0" in dependency_groups
    assert set(dependency_groups) == {
        "pytest==9.1.1",
        "basedpyright==1.39.9",
        "ruff==0.16.0",
    }

    tools = _key_as_dict(project, "tool")
    basedpyright = _key_as_dict(tools, "basedpyright")
    assert basedpyright["include"] == ["scripts/ai", "tests/ai"]
    assert basedpyright["pythonVersion"] == "3.11"
    assert basedpyright["typeCheckingMode"] == "all"

    ruff = _key_as_dict(tools, "ruff")
    assert ruff["include"] == ["scripts/ai/**/*.py", "tests/ai/**/*.py"]
    lint = _key_as_dict(ruff, "lint")
    assert lint["select"] == ["ALL"]
    assert _as_str_list(lint["ignore"]) == ["COM812", "ISC001"]
    assert _as_dict(lint["per-file-ignores"]) == {
        "tests/ai/test_toolchain.py": [
            "D100",
            "D101",
            "D102",
            "D103",
            "D104",
            "D107",
            "INP001",
            "S101",
            "S603",
            "PLR2004",
        ]
    }


def test_bootstrap_lock_is_uv_only_and_hash_locked() -> None:
    assert LOCKFILE.exists()
    lock_text = LOCKFILE.read_text(encoding="utf-8")
    assert lock_text.startswith("uv==0.11.32 \\")
    hashes = re.findall(r"--hash=sha256:[a-f0-9]{64}", lock_text)
    assert len(hashes) == 18
    assert "anyio" not in lock_text
    assert "pytest" not in lock_text


def test_uv_lock_exists_and_includes_handshake_dependencies() -> None:
    assert UV_LOCK.exists()
    lock_text = UV_LOCK.read_text(encoding="utf-8")
    assert 'name = "pydantic"' in lock_text
    assert 'name = "typer"' in lock_text
    assert 'name = "rich"' in lock_text
    assert 'name = "httpx2"' in lock_text
    assert 'name = "pytest"' in lock_text


def test_run_ai_selector_discards_relative_probe_path() -> None:
    node_executable = which("node")
    if node_executable is None:
        message = "node executable not found"
        raise RuntimeError(message)
    launcher_test = (ROOT / "tests/ai/node/python-selector.test.mjs").resolve()
    with TemporaryDirectory() as cwd:
        result = run(
            [
                node_executable,
                "--test",
                str(launcher_test),
            ],
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )
    assert result.returncode == 0
    assert result.stderr == ""


def test_cli_sync_command_lazily_dispatches_to_scripts_ai_sync() -> None:
    calls: list[str] = []
    fake_sync_module = _FakeSyncModule("scripts.ai.sync", exit_code=0)

    def _load_sync_module() -> ModuleType:
        calls.append("scripts.ai.sync")
        return fake_sync_module

    with patch.object(ai_cli, "_load_sync_module", side_effect=_load_sync_module):
        result = CliRunner().invoke(ai_cli.app, ["sync"])

    assert result.exit_code == 0
    assert calls == ["scripts.ai.sync"]


def test_cli_sync_missing_sync_module_returns_clean_exit() -> None:
    calls: list[str] = []

    def missing_import() -> ModuleType:
        calls.append("scripts.ai.sync")
        raise ModuleNotFoundError(name="scripts.ai.sync")

    with patch.object(ai_cli, "_load_sync_module", side_effect=missing_import):
        result = CliRunner().invoke(ai_cli.app, ["sync"])

    assert result.exit_code == 1
    assert calls == ["scripts.ai.sync"]
    assert "Traceback" not in result.stderr

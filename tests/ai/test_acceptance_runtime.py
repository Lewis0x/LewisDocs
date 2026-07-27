# ruff: noqa: CPY001,D100,D103,INP001,PLR2004,S101,S607

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from secrets import token_urlsafe
from typing import TYPE_CHECKING, Literal, assert_never
from uuid import uuid4

import httpx2
import pytest

from scripts.ai import sync
from scripts.ai.errors import AIAgentError, ErrorCode
from scripts.ai.http_client import create_http_client
from scripts.ai.manifest import load_sources
from scripts.ai.materialize import MaterializeOptions, materialize_ai
from scripts.ai.snapshot import RealFileOps, Snapshot, tree_snapshot
from scripts.ai.sync import SyncDeps, SyncOptions
from tests.ai.fixture_support import FaultFileOps, install_content, normalized_pages, transport_for

if TYPE_CHECKING:
    from scripts.ai.kimi import TranslationInput

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "source-ai" / "sources.yaml"
RuntimeFailure = Literal["manifest", "fetch", "translation", "validation", "write"]
RuntimeMode = Literal["noop", "changed", "failure"]


@dataclass(frozen=True, slots=True)
class _RuntimeCase:
    failure: RuntimeFailure
    code: ErrorCode
    exit_code: int
    message: str


def _options(private: Path, support: Path) -> SyncOptions:
    return SyncOptions(
        repo_root=ROOT,
        content_root=private,
        staging_root=support / "staging",
        manifest_path=MANIFEST_PATH,
        report_path=support / "report.json",
    )


def _materialize(temporary: Path, private: Path) -> Path:
    repository = temporary / "derived-repository"
    routes = materialize_ai(
        MaterializeOptions(repository, private, repository / "docs" / "ai", MANIFEST_PATH)
    )
    assert len(routes) == 22
    return repository / "docs" / "ai"


def _patch_main(
    monkeypatch: pytest.MonkeyPatch, options: SyncOptions, dependencies: SyncDeps
) -> None:
    monkeypatch.setattr(sync, "_default_options", lambda: options)
    monkeypatch.setattr(sync, "_default_deps", lambda: dependencies)


def _unreachable(client: httpx2.Client, request: TranslationInput) -> str:
    del client, request
    pytest.fail("translator must not be called")


@pytest.mark.parametrize(
    "case",
    [
        _RuntimeCase("manifest", ErrorCode.MANIFEST_INVALID, 2, "manifest is invalid"),
        _RuntimeCase("fetch", ErrorCode.FETCH_FAILED, 3, "source fetch failed"),
        _RuntimeCase("translation", ErrorCode.TRANSLATION_FAILED, 5, "translation failed"),
        _RuntimeCase("validation", ErrorCode.VALIDATION_FAILED, 6, "validation failed"),
        _RuntimeCase("write", ErrorCode.WRITE_FAILED, 7, "write failed"),
    ],
)
def test_ac5_runtime_errors_preserve_accepted_bytes_and_safe_cli_output(
    case: _RuntimeCase,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    manifest = load_sources(MANIFEST_PATH)
    private = tmp_path / "private"
    support = tmp_path / "support"
    install_content(private, normalized_pages(manifest))
    options = _options(private, support)
    prior_report = b"prior report\n"
    options.report_path.parent.mkdir(parents=True)
    _ = options.report_path.write_bytes(prior_report)
    before = tree_snapshot(private)
    dependencies = SyncDeps(
        lambda: create_http_client(transport_for(manifest)), _unreachable, RealFileOps()
    )
    source_id = "-"

    match case.failure:
        case "manifest":
            options = options.model_copy(update={"manifest_path": tmp_path / "missing.json"})
        case "fetch":

            def reject(request: httpx2.Request) -> httpx2.Response:
                return httpx2.Response(503, request=request, content=b"synthetic")

            dependencies = SyncDeps(
                lambda: create_http_client(httpx2.MockTransport(reject)),
                _unreachable,
                RealFileOps(),
            )
            source_id = str(manifest.root[0].id)
        case "translation":

            def fail_translation(client: httpx2.Client, request: TranslationInput) -> str:
                del client
                raise AIAgentError(
                    ErrorCode.TRANSLATION_FAILED, "synthetic failure", request.source_id
                )

            monkeypatch.setenv("MOONSHOT_API_KEY", token_urlsafe(24))
            dependencies = SyncDeps(
                lambda: create_http_client(transport_for(manifest, manifest.root[0].id)),
                fail_translation,
                RealFileOps(),
            )
            source_id = str(manifest.root[0].id)
        case "validation":
            options = options.model_copy(update={"staging_root": private / "unsafe-staging"})
        case "write":

            def translate(client: httpx2.Client, request: TranslationInput) -> str:
                del client
                return f"# 中文 {request.source_id}\n\n合成更新。\n"

            monkeypatch.setenv("MOONSHOT_API_KEY", token_urlsafe(24))
            dependencies = SyncDeps(
                lambda: create_http_client(transport_for(manifest, manifest.root[0].id)),
                translate,
                FaultFileOps("next:en"),
            )
        case _:
            assert_never(case.failure)

    _patch_main(monkeypatch, options, dependencies)
    actual_exit = sync.main()
    stdout, stderr = capsys.readouterr()

    assert actual_exit == case.exit_code
    assert stdout == f"code={case.code} source_id={source_id} message={case.message}\n"
    assert stderr == ""
    assert tree_snapshot(private) == before
    assert options.report_path.read_bytes() == prior_report
    assert _materialize(tmp_path, private).is_dir()


def _secret_absent(secret: str, values: tuple[bytes, ...]) -> None:
    if any(secret.encode() in value for value in values):
        pytest.fail("runtime-generated sentinel leaked")


@pytest.mark.parametrize("mode", ["noop", "changed", "failure"])
def test_ac6_runtime_secret_sentinel_never_reaches_artifacts(
    mode: RuntimeMode,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    manifest = load_sources(MANIFEST_PATH)
    private = tmp_path / "private"
    install_content(private, normalized_pages(manifest))
    before: Snapshot = tree_snapshot(private)
    support = ROOT / ".ai-local" / "acceptance" / f"runtime-{uuid4().hex}"
    options = _options(private, support)
    secret = token_urlsafe(32)
    monkeypatch.setenv("MOONSHOT_API_KEY", secret)
    dependencies = SyncDeps(
        lambda: create_http_client(transport_for(manifest)), _unreachable, RealFileOps()
    )

    match mode:
        case "noop":
            expected_exit = 0
        case "changed":

            def translate(client: httpx2.Client, request: TranslationInput) -> str:
                del client
                if request.api_key.get_secret_value() != secret:
                    pytest.fail("translator did not receive the process-only key")
                return f"# 中文 {request.source_id}\n\n合成更新。\n"

            expected_exit = 0
            dependencies = SyncDeps(
                lambda: create_http_client(transport_for(manifest, manifest.root[0].id)),
                translate,
                RealFileOps(),
            )
        case "failure":

            def fail_translation(client: httpx2.Client, request: TranslationInput) -> str:
                del client
                raise AIAgentError(
                    ErrorCode.TRANSLATION_FAILED, "synthetic failure", request.source_id
                )

            expected_exit = 5
            dependencies = SyncDeps(
                lambda: create_http_client(transport_for(manifest, manifest.root[0].id)),
                fail_translation,
                RealFileOps(),
            )
        case _:
            assert_never(mode)

    _patch_main(monkeypatch, options, dependencies)
    actual_exit = sync.main()
    stdout, stderr = capsys.readouterr()
    after = tree_snapshot(private)
    derived = _materialize(tmp_path, private)
    diff = subprocess.run(
        ["git", "diff", "--no-ext-diff", "--binary"],
        cwd=ROOT,
        check=False,
        shell=False,
        capture_output=True,
    )
    roots = (tmp_path, support, derived, ROOT / "docs" / ".vitepress" / "dist")
    files = (
        *(path for root in roots if root.exists() for path in root.rglob("*") if path.is_file()),
        Path(__file__),
        ROOT / "tests" / "ai" / "test_acceptance.py",
        ROOT / "tests" / "ai" / "fixtures" / "browser-queries.json",
        ROOT / "project-docs" / "08-ai-agent-handbook-acceptance.md",
        ROOT / ".superpowers" / "sdd" / "task-6" / "report.md",
    )

    assert actual_exit == expected_exit
    _secret_absent(secret, (stdout.encode(), stderr.encode(), diff.stdout, diff.stderr))
    _secret_absent(secret, tuple(path.read_bytes() for path in files))
    match mode:
        case "noop" | "failure":
            assert after == before
        case "changed":
            changed = manifest.root[0]
            after_hashes = {item.path: item.sha256 for item in after.files}
            paths = {item.path for item in before.files if item.sha256 != after_hashes[item.path]}
            assert paths == {
                f"en/{changed.product}/{changed.slug}.md",
                f"zh-CN/{changed.product}/{changed.slug}.md",
            }
        case _:
            assert_never(mode)

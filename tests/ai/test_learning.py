# Copyright 2026
# ruff: noqa: D103,INP001,S101

"""Strict bilingual learning-path data tests."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from scripts.ai.errors import AIAgentError, ErrorCode
from scripts.ai.learning import load_learning_bundles
from scripts.ai.manifest import load_sources

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST = load_sources(REPO_ROOT / "source-ai" / "sources.yaml")
LEARNING_ROOT = REPO_ROOT / "source-ai" / "learning"


def _copy_learning(tmp_path: Path) -> Path:
    target = tmp_path / "learning"
    target.parent.mkdir(parents=True, exist_ok=True)
    _ = shutil.copytree(LEARNING_ROOT, target)
    return target


def _json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: object) -> None:
    _ = path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _expect_invalid(root: Path) -> None:
    with pytest.raises(AIAgentError) as exc_info:
        _ = load_learning_bundles(root, MANIFEST)
    assert exc_info.value.code == ErrorCode.VALIDATION_FAILED


def test_loads_exact_bilingual_learning_paths() -> None:
    bundles = load_learning_bundles(LEARNING_ROOT, MANIFEST)

    assert [bundle.path.product for bundle in bundles] == ["claude-code", "codex"]
    assert [len(bundle.path.stages) for bundle in bundles] == [8, 7]
    for bundle in bundles:
        expected_stages = {stage.id for stage in bundle.path.stages}
        expected_tasks = {
            task.id
            for stage in bundle.path.stages
            for task in stage.tasks
        }
        assert set(bundle.en.stages) == expected_stages
        assert set(bundle.zh_cn.stages) == expected_stages
        assert set(bundle.en.tasks) == expected_tasks
        assert set(bundle.zh_cn.tasks) == expected_tasks


@pytest.mark.parametrize("mutation", ["missing", "extra", "symlink"])
def test_rejects_an_inexact_learning_file_set(
    tmp_path: Path,
    mutation: str,
) -> None:
    root = _copy_learning(tmp_path)
    target = root / "codex.zh-CN.json"
    if mutation == "missing":
        target.unlink()
    elif mutation == "extra":
        _ = (root / "extra.json").write_text("{}\n", encoding="utf-8")
    else:
        target.unlink()
        try:
            target.symlink_to(root / "codex.en.json")
        except OSError:
            pytest.skip("symlinks unavailable")

    _expect_invalid(root)


def test_rejects_unknown_or_cross_product_source_id(tmp_path: Path) -> None:
    root = _copy_learning(tmp_path)
    path = root / "codex.path.json"
    value = _json(path)
    value["stages"][0]["source_ids"][0] = "claude-code/quickstart"  # type: ignore[index]
    _write_json(path, value)

    _expect_invalid(root)


def test_rejects_missing_or_orphaned_localized_keys(tmp_path: Path) -> None:
    root = _copy_learning(tmp_path)
    path = root / "claude-code.zh-CN.json"
    value = _json(path)
    del value["stages"]["hooks"]  # type: ignore[index]
    value["tasks"]["orphan-task"] = {  # type: ignore[index]
        "title": "孤立任务",
        "instruction": "不应存在。",
        "done_when": "不应存在。",
    }
    _write_json(path, value)

    _expect_invalid(root)


def test_rejects_duplicate_global_task_ids(tmp_path: Path) -> None:
    root = _copy_learning(tmp_path)
    path = root / "claude-code.path.json"
    value = _json(path)
    duplicate = value["stages"][0]["tasks"][0]["id"]  # type: ignore[index]
    value["stages"][1]["tasks"][0]["id"] = duplicate  # type: ignore[index]
    _write_json(path, value)

    _expect_invalid(root)


def test_rejects_non_kebab_ids_and_empty_copy(tmp_path: Path) -> None:
    root = _copy_learning(tmp_path)
    structure_path = root / "codex.path.json"
    structure = _json(structure_path)
    structure["stages"][0]["id"] = "Not Safe"  # type: ignore[index]
    _write_json(structure_path, structure)
    _expect_invalid(root)

    root = _copy_learning(tmp_path / "second")
    copy_path = root / "codex.en.json"
    copy = _json(copy_path)
    copy["summary"] = " "
    _write_json(copy_path, copy)
    _expect_invalid(root)

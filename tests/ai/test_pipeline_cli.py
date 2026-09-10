# Copyright 2026
# ruff: noqa: INP001, S101

"""Smoke tests for the internal reviewed-repair control plane."""

from __future__ import annotations

import json
from contextlib import contextmanager
from typing import TYPE_CHECKING, cast

from typer.testing import CliRunner

from scripts.ai.pipeline import PipelineStore
from scripts.ai.pipeline_cli import app
from scripts.ai.pipeline_dispatcher import (
    DispatcherSnapshot,
    PipelineDispatcher,
)
from scripts.ai.review_contract import (
    RepairIssueDraft,
    RepairReadyReview,
    RepairReadyReviewDraft,
)

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

    import pytest

EXPECTED_SPAN_LINE = 3


def test_status_emits_machine_readable_empty_pipeline(tmp_path: Path) -> None:
    """The CLI exposes queue and lane state without creating provider work."""
    pipeline_root = tmp_path / "pipeline"
    result = CliRunner().invoke(
        app,
        [
            "status",
            "--repo-root",
            str(tmp_path),
            "--pipeline-root",
            str(pipeline_root),
        ],
    )

    assert result.exit_code == 0
    payload = cast("dict[str, object]", json.loads(result.stdout))
    assert payload["total"] == 0
    assert payload["repair_running_by_provider"] == {"kimi": 0, "glm": 0}
    assert payload["review_running_by_reviewer"] == {
        "gpt-5.6-terra": 0,
        "grok-4.5": 0,
    }
    metrics_result = CliRunner().invoke(
        app,
        [
            "metrics",
            "--repo-root",
            str(tmp_path),
            "--pipeline-root",
            str(pipeline_root),
        ],
    )
    assert metrics_result.exit_code == 0
    metrics = cast("dict[str, object]", json.loads(metrics_result.stdout))
    stages = cast("dict[str, dict[str, int]]", metrics["stages"])
    assert stages["repair_queue_wait"]["samples"] == 0


def test_dispatch_run_holds_singleton_coordinator_lock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A long-lived dispatcher cannot accidentally be started twice."""
    held: list[str] = []

    @contextmanager
    def record_lock(
        _store: PipelineStore,
        name: str,
    ) -> Generator[None]:
        held.append(name)
        yield

    def fake_run(
        dispatcher: PipelineDispatcher,
        **_kwargs: object,
    ) -> DispatcherSnapshot:
        return dispatcher.reconcile()

    monkeypatch.setattr(PipelineStore, "coordinator_lock", record_lock)
    monkeypatch.setattr(PipelineDispatcher, "run", fake_run)

    result = CliRunner().invoke(
        app,
        [
            "dispatch-run",
            "--max-cycles",
            "1",
            "--repo-root",
            str(tmp_path),
            "--pipeline-root",
            str(tmp_path / "pipeline"),
        ],
    )

    assert result.exit_code == 0
    assert held[0] == "dispatcher-run"
    assert "dispatcher" in held


def test_bridge_derives_hashes_lines_and_unique_span_evidence(tmp_path: Path) -> None:
    """A small draft becomes a fully validated repair-ready review."""
    source_path = tmp_path / "source-ai" / "content" / "en" / "codex" / "test.md"
    candidate_path = (
        tmp_path / ".ai-local" / "staging" / "dual-review-normalized" / "codex" / "test.md"
    )
    source_path.parent.mkdir(parents=True)
    candidate_path.parent.mkdir(parents=True)
    _ = source_path.write_text(
        "# Test\n\nThe setting must stay enabled.\n",
        encoding="utf-8",
        newline="\n",
    )
    _ = candidate_path.write_text(
        "# 测试\n\n该设置必须保持禁用。\n",
        encoding="utf-8",
        newline="\n",
    )
    draft = RepairReadyReviewDraft(
        source_id="codex/test",
        assigned_reviewer="gpt-5.6-terra",
        verdict="fail",
        source_path=source_path.relative_to(tmp_path).as_posix(),
        candidate_path=candidate_path.relative_to(tmp_path).as_posix(),
        source_report_paths=(".ai-local/reviews/terra/codex/test.json",),
        issues=(
            RepairIssueDraft(
                source_issue_refs=("terra:0",),
                severity="high",
                category="semantic_reversal",
                location="opening paragraph",
                source_excerpt="The setting must stay enabled.",
                candidate_span_text="该设置必须保持禁用。",
                explanation="The candidate reverses enabled and disabled.",
            ),
        ),
    )
    draft_path = tmp_path / ".ai-local" / "draft.json"
    output_path = tmp_path / ".ai-local" / "ready.json"
    _ = draft_path.write_text(draft.model_dump_json(indent=2), encoding="utf-8")

    result = CliRunner().invoke(
        app,
        [
            "bridge",
            str(draft_path),
            str(output_path),
            "--repo-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    review = RepairReadyReview.model_validate_json(output_path.read_text(encoding="utf-8"))
    assert review.review_model == "gpt-5.6-terra"
    assert review.issues[0].candidate_span.line_start == EXPECTED_SPAN_LINE
    assert review.issues[0].candidate_span.occurrence_count == 1

    queue_result = CliRunner().invoke(
        app,
        [
            "queue",
            str(output_path),
            "--provider",
            "kimi",
            "--attempt-id",
            "canary-1",
            "--actor",
            "test",
            "--repo-root",
            str(tmp_path),
            "--pipeline-root",
            str(tmp_path / ".ai-local" / "pipeline"),
        ],
    )
    assert queue_result.exit_code == 0
    queued = cast("dict[str, object]", json.loads(queue_result.stdout))
    assert queued["state"] == "repair_queued"
    assert queued["provider_model"] == "k3"

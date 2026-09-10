# Copyright 2026
# ruff: noqa: INP001, S101

"""Tests for atomic reviewer-partitioned deep-audit admission."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

import scripts.ai.audit_admission as admission_module
from scripts.ai.audit_admission import (
    admit_audit_pilot,
    assign_repair_providers,
)
from scripts.ai.audit_bridge import DeepAuditManifest, DeepAuditManifestEntry
from scripts.ai.audit_inventory import (
    AuditInventory,
    InventorySource,
    InventoryStatus,
    PilotBatch,
    ReviewScan,
    ReviewSourceEvidence,
    build_inventory_from_sources,
)
from scripts.ai.page_format import WARNING
from scripts.ai.pipeline import PipelineStore
from scripts.ai.pipeline_intake import (
    AuditIntakeState,
    AuditIntakeStore,
)

if TYPE_CHECKING:
    from pathlib import Path

SOURCE_ID = "codex/admission-test"
CONTENT_HASH = "a" * 64
REVIEW_WORKFLOW_V3 = 3


def test_balances_future_repair_work_deterministically() -> None:
    """One Kimi and one GLM lane receive LPT-balanced future repairs."""
    selections = (
        ("codex/large", 100),
        ("codex/medium", 60),
        ("codex/small-a", 40),
        ("codex/small-b", 20),
    )

    first = assign_repair_providers(selections)
    repeated = assign_repair_providers(reversed(selections))

    assert first == repeated
    assert first["codex/large"] == "glm"
    assert first["codex/medium"] == "kimi"
    assert set(first.values()) == {"kimi", "glm"}


def test_admits_and_replays_one_manifest_bound_intake(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A crash-safe admission replay never duplicates or reassigns a page."""
    _install_source(tmp_path)
    store = PipelineStore(tmp_path / ".ai-local/pipeline-v1", tmp_path)
    intake_store = AuditIntakeStore(store)
    source = InventorySource(
        source_id=SOURCE_ID,
        product="codex",
        title="Admission Test",
    )
    inventory = build_inventory_from_sources(
        tmp_path,
        (source,),
        manifest_path="source-ai/sources.yaml",
        manifest_sha256="f" * 64,
        review_scan=ReviewScan(
            files_scanned=1,
            exact_source_reports=1,
            ignored_malformed=0,
            ignored_unknown_source=0,
            ignored_without_reviewer=0,
            evidence=(
                ReviewSourceEvidence(
                    source_id=SOURCE_ID,
                    reviewers=("gpt-5.6-terra",),
                    reviewer_report_count=1,
                ),
            ),
        ),
    )
    assert inventory.items[0].status == InventoryStatus.ELIGIBLE_ASSIGNED

    def fake_build_inventory(
        *_args: object,
        **_kwargs: object,
    ) -> AuditInventory:
        return inventory

    monkeypatch.setattr(
        admission_module,
        "build_inventory",
        fake_build_inventory,
    )

    first = admit_audit_pilot(
        repo_root=tmp_path,
        intake_store=intake_store,
        batch_id="pilot-test",
        max_pages=2,
        actor="test",
        review_workflow_version=REVIEW_WORKFLOW_V3,
    )
    repeated = admit_audit_pilot(
        repo_root=tmp_path,
        intake_store=intake_store,
        batch_id="pilot-test",
        max_pages=2,
        actor="test",
        review_workflow_version=REVIEW_WORKFLOW_V3,
    )

    assert repeated == first
    assert len(first.admitted) == 1
    intake = intake_store.load(first.admitted[0].intake_id)
    assert intake.source_id == SOURCE_ID
    assert intake.assigned_reviewer == "gpt-5.6-terra"
    assert intake.state == AuditIntakeState.AUDIT_QUEUED
    assert len(intake_store.list_items()) == 1
    manifest = DeepAuditManifest.model_validate_json(
        (tmp_path / first.manifest_path).read_text(encoding="utf-8")
    )
    entry = DeepAuditManifestEntry.model_validate(manifest.entries[0])
    assert entry.review_workflow_version == REVIEW_WORKFLOW_V3
    assert entry.v3_context_path is not None
    assert (tmp_path / entry.v3_context_path).is_file()
    selection = PilotBatch.model_validate_json(
        (
            tmp_path
            / ".ai-local/pipeline-v1/admission-batches/pilot-test.selection.json"
        ).read_text(encoding="utf-8")
    )
    assert {
        "codex/agent-configuration/rules",
        "codex/github-action",
    } <= set(selection.excluded_source_ids)


def test_v3_admission_excludes_hard_preflight_pages_before_intake(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A hard final-shape defect cannot consume a v3 reviewer slot."""
    _install_source(tmp_path)
    candidate_path = (
        tmp_path
        / ".ai-local/staging/dual-review-normalized"
        / f"{SOURCE_ID}.md"
    )
    _ = candidate_path.write_text(
        candidate_path.read_text(encoding="utf-8")
        + "\n[broken section](#missing-heading)\n",
        encoding="utf-8",
        newline="\n",
    )
    store = PipelineStore(tmp_path / ".ai-local/pipeline-v1", tmp_path)
    intake_store = AuditIntakeStore(store)
    inventory = build_inventory_from_sources(
        tmp_path,
        (
            InventorySource(
                source_id=SOURCE_ID,
                product="codex",
                title="Admission Test",
            ),
        ),
        manifest_path="source-ai/sources.yaml",
        manifest_sha256="f" * 64,
        review_scan=ReviewScan(
            files_scanned=1,
            exact_source_reports=1,
            ignored_malformed=0,
            ignored_unknown_source=0,
            ignored_without_reviewer=0,
            evidence=(
                ReviewSourceEvidence(
                    source_id=SOURCE_ID,
                    reviewers=("gpt-5.6-terra",),
                    reviewer_report_count=1,
                ),
            ),
        ),
    )

    monkeypatch.setattr(
        admission_module,
        "build_inventory",
        lambda *_args, **_kwargs: inventory,
    )

    with pytest.raises(ValueError, match="only 0 are safely eligible"):
        _ = admit_audit_pilot(
            repo_root=tmp_path,
            intake_store=intake_store,
            batch_id="hard-preflight",
            max_pages=1,
            actor="test",
            review_workflow_version=REVIEW_WORKFLOW_V3,
        )
    assert intake_store.list_items() == ()


def test_v3_admission_excludes_fenced_block_count_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An unmatched code block cannot enter a v3 reviewer lane."""
    _install_source(tmp_path)
    english_path = tmp_path / f"source-ai/content/en/{SOURCE_ID}.md"
    _ = english_path.write_text(
        english_path.read_text(encoding="utf-8")
        + "\n```text\nsource only\n```\n",
        encoding="utf-8",
        newline="\n",
    )
    store = PipelineStore(tmp_path / ".ai-local/pipeline-v1", tmp_path)
    intake_store = AuditIntakeStore(store)
    inventory = build_inventory_from_sources(
        tmp_path,
        (
            InventorySource(
                source_id=SOURCE_ID,
                product="codex",
                title="Admission Test",
            ),
        ),
        manifest_path="source-ai/sources.yaml",
        manifest_sha256="f" * 64,
        review_scan=ReviewScan(
            files_scanned=0,
            exact_source_reports=0,
            ignored_malformed=0,
            ignored_unknown_source=0,
            ignored_without_reviewer=0,
        ),
    )
    monkeypatch.setattr(
        admission_module,
        "build_inventory",
        lambda *_args, **_kwargs: inventory,
    )

    with pytest.raises(ValueError, match="only 0 are safely eligible"):
        _ = admit_audit_pilot(
            repo_root=tmp_path,
            intake_store=intake_store,
            batch_id="fence-mismatch",
            max_pages=1,
            actor="test",
            review_workflow_version=REVIEW_WORKFLOW_V3,
        )
    assert intake_store.list_items() == ()


def test_v3_admission_assigns_non_gpt_repair_to_historical_gpt_candidate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Historical GPT text may be audited while repairs stay off GPT."""
    _install_source(tmp_path)
    candidate_path = (
        tmp_path
        / ".ai-local/staging/dual-review-normalized"
        / f"{SOURCE_ID}.md"
    )
    candidate = candidate_path.read_text(encoding="utf-8").replace(
        "translation_model: k3",
        "translation_model: gpt-5.6",
        1,
    )
    _ = candidate_path.write_text(
        candidate,
        encoding="utf-8",
        newline="\n",
    )
    store = PipelineStore(tmp_path / ".ai-local/pipeline-v1", tmp_path)
    intake_store = AuditIntakeStore(store)
    inventory = build_inventory_from_sources(
        tmp_path,
        (
            InventorySource(
                source_id=SOURCE_ID,
                product="codex",
                title="Admission Test",
            ),
        ),
        manifest_path="source-ai/sources.yaml",
        manifest_sha256="f" * 64,
        review_scan=ReviewScan(
            files_scanned=1,
            exact_source_reports=1,
            ignored_malformed=0,
            ignored_unknown_source=0,
            ignored_without_reviewer=0,
            evidence=(
                ReviewSourceEvidence(
                    source_id=SOURCE_ID,
                    reviewers=("gpt-5.6-terra",),
                    reviewer_report_count=1,
                ),
            ),
        ),
    )
    assert inventory.items[0].translation_provider == "gpt"
    monkeypatch.setattr(
        admission_module,
        "build_inventory",
        lambda *_args, **_kwargs: inventory,
    )

    batch = admit_audit_pilot(
        repo_root=tmp_path,
        intake_store=intake_store,
        batch_id="historical-gpt",
        max_pages=1,
        actor="test",
        review_workflow_version=REVIEW_WORKFLOW_V3,
    )

    assert len(batch.admitted) == 1
    assert batch.admitted[0].source_id == SOURCE_ID
    assert batch.admitted[0].repair_provider in {"kimi", "glm"}
    assert len(intake_store.list_items()) == 1


def test_v3_admission_excludes_final_shape_link_count_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Selection runs the same pair-level gate as final manifest preparation."""
    _install_source(tmp_path)
    candidate_path = (
        tmp_path
        / ".ai-local/staging/dual-review-normalized"
        / f"{SOURCE_ID}.md"
    )
    _ = candidate_path.write_text(
        candidate_path.read_text(encoding="utf-8")
        + "\n[额外链接](https://example.test/extra)\n",
        encoding="utf-8",
        newline="\n",
    )
    store = PipelineStore(tmp_path / ".ai-local/pipeline-v1", tmp_path)
    intake_store = AuditIntakeStore(store)
    inventory = build_inventory_from_sources(
        tmp_path,
        (
            InventorySource(
                source_id=SOURCE_ID,
                product="codex",
                title="Admission Test",
            ),
        ),
        manifest_path="source-ai/sources.yaml",
        manifest_sha256="f" * 64,
        review_scan=ReviewScan(
            files_scanned=0,
            exact_source_reports=0,
            ignored_malformed=0,
            ignored_unknown_source=0,
            ignored_without_reviewer=0,
        ),
    )
    monkeypatch.setattr(
        admission_module,
        "build_inventory",
        lambda *_args, **_kwargs: inventory,
    )

    with pytest.raises(ValueError, match="only 0 are safely eligible"):
        _ = admit_audit_pilot(
            repo_root=tmp_path,
            intake_store=intake_store,
            batch_id="link-count-mismatch",
            max_pages=1,
            actor="test",
            review_workflow_version=REVIEW_WORKFLOW_V3,
        )
    assert intake_store.list_items() == ()


def _install_source(root: Path) -> None:
    manifest = [
        {
            "id": SOURCE_ID,
            "product": "codex",
            "slug": "admission-test",
            "title": "Admission Test",
            "canonical_url": "https://developers.openai.com/codex/admission-test",
            "fetch_url": "https://developers.openai.com/codex/admission-test.md",
            "fetch_format": "markdown",
            "owner": "OpenAI",
            "section": "Docs",
        }
    ]
    _write(
        root / "source-ai/sources.yaml",
        json.dumps(manifest, indent=2),
    )
    _write(
        root / f"source-ai/content/en/{SOURCE_ID}.md",
        (
            "---\n"
            "title: Admission Test\n"
            f"source_id: {SOURCE_ID}\n"
            "product: codex\n"
            "lang: en\n"
            "canonical_url: https://developers.openai.com/codex/admission-test\n"
            "owner: OpenAI\n"
            f"content_sha256: {CONTENT_HASH}\n"
            "---\n"
            "[Official source](https://developers.openai.com/codex/admission-test)\n\n"
            "Content owner: OpenAI\n\n"
            "# Admission Test\n\n"
            "Review this page.\n"
        ),
    )
    _write(
        root / f".ai-local/staging/dual-review-normalized/{SOURCE_ID}.md",
        (
            "---\n"
            "title: 准入测试\n"
            f"source_id: {SOURCE_ID}\n"
            "product: codex\n"
            "lang: zh-CN\n"
            "canonical_url: https://developers.openai.com/codex/admission-test\n"
            "owner: OpenAI\n"
            f"content_sha256: {CONTENT_HASH}\n"
            f"translation_of: {SOURCE_ID}\n"
            "translation_model: k3\n"
            "ai_translated: true\n"
            "---\n"
            f"{WARNING}\n\n"
            "[官方来源](https://developers.openai.com/codex/admission-test)\n\n"
            "内容所有者: OpenAI\n\n"
            "# 准入测试\n\n"
            "审核此页面。\n"
        ),
    )
    _write(
        root / f".ai-local/reviews/assigned/{SOURCE_ID}.json",
        json.dumps(
            {
                "source_id": SOURCE_ID,
                "assigned_reviewer": "gpt-5.6-terra",
                "status": "warn",
            }
        ),
    )


def _write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(value, encoding="utf-8", newline="\n")

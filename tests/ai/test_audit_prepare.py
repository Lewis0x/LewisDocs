# Copyright 2026
# ruff: noqa: INP001, S101

"""Tests for explicit deep-audit manifest preparation."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import pytest

from scripts.ai.audit_bridge import DeepAuditManifestEntry
from scripts.ai.audit_context import AuditV3Context
from scripts.ai.audit_coverage import AuditPass
from scripts.ai.audit_history import AuditHistoryRecovery
from scripts.ai.audit_preflight import AuditPreflightEvidence
from scripts.ai.audit_prepare import prepare_deep_audit_manifest
from scripts.ai.audit_v3 import AuditV3Plan, AuditV3SliceReport
from scripts.ai.audit_worker import (
    AuditWorkerManifest,
    finalize_assigned_audit_worker,
    prepare_assigned_audit_worker,
)
from scripts.ai.page_format import WARNING
from scripts.ai.pipeline import PipelineStore
from scripts.ai.pipeline_intake import AuditIntakeSpec, AuditIntakeStore
from scripts.ai.review_contract import sha256_path

if TYPE_CHECKING:
    from pathlib import Path

    from scripts.ai.audit_bridge import DeepAuditManifest

SOURCE_ID = "codex/explicit-audit"
CONTENT_HASH = "a" * 64
COVERAGE_VERSION = 2
REVIEW_WORKFLOW_V3 = 3
EXPECTED_CATEGORY_COUNT = 14


def _write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(value, encoding="utf-8", newline="\n")


def _install_pair(root: Path) -> None:
    _write(
        root / f"source-ai/content/en/{SOURCE_ID}.md",
        (
            "---\n"
            "title: Explicit audit\n"
            f"source_id: {SOURCE_ID}\n"
            "product: codex\n"
            "lang: en\n"
            "canonical_url: https://example.test/explicit-audit\n"
            "owner: OpenAI\n"
            f"content_sha256: {CONTENT_HASH}\n"
            "---\n"
            "[Official source](https://example.test/explicit-audit)\n\n"
            "Content owner: OpenAI\n\n"
            "# Explicit audit\n\n"
            "## Details\n\n"
            "Review this page.\n"
        ),
    )
    _write(
        root
        / f".ai-local/staging/dual-review-normalized/{SOURCE_ID}.md",
        (
            "---\n"
            "title: 显式审核\n"
            f"source_id: {SOURCE_ID}\n"
            "product: codex\n"
            "lang: zh-CN\n"
            "canonical_url: https://example.test/explicit-audit\n"
            "owner: OpenAI\n"
            f"content_sha256: {CONTENT_HASH}\n"
            f"translation_of: {SOURCE_ID}\n"
            "translation_model: glm-5.2\n"
            "ai_translated: true\n"
            "---\n"
            f"{WARNING}\n\n"
            "[官方来源](https://example.test/explicit-audit)\n\n"
            "内容所有者: OpenAI\n\n"
            "# 显式审核\n\n"
            "## 详情\n\n"
            "审核此页面。\n"
        ),
    )


def _prepare(root: Path) -> tuple[DeepAuditManifest, Path]:
    output = root / ".ai-local/explicit-audit.json"
    store = PipelineStore(root / ".ai-local/pipeline-v1", root)
    manifest = prepare_deep_audit_manifest(
        repo_root=root,
        output_path=output,
        source_ids=(SOURCE_ID,),
        intake_store=AuditIntakeStore(store),
    )
    return manifest, output


def test_prepares_idempotent_hash_bound_public_pair(tmp_path: Path) -> None:
    """Write review files and deterministic evidence before an LLM sees them."""
    _install_pair(tmp_path)

    manifest, output = _prepare(tmp_path)
    first_bytes = output.read_bytes()
    repeated, _ = _prepare(tmp_path)

    assert manifest == repeated
    assert output.read_bytes() == first_bytes
    entry = manifest.entries[0]
    assert entry["audit_contract_version"] == COVERAGE_VERSION
    coverage = entry["coverage_contract"]
    assert isinstance(coverage, dict)
    coverage_record = cast("dict[str, object]", coverage)
    assert coverage_record["version"] == COVERAGE_VERSION
    assert coverage_record["mandatory_passes"] == (
        "semantic",
        "surface",
        "coverage",
    )
    mandatory_categories = cast(
        "tuple[object, ...]",
        coverage_record["mandatory_categories"],
    )
    assert len(mandatory_categories) == EXPECTED_CATEGORY_COUNT
    sections = cast(
        "tuple[dict[str, object], ...]",
        coverage_record["sections"],
    )
    assert sections[0]["section_id"] == "frontmatter"
    assert sections[-1]["section_id"] == "eof"
    english = tmp_path / str(entry["english_path"])
    chinese = tmp_path / str(entry["chinese_path"])
    evidence = (
        tmp_path
        / ".ai-local/final-shape-evidence/codex/explicit-audit.json"
    )
    assert sha256_path(english) == entry["source_sha256"]
    assert sha256_path(chinese) == entry["candidate_sha256"]
    assert evidence.is_file()
    assert '"passed": true' in evidence.read_text(encoding="utf-8")


def test_prepares_candidate_override_under_isolated_artifact_root(
    tmp_path: Path,
) -> None:
    """Keep post-repair review evidence separate from canonical audit files."""
    _install_pair(tmp_path)
    default_candidate = (
        tmp_path
        / f".ai-local/staging/dual-review-normalized/{SOURCE_ID}.md"
    )
    snapshot = tmp_path / f".ai-local/snapshot/zh-CN/{SOURCE_ID}.md"
    snapshot_text = (
        default_candidate.read_text(encoding="utf-8").rstrip()
        + "\n\nSnapshot candidate.\n"
    )
    _write(snapshot, snapshot_text)
    artifact_root = tmp_path / ".ai-local/isolated-grok"
    output = artifact_root / "manifest.json"
    store = PipelineStore(artifact_root / "pipeline", tmp_path)

    manifest = prepare_deep_audit_manifest(
        repo_root=tmp_path,
        output_path=output,
        source_ids=(SOURCE_ID,),
        intake_store=AuditIntakeStore(store),
        review_workflow_version=3,
        assigned_reviewers={SOURCE_ID: "grok-4.5"},
        candidate_paths={SOURCE_ID: snapshot},
        artifact_root=artifact_root / "evidence",
    )

    entry = DeepAuditManifestEntry.model_validate(manifest.entries[0])
    assert entry.chinese_path.startswith(
        ".ai-local/isolated-grok/evidence/audit-materialized/"
    )
    assert entry.normalized_candidate_path.startswith(
        ".ai-local/isolated-grok/evidence/audit-normalized-v3/"
    )
    assert entry.v3_context_path is not None
    assert entry.v3_context_path.startswith(
        ".ai-local/isolated-grok/evidence/audit-v3-context/"
    )
    assert "Snapshot candidate." in (
        tmp_path / entry.normalized_candidate_path
    ).read_text(encoding="utf-8")
    assert not (
        tmp_path / f".ai-local/audit-materialized/{SOURCE_ID}/en.md"
    ).exists()


def test_rejects_duplicate_or_reserved_source(tmp_path: Path) -> None:
    """Do not prepare duplicate work or bypass source-level ownership."""
    _install_pair(tmp_path)
    store = PipelineStore(tmp_path / ".ai-local/pipeline-v1", tmp_path)
    with pytest.raises(ValueError, match="must be unique"):
        _ = prepare_deep_audit_manifest(
            repo_root=tmp_path,
            output_path=tmp_path / ".ai-local/duplicate.json",
            source_ids=(SOURCE_ID, SOURCE_ID),
            intake_store=AuditIntakeStore(store),
        )

    _ = store.reserve_source(SOURCE_ID, "b" * 64)
    with pytest.raises(ValueError, match="active intake"):
        _ = prepare_deep_audit_manifest(
            repo_root=tmp_path,
            output_path=tmp_path / ".ai-local/reserved.json",
            source_ids=(SOURCE_ID,),
            intake_store=AuditIntakeStore(store),
        )


def test_rejects_existing_formal_target(tmp_path: Path) -> None:
    """Never replace a formal page while merely preparing an audit."""
    _install_pair(tmp_path)
    _write(
        tmp_path / f"source-ai/content/zh-CN/{SOURCE_ID}.md",
        "already formal\n",
    )

    with pytest.raises(ValueError, match="formal Chinese target"):
        _ = _prepare(tmp_path)


def test_rejects_existing_canonical_intake(tmp_path: Path) -> None:
    """A completed or terminal intake must not silently start over."""
    _install_pair(tmp_path)
    store = PipelineStore(tmp_path / ".ai-local/pipeline-v1", tmp_path)
    intake_store = AuditIntakeStore(store)
    manifest_path = tmp_path / ".ai-local/first.json"
    _ = prepare_deep_audit_manifest(
        repo_root=tmp_path,
        output_path=manifest_path,
        source_ids=(SOURCE_ID,),
        intake_store=intake_store,
    )
    item = intake_store.create(
        AuditIntakeSpec(
            source_id=SOURCE_ID,
            manifest_path=".ai-local/first.json",
            assigned_reviewer="gpt-5.6-terra",
            provider="glm",
            attempt_id="first-canonical-audit",
        ),
        actor="test",
    )
    store.release_source_reservation(SOURCE_ID, item.intake_id)

    with pytest.raises(ValueError, match="canonical audit intake"):
        _ = prepare_deep_audit_manifest(
            repo_root=tmp_path,
            output_path=tmp_path / ".ai-local/repeated.json",
            source_ids=(SOURCE_ID,),
            intake_store=intake_store,
        )


def test_prepares_one_shared_v2_worker_contract(tmp_path: Path) -> None:
    """Terra and Grok workers receive the same immutable contract shape."""
    _install_pair(tmp_path)
    store = PipelineStore(tmp_path / ".ai-local/pipeline-v1", tmp_path)
    intake_store = AuditIntakeStore(store)
    manifest_path = tmp_path / ".ai-local/worker-audit.json"
    _ = prepare_deep_audit_manifest(
        repo_root=tmp_path,
        output_path=manifest_path,
        source_ids=(SOURCE_ID,),
        intake_store=intake_store,
    )
    intake = intake_store.create(
        AuditIntakeSpec(
            source_id=SOURCE_ID,
            manifest_path=".ai-local/worker-audit.json",
            assigned_reviewer="gpt-5.6-terra",
            provider="glm",
            attempt_id="worker-contract",
        ),
        actor="test",
    )
    _ = intake_store.claim_audit(intake.intake_id, "terra-worker")

    first = prepare_assigned_audit_worker(
        intake_store,
        intake_id=intake.intake_id,
        worker_id="terra-worker",
    )
    repeated = prepare_assigned_audit_worker(
        intake_store,
        intake_id=intake.intake_id,
        worker_id="terra-worker",
    )

    assert first == repeated
    assert (
        AuditWorkerManifest.model_validate(first).audit_contract_version
        == COVERAGE_VERSION
    )
    prompt = (tmp_path / first.prompt_path).read_text(encoding="utf-8")
    schema = (tmp_path / first.schema_path).read_text(encoding="utf-8")
    assert "Pass A" in prompt
    assert '"checked_section_ids"' in schema
    assert first.findings_path.endswith("findings-v1.json")
    assert first.coverage_contract.source_id == SOURCE_ID
    assert first.report_path.endswith(f"{SOURCE_ID}.json")


def test_prepares_hash_bound_v3_evidence_context(tmp_path: Path) -> None:
    """V3 preparation binds preflight, history, context, and orthogonal plan."""
    _install_pair(tmp_path)
    output = tmp_path / ".ai-local/v3-audit.json"
    store = PipelineStore(tmp_path / ".ai-local/pipeline-v1", tmp_path)

    manifest = prepare_deep_audit_manifest(
        repo_root=tmp_path,
        output_path=output,
        source_ids=(SOURCE_ID,),
        intake_store=AuditIntakeStore(store),
        review_workflow_version=3,
        assigned_reviewers={SOURCE_ID: "gpt-5.6-terra"},
    )

    entry = DeepAuditManifestEntry.model_validate(manifest.entries[0])
    assert entry.review_workflow_version == REVIEW_WORKFLOW_V3
    assert entry.preflight_path is not None
    assert entry.history_path is not None
    assert entry.v3_context_path is not None
    assert entry.v3_plan_path is not None
    preflight_path = tmp_path / entry.preflight_path
    history_path = tmp_path / entry.history_path
    context_path = tmp_path / entry.v3_context_path
    plan_path = tmp_path / entry.v3_plan_path
    assert sha256_path(preflight_path) == entry.preflight_sha256
    assert sha256_path(history_path) == entry.history_sha256
    assert sha256_path(context_path) == entry.v3_context_sha256
    assert sha256_path(plan_path) == entry.v3_plan_sha256

    preflight = AuditPreflightEvidence.model_validate_json(
        preflight_path.read_text(encoding="utf-8")
    )
    history = AuditHistoryRecovery.model_validate_json(
        history_path.read_text(encoding="utf-8")
    )
    context = AuditV3Context.model_validate_json(
        context_path.read_text(encoding="utf-8")
    )
    plan = AuditV3Plan.model_validate_json(
        plan_path.read_text(encoding="utf-8")
    )
    assert preflight.source_id == SOURCE_ID
    assert history.assigned_reviewer == "gpt-5.6-terra"
    assert context.plan == plan
    assert context.assigned_reviewer == "gpt-5.6-terra"


def test_v3_preparation_restores_fences_into_immutable_candidate(
    tmp_path: Path,
) -> None:
    """Review and repair the exact candidate whose code matches English."""
    _install_pair(tmp_path)
    english_path = tmp_path / f"source-ai/content/en/{SOURCE_ID}.md"
    candidate_path = (
        tmp_path
        / f".ai-local/staging/dual-review-normalized/{SOURCE_ID}.md"
    )
    _ = english_path.write_text(
        english_path.read_text(encoding="utf-8")
        + "\n```python\nprint('source')\n```\n",
        encoding="utf-8",
        newline="\n",
    )
    _ = candidate_path.write_text(
        candidate_path.read_text(encoding="utf-8")
        + "\n```python\nprint('translated')\n```\n",
        encoding="utf-8",
        newline="\n",
    )
    output = tmp_path / ".ai-local/v3-fence-audit.json"
    store = PipelineStore(tmp_path / ".ai-local/pipeline-v1", tmp_path)

    manifest = prepare_deep_audit_manifest(
        repo_root=tmp_path,
        output_path=output,
        source_ids=(SOURCE_ID,),
        intake_store=AuditIntakeStore(store),
        review_workflow_version=3,
        assigned_reviewers={SOURCE_ID: "gpt-5.6-terra"},
    )

    entry = DeepAuditManifestEntry.model_validate(manifest.entries[0])
    normalized_path = tmp_path / entry.normalized_candidate_path
    normalized_text = normalized_path.read_text(encoding="utf-8")
    public_text = (tmp_path / entry.chinese_path).read_text(encoding="utf-8")
    assert ".ai-local/audit-normalized-v3/" in entry.normalized_candidate_path
    assert entry.fenced_blocks_restored == 1
    assert sha256_path(normalized_path) == entry.normalized_candidate_sha256
    assert "print('source')" in normalized_text
    assert "print('translated')" not in normalized_text
    assert "print('source')" in public_text


def test_v3_preparation_preserves_reader_facing_fenced_prose(
    tmp_path: Path,
) -> None:
    """Keep translated reader prose while restoring executable fenced code."""
    _install_pair(tmp_path)
    english_path = tmp_path / f"source-ai/content/en/{SOURCE_ID}.md"
    candidate_path = (
        tmp_path
        / f".ai-local/staging/dual-review-normalized/{SOURCE_ID}.md"
    )
    _ = english_path.write_text(
        english_path.read_text(encoding="utf-8")
        + (
            "\n```text\nReader source\n```\n"
            "\n```python\nprint('source')\n```\n"
        ),
        encoding="utf-8",
        newline="\n",
    )
    _ = candidate_path.write_text(
        candidate_path.read_text(encoding="utf-8")
        + (
            "\n```text\nReader candidate\n```\n"
            "\n```python\nprint('translated')\n```\n"
        ),
        encoding="utf-8",
        newline="\n",
    )
    output = tmp_path / ".ai-local/v3-reader-fence-audit.json"
    store = PipelineStore(tmp_path / ".ai-local/pipeline-v1", tmp_path)

    manifest = prepare_deep_audit_manifest(
        repo_root=tmp_path,
        output_path=output,
        source_ids=(SOURCE_ID,),
        intake_store=AuditIntakeStore(store),
        review_workflow_version=3,
        assigned_reviewers={SOURCE_ID: "gpt-5.6-terra"},
    )

    entry = DeepAuditManifestEntry.model_validate(manifest.entries[0])
    normalized_path = tmp_path / entry.normalized_candidate_path
    normalized_text = normalized_path.read_text(encoding="utf-8")
    public_text = (tmp_path / entry.chinese_path).read_text(encoding="utf-8")
    assert entry.fenced_blocks_restored == 1
    assert "Reader candidate" in normalized_text
    assert "Reader source" not in normalized_text
    assert "print('source')" in normalized_text
    assert "print('translated')" not in normalized_text
    assert "Reader candidate" in public_text
    assert "print('source')" in public_text


def test_v3_preparation_requires_exact_reviewer_partition(
    tmp_path: Path,
) -> None:
    """A v3 manifest cannot be prepared before reviewer ownership is fixed."""
    _install_pair(tmp_path)
    store = PipelineStore(tmp_path / ".ai-local/pipeline-v1", tmp_path)

    with pytest.raises(ValueError, match="one assigned reviewer"):
        _ = prepare_deep_audit_manifest(
            repo_root=tmp_path,
            output_path=tmp_path / ".ai-local/v3-missing-reviewer.json",
            source_ids=(SOURCE_ID,),
            intake_store=AuditIntakeStore(store),
            review_workflow_version=3,
        )


def test_v3_worker_merges_independent_slice_reports(tmp_path: Path) -> None:
    """A claimed v3 intake merges slice JSON before submitting completion."""
    _install_pair(tmp_path)
    store = PipelineStore(tmp_path / ".ai-local/pipeline-v1", tmp_path)
    intake_store = AuditIntakeStore(store)
    manifest_path = tmp_path / ".ai-local/v3-worker-audit.json"
    _ = prepare_deep_audit_manifest(
        repo_root=tmp_path,
        output_path=manifest_path,
        source_ids=(SOURCE_ID,),
        intake_store=intake_store,
        review_workflow_version=3,
        assigned_reviewers={SOURCE_ID: "gpt-5.6-terra"},
    )
    intake = intake_store.create(
        AuditIntakeSpec(
            source_id=SOURCE_ID,
            manifest_path=".ai-local/v3-worker-audit.json",
            assigned_reviewer="gpt-5.6-terra",
            provider="glm",
            attempt_id="v3-worker-contract",
        ),
        actor="test",
    )
    _ = intake_store.claim_audit(intake.intake_id, "terra-v3-worker")
    worker = prepare_assigned_audit_worker(
        intake_store,
        intake_id=intake.intake_id,
        worker_id="terra-v3-worker",
    )
    assert worker.review_workflow_version == REVIEW_WORKFLOW_V3
    assert worker.v3_context_path is not None
    assert worker.repair_source_path == f"source-ai/content/en/{SOURCE_ID}.md"
    assert worker.repair_candidate_path is not None
    assert worker.repair_source_sha256 is not None
    assert worker.repair_candidate_sha256 is not None
    context = AuditV3Context.model_validate_json(
        (tmp_path / worker.v3_context_path).read_text(encoding="utf-8")
    )
    assert not context.mandatory_evidence
    assert len(worker.slices) == len(context.plan.slices)
    first_prompt = (
        tmp_path / worker.slices[0].prompt_path
    ).read_text(encoding="utf-8")
    assert "RAW REPAIR MAPPING CONTRACT" in first_prompt
    assert worker.repair_source_path in first_prompt
    assert worker.repair_candidate_path in first_prompt
    for artifact, audit_slice in zip(
        worker.slices,
        context.plan.slices,
        strict=True,
    ):
        report = AuditV3SliceReport.model_validate(
            {
                "version": 3,
                "plan_sha256": context.plan.plan_sha256,
                "slice_id": audit_slice.slice_id,
                "slice_sha256": audit_slice.slice_sha256,
                "coverage_contract_sha256": (
                    context.plan.coverage_contract_sha256
                ),
                "source_id": SOURCE_ID,
                "assigned_reviewer": "gpt-5.6-terra",
                "review_model": "gpt-5.6-terra",
                "source_sha256": context.source_sha256,
                "candidate_sha256": context.candidate_sha256,
                "source_eof_line": context.plan.source_eof_line,
                "candidate_eof_line": context.plan.candidate_eof_line,
                "verdict": "pass",
                "completed_units": tuple(
                    item.model_dump(mode="json", by_alias=True)
                    for item in audit_slice.coverage_units
                ),
                "reached_assigned_slice_end": True,
                "reached_real_eof": (
                    audit_slice.role == "closure"
                    or any(
                        item.section_id == "eof"
                        and item.audit_pass == AuditPass.COVERAGE
                        for item in audit_slice.coverage_units
                    )
                ),
                "issue_family_sweep_completed": True,
                "issue_family_checked_issue_ids": (),
                "mandatory_evidence_dispositions": (),
                "issues": (),
            }
        )
        _write(
            tmp_path / artifact.findings_path,
            report.model_dump_json(indent=2, by_alias=True) + "\n",
        )

    completion = finalize_assigned_audit_worker(
        intake_store,
        worker_manifest_path=(
            store.root
            / "audit-workers"
            / intake.intake_id
            / "manifest-findings-v3.json"
        ),
        duration_ms=125,
    )

    assert completion.job_id == intake.intake_id
    assert completion.report_path == worker.report_path
    report_path = tmp_path / worker.report_path
    assert report_path.is_file()
    assert '"verdict": "pass"' in report_path.read_text(encoding="utf-8")

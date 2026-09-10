# Copyright 2026
# ruff: noqa: INP001, S101

"""Tests for the resumable reviewed-repair pipeline."""

from __future__ import annotations

import json
import os
import subprocess
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from scripts.ai import pipeline_dispatcher, pipeline_promotion
from scripts.ai.final_shape import (
    require_final_shape_pair,
    write_final_shape_evidence,
)
from scripts.ai.page_format import WARNING
from scripts.ai.pipeline import (
    EventKind,
    FinalReviewInvalidationRecord,
    FinalReviewRecord,
    GateEvidence,
    JobLease,
    LockOwner,
    PipelinePolicy,
    PipelineState,
    PipelineStore,
    PromotionEvidence,
    Provider,
    ProviderResultRecord,
    RepairJob,
    RepairJobSpec,
    ReviewArtifactRecord,
    ReviewOutcome,
)
from scripts.ai.pipeline_adapters import (
    MaterializedReviewManifest,
    TargetedFixArtifact,
    TargetedFixWorkerManifest,
    finalize_targeted_fix_worker,
    ingest_grok_final_review,
    ingest_terra_final_review,
    prepare_targeted_fix_worker,
)
from scripts.ai.pipeline_dispatcher import (
    CompletionEnvelope,
    CompletionKind,
    DispatchStage,
    PipelineDispatcher,
    RejectedCompletionRecord,
)
from scripts.ai.pipeline_promotion import (
    PromotionBatchRunner,
    PromotionTransaction,
    SiteGateResult,
    run_default_site_gates,
)
from scripts.ai.provenance import stamp_translation_model
from scripts.ai.review_contract import (
    AssignedReviewer,
    RepairReadyReview,
    create_repair_issue,
    locate_candidate_span,
    sha256_path,
    sha256_text,
    write_repair_ready_review,
)

if TYPE_CHECKING:
    from pydantic import BaseModel

EXPECTED_ERROR_LINE = 5
EXPECTED_FAILURE_DURATION_MS = 1234
EXPECTED_LOCK_OPEN_ATTEMPTS = 2
PROMOTION_INTERRUPTION_CALL = 2
EXPECTED_SITE_GATE_CALLS_WITH_RETRY = 7
EXPECTED_SITE_GATE_CALLS_WITH_FAILURE = 5
EXPECTED_INVALID_REVIEW_ATTEMPTS = 2
EXPECTED_DISPATCH_CYCLES = 2
TRANSIENT_ATOMIC_FAILURES = 2
EXPECTED_ATOMIC_REPLACE_ATTEMPTS = 3
PILOT_DEEP_AUDIT_PARALLELISM = 6
PILOT_DEEP_AUDIT_LANE_PARALLELISM = 3
PILOT_PROVIDER_PARALLELISM = 2
PILOT_REVIEW_PARALLELISM = 4
PILOT_REVIEW_LANE_PARALLELISM = 2
PILOT_DOWNSTREAM_WIP = 12
PILOT_PROMOTION_BATCH_SIZE = 3
PILOT_PROMOTION_WAIT_SECONDS = 300
CENSUS_DEEP_AUDIT_PARALLELISM = 10
CENSUS_DEEP_AUDIT_LANE_PARALLELISM = 5
CENSUS_REVIEW_ONLY_WIP_LIMIT = 256


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(value, encoding="utf-8", newline="\n")


def _write_model(path: Path, value: BaseModel) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(value.model_dump_json(indent=2) + "\n", encoding="utf-8")


def test_default_policy_matches_quality_first_parallel_pilot() -> None:
    """Defaults reserve deep-audit capacity without overfeeding repairs."""
    policy = PipelinePolicy()

    assert policy.deep_audit_parallelism == PILOT_DEEP_AUDIT_PARALLELISM
    assert (
        policy.deep_audit_terra_parallelism
        == PILOT_DEEP_AUDIT_LANE_PARALLELISM
    )
    assert (
        policy.deep_audit_grok_parallelism
        == PILOT_DEEP_AUDIT_LANE_PARALLELISM
    )
    assert (
        policy.repair_parallelism
        == PILOT_PROVIDER_PARALLELISM
    )
    assert policy.kimi_parallelism == 1
    assert policy.glm_parallelism == 1
    assert (
        policy.review_parallelism
        == PILOT_REVIEW_PARALLELISM
    )
    assert policy.terra_parallelism == PILOT_REVIEW_LANE_PARALLELISM
    assert policy.grok_parallelism == PILOT_REVIEW_LANE_PARALLELISM
    assert policy.downstream_wip_limit == PILOT_DOWNSTREAM_WIP
    assert policy.promotion_batch_size == PILOT_PROMOTION_BATCH_SIZE
    assert (
        policy.promotion_batch_max_wait_seconds
        == PILOT_PROMOTION_WAIT_SECONDS
    )


def test_policy_supports_ten_way_read_only_audit_census() -> None:
    """A separate review-only census may use five lanes per reviewer."""
    policy = PipelinePolicy(
        deep_audit_parallelism=CENSUS_DEEP_AUDIT_PARALLELISM,
        deep_audit_terra_parallelism=CENSUS_DEEP_AUDIT_LANE_PARALLELISM,
        deep_audit_grok_parallelism=CENSUS_DEEP_AUDIT_LANE_PARALLELISM,
        downstream_wip_limit=CENSUS_REVIEW_ONLY_WIP_LIMIT,
    )

    assert (
        policy.deep_audit_parallelism
        == CENSUS_DEEP_AUDIT_PARALLELISM
    )
    assert (
        policy.deep_audit_terra_parallelism
        == CENSUS_DEEP_AUDIT_LANE_PARALLELISM
    )
    assert (
        policy.deep_audit_grok_parallelism
        == CENSUS_DEEP_AUDIT_LANE_PARALLELISM
    )
    assert policy.downstream_wip_limit == CENSUS_REVIEW_ONLY_WIP_LIMIT


def _ready_job(  # noqa: PLR0913
    tmp_path: Path,
    *,
    source_id: str = "codex/example",
    attempt_id: str = "attempt-1",
    provider: Provider = "kimi",
    reviewer: AssignedReviewer = "gpt-5.6-terra",
    source_text: str | None = None,
    candidate_text: str | None = None,
    candidate_span_text: str = "该设置必须保持禁用。",
) -> tuple[PipelineStore, RepairJob, Path]:
    source_path = tmp_path / "content" / source_id / "en.md"
    candidate_path = tmp_path / "content" / source_id / "zh-CN.md"
    source_text = source_text or "# Example\n\nThe setting must remain enabled.\n"
    candidate_text = candidate_text or "# 示例\n\n该设置必须保持禁用。\n"
    _write_text(source_path, source_text)
    _write_text(candidate_path, candidate_text)
    issue = create_repair_issue(
        source_id=source_id,
        source_issue_refs=("initial:0",),
        severity="high",
        category="semantic_reversal",
        location="opening paragraph",
        source_excerpt="The setting must remain enabled.",
        candidate_text=candidate_text,
        candidate_span_text=candidate_span_text,
        explanation="The Chinese candidate reverses enabled and disabled.",
    )
    review = RepairReadyReview(
        source_id=source_id,
        assigned_reviewer=reviewer,
        review_model=reviewer,
        verdict="fail",
        source_path=source_path.relative_to(tmp_path).as_posix(),
        candidate_path=candidate_path.relative_to(tmp_path).as_posix(),
        source_sha256=sha256_path(source_path),
        candidate_sha256=sha256_path(candidate_path),
        source_report_paths=("reviews/original.json",),
        issues=(issue,),
    )
    ready_path = tmp_path / "reviews" / f"{attempt_id}.json"
    write_repair_ready_review(ready_path, review)
    store = PipelineStore(
        tmp_path / "pipeline",
        tmp_path,
        PipelinePolicy(
            repair_parallelism=4,
            kimi_parallelism=2,
            glm_parallelism=2,
            review_parallelism=4,
            terra_parallelism=2,
            grok_parallelism=2,
            review_queue_limit=8,
            lease_seconds=60,
        ),
    )
    spec = RepairJobSpec(
        source_id=source_id,
        source_path=review.source_path,
        candidate_path=review.candidate_path,
        source_sha256=review.source_sha256,
        base_candidate_sha256=review.candidate_sha256,
        review_path=ready_path.relative_to(tmp_path).as_posix(),
        assigned_reviewer=reviewer,
        provider=provider,
        provider_model="k3" if provider == "kimi" else "glm-5.2",
        attempt_id=attempt_id,
    )
    return store, store.create_job(spec, actor="test"), ready_path


def _complete_repair(  # noqa: PLR0913
    tmp_path: Path,
    store: PipelineStore,
    job: RepairJob,
    *,
    worker_id: str = "repair-worker",
    already_claimed: bool = False,
    public_source_text: str = "# Public English\n",
    public_candidate_text: str = "# 公开中文\n",
) -> RepairJob:
    claimed = (
        store.load_job(job.job_id)
        if already_claimed
        else store.claim_repair(job.job_id, worker_id)
    )
    output_path = tmp_path / "outputs" / f"{job.job_id}.md"
    _write_text(
        output_path,
        "\n".join(
            (
                "---",
                "title: 示例",
                f"source_id: {job.source_id}",
                "product: codex",
                "lang: zh-CN",
                "canonical_url: https://example.com/test",
                "owner: OpenAI",
                f"content_sha256: {'0' * 64}",
                f"translation_of: {job.source_id}",
                f"translation_model: {job.provider_model}",
                "ai_translated: true",
                "---",
                "# 示例",
                "",
                "该设置必须保持启用。",
                "",
            )
        ),
    )
    result = ProviderResultRecord(
        job_id=job.job_id,
        source_id=job.source_id,
        provider=job.provider,
        model=job.provider_model,
        output_path=output_path.relative_to(tmp_path).as_posix(),
        output_sha256=sha256_path(output_path),
        replacement_count=1,
        covered_issue_ids=job.issue_ids,
        gates=GateEvidence(
            frontmatter=True,
            fenced_code=True,
            inline_code=True,
            mdx=True,
            links=True,
            lf=True,
            materialized=True,
        ),
        duration_ms=5000,
    )
    result_path = tmp_path / "results" / f"{job.job_id}.json"
    _write_model(result_path, result)
    assert claimed.state == PipelineState.REPAIR_RUNNING
    candidate = store.complete_repair(
        job.job_id,
        worker_id,
        result_path.relative_to(tmp_path).as_posix(),
    )
    public_source_path = tmp_path / "public" / job.source_id / "en.md"
    public_candidate_path = tmp_path / "public" / job.source_id / "zh-CN.md"
    _write_text(public_source_path, public_source_text)
    _write_text(public_candidate_path, public_candidate_text)
    public_source_value = public_source_path.relative_to(tmp_path).as_posix()
    public_candidate_value = public_candidate_path.relative_to(tmp_path).as_posix()
    structure_evidence = require_final_shape_pair(
        job.source_id,
        public_source_path,
        public_candidate_path,
        source_path_value=public_source_value,
        candidate_path_value=public_candidate_value,
    )
    structure_evidence_path = (
        tmp_path / "structure-evidence" / f"{job.job_id}.json"
    )
    write_final_shape_evidence(structure_evidence_path, structure_evidence)
    artifact = ReviewArtifactRecord(
        job_id=job.job_id,
        source_id=job.source_id,
        assigned_reviewer=job.assigned_reviewer,
        translation_model=job.provider_model,
        raw_source_path=job.source_path,
        raw_source_sha256=job.source_sha256,
        raw_candidate_path=_required(candidate.output_path),
        raw_candidate_sha256=_required(candidate.output_sha256),
        review_source_path=public_source_value,
        review_source_sha256=sha256_path(public_source_path),
        review_candidate_path=public_candidate_value,
        review_candidate_sha256=sha256_path(public_candidate_path),
        structure_evidence_path=structure_evidence_path.relative_to(
            tmp_path
        ).as_posix(),
        structure_evidence_sha256=sha256_path(structure_evidence_path),
    )
    artifact_path = tmp_path / "review-artifacts" / f"{job.job_id}.json"
    _write_model(artifact_path, artifact)
    return store.attach_review_artifact(
        job.job_id,
        artifact_path.relative_to(tmp_path).as_posix(),
        actor=worker_id,
    )


def _complete_review(
    tmp_path: Path,
    store: PipelineStore,
    job: RepairJob,
    *,
    verdict: ReviewOutcome = "pass",
    worker_id: str = "review-worker",
) -> RepairJob:
    claimed = store.claim_review(job.job_id, worker_id)
    detailed_path = tmp_path / "detailed-reviews" / f"{job.job_id}.json"
    _write_text(
        detailed_path,
        json.dumps(
            {
                "source_id": job.source_id,
                "verdict": verdict,
                "issues": [] if verdict == "pass" else [{"id": "issue-1"}],
            }
        ),
    )
    review = FinalReviewRecord(
        job_id=job.job_id,
        source_id=job.source_id,
        assigned_reviewer=job.assigned_reviewer,
        review_model=job.assigned_reviewer,
        source_sha256=_required(job.review_source_sha256),
        candidate_sha256=_required(job.review_candidate_sha256),
        verdict=verdict,
        issue_count=0 if verdict == "pass" else 1,
        reached_real_eof=True,
        duration_ms=70000,
        detailed_report_path=detailed_path.relative_to(tmp_path).as_posix(),
        detailed_report_sha256=sha256_path(detailed_path),
        structure_evidence_sha256=_required(job.structure_evidence_sha256),
        review_attempt_id=f"{worker_id}-attempt-1",
        invalid_attempt_count=0,
        reviewed_at=datetime.now(UTC),
    )
    review_path = tmp_path / "final-reviews" / f"{job.job_id}.json"
    _write_model(review_path, review)
    assert claimed.state == PipelineState.REVIEW_RUNNING
    return store.complete_review(
        job.job_id,
        worker_id,
        review_path.relative_to(tmp_path).as_posix(),
    )


def test_prepare_targeted_fix_worker_is_idempotent_and_hash_bound(
    tmp_path: Path,
) -> None:
    """A claimed job yields one replayable manifest and rejects input drift."""
    store, job, _ = _ready_job(tmp_path)
    worker_id = "repair-worker"
    _ = store.claim_repair(job.job_id, worker_id)

    prepared = prepare_targeted_fix_worker(
        store,
        job_id=job.job_id,
        worker_id=worker_id,
    )
    repeated = prepare_targeted_fix_worker(
        store,
        job_id=job.job_id,
        worker_id=worker_id,
    )

    assert repeated == prepared
    manifest_path = tmp_path / prepared.manifest_path
    manifest = TargetedFixWorkerManifest.model_validate_json(
        manifest_path.read_text(encoding="utf-8")
    )
    entry = manifest.entries[0]
    assert entry.pipeline_job_id == job.job_id
    assert entry.provider == job.provider
    assert entry.chinese_path == job.candidate_path
    assert prepared.result_path.endswith(f"/{job.source_id}.json")

    candidate_path = tmp_path / job.candidate_path
    _write_text(candidate_path, candidate_path.read_text(encoding="utf-8") + "\n")
    with pytest.raises(ValueError, match="Chinese candidate hash changed"):
        _ = prepare_targeted_fix_worker(
            store,
            job_id=job.job_id,
            worker_id=worker_id,
        )


def test_finalize_targeted_fix_worker_materializes_and_ingests(
    tmp_path: Path,
) -> None:
    """A provider artifact advances directly to a hash-bound review pair."""
    source_page = "\n".join(
        (
            "---",
            "title: Example",
            "source_id: codex/example",
            "product: codex",
            "lang: en",
            "canonical_url: https://example.com/test",
            "owner: OpenAI",
            f"content_sha256: {'0' * 64}",
            "---",
            "[Official source](https://example.com/test)",
            "",
            "Content owner: OpenAI",
            "",
            "# Example",
            "",
            "The setting must remain enabled.",
            "",
        )
    )
    candidate_page = "\n".join(
        (
            "---",
            "title: Example Chinese",
            "source_id: codex/example",
            "product: codex",
            "lang: zh-CN",
            "canonical_url: https://example.com/test",
            "owner: OpenAI",
            f"content_sha256: {'0' * 64}",
            "translation_of: codex/example",
            "translation_model: k3",
            "ai_translated: true",
            "---",
            WARNING,
            "[Official source](https://example.com/test)",
            "",
            "Content owner: OpenAI",
            "",
            "# Example Chinese",
            "",
            "该设置必须保持禁用。",
            "",
        )
    )
    store, job, _ = _ready_job(
        tmp_path,
        source_text=source_page,
        candidate_text=candidate_page,
    )
    worker_id = "repair-worker"
    _ = store.claim_repair(job.job_id, worker_id)
    output_path = tmp_path / "outputs" / f"{job.job_id}.md"
    repaired_page = "\n".join(
        (
            "---",
            "title: Example Chinese",
            f"source_id: {job.source_id}",
            "product: codex",
            "lang: zh-CN",
            "canonical_url: https://example.com/test",
            "owner: OpenAI",
            f"content_sha256: {'0' * 64}",
            f"translation_of: {job.source_id}",
            "translation_model: k3",
            "ai_translated: true",
            "---",
            WARNING,
            "[Official source](https://example.com/test)",
            "",
            "Content owner: OpenAI",
            "",
            "# Example Chinese",
            "",
            "该设置必须保持启用。",
            "",
        )
    )
    _write_text(output_path, repaired_page)
    artifact = TargetedFixArtifact(
        source_id=job.source_id,
        provider=job.provider,
        model=job.provider_model,
        base_candidate_path=job.candidate_path,
        base_candidate_sha256=job.base_candidate_sha256,
        source_sha256=job.source_sha256,
        review_path=job.review_path,
        assigned_reviewer=job.assigned_reviewer,
        review_integrity_warnings=(),
        issue_count=1,
        covered_issue_ids=job.issue_ids,
        replacement_count=1,
        replacement_contract="span-id-v1",
        output_path=output_path.relative_to(tmp_path).as_posix(),
        output_sha256=sha256_path(output_path),
        cache_hit=False,
        provider_duration_ms=100,
        status="candidate_validated_pending_assigned_review",
    )
    with pytest.raises(ValueError, match="span-id-v1"):
        _ = TargetedFixArtifact.model_validate(
            {
                **artifact.model_dump(mode="python"),
                "replacement_contract": "legacy-old-new-v1",
            }
        )
    artifact_path = tmp_path / "targeted-result.json"
    _write_model(artifact_path, artifact)

    candidate = finalize_targeted_fix_worker(
        store,
        job_id=job.job_id,
        worker_id=worker_id,
        artifact_path_value=artifact_path.relative_to(tmp_path).as_posix(),
    )

    assert candidate.state == PipelineState.REVIEW_QUEUED
    assert candidate.review_source_path is not None
    assert candidate.review_candidate_path is not None
    manifest_path = (
        store.root / "review-pairs" / job.job_id / "manifest.json"
    )
    manifest = MaterializedReviewManifest.model_validate_json(
        manifest_path.read_text(encoding="utf-8")
    )
    assert manifest.entries[0].raw_candidate_path == artifact.output_path


def test_candidate_span_requires_unique_repairable_text() -> None:
    """Exact prose is repairable while frontmatter and executable code are not."""
    candidate = "---\ntitle: Test\n---\n\n错误句子。\n\n```python\n代码句子。\n```\n"
    located = locate_candidate_span(candidate, "错误句子。")
    assert located.line_start == EXPECTED_ERROR_LINE
    with pytest.raises(ValueError, match="frontmatter"):
        _ = locate_candidate_span(candidate, "title: Test")
    with pytest.raises(ValueError, match="fenced code"):
        _ = locate_candidate_span(candidate, "代码句子。")
    with pytest.raises(ValueError, match="occurs 0 times"):
        _ = locate_candidate_span(candidate, "不存在")


def test_translation_model_provenance_is_deterministic_and_narrow() -> None:
    """Provider provenance changes one frontmatter value and no page prose."""
    candidate = (
        "---\n"
        "title: 测试\n"
        "translation_model: glm-5.2\n"
        "ai_translated: true\n"
        "---\n"
        "正文中的 glm-5.2 不应改变。\n"
    )
    stamped = stamp_translation_model(candidate, "k3")
    assert stamped == candidate.replace(
        "translation_model: glm-5.2",
        "translation_model: k3",
        1,
    )
    assert stamp_translation_model(stamped, "k3") == stamped


def test_create_job_is_idempotent_and_records_ordered_events(tmp_path: Path) -> None:
    """Creating the same immutable attempt twice returns one queued job."""
    store, job, ready_path = _ready_job(tmp_path)
    review = RepairReadyReview.model_validate_json(ready_path.read_text(encoding="utf-8"))
    duplicate = store.create_job(
        RepairJobSpec(
            source_id=job.source_id,
            source_path=job.source_path,
            candidate_path=job.candidate_path,
            source_sha256=job.source_sha256,
            base_candidate_sha256=job.base_candidate_sha256,
            review_path=job.review_path,
            assigned_reviewer=job.assigned_reviewer,
            provider=job.provider,
            provider_model=job.provider_model,
            attempt_id=job.attempt_id,
        ),
        actor="test-again",
    )
    assert review.source_id == job.source_id
    assert duplicate == job
    assert job.state == PipelineState.REPAIR_QUEUED
    events = store.events(job.job_id)
    assert [event.sequence for event in events] == [1, 2, 3]
    assert [event.to_state for event in events] == [
        PipelineState.DISCOVERED,
        PipelineState.BRIDGE_VERIFIED,
        PipelineState.REPAIR_QUEUED,
    ]


def test_create_job_resumes_after_interrupted_initial_transition(tmp_path: Path) -> None:
    """An existing bridge event resumes to repair_queued without duplication."""
    store, job, _ = _ready_job(tmp_path)
    event_path = store.events_root / f"{job.job_id}.jsonl"
    event_lines = event_path.read_text(encoding="utf-8").splitlines()
    _write_text(event_path, "\n".join(event_lines[:2]) + "\n")
    (store.jobs_root / f"{job.job_id}.json").unlink()

    resumed = store.create_job(
        RepairJobSpec(
            source_id=job.source_id,
            source_path=job.source_path,
            candidate_path=job.candidate_path,
            source_sha256=job.source_sha256,
            base_candidate_sha256=job.base_candidate_sha256,
            review_path=job.review_path,
            assigned_reviewer=job.assigned_reviewer,
            provider=job.provider,
            provider_model=job.provider_model,
            attempt_id=job.attempt_id,
        ),
        actor="resume-test",
    )

    assert resumed.state == PipelineState.REPAIR_QUEUED
    assert [event.sequence for event in store.events(job.job_id)] == [1, 2, 3]


def test_parallel_attempt_for_same_source_is_rejected(tmp_path: Path) -> None:
    """A source cannot have two active candidates with different attempt ids."""
    store, job, _ = _ready_job(tmp_path)
    with pytest.raises(ValueError, match="active repair attempt"):
        _ = store.create_job(
            RepairJobSpec(
                source_id=job.source_id,
                source_path=job.source_path,
                candidate_path=job.candidate_path,
                source_sha256=job.source_sha256,
                base_candidate_sha256=job.base_candidate_sha256,
                review_path=job.review_path,
                assigned_reviewer=job.assigned_reviewer,
                provider=job.provider,
                provider_model=job.provider_model,
                attempt_id="attempt-2",
            ),
            actor="test",
        )


def test_provider_lane_limit_prevents_one_model_from_consuming_all_slots(
    tmp_path: Path,
) -> None:
    """Two Kimi leases leave the remaining global slots available to GLM."""
    store, first, _ = _ready_job(tmp_path, source_id="codex/kimi-first")
    _, second, _ = _ready_job(
        tmp_path,
        source_id="codex/kimi-second",
        attempt_id="attempt-2",
    )
    _, third, _ = _ready_job(
        tmp_path,
        source_id="codex/kimi-third",
        attempt_id="attempt-3",
    )
    _, glm_job, _ = _ready_job(
        tmp_path,
        source_id="codex/glm-first",
        attempt_id="attempt-4",
        provider="glm",
    )

    _ = store.claim_repair(first.job_id, "kimi-1")
    _ = store.claim_repair(second.job_id, "kimi-2")
    with pytest.raises(ValueError, match="kimi repair concurrency"):
        _ = store.claim_repair(third.job_id, "kimi-3")
    claimed_glm = store.claim_repair(glm_job.job_id, "glm-1")

    assert claimed_glm.state == PipelineState.REPAIR_RUNNING
    assert store.status().repair_running_by_provider == {"kimi": 2, "glm": 1}


def test_reviewer_lane_limit_preserves_mutually_exclusive_capacity(
    tmp_path: Path,
) -> None:
    """A configured reviewer cap applies without changing page assignment."""
    store, first, _ = _ready_job(tmp_path, source_id="codex/terra-first")
    store.policy = PipelinePolicy(
        repair_parallelism=4,
        kimi_parallelism=2,
        glm_parallelism=2,
        review_parallelism=4,
        terra_parallelism=2,
        grok_parallelism=4,
        review_queue_limit=8,
        lease_seconds=60,
    )
    _, second, _ = _ready_job(
        tmp_path,
        source_id="codex/terra-second",
        attempt_id="attempt-2",
        provider="glm",
    )
    _, third, _ = _ready_job(
        tmp_path,
        source_id="codex/terra-third",
        attempt_id="attempt-3",
    )
    first = _complete_repair(tmp_path, store, first)
    second = _complete_repair(tmp_path, store, second)
    third = _complete_repair(tmp_path, store, third)

    _ = store.claim_review(first.job_id, "terra-1")
    _ = store.claim_review(second.job_id, "terra-2")
    with pytest.raises(ValueError, match=r"gpt-5\.6-terra review concurrency"):
        _ = store.claim_review(third.job_id, "terra-3")

    assert store.status().review_running_by_reviewer == {
        "gpt-5.6-terra": 2,
        "grok-4.5": 0,
    }


def test_repair_result_routes_immediately_to_assigned_review(tmp_path: Path) -> None:
    """A materialized provider result enters the bounded assigned-review queue."""
    store, job, _ = _ready_job(tmp_path)
    reviewed = _complete_repair(tmp_path, store, job)
    assert reviewed.state == PipelineState.REVIEW_QUEUED
    assert reviewed.translation_model == "k3"
    assert reviewed.output_sha256 is not None
    assert reviewed.review_candidate_sha256 is not None
    assert reviewed.output_sha256 != reviewed.review_candidate_sha256
    assert store.status().review_queued == 1


def test_final_review_must_use_original_assigned_model(tmp_path: Path) -> None:
    """Cross-model final review cannot advance a repair attempt."""
    store, job, _ = _ready_job(tmp_path)
    queued = _complete_repair(tmp_path, store, job)
    _ = store.claim_review(job.job_id, "review-worker")
    bad = FinalReviewRecord(
        job_id=job.job_id,
        source_id=job.source_id,
        assigned_reviewer="grok-4.5",
        review_model="grok-4.5",
        source_sha256=_required(queued.review_source_sha256),
        candidate_sha256=_required(queued.review_candidate_sha256),
        verdict="pass",
        issue_count=0,
        reached_real_eof=True,
        duration_ms=1000,
    )
    path = tmp_path / "final-reviews" / "cross-model.json"
    _write_model(path, bad)
    with pytest.raises(ValueError, match="assigned repair job"):
        _ = store.complete_review(
            job.job_id,
            "review-worker",
            path.relative_to(tmp_path).as_posix(),
        )


def test_warn_is_isolated_and_pass_is_promotion_ready(tmp_path: Path) -> None:
    """The assigned full-page verdict alone selects promotion or isolation."""
    warn_store, warn_job, _ = _ready_job(
        tmp_path / "warn",
        source_id="codex/warn-page",
    )
    warn_candidate = _complete_repair(tmp_path / "warn", warn_store, warn_job)
    isolated = _complete_review(
        tmp_path / "warn",
        warn_store,
        warn_candidate,
        verdict="warn",
    )
    assert isolated.state == PipelineState.ISOLATED

    pass_store, pass_job, _ = _ready_job(
        tmp_path / "pass",
        source_id="codex/pass-page",
    )
    pass_candidate = _complete_repair(tmp_path / "pass", pass_store, pass_job)
    ready = _complete_review(tmp_path / "pass", pass_store, pass_candidate)
    assert ready.state == PipelineState.PROMOTION_READY


def test_grok_adapter_records_public_hashes_not_raw_candidate_hash(
    tmp_path: Path,
) -> None:
    """The local Grok adapter binds its verdict to final-site-shape bytes."""
    store, job, _ = _ready_job(
        tmp_path,
        source_id="codex/grok-public-review",
        reviewer="grok-4.5",
    )
    queued = _complete_repair(tmp_path, store, job)
    worker_id = "grok-worker"
    _ = store.claim_review(job.job_id, worker_id)
    assert queued.output_sha256 != queued.review_candidate_sha256
    report: dict[str, object] = {
        "source_id": job.source_id,
        "status": "pass",
        "review_model": "grok-4.5",
        "candidate_path": _required(queued.review_candidate_path),
        "candidate_sha256": _required(queued.review_candidate_sha256),
        "source_sha256": _required(queued.review_source_sha256),
        "translation_model": job.provider_model,
        "structure_counts": {
            "source_headings": 1,
            "candidate_headings": 1,
            "source_code_fences": 0,
            "candidate_code_fences": 0,
            "source_links": 0,
            "candidate_links": 0,
        },
        "issues": [],
        "reached_real_eof": True,
        "reviewed_at": datetime.now(UTC).isoformat(),
        "review_method": "manual_semantic_via_local_grok_cli_json_schema",
    }
    status: dict[str, object] = {
        "state": "completed",
        "completed": 1,
        "pass": 1,
        "warn": 0,
        "fail": 0,
        "last_source": job.source_id,
    }
    report_path = tmp_path / "grok" / "report.json"
    status_path = tmp_path / "grok" / "status.json"
    _write_text(report_path, json.dumps(report))
    _write_text(status_path, json.dumps(status))

    ready = ingest_grok_final_review(
        store,
        job_id=job.job_id,
        worker_id=worker_id,
        report_path_value=report_path.relative_to(tmp_path).as_posix(),
        status_path_value=status_path.relative_to(tmp_path).as_posix(),
    )

    assert ready.state == PipelineState.PROMOTION_READY
    assert ready.final_review_path is not None


def test_grok_adapter_rejects_invented_structure_counts(tmp_path: Path) -> None:
    """A shallow report cannot pass by asserting counts contradicted by the files."""
    store, job, _ = _ready_job(
        tmp_path,
        source_id="codex/grok-bad-counts",
        reviewer="grok-4.5",
    )
    queued = _complete_repair(tmp_path, store, job)
    worker_id = "grok-worker"
    _ = store.claim_review(job.job_id, worker_id)
    report: dict[str, object] = {
        "source_id": job.source_id,
        "status": "pass",
        "review_model": "grok-4.5",
        "candidate_path": _required(queued.review_candidate_path),
        "candidate_sha256": _required(queued.review_candidate_sha256),
        "source_sha256": _required(queued.review_source_sha256),
        "translation_model": job.provider_model,
        "structure_counts": {
            "source_headings": 0,
            "candidate_headings": 0,
            "source_code_fences": 0,
            "candidate_code_fences": 0,
            "source_links": 0,
            "candidate_links": 0,
        },
        "issues": [],
        "reached_real_eof": True,
        "reviewed_at": datetime.now(UTC).isoformat(),
        "review_method": "manual_semantic_via_local_grok_cli_json_schema",
    }
    status: dict[str, object] = {
        "state": "completed",
        "completed": 1,
        "pass": 1,
        "warn": 0,
        "fail": 0,
        "last_source": job.source_id,
    }
    report_path = tmp_path / "grok" / "report.json"
    status_path = tmp_path / "grok" / "status.json"
    _write_text(report_path, json.dumps(report))
    _write_text(status_path, json.dumps(status))

    with pytest.raises(ValueError, match="structure counts"):
        _ = ingest_grok_final_review(
            store,
            job_id=job.job_id,
            worker_id=worker_id,
            report_path_value=report_path.relative_to(tmp_path).as_posix(),
            status_path_value=status_path.relative_to(tmp_path).as_posix(),
        )


def test_terra_adapter_binds_detailed_report_and_eof_evidence(
    tmp_path: Path,
) -> None:
    """A Terra verdict is canonical only when its exact detailed report is bound."""
    store, job, _ = _ready_job(
        tmp_path,
        source_id="codex/terra-public-review",
    )
    queued = _complete_repair(tmp_path, store, job)
    worker_id = "terra-worker"
    _ = store.claim_review(job.job_id, worker_id)
    report: dict[str, object] = {
        "source_id": job.source_id,
        "english_path": _required(queued.review_source_path),
        "chinese_path": _required(queued.review_candidate_path),
        "expected_source_sha256": _required(queued.review_source_sha256),
        "actual_source_sha256": _required(queued.review_source_sha256),
        "expected_candidate_sha256": _required(queued.review_candidate_sha256),
        "actual_candidate_sha256": _required(queued.review_candidate_sha256),
        "review_model": "gpt-5.6-terra",
        "verdict": "pass",
        "issues": [],
        "reviewed_at": datetime.now(UTC).isoformat(),
        "eof_verification": {"complete_to_eof": True},
    }
    report_path = tmp_path / "terra" / "report.json"
    _write_text(report_path, json.dumps(report))

    ready = ingest_terra_final_review(
        store,
        job_id=job.job_id,
        worker_id=worker_id,
        report_path_value=report_path.relative_to(tmp_path).as_posix(),
        invalid_attempt_count=1,
    )

    assert ready.state == PipelineState.PROMOTION_READY
    canonical_path = tmp_path / _required(ready.final_review_path)
    canonical = FinalReviewRecord.model_validate_json(
        canonical_path.read_text(encoding="utf-8")
    )
    assert canonical.detailed_report_path == report_path.relative_to(
        tmp_path
    ).as_posix()
    assert canonical.detailed_report_sha256 == sha256_path(report_path)
    assert canonical.invalid_attempt_count == 1


def test_terra_adapter_normalizes_hash_bound_structured_output(
    tmp_path: Path,
) -> None:
    """Structured Terra output is accepted only with complete file evidence."""
    store, job, _ = _ready_job(
        tmp_path,
        source_id="codex/terra-structured-review",
    )
    queued = _complete_repair(tmp_path, store, job)
    worker_id = "terra-structured-worker"
    _ = store.claim_review(job.job_id, worker_id)
    source_path_value = _required(queued.review_source_path)
    candidate_path_value = _required(queued.review_candidate_path)
    source_path = tmp_path / source_path_value
    candidate_path = tmp_path / candidate_path_value
    report: dict[str, object] = {
        "source_id": job.source_id,
        "review_model": "gpt-5.6-terra",
        "status": "completed",
        "verdict": "needs_repair",
        "issue_count": 1,
        "review_scope": {
            "english_path": source_path_value,
            "chinese_path": candidate_path_value,
            "translation_modified": False,
            "sensitive_key_or_proxy_values_recorded": False,
        },
        "inputs": {
            "english": {
                "path": source_path_value,
                "sha256": _required(queued.review_source_sha256),
                "expected_sha256": _required(queued.review_source_sha256),
                "sha256_match": True,
            },
            "chinese": {
                "path": candidate_path_value,
                "sha256": _required(queued.review_candidate_sha256),
                "expected_sha256": _required(queued.review_candidate_sha256),
                "sha256_match": True,
            },
        },
        "issues": [
            {
                "id": "structured-1",
                "category": "semantic_distortion",
                "source_excerpt": "# Public English",
                "chinese_excerpt": "# 公开中文",
                "finding": "meaning changed",
            }
        ],
        "reached_real_eof": True,
        "read_coverage": {
            "english": {
                "first_line_read": 1,
                "last_line_read": len(
                    source_path.read_text(encoding="utf-8").splitlines()
                ),
                "reached_real_eof": True,
            },
            "chinese": {
                "first_line_read": 1,
                "last_line_read": len(
                    candidate_path.read_text(encoding="utf-8").splitlines()
                ),
                "reached_real_eof": True,
            },
        },
    }
    report_path = tmp_path / "terra" / "structured-report.json"
    _write_text(report_path, json.dumps(report))

    isolated = ingest_terra_final_review(
        store,
        job_id=job.job_id,
        worker_id=worker_id,
        report_path_value=report_path.relative_to(tmp_path).as_posix(),
    )

    assert isolated.state == PipelineState.ISOLATED
    canonical_path = tmp_path / _required(isolated.final_review_path)
    canonical = FinalReviewRecord.model_validate_json(
        canonical_path.read_text(encoding="utf-8")
    )
    assert canonical.verdict == "fail"
    assert canonical.detailed_report_sha256 == sha256_path(report_path)


def test_terra_adapter_requeues_a_locally_contradicted_missing_section(
    tmp_path: Path,
) -> None:
    """A false EOF/section claim cannot become a terminal isolation."""
    store, job, _ = _ready_job(
        tmp_path,
        source_id="claude-code/false-missing-section",
    )
    queued = _complete_repair(
        tmp_path,
        store,
        job,
        public_source_text=(
            "# Guide\n\nIntro.\n\n## Next steps\n\nRead the deployment guide.\n"
        ),
        public_candidate_text=(
            "# 指南\n\n简介。\n\n## 后续步骤\n\n请阅读部署指南。\n"
        ),
    )
    worker_id = "terra-false-missing-worker"
    _ = store.claim_review(job.job_id, worker_id)
    report = {
        "source_id": job.source_id,
        "english_path": _required(queued.review_source_path),
        "chinese_path": _required(queued.review_candidate_path),
        "expected_source_sha256": _required(queued.review_source_sha256),
        "actual_source_sha256": _required(queued.review_source_sha256),
        "expected_candidate_sha256": _required(queued.review_candidate_sha256),
        "actual_candidate_sha256": _required(queued.review_candidate_sha256),
        "review_model": "gpt-5.6-terra",
        "verdict": "fail",
        "issues": [
            {
                "severity": "high",
                "category": "missing_translation_content",
                "english_excerpt": (
                    "## Next steps\n\nRead the deployment guide."
                ),
                "chinese_excerpt": "## 后续步骤",
                "explanation": "The entire section is absent.",
            }
        ],
        "reviewed_at": datetime.now(UTC).isoformat(),
        "eof_verification": {"complete_to_eof": True},
    }
    report_path = tmp_path / "terra" / "false-missing.json"
    _write_text(report_path, json.dumps(report))

    retried = ingest_terra_final_review(
        store,
        job_id=job.job_id,
        worker_id=worker_id,
        report_path_value=report_path.relative_to(tmp_path).as_posix(),
    )

    assert retried.state == PipelineState.REVIEW_QUEUED
    assert retried.final_review_path is None
    assert retried.output_sha256 == queued.output_sha256
    invalidations = tuple(store.review_invalidations_root.glob("*.json"))
    assert len(invalidations) == 1
    record = FinalReviewInvalidationRecord.model_validate_json(
        invalidations[0].read_text(encoding="utf-8")
    )
    assert record.evidence_code == "missing_section_claim_contradicted"
    assert store.events(job.job_id)[-1].kind == EventKind.REVIEW_INVALIDATED


def test_second_invalid_final_review_blocks_without_semantic_isolation(
    tmp_path: Path,
) -> None:
    """Two invalid evidence attempts stop safely without rerunning repair."""
    store, job, _ = _ready_job(
        tmp_path,
        source_id="claude-code/repeated-invalid-review",
    )
    queued = _complete_repair(
        tmp_path,
        store,
        job,
        public_source_text="# Guide\n\n## Details\n\nSource body.\n",
        public_candidate_text="# 指南\n\n## 详情\n\n中文正文。\n",
    )

    for attempt in (1, 2):
        worker_id = f"terra-invalid-{attempt}"
        _ = store.claim_review(job.job_id, worker_id)
        report = {
            "source_id": job.source_id,
            "english_path": _required(queued.review_source_path),
            "chinese_path": _required(queued.review_candidate_path),
            "expected_source_sha256": _required(queued.review_source_sha256),
            "actual_source_sha256": _required(queued.review_source_sha256),
            "expected_candidate_sha256": _required(
                queued.review_candidate_sha256
            ),
            "actual_candidate_sha256": _required(
                queued.review_candidate_sha256
            ),
            "review_model": "gpt-5.6-terra",
            "verdict": "fail",
            "issues": [
                {
                    "severity": "high",
                    "category": "missing_translation_content",
                    "english_excerpt": "## Details\n\nSource body.",
                    "chinese_excerpt": "## 详情",
                    "explanation": f"Invalid missing claim attempt {attempt}.",
                }
            ],
            "reviewed_at": datetime.now(UTC).isoformat(),
            "eof_verification": {"complete_to_eof": True},
        }
        report_path = tmp_path / "terra" / f"invalid-{attempt}.json"
        _write_text(report_path, json.dumps(report))
        result = ingest_terra_final_review(
            store,
            job_id=job.job_id,
            worker_id=worker_id,
            report_path_value=report_path.relative_to(tmp_path).as_posix(),
        )

    assert result.state == PipelineState.BLOCKED
    assert result.final_review_path is None
    assert result.output_sha256 == queued.output_sha256
    assert "contract blocked" in _required(result.terminal_reason)
    assert sum(
        event.kind == EventKind.REVIEW_INVALIDATED
        for event in store.events(job.job_id)
    ) == EXPECTED_INVALID_REVIEW_ATTEMPTS


def test_terra_adapter_rejects_structured_output_without_real_eof(
    tmp_path: Path,
) -> None:
    """A structured report cannot claim EOF with a truncated line range."""
    store, job, _ = _ready_job(
        tmp_path,
        source_id="codex/terra-structured-truncated",
    )
    queued = _complete_repair(tmp_path, store, job)
    worker_id = "terra-structured-truncated-worker"
    _ = store.claim_review(job.job_id, worker_id)
    source_path_value = _required(queued.review_source_path)
    candidate_path_value = _required(queued.review_candidate_path)
    report: dict[str, object] = {
        "source_id": job.source_id,
        "review_model": "gpt-5.6-terra",
        "status": "completed",
        "verdict": "needs_repair",
        "issue_count": 1,
        "review_scope": {
            "english_path": source_path_value,
            "chinese_path": candidate_path_value,
            "translation_modified": False,
            "sensitive_key_or_proxy_values_recorded": False,
        },
        "inputs": {
            "english": {
                "path": source_path_value,
                "sha256": _required(queued.review_source_sha256),
                "expected_sha256": _required(queued.review_source_sha256),
                "sha256_match": True,
            },
            "chinese": {
                "path": candidate_path_value,
                "sha256": _required(queued.review_candidate_sha256),
                "expected_sha256": _required(queued.review_candidate_sha256),
                "sha256_match": True,
            },
        },
        "issues": [{"id": "structured-1"}],
        "reached_real_eof": True,
        "read_coverage": {
            "english": {
                "first_line_read": 1,
                "last_line_read": 2,
                "reached_real_eof": True,
            },
            "chinese": {
                "first_line_read": 1,
                "last_line_read": 2,
                "reached_real_eof": True,
            },
        },
    }
    report_path = tmp_path / "terra" / "truncated-report.json"
    _write_text(report_path, json.dumps(report))

    with pytest.raises(ValueError, match="actual EOF line"):
        _ = ingest_terra_final_review(
            store,
            job_id=job.job_id,
            worker_id=worker_id,
            report_path_value=report_path.relative_to(tmp_path).as_posix(),
        )


def test_review_backpressure_holds_validated_candidates(tmp_path: Path) -> None:
    """A full review queue stops repair feed without discarding candidates."""
    root = tmp_path
    first_store, first_job, _ = _ready_job(root, source_id="codex/first")
    first_store.policy = PipelinePolicy(
        repair_parallelism=4,
        kimi_parallelism=2,
        glm_parallelism=2,
        review_parallelism=4,
        terra_parallelism=2,
        grok_parallelism=2,
        review_queue_limit=1,
        lease_seconds=60,
    )
    _, second_job, _ = _ready_job(
        root,
        source_id="codex/second",
        attempt_id="attempt-2",
        provider="glm",
        reviewer="grok-4.5",
    )
    _ = first_store.claim_repair(first_job.job_id, "repair-worker-1")
    _ = first_store.claim_repair(second_job.job_id, "repair-worker-2")
    first = _complete_repair(
        root,
        first_store,
        first_job,
        worker_id="repair-worker-1",
        already_claimed=True,
    )
    second = _complete_repair(
        root,
        first_store,
        second_job,
        worker_id="repair-worker-2",
        already_claimed=True,
    )
    assert first.state == PipelineState.REVIEW_QUEUED
    assert second.state == PipelineState.CANDIDATE_VALIDATED
    isolated = _complete_review(root, first_store, first, verdict="warn")
    assert isolated.state == PipelineState.ISOLATED
    queued = first_store.enqueue_waiting_reviews()
    assert [job.job_id for job in queued] == [second.job_id]


def test_dispatcher_publishes_one_stable_action_and_claims_it_once(
    tmp_path: Path,
) -> None:
    """Repeated reconciles do not duplicate a runnable provider action."""
    store, job, _ = _ready_job(tmp_path)
    dispatcher = PipelineDispatcher(store)

    first = dispatcher.reconcile()
    second = dispatcher.reconcile()

    assert len(first.actions) == 1
    assert second.actions == first.actions
    assert len(tuple(dispatcher.actions_root.glob("*.json"))) == 1
    claim = dispatcher.claim_next(DispatchStage.REPAIR, "kimi", "kimi-worker")
    duplicate = dispatcher.claim_next(
        DispatchStage.REPAIR,
        "kimi",
        "other-worker",
    )
    assert claim.claimed is True
    assert claim.job is not None
    assert claim.job.state == PipelineState.REPAIR_RUNNING
    assert duplicate.claimed is False
    assert store.load_job(job.job_id).state == PipelineState.REPAIR_RUNNING


def test_dispatcher_tolerates_concurrent_action_archive(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A second reconciler treats an already archived action as success."""
    store, job, _ = _ready_job(tmp_path)
    dispatcher = PipelineDispatcher(store)
    snapshot = dispatcher.reconcile()
    action = snapshot.actions[0]
    action_path = dispatcher.actions_root / f"{action.action_id}.json"
    original_archive = PipelineDispatcher._archive  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]

    _ = store.claim_repair(job.job_id, "external-worker")

    def archive_after_competing_claim(
        path: Path,
        root: Path,
        name: str,
    ) -> Path:
        path.unlink(missing_ok=True)
        return original_archive(path, root, name)

    monkeypatch.setattr(
        PipelineDispatcher,
        "_archive",
        staticmethod(archive_after_competing_claim),
    )

    repeated = dispatcher.reconcile()

    assert repeated.actions == ()
    assert not action_path.exists()


def test_dispatcher_auto_ingests_completed_terra_review(tmp_path: Path) -> None:
    """A completed detailed report reaches the ledger without a wave boundary."""
    store, job, _ = _ready_job(
        tmp_path,
        source_id="codex/dispatcher-terra",
    )
    queued = _complete_repair(tmp_path, store, job)
    dispatcher = PipelineDispatcher(store)
    worker_id = "terra-dispatch-worker"
    claim = dispatcher.claim_next(
        DispatchStage.REVIEW,
        "gpt-5.6-terra",
        worker_id,
    )
    assert claim.claimed is True
    report: dict[str, object] = {
        "source_id": job.source_id,
        "english_path": _required(queued.review_source_path),
        "chinese_path": _required(queued.review_candidate_path),
        "expected_source_sha256": _required(queued.review_source_sha256),
        "actual_source_sha256": _required(queued.review_source_sha256),
        "expected_candidate_sha256": _required(queued.review_candidate_sha256),
        "actual_candidate_sha256": _required(queued.review_candidate_sha256),
        "review_model": "gpt-5.6-terra",
        "verdict": "pass",
        "issues": [],
        "reviewed_at": datetime.now(UTC).isoformat(),
        "eof_verification": {"complete_to_eof": True},
    }
    report_path = tmp_path / "terra" / "dispatcher-report.json"
    _write_text(report_path, json.dumps(report))
    envelope = CompletionEnvelope(
        completion_id="terra-dispatcher-review-1",
        kind=CompletionKind.TERRA_REVIEW,
        job_id=job.job_id,
        worker_id=worker_id,
        report_path=report_path.relative_to(tmp_path).as_posix(),
    )
    assert dispatcher.submit_completion(envelope) == envelope
    assert dispatcher.submit_completion(envelope) == envelope

    snapshot = dispatcher.reconcile()
    repeated = dispatcher.reconcile()

    assert snapshot.processed_completion_ids == ("terra-dispatcher-review-1",)
    assert store.load_job(job.job_id).state == PipelineState.PROMOTION_READY
    assert repeated.processed_completion_ids == ()
    assert [action.stage for action in repeated.actions] == [
        DispatchStage.PROMOTION
    ]


def test_dispatcher_fails_closed_after_control_plane_code_changes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A long-lived process cannot consume artifacts under stale schemas."""
    fingerprints = iter(("a" * 64, "b" * 64))
    monkeypatch.setattr(
        pipeline_dispatcher,
        "_dispatcher_code_sha256",
        lambda: next(fingerprints),
    )
    store = PipelineStore(tmp_path / ".ai-local/pipeline-v1", tmp_path)
    dispatcher = PipelineDispatcher(store)

    with pytest.raises(RuntimeError, match="code changed after process startup"):
        _ = dispatcher.reconcile()

    runtime_path = (
        dispatcher.runtime_root / f"{dispatcher.runtime.instance_id}.json"
    )
    assert runtime_path.is_file()
    assert dispatcher.runtime.code_sha256 == "a" * 64


def test_dispatcher_replays_a_post_commit_terra_completion(
    tmp_path: Path,
) -> None:
    """A crash after state commit but before inbox archival remains recoverable."""
    store, job, _ = _ready_job(
        tmp_path,
        source_id="codex/dispatcher-terra-replay",
    )
    queued = _complete_repair(tmp_path, store, job)
    dispatcher = PipelineDispatcher(store)
    worker_id = "terra-dispatch-replay"
    claim = dispatcher.claim_next(
        DispatchStage.REVIEW,
        "gpt-5.6-terra",
        worker_id,
    )
    assert claim.claimed
    report: dict[str, object] = {
        "source_id": job.source_id,
        "english_path": _required(queued.review_source_path),
        "chinese_path": _required(queued.review_candidate_path),
        "expected_source_sha256": _required(queued.review_source_sha256),
        "actual_source_sha256": _required(queued.review_source_sha256),
        "expected_candidate_sha256": _required(queued.review_candidate_sha256),
        "actual_candidate_sha256": _required(queued.review_candidate_sha256),
        "review_model": "gpt-5.6-terra",
        "verdict": "pass",
        "issues": [],
        "reviewed_at": datetime.now(UTC).isoformat(),
        "eof_verification": {"complete_to_eof": True},
    }
    review_path = tmp_path / "terra" / "dispatcher-replay-report.json"
    _write_text(review_path, json.dumps(report))
    envelope = CompletionEnvelope(
        completion_id="terra-dispatcher-replay-1",
        kind=CompletionKind.TERRA_REVIEW,
        job_id=job.job_id,
        worker_id=worker_id,
        report_path=review_path.relative_to(tmp_path).as_posix(),
    )
    _ = dispatcher.submit_completion(envelope)
    first = dispatcher.reconcile()
    assert first.rejected_completion_ids == ()
    assert store.load_job(job.job_id).state == PipelineState.PROMOTION_READY

    processed = (
        dispatcher.processed_root / f"{envelope.completion_id}.json"
    )
    inbox = dispatcher.inbox_root / f"{envelope.completion_id}.json"
    _ = processed.replace(inbox)
    replayed = dispatcher.reconcile()
    assert replayed.processed_completion_ids == (envelope.completion_id,)
    assert replayed.rejected_completion_ids == ()
    assert store.load_job(job.job_id).state == PipelineState.PROMOTION_READY


def test_dispatcher_records_retryable_rejection_evidence(
    tmp_path: Path,
) -> None:
    """A missing external report is diagnosed rather than silently archived."""
    store, job, _ = _ready_job(
        tmp_path,
        source_id="codex/dispatcher-rejection-evidence",
    )
    _ = _complete_repair(tmp_path, store, job)
    dispatcher = PipelineDispatcher(store)
    envelope = CompletionEnvelope(
        completion_id="terra-missing-report-1",
        kind=CompletionKind.TERRA_REVIEW,
        job_id=job.job_id,
        worker_id="terra-missing-report-worker",
        report_path="terra/missing-report.json",
    )
    _ = dispatcher.submit_completion(envelope)

    snapshot = dispatcher.reconcile()

    assert snapshot.rejected_completion_ids == (envelope.completion_id,)
    record_path = next(dispatcher.rejection_records_root.glob("*.json"))
    record = RejectedCompletionRecord.model_validate_json(
        record_path.read_text(encoding="utf-8")
    )
    assert record.completion_id == envelope.completion_id
    assert record.error_type == "FileNotFoundError"
    assert record.retryable is True
    archived = tmp_path / record.archived_envelope_path
    assert record.archived_envelope_sha256 == sha256_path(archived)


def test_promotion_wip_backpressures_new_repairs_and_becomes_due(
    tmp_path: Path,
) -> None:
    """An old or full promotion batch is prioritized before more provider work."""
    store, first, _ = _ready_job(tmp_path, source_id="codex/ready-first")
    store.policy = PipelinePolicy(
        repair_parallelism=4,
        kimi_parallelism=2,
        glm_parallelism=2,
        review_parallelism=4,
        terra_parallelism=2,
        grok_parallelism=2,
        review_queue_limit=8,
        promotion_ready_limit=1,
        promotion_batch_size=1,
        lease_seconds=60,
    )
    ready = _complete_review(
        tmp_path,
        store,
        _complete_repair(tmp_path, store, first),
    )
    _, second, _ = _ready_job(
        tmp_path,
        source_id="codex/blocked-second",
        attempt_id="attempt-2",
        provider="glm",
    )

    status = store.status()
    snapshot = PipelineDispatcher(store).reconcile()

    assert ready.state == PipelineState.PROMOTION_READY
    assert status.downstream_backpressure is True
    assert status.review_backpressure is True
    assert snapshot.promotion_due is True
    with pytest.raises(ValueError, match="backpressure"):
        _ = store.claim_repair(second.job_id, "glm-worker")


def test_dispatcher_run_consumes_due_promotion_signal(
    tmp_path: Path,
) -> None:
    """The continuous reconciler can hand a due batch to its gate runner."""
    store, job, _ = _ready_job(
        tmp_path,
        source_id="codex/dispatcher-auto-promotion",
    )
    store.policy = PipelinePolicy(
        repair_parallelism=4,
        kimi_parallelism=2,
        glm_parallelism=2,
        review_parallelism=4,
        terra_parallelism=2,
        grok_parallelism=2,
        review_queue_limit=8,
        promotion_batch_size=1,
        lease_seconds=60,
    )
    _ = _complete_review(
        tmp_path,
        store,
        _complete_repair(tmp_path, store, job),
    )
    calls: list[str] = []

    snapshot = PipelineDispatcher(store).run(
        max_cycles=1,
        on_promotion_due=lambda: calls.append("due"),
    )

    assert calls == ["due"]
    assert snapshot.promotion_due is True


def test_dispatcher_run_invokes_continuous_admission_before_actions(
    tmp_path: Path,
) -> None:
    """Every dispatcher cycle can safely feed its bounded audit inventory."""
    store = PipelineStore(tmp_path / "pipeline", tmp_path)
    calls: list[str] = []

    _ = PipelineDispatcher(store).run(
        max_cycles=1,
        on_admission_cycle=lambda: calls.append("admit"),
    )

    assert calls == ["admit"]


def test_dispatcher_review_only_audit_skips_intake_routing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A census dispatcher ingests evidence without feeding repair stages."""
    store = PipelineStore(tmp_path / "pipeline", tmp_path)
    dispatcher = PipelineDispatcher(store)
    route_calls: list[str] = []
    monkeypatch.setattr(
        dispatcher.intake,
        "route_completed_audits",
        lambda: route_calls.append("route"),
    )

    _ = dispatcher.run(max_cycles=1, review_only_audit=True)

    assert route_calls == []


def test_dispatcher_review_only_audit_rejects_automation(
    tmp_path: Path,
) -> None:
    """Review-only mode cannot accidentally enable downstream automation."""
    store = PipelineStore(tmp_path / "pipeline", tmp_path)

    with pytest.raises(ValueError, match="cannot admit, bridge, or promote"):
        _ = PipelineDispatcher(store).run(
            max_cycles=1,
            auto_bridge=True,
            review_only_audit=True,
        )


def test_dispatcher_run_isolates_admission_failure_and_keeps_running(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed local controller callback must not kill the durable loop."""
    store = PipelineStore(tmp_path / "pipeline", tmp_path)
    dispatcher = PipelineDispatcher(store)
    calls = 0

    def flaky_admission() -> None:
        nonlocal calls
        calls += 1
        if calls == 1:
            message = "simulated transient controller failure"
            raise PermissionError(message)

    monkeypatch.setattr(pipeline_dispatcher.time, "sleep", lambda _delay: None)

    _ = dispatcher.run(
        max_cycles=2,
        on_admission_cycle=flaky_admission,
    )

    assert calls == EXPECTED_DISPATCH_CYCLES
    records = tuple(dispatcher.automation_failures_root.glob("*.json"))
    assert len(records) == 1
    record = pipeline_dispatcher.DispatcherAutomationFailureRecord.model_validate_json(
        records[0].read_text(encoding="utf-8")
    )
    assert record.stage == "admission"
    assert record.error_type == "PermissionError"
    assert record.retryable is True


def test_dispatcher_atomic_write_retries_transient_windows_lock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Dispatcher-owned records survive a short Windows reader lock."""
    target = tmp_path / "status.json"
    original_replace = Path.replace
    attempts = 0

    def flaky_replace(path: Path, destination: Path) -> Path:
        nonlocal attempts
        if destination == target and attempts < TRANSIENT_ATOMIC_FAILURES:
            attempts += 1
            message = "simulated Windows sharing violation"
            raise PermissionError(message)
        attempts += 1
        return original_replace(path, destination)

    monkeypatch.setattr(Path, "replace", flaky_replace)
    monkeypatch.setattr(pipeline_dispatcher.time, "sleep", lambda _delay: None)

    pipeline_dispatcher._atomic_model(  # noqa: SLF001
        target,
        pipeline_dispatcher.DispatcherRuntimeRecord(
            instance_id="a" * 32,
            process_id=1,
            code_sha256="b" * 64,
            started_at=datetime.now(UTC),
        ),
    )

    assert attempts == EXPECTED_ATOMIC_REPLACE_ATTEMPTS
    assert target.is_file()
    assert not tuple(tmp_path.glob("*.tmp"))


def test_default_site_gates_retry_transient_windows_materialize_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Windows write contention retries only the failing materialize command."""
    outcomes = iter(
        (
            (0, "page tests passed\n"),
            (0, "ruff passed\n"),
            (0, "typecheck passed\n"),
            (0, "biome passed\n"),
            (1, "WRITE_FAILED: AI handbook materialization failed\n"),
            (0, "materialized 10 AI handbook routes\n"),
            (0, "build passed\n"),
        )
    )
    calls: list[tuple[str, ...]] = []
    delays: list[float] = []

    def fake_run(
        command: tuple[str, ...],
        **_kwargs: object,
    ) -> subprocess.CompletedProcess[str]:
        assert _kwargs["encoding"] == "utf-8"
        assert _kwargs["errors"] == "replace"
        calls.append(command)
        return_code, output = next(outcomes)
        return subprocess.CompletedProcess(
            command,
            return_code,
            stdout=output,
        )

    def record_delay(delay: float) -> None:
        delays.append(delay)

    monkeypatch.setattr(pipeline_promotion, "_IS_WINDOWS", True)
    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(time, "sleep", record_delay)

    result = run_default_site_gates(tmp_path, tmp_path / "gates.log")

    assert result.materialization is True
    assert calls[4] == calls[5]
    assert len(calls) == EXPECTED_SITE_GATE_CALLS_WITH_RETRY
    assert delays == [0.25]
    assert "retrying transient Windows materialization write" in (
        tmp_path / "gates.log"
    ).read_text(encoding="utf-8")


def test_default_site_gates_do_not_retry_materialize_validation_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A deterministic content failure remains terminal on Windows."""
    outcomes = iter(
        (
            (0, "page tests passed\n"),
            (0, "ruff passed\n"),
            (0, "typecheck passed\n"),
            (0, "biome passed\n"),
            (1, "VALIDATION_FAILED: AI handbook materialization failed\n"),
        )
    )
    calls: list[tuple[str, ...]] = []

    def fake_run(
        command: tuple[str, ...],
        **_kwargs: object,
    ) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        return_code, output = next(outcomes)
        return subprocess.CompletedProcess(
            command,
            return_code,
            stdout=output,
        )

    monkeypatch.setattr(pipeline_promotion, "_IS_WINDOWS", True)
    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(ValueError, match="materialize failed"):
        _ = run_default_site_gates(tmp_path, tmp_path / "gates.log")

    assert len(calls) == EXPECTED_SITE_GATE_CALLS_WITH_FAILURE


def test_small_batch_promotion_writes_target_after_all_gates(
    tmp_path: Path,
) -> None:
    """A clean reviewed candidate is copied and promoted with one gate result."""
    store, job, _ = _ready_job(
        tmp_path,
        source_id="codex/batch-promotion",
    )
    ready = _complete_review(
        tmp_path,
        store,
        _complete_repair(tmp_path, store, job),
    )

    def green_gates(repo_root: Path, log_path: Path) -> SiteGateResult:
        _write_text(log_path, "all green\n")
        return SiteGateResult(
            page_tests=True,
            typecheck=True,
            lint=True,
            materialization=True,
            build=True,
            routes=True,
            duration_ms=100,
            log_path=log_path.relative_to(repo_root).as_posix(),
        )

    result = PromotionBatchRunner(
        store,
        green_gates,
        lambda _root, _jobs: None,
        lambda _root: None,
    ).run_due(force=True)
    target = (
        tmp_path
        / "source-ai"
        / "content"
        / "zh-CN"
        / "codex"
        / "batch-promotion.md"
    )

    assert result.promoted_job_ids == (job.job_id,)
    assert target.read_bytes() == (
        tmp_path / _required(ready.output_path)
    ).read_bytes()
    assert store.load_job(job.job_id).state == PipelineState.PROMOTED


def test_promotion_gates_renew_other_active_worker_leases(
    tmp_path: Path,
) -> None:
    """A long gate starts by preserving unrelated active external work."""
    store, active, _ = _ready_job(
        tmp_path,
        source_id="codex/active-during-promotion",
    )
    _, promotable, _ = _ready_job(
        tmp_path,
        source_id="codex/promotable-with-active-work",
        attempt_id="second",
    )
    _ = store.claim_repair(active.job_id, "active-worker")
    lease_path = store.leases_root / f"{active.job_id}.json"
    before = JobLease.model_validate_json(
        lease_path.read_text(encoding="utf-8")
    )
    _ = _complete_review(
        tmp_path,
        store,
        _complete_repair(tmp_path, store, promotable),
    )

    def green_gates(repo_root: Path, log_path: Path) -> SiteGateResult:
        renewed = JobLease.model_validate_json(
            lease_path.read_text(encoding="utf-8")
        )
        assert renewed.heartbeat_at > before.heartbeat_at
        assert renewed.expires_at > before.expires_at
        _write_text(log_path, "all green\n")
        return SiteGateResult(
            page_tests=True,
            typecheck=True,
            lint=True,
            materialization=True,
            build=True,
            routes=True,
            duration_ms=100,
            log_path=log_path.relative_to(repo_root).as_posix(),
        )

    result = PromotionBatchRunner(
        store,
        green_gates,
        lambda _root, _jobs: None,
        lambda _root: None,
    ).run_due(force=True)

    assert result.promoted_job_ids == (promotable.job_id,)
    assert store.load_job(active.job_id).state == PipelineState.REPAIR_RUNNING


def test_small_batch_promotion_restores_target_when_gate_fails(
    tmp_path: Path,
) -> None:
    """A failing site gate cannot leave an unpromoted formal page behind."""
    store, job, _ = _ready_job(
        tmp_path,
        source_id="codex/batch-rollback",
    )
    _ = _complete_review(
        tmp_path,
        store,
        _complete_repair(tmp_path, store, job),
    )

    def failed_gates(_repo_root: Path, _log_path: Path) -> SiteGateResult:
        message = "synthetic build failure"
        raise ValueError(message)

    with pytest.raises(ValueError, match="synthetic build failure"):
        _ = PromotionBatchRunner(
            store,
            failed_gates,
            lambda _root, _jobs: None,
            lambda _root: None,
        ).run_due(force=True)

    target = (
        tmp_path
        / "source-ai"
        / "content"
        / "zh-CN"
        / "codex"
        / "batch-rollback.md"
    )
    assert not target.exists()
    assert store.load_job(job.job_id).state == PipelineState.PROMOTION_READY
    transaction_paths = sorted(
        (store.root / "promotion-transactions").glob("*/intent.json")
    )
    assert len(transaction_paths) == 1
    transaction = PromotionTransaction.model_validate_json(
        transaction_paths[0].read_text(encoding="utf-8")
    )
    assert transaction.state == "rolled_back"


def test_promotion_recovery_finishes_partial_ledger_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Passed gates survive a crash while individual jobs enter the ledger."""
    store, first, _ = _ready_job(
        tmp_path,
        source_id="codex/promotion-recovery-first",
    )
    _, second, _ = _ready_job(
        tmp_path,
        source_id="codex/promotion-recovery-second",
        attempt_id="attempt-2",
        provider="glm",
    )
    store.policy = PipelinePolicy(
        repair_parallelism=4,
        kimi_parallelism=2,
        glm_parallelism=2,
        review_parallelism=4,
        terra_parallelism=2,
        grok_parallelism=2,
        review_queue_limit=8,
        promotion_batch_size=2,
        lease_seconds=60,
    )
    first = _complete_review(
        tmp_path,
        store,
        _complete_repair(tmp_path, store, first),
        worker_id="review-first",
    )
    second = _complete_review(
        tmp_path,
        store,
        _complete_repair(tmp_path, store, second),
        worker_id="review-second",
    )

    def green_gates(repo_root: Path, log_path: Path) -> SiteGateResult:
        _write_text(log_path, "all green\n")
        return SiteGateResult(
            page_tests=True,
            typecheck=True,
            lint=True,
            materialization=True,
            build=True,
            routes=True,
            duration_ms=100,
            log_path=log_path.relative_to(repo_root).as_posix(),
        )

    original_promote = store.promote
    promote_calls = 0

    def fail_after_first_promotion(
        job_id: str,
        evidence_path_value: str,
        *,
        actor: str,
    ) -> RepairJob:
        nonlocal promote_calls
        promote_calls += 1
        if promote_calls == PROMOTION_INTERRUPTION_CALL:
            message = "synthetic ledger interruption"
            raise RuntimeError(message)
        return original_promote(
            job_id,
            evidence_path_value,
            actor=actor,
        )

    monkeypatch.setattr(store, "promote", fail_after_first_promotion)
    runner = PromotionBatchRunner(
        store,
        green_gates,
        lambda _root, _jobs: None,
        lambda _root: None,
    )
    with pytest.raises(RuntimeError, match="synthetic ledger interruption"):
        _ = runner.run_due(force=True)

    transaction_path = next(
        (store.root / "promotion-transactions").glob("*/intent.json")
    )
    interrupted = PromotionTransaction.model_validate_json(
        transaction_path.read_text(encoding="utf-8")
    )
    assert interrupted.state == "gates_passed"
    assert store.load_job(first.job_id).state == PipelineState.PROMOTED
    assert store.load_job(second.job_id).state == PipelineState.PROMOTION_READY

    monkeypatch.setattr(store, "promote", original_promote)
    _ = runner.run_due()

    recovered = PromotionTransaction.model_validate_json(
        transaction_path.read_text(encoding="utf-8")
    )
    assert recovered.state == "recorded"
    assert store.load_job(first.job_id).state == PipelineState.PROMOTED
    assert store.load_job(second.job_id).state == PipelineState.PROMOTED


def test_expired_worker_lease_is_requeued(tmp_path: Path) -> None:
    """Crash recovery returns a running job to its original queue."""
    store, job, _ = _ready_job(tmp_path)
    running = store.claim_repair(job.job_id, "worker")
    now = datetime.now(UTC)
    expired = JobLease(
        job_id=job.job_id,
        stage="repair",
        worker_id="worker",
        acquired_at=now - timedelta(minutes=2),
        heartbeat_at=now - timedelta(minutes=1),
        expires_at=now - timedelta(seconds=1),
    )
    _write_model(store.leases_root / f"{job.job_id}.json", expired)
    recovered = store.recover_expired_leases()
    assert running.state == PipelineState.REPAIR_RUNNING
    assert [item.state for item in recovered] == [PipelineState.REPAIR_QUEUED]


def test_live_process_coordination_lock_is_not_reclaimed_by_age(
    tmp_path: Path,
) -> None:
    """A long build lock remains exclusive while its owner process is alive."""
    store = PipelineStore(
        tmp_path / "pipeline",
        tmp_path,
        PipelinePolicy(
            lock_timeout_seconds=0.05,
            stale_lock_seconds=1.1,
        ),
    )
    with store.coordinator_lock("long-site-gate"):
        lock_path = next(store.locks_root.glob("*.lock"))
        stale = lock_path.stat().st_mtime - 10
        os.utime(lock_path, (stale, stale))
        with (
            pytest.raises(TimeoutError, match="timed out waiting"),
            store.coordinator_lock("long-site-gate"),
        ):
            pytest.fail("a live owner lock must not be reclaimed")
        assert lock_path.is_file()
    assert not lock_path.exists()


def test_windows_permission_error_on_existing_lock_is_retried(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Treat Windows sharing violations as lock contention, not a crash."""
    store = PipelineStore(tmp_path / "pipeline", tmp_path)
    key = f"coordinator-{sha256_text('windows-contention')}"
    lock_path = store.locks_root / f"{key}.lock"
    owner = LockOwner(
        token="d" * 32,
        pid=2_147_483_647,
        acquired_at=datetime.now(UTC),
    )
    _write_model(lock_path, owner)
    original_open = os.open
    attempts = 0

    def permission_once(
        path: str | bytes | os.PathLike[str] | os.PathLike[bytes],
        flags: int,
        mode: int = 0o777,
    ) -> int:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise PermissionError
        return original_open(path, flags, mode)

    monkeypatch.setattr(os, "open", permission_once)

    with store.coordinator_lock("windows-contention"):
        assert attempts >= EXPECTED_LOCK_OPEN_ATTEMPTS
    assert not lock_path.exists()


def test_terminal_repair_failure_releases_lease_idempotently(tmp_path: Path) -> None:
    """A non-retryable provider or gate failure cannot remain falsely running."""
    store, job, _ = _ready_job(tmp_path)
    _ = store.claim_repair(job.job_id, "worker")

    failed = store.fail_repair(
        job.job_id,
        "worker",
        reason="inline-code literal gate rejected the candidate",
        retryable=False,
        duration_ms=EXPECTED_FAILURE_DURATION_MS,
    )
    repeated = store.fail_repair(
        job.job_id,
        "worker",
        reason="inline-code literal gate rejected the candidate",
        retryable=False,
        duration_ms=EXPECTED_FAILURE_DURATION_MS,
    )

    assert failed.state == PipelineState.FAILED_TERMINAL
    assert failed.terminal_reason == "inline-code literal gate rejected the candidate"
    assert repeated == failed
    assert not (store.leases_root / f"{job.job_id}.json").exists()
    assert store.events(job.job_id)[-1].duration_ms == EXPECTED_FAILURE_DURATION_MS
    metrics = store.metrics()
    assert metrics.stages["repair_turnaround"].samples == 1
    assert metrics.stages["provider_service"].samples == 1
    assert metrics.counters["provider_failures_terminal"] == 1


def test_retryable_repair_failure_requires_explicit_requeue(tmp_path: Path) -> None:
    """Transient failures stay visible until an actor explicitly approves retry."""
    store, job, _ = _ready_job(tmp_path)
    _ = store.claim_repair(job.job_id, "worker")
    failed = store.fail_repair(
        job.job_id,
        "worker",
        reason="transient provider transport timeout",
        retryable=True,
    )

    assert failed.state == PipelineState.FAILED_RETRYABLE
    assert store.status().repair_running == 0
    requeued = store.requeue_failed_repair(job.job_id, actor="operator")
    repeated = store.requeue_failed_repair(job.job_id, actor="operator")
    assert requeued.state == PipelineState.REPAIR_QUEUED
    assert requeued.terminal_reason is None
    assert repeated == requeued
    metrics = store.metrics()
    assert metrics.counters["provider_failures_retryable"] == 1
    assert metrics.counters["explicit_repair_retries"] == 1


def test_second_retry_generation_can_record_the_same_failure_reason(
    tmp_path: Path,
) -> None:
    """Failure idempotency is scoped to one lease generation, not all history."""
    store, job, _ = _ready_job(tmp_path)
    reason = "transient provider transport timeout"
    first_claim = store.claim_repair(job.job_id, "worker")
    first_lease = JobLease.model_validate_json(
        (store.leases_root / f"{job.job_id}.json").read_text(encoding="utf-8")
    )
    first_failure = store.fail_repair(
        first_claim.job_id,
        "worker",
        reason=reason,
        retryable=True,
    )
    _ = store.requeue_failed_repair(job.job_id, actor="operator")
    second_claim = store.claim_repair(job.job_id, "worker")
    second_lease = JobLease.model_validate_json(
        (store.leases_root / f"{job.job_id}.json").read_text(encoding="utf-8")
    )
    second_failure = store.fail_repair(
        second_claim.job_id,
        "worker",
        reason=reason,
        retryable=True,
    )

    assert first_lease.lease_id != second_lease.lease_id
    assert second_failure.last_sequence > first_failure.last_sequence
    assert not (store.leases_root / f"{job.job_id}.json").exists()
    expected_failure_count = 2
    assert (
        store.metrics().counters["provider_failures_retryable"]
        == expected_failure_count
    )


def test_dispatcher_absorbs_repair_failure_completion_once(tmp_path: Path) -> None:
    """Workers can report a failed gate through the same idempotent inbox."""
    store, job, _ = _ready_job(tmp_path)
    dispatcher = PipelineDispatcher(store)
    claim = dispatcher.claim_next(DispatchStage.REPAIR, "kimi", "kimi-worker")
    assert claim.claimed
    envelope = CompletionEnvelope(
        completion_id="repair-failure-1",
        kind=CompletionKind.REPAIR_FAILURE,
        job_id=job.job_id,
        worker_id="kimi-worker",
        failure_reason="candidate failed the inline-code invariant",
        retryable=False,
    )
    assert dispatcher.submit_completion(envelope) == envelope
    assert dispatcher.submit_completion(envelope) == envelope

    snapshot = dispatcher.reconcile()
    repeated = dispatcher.reconcile()
    failed = store.load_job(job.job_id)
    assert snapshot.processed_completion_ids == ("repair-failure-1",)
    assert repeated.processed_completion_ids == ()
    assert failed.state == PipelineState.FAILED_TERMINAL
    assert not (store.leases_root / f"{job.job_id}.json").exists()


def test_event_ledger_repairs_missing_snapshot(tmp_path: Path) -> None:
    """The latest immutable event reconstructs a lost materialized job view."""
    store, job, _ = _ready_job(tmp_path)
    snapshot = store.jobs_root / f"{job.job_id}.json"
    snapshot.unlink()
    restored = store.load_job(job.job_id)
    assert restored == job
    assert snapshot.is_file()


def test_promotion_requires_clean_review_and_green_site_gates(tmp_path: Path) -> None:
    """Promotion records the reviewed hash only after all final gates pass."""
    store, job, _ = _ready_job(tmp_path)
    candidate = _complete_repair(tmp_path, store, job)
    ready = _complete_review(tmp_path, store, candidate)
    evidence = PromotionEvidence(
        job_id=job.job_id,
        source_id=job.source_id,
        target_path=_required(ready.output_path),
        target_sha256=_required(ready.output_sha256),
        page_tests=True,
        typecheck=True,
        lint=True,
        materialization=True,
        build=True,
        routes=True,
    )
    evidence_path = tmp_path / "promotion" / f"{job.job_id}.json"
    _write_model(evidence_path, evidence)
    promoted = store.promote(
        job.job_id,
        evidence_path.relative_to(tmp_path).as_posix(),
        actor="promotion-worker",
    )
    assert promoted.state == PipelineState.PROMOTED
    assert store.events(job.job_id)[-1].to_state == PipelineState.PROMOTED
    metrics = store.metrics()
    assert metrics.stages["repair_turnaround"].samples == 1
    assert metrics.stages["provider_service"].samples == 1
    assert metrics.stages["candidate_to_artifact"].samples == 1
    assert metrics.stages["review_turnaround"].samples == 1
    assert metrics.stages["review_model_service"].samples == 1
    assert metrics.stages["report_ingestion_wait"].samples == 1
    assert metrics.stages["promotion_gate_wait"].samples == 1
    assert metrics.stages["end_to_end"].samples == 1
    assert metrics.counters["clean_reviews"] == 1
    assert metrics.counters["promoted"] == 1


def _required(value: str | None) -> str:
    if value is None:
        message = "test expected populated pipeline provenance"
        raise AssertionError(message)
    return value

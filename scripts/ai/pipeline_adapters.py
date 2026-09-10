# Copyright 2026

"""Validated adapters from legacy local runners into canonical pipeline records."""

from __future__ import annotations

import datetime as dt
import re
import time
import uuid
from datetime import UTC
from typing import TYPE_CHECKING, ClassVar, Final, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from scripts.ai.final_review_evidence import (
    FinalReviewEvidenceError,
    validate_final_review_issue_evidence,
)
from scripts.ai.final_shape import (
    require_final_shape_pair,
    write_final_shape_evidence,
)
from scripts.ai.materialize import derive_review_pair
from scripts.ai.page_format import parse_accepted_page
from scripts.ai.pipeline import (
    FinalReviewInvalidationRecord,
    FinalReviewRecord,
    GateEvidence,
    PipelineState,
    PipelineStore,
    Provider,
    ProviderModel,
    ProviderResultRecord,
    RepairJob,
    ReviewArtifactRecord,
)
from scripts.ai.review_contract import (
    AssignedReviewer,
    resolve_repo_path,
    sha256_path,
    sha256_text,
)
from scripts.ai.types import SourceId

if TYPE_CHECKING:
    from pathlib import Path

_ATOMIC_REPLACE_ATTEMPTS: Final = 8
_HEADING_RE: Final = re.compile(r"^[ \t]*(?:>[ \t]*)*#{1,6}[ \t]+")
_FENCE_RE: Final = re.compile(r"^[ \t]*(`{3,}|~{3,})")
_LINK_RE: Final = re.compile(r"!?\[[^\]\n]*\]\([^)\r\n]*\)")


class _AdapterModel(BaseModel):
    """Strict base for local adapter inputs."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="allow",
        frozen=True,
        str_strip_whitespace=True,
    )


class TargetedFixArtifact(_AdapterModel):
    """Required evidence emitted by the existing targeted repair runner."""

    source_id: str = Field(min_length=1)
    provider: Provider
    model: ProviderModel
    base_candidate_path: str = Field(min_length=1)
    base_candidate_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    review_path: str = Field(min_length=1)
    assigned_reviewer: AssignedReviewer
    review_integrity_warnings: tuple[str, ...]
    issue_count: int = Field(ge=1)
    covered_issue_ids: tuple[str, ...] = Field(min_length=1)
    replacement_count: int = Field(ge=1)
    replacement_contract: Literal["span-id-v1"]
    output_path: str = Field(min_length=1)
    output_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    cache_hit: bool
    provider_duration_ms: int = Field(ge=0)
    status: Literal["candidate_validated_pending_assigned_review"]

    @model_validator(mode="after")
    def _artifact_is_complete(self) -> Self:
        if self.review_integrity_warnings:
            message = "targeted fix has review integrity warnings"
            raise ValueError(message)
        if len(self.covered_issue_ids) != len(set(self.covered_issue_ids)):
            message = "targeted fix issue ids are not unique"
            raise ValueError(message)
        return self


class TargetedFixWorkerEntry(_AdapterModel):
    """One deterministic legacy-runner entry derived from a canonical job."""

    source_id: str = Field(min_length=1)
    pipeline_job_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    provider: Provider
    model: ProviderModel
    assigned_reviewer: AssignedReviewer
    english_path: str = Field(min_length=1)
    chinese_path: str = Field(min_length=1)
    review_path: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    candidate_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    output_root: str = Field(min_length=1)
    result_tag: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{0,127}$")
    strict_candidate_spans: Literal[True] = True
    replacement_contract: Literal["span-id-v1"] = "span-id-v1"
    stamp_provider_model: Literal[True] = True


class TargetedFixWorkerManifest(_AdapterModel):
    """Single-page manifest consumed by the existing targeted repair runner."""

    version: Literal[1] = 1
    purpose: Literal["canonical-pipeline-targeted-repair"] = (
        "canonical-pipeline-targeted-repair"
    )
    policy: Literal["exact-frozen-spans-single-assigned-reviewer"] = (
        "exact-frozen-spans-single-assigned-reviewer"
    )
    entries: tuple[TargetedFixWorkerEntry, ...] = Field(
        min_length=1,
        max_length=1,
    )


class PreparedTargetedFixWorker(_AdapterModel):
    """Paths and hashes needed to execute and ingest one targeted repair."""

    version: Literal[1] = 1
    job_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_id: str = Field(min_length=1)
    provider: Provider
    model: ProviderModel
    manifest_path: str = Field(min_length=1)
    manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    output_path: str = Field(min_length=1)
    result_path: str = Field(min_length=1)


class MaterializedReviewEntry(_AdapterModel):
    """One final-site-shape pair derived from a repaired raw candidate."""

    source_id: str = Field(min_length=1)
    status: Literal["prepared"]
    english_path: str = Field(min_length=1)
    chinese_path: str = Field(min_length=1)
    raw_source_path: str = Field(min_length=1)
    raw_candidate_path: str = Field(min_length=1)
    raw_source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    raw_candidate_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    candidate_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    translation_model: ProviderModel
    assigned_reviewer: AssignedReviewer


class MaterializedReviewManifest(_AdapterModel):
    """A single-page materialization manifest from prepare-fixed-review."""

    version: Literal[1] = 1
    entries: tuple[MaterializedReviewEntry, ...] = Field(min_length=1, max_length=1)


class PreparedMaterializedReview(_AdapterModel):
    """Paths and hashes created before ingesting one targeted repair."""

    version: Literal[1] = 1
    job_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_id: str = Field(min_length=1)
    manifest_path: str = Field(min_length=1)
    manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    english_path: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    chinese_path: str = Field(min_length=1)
    candidate_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class GrokStructureCounts(_AdapterModel):
    """Machine-checkable Markdown counts asserted by a Grok review."""

    source_headings: int = Field(ge=0)
    candidate_headings: int = Field(ge=0)
    source_code_fences: int = Field(ge=0)
    candidate_code_fences: int = Field(ge=0)
    source_links: int = Field(ge=0)
    candidate_links: int = Field(ge=0)


class GrokReviewArtifact(_AdapterModel):
    """Required evidence emitted by the local Grok full-page audit runner."""

    source_id: str = Field(min_length=1)
    status: Literal["pass", "warn", "fail"]
    review_model: Literal["grok-4.5"]
    candidate_path: str = Field(min_length=1)
    candidate_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    translation_model: ProviderModel
    structure_counts: GrokStructureCounts
    issues: tuple[dict[str, object], ...]
    reached_real_eof: Literal[True]
    reviewed_at: dt.datetime
    review_method: Literal["manual_semantic_via_local_grok_cli_json_schema"]

    @model_validator(mode="after")
    def _verdict_matches_issues(self) -> Self:
        if self.status == "pass" and self.issues:
            message = "passing Grok review contains issues"
            raise ValueError(message)
        if self.status != "pass" and not self.issues:
            message = "non-passing Grok review has no issues"
            raise ValueError(message)
        return self


class GrokRunnerStatus(_AdapterModel):
    """Successful terminal status from one local Grok audit process."""

    state: Literal["completed"]
    completed: Literal[1]
    pass_count: int = Field(alias="pass", ge=0, le=1)
    warn_count: int = Field(alias="warn", ge=0, le=1)
    fail_count: int = Field(alias="fail", ge=0, le=1)
    last_source: str = Field(min_length=1)

    @model_validator(mode="after")
    def _has_one_verdict(self) -> Self:
        if self.pass_count + self.warn_count + self.fail_count != 1:
            message = "Grok runner status does not contain exactly one verdict"
            raise ValueError(message)
        return self


class TerraEofVerification(_AdapterModel):
    """Proof that a Terra review read the complete source and candidate."""

    complete_to_eof: Literal[True]


class TerraReviewArtifact(_AdapterModel):
    """Required evidence emitted by an assigned Terra full-page reviewer."""

    source_id: str = Field(min_length=1)
    english_path: str = Field(min_length=1)
    chinese_path: str = Field(min_length=1)
    expected_source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    actual_source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    expected_candidate_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    actual_candidate_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    review_model: Literal["gpt-5.6-terra"]
    verdict: Literal["pass", "warn", "fail"]
    issues: tuple[dict[str, object], ...]
    reviewed_at: dt.datetime
    eof_verification: TerraEofVerification

    @model_validator(mode="after")
    def _verdict_matches_issues(self) -> Self:
        if self.verdict == "pass" and self.issues:
            message = "passing Terra review contains issues"
            raise ValueError(message)
        if self.verdict != "pass" and not self.issues:
            message = "non-passing Terra review has no issues"
            raise ValueError(message)
        return self


class TerraStructuredInput(_AdapterModel):
    """One hash-bound input from the structured Terra sidecar format."""

    path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    expected_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    sha256_match: Literal[True]


class TerraStructuredInputs(_AdapterModel):
    """English and Chinese evidence from a structured Terra report."""

    english: TerraStructuredInput
    chinese: TerraStructuredInput


class TerraStructuredScope(_AdapterModel):
    """Read-only file scope recorded by a structured Terra report."""

    english_path: str = Field(min_length=1)
    chinese_path: str = Field(min_length=1)
    translation_modified: Literal[False]
    sensitive_key_or_proxy_values_recorded: Literal[False]


class TerraStructuredCoverageItem(_AdapterModel):
    """Proof that a structured Terra review reached one file's real EOF."""

    first_line_read: Literal[1]
    last_line_read: int = Field(ge=1)
    reached_real_eof: Literal[True]


class TerraStructuredCoverage(_AdapterModel):
    """EOF coverage for both files in a structured Terra report."""

    english: TerraStructuredCoverageItem
    chinese: TerraStructuredCoverageItem


class TerraStructuredReviewArtifact(_AdapterModel):
    """Alternative Terra output accepted through strict normalization."""

    source_id: str = Field(min_length=1)
    review_model: Literal["gpt-5.6-terra"]
    status: Literal["completed"]
    verdict: Literal["needs_repair"]
    issue_count: int = Field(ge=1)
    review_scope: TerraStructuredScope
    inputs: TerraStructuredInputs
    issues: tuple[dict[str, object], ...] = Field(min_length=1)
    reached_real_eof: Literal[True]
    read_coverage: TerraStructuredCoverage

    @model_validator(mode="after")
    def _issue_count_matches(self) -> Self:
        if self.issue_count != len(self.issues):
            message = "structured Terra report issue count is inconsistent"
            raise ValueError(message)
        return self


def prepare_targeted_fix_worker(
    store: PipelineStore,
    *,
    job_id: str,
    worker_id: str,
) -> PreparedTargetedFixWorker:
    """Write an idempotent targeted-runner manifest for the active repair lease."""
    job = store.load_job(job_id)
    if job.state != PipelineState.REPAIR_RUNNING:
        message = "targeted repair worker requires a running canonical job"
        raise ValueError(message)
    _ = store.heartbeat(job_id, worker_id)
    immutable_inputs = (
        (job.source_path, job.source_sha256, "English source"),
        (job.candidate_path, job.base_candidate_sha256, "Chinese candidate"),
        (job.review_path, job.review_sha256, "repair review"),
    )
    for path_value, expected_sha256, label in immutable_inputs:
        path = resolve_repo_path(store.repo_root, path_value)
        if sha256_path(path) != expected_sha256:
            message = f"{label} hash changed before targeted repair"
            raise ValueError(message)

    worker_root = store.root / "worker-output" / job.job_id / "zh-CN"
    manifest_path = store.root / "worker-manifests" / f"{job.job_id}.json"
    result_tag = f"pipeline-v1-{job.job_id}"
    manifest = TargetedFixWorkerManifest(
        entries=(
            TargetedFixWorkerEntry(
                source_id=job.source_id,
                pipeline_job_id=job.job_id,
                provider=job.provider,
                model=job.provider_model,
                assigned_reviewer=job.assigned_reviewer,
                english_path=job.source_path,
                chinese_path=job.candidate_path,
                review_path=job.review_path,
                source_sha256=job.source_sha256,
                candidate_sha256=job.base_candidate_sha256,
                output_root=worker_root.relative_to(store.repo_root).as_posix(),
                result_tag=result_tag,
            ),
        ),
    )
    if manifest_path.exists():
        existing = TargetedFixWorkerManifest.model_validate_json(
            manifest_path.read_text(encoding="utf-8-sig")
        )
        if existing != manifest:
            message = "existing targeted repair worker manifest differs from the job"
            raise ValueError(message)
    else:
        _atomic_model(manifest_path, manifest)

    manifest_path_value = manifest_path.relative_to(store.repo_root).as_posix()
    output_path = worker_root / f"{job.source_id}.md"
    result_path = (
        store.repo_root
        / ".ai-local"
        / "targeted-fix-results"
        / result_tag
        / f"{job.source_id}.json"
    )
    return PreparedTargetedFixWorker(
        job_id=job.job_id,
        source_id=job.source_id,
        provider=job.provider,
        model=job.provider_model,
        manifest_path=manifest_path_value,
        manifest_sha256=sha256_path(manifest_path),
        output_path=output_path.relative_to(store.repo_root).as_posix(),
        result_path=result_path.relative_to(store.repo_root).as_posix(),
    )


def ingest_targeted_fix(
    store: PipelineStore,
    *,
    job_id: str,
    worker_id: str,
    artifact_path_value: str,
    materialized_manifest_path_value: str,
) -> RepairJob:
    """Validate a legacy repair artifact and complete its canonical repair stage."""
    job = store.load_job(job_id)
    artifact_path = resolve_repo_path(store.repo_root, artifact_path_value)
    artifact = TargetedFixArtifact.model_validate_json(
        artifact_path.read_text(encoding="utf-8-sig")
    )
    materialized_path = resolve_repo_path(
        store.repo_root,
        materialized_manifest_path_value,
    )
    materialized = MaterializedReviewManifest.model_validate_json(
        materialized_path.read_text(encoding="utf-8-sig")
    ).entries[0]
    _validate_artifact(job, artifact, materialized, store.repo_root)
    canonical = ProviderResultRecord(
        job_id=job.job_id,
        source_id=job.source_id,
        provider=artifact.provider,
        model=artifact.model,
        output_path=artifact.output_path,
        output_sha256=artifact.output_sha256,
        replacement_count=artifact.replacement_count,
        covered_issue_ids=artifact.covered_issue_ids,
        gates=GateEvidence(
            frontmatter=True,
            fenced_code=True,
            inline_code=True,
            mdx=True,
            links=True,
            lf=True,
            materialized=True,
        ),
        duration_ms=artifact.provider_duration_ms,
        cache_hit=artifact.cache_hit,
    )
    result_path = store.root / "results" / f"{job.job_id}.json"
    _atomic_model(result_path, canonical)
    result_path_value = result_path.relative_to(store.repo_root).as_posix()
    _ = store.complete_repair(job.job_id, worker_id, result_path_value)
    return attach_materialized_review(
        store,
        job_id=job.job_id,
        materialized_manifest_path_value=materialized_manifest_path_value,
        actor=worker_id,
    )


def prepare_materialized_repair_review(
    store: PipelineStore,
    *,
    job_id: str,
    worker_id: str,
    artifact_path_value: str,
) -> PreparedMaterializedReview:
    """Derive one exact public pair from a completed targeted-fix artifact."""
    job = store.load_job(job_id)
    if job.state != PipelineState.REPAIR_RUNNING:
        message = "targeted repair must be running before materialization"
        raise ValueError(message)
    _ = store.heartbeat(job_id, worker_id)

    artifact_path = resolve_repo_path(store.repo_root, artifact_path_value)
    artifact = TargetedFixArtifact.model_validate_json(
        artifact_path.read_text(encoding="utf-8-sig")
    )
    expected = (
        job.source_id,
        job.provider,
        job.provider_model,
        job.base_candidate_sha256,
        job.source_sha256,
        job.review_path,
        job.assigned_reviewer,
        set(job.issue_ids),
    )
    actual = (
        artifact.source_id,
        artifact.provider,
        artifact.model,
        artifact.base_candidate_sha256,
        artifact.source_sha256,
        artifact.review_path,
        artifact.assigned_reviewer,
        set(artifact.covered_issue_ids),
    )
    if expected != actual:
        message = "targeted fix artifact does not match the canonical job"
        raise ValueError(message)

    raw_source_path = resolve_repo_path(store.repo_root, job.source_path)
    raw_candidate_path = resolve_repo_path(store.repo_root, artifact.output_path)
    if sha256_path(raw_source_path) != job.source_sha256:
        message = "targeted repair source hash changed before materialization"
        raise ValueError(message)
    if sha256_path(raw_candidate_path) != artifact.output_sha256:
        message = "targeted fix output hash changed before materialization"
        raise ValueError(message)
    if parse_accepted_page(raw_candidate_path).translation_model != artifact.model:
        message = "targeted fix output has incorrect translation provenance"
        raise ValueError(message)

    english_data, chinese_data = derive_review_pair(
        SourceId(job.source_id),
        raw_source_path.read_bytes(),
        raw_candidate_path.read_bytes(),
    )
    pair_root = store.root / "review-pairs" / job.job_id / job.source_id
    english_path = pair_root / "en.md"
    chinese_path = pair_root / "zh-CN.md"
    _atomic_bytes(english_path, english_data)
    _atomic_bytes(chinese_path, chinese_data)
    english_path_value = english_path.relative_to(store.repo_root).as_posix()
    chinese_path_value = chinese_path.relative_to(store.repo_root).as_posix()
    _ = require_final_shape_pair(
        job.source_id,
        english_path,
        chinese_path,
        source_path_value=english_path_value,
        candidate_path_value=chinese_path_value,
    )
    entry = MaterializedReviewEntry(
        source_id=job.source_id,
        status="prepared",
        english_path=english_path_value,
        chinese_path=chinese_path_value,
        raw_source_path=job.source_path,
        raw_candidate_path=artifact.output_path,
        raw_source_sha256=job.source_sha256,
        raw_candidate_sha256=artifact.output_sha256,
        source_sha256=sha256_path(english_path),
        candidate_sha256=sha256_path(chinese_path),
        translation_model=artifact.model,
        assigned_reviewer=job.assigned_reviewer,
    )
    manifest = MaterializedReviewManifest(entries=(entry,))
    manifest_path = store.root / "review-pairs" / job.job_id / "manifest.json"
    if manifest_path.is_file():
        existing = MaterializedReviewManifest.model_validate_json(
            manifest_path.read_text(encoding="utf-8-sig")
        )
        if existing != manifest:
            message = "existing materialized review manifest differs from repair"
            raise ValueError(message)
    else:
        _atomic_model(manifest_path, manifest)
    return PreparedMaterializedReview(
        job_id=job.job_id,
        source_id=job.source_id,
        manifest_path=manifest_path.relative_to(store.repo_root).as_posix(),
        manifest_sha256=sha256_path(manifest_path),
        english_path=english_path_value,
        source_sha256=entry.source_sha256,
        chinese_path=chinese_path_value,
        candidate_sha256=entry.candidate_sha256,
    )


def finalize_targeted_fix_worker(
    store: PipelineStore,
    *,
    job_id: str,
    worker_id: str,
    artifact_path_value: str,
) -> RepairJob:
    """Materialize, validate, and ingest one completed targeted repair."""
    prepared = prepare_materialized_repair_review(
        store,
        job_id=job_id,
        worker_id=worker_id,
        artifact_path_value=artifact_path_value,
    )
    return ingest_targeted_fix(
        store,
        job_id=job_id,
        worker_id=worker_id,
        artifact_path_value=artifact_path_value,
        materialized_manifest_path_value=prepared.manifest_path,
    )


def attach_materialized_review(
    store: PipelineStore,
    *,
    job_id: str,
    materialized_manifest_path_value: str,
    actor: str,
) -> RepairJob:
    """Convert a verified materialization manifest into canonical review provenance."""
    job = store.load_job(job_id)
    materialized_path = resolve_repo_path(
        store.repo_root,
        materialized_manifest_path_value,
    )
    materialized = MaterializedReviewManifest.model_validate_json(
        materialized_path.read_text(encoding="utf-8-sig")
    ).entries[0]
    _validate_materialized_review(job, materialized, store.repo_root)
    source_path = resolve_repo_path(store.repo_root, materialized.english_path)
    candidate_path = resolve_repo_path(store.repo_root, materialized.chinese_path)
    structure_evidence = require_final_shape_pair(
        job.source_id,
        source_path,
        candidate_path,
        source_path_value=materialized.english_path,
        candidate_path_value=materialized.chinese_path,
    )
    structure_evidence_path = (
        store.root / "structure-evidence" / f"{job.job_id}.json"
    )
    write_final_shape_evidence(structure_evidence_path, structure_evidence)
    structure_evidence_path_value = structure_evidence_path.relative_to(
        store.repo_root
    ).as_posix()
    artifact = ReviewArtifactRecord(
        job_id=job.job_id,
        source_id=job.source_id,
        assigned_reviewer=job.assigned_reviewer,
        translation_model=job.provider_model,
        raw_source_path=materialized.raw_source_path,
        raw_source_sha256=materialized.raw_source_sha256,
        raw_candidate_path=materialized.raw_candidate_path,
        raw_candidate_sha256=materialized.raw_candidate_sha256,
        review_source_path=materialized.english_path,
        review_source_sha256=materialized.source_sha256,
        review_candidate_path=materialized.chinese_path,
        review_candidate_sha256=materialized.candidate_sha256,
        structure_evidence_path=structure_evidence_path_value,
        structure_evidence_sha256=sha256_path(structure_evidence_path),
    )
    artifact_path = store.root / "review-artifacts" / f"{job.job_id}.json"
    _atomic_model(artifact_path, artifact)
    return store.attach_review_artifact(
        job.job_id,
        artifact_path.relative_to(store.repo_root).as_posix(),
        actor=actor,
    )


def ingest_grok_final_review(
    store: PipelineStore,
    *,
    job_id: str,
    worker_id: str,
    report_path_value: str,
    status_path_value: str,
) -> RepairJob:
    """Validate one assigned Grok report and complete its canonical review lease."""
    job = store.load_job(job_id)
    if job.assigned_reviewer != "grok-4.5":
        message = "Grok report cannot complete a Terra-assigned job"
        raise ValueError(message)
    report_path = resolve_repo_path(store.repo_root, report_path_value)
    report = GrokReviewArtifact.model_validate_json(
        report_path.read_text(encoding="utf-8-sig")
    )
    status_path = resolve_repo_path(store.repo_root, status_path_value)
    status = GrokRunnerStatus.model_validate_json(
        status_path.read_text(encoding="utf-8-sig")
    )
    _validate_grok_review(job, report, status, store.repo_root)
    report_sha256 = sha256_path(report_path)
    invalidated = _invalidate_unproven_final_review(
        store,
        job=job,
        worker_id=worker_id,
        report_path_value=report_path_value,
        report_sha256=report_sha256,
        issues=report.issues,
    )
    if invalidated is not None:
        return invalidated
    replay_path = _existing_final_review_replay_path(
        store,
        job,
        report_path_value=report_path_value,
        report_sha256=report_sha256,
    )
    if replay_path is not None:
        return store.complete_review(
            job.job_id,
            worker_id,
            replay_path,
        )
    duration_ms = max(
        0,
        round((report.reviewed_at - job.updated_at).total_seconds() * 1000),
    )
    canonical = FinalReviewRecord(
        job_id=job.job_id,
        source_id=job.source_id,
        assigned_reviewer=job.assigned_reviewer,
        review_model=report.review_model,
        source_sha256=_required(job.review_source_sha256),
        candidate_sha256=_required(job.review_candidate_sha256),
        verdict=report.status,
        issue_count=len(report.issues),
        reached_real_eof=True,
        duration_ms=duration_ms,
        detailed_report_path=report_path_value,
        detailed_report_sha256=report_sha256,
        structure_evidence_sha256=_required(job.structure_evidence_sha256),
        review_attempt_id=_review_attempt_id(
            worker_id,
            report_sha256,
        ),
        invalid_attempt_count=0,
        reviewed_at=report.reviewed_at,
    )
    canonical_path = store.root / "final-reviews" / f"{job.job_id}.json"
    _atomic_model(canonical_path, canonical)
    return store.complete_review(
        job.job_id,
        worker_id,
        canonical_path.relative_to(store.repo_root).as_posix(),
    )


def ingest_terra_final_review(
    store: PipelineStore,
    *,
    job_id: str,
    worker_id: str,
    report_path_value: str,
    invalid_attempt_count: int = 0,
) -> RepairJob:
    """Validate one assigned Terra report and complete its canonical review lease."""
    job = store.load_job(job_id)
    if job.assigned_reviewer != "gpt-5.6-terra":
        message = "Terra report cannot complete a Grok-assigned job"
        raise ValueError(message)
    report_path = resolve_repo_path(store.repo_root, report_path_value)
    report = _load_terra_review_artifact(report_path, store.repo_root)
    _validate_terra_review(job, report, store.repo_root)
    report_sha256 = sha256_path(report_path)
    invalidated = _invalidate_unproven_final_review(
        store,
        job=job,
        worker_id=worker_id,
        report_path_value=report_path_value,
        report_sha256=report_sha256,
        issues=report.issues,
    )
    if invalidated is not None:
        return invalidated
    replay_path = _existing_final_review_replay_path(
        store,
        job,
        report_path_value=report_path_value,
        report_sha256=report_sha256,
    )
    if replay_path is not None:
        return store.complete_review(
            job.job_id,
            worker_id,
            replay_path,
        )
    duration_ms = max(
        0,
        round((report.reviewed_at - job.updated_at).total_seconds() * 1000),
    )
    canonical = FinalReviewRecord(
        job_id=job.job_id,
        source_id=job.source_id,
        assigned_reviewer=job.assigned_reviewer,
        review_model=report.review_model,
        source_sha256=_required(job.review_source_sha256),
        candidate_sha256=_required(job.review_candidate_sha256),
        verdict=report.verdict,
        issue_count=len(report.issues),
        reached_real_eof=True,
        duration_ms=duration_ms,
        detailed_report_path=report_path_value,
        detailed_report_sha256=report_sha256,
        structure_evidence_sha256=_required(job.structure_evidence_sha256),
        review_attempt_id=_review_attempt_id(worker_id, report_sha256),
        invalid_attempt_count=invalid_attempt_count,
        reviewed_at=report.reviewed_at,
    )
    canonical_path = store.root / "final-reviews" / f"{job.job_id}.json"
    _atomic_model(canonical_path, canonical)
    return store.complete_review(
        job.job_id,
        worker_id,
        canonical_path.relative_to(store.repo_root).as_posix(),
    )


def _load_terra_review_artifact(
    report_path: Path,
    repo_root: Path,
) -> TerraReviewArtifact:
    """Load canonical Terra output or normalize its strict structured variant."""
    report_text = report_path.read_text(encoding="utf-8-sig")
    try:
        return TerraReviewArtifact.model_validate_json(report_text)
    except ValidationError:
        structured = TerraStructuredReviewArtifact.model_validate_json(report_text)

    english = structured.inputs.english
    chinese = structured.inputs.chinese
    expected_scope = (
        structured.review_scope.english_path,
        structured.review_scope.chinese_path,
    )
    actual_scope = (english.path, chinese.path)
    if expected_scope != actual_scope:
        message = "structured Terra report scope differs from its hash evidence"
        raise ValueError(message)

    for input_record, coverage in (
        (english, structured.read_coverage.english),
        (chinese, structured.read_coverage.chinese),
    ):
        if input_record.sha256 != input_record.expected_sha256:
            message = "structured Terra report expected and actual hashes differ"
            raise ValueError(message)
        input_path = resolve_repo_path(repo_root, input_record.path)
        if sha256_path(input_path) != input_record.sha256:
            message = "structured Terra reviewed file hash changed"
            raise ValueError(message)
        line_count = len(input_path.read_text(encoding="utf-8-sig").splitlines())
        if coverage.last_line_read != line_count:
            message = "structured Terra report did not prove the actual EOF line"
            raise ValueError(message)

    reviewed_at = dt.datetime.fromtimestamp(
        report_path.stat().st_mtime,
        tz=dt.UTC,
    )
    return TerraReviewArtifact(
        source_id=structured.source_id,
        english_path=english.path,
        chinese_path=chinese.path,
        expected_source_sha256=english.expected_sha256,
        actual_source_sha256=english.sha256,
        expected_candidate_sha256=chinese.expected_sha256,
        actual_candidate_sha256=chinese.sha256,
        review_model=structured.review_model,
        verdict="fail",
        issues=structured.issues,
        reviewed_at=reviewed_at,
        eof_verification=TerraEofVerification(complete_to_eof=True),
    )


def _existing_final_review_replay_path(
    store: PipelineStore,
    job: RepairJob,
    *,
    report_path_value: str,
    report_sha256: str,
) -> str | None:
    """Return canonical evidence for a post-commit completion replay."""
    if job.state not in {
        PipelineState.PROMOTION_READY,
        PipelineState.PROMOTED,
        PipelineState.ISOLATED,
    }:
        return None
    if job.final_review_path is None or job.final_review_sha256 is None:
        message = "terminal review job has no canonical review evidence"
        raise ValueError(message)
    canonical_path = resolve_repo_path(store.repo_root, job.final_review_path)
    if sha256_path(canonical_path) != job.final_review_sha256:
        message = "canonical review evidence changed after completion"
        raise ValueError(message)
    canonical = FinalReviewRecord.model_validate_json(
        canonical_path.read_text(encoding="utf-8-sig")
    )
    if (
        canonical.detailed_report_path != report_path_value
        or canonical.detailed_report_sha256 != report_sha256
    ):
        message = "review replay uses different detailed evidence"
        raise ValueError(message)
    return job.final_review_path


def _validate_terra_review(
    job: RepairJob,
    report: TerraReviewArtifact,
    repo_root: Path,
) -> None:
    expected = (
        job.source_id,
        job.review_source_path,
        job.review_candidate_path,
        job.review_source_sha256,
        job.review_source_sha256,
        job.review_candidate_sha256,
        job.review_candidate_sha256,
    )
    actual = (
        report.source_id,
        report.english_path,
        report.chinese_path,
        report.expected_source_sha256,
        report.actual_source_sha256,
        report.expected_candidate_sha256,
        report.actual_candidate_sha256,
    )
    if expected != actual:
        message = "Terra report does not match the assigned materialized review pair"
        raise ValueError(message)
    review_files = (
        (_required(job.review_source_path), _required(job.review_source_sha256)),
        (_required(job.review_candidate_path), _required(job.review_candidate_sha256)),
    )
    for path_value, expected_sha256 in review_files:
        if sha256_path(resolve_repo_path(repo_root, path_value)) != expected_sha256:
            message = "reviewed final-site-shape file hash changed"
            raise ValueError(message)


def _validate_grok_review(
    job: RepairJob,
    report: GrokReviewArtifact,
    status: GrokRunnerStatus,
    repo_root: Path,
) -> None:
    expected = (
        job.source_id,
        job.assigned_reviewer,
        job.review_candidate_path,
        job.review_candidate_sha256,
        job.review_source_sha256,
        job.provider_model,
    )
    actual = (
        report.source_id,
        report.review_model,
        report.candidate_path,
        report.candidate_sha256,
        report.source_sha256,
        report.translation_model,
    )
    if expected != actual:
        message = "Grok report does not match the assigned materialized review pair"
        raise ValueError(message)
    status_verdict = (
        "pass"
        if status.pass_count
        else "warn"
        if status.warn_count
        else "fail"
    )
    if status.last_source != job.source_id or status_verdict != report.status:
        message = "Grok runner status does not match its review report"
        raise ValueError(message)
    review_files = (
        (_required(job.review_source_path), _required(job.review_source_sha256)),
        (_required(job.review_candidate_path), _required(job.review_candidate_sha256)),
    )
    for path_value, expected_sha256 in review_files:
        if sha256_path(resolve_repo_path(repo_root, path_value)) != expected_sha256:
            message = "reviewed final-site-shape file hash changed"
            raise ValueError(message)
    actual_counts = review_structure_counts(
        resolve_repo_path(repo_root, _required(job.review_source_path)),
        resolve_repo_path(repo_root, _required(job.review_candidate_path)),
    )
    if report.structure_counts != actual_counts:
        message = "Grok report structure counts do not match the reviewed files"
        raise ValueError(message)


def _invalidate_unproven_final_review(  # noqa: PLR0913
    store: PipelineStore,
    *,
    job: RepairJob,
    worker_id: str,
    report_path_value: str,
    report_sha256: str,
    issues: tuple[dict[str, object], ...],
) -> RepairJob | None:
    """Keep schema-valid but unproven model claims out of terminal states."""
    try:
        validate_final_review_issue_evidence(
            source_path=resolve_repo_path(
                store.repo_root,
                _required(job.review_source_path),
            ),
            candidate_path=resolve_repo_path(
                store.repo_root,
                _required(job.review_candidate_path),
            ),
            issues=issues,
        )
    except FinalReviewEvidenceError as error:
        invalidation_id = sha256_text(
            "\0".join(
                (
                    job.job_id,
                    report_sha256,
                    error.code,
                    str(error),
                )
            )
        )
        record = FinalReviewInvalidationRecord(
            invalidation_id=invalidation_id,
            job_id=job.job_id,
            source_id=job.source_id,
            assigned_reviewer=job.assigned_reviewer,
            report_path=report_path_value,
            report_sha256=report_sha256,
            source_sha256=_required(job.review_source_sha256),
            candidate_sha256=_required(job.review_candidate_sha256),
            evidence_code=error.code,
            evidence_message=str(error),
            invalidated_at=dt.datetime.now(UTC),
        )
        path = store.review_invalidations_root / f"{record.invalidation_id}.json"
        _atomic_model(path, record)
        return store.invalidate_review_attempt(
            job.job_id,
            worker_id,
            path.relative_to(store.repo_root).as_posix(),
        )
    return None


def review_structure_counts(
    source_path: Path,
    candidate_path: Path,
) -> GrokStructureCounts:
    """Count the structural evidence the Grok report claims to have inspected."""
    source = source_path.read_text(encoding="utf-8-sig")
    candidate = candidate_path.read_text(encoding="utf-8-sig")
    source_fences = sum(bool(_FENCE_RE.match(line)) for line in source.splitlines())
    candidate_fences = sum(
        bool(_FENCE_RE.match(line)) for line in candidate.splitlines()
    )
    if source_fences % 2 or candidate_fences % 2:
        message = "reviewed final-site-shape file has an unbalanced code fence"
        raise ValueError(message)
    return GrokStructureCounts(
        source_headings=sum(
            bool(_HEADING_RE.match(line)) for line in source.splitlines()
        ),
        candidate_headings=sum(
            bool(_HEADING_RE.match(line)) for line in candidate.splitlines()
        ),
        source_code_fences=source_fences // 2,
        candidate_code_fences=candidate_fences // 2,
        source_links=len(_LINK_RE.findall(source)),
        candidate_links=len(_LINK_RE.findall(candidate)),
    )


def _validate_artifact(
    job: RepairJob,
    artifact: TargetedFixArtifact,
    materialized: MaterializedReviewEntry,
    repo_root: Path,
) -> None:
    expected = (
        job.source_id,
        job.provider,
        job.provider_model,
        job.base_candidate_sha256,
        job.source_sha256,
        job.review_path,
        job.assigned_reviewer,
        set(job.issue_ids),
    )
    actual = (
        artifact.source_id,
        artifact.provider,
        artifact.model,
        artifact.base_candidate_sha256,
        artifact.source_sha256,
        artifact.review_path,
        artifact.assigned_reviewer,
        set(artifact.covered_issue_ids),
    )
    if expected != actual:
        message = "targeted fix artifact does not match the canonical job"
        raise ValueError(message)
    output_path = resolve_repo_path(repo_root, artifact.output_path)
    if sha256_path(output_path) != artifact.output_sha256:
        message = "targeted fix output hash changed"
        raise ValueError(message)
    if parse_accepted_page(output_path).translation_model != artifact.model:
        message = "targeted fix output has incorrect translation provenance"
        raise ValueError(message)
    materialized_expected = (
        job.source_id,
        artifact.output_path,
        artifact.output_sha256,
        job.source_path,
        job.source_sha256,
        artifact.model,
        job.assigned_reviewer,
    )
    _validate_materialized_values(materialized_expected, materialized, repo_root)


def _validate_materialized_review(
    job: RepairJob,
    materialized: MaterializedReviewEntry,
    repo_root: Path,
) -> None:
    """Verify one final-site-shape pair against canonical raw job provenance."""
    materialized_expected = (
        job.source_id,
        job.output_path,
        job.output_sha256,
        job.source_path,
        job.source_sha256,
        job.provider_model,
        job.assigned_reviewer,
    )
    _validate_materialized_values(materialized_expected, materialized, repo_root)


def _validate_materialized_values(
    expected: tuple[str | None, ...],
    materialized: MaterializedReviewEntry,
    repo_root: Path,
) -> None:
    """Verify public files and their binding to one raw candidate."""
    materialized_actual = (
        materialized.source_id,
        materialized.raw_candidate_path,
        materialized.raw_candidate_sha256,
        materialized.raw_source_path,
        materialized.raw_source_sha256,
        materialized.translation_model,
        materialized.assigned_reviewer,
    )
    if expected != materialized_actual:
        message = "materialized review pair does not match the repaired candidate"
        raise ValueError(message)
    public_paths = (
        (materialized.english_path, materialized.source_sha256),
        (materialized.chinese_path, materialized.candidate_sha256),
    )
    for path_value, expected_sha256 in public_paths:
        if sha256_path(resolve_repo_path(repo_root, path_value)) != expected_sha256:
            message = "materialized review file hash changed"
            raise ValueError(message)


def _atomic_model(path: Path, value: BaseModel) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".{uuid.uuid4().hex}.tmp")
    _ = temporary.write_text(
        value.model_dump_json(indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    delay = 0.01
    for attempt in range(_ATOMIC_REPLACE_ATTEMPTS):
        try:
            _ = temporary.replace(path)
        except PermissionError:
            if attempt + 1 == _ATOMIC_REPLACE_ATTEMPTS:
                raise
            time.sleep(delay)
            delay *= 2
        else:
            return


def _atomic_bytes(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        if path.read_bytes() != value:
            message = "existing materialized review file differs from repair"
            raise ValueError(message)
        return
    temporary = path.with_suffix(path.suffix + f".{uuid.uuid4().hex}.tmp")
    _ = temporary.write_bytes(value)
    delay = 0.01
    for attempt in range(_ATOMIC_REPLACE_ATTEMPTS):
        try:
            _ = temporary.replace(path)
        except PermissionError:
            if attempt + 1 == _ATOMIC_REPLACE_ATTEMPTS:
                raise
            time.sleep(delay)
            delay *= 2
        else:
            return


def _required(value: str | None) -> str:
    if value is None:
        message = "pipeline review provenance is incomplete"
        raise ValueError(message)
    return value


def _review_attempt_id(worker_id: str, report_sha256: str) -> str:
    """Derive a safe, collision-resistant review-attempt identity."""
    normalized = re.sub(r"[^a-z0-9._-]+", "-", worker_id.lower()).strip("-.")
    prefix = normalized or "review"
    return f"{prefix[:100]}-{report_sha256[:12]}"

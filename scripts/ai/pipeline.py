# Copyright 2026

"""Resumable state machine for reviewed translation repairs."""

from __future__ import annotations

import ctypes
import os
import time
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from math import ceil
from typing import TYPE_CHECKING, ClassVar, Final, Literal, Self, cast

from pydantic import BaseModel, ConfigDict, Field, model_validator

from scripts.ai.final_shape import (
    FinalShapeEvidence,
    validate_final_shape_evidence,
)
from scripts.ai.page_format import parse_accepted_page
from scripts.ai.review_contract import (
    AssignedReviewer,
    RepairReadyReview,
    load_repair_ready_review,
    resolve_repo_path,
    sha256_path,
    sha256_text,
)

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

Provider = Literal["kimi", "glm"]
ProviderModel = Literal["k3", "glm-5.2"]
ReviewOutcome = Literal["pass", "warn", "fail"]

_PROVIDER_MODELS: Final[dict[str, str]] = {
    "kimi": "k3",
    "glm": "glm-5.2",
}
_ATOMIC_REPLACE_ATTEMPTS: Final = 8
_ATOMIC_REPLACE_INITIAL_DELAY_SECONDS: Final = 0.01


class PipelineState(StrEnum):
    """Canonical lifecycle states for one repair attempt."""

    DISCOVERED = "discovered"
    BRIDGE_VERIFIED = "bridge_verified"
    REPAIR_QUEUED = "repair_queued"
    REPAIR_RUNNING = "repair_running"
    CANDIDATE_VALIDATED = "candidate_validated"
    REVIEW_QUEUED = "review_queued"
    REVIEW_RUNNING = "review_running"
    PROMOTION_READY = "promotion_ready"
    PROMOTED = "promoted"
    ISOLATED = "isolated"
    BLOCKED = "blocked"
    FAILED_RETRYABLE = "failed_retryable"
    FAILED_TERMINAL = "failed_terminal"


TERMINAL_STATES: Final[frozenset[PipelineState]] = frozenset(
    {
        PipelineState.PROMOTED,
        PipelineState.ISOLATED,
        PipelineState.FAILED_TERMINAL,
    }
)


class EventKind(StrEnum):
    """Stable event names in the append-only job ledger."""

    DISCOVERED = "discovered"
    BRIDGE_VERIFIED = "bridge_verified"
    REPAIR_QUEUED = "repair_queued"
    REPAIR_CLAIMED = "repair_claimed"
    REPAIR_RECOVERED = "repair_recovered"
    REPAIR_REQUEUED = "repair_requeued"
    CANDIDATE_VALIDATED = "candidate_validated"
    REVIEW_ARTIFACT_ATTACHED = "review_artifact_attached"
    REVIEW_QUEUED = "review_queued"
    REVIEW_CLAIMED = "review_claimed"
    REVIEW_RECOVERED = "review_recovered"
    REVIEW_INVALIDATED = "review_invalidated"
    REVIEW_COMPLETED = "review_completed"
    PROMOTED = "promoted"
    ISOLATED = "isolated"
    BLOCKED = "blocked"
    FAILED_RETRYABLE = "failed_retryable"
    FAILED_TERMINAL = "failed_terminal"


class _StrictModel(BaseModel):
    """Base class for immutable pipeline records."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )


class PipelinePolicy(_StrictModel):
    """Concurrency and backpressure controls for the local pipeline."""

    version: Literal[1] = 1
    repair_parallelism: int = Field(default=2, ge=1, le=4)
    kimi_parallelism: int = Field(default=1, ge=1, le=2)
    glm_parallelism: int = Field(default=1, ge=1, le=2)
    review_parallelism: int = Field(default=4, ge=1, le=4)
    terra_parallelism: int = Field(default=2, ge=1, le=4)
    grok_parallelism: int = Field(default=2, ge=1, le=4)
    deep_audit_parallelism: int = Field(default=6, ge=1, le=12)
    deep_audit_terra_parallelism: int = Field(default=3, ge=1, le=6)
    deep_audit_grok_parallelism: int = Field(default=3, ge=1, le=6)
    bridge_parallelism: int = Field(default=2, ge=1, le=4)
    review_queue_limit: int = Field(default=8, ge=1, le=32)
    downstream_wip_limit: int = Field(default=12, ge=4, le=256)
    promotion_ready_limit: int = Field(default=8, ge=1, le=32)
    promotion_batch_size: int = Field(default=3, ge=1, le=6)
    promotion_batch_max_wait_seconds: int = Field(
        default=300,
        ge=30,
        le=1800,
    )
    promotion_max_wait_seconds: int = Field(default=600, ge=60, le=3600)
    lease_seconds: int = Field(default=900, ge=30, le=7200)
    lock_timeout_seconds: float = Field(default=5.0, gt=0, le=60)
    stale_lock_seconds: float = Field(default=60.0, gt=1, le=600)

    @model_validator(mode="after")
    def _lane_limits_fit_global_limits(self) -> Self:
        if self.kimi_parallelism + self.glm_parallelism < self.repair_parallelism:
            message = "provider lane limits cannot satisfy repair parallelism"
            raise ValueError(message)
        if self.terra_parallelism + self.grok_parallelism < self.review_parallelism:
            message = "reviewer lane limits cannot satisfy review parallelism"
            raise ValueError(message)
        if (
            self.deep_audit_terra_parallelism
            + self.deep_audit_grok_parallelism
            < self.deep_audit_parallelism
        ):
            message = "deep-audit lane limits cannot satisfy audit parallelism"
            raise ValueError(message)
        return self


class GateEvidence(_StrictModel):
    """Local invariants that must all pass before semantic re-review."""

    frontmatter: bool
    fenced_code: bool
    inline_code: bool
    mdx: bool
    links: bool
    lf: bool
    materialized: bool

    @model_validator(mode="after")
    def _all_green(self) -> Self:
        if not all(self.model_dump().values()):
            message = "candidate local gates are not all green"
            raise ValueError(message)
        return self


class ProviderResultRecord(_StrictModel):
    """Secret-free result metadata produced by one repair provider call."""

    version: Literal[1] = 1
    job_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_id: str = Field(min_length=1)
    provider: Provider
    model: ProviderModel
    output_path: str = Field(min_length=1)
    output_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    replacement_count: int = Field(ge=1)
    covered_issue_ids: tuple[str, ...] = Field(min_length=1)
    gates: GateEvidence
    duration_ms: int = Field(ge=0)
    cache_hit: bool = False

    @model_validator(mode="after")
    def _provider_model_matches(self) -> Self:
        if _PROVIDER_MODELS[self.provider] != self.model:
            message = "provider result model does not match its provider"
            raise ValueError(message)
        if len(self.covered_issue_ids) != len(set(self.covered_issue_ids)):
            message = "covered issue ids must be unique"
            raise ValueError(message)
        return self


class ReviewArtifactRecord(_StrictModel):
    """Final-site-shape files reviewed after a raw repair candidate passes gates."""

    version: Literal[1] = 1
    job_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_id: str = Field(min_length=1)
    assigned_reviewer: AssignedReviewer
    translation_model: ProviderModel
    raw_source_path: str = Field(min_length=1)
    raw_source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    raw_candidate_path: str = Field(min_length=1)
    raw_candidate_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    review_source_path: str = Field(min_length=1)
    review_source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    review_candidate_path: str = Field(min_length=1)
    review_candidate_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    structure_evidence_path: str = Field(min_length=1)
    structure_evidence_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class FinalReviewRecord(_StrictModel):
    """Canonical review of the materialized final-site-shape page pair."""

    version: Literal[1] = 1
    job_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_id: str = Field(min_length=1)
    assigned_reviewer: AssignedReviewer
    review_model: AssignedReviewer
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    candidate_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    verdict: ReviewOutcome
    issue_count: int = Field(ge=0)
    reached_real_eof: bool
    duration_ms: int = Field(ge=0)
    detailed_report_path: str | None = Field(default=None, min_length=1)
    detailed_report_sha256: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )
    structure_evidence_sha256: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )
    review_attempt_id: str | None = Field(
        default=None,
        pattern=r"^[a-z0-9][a-z0-9._-]{0,119}$",
    )
    invalid_attempt_count: int | None = Field(default=None, ge=0)
    reviewed_at: datetime | None = None

    @model_validator(mode="after")
    def _review_is_consistent(self) -> Self:
        if self.assigned_reviewer != self.review_model:
            message = "final review model does not match the assigned reviewer"
            raise ValueError(message)
        if not self.reached_real_eof:
            message = "final review did not reach the real EOF"
            raise ValueError(message)
        if self.verdict == "pass" and self.issue_count != 0:
            message = "a passing final review cannot contain issues"
            raise ValueError(message)
        if self.verdict != "pass" and self.issue_count == 0:
            message = "a non-passing final review must contain issues"
            raise ValueError(message)
        detailed_fields = (
            self.detailed_report_path,
            self.detailed_report_sha256,
            self.structure_evidence_sha256,
            self.review_attempt_id,
            self.invalid_attempt_count,
            self.reviewed_at,
        )
        if any(value is not None for value in detailed_fields) and not all(
            value is not None for value in detailed_fields
        ):
            message = "detailed final review provenance is incomplete"
            raise ValueError(message)
        if self.reviewed_at is not None and self.reviewed_at.utcoffset() is None:
            message = "final review timestamp must be timezone-aware"
            raise ValueError(message)
        return self


class FinalReviewInvalidationRecord(_StrictModel):
    """Immutable proof that one assigned final report cannot enter a terminal state."""

    version: Literal[1] = 1
    invalidation_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    job_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_id: str = Field(min_length=1)
    assigned_reviewer: AssignedReviewer
    report_path: str = Field(min_length=1)
    report_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    candidate_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    evidence_code: str = Field(pattern=r"^[a-z0-9_]+$")
    evidence_message: str = Field(min_length=1, max_length=1000)
    invalidated_at: datetime


class PromotionEvidence(_StrictModel):
    """Evidence required before the promotion actor writes a formal page."""

    version: Literal[1] = 1
    job_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_id: str = Field(min_length=1)
    target_path: str = Field(min_length=1)
    target_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    page_tests: bool
    typecheck: bool
    lint: bool
    materialization: bool
    build: bool
    routes: bool

    @model_validator(mode="after")
    def _promotion_gates_green(self) -> Self:
        gates = (
            self.page_tests,
            self.typecheck,
            self.lint,
            self.materialization,
            self.build,
            self.routes,
        )
        if not all(gates):
            message = "promotion evidence contains a failed gate"
            raise ValueError(message)
        return self


class RepairJobSpec(_StrictModel):
    """Immutable identity and routing for one repair attempt."""

    version: Literal[1] = 1
    source_id: str = Field(min_length=1)
    source_path: str = Field(min_length=1)
    candidate_path: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    base_candidate_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    review_path: str = Field(min_length=1)
    assigned_reviewer: AssignedReviewer
    provider: Provider
    provider_model: ProviderModel
    attempt_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{0,79}$")
    intake_id: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )

    @model_validator(mode="after")
    def _provider_model_matches(self) -> Self:
        if _PROVIDER_MODELS[self.provider] != self.provider_model:
            message = "repair job model does not match its provider"
            raise ValueError(message)
        return self


class RepairJob(_StrictModel):
    """Materialized state for one immutable repair attempt identity."""

    version: Literal[1] = 1
    job_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_id: str
    source_path: str
    candidate_path: str
    source_sha256: str
    base_candidate_sha256: str
    review_path: str
    review_sha256: str
    assigned_reviewer: AssignedReviewer
    provider: Provider
    provider_model: ProviderModel
    attempt_id: str
    intake_id: str | None = None
    issue_ids: tuple[str, ...] = Field(min_length=1)
    state: PipelineState
    created_at: datetime
    updated_at: datetime
    last_sequence: int = Field(ge=1)
    output_path: str | None = None
    output_sha256: str | None = None
    provider_result_path: str | None = None
    provider_result_sha256: str | None = None
    translation_model: ProviderModel | None = None
    review_artifact_path: str | None = None
    review_artifact_sha256: str | None = None
    review_source_path: str | None = None
    review_source_sha256: str | None = None
    review_candidate_path: str | None = None
    review_candidate_sha256: str | None = None
    structure_evidence_path: str | None = None
    structure_evidence_sha256: str | None = None
    final_review_path: str | None = None
    final_review_sha256: str | None = None
    promotion_evidence_path: str | None = None
    promotion_evidence_sha256: str | None = None
    terminal_reason: str | None = None

    @model_validator(mode="after")
    def _identity_and_state_are_consistent(self) -> Self:
        expected = job_id_for(
            self.source_id,
            self.source_sha256,
            self.base_candidate_sha256,
            self.attempt_id,
        )
        if self.job_id != expected:
            message = "repair job id does not match its immutable identity"
            raise ValueError(message)
        if _PROVIDER_MODELS[self.provider] != self.provider_model:
            message = "repair job provider/model provenance is inconsistent"
            raise ValueError(message)
        if self.translation_model is not None and self.translation_model != self.provider_model:
            message = "translation model must come from the configured repair provider"
            raise ValueError(message)
        output_fields = (
            self.output_path,
            self.output_sha256,
            self.provider_result_path,
            self.provider_result_sha256,
            self.translation_model,
        )
        if any(value is not None for value in output_fields) and not all(
            value is not None for value in output_fields
        ):
            message = "candidate output provenance is incomplete"
            raise ValueError(message)
        review_artifact_fields = (
            self.review_artifact_path,
            self.review_artifact_sha256,
            self.review_source_path,
            self.review_source_sha256,
            self.review_candidate_path,
            self.review_candidate_sha256,
        )
        if any(value is not None for value in review_artifact_fields) and not all(
            value is not None for value in review_artifact_fields
        ):
            message = "materialized review provenance is incomplete"
            raise ValueError(message)
        if any(value is not None for value in review_artifact_fields) and self.output_path is None:
            message = "materialized review provenance requires a raw repair candidate"
            raise ValueError(message)
        structure_evidence_fields = (
            self.structure_evidence_path,
            self.structure_evidence_sha256,
        )
        if any(value is not None for value in structure_evidence_fields) and not all(
            value is not None for value in structure_evidence_fields
        ):
            message = "final-shape evidence provenance is incomplete"
            raise ValueError(message)
        return self


class PipelineEvent(_StrictModel):
    """One immutable transition event containing a recoverable job snapshot."""

    version: Literal[1] = 1
    event_id: str = Field(pattern=r"^[0-9a-f]{32}$")
    job_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    sequence: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=160)
    kind: EventKind
    actor: str = Field(min_length=1, max_length=120)
    from_state: PipelineState | None
    to_state: PipelineState
    created_at: datetime
    duration_ms: int | None = Field(default=None, ge=0)
    reason: str | None = Field(default=None, max_length=500)
    snapshot: RepairJob

    @model_validator(mode="after")
    def _snapshot_matches_event(self) -> Self:
        if self.snapshot.job_id != self.job_id:
            message = "event snapshot belongs to a different job"
            raise ValueError(message)
        if self.snapshot.last_sequence != self.sequence:
            message = "event sequence does not match its snapshot"
            raise ValueError(message)
        if self.snapshot.state != self.to_state:
            message = "event state does not match its snapshot"
            raise ValueError(message)
        return self


class JobLease(_StrictModel):
    """Exclusive renewable lease for a running repair or review."""

    version: Literal[1] = 1
    lease_id: str | None = Field(default=None, pattern=r"^[0-9a-f]{32}$")
    job_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    stage: Literal["repair", "review"]
    worker_id: str = Field(min_length=1, max_length=120)
    acquired_at: datetime
    heartbeat_at: datetime
    expires_at: datetime

    @model_validator(mode="after")
    def _lease_times_are_ordered(self) -> Self:
        if self.expires_at <= self.heartbeat_at or self.heartbeat_at < self.acquired_at:
            message = "lease timestamps are not ordered"
            raise ValueError(message)
        return self


class LockOwner(_StrictModel):
    """Process identity guarding a local coordination lock."""

    version: Literal[1] = 1
    token: str = Field(pattern=r"^[0-9a-f]{32}$")
    pid: int = Field(gt=0)
    acquired_at: datetime


class SourceReservation(_StrictModel):
    """Exclusive source ownership shared by audit intake and repair jobs."""

    version: Literal[1] = 1
    source_id: str = Field(min_length=1)
    owner_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    created_at: datetime


class PipelineStatus(_StrictModel):
    """Current queue and WIP counts."""

    version: Literal[1] = 1
    total: int = Field(ge=0)
    states: dict[PipelineState, int]
    repair_running: int = Field(ge=0)
    repair_running_by_provider: dict[Provider, int]
    review_running: int = Field(ge=0)
    review_running_by_reviewer: dict[AssignedReviewer, int]
    review_queued: int = Field(ge=0)
    candidate_validated: int = Field(ge=0)
    promotion_ready: int = Field(ge=0)
    downstream_wip: int = Field(ge=0)
    oldest_repair_queued_ms: int = Field(ge=0)
    oldest_review_queued_ms: int = Field(ge=0)
    oldest_promotion_ready_ms: int = Field(ge=0)
    downstream_backpressure: bool
    review_backpressure: bool


class TimingSummary(_StrictModel):
    """Aggregated wall-clock samples for one pipeline stage."""

    samples: int = Field(ge=0)
    total_ms: int = Field(ge=0)
    mean_ms: int = Field(ge=0)
    p50_ms: int = Field(ge=0)
    p95_ms: int = Field(ge=0)
    max_ms: int = Field(ge=0)


class PipelineMetrics(_StrictModel):
    """Stage timing evidence derived from immutable pipeline events."""

    version: Literal[1] = 1
    generated_at: datetime
    stages: dict[str, TimingSummary]
    counters: dict[str, int]


def job_id_for(
    source_id: str,
    source_sha256: str,
    base_candidate_sha256: str,
    attempt_id: str,
) -> str:
    """Derive a stable job id from the full immutable attempt identity."""
    return sha256_text(
        f"{source_id}\0{source_sha256}\0{base_candidate_sha256}\0{attempt_id}"
    )


class PipelineStore:
    """Atomic local job store with append-only events and renewable leases."""

    def __init__(
        self,
        root: Path,
        repo_root: Path,
        policy: PipelinePolicy | None = None,
    ) -> None:
        """Initialize the store without performing network or provider work."""
        self.root: Path = root.resolve()
        self.repo_root: Path = repo_root.resolve()
        self.policy: PipelinePolicy = policy or PipelinePolicy()
        self.jobs_root: Path = self.root / "jobs"
        self.events_root: Path = self.root / "events"
        self.leases_root: Path = self.root / "leases"
        self.locks_root: Path = self.root / "locks"
        self.source_reservations_root: Path = (
            self.root / "source-reservations"
        )
        self.review_invalidations_root: Path = (
            self.root / "review-invalidations"
        )
        for path in (
            self.jobs_root,
            self.events_root,
            self.leases_root,
            self.locks_root,
            self.source_reservations_root,
            self.review_invalidations_root,
        ):
            path.mkdir(parents=True, exist_ok=True)

    def create_job(
        self,
        spec: RepairJobSpec,
        *,
        actor: str,
    ) -> RepairJob:
        """Validate a repair-ready report and atomically queue a new attempt."""
        review_path = resolve_repo_path(self.repo_root, spec.review_path)
        review = load_repair_ready_review(review_path, self.repo_root)
        self._validate_spec_review(spec, review)
        job_id = job_id_for(
            spec.source_id,
            spec.source_sha256,
            spec.base_candidate_sha256,
            spec.attempt_id,
        )
        source_lock = f"source-{sha256_text(spec.source_id)}"
        with self._lock(source_lock):
            if self._job_path(job_id).is_file() or self._event_path(job_id).is_file():
                existing = self.load_job(job_id)
                self._validate_existing_job_spec(existing, spec)
                return self._resume_job_creation(existing, actor)
            self._validate_source_reservation(
                spec.source_id,
                spec.intake_id,
            )
            self._reject_parallel_source_attempt(spec.source_id)
            now = _utc_now()
            job = RepairJob(
                job_id=job_id,
                source_id=spec.source_id,
                source_path=spec.source_path,
                candidate_path=spec.candidate_path,
                source_sha256=spec.source_sha256,
                base_candidate_sha256=spec.base_candidate_sha256,
                review_path=spec.review_path,
                review_sha256=sha256_path(review_path),
                assigned_reviewer=spec.assigned_reviewer,
                provider=spec.provider,
                provider_model=spec.provider_model,
                attempt_id=spec.attempt_id,
                intake_id=spec.intake_id,
                issue_ids=tuple(issue.issue_id for issue in review.issues),
                state=PipelineState.DISCOVERED,
                created_at=now,
                updated_at=now,
                last_sequence=1,
            )
            self._write_initial_event(job, actor)
            job = self._transition_locked(
                job,
                state=PipelineState.BRIDGE_VERIFIED,
                kind=EventKind.BRIDGE_VERIFIED,
                actor=actor,
                idempotency_key="bridge-verified",
            )
            return self._transition_locked(
                job,
                state=PipelineState.REPAIR_QUEUED,
                kind=EventKind.REPAIR_QUEUED,
                actor=actor,
                idempotency_key="repair-queued",
            )

    def reserve_source(
        self,
        source_id: str,
        owner_id: str,
    ) -> SourceReservation:
        """Reserve one source before audit intake begins."""
        reservation = SourceReservation(
            source_id=source_id,
            owner_id=owner_id,
            created_at=_utc_now(),
        )
        lock_name = f"source-{sha256_text(source_id)}"
        with self._lock(lock_name):
            self._reject_parallel_source_attempt(source_id)
            path = self._source_reservation_path(source_id)
            if path.is_file():
                existing = SourceReservation.model_validate_json(
                    path.read_text(encoding="utf-8-sig")
                )
                if existing.source_id != source_id:
                    message = "source reservation hash collision"
                    raise ValueError(message)
                if existing.owner_id != owner_id:
                    message = f"source already has an active intake: {source_id}"
                    raise ValueError(message)
                return existing
            self._atomic_model(path, reservation)
            return reservation

    def release_source_reservation(
        self,
        source_id: str,
        owner_id: str,
    ) -> None:
        """Release only the exact intake reservation that created a repair."""
        lock_name = f"source-{sha256_text(source_id)}"
        with self._lock(lock_name):
            path = self._source_reservation_path(source_id)
            if not path.is_file():
                return
            existing = SourceReservation.model_validate_json(
                path.read_text(encoding="utf-8-sig")
            )
            if existing.source_id != source_id or existing.owner_id != owner_id:
                message = "source reservation belongs to another intake"
                raise ValueError(message)
            path.unlink()

    def source_reservation(
        self,
        source_id: str,
    ) -> SourceReservation | None:
        """Read current source ownership without changing it."""
        path = self._source_reservation_path(source_id)
        if not path.is_file():
            return None
        reservation = SourceReservation.model_validate_json(
            path.read_text(encoding="utf-8-sig")
        )
        if reservation.source_id != source_id:
            message = "source reservation hash collision"
            raise ValueError(message)
        return reservation

    def _resume_job_creation(self, job: RepairJob, actor: str) -> RepairJob:
        """Finish idempotent initial transitions after a process interruption."""
        if job.state == PipelineState.DISCOVERED:
            job = self._transition_locked(
                job,
                state=PipelineState.BRIDGE_VERIFIED,
                kind=EventKind.BRIDGE_VERIFIED,
                actor=actor,
                idempotency_key="bridge-verified",
            )
        if job.state == PipelineState.BRIDGE_VERIFIED:
            job = self._transition_locked(
                job,
                state=PipelineState.REPAIR_QUEUED,
                kind=EventKind.REPAIR_QUEUED,
                actor=actor,
                idempotency_key="repair-queued",
            )
        return job

    def load_job(self, job_id: str) -> RepairJob:
        """Load the latest event snapshot and repair a stale materialized view."""
        events = self._read_events(job_id)
        if not events:
            message = f"pipeline job does not exist: {job_id}"
            raise ValueError(message)
        latest = events[-1].snapshot
        snapshot_path = self._job_path(job_id)
        current: RepairJob | None = None
        if snapshot_path.is_file():
            current = RepairJob.model_validate_json(
                snapshot_path.read_text(encoding="utf-8-sig")
            )
        if current is None or current.last_sequence != latest.last_sequence:
            self._atomic_model(snapshot_path, latest)
        return latest

    def list_jobs(self) -> tuple[RepairJob, ...]:
        """Return latest snapshots sorted by creation time and job id."""
        jobs = [self.load_job(path.stem) for path in self.events_root.glob("*.jsonl")]
        return tuple(sorted(jobs, key=lambda job: (job.created_at, job.job_id)))

    def status(self) -> PipelineStatus:
        """Return queue, WIP, and backpressure counts."""
        jobs = self.list_jobs()
        now = _utc_now()
        counts = dict.fromkeys(PipelineState, 0)
        repair_by_provider: dict[Provider, int] = {"kimi": 0, "glm": 0}
        review_by_reviewer: dict[AssignedReviewer, int] = {
            "gpt-5.6-terra": 0,
            "grok-4.5": 0,
        }
        for job in jobs:
            counts[job.state] += 1
            if job.state == PipelineState.REPAIR_RUNNING:
                repair_by_provider[job.provider] += 1
            if job.state == PipelineState.REVIEW_RUNNING:
                review_by_reviewer[job.assigned_reviewer] += 1
        review_queued = counts[PipelineState.REVIEW_QUEUED]
        downstream_states = frozenset(
            {
                PipelineState.REPAIR_RUNNING,
                PipelineState.CANDIDATE_VALIDATED,
                PipelineState.REVIEW_QUEUED,
                PipelineState.REVIEW_RUNNING,
                PipelineState.PROMOTION_READY,
            }
        )
        downstream_wip = sum(
            count for state, count in counts.items() if state in downstream_states
        )
        promotion_ready = counts[PipelineState.PROMOTION_READY]
        oldest_repair_queued_ms = _oldest_state_age_ms(
            jobs,
            PipelineState.REPAIR_QUEUED,
            now,
        )
        oldest_review_queued_ms = _oldest_state_age_ms(
            jobs,
            PipelineState.REVIEW_QUEUED,
            now,
        )
        oldest_promotion_ready_ms = _oldest_state_age_ms(
            jobs,
            PipelineState.PROMOTION_READY,
            now,
        )
        downstream_backpressure = (
            downstream_wip >= self.policy.downstream_wip_limit
            or promotion_ready >= self.policy.promotion_ready_limit
            or oldest_promotion_ready_ms
            >= self.policy.promotion_max_wait_seconds * 1000
        )
        return PipelineStatus(
            total=len(jobs),
            states=counts,
            repair_running=counts[PipelineState.REPAIR_RUNNING],
            repair_running_by_provider=repair_by_provider,
            review_running=counts[PipelineState.REVIEW_RUNNING],
            review_running_by_reviewer=review_by_reviewer,
            review_queued=review_queued,
            candidate_validated=counts[PipelineState.CANDIDATE_VALIDATED],
            promotion_ready=promotion_ready,
            downstream_wip=downstream_wip,
            oldest_repair_queued_ms=oldest_repair_queued_ms,
            oldest_review_queued_ms=oldest_review_queued_ms,
            oldest_promotion_ready_ms=oldest_promotion_ready_ms,
            downstream_backpressure=downstream_backpressure,
            review_backpressure=(
                review_queued >= self.policy.review_queue_limit
                or downstream_backpressure
            ),
        )

    def metrics(self) -> PipelineMetrics:
        """Aggregate queue, execution, review, and promotion wall times."""
        samples: dict[str, list[int]] = {
            "repair_queue_wait": [],
            "repair_turnaround": [],
            "provider_service": [],
            "candidate_to_artifact": [],
            "review_queue_wait": [],
            "review_turnaround": [],
            "review_model_service": [],
            "report_ingestion_wait": [],
            "promotion_gate_wait": [],
            "end_to_end": [],
        }
        jobs = self.list_jobs()
        counters = {
            "attempts": len(jobs),
            "unique_sources": len({job.source_id for job in jobs}),
            "provider_results": 0,
            "provider_cache_hits": 0,
            "provider_failures_retryable": 0,
            "provider_failures_terminal": 0,
            "explicit_repair_retries": 0,
            "final_reviews": 0,
            "clean_reviews": 0,
            "invalid_review_attempts": 0,
            "promoted": 0,
            "isolated": 0,
        }
        for job in jobs:
            events = self.events(job.job_id)
            _collect_event_interval(
                events,
                EventKind.REPAIR_QUEUED,
                frozenset({EventKind.REPAIR_CLAIMED}),
                samples["repair_queue_wait"],
            )
            _collect_event_interval(
                events,
                EventKind.REPAIR_CLAIMED,
                frozenset(
                    {
                        EventKind.CANDIDATE_VALIDATED,
                        EventKind.FAILED_RETRYABLE,
                        EventKind.FAILED_TERMINAL,
                    }
                ),
                samples["repair_turnaround"],
            )
            provider_terminal_events = tuple(
                event
                for event in events
                if event.kind
                in {
                    EventKind.CANDIDATE_VALIDATED,
                    EventKind.FAILED_RETRYABLE,
                    EventKind.FAILED_TERMINAL,
                }
            )
            samples["provider_service"].extend(
                event.duration_ms
                for event in provider_terminal_events
                if event.duration_ms is not None
            )
            counters["provider_failures_retryable"] += sum(
                event.kind == EventKind.FAILED_RETRYABLE
                for event in provider_terminal_events
            )
            counters["provider_failures_terminal"] += sum(
                event.kind == EventKind.FAILED_TERMINAL
                for event in provider_terminal_events
            )
            counters["explicit_repair_retries"] += sum(
                event.kind == EventKind.REPAIR_REQUEUED for event in events
            )
            _collect_event_interval(
                events,
                EventKind.CANDIDATE_VALIDATED,
                frozenset({EventKind.REVIEW_ARTIFACT_ATTACHED}),
                samples["candidate_to_artifact"],
            )
            _collect_event_interval(
                events,
                EventKind.REVIEW_QUEUED,
                frozenset({EventKind.REVIEW_CLAIMED}),
                samples["review_queue_wait"],
            )
            _collect_event_interval(
                events,
                EventKind.REVIEW_CLAIMED,
                frozenset({EventKind.REVIEW_COMPLETED, EventKind.ISOLATED}),
                samples["review_turnaround"],
            )
            _collect_event_interval(
                events,
                EventKind.REVIEW_COMPLETED,
                frozenset({EventKind.PROMOTED}),
                samples["promotion_gate_wait"],
            )
            provider_result = self._load_provider_result(job)
            if provider_result is not None:
                counters["provider_results"] += 1
                counters["provider_cache_hits"] += int(provider_result.cache_hit)
            final_review = self._load_final_review(job)
            if final_review is not None:
                counters["final_reviews"] += 1
                counters["clean_reviews"] += int(final_review.verdict == "pass")
                counters["invalid_review_attempts"] += (
                    final_review.invalid_attempt_count or 0
                )
                samples["review_model_service"].append(
                    final_review.duration_ms
                )
                terminal_event = next(
                    (
                        event
                        for event in reversed(events)
                        if event.kind
                        in {EventKind.REVIEW_COMPLETED, EventKind.ISOLATED}
                    ),
                    None,
                )
                if (
                    terminal_event is not None
                    and final_review.reviewed_at is not None
                ):
                    elapsed = round(
                        (
                            terminal_event.created_at - final_review.reviewed_at
                        ).total_seconds()
                        * 1000
                    )
                    samples["report_ingestion_wait"].append(max(0, elapsed))
            terminal_kinds = frozenset(
                {
                    EventKind.PROMOTED,
                    EventKind.ISOLATED,
                    EventKind.FAILED_TERMINAL,
                }
            )
            _collect_event_interval(
                events,
                EventKind.DISCOVERED,
                terminal_kinds,
                samples["end_to_end"],
            )
            counters["promoted"] += int(job.state == PipelineState.PROMOTED)
            counters["isolated"] += int(job.state == PipelineState.ISOLATED)
        return PipelineMetrics(
            generated_at=_utc_now(),
            stages={name: _timing_summary(values) for name, values in samples.items()},
            counters=counters,
        )

    def claim_repair(self, job_id: str, worker_id: str) -> RepairJob:
        """Claim one queued repair while honoring concurrency and backpressure."""
        with self._lock("repair-dispatch"), self._lock(job_id):
            job = self.load_job(job_id)
            if job.state != PipelineState.REPAIR_QUEUED:
                message = "repair job is not queued"
                raise ValueError(message)
            status = self.status()
            if status.repair_running >= self.policy.repair_parallelism:
                message = "repair concurrency limit is reached"
                raise ValueError(message)
            provider_limit = (
                self.policy.kimi_parallelism
                if job.provider == "kimi"
                else self.policy.glm_parallelism
            )
            if status.repair_running_by_provider[job.provider] >= provider_limit:
                message = f"{job.provider} repair concurrency limit is reached"
                raise ValueError(message)
            if status.review_backpressure:
                message = "review queue backpressure is active"
                raise ValueError(message)
            lease = self._create_lease(job, "repair", worker_id)
            try:
                return self._transition_locked(
                    job,
                    state=PipelineState.REPAIR_RUNNING,
                    kind=EventKind.REPAIR_CLAIMED,
                    actor=worker_id,
                    idempotency_key=f"repair-claimed:{worker_id}:{lease.acquired_at.isoformat()}",
                )
            except Exception:
                self._remove_lease(job_id, worker_id)
                raise

    def complete_repair(
        self,
        job_id: str,
        worker_id: str,
        result_path_value: str,
    ) -> RepairJob:
        """Record a validated raw provider result before materialized re-review."""
        with self._lock(job_id):
            job = self.load_job(job_id)
            result_path = resolve_repo_path(self.repo_root, result_path_value)
            result = ProviderResultRecord.model_validate_json(
                result_path.read_text(encoding="utf-8-sig")
            )
            self._validate_provider_result(job, result)
            result_sha256 = sha256_path(result_path)
            output_path = resolve_repo_path(self.repo_root, result.output_path)
            if sha256_path(output_path) != result.output_sha256:
                message = "provider output hash changed"
                raise ValueError(message)
            output_page = parse_accepted_page(output_path)
            if output_page.translation_model != result.model:
                message = "candidate translation_model differs from provider result"
                raise ValueError(message)
            if job.state != PipelineState.REPAIR_RUNNING:
                if (
                    job.provider_result_sha256 == result_sha256
                    and job.output_sha256 == result.output_sha256
                    and job.state
                    in {
                        PipelineState.CANDIDATE_VALIDATED,
                        PipelineState.REVIEW_QUEUED,
                        PipelineState.REVIEW_RUNNING,
                        PipelineState.PROMOTION_READY,
                        PipelineState.PROMOTED,
                        PipelineState.ISOLATED,
                    }
                ):
                    return job
                message = "repair job is not running"
                raise ValueError(message)
            _ = self._require_lease(job, "repair", worker_id)
            updated = _updated_job(
                job,
                output_path=result.output_path,
                output_sha256=result.output_sha256,
                provider_result_path=result_path_value,
                provider_result_sha256=result_sha256,
                translation_model=result.model,
            )
            updated = self._transition_locked(
                updated,
                state=PipelineState.CANDIDATE_VALIDATED,
                kind=EventKind.CANDIDATE_VALIDATED,
                actor=worker_id,
                idempotency_key=f"candidate-validated:{result.output_sha256}",
                duration_ms=result.duration_ms,
            )
            self._remove_lease(job_id, worker_id)
            return updated

    def fail_repair(
        self,
        job_id: str,
        worker_id: str,
        *,
        reason: str,
        retryable: bool,
        duration_ms: int | None = None,
    ) -> RepairJob:
        """Record a provider or local-gate failure and release its repair lease."""
        normalized_reason = reason.strip()
        if not normalized_reason:
            message = "repair failure reason must not be empty"
            raise ValueError(message)
        target = (
            PipelineState.FAILED_RETRYABLE
            if retryable
            else PipelineState.FAILED_TERMINAL
        )
        kind = (
            EventKind.FAILED_RETRYABLE
            if retryable
            else EventKind.FAILED_TERMINAL
        )
        with self._lock(job_id):
            job = self.load_job(job_id)
            events = self._read_events(job_id)
            if job.state in {
                PipelineState.FAILED_RETRYABLE,
                PipelineState.FAILED_TERMINAL,
            }:
                latest = events[-1]
                if (
                    latest.kind == kind
                    and latest.actor == worker_id
                    and latest.reason == normalized_reason
                ):
                    return job
                message = "repair job already has a different failure outcome"
                raise ValueError(message)
            if job.state != PipelineState.REPAIR_RUNNING:
                message = "repair job is not running"
                raise ValueError(message)
            lease = self._require_lease(job, "repair", worker_id)
            lease_generation = lease.lease_id or sha256_text(
                f"{lease.worker_id}\0{lease.acquired_at.isoformat()}"
            )[:32]
            idempotency_key = (
                f"repair-failed:{target.value}:{lease_generation}:"
                f"{sha256_text(normalized_reason)}"
            )
            updated = _updated_job(job, terminal_reason=normalized_reason)
            updated = self._transition_locked(
                updated,
                state=target,
                kind=kind,
                actor=worker_id,
                idempotency_key=idempotency_key,
                duration_ms=duration_ms,
                reason=normalized_reason,
            )
            self._remove_lease(job_id, worker_id)
            return updated

    def requeue_failed_repair(
        self,
        job_id: str,
        *,
        actor: str,
    ) -> RepairJob:
        """Explicitly requeue one retryable repair without an automatic loop."""
        with self._lock(job_id):
            job = self.load_job(job_id)
            events = self._read_events(job_id)
            if (
                job.state == PipelineState.REPAIR_QUEUED
                and events[-1].kind == EventKind.REPAIR_REQUEUED
            ):
                return job
            if job.state != PipelineState.FAILED_RETRYABLE:
                message = "repair job is not in a retryable failure state"
                raise ValueError(message)
            idempotency_key = f"repair-requeued:{job.last_sequence}"
            updated = _updated_job(job, terminal_reason=None)
            return self._transition_locked(
                updated,
                state=PipelineState.REPAIR_QUEUED,
                kind=EventKind.REPAIR_REQUEUED,
                actor=actor,
                idempotency_key=idempotency_key,
                reason="explicit retry approved",
            )

    def attach_review_artifact(
        self,
        job_id: str,
        artifact_path_value: str,
        *,
        actor: str,
    ) -> RepairJob:
        """Attach verified final-site-shape files and queue assigned re-review."""
        with self._lock("review-dispatch"), self._lock(job_id):
            job = self.load_job(job_id)
            if job.state not in {
                PipelineState.CANDIDATE_VALIDATED,
                PipelineState.REVIEW_QUEUED,
            }:
                message = "review artifact can only attach to a validated candidate"
                raise ValueError(message)
            artifact_path = resolve_repo_path(self.repo_root, artifact_path_value)
            artifact = ReviewArtifactRecord.model_validate_json(
                artifact_path.read_text(encoding="utf-8-sig")
            )
            self._validate_review_artifact(job, artifact)
            updated = _updated_job(
                job,
                review_artifact_path=artifact_path_value,
                review_artifact_sha256=sha256_path(artifact_path),
                review_source_path=artifact.review_source_path,
                review_source_sha256=artifact.review_source_sha256,
                review_candidate_path=artifact.review_candidate_path,
                review_candidate_sha256=artifact.review_candidate_sha256,
                structure_evidence_path=artifact.structure_evidence_path,
                structure_evidence_sha256=artifact.structure_evidence_sha256,
            )
            updated = self._transition_locked(
                updated,
                state=job.state,
                kind=EventKind.REVIEW_ARTIFACT_ATTACHED,
                actor=actor,
                idempotency_key=(
                    f"review-artifact-attached:{updated.review_artifact_sha256}"
                ),
            )
            if updated.state == PipelineState.REVIEW_QUEUED:
                return updated
            if self.status().review_queued >= self.policy.review_queue_limit:
                return updated
            return self._transition_locked(
                updated,
                state=PipelineState.REVIEW_QUEUED,
                kind=EventKind.REVIEW_QUEUED,
                actor="pipeline",
                idempotency_key=f"review-queued:{artifact.review_candidate_sha256}",
            )

    def enqueue_waiting_reviews(self) -> tuple[RepairJob, ...]:
        """Move validated candidates into the bounded assigned-review queue."""
        queued: list[RepairJob] = []
        with self._lock("review-dispatch"):
            candidates = [
                job
                for job in self.list_jobs()
                if job.state == PipelineState.CANDIDATE_VALIDATED
                and job.review_artifact_path is not None
            ]
            for candidate in candidates:
                if self.status().review_queued >= self.policy.review_queue_limit:
                    break
                with self._lock(candidate.job_id):
                    current = self.load_job(candidate.job_id)
                    if current.state != PipelineState.CANDIDATE_VALIDATED:
                        continue
                    queued.append(
                        self._transition_locked(
                            current,
                            state=PipelineState.REVIEW_QUEUED,
                            kind=EventKind.REVIEW_QUEUED,
                            actor="pipeline",
                            idempotency_key=f"review-queued:{current.output_sha256}",
                        )
                    )
        return tuple(queued)

    def claim_review(self, job_id: str, worker_id: str) -> RepairJob:
        """Claim one assigned final review under the reviewer WIP limit."""
        with self._lock("review-dispatch"), self._lock(job_id):
            job = self.load_job(job_id)
            if job.state != PipelineState.REVIEW_QUEUED:
                message = "review job is not queued"
                raise ValueError(message)
            if job.review_artifact_path is None:
                message = "review job has no materialized review artifact"
                raise ValueError(message)
            if self.status().review_running >= self.policy.review_parallelism:
                message = "review concurrency limit is reached"
                raise ValueError(message)
            status = self.status()
            reviewer_limit = (
                self.policy.terra_parallelism
                if job.assigned_reviewer == "gpt-5.6-terra"
                else self.policy.grok_parallelism
            )
            if (
                status.review_running_by_reviewer[job.assigned_reviewer]
                >= reviewer_limit
            ):
                message = (
                    f"{job.assigned_reviewer} review concurrency limit is reached"
                )
                raise ValueError(message)
            lease = self._create_lease(job, "review", worker_id)
            try:
                return self._transition_locked(
                    job,
                    state=PipelineState.REVIEW_RUNNING,
                    kind=EventKind.REVIEW_CLAIMED,
                    actor=worker_id,
                    idempotency_key=f"review-claimed:{worker_id}:{lease.acquired_at.isoformat()}",
                )
            except Exception:
                self._remove_lease(job_id, worker_id)
                raise

    def complete_review(
        self,
        job_id: str,
        worker_id: str,
        review_path_value: str,
    ) -> RepairJob:
        """Route a complete assigned review to promotion-ready or isolation."""
        with self._lock(job_id):
            job = self.load_job(job_id)
            review_path = resolve_repo_path(self.repo_root, review_path_value)
            review = FinalReviewRecord.model_validate_json(
                review_path.read_text(encoding="utf-8-sig")
            )
            self._validate_final_review(job, review)
            review_sha256 = sha256_path(review_path)
            if job.state != PipelineState.REVIEW_RUNNING:
                if (
                    job.final_review_sha256 == review_sha256
                    and job.state
                    in {
                        PipelineState.PROMOTION_READY,
                        PipelineState.PROMOTED,
                        PipelineState.ISOLATED,
                    }
                ):
                    return job
                message = "review job is not running"
                raise ValueError(message)
            _ = self._require_lease(job, "review", worker_id)
            updated = _updated_job(
                job,
                final_review_path=review_path_value,
                final_review_sha256=review_sha256,
            )
            self._remove_lease(job_id, worker_id)
            if review.verdict == "pass":
                return self._transition_locked(
                    updated,
                    state=PipelineState.PROMOTION_READY,
                    kind=EventKind.REVIEW_COMPLETED,
                    actor=worker_id,
                    idempotency_key=f"review-pass:{updated.final_review_sha256}",
                    duration_ms=review.duration_ms,
                )
            updated = _updated_job(
                updated,
                terminal_reason=f"assigned review {review.verdict}: {review.issue_count} issues",
            )
            return self._transition_locked(
                updated,
                state=PipelineState.ISOLATED,
                kind=EventKind.ISOLATED,
                actor=worker_id,
                idempotency_key=f"review-{review.verdict}:{updated.final_review_sha256}",
                duration_ms=review.duration_ms,
                reason=updated.terminal_reason,
            )

    def invalidate_review_attempt(
        self,
        job_id: str,
        worker_id: str,
        invalidation_path_value: str,
    ) -> RepairJob:
        """Reject unproven review claims and retry only the same reviewer once."""
        with self._lock(job_id):
            events = self._read_events(job_id)
            invalidation_path = resolve_repo_path(
                self.repo_root,
                invalidation_path_value,
            )
            invalidation = FinalReviewInvalidationRecord.model_validate_json(
                invalidation_path.read_text(encoding="utf-8-sig")
            )
            idempotency_key = (
                f"review-invalidated:{invalidation.invalidation_id}"
            )
            replay = next(
                (
                    event.snapshot
                    for event in events
                    if event.idempotency_key == idempotency_key
                ),
                None,
            )
            if replay is not None:
                return replay
            job = self.load_job(job_id)
            expected = (
                job.job_id,
                job.source_id,
                job.assigned_reviewer,
                job.review_source_sha256,
                job.review_candidate_sha256,
            )
            actual = (
                invalidation.job_id,
                invalidation.source_id,
                invalidation.assigned_reviewer,
                invalidation.source_sha256,
                invalidation.candidate_sha256,
            )
            if expected != actual:
                message = "review invalidation does not match the assigned job"
                raise ValueError(message)
            report_path = resolve_repo_path(
                self.repo_root,
                invalidation.report_path,
            )
            if sha256_path(report_path) != invalidation.report_sha256:
                message = "invalidated final report hash changed"
                raise ValueError(message)
            if job.state != PipelineState.REVIEW_RUNNING:
                message = "review job is not running"
                raise ValueError(message)
            _ = self._require_lease(job, "review", worker_id)
            prior_invalidations = sum(
                event.kind == EventKind.REVIEW_INVALIDATED for event in events
            )
            self._remove_lease(job_id, worker_id)
            if prior_invalidations >= 1:
                updated = _updated_job(
                    job,
                    terminal_reason=(
                        "assigned reviewer contract blocked after two invalid "
                        "evidence attempts"
                    ),
                )
                return self._transition_locked(
                    updated,
                    state=PipelineState.BLOCKED,
                    kind=EventKind.REVIEW_INVALIDATED,
                    actor=worker_id,
                    idempotency_key=idempotency_key,
                    reason=updated.terminal_reason,
                )
            return self._transition_locked(
                job,
                state=PipelineState.REVIEW_QUEUED,
                kind=EventKind.REVIEW_INVALIDATED,
                actor=worker_id,
                idempotency_key=idempotency_key,
                reason=invalidation.evidence_message,
            )

    def promote(
        self,
        job_id: str,
        evidence_path_value: str,
        *,
        actor: str,
    ) -> RepairJob:
        """Mark a clean reviewed page promoted after all site gates pass."""
        with self._lock(job_id):
            job = self.load_job(job_id)
            self._validate_promotion_candidate_locked(job)
            evidence_path = resolve_repo_path(self.repo_root, evidence_path_value)
            evidence = PromotionEvidence.model_validate_json(
                evidence_path.read_text(encoding="utf-8-sig")
            )
            if evidence.job_id != job.job_id or evidence.source_id != job.source_id:
                message = "promotion evidence belongs to a different job"
                raise ValueError(message)
            if evidence.target_sha256 != job.output_sha256:
                message = "promotion target hash differs from the reviewed candidate"
                raise ValueError(message)
            target_path = resolve_repo_path(self.repo_root, evidence.target_path)
            if sha256_path(target_path) != evidence.target_sha256:
                message = "promotion target file hash changed"
                raise ValueError(message)
            evidence_sha256 = sha256_path(evidence_path)
            if job.state == PipelineState.PROMOTED:
                if job.promotion_evidence_sha256 == evidence_sha256:
                    return job
                message = "promoted job has different promotion evidence"
                raise ValueError(message)
            if job.state != PipelineState.PROMOTION_READY:
                message = "job is not ready for promotion"
                raise ValueError(message)
            updated = _updated_job(
                job,
                promotion_evidence_path=evidence_path_value,
                promotion_evidence_sha256=evidence_sha256,
            )
            return self._transition_locked(
                updated,
                state=PipelineState.PROMOTED,
                kind=EventKind.PROMOTED,
                actor=actor,
                idempotency_key=f"promoted:{evidence.target_sha256}",
            )

    def validate_promotion_candidate(self, job_id: str) -> RepairJob:
        """Revalidate the complete clean-review chain before site gates run."""
        with self._lock(job_id):
            job = self.load_job(job_id)
            self._validate_promotion_candidate_locked(job)
            return job

    def heartbeat(self, job_id: str, worker_id: str) -> JobLease:
        """Renew an active worker lease without changing job state."""
        with self._lock(job_id):
            job = self.load_job(job_id)
            stage = (
                "repair"
                if job.state == PipelineState.REPAIR_RUNNING
                else "review"
                if job.state == PipelineState.REVIEW_RUNNING
                else None
            )
            if stage is None:
                message = "job has no running stage to heartbeat"
                raise ValueError(message)
            lease = self._require_lease(job, stage, worker_id)
            now = _utc_now()
            renewed = JobLease(
                lease_id=lease.lease_id,
                job_id=lease.job_id,
                stage=lease.stage,
                worker_id=lease.worker_id,
                acquired_at=lease.acquired_at,
                heartbeat_at=now,
                expires_at=now + timedelta(seconds=self.policy.lease_seconds),
            )
            self._atomic_model(self._lease_path(job_id), renewed)
            return renewed

    def recover_expired_leases(self) -> tuple[RepairJob, ...]:
        """Requeue running jobs whose worker lease expired or disappeared."""
        recovered: list[RepairJob] = []
        now = _utc_now()
        for job in self.list_jobs():
            if job.state not in {
                PipelineState.REPAIR_RUNNING,
                PipelineState.REVIEW_RUNNING,
            }:
                continue
            with self._lock(job.job_id):
                current = self.load_job(job.job_id)
                lease = self._load_lease(current.job_id)
                if lease is not None and lease.expires_at > now:
                    continue
                if lease is not None:
                    self._lease_path(current.job_id).unlink(missing_ok=True)
                if current.state == PipelineState.REPAIR_RUNNING:
                    recovered.append(
                        self._transition_locked(
                            current,
                            state=PipelineState.REPAIR_QUEUED,
                            kind=EventKind.REPAIR_RECOVERED,
                            actor="pipeline",
                            idempotency_key=f"repair-recovered:{current.last_sequence}",
                            reason="worker lease expired",
                        )
                    )
                elif current.state == PipelineState.REVIEW_RUNNING:
                    recovered.append(
                        self._transition_locked(
                            current,
                            state=PipelineState.REVIEW_QUEUED,
                            kind=EventKind.REVIEW_RECOVERED,
                            actor="pipeline",
                            idempotency_key=f"review-recovered:{current.last_sequence}",
                            reason="worker lease expired",
                        )
                    )
        return tuple(recovered)

    def events(self, job_id: str) -> tuple[PipelineEvent, ...]:
        """Return every immutable event for a job."""
        return self._read_events(job_id)

    @contextmanager
    def coordinator_lock(self, name: str) -> Generator[None, None, None]:
        """Serialize one local control-plane reconciler across processes."""
        with self._lock(f"coordinator-{sha256_text(name)}"):
            yield

    def _load_provider_result(
        self,
        job: RepairJob,
    ) -> ProviderResultRecord | None:
        """Load trusted provider metadata when a job has reached that stage."""
        if (
            job.provider_result_path is None
            or job.provider_result_sha256 is None
        ):
            return None
        path = resolve_repo_path(self.repo_root, job.provider_result_path)
        if sha256_path(path) != job.provider_result_sha256:
            message = "provider result metadata hash changed"
            raise ValueError(message)
        return ProviderResultRecord.model_validate_json(
            path.read_text(encoding="utf-8-sig")
        )

    def _load_final_review(
        self,
        job: RepairJob,
    ) -> FinalReviewRecord | None:
        """Load trusted canonical review metadata when one is recorded."""
        if job.final_review_path is None or job.final_review_sha256 is None:
            return None
        path = resolve_repo_path(self.repo_root, job.final_review_path)
        if sha256_path(path) != job.final_review_sha256:
            message = "canonical final review hash changed"
            raise ValueError(message)
        return FinalReviewRecord.model_validate_json(
            path.read_text(encoding="utf-8-sig")
        )

    def _validate_spec_review(
        self,
        spec: RepairJobSpec,
        review: RepairReadyReview,
    ) -> None:
        expected = (
            spec.source_id,
            spec.source_path,
            spec.candidate_path,
            spec.source_sha256,
            spec.base_candidate_sha256,
            spec.assigned_reviewer,
        )
        actual = (
            review.source_id,
            review.source_path,
            review.candidate_path,
            review.source_sha256,
            review.candidate_sha256,
            review.assigned_reviewer,
        )
        if expected != actual:
            message = "repair job spec does not match its repair-ready review"
            raise ValueError(message)

    def _validate_existing_job_spec(
        self,
        job: RepairJob,
        spec: RepairJobSpec,
    ) -> None:
        expected = (
            job.source_id,
            job.source_path,
            job.candidate_path,
            job.source_sha256,
            job.base_candidate_sha256,
            job.assigned_reviewer,
            job.provider,
            job.provider_model,
            job.attempt_id,
            job.intake_id,
        )
        actual = (
            spec.source_id,
            spec.source_path,
            spec.candidate_path,
            spec.source_sha256,
            spec.base_candidate_sha256,
            spec.assigned_reviewer,
            spec.provider,
            spec.provider_model,
            spec.attempt_id,
            spec.intake_id,
        )
        if expected != actual:
            message = "existing repair job has different immutable routing"
            raise ValueError(message)

    def _validate_provider_result(
        self,
        job: RepairJob,
        result: ProviderResultRecord,
    ) -> None:
        expected = (
            job.job_id,
            job.source_id,
            job.provider,
            job.provider_model,
            set(job.issue_ids),
        )
        actual = (
            result.job_id,
            result.source_id,
            result.provider,
            result.model,
            set(result.covered_issue_ids),
        )
        if expected != actual:
            message = "provider result does not cover the exact repair job"
            raise ValueError(message)

    def _validate_review_artifact(
        self,
        job: RepairJob,
        artifact: ReviewArtifactRecord,
    ) -> None:
        expected = (
            job.job_id,
            job.source_id,
            job.assigned_reviewer,
            job.provider_model,
            job.source_path,
            job.source_sha256,
            job.output_path,
            job.output_sha256,
        )
        actual = (
            artifact.job_id,
            artifact.source_id,
            artifact.assigned_reviewer,
            artifact.translation_model,
            artifact.raw_source_path,
            artifact.raw_source_sha256,
            artifact.raw_candidate_path,
            artifact.raw_candidate_sha256,
        )
        if expected != actual:
            message = "materialized review artifact does not match the repair job"
            raise ValueError(message)
        review_files = (
            (artifact.review_source_path, artifact.review_source_sha256),
            (artifact.review_candidate_path, artifact.review_candidate_sha256),
        )
        for path_value, expected_sha256 in review_files:
            path = resolve_repo_path(self.repo_root, path_value)
            if sha256_path(path) != expected_sha256:
                message = "materialized review file hash changed"
                raise ValueError(message)
        evidence_path = resolve_repo_path(
            self.repo_root,
            artifact.structure_evidence_path,
        )
        if sha256_path(evidence_path) != artifact.structure_evidence_sha256:
            message = "final-shape evidence hash changed"
            raise ValueError(message)
        evidence = FinalShapeEvidence.model_validate_json(
            evidence_path.read_text(encoding="utf-8-sig")
        )
        evidence_identity = (
            evidence.source_id,
            evidence.source_path,
            evidence.source_sha256,
            evidence.candidate_path,
            evidence.candidate_sha256,
        )
        artifact_identity = (
            artifact.source_id,
            artifact.review_source_path,
            artifact.review_source_sha256,
            artifact.review_candidate_path,
            artifact.review_candidate_sha256,
        )
        if evidence_identity != artifact_identity:
            message = "final-shape evidence belongs to a different review pair"
            raise ValueError(message)
        validate_final_shape_evidence(
            evidence,
            resolve_repo_path(self.repo_root, artifact.review_source_path),
            resolve_repo_path(self.repo_root, artifact.review_candidate_path),
        )

    def _validate_final_review(
        self,
        job: RepairJob,
        review: FinalReviewRecord,
    ) -> None:
        expected = (
            job.job_id,
            job.source_id,
            job.assigned_reviewer,
            job.review_source_sha256,
            job.review_candidate_sha256,
        )
        actual = (
            review.job_id,
            review.source_id,
            review.review_model,
            review.source_sha256,
            review.candidate_sha256,
        )
        if expected != actual:
            message = "final review does not match the assigned repair job"
            raise ValueError(message)
        if job.structure_evidence_sha256 is not None:
            if review.detailed_report_path is None:
                message = "final review does not bind its detailed report"
                raise ValueError(message)
            if (
                review.structure_evidence_sha256
                != job.structure_evidence_sha256
            ):
                message = "final review structure evidence does not match the job"
                raise ValueError(message)
            detailed_report_path = resolve_repo_path(
                self.repo_root,
                review.detailed_report_path,
            )
            if sha256_path(detailed_report_path) != review.detailed_report_sha256:
                message = "final review detailed report hash changed"
                raise ValueError(message)

    def _validate_promotion_candidate_locked(self, job: RepairJob) -> None:
        if job.state not in {
            PipelineState.PROMOTION_READY,
            PipelineState.PROMOTED,
        }:
            message = "job is not ready for promotion"
            raise ValueError(message)
        final_review = self._load_final_review(job)
        if final_review is None or final_review.verdict != "pass":
            message = "promotion candidate does not have a clean final review"
            raise ValueError(message)
        self._validate_final_review(job, final_review)

    def _reject_parallel_source_attempt(self, source_id: str) -> None:
        for job in self.list_jobs():
            if job.source_id == source_id and job.state not in TERMINAL_STATES:
                message = f"source already has an active repair attempt: {source_id}"
                raise ValueError(message)

    def _validate_source_reservation(
        self,
        source_id: str,
        intake_id: str | None,
    ) -> None:
        reservation = self.source_reservation(source_id)
        if reservation is None:
            if intake_id is not None:
                message = "repair references a missing source intake reservation"
                raise ValueError(message)
            return
        if intake_id != reservation.owner_id:
            message = f"source is reserved by an active intake: {source_id}"
            raise ValueError(message)

    def _write_initial_event(self, job: RepairJob, actor: str) -> None:
        event = PipelineEvent(
            event_id=uuid.uuid4().hex,
            job_id=job.job_id,
            sequence=1,
            idempotency_key="discovered",
            kind=EventKind.DISCOVERED,
            actor=actor,
            from_state=None,
            to_state=PipelineState.DISCOVERED,
            created_at=job.created_at,
            snapshot=job,
        )
        self._append_event(event)
        self._atomic_model(self._job_path(job.job_id), job)

    def _transition_locked(  # noqa: PLR0913
        self,
        job: RepairJob,
        *,
        state: PipelineState,
        kind: EventKind,
        actor: str,
        idempotency_key: str,
        duration_ms: int | None = None,
        reason: str | None = None,
    ) -> RepairJob:
        events = self._read_events(job.job_id)
        for event in events:
            if event.idempotency_key == idempotency_key:
                return event.snapshot
        self._validate_transition(job.state, state)
        now = _utc_now()
        next_job = _updated_job(
            job,
            state=state,
            updated_at=now,
            last_sequence=job.last_sequence + 1,
        )
        event = PipelineEvent(
            event_id=uuid.uuid4().hex,
            job_id=job.job_id,
            sequence=next_job.last_sequence,
            idempotency_key=idempotency_key,
            kind=kind,
            actor=actor,
            from_state=job.state,
            to_state=state,
            created_at=now,
            duration_ms=duration_ms,
            reason=reason,
            snapshot=next_job,
        )
        self._append_event(event)
        self._atomic_model(self._job_path(job.job_id), next_job)
        return next_job

    def _validate_transition(
        self,
        current: PipelineState,
        target: PipelineState,
    ) -> None:
        allowed: dict[PipelineState, frozenset[PipelineState]] = {
            PipelineState.DISCOVERED: frozenset({PipelineState.BRIDGE_VERIFIED}),
            PipelineState.BRIDGE_VERIFIED: frozenset({PipelineState.REPAIR_QUEUED}),
            PipelineState.REPAIR_QUEUED: frozenset(
                {
                    PipelineState.REPAIR_RUNNING,
                    PipelineState.BLOCKED,
                    PipelineState.FAILED_TERMINAL,
                }
            ),
            PipelineState.REPAIR_RUNNING: frozenset(
                {
                    PipelineState.CANDIDATE_VALIDATED,
                    PipelineState.REPAIR_QUEUED,
                    PipelineState.FAILED_RETRYABLE,
                    PipelineState.FAILED_TERMINAL,
                }
            ),
            PipelineState.CANDIDATE_VALIDATED: frozenset(
                {
                    PipelineState.CANDIDATE_VALIDATED,
                    PipelineState.REVIEW_QUEUED,
                    PipelineState.ISOLATED,
                }
            ),
            PipelineState.REVIEW_QUEUED: frozenset(
                {
                    PipelineState.REVIEW_QUEUED,
                    PipelineState.REVIEW_RUNNING,
                    PipelineState.BLOCKED,
                    PipelineState.ISOLATED,
                }
            ),
            PipelineState.REVIEW_RUNNING: frozenset(
                {
                    PipelineState.PROMOTION_READY,
                    PipelineState.ISOLATED,
                    PipelineState.REVIEW_QUEUED,
                    PipelineState.BLOCKED,
                }
            ),
            PipelineState.PROMOTION_READY: frozenset(
                {PipelineState.PROMOTED, PipelineState.ISOLATED}
            ),
            PipelineState.BLOCKED: frozenset(
                {PipelineState.REPAIR_QUEUED, PipelineState.REVIEW_QUEUED}
            ),
            PipelineState.FAILED_RETRYABLE: frozenset(
                {PipelineState.REPAIR_QUEUED}
            ),
            PipelineState.PROMOTED: frozenset(),
            PipelineState.ISOLATED: frozenset(),
            PipelineState.FAILED_TERMINAL: frozenset(),
        }
        if target not in allowed[current]:
            message = f"invalid pipeline transition: {current} -> {target}"
            raise ValueError(message)

    def _append_event(self, event: PipelineEvent) -> None:
        path = self._event_path(event.job_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        current = path.read_bytes() if path.is_file() else b""
        line = (event.model_dump_json() + "\n").encode("utf-8")
        temporary = path.with_suffix(path.suffix + f".{uuid.uuid4().hex}.tmp")
        _ = temporary.write_bytes(current + line)
        _ = temporary.replace(path)

    def _read_events(self, job_id: str) -> tuple[PipelineEvent, ...]:
        path = self._event_path(job_id)
        if not path.is_file():
            return ()
        events = tuple(
            PipelineEvent.model_validate_json(line)
            for line in path.read_text(encoding="utf-8-sig").splitlines()
            if line.strip()
        )
        for expected, event in enumerate(events, start=1):
            if event.sequence != expected:
                message = f"pipeline event sequence is discontinuous for {job_id}"
                raise ValueError(message)
        return events

    def _create_lease(
        self,
        job: RepairJob,
        stage: Literal["repair", "review"],
        worker_id: str,
    ) -> JobLease:
        path = self._lease_path(job.job_id)
        existing = self._load_lease(job.job_id)
        now = _utc_now()
        if existing is not None:
            if existing.expires_at > now:
                message = "job already has an active worker lease"
                raise ValueError(message)
            path.unlink(missing_ok=True)
        lease = JobLease(
            lease_id=uuid.uuid4().hex,
            job_id=job.job_id,
            stage=stage,
            worker_id=worker_id,
            acquired_at=now,
            heartbeat_at=now,
            expires_at=now + timedelta(seconds=self.policy.lease_seconds),
        )
        serialized = lease.model_dump_json(indent=2).encode("utf-8") + b"\n"
        try:
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
        except FileExistsError as exc:
            message = "job lease was claimed concurrently"
            raise ValueError(message) from exc
        try:
            _ = os.write(descriptor, serialized)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        return lease

    def _load_lease(self, job_id: str) -> JobLease | None:
        path = self._lease_path(job_id)
        if not path.is_file():
            return None
        return JobLease.model_validate_json(path.read_text(encoding="utf-8-sig"))

    def _require_lease(
        self,
        job: RepairJob,
        stage: Literal["repair", "review"],
        worker_id: str,
    ) -> JobLease:
        lease = self._load_lease(job.job_id)
        if lease is None:
            message = "running job has no worker lease"
            raise ValueError(message)
        if lease.stage != stage or lease.worker_id != worker_id:
            message = "worker does not own the required job lease"
            raise ValueError(message)
        if lease.expires_at <= _utc_now():
            message = "worker lease expired"
            raise ValueError(message)
        return lease

    def _remove_lease(self, job_id: str, worker_id: str) -> None:
        lease = self._load_lease(job_id)
        if lease is None:
            return
        if lease.worker_id != worker_id:
            message = "worker cannot release another worker's lease"
            raise ValueError(message)
        self._lease_path(job_id).unlink(missing_ok=True)

    @contextmanager
    def _lock(self, key: str) -> Generator[None, None, None]:
        path = self.locks_root / f"{key}.lock"
        token = uuid.uuid4().hex
        owner = LockOwner(
            token=token,
            pid=os.getpid(),
            acquired_at=_utc_now(),
        )
        serialized_owner = owner.model_dump_json().encode("utf-8")
        deadline = time.monotonic() + self.policy.lock_timeout_seconds
        while True:
            try:
                descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
            except (FileExistsError, PermissionError) as error:
                self._wait_for_lock(path, key, deadline, error)
                continue
            try:
                _ = os.write(descriptor, serialized_owner)
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            break
        try:
            yield
        finally:
            current_owner = self._load_lock_owner(path)
            if current_owner is not None and current_owner.token == token:
                path.unlink(missing_ok=True)

    def _wait_for_lock(
        self,
        path: Path,
        key: str,
        deadline: float,
        error: FileExistsError | PermissionError,
    ) -> None:
        """Wait or reclaim one contended cross-process lock."""
        if isinstance(error, PermissionError) and not path.exists():
            raise error
        try:
            age = time.time() - path.stat().st_mtime
        except FileNotFoundError:
            return
        except PermissionError:
            age = 0.0
        current_owner = self._load_lock_owner(path)
        reclaim = (
            current_owner is not None and not _pid_is_alive(current_owner.pid)
        ) or (
            current_owner is None
            and age > self.policy.stale_lock_seconds
        )
        if reclaim:
            try:
                path.unlink(missing_ok=True)
            except PermissionError:
                time.sleep(0.01)
            return
        if time.monotonic() >= deadline:
            message = f"timed out waiting for pipeline lock: {key}"
            raise TimeoutError(message) from None
        time.sleep(0.01)

    @staticmethod
    def _load_lock_owner(path: Path) -> LockOwner | None:
        try:
            return LockOwner.model_validate_json(
                path.read_text(encoding="utf-8-sig")
            )
        except (OSError, ValueError):
            return None

    def _atomic_model(self, path: Path, value: BaseModel) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + f".{uuid.uuid4().hex}.tmp")
        _ = temporary.write_text(
            value.model_dump_json(indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        delay = _ATOMIC_REPLACE_INITIAL_DELAY_SECONDS
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

    def _job_path(self, job_id: str) -> Path:
        return self.jobs_root / f"{job_id}.json"

    def _source_reservation_path(self, source_id: str) -> Path:
        return self.source_reservations_root / f"{sha256_text(source_id)}.json"

    def _event_path(self, job_id: str) -> Path:
        return self.events_root / f"{job_id}.jsonl"

    def _lease_path(self, job_id: str) -> Path:
        return self.leases_root / f"{job_id}.json"


def _updated_job(job: RepairJob, **updates: object) -> RepairJob:
    payload = job.model_dump(mode="python")
    payload.update(updates)
    return RepairJob.model_validate(payload)


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _pid_is_alive(pid: int) -> bool:
    """Return whether a local process still owns a coordination lock."""
    if os.name == "nt":
        process_query_limited_information = 0x1000
        error_access_denied = 5
        do_not_inherit_handle = 0
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        open_process = kernel32.OpenProcess
        open_process.argtypes = (
            ctypes.c_uint32,
            ctypes.c_int,
            ctypes.c_uint32,
        )
        open_process.restype = ctypes.c_void_p
        handle = cast(
            "int | None",
            open_process(
                process_query_limited_information,
                do_not_inherit_handle,
                pid,
            ),
        )
        if handle:
            close_handle = kernel32.CloseHandle
            close_handle.argtypes = (ctypes.c_void_p,)
            close_handle.restype = ctypes.c_int
            _ = cast("int", close_handle(handle))
            return True
        return ctypes.get_last_error() == error_access_denied
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _oldest_state_age_ms(
    jobs: tuple[RepairJob, ...],
    state: PipelineState,
    now: datetime,
) -> int:
    """Return the oldest current wait age for one state."""
    waiting = [job for job in jobs if job.state == state]
    if not waiting:
        return 0
    oldest = min(job.updated_at for job in waiting)
    return max(0, round((now - oldest).total_seconds() * 1000))


def _collect_event_interval(
    events: tuple[PipelineEvent, ...],
    start_kind: EventKind,
    end_kinds: frozenset[EventKind],
    output: list[int],
) -> None:
    """Append the latest matching start-to-end interval for one attempt."""
    end = next((event for event in reversed(events) if event.kind in end_kinds), None)
    if end is None:
        return
    start = next(
        (
            event
            for event in reversed(events)
            if event.kind == start_kind and event.sequence < end.sequence
        ),
        None,
    )
    if start is None:
        return
    elapsed = round((end.created_at - start.created_at).total_seconds() * 1000)
    output.append(max(0, elapsed))


def _timing_summary(values: list[int]) -> TimingSummary:
    """Return stable nearest-rank percentiles for non-negative milliseconds."""
    if not values:
        return TimingSummary(
            samples=0,
            total_ms=0,
            mean_ms=0,
            p50_ms=0,
            p95_ms=0,
            max_ms=0,
        )
    ordered = sorted(values)

    def percentile(fraction: float) -> int:
        index = max(0, ceil(len(ordered) * fraction) - 1)
        return ordered[index]

    total = sum(ordered)
    return TimingSummary(
        samples=len(ordered),
        total_ms=total,
        mean_ms=round(total / len(ordered)),
        p50_ms=percentile(0.5),
        p95_ms=percentile(0.95),
        max_ms=ordered[-1],
    )

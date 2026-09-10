# Copyright 2026

"""Continuous, idempotent control-plane reconciliation for the AI pipeline."""

from __future__ import annotations

import hashlib
import os
import time
import uuid
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from scripts.ai.pipeline import (
    PipelineState,
    PipelineStatus,
    PipelineStore,
    PromotionEvidence,
    RepairJob,
)
from scripts.ai.pipeline_adapters import (
    ingest_grok_final_review,
    ingest_targeted_fix,
    ingest_terra_final_review,
)
from scripts.ai.pipeline_intake import (
    AuditIntakeItem,
    AuditIntakeState,
    AuditIntakeStatus,
    AuditIntakeStore,
)
from scripts.ai.review_contract import (
    AssignedReviewer,
    resolve_repo_path,
    sha256_path,
    sha256_text,
)

if TYPE_CHECKING:
    from collections.abc import Callable

_ATOMIC_REPLACE_ATTEMPTS = 20
_ATOMIC_REPLACE_INITIAL_DELAY_SECONDS = 0.05
_ATOMIC_REPLACE_MAX_DELAY_SECONDS = 0.25


class DispatchStage(StrEnum):
    """Runnable control-plane stages."""

    AUDIT = "audit"
    BRIDGE = "bridge"
    REPAIR = "repair"
    REVIEW = "review"
    PROMOTION = "promotion"


class CompletionKind(StrEnum):
    """Completion envelopes accepted by the local dispatcher inbox."""

    DEEP_AUDIT = "deep_audit"
    REPAIR = "repair"
    REPAIR_FAILURE = "repair_failure"
    GROK_REVIEW = "grok_review"
    TERRA_REVIEW = "terra_review"
    PROMOTION = "promotion"


class _StrictModel(BaseModel):
    """Immutable dispatcher record base."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )


class CompletionEnvelope(_StrictModel):
    """One idempotent request to absorb a completed external stage."""

    version: Literal[1] = 1
    completion_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{0,119}$")
    kind: CompletionKind
    job_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    worker_id: str = Field(min_length=1, max_length=120)
    artifact_path: str | None = Field(default=None, min_length=1)
    materialized_manifest_path: str | None = Field(default=None, min_length=1)
    report_path: str | None = Field(default=None, min_length=1)
    status_path: str | None = Field(default=None, min_length=1)
    evidence_path: str | None = Field(default=None, min_length=1)
    failure_reason: str | None = Field(default=None, min_length=1, max_length=500)
    retryable: bool | None = None
    invalid_attempt_count: int = Field(default=0, ge=0)
    duration_ms: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _paths_match_completion_kind(self) -> Self:
        required: dict[CompletionKind, tuple[str, ...]] = {
            CompletionKind.DEEP_AUDIT: ("report_path",),
            CompletionKind.REPAIR: (
                "artifact_path",
                "materialized_manifest_path",
            ),
            CompletionKind.REPAIR_FAILURE: (),
            CompletionKind.GROK_REVIEW: ("report_path", "status_path"),
            CompletionKind.TERRA_REVIEW: ("report_path",),
            CompletionKind.PROMOTION: ("evidence_path",),
        }
        populated = {
            name
            for name in (
                "artifact_path",
                "materialized_manifest_path",
                "report_path",
                "status_path",
                "evidence_path",
            )
            if getattr(self, name) is not None
        }
        expected = set(required[self.kind])
        if populated != expected:
            message = (
                f"{self.kind} completion requires exactly "
                f"{', '.join(sorted(expected))}"
            )
            raise ValueError(message)
        if (
            self.kind != CompletionKind.TERRA_REVIEW
            and self.invalid_attempt_count
        ):
            message = "invalid review attempts only apply to Terra completions"
            raise ValueError(message)
        failure_fields = (self.failure_reason, self.retryable)
        if self.kind == CompletionKind.REPAIR_FAILURE:
            if any(value is None for value in failure_fields):
                message = "repair failure completion requires reason and retryability"
                raise ValueError(message)
        elif any(value is not None for value in failure_fields):
            message = "failure fields only apply to repair failure completions"
            raise ValueError(message)
        if (
            self.kind == CompletionKind.DEEP_AUDIT
            and self.duration_ms is None
        ):
            message = "deep-audit completion requires model duration"
            raise ValueError(message)
        if (
            self.kind != CompletionKind.DEEP_AUDIT
            and self.duration_ms is not None
        ):
            message = "completion duration only applies to deep audits"
            raise ValueError(message)
        return self


class DispatchAction(_StrictModel):
    """One stable, deduplicated stage action available to a worker."""

    version: Literal[1] = 1
    action_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    stage: DispatchStage
    job_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_id: str = Field(min_length=1)
    candidate_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    lane: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{0,79}$")
    assigned_reviewer: AssignedReviewer
    expected_state: PipelineState | AuditIntakeState
    created_at: datetime

    @model_validator(mode="after")
    def _identity_is_stable(self) -> Self:
        expected = action_id_for(
            self.source_id,
            self.candidate_sha256,
            self.lane,
            self.stage,
        )
        if self.action_id != expected:
            message = "dispatch action id does not match its stable identity"
            raise ValueError(message)
        return self


class DispatchClaim(_StrictModel):
    """Result of an atomic claim-next operation."""

    version: Literal[1] = 1
    claimed: bool
    action: DispatchAction | None = None
    job: RepairJob | AuditIntakeItem | None = None

    @model_validator(mode="after")
    def _claim_fields_are_consistent(self) -> Self:
        if self.claimed != (self.action is not None and self.job is not None):
            message = "dispatch claim flag does not match its payload"
            raise ValueError(message)
        return self


class DispatcherSnapshot(_StrictModel):
    """One reconciler cycle with queue and idempotency evidence."""

    version: Literal[1] = 1
    generated_at: datetime
    processed_completion_ids: tuple[str, ...]
    rejected_completion_ids: tuple[str, ...]
    recovered_job_ids: tuple[str, ...]
    recovered_intake_ids: tuple[str, ...]
    routed_intake_ids: tuple[str, ...]
    queued_review_job_ids: tuple[str, ...]
    actions: tuple[DispatchAction, ...]
    bridge_due: bool
    promotion_due: bool
    status: PipelineStatus
    intake_status: AuditIntakeStatus


class RejectedCompletionRecord(_StrictModel):
    """Reasoned evidence for one completion the dispatcher could not absorb."""

    version: Literal[1] = 1
    rejection_id: str = Field(pattern=r"^[0-9a-f]{32}$")
    completion_id: str = Field(min_length=1, max_length=120)
    archived_envelope_path: str = Field(min_length=1)
    archived_envelope_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    error_type: str = Field(min_length=1, max_length=120)
    error_message: str = Field(min_length=1, max_length=1000)
    retryable: bool
    rejected_at: datetime


class DispatcherRuntimeRecord(_StrictModel):
    """Immutable code contract for one dispatcher process instance."""

    version: Literal[1] = 1
    instance_id: str = Field(pattern=r"^[0-9a-f]{32}$")
    process_id: int = Field(ge=1)
    code_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    supported_review_workflow_versions: tuple[Literal[2, 3], ...] = (2, 3)
    completion_envelope_version: Literal[1] = 1
    started_at: datetime


class DispatcherAutomationFailureRecord(_StrictModel):
    """One local automation callback failure isolated from the durable loop."""

    version: Literal[1] = 1
    failure_id: str = Field(pattern=r"^[0-9a-f]{32}$")
    stage: Literal["admission", "bridge", "promotion"]
    error_type: str = Field(min_length=1, max_length=120)
    error_message: str = Field(min_length=1, max_length=1000)
    retryable: bool
    failed_at: datetime


def action_id_for(
    source_id: str,
    candidate_sha256: str,
    lane: str,
    stage: DispatchStage,
) -> str:
    """Return the required active-run registry key."""
    return sha256_text(
        f"{source_id}\0{candidate_sha256}\0{lane}\0{stage.value}"
    )


class PipelineDispatcher:
    """Reconcile completed envelopes and publish unique runnable actions."""

    def __init__(self, store: PipelineStore) -> None:
        """Initialize dispatcher directories without launching provider work."""
        self.store: PipelineStore = store
        self.intake: AuditIntakeStore = AuditIntakeStore(store)
        self.root: Path = store.root / "dispatcher"
        self.inbox_root: Path = self.root / "inbox"
        self.processed_root: Path = self.root / "processed"
        self.rejected_root: Path = self.root / "rejected"
        self.rejection_records_root: Path = self.root / "rejection-records"
        self.actions_root: Path = self.root / "actions"
        self.archived_actions_root: Path = self.root / "archived-actions"
        self.runtime_root: Path = self.root / "runtime"
        self.automation_failures_root: Path = self.root / "automation-failures"
        for path in (
            self.inbox_root,
            self.processed_root,
            self.rejected_root,
            self.rejection_records_root,
            self.actions_root,
            self.archived_actions_root,
            self.runtime_root,
            self.automation_failures_root,
        ):
            path.mkdir(parents=True, exist_ok=True)
        self.runtime = DispatcherRuntimeRecord(
            instance_id=uuid.uuid4().hex,
            process_id=os.getpid(),
            code_sha256=_dispatcher_code_sha256(),
            started_at=datetime.now(UTC),
        )
        _atomic_model(
            self.runtime_root / f"{self.runtime.instance_id}.json",
            self.runtime,
        )

    def reconcile(
        self,
        *,
        route_completed_audits: bool = True,
    ) -> DispatcherSnapshot:
        """Run one ingestion-first, idempotent dispatcher cycle."""
        self._require_current_runtime()
        with self.store.coordinator_lock("dispatcher"):
            processed, rejected = self._ingest_inbox()
            recovered = self.store.recover_expired_leases()
            recovered_intake = self.intake.recover_expired_leases()
            routed_intake = (
                self.intake.route_completed_audits()
                if route_completed_audits
                else ()
            )
            queued = self.store.enqueue_waiting_reviews()
            actions = self._sync_actions()
            status = self.store.status()
            intake_status = self.intake.status()
            promotion_due = (
                status.promotion_ready >= self.store.policy.promotion_batch_size
                or status.oldest_promotion_ready_ms
                >= self.store.policy.promotion_batch_max_wait_seconds * 1000
                or intake_status.clean_adoption_ready
                >= self.store.policy.promotion_batch_size
                or intake_status.oldest_clean_adoption_ready_ms
                >= self.store.policy.promotion_batch_max_wait_seconds * 1000
            )
            return DispatcherSnapshot(
                generated_at=datetime.now(UTC),
                processed_completion_ids=processed,
                rejected_completion_ids=rejected,
                recovered_job_ids=tuple(job.job_id for job in recovered),
                recovered_intake_ids=tuple(
                    item.intake_id for item in recovered_intake
                ),
                routed_intake_ids=tuple(
                    item.intake_id for item in routed_intake
                ),
                queued_review_job_ids=tuple(job.job_id for job in queued),
                actions=actions,
                bridge_due=intake_status.bridge_backlog > 0,
                promotion_due=promotion_due,
                status=status,
                intake_status=intake_status,
            )

    def submit_completion(
        self,
        envelope: CompletionEnvelope,
    ) -> CompletionEnvelope:
        """Atomically submit one completion while preserving idempotency."""
        self._require_current_runtime()
        lock_name = f"completion-{sha256_text(envelope.completion_id)}"
        with self.store.coordinator_lock(lock_name):
            processed_path = self.processed_root / f"{envelope.completion_id}.json"
            if processed_path.is_file():
                existing = CompletionEnvelope.model_validate_json(
                    processed_path.read_text(encoding="utf-8-sig")
                )
                if existing != envelope:
                    message = "completion id already belongs to different evidence"
                    raise ValueError(message)
                return existing
            path = self.inbox_root / f"{envelope.completion_id}.json"
            if path.is_file():
                existing = CompletionEnvelope.model_validate_json(
                    path.read_text(encoding="utf-8-sig")
                )
                if existing != envelope:
                    message = "completion id already belongs to different evidence"
                    raise ValueError(message)
                return existing
            _atomic_model(path, envelope)
            return envelope

    def _require_current_runtime(self) -> None:
        """Stop before consuming work when on-disk dispatcher code changed."""
        if _dispatcher_code_sha256() != self.runtime.code_sha256:
            message = (
                "dispatcher code changed after process startup; restart the "
                "dispatcher before consuming pipeline work"
            )
            raise RuntimeError(message)

    def claim_next(
        self,
        stage: DispatchStage,
        lane: str,
        worker_id: str,
    ) -> DispatchClaim:
        """Atomically claim the oldest compatible repair or review action."""
        _ = self.reconcile()
        if stage == DispatchStage.PROMOTION:
            message = "promotion actions require explicit gate evidence"
            raise ValueError(message)
        with self.store.coordinator_lock("dispatcher-claim"):
            if stage in {DispatchStage.AUDIT, DispatchStage.BRIDGE}:
                for item in self.intake.list_items():
                    if not _matches_intake_lane(item, stage, lane):
                        continue
                    action = self._action_for_intake(item)
                    try:
                        claimed_intake = (
                            self.intake.claim_audit(
                                item.intake_id,
                                worker_id,
                            )
                            if stage == DispatchStage.AUDIT
                            else self.intake.claim_bridge(
                                item.intake_id,
                                worker_id,
                            )
                        )
                    except ValueError:
                        continue
                    self._archive_action(action.action_id)
                    return DispatchClaim(
                        claimed=True,
                        action=action,
                        job=claimed_intake,
                    )
                return DispatchClaim(claimed=False)
            for job in self.store.list_jobs():
                if not _matches_lane(job, stage, lane):
                    continue
                action = self._action_for_job(job)
                try:
                    claimed = (
                        self.store.claim_repair(job.job_id, worker_id)
                        if stage == DispatchStage.REPAIR
                        else self.store.claim_review(job.job_id, worker_id)
                    )
                except ValueError:
                    continue
                self._archive_action(action.action_id)
                return DispatchClaim(
                    claimed=True,
                    action=action,
                    job=claimed,
                )
        return DispatchClaim(claimed=False)

    def run(  # noqa: PLR0913
        self,
        *,
        poll_seconds: float = 2.0,
        max_cycles: int | None = None,
        on_admission_cycle: Callable[[], object] | None = None,
        on_promotion_due: Callable[[], object] | None = None,
        auto_bridge: bool = False,
        review_only_audit: bool = False,
    ) -> DispatcherSnapshot:
        """Continuously reconcile and optionally execute due promotion batches."""
        if poll_seconds <= 0:
            message = "dispatcher poll interval must be positive"
            raise ValueError(message)
        if max_cycles is not None and max_cycles < 1:
            message = "bounded dispatcher runs require at least one cycle"
            raise ValueError(message)
        if review_only_audit and (
            auto_bridge
            or on_admission_cycle is not None
            or on_promotion_due is not None
        ):
            message = (
                "review-only audit dispatch cannot admit, bridge, or promote"
            )
            raise ValueError(message)
        cycle = 0
        snapshot = self._reconcile_with_automation(
            on_admission_cycle,
            on_promotion_due,
            auto_bridge=auto_bridge,
            review_only_audit=review_only_audit,
        )
        while max_cycles is None or cycle + 1 < max_cycles:
            time.sleep(poll_seconds)
            snapshot = self._reconcile_with_automation(
                on_admission_cycle,
                on_promotion_due,
                auto_bridge=auto_bridge,
                review_only_audit=review_only_audit,
            )
            cycle += 1
        return snapshot

    def _reconcile_with_automation(
        self,
        on_admission_cycle: Callable[[], object] | None,
        on_promotion_due: Callable[[], object] | None,
        *,
        auto_bridge: bool,
        review_only_audit: bool,
    ) -> DispatcherSnapshot:
        """Reconcile once and consume safe bridge and promotion work."""
        snapshot = self.reconcile(
            route_completed_audits=not review_only_audit,
        )
        if on_admission_cycle is not None:
            try:
                _ = on_admission_cycle()
            except Exception as error:  # noqa: BLE001
                self._record_automation_failure("admission", error)
            snapshot = self.reconcile(
                route_completed_audits=not review_only_audit,
            )
        if snapshot.bridge_due and auto_bridge:
            try:
                self._drain_ready_bridges()
            except Exception as error:  # noqa: BLE001
                self._record_automation_failure("bridge", error)
            snapshot = self.reconcile(
                route_completed_audits=not review_only_audit,
            )
        if snapshot.promotion_due and on_promotion_due is not None:
            try:
                _ = on_promotion_due()
            except Exception as error:  # noqa: BLE001
                self._record_automation_failure("promotion", error)
            snapshot = self.reconcile(
                route_completed_audits=not review_only_audit,
            )
        return snapshot

    def _record_automation_failure(
        self,
        stage: Literal["admission", "bridge", "promotion"],
        error: Exception,
    ) -> DispatcherAutomationFailureRecord:
        """Persist a bounded local diagnosis without terminating reconciliation."""
        record = DispatcherAutomationFailureRecord(
            failure_id=uuid.uuid4().hex,
            stage=stage,
            error_type=type(error).__name__,
            error_message=(str(error) or type(error).__name__)[:1000],
            retryable=isinstance(error, OSError),
            failed_at=datetime.now(UTC),
        )
        _atomic_model(
            self.automation_failures_root / f"{record.failure_id}.json",
            record,
        )
        return record

    def _drain_ready_bridges(self) -> None:
        """Run bounded local-only bridges without launching a model."""
        for _index in range(self.store.policy.bridge_parallelism):
            claim = self.claim_next(
                DispatchStage.BRIDGE,
                "bridge",
                "dispatcher-bridge",
            )
            if not claim.claimed or claim.action is None:
                return
            try:
                _ = self.intake.complete_bridge(
                    claim.action.job_id,
                    "dispatcher-bridge",
                )
            except ValueError as error:
                _ = self.intake.block(
                    claim.action.job_id,
                    actor="dispatcher-bridge",
                    reason=str(error),
                    invalid=True,
                )

    def _ingest_inbox(self) -> tuple[tuple[str, ...], tuple[str, ...]]:
        processed: list[str] = []
        rejected: list[str] = []
        for path in sorted(self.inbox_root.glob("*.json")):
            try:
                envelope = CompletionEnvelope.model_validate_json(
                    path.read_text(encoding="utf-8-sig")
                )
            except (OSError, ValueError) as error:
                archived = self._archive(path, self.rejected_root, path.stem)
                self._record_rejection(
                    archived,
                    completion_id=(path.stem[:120] or "unknown"),
                    error=error,
                )
                rejected.append(path.stem)
                continue
            processed_path = self.processed_root / f"{envelope.completion_id}.json"
            if processed_path.is_file():
                _ = self._archive(
                    path,
                    self.processed_root / "duplicates",
                    path.stem,
                )
                processed.append(envelope.completion_id)
                continue
            try:
                _ = self._process_completion(envelope)
            except (OSError, ValueError) as error:
                archived = self._archive(
                    path,
                    self.rejected_root,
                    envelope.completion_id,
                )
                self._record_rejection(
                    archived,
                    completion_id=envelope.completion_id,
                    error=error,
                )
                rejected.append(envelope.completion_id)
                continue
            _ = self._archive(
                path,
                self.processed_root,
                envelope.completion_id,
            )
            processed.append(envelope.completion_id)
        return tuple(processed), tuple(rejected)

    def _process_completion(
        self,
        envelope: CompletionEnvelope,
    ) -> RepairJob | AuditIntakeItem:
        if envelope.kind == CompletionKind.DEEP_AUDIT:
            if envelope.duration_ms is None:
                message = "deep-audit completion lost its duration"
                raise ValueError(message)
            return self.intake.complete_audit(
                envelope.job_id,
                envelope.worker_id,
                _required(envelope.report_path),
                duration_ms=envelope.duration_ms,
            )
        if envelope.kind == CompletionKind.REPAIR:
            return ingest_targeted_fix(
                self.store,
                job_id=envelope.job_id,
                worker_id=envelope.worker_id,
                artifact_path_value=_required(envelope.artifact_path),
                materialized_manifest_path_value=_required(
                    envelope.materialized_manifest_path
                ),
            )
        if envelope.kind == CompletionKind.REPAIR_FAILURE:
            if envelope.retryable is None:
                message = "repair failure completion retryability is incomplete"
                raise ValueError(message)
            return self.store.fail_repair(
                envelope.job_id,
                envelope.worker_id,
                reason=_required(envelope.failure_reason),
                retryable=envelope.retryable,
            )
        if envelope.kind == CompletionKind.GROK_REVIEW:
            return ingest_grok_final_review(
                self.store,
                job_id=envelope.job_id,
                worker_id=envelope.worker_id,
                report_path_value=_required(envelope.report_path),
                status_path_value=_required(envelope.status_path),
            )
        if envelope.kind == CompletionKind.TERRA_REVIEW:
            return ingest_terra_final_review(
                self.store,
                job_id=envelope.job_id,
                worker_id=envelope.worker_id,
                report_path_value=_required(envelope.report_path),
                invalid_attempt_count=envelope.invalid_attempt_count,
            )
        evidence_path = _required(envelope.evidence_path)
        evidence = PromotionEvidence.model_validate_json(
            resolve_repo_path(self.store.repo_root, evidence_path).read_text(
                encoding="utf-8-sig"
            )
        )
        if evidence.job_id != envelope.job_id:
            message = "promotion completion belongs to a different job"
            raise ValueError(message)
        return self.store.promote(
            envelope.job_id,
            evidence_path,
            actor=envelope.worker_id,
        )

    def _sync_actions(self) -> tuple[DispatchAction, ...]:
        self._archive_stale_actions()
        actions = [
            *self._sync_intake_actions(),
            *self._sync_job_actions(),
        ]
        return tuple(sorted(actions, key=_action_sort_key))

    def _archive_stale_actions(self) -> None:
        """Remove actions whose immutable work item has moved on."""
        for path in sorted(self.actions_root.glob("*.json")):
            try:
                action = DispatchAction.model_validate_json(
                    path.read_text(encoding="utf-8-sig")
                )
                current_state = (
                    self.intake.load(action.job_id).state
                    if action.stage
                    in {DispatchStage.AUDIT, DispatchStage.BRIDGE}
                    else self.store.load_job(action.job_id).state
                )
            except (OSError, ValueError):
                self._archive_action(path.stem)
                continue
            if current_state != action.expected_state:
                self._archive_action(action.action_id)

    def _sync_intake_actions(self) -> tuple[DispatchAction, ...]:
        """Publish audit and bridge work without duplicating active sources."""
        intake_status = self.intake.status()
        actions: list[DispatchAction] = []
        for item in self.intake.list_items():
            if (
                item.state == AuditIntakeState.AUDIT_QUEUED
                and intake_status.backpressure
            ):
                continue
            if item.state not in {
                AuditIntakeState.AUDIT_QUEUED,
                AuditIntakeState.BRIDGE_QUEUED,
            }:
                continue
            action = self._action_for_intake(item)
            path = self.actions_root / f"{action.action_id}.json"
            if path.is_file():
                action = DispatchAction.model_validate_json(
                    path.read_text(encoding="utf-8-sig")
                )
            else:
                _atomic_model(path, action)
            actions.append(action)
        return tuple(actions)

    def _sync_job_actions(self) -> tuple[DispatchAction, ...]:
        """Publish repair, final-review, and promotion work."""
        status = self.store.status()
        actions: list[DispatchAction] = []
        for job in self.store.list_jobs():
            if (
                job.state == PipelineState.REPAIR_QUEUED
                and status.review_backpressure
            ):
                continue
            if job.state not in {
                PipelineState.REPAIR_QUEUED,
                PipelineState.REVIEW_QUEUED,
                PipelineState.PROMOTION_READY,
            }:
                continue
            action = self._action_for_job(job)
            path = self.actions_root / f"{action.action_id}.json"
            if path.is_file():
                action = DispatchAction.model_validate_json(
                    path.read_text(encoding="utf-8-sig")
                )
            else:
                _atomic_model(path, action)
            actions.append(action)
        return tuple(actions)

    def _action_for_intake(
        self,
        item: AuditIntakeItem,
    ) -> DispatchAction:
        stage, lane, candidate_sha256 = _intake_action_identity(item)
        action_id = action_id_for(
            item.source_id,
            candidate_sha256,
            lane,
            stage,
        )
        path = self.actions_root / f"{action_id}.json"
        if path.is_file():
            return DispatchAction.model_validate_json(
                path.read_text(encoding="utf-8-sig")
            )
        return DispatchAction(
            action_id=action_id,
            stage=stage,
            job_id=item.intake_id,
            source_id=item.source_id,
            candidate_sha256=candidate_sha256,
            lane=lane,
            assigned_reviewer=item.assigned_reviewer,
            expected_state=item.state,
            created_at=datetime.now(UTC),
        )

    def _action_for_job(self, job: RepairJob) -> DispatchAction:
        stage, lane, candidate_sha256 = _job_action_identity(job)
        action_id = action_id_for(
            job.source_id,
            candidate_sha256,
            lane,
            stage,
        )
        path = self.actions_root / f"{action_id}.json"
        if path.is_file():
            return DispatchAction.model_validate_json(
                path.read_text(encoding="utf-8-sig")
            )
        return DispatchAction(
            action_id=action_id,
            stage=stage,
            job_id=job.job_id,
            source_id=job.source_id,
            candidate_sha256=candidate_sha256,
            lane=lane,
            assigned_reviewer=job.assigned_reviewer,
            expected_state=job.state,
            created_at=datetime.now(UTC),
        )

    def _archive_action(self, action_id: str) -> None:
        path = self.actions_root / f"{action_id}.json"
        try:
            if path.is_file():
                _ = self._archive(
                    path,
                    self.archived_actions_root,
                    action_id,
                )
        except FileNotFoundError:
            # A concurrent claim may archive the same derived action after
            # the existence check. The work item transition is authoritative.
            return

    def _record_rejection(
        self,
        archived_path: Path,
        *,
        completion_id: str,
        error: OSError | ValueError,
    ) -> None:
        """Persist a secret-free, retry-aware rejection diagnosis."""
        rejection = RejectedCompletionRecord(
            rejection_id=uuid.uuid4().hex,
            completion_id=completion_id,
            archived_envelope_path=archived_path.relative_to(
                self.store.repo_root
            ).as_posix(),
            archived_envelope_sha256=sha256_path(archived_path),
            error_type=type(error).__name__,
            error_message=(str(error) or type(error).__name__)[:1000],
            retryable=isinstance(error, OSError),
            rejected_at=datetime.now(UTC),
        )
        path = self.rejection_records_root / f"{rejection.rejection_id}.json"
        _atomic_model(path, rejection)

    @staticmethod
    def _archive(path: Path, root: Path, name: str) -> Path:
        root.mkdir(parents=True, exist_ok=True)
        target = root / f"{name}.json"
        if target.exists():
            target = root / f"{name}.{uuid.uuid4().hex}.json"
        _replace_with_retry(path, target)
        return target


def _job_action_identity(
    job: RepairJob,
) -> tuple[DispatchStage, str, str]:
    if job.state == PipelineState.REPAIR_QUEUED:
        return DispatchStage.REPAIR, job.provider, job.base_candidate_sha256
    if job.state == PipelineState.REVIEW_QUEUED:
        return (
            DispatchStage.REVIEW,
            job.assigned_reviewer,
            _required(job.review_candidate_sha256),
        )
    if job.state == PipelineState.PROMOTION_READY:
        return (
            DispatchStage.PROMOTION,
            "site-gate",
            _required(job.output_sha256),
        )
    message = f"job state has no dispatch action: {job.state}"
    raise ValueError(message)


def _intake_action_identity(
    item: AuditIntakeItem,
) -> tuple[DispatchStage, str, str]:
    if item.state == AuditIntakeState.AUDIT_QUEUED:
        return (
            DispatchStage.AUDIT,
            item.assigned_reviewer,
            item.candidate_sha256,
        )
    if item.state == AuditIntakeState.BRIDGE_QUEUED:
        return (
            DispatchStage.BRIDGE,
            "bridge",
            item.normalized_candidate_sha256,
        )
    message = f"intake state has no dispatch action: {item.state}"
    raise ValueError(message)


def _matches_lane(
    job: RepairJob,
    stage: DispatchStage,
    lane: str,
) -> bool:
    if stage == DispatchStage.REPAIR:
        return job.state == PipelineState.REPAIR_QUEUED and job.provider == lane
    if stage == DispatchStage.REVIEW:
        return (
            job.state == PipelineState.REVIEW_QUEUED
            and job.assigned_reviewer == lane
        )
    return False


def _matches_intake_lane(
    item: AuditIntakeItem,
    stage: DispatchStage,
    lane: str,
) -> bool:
    if stage == DispatchStage.AUDIT:
        return (
            item.state == AuditIntakeState.AUDIT_QUEUED
            and item.assigned_reviewer == lane
        )
    if stage == DispatchStage.BRIDGE:
        return (
            item.state == AuditIntakeState.BRIDGE_QUEUED
            and lane == "bridge"
        )
    return False


def _action_sort_key(action: DispatchAction) -> tuple[int, datetime, str]:
    priority = {
        DispatchStage.PROMOTION: 0,
        DispatchStage.BRIDGE: 1,
        DispatchStage.REVIEW: 2,
        DispatchStage.REPAIR: 3,
        DispatchStage.AUDIT: 4,
    }[action.stage]
    return priority, action.created_at, action.action_id


def _atomic_model(path: Path, value: BaseModel) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".{uuid.uuid4().hex}.tmp")
    try:
        _ = temporary.write_text(
            value.model_dump_json(indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        _replace_with_retry(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _replace_with_retry(source: Path, target: Path) -> None:
    """Replace one file despite transient Windows reader sharing violations."""
    delay = _ATOMIC_REPLACE_INITIAL_DELAY_SECONDS
    for attempt in range(_ATOMIC_REPLACE_ATTEMPTS):
        try:
            _ = source.replace(target)
        except PermissionError:
            if attempt + 1 == _ATOMIC_REPLACE_ATTEMPTS:
                raise
            time.sleep(delay)
            delay = min(delay * 2, _ATOMIC_REPLACE_MAX_DELAY_SECONDS)
        else:
            return


def _dispatcher_code_sha256() -> str:
    """Hash the complete local AI control-plane Python source tree."""
    digest = hashlib.sha256()
    source_root = Path(__file__).resolve().parent
    for path in sorted(source_root.glob("*.py")):
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _required(value: str | None) -> str:
    if value is None:
        message = "dispatcher completion provenance is incomplete"
        raise ValueError(message)
    return value

# Copyright 2026

"""First-class deep-audit and repair-bridge intake for the AI pipeline."""

from __future__ import annotations

import os
import time
import uuid
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from math import ceil
from typing import TYPE_CHECKING, ClassVar, Final, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from scripts.ai.audit_bridge import (
    DeepAuditManifest,
    DeepAuditManifestEntry,
    bridge_and_queue_deep_audit,
    bridge_deep_audit_report,
    validate_deep_audit_report,
)
from scripts.ai.pipeline import (
    PipelineState,
    PipelineStore,
    Provider,
    ProviderModel,
    TimingSummary,
)
from scripts.ai.review_contract import (
    AssignedReviewer,
    resolve_repo_path,
    sha256_path,
    sha256_text,
)

if TYPE_CHECKING:
    from contextlib import AbstractContextManager
    from pathlib import Path

_ATOMIC_REPLACE_ATTEMPTS: Final = 8
_ATOMIC_REPLACE_INITIAL_DELAY_SECONDS: Final = 0.01


class AuditIntakeState(StrEnum):
    """Lifecycle states before a page enters targeted repair."""

    AUDIT_QUEUED = "audit_queued"
    AUDIT_RUNNING = "audit_running"
    AUDIT_COMPLETE = "audit_complete"
    BRIDGE_QUEUED = "bridge_queued"
    BRIDGE_RUNNING = "bridge_running"
    BRIDGE_VERIFIED = "bridge_verified"
    QUEUED_TO_REPAIR = "queued_to_repair"
    CLEAN_ADOPTION_READY = "clean_adoption_ready"
    CLEAN_ADOPTED = "clean_adopted"
    STRUCTURAL_BLOCKED = "structural_blocked"
    INVALID = "invalid"


class AuditIntakeEventKind(StrEnum):
    """Append-only event names for audit and bridge work."""

    AUDIT_QUEUED = "audit_queued"
    AUDIT_CLAIMED = "audit_claimed"
    AUDIT_RECOVERED = "audit_recovered"
    AUDIT_COMPLETED = "audit_completed"
    BRIDGE_QUEUED = "bridge_queued"
    BRIDGE_CLAIMED = "bridge_claimed"
    BRIDGE_RECOVERED = "bridge_recovered"
    BRIDGE_VERIFIED = "bridge_verified"
    REPAIR_QUEUED = "repair_queued"
    CLEAN_ADOPTION_READY = "clean_adoption_ready"
    CLEAN_ADOPTED = "clean_adopted"
    STRUCTURAL_BLOCKED = "structural_blocked"
    INVALID = "invalid"


_TERMINAL_INTAKE_STATES: Final[frozenset[AuditIntakeState]] = frozenset(
    {
        AuditIntakeState.QUEUED_TO_REPAIR,
        AuditIntakeState.CLEAN_ADOPTED,
        AuditIntakeState.STRUCTURAL_BLOCKED,
        AuditIntakeState.INVALID,
    }
)


class _StrictModel(BaseModel):
    """Immutable audit-intake record base."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )


class AuditIntakeSpec(_StrictModel):
    """Operator input for one immutable assigned deep audit."""

    version: Literal[1] = 1
    source_id: str = Field(min_length=1)
    manifest_path: str = Field(min_length=1)
    assigned_reviewer: AssignedReviewer
    provider: Provider
    attempt_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{0,79}$")


class CleanAdoptionEvidence(_StrictModel):
    """Hash-bound proof for one clean audited page adopted without repair."""

    version: Literal[1] = 1
    intake_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_id: str
    assigned_reviewer: AssignedReviewer
    audit_report_path: str
    audit_report_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    target_path: str
    target_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    public_source_path: str
    public_source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    public_candidate_path: str
    public_candidate_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    gate_log_path: str
    gate_log_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    page_tests: bool
    typecheck: bool
    lint: bool
    materialization: bool
    build: bool
    routes: bool
    recorded_at: datetime


class AuditIntakeItem(_StrictModel):
    """Materialized snapshot for one audit-to-repair intake."""

    version: Literal[1] = 1
    intake_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_id: str
    manifest_path: str
    manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    english_path: str
    chinese_path: str
    normalized_candidate_path: str
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    candidate_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    normalized_candidate_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    assigned_reviewer: AssignedReviewer
    provider: Provider
    provider_model: ProviderModel
    attempt_id: str
    state: AuditIntakeState
    created_at: datetime
    updated_at: datetime
    last_sequence: int = Field(ge=1)
    audit_report_path: str | None = None
    audit_report_sha256: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )
    audit_verdict: Literal["pass", "warn", "fail"] | None = None
    repair_review_path: str | None = None
    repair_review_sha256: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )
    repair_job_id: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )
    adoption_evidence_path: str | None = None
    adoption_evidence_sha256: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )
    terminal_reason: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def _identity_and_evidence_are_consistent(self) -> Self:
        expected = intake_id_for(
            self.source_id,
            self.source_sha256,
            self.candidate_sha256,
            self.assigned_reviewer,
        )
        if self.intake_id != expected:
            message = "audit intake id does not match immutable inputs"
            raise ValueError(message)
        expected_model: ProviderModel = (
            "k3" if self.provider == "kimi" else "glm-5.2"
        )
        if self.provider_model != expected_model:
            message = "audit intake provider/model routing is inconsistent"
            raise ValueError(message)
        audit_fields = (
            self.audit_report_path,
            self.audit_report_sha256,
            self.audit_verdict,
        )
        if any(value is not None for value in audit_fields) and not all(
            value is not None for value in audit_fields
        ):
            message = "audit report provenance is incomplete"
            raise ValueError(message)
        repair_fields = (
            self.repair_review_path,
            self.repair_review_sha256,
            self.repair_job_id,
        )
        if any(value is not None for value in repair_fields) and not all(
            value is not None for value in repair_fields
        ):
            message = "repair bridge provenance is incomplete"
            raise ValueError(message)
        adoption_fields = (
            self.adoption_evidence_path,
            self.adoption_evidence_sha256,
        )
        if any(value is not None for value in adoption_fields) and not all(
            value is not None for value in adoption_fields
        ):
            message = "clean adoption provenance is incomplete"
            raise ValueError(message)
        if self.state in {
            AuditIntakeState.AUDIT_COMPLETE,
            AuditIntakeState.BRIDGE_QUEUED,
            AuditIntakeState.BRIDGE_RUNNING,
            AuditIntakeState.BRIDGE_VERIFIED,
            AuditIntakeState.QUEUED_TO_REPAIR,
            AuditIntakeState.CLEAN_ADOPTION_READY,
            AuditIntakeState.CLEAN_ADOPTED,
        } and self.audit_report_path is None:
            message = "post-audit intake state lacks report provenance"
            raise ValueError(message)
        if self.state in {
            AuditIntakeState.BRIDGE_VERIFIED,
            AuditIntakeState.QUEUED_TO_REPAIR,
        } and self.repair_job_id is None:
            message = "verified bridge lacks repair job provenance"
            raise ValueError(message)
        if (
            self.state == AuditIntakeState.CLEAN_ADOPTED
            and self.adoption_evidence_path is None
        ):
            message = "clean adopted intake lacks promotion evidence"
            raise ValueError(message)
        if (
            self.state
            in {
                AuditIntakeState.CLEAN_ADOPTION_READY,
                AuditIntakeState.CLEAN_ADOPTED,
            }
            and self.audit_verdict != "pass"
        ):
            message = "clean adoption requires a passing assigned audit"
            raise ValueError(message)
        return self


class AuditIntakeEvent(_StrictModel):
    """One immutable audit-intake transition with its full snapshot."""

    version: Literal[1] = 1
    event_id: str = Field(pattern=r"^[0-9a-f]{32}$")
    intake_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    sequence: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=160)
    kind: AuditIntakeEventKind
    actor: str = Field(min_length=1, max_length=120)
    from_state: AuditIntakeState | None
    to_state: AuditIntakeState
    created_at: datetime
    duration_ms: int | None = Field(default=None, ge=0)
    reason: str | None = Field(default=None, max_length=500)
    snapshot: AuditIntakeItem

    @model_validator(mode="after")
    def _snapshot_matches_event(self) -> Self:
        if self.snapshot.intake_id != self.intake_id:
            message = "audit event snapshot belongs to another intake"
            raise ValueError(message)
        if self.snapshot.last_sequence != self.sequence:
            message = "audit event sequence differs from its snapshot"
            raise ValueError(message)
        if self.snapshot.state != self.to_state:
            message = "audit event state differs from its snapshot"
            raise ValueError(message)
        return self


class AuditIntakeLease(_StrictModel):
    """Exclusive renewable lease for one audit or bridge worker."""

    version: Literal[1] = 1
    lease_id: str = Field(pattern=r"^[0-9a-f]{32}$")
    intake_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    stage: Literal["audit", "bridge"]
    worker_id: str = Field(min_length=1, max_length=120)
    acquired_at: datetime
    heartbeat_at: datetime
    expires_at: datetime


class AuditIntakeStatus(_StrictModel):
    """Audit backlog, active WIP, and combined downstream pressure."""

    version: Literal[1] = 1
    total: int = Field(ge=0)
    states: dict[AuditIntakeState, int]
    audit_running: int = Field(ge=0)
    audit_running_by_reviewer: dict[AssignedReviewer, int]
    bridge_running: int = Field(ge=0)
    audit_backlog: int = Field(ge=0)
    bridge_backlog: int = Field(ge=0)
    clean_adoption_ready: int = Field(ge=0)
    oldest_audit_queued_ms: int = Field(ge=0)
    oldest_bridge_queued_ms: int = Field(ge=0)
    oldest_clean_adoption_ready_ms: int = Field(ge=0)
    pre_repair_wip: int = Field(ge=0)
    repair_and_later_wip: int = Field(ge=0)
    combined_downstream_wip: int = Field(ge=0)
    backpressure: bool


class AuditIntakeMetrics(_StrictModel):
    """Queue and service timing derived from immutable intake events."""

    version: Literal[1] = 1
    generated_at: datetime
    stages: dict[str, TimingSummary]
    counters: dict[str, int]


def intake_id_for(
    source_id: str,
    source_sha256: str,
    candidate_sha256: str,
    assigned_reviewer: AssignedReviewer,
) -> str:
    """Derive stable ownership for one reviewed source/candidate pair."""
    return sha256_text(
        f"{source_id}\0{source_sha256}\0{candidate_sha256}\0{assigned_reviewer}"
    )


class AuditIntakeStore:
    """Crash-resumable audit and bridge ledger sharing source ownership."""

    def __init__(self, store: PipelineStore) -> None:
        """Initialize intake paths without starting external model work."""
        self.store: PipelineStore = store
        self.root: Path = store.root / "intake"
        self.items_root: Path = self.root / "items"
        self.events_root: Path = self.root / "events"
        self.leases_root: Path = self.root / "leases"
        self.repair_reviews_root: Path = self.root / "repair-ready"
        for path in (
            self.items_root,
            self.events_root,
            self.leases_root,
            self.repair_reviews_root,
        ):
            path.mkdir(parents=True, exist_ok=True)

    def create(self, spec: AuditIntakeSpec, *, actor: str) -> AuditIntakeItem:
        """Validate a manifest pair, reserve its source, and queue deep audit."""
        manifest_path = resolve_repo_path(
            self.store.repo_root,
            spec.manifest_path,
        )
        entry = _manifest_entry(manifest_path, spec.source_id)
        _validate_manifest_entry(self.store.repo_root, entry)
        intake_id = intake_id_for(
            spec.source_id,
            entry.source_sha256,
            entry.candidate_sha256,
            spec.assigned_reviewer,
        )
        with self._lock(intake_id):
            if self._event_path(intake_id).is_file():
                existing = self.load(intake_id)
                self._validate_existing_spec(existing, spec, entry)
                return existing
            _ = self.store.reserve_source(spec.source_id, intake_id)
            try:
                now = _utc_now()
                provider_model: ProviderModel = (
                    "k3" if spec.provider == "kimi" else "glm-5.2"
                )
                item = AuditIntakeItem(
                    intake_id=intake_id,
                    source_id=spec.source_id,
                    manifest_path=spec.manifest_path,
                    manifest_sha256=sha256_path(manifest_path),
                    english_path=entry.english_path,
                    chinese_path=entry.chinese_path,
                    normalized_candidate_path=entry.normalized_candidate_path,
                    source_sha256=entry.source_sha256,
                    candidate_sha256=entry.candidate_sha256,
                    normalized_candidate_sha256=(
                        entry.normalized_candidate_sha256
                    ),
                    assigned_reviewer=spec.assigned_reviewer,
                    provider=spec.provider,
                    provider_model=provider_model,
                    attempt_id=spec.attempt_id,
                    state=AuditIntakeState.AUDIT_QUEUED,
                    created_at=now,
                    updated_at=now,
                    last_sequence=1,
                )
                self._write_initial_event(item, actor)
            except Exception:
                self.store.release_source_reservation(
                    spec.source_id,
                    intake_id,
                )
                raise
            else:
                return item

    def load(self, intake_id: str) -> AuditIntakeItem:
        """Load the latest event and repair a stale materialized snapshot."""
        events = self.events(intake_id)
        if not events:
            message = f"audit intake does not exist: {intake_id}"
            raise ValueError(message)
        latest = events[-1].snapshot
        path = self._item_path(intake_id)
        current: AuditIntakeItem | None = None
        if path.is_file():
            current = AuditIntakeItem.model_validate_json(
                path.read_text(encoding="utf-8-sig")
            )
        if current is None or current.last_sequence != latest.last_sequence:
            _atomic_model(path, latest)
        return latest

    def list_items(self) -> tuple[AuditIntakeItem, ...]:
        """Return current snapshots sorted by creation time."""
        items = [
            self.load(path.stem)
            for path in self.events_root.glob("*.jsonl")
        ]
        return tuple(
            sorted(items, key=lambda item: (item.created_at, item.intake_id))
        )

    def events(self, intake_id: str) -> tuple[AuditIntakeEvent, ...]:
        """Load and verify the append-only event sequence."""
        path = self._event_path(intake_id)
        if not path.is_file():
            return ()
        events = tuple(
            AuditIntakeEvent.model_validate_json(line)
            for line in path.read_text(encoding="utf-8-sig").splitlines()
            if line.strip()
        )
        for expected, event in enumerate(events, start=1):
            if event.sequence != expected:
                message = "audit intake event sequence is not contiguous"
                raise ValueError(message)
        return events

    def claim_audit(
        self,
        intake_id: str,
        worker_id: str,
    ) -> AuditIntakeItem:
        """Claim one audit within global, reviewer-lane, and WIP limits."""
        with self.store.coordinator_lock("audit-intake-dispatch"), self._lock(
            intake_id
        ):
            item = self.load(intake_id)
            if item.state != AuditIntakeState.AUDIT_QUEUED:
                message = "audit intake is not queued"
                raise ValueError(message)
            status = self.status()
            if status.audit_running >= self.store.policy.deep_audit_parallelism:
                message = "deep-audit concurrency limit is reached"
                raise ValueError(message)
            lane_limit = (
                self.store.policy.deep_audit_terra_parallelism
                if item.assigned_reviewer == "gpt-5.6-terra"
                else self.store.policy.deep_audit_grok_parallelism
            )
            if (
                status.audit_running_by_reviewer[item.assigned_reviewer]
                >= lane_limit
            ):
                message = "assigned deep-audit reviewer limit is reached"
                raise ValueError(message)
            if status.backpressure:
                message = "deep-audit downstream backpressure is active"
                raise ValueError(message)
            lease = self._create_lease(item, "audit", worker_id)
            try:
                return self._transition(
                    item,
                    state=AuditIntakeState.AUDIT_RUNNING,
                    kind=AuditIntakeEventKind.AUDIT_CLAIMED,
                    actor=worker_id,
                    idempotency_key=f"audit-claimed:{lease.lease_id}",
                )
            except Exception:
                self._remove_lease(intake_id)
                raise

    def complete_audit(
        self,
        intake_id: str,
        worker_id: str,
        report_path_value: str,
        *,
        duration_ms: int,
    ) -> AuditIntakeItem:
        """Bind one assigned deep-audit report and expose it for routing."""
        with self._lock(intake_id):
            item = self.load(intake_id)
            report_path = resolve_repo_path(
                self.store.repo_root,
                report_path_value,
            )
            validated = validate_deep_audit_report(
                repo_root=self.store.repo_root,
                manifest_path=resolve_repo_path(
                    self.store.repo_root,
                    item.manifest_path,
                ),
                report_path=report_path,
                source_id=item.source_id,
                assigned_reviewer=item.assigned_reviewer,
            )
            if item.state != AuditIntakeState.AUDIT_RUNNING:
                if (
                    item.audit_report_sha256
                    == validated.report_sha256
                    and item.state
                    not in {
                        AuditIntakeState.AUDIT_QUEUED,
                        AuditIntakeState.AUDIT_RUNNING,
                    }
                ):
                    self._remove_lease(intake_id)
                    return item
                message = "audit intake is not running"
                raise ValueError(message)
            _ = self._require_lease(item, "audit", worker_id)
            bridge_error: ValueError | None = None
            if validated.verdict != "pass":
                try:
                    _ = bridge_deep_audit_report(
                        repo_root=self.store.repo_root,
                        manifest_path=resolve_repo_path(
                            self.store.repo_root,
                            item.manifest_path,
                        ),
                        report_path=report_path,
                        source_id=item.source_id,
                        assigned_reviewer=item.assigned_reviewer,
                    )
                except ValueError as error:
                    bridge_error = error
            updated = _updated_item(
                item,
                audit_report_path=validated.report_path,
                audit_report_sha256=validated.report_sha256,
                audit_verdict=validated.verdict,
            )
            completed = self._transition(
                updated,
                state=AuditIntakeState.AUDIT_COMPLETE,
                kind=AuditIntakeEventKind.AUDIT_COMPLETED,
                actor=worker_id,
                idempotency_key=(
                    f"audit-completed:{validated.report_sha256}"
                ),
                duration_ms=duration_ms,
            )
            self._remove_lease(intake_id)
            if bridge_error is not None:
                reason = f"bridge preflight failed: {bridge_error}"
                terminal = self._transition(
                    _updated_item(completed, terminal_reason=reason),
                    state=AuditIntakeState.STRUCTURAL_BLOCKED,
                    kind=AuditIntakeEventKind.STRUCTURAL_BLOCKED,
                    actor=worker_id,
                    idempotency_key=(
                        "structural-blocked:"
                        f"{validated.report_sha256}:{sha256_text(reason)}"
                    ),
                    reason=reason,
                )
                self.store.release_source_reservation(
                    terminal.source_id,
                    terminal.intake_id,
                )
                return terminal
            return completed

    def route_completed_audits(self) -> tuple[AuditIntakeItem, ...]:
        """Route complete reports to adoption or exact-span bridge queues."""
        routed: list[AuditIntakeItem] = []
        for current in self.list_items():
            if current.state != AuditIntakeState.AUDIT_COMPLETE:
                continue
            with self._lock(current.intake_id):
                item = self.load(current.intake_id)
                if item.state != AuditIntakeState.AUDIT_COMPLETE:
                    continue
                if item.audit_verdict == "pass":
                    routed.append(
                        self._transition(
                            item,
                            state=AuditIntakeState.CLEAN_ADOPTION_READY,
                            kind=(
                                AuditIntakeEventKind.CLEAN_ADOPTION_READY
                            ),
                            actor="intake-router",
                            idempotency_key="clean-adoption-ready",
                        )
                    )
                else:
                    routed.append(
                        self._transition(
                            item,
                            state=AuditIntakeState.BRIDGE_QUEUED,
                            kind=AuditIntakeEventKind.BRIDGE_QUEUED,
                            actor="intake-router",
                            idempotency_key="bridge-queued",
                        )
                    )
        return tuple(routed)

    def claim_bridge(
        self,
        intake_id: str,
        worker_id: str,
    ) -> AuditIntakeItem:
        """Claim one exact-span bridge worker."""
        with self.store.coordinator_lock("bridge-intake-dispatch"), self._lock(
            intake_id
        ):
            item = self.load(intake_id)
            if item.state != AuditIntakeState.BRIDGE_QUEUED:
                message = "audit bridge is not queued"
                raise ValueError(message)
            if self.status().bridge_running >= self.store.policy.bridge_parallelism:
                message = "audit bridge concurrency limit is reached"
                raise ValueError(message)
            lease = self._create_lease(item, "bridge", worker_id)
            try:
                return self._transition(
                    item,
                    state=AuditIntakeState.BRIDGE_RUNNING,
                    kind=AuditIntakeEventKind.BRIDGE_CLAIMED,
                    actor=worker_id,
                    idempotency_key=f"bridge-claimed:{lease.lease_id}",
                )
            except Exception:
                self._remove_lease(intake_id)
                raise

    def complete_bridge(
        self,
        intake_id: str,
        worker_id: str,
        *,
        duration_ms: int | None = None,
    ) -> AuditIntakeItem:
        """Create one stable repair job and recover safely across crashes."""
        with self._lock(intake_id):
            item = self.load(intake_id)
            if item.state == AuditIntakeState.QUEUED_TO_REPAIR:
                self._remove_lease(intake_id)
                self.store.release_source_reservation(
                    item.source_id,
                    item.intake_id,
                )
                return item
            if item.state == AuditIntakeState.BRIDGE_VERIFIED:
                queued = self._transition(
                    item,
                    state=AuditIntakeState.QUEUED_TO_REPAIR,
                    kind=AuditIntakeEventKind.REPAIR_QUEUED,
                    actor=worker_id,
                    idempotency_key="repair-queued",
                )
                self._remove_lease(intake_id)
                self.store.release_source_reservation(
                    queued.source_id,
                    queued.intake_id,
                )
                return queued
            if item.state != AuditIntakeState.BRIDGE_RUNNING:
                message = "audit bridge is not running"
                raise ValueError(message)
            _ = self._require_lease(item, "bridge", worker_id)
            started = time.perf_counter()
            repair_review_path = (
                self.repair_reviews_root / f"{item.intake_id}.json"
            )
            result = bridge_and_queue_deep_audit(
                store=self.store,
                manifest_path=resolve_repo_path(
                    self.store.repo_root,
                    item.manifest_path,
                ),
                report_path=resolve_repo_path(
                    self.store.repo_root,
                    _required(item.audit_report_path),
                ),
                repair_review_path=repair_review_path,
                source_id=item.source_id,
                assigned_reviewer=item.assigned_reviewer,
                provider=item.provider,
                attempt_id=item.attempt_id,
                actor=worker_id,
                intake_id=item.intake_id,
            )
            measured_duration_ms = max(
                0,
                round((time.perf_counter() - started) * 1000),
            )
            updated = _updated_item(
                item,
                repair_review_path=result.repair_review_path,
                repair_review_sha256=result.repair_review_sha256,
                repair_job_id=result.job.job_id,
            )
            verified = self._transition(
                updated,
                state=AuditIntakeState.BRIDGE_VERIFIED,
                kind=AuditIntakeEventKind.BRIDGE_VERIFIED,
                actor=worker_id,
                idempotency_key=(
                    f"bridge-verified:{result.repair_review_sha256}"
                ),
                duration_ms=(
                    measured_duration_ms
                    if duration_ms is None
                    else duration_ms
                ),
            )
            self._remove_lease(intake_id)
            queued = self._transition(
                verified,
                state=AuditIntakeState.QUEUED_TO_REPAIR,
                kind=AuditIntakeEventKind.REPAIR_QUEUED,
                actor=worker_id,
                idempotency_key="repair-queued",
            )
            self.store.release_source_reservation(
                queued.source_id,
                queued.intake_id,
            )
            return queued

    def block(
        self,
        intake_id: str,
        *,
        actor: str,
        reason: str,
        invalid: bool = False,
    ) -> AuditIntakeItem:
        """Terminally classify deterministic structure or evidence failures."""
        with self._lock(intake_id):
            item = self.load(intake_id)
            if item.state in _TERMINAL_INTAKE_STATES:
                self._remove_lease(intake_id)
                if item.state != AuditIntakeState.CLEAN_ADOPTION_READY:
                    self.store.release_source_reservation(
                        item.source_id,
                        item.intake_id,
                    )
                return item
            state = (
                AuditIntakeState.INVALID
                if invalid
                else AuditIntakeState.STRUCTURAL_BLOCKED
            )
            kind = (
                AuditIntakeEventKind.INVALID
                if invalid
                else AuditIntakeEventKind.STRUCTURAL_BLOCKED
            )
            updated = _updated_item(item, terminal_reason=reason)
            terminal = self._transition(
                updated,
                state=state,
                kind=kind,
                actor=actor,
                idempotency_key=f"{state.value}:{sha256_text(reason)}",
                reason=reason,
            )
            self._remove_lease(intake_id)
            self.store.release_source_reservation(
                terminal.source_id,
                terminal.intake_id,
            )
            return terminal

    def adopt_clean(
        self,
        intake_id: str,
        evidence_path: str,
        *,
        actor: str,
    ) -> AuditIntakeItem:
        """Record one fully gated clean adoption and release source ownership."""
        with self._lock(intake_id):
            item = self.load(intake_id)
            path = resolve_repo_path(self.store.repo_root, evidence_path)
            evidence_sha256 = sha256_path(path)
            evidence = CleanAdoptionEvidence.model_validate_json(
                path.read_text(encoding="utf-8-sig")
            )
            if item.state == AuditIntakeState.CLEAN_ADOPTED:
                expected = (
                    item.adoption_evidence_path,
                    item.adoption_evidence_sha256,
                )
                if expected != (evidence_path, evidence_sha256):
                    message = "clean adoption already uses different evidence"
                    raise ValueError(message)
                self.store.release_source_reservation(
                    item.source_id,
                    item.intake_id,
                )
                return item
            if item.state != AuditIntakeState.CLEAN_ADOPTION_READY:
                message = "audit intake is not ready for clean adoption"
                raise ValueError(message)
            target_path, public_source_path, public_candidate_path = (
                _clean_adoption_paths(item.source_id)
            )
            expected = (
                item.intake_id,
                item.source_id,
                item.assigned_reviewer,
                _required(item.audit_report_path),
                _required(item.audit_report_sha256),
                target_path,
                item.normalized_candidate_sha256,
                public_source_path,
                item.source_sha256,
                public_candidate_path,
                item.candidate_sha256,
            )
            actual = (
                evidence.intake_id,
                evidence.source_id,
                evidence.assigned_reviewer,
                evidence.audit_report_path,
                evidence.audit_report_sha256,
                evidence.target_path,
                evidence.target_sha256,
                evidence.public_source_path,
                evidence.public_source_sha256,
                evidence.public_candidate_path,
                evidence.public_candidate_sha256,
            )
            if expected != actual:
                message = "clean adoption evidence does not match its intake"
                raise ValueError(message)
            gates = (
                evidence.page_tests,
                evidence.typecheck,
                evidence.lint,
                evidence.materialization,
                evidence.build,
                evidence.routes,
            )
            if not all(gates):
                message = "clean adoption evidence contains a failed site gate"
                raise ValueError(message)
            files = (
                (evidence.audit_report_path, evidence.audit_report_sha256),
                (evidence.target_path, evidence.target_sha256),
                (
                    evidence.public_source_path,
                    evidence.public_source_sha256,
                ),
                (
                    evidence.public_candidate_path,
                    evidence.public_candidate_sha256,
                ),
                (evidence.gate_log_path, evidence.gate_log_sha256),
            )
            for path_value, expected_sha256 in files:
                current = resolve_repo_path(
                    self.store.repo_root,
                    path_value,
                )
                if sha256_path(current) != expected_sha256:
                    message = (
                        "clean adoption evidence file changed: "
                        f"{path_value}"
                    )
                    raise ValueError(message)
            updated = _updated_item(
                item,
                adoption_evidence_path=evidence_path,
                adoption_evidence_sha256=evidence_sha256,
            )
            adopted = self._transition(
                updated,
                state=AuditIntakeState.CLEAN_ADOPTED,
                kind=AuditIntakeEventKind.CLEAN_ADOPTED,
                actor=actor,
                idempotency_key=f"clean-adopted:{evidence_sha256}",
            )
            self.store.release_source_reservation(
                adopted.source_id,
                adopted.intake_id,
            )
            return adopted

    def heartbeat(
        self,
        intake_id: str,
        worker_id: str,
    ) -> AuditIntakeLease:
        """Renew a live audit or bridge lease."""
        with self._lock(intake_id):
            item = self.load(intake_id)
            stage = (
                "audit"
                if item.state == AuditIntakeState.AUDIT_RUNNING
                else "bridge"
                if item.state == AuditIntakeState.BRIDGE_RUNNING
                else None
            )
            if stage is None:
                message = "audit intake has no running stage"
                raise ValueError(message)
            lease = self._require_lease(item, stage, worker_id)
            now = _utc_now()
            renewed = AuditIntakeLease.model_validate(
                {
                    **lease.model_dump(mode="python"),
                    "heartbeat_at": now,
                    "expires_at": now
                    + timedelta(seconds=self.store.policy.lease_seconds),
                }
            )
            _atomic_model(self._lease_path(intake_id), renewed)
            return renewed

    def recover_expired_leases(self) -> tuple[AuditIntakeItem, ...]:
        """Return expired audit and bridge work to their previous queues."""
        recovered: list[AuditIntakeItem] = []
        for path in sorted(self.leases_root.glob("*.json")):
            try:
                lease = AuditIntakeLease.model_validate_json(
                    path.read_text(encoding="utf-8-sig")
                )
            except FileNotFoundError:
                continue
            if lease.expires_at > _utc_now():
                continue
            with self._lock(lease.intake_id):
                item = self.load(lease.intake_id)
                current_path = self._lease_path(lease.intake_id)
                if not current_path.is_file():
                    continue
                try:
                    current = AuditIntakeLease.model_validate_json(
                        current_path.read_text(encoding="utf-8-sig")
                    )
                except FileNotFoundError:
                    continue
                if current.lease_id != lease.lease_id:
                    continue
                if (
                    lease.stage == "audit"
                    and item.state == AuditIntakeState.AUDIT_RUNNING
                ):
                    state = AuditIntakeState.AUDIT_QUEUED
                    kind = AuditIntakeEventKind.AUDIT_RECOVERED
                elif (
                    lease.stage == "bridge"
                    and item.state == AuditIntakeState.BRIDGE_RUNNING
                ):
                    state = AuditIntakeState.BRIDGE_QUEUED
                    kind = AuditIntakeEventKind.BRIDGE_RECOVERED
                else:
                    current_path.unlink(missing_ok=True)
                    continue
                recovered_item = self._transition(
                    item,
                    state=state,
                    kind=kind,
                    actor="lease-recovery",
                    idempotency_key=(
                        f"{kind.value}:{lease.lease_id}"
                    ),
                )
                current_path.unlink(missing_ok=True)
                recovered.append(recovered_item)
        return tuple(recovered)

    def status(self) -> AuditIntakeStatus:
        """Aggregate audit backlog and all downstream work in progress."""
        items = self.list_items()
        counts = dict.fromkeys(AuditIntakeState, 0)
        running_by_reviewer: dict[AssignedReviewer, int] = {
            "gpt-5.6-terra": 0,
            "grok-4.5": 0,
        }
        for item in items:
            counts[item.state] += 1
            if item.state == AuditIntakeState.AUDIT_RUNNING:
                running_by_reviewer[item.assigned_reviewer] += 1
        pre_repair_states = frozenset(
            {
                AuditIntakeState.AUDIT_RUNNING,
                AuditIntakeState.AUDIT_COMPLETE,
                AuditIntakeState.BRIDGE_QUEUED,
                AuditIntakeState.BRIDGE_RUNNING,
                AuditIntakeState.BRIDGE_VERIFIED,
                AuditIntakeState.CLEAN_ADOPTION_READY,
            }
        )
        pre_repair_wip = sum(
            count
            for state, count in counts.items()
            if state in pre_repair_states
        )
        pipeline_status = self.store.status()
        repair_and_later_wip = (
            pipeline_status.states[PipelineState.REPAIR_QUEUED]
            + pipeline_status.downstream_wip
        )
        combined = pre_repair_wip + repair_and_later_wip
        now = _utc_now()
        return AuditIntakeStatus(
            total=len(items),
            states=counts,
            audit_running=counts[AuditIntakeState.AUDIT_RUNNING],
            audit_running_by_reviewer=running_by_reviewer,
            bridge_running=counts[AuditIntakeState.BRIDGE_RUNNING],
            audit_backlog=counts[AuditIntakeState.AUDIT_QUEUED],
            bridge_backlog=counts[AuditIntakeState.BRIDGE_QUEUED],
            clean_adoption_ready=counts[
                AuditIntakeState.CLEAN_ADOPTION_READY
            ],
            oldest_audit_queued_ms=_oldest_state_age_ms(
                items,
                AuditIntakeState.AUDIT_QUEUED,
                now,
            ),
            oldest_bridge_queued_ms=_oldest_state_age_ms(
                items,
                AuditIntakeState.BRIDGE_QUEUED,
                now,
            ),
            oldest_clean_adoption_ready_ms=_oldest_state_age_ms(
                items,
                AuditIntakeState.CLEAN_ADOPTION_READY,
                now,
            ),
            pre_repair_wip=pre_repair_wip,
            repair_and_later_wip=repair_and_later_wip,
            combined_downstream_wip=combined,
            backpressure=(
                pipeline_status.downstream_backpressure
                or combined >= self.store.policy.downstream_wip_limit
            ),
        )

    def metrics(self) -> AuditIntakeMetrics:
        """Derive audit and bridge wait/service times from event evidence."""
        samples: dict[str, list[int]] = {
            "audit_queue_wait": [],
            "audit_turnaround": [],
            "audit_service": [],
            "audit_route_wait": [],
            "bridge_queue_wait": [],
            "bridge_turnaround": [],
            "bridge_service": [],
            "intake_to_repair": [],
            "clean_adoption_wait": [],
        }
        items = self.list_items()
        counters = {
            "intakes": len(items),
            "unique_sources": len({item.source_id for item in items}),
            "audit_reports": 0,
            "clean_audits": 0,
            "repair_audits": 0,
            "bridges_verified": 0,
            "queued_to_repair": 0,
            "clean_adoption_ready": 0,
            "clean_adopted": 0,
            "structural_blocked": 0,
            "invalid": 0,
        }
        for item in items:
            events = self.events(item.intake_id)
            _collect_event_interval(
                events,
                AuditIntakeEventKind.AUDIT_QUEUED,
                frozenset({AuditIntakeEventKind.AUDIT_CLAIMED}),
                samples["audit_queue_wait"],
            )
            _collect_event_interval(
                events,
                AuditIntakeEventKind.AUDIT_CLAIMED,
                frozenset({AuditIntakeEventKind.AUDIT_COMPLETED}),
                samples["audit_turnaround"],
            )
            samples["audit_service"].extend(
                event.duration_ms
                for event in events
                if event.kind == AuditIntakeEventKind.AUDIT_COMPLETED
                and event.duration_ms is not None
            )
            _collect_event_interval(
                events,
                AuditIntakeEventKind.AUDIT_COMPLETED,
                frozenset(
                    {
                        AuditIntakeEventKind.BRIDGE_QUEUED,
                        AuditIntakeEventKind.CLEAN_ADOPTION_READY,
                    }
                ),
                samples["audit_route_wait"],
            )
            _collect_event_interval(
                events,
                AuditIntakeEventKind.BRIDGE_QUEUED,
                frozenset({AuditIntakeEventKind.BRIDGE_CLAIMED}),
                samples["bridge_queue_wait"],
            )
            _collect_event_interval(
                events,
                AuditIntakeEventKind.BRIDGE_CLAIMED,
                frozenset({AuditIntakeEventKind.BRIDGE_VERIFIED}),
                samples["bridge_turnaround"],
            )
            samples["bridge_service"].extend(
                event.duration_ms
                for event in events
                if event.kind == AuditIntakeEventKind.BRIDGE_VERIFIED
                and event.duration_ms is not None
            )
            _collect_event_interval(
                events,
                AuditIntakeEventKind.AUDIT_QUEUED,
                frozenset({AuditIntakeEventKind.REPAIR_QUEUED}),
                samples["intake_to_repair"],
            )
            _collect_event_interval(
                events,
                AuditIntakeEventKind.CLEAN_ADOPTION_READY,
                frozenset({AuditIntakeEventKind.CLEAN_ADOPTED}),
                samples["clean_adoption_wait"],
            )
            counters["audit_reports"] += int(item.audit_report_path is not None)
            counters["clean_audits"] += int(item.audit_verdict == "pass")
            counters["repair_audits"] += int(
                item.audit_verdict in {"warn", "fail"}
            )
            counters["bridges_verified"] += int(
                item.repair_review_path is not None
            )
            counters["queued_to_repair"] += int(
                item.state == AuditIntakeState.QUEUED_TO_REPAIR
            )
            counters["clean_adoption_ready"] += int(
                item.state == AuditIntakeState.CLEAN_ADOPTION_READY
            )
            counters["clean_adopted"] += int(
                item.state == AuditIntakeState.CLEAN_ADOPTED
            )
            counters["structural_blocked"] += int(
                item.state == AuditIntakeState.STRUCTURAL_BLOCKED
            )
            counters["invalid"] += int(
                item.state == AuditIntakeState.INVALID
            )
        return AuditIntakeMetrics(
            generated_at=_utc_now(),
            stages={
                name: _timing_summary(values)
                for name, values in samples.items()
            },
            counters=counters,
        )

    def _validate_existing_spec(
        self,
        item: AuditIntakeItem,
        spec: AuditIntakeSpec,
        entry: DeepAuditManifestEntry,
    ) -> None:
        expected = (
            item.source_id,
            item.manifest_path,
            item.assigned_reviewer,
            item.provider,
            item.attempt_id,
            item.source_sha256,
            item.candidate_sha256,
            item.normalized_candidate_sha256,
        )
        actual = (
            spec.source_id,
            spec.manifest_path,
            spec.assigned_reviewer,
            spec.provider,
            spec.attempt_id,
            entry.source_sha256,
            entry.candidate_sha256,
            entry.normalized_candidate_sha256,
        )
        if expected != actual:
            message = "existing audit intake has different immutable routing"
            raise ValueError(message)

    def _write_initial_event(
        self,
        item: AuditIntakeItem,
        actor: str,
    ) -> None:
        event = AuditIntakeEvent(
            event_id=uuid.uuid4().hex,
            intake_id=item.intake_id,
            sequence=1,
            idempotency_key="audit-queued",
            kind=AuditIntakeEventKind.AUDIT_QUEUED,
            actor=actor,
            from_state=None,
            to_state=AuditIntakeState.AUDIT_QUEUED,
            created_at=item.created_at,
            snapshot=item,
        )
        self._append_event(event)
        _atomic_model(self._item_path(item.intake_id), item)

    def _transition(  # noqa: PLR0913
        self,
        item: AuditIntakeItem,
        *,
        state: AuditIntakeState,
        kind: AuditIntakeEventKind,
        actor: str,
        idempotency_key: str,
        duration_ms: int | None = None,
        reason: str | None = None,
    ) -> AuditIntakeItem:
        events = self.events(item.intake_id)
        for event in events:
            if event.idempotency_key == idempotency_key:
                return event.snapshot
        _validate_transition(item.state, state)
        now = _utc_now()
        updated = _updated_item(
            item,
            state=state,
            updated_at=now,
            last_sequence=item.last_sequence + 1,
        )
        event = AuditIntakeEvent(
            event_id=uuid.uuid4().hex,
            intake_id=item.intake_id,
            sequence=updated.last_sequence,
            idempotency_key=idempotency_key,
            kind=kind,
            actor=actor,
            from_state=item.state,
            to_state=state,
            created_at=now,
            duration_ms=duration_ms,
            reason=reason,
            snapshot=updated,
        )
        self._append_event(event)
        _atomic_model(self._item_path(item.intake_id), updated)
        return updated

    def _create_lease(
        self,
        item: AuditIntakeItem,
        stage: Literal["audit", "bridge"],
        worker_id: str,
    ) -> AuditIntakeLease:
        path = self._lease_path(item.intake_id)
        if path.is_file():
            message = "audit intake already has an active lease"
            raise ValueError(message)
        now = _utc_now()
        lease = AuditIntakeLease(
            lease_id=uuid.uuid4().hex,
            intake_id=item.intake_id,
            stage=stage,
            worker_id=worker_id,
            acquired_at=now,
            heartbeat_at=now,
            expires_at=now
            + timedelta(seconds=self.store.policy.lease_seconds),
        )
        _atomic_model(path, lease)
        return lease

    def _require_lease(
        self,
        item: AuditIntakeItem,
        stage: Literal["audit", "bridge"],
        worker_id: str,
    ) -> AuditIntakeLease:
        path = self._lease_path(item.intake_id)
        if not path.is_file():
            message = "audit intake lease is missing"
            raise ValueError(message)
        lease = AuditIntakeLease.model_validate_json(
            path.read_text(encoding="utf-8-sig")
        )
        if (
            lease.intake_id != item.intake_id
            or lease.stage != stage
            or lease.worker_id != worker_id
        ):
            message = "audit intake lease belongs to another worker"
            raise ValueError(message)
        if lease.expires_at <= _utc_now():
            message = "audit intake lease expired"
            raise ValueError(message)
        return lease

    def _remove_lease(self, intake_id: str) -> None:
        self._lease_path(intake_id).unlink(missing_ok=True)

    def _append_event(self, event: AuditIntakeEvent) -> None:
        path = self._event_path(event.intake_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        line = event.model_dump_json() + "\n"
        with path.open("a", encoding="utf-8", newline="\n") as stream:
            _ = stream.write(line)
            stream.flush()
            os.fsync(stream.fileno())

    def _item_path(self, intake_id: str) -> Path:
        return self.items_root / f"{intake_id}.json"

    def _event_path(self, intake_id: str) -> Path:
        return self.events_root / f"{intake_id}.jsonl"

    def _lease_path(self, intake_id: str) -> Path:
        return self.leases_root / f"{intake_id}.json"

    def _lock(
        self,
        intake_id: str,
    ) -> AbstractContextManager[None]:
        return self.store.coordinator_lock(f"audit-intake-{intake_id}")


def _manifest_entry(
    manifest_path: Path,
    source_id: str,
) -> DeepAuditManifestEntry:
    manifest = DeepAuditManifest.model_validate_json(
        manifest_path.read_text(encoding="utf-8-sig")
    )
    matching = [
        value
        for value in manifest.entries
        if value.get("source_id") == source_id
        and value.get("status") == "prepared"
    ]
    if len(matching) != 1:
        message = f"expected one prepared audit manifest entry: {source_id}"
        raise ValueError(message)
    return DeepAuditManifestEntry.model_validate(matching[0])


def _validate_manifest_entry(
    repo_root: Path,
    entry: DeepAuditManifestEntry,
) -> None:
    expected = (
        (entry.english_path, entry.source_sha256),
        (entry.chinese_path, entry.candidate_sha256),
        (
            entry.normalized_candidate_path,
            entry.normalized_candidate_sha256,
        ),
    )
    for path_value, expected_sha256 in expected:
        path = resolve_repo_path(repo_root, path_value)
        if sha256_path(path) != expected_sha256:
            message = f"audit intake manifest hash changed: {path_value}"
            raise ValueError(message)


def _clean_adoption_paths(source_id: str) -> tuple[str, str, str]:
    product, separator, slug = source_id.partition("/")
    if (
        not separator
        or product not in {"claude-code", "codex"}
        or not slug
        or ".." in slug.split("/")
    ):
        message = "clean adoption source_id is not a safe AI content route"
        raise ValueError(message)
    return (
        f"source-ai/content/zh-CN/{product}/{slug}.md",
        f"docs/ai/en/{product}/{slug}.md",
        f"docs/ai/zh-CN/{product}/{slug}.md",
    )


def _validate_transition(
    current: AuditIntakeState,
    target: AuditIntakeState,
) -> None:
    allowed: dict[AuditIntakeState, frozenset[AuditIntakeState]] = {
        AuditIntakeState.AUDIT_QUEUED: frozenset(
            {
                AuditIntakeState.AUDIT_RUNNING,
                AuditIntakeState.STRUCTURAL_BLOCKED,
                AuditIntakeState.INVALID,
            }
        ),
        AuditIntakeState.AUDIT_RUNNING: frozenset(
            {
                AuditIntakeState.AUDIT_COMPLETE,
                AuditIntakeState.AUDIT_QUEUED,
                AuditIntakeState.STRUCTURAL_BLOCKED,
                AuditIntakeState.INVALID,
            }
        ),
        AuditIntakeState.AUDIT_COMPLETE: frozenset(
            {
                AuditIntakeState.BRIDGE_QUEUED,
                AuditIntakeState.CLEAN_ADOPTION_READY,
                AuditIntakeState.STRUCTURAL_BLOCKED,
                AuditIntakeState.INVALID,
            }
        ),
        AuditIntakeState.BRIDGE_QUEUED: frozenset(
            {
                AuditIntakeState.BRIDGE_RUNNING,
                AuditIntakeState.STRUCTURAL_BLOCKED,
                AuditIntakeState.INVALID,
            }
        ),
        AuditIntakeState.BRIDGE_RUNNING: frozenset(
            {
                AuditIntakeState.BRIDGE_VERIFIED,
                AuditIntakeState.BRIDGE_QUEUED,
                AuditIntakeState.STRUCTURAL_BLOCKED,
                AuditIntakeState.INVALID,
            }
        ),
        AuditIntakeState.BRIDGE_VERIFIED: frozenset(
            {AuditIntakeState.QUEUED_TO_REPAIR}
        ),
        AuditIntakeState.QUEUED_TO_REPAIR: frozenset(),
        AuditIntakeState.CLEAN_ADOPTION_READY: frozenset(
            {
                AuditIntakeState.CLEAN_ADOPTED,
                AuditIntakeState.STRUCTURAL_BLOCKED,
                AuditIntakeState.INVALID,
            }
        ),
        AuditIntakeState.CLEAN_ADOPTED: frozenset(),
        AuditIntakeState.STRUCTURAL_BLOCKED: frozenset(),
        AuditIntakeState.INVALID: frozenset(),
    }
    if target not in allowed[current]:
        message = f"invalid audit intake transition: {current} -> {target}"
        raise ValueError(message)


def _collect_event_interval(
    events: tuple[AuditIntakeEvent, ...],
    start_kind: AuditIntakeEventKind,
    end_kinds: frozenset[AuditIntakeEventKind],
    output: list[int],
) -> None:
    start: datetime | None = None
    for event in events:
        if event.kind == start_kind:
            start = event.created_at
            continue
        if start is not None and event.kind in end_kinds:
            elapsed = round((event.created_at - start).total_seconds() * 1000)
            output.append(max(0, elapsed))
            start = None


def _timing_summary(values: list[int]) -> TimingSummary:
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
    total = sum(ordered)
    return TimingSummary(
        samples=len(ordered),
        total_ms=total,
        mean_ms=round(total / len(ordered)),
        p50_ms=_percentile(ordered, 0.5),
        p95_ms=_percentile(ordered, 0.95),
        max_ms=ordered[-1],
    )


def _percentile(values: list[int], fraction: float) -> int:
    index = max(0, ceil(len(values) * fraction) - 1)
    return values[index]


def _oldest_state_age_ms(
    items: tuple[AuditIntakeItem, ...],
    state: AuditIntakeState,
    now: datetime,
) -> int:
    ages = [
        round((now - item.updated_at).total_seconds() * 1000)
        for item in items
        if item.state == state
    ]
    return max(0, max(ages, default=0))


def _updated_item(
    item: AuditIntakeItem,
    **changes: object,
) -> AuditIntakeItem:
    payload = item.model_dump(mode="python")
    payload.update(changes)
    return AuditIntakeItem.model_validate(payload)


def _atomic_model(path: Path, value: BaseModel) -> None:
    _atomic_bytes(
        path,
        value.model_dump_json(indent=2).encode("utf-8") + b"\n",
    )


def _atomic_bytes(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(_ATOMIC_REPLACE_ATTEMPTS):
        temporary = path.with_suffix(
            path.suffix + f".{uuid.uuid4().hex}.tmp"
        )
        _ = temporary.write_bytes(value)
        try:
            _ = temporary.replace(path)
        except PermissionError:
            temporary.unlink(missing_ok=True)
            if attempt + 1 >= _ATOMIC_REPLACE_ATTEMPTS:
                raise
            time.sleep(
                _ATOMIC_REPLACE_INITIAL_DELAY_SECONDS * (1 << attempt)
            )
        else:
            return


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _required(value: str | None) -> str:
    if value is None:
        message = "audit intake provenance is incomplete"
        raise ValueError(message)
    return value

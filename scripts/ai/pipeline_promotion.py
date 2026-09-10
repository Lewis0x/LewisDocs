# Copyright 2026

"""Transactional small-batch promotion for clean reviewed AI pages."""

from __future__ import annotations

import os
import subprocess
import time
import uuid
from collections.abc import Callable, Generator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from threading import Event, Thread
from typing import ClassVar, Literal, Self, TextIO

from pydantic import BaseModel, ConfigDict, Field, model_validator

from scripts.ai.audit_bridge import validate_deep_audit_report
from scripts.ai.final_shape import require_final_shape_pair
from scripts.ai.pipeline import (
    JobLease,
    PipelineState,
    PipelineStore,
    PromotionEvidence,
    RepairJob,
)
from scripts.ai.pipeline_intake import (
    AuditIntakeItem,
    AuditIntakeLease,
    AuditIntakeState,
    AuditIntakeStore,
    CleanAdoptionEvidence,
)
from scripts.ai.review_contract import resolve_repo_path, sha256_path

GateRunner = Callable[[Path, Path], "SiteGateResult"]
FinalShapeChecker = Callable[[Path, tuple[RepairJob, ...]], None]
CleanFinalShapeChecker = Callable[
    [Path, tuple[AuditIntakeItem, ...]],
    None,
]
RollbackRunner = Callable[[Path], None]

_IS_WINDOWS = os.name == "nt"
_WINDOWS_MATERIALIZE_WRITE_RETRY_DELAYS = (0.25, 1.0, 2.0)
_MAX_LEASE_HEARTBEAT_SECONDS = 30.0


@contextmanager
def _preserve_active_leases(store: PipelineStore) -> Generator[None, None, None]:
    """Keep already-running external work alive during long site gates."""
    stop = Event()
    interval = min(
        _MAX_LEASE_HEARTBEAT_SECONDS,
        max(1.0, store.policy.lease_seconds / 3),
    )

    def heartbeat_loop() -> None:
        while not stop.wait(interval):
            _renew_active_leases_once(store)

    _renew_active_leases_once(store)
    thread = Thread(
        target=heartbeat_loop,
        name="promotion-lease-heartbeat",
        daemon=True,
    )
    thread.start()
    try:
        yield
    finally:
        stop.set()
        thread.join(timeout=interval + 1)


def _renew_active_leases_once(store: PipelineStore) -> None:
    """Renew every still-active lease without claiming or recovering work."""
    for path in sorted(store.leases_root.glob("*.json")):
        try:
            lease = JobLease.model_validate_json(
                path.read_text(encoding="utf-8-sig")
            )
            _ = store.heartbeat(lease.job_id, lease.worker_id)
        except (OSError, ValueError):
            continue
    intake = AuditIntakeStore(store)
    for path in sorted(intake.leases_root.glob("*.json")):
        try:
            lease = AuditIntakeLease.model_validate_json(
                path.read_text(encoding="utf-8-sig")
            )
            _ = intake.heartbeat(lease.intake_id, lease.worker_id)
        except (OSError, ValueError):
            continue


class _StrictModel(BaseModel):
    """Immutable promotion record base."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )


class SiteGateResult(_StrictModel):
    """Result of one complete local site-gate batch."""

    version: Literal[1] = 1
    page_tests: bool
    typecheck: bool
    lint: bool
    materialization: bool
    build: bool
    routes: bool
    duration_ms: int = Field(ge=0)
    log_path: str = Field(min_length=1)


class PromotionBatchResult(_StrictModel):
    """One small-batch promotion attempt."""

    version: Literal[1] = 1
    batch_id: str = Field(pattern=r"^[0-9a-f]{32}$")
    due: bool
    selected_job_ids: tuple[str, ...]
    promoted_job_ids: tuple[str, ...]
    gates: SiteGateResult | None
    completed_at: datetime


class PromotionTargetBackup(_StrictModel):
    """Original formal target captured before one promotion transaction."""

    target_path: str = Field(min_length=1)
    target_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    was_present: bool
    backup_path: str | None = Field(default=None, min_length=1)
    backup_sha256: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )

    @model_validator(mode="after")
    def _backup_matches_presence(self) -> Self:
        if self.was_present != (
            self.backup_path is not None and self.backup_sha256 is not None
        ):
            message = "promotion backup presence metadata is inconsistent"
            raise ValueError(message)
        return self


class PromotionTransaction(_StrictModel):
    """Recoverable intent spanning target writes, gates, and ledger commits."""

    version: Literal[1] = 1
    batch_id: str = Field(pattern=r"^[0-9a-f]{32}$")
    state: Literal[
        "prepared",
        "targets_applied",
        "gates_passed",
        "recorded",
        "rolled_back",
    ]
    selected_job_ids: tuple[str, ...] = Field(min_length=1, max_length=6)
    targets: tuple[PromotionTargetBackup, ...] = Field(min_length=1, max_length=6)
    gates: SiteGateResult | None = None
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def _transaction_is_consistent(self) -> Self:
        if len(self.selected_job_ids) != len(self.targets):
            message = "promotion transaction job and target counts differ"
            raise ValueError(message)
        if self.state in {"gates_passed", "recorded"} and self.gates is None:
            message = "passed promotion transaction has no gate evidence"
            raise ValueError(message)
        return self


class CleanAdoptionBatchResult(_StrictModel):
    """One transactionally gated batch of already-clean audit candidates."""

    version: Literal[1] = 1
    batch_id: str = Field(pattern=r"^[0-9a-f]{32}$")
    due: bool
    selected_intake_ids: tuple[str, ...]
    adopted_intake_ids: tuple[str, ...]
    gates: SiteGateResult | None
    completed_at: datetime


class CleanAdoptionTransaction(_StrictModel):
    """Recoverable intent for clean adoption target writes and evidence."""

    version: Literal[1] = 1
    batch_id: str = Field(pattern=r"^[0-9a-f]{32}$")
    state: Literal[
        "prepared",
        "targets_applied",
        "gates_passed",
        "recorded",
        "rolled_back",
    ]
    selected_intake_ids: tuple[str, ...] = Field(
        min_length=1,
        max_length=6,
    )
    targets: tuple[PromotionTargetBackup, ...] = Field(
        min_length=1,
        max_length=6,
    )
    gates: SiteGateResult | None = None
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def _transaction_is_consistent(self) -> Self:
        if len(self.selected_intake_ids) != len(self.targets):
            message = "clean adoption transaction target count differs"
            raise ValueError(message)
        if self.state in {"gates_passed", "recorded"} and self.gates is None:
            message = "passed clean adoption transaction has no gates"
            raise ValueError(message)
        return self


class PromotionBatchRunner:
    """Apply clean candidates, run all gates once, then record promotion."""

    def __init__(
        self,
        store: PipelineStore,
        gate_runner: GateRunner | None = None,
        final_shape_checker: FinalShapeChecker | None = None,
        rollback_runner: RollbackRunner | None = None,
    ) -> None:
        """Initialize without writing formal content."""
        self.store: PipelineStore = store
        self.gate_runner: GateRunner = gate_runner or run_default_site_gates
        self.final_shape_checker: FinalShapeChecker = (
            final_shape_checker or check_promoted_final_shapes
        )
        self.rollback_runner: RollbackRunner = (
            rollback_runner or rematerialize_after_rollback
        )
        self.transactions_root: Path = (
            self.store.root / "promotion-transactions"
        )
        self.transactions_root.mkdir(parents=True, exist_ok=True)

    def run_due(self, *, force: bool = False) -> PromotionBatchResult:
        """Promote up to six pages when batch size or max wait is reached."""
        with self.store.coordinator_lock("promotion-batch"):
            self._recover_incomplete_transactions()
            ready = tuple(
                sorted(
                    (
                        job
                        for job in self.store.list_jobs()
                        if job.state == PipelineState.PROMOTION_READY
                    ),
                    key=lambda job: (
                        _promotion_ready_at(self.store, job),
                        job.job_id,
                    ),
                )
            )
            status = self.store.status()
            due = force or (
                len(ready) >= self.store.policy.promotion_batch_size
                or status.oldest_promotion_ready_ms
                >= self.store.policy.promotion_batch_max_wait_seconds * 1000
            )
            batch_id = uuid.uuid4().hex
            if not ready or not due:
                return PromotionBatchResult(
                    batch_id=batch_id,
                    due=due,
                    selected_job_ids=(),
                    promoted_job_ids=(),
                    gates=None,
                    completed_at=datetime.now(UTC),
                )
            selected = ready[:6]
            targets = self._validate_targets(selected)
            transaction = self._begin_transaction(
                batch_id,
                selected,
                targets,
            )
            try:
                for job, target in zip(selected, targets, strict=True):
                    output_path = resolve_repo_path(
                        self.store.repo_root,
                        _required(job.output_path),
                    )
                    _atomic_bytes(target, output_path.read_bytes())
                transaction = self._update_transaction(
                    transaction,
                    state="targets_applied",
                )
                log_path = (
                    self.store.root
                    / "promotion-logs"
                    / f"{batch_id}.log"
                )
                with _preserve_active_leases(self.store):
                    gates = self.gate_runner(self.store.repo_root, log_path)
                _require_green_gates(gates)
                self.final_shape_checker(self.store.repo_root, selected)
                transaction = self._update_transaction(
                    transaction,
                    state="gates_passed",
                    gates=gates,
                )
            except Exception:
                self._rollback_transaction(transaction)
                raise
            promoted = self._record_promotions(
                selected,
                targets,
                gates,
            )
            _ = self._update_transaction(
                transaction,
                state="recorded",
                gates=gates,
            )
            return PromotionBatchResult(
                batch_id=batch_id,
                due=True,
                selected_job_ids=tuple(job.job_id for job in selected),
                promoted_job_ids=tuple(job.job_id for job in promoted),
                gates=gates,
                completed_at=datetime.now(UTC),
            )

    def _begin_transaction(
        self,
        batch_id: str,
        jobs: tuple[RepairJob, ...],
        targets: tuple[Path, ...],
    ) -> PromotionTransaction:
        transaction_root = self.transactions_root / batch_id
        backups_root = transaction_root / "backups"
        backups: list[PromotionTargetBackup] = []
        for index, (job, target) in enumerate(
            zip(jobs, targets, strict=True)
        ):
            backup_path: Path | None = None
            backup_sha256: str | None = None
            if target.is_file():
                backup_path = backups_root / f"{index}.md"
                _atomic_bytes(backup_path, target.read_bytes())
                backup_sha256 = sha256_path(backup_path)
            backups.append(
                PromotionTargetBackup(
                    target_path=target.relative_to(
                        self.store.repo_root
                    ).as_posix(),
                    target_sha256=_required(job.output_sha256),
                    was_present=backup_path is not None,
                    backup_path=(
                        backup_path.relative_to(
                            self.store.repo_root
                        ).as_posix()
                        if backup_path is not None
                        else None
                    ),
                    backup_sha256=backup_sha256,
                )
            )
        now = datetime.now(UTC)
        transaction = PromotionTransaction(
            batch_id=batch_id,
            state="prepared",
            selected_job_ids=tuple(job.job_id for job in jobs),
            targets=tuple(backups),
            created_at=now,
            updated_at=now,
        )
        _atomic_model(self._transaction_path(batch_id), transaction)
        return transaction

    def _recover_incomplete_transactions(self) -> None:
        for path in sorted(self.transactions_root.glob("*/intent.json")):
            transaction = PromotionTransaction.model_validate_json(
                path.read_text(encoding="utf-8-sig")
            )
            if transaction.state in {"recorded", "rolled_back"}:
                continue
            if transaction.state != "gates_passed":
                self._rollback_transaction(transaction)
                continue
            jobs = tuple(
                self.store.load_job(job_id)
                for job_id in transaction.selected_job_ids
            )
            targets = tuple(
                resolve_repo_path(self.store.repo_root, item.target_path)
                for item in transaction.targets
            )
            for item, target in zip(
                transaction.targets,
                targets,
                strict=True,
            ):
                if sha256_path(target) != item.target_sha256:
                    message = "passed promotion transaction target changed"
                    raise ValueError(message)
            gates = transaction.gates
            if gates is None:
                message = "passed promotion transaction lost its gate evidence"
                raise ValueError(message)
            _ = self._record_promotions(jobs, targets, gates)
            _ = self._update_transaction(
                transaction,
                state="recorded",
                gates=gates,
            )

    def _rollback_transaction(
        self,
        transaction: PromotionTransaction,
    ) -> None:
        if transaction.state in {"recorded", "rolled_back"}:
            return
        for item in transaction.targets:
            target = resolve_repo_path(
                self.store.repo_root,
                item.target_path,
            )
            if item.was_present:
                backup_path = resolve_repo_path(
                    self.store.repo_root,
                    _required(item.backup_path),
                )
                if sha256_path(backup_path) != item.backup_sha256:
                    message = "promotion rollback backup changed"
                    raise ValueError(message)
                _atomic_bytes(target, backup_path.read_bytes())
            else:
                target.unlink(missing_ok=True)
        self.rollback_runner(self.store.repo_root)
        _ = self._update_transaction(
            transaction,
            state="rolled_back",
        )

    def _update_transaction(
        self,
        transaction: PromotionTransaction,
        *,
        state: Literal[
            "prepared",
            "targets_applied",
            "gates_passed",
            "recorded",
            "rolled_back",
        ],
        gates: SiteGateResult | None = None,
    ) -> PromotionTransaction:
        payload = transaction.model_dump(mode="python")
        payload.update(
            {
                "state": state,
                "gates": gates if gates is not None else transaction.gates,
                "updated_at": datetime.now(UTC),
            }
        )
        updated = PromotionTransaction.model_validate(payload)
        _atomic_model(self._transaction_path(transaction.batch_id), updated)
        return updated

    def _transaction_path(self, batch_id: str) -> Path:
        return self.transactions_root / batch_id / "intent.json"

    def _validate_targets(
        self,
        jobs: tuple[RepairJob, ...],
    ) -> tuple[Path, ...]:
        targets: list[Path] = []
        for job in jobs:
            _ = self.store.validate_promotion_candidate(job.job_id)
            output_path = resolve_repo_path(
                self.store.repo_root,
                _required(job.output_path),
            )
            if sha256_path(output_path) != job.output_sha256:
                message = "promotion candidate hash changed"
                raise ValueError(message)
            target = _formal_target(self.store.repo_root, job.source_id)
            if target.is_file() and sha256_path(target) != job.output_sha256:
                message = (
                    "automatic promotion refuses to overwrite a different "
                    f"formal candidate: {job.source_id}"
                )
                raise ValueError(message)
            targets.append(target)
        return tuple(targets)

    def _record_promotions(
        self,
        jobs: tuple[RepairJob, ...],
        targets: tuple[Path, ...],
        gates: SiteGateResult,
    ) -> tuple[RepairJob, ...]:
        promoted: list[RepairJob] = []
        for job, target in zip(jobs, targets, strict=True):
            target_value = target.relative_to(self.store.repo_root).as_posix()
            evidence = PromotionEvidence(
                job_id=job.job_id,
                source_id=job.source_id,
                target_path=target_value,
                target_sha256=_required(job.output_sha256),
                page_tests=gates.page_tests,
                typecheck=gates.typecheck,
                lint=gates.lint,
                materialization=gates.materialization,
                build=gates.build,
                routes=gates.routes,
            )
            evidence_path = (
                self.store.root
                / "promotion-evidence"
                / f"{job.job_id}.json"
            )
            _atomic_model(evidence_path, evidence)
            promoted.append(
                self.store.promote(
                    job.job_id,
                    evidence_path.relative_to(
                        self.store.repo_root
                    ).as_posix(),
                    actor="promotion-batch",
                )
            )
        return tuple(promoted)


class CleanAdoptionBatchRunner:
    """Adopt assigned-review clean pages without fabricating repair jobs."""

    def __init__(
        self,
        store: PipelineStore,
        gate_runner: GateRunner | None = None,
        final_shape_checker: CleanFinalShapeChecker | None = None,
        rollback_runner: RollbackRunner | None = None,
    ) -> None:
        """Initialize a recoverable clean-adoption coordinator."""
        self.store: PipelineStore = store
        self.intake: AuditIntakeStore = AuditIntakeStore(store)
        self.gate_runner: GateRunner = gate_runner or run_default_site_gates
        self.final_shape_checker: CleanFinalShapeChecker = (
            final_shape_checker or check_clean_adoption_final_shapes
        )
        self.rollback_runner: RollbackRunner = (
            rollback_runner or rematerialize_after_rollback
        )
        self.transactions_root: Path = (
            self.store.root / "clean-adoption-transactions"
        )
        self.transactions_root.mkdir(parents=True, exist_ok=True)

    def run_due(self, *, force: bool = False) -> CleanAdoptionBatchResult:
        """Adopt up to six clean pages after size or wait thresholds."""
        with self.store.coordinator_lock("promotion-batch"):
            self._recover_incomplete_transactions()
            ready = tuple(
                sorted(
                    (
                        item
                        for item in self.intake.list_items()
                        if item.state
                        == AuditIntakeState.CLEAN_ADOPTION_READY
                    ),
                    key=lambda item: (item.updated_at, item.intake_id),
                )
            )
            oldest_wait_ms = (
                round(
                    (
                        datetime.now(UTC) - ready[0].updated_at
                    ).total_seconds()
                    * 1000
                )
                if ready
                else 0
            )
            due = force or (
                len(ready) >= self.store.policy.promotion_batch_size
                or oldest_wait_ms
                >= (
                    self.store.policy.promotion_batch_max_wait_seconds
                    * 1000
                )
            )
            batch_id = uuid.uuid4().hex
            if not ready or not due:
                return CleanAdoptionBatchResult(
                    batch_id=batch_id,
                    due=due,
                    selected_intake_ids=(),
                    adopted_intake_ids=(),
                    gates=None,
                    completed_at=datetime.now(UTC),
                )
            selected = ready[:6]
            targets = self._validate_targets(selected)
            transaction = self._begin_transaction(
                batch_id,
                selected,
                targets,
            )
            try:
                for item, target in zip(
                    selected,
                    targets,
                    strict=True,
                ):
                    candidate = resolve_repo_path(
                        self.store.repo_root,
                        item.normalized_candidate_path,
                    )
                    _atomic_bytes(target, candidate.read_bytes())
                transaction = self._update_transaction(
                    transaction,
                    state="targets_applied",
                )
                log_path = (
                    self.store.root
                    / "clean-adoption-logs"
                    / f"{batch_id}.log"
                )
                with _preserve_active_leases(self.store):
                    gates = self.gate_runner(self.store.repo_root, log_path)
                _require_green_gates(gates)
                self.final_shape_checker(self.store.repo_root, selected)
                transaction = self._update_transaction(
                    transaction,
                    state="gates_passed",
                    gates=gates,
                )
            except Exception:
                self._rollback_transaction(transaction)
                raise
            adopted = self._record_adoptions(
                selected,
                targets,
                gates,
            )
            _ = self._update_transaction(
                transaction,
                state="recorded",
                gates=gates,
            )
            return CleanAdoptionBatchResult(
                batch_id=batch_id,
                due=True,
                selected_intake_ids=tuple(
                    item.intake_id for item in selected
                ),
                adopted_intake_ids=tuple(
                    item.intake_id for item in adopted
                ),
                gates=gates,
                completed_at=datetime.now(UTC),
            )

    def _validate_targets(
        self,
        items: tuple[AuditIntakeItem, ...],
    ) -> tuple[Path, ...]:
        targets: list[Path] = []
        for item in items:
            if item.audit_verdict != "pass":
                message = "clean adoption requires a passing audit"
                raise ValueError(message)
            manifest_path = resolve_repo_path(
                self.store.repo_root,
                item.manifest_path,
            )
            if sha256_path(manifest_path) != item.manifest_sha256:
                message = "clean adoption manifest hash changed"
                raise ValueError(message)
            report_path = resolve_repo_path(
                self.store.repo_root,
                _required(item.audit_report_path),
            )
            if sha256_path(report_path) != item.audit_report_sha256:
                message = "clean adoption audit report hash changed"
                raise ValueError(message)
            validated = validate_deep_audit_report(
                repo_root=self.store.repo_root,
                manifest_path=manifest_path,
                report_path=report_path,
                source_id=item.source_id,
                assigned_reviewer=item.assigned_reviewer,
            )
            if validated.verdict != "pass":
                message = "clean adoption audit is no longer passing"
                raise ValueError(message)
            candidate = resolve_repo_path(
                self.store.repo_root,
                item.normalized_candidate_path,
            )
            if (
                sha256_path(candidate)
                != item.normalized_candidate_sha256
            ):
                message = "clean adoption raw candidate hash changed"
                raise ValueError(message)
            target = _formal_target(self.store.repo_root, item.source_id)
            if (
                target.is_file()
                and sha256_path(target)
                != item.normalized_candidate_sha256
            ):
                message = (
                    "clean adoption refuses to overwrite a different "
                    f"formal candidate: {item.source_id}"
                )
                raise ValueError(message)
            targets.append(target)
        return tuple(targets)

    def _begin_transaction(
        self,
        batch_id: str,
        items: tuple[AuditIntakeItem, ...],
        targets: tuple[Path, ...],
    ) -> CleanAdoptionTransaction:
        transaction_root = self.transactions_root / batch_id
        backups_root = transaction_root / "backups"
        backups: list[PromotionTargetBackup] = []
        for index, (item, target) in enumerate(
            zip(items, targets, strict=True)
        ):
            backup_path: Path | None = None
            backup_sha256: str | None = None
            if target.is_file():
                backup_path = backups_root / f"{index}.md"
                _atomic_bytes(backup_path, target.read_bytes())
                backup_sha256 = sha256_path(backup_path)
            backups.append(
                PromotionTargetBackup(
                    target_path=target.relative_to(
                        self.store.repo_root
                    ).as_posix(),
                    target_sha256=item.normalized_candidate_sha256,
                    was_present=backup_path is not None,
                    backup_path=(
                        backup_path.relative_to(
                            self.store.repo_root
                        ).as_posix()
                        if backup_path is not None
                        else None
                    ),
                    backup_sha256=backup_sha256,
                )
            )
        now = datetime.now(UTC)
        transaction = CleanAdoptionTransaction(
            batch_id=batch_id,
            state="prepared",
            selected_intake_ids=tuple(
                item.intake_id for item in items
            ),
            targets=tuple(backups),
            created_at=now,
            updated_at=now,
        )
        _atomic_model(self._transaction_path(batch_id), transaction)
        return transaction

    def _recover_incomplete_transactions(self) -> None:
        for path in sorted(self.transactions_root.glob("*/intent.json")):
            transaction = CleanAdoptionTransaction.model_validate_json(
                path.read_text(encoding="utf-8-sig")
            )
            if transaction.state in {"recorded", "rolled_back"}:
                continue
            if transaction.state != "gates_passed":
                self._rollback_transaction(transaction)
                continue
            items = tuple(
                self.intake.load(intake_id)
                for intake_id in transaction.selected_intake_ids
            )
            targets = tuple(
                resolve_repo_path(self.store.repo_root, item.target_path)
                for item in transaction.targets
            )
            for target_record, target in zip(
                transaction.targets,
                targets,
                strict=True,
            ):
                if sha256_path(target) != target_record.target_sha256:
                    message = "passed clean adoption target changed"
                    raise ValueError(message)
            gates = transaction.gates
            if gates is None:
                message = "clean adoption transaction lost gate evidence"
                raise ValueError(message)
            self.final_shape_checker(self.store.repo_root, items)
            _ = self._record_adoptions(items, targets, gates)
            _ = self._update_transaction(
                transaction,
                state="recorded",
                gates=gates,
            )

    def _rollback_transaction(
        self,
        transaction: CleanAdoptionTransaction,
    ) -> None:
        if transaction.state in {"recorded", "rolled_back"}:
            return
        for item in transaction.targets:
            target = resolve_repo_path(
                self.store.repo_root,
                item.target_path,
            )
            if item.was_present:
                backup_path = resolve_repo_path(
                    self.store.repo_root,
                    _required(item.backup_path),
                )
                if sha256_path(backup_path) != item.backup_sha256:
                    message = "clean adoption rollback backup changed"
                    raise ValueError(message)
                _atomic_bytes(target, backup_path.read_bytes())
            else:
                target.unlink(missing_ok=True)
        self.rollback_runner(self.store.repo_root)
        _ = self._update_transaction(
            transaction,
            state="rolled_back",
        )

    def _update_transaction(
        self,
        transaction: CleanAdoptionTransaction,
        *,
        state: Literal[
            "prepared",
            "targets_applied",
            "gates_passed",
            "recorded",
            "rolled_back",
        ],
        gates: SiteGateResult | None = None,
    ) -> CleanAdoptionTransaction:
        payload = transaction.model_dump(mode="python")
        payload.update(
            {
                "state": state,
                "gates": gates if gates is not None else transaction.gates,
                "updated_at": datetime.now(UTC),
            }
        )
        updated = CleanAdoptionTransaction.model_validate(payload)
        _atomic_model(self._transaction_path(transaction.batch_id), updated)
        return updated

    def _record_adoptions(
        self,
        items: tuple[AuditIntakeItem, ...],
        targets: tuple[Path, ...],
        gates: SiteGateResult,
    ) -> tuple[AuditIntakeItem, ...]:
        log_path = resolve_repo_path(
            self.store.repo_root,
            gates.log_path,
        )
        log_sha256 = sha256_path(log_path)
        adopted: list[AuditIntakeItem] = []
        for item, target in zip(items, targets, strict=True):
            public_source, public_candidate = _public_paths(
                self.store.repo_root,
                item.source_id,
            )
            evidence = CleanAdoptionEvidence(
                intake_id=item.intake_id,
                source_id=item.source_id,
                assigned_reviewer=item.assigned_reviewer,
                audit_report_path=_required(item.audit_report_path),
                audit_report_sha256=_required(
                    item.audit_report_sha256
                ),
                target_path=target.relative_to(
                    self.store.repo_root
                ).as_posix(),
                target_sha256=item.normalized_candidate_sha256,
                public_source_path=public_source.relative_to(
                    self.store.repo_root
                ).as_posix(),
                public_source_sha256=item.source_sha256,
                public_candidate_path=public_candidate.relative_to(
                    self.store.repo_root
                ).as_posix(),
                public_candidate_sha256=item.candidate_sha256,
                gate_log_path=gates.log_path,
                gate_log_sha256=log_sha256,
                page_tests=gates.page_tests,
                typecheck=gates.typecheck,
                lint=gates.lint,
                materialization=gates.materialization,
                build=gates.build,
                routes=gates.routes,
                recorded_at=datetime.now(UTC),
            )
            evidence_path = (
                self.store.root
                / "clean-adoption-evidence"
                / f"{item.intake_id}.json"
            )
            _atomic_model(evidence_path, evidence)
            adopted.append(
                self.intake.adopt_clean(
                    item.intake_id,
                    evidence_path.relative_to(
                        self.store.repo_root
                    ).as_posix(),
                    actor="clean-adoption-batch",
                )
            )
        return tuple(adopted)

    def _transaction_path(self, batch_id: str) -> Path:
        return self.transactions_root / batch_id / "intent.json"


def run_default_site_gates(repo_root: Path, log_path: Path) -> SiteGateResult:
    """Run the complete local page, type, lint, materialize, build, and route gates."""
    started = datetime.now(UTC)
    python = repo_root / ".ai-local" / "venv" / "Scripts" / "python.exe"
    npm = "npm.cmd" if os.name == "nt" else "npm"
    env = os.environ.copy()
    env["PATH"] = (
        f"{python.parent}{os.pathsep}{env.get('PATH', '')}"
    )
    env["AI_CONTENT_ROOT"] = str(
        (repo_root / "source-ai" / "content").resolve()
    )
    commands = (
        (
            "page-tests",
            (
                str(python),
                "-m",
                "pytest",
                "tests/ai/test_pages.py",
                "tests/ai/test_materialize.py",
                "-q",
            ),
        ),
        (
            "python-lint",
            (
                str(python),
                "-m",
                "ruff",
                "check",
                "scripts/ai",
                "tests/ai",
            ),
        ),
        ("typecheck", (npm, "run", "typecheck")),
        ("typescript-lint", (npm, "run", "lint:ts")),
        ("materialize", (str(python), "-m", "scripts.ai.materialize")),
        ("build-and-routes", (npm, "run", "build")),
    )
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8", newline="\n") as stream:
        for stage, command in commands:
            _ = stream.write(f"## {stage}\n")
            _ = stream.write(f"$ {' '.join(command)}\n")
            _run_site_gate_command(
                stage=stage,
                command=command,
                repo_root=repo_root,
                env=env,
                stream=stream,
            )
    duration_ms = round(
        (datetime.now(UTC) - started).total_seconds() * 1000
    )
    log_value = log_path.relative_to(repo_root).as_posix()
    return SiteGateResult(
        page_tests=True,
        typecheck=True,
        lint=True,
        materialization=True,
        build=True,
        routes=True,
        duration_ms=max(0, duration_ms),
        log_path=log_value,
    )


def _run_site_gate_command(
    *,
    stage: str,
    command: tuple[str, ...],
    repo_root: Path,
    env: dict[str, str],
    stream: TextIO,
) -> None:
    """Run one gate, retrying only transient Windows materialization writes."""
    for attempt in range(len(_WINDOWS_MATERIALIZE_WRITE_RETRY_DELAYS) + 1):
        result = subprocess.run(  # noqa: S603
            command,
            cwd=repo_root,
            env=env,
            check=False,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        output = result.stdout or ""
        _ = stream.write(output)
        if result.returncode == 0:
            return
        can_retry = (
            _IS_WINDOWS
            and stage == "materialize"
            and "WRITE_FAILED: AI handbook materialization failed" in output
            and attempt < len(_WINDOWS_MATERIALIZE_WRITE_RETRY_DELAYS)
        )
        if not can_retry:
            message = (
                f"promotion site gate {stage} failed with exit code "
                f"{result.returncode}"
            )
            raise ValueError(message)
        delay = _WINDOWS_MATERIALIZE_WRITE_RETRY_DELAYS[attempt]
        _ = stream.write(
            f"retrying transient Windows materialization write in {delay}s\n"
        )
        stream.flush()
        time.sleep(delay)


def check_promoted_final_shapes(
    repo_root: Path,
    jobs: tuple[RepairJob, ...],
) -> None:
    """Recompute deterministic final-site-shape evidence after materialization."""
    for job in jobs:
        product, _, slug = job.source_id.partition("/")
        source_path = (
            repo_root / "docs" / "ai" / "en" / product / f"{slug}.md"
        )
        candidate_path = (
            repo_root / "docs" / "ai" / "zh-CN" / product / f"{slug}.md"
        )
        _ = require_final_shape_pair(
            job.source_id,
            source_path,
            candidate_path,
        )


def check_clean_adoption_final_shapes(
    repo_root: Path,
    items: tuple[AuditIntakeItem, ...],
) -> None:
    """Prove the built public pair matches the exact assigned audit pair."""
    for item in items:
        source_path, candidate_path = _public_paths(
            repo_root,
            item.source_id,
        )
        if sha256_path(source_path) != item.source_sha256:
            message = "clean adoption public English hash changed"
            raise ValueError(message)
        if sha256_path(candidate_path) != item.candidate_sha256:
            message = "clean adoption public Chinese hash changed"
            raise ValueError(message)
        _ = require_final_shape_pair(
            item.source_id,
            source_path,
            candidate_path,
        )


def rematerialize_after_rollback(repo_root: Path) -> None:
    """Restore derived docs after a failed batch rolls formal files back."""
    python = repo_root / ".ai-local" / "venv" / "Scripts" / "python.exe"
    env = os.environ.copy()
    env["AI_CONTENT_ROOT"] = str(
        (repo_root / "source-ai" / "content").resolve()
    )
    result = subprocess.run(  # noqa: S603
        (str(python), "-m", "scripts.ai.materialize"),
        cwd=repo_root,
        env=env,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode:
        message = "failed to restore derived AI docs after promotion rollback"
        raise RuntimeError(message)


def _formal_target(repo_root: Path, source_id: str) -> Path:
    product, separator, slug = source_id.partition("/")
    if (
        not separator
        or product not in {"claude-code", "codex"}
        or not slug
        or ".." in slug.split("/")
    ):
        message = "promotion source_id is not a safe AI content route"
        raise ValueError(message)
    return repo_root / "source-ai" / "content" / "zh-CN" / product / f"{slug}.md"


def _public_paths(repo_root: Path, source_id: str) -> tuple[Path, Path]:
    product, separator, slug = source_id.partition("/")
    if (
        not separator
        or product not in {"claude-code", "codex"}
        or not slug
        or ".." in slug.split("/")
    ):
        message = "promotion source_id is not a safe public AI route"
        raise ValueError(message)
    return (
        repo_root / "docs" / "ai" / "en" / product / f"{slug}.md",
        repo_root / "docs" / "ai" / "zh-CN" / product / f"{slug}.md",
    )


def _promotion_ready_at(store: PipelineStore, job: RepairJob) -> datetime:
    event = next(
        (
            item
            for item in reversed(store.events(job.job_id))
            if item.to_state == PipelineState.PROMOTION_READY
        ),
        None,
    )
    if event is None:
        message = "promotion-ready job has no matching transition event"
        raise ValueError(message)
    return event.created_at


def _require_green_gates(gates: SiteGateResult) -> None:
    values = (
        gates.page_tests,
        gates.typecheck,
        gates.lint,
        gates.materialization,
        gates.build,
        gates.routes,
    )
    if not all(values):
        message = "promotion batch contains a failed site gate"
        raise ValueError(message)


def _atomic_model(path: Path, value: BaseModel) -> None:
    _atomic_bytes(
        path,
        value.model_dump_json(indent=2).encode("utf-8") + b"\n",
    )


def _atomic_bytes(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".{uuid.uuid4().hex}.tmp")
    _ = temporary.write_bytes(value)
    _ = temporary.replace(path)


def _required(value: str | None) -> str:
    if value is None:
        message = "promotion candidate provenance is incomplete"
        raise ValueError(message)
    return value

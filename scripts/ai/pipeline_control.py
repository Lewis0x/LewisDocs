# Copyright 2026

"""Quality-gated continuous admission for the local review pipeline."""

from __future__ import annotations

import os
import re
import time
from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING, ClassVar, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from scripts.ai.audit_admission import (
    AuditAdmissionBatch,
    admit_audit_pilot,
)
from scripts.ai.audit_inventory import (
    InventoryStatus,
    build_inventory,
)
from scripts.ai.pipeline import PipelineState, PipelineStore
from scripts.ai.pipeline_intake import AuditIntakeState, AuditIntakeStore

if TYPE_CHECKING:
    from pathlib import Path

_STATUS_REPLACE_ATTEMPTS = 20
_STATUS_RETRY_BASE_SECONDS = 0.05
_STATUS_RETRY_MAX_SECONDS = 0.25


class AdmissionPhase(StrEnum):
    """One observable controller outcome."""

    BOOTSTRAP = "bootstrap"
    WAITING_FOR_QUALITY = "waiting_for_quality"
    PAUSED_ON_QUALITY = "paused_on_quality"
    BACKPRESSURE = "backpressure"
    ADMITTED = "admitted"
    COMPLETE = "complete"


class _StrictModel(BaseModel):
    """Immutable controller record base."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )


class AdmissionControlPolicy(_StrictModel):
    """First-principles quality and WIP limits for continuous admission."""

    version: Literal[1] = 1
    target_wip: int = Field(default=12, ge=1, le=32)
    max_batch_pages: int = Field(default=4, ge=1, le=12)
    minimum_quality_samples: int = Field(default=5, ge=1, le=20)
    minimum_clean_yield: float = Field(default=0.60, ge=0, le=1)
    maximum_post_repair_issue_rate: float = Field(default=0.20, ge=0, le=1)
    maximum_invalid_audit_rate: float = Field(default=0.05, ge=0, le=1)
    review_workflow_version: Literal[2, 3] = 3
    allow_quality_reset: bool = False
    batch_prefix: str = Field(
        default="deep-audit-v3-flow",
        pattern=r"^[a-z0-9][a-z0-9._-]{0,47}$",
    )


class AdmissionQualitySnapshot(_StrictModel):
    """Quality evidence from every controller-managed admission batch."""

    admitted_pages: int = Field(ge=0)
    active_pages: int = Field(ge=0)
    audit_terminal_pages: int = Field(ge=0)
    invalid_audits: int = Field(ge=0)
    final_samples: int = Field(ge=0)
    clean_final_pages: int = Field(ge=0)
    post_repair_issue_pages: int = Field(ge=0)
    clean_yield: float | None = Field(default=None, ge=0, le=1)
    post_repair_issue_rate: float | None = Field(default=None, ge=0, le=1)
    invalid_audit_rate: float | None = Field(default=None, ge=0, le=1)


class AdmissionControlDecision(_StrictModel):
    """Persisted result of one idempotent admission-control cycle."""

    version: Literal[1] = 1
    generated_at: datetime
    phase: AdmissionPhase
    reason: str
    combined_wip: int = Field(ge=0)
    free_slots: int = Field(ge=0)
    eligible_pages: int = Field(ge=0)
    admitted_count: int = Field(ge=0)
    batch_id: str | None = None
    quality: AdmissionQualitySnapshot


def admission_quality_failure(
    policy: AdmissionControlPolicy,
    quality: AdmissionQualitySnapshot,
) -> str | None:
    """Return the first quality rollback reason supported by enough evidence."""
    if (
        quality.audit_terminal_pages >= policy.minimum_quality_samples
        and quality.invalid_audit_rate is not None
        and quality.invalid_audit_rate > policy.maximum_invalid_audit_rate
    ):
        return "deep-audit contract invalid rate exceeds the quality limit"
    if quality.final_samples < policy.minimum_quality_samples:
        return None
    if (
        quality.post_repair_issue_rate is not None
        and quality.post_repair_issue_rate
        > policy.maximum_post_repair_issue_rate
    ):
        return "post-repair full-page issue rate exceeds the quality limit"
    if (
        quality.clean_yield is not None
        and quality.clean_yield < policy.minimum_clean_yield
    ):
        return "clean final-review yield is below the quality limit"
    return None


class ContinuousAuditAdmissionController:
    """Keep deep audit fed while preserving bounded WIP and quality."""

    def __init__(
        self,
        store: PipelineStore,
        *,
        policy: AdmissionControlPolicy | None = None,
    ) -> None:
        """Bind the controller to one canonical local pipeline store."""
        self.store: PipelineStore = store
        self.intake: AuditIntakeStore = AuditIntakeStore(store)
        self.repo_root: Path = store.repo_root
        self.policy: AdmissionControlPolicy = (
            policy or AdmissionControlPolicy()
        )
        self.status_path: Path = (
            store.root / "admission-controller" / "status.json"
        )

    def tick(self) -> AdmissionControlDecision:
        """Evaluate quality and admit one bounded batch when permitted."""
        with self.store.coordinator_lock("continuous-audit-admission"):
            batches = self._load_batches()
            quality = self._quality_snapshot(batches)
            intake_status = self.intake.status()
            combined_wip = (
                intake_status.combined_downstream_wip
                + intake_status.audit_backlog
            )
            free_slots = max(self.policy.target_wip - combined_wip, 0)
            previous = self._load_status()

            if (
                not batches
                and previous is not None
                and previous.phase == AdmissionPhase.PAUSED_ON_QUALITY
                and not self.policy.allow_quality_reset
            ):
                decision = self._decision(
                    AdmissionPhase.PAUSED_ON_QUALITY,
                    "fresh batch prefix cannot bypass the existing quality pause",
                    combined_wip=combined_wip,
                    free_slots=free_slots,
                    quality=previous.quality,
                )
                self._write_status(decision)
                return decision

            quality_failure = admission_quality_failure(
                self.policy,
                quality,
            )
            if quality_failure is not None:
                decision = self._decision(
                    AdmissionPhase.PAUSED_ON_QUALITY,
                    quality_failure,
                    combined_wip=combined_wip,
                    free_slots=free_slots,
                    quality=quality,
                )
                self._write_status(decision)
                return decision

            if batches and quality.final_samples < self.policy.minimum_quality_samples:
                if quality.active_pages == 0:
                    phase = AdmissionPhase.PAUSED_ON_QUALITY
                    reason = (
                        "bounded pilot ended without enough final-review "
                        "quality samples"
                    )
                else:
                    phase = AdmissionPhase.WAITING_FOR_QUALITY
                    reason = (
                        "draining the bounded pilot until enough final-review "
                        "quality samples exist"
                    )
                decision = self._decision(
                    phase,
                    reason,
                    combined_wip=combined_wip,
                    free_slots=free_slots,
                    quality=quality,
                )
                self._write_status(decision)
                return decision

            if free_slots == 0 or intake_status.backpressure:
                decision = self._decision(
                    AdmissionPhase.BACKPRESSURE,
                    "combined downstream WIP is at its configured limit",
                    combined_wip=combined_wip,
                    free_slots=free_slots,
                    quality=quality,
                )
                self._write_status(decision)
                return decision

            inventory = build_inventory(
                self.repo_root,
                pipeline_store=self.store,
                intake_store=self.intake,
            )
            eligible_pages = sum(
                item.status
                in {
                    InventoryStatus.ELIGIBLE_ASSIGNED,
                    InventoryStatus.ELIGIBLE_UNASSIGNED,
                }
                for item in inventory.items
            )
            admit_count = min(
                free_slots,
                eligible_pages,
                self.policy.max_batch_pages,
            )
            if admit_count == 0:
                decision = self._decision(
                    AdmissionPhase.COMPLETE,
                    "no safely eligible source_id remains for admission",
                    combined_wip=combined_wip,
                    free_slots=free_slots,
                    eligible_pages=eligible_pages,
                    quality=quality,
                )
                self._write_status(decision)
                return decision

            batch_id = self._next_batch_id()
            batch = admit_audit_pilot(
                repo_root=self.repo_root,
                intake_store=self.intake,
                batch_id=batch_id,
                max_pages=admit_count,
                actor="continuous-audit-admission",
                review_workflow_version=self.policy.review_workflow_version,
            )
            phase = (
                AdmissionPhase.BOOTSTRAP
                if not batches
                else AdmissionPhase.ADMITTED
            )
            decision = self._decision(
                phase,
                "admitted a bounded reviewer-partitioned deep-audit batch",
                combined_wip=combined_wip,
                free_slots=free_slots,
                eligible_pages=eligible_pages,
                admitted_count=len(batch.admitted),
                batch_id=batch.batch_id,
                quality=quality,
            )
            self._write_status(decision)
            return decision

    def _load_batches(self) -> tuple[AuditAdmissionBatch, ...]:
        root = self.store.root / "admission-batches"
        batches: list[AuditAdmissionBatch] = []
        for path in sorted(root.glob(f"{self.policy.batch_prefix}-*.json")):
            if any(
                path.name.endswith(suffix)
                for suffix in (
                    ".plan.json",
                    ".inventory.json",
                    ".selection.json",
                    ".audit-manifest.json",
                )
            ):
                continue
            batches.append(
                AuditAdmissionBatch.model_validate_json(
                    path.read_text(encoding="utf-8-sig")
                )
            )
        return tuple(batches)

    def _load_status(self) -> AdmissionControlDecision | None:
        if not self.status_path.is_file():
            return None
        return AdmissionControlDecision.model_validate_json(
            self.status_path.read_text(encoding="utf-8-sig")
        )

    def _quality_snapshot(
        self,
        batches: tuple[AuditAdmissionBatch, ...],
    ) -> AdmissionQualitySnapshot:
        jobs_by_attempt = {
            job.attempt_id: job for job in self.store.list_jobs()
        }
        admitted_pages = 0
        active_pages = 0
        audit_terminal_pages = 0
        invalid_audits = 0
        clean_final_pages = 0
        post_repair_issue_pages = 0
        audit_terminal_states = {
            AuditIntakeState.QUEUED_TO_REPAIR,
            AuditIntakeState.CLEAN_ADOPTION_READY,
            AuditIntakeState.CLEAN_ADOPTED,
            AuditIntakeState.STRUCTURAL_BLOCKED,
            AuditIntakeState.INVALID,
        }
        for batch in batches:
            for admitted in batch.admitted:
                admitted_pages += 1
                intake = self.intake.load(admitted.intake_id)
                if intake.state in audit_terminal_states:
                    audit_terminal_pages += 1
                if intake.state == AuditIntakeState.INVALID:
                    invalid_audits += 1
                job = jobs_by_attempt.get(admitted.attempt_id)
                if intake.state in {
                    AuditIntakeState.CLEAN_ADOPTION_READY,
                    AuditIntakeState.CLEAN_ADOPTED,
                }:
                    clean_final_pages += 1
                    continue
                if job is not None and job.state in {
                    PipelineState.PROMOTION_READY,
                    PipelineState.PROMOTED,
                }:
                    clean_final_pages += 1
                    continue
                if job is not None and job.state == PipelineState.ISOLATED:
                    post_repair_issue_pages += 1
                    continue
                if (
                    intake.state
                    not in {
                        AuditIntakeState.STRUCTURAL_BLOCKED,
                        AuditIntakeState.INVALID,
                    }
                    and (
                        job is None
                        or job.state != PipelineState.FAILED_TERMINAL
                    )
                ):
                    active_pages += 1

        final_samples = clean_final_pages + post_repair_issue_pages
        clean_yield = (
            clean_final_pages / final_samples if final_samples else None
        )
        post_repair_issue_rate = (
            post_repair_issue_pages / final_samples if final_samples else None
        )
        invalid_audit_rate = (
            invalid_audits / audit_terminal_pages
            if audit_terminal_pages
            else None
        )
        return AdmissionQualitySnapshot(
            admitted_pages=admitted_pages,
            active_pages=active_pages,
            audit_terminal_pages=audit_terminal_pages,
            invalid_audits=invalid_audits,
            final_samples=final_samples,
            clean_final_pages=clean_final_pages,
            post_repair_issue_pages=post_repair_issue_pages,
            clean_yield=clean_yield,
            post_repair_issue_rate=post_repair_issue_rate,
            invalid_audit_rate=invalid_audit_rate,
        )

    def _next_batch_id(self) -> str:
        root = self.store.root / "admission-batches"
        pattern = re.compile(
            rf"^{re.escape(self.policy.batch_prefix)}-(\d{{4}})(?:\.plan)?\.json$"
        )
        generations = [
            int(match.group(1))
            for path in root.glob(f"{self.policy.batch_prefix}-*.json")
            if (match := pattern.fullmatch(path.name)) is not None
        ]
        generation = max(generations, default=0) + 1
        return f"{self.policy.batch_prefix}-{generation:04d}"

    def _decision(  # noqa: PLR0913
        self,
        phase: AdmissionPhase,
        reason: str,
        *,
        combined_wip: int,
        free_slots: int,
        quality: AdmissionQualitySnapshot,
        eligible_pages: int = 0,
        admitted_count: int = 0,
        batch_id: str | None = None,
    ) -> AdmissionControlDecision:
        return AdmissionControlDecision(
            generated_at=datetime.now(UTC),
            phase=phase,
            reason=reason,
            combined_wip=combined_wip,
            free_slots=free_slots,
            eligible_pages=eligible_pages,
            admitted_count=admitted_count,
            batch_id=batch_id,
            quality=quality,
        )

    def _write_status(self, decision: AdmissionControlDecision) -> None:
        self.status_path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.status_path.with_name(
            f".{self.status_path.name}.{os.getpid()}.{uuid4().hex}.tmp"
        )
        try:
            _ = temp.write_text(
                decision.model_dump_json(indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            for attempt in range(_STATUS_REPLACE_ATTEMPTS):
                try:
                    _ = temp.replace(self.status_path)
                    break
                except PermissionError:
                    if attempt + 1 == _STATUS_REPLACE_ATTEMPTS:
                        raise
                    time.sleep(
                        min(
                            _STATUS_RETRY_BASE_SECONDS * (attempt + 1),
                            _STATUS_RETRY_MAX_SECONDS,
                        )
                    )
        finally:
            temp.unlink(missing_ok=True)

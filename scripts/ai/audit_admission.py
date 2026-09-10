# Copyright 2026

"""Idempotently admit one bounded deep-audit pilot into the canonical intake."""

from __future__ import annotations

import re
import tempfile
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, Final, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from scripts.ai.audit_bridge import (
    DeepAuditManifest,
    DeepAuditManifestEntry,
)
from scripts.ai.audit_inventory import (
    AuditInventory,
    InventoryStatus,
    build_inventory,
    select_pilot,
    write_inventory_atomic,
)
from scripts.ai.audit_preflight import (
    AuditPreflightEvidence,
    inspect_audit_preflight_pair,
)
from scripts.ai.audit_prepare import prepare_deep_audit_manifest
from scripts.ai.final_shape import require_final_shape_pair
from scripts.ai.materialize import derive_review_pair
from scripts.ai.pipeline_intake import (
    AuditIntakeItem,
    AuditIntakeSpec,
    AuditIntakeStore,
)
from scripts.ai.protect import restore_fenced_blocks
from scripts.ai.review_contract import (
    AssignedReviewer,
    resolve_repo_path,
    sha256_path,
)
from scripts.ai.types import SourceId

if TYPE_CHECKING:
    from collections.abc import Iterable

_BATCH_ID_PATTERN = r"^[a-z0-9][a-z0-9._-]{0,63}$"
_REVIEW_WORKFLOW_V3: Final = 3
_NEVER_READMIT_SOURCE_IDS: Final[frozenset[str]] = frozenset(
    {
        # These historical canaries exhausted their bounded repair attempts.
        "codex/agent-configuration/rules",
        "codex/github-action",
    }
)
RepairProvider = Literal["kimi", "glm"]
ReviewWorkflowVersion = Literal[2, 3]


class _StrictModel(BaseModel):
    """Base for immutable admission records."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )


class AuditAdmissionPlanItem(_StrictModel):
    """One source's immutable reviewer, repair lane, and audit identity."""

    source_id: str
    assigned_reviewer: AssignedReviewer
    repair_provider: RepairProvider
    attempt_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{0,79}$")
    audit_lane_index: int = Field(ge=0)
    estimated_work_units: int = Field(ge=1)


class AuditAdmissionPlan(_StrictModel):
    """Crash-safe plan persisted before any source reservation is created."""

    version: Literal[1] = 1
    batch_id: str = Field(pattern=_BATCH_ID_PATTERN)
    inventory_path: str
    inventory_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    selection_path: str
    selection_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    manifest_path: str
    review_workflow_version: ReviewWorkflowVersion = 2
    items: tuple[AuditAdmissionPlanItem, ...] = Field(min_length=1, max_length=12)

    @model_validator(mode="after")
    def _items_are_unique(self) -> AuditAdmissionPlan:
        source_ids = tuple(item.source_id for item in self.items)
        if len(source_ids) != len(set(source_ids)):
            message = "audit admission plan contains duplicate source_id values"
            raise ValueError(message)
        return self


class AdmittedAudit(_StrictModel):
    """One canonical intake created from an immutable admission plan."""

    source_id: str
    intake_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    assigned_reviewer: AssignedReviewer
    repair_provider: RepairProvider
    attempt_id: str


class AuditAdmissionBatch(_StrictModel):
    """Final proof that every planned page was admitted exactly once."""

    version: Literal[1] = 1
    batch_id: str = Field(pattern=_BATCH_ID_PATTERN)
    plan_path: str
    plan_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    manifest_path: str
    manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    admitted: tuple[AdmittedAudit, ...] = Field(min_length=1, max_length=12)

    @model_validator(mode="after")
    def _admitted_sources_are_unique(self) -> AuditAdmissionBatch:
        source_ids = tuple(item.source_id for item in self.admitted)
        if len(source_ids) != len(set(source_ids)):
            message = "audit admission batch contains duplicate source_id values"
            raise ValueError(message)
        return self


def admit_audit_pilot(  # noqa: PLR0913
    *,
    repo_root: Path,
    intake_store: AuditIntakeStore,
    batch_id: str,
    max_pages: int = 12,
    actor: str = "audit-admission",
    review_workflow_version: ReviewWorkflowVersion = 2,
    excluded_source_ids: Iterable[str] = (),
) -> AuditAdmissionBatch:
    """Prepare and admit one resumable reviewer-partitioned pilot batch."""
    _require_batch_id(batch_id)
    root = repo_root.resolve()
    batch_root = intake_store.store.root / "admission-batches"
    final_path = batch_root / f"{batch_id}.json"
    if final_path.is_file():
        result = AuditAdmissionBatch.model_validate_json(
            final_path.read_text(encoding="utf-8-sig")
        )
        _validate_completed_batch(
            root,
            intake_store,
            result,
            review_workflow_version=review_workflow_version,
        )
        return result

    plan_path = batch_root / f"{batch_id}.plan.json"
    plan = (
        _load_plan(
            root,
            plan_path,
            batch_id=batch_id,
            review_workflow_version=review_workflow_version,
        )
        if plan_path.is_file()
        else _create_plan(
            root=root,
            intake_store=intake_store,
            batch_root=batch_root,
            batch_id=batch_id,
            max_pages=max_pages,
            review_workflow_version=review_workflow_version,
            excluded_source_ids=excluded_source_ids,
        )
    )
    manifest_path = resolve_repo_path(root, plan.manifest_path)
    if manifest_path.is_file():
        _validate_manifest_sources(
            root,
            manifest_path,
            _plan_source_ids(plan),
            review_workflow_version=plan.review_workflow_version,
        )
    else:
        _ = prepare_deep_audit_manifest(
            repo_root=root,
            output_path=manifest_path,
            source_ids=_plan_source_ids(plan),
            intake_store=intake_store,
            purpose=(
                f"deep-audit-v{plan.review_workflow_version}-pilot:{batch_id}"
            ),
            review_workflow_version=plan.review_workflow_version,
            assigned_reviewers={
                item.source_id: item.assigned_reviewer
                for item in plan.items
            },
        )

    admitted = tuple(
        _admit_item(
            intake_store=intake_store,
            plan=plan,
            item=item,
            actor=actor,
        )
        for item in plan.items
    )
    result = AuditAdmissionBatch(
        batch_id=batch_id,
        plan_path=_relative(root, plan_path),
        plan_sha256=sha256_path(plan_path),
        manifest_path=plan.manifest_path,
        manifest_sha256=sha256_path(manifest_path),
        admitted=admitted,
    )
    _write_immutable(
        final_path,
        (result.model_dump_json(indent=2) + "\n").encode("utf-8"),
    )
    return result


def assign_repair_providers(
    selections: Iterable[tuple[str, int]],
) -> dict[str, RepairProvider]:
    """Balance future repair work across one Kimi and one GLM lane."""
    loads: dict[RepairProvider, int] = {"kimi": 0, "glm": 0}
    providers: tuple[RepairProvider, ...] = ("kimi", "glm")
    result: dict[str, RepairProvider] = {}
    for source_id, work_units in sorted(
        selections,
        key=lambda value: (-value[1], value[0]),
    ):
        provider = min(
            providers,
            key=lambda value: (loads[value], value),
        )
        result[source_id] = provider
        loads[provider] += work_units
    return result


def _create_plan(  # noqa: PLR0913
    *,
    root: Path,
    intake_store: AuditIntakeStore,
    batch_root: Path,
    batch_id: str,
    max_pages: int,
    review_workflow_version: ReviewWorkflowVersion,
    excluded_source_ids: Iterable[str],
) -> AuditAdmissionPlan:
    inventory = build_inventory(
        root,
        pipeline_store=intake_store.store,
        intake_store=intake_store,
    )
    hard_exclusions = (
        _v3_hard_preflight_exclusions(root, inventory)
        if review_workflow_version == _REVIEW_WORKFLOW_V3
        else ()
    )
    all_exclusions = tuple(
        sorted(
            set(excluded_source_ids)
            .union(hard_exclusions)
            .union(_NEVER_READMIT_SOURCE_IDS)
        )
    )
    selection = select_pilot(
        inventory,
        max_pages=max_pages,
        excluded_source_ids=all_exclusions,
    )
    if selection.selected_count == 0:
        message = (
            f"audit pilot requested {max_pages} pages but only "
            f"{selection.selected_count} are safely eligible"
        )
        raise ValueError(message)
    inventory_path = batch_root / f"{batch_id}.inventory.json"
    selection_path = batch_root / f"{batch_id}.selection.json"
    manifest_path = batch_root / f"{batch_id}.audit-manifest.json"
    _ = write_inventory_atomic(inventory_path, inventory)
    _write_immutable(
        selection_path,
        (selection.model_dump_json(indent=2) + "\n").encode("utf-8"),
    )
    provider_by_source = assign_repair_providers(
        (item.source_id, item.estimated_work_units)
        for item in selection.selections
    )
    items = tuple(
        AuditAdmissionPlanItem(
            source_id=item.source_id,
            assigned_reviewer=item.reviewer,
            repair_provider=provider_by_source[item.source_id],
            attempt_id=f"{batch_id}-{index:02d}",
            audit_lane_index=item.lane_index,
            estimated_work_units=item.estimated_work_units,
        )
        for index, item in enumerate(selection.selections, start=1)
    )
    plan = AuditAdmissionPlan(
        batch_id=batch_id,
        inventory_path=_relative(root, inventory_path),
        inventory_sha256=sha256_path(inventory_path),
        selection_path=_relative(root, selection_path),
        selection_sha256=sha256_path(selection_path),
        manifest_path=_relative(root, manifest_path),
        review_workflow_version=review_workflow_version,
        items=items,
    )
    plan_path = batch_root / f"{batch_id}.plan.json"
    _write_immutable(
        plan_path,
        (plan.model_dump_json(indent=2) + "\n").encode("utf-8"),
    )
    return plan


def _load_plan(
    root: Path,
    plan_path: Path,
    *,
    batch_id: str | None = None,
    review_workflow_version: ReviewWorkflowVersion | None = None,
) -> AuditAdmissionPlan:
    plan = AuditAdmissionPlan.model_validate_json(
        plan_path.read_text(encoding="utf-8-sig")
    )
    if batch_id is not None and plan.batch_id != batch_id:
        message = "audit admission plan belongs to a different batch"
        raise ValueError(message)
    if (
        review_workflow_version is not None
        and plan.review_workflow_version != review_workflow_version
    ):
        message = "audit admission plan uses a different review workflow"
        raise ValueError(message)
    evidence = (
        (plan.inventory_path, plan.inventory_sha256),
        (plan.selection_path, plan.selection_sha256),
    )
    for path_value, expected_hash in evidence:
        if sha256_path(resolve_repo_path(root, path_value)) != expected_hash:
            message = f"audit admission evidence changed: {path_value}"
            raise ValueError(message)
    return plan


def _admit_item(
    *,
    intake_store: AuditIntakeStore,
    plan: AuditAdmissionPlan,
    item: AuditAdmissionPlanItem,
    actor: str,
) -> AdmittedAudit:
    intake = intake_store.create(
        AuditIntakeSpec(
            source_id=item.source_id,
            manifest_path=plan.manifest_path,
            assigned_reviewer=item.assigned_reviewer,
            provider=item.repair_provider,
            attempt_id=item.attempt_id,
        ),
        actor=actor,
    )
    _validate_intake_matches_plan(intake, item)
    return AdmittedAudit(
        source_id=item.source_id,
        intake_id=intake.intake_id,
        assigned_reviewer=item.assigned_reviewer,
        repair_provider=item.repair_provider,
        attempt_id=item.attempt_id,
    )


def _validate_completed_batch(
    root: Path,
    intake_store: AuditIntakeStore,
    batch: AuditAdmissionBatch,
    *,
    review_workflow_version: ReviewWorkflowVersion,
) -> None:
    plan_path = resolve_repo_path(root, batch.plan_path)
    manifest_path = resolve_repo_path(root, batch.manifest_path)
    if sha256_path(plan_path) != batch.plan_sha256:
        message = "completed audit admission plan hash changed"
        raise ValueError(message)
    if sha256_path(manifest_path) != batch.manifest_sha256:
        message = "completed audit admission manifest hash changed"
        raise ValueError(message)
    plan = _load_plan(
        root,
        plan_path,
        batch_id=batch.batch_id,
        review_workflow_version=review_workflow_version,
    )
    _validate_manifest_sources(
        root,
        manifest_path,
        _plan_source_ids(plan),
        review_workflow_version=review_workflow_version,
    )
    expected = {item.source_id: item for item in plan.items}
    if set(expected) != {item.source_id for item in batch.admitted}:
        message = "completed audit admission does not match its plan"
        raise ValueError(message)
    for admitted in batch.admitted:
        intake = intake_store.load(admitted.intake_id)
        _validate_intake_matches_plan(intake, expected[admitted.source_id])


def _validate_intake_matches_plan(
    intake: AuditIntakeItem,
    item: AuditAdmissionPlanItem,
) -> None:
    expected = (
        item.source_id,
        item.assigned_reviewer,
        item.repair_provider,
        item.attempt_id,
    )
    actual = (
        intake.source_id,
        intake.assigned_reviewer,
        intake.provider,
        intake.attempt_id,
    )
    if actual != expected:
        message = "canonical audit intake differs from admission plan"
        raise ValueError(message)


def _validate_manifest_sources(
    root: Path,
    manifest_path: Path,
    expected_source_ids: tuple[str, ...],
    *,
    review_workflow_version: ReviewWorkflowVersion,
) -> None:
    manifest = DeepAuditManifest.model_validate_json(
        manifest_path.read_text(encoding="utf-8-sig")
    )
    entries = tuple(
        DeepAuditManifestEntry.model_validate(value)
        for value in manifest.entries
    )
    actual = tuple(item.source_id for item in entries)
    if actual != expected_source_ids:
        message = "existing audit manifest differs from its admission plan"
        raise ValueError(message)
    if any(
        item.review_workflow_version != review_workflow_version
        for item in entries
    ):
        message = "existing audit manifest uses a different review workflow"
        raise ValueError(message)
    if review_workflow_version == _REVIEW_WORKFLOW_V3:
        for item in entries:
            _validate_v3_preflight(root, item)


def _v3_hard_preflight_exclusions(
    root: Path,
    inventory: AuditInventory,
) -> tuple[str, ...]:
    """Fail closed before selecting pages for a v3 deep-audit pilot."""
    eligible_statuses = {
        InventoryStatus.ELIGIBLE_ASSIGNED,
        InventoryStatus.ELIGIBLE_UNASSIGNED,
    }
    local_root = root / ".ai-local"
    local_root.mkdir(parents=True, exist_ok=True)
    excluded: list[str] = []
    with tempfile.TemporaryDirectory(
        prefix="audit-admission-preflight-",
        dir=local_root,
    ) as temporary_value:
        temporary_root = Path(temporary_value)
        for item in inventory.items:
            if item.status not in eligible_statuses:
                continue
            # Historical GPT translations may be audited, but any repair is
            # still assigned independently to a Kimi or GLM lane.
            if item.translation_provider not in {"kimi", "glm", "gpt"}:
                excluded.append(item.source_id)
                continue
            try:
                raw_source = resolve_repo_path(root, item.english_path)
                raw_candidate = resolve_repo_path(
                    root,
                    item.normalized_candidate_path,
                )
                source_bytes = raw_source.read_bytes()
                restoration = restore_fenced_blocks(
                    source_bytes.decode("utf-8-sig"),
                    raw_candidate.read_bytes().decode("utf-8-sig"),
                )
                public_english, public_chinese = derive_review_pair(
                    SourceId(item.source_id),
                    source_bytes,
                    restoration.text.encode("utf-8"),
                )
                pair_root = temporary_root / item.source_id
                pair_root.mkdir(parents=True, exist_ok=True)
                english_path = pair_root / "en.md"
                chinese_path = pair_root / "zh-CN.md"
                _ = english_path.write_bytes(public_english)
                _ = chinese_path.write_bytes(public_chinese)
                source_path_value = (
                    f".ai-local/audit-materialized/{item.source_id}/en.md"
                )
                candidate_path_value = (
                    f".ai-local/audit-materialized/{item.source_id}/zh-CN.md"
                )
                _ = require_final_shape_pair(
                    item.source_id,
                    english_path,
                    chinese_path,
                    source_path_value=source_path_value,
                    candidate_path_value=candidate_path_value,
                )
                preflight = inspect_audit_preflight_pair(
                    item.source_id,
                    english_path,
                    chinese_path,
                    source_path_value=source_path_value,
                    candidate_path_value=candidate_path_value,
                )
            except (OSError, UnicodeError, ValueError):
                excluded.append(item.source_id)
                continue
            if not preflight.hard_passed:
                excluded.append(item.source_id)
    return tuple(sorted(excluded))


def _validate_v3_preflight(
    root: Path,
    entry: DeepAuditManifestEntry,
) -> None:
    """Require immutable, hard-passing preflight evidence for v3 admission."""
    if entry.preflight_path is None or entry.preflight_sha256 is None:
        message = f"v3 manifest lacks preflight evidence: {entry.source_id}"
        raise ValueError(message)
    preflight_path = resolve_repo_path(root, entry.preflight_path)
    if sha256_path(preflight_path) != entry.preflight_sha256:
        message = f"v3 preflight hash changed: {entry.source_id}"
        raise ValueError(message)
    preflight = AuditPreflightEvidence.model_validate_json(
        preflight_path.read_text(encoding="utf-8-sig")
    )
    if (
        preflight.source_id != entry.source_id
        or preflight.source_sha256 != entry.source_sha256
        or preflight.candidate_sha256 != entry.candidate_sha256
    ):
        message = f"v3 preflight identity differs from manifest: {entry.source_id}"
        raise ValueError(message)
    if not preflight.hard_passed:
        message = f"v3 manifest contains a hard-preflight page: {entry.source_id}"
        raise ValueError(message)


def _plan_source_ids(plan: AuditAdmissionPlan) -> tuple[str, ...]:
    return tuple(item.source_id for item in plan.items)


def _relative(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def _require_batch_id(batch_id: str) -> None:
    if re.fullmatch(_BATCH_ID_PATTERN, batch_id) is None:
        message = "audit admission batch_id is unsafe"
        raise ValueError(message)


def _write_immutable(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        if path.read_bytes() != value:
            message = f"immutable audit admission artifact changed: {path}"
            raise ValueError(message)
        return
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        _ = temporary.write_bytes(value)
        _ = temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)

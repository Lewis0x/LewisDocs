# Copyright 2026

"""Prepare one claimed deep-audit lease for either assigned reviewer."""

from __future__ import annotations

import json
import uuid
from typing import TYPE_CHECKING, ClassVar, Final, Literal, Self, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator

from scripts.ai.audit_bridge import (
    DeepAuditManifest,
    DeepAuditManifestEntry,
    map_reviewed_excerpts_to_raw,
    validate_deep_audit_report,
)
from scripts.ai.audit_context import (
    AuditV3Context,
    build_audit_v3_slice_prompt,
    merge_audit_v3_context_reports,
)
from scripts.ai.audit_coverage import (
    DeepAuditCoverageContract,
    DeepAuditFindingReport,
    build_reviewer_prompt,
    canonicalize_finding_excerpts,
    materialize_coverage_report,
    recover_unique_whitespace_span,
    validate_coverage_contract,
)
from scripts.ai.audit_history import AuditHistoryRecovery
from scripts.ai.audit_preflight import AuditPreflightEvidence
from scripts.ai.audit_v3 import (
    AuditV3Plan,
    AuditV3SliceReport,
    validate_audit_v3_plan,
)
from scripts.ai.pipeline_dispatcher import (
    CompletionEnvelope,
    CompletionKind,
    PipelineDispatcher,
)
from scripts.ai.pipeline_intake import (
    AuditIntakeState,
    AuditIntakeStore,
)
from scripts.ai.review_contract import (
    AssignedReviewer,
    resolve_repo_path,
    sha256_bytes,
    sha256_path,
)

if TYPE_CHECKING:
    from pathlib import Path

    from scripts.ai.pipeline_intake import AuditIntakeItem

_COVERAGE_CONTRACT_VERSION: Final = 2
_REVIEW_WORKFLOW_V2: Final = 2
_REVIEW_WORKFLOW_V3: Final = 3
_T = TypeVar("_T")


class _StrictModel(BaseModel):
    """Base for immutable audit-worker artifacts."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )


class AuditWorkerSliceArtifact(_StrictModel):
    """Prompt and result path for one independently executed v3 slice."""

    slice_id: str
    slice_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    prompt_path: str
    prompt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    schema_path: str
    schema_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    findings_path: str
    status_path: str


class AuditWorkerManifest(_StrictModel):
    """Deterministic files and ownership for one claimed deep audit."""

    version: Literal[1] = 1
    audit_contract_version: Literal[2] = 2
    review_workflow_version: Literal[2, 3] = 2
    response_contract_version: Literal[1] = 1
    intake_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_id: str
    assigned_reviewer: AssignedReviewer
    worker_id: str = Field(min_length=1, max_length=120)
    source_path: str
    candidate_path: str
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    candidate_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    repair_source_path: str | None = None
    repair_candidate_path: str | None = None
    repair_source_sha256: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )
    repair_candidate_sha256: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )
    prompt_path: str
    prompt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    schema_path: str
    schema_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    findings_path: str
    report_path: str
    status_path: str
    coverage_contract: DeepAuditCoverageContract
    v3_context_path: str | None = None
    v3_context_sha256: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )
    v3_plan_path: str | None = None
    v3_plan_sha256: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )
    slices: tuple[AuditWorkerSliceArtifact, ...] = ()

    @model_validator(mode="after")
    def _workflow_artifacts_are_consistent(self) -> Self:
        v3_values = (
            self.v3_context_path,
            self.v3_context_sha256,
            self.v3_plan_path,
            self.v3_plan_sha256,
        )
        repair_values = (
            self.repair_source_path,
            self.repair_candidate_path,
            self.repair_source_sha256,
            self.repair_candidate_sha256,
        )
        if self.review_workflow_version == _REVIEW_WORKFLOW_V2:
            if (
                self.slices
                or any(value is not None for value in v3_values)
                or any(value is not None for value in repair_values)
            ):
                message = "v2 audit worker unexpectedly contains v3 artifacts"
                raise ValueError(message)
            return self
        if (
            not self.slices
            or any(value is None for value in v3_values)
            or any(value is None for value in repair_values)
        ):
            message = "v3 audit worker lacks slice, context, or repair artifacts"
            raise ValueError(message)
        slice_ids = tuple(item.slice_id for item in self.slices)
        if slice_ids != tuple(dict.fromkeys(slice_ids)):
            message = "v3 audit worker repeats a slice id"
            raise ValueError(message)
        return self


def finalize_assigned_audit_worker(
    intake_store: AuditIntakeStore,
    *,
    worker_manifest_path: Path,
    duration_ms: int,
) -> CompletionEnvelope:
    """Validate compact findings, materialize evidence, and submit completion."""
    if duration_ms < 0:
        message = "audit duration cannot be negative"
        raise ValueError(message)
    repo_root = intake_store.store.repo_root
    manifest = AuditWorkerManifest.model_validate_json(
        worker_manifest_path.read_text(encoding="utf-8-sig")
    )
    _ = intake_store.heartbeat(manifest.intake_id, manifest.worker_id)
    item = intake_store.load(manifest.intake_id)
    if item.state != AuditIntakeState.AUDIT_RUNNING:
        message = "audit findings can only finalize a running deep audit"
        raise ValueError(message)
    expected_identity = (
        item.intake_id,
        item.source_id,
        item.assigned_reviewer,
        item.source_sha256,
        item.candidate_sha256,
    )
    actual_identity = (
        manifest.intake_id,
        manifest.source_id,
        manifest.assigned_reviewer,
        manifest.source_sha256,
        manifest.candidate_sha256,
    )
    if actual_identity != expected_identity:
        message = "audit findings manifest differs from its active intake"
        raise ValueError(message)

    source_path = resolve_repo_path(repo_root, manifest.source_path)
    candidate_path = resolve_repo_path(repo_root, manifest.candidate_path)
    prompt_path = resolve_repo_path(repo_root, manifest.prompt_path)
    schema_path = resolve_repo_path(repo_root, manifest.schema_path)
    immutable_files = [
        (source_path, manifest.source_sha256, "source"),
        (candidate_path, manifest.candidate_sha256, "candidate"),
        (prompt_path, manifest.prompt_sha256, "prompt"),
        (schema_path, manifest.schema_sha256, "schema"),
    ]
    if manifest.review_workflow_version == _REVIEW_WORKFLOW_V3:
        immutable_files.extend(
            (
                (
                    resolve_repo_path(
                        repo_root,
                        _required(
                            manifest.repair_source_path,
                            "repair source path",
                        ),
                    ),
                    _required(
                        manifest.repair_source_sha256,
                        "repair source hash",
                    ),
                    "repair source",
                ),
                (
                    resolve_repo_path(
                        repo_root,
                        _required(
                            manifest.repair_candidate_path,
                            "repair candidate path",
                        ),
                    ),
                    _required(
                        manifest.repair_candidate_sha256,
                        "repair candidate hash",
                    ),
                    "repair candidate",
                ),
            )
        )
    for path, expected_sha256, label in immutable_files:
        if sha256_path(path) != expected_sha256:
            message = f"audit worker {label} hash changed"
            raise ValueError(message)
    validate_coverage_contract(
        manifest.coverage_contract,
        english_path=source_path,
        chinese_path=candidate_path,
    )

    findings_path = resolve_repo_path(repo_root, manifest.findings_path)
    raw_findings = (
        _load_v3_findings(
            repo_root=repo_root,
            manifest=manifest,
            source_path=source_path,
            candidate_path=candidate_path,
        )
        if manifest.review_workflow_version == _REVIEW_WORKFLOW_V3
        else DeepAuditFindingReport.model_validate_json(
            findings_path.read_text(encoding="utf-8-sig")
        )
    )
    findings = canonicalize_finding_excerpts(
        raw_findings,
        english_path=source_path,
        chinese_path=candidate_path,
    )
    if findings != raw_findings:
        normalized_path = findings_path.with_name("findings-normalized-v1.json")
        _write_replaceable(
            normalized_path,
            (findings.model_dump_json(indent=2, by_alias=True) + "\n").encode(
                "utf-8"
            ),
        )
    if manifest.review_workflow_version == _REVIEW_WORKFLOW_V3:
        _write_replaceable(
            findings_path,
            (findings.model_dump_json(indent=2, by_alias=True) + "\n").encode(
                "utf-8"
            ),
        )

    report = materialize_coverage_report(
        findings,
        contract=manifest.coverage_contract,
        assigned_reviewer=manifest.assigned_reviewer,
    )
    report_path = resolve_repo_path(repo_root, manifest.report_path)
    _write_replaceable(
        report_path,
        (report.model_dump_json(indent=2, by_alias=True) + "\n").encode("utf-8"),
    )
    _ = validate_deep_audit_report(
        repo_root=repo_root,
        manifest_path=resolve_repo_path(repo_root, item.manifest_path),
        report_path=report_path,
        source_id=manifest.source_id,
        assigned_reviewer=manifest.assigned_reviewer,
    )
    report_sha256 = sha256_path(report_path)
    completion = CompletionEnvelope(
        completion_id=(
            f"deep-audit-{manifest.intake_id[:40]}-{report_sha256[:16]}"
        ),
        kind=CompletionKind.DEEP_AUDIT,
        job_id=manifest.intake_id,
        worker_id=manifest.worker_id,
        report_path=_relative(repo_root, report_path),
        duration_ms=duration_ms,
    )
    _ = PipelineDispatcher(intake_store.store).submit_completion(completion)
    return completion


def prepare_assigned_audit_worker(
    intake_store: AuditIntakeStore,
    *,
    intake_id: str,
    worker_id: str,
) -> AuditWorkerManifest:
    """Bind one active lease to a shared prompt, schema, and report target."""
    _ = intake_store.heartbeat(intake_id, worker_id)
    item = intake_store.load(intake_id)
    if item.state != AuditIntakeState.AUDIT_RUNNING:
        message = "audit worker can only prepare a running deep audit"
        raise ValueError(message)

    repo_root = intake_store.store.repo_root
    manifest_path = resolve_repo_path(repo_root, item.manifest_path)
    entry = _load_entry(manifest_path, item.source_id)
    contract = entry.coverage_contract
    if contract is None:
        message = "v2 audit worker has no coverage contract"
        raise ValueError(message)
    source_path = resolve_repo_path(repo_root, entry.english_path)
    candidate_path = resolve_repo_path(repo_root, entry.chinese_path)
    validate_coverage_contract(
        contract,
        english_path=source_path,
        chinese_path=candidate_path,
    )
    if (
        item.source_sha256 != contract.source_sha256
        or item.candidate_sha256 != contract.candidate_sha256
        or item.assigned_reviewer not in {"gpt-5.6-terra", "grok-4.5"}
    ):
        message = "audit worker identity differs from its intake contract"
        raise ValueError(message)

    if entry.review_workflow_version == _REVIEW_WORKFLOW_V3:
        return _prepare_v3_worker(
            intake_store,
            item=item,
            entry=entry,
            contract=contract,
            worker_id=worker_id,
        )
    return _prepare_v2_worker(
        intake_store,
        item=item,
        entry=entry,
        contract=contract,
        worker_id=worker_id,
    )


def _prepare_v2_worker(
    intake_store: AuditIntakeStore,
    *,
    item: AuditIntakeItem,
    entry: DeepAuditManifestEntry,
    contract: DeepAuditCoverageContract,
    worker_id: str,
) -> AuditWorkerManifest:
    repo_root = intake_store.store.repo_root
    worker_root = (
        intake_store.store.root / "audit-workers" / item.intake_id
    )
    prompt_path = worker_root / "prompt-findings-v1.txt"
    schema_path = worker_root / "report-schema-findings-v1.json"
    findings_path = worker_root / "findings-v1.json"
    status_path = worker_root / "status-findings-v1.json"
    report_path = (
        repo_root
        / ".ai-local"
        / "reviews"
        / "deep-audit-v2"
        / item.attempt_id
        / f"{item.source_id}.json"
    )
    prompt_bytes = build_reviewer_prompt(
        contract,
        assigned_reviewer=item.assigned_reviewer,
    ).encode("utf-8")
    schema_bytes = (
        json.dumps(
            DeepAuditFindingReport.model_json_schema(
                by_alias=True,
                mode="validation",
            ),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    _write_immutable(prompt_path, prompt_bytes)
    _write_immutable(schema_path, schema_bytes)

    prepared = AuditWorkerManifest(
        intake_id=item.intake_id,
        source_id=item.source_id,
        assigned_reviewer=item.assigned_reviewer,
        worker_id=worker_id,
        source_path=entry.english_path,
        candidate_path=entry.chinese_path,
        source_sha256=entry.source_sha256,
        candidate_sha256=entry.candidate_sha256,
        prompt_path=_relative(repo_root, prompt_path),
        prompt_sha256=sha256_path(prompt_path),
        schema_path=_relative(repo_root, schema_path),
        schema_sha256=sha256_path(schema_path),
        findings_path=_relative(repo_root, findings_path),
        report_path=_relative(repo_root, report_path),
        status_path=_relative(repo_root, status_path),
        coverage_contract=contract,
    )
    _write_immutable(
        worker_root / "manifest-findings-v1.json",
        (prepared.model_dump_json(indent=2) + "\n").encode("utf-8"),
    )
    return prepared


def _prepare_v3_worker(
    intake_store: AuditIntakeStore,
    *,
    item: AuditIntakeItem,
    entry: DeepAuditManifestEntry,
    contract: DeepAuditCoverageContract,
    worker_id: str,
) -> AuditWorkerManifest:
    repo_root = intake_store.store.repo_root
    context_path_value = _required(entry.v3_context_path, "v3 context path")
    context_sha256 = _required(entry.v3_context_sha256, "v3 context hash")
    plan_path_value = _required(entry.v3_plan_path, "v3 plan path")
    plan_sha256 = _required(entry.v3_plan_sha256, "v3 plan hash")
    preflight_path_value = _required(entry.preflight_path, "preflight path")
    preflight_sha256 = _required(entry.preflight_sha256, "preflight hash")
    history_path_value = _required(entry.history_path, "history path")
    history_sha256 = _required(entry.history_sha256, "history hash")
    context_path = resolve_repo_path(repo_root, context_path_value)
    plan_path = resolve_repo_path(repo_root, plan_path_value)
    preflight_path = resolve_repo_path(repo_root, preflight_path_value)
    history_path = resolve_repo_path(repo_root, history_path_value)
    immutable = (
        (context_path, context_sha256, "v3 context"),
        (plan_path, plan_sha256, "v3 plan"),
        (preflight_path, preflight_sha256, "preflight"),
        (history_path, history_sha256, "history"),
    )
    for path, expected_sha256, label in immutable:
        if sha256_path(path) != expected_sha256:
            message = f"audit worker {label} hash changed"
            raise ValueError(message)
    context = AuditV3Context.model_validate_json(
        context_path.read_text(encoding="utf-8-sig")
    )
    plan = AuditV3Plan.model_validate_json(
        plan_path.read_text(encoding="utf-8-sig")
    )
    preflight = AuditPreflightEvidence.model_validate_json(
        preflight_path.read_text(encoding="utf-8-sig")
    )
    history = AuditHistoryRecovery.model_validate_json(
        history_path.read_text(encoding="utf-8-sig")
    )
    if (
        context.plan != plan
        or context.preflight != preflight
        or context.history != history
        or context.assigned_reviewer != item.assigned_reviewer
    ):
        message = "v3 audit evidence differs from its assigned context"
        raise ValueError(message)
    validate_audit_v3_plan(plan, contract=contract)
    (
        repair_source_path,
        repair_candidate_path,
        repair_source_sha256,
        repair_candidate_sha256,
    ) = _repair_shape_artifacts(
        repo_root=repo_root,
        source_id=item.source_id,
        entry=entry,
    )

    worker_root = intake_store.store.root / "audit-workers" / item.intake_id
    schema_path = worker_root / "report-schema-slice-v3.json"
    schema_bytes = (
        json.dumps(
            AuditV3SliceReport.model_json_schema(
                by_alias=True,
                mode="validation",
            ),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    _write_immutable(schema_path, schema_bytes)
    slices: list[AuditWorkerSliceArtifact] = []
    for audit_slice in plan.slices:
        prompt_path = worker_root / f"prompt-{audit_slice.slice_id}-v3.txt"
        findings_path = worker_root / f"findings-{audit_slice.slice_id}-v3.json"
        status_path = worker_root / f"status-{audit_slice.slice_id}-v3.json"
        prompt = build_audit_v3_slice_prompt(
            context,
            audit_slice,
            contract=contract,
        )
        prompt_bytes = _append_repair_mapping_contract(
            prompt,
            repair_source_path=_relative(repo_root, repair_source_path),
            repair_candidate_path=_relative(repo_root, repair_candidate_path),
            repair_source_sha256=repair_source_sha256,
            repair_candidate_sha256=repair_candidate_sha256,
        ).encode("utf-8")
        _write_immutable(prompt_path, prompt_bytes)
        slices.append(
            AuditWorkerSliceArtifact(
                slice_id=audit_slice.slice_id,
                slice_sha256=audit_slice.slice_sha256,
                prompt_path=_relative(repo_root, prompt_path),
                prompt_sha256=sha256_path(prompt_path),
                schema_path=_relative(repo_root, schema_path),
                schema_sha256=sha256_path(schema_path),
                findings_path=_relative(repo_root, findings_path),
                status_path=_relative(repo_root, status_path),
            )
        )
    first = slices[0]
    findings_path = worker_root / "findings-merged-v3.json"
    status_path = worker_root / "status-v3.json"
    report_path = (
        repo_root
        / ".ai-local"
        / "reviews"
        / "deep-audit-v3"
        / item.attempt_id
        / f"{item.source_id}.json"
    )
    prepared = AuditWorkerManifest(
        review_workflow_version=3,
        intake_id=item.intake_id,
        source_id=item.source_id,
        assigned_reviewer=item.assigned_reviewer,
        worker_id=worker_id,
        source_path=entry.english_path,
        candidate_path=entry.chinese_path,
        source_sha256=entry.source_sha256,
        candidate_sha256=entry.candidate_sha256,
        repair_source_path=_relative(repo_root, repair_source_path),
        repair_candidate_path=_relative(repo_root, repair_candidate_path),
        repair_source_sha256=repair_source_sha256,
        repair_candidate_sha256=repair_candidate_sha256,
        prompt_path=first.prompt_path,
        prompt_sha256=first.prompt_sha256,
        schema_path=first.schema_path,
        schema_sha256=first.schema_sha256,
        findings_path=_relative(repo_root, findings_path),
        report_path=_relative(repo_root, report_path),
        status_path=_relative(repo_root, status_path),
        coverage_contract=contract,
        v3_context_path=context_path_value,
        v3_context_sha256=context_sha256,
        v3_plan_path=plan_path_value,
        v3_plan_sha256=plan_sha256,
        slices=tuple(slices),
    )
    _write_immutable(
        worker_root / "manifest-findings-v3.json",
        (prepared.model_dump_json(indent=2) + "\n").encode("utf-8"),
    )
    return prepared


def _load_entry(
    manifest_path: Path,
    source_id: str,
) -> DeepAuditManifestEntry:
    manifest = DeepAuditManifest.model_validate_json(
        manifest_path.read_text(encoding="utf-8-sig")
    )
    matches = [
        DeepAuditManifestEntry.model_validate(value)
        for value in manifest.entries
        if value.get("source_id") == source_id
        and value.get("status") == "prepared"
    ]
    if len(matches) != 1:
        message = f"expected one prepared audit worker entry: {source_id}"
        raise ValueError(message)
    if matches[0].audit_contract_version != _COVERAGE_CONTRACT_VERSION:
        message = "audit worker requires a v2 coverage contract"
        raise ValueError(message)
    return matches[0]


def _load_v3_findings(
    *,
    repo_root: Path,
    manifest: AuditWorkerManifest,
    source_path: Path,
    candidate_path: Path,
) -> DeepAuditFindingReport:
    context_path = resolve_repo_path(
        repo_root,
        _required(manifest.v3_context_path, "v3 context path"),
    )
    plan_path = resolve_repo_path(
        repo_root,
        _required(manifest.v3_plan_path, "v3 plan path"),
    )
    if sha256_path(context_path) != _required(
        manifest.v3_context_sha256,
        "v3 context hash",
    ):
        message = "audit worker v3 context hash changed"
        raise ValueError(message)
    if sha256_path(plan_path) != _required(
        manifest.v3_plan_sha256,
        "v3 plan hash",
    ):
        message = "audit worker v3 plan hash changed"
        raise ValueError(message)
    context = AuditV3Context.model_validate_json(
        context_path.read_text(encoding="utf-8-sig")
    )
    plan = AuditV3Plan.model_validate_json(
        plan_path.read_text(encoding="utf-8-sig")
    )
    if context.plan != plan:
        message = "audit worker v3 plan differs from its context"
        raise ValueError(message)
    validate_audit_v3_plan(plan, contract=manifest.coverage_contract)
    expected_slices = {item.slice_id: item for item in manifest.slices}
    if tuple(expected_slices) != tuple(item.slice_id for item in plan.slices):
        message = "audit worker v3 slice artifacts differ from its plan"
        raise ValueError(message)
    reports: list[AuditV3SliceReport] = []
    repair_source_path = resolve_repo_path(
        repo_root,
        _required(manifest.repair_source_path, "repair source path"),
    )
    repair_candidate_path = resolve_repo_path(
        repo_root,
        _required(manifest.repair_candidate_path, "repair candidate path"),
    )
    for audit_slice in plan.slices:
        artifact = expected_slices[audit_slice.slice_id]
        prompt_path = resolve_repo_path(repo_root, artifact.prompt_path)
        schema_path = resolve_repo_path(repo_root, artifact.schema_path)
        if sha256_path(prompt_path) != artifact.prompt_sha256:
            message = f"audit worker prompt hash changed: {artifact.slice_id}"
            raise ValueError(message)
        if sha256_path(schema_path) != artifact.schema_sha256:
            message = f"audit worker schema hash changed: {artifact.slice_id}"
            raise ValueError(message)
        findings_path = resolve_repo_path(repo_root, artifact.findings_path)
        reports.append(
            canonicalize_audit_v3_slice_report(
                AuditV3SliceReport.model_validate_json(
                    findings_path.read_text(encoding="utf-8-sig")
                ),
                source_path=source_path,
                candidate_path=candidate_path,
                repair_source_path=repair_source_path,
                repair_candidate_path=repair_candidate_path,
            )
        )
    merged = merge_audit_v3_context_reports(
        context=context,
        reports=tuple(reports),
        contract=manifest.coverage_contract,
    )
    return canonicalize_finding_excerpts(
        merged,
        english_path=source_path,
        chinese_path=candidate_path,
    )


def canonicalize_audit_v3_slice_report(
    report: AuditV3SliceReport,
    *,
    source_path: Path,
    candidate_path: Path,
    repair_source_path: Path,
    repair_candidate_path: Path,
) -> AuditV3SliceReport:
    """Recover public excerpts and prove their unique raw repair mapping."""
    source = source_path.read_text(encoding="utf-8-sig")
    candidate = candidate_path.read_text(encoding="utf-8-sig")
    repair_source = repair_source_path.read_text(encoding="utf-8-sig")
    repair_candidate = repair_candidate_path.read_text(encoding="utf-8-sig")
    payload = report.model_dump(mode="python", by_alias=True)
    issues: list[dict[str, object]] = []
    for issue in report.issues:
        source_excerpt = recover_unique_whitespace_span(
            source,
            issue.source_excerpt,
            issue_id=issue.issue_id,
            field_name="source_excerpt",
        )
        candidate_span_text = recover_unique_whitespace_span(
            candidate,
            issue.candidate_span_text,
            issue_id=issue.issue_id,
            field_name="candidate_span_text",
        )
        _ = map_reviewed_excerpts_to_raw(
            reviewed_source_excerpt=source_excerpt,
            reviewed_candidate_span=candidate_span_text,
            raw_source=repair_source,
            raw_candidate=repair_candidate,
        )
        issue_payload = issue.model_dump(mode="python", by_alias=True)
        issue_payload["source_excerpt"] = source_excerpt
        issue_payload["candidate_span_text"] = candidate_span_text
        issues.append(issue_payload)
    payload["issues"] = issues
    return AuditV3SliceReport.model_validate(payload)


def _repair_shape_artifacts(
    *,
    repo_root: Path,
    source_id: str,
    entry: DeepAuditManifestEntry,
) -> tuple[Path, Path, str, str]:
    """Resolve and hash the source pair that exact repairs will modify."""
    source_path = (
        repo_root / "source-ai" / "content" / "en" / f"{source_id}.md"
    )
    candidate_path = resolve_repo_path(
        repo_root,
        entry.normalized_candidate_path,
    )
    if not source_path.is_file() or not candidate_path.is_file():
        message = "v3 audit worker repair-shape source pair is incomplete"
        raise ValueError(message)
    source_sha256 = sha256_path(source_path)
    candidate_sha256 = sha256_path(candidate_path)
    if candidate_sha256 != entry.normalized_candidate_sha256:
        message = "v3 audit worker normalized repair candidate hash changed"
        raise ValueError(message)
    return source_path, candidate_path, source_sha256, candidate_sha256


def _append_repair_mapping_contract(
    prompt: str,
    *,
    repair_source_path: str,
    repair_candidate_path: str,
    repair_source_sha256: str,
    repair_candidate_sha256: str,
) -> str:
    """Add the immutable public-to-repair mapping requirement to one prompt."""
    return "\n".join(
        (
            prompt.rstrip(),
            "",
            "RAW REPAIR MAPPING CONTRACT",
            f"English repair-shape file: {repair_source_path}",
            f"Chinese repair-shape file: {repair_candidate_path}",
            f"English repair-shape SHA-256: {repair_source_sha256}",
            f"Chinese repair-shape SHA-256: {repair_candidate_sha256}",
            (
                "Keep source_excerpt and candidate_span_text byte-exact from "
                "the final-shape files named above in the main task."
            ),
            (
                "Before reporting an issue, verify those public excerpts also "
                "map deterministically to exactly one span in the corresponding "
                "repair-shape file. Same-page fragment and localized title "
                "rewrites are the only allowed representation differences."
            ),
            (
                "If an otherwise-correct public excerpt is repeated in a "
                "repair-shape file, lengthen the public excerpt with surrounding "
                "text until the repair mapping is unique. Do not quote raw text "
                "in place of the required public excerpt."
            ),
            "",
        )
    )


def _required(value: _T | None, label: str) -> _T:
    if value is None:
        message = f"audit worker has no {label}"
        raise ValueError(message)
    return value


def _relative(repo_root: Path, path: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def _write_immutable(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        if sha256_path(path) != sha256_bytes(value):
            message = f"immutable audit-worker artifact changed: {path}"
            raise ValueError(message)
        return
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        _ = temporary.write_bytes(value)
        _ = temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _write_replaceable(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        _ = temporary.write_bytes(value)
        _ = temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)

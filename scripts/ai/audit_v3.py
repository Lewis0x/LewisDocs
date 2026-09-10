# Copyright 2026

"""Orthogonal, hash-bound v3 deep-audit planning and deterministic merging."""

from __future__ import annotations

import hashlib
import json
import math
from enum import StrEnum
from typing import Annotated, ClassVar, Final, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)

from scripts.ai.audit_coverage import (
    AuditCategory,
    AuditPass,
    CoverageIssue,
    DeepAuditCoverageContract,
    DeepAuditFindingReport,
)
from scripts.ai.review_contract import AssignedReviewer  # noqa: TC001

__all__ = (
    "AuditComplexity",
    "AuditComplexityMetrics",
    "AuditV3Plan",
    "AuditV3Slice",
    "AuditV3SliceReport",
    "CoverageUnit",
    "MandatoryEvidenceDisposition",
    "build_audit_v3_plan",
    "merge_audit_v3_reports",
    "validate_audit_v3_plan",
)

_HASH_RE: Final = r"^[0-9a-f]{64}$"
_SECTION_ID_RE: Final = (
    r"^(?:frontmatter|preamble|eof|section-[0-9]{4}-[0-9a-f]{12})$"
)
_SLICE_ID_RE: Final = r"^[a-z][a-z0-9-]{0,63}$"
_EVIDENCE_ID_RE: Final = r"^[a-z0-9][a-z0-9._:/-]{0,127}$"
_SIMPLE_MAX_LINES: Final = 400
_SIMPLE_MAX_HEADINGS: Final = 40
_SIMPLE_MAX_LINKS: Final = 60
_SIMPLE_MAX_FENCES: Final = 25
_SIMPLE_MAX_BYTES: Final = 20_000
_EXTREME_MIN_LINES: Final = 1000
_EXTREME_MIN_HEADINGS: Final = 48
_EXTREME_MIN_LINKS: Final = 200
_EXTREME_MIN_BYTES: Final = 60_000
_H2_LEVEL: Final = 2
_MIN_SEMANTIC_GROUPS: Final = 2
_MAX_SEMANTIC_GROUPS: Final = 4

NonEmptyString = Annotated[str, StringConstraints(min_length=1)]
Sha256String = Annotated[str, StringConstraints(pattern=_HASH_RE)]


class _StrictModel(BaseModel):
    """Immutable schema base for every v3 plan and model-authored record."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid",
        frozen=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        use_enum_values=True,
    )


class AuditComplexity(StrEnum):
    """Final-site-shape complexity class used to choose orthogonal slices."""

    SIMPLE = "simple"
    COMPLEX = "complex"
    EXTREME = "extreme"


class AuditComplexityMetrics(_StrictModel):
    """Worst-case deterministic metrics across the English and Chinese page."""

    line_count: int = Field(ge=0)
    heading_count: int = Field(ge=0)
    link_count: int = Field(ge=0)
    fenced_code_count: int = Field(ge=0)
    byte_count: int | None = Field(default=None, ge=0)


class CoverageUnit(_StrictModel):
    """One section/pass pair that must be completed by exactly one slice."""

    section_id: str = Field(pattern=_SECTION_ID_RE)
    audit_pass: AuditPass = Field(alias="pass")


class MandatoryEvidenceDisposition(_StrictModel):
    """Closure status for one historical seed or deterministic preflight fact."""

    evidence_id: str = Field(pattern=_EVIDENCE_ID_RE)
    disposition: Literal[
        "confirmed_clean",
        "issue_reported",
        "not_applicable",
        "unresolved",
    ]
    rationale: NonEmptyString
    issue_ids: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _disposition_is_consistent(self) -> Self:
        if len(self.issue_ids) != len(set(self.issue_ids)):
            message = "mandatory evidence disposition repeats an issue id"
            raise ValueError(message)
        if self.disposition == "issue_reported" and not self.issue_ids:
            message = "issue_reported evidence must reference at least one issue"
            raise ValueError(message)
        if self.disposition != "issue_reported" and self.issue_ids:
            message = "only issue_reported evidence may reference issues"
            raise ValueError(message)
        return self


class AuditV3Slice(_StrictModel):
    """One independently executable, immutable slice of an audit plan."""

    version: Literal[3] = 3
    slice_id: str = Field(pattern=_SLICE_ID_RE)
    slice_sha256: Sha256String
    role: Literal[
        "abc",
        "semantic",
        "surface",
        "coverage",
        "surface_coverage",
        "closure",
        "reconcile",
    ]
    source_id: NonEmptyString
    assigned_reviewer: AssignedReviewer
    coverage_contract_sha256: Sha256String
    source_sha256: Sha256String
    candidate_sha256: Sha256String
    source_eof_line: int = Field(ge=0)
    candidate_eof_line: int = Field(ge=0)
    passes: tuple[AuditPass, ...] = ()
    section_ids: tuple[str, ...] = Field(min_length=1)
    coverage_units: tuple[CoverageUnit, ...] = ()
    mandatory_evidence_ids: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _slice_is_complete_and_hash_bound(self) -> Self:
        passes = tuple(AuditPass(item) for item in self.passes)
        if len(passes) != len(set(passes)):
            message = "audit slice repeats a pass"
            raise ValueError(message)
        if len(self.section_ids) != len(set(self.section_ids)):
            message = "audit slice repeats a section"
            raise ValueError(message)
        if len(self.mandatory_evidence_ids) != len(
            set(self.mandatory_evidence_ids)
        ):
            message = "audit slice repeats mandatory evidence"
            raise ValueError(message)
        auxiliary = _validate_auxiliary_slice(
            role=self.role,
            passes=passes,
            coverage_units=self.coverage_units,
            mandatory_evidence_ids=self.mandatory_evidence_ids,
        )
        if not auxiliary and (not passes or not self.coverage_units):
            message = "primary audit slice requires pass/section coverage"
            raise ValueError(message)
        expected = _coverage_units(passes, self.section_ids)
        if self.coverage_units != expected:
            message = "audit slice coverage units are not its exact pass/section product"
            raise ValueError(message)
        if self.slice_sha256 != _model_sha256(self, exclude={"slice_sha256"}):
            message = "audit slice hash does not match its immutable payload"
            raise ValueError(message)
        return self


class AuditV3Plan(_StrictModel):
    """Complete v3 plan bound to one v2 contract and one assigned reviewer."""

    version: Literal[3] = 3
    plan_sha256: Sha256String
    coverage_contract_sha256: Sha256String
    source_id: NonEmptyString
    assigned_reviewer: AssignedReviewer
    source_sha256: Sha256String
    candidate_sha256: Sha256String
    source_eof_line: int = Field(ge=0)
    candidate_eof_line: int = Field(ge=0)
    complexity: AuditComplexity
    complexity_metrics: AuditComplexityMetrics
    mandatory_evidence_ids: tuple[str, ...] = ()
    slices: tuple[AuditV3Slice, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _plan_is_complete_and_hash_bound(self) -> Self:
        slice_ids = [item.slice_id for item in self.slices]
        if len(slice_ids) != len(set(slice_ids)):
            message = "audit plan repeats a slice id"
            raise ValueError(message)
        if len(self.mandatory_evidence_ids) != len(
            set(self.mandatory_evidence_ids)
        ):
            message = "audit plan repeats mandatory evidence"
            raise ValueError(message)
        expected_complexity = _classify(self.complexity_metrics)
        if AuditComplexity(self.complexity) != expected_complexity:
            message = "audit plan complexity conflicts with final-shape metrics"
            raise ValueError(message)
        _validate_topology(self)
        expected_hashes = {
            _model_sha256(self, exclude={"plan_sha256"}),
        }
        if self.complexity_metrics.byte_count is None:
            expected_hashes.add(_legacy_plan_sha256(self))
        if self.plan_sha256 not in expected_hashes:
            message = "audit plan hash does not match its immutable payload"
            raise ValueError(message)
        return self


class AuditV3SliceReport(_StrictModel):
    """One assigned reviewer completion report for exactly one planned slice."""

    version: Literal[3] = 3
    plan_sha256: Sha256String
    slice_id: str = Field(pattern=_SLICE_ID_RE)
    slice_sha256: Sha256String
    coverage_contract_sha256: Sha256String
    source_id: NonEmptyString
    assigned_reviewer: AssignedReviewer
    review_model: AssignedReviewer
    source_sha256: Sha256String
    candidate_sha256: Sha256String
    source_eof_line: int = Field(ge=0)
    candidate_eof_line: int = Field(ge=0)
    verdict: Literal["pass", "warn", "fail"]
    completed_units: tuple[CoverageUnit, ...] = ()
    reached_assigned_slice_end: Literal[True]
    reached_real_eof: bool
    issue_family_sweep_completed: Literal[True]
    issue_family_checked_issue_ids: tuple[str, ...]
    mandatory_evidence_dispositions: tuple[MandatoryEvidenceDisposition, ...] = ()
    issues: tuple[CoverageIssue, ...]

    @model_validator(mode="after")
    def _report_is_internally_consistent(self) -> Self:
        if self.assigned_reviewer != self.review_model:
            message = "slice report model does not match its assigned reviewer"
            raise ValueError(message)
        if len(self.completed_units) != len(set(self.completed_units)):
            message = "slice report repeats a completed coverage unit"
            raise ValueError(message)
        issue_ids = [item.issue_id for item in self.issues]
        if len(issue_ids) != len(set(issue_ids)):
            message = "slice report repeats an issue id"
            raise ValueError(message)
        if self.issue_family_checked_issue_ids != tuple(issue_ids):
            message = (
                "slice report issue-family closure must list every issue id "
                "once and in report order"
            )
            raise ValueError(message)
        spans = [item.candidate_span_text for item in self.issues]
        if len(spans) != len(set(spans)):
            message = "slice report repeats an exact candidate span"
            raise ValueError(message)
        evidence_ids = [
            item.evidence_id for item in self.mandatory_evidence_dispositions
        ]
        if len(evidence_ids) != len(set(evidence_ids)):
            message = "slice report repeats a mandatory evidence disposition"
            raise ValueError(message)
        expected_verdict = _verdict(self.issues)
        if self.verdict != expected_verdict:
            message = (
                "slice verdict conflicts with issue severities; "
                f"expected {expected_verdict}"
            )
            raise ValueError(message)
        return self


class _SliceIdentity(_StrictModel):
    """Typed immutable identity shared by every slice in one plan."""

    source_id: NonEmptyString
    assigned_reviewer: AssignedReviewer
    coverage_contract_sha256: Sha256String
    source_sha256: Sha256String
    candidate_sha256: Sha256String
    source_eof_line: int = Field(ge=0)
    candidate_eof_line: int = Field(ge=0)


def build_audit_v3_plan(
    *,
    contract: DeepAuditCoverageContract,
    assigned_reviewer: AssignedReviewer,
    mandatory_evidence_ids: tuple[str, ...] = (),
    orthogonal_simple: bool = False,
    adversarial_closure: bool = False,
) -> AuditV3Plan:
    """Build deterministic orthogonal slices without splitting Markdown text."""
    if len(mandatory_evidence_ids) != len(set(mandatory_evidence_ids)):
        message = "mandatory evidence ids must be unique"
        raise ValueError(message)
    metrics = _complexity_metrics(contract)
    complexity = _classify(metrics)
    contract_sha256 = _model_sha256(contract)
    all_sections = tuple(item.section_id for item in contract.sections)
    identity = _SliceIdentity(
        source_id=contract.source_id,
        assigned_reviewer=assigned_reviewer,
        coverage_contract_sha256=contract_sha256,
        source_sha256=contract.source_sha256,
        candidate_sha256=contract.candidate_sha256,
        source_eof_line=contract.evidence.english.eof_line_number,
        candidate_eof_line=contract.evidence.chinese.eof_line_number,
    )
    slices: list[AuditV3Slice]
    if complexity == AuditComplexity.SIMPLE:
        if orthogonal_simple:
            slices = [
                _build_slice(
                    slice_id="semantic",
                    role="semantic",
                    passes=(AuditPass.SEMANTIC,),
                    section_ids=all_sections,
                    mandatory_evidence_ids=(),
                    identity=identity,
                ),
                _build_slice(
                    slice_id="surface-coverage",
                    role="surface_coverage",
                    passes=(AuditPass.SURFACE, AuditPass.COVERAGE),
                    section_ids=all_sections,
                    mandatory_evidence_ids=(),
                    identity=identity,
                ),
            ]
        else:
            slices = [
                _build_slice(
                    slice_id="abc",
                    role="abc",
                    passes=tuple(AuditPass),
                    section_ids=all_sections,
                    mandatory_evidence_ids=(),
                    identity=identity,
                )
            ]
    elif complexity == AuditComplexity.COMPLEX:
        slices = [
            _build_slice(
                slice_id="semantic",
                role="semantic",
                passes=(AuditPass.SEMANTIC,),
                section_ids=all_sections,
                mandatory_evidence_ids=(),
                identity=identity,
            ),
            _build_slice(
                slice_id="surface-coverage",
                role="surface_coverage",
                passes=(AuditPass.SURFACE, AuditPass.COVERAGE),
                section_ids=all_sections,
                mandatory_evidence_ids=(),
                identity=identity,
            ),
        ]
    else:
        semantic_groups = _extreme_semantic_groups(contract, metrics)
        slices = [
            _build_slice(
                slice_id=f"semantic-{index:02d}",
                role="semantic",
                passes=(AuditPass.SEMANTIC,),
                section_ids=section_ids,
                mandatory_evidence_ids=(),
                identity=identity,
            )
            for index, section_ids in enumerate(semantic_groups, start=1)
        ]
        slices.extend(
            (
                _build_slice(
                    slice_id="surface",
                    role="surface",
                    passes=(AuditPass.SURFACE,),
                    section_ids=all_sections,
                    mandatory_evidence_ids=(),
                    identity=identity,
                ),
                _build_slice(
                    slice_id="coverage-global",
                    role="coverage",
                    passes=(AuditPass.COVERAGE,),
                    section_ids=all_sections,
                    mandatory_evidence_ids=(),
                    identity=identity,
                ),
            )
        )
    if adversarial_closure:
        slices.append(
            _build_slice(
                slice_id="adversarial-closure",
                role="closure",
                passes=(),
                section_ids=all_sections,
                mandatory_evidence_ids=(),
                identity=identity,
            )
        )
    if mandatory_evidence_ids:
        slices.append(
            _build_slice(
                slice_id="reconcile-evidence",
                role="reconcile",
                passes=(),
                section_ids=all_sections,
                mandatory_evidence_ids=mandatory_evidence_ids,
                identity=identity,
            )
        )
    value = {
        "version": 3,
        "coverage_contract_sha256": contract_sha256,
        "source_id": contract.source_id,
        "assigned_reviewer": assigned_reviewer,
        "source_sha256": contract.source_sha256,
        "candidate_sha256": contract.candidate_sha256,
        "source_eof_line": contract.evidence.english.eof_line_number,
        "candidate_eof_line": contract.evidence.chinese.eof_line_number,
        "complexity": complexity,
        "complexity_metrics": metrics,
        "mandatory_evidence_ids": mandatory_evidence_ids,
        "slices": tuple(slices),
    }
    return AuditV3Plan(
        plan_sha256=_mapping_sha256(value),
        coverage_contract_sha256=contract_sha256,
        source_id=contract.source_id,
        assigned_reviewer=assigned_reviewer,
        source_sha256=contract.source_sha256,
        candidate_sha256=contract.candidate_sha256,
        source_eof_line=contract.evidence.english.eof_line_number,
        candidate_eof_line=contract.evidence.chinese.eof_line_number,
        complexity=complexity,
        complexity_metrics=metrics,
        mandatory_evidence_ids=mandatory_evidence_ids,
        slices=tuple(slices),
    )


def validate_audit_v3_plan(
    plan: AuditV3Plan,
    *,
    contract: DeepAuditCoverageContract,
) -> None:
    """Rebind a plan to its exact v2 contract and reject hand-authored coverage."""
    contract_sha256 = _model_sha256(contract)
    identity = (
        (plan.coverage_contract_sha256, contract_sha256, "coverage contract hash"),
        (plan.source_id, contract.source_id, "source_id"),
        (plan.source_sha256, contract.source_sha256, "source hash"),
        (plan.candidate_sha256, contract.candidate_sha256, "candidate hash"),
        (
            plan.source_eof_line,
            contract.evidence.english.eof_line_number,
            "source EOF",
        ),
        (
            plan.candidate_eof_line,
            contract.evidence.chinese.eof_line_number,
            "candidate EOF",
        ),
    )
    for actual, expected, label in identity:
        if actual != expected:
            message = f"audit v3 plan {label} does not match its contract"
            raise ValueError(message)
    expected_metrics = _complexity_metrics(contract)
    if plan.complexity_metrics.byte_count is None:
        expected_metrics = expected_metrics.model_copy(update={"byte_count": None})
    if plan.complexity_metrics != expected_metrics:
        message = "audit v3 plan complexity metrics do not match its contract"
        raise ValueError(message)
    for audit_slice in plan.slices:
        _validate_slice_identity(audit_slice, plan)

    expected_units = set(
        _coverage_units(
            tuple(AuditPass),
            tuple(item.section_id for item in contract.sections),
        )
    )
    actual_units = [
        unit for audit_slice in plan.slices for unit in audit_slice.coverage_units
    ]
    if len(actual_units) != len(set(actual_units)):
        message = "audit v3 plan assigns a section/pass unit more than once"
        raise ValueError(message)
    if set(actual_units) != expected_units:
        message = "audit v3 plan does not cover every section/pass unit"
        raise ValueError(message)

    evidence_ids = [
        evidence_id
        for audit_slice in plan.slices
        for evidence_id in audit_slice.mandatory_evidence_ids
    ]
    if tuple(evidence_ids) != plan.mandatory_evidence_ids:
        message = "audit v3 plan does not assign mandatory evidence exactly once"
        raise ValueError(message)
    if AuditComplexity(plan.complexity) == AuditComplexity.EXTREME:
        _validate_extreme_semantic_boundaries(plan, contract)


def merge_audit_v3_reports(
    *,
    plan: AuditV3Plan,
    reports: tuple[AuditV3SliceReport, ...],
    contract: DeepAuditCoverageContract,
) -> DeepAuditFindingReport:
    """Validate every actual slice completion and merge exact-span findings."""
    validate_audit_v3_plan(plan, contract=contract)
    reports_by_slice: dict[str, AuditV3SliceReport] = {}
    for report in reports:
        if report.slice_id in reports_by_slice:
            message = f"duplicate audit v3 report for slice {report.slice_id}"
            raise ValueError(message)
        reports_by_slice[report.slice_id] = report
    expected_slice_ids = tuple(item.slice_id for item in plan.slices)
    if set(reports_by_slice) != set(expected_slice_ids):
        missing = sorted(set(expected_slice_ids).difference(reports_by_slice))
        extra = sorted(set(reports_by_slice).difference(expected_slice_ids))
        message = f"audit v3 slice reports are incomplete; missing={missing}, extra={extra}"
        raise ValueError(message)

    completed_units: list[CoverageUnit] = []
    ordered_issues: list[CoverageIssue] = []
    dispositions: list[MandatoryEvidenceDisposition] = []
    for audit_slice in plan.slices:
        report = reports_by_slice[audit_slice.slice_id]
        validate_audit_v3_slice_report(
            report,
            audit_slice=audit_slice,
            plan=plan,
        )
        completed_units.extend(report.completed_units)
        ordered_issues.extend(report.issues)
        dispositions.extend(report.mandatory_evidence_dispositions)

    expected_units = set(
        _coverage_units(
            tuple(AuditPass),
            tuple(item.section_id for item in contract.sections),
        )
    )
    if len(completed_units) != len(set(completed_units)):
        message = "actual slice completions overlap on a section/pass unit"
        raise ValueError(message)
    if set(completed_units) != expected_units:
        message = "actual slice completions omit required section/pass coverage"
        raise ValueError(message)

    issues, issue_aliases = _merge_exact_spans(tuple(ordered_issues))
    _validate_evidence_closure(
        plan=plan,
        dispositions=tuple(dispositions),
        issues=issues,
        issue_aliases=issue_aliases,
    )
    return DeepAuditFindingReport(
        source_id=plan.source_id,
        review_model=plan.assigned_reviewer,
        verdict=_verdict(issues),
        checked_passes=tuple(AuditPass),
        checked_categories=tuple(AuditCategory),
        checked_section_ids=tuple(item.section_id for item in contract.sections),
        reached_real_eof=True,
        issues=issues,
    )


def validate_audit_v3_slice_report(
    report: AuditV3SliceReport,
    *,
    audit_slice: AuditV3Slice,
    plan: AuditV3Plan,
) -> None:
    """Validate one slice before it is accepted as reusable worker output."""
    _validate_slice_report(report, audit_slice=audit_slice, plan=plan)


def _build_slice(  # noqa: PLR0913
    *,
    slice_id: str,
    role: Literal[
        "abc",
        "semantic",
        "surface",
        "coverage",
        "surface_coverage",
        "closure",
        "reconcile",
    ],
    identity: _SliceIdentity,
    passes: tuple[AuditPass, ...],
    section_ids: tuple[str, ...],
    mandatory_evidence_ids: tuple[str, ...],
) -> AuditV3Slice:
    value = {
        "version": 3,
        "slice_id": slice_id,
        "role": role,
        "source_id": identity.source_id,
        "assigned_reviewer": identity.assigned_reviewer,
        "coverage_contract_sha256": identity.coverage_contract_sha256,
        "source_sha256": identity.source_sha256,
        "candidate_sha256": identity.candidate_sha256,
        "source_eof_line": identity.source_eof_line,
        "candidate_eof_line": identity.candidate_eof_line,
        "passes": passes,
        "section_ids": section_ids,
        "coverage_units": _coverage_units(passes, section_ids),
        "mandatory_evidence_ids": mandatory_evidence_ids,
    }
    return AuditV3Slice(
        slice_sha256=_mapping_sha256(value),
        slice_id=slice_id,
        role=role,
        source_id=identity.source_id,
        assigned_reviewer=identity.assigned_reviewer,
        coverage_contract_sha256=identity.coverage_contract_sha256,
        source_sha256=identity.source_sha256,
        candidate_sha256=identity.candidate_sha256,
        source_eof_line=identity.source_eof_line,
        candidate_eof_line=identity.candidate_eof_line,
        passes=passes,
        section_ids=section_ids,
        coverage_units=_coverage_units(passes, section_ids),
        mandatory_evidence_ids=mandatory_evidence_ids,
    )


def _complexity_metrics(
    contract: DeepAuditCoverageContract,
) -> AuditComplexityMetrics:
    english = contract.evidence.english
    chinese = contract.evidence.chinese
    return AuditComplexityMetrics(
        line_count=max(english.line_count, chinese.line_count),
        heading_count=max(english.heading_count, chinese.heading_count),
        link_count=max(english.link_count, chinese.link_count),
        fenced_code_count=max(
            english.fenced_code_count,
            chinese.fenced_code_count,
        ),
        byte_count=max(english.byte_count, chinese.byte_count),
    )


def _classify(metrics: AuditComplexityMetrics) -> AuditComplexity:
    if (
        metrics.line_count > _EXTREME_MIN_LINES
        or metrics.heading_count > _EXTREME_MIN_HEADINGS
        or metrics.link_count > _EXTREME_MIN_LINKS
        or (
            metrics.byte_count is not None
            and metrics.byte_count > _EXTREME_MIN_BYTES
        )
    ):
        return AuditComplexity.EXTREME
    if (
        metrics.line_count <= _SIMPLE_MAX_LINES
        and metrics.heading_count <= _SIMPLE_MAX_HEADINGS
        and metrics.link_count <= _SIMPLE_MAX_LINKS
        and metrics.fenced_code_count <= _SIMPLE_MAX_FENCES
        and (
            metrics.byte_count is None
            or metrics.byte_count <= _SIMPLE_MAX_BYTES
        )
    ):
        return AuditComplexity.SIMPLE
    return AuditComplexity.COMPLEX


def _coverage_units(
    passes: tuple[AuditPass, ...],
    section_ids: tuple[str, ...],
) -> tuple[CoverageUnit, ...]:
    return tuple(
        CoverageUnit.model_validate(
            {"section_id": section_id, "pass": audit_pass}
        )
        for audit_pass in passes
        for section_id in section_ids
    )


def _logical_subtrees(
    contract: DeepAuditCoverageContract,
) -> tuple[tuple[str, ...], ...]:
    """Return complete, contiguous H2 subtrees plus their structural prefix."""
    groups: list[list[str]] = []
    current: list[str] = []
    for section in contract.sections:
        level = section.english_level or section.chinese_level
        if section.kind == "heading" and level == _H2_LEVEL and current:
            groups.append(current)
            current = []
        current.append(section.section_id)
    if current:
        groups.append(current)
    return tuple(tuple(group) for group in groups)


def _extreme_semantic_groups(
    contract: DeepAuditCoverageContract,
    metrics: AuditComplexityMetrics,
) -> tuple[tuple[str, ...], ...]:
    logical_subtrees = _logical_subtrees(contract)
    requested = min(
        _MAX_SEMANTIC_GROUPS,
        max(
            _MIN_SEMANTIC_GROUPS,
            math.ceil(metrics.line_count / _SIMPLE_MAX_LINES),
            math.ceil(metrics.heading_count / _SIMPLE_MAX_HEADINGS),
            math.ceil(metrics.link_count / _SIMPLE_MAX_LINKS),
            (
                math.ceil(metrics.byte_count / _SIMPLE_MAX_BYTES)
                if metrics.byte_count is not None
                else 0
            ),
        ),
    )
    group_count = min(requested, len(logical_subtrees))
    if group_count < _MIN_SEMANTIC_GROUPS:
        message = (
            "extreme page lacks two complete logical heading groups; "
            "refusing character-based splitting"
        )
        raise ValueError(message)
    return _partition_contiguous(logical_subtrees, group_count)


def _partition_contiguous(
    logical_subtrees: tuple[tuple[str, ...], ...],
    group_count: int,
) -> tuple[tuple[str, ...], ...]:
    """Balance contiguous section groups while keeping every subtree intact."""
    output: list[tuple[str, ...]] = []
    cursor = 0
    for group_index in range(group_count):
        groups_left = group_count - group_index
        remaining = logical_subtrees[cursor:]
        if groups_left == 1:
            chosen = remaining
        else:
            remaining_weight = sum(len(item) for item in remaining)
            target = remaining_weight / groups_left
            take = 0
            weight = 0
            max_take = len(remaining) - (groups_left - 1)
            while take < max_take:
                next_weight = len(remaining[take])
                if take and abs(weight - target) <= abs(
                    weight + next_weight - target
                ):
                    break
                weight += next_weight
                take += 1
            chosen = remaining[: max(1, take)]
        output.append(tuple(section for subtree in chosen for section in subtree))
        cursor += len(chosen)
    return tuple(output)


def _primary_topology(roles: tuple[str, ...]) -> tuple[str, ...]:
    if "reconcile" in roles:
        if roles[-1] != "reconcile" or roles.count("reconcile") != 1:
            message = "audit reconciliation slice must be unique and last"
            raise ValueError(message)
        roles = roles[:-1]
    if "closure" in roles:
        if roles[-1] != "closure" or roles.count("closure") != 1:
            message = "adversarial closure slice must be unique and last"
            raise ValueError(message)
        roles = roles[:-1]
    return roles


def _validate_topology(plan: AuditV3Plan) -> None:
    complexity = AuditComplexity(plan.complexity)
    roles = _primary_topology(tuple(item.role for item in plan.slices))
    if complexity == AuditComplexity.SIMPLE:
        if roles == ("abc",):
            if tuple(
                AuditPass(item) for item in plan.slices[0].passes
            ) != tuple(AuditPass):
                message = "simple ABC audit plan has incomplete passes"
                raise ValueError(message)
            return
        if roles != ("semantic", "surface_coverage"):
            message = (
                "simple audit plan must use ABC or orthogonal "
                "semantic plus surface/coverage slices"
            )
            raise ValueError(message)
        return
    if complexity == AuditComplexity.COMPLEX:
        if roles != ("semantic", "surface_coverage"):
            message = "complex audit plan must separate semantic and surface/coverage"
            raise ValueError(message)
        return
    semantic_count = sum(role == "semantic" for role in roles)
    if (
        not _MIN_SEMANTIC_GROUPS
        <= semantic_count
        <= _MAX_SEMANTIC_GROUPS
        or roles[-2:] != ("surface", "coverage")
        or any(role != "semantic" for role in roles[:-2])
    ):
        message = (
            "extreme audit plan requires 2-4 semantic slices plus independent "
            "surface and coverage slices"
        )
        raise ValueError(message)


def _validate_auxiliary_slice(
    *,
    role: str,
    passes: tuple[AuditPass, ...],
    coverage_units: tuple[CoverageUnit, ...],
    mandatory_evidence_ids: tuple[str, ...],
) -> bool:
    if role == "reconcile":
        if passes or coverage_units:
            message = "reconciliation slice cannot claim primary coverage units"
            raise ValueError(message)
        if not mandatory_evidence_ids:
            message = "reconciliation slice requires mandatory evidence"
            raise ValueError(message)
        return True
    if role != "closure":
        return False
    if passes or coverage_units or mandatory_evidence_ids:
        message = (
            "adversarial closure cannot claim primary coverage "
            "or mandatory evidence"
        )
        raise ValueError(message)
    return True


def _validate_slice_identity(audit_slice: AuditV3Slice, plan: AuditV3Plan) -> None:
    identity = (
        (audit_slice.source_id, plan.source_id, "source_id"),
        (
            audit_slice.assigned_reviewer,
            plan.assigned_reviewer,
            "assigned reviewer",
        ),
        (
            audit_slice.coverage_contract_sha256,
            plan.coverage_contract_sha256,
            "contract hash",
        ),
        (audit_slice.source_sha256, plan.source_sha256, "source hash"),
        (audit_slice.candidate_sha256, plan.candidate_sha256, "candidate hash"),
        (audit_slice.source_eof_line, plan.source_eof_line, "source EOF"),
        (
            audit_slice.candidate_eof_line,
            plan.candidate_eof_line,
            "candidate EOF",
        ),
    )
    for actual, expected, label in identity:
        if actual != expected:
            message = f"audit slice {audit_slice.slice_id} {label} mismatch"
            raise ValueError(message)


def _validate_extreme_semantic_boundaries(
    plan: AuditV3Plan,
    contract: DeepAuditCoverageContract,
) -> None:
    owner = {
        section_id: audit_slice.slice_id
        for audit_slice in plan.slices
        if audit_slice.role == "semantic"
        for section_id in audit_slice.section_ids
    }
    for subtree in _logical_subtrees(contract):
        owners = {owner[section_id] for section_id in subtree}
        if len(owners) != 1:
            message = "extreme semantic plan splits a complete H2 subtree"
            raise ValueError(message)


def _validate_slice_report(
    report: AuditV3SliceReport,
    *,
    audit_slice: AuditV3Slice,
    plan: AuditV3Plan,
) -> None:
    identity = (
        (report.plan_sha256, plan.plan_sha256, "plan hash"),
        (report.slice_sha256, audit_slice.slice_sha256, "slice hash"),
        (
            report.coverage_contract_sha256,
            plan.coverage_contract_sha256,
            "contract hash",
        ),
        (report.source_id, plan.source_id, "source_id"),
        (report.assigned_reviewer, plan.assigned_reviewer, "assigned reviewer"),
        (report.review_model, plan.assigned_reviewer, "review model"),
        (report.source_sha256, plan.source_sha256, "source hash"),
        (report.candidate_sha256, plan.candidate_sha256, "candidate hash"),
        (report.source_eof_line, plan.source_eof_line, "source EOF"),
        (report.candidate_eof_line, plan.candidate_eof_line, "candidate EOF"),
    )
    for actual, expected, label in identity:
        if actual != expected:
            message = f"slice report {report.slice_id} {label} mismatch"
            raise ValueError(message)
    if report.completed_units != audit_slice.coverage_units:
        message = f"slice report {report.slice_id} did not complete its actual units"
        raise ValueError(message)
    if audit_slice.role == "closure" and not report.reached_real_eof:
        message = (
            f"slice report {report.slice_id} did not complete the adversarial "
            "full-page read"
        )
        raise ValueError(message)
    if any(
        AuditPass(unit.audit_pass) == AuditPass.COVERAGE
        and unit.section_id == "eof"
        for unit in report.completed_units
    ) and not report.reached_real_eof:
        message = f"slice report {report.slice_id} did not reach the true EOF"
        raise ValueError(message)
    completed = set(report.completed_units)
    evidence_issue_ids = {
        issue_id
        for disposition in report.mandatory_evidence_dispositions
        if disposition.disposition == "issue_reported"
        for issue_id in disposition.issue_ids
    }
    for issue in report.issues:
        unit = CoverageUnit.model_validate(
            {"section_id": issue.section_id, "pass": issue.audit_pass}
        )
        if (
            audit_slice.role != "closure"
            and unit not in completed
            and issue.issue_id not in evidence_issue_ids
        ):
            message = (
                f"issue {issue.issue_id} lies outside slice "
                f"{report.slice_id} completion"
            )
            raise ValueError(message)
    disposition_ids = tuple(
        item.evidence_id for item in report.mandatory_evidence_dispositions
    )
    if disposition_ids != audit_slice.mandatory_evidence_ids:
        message = (
            f"slice report {report.slice_id} did not disposition every "
            "mandatory evidence id"
        )
        raise ValueError(message)


def _merge_exact_spans(
    issues: tuple[CoverageIssue, ...],
) -> tuple[tuple[CoverageIssue, ...], dict[str, str]]:
    by_span: dict[str, list[CoverageIssue]] = {}
    by_issue_id: dict[str, str] = {}
    aliases: dict[str, str] = {}
    for issue in issues:
        prior_span = by_issue_id.get(issue.issue_id)
        if prior_span is not None and prior_span != issue.candidate_span_text:
            message = f"issue id {issue.issue_id} refers to conflicting exact spans"
            raise ValueError(message)
        by_issue_id[issue.issue_id] = issue.candidate_span_text
        by_span.setdefault(issue.candidate_span_text, []).append(issue)

    output: list[CoverageIssue] = []
    for group in by_span.values():
        merged = _merge_span_group(tuple(group))
        output.append(merged)
        for issue in group:
            aliases[issue.issue_id] = merged.issue_id
    return tuple(output), aliases


def _merge_span_group(
    issues: tuple[CoverageIssue, ...],
) -> CoverageIssue:
    """Conserve every orthogonal finding while keeping one repair-safe span."""
    severity_order = {"high": 0, "medium": 1, "low": 2}
    pass_order = {
        AuditPass.SEMANTIC: 0,
        AuditPass.SURFACE: 1,
        AuditPass.COVERAGE: 2,
    }
    canonical = min(
        issues,
        key=lambda issue: (
            severity_order[issue.severity],
            pass_order[AuditPass(issue.audit_pass)],
            str(issue.category),
            issue.issue_id,
        ),
    )
    payloads = []
    for issue in issues:
        payload = issue.model_dump(mode="json", by_alias=True)
        del payload["issue_id"]
        payloads.append(payload)
    if all(payload == payloads[0] for payload in payloads[1:]):
        return canonical

    explanations = tuple(
        dict.fromkeys(
            (
                f"[{issue.audit_pass}/{issue.category}/{issue.issue_id}] "
                f"Source: {issue.source_excerpt} Finding: {issue.explanation}"
            )
            for issue in issues
        )
    )
    return CoverageIssue.model_validate(
        {
            **canonical.model_dump(mode="json", by_alias=True),
            "explanation": "\n".join(explanations),
        }
    )


def _validate_evidence_closure(
    *,
    plan: AuditV3Plan,
    dispositions: tuple[MandatoryEvidenceDisposition, ...],
    issues: tuple[CoverageIssue, ...],
    issue_aliases: dict[str, str],
) -> None:
    evidence_ids = tuple(item.evidence_id for item in dispositions)
    if evidence_ids != plan.mandatory_evidence_ids:
        message = "mandatory evidence was not dispositioned exactly once"
        raise ValueError(message)
    if any(item.disposition == "unresolved" for item in dispositions):
        message = "mandatory evidence remains unresolved; clean merge is forbidden"
        raise ValueError(message)
    merged_issue_ids = {item.issue_id for item in issues}
    for item in dispositions:
        if item.disposition != "issue_reported":
            continue
        canonical_ids = {
            issue_aliases.get(issue_id, issue_id) for issue_id in item.issue_ids
        }
        if not canonical_ids.issubset(merged_issue_ids):
            message = (
                f"mandatory evidence {item.evidence_id} references an unknown issue"
            )
            raise ValueError(message)


def _verdict(
    issues: tuple[CoverageIssue, ...],
) -> Literal["pass", "warn", "fail"]:
    if any(item.severity == "high" for item in issues):
        return "fail"
    if issues:
        return "warn"
    return "pass"


def _model_sha256(
    model: BaseModel,
    *,
    exclude: set[str] | None = None,
) -> str:
    return _mapping_sha256(
        model.model_dump(mode="json", by_alias=True, exclude=exclude or set())
    )


def _legacy_plan_sha256(plan: AuditV3Plan) -> str:
    """Validate plans created before byte-aware complexity was introduced."""
    payload = plan.model_dump(
        mode="json",
        by_alias=True,
        exclude={"plan_sha256"},
    )
    metrics = payload["complexity_metrics"]
    if not isinstance(metrics, dict):
        message = "audit plan complexity metrics are not a JSON object"
        raise TypeError(message)
    metrics.pop("byte_count", None)
    return _mapping_sha256(payload)


def _mapping_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        default=_json_default,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _json_default(value: object) -> object:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json", by_alias=True)
    message = f"{type(value).__name__} is not canonical-JSON serializable"
    raise TypeError(message)

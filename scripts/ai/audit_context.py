# Copyright 2026

"""Hash-bound v3 audit context built from local and historical evidence."""

from __future__ import annotations

import hashlib
import json
from enum import StrEnum
from typing import ClassVar, Literal, Self, cast

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from scripts.ai.audit_coverage import (  # noqa: TC001
    DeepAuditCoverageContract,
    DeepAuditFindingReport,
)
from scripts.ai.audit_history import (  # noqa: TC001
    AuditHistoryRecovery,
    HistoricalIssueRecovery,
)
from scripts.ai.audit_preflight import (
    AuditPreflightEvidence,
    PreflightFinding,
    PreflightSeverity,
)
from scripts.ai.audit_v3 import (
    AuditV3Plan,
    AuditV3Slice,
    AuditV3SliceReport,
    build_audit_v3_plan,
    merge_audit_v3_reports,
    validate_audit_v3_plan,
)
from scripts.ai.review_contract import AssignedReviewer, sha256_text

__all__ = (
    "AuditEvidenceKind",
    "AuditEvidenceRequirement",
    "AuditV3Context",
    "AuditV3MandatoryEvidence",
    "build_audit_v3_context",
    "build_audit_v3_slice_prompt",
    "merge_audit_v3_context_reports",
)

_HASH_RE = r"^[0-9a-f]{64}$"
_EVIDENCE_ID_RE = r"^[a-z0-9][a-z0-9._:/-]{0,127}$"
_MAX_MANDATORY_PREFLIGHT_HINTS = 4
_PREFLIGHT_HINT_PRIORITY = {
    "identical_user_facing_fence": 0,
    "candidate_only_truncation_marker": 1,
    "visible_english_link_label": 2,
}


class AuditEvidenceKind(StrEnum):
    """Origin and confidence class for mandatory reviewer evidence."""

    PREFLIGHT_HARD = "preflight_hard"
    PREFLIGHT_HINT = "preflight_hint"
    HISTORY_CARRY = "history_carry"
    HISTORY_RECONCILE = "history_reconcile"


class AuditEvidenceRequirement(StrEnum):
    """Minimum acceptable reviewer disposition for one evidence item."""

    ISSUE_REQUIRED = "issue_required"
    ISSUE_OR_BLOCK = "issue_or_block"
    REVIEW_REQUIRED = "review_required"


class _StrictModel(BaseModel):
    """Immutable evidence base."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
        use_enum_values=True,
    )


class AuditV3MandatoryEvidence(_StrictModel):
    """One exact fact that a planned v3 slice must explicitly close."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=False,
        use_enum_values=True,
    )

    evidence_id: str = Field(pattern=_EVIDENCE_ID_RE)
    kind: AuditEvidenceKind
    severity: Literal["high", "medium", "low"]
    requirement: AuditEvidenceRequirement
    summary: str = Field(min_length=1)
    source_excerpt: str = ""
    candidate_span_text: str = ""
    candidate_span_sha256: str | None = Field(
        default=None,
        pattern=_HASH_RE,
    )
    origin_ids: tuple[str, ...] = Field(min_length=1)
    report_paths: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _span_and_origin_are_consistent(self) -> Self:
        if bool(self.candidate_span_text) != bool(self.candidate_span_sha256):
            message = "mandatory evidence span and hash must be present together"
            raise ValueError(message)
        if (
            self.candidate_span_text
            and self.candidate_span_sha256
            != sha256_text(self.candidate_span_text)
        ):
            message = "mandatory evidence candidate span hash does not match"
            raise ValueError(message)
        if self.origin_ids != tuple(sorted(set(self.origin_ids))):
            message = "mandatory evidence origin ids must be unique and sorted"
            raise ValueError(message)
        if self.report_paths != tuple(sorted(set(self.report_paths))):
            message = "mandatory evidence report paths must be unique and sorted"
            raise ValueError(message)
        if (
            self.requirement == AuditEvidenceRequirement.ISSUE_REQUIRED
            and not self.candidate_span_text
        ):
            message = "issue-required evidence needs an exact candidate span"
            raise ValueError(message)
        return self


class AuditV3Context(_StrictModel):
    """Complete local evidence and immutable plan for one assigned reviewer."""

    version: Literal[3] = 3
    context_sha256: str = Field(pattern=_HASH_RE)
    source_id: str = Field(min_length=1)
    assigned_reviewer: AssignedReviewer
    source_path: str = Field(min_length=1)
    candidate_path: str = Field(min_length=1)
    source_sha256: str = Field(pattern=_HASH_RE)
    candidate_sha256: str = Field(pattern=_HASH_RE)
    preflight: AuditPreflightEvidence
    history: AuditHistoryRecovery
    mandatory_evidence: tuple[AuditV3MandatoryEvidence, ...]
    plan: AuditV3Plan

    @field_validator("source_path", "candidate_path")
    @classmethod
    def _relative_path(cls, value: str) -> str:
        normalized = value.replace("\\", "/")
        if (
            normalized.startswith("/")
            or ":" in normalized.split("/", maxsplit=1)[0]
            or ".." in normalized.split("/")
        ):
            message = "audit v3 context paths must be repository-relative"
            raise ValueError(message)
        return normalized

    @model_validator(mode="after")
    def _identity_and_hash_are_consistent(self) -> Self:
        identities = (
            (self.preflight.source_id, self.source_id, "preflight source_id"),
            (self.history.source_id, self.source_id, "history source_id"),
            (self.plan.source_id, self.source_id, "plan source_id"),
            (
                self.history.assigned_reviewer,
                self.assigned_reviewer,
                "history reviewer",
            ),
            (
                self.plan.assigned_reviewer,
                self.assigned_reviewer,
                "plan reviewer",
            ),
            (
                self.preflight.source_sha256,
                self.source_sha256,
                "preflight source hash",
            ),
            (
                self.preflight.candidate_sha256,
                self.candidate_sha256,
                "preflight candidate hash",
            ),
            (
                self.history.english_sha256,
                self.source_sha256,
                "history source hash",
            ),
            (
                self.history.chinese_sha256,
                self.candidate_sha256,
                "history candidate hash",
            ),
            (self.plan.source_sha256, self.source_sha256, "plan source hash"),
            (
                self.plan.candidate_sha256,
                self.candidate_sha256,
                "plan candidate hash",
            ),
        )
        for actual, expected, label in identities:
            if actual != expected:
                message = f"audit v3 context {label} mismatch"
                raise ValueError(message)
        evidence_ids = tuple(item.evidence_id for item in self.mandatory_evidence)
        if evidence_ids != tuple(sorted(set(evidence_ids))):
            message = "mandatory evidence must be unique and sorted by id"
            raise ValueError(message)
        if evidence_ids != self.plan.mandatory_evidence_ids:
            message = "audit v3 plan does not bind the context evidence ids"
            raise ValueError(message)
        if self.context_sha256 != _model_sha256(
            self,
            exclude={"context_sha256"},
        ):
            message = "audit v3 context hash does not match its payload"
            raise ValueError(message)
        return self


def build_audit_v3_context(
    *,
    contract: DeepAuditCoverageContract,
    assigned_reviewer: AssignedReviewer,
    preflight: AuditPreflightEvidence,
    history: AuditHistoryRecovery,
) -> AuditV3Context:
    """Build a deterministic plan that cannot omit local or historical evidence."""
    identities = (
        (preflight.source_id, contract.source_id, "preflight source_id"),
        (history.source_id, contract.source_id, "history source_id"),
        (history.assigned_reviewer, assigned_reviewer, "history reviewer"),
        (preflight.source_path, contract.english_path, "preflight source path"),
        (
            preflight.candidate_path,
            contract.chinese_path,
            "preflight candidate path",
        ),
        (history.english_path, contract.english_path, "history source path"),
        (history.chinese_path, contract.chinese_path, "history candidate path"),
        (preflight.source_sha256, contract.source_sha256, "preflight source hash"),
        (
            preflight.candidate_sha256,
            contract.candidate_sha256,
            "preflight candidate hash",
        ),
        (history.english_sha256, contract.source_sha256, "history source hash"),
        (
            history.chinese_sha256,
            contract.candidate_sha256,
            "history candidate hash",
        ),
    )
    for actual, expected, label in identities:
        if actual != expected:
            message = f"cannot build audit v3 context: {label} mismatch"
            raise ValueError(message)

    evidence = tuple(
        sorted(
            (
                *(
                    _preflight_evidence(item)
                    for item in _selected_preflight_findings(preflight)
                ),
                *(
                    _history_evidence(item)
                    for item in history.issues
                    if item.disposition in {"carry-forward", "needs-reconcile"}
                ),
            ),
            key=lambda item: item.evidence_id,
        )
    )
    plan = build_audit_v3_plan(
        contract=contract,
        assigned_reviewer=assigned_reviewer,
        mandatory_evidence_ids=tuple(item.evidence_id for item in evidence),
        orthogonal_simple=True,
        adversarial_closure=True,
    )
    value = {
        "version": 3,
        "source_id": contract.source_id,
        "assigned_reviewer": assigned_reviewer,
        "source_path": contract.english_path,
        "candidate_path": contract.chinese_path,
        "source_sha256": contract.source_sha256,
        "candidate_sha256": contract.candidate_sha256,
        "preflight": preflight,
        "history": history,
        "mandatory_evidence": evidence,
        "plan": plan,
    }
    return AuditV3Context(
        context_sha256=_mapping_sha256(value),
        source_id=contract.source_id,
        assigned_reviewer=assigned_reviewer,
        source_path=contract.english_path,
        candidate_path=contract.chinese_path,
        source_sha256=contract.source_sha256,
        candidate_sha256=contract.candidate_sha256,
        preflight=preflight,
        history=history,
        mandatory_evidence=evidence,
        plan=plan,
    )


def build_audit_v3_slice_prompt(
    context: AuditV3Context,
    audit_slice: AuditV3Slice,
    *,
    contract: DeepAuditCoverageContract,
) -> str:
    """Render one independent reviewer prompt from immutable v3 artifacts."""
    validate_audit_v3_plan(context.plan, contract=contract)
    matching = tuple(
        item
        for item in context.plan.slices
        if item.slice_id == audit_slice.slice_id
    )
    if matching != (audit_slice,):
        message = "audit v3 slice is not the exact slice bound to its context"
        raise ValueError(message)
    evidence_by_id = {
        item.evidence_id: item for item in context.mandatory_evidence
    }
    evidence = tuple(
        evidence_by_id[evidence_id]
        for evidence_id in audit_slice.mandatory_evidence_ids
    )
    sections = tuple(
        item.model_dump(mode="json")
        for item in contract.sections
        if item.section_id in set(audit_slice.section_ids)
    )
    categories = tuple(
        item.model_dump(mode="json", by_alias=True)
        for item in contract.mandatory_categories
        if (
            audit_slice.role == "closure"
            or item.audit_pass in set(audit_slice.passes)
        )
    )
    payload = {
        "context_sha256": context.context_sha256,
        "plan_sha256": context.plan.plan_sha256,
        "complexity": context.plan.complexity,
        "complexity_metrics": context.plan.complexity_metrics.model_dump(
            mode="json"
        ),
        "slice": audit_slice.model_dump(mode="json", by_alias=True),
        "sections": sections,
        "categories": categories,
        "mandatory_evidence": tuple(
            item.model_dump(mode="json") for item in evidence
        ),
    }
    return "\n".join(
        (
            "You are the sole assigned translation auditor for this slice.",
            f"Reviewer model: {context.assigned_reviewer}",
            f"English final-shape file: {context.source_path}",
            f"Chinese final-shape file: {context.candidate_path}",
            "",
            (
                "Read the exact files from disk. Inspect only the assigned passes "
                "and sections, but read enough surrounding context to resolve "
                "references."
            ),
            (
                "Return exactly one JSON object matching AuditV3SliceReport. Do "
                "not write prose, Markdown fences, repairs, or replacement text."
            ),
            (
                "Use the exact identity hashes, coverage units, EOF line numbers, "
                "and mandatory evidence order from the payload below."
            ),
            (
                "Each issue must quote one exact unique Chinese candidate span "
                "and use the correct pass, category, and section_id."
            ),
            (
                "Whenever you find one issue, search the entire assigned scope for "
                "the same issue family (terminology, UI literal, residual English, "
                "role/subject-object mapping, condition, number, API field, link, "
                "or structural pattern) and report every distinct exact span. Do "
                "not return only a representative example."
            ),
            (
                "Use complexity_metrics as an attention budget, not as permission "
                "to sample. If a low physical line count hides many links or cards, "
                "compare every card's title, label, date, and description as an "
                "independent semantic unit. If the scope contains many headings, "
                "complete a section-by-section semantic scan."
            ),
            (
                "For coverage and closure work, inspect every fenced block. "
                "Only fences whose language is text, markdown, md, or plaintext "
                "may contain localized reader-facing prose. Executable-language "
                "fences are immutable: code, commands, identifiers, comments, "
                "prompt strings, and literal output inside them must remain "
                "unchanged and must not be reported as residual English. In the "
                "four reader-facing fence languages, prose or Markdown templates "
                "(for example email, Slack, Teams, announcement, or tutorial copy) "
                "must be localized. For an issue inside a reader-facing fence, "
                "candidate_span_text must quote only the exact inner content; "
                "never include the opening or closing fence marker."
            ),
            (
                "For semantic and closure work, compare complete clauses rather "
                "than isolated terms. Check the actor, object, attachment, "
                "condition, negation, numeric bound, and API/file/field relation. "
                "Also reject dangling sentence-final words, missing complements, "
                "or grammatical fragments that make a statement incomplete."
            ),
            (
                "After that search, set issue_family_sweep_completed=true and put "
                "every reported issue_id in issue_family_checked_issue_ids in the "
                "same order as issues. A missing or reordered id invalidates the "
                "entire slice."
            ),
            (
                "Mandatory evidence is not a verdict to copy. Re-check it against "
                "the current files. issue_required evidence must be "
                "issue_reported. issue_or_block evidence must be issue_reported "
                "or unresolved. review_required evidence must receive a reasoned "
                "disposition."
            ),
            (
                "An issue outside this slice's primary coverage units is legal "
                "only when an issue_reported disposition in this report references "
                "it."
            ),
            (
                "A reconcile slice has no primary coverage units. It exists only "
                "after the blind semantic and surface/coverage slices to re-check "
                "mandatory evidence. Every issue it reports must be referenced by "
                "an issue_reported evidence disposition."
            ),
            (
                "An adversarial closure slice is an independent full-page red-team "
                "read. Start with a blind second semantic pass: compare every "
                "complete clause or card again for actor/object attachment, scope, "
                "conditions, numeric bounds, domain-specific word senses, named "
                "labels, and duplicate renderings. Ignore the fact that primary "
                "slices also exist, read both files through the real EOF, and then "
                "search for any remaining surface or coverage contradiction. It "
                "may report any semantic, surface, or coverage category in any "
                "listed section and must not assume an unreported span is clean."
            ),
            (
                "Set reached_real_eof=true only after reading the real EOF when "
                "the slice includes the coverage/eof unit."
            ),
            "",
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
            "",
        )
    )


def merge_audit_v3_context_reports(
    *,
    context: AuditV3Context,
    reports: tuple[AuditV3SliceReport, ...],
    contract: DeepAuditCoverageContract,
) -> DeepAuditFindingReport:
    """Enforce evidence requirements before the standard fail-closed merge."""
    dispositions = {
        item.evidence_id: item
        for report in reports
        for item in report.mandatory_evidence_dispositions
    }
    for evidence in context.mandatory_evidence:
        disposition = dispositions.get(evidence.evidence_id)
        if disposition is None:
            message = f"missing disposition for evidence {evidence.evidence_id}"
            raise ValueError(message)
        if (
            evidence.requirement == AuditEvidenceRequirement.ISSUE_REQUIRED
            and disposition.disposition != "issue_reported"
        ):
            message = (
                f"evidence {evidence.evidence_id} requires an issue_reported "
                "disposition"
            )
            raise ValueError(message)
        if (
            evidence.requirement == AuditEvidenceRequirement.ISSUE_OR_BLOCK
            and disposition.disposition
            not in {"issue_reported", "unresolved"}
        ):
            message = (
                f"evidence {evidence.evidence_id} must report an issue or block"
            )
            raise ValueError(message)
    return merge_audit_v3_reports(
        plan=context.plan,
        reports=reports,
        contract=contract,
    )


def _preflight_evidence(
    finding: PreflightFinding,
) -> AuditV3MandatoryEvidence:
    hard = finding.severity == PreflightSeverity.HARD
    candidate_span = finding.candidate_span
    requirement = (
        AuditEvidenceRequirement.ISSUE_REQUIRED
        if hard and candidate_span is not None
        else AuditEvidenceRequirement.ISSUE_OR_BLOCK
        if hard
        else AuditEvidenceRequirement.REVIEW_REQUIRED
    )
    return AuditV3MandatoryEvidence(
        evidence_id=f"preflight:{finding.finding_id}",
        kind=(
            AuditEvidenceKind.PREFLIGHT_HARD
            if hard
            else AuditEvidenceKind.PREFLIGHT_HINT
        ),
        severity="high" if hard else "low",
        requirement=requirement,
        summary=f"{finding.code}: {finding.message}",
        candidate_span_text=candidate_span.text if candidate_span else "",
        candidate_span_sha256=(
            candidate_span.sha256 if candidate_span else None
        ),
        origin_ids=(finding.finding_id,),
    )


def _history_evidence(
    issue: HistoricalIssueRecovery,
) -> AuditV3MandatoryEvidence:
    carry = issue.disposition == "carry-forward"
    return AuditV3MandatoryEvidence(
        evidence_id=issue.recovery_id,
        kind=(
            AuditEvidenceKind.HISTORY_CARRY
            if carry
            else AuditEvidenceKind.HISTORY_RECONCILE
        ),
        severity=issue.severity,
        requirement=AuditEvidenceRequirement.REVIEW_REQUIRED,
        summary=f"{issue.category} at {issue.location}: {issue.explanation or issue.reason}",
        source_excerpt=issue.source_excerpt,
        candidate_span_text=issue.candidate_span_text if carry else "",
        candidate_span_sha256=(
            sha256_text(issue.candidate_span_text)
            if carry
            else None
        ),
        origin_ids=tuple(
            sorted(
                f"{item.report_path}:{item.issue_id}"
                for item in issue.source_reports
            )
        ),
        report_paths=tuple(
            sorted({item.report_path for item in issue.source_reports})
        ),
    )


def _selected_preflight_findings(
    preflight: AuditPreflightEvidence,
) -> tuple[PreflightFinding, ...]:
    hard = tuple(
        item
        for item in preflight.findings
        if item.severity == PreflightSeverity.HARD
    )
    deduplicated: list[PreflightFinding] = []
    seen: set[tuple[str, str]] = set()
    for item in sorted(
        (
            finding
            for finding in preflight.findings
            if finding.severity == PreflightSeverity.CANDIDATE_HINT
        ),
        key=lambda finding: (
            _PREFLIGHT_HINT_PRIORITY.get(finding.code, 99),
            finding.candidate_lines,
            finding.finding_id,
        ),
    ):
        key = (
            item.code,
            (
                item.candidate_span.sha256
                if item.candidate_span is not None
                else item.blocked_reason or item.finding_id
            ),
        )
        if key in seen:
            continue
        seen.add(key)
        deduplicated.append(item)

    hints: list[PreflightFinding] = []
    priorities = tuple(
        sorted(
            {
                _PREFLIGHT_HINT_PRIORITY.get(item.code, 99)
                for item in deduplicated
            }
        )
    )
    for priority in priorities:
        remaining = _MAX_MANDATORY_PREFLIGHT_HINTS - len(hints)
        if remaining <= 0:
            break
        group = tuple(
            item
            for item in deduplicated
            if _PREFLIGHT_HINT_PRIORITY.get(item.code, 99) == priority
        )
        hints.extend(_stratified_findings(group, remaining))
    return (*hard, *hints)


def _stratified_findings(
    findings: tuple[PreflightFinding, ...],
    limit: int,
) -> tuple[PreflightFinding, ...]:
    """Sample the whole page instead of biasing mandatory hints to its prefix."""
    if limit <= 0 or not findings:
        return ()
    if len(findings) <= limit:
        return findings
    if limit == 1:
        return (findings[len(findings) // 2],)
    last = len(findings) - 1
    indices = tuple(round(index * last / (limit - 1)) for index in range(limit))
    return tuple(findings[index] for index in indices)


def _mapping_sha256(value: object) -> str:
    payload = _json_value(value)
    return hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _model_sha256(
    model: BaseModel,
    *,
    exclude: set[str] | None = None,
) -> str:
    return _mapping_sha256(
        model.model_dump(
            mode="json",
            by_alias=True,
            exclude=exclude,
        )
    )


def _json_value(value: object) -> object:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json", by_alias=True)
    if isinstance(value, dict):
        mapping = cast("dict[object, object]", value)
        return {
            str(key): _json_value(item)
            for key, item in mapping.items()
        }
    if isinstance(value, (list, tuple)):
        sequence = cast("list[object] | tuple[object, ...]", value)
        return [_json_value(item) for item in sequence]
    if isinstance(value, StrEnum):
        return value.value
    return value

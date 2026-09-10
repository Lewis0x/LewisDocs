# Copyright 2026

"""Deterministic coverage contract for complete deep translation audits."""

from __future__ import annotations

import hashlib
import json
import re
from enum import StrEnum
from typing import TYPE_CHECKING, Annotated, ClassVar, Final, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)

from scripts.ai.review_contract import AssignedReviewer, sha256_path

if TYPE_CHECKING:
    from pathlib import Path

__all__ = (
    "AuditCategory",
    "AuditPass",
    "DeepAuditCoverageContract",
    "DeepAuditCoverageReport",
    "DeepAuditFindingReport",
    "ReviewerContractPayload",
    "build_reviewer_contract_payload",
    "build_reviewer_prompt",
    "canonicalize_finding_excerpts",
    "derive_coverage_contract",
    "materialize_coverage_report",
    "recover_unique_whitespace_span",
    "validate_coverage_contract",
    "validate_coverage_report",
)

_HEADING_RE: Final = re.compile(
    r"^[ \t]*(?:>[ \t]*)*(?P<marks>#{1,6})[ \t]+(?P<heading>.*?)[ \t]*#*[ \t]*$"
)
_FENCE_RE: Final = re.compile(
    r"^[ \t]*(?P<marker>`{3,}|~{3,})(?P<header>[^\r\n]*)$"
)
_INLINE_CODE_RE: Final = re.compile(r"(?<!`)`[^`\r\n]+`(?!`)")
_MARKDOWN_LINK_RE: Final = re.compile(
    r"(?<!!)\[(?P<label>[^\]\r\n]+)\]\((?P<target>[^)\r\n]+)\)"
)
_SURFACE_LITERAL_RE: Final = re.compile(
    r'`[^`\r\n]+`|<kbd>[^<\r\n]+</kbd>|\*\*[^*\r\n]+\*\*|["\u201c][^"\u201d\r\n]+["\u201d]'
)
_FRONTMATTER_KEY_RE: Final = re.compile(
    r"^(?P<key>[A-Za-z][A-Za-z0-9_-]*):"
)
_SECTION_ID_RE: Final = r"^(?:frontmatter|preamble|eof|section-[0-9]{4}-[0-9a-f]{12})$"
_ISSUE_ID_RE: Final = r"^[a-z0-9][a-z0-9._:-]{0,127}$"
_HASH_RE: Final = r"^[0-9a-f]{64}$"


class AuditPass(StrEnum):
    """One mandatory pass in the deep-audit workflow."""

    SEMANTIC = "semantic"
    SURFACE = "surface"
    COVERAGE = "coverage"


class AuditCategory(StrEnum):
    """Mandatory checks that cannot be omitted from a v2 report."""

    SEMANTIC_ROLES = "semantic_roles"
    SEMANTIC_SUBJECT_OBJECT = "semantic_subject_object"
    SEMANTIC_CONDITIONS = "semantic_conditions"
    SEMANTIC_NEGATION = "semantic_negation"
    SEMANTIC_NUMBERS = "semantic_numbers"
    SEMANTIC_API_MAPPING = "semantic_api_mapping"
    SURFACE_FRONTMATTER_H1 = "surface_frontmatter_h1"
    SURFACE_UI_LITERALS = "surface_ui_literals"
    SURFACE_CODE_LITERALS = "surface_code_literals"
    SURFACE_TERMINOLOGY = "surface_terminology"
    SURFACE_LINK_LABELS = "surface_link_labels"
    COVERAGE_SECTIONS = "coverage_sections"
    COVERAGE_STRUCTURE = "coverage_structure"
    COVERAGE_EOF = "coverage_eof"


_CATEGORY_PASS: Final[dict[AuditCategory, AuditPass]] = {
    AuditCategory.SEMANTIC_ROLES: AuditPass.SEMANTIC,
    AuditCategory.SEMANTIC_SUBJECT_OBJECT: AuditPass.SEMANTIC,
    AuditCategory.SEMANTIC_CONDITIONS: AuditPass.SEMANTIC,
    AuditCategory.SEMANTIC_NEGATION: AuditPass.SEMANTIC,
    AuditCategory.SEMANTIC_NUMBERS: AuditPass.SEMANTIC,
    AuditCategory.SEMANTIC_API_MAPPING: AuditPass.SEMANTIC,
    AuditCategory.SURFACE_FRONTMATTER_H1: AuditPass.SURFACE,
    AuditCategory.SURFACE_UI_LITERALS: AuditPass.SURFACE,
    AuditCategory.SURFACE_CODE_LITERALS: AuditPass.SURFACE,
    AuditCategory.SURFACE_TERMINOLOGY: AuditPass.SURFACE,
    AuditCategory.SURFACE_LINK_LABELS: AuditPass.SURFACE,
    AuditCategory.COVERAGE_SECTIONS: AuditPass.COVERAGE,
    AuditCategory.COVERAGE_STRUCTURE: AuditPass.COVERAGE,
    AuditCategory.COVERAGE_EOF: AuditPass.COVERAGE,
}
MANDATORY_PASSES: Final = tuple(AuditPass)
MANDATORY_CATEGORIES: Final = tuple(AuditCategory)

NonEmptyString = Annotated[str, StringConstraints(min_length=1)]
ExactNonEmptyString = Annotated[
    str,
    StringConstraints(min_length=1, strip_whitespace=False),
]
Sha256String = Annotated[str, StringConstraints(pattern=_HASH_RE)]


class _StrictModel(BaseModel):
    """Immutable schema shared by manifests, prompts, and reports."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid",
        frozen=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        use_enum_values=True,
    )


class FileDeterministicEvidence(_StrictModel):
    """Locally derived evidence for one exact final-site-shape file."""

    sha256: Sha256String
    byte_count: int = Field(ge=0)
    line_count: int = Field(ge=0)
    frontmatter_present: bool
    frontmatter_sha256: Sha256String
    frontmatter_keys: tuple[str, ...]
    h1_headings: tuple[str, ...]
    heading_count: int = Field(ge=0)
    headings_sha256: Sha256String
    fenced_code_count: int = Field(ge=0)
    fenced_code_sha256: Sha256String
    inline_code_count: int = Field(ge=0)
    inline_code_sha256: Sha256String
    surface_literal_count: int = Field(ge=0)
    surface_literal_sha256: Sha256String
    link_count: int = Field(ge=0)
    links_sha256: Sha256String
    eof_line_number: int = Field(ge=0)
    eof_tail_sha256: Sha256String


class PairDeterministicEvidence(_StrictModel):
    """Locally recomputable evidence for both reviewed files."""

    english: FileDeterministicEvidence
    chinese: FileDeterministicEvidence


class ExpectedSection(_StrictModel):
    """One stable section that every v2 report must acknowledge."""

    section_id: str = Field(pattern=_SECTION_ID_RE)
    ordinal: int = Field(ge=0)
    kind: Literal["frontmatter", "preamble", "heading", "eof"]
    heading: NonEmptyString
    english_heading: str | None = None
    chinese_heading: str | None = None
    english_level: int | None = Field(default=None, ge=1, le=6)
    chinese_level: int | None = Field(default=None, ge=1, le=6)


class MandatoryCategorySpec(_StrictModel):
    """One category assigned to exactly one of the three passes."""

    audit_pass: AuditPass = Field(alias="pass")
    category: AuditCategory

    @model_validator(mode="after")
    def _category_belongs_to_pass(self) -> Self:
        category = AuditCategory(self.category)
        if AuditPass(self.audit_pass) != _CATEGORY_PASS[category]:
            message = f"{category} belongs to {_CATEGORY_PASS[category]}"
            raise ValueError(message)
        return self


class DeepAuditCoverageContract(_StrictModel):
    """Expected v2 coverage and deterministic evidence for one page pair."""

    version: Literal[2] = 2
    source_id: NonEmptyString
    english_path: NonEmptyString
    chinese_path: NonEmptyString
    source_sha256: Sha256String
    candidate_sha256: Sha256String
    mandatory_passes: tuple[AuditPass, ...]
    mandatory_categories: tuple[MandatoryCategorySpec, ...]
    sections: tuple[ExpectedSection, ...] = Field(min_length=3)
    evidence: PairDeterministicEvidence

    @model_validator(mode="after")
    def _contract_is_complete(self) -> Self:
        if tuple(AuditPass(item) for item in self.mandatory_passes) != MANDATORY_PASSES:
            message = "coverage contract does not list all three passes in order"
            raise ValueError(message)
        categories = tuple(
            AuditCategory(item.category) for item in self.mandatory_categories
        )
        if categories != MANDATORY_CATEGORIES:
            message = "coverage contract does not list every mandatory category"
            raise ValueError(message)
        section_ids = [item.section_id for item in self.sections]
        if len(section_ids) != len(set(section_ids)):
            message = "coverage contract contains duplicate section ids"
            raise ValueError(message)
        if tuple(item.ordinal for item in self.sections) != tuple(
            range(len(self.sections))
        ):
            message = "coverage contract section ordinals are not contiguous"
            raise ValueError(message)
        if self.sections[0].kind != "frontmatter":
            message = "coverage contract must begin with frontmatter"
            raise ValueError(message)
        if self.sections[-1].kind != "eof":
            message = "coverage contract must end with EOF"
            raise ValueError(message)
        return self


class PassCoverage(_StrictModel):
    """Reviewer acknowledgement for one complete audit pass."""

    audit_pass: AuditPass = Field(alias="pass")
    checked: Literal[True]
    issue_count: int = Field(ge=0)


class CategoryCoverage(_StrictModel):
    """Reviewer acknowledgement for one mandatory category."""

    audit_pass: AuditPass = Field(alias="pass")
    category: AuditCategory
    checked: Literal[True]
    issue_count: int = Field(ge=0)

    @model_validator(mode="after")
    def _category_belongs_to_pass(self) -> Self:
        category = AuditCategory(self.category)
        if AuditPass(self.audit_pass) != _CATEGORY_PASS[category]:
            message = f"{category} belongs to {_CATEGORY_PASS[category]}"
            raise ValueError(message)
        return self


class SectionCoverage(_StrictModel):
    """Reviewer acknowledgement for one expected section."""

    section_id: str = Field(pattern=_SECTION_ID_RE)
    ordinal: int = Field(ge=0)
    heading: NonEmptyString
    checked: Literal[True]
    issue_count: int = Field(ge=0)


class CoverageIssue(_StrictModel):
    """One exact, uniquely locatable issue discovered during one pass."""

    issue_id: str = Field(pattern=_ISSUE_ID_RE)
    audit_pass: AuditPass = Field(alias="pass")
    category: AuditCategory
    section_id: str = Field(pattern=_SECTION_ID_RE)
    severity: Literal["high", "medium", "low"]
    location: NonEmptyString
    source_excerpt: ExactNonEmptyString
    candidate_span_text: ExactNonEmptyString
    explanation: NonEmptyString

    @model_validator(mode="after")
    def _category_belongs_to_pass(self) -> Self:
        category = AuditCategory(self.category)
        if AuditPass(self.audit_pass) != _CATEGORY_PASS[category]:
            message = f"{category} belongs to {_CATEGORY_PASS[category]}"
            raise ValueError(message)
        return self


class DeepAuditCoverageReport(_StrictModel):
    """Single symmetric Terra/Grok report schema for v2 deep audits."""

    version: Literal[2] = 2
    audit_contract_version: Literal[2] = 2
    source_id: NonEmptyString
    review_model: AssignedReviewer
    verdict: Literal["pass", "warn", "fail"]
    english_path: NonEmptyString
    chinese_path: NonEmptyString
    source_sha256: Sha256String
    candidate_sha256: Sha256String
    passes: tuple[PassCoverage, ...] = Field(min_length=3, max_length=3)
    categories: tuple[CategoryCoverage, ...] = Field(
        min_length=len(MANDATORY_CATEGORIES),
        max_length=len(MANDATORY_CATEGORIES),
    )
    sections: tuple[SectionCoverage, ...] = Field(min_length=3)
    evidence: PairDeterministicEvidence
    issues: tuple[CoverageIssue, ...]

    @model_validator(mode="after")
    def _report_is_internally_consistent(self) -> Self:
        issue_ids = [item.issue_id for item in self.issues]
        if len(issue_ids) != len(set(issue_ids)):
            message = "coverage report contains duplicate issue ids"
            raise ValueError(message)
        if self.verdict == "pass" and self.issues:
            message = "passing coverage report contains issues"
            raise ValueError(message)
        if self.verdict != "pass" and not self.issues:
            message = "non-passing coverage report has no issues"
            raise ValueError(message)
        _validate_report_counts(self)
        return self


class DeepAuditFindingReport(_StrictModel):
    """Compact model-authored findings expanded locally into canonical evidence."""

    version: Literal[1] = 1
    audit_contract_version: Literal[2] = 2
    source_id: NonEmptyString
    review_model: AssignedReviewer
    verdict: Literal["pass", "warn", "fail"]
    checked_passes: tuple[AuditPass, ...] = Field(min_length=3, max_length=3)
    checked_categories: tuple[AuditCategory, ...] = Field(
        min_length=len(MANDATORY_CATEGORIES),
        max_length=len(MANDATORY_CATEGORIES),
    )
    checked_section_ids: tuple[str, ...] = Field(min_length=3)
    reached_real_eof: Literal[True]
    issues: tuple[CoverageIssue, ...]

    @model_validator(mode="after")
    def _findings_are_complete_and_deduplicated(self) -> Self:
        if tuple(AuditPass(item) for item in self.checked_passes) != MANDATORY_PASSES:
            message = "finding report does not attest all three passes in order"
            raise ValueError(message)
        categories = tuple(
            AuditCategory(item) for item in self.checked_categories
        )
        if categories != MANDATORY_CATEGORIES:
            message = "finding report does not attest every category in order"
            raise ValueError(message)
        issue_ids = [item.issue_id for item in self.issues]
        if len(issue_ids) != len(set(issue_ids)):
            message = "finding report contains duplicate issue ids"
            raise ValueError(message)
        _validate_distinct_candidate_spans(self.issues)
        expected_verdict: Literal["pass", "warn", "fail"]
        if any(item.severity == "high" for item in self.issues):
            expected_verdict = "fail"
        elif self.issues:
            expected_verdict = "warn"
        else:
            expected_verdict = "pass"
        if self.verdict != expected_verdict:
            message = (
                "finding verdict conflicts with issue severities; "
                f"expected {expected_verdict}"
            )
            raise ValueError(message)
        return self


class ReviewerContractPayload(_StrictModel):
    """Portable prompt payload for either assigned reviewer model."""

    audit_contract_version: Literal[2] = 2
    assigned_reviewer: AssignedReviewer
    workflow: tuple[NonEmptyString, ...]
    exact_excerpt_policy: tuple[NonEmptyString, ...]
    coverage_contract: DeepAuditCoverageContract
    report_schema: dict[str, object]


def derive_coverage_contract(
    *,
    source_id: str,
    english_path: Path,
    chinese_path: Path,
    english_path_value: str | None = None,
    chinese_path_value: str | None = None,
) -> DeepAuditCoverageContract:
    """Derive the immutable v2 coverage ledger from final-site-shape files."""
    english_text = english_path.read_text(encoding="utf-8-sig")
    chinese_text = chinese_path.read_text(encoding="utf-8-sig")
    english_headings = _headings(english_text)
    chinese_headings = _headings(chinese_text)
    sections = _expected_sections(english_headings, chinese_headings)
    categories = tuple(
        MandatoryCategorySpec.model_validate(
            {
                "pass": _CATEGORY_PASS[category],
                "category": category,
            }
        )
        for category in MANDATORY_CATEGORIES
    )
    return DeepAuditCoverageContract(
        source_id=source_id,
        english_path=english_path_value or english_path.as_posix(),
        chinese_path=chinese_path_value or chinese_path.as_posix(),
        source_sha256=sha256_path(english_path),
        candidate_sha256=sha256_path(chinese_path),
        mandatory_passes=MANDATORY_PASSES,
        mandatory_categories=categories,
        sections=sections,
        evidence=PairDeterministicEvidence(
            english=_file_evidence(english_path, english_text),
            chinese=_file_evidence(chinese_path, chinese_text),
        ),
    )


def validate_coverage_contract(
    contract: DeepAuditCoverageContract,
    *,
    english_path: Path,
    chinese_path: Path,
) -> None:
    """Reject a stale or hand-authored manifest coverage contract."""
    actual = derive_coverage_contract(
        source_id=contract.source_id,
        english_path=english_path,
        chinese_path=chinese_path,
        english_path_value=contract.english_path,
        chinese_path_value=contract.chinese_path,
    )
    if actual != contract:
        message = "deep-audit coverage contract does not match reviewed files"
        raise ValueError(message)


def validate_coverage_report(
    report_value: object,
    *,
    contract: DeepAuditCoverageContract,
    assigned_reviewer: AssignedReviewer,
    english_path: Path,
    chinese_path: Path,
) -> DeepAuditCoverageReport:
    """Validate complete v2 coverage, counts, local evidence, and excerpts."""
    report = DeepAuditCoverageReport.model_validate(report_value)
    validate_coverage_contract(
        contract,
        english_path=english_path,
        chinese_path=chinese_path,
    )
    if report.source_id != contract.source_id:
        message = "coverage report source_id does not match its contract"
        raise ValueError(message)
    if report.review_model != assigned_reviewer:
        message = "coverage report does not match its assigned reviewer"
        raise ValueError(message)
    expected_identity = (
        (report.english_path, contract.english_path, "English path"),
        (report.chinese_path, contract.chinese_path, "Chinese path"),
        (report.source_sha256, contract.source_sha256, "English hash"),
        (report.candidate_sha256, contract.candidate_sha256, "Chinese hash"),
        (report.evidence, contract.evidence, "deterministic evidence"),
    )
    for actual, expected, label in expected_identity:
        if actual != expected:
            message = f"coverage report {label} does not match its contract"
            raise ValueError(message)
    if tuple(AuditPass(item.audit_pass) for item in report.passes) != MANDATORY_PASSES:
        message = "coverage report is missing or duplicating an audit pass"
        raise ValueError(message)
    report_categories = tuple(
        AuditCategory(item.category) for item in report.categories
    )
    if report_categories != MANDATORY_CATEGORIES:
        message = "coverage report is missing or duplicating a mandatory category"
        raise ValueError(message)
    expected_sections = tuple(
        (item.section_id, item.ordinal, item.heading) for item in contract.sections
    )
    actual_sections = tuple(
        (item.section_id, item.ordinal, item.heading) for item in report.sections
    )
    if actual_sections != expected_sections:
        message = "coverage report has duplicate, unknown, missing, or reordered sections"
        raise ValueError(message)
    _validate_distinct_candidate_spans(report.issues)
    _validate_exact_excerpts(report, english_path, chinese_path)
    return report


def materialize_coverage_report(
    findings: DeepAuditFindingReport,
    *,
    contract: DeepAuditCoverageContract,
    assigned_reviewer: AssignedReviewer,
) -> DeepAuditCoverageReport:
    """Expand compact model findings into deterministic canonical evidence."""
    if findings.source_id != contract.source_id:
        message = "finding report source_id does not match its contract"
        raise ValueError(message)
    if findings.review_model != assigned_reviewer:
        message = "finding report does not match its assigned reviewer"
        raise ValueError(message)
    expected_section_ids = tuple(item.section_id for item in contract.sections)
    if findings.checked_section_ids != expected_section_ids:
        message = "finding report did not attest every contract section in order"
        raise ValueError(message)
    issues = tuple(findings.issues)
    pass_counts = {
        audit_pass: sum(
            AuditPass(issue.audit_pass) == audit_pass for issue in issues
        )
        for audit_pass in MANDATORY_PASSES
    }
    category_counts = {
        category: sum(
            AuditCategory(issue.category) == category for issue in issues
        )
        for category in MANDATORY_CATEGORIES
    }
    section_counts = {
        section.section_id: sum(
            issue.section_id == section.section_id for issue in issues
        )
        for section in contract.sections
    }
    return DeepAuditCoverageReport(
        source_id=contract.source_id,
        review_model=assigned_reviewer,
        verdict=findings.verdict,
        english_path=contract.english_path,
        chinese_path=contract.chinese_path,
        source_sha256=contract.source_sha256,
        candidate_sha256=contract.candidate_sha256,
        passes=tuple(
            PassCoverage.model_validate(
                {
                    "pass": audit_pass,
                    "checked": True,
                    "issue_count": pass_counts[audit_pass],
                }
            )
            for audit_pass in MANDATORY_PASSES
        ),
        categories=tuple(
            CategoryCoverage.model_validate(
                {
                    "pass": _CATEGORY_PASS[category],
                    "category": category,
                    "checked": True,
                    "issue_count": category_counts[category],
                }
            )
            for category in MANDATORY_CATEGORIES
        ),
        sections=tuple(
            SectionCoverage(
                section_id=section.section_id,
                ordinal=section.ordinal,
                heading=section.heading,
                checked=True,
                issue_count=section_counts[section.section_id],
            )
            for section in contract.sections
        ),
        evidence=contract.evidence,
        issues=issues,
    )


def canonicalize_finding_excerpts(
    findings: DeepAuditFindingReport,
    *,
    english_path: Path,
    chinese_path: Path,
) -> DeepAuditFindingReport:
    """Recover exact excerpts when a reviewer only collapsed Markdown whitespace."""
    english = english_path.read_text(encoding="utf-8-sig")
    chinese = chinese_path.read_text(encoding="utf-8-sig")
    issues: list[CoverageIssue] = []
    for issue in findings.issues:
        source_excerpt = recover_unique_whitespace_span(
            english,
            issue.source_excerpt,
            issue_id=issue.issue_id,
            field_name="source_excerpt",
        )
        candidate_span_text = recover_unique_whitespace_span(
            chinese,
            issue.candidate_span_text,
            issue_id=issue.issue_id,
            field_name="candidate_span_text",
        )
        issues.append(
            issue.model_copy(
                update={
                    "source_excerpt": source_excerpt,
                    "candidate_span_text": candidate_span_text,
                }
            )
        )
    return DeepAuditFindingReport(
        version=findings.version,
        audit_contract_version=findings.audit_contract_version,
        source_id=findings.source_id,
        review_model=findings.review_model,
        verdict=findings.verdict,
        checked_passes=findings.checked_passes,
        checked_categories=findings.checked_categories,
        checked_section_ids=findings.checked_section_ids,
        reached_real_eof=True,
        issues=tuple(issues),
    )


def build_reviewer_contract_payload(
    contract: DeepAuditCoverageContract,
    *,
    assigned_reviewer: AssignedReviewer,
) -> ReviewerContractPayload:
    """Build one model-neutral prompt payload for the assigned reviewer."""
    return ReviewerContractPayload(
        assigned_reviewer=assigned_reviewer,
        workflow=(
            (
                "Pass A semantic: check roles, subject/object direction, "
                "conditions, negation, numbers, and API mappings."
            ),
            (
                "Pass B surface: check frontmatter/H1, UI literals, inline-code "
                "literals, terminology consistency, visible link labels, and "
                "reader-facing prose only in text, markdown, md, or plaintext "
                "fences. Treat every executable-language fence as immutable and "
                "do not report untranslated English inside it. For a valid issue "
                "inside a reader-facing fence, quote only the exact inner content "
                "and never include either fence marker."
            ),
            (
                "Pass C coverage: compare every expected heading/section, "
                "structure, and the true physical EOF of both files."
            ),
        ),
        exact_excerpt_policy=(
            "Read the exact hash-bound files; do not rely on truncated tool output.",
            (
                "Every issue must use one exact contiguous source_excerpt and "
                "one exact contiguous candidate_span_text, each occurring once."
            ),
            (
                "Every issue must name pass, category, and section_id; complete "
                "the checked pass/category/section-id lists even for pass verdicts."
            ),
            (
                "Never emit the same candidate_span_text in multiple issues. "
                "Choose one primary category for each exact repair span."
            ),
            (
                "This source_id belongs only to the assigned reviewer; do not "
                "request or simulate a second Terra/Grok review."
            ),
        ),
        coverage_contract=contract,
        report_schema=DeepAuditFindingReport.model_json_schema(
            by_alias=True,
            mode="validation",
        ),
    )


def build_reviewer_prompt(
    contract: DeepAuditCoverageContract,
    *,
    assigned_reviewer: AssignedReviewer,
) -> str:
    """Render the strict three-pass contract as a reviewer-ready prompt."""
    payload = build_reviewer_contract_payload(
        contract,
        assigned_reviewer=assigned_reviewer,
    )
    payload_json = json.dumps(
        payload.model_dump(mode="json", by_alias=True),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    return (
        "Perform exactly one assigned deep audit. Follow Pass A, then Pass B, "
        "then Pass C. Read both files through their true physical EOF. Return "
        "only one compact JSON object matching report_schema; do not add prose. "
        "Copy checked_passes, checked_categories, and checked_section_ids exactly "
        "from the coverage contract. Local code will deterministically expand "
        "paths, hashes, counts, headings, and evidence after validation.\n\n"
        f"{payload_json}\n"
    )


def _validate_distinct_candidate_spans(
    issues: tuple[CoverageIssue, ...],
) -> None:
    spans = [item.candidate_span_text for item in issues]
    if len(spans) != len(set(spans)):
        message = "multiple issues reuse the same exact candidate span"
        raise ValueError(message)


def _validate_report_counts(report: DeepAuditCoverageReport) -> None:
    issues = tuple(report.issues)
    expected_pass_counts = {
        audit_pass: sum(
            AuditPass(issue.audit_pass) == audit_pass for issue in issues
        )
        for audit_pass in MANDATORY_PASSES
    }
    expected_category_counts = {
        category: sum(
            AuditCategory(issue.category) == category for issue in issues
        )
        for category in MANDATORY_CATEGORIES
    }
    expected_section_counts: dict[str, int] = {}
    for issue in issues:
        expected_section_counts[issue.section_id] = (
            expected_section_counts.get(issue.section_id, 0) + 1
        )
    for item in report.passes:
        audit_pass = AuditPass(item.audit_pass)
        if item.issue_count != expected_pass_counts[audit_pass]:
            message = f"{audit_pass} pass issue_count does not match issues"
            raise ValueError(message)
    for item in report.categories:
        category = AuditCategory(item.category)
        if item.issue_count != expected_category_counts[category]:
            message = f"{category} category issue_count does not match issues"
            raise ValueError(message)
    section_ids = {item.section_id for item in report.sections}
    unknown = set(expected_section_counts).difference(section_ids)
    if unknown:
        message = f"coverage issues reference unknown sections: {sorted(unknown)}"
        raise ValueError(message)
    for item in report.sections:
        if item.issue_count != expected_section_counts.get(item.section_id, 0):
            message = (
                f"{item.section_id} section issue_count does not match issues"
            )
            raise ValueError(message)


def _validate_exact_excerpts(
    report: DeepAuditCoverageReport,
    english_path: Path,
    chinese_path: Path,
) -> None:
    english = english_path.read_text(encoding="utf-8-sig")
    chinese = chinese_path.read_text(encoding="utf-8-sig")
    for issue in report.issues:
        if english.count(issue.source_excerpt) != 1:
            message = (
                f"issue {issue.issue_id} source_excerpt is not exact and unique"
            )
            raise ValueError(message)
        if chinese.count(issue.candidate_span_text) != 1:
            message = (
                f"issue {issue.issue_id} candidate_span_text is not exact and unique"
            )
            raise ValueError(message)


def recover_unique_whitespace_span(
    text: str,
    excerpt: str,
    *,
    issue_id: str,
    field_name: str,
) -> str:
    """Recover one exact source span when only Markdown whitespace differs."""
    if text.count(excerpt) == 1:
        return excerpt

    compact_excerpt = "".join(character for character in excerpt if not character.isspace())
    if not compact_excerpt:
        message = f"issue {issue_id} {field_name} contains only whitespace"
        raise ValueError(message)

    compact_text_characters: list[str] = []
    original_offsets: list[int] = []
    for offset, character in enumerate(text):
        if character.isspace():
            continue
        compact_text_characters.append(character)
        original_offsets.append(offset)
    compact_text = "".join(compact_text_characters)

    matches: list[int] = []
    start = 0
    while True:
        match = compact_text.find(compact_excerpt, start)
        if match < 0:
            break
        matches.append(match)
        start = match + 1
    if len(matches) != 1:
        message = (
            f"issue {issue_id} {field_name} is not exact or uniquely "
            "whitespace-equivalent"
        )
        raise ValueError(message)

    compact_start = matches[0]
    compact_end = compact_start + len(compact_excerpt) - 1
    original_start = original_offsets[compact_start]
    original_end = original_offsets[compact_end] + 1
    resolved = text[original_start:original_end]
    if text.count(resolved) != 1:
        message = (
            f"issue {issue_id} {field_name} whitespace recovery is not unique"
        )
        raise ValueError(message)
    return resolved


def _expected_sections(
    english: tuple[tuple[int, str], ...],
    chinese: tuple[tuple[int, str], ...],
) -> tuple[ExpectedSection, ...]:
    sections: list[ExpectedSection] = [
        ExpectedSection(
            section_id="frontmatter",
            ordinal=0,
            kind="frontmatter",
            heading="[frontmatter]",
        ),
        ExpectedSection(
            section_id="preamble",
            ordinal=1,
            kind="preamble",
            heading="[content before first heading]",
        ),
    ]
    for index in range(max(len(english), len(chinese))):
        english_item = english[index] if index < len(english) else None
        chinese_item = chinese[index] if index < len(chinese) else None
        english_heading = english_item[1] if english_item is not None else None
        chinese_heading = chinese_item[1] if chinese_item is not None else None
        heading = english_heading or chinese_heading or "[missing heading]"
        ordinal = len(sections)
        identity = (
            f"{ordinal}\0"
            f"{english_item[0] if english_item else ''}\0"
            f"{english_heading or ''}"
        )
        section_id = (
            f"section-{ordinal:04d}-{_sha256_text(identity)[:12]}"
        )
        sections.append(
            ExpectedSection(
                section_id=section_id,
                ordinal=ordinal,
                kind="heading",
                heading=heading,
                english_heading=english_heading,
                chinese_heading=chinese_heading,
                english_level=english_item[0] if english_item else None,
                chinese_level=chinese_item[0] if chinese_item else None,
            )
        )
    sections.append(
        ExpectedSection(
            section_id="eof",
            ordinal=len(sections),
            kind="eof",
            heading="[true physical EOF]",
        )
    )
    return tuple(sections)


def _headings(markdown: str) -> tuple[tuple[int, str], ...]:
    frontmatter_end = _frontmatter_end_line(markdown)
    active_fence: tuple[str, int] | None = None
    headings: list[tuple[int, str]] = []
    for line_number, line in enumerate(markdown.splitlines(), start=1):
        if line_number <= frontmatter_end:
            continue
        fence = _FENCE_RE.match(line)
        if active_fence is not None:
            if (
                fence is not None
                and not fence.group("header").strip()
                and fence.group("marker")[0] == active_fence[0]
                and len(fence.group("marker")) >= active_fence[1]
            ):
                active_fence = None
            continue
        if fence is not None:
            marker = fence.group("marker")
            active_fence = (marker[0], len(marker))
            continue
        match = _HEADING_RE.match(line)
        if match is not None:
            headings.append(
                (len(match.group("marks")), match.group("heading").strip())
            )
    return tuple(headings)


def _file_evidence(path: Path, markdown: str) -> FileDeterministicEvidence:
    frontmatter = _frontmatter(markdown)
    headings = _headings(markdown)
    body_without_fences, fences = _mask_fences(markdown)
    inline_code = tuple(_INLINE_CODE_RE.findall(body_without_fences))
    surface_literals = tuple(_SURFACE_LITERAL_RE.findall(body_without_fences))
    links = tuple(
        (match.group("label"), match.group("target"))
        for match in _MARKDOWN_LINK_RE.finditer(body_without_fences)
    )
    non_empty_lines = [
        (index, line)
        for index, line in enumerate(markdown.splitlines(), start=1)
        if line.strip()
    ]
    eof_line_number, eof_tail = (
        non_empty_lines[-1] if non_empty_lines else (0, "")
    )
    return FileDeterministicEvidence(
        sha256=sha256_path(path),
        byte_count=len(path.read_bytes()),
        line_count=len(markdown.splitlines()),
        frontmatter_present=bool(frontmatter),
        frontmatter_sha256=_sha256_text(frontmatter),
        frontmatter_keys=tuple(
            match.group("key")
            for line in frontmatter.splitlines()
            if (match := _FRONTMATTER_KEY_RE.match(line)) is not None
        ),
        h1_headings=tuple(
            heading for level, heading in headings if level == 1
        ),
        heading_count=len(headings),
        headings_sha256=_digest_sequence(headings),
        fenced_code_count=len(fences),
        fenced_code_sha256=_digest_sequence(fences),
        inline_code_count=len(inline_code),
        inline_code_sha256=_digest_sequence(inline_code),
        surface_literal_count=len(surface_literals),
        surface_literal_sha256=_digest_sequence(surface_literals),
        link_count=len(links),
        links_sha256=_digest_sequence(links),
        eof_line_number=eof_line_number,
        eof_tail_sha256=_sha256_text(eof_tail),
    )


def _frontmatter(markdown: str) -> str:
    lines = markdown.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return ""
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return "".join(lines[: index + 1])
    return ""


def _frontmatter_end_line(markdown: str) -> int:
    frontmatter = _frontmatter(markdown)
    return len(frontmatter.splitlines()) if frontmatter else 0


def _mask_fences(markdown: str) -> tuple[str, tuple[str, ...]]:
    output: list[str] = []
    blocks: list[str] = []
    active: tuple[str, int] | None = None
    current: list[str] = []
    for line in markdown.splitlines(keepends=True):
        fence = _FENCE_RE.match(line.rstrip("\r\n"))
        if active is None:
            if fence is None:
                output.append(line)
                continue
            marker = fence.group("marker")
            active = (marker[0], len(marker))
            current = [line]
            output.append("\n" if line.endswith(("\n", "\r")) else "")
            continue
        current.append(line)
        output.append("\n" if line.endswith(("\n", "\r")) else "")
        if (
            fence is not None
            and not fence.group("header").strip()
            and fence.group("marker")[0] == active[0]
            and len(fence.group("marker")) >= active[1]
        ):
            blocks.append("".join(current))
            active = None
            current = []
    if current:
        blocks.append("".join(current))
    return "".join(output), tuple(blocks)


def _digest_sequence(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

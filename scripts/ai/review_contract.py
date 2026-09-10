# Copyright 2026

"""Repair-ready review contracts for the bilingual documentation pipeline."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, ClassVar, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

AssignedReviewer = Literal["gpt-5.6-terra", "grok-4.5"]
ReviewVerdict = Literal["warn", "fail"]
IssueSeverity = Literal["high", "medium", "low"]

_HEX_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SOURCE_ID = re.compile(r"^(?:claude-code|codex)/[a-z0-9][a-z0-9/-]*$")
_REPORT_EVIDENCE_VERSION = 2
READER_FACING_FENCE_LANGUAGES = frozenset(
    {"text", "markdown", "md", "plaintext"}
)
ExactString = Annotated[str, StringConstraints(strip_whitespace=False)]


@dataclass(frozen=True)
class MarkdownFence:
    """One parsed fenced block with byte-stable marker boundaries."""

    start: int
    content_start: int
    content_end: int
    end: int
    language: str

    @property
    def reader_facing(self) -> bool:
        """Return whether prose-only edits are permitted inside the fence."""
        return self.language in READER_FACING_FENCE_LANGUAGES


class _StrictModel(BaseModel):
    """Base class for immutable versioned pipeline records."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )


class CandidateSpan(_StrictModel):
    """One exact, unique Chinese span that may be safely replaced."""

    text: Annotated[
        ExactString,
        StringConstraints(min_length=1, max_length=3500),
    ]
    sha256: str
    line_start: int = Field(ge=1)
    line_end: int = Field(ge=1)
    occurrence_count: Literal[1] = 1

    @field_validator("sha256")
    @classmethod
    def _valid_sha256(cls, value: str) -> str:
        if _HEX_SHA256.fullmatch(value) is None:
            message = "candidate span sha256 must be lowercase hexadecimal"
            raise ValueError(message)
        return value

    @model_validator(mode="after")
    def _consistent_span(self) -> Self:
        if self.line_end < self.line_start:
            message = "candidate span line range is reversed"
            raise ValueError(message)
        if sha256_text(self.text) != self.sha256:
            message = "candidate span sha256 does not match its text"
            raise ValueError(message)
        return self


class RepairIssue(_StrictModel):
    """One independently executable repair item."""

    issue_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_issue_refs: tuple[str, ...] = Field(min_length=1)
    severity: IssueSeverity
    category: str = Field(min_length=1)
    location: str = Field(min_length=1)
    source_excerpt: str = Field(min_length=1)
    candidate_span: CandidateSpan
    explanation: str = Field(min_length=1)

    @field_validator("source_issue_refs")
    @classmethod
    def _unique_refs(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(value) != len(set(value)):
            message = "source issue references must be unique"
            raise ValueError(message)
        return value


class SourceReportEvidence(_StrictModel):
    """Immutable binding to one detailed audit report used by the bridge."""

    path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class RepairReadyReview(_StrictModel):
    """A complete review whose issues are directly safe to send for repair."""

    version: Literal[1, 2] = 1
    source_id: str
    assigned_reviewer: AssignedReviewer
    review_model: AssignedReviewer
    verdict: ReviewVerdict
    source_path: str = Field(min_length=1)
    candidate_path: str = Field(min_length=1)
    source_sha256: str
    candidate_sha256: str
    source_report_paths: tuple[str, ...] = Field(min_length=1)
    source_report_evidence: tuple[SourceReportEvidence, ...] = ()
    issues: tuple[RepairIssue, ...] = Field(min_length=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("source_id")
    @classmethod
    def _valid_source_id(cls, value: str) -> str:
        if _SOURCE_ID.fullmatch(value) is None or ".." in value:
            message = "source_id is not a safe AI documentation route"
            raise ValueError(message)
        return value

    @field_validator("source_sha256", "candidate_sha256")
    @classmethod
    def _valid_document_sha256(cls, value: str) -> str:
        if _HEX_SHA256.fullmatch(value) is None:
            message = "document sha256 must be lowercase hexadecimal"
            raise ValueError(message)
        return value

    @model_validator(mode="after")
    def _consistent_review(self) -> Self:
        if self.assigned_reviewer != self.review_model:
            message = "review model must match the assigned reviewer"
            raise ValueError(message)
        issue_ids = [issue.issue_id for issue in self.issues]
        if len(issue_ids) != len(set(issue_ids)):
            message = "repair issue ids must be unique"
            raise ValueError(message)
        span_hashes = [issue.candidate_span.sha256 for issue in self.issues]
        if len(span_hashes) != len(set(span_hashes)):
            message = "each exact candidate span must appear in only one repair issue"
            raise ValueError(message)
        if self.version == _REPORT_EVIDENCE_VERSION:
            evidence_paths = tuple(
                evidence.path for evidence in self.source_report_evidence
            )
            if evidence_paths != self.source_report_paths:
                message = "v2 repair review must bind every source report in order"
                raise ValueError(message)
        elif self.source_report_evidence:
            message = "v1 repair review cannot contain v2 source report evidence"
            raise ValueError(message)
        return self


class RepairIssueDraft(_StrictModel):
    """Human- or reviewer-authored inputs for one exact repair issue."""

    source_issue_refs: tuple[str, ...] = Field(min_length=1)
    severity: IssueSeverity
    category: str = Field(min_length=1)
    location: str = Field(min_length=1)
    source_excerpt: str = Field(min_length=1)
    candidate_span_text: Annotated[
        ExactString,
        StringConstraints(min_length=1, max_length=3500),
    ]
    explanation: str = Field(min_length=1)


class RepairReadyReviewDraft(_StrictModel):
    """Minimal bridge input that derives all hashes and line evidence locally."""

    version: Literal[1, 2] = 1
    source_id: str
    assigned_reviewer: AssignedReviewer
    verdict: ReviewVerdict
    source_path: str = Field(min_length=1)
    candidate_path: str = Field(min_length=1)
    source_report_paths: tuple[str, ...] = Field(min_length=1)
    issues: tuple[RepairIssueDraft, ...] = Field(min_length=1)

    @field_validator("source_id")
    @classmethod
    def _valid_source_id(cls, value: str) -> str:
        if _SOURCE_ID.fullmatch(value) is None or ".." in value:
            message = "source_id is not a safe AI documentation route"
            raise ValueError(message)
        return value


def sha256_bytes(value: bytes) -> str:
    """Return a lowercase SHA-256 digest for bytes."""
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    """Return a lowercase SHA-256 digest for UTF-8 text."""
    return sha256_bytes(value.encode("utf-8"))


def sha256_path(path: Path) -> str:
    """Return a lowercase SHA-256 digest for one file."""
    return sha256_bytes(path.read_bytes())


def resolve_repo_path(repo_root: Path, value: str) -> Path:
    """Resolve a repository-relative path without allowing path traversal."""
    relative = Path(value)
    if relative.is_absolute():
        message = "pipeline artifact paths must be repository-relative"
        raise ValueError(message)
    root = repo_root.resolve()
    resolved = (root / relative).resolve()
    try:
        _ = resolved.relative_to(root)
    except ValueError as exc:
        message = "pipeline artifact path escapes the repository"
        raise ValueError(message) from exc
    return resolved


def locate_candidate_span(candidate: str, text: str) -> CandidateSpan:
    """Locate and validate an exact replacement span in a Chinese candidate."""
    occurrence_count = candidate.count(text)
    if occurrence_count != 1:
        message = f"candidate span occurs {occurrence_count} times, not once"
        raise ValueError(message)
    start = candidate.index(text)
    end = start + len(text)
    if start < _frontmatter_end(candidate):
        message = "candidate span touches frontmatter"
        raise ValueError(message)
    overlapping_fences = tuple(
        fence
        for fence in parse_markdown_fences(candidate)
        if start < fence.end and end > fence.start
    )
    if overlapping_fences:
        if len(overlapping_fences) != 1:
            message = "candidate span crosses fenced block boundaries"
            raise ValueError(message)
        fence = overlapping_fences[0]
        if (
            not fence.reader_facing
            or start < fence.content_start
            or end > fence.content_end
        ):
            message = "candidate span touches protected fenced code"
            raise ValueError(message)
    return CandidateSpan(
        text=text,
        sha256=sha256_text(text),
        line_start=candidate.count("\n", 0, start) + 1,
        line_end=candidate.count("\n", 0, max(start, end - 1)) + 1,
        occurrence_count=1,
    )


def create_repair_issue(  # noqa: PLR0913
    *,
    source_id: str,
    source_issue_refs: tuple[str, ...],
    severity: IssueSeverity,
    category: str,
    location: str,
    source_excerpt: str,
    candidate_text: str,
    candidate_span_text: str,
    explanation: str,
) -> RepairIssue:
    """Create one deterministic repair issue from an exact Chinese span."""
    span = locate_candidate_span(candidate_text, candidate_span_text)
    identity = "\0".join(
        (
            source_id,
            span.sha256,
            *sorted(source_issue_refs),
        )
    )
    return RepairIssue(
        issue_id=sha256_text(identity),
        source_issue_refs=source_issue_refs,
        severity=severity,
        category=category,
        location=location,
        source_excerpt=source_excerpt,
        candidate_span=span,
        explanation=explanation,
    )


def materialize_repair_ready_review(
    draft: RepairReadyReviewDraft,
    repo_root: Path,
) -> RepairReadyReview:
    """Derive immutable hashes and exact span evidence from a bridge draft."""
    source_path = resolve_repo_path(repo_root, draft.source_path)
    candidate_path = resolve_repo_path(repo_root, draft.candidate_path)
    candidate = candidate_path.read_text(encoding="utf-8")
    issues = tuple(
        create_repair_issue(
            source_id=draft.source_id,
            source_issue_refs=issue.source_issue_refs,
            severity=issue.severity,
            category=issue.category,
            location=issue.location,
            source_excerpt=issue.source_excerpt,
            candidate_text=candidate,
            candidate_span_text=issue.candidate_span_text,
            explanation=issue.explanation,
        )
        for issue in draft.issues
    )
    source_report_evidence = (
        tuple(
            SourceReportEvidence(
                path=path_value,
                sha256=sha256_path(resolve_repo_path(repo_root, path_value)),
            )
            for path_value in draft.source_report_paths
        )
        if draft.version == _REPORT_EVIDENCE_VERSION
        else ()
    )
    review = RepairReadyReview(
        version=draft.version,
        source_id=draft.source_id,
        assigned_reviewer=draft.assigned_reviewer,
        review_model=draft.assigned_reviewer,
        verdict=draft.verdict,
        source_path=draft.source_path,
        candidate_path=draft.candidate_path,
        source_sha256=sha256_path(source_path),
        candidate_sha256=sha256_path(candidate_path),
        source_report_paths=draft.source_report_paths,
        source_report_evidence=source_report_evidence,
        issues=issues,
    )
    validate_review_artifacts(review, repo_root)
    return review


def validate_review_artifacts(review: RepairReadyReview, repo_root: Path) -> None:
    """Validate hashes, excerpts, exact spans, and protected regions on disk."""
    source_path = resolve_repo_path(repo_root, review.source_path)
    candidate_path = resolve_repo_path(repo_root, review.candidate_path)
    if sha256_path(source_path) != review.source_sha256:
        message = "repair-ready review English source hash changed"
        raise ValueError(message)
    if sha256_path(candidate_path) != review.candidate_sha256:
        message = "repair-ready review Chinese candidate hash changed"
        raise ValueError(message)
    source = source_path.read_text(encoding="utf-8")
    candidate = candidate_path.read_text(encoding="utf-8")
    for evidence in review.source_report_evidence:
        report_path = resolve_repo_path(repo_root, evidence.path)
        if sha256_path(report_path) != evidence.sha256:
            message = f"source audit report hash changed: {evidence.path}"
            raise ValueError(message)
    for issue in review.issues:
        if issue.source_excerpt not in source:
            message = f"English excerpt is absent for issue {issue.issue_id}"
            raise ValueError(message)
        located = locate_candidate_span(candidate, issue.candidate_span.text)
        if located != issue.candidate_span:
            message = f"candidate span metadata changed for issue {issue.issue_id}"
            raise ValueError(message)


def load_repair_ready_review(path: Path, repo_root: Path) -> RepairReadyReview:
    """Load a UTF-8 or UTF-8-BOM repair-ready review and validate its files."""
    review = RepairReadyReview.model_validate_json(path.read_text(encoding="utf-8-sig"))
    validate_review_artifacts(review, repo_root)
    return review


def write_repair_ready_review(path: Path, review: RepairReadyReview) -> None:
    """Atomically write a canonical repair-ready review."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    _ = temporary.write_text(
        review.model_dump_json(indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    _ = temporary.replace(path)


def _frontmatter_end(markdown: str) -> int:
    if not markdown.startswith("---\n") and not markdown.startswith("---\r\n"):
        return 0
    match = re.search(r"(?:\r?\n)---(?:\r?\n)", markdown[3:])
    if match is None:
        message = "candidate has unclosed frontmatter"
        raise ValueError(message)
    return 3 + match.end()


def parse_markdown_fences(markdown: str) -> tuple[MarkdownFence, ...]:
    """Parse fenced blocks and retain exact content and marker boundaries."""
    intervals: list[MarkdownFence] = []
    offset = 0
    active_start: int | None = None
    active_content_start = 0
    active_marker = ""
    active_marker_length = 0
    active_language = ""
    for line in markdown.splitlines(keepends=True):
        marker = re.match(r"^\s*(`{3,}|~{3,})([^\r\n]*)", line)
        if active_start is None:
            if marker is not None:
                active_start = offset
                active_content_start = offset + len(line)
                active_marker = marker.group(1)[0]
                active_marker_length = len(marker.group(1))
                info = marker.group(2).strip()
                active_language = (
                    info.split(maxsplit=1)[0].casefold() if info else ""
                )
        elif re.match(
            rf"^\s*{re.escape(active_marker)}"
            rf"{{{active_marker_length},}}\s*(?:\r?\n)?$",
            line,
        ):
            intervals.append(
                MarkdownFence(
                    start=active_start,
                    content_start=active_content_start,
                    content_end=offset,
                    end=offset + len(line),
                    language=active_language,
                )
            )
            active_start = None
            active_content_start = 0
            active_marker = ""
            active_marker_length = 0
            active_language = ""
        offset += len(line)
    if active_start is not None:
        message = "candidate has an unclosed fenced code block"
        raise ValueError(message)
    return tuple(intervals)

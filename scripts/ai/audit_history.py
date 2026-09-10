# Copyright 2026

"""Recover still-applicable historical audit issues from content evidence."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, Literal, cast

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

if TYPE_CHECKING:
    from pathlib import Path

AssignedReviewer = Literal["gpt-5.6-terra", "grok-4.5"]

AuditDisposition = Literal[
    "carry-forward",
    "needs-reconcile",
    "not-present-after-source-change",
    "rejected-with-reason",
]
MatchKind = Literal["exact", "whitespace"]
Severity = Literal["high", "medium", "low"]

_SOURCE_ID_RE = re.compile(r"^(?:claude-code|codex)/[a-z0-9][a-z0-9/-]*$")
_WHITESPACE_RE = re.compile(r"\s+")
_CJK_RE = re.compile(r"[\u3400-\u9fff]")
_MIN_WHITESPACE_WORDS = 2
_NUL = "\0"
_INVALID_STATUSES = frozenset(
    {
        "invalid",
        "rejected",
        "network-error",
        "network_error",
        "synthetic",
        "error",
    }
)
_SEVERITY_ALIASES: dict[str, Severity] = {
    "critical": "high",
    "error": "high",
    "fail": "high",
    "high": "high",
    "major": "medium",
    "medium": "medium",
    "warn": "medium",
    "warning": "medium",
    "info": "low",
    "low": "low",
    "minor": "low",
}
_CANDIDATE_FIELDS = (
    "candidate_span_text",
    "chinese_excerpt",
    "candidate_excerpt",
)
_SOURCE_FIELDS = (
    "source_excerpt",
    "english_excerpt",
    "source_span_text",
    "english_span_text",
    "source_text",
)

__all__ = (
    "AuditDisposition",
    "AuditHistoryRecovery",
    "AuditHistoryReportRejection",
    "HistoricalIssueRecovery",
    "HistoricalReportReference",
    "MatchedSpan",
    "recover_audit_history",
)


class _StrictModel(BaseModel):
    """Immutable, extra-forbidding history recovery contract."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )


class MatchedSpan(_StrictModel):
    """One current final-site-shape span recovered without semantic guessing."""

    text: str = Field(min_length=1)
    match_kind: MatchKind
    start_offset: int = Field(ge=0)
    end_offset: int = Field(gt=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _offsets_cover_text(self) -> MatchedSpan:
        if self.end_offset - self.start_offset != len(self.text):
            message = "matched span offsets do not cover its text"
            raise ValueError(message)
        return self


class HistoricalReportReference(_StrictModel):
    """One exact historical report issue contributing evidence to a recovery."""

    report_path: str = Field(min_length=1)
    report_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    issue_id: str = Field(min_length=1)

    @field_validator("report_path")
    @classmethod
    def _path_is_relative(cls, value: str) -> str:
        return _require_relative_path(value)


class AuditHistoryReportRejection(_StrictModel):
    """A historical file deliberately excluded before it can affect repairs."""

    report_path: str = Field(min_length=1)
    reason: str = Field(min_length=1)

    @field_validator("report_path")
    @classmethod
    def _path_is_relative(cls, value: str) -> str:
        return _require_relative_path(value)


class HistoricalIssueRecovery(_StrictModel):
    """A deduplicated historical issue and its current-content disposition."""

    recovery_id: str = Field(pattern=r"^history-[0-9a-f]{20}$")
    source_id: str
    assigned_reviewer: AssignedReviewer
    severity: Severity
    category: str = Field(min_length=1)
    location: str = Field(min_length=1)
    source_excerpt: str = ""
    candidate_span_text: str = ""
    explanation: str = ""
    semantic_evidence_key: str = Field(pattern=r"^[0-9a-f]{64}$")
    candidate_span_key: str = Field(pattern=r"^[0-9a-f]{64}$")
    disposition: AuditDisposition
    reason: str = Field(min_length=1)
    source_match: MatchedSpan | None = None
    candidate_match: MatchedSpan | None = None
    source_reports: tuple[HistoricalReportReference, ...] = Field(min_length=1)

    @field_validator("source_id")
    @classmethod
    def _safe_source_id(cls, value: str) -> str:
        if _SOURCE_ID_RE.fullmatch(value) is None or ".." in value:
            message = "history recovery source_id is not a safe manifest route"
            raise ValueError(message)
        return value

    @model_validator(mode="after")
    def _disposition_has_sufficient_evidence(self) -> HistoricalIssueRecovery:
        if (
            self.disposition == "carry-forward"
            and (self.source_match is None or self.candidate_match is None)
        ):
            message = "carry-forward recovery lacks current source or candidate evidence"
            raise ValueError(message)
        if self.disposition == "not-present-after-source-change" and self.source_match is not None:
            message = "source-change disposition unexpectedly has a source match"
            raise ValueError(message)
        if self.source_reports != tuple(sorted(self.source_reports, key=_reference_sort_key)):
            message = "history report references are not deterministically ordered"
            raise ValueError(message)
        return self


class AuditHistoryRecovery(_StrictModel):
    """Strict, deterministic recovery result for one assigned page reviewer."""

    version: Literal[1] = 1
    source_id: str
    assigned_reviewer: AssignedReviewer
    english_path: str = Field(min_length=1)
    chinese_path: str = Field(min_length=1)
    english_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    chinese_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    include_low: bool
    scanned_report_count: int = Field(ge=0)
    accepted_report_count: int = Field(ge=0)
    rejected_reports: tuple[AuditHistoryReportRejection, ...] = ()
    issues: tuple[HistoricalIssueRecovery, ...] = ()

    @field_validator("source_id")
    @classmethod
    def _safe_source_id(cls, value: str) -> str:
        if _SOURCE_ID_RE.fullmatch(value) is None or ".." in value:
            message = "history recovery source_id is not a safe manifest route"
            raise ValueError(message)
        return value

    @field_validator("english_path", "chinese_path")
    @classmethod
    def _paths_are_relative(cls, value: str) -> str:
        return _require_relative_path(value)

    @model_validator(mode="after")
    def _result_is_deterministic(self) -> AuditHistoryRecovery:
        if self.accepted_report_count > self.scanned_report_count:
            message = "accepted history report count exceeds scanned reports"
            raise ValueError(message)
        if self.rejected_reports != tuple(
            sorted(self.rejected_reports, key=lambda item: (item.report_path, item.reason))
        ):
            message = "rejected history reports are not deterministically ordered"
            raise ValueError(message)
        if self.issues != tuple(sorted(self.issues, key=lambda item: item.recovery_id)):
            message = "history recoveries are not deterministically ordered"
            raise ValueError(message)
        return self


@dataclass(frozen=True)
class _DraftIssue:
    """Mutable implementation detail collected before immutable output construction."""

    report: HistoricalReportReference
    severity: Severity
    category: str
    location: str
    source_excerpt: str
    candidate_span_text: str
    explanation: str


def recover_audit_history(  # noqa: PLR0913
    *,
    repo_root: Path,
    source_id: str,
    assigned_reviewer: AssignedReviewer,
    english_path: Path,
    english_text: str,
    chinese_path: Path,
    chinese_text: str,
    history_root: Path,
    invalidation_root: Path | None = None,
    include_low: bool = False,
) -> AuditHistoryRecovery:
    """Recover exact historical issues without treating a page hash as a verdict.

    A report is accepted only when it names this exact source and the same assigned
    reviewer. Current text, not a stale page-level hash, determines whether its
    evidence can be carried into the next repair pass.
    """
    _require_source_id(source_id)
    root = repo_root.resolve()
    english_relative = _repo_relative(root, english_path)
    chinese_relative = _repo_relative(root, chinese_path)
    review_root = history_root.resolve()
    review_root_relative = _repo_relative(root, review_root)
    invalidated_reports = _load_invalidated_report_paths(
        root,
        (
            invalidation_root.resolve()
            if invalidation_root is not None
            else root / ".ai-local/rejected-reviews"
        ),
        review_root_relative=review_root_relative,
    )
    report_paths = (
        tuple(sorted(path for path in review_root.rglob("*.json") if path.is_file()))
        if review_root.is_dir()
        else ()
    )
    rejected: list[AuditHistoryReportRejection] = []
    drafts: list[_DraftIssue] = []
    accepted_reports = 0
    for report_path in report_paths:
        report_relative = _repo_relative(root, report_path)
        document = _read_json_object(report_path)
        if document is None:
            continue
        if document.get("source_id") != source_id:
            continue
        invalidation_reason = _invalidation_reason(
            report_relative,
            invalidated_reports,
        )
        rejection = invalidation_reason or _report_rejection_reason(
            document,
            report_path,
            assigned_reviewer,
        )
        if rejection is not None:
            rejected.append(
                AuditHistoryReportRejection(report_path=report_relative, reason=rejection)
            )
            continue
        accepted_reports += 1
        reference = HistoricalReportReference(
            report_path=report_relative,
            report_sha256=_sha256_path(report_path),
            issue_id="report",
        )
        issues_value = document.get("issues")
        if not isinstance(issues_value, list):
            continue
        issues = cast("list[object]", issues_value)
        for index, value in enumerate(issues):
            if not isinstance(value, dict):
                continue
            issue = cast("dict[str, object]", value)
            severity = _severity(issue.get("severity"))
            if severity is None or (severity == "low" and not include_low):
                continue
            issue_id = str(
                issue.get("issue_id")
                or issue.get("id")
                or f"issue-{index:04d}"
            ).strip()
            if not issue_id:
                issue_id = f"issue-{index:04d}"
            source_excerpt = _first_text(issue, _SOURCE_FIELDS)
            candidate_span_text = _first_text(issue, _CANDIDATE_FIELDS)
            drafts.append(
                _DraftIssue(
                    report=reference.model_copy(update={"issue_id": issue_id}),
                    severity=severity,
                    category=_required_text(issue, "category", "uncategorized"),
                    location=_required_text(issue, "location", "unspecified"),
                    source_excerpt=source_excerpt,
                    candidate_span_text=candidate_span_text,
                    explanation=_first_text(issue, ("explanation", "description", "finding")),
                )
            )
    issues = _recover_drafts(
        source_id=source_id,
        assigned_reviewer=assigned_reviewer,
        english_text=english_text,
        chinese_text=chinese_text,
        drafts=drafts,
    )
    return AuditHistoryRecovery(
        source_id=source_id,
        assigned_reviewer=assigned_reviewer,
        english_path=english_relative,
        chinese_path=chinese_relative,
        english_sha256=_sha256_text(english_text),
        chinese_sha256=_sha256_text(chinese_text),
        include_low=include_low,
        scanned_report_count=len(report_paths),
        accepted_report_count=accepted_reports,
        rejected_reports=tuple(sorted(rejected, key=lambda item: (item.report_path, item.reason))),
        issues=issues,
    )


def _load_invalidated_report_paths(
    repo_root: Path,
    invalidation_root: Path,
    *,
    review_root_relative: str,
) -> dict[str, tuple[str, ...]]:
    _ = _repo_relative(repo_root, invalidation_root)
    if not invalidation_root.is_dir():
        return {}
    ledgers: dict[str, list[str]] = {}
    for ledger_path in sorted(
        path for path in invalidation_root.rglob("*.json") if path.is_file()
    ):
        document = _read_json_object(ledger_path)
        if document is None:
            continue
        target = document.get("invalidated_report_path")
        if not isinstance(target, str):
            continue
        try:
            target_relative = _require_relative_path(target)
            ledger_relative = _repo_relative(repo_root, ledger_path)
        except ValueError:
            continue
        if target_relative != review_root_relative and not target_relative.startswith(
            f"{review_root_relative}/"
        ):
            continue
        ledgers.setdefault(target_relative, []).append(ledger_relative)
    return {
        target: tuple(sorted(set(paths)))
        for target, paths in sorted(ledgers.items())
    }


def _invalidation_reason(
    report_path: str,
    invalidated_reports: dict[str, tuple[str, ...]],
) -> str | None:
    ledgers = invalidated_reports.get(report_path)
    if ledgers is None:
        return None
    return f"invalidated-by-ledger:{','.join(ledgers)}"


def _recover_drafts(
    *,
    source_id: str,
    assigned_reviewer: AssignedReviewer,
    english_text: str,
    chinese_text: str,
    drafts: list[_DraftIssue],
) -> tuple[HistoricalIssueRecovery, ...]:
    grouped: dict[tuple[str, str], list[_DraftIssue]] = {}
    for draft in drafts:
        semantic_key = _semantic_key(source_id, draft)
        candidate_key = _sha256_text(_compact_whitespace(draft.candidate_span_text))
        grouped.setdefault((semantic_key, candidate_key), []).append(draft)
    recoveries: list[HistoricalIssueRecovery] = []
    for (semantic_key, candidate_key), group in sorted(grouped.items()):
        exemplar = min(group, key=_draft_sort_key)
        source_match, source_reason = _unique_span(english_text, exemplar.source_excerpt)
        candidate_match, candidate_reason = _unique_span(
            chinese_text,
            exemplar.candidate_span_text,
        )
        disposition, reason = _disposition(
            source_excerpt=exemplar.source_excerpt,
            candidate_excerpt=exemplar.candidate_span_text,
            source_match=source_match,
            source_reason=source_reason,
            candidate_match=candidate_match,
            candidate_reason=candidate_reason,
        )
        identity = (
            f"{source_id}{_NUL}{assigned_reviewer}{_NUL}"
            f"{semantic_key}{_NUL}{candidate_key}"
        )
        recovery_id = f"history-{_sha256_text(identity)[:20]}"
        references = tuple(sorted((draft.report for draft in group), key=_reference_sort_key))
        recoveries.append(
            HistoricalIssueRecovery(
                recovery_id=recovery_id,
                source_id=source_id,
                assigned_reviewer=assigned_reviewer,
                severity=exemplar.severity,
                category=exemplar.category,
                location=exemplar.location,
                source_excerpt=exemplar.source_excerpt,
                candidate_span_text=exemplar.candidate_span_text,
                explanation=exemplar.explanation,
                semantic_evidence_key=semantic_key,
                candidate_span_key=candidate_key,
                disposition=disposition,
                reason=reason,
                source_match=source_match,
                candidate_match=candidate_match,
                source_reports=references,
            )
        )
    return tuple(sorted(recoveries, key=lambda item: item.recovery_id))


def _report_rejection_reason(  # noqa: PLR0911
    document: dict[str, object],
    path: Path,
    assigned_reviewer: AssignedReviewer,
) -> str | None:
    path_parts = {part.casefold() for part in path.parts}
    if path_parts & {"rejected-reviews", "rejected", "invalid", "synthetic"}:
        return "rejected-or-invalid-report-path"
    if document.get("synthetic") is True:
        return "synthetic-report"
    if (
        document.get("review_completed") is False
        or document.get("review_verdict_recorded") is False
    ):
        return "incomplete-or-network-report"
    for field in ("status", "verdict", "outcome", "state"):
        value = document.get(field)
        if isinstance(value, str) and value.casefold().replace("_", "-") in _INVALID_STATUSES:
            return f"excluded-{field}"
    reviewer_values = tuple(
        str(document[field]).strip()
        for field in ("assigned_reviewer", "review_model", "reviewer")
        if isinstance(document.get(field), str) and str(document[field]).strip()
    )
    if not reviewer_values:
        return "missing-assigned-reviewer"
    if len(set(reviewer_values)) != 1:
        return "inconsistent-reviewer-fields"
    if reviewer_values[0] != assigned_reviewer:
        return "assigned-reviewer-mismatch"
    return None


def _disposition(  # noqa: PLR0913
    *,
    source_excerpt: str,
    candidate_excerpt: str,
    source_match: MatchedSpan | None,
    source_reason: str,
    candidate_match: MatchedSpan | None,
    candidate_reason: str,
) -> tuple[AuditDisposition, str]:
    if not candidate_excerpt:
        return "rejected-with-reason", "report issue has no candidate excerpt"
    if not source_excerpt:
        return "needs-reconcile", "report issue has no source excerpt"
    if source_match is None and source_reason == "not-present":
        return "not-present-after-source-change", "source excerpt is absent from current English"
    if source_match is None:
        return "needs-reconcile", f"source excerpt {source_reason} in current English"
    if candidate_match is None:
        return "needs-reconcile", f"candidate excerpt {candidate_reason} in current Chinese"
    return "carry-forward", "source and candidate evidence uniquely recovered"


def _unique_span(  # noqa: PLR0911
    text: str,
    excerpt: str,
) -> tuple[MatchedSpan | None, str]:
    if not excerpt:
        return None, "missing"
    exact_starts = _all_starts(text, excerpt)
    if len(exact_starts) == 1:
        return _matched_span(text, exact_starts[0], len(excerpt), "exact"), "exact"
    if len(exact_starts) > 1:
        return None, "ambiguous"
    compact_excerpt = _compact_whitespace(excerpt)
    if not compact_excerpt:
        return None, "not-present"
    words = tuple(part for part in _WHITESPACE_RE.split(excerpt.strip()) if part)
    separator = r"\s+"
    if len(words) < _MIN_WHITESPACE_WORDS:
        if _CJK_RE.search(excerpt) is None:
            return None, "not-present"
        words = tuple(excerpt)
        separator = r"\s*"
    expression = re.compile(separator.join(re.escape(word) for word in words))
    matches = tuple(expression.finditer(text))
    if len(matches) != 1:
        return None, "ambiguous" if matches else "not-present"
    match = matches[0]
    recovered = match.group(0)
    if _without_whitespace(recovered) != _without_whitespace(excerpt):
        return None, "not-present"
    return _matched_span(text, match.start(), len(recovered), "whitespace"), "whitespace"


def _matched_span(text: str, start: int, length: int, match_kind: MatchKind) -> MatchedSpan:
    value = text[start : start + length]
    return MatchedSpan(
        text=value,
        match_kind=match_kind,
        start_offset=start,
        end_offset=start + length,
        sha256=_sha256_text(value),
    )


def _all_starts(text: str, excerpt: str) -> tuple[int, ...]:
    starts: list[int] = []
    start = 0
    while True:
        found = text.find(excerpt, start)
        if found < 0:
            return tuple(starts)
        starts.append(found)
        start = found + 1


def _semantic_key(source_id: str, draft: _DraftIssue) -> str:
    payload = {
        "source_id": source_id,
        "severity": draft.severity,
        "category": _compact_whitespace(draft.category),
        "location": _compact_whitespace(draft.location),
        "source_excerpt": _compact_whitespace(draft.source_excerpt),
        "explanation": _compact_whitespace(draft.explanation),
    }
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return _sha256_text(encoded)


def _first_text(issue: dict[str, object], fields: tuple[str, ...]) -> str:
    for field in fields:
        value = issue.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _required_text(issue: dict[str, object], field: str, fallback: str) -> str:
    value = issue.get(field)
    return value.strip() if isinstance(value, str) and value.strip() else fallback


def _severity(value: object) -> Severity | None:
    if not isinstance(value, str):
        return None
    normalized = value.casefold().strip()
    return _SEVERITY_ALIASES.get(normalized)


def _read_json_object(path: Path) -> dict[str, object] | None:
    try:
        value = cast("object", json.loads(path.read_text(encoding="utf-8-sig")))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return cast("dict[str, object]", value) if isinstance(value, dict) else None


def _draft_sort_key(draft: _DraftIssue) -> tuple[str, str, str, str, str]:
    return (
        draft.report.report_path,
        draft.report.issue_id,
        draft.category,
        draft.location,
        draft.explanation,
    )


def _reference_sort_key(reference: HistoricalReportReference) -> tuple[str, str]:
    return reference.report_path, reference.issue_id


def _compact_whitespace(value: str) -> str:
    return _WHITESPACE_RE.sub(" ", value).strip()


def _without_whitespace(value: str) -> str:
    return _WHITESPACE_RE.sub("", value)


def _sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _require_source_id(source_id: str) -> None:
    if _SOURCE_ID_RE.fullmatch(source_id) is None or ".." in source_id:
        message = "history recovery source_id is not a safe manifest route"
        raise ValueError(message)


def _repo_relative(repo_root: Path, path: Path) -> str:
    try:
        relative = path.resolve().relative_to(repo_root)
    except ValueError as error:
        message = "history recovery path is outside repo_root"
        raise ValueError(message) from error
    return _require_relative_path(relative.as_posix())


def _require_relative_path(value: str) -> str:
    normalized = value.replace("\\", "/")
    if not normalized or normalized.startswith("/") or ":" in normalized:
        message = "history recovery path must be sanitized repository-relative"
        raise ValueError(message)
    parts = tuple(part for part in normalized.split("/") if part)
    if not parts or any(part in {".", ".."} for part in parts):
        message = "history recovery path must be sanitized repository-relative"
        raise ValueError(message)
    return "/".join(parts)

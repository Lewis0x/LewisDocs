# Copyright 2026

"""Deterministic evidence checks for assigned full-page review findings."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Final

from scripts.ai.audit_coverage import recover_unique_whitespace_span

if TYPE_CHECKING:
    from pathlib import Path

_HEADING_RE: Final = re.compile(
    r"^(?P<marks>#{1,6})[ \t]+(?P<title>.+?)[ \t]*$"
)
_FENCE_RE: Final = re.compile(r"^[ \t]*(?P<marker>`{3,}|~{3,})")
_HTML_COMMENT_RE: Final = re.compile(r"<!--.*?-->", re.DOTALL)
_MISSING_SECTION_CATEGORY: Final = "missing_translation_content"


class FinalReviewEvidenceError(ValueError):
    """A schema-valid reviewer claim contradicted by hash-bound files."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        issue_index: int | None = None,
    ) -> None:
        """Store a stable evidence code alongside the human-readable reason."""
        self.code = code
        self.issue_index = issue_index
        prefix = (
            f"issue {issue_index + 1}: "
            if issue_index is not None
            else ""
        )
        super().__init__(f"{code}: {prefix}{message}")


@dataclass(frozen=True)
class _Section:
    level: int
    start: int
    content_start: int
    end: int


def validate_final_review_issue_evidence(
    *,
    source_path: Path,
    candidate_path: Path,
    issues: tuple[dict[str, object], ...],
) -> None:
    """Reject issue claims that cannot be proven from the reviewed page pair."""
    if not issues:
        return
    source = source_path.read_text(encoding="utf-8-sig")
    candidate = candidate_path.read_text(encoding="utf-8-sig")
    source_sections = _sections(source)
    candidate_sections = _sections(candidate)

    for index, issue in enumerate(issues):
        issue_id = _issue_id(issue, index)
        category = _required_text(issue, ("category",), index)
        source_excerpt = _required_text(
            issue,
            ("source_excerpt", "english_excerpt", "english_span"),
            index,
        )
        resolved_source = _recover(
            source,
            source_excerpt,
            issue_id=issue_id,
            field_name="source_excerpt",
            issue_index=index,
        )
        candidate_excerpt = _optional_text(
            issue,
            (
                "candidate_span_text",
                "chinese_excerpt",
                "candidate_excerpt",
                "chinese_span",
            ),
        )
        if candidate_excerpt is not None:
            _ = _recover(
                candidate,
                candidate_excerpt,
                issue_id=issue_id,
                field_name="candidate_excerpt",
                issue_index=index,
            )

        if category == _MISSING_SECTION_CATEGORY:
            _validate_missing_section_claim(
                source,
                candidate,
                source_sections,
                candidate_sections,
                resolved_source,
                issue_index=index,
            )
        elif candidate_excerpt is None:
            code = "candidate_excerpt_missing"
            message = "a non-missing-content issue has no exact Chinese evidence"
            raise FinalReviewEvidenceError(
                code,
                message,
                issue_index=index,
            )


def _validate_missing_section_claim(  # noqa: PLR0913
    source: str,
    candidate: str,
    source_sections: tuple[_Section, ...],
    candidate_sections: tuple[_Section, ...],
    source_excerpt: str,
    *,
    issue_index: int,
) -> None:
    first_line = source_excerpt.splitlines()[0] if source_excerpt else ""
    heading = _HEADING_RE.fullmatch(first_line)
    if heading is None:
        code = "missing_section_identity_unproven"
        message = "missing content must identify an exact source heading"
        raise FinalReviewEvidenceError(
            code,
            message,
            issue_index=issue_index,
        )
    excerpt_start = source.index(source_excerpt)
    source_index = next(
        (
            index
            for index, section in enumerate(source_sections)
            if section.start == excerpt_start
        ),
        None,
    )
    if source_index is None:
        code = "missing_section_identity_unproven"
        message = "source excerpt does not start at a parsed heading"
        raise FinalReviewEvidenceError(
            code,
            message,
            issue_index=issue_index,
        )
    if source_index >= len(candidate_sections):
        return
    source_section = source_sections[source_index]
    candidate_section = candidate_sections[source_index]
    if source_section.level != candidate_section.level:
        return
    candidate_body = candidate[
        candidate_section.content_start : candidate_section.end
    ]
    if _has_meaningful_body(candidate_body):
        code = "missing_section_claim_contradicted"
        message = (
            "the structurally corresponding Chinese section exists and "
            "contains a non-empty body"
        )
        raise FinalReviewEvidenceError(
            code,
            message,
            issue_index=issue_index,
        )


def _recover(
    text: str,
    excerpt: str,
    *,
    issue_id: str,
    field_name: str,
    issue_index: int,
) -> str:
    try:
        return recover_unique_whitespace_span(
            text,
            excerpt,
            issue_id=issue_id,
            field_name=field_name,
        )
    except ValueError as error:
        code = f"{field_name}_unproven"
        raise FinalReviewEvidenceError(
            code,
            str(error),
            issue_index=issue_index,
        ) from error


def _sections(markdown: str) -> tuple[_Section, ...]:
    headings: list[tuple[int, int, int]] = []
    offset = 0
    active_fence: tuple[str, int] | None = None
    for line in markdown.splitlines(keepends=True):
        fence = _FENCE_RE.match(line)
        if active_fence is not None:
            if (
                fence is not None
                and fence.group("marker")[0] == active_fence[0]
                and len(fence.group("marker")) >= active_fence[1]
                and not line[len(fence.group("marker")) :].strip()
            ):
                active_fence = None
            offset += len(line)
            continue
        if fence is not None:
            marker = fence.group("marker")
            active_fence = (marker[0], len(marker))
            offset += len(line)
            continue
        heading = _HEADING_RE.match(line.rstrip("\r\n"))
        if heading is not None:
            headings.append(
                (len(heading.group("marks")), offset, offset + len(line))
            )
        offset += len(line)

    sections: list[_Section] = []
    for index, (level, start, content_start) in enumerate(headings):
        end = len(markdown)
        for next_level, next_start, _next_content_start in headings[index + 1 :]:
            if next_level <= level:
                end = next_start
                break
        sections.append(
            _Section(
                level=level,
                start=start,
                content_start=content_start,
                end=end,
            )
        )
    return tuple(sections)


def _has_meaningful_body(body: str) -> bool:
    without_comments = _HTML_COMMENT_RE.sub("", body)
    for line in without_comments.splitlines():
        stripped = line.strip()
        if not stripped or _HEADING_RE.match(stripped):
            continue
        return True
    return False


def _issue_id(issue: dict[str, object], index: int) -> str:
    value = _optional_text(issue, ("issue_id", "id"))
    return value or f"final-review-{index + 1}"


def _required_text(
    issue: dict[str, object],
    keys: tuple[str, ...],
    issue_index: int,
) -> str:
    value = _optional_text(issue, keys)
    if value is None:
        code = "issue_evidence_missing"
        message = f"missing required field from {', '.join(keys)}"
        raise FinalReviewEvidenceError(
            code,
            message,
            issue_index=issue_index,
        )
    return value


def _optional_text(
    issue: dict[str, object],
    keys: tuple[str, ...],
) -> str | None:
    for key in keys:
        value: Any = issue.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return None

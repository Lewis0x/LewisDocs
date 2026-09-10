# Copyright 2026

"""Deterministic local checks that make deep semantic audits more complete.

The preflight is intentionally narrower than a semantic review: it derives
high-confidence structural defects and candidate hints directly from the final
VitePress-shaped EN/ZH Markdown pair.  It never calls a provider or reads
pipeline state.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, ClassVar, Final, Literal, Self, cast

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from scripts.ai.final_shape import inspect_final_shape_pair
from scripts.ai.review_contract import sha256_path, sha256_text
from scripts.rewrite_links import vitepress_slugify

if TYPE_CHECKING:
    from pathlib import Path

_SOURCE_ID_RE: Final = re.compile(r"^(?:claude-code|codex)/[a-z0-9][a-z0-9/-]*$")
_HEADING_RE: Final = re.compile(r"^(?P<indent>[ \t]*)(?P<marks>#{1,6})[ \t]+(?P<title>.+?)\s*$")
_CUSTOM_HEADING_ANCHOR_RE: Final = re.compile(r"[ \t]+\{#(?P<anchor>[^}\s]+)\}[ \t]*$")
_INLINE_LINK_LABEL_RE: Final = re.compile(r"!?\[([^\]]*)]\([^\)\r\n]*\)")
_INLINE_HTML_RE: Final = re.compile(r"<[^>\r\n]+>")
_FENCE_RE: Final = re.compile(
    r"^(?P<indent>[ \t]*)(?P<marker>`{3,}|~{3,})(?P<header>[^\r\n]*)$"
)
_INLINE_CODE_RE: Final = re.compile(r"(?<![\\`])`(?:\\`|[^`\r\n])+`(?!`)")
_LIST_RE: Final = re.compile(
    r"^(?P<indent>[ \t]*)(?P<marker>(?:[-+*])|(?:\d+[.)]))[ \t]+(?P<body>\S.*)$"
)
_MARKDOWN_FRAGMENT_RE: Final = re.compile(
    r"(?<!\!)\[(?P<label>[^\]\r\n]+)]\(\s*#(?P<fragment>[^)\s]+)[^)]*\)"
)
_HTML_FRAGMENT_RE: Final = re.compile(
    r"<a\b[^>]*?\bhref\s*=\s*(?P<quote>[\"'])#(?P<fragment>[^\"'\s>]+)(?P=quote)[^>]*>",
    re.IGNORECASE,
)
_HTML_HEADING_ID_RE: Final = re.compile(
    r"<h[1-6]\b[^>]*?\bid\s*=\s*(?P<quote>[\"'])(?P<anchor>[^\"'\s>]+)(?P=quote)[^>]*>",
    re.IGNORECASE,
)
_MARKDOWN_LINK_RE: Final = re.compile(
    r"(?<!\!)\[(?P<label>[^\]\r\n]+)]\((?P<target>[^)\r\n]+)\)"
)
_ELLIPSIS_RE: Final = re.compile(
    r"(?:\.\.\.|…{1,}|\[\s*(?:truncated|omitted)\s*]|(?:已)?截断)",
    re.IGNORECASE,
)
_ASCII_WORD_RE: Final = re.compile(r"[A-Za-z]{2,}")
_HAN_RE: Final = re.compile(r"[\u3400-\u9fff]")
_URL_LABEL_RE: Final = re.compile(r"^(?:https?://|www\.)", re.IGNORECASE)
_HTML_RE: Final = re.compile(r"<[^>]+>")
_USER_FACING_FENCE_LANGUAGES: Final = frozenset(
    {"markdown", "md", "plaintext", "text"}
)
_MIN_USER_FACING_FENCE_WORDS: Final = 12
_DEFAULT_LINK_LABEL_ALLOWLIST: Final = (
    "AI",
    "API",
    "CLI",
    "Codex",
    "Claude",
    "GitHub",
    "GLM",
    "Grok",
    "IDE",
    "Kimi",
    "MCP",
    "OpenAI",
    "SDK",
    "VitePress",
)


class PreflightSeverity(StrEnum):
    """Severity of a deterministic preflight result."""

    HARD = "hard"
    CANDIDATE_HINT = "candidate_hint"


@dataclass(frozen=True, slots=True)
class _FenceBlock:
    """One complete fenced block with exact line and text evidence."""

    header: str
    body: str
    text: str
    line_start: int
    line_end: int


class _StrictModel(BaseModel):
    """Immutable evidence model base."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )


class CandidateSpan(_StrictModel):
    """One exact unique visible Chinese span suitable for a repair prompt."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=False,
    )

    text: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    line_start: int = Field(ge=1)
    line_end: int = Field(ge=1)
    occurrence_count: Literal[1] = 1

    @field_validator("text")
    @classmethod
    def _visible_exact_text(cls, value: str) -> str:
        if not value.strip():
            message = "candidate span text must contain visible content"
            raise ValueError(message)
        return value

    @model_validator(mode="after")
    def _valid_span(self) -> Self:
        if self.line_end < self.line_start:
            message = "candidate span line range is reversed"
            raise ValueError(message)
        if self.sha256 != sha256_text(self.text):
            message = "candidate span hash does not match its text"
            raise ValueError(message)
        return self


class PreflightFinding(_StrictModel):
    """A deterministic preflight result with repair-safe local evidence."""

    source_id: str
    finding_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    severity: PreflightSeverity
    code: str = Field(pattern=r"^[a-z0-9_]+$")
    message: str = Field(min_length=1)
    source_lines: tuple[int, ...] = ()
    candidate_lines: tuple[int, ...] = ()
    candidate_span: CandidateSpan | None = None
    blocked_reason: str | None = None

    @field_validator("source_id")
    @classmethod
    def _safe_source_id(cls, value: str) -> str:
        if _SOURCE_ID_RE.fullmatch(value) is None or ".." in value:
            message = "preflight source_id is not a safe AI route"
            raise ValueError(message)
        return value

    @model_validator(mode="after")
    def _deterministic_identity(self) -> Self:
        if (self.candidate_span is None) == (self.blocked_reason is None):
            message = "finding must have exactly one candidate span or blocked reason"
            raise ValueError(message)
        identity = "\0".join(
            (
                self.source_id,
                self.severity,
                self.code,
                self.message,
                self.candidate_span.sha256 if self.candidate_span else "",
                ",".join(map(str, self.source_lines)),
                ",".join(map(str, self.candidate_lines)),
                self.blocked_reason or "",
            )
        )
        if self.finding_id != sha256_text(identity):
            message = "preflight finding id is not deterministic"
            raise ValueError(message)
        return self


class AuditPreflightEvidence(_StrictModel):
    """Immutable deterministic preflight evidence for one final-site pair."""

    version: Literal[1] = 1
    source_id: str
    source_path: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    candidate_path: str = Field(min_length=1)
    candidate_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_heading_ids: tuple[str, ...]
    candidate_heading_ids: tuple[str, ...]
    findings: tuple[PreflightFinding, ...]
    hard_passed: bool

    @field_validator("source_id")
    @classmethod
    def _safe_source_id(cls, value: str) -> str:
        if _SOURCE_ID_RE.fullmatch(value) is None or ".." in value:
            message = "preflight source_id is not a safe AI route"
            raise ValueError(message)
        return value

    @model_validator(mode="after")
    def _result_matches_findings(self) -> Self:
        if self.hard_passed != all(
            finding.severity is not PreflightSeverity.HARD
            for finding in self.findings
        ):
            message = "hard pass flag does not match preflight findings"
            raise ValueError(message)
        if tuple(sorted(self.findings, key=lambda finding: finding.finding_id)) != self.findings:
            message = "preflight findings must be sorted by deterministic id"
            raise ValueError(message)
        if any(finding.source_id != self.source_id for finding in self.findings):
            message = "preflight finding source ids do not match their evidence"
            raise ValueError(message)
        return self


def inspect_audit_preflight_pair(  # noqa: PLR0913
    source_id: str,
    source_path: Path,
    candidate_path: Path,
    *,
    link_label_allowlist: tuple[str, ...] = _DEFAULT_LINK_LABEL_ALLOWLIST,
    source_path_value: str | None = None,
    candidate_path_value: str | None = None,
) -> AuditPreflightEvidence:
    """Inspect one materialized English/Chinese page pair without an LLM.

    ``source_path`` is English and ``candidate_path`` is Chinese.  The result
    is a stable evidence record: files with identical bytes produce identical
    hashes, findings, finding ids, and ordering.
    """
    source = source_path.read_text(encoding="utf-8")
    candidate = candidate_path.read_text(encoding="utf-8")
    # Reuse the existing final-site gate before deriving more repair-specific
    # evidence; this keeps fence and Markdown rendering assumptions aligned.
    final_shape = inspect_final_shape_pair(source_id, source_path, candidate_path)
    source_headings = _visible_headings(source)
    candidate_headings = _visible_headings(candidate)
    source_heading_ids = _vitepress_heading_ids(source)
    candidate_heading_ids = _vitepress_heading_ids(candidate)
    findings = [
        *_fragment_findings(source_id, candidate, set(candidate_heading_ids)),
        *_hierarchy_findings(
            source_id,
            source,
            candidate,
            source_headings,
            candidate_headings,
            final_shape_codes={finding.code for finding in final_shape.findings},
        ),
        *_user_facing_fence_findings(source_id, source, candidate),
        *_candidate_only_marker_findings(source_id, source, candidate),
        *_english_link_label_findings(source_id, candidate, link_label_allowlist),
    ]
    ordered = tuple(sorted(findings, key=lambda finding: finding.finding_id))
    return AuditPreflightEvidence(
        source_id=source_id,
        source_path=source_path_value or source_path.as_posix(),
        source_sha256=sha256_path(source_path),
        candidate_path=candidate_path_value or candidate_path.as_posix(),
        candidate_sha256=sha256_path(candidate_path),
        source_heading_ids=source_heading_ids,
        candidate_heading_ids=candidate_heading_ids,
        findings=ordered,
        hard_passed=not any(
            finding.severity is PreflightSeverity.HARD for finding in ordered
        ),
    )


def _visible_headings(markdown: str) -> list[tuple[int, int, str]]:
    return [
        (line_number, len(match.group("marks")), match.group("title"))
        for line_number, line, visible in _visible_lines(markdown)
        if visible
        and (match := _HEADING_RE.match(line)) is not None
    ]


def _visible_lists(markdown: str) -> list[tuple[int, int, str]]:
    return [
        (line_number, len(match.group("indent").expandtabs(4)), _list_kind(match.group("marker")))
        for line_number, line, visible in _visible_lines(markdown)
        if visible
        and (match := _LIST_RE.match(line)) is not None
    ]


def _visible_lines(markdown: str) -> list[tuple[int, str, bool]]:
    lines = markdown.splitlines()
    frontmatter = _frontmatter_line_numbers(lines)
    output: list[tuple[int, str, bool]] = []
    active_fence: tuple[str, int] | None = None
    for line_number, line in enumerate(lines, start=1):
        if line_number in frontmatter:
            output.append((line_number, line, False))
            continue
        fence = _FENCE_RE.match(line)
        if active_fence is not None:
            output.append((line_number, line, False))
            if _closes_fence(fence, active_fence):
                active_fence = None
            continue
        if fence is not None:
            marker = fence.group("marker")
            active_fence = (marker[0], len(marker))
            output.append((line_number, line, False))
            continue
        output.append((line_number, line, True))
    return output


def _closes_fence(
    match: re.Match[str] | None,
    active: tuple[str, int],
) -> bool:
    if match is None or match.group("header").strip():
        return False
    marker = match.group("marker")
    return marker[0] == active[0] and len(marker) >= active[1]


def _vitepress_heading_ids(markdown: str) -> tuple[str, ...]:
    """Derive VitePress-compatible and explicit HTML heading anchors."""
    seen: dict[str, int] = {}
    anchors: list[str] = []
    for _, line, visible in _visible_lines(markdown):
        if not visible:
            continue
        heading = _HEADING_RE.match(line)
        if heading is not None:
            title = heading.group("title")
            custom = _CUSTOM_HEADING_ANCHOR_RE.search(title)
            if custom is not None:
                base = custom.group("anchor")
            else:
                rendered = _INLINE_LINK_LABEL_RE.sub(r"\1", title)
                base = vitepress_slugify(_INLINE_HTML_RE.sub("", rendered))
            duplicate = seen.get(base, 0)
            seen[base] = duplicate + 1
            anchors.append(base if duplicate == 0 else f"{base}-{duplicate}")
        anchors.extend(
            match.group("anchor") for match in _HTML_HEADING_ID_RE.finditer(line)
        )
    return tuple(anchors)


def _frontmatter_line_numbers(lines: list[str]) -> set[int]:
    if not lines or lines[0].strip() != "---":
        return set()
    for index, line in enumerate(lines[1:], start=2):
        if line.strip() == "---":
            return set(range(1, index + 1))
    return set()


def _fragment_findings(
    source_id: str,
    candidate: str,
    heading_ids: set[str],
) -> list[PreflightFinding]:
    findings: list[PreflightFinding] = []
    for line_number, line, visible in _visible_lines(candidate):
        if not visible:
            continue
        masked = _INLINE_CODE_RE.sub(lambda match: " " * len(match.group()), line)
        for match in (*_MARKDOWN_FRAGMENT_RE.finditer(masked), *_HTML_FRAGMENT_RE.finditer(masked)):
            fragment = match.group("fragment")
            if fragment in heading_ids:
                continue
            span, blocked_reason = _span_or_blocked(candidate, line_number, line, match.group())
            findings.append(
                _finding(
                    source_id,
                    PreflightSeverity.HARD,
                    "broken_same_page_fragment",
                    f"Broken Chinese same-page fragment: #{fragment}.",
                    candidate_lines=(line_number,),
                    candidate_span=span,
                    blocked_reason=blocked_reason,
                )
            )
    return findings


def _hierarchy_findings(  # noqa: PLR0913
    source_id: str,
    source: str,
    candidate: str,
    source_headings: list[tuple[int, int, str]],
    candidate_headings: list[tuple[int, int, str]],
    *,
    final_shape_codes: set[str],
) -> list[PreflightFinding]:
    findings: list[PreflightFinding] = []
    source_levels = tuple(level for _, level, _ in source_headings)
    candidate_levels = tuple(level for _, level, _ in candidate_headings)
    if source_levels != candidate_levels or "heading_structure" in final_shape_codes:
        index = _first_difference(source_levels, candidate_levels)
        candidate_line = candidate_headings[index][0] if index < len(candidate_headings) else None
        source_line = source_headings[index][0] if index < len(source_headings) else None
        span, blocked_reason = _line_span_or_blocked(candidate, candidate_line)
        findings.append(
            _finding(
                source_id,
                PreflightSeverity.HARD,
                "heading_hierarchy_mismatch",
                "English and Chinese heading ancestor levels differ.",
                source_lines=() if source_line is None else (source_line,),
                candidate_lines=() if candidate_line is None else (candidate_line,),
                candidate_span=span,
                blocked_reason=blocked_reason,
            )
        )

    source_lists = _visible_lists(source)
    candidate_lists = _visible_lists(candidate)
    source_signature = tuple((indent, kind) for _, indent, kind in source_lists)
    candidate_signature = tuple((indent, kind) for _, indent, kind in candidate_lists)
    if source_signature != candidate_signature or "list_structure" in final_shape_codes:
        index = _first_difference(source_signature, candidate_signature)
        candidate_line = candidate_lists[index][0] if index < len(candidate_lists) else None
        source_line = source_lists[index][0] if index < len(source_lists) else None
        span, blocked_reason = _line_span_or_blocked(candidate, candidate_line)
        findings.append(
            _finding(
                source_id,
                PreflightSeverity.HARD,
                "list_hierarchy_mismatch",
                "English and Chinese list nesting or marker hierarchy differs.",
                source_lines=() if source_line is None else (source_line,),
                candidate_lines=() if candidate_line is None else (candidate_line,),
                candidate_span=span,
                blocked_reason=blocked_reason,
            )
        )
    return findings


def _candidate_only_marker_findings(
    source_id: str,
    source: str,
    candidate: str,
) -> list[PreflightFinding]:
    source_markers = _markers(source)
    candidate_markers = _markers(candidate)
    source_counts = _marker_counts(source_markers)
    seen: dict[str, int] = {}
    findings: list[PreflightFinding] = []
    for line_number, line, marker in candidate_markers:
        kind = _marker_kind(marker)
        seen[kind] = seen.get(kind, 0) + 1
        if seen[kind] <= source_counts.get(kind, 0):
            continue
        span, blocked_reason = _span_or_blocked(candidate, line_number, line, marker)
        findings.append(
            _finding(
                source_id,
                PreflightSeverity.CANDIDATE_HINT,
                "candidate_only_truncation_marker",
                "Chinese visible text has an ellipsis or truncation marker absent from English.",
                candidate_lines=(line_number,),
                candidate_span=span,
                blocked_reason=blocked_reason,
            )
        )
    return findings


def _user_facing_fence_findings(
    source_id: str,
    source: str,
    candidate: str,
) -> list[PreflightFinding]:
    """Flag long reader-facing fence bodies copied unchanged into Chinese."""
    source_blocks = _fenced_blocks(source)
    candidate_blocks = _fenced_blocks(candidate)
    findings: list[PreflightFinding] = []
    for source_block, candidate_block in zip(
        source_blocks,
        candidate_blocks,
        strict=False,
    ):
        source_language = _fence_language(source_block.header)
        candidate_language = _fence_language(candidate_block.header)
        if (
            source_language not in _USER_FACING_FENCE_LANGUAGES
            or candidate_language != source_language
            or source_block.body.strip() != candidate_block.body.strip()
            or _HAN_RE.search(candidate_block.body) is not None
            or len(_ASCII_WORD_RE.findall(candidate_block.body))
            < _MIN_USER_FACING_FENCE_WORDS
        ):
            continue
        span, blocked_reason = _span_or_blocked(
            candidate,
            candidate_block.line_start,
            candidate.splitlines()[candidate_block.line_start - 1],
            candidate_block.text,
        )
        findings.append(
            _finding(
                source_id,
                PreflightSeverity.CANDIDATE_HINT,
                "identical_user_facing_fence",
                (
                    "A long text/Markdown fence is identical in English and "
                    "Chinese; verify whether it is reader-facing copy that must "
                    "be localized rather than a protected literal."
                ),
                source_lines=(
                    source_block.line_start,
                    source_block.line_end,
                ),
                candidate_lines=(
                    candidate_block.line_start,
                    candidate_block.line_end,
                ),
                candidate_span=span,
                blocked_reason=blocked_reason,
            )
        )
    return findings


def _fenced_blocks(markdown: str) -> list[_FenceBlock]:
    lines = markdown.splitlines()
    output: list[_FenceBlock] = []
    active: tuple[str, int, int, str] | None = None
    for line_number, line in enumerate(lines, start=1):
        match = _FENCE_RE.match(line)
        if active is not None:
            marker_character, marker_length, start, header = active
            if _closes_fence(match, (marker_character, marker_length)):
                output.append(
                    _FenceBlock(
                        header=header,
                        body="\n".join(lines[start: line_number - 1]),
                        text="\n".join(lines[start - 1 : line_number]),
                        line_start=start,
                        line_end=line_number,
                    )
                )
                active = None
            continue
        if match is None:
            continue
        marker = match.group("marker")
        active = (
            marker[0],
            len(marker),
            line_number,
            match.group("header").strip(),
        )
    return output


def _fence_language(header: str) -> str:
    return header.split(maxsplit=1)[0].casefold() if header else ""


def _markers(markdown: str) -> list[tuple[int, str, str]]:
    output: list[tuple[int, str, str]] = []
    for line_number, line, visible in _visible_lines(markdown):
        if not visible:
            continue
        masked = _INLINE_CODE_RE.sub(lambda match: " " * len(match.group()), line)
        output.extend((line_number, line, match.group()) for match in _ELLIPSIS_RE.finditer(masked))
    return output


def _marker_counts(markers: list[tuple[int, str, str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for _, _, marker in markers:
        kind = _marker_kind(marker)
        counts[kind] = counts.get(kind, 0) + 1
    return counts


def _marker_kind(value: str) -> str:
    stripped = value.strip().casefold()
    if stripped.startswith((".", "…")):
        return "ellipsis"
    if "truncated" in stripped or "截断" in stripped:
        return "truncation"
    return "omission"


def _english_link_label_findings(
    source_id: str,
    candidate: str,
    allowlist: tuple[str, ...],
) -> list[PreflightFinding]:
    allowed = {item.casefold() for item in allowlist}
    findings: list[PreflightFinding] = []
    for line_number, line, visible in _visible_lines(candidate):
        if not visible:
            continue
        masked = _INLINE_CODE_RE.sub(lambda match: " " * len(match.group()), line)
        for match in _MARKDOWN_LINK_RE.finditer(masked):
            label = _visible_link_label(match.group("label"))
            target = match.group("target").strip()
            if not _is_residual_english_link_label(label, target, allowed):
                continue
            span, blocked_reason = _span_or_blocked(candidate, line_number, line, match.group())
            findings.append(
                _finding(
                    source_id,
                    PreflightSeverity.CANDIDATE_HINT,
                    "visible_english_link_label",
                    "Chinese visible Markdown link label still contains ordinary English prose.",
                    candidate_lines=(line_number,),
                    candidate_span=span,
                    blocked_reason=blocked_reason,
                )
            )
    return findings


def _visible_link_label(label: str) -> str:
    return _HTML_RE.sub("", label).replace("**", "").replace("__", "").strip()


def _is_residual_english_link_label(label: str, target: str, allowed: set[str]) -> bool:
    if not label or _URL_LABEL_RE.match(label) is not None:
        return False
    plain_target = target.split(maxsplit=1)[0].strip("<>")
    if label.casefold() == plain_target.casefold():
        return False
    words = tuple(cast("list[str]", _ASCII_WORD_RE.findall(label)))
    if not words:
        return False
    return any(word.casefold() not in allowed for word in words)


def _span_or_blocked(
    candidate: str,
    line_number: int,
    line: str,
    preferred: str,
) -> tuple[CandidateSpan | None, str | None]:
    for value in (preferred, line):
        if value and candidate.count(value) == 1:
            return _make_span(candidate, value), None
    return None, (
        f"candidate evidence on line {line_number} is not uniquely addressable as an exact span"
    )


def _line_span_or_blocked(
    candidate: str,
    line_number: int | None,
) -> tuple[CandidateSpan | None, str | None]:
    if line_number is None:
        return None, "candidate has no corresponding visible line for this pair mismatch"
    line = candidate.splitlines()[line_number - 1]
    return _span_or_blocked(candidate, line_number, line, line)


def _make_span(candidate: str, text: str) -> CandidateSpan:
    start = candidate.index(text)
    end = start + len(text)
    return CandidateSpan(
        text=text,
        sha256=sha256_text(text),
        line_start=candidate.count("\n", 0, start) + 1,
        line_end=candidate.count("\n", 0, max(start, end - 1)) + 1,
    )


def _finding(  # noqa: PLR0913
    source_id: str,
    severity: PreflightSeverity,
    code: str,
    message: str,
    *,
    source_lines: tuple[int, ...] = (),
    candidate_lines: tuple[int, ...] = (),
    candidate_span: CandidateSpan | None,
    blocked_reason: str | None,
) -> PreflightFinding:
    identity = "\0".join(
        (
            source_id,
            severity,
            code,
            message,
            candidate_span.sha256 if candidate_span else "",
            ",".join(map(str, source_lines)),
            ",".join(map(str, candidate_lines)),
            blocked_reason or "",
        )
    )
    return PreflightFinding(
        source_id=source_id,
        finding_id=sha256_text(identity),
        severity=severity,
        code=code,
        message=message,
        source_lines=source_lines,
        candidate_lines=candidate_lines,
        candidate_span=candidate_span,
        blocked_reason=blocked_reason,
    )


def _first_difference(left: tuple[object, ...], right: tuple[object, ...]) -> int:
    for index, (left_item, right_item) in enumerate(zip(left, right, strict=False)):
        if left_item != right_item:
            return index
    return min(len(left), len(right))


def _list_kind(marker: str) -> str:
    return "ordered" if marker[0].isdigit() else "unordered"

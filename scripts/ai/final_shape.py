# Copyright 2026

"""Deterministic final-site-shape checks that run before semantic review."""

from __future__ import annotations

import re
from collections import Counter
from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING, ClassVar, Final, Literal, Self, cast

from pydantic import BaseModel, ConfigDict, Field, model_validator

from scripts.ai.review_contract import sha256_path

if TYPE_CHECKING:
    from pathlib import Path

_FENCE_RE: Final = re.compile(
    r"^(?P<indent>[ \t]*)(?P<marker>`{3,}|~{3,})(?P<header>[^\r\n]*)$"
)
_HEADING_RE: Final = re.compile(r"^[ \t]*(?:>[ \t]*)*(#{1,6})[ \t]+")
_LIST_RE: Final = re.compile(
    r"^(?P<indent>[ \t]*)(?:>[ \t]*)*(?:[-+*] |\d+[.)] )"
)
_TABLE_RE: Final = re.compile(r"^[ \t]*(?:>[ \t]*)*\|?.+\|.+\|?[ \t]*$")
_BLOCKQUOTE_RE: Final = re.compile(r"^[ \t]*(?P<quotes>(?:>[ \t]*)+)")
_MDX_TAG_RE: Final = re.compile(
    r"</?[A-Z][A-Za-z0-9]*(?:[ \t]+[^>\r\n]*)?/?>"
)
_INLINE_CODE_RE: Final = re.compile(
    r"(?<![\\`])`(?:\\`|[^`\r\n])+`(?!`)"
)
_HTML_IMAGE_RE: Final = re.compile(r"<img\b", re.IGNORECASE)
_MALFORMED_IMAGE_ATTRIBUTE_RE: Final = re.compile(
    r"""(?i)(?:^|[ \t])(?:alt|src)[ \t]*="""
)
_SOURCE_ID_RE: Final = re.compile(
    r"^(?:claude-code|codex)/[a-z0-9][a-z0-9/-]*$"
)
_INDENTED_CODE_WIDTH: Final = 4
_IMAGE_TITLE_MIN_LENGTH: Final = 2
_COMPACT_ITEMS_MAX: Final = 6


class FindingSide(StrEnum):
    """Location of one final-shape finding."""

    SOURCE = "source"
    CANDIDATE = "candidate"
    PAIR = "pair"


class _StrictModel(BaseModel):
    """Immutable evidence base."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )


class StructureFinding(_StrictModel):
    """One deterministic final-shape defect."""

    code: str = Field(pattern=r"^[a-z0-9_]+$")
    side: FindingSide
    message: str = Field(min_length=1)
    lines: tuple[int, ...] = ()


class MarkdownStructure(_StrictModel):
    """Stable structure extracted from one materialized Markdown page."""

    heading_levels: tuple[int, ...]
    fence_headers: tuple[str, ...]
    list_items: int = Field(ge=0)
    table_rows: int = Field(ge=0)
    blockquote_lines: int = Field(ge=0)
    links: int = Field(ge=0)
    images: int = Field(ge=0)
    non_anchor_link_targets: tuple[str, ...]
    image_targets: tuple[str, ...]
    suspicious_indented_lines: tuple[int, ...]
    malformed_image_lines: tuple[int, ...]
    residual_mdx_lines: tuple[int, ...]
    unclosed_fence_line: int | None = Field(default=None, ge=1)


class FinalShapeEvidence(_StrictModel):
    """Auditable deterministic evidence for one final-site-shape page pair."""

    version: Literal[1] = 1
    source_id: str
    source_path: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    candidate_path: str = Field(min_length=1)
    candidate_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source: MarkdownStructure
    candidate: MarkdownStructure
    findings: tuple[StructureFinding, ...]
    passed: bool
    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def _result_matches_findings(self) -> Self:
        if self.passed == bool(self.findings):
            message = "final-shape pass flag does not match its findings"
            raise ValueError(message)
        if _SOURCE_ID_RE.fullmatch(self.source_id) is None or ".." in self.source_id:
            message = "final-shape source_id is not a safe AI route"
            raise ValueError(message)
        return self


def inspect_final_shape_pair(
    source_id: str,
    source_path: Path,
    candidate_path: Path,
    *,
    source_path_value: str | None = None,
    candidate_path_value: str | None = None,
) -> FinalShapeEvidence:
    """Inspect a materialized English/Chinese pair without invoking an LLM."""
    source_text = source_path.read_text(encoding="utf-8")
    candidate_text = candidate_path.read_text(encoding="utf-8")
    source_structure, source_findings = _inspect_markdown(
        source_text,
        FindingSide.SOURCE,
    )
    candidate_structure, candidate_findings = _inspect_markdown(
        candidate_text,
        FindingSide.CANDIDATE,
    )
    findings = [
        *source_findings,
        *candidate_findings,
        *_pair_findings(source_structure, candidate_structure),
    ]
    return FinalShapeEvidence(
        source_id=source_id,
        source_path=source_path_value or source_path.as_posix(),
        source_sha256=sha256_path(source_path),
        candidate_path=candidate_path_value or candidate_path.as_posix(),
        candidate_sha256=sha256_path(candidate_path),
        source=source_structure,
        candidate=candidate_structure,
        findings=tuple(findings),
        passed=not findings,
    )


def require_final_shape_pair(
    source_id: str,
    source_path: Path,
    candidate_path: Path,
    *,
    source_path_value: str | None = None,
    candidate_path_value: str | None = None,
) -> FinalShapeEvidence:
    """Return evidence only when every deterministic final-shape gate passes."""
    evidence = inspect_final_shape_pair(
        source_id,
        source_path,
        candidate_path,
        source_path_value=source_path_value,
        candidate_path_value=candidate_path_value,
    )
    if evidence.findings:
        summary = "; ".join(
            f"{finding.code}:{finding.side}" for finding in evidence.findings[:8]
        )
        message = f"final-site-shape structural gate failed: {summary}"
        raise ValueError(message)
    return evidence


def validate_final_shape_evidence(
    evidence: FinalShapeEvidence,
    source_path: Path,
    candidate_path: Path,
) -> None:
    """Recompute evidence and reject stale or hand-authored structural claims."""
    if not evidence.passed:
        message = "final-shape evidence is not passing"
        raise ValueError(message)
    actual = inspect_final_shape_pair(
        evidence.source_id,
        source_path,
        candidate_path,
        source_path_value=evidence.source_path,
        candidate_path_value=evidence.candidate_path,
    )
    expected_payload = evidence.model_dump(
        mode="python",
        exclude={"checked_at", "source_path", "candidate_path"},
    )
    actual_payload = actual.model_dump(
        mode="python",
        exclude={"checked_at", "source_path", "candidate_path"},
    )
    if expected_payload != actual_payload:
        message = "final-shape evidence does not match the reviewed files"
        raise ValueError(message)


def write_final_shape_evidence(path: Path, evidence: FinalShapeEvidence) -> None:
    """Atomically write deterministic final-shape evidence."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    _ = temporary.write_text(
        evidence.model_dump_json(indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    _ = temporary.replace(path)


def _inspect_markdown(  # noqa: C901, PLR0912, PLR0915
    markdown: str,
    side: FindingSide,
) -> tuple[MarkdownStructure, list[StructureFinding]]:
    lines = markdown.splitlines()
    frontmatter = _frontmatter_lines(lines)
    heading_levels: list[int] = []
    fence_headers: list[str] = []
    link_targets: list[str] = []
    image_targets: list[str] = []
    suspicious_indented: list[int] = []
    malformed_images: list[int] = []
    residual_mdx: list[int] = []
    list_items = 0
    table_rows = 0
    blockquote_lines = 0
    active_fence: tuple[str, int] | None = None
    opening_fence_line: int | None = None
    active_list_content_indent: int | None = None
    links = 0
    images = 0

    for line_number, line in enumerate(lines, start=1):
        if line_number in frontmatter:
            continue
        fence = _FENCE_RE.match(line)
        if active_fence is not None:
            if _closes_fence(fence, active_fence):
                active_fence = None
                opening_fence_line = None
            continue
        if fence is not None:
            marker = fence.group("marker")
            active_fence = (marker[0], len(marker))
            opening_fence_line = line_number
            fence_headers.append(
                f"{marker[0] * 3}{fence.group('header').strip()}"
            )
            continue
        if not line.strip():
            continue

        heading = _HEADING_RE.match(line)
        if heading is not None:
            heading_levels.append(len(heading.group(1)))

        list_item = _LIST_RE.match(line)
        if list_item is not None:
            list_items += 1
            active_list_content_indent = _indent_width(list_item.group(0))
        else:
            indent = _leading_indent_width(line)
            if (
                active_list_content_indent is not None
                and indent >= active_list_content_indent
            ):
                pass
            else:
                active_list_content_indent = None
            if (
                indent >= _INDENTED_CODE_WIDTH
                and active_list_content_indent is None
            ):
                suspicious_indented.append(line_number)

        table_rows += _TABLE_RE.fullmatch(line) is not None
        blockquote = _BLOCKQUOTE_RE.match(line)
        if blockquote is not None:
            blockquote_lines += blockquote.group("quotes").count(">")

        parsed_links, unmatched_images = _inline_links(line)
        links += sum(not item[0] for item in parsed_links)
        images += sum(item[0] for item in parsed_links)
        link_targets.extend(
            _normalize_target(item[1])
            for item in parsed_links
            if not item[0] and not item[1].lstrip().startswith("#")
        )
        image_targets.extend(
            _normalize_target(item[1]) for item in parsed_links if item[0]
        )
        if (
            unmatched_images
            or _HTML_IMAGE_RE.search(line) is not None
            or any(
                not _valid_image_target(item[1])
                for item in parsed_links
                if item[0]
            )
        ):
            malformed_images.append(line_number)
        if _MDX_TAG_RE.search(_INLINE_CODE_RE.sub("", line)) is not None:
            residual_mdx.append(line_number)

    unclosed_fence_line = opening_fence_line
    structure = MarkdownStructure(
        heading_levels=tuple(heading_levels),
        fence_headers=tuple(fence_headers),
        list_items=list_items,
        table_rows=table_rows,
        blockquote_lines=blockquote_lines,
        links=links,
        images=images,
        non_anchor_link_targets=tuple(sorted(link_targets)),
        image_targets=tuple(sorted(image_targets)),
        suspicious_indented_lines=tuple(suspicious_indented),
        malformed_image_lines=tuple(malformed_images),
        residual_mdx_lines=tuple(residual_mdx),
        unclosed_fence_line=unclosed_fence_line,
    )
    findings = _single_page_findings(structure, side)
    return structure, findings


def _single_page_findings(
    structure: MarkdownStructure,
    side: FindingSide,
) -> list[StructureFinding]:
    findings: list[StructureFinding] = []
    if structure.unclosed_fence_line is not None:
        findings.append(
            StructureFinding(
                code="unclosed_fence",
                side=side,
                message="A fenced code block is not closed.",
                lines=(structure.unclosed_fence_line,),
            )
        )
    if structure.suspicious_indented_lines:
        findings.append(
            StructureFinding(
                code="top_level_indented_code",
                side=side,
                message=(
                    "Top-level four-space content would render as an indented "
                    "CommonMark code block."
                ),
                lines=structure.suspicious_indented_lines,
            )
        )
    if structure.malformed_image_lines:
        findings.append(
            StructureFinding(
                code="malformed_image",
                side=side,
                message="An image node is malformed or retained as raw HTML.",
                lines=structure.malformed_image_lines,
            )
        )
    if structure.residual_mdx_lines:
        findings.append(
            StructureFinding(
                code="residual_mdx",
                side=side,
                message="A final-site-shape page still contains an MDX component tag.",
                lines=structure.residual_mdx_lines,
            )
        )
    return findings


def _pair_findings(
    source: MarkdownStructure,
    candidate: MarkdownStructure,
) -> list[StructureFinding]:
    fields: tuple[tuple[str, object, object], ...] = (
        ("heading_structure", source.heading_levels, candidate.heading_levels),
        ("fence_structure", source.fence_headers, candidate.fence_headers),
        ("list_structure", source.list_items, candidate.list_items),
        ("table_structure", source.table_rows, candidate.table_rows),
        (
            "blockquote_structure",
            source.blockquote_lines,
            candidate.blockquote_lines,
        ),
        ("link_count", source.links, candidate.links),
        ("image_count", source.images, candidate.images),
        (
            "link_targets",
            source.non_anchor_link_targets,
            candidate.non_anchor_link_targets,
        ),
        ("image_targets", source.image_targets, candidate.image_targets),
    )
    findings: list[StructureFinding] = []
    for code, source_value, candidate_value in fields:
        if source_value == candidate_value:
            continue
        findings.append(
            StructureFinding(
                code=code,
                side=FindingSide.PAIR,
                message=(
                    f"English and Chinese final-site-shape {code} differs: "
                    f"en={_compact_value(source_value)}, "
                    f"zh-CN={_compact_value(candidate_value)}."
                ),
            )
        )
    return findings


def _frontmatter_lines(lines: list[str]) -> set[int]:
    if not lines or lines[0].strip() != "---":
        return set()
    for index, line in enumerate(lines[1:], start=2):
        if line.strip() == "---":
            return set(range(1, index + 1))
    return set()


def _closes_fence(
    match: re.Match[str] | None,
    active: tuple[str, int],
) -> bool:
    if match is None or match.group("header").strip():
        return False
    marker = match.group("marker")
    return marker[0] == active[0] and len(marker) >= active[1]


def _leading_indent_width(line: str) -> int:
    prefix = line[: len(line) - len(line.lstrip(" \t"))]
    return _indent_width(prefix)


def _indent_width(value: str) -> int:
    return len(value.expandtabs(4))


def _inline_links(line: str) -> tuple[list[tuple[bool, str]], bool]:
    parsed: list[tuple[bool, str]] = []
    cursor = 0
    unmatched_image = False
    while cursor < len(line):
        bracket = line.find("[", cursor)
        if bracket < 0:
            break
        is_image = bracket > 0 and line[bracket - 1] == "!"
        close = line.find("](", bracket + 1)
        if close < 0:
            unmatched_image = unmatched_image or is_image
            cursor = bracket + 1
            continue
        target_start = close + 2
        target_end = _closing_parenthesis(line, target_start)
        if target_end is None:
            unmatched_image = unmatched_image or is_image
            cursor = target_start
            continue
        parsed.append((is_image, line[target_start:target_end]))
        cursor = target_end + 1
    return parsed, unmatched_image


def _closing_parenthesis(line: str, start: int) -> int | None:
    depth = 1
    quote: str | None = None
    escaped = False
    for index in range(start, len(line)):
        character = line[index]
        if escaped:
            escaped = False
            continue
        if character == "\\":
            escaped = True
            continue
        if quote is not None:
            if character == quote:
                quote = None
            continue
        if character in {'"', "'"}:
            quote = character
        elif character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
            if depth == 0:
                return index
    return None


def _valid_image_target(target: str) -> bool:
    stripped = target.strip()
    if not stripped or _MALFORMED_IMAGE_ATTRIBUTE_RE.search(stripped) is not None:
        return False
    if stripped.startswith("<"):
        close = stripped.find(">")
        if close <= 1:
            return False
        remainder = stripped[close + 1 :].strip()
    else:
        destination, separator, remainder = stripped.partition(" ")
        if not destination:
            return False
        remainder = remainder.strip() if separator else ""
    if not remainder:
        return True
    return (
        len(remainder) >= _IMAGE_TITLE_MIN_LENGTH
        and remainder[0] in {'"', "'", "("}
        and remainder[-1] == {'"': '"', "'": "'", "(": ")"}[remainder[0]]
    )


def _normalize_target(value: str) -> str:
    target = value.strip()
    destination = target
    if target.startswith("<"):
        close = target.find(">")
        destination = target[1:close] if close > 0 else target
    elif " " in target:
        destination = target.split(" ", maxsplit=1)[0]
    return (
        destination.replace("/docs/zh-CN/", "/docs/en/")
        .replace("/ai/zh-CN/", "/ai/en/")
        .replace("\\", "/")
    )


def _compact_value(value: object) -> str:
    if isinstance(value, tuple):
        values = cast("tuple[object, ...]", value)
        if len(values) <= _COMPACT_ITEMS_MAX:
            return repr(values)
        return f"{len(values)} items"
    return str(value)


def structure_counter(structure: MarkdownStructure) -> Counter[str]:
    """Expose stable structural counts for adapters and diagnostics."""
    return Counter(
        {
            "headings": len(structure.heading_levels),
            "fences": len(structure.fence_headers),
            "lists": structure.list_items,
            "table_rows": structure.table_rows,
            "blockquotes": structure.blockquote_lines,
            "links": structure.links,
            "images": structure.images,
        }
    )

# Copyright 2026

"""Protect Markdown literals while prose is translated."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Final, NoReturn, TypeAlias

from scripts.ai.errors import AIAgentError, ErrorCode

_TOKEN_TEMPLATE: Final = "⟦LEWISDOCS_{index:04d}⟧"  # noqa: S105
_TOKEN_RE: Final = re.compile(r"⟦LEWISDOCS_\d{4}⟧")
_FAILURE_MESSAGE: Final = "translation validation failed"

_FENCE_RE: Final = re.compile(r"(?ms)^(?P<mark>`{3,}|~{3,})[^\n]*\n.*?^(?P=mark)[ \t]*(?:\n|$)")
_INLINE_CODE_RE: Final = re.compile(r"`[^`\n]+`")
_LINK_RE: Final = re.compile(r"!?\[[^\]\n]*\]\((?P<target>[^)\s]+)\)")
_URL_RE: Final = re.compile(r"https?://[^\s<>()\]]+")
_COMMAND_RE: Final = re.compile(r"npm run ai:sync")
_OPTION_RE: Final = re.compile(r"--[a-z0-9][a-z0-9-]*")
_IDENTIFIER_RE: Final = re.compile(
    r"(?:[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+|[A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+)"
)
_PATH_RE: Final = re.compile(r"(?:\.{0,2}/|/)[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]*[A-Za-z0-9_-])+")
_FILE_EXTENSIONS: Final = "cfg|css|html|ini|js|json|md|png|py|sh|svg|toml|ts|tsx|txt|yaml|yml"
_FILENAME_RE: Final = re.compile(rf"\b[A-Za-z0-9_.-]+\.(?:{_FILE_EXTENSIONS})\b")
_KNOWN_NAME_RE: Final = re.compile(
    r"(?:Claude Code|Codex CLI|Kimi Code|Moonshot API|kimi-for-coding|kimi-k3|k3)"
)

_HEADING_RE: Final = re.compile(r"^(#{1,6})\s+")
_LIST_RE: Final = re.compile(r"^([ \t]*)([-+*] |\d+\. )")
_QUOTE_RE: Final = re.compile(r"^[ \t]*(>+)")
_TABLE_DELIMITER_RE: Final = re.compile(r"^\s*:?-{3,}:?(?:\s*\|\s*:?-{3,}:?)+\s*$")

Match: TypeAlias = tuple[int, str, int, int]
StructureSignature: TypeAlias = tuple[
    tuple[int, ...],
    tuple[tuple[int, str], ...],
    tuple[int, ...],
    tuple[tuple[tuple[int, bool], ...], ...],
]


@dataclass(frozen=True, slots=True)
class ProtectedSpan:
    """One literal and its deterministic placeholder."""

    placeholder: str
    original: str


@dataclass(frozen=True, slots=True)
class ProtectedMarkdown:
    """Translation input plus the literals needed to restore it."""

    text: str
    spans: tuple[ProtectedSpan, ...]


def protect_markdown(markdown: str) -> ProtectedMarkdown:
    """Replace protected literals with deterministic source-order tokens."""
    matches = _select_matches(markdown)
    spans: list[ProtectedSpan] = []
    parts: list[str] = []
    cursor = 0
    for index, (_, _, start, end) in enumerate(matches):
        placeholder = _TOKEN_TEMPLATE.format(index=index)
        parts.extend((markdown[cursor:start], placeholder))
        spans.append(
            ProtectedSpan(
                placeholder=placeholder,
                original=markdown[start:end],
            )
        )
        cursor = end
    parts.append(markdown[cursor:])
    return ProtectedMarkdown(text="".join(parts), spans=tuple(spans))


def restore_and_validate(
    source: str,
    protected: ProtectedMarkdown,
    translated: str,
) -> str:
    """Restore literals after checking tokens and Markdown structure."""
    expected_tokens = tuple(span.placeholder for span in protected.spans)
    found_tokens = tuple(_TOKEN_RE.findall(translated))
    if found_tokens != expected_tokens:
        _fail()
    if _structure_signature(source) != _structure_signature(translated):
        _fail()

    restored = translated
    for span in protected.spans:
        restored = restored.replace(span.placeholder, span.original, 1)

    if _literal_signature(source) != _literal_signature(restored):
        _fail()
    return restored


def _select_matches(markdown: str) -> tuple[Match, ...]:
    candidates: list[Match] = []
    candidates.extend(_matches(markdown, _FENCE_RE, priority=0, kind="fence"))
    candidates.extend(_matches(markdown, _INLINE_CODE_RE, priority=1, kind="inline"))
    for match in _LINK_RE.finditer(markdown):
        start, end = match.span("target")
        candidates.append((2, "link_target", start, end))
    candidates.extend(_matches(markdown, _URL_RE, priority=3, kind="url"))
    literal_patterns = (
        ("command", _COMMAND_RE),
        ("option", _OPTION_RE),
        ("identifier", _IDENTIFIER_RE),
        ("path", _PATH_RE),
        ("filename", _FILENAME_RE),
        ("known_name", _KNOWN_NAME_RE),
    )
    for kind, pattern in literal_patterns:
        candidates.extend(_matches(markdown, pattern, priority=4, kind=kind))

    selected: list[Match] = []
    for candidate in sorted(candidates, key=lambda item: (item[0], item[2])):
        if not _overlaps(candidate, selected):
            selected.append(candidate)
    return tuple(sorted(selected, key=lambda item: item[2]))


def _matches(
    markdown: str,
    pattern: re.Pattern[str],
    *,
    priority: int,
    kind: str,
) -> list[Match]:
    return [(priority, kind, match.start(), match.end()) for match in pattern.finditer(markdown)]


def _overlaps(candidate: Match, selected: list[Match]) -> bool:
    start, end = candidate[2], candidate[3]
    return any(start < item[3] and end > item[2] for item in selected)


def _literal_signature(markdown: str) -> tuple[tuple[str, tuple[str, ...]], ...]:
    grouped: dict[str, Counter[str]] = {}
    for _, kind, start, end in _select_matches(markdown):
        grouped.setdefault(kind, Counter())[markdown[start:end]] += 1
    return tuple(
        (kind, tuple(sorted(counter.elements()))) for kind, counter in sorted(grouped.items())
    )


def _structure_signature(markdown: str) -> StructureSignature:
    headings: list[int] = []
    lists: list[tuple[int, str]] = []
    quotes: list[int] = []
    tables: list[tuple[tuple[int, bool], ...]] = []
    lines = markdown.splitlines()
    fenced_lines = _fenced_line_indexes(markdown)
    index = 0
    while index < len(lines):
        if index in fenced_lines:
            index += 1
            continue
        line = lines[index]
        if heading := _HEADING_RE.match(line):
            headings.append(len(heading.group(1)))
        if list_item := _LIST_RE.match(line):
            lists.append((len(list_item.group(1)), list_item.group(2)))
        if quote := _QUOTE_RE.match(line):
            quotes.append(len(quote.group(1)))
        if "|" in line:
            rows: list[str] = []
            while index < len(lines) and "|" in lines[index]:
                rows.append(lines[index])
                index += 1
            tables.append(_table_shape(rows))
            continue
        index += 1
    return (tuple(headings), tuple(lists), tuple(quotes), tuple(tables))


def _fenced_line_indexes(markdown: str) -> set[int]:
    indexes: set[int] = set()
    for match in _FENCE_RE.finditer(markdown):
        start = markdown.count("\n", 0, match.start())
        end = start + match.group(0).count("\n")
        indexes.update(range(start, end + 1))
    return indexes


def _table_shape(rows: list[str]) -> tuple[tuple[int, bool], ...]:
    shape: list[tuple[int, bool]] = []
    for row in rows:
        body = row.strip().strip("|")
        columns = len(body.split("|"))
        shape.append((columns, _TABLE_DELIMITER_RE.fullmatch(body) is not None))
    return tuple(shape)


def _fail() -> NoReturn:
    raise AIAgentError(
        code=ErrorCode.TRANSLATION_FAILED,
        message=_FAILURE_MESSAGE,
    )

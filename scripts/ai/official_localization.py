# Copyright 2026

"""Validation helpers for owner-published Chinese documentation."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Final

from scripts.rewrite_links import vitepress_slugify

if TYPE_CHECKING:
    from scripts.ai.types import Source

_EN_LOCALE: Final = "/docs/en/"
_ZH_LOCALE: Final = "/docs/zh-CN/"
_CJK_RE: Final = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
_FENCE_RE: Final = re.compile(
    r"(?ms)^(?P<indent>[ \t]*)(?P<mark>`{3,}|~{3,})[^\n]*\n"
    r".*?^(?P=indent)(?P=mark)[ \t]*(?:\n|$)"
)
_INLINE_CODE_RE: Final = re.compile(r"`[^`\n]+`")
_LINK_RE: Final = re.compile(r"!?\[[^\]\n]*\]\([^)]+\)")
_URL_RE: Final = re.compile(r"https?://\S+")
_HTML_RE: Final = re.compile(r"<[^>\n]+>")
_MDX_TAG_RE: Final = re.compile(r"<(/?)([A-Z][A-Za-z0-9]*)\b")
_HEADING_RE: Final = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*$")
_HTML_HEADING_RE: Final = re.compile(
    r"""^\s*<h([1-6])\s+id=["']([^"']+)["'][^>]*>""",
    re.IGNORECASE,
)
_LIST_RE: Final = re.compile(r"^[ \t]*(?:[-+*] |\d+[.)] )")
_TABLE_RE: Final = re.compile(r"^\s*\|?.+\|.+\|?\s*$")
_MARKDOWN_LINK_RE: Final = re.compile(r"!?\[[^\]\n]*\]\(([^)\s]+)\)")
_CUSTOM_HEADING_ANCHOR_RE: Final = re.compile(r"[ \t]+\{#([^}\s]+)\}[ \t]*$")
_INLINE_LINK_RE: Final = re.compile(r"!?\[([^\]]*)]\([^)\r\n]*\)")
_INLINE_HTML_RE: Final = re.compile(r"<[^>\r\n]+>")
_LONG_PROSE_MIN: Final = 80
_MIN_CJK: Final = 50
_UNTRANSLATED_PROSE_RATIO: Final = 0.8


def official_chinese_urls(source: Source) -> tuple[str, str]:
    """Derive exact owner-controlled zh-CN URLs from one Anthropic manifest row."""
    if (
        source.owner != "Anthropic"
        or source.canonical_url.count(_EN_LOCALE) != 1
        or source.fetch_url.count(_EN_LOCALE) != 1
    ):
        msg = "source has no exact official Chinese locale mapping"
        raise ValueError(msg)
    return (
        source.canonical_url.replace(_EN_LOCALE, _ZH_LOCALE, 1),
        source.fetch_url.replace(_EN_LOCALE, _ZH_LOCALE, 1),
    )


def validate_official_localization(english: str, chinese: str) -> None:
    """Reject a localization unless its current body matches the English structure."""
    english_lf = _lf(english)
    chinese_lf = _lf(chinese)
    if len(_CJK_RE.findall(chinese_lf)) < _MIN_CJK:
        message = "official localization lacks substantial Chinese prose"
        raise ValueError(message)
    english_structure = _structure_signature(english_lf)
    chinese_structure = _structure_signature(chinese_lf)
    if english_structure != chinese_structure:
        details = _structure_difference_details(
            english_structure,
            chinese_structure,
        )
        message = (
            "official localization Markdown structure differs: "
            + "; ".join(details)
        )
        raise ValueError(message)
    if _literal_signature(english_lf) != _literal_signature(chinese_lf):
        message = "official localization protected literals differ"
        raise ValueError(message)
    if _MDX_TAG_RE.findall(english_lf) != _MDX_TAG_RE.findall(chinese_lf):
        message = "official localization MDX structure differs"
        raise ValueError(message)
    if _long_untranslated_prose(chinese_lf):
        message = "official localization contains long untranslated prose"
        raise ValueError(message)


def _lf(markdown: str) -> str:
    return markdown.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n") + "\n"


def _normalize_locale(markdown: str) -> str:
    return markdown.replace(_ZH_LOCALE, _EN_LOCALE)


def _structure_signature(
    markdown: str,
) -> tuple[tuple[tuple[int, str | None], ...], int, int, int, int]:
    fenced_lines = _fenced_line_indexes(markdown)
    headings: list[tuple[int, str | None]] = []
    table_rows = 0
    list_items = 0
    links = 0
    for index, line in enumerate(markdown.splitlines()):
        if index in fenced_lines:
            continue
        markdown_heading = _HEADING_RE.match(line)
        html_heading = _HTML_HEADING_RE.match(line)
        if markdown_heading is not None:
            level = len(markdown_heading.group(1))
            title = markdown_heading.group(2)
            custom = _CUSTOM_HEADING_ANCHOR_RE.search(title)
            rendered = _INLINE_LINK_RE.sub(r"\1", title)
            rendered = _INLINE_HTML_RE.sub("", rendered)
            stable_id = (
                custom.group(1)
                if custom is not None
                else vitepress_slugify(rendered)
            )
            headings.append(
                (level, None if level == 1 else _normalize_heading_id(stable_id))
            )
        elif html_heading is not None:
            level = int(html_heading.group(1))
            headings.append(
                (
                    level,
                    None
                    if level == 1
                    else _normalize_heading_id(html_heading.group(2)),
                )
            )
        table_rows += _TABLE_RE.fullmatch(line) is not None
        list_items += _LIST_RE.match(line) is not None
        links += len(_MARKDOWN_LINK_RE.findall(line))
    return (
        tuple(headings),
        len(tuple(_FENCE_RE.finditer(markdown))),
        table_rows,
        list_items,
        links,
    )


def _structure_difference_details(
    english: tuple[tuple[tuple[int, str | None], ...], int, int, int, int],
    chinese: tuple[tuple[tuple[int, str | None], ...], int, int, int, int],
) -> tuple[str, ...]:
    labels = ("headings", "fences", "table_rows", "list_items", "links")
    details: list[str] = []
    for label, english_value, chinese_value in zip(
        labels,
        english,
        chinese,
        strict=True,
    ):
        if english_value == chinese_value:
            continue
        if label == "headings":
            details.append(
                f"{label} en={len(english_value)} zh-CN={len(chinese_value)}"
            )
        else:
            details.append(f"{label} en={english_value} zh-CN={chinese_value}")
    return tuple(details)


def _literal_signature(
    markdown: str,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    normalized = _normalize_locale(markdown)
    fence_headers = tuple(
        match.group(0).splitlines()[0].strip()
        for match in _FENCE_RE.finditer(normalized)
    )
    without_fences = _FENCE_RE.sub("", normalized)
    link_targets = tuple(_MARKDOWN_LINK_RE.findall(without_fences))
    return fence_headers, link_targets


def _normalize_heading_id(value: str) -> str:
    normalized = re.sub(r"[/\\'\u2019]+", "-", value.casefold())
    return re.sub(r"-{2,}", "-", normalized).strip("-")


def _fenced_line_indexes(markdown: str) -> set[int]:
    indexes: set[int] = set()
    for match in _FENCE_RE.finditer(markdown):
        start = markdown.count("\n", 0, match.start())
        end = start + match.group(0).count("\n")
        indexes.update(range(start, end + 1))
    return indexes


def _long_untranslated_prose(markdown: str) -> tuple[str, ...]:
    prose = _FENCE_RE.sub("", markdown)
    prose = _INLINE_CODE_RE.sub("", prose)
    prose = _LINK_RE.sub("", prose)
    prose = _URL_RE.sub("", prose)
    prose = _HTML_RE.sub("", prose)
    findings: list[str] = []
    for raw_line in prose.splitlines():
        line = raw_line.lstrip("#>-*+0123456789. ").strip()
        letters = [character for character in line if character.isalpha()]
        if len(line) < _LONG_PROSE_MIN or not letters:
            continue
        ascii_letters = sum(character.isascii() for character in letters)
        if ascii_letters / len(letters) >= _UNTRANSLATED_PROSE_RATIO:
            findings.append(line)
    return tuple(findings)

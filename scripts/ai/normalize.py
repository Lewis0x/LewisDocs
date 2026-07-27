# Copyright 2026

"""Content normalization for fetched AI pages."""

from __future__ import annotations

import json
import re
from hashlib import sha256
from typing import TYPE_CHECKING, Final, NoReturn

from scripts.ai.errors import AIAgentError, ErrorCode
from scripts.ai.html_normalize import finalize_markdown, normalize_html_content
from scripts.ai.types import NormalizedPage

if TYPE_CHECKING:
    from scripts.ai.types import FetchedPage, Source

_FETCH_FAILED_MESSAGE: Final = "fetch failed"
_NORMALIZATION_ERROR: Final = "normalization failed"
_MARKDOWN_CONTENT_TYPES: Final = frozenset({"text/markdown", "text/plain", "application/markdown"})
_HTML_CONTENT_TYPES: Final = frozenset({"text/html"})
_MARKDOWN_HTML_RE: Final = re.compile(r"(?is)^\s*(?:<!doctype\s+html\b|<html\b)")
_MARKDOWN_COMMENT_RE: Final = re.compile(
    r"^\s*<!--\s*(?:fetched-at|source-url)\b[^>]*-->\s*$",
    re.IGNORECASE,
)
_H1_RE: Final = re.compile(r"(?m)^#\s+\S")


def normalize_source(*, source: Source, fetched: FetchedPage) -> NormalizedPage:
    """Normalize source payloads into canonical markdown."""
    try:
        if fetched.source_id != source.id:
            _raise_normalize_error(source)
        content_type = _normalize_content_type(fetched.content_type)
        if source.fetch_format == "markdown":
            if content_type not in _MARKDOWN_CONTENT_TYPES:
                _raise_normalize_error(source)
            markdown = _normalize_markdown_content(fetched.text)
        else:
            if content_type not in _HTML_CONTENT_TYPES:
                _raise_normalize_error(source)
            markdown = normalize_html_content(fetched.text)
            if _H1_RE.search(markdown) is None:
                markdown = f"# {source.title}\n\n{markdown}"
        return NormalizedPage(
            source=source,
            markdown=markdown,
            content_sha256=sha256(markdown.encode("utf-8")).hexdigest(),
        )
    except AIAgentError:
        raise
    except (TypeError, ValueError) as exc:
        _raise_normalize_error(source, cause=exc)


def _raise_normalize_error(source: Source, cause: Exception | None = None) -> NoReturn:
    raise AIAgentError(
        code=ErrorCode.FETCH_FAILED,
        message=_FETCH_FAILED_MESSAGE,
        source_id=source.id,
    ) from cause


def _normalize_content_type(raw_mime: str) -> str:
    media_type = raw_mime.split(";", 1)[0].strip().lower()
    if not media_type:
        raise ValueError(_NORMALIZATION_ERROR)
    return media_type


def _normalize_markdown_content(raw: str) -> str:
    text = raw.replace("\r\n", "\n").replace("\r", "\n").removeprefix("\ufeff")
    if _MARKDOWN_HTML_RE.search(text) is not None or _looks_like_json_shell(text):
        raise ValueError(_NORMALIZATION_ERROR)
    lines = text.split("\n")
    if lines and lines[0].strip() == "---":
        for index in range(1, len(lines)):
            if lines[index].strip() == "---":
                lines = lines[index + 1 :]
                break
        else:
            raise ValueError(_NORMALIZATION_ERROR)
    return finalize_markdown(
        "\n".join(line for line in lines if _MARKDOWN_COMMENT_RE.fullmatch(line) is None)
    )


def _looks_like_json_shell(text: str) -> bool:
    stripped = text.strip()
    if not stripped.startswith(("{", "[")):
        return False
    try:
        json.loads(stripped)
    except json.JSONDecodeError:
        return False
    return True

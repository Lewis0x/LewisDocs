# Copyright 2026

"""Fetch utility for downloading source pages under strict validation."""

from __future__ import annotations

from typing import Final, NoReturn
from urllib.parse import urlparse

import httpx2
from pydantic import ValidationError

from scripts.ai.errors import AIAgentError, ErrorCode
from scripts.ai.types import FetchedPage, Source

_FETCH_FAILED_MESSAGE: Final = "fetch failed"
_HTTP_SUCCESS_STATUS_MIN: Final = 200
_HTTP_SUCCESS_STATUS_MAX: Final = 300
_MARKDOWN_CONTENT_TYPES: Final = frozenset(
    {
        "text/markdown",
        "text/plain",
        "application/markdown",
    },
)
_HTML_CONTENT_TYPES: Final = frozenset({"text/html"})


def _fetch_error(source: Source, cause: Exception | None = None) -> NoReturn:
    raise AIAgentError(
        code=ErrorCode.FETCH_FAILED,
        message=_FETCH_FAILED_MESSAGE,
        source_id=source.id,
    ) from cause


def _parse_hostname_and_scheme(url: str) -> tuple[str, str]:
    parsed = urlparse(url)
    if parsed.hostname is None or parsed.scheme == "":
        message = "response url missing host or scheme"
        raise ValueError(message)
    return parsed.hostname, parsed.scheme


def _normalize_mime_type(raw_mime: str | None) -> str:
    if raw_mime is None:
        message = "response content type missing"
        raise ValueError(message)
    media_type = raw_mime.split(";", 1)[0].strip().lower()
    if not media_type:
        message = "response content type missing"
        raise ValueError(message)
    return media_type


def _allowed_content_types(source: Source) -> frozenset[str]:
    if source.fetch_format == "markdown":
        return _MARKDOWN_CONTENT_TYPES
    return _HTML_CONTENT_TYPES


def fetch_source(client: httpx2.Client, source: Source) -> FetchedPage:  # noqa: C901
    """Fetch and validate a single source with strict boundary guarantees."""
    try:
        response = client.get(source.fetch_url)
    except httpx2.HTTPError as exc:
        _fetch_error(source=source, cause=exc)

    final_url = str(response.url)
    try:
        final_hostname, final_scheme = _parse_hostname_and_scheme(final_url)
        source_hostname, source_scheme = _parse_hostname_and_scheme(source.fetch_url)
    except ValueError as exc:
        _fetch_error(source, cause=exc)

    if final_scheme != "https" or source_scheme != "https":
        _fetch_error(source)

    allowed_redirect = (
        source.owner == "OpenAI"
        and source_hostname == "developers.openai.com"
        and final_hostname == "learn.chatgpt.com"
    )
    if final_hostname != source_hostname and not allowed_redirect:
        _fetch_error(source)

    if (
        response.status_code < _HTTP_SUCCESS_STATUS_MIN
        or response.status_code >= _HTTP_SUCCESS_STATUS_MAX
    ):
        _fetch_error(source)

    try:
        raw_content_type = response.headers["content-type"]
    except KeyError:
        raw_content_type = None
    try:
        content_type = _normalize_mime_type(raw_content_type)
    except ValueError as exc:
        _fetch_error(source, cause=exc)

    if content_type not in _allowed_content_types(source):
        _fetch_error(source)

    try:
        text = response.content.decode("utf-8")
    except UnicodeDecodeError as exc:
        _fetch_error(source, cause=exc)

    if not text or not text.strip():
        message = "response text is empty or whitespace-only"
        _fetch_error(source, cause=ValueError(message))

    try:
        return FetchedPage(
            source_id=source.id,
            final_url=final_url,
            content_type=content_type,
            text=text,
        )
    except ValidationError as exc:
        _fetch_error(source, cause=exc)

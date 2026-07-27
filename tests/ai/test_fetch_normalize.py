# Copyright 2026
# ruff: noqa: INP001
"""Tests for AI fetch + normalize behavior."""

from __future__ import annotations

import socket
from hashlib import sha256
from pathlib import Path
from typing import Final
from urllib.parse import urlparse

import httpx2
import pytest

from scripts.ai.errors import AIAgentError, ErrorCode
from scripts.ai.fetch import fetch_source
from scripts.ai.http_client import create_http_client
from scripts.ai.manifest import load_sources
from scripts.ai.normalize import normalize_source
from scripts.ai.types import FetchedPage, Source, SourceId

ROOT = Path(__file__).resolve().parents[2]
SOURCES = load_sources(ROOT / "source-ai" / "sources.yaml").root
EXPECTED_ERROR_MESSAGE: Final = "fetch failed"
EXPECTED_FINAL_NEWLINE: Final = "\n"
_FIXTURE_DIR: Final = ROOT / "tests" / "ai" / "fixtures"
_EXPECTED_RETRIES: Final = 3
_EXPECTED_TIMEOUT_CONNECT: Final = 5.0
_EXPECTED_KEEPALIVE_EXPIRY: Final = 30.0
_EXPECTED_TIMEOUT_POOL: Final = 10.0
_EXPECTED_TIMEOUT_READ: Final = 30.0
_EXPECTED_TIMEOUT_WRITE: Final = 10.0
_EXPECTED_MAX_CONNECTIONS: Final = 200
_EXPECTED_MAX_KEEPALIVE: Final = 40


def _source_by_fetch_format(fetch_format: str) -> Source:
    for source in SOURCES:
        if source.fetch_format == fetch_format:
            return source
    message = "expected source not found in manifest"
    raise RuntimeError(message)


def _expect_fetch_failed(transport: httpx2.BaseTransport, source: Source) -> None:
    with pytest.raises(AIAgentError) as exc_info, create_http_client(transport=transport) as client:
        _ = fetch_source(client, source)
    assert exc_info.value.code == ErrorCode.FETCH_FAILED  # noqa: S101
    assert exc_info.value.source_id == source.id  # noqa: S101
    assert exc_info.value.args[0] == EXPECTED_ERROR_MESSAGE  # noqa: S101


def _hostname(url: str) -> str:
    parsed = urlparse(url)
    if parsed.hostname is None:
        message = "manifest source must have hostname"
        raise ValueError(message)
    return parsed.hostname


def _fetch_text(source: Source, content_type: str, body: str) -> str:
    transport = httpx2.MockTransport(
        lambda request: httpx2.Response(
            status_code=200,
            request=request,
            headers={"content-type": content_type},
            content=body.encode("utf-8"),
        )
    )
    with create_http_client(transport=transport) as client:
        page = fetch_source(client, source)
    return page.text


def _fetched_page(
    source: Source,
    text: str,
    *,
    content_type: str = "text/markdown",
) -> FetchedPage:
    return FetchedPage(
        source_id=source.id,
        final_url=source.fetch_url,
        content_type=content_type,
        text=text,
    )


def _expect_normalize_failed(source: Source, fetched: FetchedPage) -> None:
    with pytest.raises(AIAgentError) as exc_info:
        _ = normalize_source(source=source, fetched=fetched)
    assert exc_info.value.code == ErrorCode.FETCH_FAILED  # noqa: S101
    assert exc_info.value.source_id == source.id  # noqa: S101
    assert str(exc_info.value) == EXPECTED_ERROR_MESSAGE  # noqa: S101


def test_http_client_default_factory_config_is_exact() -> None:
    """Verify default factory creates the required transport, timeouts, and hooks."""
    with create_http_client() as client:
        transport = client._transport  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
        assert isinstance(transport, httpx2.HTTPTransport)  # noqa: S101
        assert transport._pool._max_connections == _EXPECTED_MAX_CONNECTIONS  # noqa: S101,SLF001  # pyright: ignore[reportPrivateUsage]
        assert transport._pool._max_keepalive_connections == _EXPECTED_MAX_KEEPALIVE  # noqa: S101,SLF001  # pyright: ignore[reportPrivateUsage]
        assert transport._pool._keepalive_expiry == _EXPECTED_KEEPALIVE_EXPIRY  # noqa: S101,SLF001  # pyright: ignore[reportPrivateUsage]
        assert transport._pool._retries == _EXPECTED_RETRIES  # noqa: S101,SLF001  # pyright: ignore[reportPrivateUsage]
        assert transport._pool._socket_options == [  # noqa: S101,SLF001  # pyright: ignore[reportPrivateUsage]
            (socket.IPPROTO_TCP, socket.TCP_NODELAY, 1),
        ]
        assert transport._pool._http2 is True  # noqa: S101,SLF001  # pyright: ignore[reportPrivateUsage]
        assert client._timeout.connect == _EXPECTED_TIMEOUT_CONNECT  # noqa: S101,SLF001  # pyright: ignore[reportPrivateUsage]
        assert client._timeout.read == _EXPECTED_TIMEOUT_READ  # noqa: S101,SLF001  # pyright: ignore[reportPrivateUsage]
        assert client._timeout.write == _EXPECTED_TIMEOUT_WRITE  # noqa: S101,SLF001  # pyright: ignore[reportPrivateUsage]
        assert client._timeout.pool == _EXPECTED_TIMEOUT_POOL  # noqa: S101,SLF001  # pyright: ignore[reportPrivateUsage]
        assert client.follow_redirects is True  # noqa: S101
        assert len(client._event_hooks["response"]) == 1  # noqa: S101,SLF001  # pyright: ignore[reportPrivateUsage]


def test_http_client_retains_injected_transport() -> None:
    """Verify injected transport is retained exactly by the created client."""
    requests: list[str] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        requests.append(str(request.url))
        return httpx2.Response(
            status_code=200,
            request=request,
            headers={"content-type": "text/markdown"},
            content=b"ok",
        )

    transport = httpx2.MockTransport(handler)
    with create_http_client(transport=transport) as client:
        assert client._transport is transport  # noqa: S101,SLF001  # pyright: ignore[reportPrivateUsage]
        page = fetch_source(client, _source_by_fetch_format("markdown"))
        assert page.text == "ok"  # noqa: S101
    assert requests == [str(_source_by_fetch_format("markdown").fetch_url)]  # noqa: S101


def test_fetch_source_uses_exact_get_wire_path() -> None:
    """Verify the fetch always issues a GET for the source fetch_url."""
    source = _source_by_fetch_format("markdown")
    observed: list[tuple[str, str]] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        observed.append((request.method, str(request.url)))
        return httpx2.Response(
            status_code=200,
            request=request,
            headers={"content-type": "text/markdown"},
            content=b"markdown text",
        )

    with create_http_client(httpx2.MockTransport(handler)) as client:
        page = fetch_source(client, source)
    assert observed == [("GET", source.fetch_url)]  # noqa: S101
    assert page.final_url == source.fetch_url  # noqa: S101
    assert page.content_type == "text/markdown"  # noqa: S101
    assert page.text == "markdown text"  # noqa: S101


def test_fetch_source_allows_safe_same_host_redirect() -> None:
    """Follow-safe redirect to same host updates final URL and remains valid."""
    source = _source_by_fetch_format("markdown")

    def handler(request: httpx2.Request) -> httpx2.Response:
        if str(request.url) == source.fetch_url:
            return httpx2.Response(
                status_code=307,
                request=request,
                headers={"Location": source.fetch_url + "?redirected=true"},
            )
        return httpx2.Response(
            status_code=200,
            request=request,
            headers={"content-type": "text/markdown;charset=UTF-8"},
            content=b"redirected\nbody",
        )

    with create_http_client(httpx2.MockTransport(handler)) as client:
        page = fetch_source(client, source)
    assert page.final_url == source.fetch_url + "?redirected=true"  # noqa: S101
    assert page.content_type == "text/markdown"  # noqa: S101
    assert page.text == "redirected\nbody"  # noqa: S101


@pytest.mark.parametrize(
    ("source", "redirect_host"),
    [
        (_source_by_fetch_format("markdown"), _hostname(_source_by_fetch_format("html").fetch_url)),
        (_source_by_fetch_format("html"), _hostname(_source_by_fetch_format("markdown").fetch_url)),
    ],
)
def test_fetch_source_rejects_cross_product_redirects(
    source: Source,
    redirect_host: str,
) -> None:
    """Reject redirects that change host across product domains."""
    redirect_url = f"https://{redirect_host}/redirect-target"

    def handler(request: httpx2.Request) -> httpx2.Response:
        if str(request.url) == source.fetch_url:
            return httpx2.Response(
                status_code=307,
                request=request,
                headers={"Location": redirect_url},
            )
        return httpx2.Response(
            status_code=200,
            request=request,
            headers={
                "content-type": "text/html" if source.fetch_format == "html" else "text/plain"
            },
            content=b"final body",
        )

    _expect_fetch_failed(httpx2.MockTransport(handler), source)


def test_fetch_source_rejects_non_2xx() -> None:
    """Transport should surface any non-2xx response as fetch failure."""
    source = _source_by_fetch_format("markdown")

    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            status_code=500,
            request=request,
            headers={"content-type": "text/markdown"},
            content=b"server error",
        )

    with (
        pytest.raises(AIAgentError) as exc_info,
        create_http_client(httpx2.MockTransport(handler)) as client,
    ):
        _ = fetch_source(client, source)
    assert exc_info.value.code == ErrorCode.FETCH_FAILED  # noqa: S101
    assert exc_info.value.source_id == source.id  # noqa: S101
    assert exc_info.value.__cause__ is not None  # noqa: S101


@pytest.mark.parametrize(
    "content_type",
    [
        None,
        "application/json",
    ],
)
def test_fetch_source_rejects_invalid_content_type(content_type: str | None) -> None:
    """Reject missing or unsupported MIME types, including non-whitelisted markdown types."""
    source = _source_by_fetch_format("markdown")

    def handler(request: httpx2.Request) -> httpx2.Response:
        if content_type is not None:
            return httpx2.Response(
                status_code=200,
                request=request,
                headers={"content-type": content_type},
                content=b"ok",
            )
        return httpx2.Response(
            status_code=200,
            request=request,
            content=b"ok",
        )

    with (
        pytest.raises(AIAgentError) as exc_info,
        create_http_client(httpx2.MockTransport(handler)) as client,
    ):
        _ = fetch_source(client, source)
    assert exc_info.value.code == ErrorCode.FETCH_FAILED  # noqa: S101


def test_fetch_source_accepts_case_insensitive_content_type_with_parameters() -> None:
    """Accept case-insensitive markdown MIME with charset parameters."""
    source = _source_by_fetch_format("markdown")

    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            status_code=200,
            request=request,
            headers={"content-type": "Text/Markdown; Charset=UTF-8"},
            content=b"markdown",
        )

    with create_http_client(httpx2.MockTransport(handler)) as client:
        page = fetch_source(client, source)
    assert page.content_type == "text/markdown"  # noqa: S101


def test_fetch_source_rejects_invalid_utf8() -> None:
    """Reject undecodable UTF-8 payloads from the response body."""
    source = _source_by_fetch_format("markdown")

    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            status_code=200,
            request=request,
            headers={"content-type": "text/plain"},
            content=b"\xff\xfe",
        )

    with (
        pytest.raises(AIAgentError) as exc_info,
        create_http_client(httpx2.MockTransport(handler)) as client,
    ):
        _ = fetch_source(client, source)
    assert exc_info.value.code == ErrorCode.FETCH_FAILED  # noqa: S101
    assert exc_info.value.__cause__ is not None  # noqa: S101


def test_fetch_source_preserves_raw_crlf_and_whitespace() -> None:
    """Preserve raw CRLF and trailing spaces in response text."""
    source = _source_by_fetch_format("markdown")
    body = "line1\r\n  \tline2\r\n\r\n  "

    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            status_code=200,
            request=request,
            headers={"content-type": "text/markdown"},
            content=body.encode("utf-8"),
        )

    with create_http_client(httpx2.MockTransport(handler)) as client:
        page = fetch_source(client, source)
    assert page.text == body  # noqa: S101


def test_fetch_source_safe_error_message_and_no_secret_leak() -> None:
    """Return a fixed safe error message without exposing body/header secrets."""
    source = _source_by_fetch_format("markdown")

    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            status_code=401,
            request=request,
            headers={"x-secret": "SECRET_API_KEY=shh"},
            content=b"SECRET_PAYLOAD=do-not-leak",
        )

    with (
        pytest.raises(AIAgentError) as exc_info,
        create_http_client(httpx2.MockTransport(handler)) as client,
    ):
        _ = fetch_source(client, source)

    assert str(exc_info.value) == EXPECTED_ERROR_MESSAGE  # noqa: S101
    message = str(exc_info.value)
    assert "SECRET" not in message  # noqa: S101
    assert "x-secret" not in message.lower()  # noqa: S101


def test_normalize_markdown_crlf_bom_frontmatter_and_noise() -> None:
    """Normalize markdown by removing UTF-8 BOM, frontmatter, and transport noise comments."""
    source = _source_by_fetch_format("markdown")
    raw = (
        "\ufeff---\r\n"
        "title: codex\r\n"
        "layout: docs\r\n"
        "---\r\n"
        "\r\n"
        "# Codex Task\r\n"
        "Paragraph with hard break  \r\n"
        "next line\r\n"
        "\r\n"
        "<!-- fetched-at: 2026-01-01 -->\r\n"
        "Trailing paragraph.\r\n"
    )

    expected = "# Codex Task\n\nParagraph with hard break  \nnext line\n\nTrailing paragraph.\n"

    normalized = normalize_source(source=source, fetched=_fetched_page(source, raw))
    assert normalized.markdown == expected  # noqa: S101
    assert normalized.content_sha256 == sha256(expected.encode("utf-8")).hexdigest()  # noqa: S101


def test_normalize_markdown_rejects_blank_unreadable_or_shell_like_content() -> None:
    """Reject blank, JSON-like shells, and HTML-like shells from markdown fetches."""
    source = _source_by_fetch_format("markdown")
    _expect_normalize_failed(
        source,
        FetchedPage.model_construct(
            source_id=source.id,
            final_url=source.fetch_url,
            content_type="text/markdown",
            text="   \r\n  ",
        ),
    )
    _expect_normalize_failed(source, _fetched_page(source, '{\n  "title": "shell"\n}'))
    _expect_normalize_failed(
        source,
        _fetched_page(
            source,
            "<!doctype html><html><head><title>x</title></head><body><p>nope</p></body></html>",
        ),
    )


def test_normalize_markdown_preserves_complex_structure_exactly() -> None:
    """Preserve markdown structure while normalizing only line endings and final newline."""
    source = _source_by_fetch_format("markdown")
    raw = (
        "# Overview\r\n"
        "\r\n"
        "1. first item\r\n"
        "2. second item\r\n"
        "\r\n"
        "- bullet one\r\n"
        "- bullet two\r\n"
        "\r\n"
        "| key | value |\r\n"
        "| --- | --- |\r\n"
        "| foo | bar |\r\n"
        "\r\n"
        "```python\r\n"
        'print("a")\r\n'
        "```\r\n"
        "\r\n"
        "Use `inline code` plus [link](https://example.com) and ![img](https://example.com/image.png).\r\n"
        "\r\n"
        "> Quote this.\r\n"
    )
    expected = (
        "# Overview\n"
        "\n"
        "1. first item\n"
        "2. second item\n"
        "\n"
        "- bullet one\n"
        "- bullet two\n"
        "\n"
        "| key | value |\n"
        "| --- | --- |\n"
        "| foo | bar |\n"
        "\n"
        "```python\n"
        'print("a")\n'
        "```\n"
        "\n"
        "Use `inline code` plus [link](https://example.com) and ![img](https://example.com/image.png).\n"
        "\n"
        "> Quote this.\n"
    )
    normalized = normalize_source(source=source, fetched=_fetched_page(source, raw))
    assert normalized.markdown == expected  # noqa: S101


def test_normalize_markdown_rejects_unterminated_frontmatter() -> None:
    """Fail when markdown frontmatter is opened but not terminated."""
    source = _source_by_fetch_format("markdown")
    raw = "---\nkey: value\n# no end marker"
    _expect_normalize_failed(source, _fetched_page(source, raw))


def test_normalize_markdown_idempotence() -> None:
    """Run normalized markdown through normalize_source twice and preserve identical output."""
    source = _source_by_fetch_format("markdown")
    raw = _fetch_text(
        source=source,
        content_type="text/markdown",
        body="# Head\r\n\r\nBody text.\r\n",
    )
    normalized = normalize_source(source=source, fetched=_fetched_page(source, raw))
    rewrapped = _fetched_page(
        source=source,
        text=normalized.markdown,
        content_type="text/markdown",
    )
    normalized_again = normalize_source(source=source, fetched=rewrapped)
    assert normalized_again.markdown == normalized.markdown  # noqa: S101
    assert normalized_again.content_sha256 == normalized.content_sha256  # noqa: S101


def test_normalize_source_checks_expected_content_type_match() -> None:
    """Reject markdown/HTML content-type mismatches before parsing."""
    markdown_source = _source_by_fetch_format("markdown")
    html_source = _source_by_fetch_format("html")
    _expect_normalize_failed(
        markdown_source,
        _fetched_page(markdown_source, "ok", content_type="text/html"),
    )
    _expect_normalize_failed(
        html_source,
        _fetched_page(html_source, "<p>ok</p>", content_type="text/plain"),
    )


def test_normalize_source_rejects_source_id_mismatch() -> None:
    """Reject fetched pages not tied to the requested source."""
    source = _source_by_fetch_format("markdown")
    mismatched = SourceId("codex/prompting")
    fetched = _fetched_page(
        source=source,
        text="text",
        content_type="text/markdown",
    ).model_copy(update={"source_id": mismatched})
    with pytest.raises(AIAgentError) as exc_info:
        _ = normalize_source(source=source, fetched=fetched)
    assert exc_info.value.code == ErrorCode.FETCH_FAILED  # noqa: S101
    assert str(exc_info.value) == EXPECTED_ERROR_MESSAGE  # noqa: S101


def test_normalize_html_exact_fixture_round_trip() -> None:
    """Normalize the minimal HTML fixture and compare exact markdown + SHA."""
    source = _source_by_fetch_format("html")
    raw_html = (_FIXTURE_DIR / "codex-cli-minimal.html").read_text(encoding="utf-8")
    expected_markdown = (_FIXTURE_DIR / "codex-cli-normalized.md").read_text(encoding="utf-8")
    expected_sha = (
        (_FIXTURE_DIR / "codex-cli-normalized.sha256").read_text(encoding="utf-8").strip()
    )

    normalized = normalize_source(
        source=source,
        fetched=_fetched_page(source, raw_html, content_type="text/html"),
    )
    assert normalized.markdown == expected_markdown  # noqa: S101
    assert normalized.content_sha256 == expected_sha  # noqa: S101
    assert normalized.markdown.endswith(EXPECTED_FINAL_NEWLINE)  # noqa: S101


def test_normalize_html_prepends_manifest_title_when_article_has_no_h1() -> None:
    """Keep server-rendered component pages readable when their H1 is outside the article."""
    source = _source_by_fetch_format("html")
    raw = '<html><body><article id="mainContent"><p>Full guide body.</p></article></body></html>'

    normalized = normalize_source(
        source=source,
        fetched=_fetched_page(source, raw, content_type="text/html"),
    )

    assert normalized.markdown == f"# {source.title}\n\nFull guide body.\n"  # noqa: S101


def test_normalize_html_sibling_noise_absent() -> None:
    """Ensure sibling nav/footer/script/style are never included in article extraction."""
    source = _source_by_fetch_format("html")
    raw_html = (_FIXTURE_DIR / "codex-cli-minimal.html").read_text(encoding="utf-8")
    fetched = _fetched_page(source, raw_html, content_type="text/html")
    normalized = normalize_source(source=source, fetched=fetched)
    assert "Navigation" not in normalized.markdown  # noqa: S101
    assert "Footer noise" not in normalized.markdown  # noqa: S101
    assert "ignore this script" not in normalized.markdown  # noqa: S101
    assert "console.log" not in normalized.markdown  # noqa: S101
    assert "stylesheet" not in normalized.markdown  # noqa: S101


def test_normalize_html_rejects_no_main_content_articles() -> None:
    """No `article#mainContent` should fail fast with fetch-failed."""
    source = _source_by_fetch_format("html")
    raw = '<html><body><article id="other"></article></body></html>'
    _expect_normalize_failed(source, _fetched_page(source, raw, content_type="text/html"))


def test_normalize_html_rejects_duplicate_main_content_articles() -> None:
    """More than one `article#mainContent` should fail fast with fetch-failed."""
    source = _source_by_fetch_format("html")
    raw = (
        "<html><body>"
        '<article id="mainContent"><p>one</p></article>'
        '<article id="mainContent"><p>two</p></article>'
        "</body></html>"
    )
    _expect_normalize_failed(source, _fetched_page(source, raw, content_type="text/html"))


def test_normalize_html_rejects_empty_main_content_article() -> None:
    """Empty `article#mainContent` should fail as unreadable content."""
    source = _source_by_fetch_format("html")
    raw = "<html><body><article id='mainContent'>  \r\n\t</article></body></html>"
    _expect_normalize_failed(source, _fetched_page(source, raw, content_type="text/html"))

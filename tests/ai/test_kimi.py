# Copyright 2026
# ruff: noqa: INP001
"""Behavior tests for the fixed Kimi translation adapter."""

from __future__ import annotations

import hmac
import json
import secrets
import subprocess
from dataclasses import dataclass
from pathlib import Path
from shutil import which
from typing import TYPE_CHECKING, Final, cast

import httpx2
import pytest
from pydantic import SecretStr, ValidationError
from typing_extensions import override

from scripts.ai.errors import AIAgentError, ErrorCode
from scripts.ai.http_client import create_http_client
from scripts.ai.kimi import (
    KimiMessage,
    KimiRequest,
    KimiResponse,
    TranslationInput,
    translate_markdown,
)
from scripts.ai.protect import protect_markdown
from scripts.ai.types import SourceId

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

ROOT = Path(__file__).resolve().parents[2]
SOURCE_ID: Final = SourceId("claude-code/quickstart")
MARKDOWN: Final = (
    "# Synthetic handbook\n\nRun `npm run ai:sync` against https://example.test/docs\n"
)
FAILURE_MESSAGE: Final = "translation failed"
ENDPOINT: Final = "https://api.kimi.com/coding/v1/chat/completions"
EXPECTED_TRANSLATION_READ_TIMEOUT: Final = 900.0
EXPECTED_SOURCE_CHUNK_CHARS: Final = 4_000
EXPECTED_MAX_PROVIDER_CHARS: Final = 6_000
MIN_SEMANTIC_CHUNK_CHARS: Final = EXPECTED_SOURCE_CHUNK_CHARS // 2
MIN_TRANSLATION_CHUNKS: Final = 4
EXPECTED_SECTION_CHUNKS: Final = 2
RETRY_FAILURE_THRESHOLD: Final = 2_000
PROVIDER_PLACEHOLDER: Final = "@@LEWISDOCS_LITERAL@@"
MIN_STRUCTURE_PLACEHOLDERS: Final = 8

BAD_RESPONSES: Final[tuple[bytes, ...]] = (
    b"not json",
    b"{}",
    b'{"choices":[]}',
    b'{"choices":[{"message":{}}]}',
    b'{"choices":[{"message":{"content":"   "}}]}',
)


@dataclass(frozen=True, slots=True)
class ObservedRequest:
    """Typed wire observation that never stores credentials."""

    method: str
    url: str
    payload: KimiRequest
    authorization_ok: bool
    raw_body: str


def _translation_input(api_key: SecretStr) -> TranslationInput:
    return TranslationInput(
        source_id=SOURCE_ID,
        markdown=MARKDOWN,
        api_key=api_key,
    )


def _provider_markdown(markdown: str) -> str:
    protected = protect_markdown(markdown)
    text = protected.text
    for span in protected.spans:
        text = text.replace(span.placeholder, PROVIDER_PLACEHOLDER, 1)
    if text.startswith("# "):
        text = PROVIDER_PLACEHOLDER + text[2:]
    return text


def _call(transport: httpx2.BaseTransport, api_key: SecretStr) -> str:
    with httpx2.Client(transport=transport) as client:
        return translate_markdown(client, _translation_input(api_key))


def _assert_translation_failed(
    operation: Callable[[], str],
    expected_reason: str | None = None,
) -> None:
    with pytest.raises(AIAgentError) as exc_info:
        _ = operation()
    assert exc_info.value.code == ErrorCode.TRANSLATION_FAILED  # noqa: S101
    assert exc_info.value.source_id == SOURCE_ID  # noqa: S101
    assert str(exc_info.value) == FAILURE_MESSAGE  # noqa: S101
    assert getattr(exc_info.value, "reason", None) == expected_reason  # noqa: S101


def _authorization(request: httpx2.Request) -> str:
    for name, value in request.headers.raw:
        if name.lower() == b"authorization":
            return value.decode("latin-1")
    return ""


def _json_response(request: httpx2.Request, content: str) -> httpx2.Response:
    body = {
        "id": "synthetic-completion",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content,
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 1},
    }
    return httpx2.Response(
        status_code=200,
        request=request,
        headers={"content-type": "application/json"},
        content=json.dumps(body, ensure_ascii=False).encode("utf-8"),
    )


def test_boundary_models_are_frozen_and_validate_required_shapes() -> None:
    """Accept the fixed request and standard response while rejecting bad shapes."""
    request = KimiRequest(
        model="k3",
        reasoning_effort="low",
        messages=(
            KimiMessage(role="system", content="system"),
            KimiMessage(role="user", content="user"),
        ),
    )
    assert request.model_dump(mode="json") == {  # noqa: S101
        "model": "k3",
        "reasoning_effort": "low",
        "messages": [
            {"role": "system", "content": "system"},
            {"role": "user", "content": "user"},
        ],
    }
    with pytest.raises(ValidationError):
        _ = KimiRequest.model_validate(
            {
                **request.model_dump(mode="json"),
                "temperature": 0,
            }
        )

    response = KimiResponse.model_validate_json(
        _json_response(
            httpx2.Request("POST", ENDPOINT),
            "translated",
        ).content
    )
    assert response.choices[0].message.content == "translated"  # noqa: S101
    for invalid in BAD_RESPONSES[1:]:
        with pytest.raises(ValidationError):
            _ = KimiResponse.model_validate_json(invalid)


def test_translate_posts_exact_wire_and_restores_protected_literals(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Send only the fixed payload and return validated translated Markdown."""
    sentinel = secrets.token_urlsafe(48)
    api_key = SecretStr(sentinel)
    translated = _provider_markdown(MARKDOWN).replace("Synthetic handbook", "合成手册")
    observations: list[ObservedRequest] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        timeout = cast("dict[str, float]", request.extensions["timeout"])
        assert timeout["read"] == EXPECTED_TRANSLATION_READ_TIMEOUT  # noqa: S101
        raw_body = request.content.decode("utf-8")
        observations.append(
            ObservedRequest(
                method=request.method,
                url=str(request.url),
                payload=KimiRequest.model_validate_json(raw_body),
                authorization_ok=hmac.compare_digest(
                    _authorization(request),
                    f"Bearer {sentinel}",
                ),
                raw_body=raw_body,
            )
        )
        if not observations[-1].authorization_ok:
            return httpx2.Response(
                status_code=401,
                request=request,
                content=b"denied",
            )
        return _json_response(request, translated)

    result = _call(httpx2.MockTransport(handler), api_key)

    assert len(observations) == 1  # noqa: S101
    observed = observations[0]
    assert observed.method == "POST"  # noqa: S101
    assert observed.url == ENDPOINT  # noqa: S101
    assert observed.authorization_ok  # noqa: S101
    assert observed.payload.model == "k3"  # noqa: S101
    assert observed.payload.reasoning_effort == "low"  # noqa: S101
    assert observed.payload.messages[0].role == "system"  # noqa: S101
    assert "逐行翻译" in observed.payload.messages[0].content  # noqa: S101
    assert "不得增删或移动任何 @@LEWISDOCS_LITERAL@@ 令牌" in observed.payload.messages[0].content  # noqa: S101
    assert observed.payload.messages[1].role == "user"  # noqa: S101
    assert observed.payload.messages[1].content == _provider_markdown(MARKDOWN)  # noqa: S101
    assert all(  # noqa: S101
        field not in observed.raw_body
        for field in (
            "temperature",
            "top_p",
            '"n"',
            "presence_penalty",
            "frequency_penalty",
        )
    )
    assert "# 合成手册" in result  # noqa: S101
    assert "`npm run ai:sync`" in result  # noqa: S101
    assert "https://example.test/docs" in result  # noqa: S101
    captured = capsys.readouterr()
    assert sentinel not in captured.out + captured.err  # noqa: S101


def test_translate_chunks_large_markdown_and_reassembles_original_boundaries() -> None:
    """Keep large documents ordered by validating bounded provider calls."""
    paragraph = "Translate this sentence exactly. " * 220
    markdown = "# Chunked handbook\n\n" + "\n\n".join(
        f"{paragraph}`literal_{index}`." for index in range(3)
    )
    observed_chunks: list[str] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        payload = KimiRequest.model_validate_json(request.content)
        chunk = payload.messages[1].content
        observed_chunks.append(chunk)
        return _json_response(request, chunk)

    api_key = SecretStr(secrets.token_urlsafe(48))
    with httpx2.Client(transport=httpx2.MockTransport(handler)) as client:
        result = translate_markdown(
            client,
            TranslationInput(source_id=SOURCE_ID, markdown=markdown, api_key=api_key),
        )

    assert result == markdown  # noqa: S101
    assert len(observed_chunks) >= MIN_TRANSLATION_CHUNKS  # noqa: S101
    assert all(len(chunk) <= EXPECTED_MAX_PROVIDER_CHARS for chunk in observed_chunks)  # noqa: S101


def test_translate_prefers_markdown_section_boundaries() -> None:
    """Keep a heading with its section instead of filling the preceding chunk."""
    introduction = "Introductory context. " * 20
    section_one = "First section detail. " * 120
    section_two = "Second section detail. " * 120
    markdown = (
        f"# Sectioned handbook\n\n{introduction}\n\n"
        f"## Section one\n\n{section_one}\n\n"
        f"## Section two\n\n{section_two}"
    )
    observed_chunks: list[str] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        payload = KimiRequest.model_validate_json(request.content)
        chunk = payload.messages[1].content
        observed_chunks.append(chunk)
        return _json_response(request, chunk)

    api_key = SecretStr(secrets.token_urlsafe(48))
    with httpx2.Client(transport=httpx2.MockTransport(handler)) as client:
        result = translate_markdown(
            client,
            TranslationInput(source_id=SOURCE_ID, markdown=markdown, api_key=api_key),
        )

    assert result == markdown  # noqa: S101
    assert len(observed_chunks) == EXPECTED_SECTION_CHUNKS  # noqa: S101
    assert "Section two" not in observed_chunks[0]  # noqa: S101
    assert observed_chunks[1].startswith(  # noqa: S101
        f"{PROVIDER_PLACEHOLDER}Section two"
    )
    assert all(len(chunk) <= EXPECTED_MAX_PROVIDER_CHARS for chunk in observed_chunks)  # noqa: S101


def test_translate_avoids_tiny_chunks_at_early_section_boundaries() -> None:
    """Pack a short section with following prose before falling back within that section."""
    markdown = "".join(
        (
            "# Handbook\n\n",
            "## Short section\n\nBrief context.\n\n",
            "## Long section\n\n",
            "Long section detail. " * 320,
        )
    )
    observed_chunks: list[str] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        payload = KimiRequest.model_validate_json(request.content)
        chunk = payload.messages[1].content
        observed_chunks.append(chunk)
        return _json_response(request, chunk)

    api_key = SecretStr(secrets.token_urlsafe(48))
    with httpx2.Client(transport=httpx2.MockTransport(handler)) as client:
        result = translate_markdown(
            client,
            TranslationInput(source_id=SOURCE_ID, markdown=markdown, api_key=api_key),
        )

    assert result == markdown  # noqa: S101
    assert len(observed_chunks[0]) >= MIN_SEMANTIC_CHUNK_CHARS  # noqa: S101
    assert "Long section" in observed_chunks[0]  # noqa: S101
    assert all(len(chunk) <= EXPECTED_MAX_PROVIDER_CHARS for chunk in observed_chunks)  # noqa: S101


def test_translate_protects_markdown_link_structure_around_translated_labels() -> None:
    """Keep a protected link target in the target slot while translating its label."""
    markdown = "Read [global settings](/docs/en/settings#global-config-settings) for details."
    observed_chunks: list[str] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        payload = KimiRequest.model_validate_json(request.content)
        chunk = payload.messages[1].content
        observed_chunks.append(chunk)
        return _json_response(request, chunk)

    api_key = SecretStr(secrets.token_urlsafe(48))
    with httpx2.Client(transport=httpx2.MockTransport(handler)) as client:
        result = translate_markdown(
            client,
            TranslationInput(source_id=SOURCE_ID, markdown=markdown, api_key=api_key),
        )

    assert result == markdown  # noqa: S101
    assert observed_chunks == [  # noqa: S101
        (
            f"Read {PROVIDER_PLACEHOLDER}global settings"
            f"{PROVIDER_PLACEHOLDER * 3} for details."
        )
    ]


def test_translate_retries_failed_chunk_at_smaller_boundaries() -> None:
    """Retry only invalid provider output by splitting the failed chunk."""
    paragraph_a = ("Translate the first sentence exactly. " * 90) + "`literal_a`."
    paragraph_b = ("Translate the second sentence exactly. " * 90) + "`literal_b`."
    markdown = f"# Retry handbook\n\n{paragraph_a}\n\n{paragraph_b}"
    observed_chunks: list[str] = []
    successful_chunks: list[str] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        payload = KimiRequest.model_validate_json(request.content)
        chunk = payload.messages[1].content
        observed_chunks.append(chunk)
        if len(chunk) <= RETRY_FAILURE_THRESHOLD:
            successful_chunks.append(chunk)
            return _json_response(request, chunk)

        return _json_response(request, chunk.replace(PROVIDER_PLACEHOLDER, "", 1))

    api_key = SecretStr(secrets.token_urlsafe(48))
    with httpx2.Client(transport=httpx2.MockTransport(handler)) as client:
        result = translate_markdown(
            client,
            TranslationInput(source_id=SOURCE_ID, markdown=markdown, api_key=api_key),
        )

    assert result == markdown  # noqa: S101
    assert len(observed_chunks[0]) > RETRY_FAILURE_THRESHOLD  # noqa: S101
    assert successful_chunks  # noqa: S101
    assert all(len(chunk) <= RETRY_FAILURE_THRESHOLD for chunk in successful_chunks)  # noqa: S101


def test_translate_retry_never_splits_a_protected_placeholder() -> None:
    """Keep each protected placeholder atomic across recursive hard splits."""
    markdown = ("a" * 3_500) + "`literal_at_boundary`" + ("b" * 3_500)

    def handler(request: httpx2.Request) -> httpx2.Response:
        payload = KimiRequest.model_validate_json(request.content)
        chunk = payload.messages[1].content
        if len(chunk) > RETRY_FAILURE_THRESHOLD:
            return _json_response(request, chunk.replace(PROVIDER_PLACEHOLDER, "", 1))
        return _json_response(request, chunk)

    api_key = SecretStr(secrets.token_urlsafe(48))
    with httpx2.Client(transport=httpx2.MockTransport(handler)) as client:
        result = translate_markdown(
            client,
            TranslationInput(source_id=SOURCE_ID, markdown=markdown, api_key=api_key),
        )

    assert result == markdown  # noqa: S101


def test_translate_uses_one_stable_provider_placeholder_for_all_literals() -> None:
    """Use repeated provider markers while restoring unique literals in order."""
    markdown = "# Short retry\n\nFirst `literal_a`, then `literal_b`."
    observed_chunks: list[str] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        payload = KimiRequest.model_validate_json(request.content)
        chunk = payload.messages[1].content
        observed_chunks.append(chunk)
        return _json_response(request, chunk)

    api_key = SecretStr(secrets.token_urlsafe(48))
    with httpx2.Client(transport=httpx2.MockTransport(handler)) as client:
        result = translate_markdown(
            client,
            TranslationInput(source_id=SOURCE_ID, markdown=markdown, api_key=api_key),
        )

    assert result == markdown  # noqa: S101
    assert observed_chunks == [  # noqa: S101
        (
            f"{PROVIDER_PLACEHOLDER}Short retry\n\n"
            f"First {PROVIDER_PLACEHOLDER}, then {PROVIDER_PLACEHOLDER}."
        )
    ]


def test_translate_protects_markdown_structure_before_provider() -> None:
    """Keep Markdown structure out of the provider's editable text."""
    markdown = "# Short heading that must keep its exact level"
    observed_chunks: list[str] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        payload = KimiRequest.model_validate_json(request.content)
        chunk = payload.messages[1].content
        observed_chunks.append(chunk)
        return _json_response(request, chunk.replace("# ", "## ", 1))

    api_key = SecretStr(secrets.token_urlsafe(48))
    with httpx2.Client(transport=httpx2.MockTransport(handler)) as client:
        result = translate_markdown(
            client,
            TranslationInput(source_id=SOURCE_ID, markdown=markdown, api_key=api_key),
        )

    assert result == markdown  # noqa: S101
    assert observed_chunks == [  # noqa: S101
        f"{PROVIDER_PLACEHOLDER}Short heading that must keep its exact level"
    ]


def test_translate_protects_lists_quotes_and_table_syntax() -> None:
    """Restore structural markers exactly after translating prose."""
    markdown = (
        "# Structure\n\n"
        "- list item\n\n"
        "> quoted text\n\n"
        "| A | B |\n"
        "| --- | --- |\n"
        "| value | value |\n"
    )
    observed_chunks: list[str] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        payload = KimiRequest.model_validate_json(request.content)
        chunk = payload.messages[1].content
        observed_chunks.append(chunk)
        return _json_response(request, chunk)

    api_key = SecretStr(secrets.token_urlsafe(48))
    with httpx2.Client(transport=httpx2.MockTransport(handler)) as client:
        result = translate_markdown(
            client,
            TranslationInput(source_id=SOURCE_ID, markdown=markdown, api_key=api_key),
        )

    assert result == markdown  # noqa: S101
    assert len(observed_chunks) == 1  # noqa: S101
    assert (  # noqa: S101
        observed_chunks[0].count(PROVIDER_PLACEHOLDER) >= MIN_STRUCTURE_PLACEHOLDERS
    )
    assert "# " not in observed_chunks[0]  # noqa: S101
    assert "| --- | --- |" not in observed_chunks[0]  # noqa: S101


@pytest.mark.parametrize("response_body", BAD_RESPONSES)
def test_translate_maps_invalid_responses_to_safe_failure(response_body: bytes) -> None:
    """Map malformed or incomplete provider responses to one safe error."""
    api_key = SecretStr(secrets.token_urlsafe(48))

    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            status_code=200,
            request=request,
            headers={"content-type": "application/json"},
            content=response_body,
        )

    _assert_translation_failed(
        lambda: _call(httpx2.MockTransport(handler), api_key),
        "response_invalid",
    )


def test_translate_maps_http_transport_and_restore_failures() -> None:
    """Map all adapter and protected-output failures to one safe error."""
    api_key = SecretStr(secrets.token_urlsafe(48))

    def transport_failure(request: httpx2.Request) -> httpx2.Response:
        message = "synthetic network failure"
        raise httpx2.ConnectError(message, request=request)

    _assert_translation_failed(
        lambda: _call(httpx2.MockTransport(transport_failure), api_key),
        "transport",
    )

    def missing_token(request: httpx2.Request) -> httpx2.Response:
        return _json_response(request, "translated without tokens")

    _assert_translation_failed(
        lambda: _call(httpx2.MockTransport(missing_token), api_key),
        "output_token_missing",
    )

    def non_success(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            status_code=500,
            request=request,
            content=b"provider failure",
        )

    with create_http_client(httpx2.MockTransport(non_success)) as client:
        _assert_translation_failed(
            lambda: translate_markdown(client, _translation_input(api_key)),
            "provider_server",
        )


@pytest.mark.parametrize(
    ("status_code", "expected_reason"),
    [
        (400, "provider_request"),
        (401, "provider_auth"),
        (403, "provider_permission"),
        (404, "provider_not_found"),
        (429, "provider_quota"),
    ],
)
def test_translate_classifies_provider_status_without_exposing_response(
    status_code: int,
    expected_reason: str,
) -> None:
    """Expose only a fixed failure category for provider HTTP errors."""
    api_key = SecretStr(secrets.token_urlsafe(48))

    def reject(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            status_code=status_code,
            request=request,
            content=b'{"error":{"message":"unsafe provider detail"}}',
        )

    with create_http_client(httpx2.MockTransport(reject)) as client:
        _assert_translation_failed(
            lambda: translate_markdown(client, _translation_input(api_key)),
            expected_reason,
        )


def test_translate_retries_transient_rate_limit_inside_the_current_chunk() -> None:
    """Keep completed chunks in memory when a transient provider limit clears."""
    attempts = 0
    api_key = SecretStr(secrets.token_urlsafe(48))

    class UnreadBody(httpx2.SyncByteStream):
        @override
        def __iter__(self) -> Iterator[bytes]:
            yield b'{"error":{"message":"We are receiving too many requests"}}'

    def handler(request: httpx2.Request) -> httpx2.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx2.Response(
                status_code=429,
                request=request,
                headers={"retry-after": "0"},
                stream=UnreadBody(),
            )
        payload = KimiRequest.model_validate_json(request.content)
        return _json_response(request, payload.messages[1].content)

    with create_http_client(httpx2.MockTransport(handler)) as client:
        result = translate_markdown(client, _translation_input(api_key))

    assert result == MARKDOWN  # noqa: S101
    assert attempts == EXPECTED_SECTION_CHUNKS  # noqa: S101


def test_runtime_secret_is_absent_from_output_files_and_diff(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Keep a runtime-only key out of every task evidence surface."""
    sentinel = secrets.token_urlsafe(48)
    api_key = SecretStr(sentinel)
    checks: list[bool] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        checks.append(
            hmac.compare_digest(
                _authorization(request),
                f"Bearer {sentinel}",
            )
        )
        if not checks[-1]:
            return httpx2.Response(
                status_code=401,
                request=request,
                content=b"denied",
            )
        return _json_response(request, _provider_markdown(MARKDOWN))

    _ = _call(httpx2.MockTransport(handler), api_key)
    _ = (tmp_path / "evidence.txt").write_text("safe", encoding="utf-8")
    captured = capsys.readouterr()
    assert checks == [True]  # noqa: S101
    assert sentinel not in captured.out + captured.err  # noqa: S101

    roots = (
        tmp_path,
        ROOT / ".ai-local",
        ROOT / ".superpowers" / "sdd" / "task-3",
        ROOT / "docs" / ".vitepress" / "dist",
    )
    owned_files = (
        ROOT / "scripts" / "ai" / "kimi.py",
        ROOT / "tests" / "ai" / "test_kimi.py",
    )
    for path in (*roots, *owned_files):
        assert not _contains(path, sentinel)  # noqa: S101

    git = which("git")
    if git is None:
        message = "git executable is required"
        raise RuntimeError(message)
    diff = subprocess.run(  # noqa: S603
        [git, "diff", "--no-ext-diff"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert diff.returncode == 0  # noqa: S101
    assert sentinel not in diff.stdout + diff.stderr  # noqa: S101


def _contains(path: Path, sentinel: str) -> bool:
    if not path.exists():
        return False
    files = (path,) if path.is_file() else tuple(item for item in path.rglob("*") if item.is_file())
    for file in files:
        try:
            if sentinel in file.read_text(encoding="utf-8"):
                return True
        except (OSError, UnicodeError):
            continue
    return False

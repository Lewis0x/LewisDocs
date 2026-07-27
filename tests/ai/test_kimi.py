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
    from collections.abc import Callable

ROOT = Path(__file__).resolve().parents[2]
SOURCE_ID: Final = SourceId("claude-code/quickstart")
MARKDOWN: Final = (
    "# Synthetic handbook\n\nRun `npm run ai:sync` against https://example.test/docs\n"
)
FAILURE_MESSAGE: Final = "translation failed"
ENDPOINT: Final = "https://api.kimi.com/coding/v1/chat/completions"
EXPECTED_TRANSLATION_READ_TIMEOUT: Final = 900.0
EXPECTED_MAX_TRANSLATION_CHARS: Final = 10_000
EXPECTED_TRANSLATION_CHUNKS: Final = 3
RETRY_FAILURE_THRESHOLD: Final = 4_000
EXPECTED_RETRY_TOKENS: Final = 2

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
    protected = protect_markdown(MARKDOWN)
    translated = protected.text.replace("Synthetic handbook", "合成手册")
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
    assert "不得移动任何 @@LEWISDOCS_0000@@ 令牌" in observed.payload.messages[0].content  # noqa: S101
    assert observed.payload.messages[1].role == "user"  # noqa: S101
    assert observed.payload.messages[1].content == protected.text  # noqa: S101
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
    assert len(observed_chunks) == EXPECTED_TRANSLATION_CHUNKS  # noqa: S101
    assert all(len(chunk) <= EXPECTED_MAX_TRANSLATION_CHARS for chunk in observed_chunks)  # noqa: S101


def test_translate_retries_failed_chunk_at_smaller_boundaries() -> None:
    """Retry only invalid provider output by splitting the failed chunk."""
    paragraph_a = ("Translate the first sentence exactly. " * 90) + "`literal_a`."
    paragraph_b = ("Translate the second sentence exactly. " * 90) + "`literal_b`."
    markdown = f"# Retry handbook\n\n{paragraph_a}\n\n{paragraph_b}"
    expected_tokens = tuple(span.placeholder for span in protect_markdown(markdown).spans)
    observed_chunks: list[str] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        payload = KimiRequest.model_validate_json(request.content)
        chunk = payload.messages[1].content
        observed_chunks.append(chunk)
        if len(chunk) <= RETRY_FAILURE_THRESHOLD:
            return _json_response(request, chunk)

        assert len(expected_tokens) == EXPECTED_RETRY_TOKENS  # noqa: S101
        swapped = chunk.replace(expected_tokens[0], "@@SWAP@@", 1)
        swapped = swapped.replace(expected_tokens[1], expected_tokens[0], 1)
        return _json_response(
            request,
            swapped.replace("@@SWAP@@", expected_tokens[1], 1),
        )

    api_key = SecretStr(secrets.token_urlsafe(48))
    with httpx2.Client(transport=httpx2.MockTransport(handler)) as client:
        result = translate_markdown(
            client,
            TranslationInput(source_id=SOURCE_ID, markdown=markdown, api_key=api_key),
        )

    assert result == markdown  # noqa: S101
    assert len(observed_chunks[0]) > RETRY_FAILURE_THRESHOLD  # noqa: S101
    assert all(  # noqa: S101
        len(chunk) <= RETRY_FAILURE_THRESHOLD for chunk in observed_chunks[1:]
    )


def test_translate_retry_never_splits_a_protected_placeholder() -> None:
    """Keep each protected placeholder atomic across recursive hard splits."""
    markdown = ("a" * 3_500) + "`literal_at_boundary`" + ("b" * 3_500)
    expected_token = protect_markdown(markdown).spans[0].placeholder

    def handler(request: httpx2.Request) -> httpx2.Response:
        payload = KimiRequest.model_validate_json(request.content)
        chunk = payload.messages[1].content
        if len(chunk) > RETRY_FAILURE_THRESHOLD:
            return _json_response(request, chunk.replace(expected_token, "", 1))
        return _json_response(request, chunk)

    api_key = SecretStr(secrets.token_urlsafe(48))
    with httpx2.Client(transport=httpx2.MockTransport(handler)) as client:
        result = translate_markdown(
            client,
            TranslationInput(source_id=SOURCE_ID, markdown=markdown, api_key=api_key),
        )

    assert result == markdown  # noqa: S101


def test_translate_keeps_splitting_short_failed_chunks_with_multiple_tokens() -> None:
    """Split below the character floor until reordered tokens are isolated."""
    markdown = "# Short retry\n\nFirst `literal_a`, then `literal_b`."
    expected_tokens = tuple(span.placeholder for span in protect_markdown(markdown).spans)
    observed_chunks: list[str] = []
    successful_chunks: list[str] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        payload = KimiRequest.model_validate_json(request.content)
        chunk = payload.messages[1].content
        observed_chunks.append(chunk)
        if all(token in chunk for token in expected_tokens):
            swapped = chunk.replace(expected_tokens[0], "@@SWAP@@", 1)
            swapped = swapped.replace(expected_tokens[1], expected_tokens[0], 1)
            return _json_response(
                request,
                swapped.replace("@@SWAP@@", expected_tokens[1], 1),
            )
        successful_chunks.append(chunk)
        return _json_response(request, chunk)

    api_key = SecretStr(secrets.token_urlsafe(48))
    with httpx2.Client(transport=httpx2.MockTransport(handler)) as client:
        result = translate_markdown(
            client,
            TranslationInput(source_id=SOURCE_ID, markdown=markdown, api_key=api_key),
        )

    assert result == markdown  # noqa: S101
    assert len(observed_chunks) > 1  # noqa: S101
    assert all(  # noqa: S101
        sum(token in chunk for token in expected_tokens) <= 1 for chunk in successful_chunks
    )


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
        return _json_response(request, "# 合成手册\n\ntranslated without tokens\n")

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


def test_runtime_secret_is_absent_from_output_files_and_diff(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Keep a runtime-only key out of every task evidence surface."""
    sentinel = secrets.token_urlsafe(48)
    api_key = SecretStr(sentinel)
    checks: list[bool] = []
    protected = protect_markdown(MARKDOWN)

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
        return _json_response(request, protected.text)

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

# Copyright 2026
"""Kimi Code API adapter for Chinese markdown translation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from time import sleep
from typing import TYPE_CHECKING, ClassVar, Final, Literal, NoReturn, cast

import httpx2
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SecretStr,
    ValidationError,
    field_validator,
)

from scripts.ai.errors import AIAgentError, ErrorCode, TranslationFailureReason
from scripts.ai.protect import ProtectedMarkdown, protect_markdown, restore_and_validate

if TYPE_CHECKING:
    from scripts.ai.types import SourceId

# Kimi Code Console keys require the managed coding endpoint.
# https://www.kimi.com/code/docs/#api-%E6%8E%A5%E5%85%A5
_ENDPOINT: Final = "https://api.kimi.com/coding/v1/chat/completions"
_SERVER_ERROR_MIN_STATUS: Final = 500
_RATE_LIMIT_STATUS: Final = 429
_RATE_LIMIT_RETRY_DELAYS: Final = (5.0, 15.0, 45.0)
_MAX_RETRY_AFTER_SECONDS: Final = 300.0
_TRANSIENT_RATE_LIMIT_MARKERS: Final = (
    b"engine is currently overloaded",
    b"too many requests",
)
_MAX_TRANSLATION_CHARS: Final = 4_000
_PROVIDER_PLACEHOLDER: Final = "@@LEWISDOCS_LITERAL@@"
_PROVIDER_LINK_LABEL_PATTERN: Final = (
    r"(?P<prefix>!?\[)(?P<label>[^\]\n]*)(?P<middle>\]\()"
)
_PROVIDER_LINK_TARGET_PATTERN: Final = (
    r"(?P<target>@@LEWISDOCS_\d{4}@@)(?P<suffix>\))"
)
_PROVIDER_LINK_RE: Final = re.compile(
    f"{_PROVIDER_LINK_LABEL_PATTERN}{_PROVIDER_LINK_TARGET_PATTERN}"
)
_STRUCTURE_PREFIX_PATTERN: Final = (
    r"(?m)^(?:#{1,6}[ \t]+|[ \t]*(?:[-+*]|\d+\.)[ \t]+|[ \t]*>+[ \t]*)"
)
_TABLE_DELIMITER_PATTERN: Final = (
    r"^[ \t]*\|?[ \t]*:?-{3,}:?" + r"(?:[ \t]*\|[ \t]*:?-{3,}:?)+[ \t]*\|?[ \t]*$"
)
_STRUCTURE_RE: Final = re.compile(rf"{_STRUCTURE_PREFIX_PATTERN}|{_TABLE_DELIMITER_PATTERN}|\|")
_SECTION_HEADING_RE: Final = re.compile(r"(?m)^#{1,6}[ \t]+")
_TRANSLATION_TIMEOUT: Final = httpx2.Timeout(
    connect=10.0,
    read=900.0,
    write=30.0,
    pool=10.0,
)
_SYSTEM_PROMPT: Final = (
    "你必须逐行翻译并只输出中文 Markdown, 不要解释, 不要用代码围栏包裹答案; "
    "输出行数、行顺序和段落顺序必须与输入完全一致, "
    "保持原文结构与占位符令牌不变, @@LEWISDOCS_LITERAL@@ 必须逐字、逐个保留; "
    "不得增删或移动任何 @@LEWISDOCS_LITERAL@@ 令牌, 不得修改格式、标点或保护段落。"
)
_TRANSLATION_FAILED_MESSAGE: Final = "translation failed"
_RETRYABLE_OUTPUT_REASONS: Final = frozenset(
    {
        TranslationFailureReason.OUTPUT_INVALID,
        TranslationFailureReason.OUTPUT_TOKEN_INVALID,
        TranslationFailureReason.OUTPUT_TOKEN_MISSING,
        TranslationFailureReason.OUTPUT_TOKEN_UNEXPECTED,
        TranslationFailureReason.OUTPUT_TOKEN_REORDERED,
        TranslationFailureReason.OUTPUT_STRUCTURE_INVALID,
        TranslationFailureReason.OUTPUT_LITERAL_INVALID,
    }
)


class KimiMessage(BaseModel):
    """Chat message payload used in requests."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")

    role: Literal["system", "user"]
    content: str = Field(min_length=1)


class KimiRequest(BaseModel):
    """Canonical request model for the Kimi Code OpenAI-compatible API."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")

    model: Literal["k3"]
    reasoning_effort: Literal["low"]
    messages: tuple[KimiMessage, ...] = Field(min_length=2, max_length=2)


class KimiResponseMessage(BaseModel):
    """Subset message payload returned by Moonshot."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="ignore")

    content: str

    @field_validator("content")
    @classmethod
    def _non_empty_content(cls, value: str) -> str:
        text = value.strip()
        if not text:
            message = "content must be non-empty"
            raise ValueError(message)
        return value


class KimiResponseChoice(BaseModel):
    """Single completion choice."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="ignore")

    message: KimiResponseMessage


class KimiResponse(BaseModel):
    """Flexible response model for Kimi Code chat completions."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="ignore")

    choices: tuple[KimiResponseChoice, ...] = Field(min_length=1)


@dataclass(frozen=True, slots=True)
class TranslationInput:
    """Input to the Kimi translator."""

    source_id: SourceId
    markdown: str
    api_key: SecretStr


@dataclass(frozen=True, slots=True)
class _TranslationChunk:
    protected: ProtectedMarkdown
    source: str
    separator: str


@dataclass(frozen=True, slots=True)
class _ProviderPayload:
    text: str
    replacements: tuple[str, ...]


def _raise_translation_failed(
    source_id: SourceId,
    reason: TranslationFailureReason,
) -> NoReturn:
    raise AIAgentError(
        code=ErrorCode.TRANSLATION_FAILED,
        message=_TRANSLATION_FAILED_MESSAGE,
        source_id=source_id,
        reason=reason,
    )


def _provider_failure_reason(status_code: int) -> TranslationFailureReason:
    return {
        401: TranslationFailureReason.PROVIDER_AUTH,
        403: TranslationFailureReason.PROVIDER_PERMISSION,
        404: TranslationFailureReason.PROVIDER_NOT_FOUND,
        429: TranslationFailureReason.PROVIDER_QUOTA,
    }.get(
        status_code,
        (
            TranslationFailureReason.PROVIDER_SERVER
            if status_code >= _SERVER_ERROR_MIN_STATUS
            else TranslationFailureReason.PROVIDER_REQUEST
        ),
    )


def translate_markdown(client: httpx2.Client, request: TranslationInput) -> str:
    """Protect literals, call Kimi, validate completion, and restore literals."""
    protected = protect_markdown(request.markdown)
    auth = f"Bearer {request.api_key.get_secret_value()}"

    try:
        translated: list[str] = []
        for chunk in _translation_chunks(protected):
            translated.extend(
                (
                    _translate_chunk(client, chunk, auth),
                    chunk.separator,
                )
            )
        return "".join(translated)
    except AIAgentError as error:
        _raise_translation_failed(
            request.source_id,
            error.reason or TranslationFailureReason.OUTPUT_INVALID,
        )
    except httpx2.HTTPStatusError as error:
        _raise_translation_failed(
            request.source_id,
            _provider_failure_reason(error.response.status_code),
        )
    except httpx2.HTTPError:
        _raise_translation_failed(
            request.source_id,
            TranslationFailureReason.TRANSPORT,
        )
    except ValidationError:
        _raise_translation_failed(
            request.source_id,
            TranslationFailureReason.RESPONSE_INVALID,
        )


def _translate_chunk(
    client: httpx2.Client,
    chunk: _TranslationChunk,
    auth: str,
) -> str:
    provider = _provider_payload(chunk.protected)
    payload = KimiRequest(
        model="k3",
        reasoning_effort="low",
        messages=(
            KimiMessage(role="system", content=_SYSTEM_PROMPT),
            KimiMessage(role="user", content=provider.text),
        ),
    )
    response = _post_with_rate_limit_retry(client, payload, auth)
    _ = response.raise_for_status()
    completion = KimiResponse.model_validate_json(response.content).choices[0].message.content

    try:
        normalized_completion = _normalize_provider_placeholders(
            provider,
            completion,
        )
        return restore_and_validate(
            chunk.source,
            chunk.protected,
            normalized_completion,
        )
    except AIAgentError as error:
        if error.reason not in _RETRYABLE_OUTPUT_REASONS or len(chunk.protected.text) <= 1:
            raise

        retry_max_chars = max(1, len(chunk.protected.text) // 2)
        retry_chunks = _translation_chunks(chunk.protected, retry_max_chars)
        if len(retry_chunks) <= 1:
            raise
        return "".join(
            _translate_chunk(client, retry_chunk, auth) + retry_chunk.separator
            for retry_chunk in retry_chunks
        )


def _post_with_rate_limit_retry(
    client: httpx2.Client,
    payload: KimiRequest,
    auth: str,
) -> httpx2.Response:
    for retry, fallback_delay in enumerate((*_RATE_LIMIT_RETRY_DELAYS, None)):
        try:
            return client.post(
                _ENDPOINT,
                headers={"Authorization": auth},
                json=payload.model_dump(mode="json"),
                timeout=_TRANSLATION_TIMEOUT,
            )
        except httpx2.HTTPStatusError as error:
            if (
                fallback_delay is None
                or not _is_transient_rate_limit(error.response)
                or retry >= len(_RATE_LIMIT_RETRY_DELAYS)
            ):
                raise
            sleep(_retry_delay(error.response, fallback_delay))
    raise AssertionError


def _is_transient_rate_limit(response: httpx2.Response) -> bool:
    content = response.content.lower()
    return response.status_code == _RATE_LIMIT_STATUS and any(
        marker in content for marker in _TRANSIENT_RATE_LIMIT_MARKERS
    )


def _retry_delay(response: httpx2.Response, fallback: float) -> float:
    value = cast("str | None", response.headers.get("retry-after"))
    if value is None:
        return fallback
    try:
        return min(max(float(value), 0.0), _MAX_RETRY_AFTER_SECONDS)
    except ValueError:
        return fallback


def _provider_payload(protected: ProtectedMarkdown) -> _ProviderPayload:
    candidates: list[tuple[int, int, str]] = []
    for span in protected.spans:
        start = protected.text.find(span.placeholder)
        if start < 0:
            raise AIAgentError(
                code=ErrorCode.TRANSLATION_FAILED,
                message=_TRANSLATION_FAILED_MESSAGE,
                reason=TranslationFailureReason.OUTPUT_TOKEN_MISSING,
            )
        candidates.append((start, start + len(span.placeholder), span.placeholder))
    candidates.extend(
        (match.start(), match.end(), match.group(0))
        for match in _STRUCTURE_RE.finditer(protected.text)
    )
    for match in _PROVIDER_LINK_RE.finditer(protected.text):
        candidates.extend(
            (*match.span(group), match.group(group))
            for group in ("prefix", "middle", "suffix")
        )

    parts: list[str] = []
    replacements: list[str] = []
    cursor = 0
    for start, end, replacement in sorted(candidates):
        if start < cursor:
            continue
        parts.extend((protected.text[cursor:start], _PROVIDER_PLACEHOLDER))
        replacements.append(replacement)
        cursor = end
    parts.append(protected.text[cursor:])
    return _ProviderPayload(text="".join(parts), replacements=tuple(replacements))


def _normalize_provider_placeholders(
    provider: _ProviderPayload,
    completion: str,
) -> str:
    expected_count = len(provider.replacements)
    found_count = completion.count(_PROVIDER_PLACEHOLDER)
    if found_count < expected_count:
        raise AIAgentError(
            code=ErrorCode.TRANSLATION_FAILED,
            message=_TRANSLATION_FAILED_MESSAGE,
            reason=TranslationFailureReason.OUTPUT_TOKEN_MISSING,
        )
    if found_count > expected_count:
        raise AIAgentError(
            code=ErrorCode.TRANSLATION_FAILED,
            message=_TRANSLATION_FAILED_MESSAGE,
            reason=TranslationFailureReason.OUTPUT_TOKEN_UNEXPECTED,
        )

    normalized = completion
    for replacement in provider.replacements:
        normalized = normalized.replace(_PROVIDER_PLACEHOLDER, replacement, 1)
    return normalized


def _translation_chunks(
    protected: ProtectedMarkdown,
    max_chars: int = _MAX_TRANSLATION_CHARS,
) -> tuple[_TranslationChunk, ...]:
    chunks: list[_TranslationChunk] = []
    placeholders = tuple(span.placeholder for span in protected.spans)
    for text, separator in _split_text(protected.text, max_chars, placeholders):
        spans = tuple(span for span in protected.spans if span.placeholder in text)
        chunk = ProtectedMarkdown(text=text, spans=spans)
        source = text
        for span in spans:
            source = source.replace(span.placeholder, span.original, 1)
        chunks.append(_TranslationChunk(protected=chunk, source=source, separator=separator))
    return tuple(chunks)


def _split_text(
    text: str,
    max_chars: int,
    placeholders: tuple[str, ...],
) -> tuple[tuple[str, str], ...]:
    chunks: list[tuple[str, str]] = []
    placeholder_ranges = tuple(
        (start, start + len(placeholder))
        for placeholder in placeholders
        if (start := text.find(placeholder)) >= 0
    )
    cursor = 0
    while len(text) - cursor > max_chars:
        limit = cursor + max_chars
        minimum = cursor + (max_chars // 2)
        boundary = _section_boundary(text, minimum, limit)
        if boundary < 0:
            boundary = text.rfind("\n\n", minimum, limit + 1)
        if boundary < 0:
            boundary = text.rfind("\n", minimum, limit + 1)
        if boundary < 0:
            boundary = text.rfind(" ", minimum, limit + 1)
        if boundary < 0:
            boundary = limit
        boundary = _placeholder_safe_boundary(cursor, boundary, placeholder_ranges)

        separator_end = boundary
        if text[boundary : boundary + 1] == "\n":
            while text[separator_end : separator_end + 1] == "\n":
                separator_end += 1
        elif text[boundary : boundary + 1] == " ":
            while text[separator_end : separator_end + 1] == " ":
                separator_end += 1

        chunks.append((text[cursor:boundary], text[boundary:separator_end]))
        cursor = max(boundary, separator_end)
    chunks.append((text[cursor:], ""))
    return tuple(chunk for chunk in chunks if chunk[0])


def _section_boundary(text: str, minimum: int, limit: int) -> int:
    boundary = -1
    for match in _SECTION_HEADING_RE.finditer(text, minimum, limit + 1):
        boundary = match.start()
    while boundary > minimum and text[boundary - 1 : boundary] == "\n":
        boundary -= 1
    return boundary


def _placeholder_safe_boundary(
    cursor: int,
    boundary: int,
    placeholder_ranges: tuple[tuple[int, int], ...],
) -> int:
    for start, end in placeholder_ranges:
        if start < boundary < end:
            return start if start > cursor else end
    return boundary

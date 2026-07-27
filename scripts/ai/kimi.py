# Copyright 2026
"""Kimi Code API adapter for Chinese markdown translation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, Final, Literal, NoReturn

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
from scripts.ai.protect import protect_markdown, restore_and_validate

if TYPE_CHECKING:
    from scripts.ai.types import SourceId

# Kimi Code Console keys require the managed coding endpoint.
# https://www.kimi.com/code/docs/#api-%E6%8E%A5%E5%85%A5
_ENDPOINT: Final = "https://api.kimi.com/coding/v1/chat/completions"
_SERVER_ERROR_MIN_STATUS: Final = 500
_TRANSLATION_TIMEOUT: Final = httpx2.Timeout(
    connect=10.0,
    read=900.0,
    write=30.0,
    pool=10.0,
)
_SYSTEM_PROMPT: Final = (
    "你必须逐行翻译并只输出中文 Markdown, 不要解释, 不要用代码围栏包裹答案; "
    "输出行数、行顺序和段落顺序必须与输入完全一致, "
    "保持原文结构与占位符令牌不变, 例如 @@LEWISDOCS_0000@@ 必须逐字保留; "
    "不得移动任何 @@LEWISDOCS_0000@@ 令牌, 不得修改格式、标点或保护段落。"
)
_TRANSLATION_FAILED_MESSAGE: Final = "translation failed"


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
    payload = KimiRequest(
        model="k3",
        reasoning_effort="low",
        messages=(
            KimiMessage(
                role="system",
                content=_SYSTEM_PROMPT,
            ),
            KimiMessage(role="user", content=protected.text),
        ),
    )
    auth = f"Bearer {request.api_key.get_secret_value()}"

    try:
        response = client.post(
            _ENDPOINT,
            headers={"Authorization": auth},
            json=payload.model_dump(mode="json"),
            timeout=_TRANSLATION_TIMEOUT,
        )
        _ = response.raise_for_status()
        completion = KimiResponse.model_validate_json(response.content).choices[0].message.content
        return restore_and_validate(request.markdown, protected, completion)
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

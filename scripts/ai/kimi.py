# Copyright 2026
"""Moonshot API adapter for Chinese markdown translation."""

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

from scripts.ai.errors import AIAgentError, ErrorCode
from scripts.ai.protect import protect_markdown, restore_and_validate

if TYPE_CHECKING:
    from scripts.ai.types import SourceId

# China-platform keys require the matching regional endpoint.
# https://platform.kimi.com/docs/api/overview
_ENDPOINT: Final = "https://api.moonshot.cn/v1/chat/completions"
_SYSTEM_PROMPT: Final = (
    "你必须只输出中文 Markdown, 并保持原文结构与占位符令牌不变, 不得修改格式、标点或保护段落。"
)
_TRANSLATION_FAILED_MESSAGE: Final = "translation failed"


class KimiMessage(BaseModel):
    """Chat message payload used in requests."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")

    role: Literal["system", "user"]
    content: str = Field(min_length=1)


class KimiRequest(BaseModel):
    """Canonical request model for Moonshot API."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")

    model: Literal["kimi-k3"]
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
    """Flexible response model for Moonshot chat completions."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="ignore")

    choices: tuple[KimiResponseChoice, ...] = Field(min_length=1)


@dataclass(frozen=True, slots=True)
class TranslationInput:
    """Input to the Kimi translator."""

    source_id: SourceId
    markdown: str
    api_key: SecretStr


def _raise_translation_failed(source_id: SourceId) -> NoReturn:
    raise AIAgentError(
        code=ErrorCode.TRANSLATION_FAILED,
        message=_TRANSLATION_FAILED_MESSAGE,
        source_id=source_id,
    )


def translate_markdown(client: httpx2.Client, request: TranslationInput) -> str:
    """Protect literals, call Kimi, validate completion, and restore literals."""
    protected = protect_markdown(request.markdown)
    payload = KimiRequest(
        model="kimi-k3",
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
        )
        _ = response.raise_for_status()
        completion = KimiResponse.model_validate_json(response.content).choices[0].message.content
        return restore_and_validate(request.markdown, protected, completion)
    except (AIAgentError, httpx2.HTTPError, ValidationError):
        _raise_translation_failed(request.source_id)

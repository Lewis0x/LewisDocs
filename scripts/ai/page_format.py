# Copyright 2026

"""Exact accepted-page rendering and frontmatter parsing."""

from __future__ import annotations

import re
from pathlib import Path  # noqa: TC003
from typing import ClassVar, Final, Literal, NoReturn, assert_never

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator, model_validator

from scripts.ai.errors import AIAgentError, ErrorCode
from scripts.ai.types import NormalizedPage, Owner, Product, SourceId  # noqa: TC001

_COMMON_FIELDS: Final = (
    "title",
    "source_id",
    "product",
    "lang",
    "canonical_url",
    "owner",
    "content_sha256",
)
_CHINESE_FIELDS: Final = (*_COMMON_FIELDS, "translation_of", "translation_model", "ai_translated")
WARNING: Final = "本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。"  # noqa: RUF001
_DEFAULT_MODEL: Final = "k3"
_TRANSLATION_MODELS: Final = ("k3", "glm-5.2")
_FRONTMATTER_ERROR: Final = "invalid frontmatter"
_HASH_RE: Final = re.compile(r"[0-9a-f]{64}\Z")
_H1_RE: Final = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)


class AcceptedPage(BaseModel):
    """One parsed accepted page, including ordered frontmatter and body."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid", strict=True)

    title: str
    source_id: SourceId
    product: Product
    lang: Literal["en", "zh-CN"]
    canonical_url: str
    owner: Owner
    content_sha256: str
    translation_of: SourceId | None = None
    translation_model: Literal["k3", "glm-5.2"] | None = None
    ai_translated: Literal[True] | None = None
    body: str

    @field_validator("title", "canonical_url", "body")
    @classmethod
    def _require_text(cls, value: str) -> str:
        if not value.strip():
            msg = "page text fields must be non-empty"
            raise ValueError(msg)
        return value

    @field_validator("content_sha256")
    @classmethod
    def _require_hash(cls, value: str) -> str:
        if _HASH_RE.fullmatch(value) is None:
            msg = "content_sha256 must be lowercase SHA-256"
            raise ValueError(msg)
        return value

    @model_validator(mode="after")
    def _require_translation_shape(self) -> AcceptedPage:
        language = self.lang
        match language:
            case "en":
                if any(
                    field is not None
                    for field in (
                        self.translation_of,
                        self.translation_model,
                        self.ai_translated,
                    )
                ):
                    msg = "English pages cannot contain translation metadata"
                    raise ValueError(msg)
                return self
            case "zh-CN":
                if (
                    self.translation_of is None
                    or self.translation_model not in _TRANSLATION_MODELS
                    or self.ai_translated is not True
                ):
                    msg = "Chinese pages require fixed translation metadata"
                    raise ValueError(msg)
                return self
        assert_never(language)


def render_english_page(normalized: NormalizedPage) -> bytes:
    """Render one deterministic English accepted page."""
    source = normalized.source
    body = (
        f"[Official source]({source.canonical_url})\n\n"
        f"Content owner: {source.owner}\n\n"
        f"{_lf(normalized.markdown)}"
    )
    return _render(
        (
            ("title", source.title),
            ("source_id", source.id),
            ("product", source.product),
            ("lang", "en"),
            ("canonical_url", source.canonical_url),
            ("owner", source.owner),
            ("content_sha256", normalized.content_sha256),
        ),
        body,
    )


def render_chinese_page(
    normalized: NormalizedPage,
    translated: str,
    *,
    translation_model: Literal["k3", "glm-5.2"] = _DEFAULT_MODEL,
) -> bytes:
    """Render one deterministic Chinese accepted page with its fixed warning."""
    source = normalized.source
    translated_lf = _lf(translated)
    title = first_h1(translated_lf)
    body = (
        f"{WARNING}\n\n"
        f"[Official source]({source.canonical_url})\n\n"
        f"Content owner: {source.owner}\n\n"
        f"{translated_lf}"
    )
    return _render(
        (
            ("title", title),
            ("source_id", source.id),
            ("product", source.product),
            ("lang", "zh-CN"),
            ("canonical_url", source.canonical_url),
            ("owner", source.owner),
            ("content_sha256", normalized.content_sha256),
            ("translation_of", source.id),
            ("translation_model", translation_model),
            ("ai_translated", "true"),
        ),
        body,
    )


def parse_accepted_page(path: Path) -> AcceptedPage:
    """Parse exact UTF-8/LF page frontmatter without a generic Markdown parser."""
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        _fail(cause=exc)
    if "\r" in text or not text.endswith("\n"):
        _fail()
    try:
        frontmatter, body = _split_frontmatter(text)
        values = _parse_frontmatter(frontmatter)
        values["body"] = body
        return AcceptedPage.model_validate(values)
    except (ValidationError, ValueError) as exc:
        _fail(cause=exc)


def _render(fields: tuple[tuple[str, str], ...], body: str) -> bytes:
    text = "\n".join(("---", *(f"{key}: {value}" for key, value in fields), "---", body))
    return (_lf(text).rstrip("\n") + "\n").encode("utf-8")


def _lf(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n") + "\n"


def first_h1(markdown: str) -> str:
    """Return the first Markdown H1 from text that has already been normalized."""
    match = _H1_RE.search(markdown)
    if match is None:
        _fail()
    return match.group(1)


def _split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---\n"):
        raise ValueError(_FRONTMATTER_ERROR)
    closing = text.find("\n---\n", len("---\n"))
    if closing < 0:
        raise ValueError(_FRONTMATTER_ERROR)
    return text[len("---\n") : closing], text[closing + len("\n---\n") :]


def _parse_frontmatter(frontmatter: str) -> dict[str, str | bool]:
    lines = frontmatter.splitlines()
    if len(lines) < len(_COMMON_FIELDS):
        raise ValueError(_FRONTMATTER_ERROR)
    fields: list[tuple[str, str]] = []
    for line in lines:
        key, separator, value = line.partition(": ")
        if not separator or not key or not value or "\n" in value:
            raise ValueError(_FRONTMATTER_ERROR)
        fields.append((key, value))
    names = tuple(key for key, _ in fields)
    lang = dict(fields).get("lang")
    expected = _COMMON_FIELDS if lang == "en" else _CHINESE_FIELDS
    if names != expected:
        raise ValueError(_FRONTMATTER_ERROR)
    values: dict[str, str | bool] = dict(fields)
    if lang == "zh-CN":
        values["ai_translated"] = values["ai_translated"] == "true"
    return values


def _fail(cause: Exception | None = None) -> NoReturn:
    raise AIAgentError(
        code=ErrorCode.VALIDATION_FAILED,
        message="page validation failed",
    ) from cause

# Copyright 2026

"""Typed data models used by the AI source manifest and sync boundary."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import ClassVar, Final, Literal, NewType, Self
from urllib.parse import urlparse

from pydantic import (
    BaseModel,
    ConfigDict,
    RootModel,
    ValidationInfo,
    field_validator,
    model_validator,
)

SourceId = NewType("SourceId", str)

Product = Literal["claude-code", "codex"]
FetchFormat = Literal["markdown", "html", "html-main"]
Owner = Literal["Anthropic", "OpenAI"]
RowSpec = tuple[str, str, str, str, str, str, FetchFormat, Owner]

_FROZEN_SOURCE_SET: Final[frozenset[RowSpec]] = frozenset(
    (
        (
            "claude-code/quickstart",
            "claude-code",
            "quickstart",
            "Claude Code Quickstart",
            "https://code.claude.com/docs/en/quickstart",
            "https://code.claude.com/docs/en/quickstart.md",
            "markdown",
            "Anthropic",
        ),
        (
            "claude-code/memory",
            "claude-code",
            "memory",
            "Claude Code Memory",
            "https://code.claude.com/docs/en/memory",
            "https://code.claude.com/docs/en/memory.md",
            "markdown",
            "Anthropic",
        ),
        (
            "claude-code/permissions",
            "claude-code",
            "permissions",
            "Claude Code Permissions",
            "https://code.claude.com/docs/en/permissions",
            "https://code.claude.com/docs/en/permissions.md",
            "markdown",
            "Anthropic",
        ),
        (
            "claude-code/extensions",
            "claude-code",
            "extensions",
            "Claude Code Features Overview",
            "https://code.claude.com/docs/en/features-overview",
            "https://code.claude.com/docs/en/features-overview.md",
            "markdown",
            "Anthropic",
        ),
        (
            "claude-code/best-practices",
            "claude-code",
            "best-practices",
            "Claude Code Best Practices",
            "https://code.claude.com/docs/en/best-practices",
            "https://code.claude.com/docs/en/best-practices.md",
            "markdown",
            "Anthropic",
        ),
        (
            "claude-code/how-it-works",
            "claude-code",
            "how-it-works",
            "How Claude Code Works",
            "https://code.claude.com/docs/en/how-claude-code-works",
            "https://code.claude.com/docs/en/how-claude-code-works.md",
            "markdown",
            "Anthropic",
        ),
        (
            "claude-code/common-workflows",
            "claude-code",
            "common-workflows",
            "Claude Code Common Workflows",
            "https://code.claude.com/docs/en/common-workflows",
            "https://code.claude.com/docs/en/common-workflows.md",
            "markdown",
            "Anthropic",
        ),
        (
            "claude-code/hooks-guide",
            "claude-code",
            "hooks-guide",
            "Automate Actions with Claude Code Hooks",
            "https://code.claude.com/docs/en/hooks-guide",
            "https://code.claude.com/docs/en/hooks-guide.md",
            "markdown",
            "Anthropic",
        ),
        (
            "claude-code/mcp",
            "claude-code",
            "mcp",
            "Connect Claude Code to Tools via MCP",
            "https://code.claude.com/docs/en/mcp",
            "https://code.claude.com/docs/en/mcp.md",
            "markdown",
            "Anthropic",
        ),
        (
            "claude-code/subagents",
            "claude-code",
            "subagents",
            "Create Custom Claude Code Subagents",
            "https://code.claude.com/docs/en/sub-agents",
            "https://code.claude.com/docs/en/sub-agents.md",
            "markdown",
            "Anthropic",
        ),
        (
            "codex/cli",
            "codex",
            "cli",
            "Codex CLI",
            "https://learn.chatgpt.com/docs/codex/cli",
            "https://learn.chatgpt.com/docs/codex/cli",
            "html",
            "OpenAI",
        ),
        (
            "codex/prompting",
            "codex",
            "prompting",
            "Codex Prompting",
            "https://learn.chatgpt.com/docs/prompting",
            "https://learn.chatgpt.com/docs/prompting.md",
            "markdown",
            "OpenAI",
        ),
        (
            "codex/agents-md",
            "codex",
            "agents-md",
            "Codex AGENTS.md",
            "https://learn.chatgpt.com/docs/agent-configuration/agents-md",
            "https://learn.chatgpt.com/docs/agent-configuration/agents-md.md",
            "markdown",
            "OpenAI",
        ),
        (
            "codex/approvals-security",
            "codex",
            "approvals-security",
            "Codex Agent Approvals and Security",
            "https://learn.chatgpt.com/docs/agent-approvals-security",
            "https://learn.chatgpt.com/docs/agent-approvals-security.md",
            "markdown",
            "OpenAI",
        ),
        (
            "codex/customization",
            "codex",
            "customization",
            "Codex Customization Overview",
            "https://learn.chatgpt.com/docs/customization/overview",
            "https://learn.chatgpt.com/docs/customization/overview.md",
            "markdown",
            "OpenAI",
        ),
        (
            "codex/best-practices",
            "codex",
            "best-practices",
            "Codex Best Practices",
            "https://developers.openai.com/codex/learn/best-practices",
            "https://learn.chatgpt.com/guides/best-practices",
            "html",
            "OpenAI",
        ),
        (
            "codex/ide",
            "codex",
            "ide",
            "Codex IDE Extension",
            "https://developers.openai.com/codex/ide",
            "https://learn.chatgpt.com/docs/codex/ide",
            "html",
            "OpenAI",
        ),
        (
            "codex/cloud",
            "codex",
            "cloud",
            "Codex Cloud",
            "https://developers.openai.com/codex/cloud",
            "https://learn.chatgpt.com/docs/cloud",
            "html",
            "OpenAI",
        ),
        (
            "codex/mcp",
            "codex",
            "mcp",
            "Codex Model Context Protocol",
            "https://developers.openai.com/codex/extend/mcp",
            "https://learn.chatgpt.com/docs/extend/mcp.md",
            "markdown",
            "OpenAI",
        ),
        (
            "codex/github-action",
            "codex",
            "github-action",
            "Codex GitHub Action",
            "https://developers.openai.com/codex/github-action",
            "https://learn.chatgpt.com/docs/github-action.md",
            "markdown",
            "OpenAI",
        ),
    )
)
_MANIFEST_SIZE: Final = 303
_PRODUCT_ENTRY_SIZES: Final[dict[Product, int]] = {
    "claude-code": 172,
    "codex": 131,
}
_SAFE_SLUG_RE: Final = re.compile(r"^[a-z0-9][a-z0-9-]*(?:/[a-z0-9][a-z0-9-]*)*$")


class Source(BaseModel):
    """Metadata row for one official page source."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True,
        extra="forbid",
        str_strip_whitespace=True,
    )

    id: SourceId
    product: Product
    slug: str
    title: str
    section: str
    canonical_url: str
    fetch_url: str
    fetch_format: FetchFormat
    owner: Owner

    @field_validator(
        "id",
        "product",
        "slug",
        "title",
        "section",
        "owner",
        "fetch_format",
        mode="after",
    )
    @classmethod
    def _non_empty(cls, value: str, info: ValidationInfo) -> str:
        if not value:
            message = f"{info.field_name} must be non-empty"
            raise ValueError(message)
        return value

    @field_validator("canonical_url", "fetch_url", mode="after")
    @classmethod
    def _require_https(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme != "https":
            msg = "source URLs must use HTTPS"
            raise ValueError(msg)
        if not parsed.netloc:
            msg = "source URLs must include a network location"
            raise ValueError(msg)
        return value

    @model_validator(mode="after")
    def _validate_id(self) -> Self:
        if self.id != SourceId(f"{self.product}/{self.slug}"):
            msg = "source id must match product and slug"
            raise ValueError(msg)
        if _SAFE_SLUG_RE.fullmatch(self.slug) is None:
            msg = "source slug must be a safe relative route"
            raise ValueError(msg)
        canonical_host = urlparse(self.canonical_url).hostname
        fetch_host = urlparse(self.fetch_url).hostname
        trusted_hosts = (
            {"code.claude.com"}
            if self.owner == "Anthropic"
            else {"developers.openai.com", "learn.chatgpt.com"}
        )
        if canonical_host not in trusted_hosts or fetch_host not in trusted_hosts:
            msg = "source URLs must use an owner-controlled host"
            raise ValueError(msg)
        return self


class SourceManifest(RootModel[tuple[Source, ...]]):
    """Tuple-backed manifest root container."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    @model_validator(mode="after")
    def _validate_manifest(self) -> Self:
        sources = self.root
        if len(sources) != _MANIFEST_SIZE:
            msg = "manifest must contain exactly 20 sources"
            raise ValueError(msg)

        ids = [source.id for source in sources]
        if len(set(ids)) != len(ids):
            msg = "source manifest contains duplicate id values"
            raise ValueError(msg)

        pairs = [(source.product, source.slug) for source in sources]
        if len(set(pairs)) != len(pairs):
            msg = "source manifest contains duplicate product/slug combinations"
            raise ValueError(msg)

        product_counts = Counter(source.product for source in sources)
        if any(
            product_counts[product] != expected
            for product, expected in _PRODUCT_ENTRY_SIZES.items()
        ):
            msg = "source manifest has the wrong product entry counts"
            raise ValueError(msg)

        return self


def _identity_tuple(source: Source) -> RowSpec:
    return (
        source.id,
        source.product,
        source.slug,
        source.title,
        source.canonical_url,
        source.fetch_url,
        source.fetch_format,
        source.owner,
    )


class FetchedPage(BaseModel):
    """Boundary object for fetch output."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    source_id: SourceId
    final_url: str
    content_type: str
    text: str

    @field_validator("final_url", mode="after")
    @classmethod
    def _validate_final_url(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme != "https":
            msg = "final_url must use HTTPS"
            raise ValueError(msg)
        if not parsed.netloc:
            msg = "final_url must include a network location"
            raise ValueError(msg)
        return value

    @field_validator("content_type", mode="after")
    @classmethod
    def _non_empty_content_type(cls, value: str, info: ValidationInfo) -> str:
        normalized = value.strip()
        if not normalized:
            message = f"{info.field_name} must be non-empty"
            raise ValueError(message)
        return normalized

    @field_validator("text", mode="after")
    @classmethod
    def _non_empty_text(cls, value: str, info: ValidationInfo) -> str:
        if not value:
            message = f"{info.field_name} must be non-empty"
            raise ValueError(message)
        if not value.strip():
            message = f"{info.field_name} must contain non-whitespace characters"
            raise ValueError(message)
        return value


@dataclass(frozen=True, slots=True)
class NormalizedPage:
    """Normalized page payload passed between fetch and write boundaries."""

    source: Source
    markdown: str
    content_sha256: str

# Copyright 2026
# ruff: noqa: INP001
"""Behavior tests for protecting Markdown during translation."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.ai.errors import AIAgentError, ErrorCode
from scripts.ai.protect import (
    ProtectedMarkdown,
    protect_markdown,
    restore_and_validate,
)

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "ai" / "fixtures"
FAILURE_MESSAGE = "translation validation failed"


def _fixture() -> tuple[str, str, ProtectedMarkdown]:
    source = (FIXTURES / "protected-input.md").read_text(encoding="utf-8")
    expected = (FIXTURES / "protected-output.md").read_text(encoding="utf-8")
    return source, expected, protect_markdown(source)


def _assert_translation_failure(
    source: str,
    protected: ProtectedMarkdown,
    translated: str,
) -> None:
    with pytest.raises(AIAgentError) as exc_info:
        _ = restore_and_validate(source, protected, translated)
    assert exc_info.value.code == ErrorCode.TRANSLATION_FAILED  # noqa: S101
    assert exc_info.value.source_id is None  # noqa: S101
    assert str(exc_info.value) == FAILURE_MESSAGE  # noqa: S101


def _assert_protection(
    source: str,
    expected_text: str,
    expected_originals: tuple[str, ...],
) -> None:
    protected = protect_markdown(source)
    assert protected.text == expected_text  # noqa: S101
    assert tuple(span.original for span in protected.spans) == expected_originals  # noqa: S101


def test_protect_markdown_matches_complete_golden_fixture() -> None:
    """Protect every required literal class in deterministic source order."""
    _source, expected, protected = _fixture()
    assert protected.text == expected  # noqa: S101
    assert tuple(span.placeholder for span in protected.spans) == tuple(  # noqa: S101
        f"⟦LEWISDOCS_{index:04d}⟧" for index in range(15)
    )
    assert tuple(span.original for span in protected.spans) == (  # noqa: S101
        "`codex --help`",
        '```bash\necho "synthetic"\n```\n',
        "https://example.test/docs",
        "./assets/agent.svg",
        "https://example.test/reference",
        "npm run ai:sync",
        "--dry-run",
        "MOONSHOT_API_KEY",
        "agent_config",
        "AGENTS.md",
        "./configs/prod.yaml",
        "Claude Code",
        "Codex CLI",
        "Moonshot API",
        "kimi-k3",
    )


def test_protects_fence_and_language_marker_as_one_span() -> None:
    """Protect a complete fenced block including its language marker."""
    _assert_protection(
        "before\n```python\nprint('x')\n```\nafter\n",
        "before\n⟦LEWISDOCS_0000⟧after\n",
        ("```python\nprint('x')\n```\n",),
    )


def test_protects_inline_code_with_delimiters() -> None:
    """Protect inline code including its Markdown delimiters."""
    _assert_protection(
        "Use `codex --help` now.",
        "Use ⟦LEWISDOCS_0000⟧ now.",
        ("`codex --help`",),
    )


def test_protects_bare_url() -> None:
    """Protect a URL outside a Markdown link."""
    _assert_protection(
        "Visit https://example.test/reference",
        "Visit ⟦LEWISDOCS_0000⟧",
        ("https://example.test/reference",),
    )


def test_protects_only_markdown_link_target() -> None:
    """Keep link text translatable while protecting its target."""
    _assert_protection(
        "Read [the guide](./docs/guide.md)",
        "Read [the guide](⟦LEWISDOCS_0000⟧)",
        ("./docs/guide.md",),
    )


def test_protects_command_and_option() -> None:
    """Protect the fixed sync command and a command-line option."""
    _assert_protection(
        "Run npm run ai:sync with --dry-run",
        "Run ⟦LEWISDOCS_0000⟧ with ⟦LEWISDOCS_0001⟧",
        ("npm run ai:sync", "--dry-run"),
    )


def test_protects_environment_variable() -> None:
    """Protect an uppercase environment variable identifier."""
    _assert_protection(
        "Set MOONSHOT_API_KEY",
        "Set ⟦LEWISDOCS_0000⟧",
        ("MOONSHOT_API_KEY",),
    )


def test_protects_filename_and_path() -> None:
    """Protect a filename and a slash-containing path."""
    _assert_protection(
        "Read AGENTS.md from ./configs/prod.yaml",
        "Read ⟦LEWISDOCS_0000⟧ from ⟦LEWISDOCS_0001⟧",
        ("AGENTS.md", "./configs/prod.yaml"),
    )


def test_protects_product_api_and_config_identifiers() -> None:
    """Protect known product/API names and an underscore config key."""
    _assert_protection(
        "Use Claude Code, Codex CLI, Moonshot API, kimi-k3, and agent_config",
        (
            "Use ⟦LEWISDOCS_0000⟧, ⟦LEWISDOCS_0001⟧, ⟦LEWISDOCS_0002⟧, "
            "⟦LEWISDOCS_0003⟧, and ⟦LEWISDOCS_0004⟧"
        ),
        ("Claude Code", "Codex CLI", "Moonshot API", "kimi-k3", "agent_config"),
    )


def test_restore_allows_prose_translation_and_restores_literals() -> None:
    """Permit translated prose when tokens and Markdown structure are intact."""
    source, _, protected = _fixture()
    translated = protected.text.replace(
        "# Synthetic handbook",
        "# 合成手册",
    ).replace("Run ", "运行 ")
    restored = restore_and_validate(source, protected, translated)
    assert "# 合成手册" in restored  # noqa: S101
    assert "运行 npm run ai:sync" in restored  # noqa: S101
    assert all(span.original in restored for span in protected.spans)  # noqa: S101


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "duplicate",
        "reordered",
        "unknown",
    ],
)
def test_restore_rejects_token_mutations(mutation: str) -> None:
    """Reject missing, duplicate, reordered, or invented placeholders."""
    source, _, protected = _fixture()
    first, second = protected.spans[0].placeholder, protected.spans[1].placeholder
    if mutation == "missing":
        translated = protected.text.replace(first, "", 1)
    elif mutation == "duplicate":
        translated = protected.text + first
    elif mutation == "reordered":
        translated = protected.text.replace(first, "TEMP", 1)
        translated = translated.replace(second, first, 1).replace("TEMP", second, 1)
    else:
        translated = protected.text + "⟦LEWISDOCS_9999⟧"
    _assert_translation_failure(source, protected, translated)


@pytest.mark.parametrize(
    ("before", "after"),
    [
        ("# Synthetic handbook", "## Synthetic handbook"),
        ("- list item", "  - list item"),
        ("> quoted note", ">> quoted note"),
        ("| --- | --- |", "| --- |"),
    ],
)
def test_restore_rejects_markdown_structure_changes(before: str, after: str) -> None:
    """Reject changes to headings, lists, blockquotes, and table shape."""
    source, _, protected = _fixture()
    _assert_translation_failure(
        source,
        protected,
        protected.text.replace(before, after, 1),
    )


def test_restore_rejects_new_protected_literal() -> None:
    """Reject a translated payload that invents a protected identifier."""
    source, _, protected = _fixture()
    translated = protected.text.replace("plain prose", "NEW_CONFIG")
    _assert_translation_failure(source, protected, translated)

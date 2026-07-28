# Copyright 2026
# ruff: noqa: INP001,S101

"""Tests for content-aware English publication."""

from scripts.ai.sync_english import _semantic_content


def test_semantic_content_ignores_presentation_and_link_target_changes() -> None:
    """Formatting-only source updates do not invalidate an existing translation."""
    old = "## Install\n\n- Read [the guide](https://old.example/docs).\n"
    new = "# Install\n\nRead **[the guide](https://new.example/docs)**.\n"
    assert _semantic_content(old) == _semantic_content(new)


def test_semantic_content_detects_visible_text_and_code_changes() -> None:
    """Visible instructions and code remain part of the comparison basis."""
    old = "Run `codex --safe` after installation."
    changed_text = "Run `codex --full-auto` after installation."
    changed_instruction = "Run `codex --safe` before installation."
    assert _semantic_content(old) != _semantic_content(changed_text)
    assert _semantic_content(old) != _semantic_content(changed_instruction)

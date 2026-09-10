# Copyright 2026
# ruff: noqa: INP001,RUF001,S101

"""Tests for content-aware English publication."""

from hashlib import sha256
from pathlib import Path

from scripts.ai.manifest import load_sources
from scripts.ai.pages import (
    render_english_page,
    render_official_chinese_page,
)
from scripts.ai.sync_english import _preserved_translation, _semantic_content
from scripts.ai.types import NormalizedPage

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = load_sources(ROOT / "source-ai" / "sources.yaml")


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


def test_content_refresh_preserves_official_localization_metadata(tmp_path: Path) -> None:
    """Keep owner-published localization provenance across safe English refreshes."""
    source = MANIFEST.root[0]
    markdown = f"# {source.title}\n\nShort source prose.\n"
    page = NormalizedPage(
        source=source,
        markdown=markdown,
        content_sha256=sha256(markdown.encode()).hexdigest(),
    )
    localized = (
        f"# {source.title}\n\n"
        "这是内容所有者发布的官方简体中文正文，用于确认英文内容刷新后仍保留官方本地化来源，"
        "而不会把页面错误地降级为模型生成的译文或重新添加人工智能翻译警告。"
        "这段文字也提供足够的中文内容用于页面边界验证。\n"
    )
    translation_url = source.canonical_url.replace("/docs/en/", "/docs/zh-CN/")
    english_path = tmp_path / "en" / source.product / f"{source.slug}.md"
    chinese_path = tmp_path / "zh-CN" / source.product / f"{source.slug}.md"
    english_path.parent.mkdir(parents=True)
    chinese_path.parent.mkdir(parents=True)
    _ = english_path.write_bytes(render_english_page(page))
    expected = render_official_chinese_page(
        page,
        localized,
        translation_url=translation_url,
    )
    _ = chinese_path.write_bytes(expected)

    assert _preserved_translation(tmp_path, page) == expected

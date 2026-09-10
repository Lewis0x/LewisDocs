# Copyright 2026
# ruff: noqa: EM101,INP001,RUF001,S101,TRY003

"""Private accepted-content materialization tests."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

import scripts.ai.materialize as materialize_module
from scripts.ai.errors import AIAgentError, ErrorCode
from scripts.ai.learning import load_learning_bundles
from scripts.ai.manifest import load_sources
from scripts.ai.materialize import (
    MaterializeOptions,
    _localize_chinese_attribution,
    _rewrite_localized_same_page_anchors,
    _strip_mdx_components,
    derive_review_pair,
    materialize_ai,
)
from scripts.ai.types import SourceId
from tests.ai.fixture_support import install_content, normalized_pages

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "source-ai" / "sources.yaml"


def _options(tmp_path: Path, content_root: Path) -> MaterializeOptions:
    repo = tmp_path / "repo"
    repo.mkdir(exist_ok=True)
    return MaterializeOptions(
        repo_root=repo,
        content_root=content_root,
        docs_ai_root=repo / "docs" / "ai",
        manifest_path=MANIFEST_PATH,
    )


def _frontmatter_and_body(data: bytes) -> tuple[tuple[str, ...], bytes]:
    closing = data.index(b"\n---\n", len(b"---\n"))
    fields = tuple(data[len(b"---\n") : closing].decode("utf-8").splitlines())
    return fields, data[closing + len(b"\n---\n") :]


def test_derives_exact_bilingual_review_pair() -> None:
    """Expose the public-shape derivation used before semantic review."""
    english = (
        "---\n"
        "title: Settings\n"
        "source_id: codex/settings\n"
        "product: codex\n"
        "lang: en\n"
        "canonical_url: https://example.test/settings\n"
        "owner: OpenAI\n"
        f"content_sha256: {'a' * 64}\n"
        "---\n"
        "# Settings\n\n"
        "See [details](#details).\n\n"
        "## Details\n"
    ).encode()
    chinese = (
        "---\n"
        "title: 设置\n"
        "source_id: codex/settings\n"
        "product: codex\n"
        "lang: zh-CN\n"
        "canonical_url: https://example.test/settings\n"
        "owner: OpenAI\n"
        f"content_sha256: {'a' * 64}\n"
        "translation_of: codex/settings\n"
        "translation_model: glm-5.2\n"
        "ai_translated: true\n"
        "---\n"
        "# 设置\n\n"
        "查看[详情](#details)。\n\n"
        "## 详情\n"
    ).encode()

    public_english, public_chinese = derive_review_pair(
        SourceId("codex/settings"),
        english,
        chinese,
    )

    assert b"title: EN \xc2\xb7 Settings" in public_english
    assert b"ai_counterpart: /ai/zh-CN/codex/settings" in public_english
    assert (b"title: \xe4\xb8\xad\xe6\x96\x87 \xc2\xb7 \xe8\xae\xbe\xe7\xbd\xae") in public_chinese
    assert b"ai_counterpart: /ai/en/codex/settings" in public_chinese
    assert "#详情".encode() in public_chinese


def test_rewrites_source_fragments_to_localized_heading_anchors() -> None:
    """Keep translated same-page links aligned with VitePress heading ids."""
    english = """\
## Known limitations

See [details](#known-limitations).

## Accept edits mode (`acceptEdits`)
"""
    chinese = """\
## 已知限制

参见[详细信息](#known-limitations)。
`[literal](#known-limitations)`

```md
[example](#known-limitations)
```

## 接受编辑模式 (`acceptEdits`)

参见[模式](#accept-edits-mode-acceptedits)。
"""

    rewritten = _rewrite_localized_same_page_anchors(chinese, english)

    assert "参见[详细信息](#已知限制)。" in rewritten
    assert "参见[模式](#接受编辑模式-acceptedits)。" in rewritten
    assert "`[literal](#known-limitations)`" in rewritten
    assert "[example](#known-limitations)" in rewritten


def test_rewrites_percent_encoded_source_fragments() -> None:
    """Normalize encoded source anchors before applying localized ids."""
    english = """\
## Running `/recap`
"""
    chinese = """\
## Recap command

[Run](#running-%2Frecap)
"""

    rewritten = _rewrite_localized_same_page_anchors(chinese, english)

    assert "[Run](#recap-command)" in rewritten


def test_localizes_legacy_chinese_attribution_in_public_shape() -> None:
    """Migrate legacy labels while preserving the canonical URL and owner."""
    markdown = (
        "\n---\n"
        "本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。\n\n"
        "[Official source](https://example.test/docs/page)\n\n"
        "Content owner: Anthropic\n\n"
        "# 中文标题\n"
    )

    localized = _localize_chinese_attribution(markdown)

    assert "[官方来源](https://example.test/docs/page)" in localized
    assert "内容所有者: Anthropic" in localized
    assert "Official source" not in localized
    assert "Content owner" not in localized
    assert localized.endswith("# 中文标题\n")


def test_materialize_preserves_explicit_html_heading_hierarchy() -> None:
    """Convert owner-published HTML headings without touching fenced examples."""
    markdown = """\
<h2 id="choose-an-approach">
  选择一种方法
</h2>

```html
<h2 id="example">Example only</h2>
```

<h3 id="capture-the-session-id">捕获会话 ID</h3>
"""

    public = _strip_mdx_components(markdown)

    assert public.startswith("## 选择一种方法 {#choose-an-approach}\n")
    assert "### 捕获会话 ID {#capture-the-session-id}\n" in public
    assert '<h2 id="example">Example only</h2>' in public


def test_materialize_converts_html_images_without_corrupting_attributes() -> None:
    """Convert publishable HTML images while preserving fenced examples."""
    markdown = """\
<img src="https://example.test/image.png?q=1" alt="Example image" width="16" />

```html
<img src="https://example.test/example.png" alt="Example only" />
```
"""

    public = _strip_mdx_components(markdown)

    assert "![Example image](https://example.test/image.png?q=1)" in public
    assert '<img src="https://example.test/example.png" alt="Example only" />' in public
    assert '" alt=)' not in public


def test_materialize_dedents_nested_mdx_container_bodies() -> None:
    """Keep stripped Steps and Tabs content as prose and fenced code."""
    markdown = """\
<Steps>
  <Step title="Run it">
    Paragraph.

    * Item

    ```bash
    echo ok
    ```
  </Step>
</Steps>

<Tabs>
  <Tab title="Example">
    Tab paragraph.
  </Tab>
</Tabs>

```md
<Step title="Literal">
    Keep this indentation.
</Step>
```
"""

    public = _strip_mdx_components(markdown)

    assert "\nParagraph.\n\n* Item\n\n```bash\necho ok\n```\n" in public
    assert "\nTab paragraph.\n" in public
    assert '<Step title="Literal">\n    Keep this indentation.\n</Step>' in public
    assert "\n    Paragraph." not in public
    assert "\n    Tab paragraph." not in public


def test_materialize_dedents_lowercase_html_container_bodies() -> None:
    """Do not leave indented code blocks after presentational HTML is stripped."""
    markdown = """\
<div>
  <div>
    <span>Title</span>
  </div>
  <p>Paragraph</p>
</div>
"""

    public = _strip_mdx_components(markdown)

    assert "Title\n" in public
    assert "Paragraph\n" in public
    assert "\n    Title" not in public
    assert "\n  Paragraph" not in public


def test_materialize_dedents_orphan_prose_blocks() -> None:
    """Recover prose whose wrapper was removed before the final cleanup pass."""
    markdown = """\
## Pets

    Paragraph one
    continuation
"""

    public = _strip_mdx_components(markdown)

    assert public == "## Pets\n\nParagraph one\ncontinuation\n"


def test_materialize_preserves_list_continuations() -> None:
    """Keep indentation that belongs to an active Markdown list item."""
    markdown = """\
1. Item
   continuation

   second paragraph
"""

    public = _strip_mdx_components(markdown)

    assert public == markdown


def test_materialize_preserves_fenced_code_indentation() -> None:
    """Never normalize indentation inside fenced examples."""
    markdown = """\
```python
    print("nested")
```
"""

    public = _strip_mdx_components(markdown)

    assert public == markdown


def test_materialize_normalizes_multiline_markdown_table_cells() -> None:
    """Preserve paragraph boundaries while making owner tables parse in VitePress."""
    markdown = """\
| Flag | Description | Example |
| --- | --- | --- |
| `--name` | Set a display name.

`/rename` changes it later | `claude -n demo` |
| `--print` | Print the response | `claude -p hi` |
"""

    public = _strip_mdx_components(markdown)

    assert (
        "| `--name` | Set a display name.<br><br>`/rename` changes it later | `claude -n demo` |\n"
    ) in public
    assert "| `--print` | Print the response | `claude -p hi` |\n" in public
    assert "Set a display name.\n\n`/rename`" not in public


def test_materialize_does_not_normalize_table_examples_in_fences() -> None:
    """Table adaptation never changes literal examples."""
    markdown = """\
```md
| Flag | Description |
| --- | --- |
| `--name` | First paragraph.

Second paragraph |
```
"""

    public = _strip_mdx_components(markdown)

    assert public == markdown


@pytest.mark.parametrize("kind", ["missing", "tracked_docs"])
def test_materialize_rejects_missing_or_nonprivate_content_root(
    tmp_path: Path,
    kind: str,
) -> None:
    """Given an invalid accepted root, when materialized, then validation fails."""
    # Given
    options = _options(tmp_path, tmp_path / "missing")
    if kind == "tracked_docs":
        options = MaterializeOptions(
            repo_root=REPO_ROOT,
            content_root=REPO_ROOT / "docs",
            docs_ai_root=tmp_path / "derived",
            manifest_path=MANIFEST_PATH,
        )

    # When / Then
    with pytest.raises(AIAgentError) as exc_info:
        _ = materialize_ai(options)
    assert exc_info.value.code == ErrorCode.VALIDATION_FAILED


def test_materialize_derives_exact_routes_and_preserves_accepted_content(
    tmp_path: Path,
) -> None:
    """Given 22 accepted pages, when derived, then routes and byte contracts are exact."""
    # Given
    manifest = load_sources(MANIFEST_PATH)
    content = tmp_path / "private"
    install_content(content, normalized_pages(manifest))
    options = _options(tmp_path, content)
    accepted_source_bytes = {
        (lang, source.id): (content / lang / source.product / f"{source.slug}.md").read_bytes()
        for source in manifest.root
        for lang in ("en", "zh-CN")
    }
    # When
    routes = materialize_ai(options)

    # Then
    assert len(routes) == len(manifest.root) * 2 + 2
    assert {route.route for route in routes} == {
        *{
            f"/ai/{lang}/{source.product}/{source.slug}"
            for source in manifest.root
            for lang in ("en", "zh-CN")
        },
        "/ai/learn/claude-code",
        "/ai/learn/codex",
    }
    by_route = {route.route: route for route in routes}
    for source in manifest.root:
        en_route = f"/ai/en/{source.product}/{source.slug}"
        zh_route = f"/ai/zh-CN/{source.product}/{source.slug}"
        assert by_route[en_route].counterpart == zh_route
        assert by_route[zh_route].counterpart == en_route
        assert by_route[en_route].source_id == source.id
        assert by_route[zh_route].source_id == source.id
        for lang, prefix, label, counterpart in (
            ("en", "EN · ", "EN", zh_route),
            ("zh-CN", "中文 · ", "中文", en_route),
        ):
            original = accepted_source_bytes[(lang, source.id)]
            derived = (
                options.docs_ai_root / lang / source.product / f"{source.slug}.md"
            ).read_bytes()
            original_fields, original_body = _frontmatter_and_body(original)
            derived_fields, derived_body = _frontmatter_and_body(derived)
            assert derived_body == original_body
            assert (
                derived_fields[0] == f"title: {prefix}{original_fields[0].removeprefix('title: ')}"
            )
            assert set(derived_fields[1:]) == {
                *original_fields[1:],
                f"ai_counterpart: {counterpart}",
                f"ai_search_label: {label}",
            }
    for product in ("claude-code", "codex"):
        route = by_route[f"/ai/learn/{product}"]
        assert route.source_id is None
        assert route.lang == "bilingual"
        assert route.counterpart is None
        learning = (options.docs_ai_root / "learn" / f"{product}.md").read_text(encoding="utf-8")
        assert f'<AiLearningPath product="{product}" />' in learning
        assert "ai_learning: true" in learning
        assert not (options.docs_ai_root / "zh-CN" / "learn" / f"{product}.md").exists()
    translation_status = json.loads(
        (options.docs_ai_root / "translation-status.json").read_text(
            encoding="utf-8",
        )
    )
    assert translation_status == {
        "version": 1,
        "source_ids": sorted(str(source.id) for source in manifest.root),
    }
    homepage = (options.repo_root / "docs" / "index.md").read_text(encoding="utf-8")
    assert f"<strong>{len(manifest.root)}</strong><span>篇官方文档</span>" in homepage
    assert homepage.count('href="/ai/learn/claude-code"') == 1
    assert homepage.count('href="/ai/learn/codex"') == 1
    assert "/ai/zh-CN/learn/" not in homepage
    assert "[通用 CAD 平台 API 设计哲学](/appendix/cad)" in homepage
    assert not tuple(options.docs_ai_root.parent.glob(".ai-backup-*"))
    assert not tuple((options.repo_root / ".ai-local").glob(".ai-retired-*"))


def test_materialize_publishes_all_english_and_only_available_chinese(
    tmp_path: Path,
) -> None:
    """Keep existing Chinese pages live while a larger English set is reviewed."""
    manifest = load_sources(MANIFEST_PATH)
    content = tmp_path / "private"
    pages = normalized_pages(manifest)
    install_content(content, pages)
    missing = manifest.root[-1]
    (content / "zh-CN" / missing.product / f"{missing.slug}.md").unlink()
    for product in ("claude-code", "codex"):
        routes = "\n".join(
            f"- [Page](/ai/zh-CN/{page.source.product}/{page.source.slug})"
            for page in pages
            if page.source.product == product and page.source.id != missing.id
        )
        _ = (content / "learn" / "zh-CN" / f"{product}.md").write_text(
            f"# Learning\n\n{routes}\n",
            encoding="utf-8",
            newline="\n",
        )
    options = _options(tmp_path, content)

    routes = materialize_ai(options)
    by_route = {route.route: route for route in routes}
    missing_en = f"/ai/en/{missing.product}/{missing.slug}"
    missing_zh = f"/ai/zh-CN/{missing.product}/{missing.slug}"

    assert len(routes) == len(manifest.root) * 2 + 1
    assert missing_en in by_route
    assert by_route[missing_en].counterpart is None
    assert missing_zh not in by_route
    assert not (options.docs_ai_root / "zh-CN" / missing.product / f"{missing.slug}.md").exists()
    translation_status = json.loads(
        (options.docs_ai_root / "translation-status.json").read_text(
            encoding="utf-8",
        )
    )
    assert str(missing.id) not in translation_status["source_ids"]


def test_fixture_learning_paths_are_readable_spec_examples() -> None:
    """Keep the canonical learning data complete and bilingual."""
    manifest = load_sources(MANIFEST_PATH)
    bundles = load_learning_bundles(REPO_ROOT / "source-ai" / "learning", manifest)

    assert [bundle.path.product for bundle in bundles] == ["claude-code", "codex"]
    assert all(bundle.en.summary and bundle.zh_cn.summary for bundle in bundles)


def test_materialize_keeps_previous_tree_when_copy_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Given a live derived tree, when staging copy fails, then the live bytes survive."""
    # Given
    manifest = load_sources(MANIFEST_PATH)
    content = tmp_path / "private"
    install_content(content, normalized_pages(manifest))
    options = _options(tmp_path, content)
    sentinel = options.docs_ai_root / "sentinel.md"
    sentinel.parent.mkdir(parents=True)
    _ = sentinel.write_bytes(b"previous\n")
    homepage = options.repo_root / "docs" / "index.md"
    _ = homepage.write_bytes(b"previous homepage\n")

    def fail_populate(
        staged: Path,
        content_root: Path,
        routes: object,
        learning: object,
    ) -> None:
        del staged, content_root, routes, learning
        raise OSError("controlled copy failure")

    monkeypatch.setattr(materialize_module, "_populate", fail_populate)

    # When / Then
    with pytest.raises(AIAgentError) as exc_info:
        _ = materialize_ai(options)
    assert exc_info.value.code == ErrorCode.WRITE_FAILED
    assert sentinel.read_bytes() == b"previous\n"
    assert homepage.read_bytes() == b"previous homepage\n"


def test_materialize_rolls_back_tree_when_homepage_write_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Keep the previous AI tree when the derived homepage cannot be promoted."""
    manifest = load_sources(MANIFEST_PATH)
    content = tmp_path / "private"
    install_content(content, normalized_pages(manifest))
    options = _options(tmp_path, content)
    sentinel = options.docs_ai_root / "sentinel.md"
    sentinel.parent.mkdir(parents=True)
    _ = sentinel.write_bytes(b"previous\n")
    homepage = options.repo_root / "docs" / "index.md"
    _ = homepage.write_bytes(b"previous homepage\n")

    def fail_homepage(repo_root: Path, source_manifest: object) -> None:
        del repo_root, source_manifest
        raise AIAgentError(
            code=ErrorCode.WRITE_FAILED,
            message="controlled homepage failure",
        )

    monkeypatch.setattr(materialize_module, "_write_homepage", fail_homepage)

    with pytest.raises(AIAgentError) as exc_info:
        _ = materialize_ai(options)
    assert exc_info.value.code == ErrorCode.WRITE_FAILED
    assert sentinel.read_bytes() == b"previous\n"
    assert homepage.read_bytes() == b"previous homepage\n"


def test_materialize_keeps_promoted_tree_when_retired_backup_cleanup_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Given cleanup partially fails after promotion, then the complete new tree stays live."""
    # Given
    manifest = load_sources(MANIFEST_PATH)
    content = tmp_path / "private"
    install_content(content, normalized_pages(manifest))
    options = _options(tmp_path, content)
    sentinel = options.docs_ai_root / "sentinel.md"
    sentinel.parent.mkdir(parents=True)
    _ = sentinel.write_bytes(b"previous\n")
    real_rmtree = shutil.rmtree
    cleanup_failed = False

    def fail_retired_cleanup(path: Path) -> None:
        nonlocal cleanup_failed
        cleanup_path = Path(path)
        if not cleanup_failed and cleanup_path.name.startswith((".ai-backup-", ".ai-retired-")):
            cleanup_failed = True
            first_page = next(cleanup_path.rglob("*.md"))
            first_page.unlink()
            raise OSError("controlled retired-backup cleanup failure")
        real_rmtree(cleanup_path)

    monkeypatch.setattr(shutil, "rmtree", fail_retired_cleanup)

    # When
    with pytest.raises(AIAgentError) as exc_info:
        _ = materialize_ai(options)

    # Then
    assert exc_info.value.code == ErrorCode.WRITE_FAILED
    assert cleanup_failed
    assert not sentinel.exists()
    assert len(tuple(options.docs_ai_root.rglob("*.md"))) == len(manifest.root) * 2 + 2
    assert not tuple(options.docs_ai_root.parent.glob(".ai-backup-*"))
    retired = tuple((options.repo_root / ".ai-local").glob(".ai-retired-*"))
    assert len(retired) == 1

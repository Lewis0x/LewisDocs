# Copyright 2026

"""Public accepted-content materialization boundary."""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
import tempfile
import uuid
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final, NoReturn, cast
from urllib.parse import unquote

from scripts.ai.errors import AIAgentError, ErrorCode
from scripts.ai.learning import LearningBundle, load_learning_bundles
from scripts.ai.manifest import load_sources
from scripts.ai.page_format import WARNING
from scripts.ai.pages import validate_publishable_candidate
from scripts.ai.protect import protect_markdown
from scripts.ai.sync_contracts import SyncOptions
from scripts.ai.sync_transaction import validate_content_root
from scripts.rewrite_links import vitepress_slugify

if TYPE_CHECKING:
    from scripts.ai.types import SourceId, SourceManifest

_FRONTMATTER_END: Final = b"\n---\n"
_MDX_COMPONENT_RE: Final = re.compile(r"(?ms)</?[A-Z][A-Za-z0-9]*(?:\s+[^<>]*?)?\s*/?>")
_MDX_BLOCK_OPEN_PREFIX: Final = r"^(?P<indent>[ \t]*)<(?P<tag>[A-Za-z][A-Za-z0-9]*)\b"
_MDX_BLOCK_OPEN_SUFFIX: Final = r"(?P<attributes>[^<>]*?)(?P<selfclose>/?)>(?P<tail>.*)$"
_MDX_BLOCK_OPEN_RE: Final = re.compile(f"{_MDX_BLOCK_OPEN_PREFIX}{_MDX_BLOCK_OPEN_SUFFIX}")
_MDX_BLOCK_CLOSE_RE: Final = re.compile(r"^[ \t]*</(?P<tag>[A-Za-z][A-Za-z0-9]*)>[ \t]*$")
_MDX_COMMENT_RE: Final = re.compile(r"(?s)\{/\*.*?\*/\}")
_MDX_ICON_SLOT_RE: Final = re.compile(r'(?ms)\s*<span\s+slot="icon">.*?</span>\s*')
_UNSAFE_HTML_RE: Final = re.compile(
    r"(?is)<(?:script|style)\b[^>]*(?:/>|>.*?</(?:script|style)\s*>)"
)
_JSX_STYLE_RE: Final = re.compile(r"\s+style=\{\{[^{}]*\}\}")
_HTML_IMAGE_RE: Final = re.compile(r"(?is)<img\b[^>]*>")
_HTML_ATTRIBUTE_RE: Final = re.compile(r"""(?i)\b(src|alt)=["']([^"']*)["']""")
_HTML_BREAK_RE: Final = re.compile(r"(?i)<br\s*/?>")
_HTML_TAG_RE: Final = re.compile(r"(?is)</?[A-Za-z][^>]*>")
_EXPLICIT_HTML_HEADING_RE: Final = re.compile(
    r"(?ims)^[ \t]*<h(?P<level>[1-6])\b(?P<attributes>[^>]*)>"
    r"[ \t]*(?P<title>.*?)[ \t]*</h(?P=level)>[ \t]*(?:\n|$)"
)
_EXPLICIT_HTML_HEADING_ID_RE: Final = re.compile(
    r"\bid\s*=\s*(?P<quote>[\"'])(?P<anchor>[^\"'\s>{}]+)(?P=quote)",
    re.IGNORECASE,
)
_ROOT_IMAGE_RE: Final = re.compile(r"(!\[[^\]]*]\()(/[^)\s]+)")
_HEADING_RE: Final = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*$")
_CUSTOM_HEADING_ANCHOR_RE: Final = re.compile(r"[ \t]+\{#([^}\s]+)\}[ \t]*$")
_INLINE_LINK_RE: Final = re.compile(r"!?\[([^\]]*)]\([^)\r\n]*\)")
_INLINE_HTML_RE: Final = re.compile(r"<[^>\r\n]+>")
_FENCE_RE: Final = re.compile(r"^\s*(`{3,}|~{3,})")
_TABLE_DELIMITER_CELL_RE: Final = re.compile(r"^:?-{3,}:?$")
_TABLE_MIN_COLUMNS: Final = 2
_LIST_ITEM_RE: Final = re.compile(r"^([ \t]*)(?:>[ \t]*)*(?:[-+*] |\d+[.)] )")
_SAME_PAGE_FRAGMENT_RE: Final = re.compile(r"(?P<prefix>]\()#(?P<fragment>[^)\s]+)")
_LEGACY_CHINESE_ATTRIBUTION_RE: Final = re.compile(
    "".join(
        (
            rf"\A(?P<prefix>\n---\n{re.escape(WARNING)}\n\n)",
            r"\[Official source\](?P<url>\([^\r\n)]+\))\n\n",
            r"Content owner: (?P<owner>[^\r\n]+)\n\n",
        )
    )
)
_INDENTED_CODE_WIDTH: Final = 4


@dataclass(frozen=True, slots=True)
class MaterializeOptions:
    """Paths required to derive public AI documentation."""

    repo_root: Path
    content_root: Path
    docs_ai_root: Path
    manifest_path: Path
    learning_root: Path | None = None


@dataclass(frozen=True, slots=True)
class MaterializedRoute:
    """One derived VitePress route."""

    source_id: SourceId | None
    lang: str
    route: str
    counterpart: str | None


@dataclass(frozen=True, slots=True)
class _SwapState:
    backed_up: bool
    promoted: bool


@dataclass(frozen=True, slots=True)
class _HomepageState:
    existed: bool
    data: bytes


@dataclass(frozen=True, slots=True)
class _RollbackTargets:
    repo_root: Path
    target: Path
    staged: Path
    backup: Path


def materialize_ai(options: MaterializeOptions) -> tuple[MaterializedRoute, ...]:
    """Derive validated public content into the VitePress source tree."""
    content_root = _validated_content_root(options)
    manifest = load_sources(options.manifest_path)
    learning_root = (
        options.learning_root
        if options.learning_root is not None
        else options.manifest_path.parent / "learning"
    )
    learning = load_learning_bundles(learning_root, manifest)
    translated = validate_publishable_candidate(
        managed_root=content_root,
        manifest=manifest,
    )
    _require_derived_target(options)
    source_routes = tuple(
        MaterializedRoute(
            source_id=source.id,
            lang=lang,
            route=f"/ai/{lang}/{source.product}/{source.slug}",
            counterpart=(
                f"/ai/{'zh-CN' if lang == 'en' else 'en'}/{source.product}/{source.slug}"
                if source.id in translated
                else None
            ),
        )
        for source in manifest.root
        for lang in (("en", "zh-CN") if source.id in translated else ("en",))
    )
    learning_routes = tuple(
        MaterializedRoute(
            source_id=None,
            lang="bilingual",
            route=f"/ai/learn/{bundle.path.product}",
            counterpart=None,
        )
        for bundle in learning
    )
    routes = source_routes + learning_routes
    _replace_derived_tree(options, content_root, routes, learning, manifest)
    return routes


def derive_review_pair(
    source_id: SourceId,
    english_data: bytes,
    chinese_data: bytes,
) -> tuple[bytes, bytes]:
    """Derive one bilingual pair in the exact public Markdown shape."""
    product, separator, slug = str(source_id).partition("/")
    if not separator or product not in {"claude-code", "codex"} or not slug or ".." in slug:
        _validation_failed()
    english_route = MaterializedRoute(
        source_id=source_id,
        lang="en",
        route=f"/ai/en/{product}/{slug}",
        counterpart=f"/ai/zh-CN/{product}/{slug}",
    )
    chinese_route = MaterializedRoute(
        source_id=source_id,
        lang="zh-CN",
        route=f"/ai/zh-CN/{product}/{slug}",
        counterpart=f"/ai/en/{product}/{slug}",
    )
    return (
        _derive_source_page(english_data, english_route),
        _derive_source_page(
            chinese_data,
            chinese_route,
            english_data,
        ),
    )


def main() -> int:
    """Run materialization from the repository environment."""
    repo_root = Path(__file__).resolve().parents[2]
    content_value = os.environ.get("AI_CONTENT_ROOT")
    if content_value is None or not content_value.strip():
        _validation_failed()
    content_root = Path(content_value)
    if not content_root.is_absolute():
        _validation_failed()
    try:
        routes = materialize_ai(
            MaterializeOptions(
                repo_root=repo_root,
                content_root=content_root,
                docs_ai_root=repo_root / "docs" / "ai",
                manifest_path=repo_root / "source-ai" / "sources.yaml",
            )
        )
    except AIAgentError as error:
        _ = sys.stderr.write(f"{error.code}: AI handbook materialization failed\n")
        return 1
    _ = sys.stdout.write(f"materialized {len(routes)} AI handbook routes\n")
    return 0


def _validated_content_root(options: MaterializeOptions) -> Path:
    sync_options = SyncOptions(
        repo_root=options.repo_root,
        content_root=options.content_root,
        staging_root=options.repo_root / ".ai-local" / "staging",
        manifest_path=options.manifest_path,
        report_path=options.repo_root / ".ai-local" / "report.json",
    )
    return validate_content_root(sync_options)


def _require_derived_target(options: MaterializeOptions) -> None:
    expected = (options.repo_root / "docs" / "ai").resolve(strict=False)
    try:
        actual = options.docs_ai_root.resolve(strict=False)
    except OSError:
        _validation_failed()
    if actual != expected or options.docs_ai_root.is_symlink():
        _validation_failed()


def _replace_derived_tree(
    options: MaterializeOptions,
    content_root: Path,
    routes: tuple[MaterializedRoute, ...],
    learning: tuple[LearningBundle, ...],
    manifest: SourceManifest,
) -> None:
    target = options.docs_ai_root
    parent = target.parent
    try:
        parent.mkdir(parents=True, exist_ok=True)
        staged = Path(tempfile.mkdtemp(prefix=".ai-materialize-", dir=parent))
    except OSError:
        _write_failed()
    swap_id = uuid.uuid4().hex
    backup = parent / f".ai-backup-{swap_id}"
    retired = options.repo_root / ".ai-local" / f".ai-retired-{swap_id}"
    rollback_targets = _RollbackTargets(
        repo_root=options.repo_root,
        target=target,
        staged=staged,
        backup=backup,
    )
    backed_up = False
    promoted = False
    homepage_state: _HomepageState | None = None
    try:
        _populate(staged, content_root, routes, learning)
        if target.exists():
            _ = target.replace(backup)
            backed_up = True
        _ = staged.replace(target)
        promoted = True
        homepage_state = _write_homepage(options.repo_root, manifest)
    except AIAgentError:
        _rollback_materialization(
            rollback_targets,
            _SwapState(backed_up=backed_up, promoted=promoted),
            homepage_state,
        )
        raise
    except OSError:
        _rollback_materialization(
            rollback_targets,
            _SwapState(backed_up=backed_up, promoted=promoted),
            homepage_state,
        )
        _write_failed()
    if not backed_up:
        return
    try:
        retired.parent.mkdir(parents=True, exist_ok=True)
        _ = backup.replace(retired)
    except OSError:
        _rollback_materialization(
            rollback_targets,
            _SwapState(backed_up=True, promoted=True),
            homepage_state,
        )
        _write_failed()
    try:
        shutil.rmtree(retired)
    except OSError:
        _write_failed()


def _rollback_materialization(
    targets: _RollbackTargets,
    state: _SwapState,
    homepage_state: _HomepageState | None,
) -> None:
    _rollback(targets.target, targets.staged, targets.backup, state)
    if homepage_state is not None:
        _restore_homepage(targets.repo_root, homepage_state)


def _populate(
    staged: Path,
    content_root: Path,
    routes: tuple[MaterializedRoute, ...],
    learning: tuple[LearningBundle, ...],
) -> None:
    learning_by_product = {bundle.path.product: bundle for bundle in learning}
    translated_source_ids = sorted(
        str(item.source_id)
        for item in routes
        if item.source_id is not None and item.lang == "zh-CN"
    )
    _ = (staged / "translation-status.json").write_text(
        json.dumps(
            {"version": 1, "source_ids": translated_source_ids},
            ensure_ascii=False,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    for item in routes:
        relative = item.route.removeprefix("/ai/")
        destination = staged / f"{relative}.md"
        destination.parent.mkdir(parents=True, exist_ok=True)
        if item.source_id is None:
            product = item.route.rsplit("/", maxsplit=1)[1]
            bundle = learning_by_product.get(product)
            if bundle is None:
                _validation_failed()
            _ = destination.write_bytes(_derive_learning_page(bundle))
            continue
        product, slug = str(item.source_id).split("/", maxsplit=1)
        source = content_root / item.lang / product / f"{slug}.md"
        english = content_root / "en" / product / f"{slug}.md" if item.lang == "zh-CN" else None
        _ = destination.write_bytes(
            _derive_source_page(
                source.read_bytes(),
                item,
                english.read_bytes() if english is not None else None,
            )
        )


def _derive_learning_page(bundle: LearningBundle) -> bytes:
    product = bundle.path.product
    title = f"{bundle.zh_cn.title} / {bundle.en.title}"
    return (
        "---\n"
        f"title: {title}\n"
        f"product: {product}\n"
        "ai_learning: true\n"
        "sidebar: false\n"
        "aside: false\n"
        "outline: false\n"
        "prev: false\n"
        "next: false\n"
        "pageClass: ai-learning-page\n"
        "---\n"
        f'<AiLearningPath product="{product}" />\n'
    ).encode()


def _write_homepage(repo_root: Path, manifest: SourceManifest) -> _HomepageState:
    """Regenerate the AI-first homepage after the legacy source import."""
    target = repo_root / "docs" / "index.md"
    temporary = target.with_name(f".{target.name}.{uuid.uuid4().hex}.tmp")
    claude_count = sum(source.product == "claude-code" for source in manifest.root)
    codex_count = sum(source.product == "codex" for source in manifest.root)
    total_count = claude_count + codex_count
    comma = "\N{FULLWIDTH COMMA}"
    semicolon = "\N{FULLWIDTH SEMICOLON}"
    homepage = f"""\
---
title: AI 教程及文档
sidebar: false
outline: false
pageClass: ai-home
---

# AI 教程及文档

Claude Code 与 OpenAI Codex 的官方教程、双语参考文档和分阶段学习路径。
每个产品只有一条学习路径{comma}可在页面右上角原地切换中文与英文。

<div class="ai-home-stats" aria-label="文档范围">
  <div><strong>{total_count}</strong><span>篇官方文档</span></div>
  <div><strong>{claude_count}</strong><span>篇 Claude Code</span></div>
  <div><strong>{codex_count}</strong><span>篇 Codex</span></div>
  <div><strong>中英双语</strong><span>原文与译文并存</span></div>
</div>

## 选择产品

<div class="ai-home-products">
  <a class="ai-home-product ai-home-product--claude" href="/ai/learn/claude-code">
    <span class="ai-home-product__owner">Anthropic</span>
    <strong>Claude Code</strong>
    <span>从快速入门开始{comma}继续阅读工作流、配置、Agent SDK、Hooks、MCP 与企业部署文档。</span>
    <b>开始 Claude Code 学习路径 →</b>
  </a>
  <a class="ai-home-product ai-home-product--codex" href="/ai/learn/codex">
    <span class="ai-home-product__owner">OpenAI</span>
    <strong>Codex</strong>
    <span>从快速入门开始{comma}继续阅读 CLI、IDE、Cloud、Agent 配置、安全、插件与 SDK 文档。</span>
    <b>开始 Codex 学习路径 →</b>
  </a>
</div>

## 参考文档

- [Claude Code 官方文档](/ai/zh-CN/claude-code/quickstart)
- [Codex 官方文档](/ai/en/codex/quickstart)

中文译文与英文原文共享同一套分类。中文尚未完成时{comma}导航会明确标记并回退到英文页{semicolon}
遇到歧义时{comma}以页面所列官方来源为准。

## 附录

[通用 CAD 平台 API 设计哲学](/appendix/cad)现作为附录保留{comma}包含理论框架、横向对比、
九个平台深度剖析、跨平台 UI 框架研究与术语表。
"""
    try:
        if target.is_symlink():
            _validation_failed()
        previous = _HomepageState(
            existed=target.is_file(),
            data=target.read_bytes() if target.is_file() else b"",
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        _ = temporary.write_text(homepage, encoding="utf-8", newline="\n")
        _ = temporary.replace(target)
    except OSError:
        with suppress(OSError):
            temporary.unlink(missing_ok=True)
        _write_failed()
    return previous


def _restore_homepage(repo_root: Path, previous: _HomepageState) -> None:
    target = repo_root / "docs" / "index.md"
    temporary = target.with_name(f".{target.name}.{uuid.uuid4().hex}.tmp")
    try:
        if previous.existed:
            _ = temporary.write_bytes(previous.data)
            _ = temporary.replace(target)
        else:
            target.unlink(missing_ok=True)
    except OSError:
        with suppress(OSError):
            temporary.unlink(missing_ok=True)
        _write_failed()


def _derive_source_page(
    data: bytes,
    item: MaterializedRoute,
    english_data: bytes | None = None,
) -> bytes:
    closing = data.find(_FRONTMATTER_END, len(b"---\n"))
    if not data.startswith(b"---\n") or closing < 0:
        _validation_failed()
    fields = data[len(b"---\n") : closing].decode("utf-8").splitlines()
    title_key, separator, title = fields[0].partition(": ")
    if title_key != "title" or not separator or not title:
        _validation_failed()
    prefix = "EN · " if item.lang == "en" else "中文 · "
    label = "EN" if item.lang == "en" else "中文"
    counterpart = f"\nai_counterpart: {item.counterpart}" if item.counterpart is not None else ""
    derived = (
        f"---\ntitle: {prefix}{title}\n"
        + "\n".join(fields[1:])
        + counterpart
        + f"\nai_search_label: {label}"
    ).encode()
    public_markdown = _strip_mdx_components(data[closing:].decode("utf-8"))
    if item.lang == "zh-CN":
        if english_data is None:
            _validation_failed()
        public_markdown = _localize_chinese_attribution(public_markdown)
        english_closing = english_data.find(
            _FRONTMATTER_END,
            len(b"---\n"),
        )
        if not english_data.startswith(b"---\n") or english_closing < 0:
            _validation_failed()
        english_markdown = _strip_mdx_components(english_data[english_closing:].decode("utf-8"))
        public_markdown = _rewrite_localized_same_page_anchors(
            public_markdown,
            english_markdown,
        )
    public_markdown = public_markdown.replace("{{", "&#123;&#123;")
    public_markdown = public_markdown.replace("}}", "&#125;&#125;")
    product = str(item.source_id).split("/", maxsplit=1)[0]
    asset_host = (
        "https://code.claude.com" if product == "claude-code" else "https://learn.chatgpt.com"
    )
    public_body = _ROOT_IMAGE_RE.sub(
        lambda match: f"{match.group(1)}{asset_host}{match.group(2)}",
        public_markdown,
    ).encode()
    return derived + public_body


def _localize_chinese_attribution(markdown: str) -> str:
    """Localize legacy reader-visible attribution labels without changing values."""
    return _LEGACY_CHINESE_ATTRIBUTION_RE.sub(
        lambda match: (
            f"{match.group('prefix')}[官方来源]{match.group('url')}\n\n"
            f"内容所有者: {match.group('owner')}\n\n"
        ),
        markdown,
        count=1,
    )


def _strip_mdx_components(markdown: str) -> str:
    protected = protect_markdown(_dedent_mdx_component_bodies(markdown))
    text = _normalize_explicit_html_headings(protected.text)
    text = _strip_mdx_exports(text)
    text = _MDX_COMMENT_RE.sub("", text)
    text = _MDX_ICON_SLOT_RE.sub("", text)
    text = _UNSAFE_HTML_RE.sub("", text)
    text = _JSX_STYLE_RE.sub("", text)
    text = _MDX_COMPONENT_RE.sub("", text)
    text = _HTML_IMAGE_RE.sub(_markdown_image, text)
    text = _HTML_BREAK_RE.sub("\n", text)
    text = _HTML_TAG_RE.sub("", text)
    text = _normalize_multiline_table_rows(text)
    for span in protected.spans:
        text = text.replace(span.placeholder, span.original, 1)
    return _dedent_orphan_blocks(text)


def _dedent_mdx_component_bodies(markdown: str) -> str:
    """Remove HTML/JSX container indentation while preserving Markdown depth."""
    output: list[str] = []
    component_indents: list[tuple[str, int]] = []
    fence_marker: str | None = None
    for line in markdown.splitlines(keepends=True):
        content = line.rstrip("\r\n")
        if fence_marker is not None:
            output.append(_remove_structural_indent(line, component_indents))
            fence = _FENCE_RE.match(content)
            if fence is not None and fence.group(1)[0] == fence_marker:
                fence_marker = None
            continue

        closing = _MDX_BLOCK_CLOSE_RE.fullmatch(content)
        if closing is not None and component_indents:
            tag = closing.group("tag")
            if component_indents[-1][0] == tag:
                _ = component_indents.pop()

        output.append(_remove_structural_indent(line, component_indents))

        fence = _FENCE_RE.match(content)
        if fence is not None:
            fence_marker = fence.group(1)[0]
            continue
        opening = _MDX_BLOCK_OPEN_RE.fullmatch(content)
        if opening is None:
            continue
        tag = opening.group("tag")
        if opening.group("selfclose") or f"</{tag}>" in opening.group("tail"):
            continue
        component_indents.append((tag, len(opening.group("indent")) + 2))
    return "".join(output)


def _remove_structural_indent(
    line: str,
    component_indents: list[tuple[str, int]],
) -> str:
    """Remove only the current MDX container's source indentation."""
    if not component_indents or not line.strip():
        return line
    width = component_indents[-1][1]
    prefix = len(line) - len(line.lstrip(" \t"))
    return line[min(width, prefix) :]


def _dedent_orphan_blocks(markdown: str) -> str:
    """Remove top-level indentation left after presentational wrappers disappear."""
    output: list[str] = []
    active_list_indent: int | None = None
    fence_marker: str | None = None
    for line in markdown.splitlines(keepends=True):
        content = line.rstrip("\r\n")
        fence = _FENCE_RE.match(content)
        if fence_marker is not None:
            output.append(line)
            if fence is not None and fence.group(1)[0] == fence_marker:
                fence_marker = None
            continue
        if fence is not None:
            fence_marker = fence.group(1)[0]
            output.append(line)
            continue
        if not content.strip():
            output.append(line)
            continue
        list_item = _LIST_ITEM_RE.match(content)
        indent = _leading_indent_width(content)
        if list_item is not None:
            active_list_indent = len(list_item.group(0).expandtabs(4))
            output.append(line)
            continue
        if active_list_indent is not None and indent >= active_list_indent:
            output.append(line)
            continue
        active_list_indent = None
        if indent >= _INDENTED_CODE_WIDTH:
            newline = line[len(content) :]
            output.append(content.lstrip(" \t") + newline)
        else:
            output.append(line)
    return "".join(output)


def _normalize_multiline_table_rows(markdown: str) -> str:
    """Adapt owner-supported multiline cells to VitePress Markdown rows."""
    output: list[str] = []
    pending: list[str] = []
    in_table = False
    for line in markdown.splitlines(keepends=True):
        content = line.rstrip("\r\n")
        if _is_table_delimiter(content):
            output.extend(pending)
            pending.clear()
            output.append(line)
            in_table = True
            continue
        if not in_table:
            output.append(line)
            continue

        stripped = content.strip()
        if pending and not stripped.startswith("|"):
            pending.append(line)
            if stripped.endswith("|"):
                output.append(_join_multiline_table_row(pending))
                pending = []
            continue
        output.extend(pending)
        pending.clear()
        if not stripped or not stripped.startswith("|"):
            in_table = False
            output.append(line)
        elif stripped.endswith("|"):
            output.append(line)
        else:
            pending = [line]
    output.extend(pending)
    return "".join(output)


def _is_table_delimiter(line: str) -> bool:
    stripped = line.strip().strip("|").strip()
    if not stripped:
        return False
    cells = tuple(cell.strip() for cell in stripped.split("|"))
    return len(cells) >= _TABLE_MIN_COLUMNS and all(
        _TABLE_DELIMITER_CELL_RE.fullmatch(cell) is not None for cell in cells
    )


def _join_multiline_table_row(lines: list[str]) -> str:
    first = lines[0].rstrip("\r\n")
    indent = first[: len(first) - len(first.lstrip(" \t"))]
    paragraphs: list[str] = []
    current: list[str] = []
    for line in lines:
        content = line.rstrip("\r\n").strip()
        if content:
            current.append(content)
        elif current:
            paragraphs.append(" ".join(current))
            current = []
    if current:
        paragraphs.append(" ".join(current))
    last = lines[-1]
    newline = "\r\n" if last.endswith("\r\n") else "\n" if last.endswith("\n") else ""
    return indent + "<br><br>".join(paragraphs) + newline


def _leading_indent_width(line: str) -> int:
    prefix = line[: len(line) - len(line.lstrip(" \t"))]
    return len(prefix.expandtabs(4))


def _normalize_explicit_html_headings(markdown: str) -> str:
    """Convert safe explicit HTML headings before generic HTML removal."""

    def replace(match: re.Match[str]) -> str:
        title = " ".join(line.strip() for line in match.group("title").splitlines() if line.strip())
        if not title:
            return match.group()
        explicit_id = _EXPLICIT_HTML_HEADING_ID_RE.search(match.group("attributes"))
        anchor = f" {{#{explicit_id.group('anchor')}}}" if explicit_id is not None else ""
        return f"{'#' * int(match.group('level'))} {title}{anchor}\n"

    return _EXPLICIT_HTML_HEADING_RE.sub(replace, markdown)


def _rewrite_localized_same_page_anchors(
    chinese_markdown: str,
    english_markdown: str,
) -> str:
    """Map source heading fragments to localized VitePress heading ids."""
    # VitePress 1.6.4 generates anchors from rendered heading text.
    # https://vitepress.dev/guide/markdown#header-anchors
    english_headings = _heading_anchors(english_markdown)
    chinese_headings = _heading_anchors(chinese_markdown)
    if tuple(level for level, _ in english_headings) != tuple(
        level for level, _ in chinese_headings
    ):
        return chinese_markdown
    mapping = {
        english_anchor: chinese_anchor
        for (_, english_anchor), (_, chinese_anchor) in zip(
            english_headings,
            chinese_headings,
            strict=True,
        )
        if english_anchor != chinese_anchor
    }
    if not mapping:
        return chinese_markdown

    output: list[str] = []
    fence_marker: str | None = None
    for line in chinese_markdown.splitlines(keepends=True):
        fence = _FENCE_RE.match(line)
        if fence_marker is not None:
            output.append(line)
            if fence and fence.group(1)[0] == fence_marker:
                fence_marker = None
            continue
        if fence:
            fence_marker = fence.group(1)[0]
            output.append(line)
            continue

        def replace(
            match: re.Match[str],
            current_line: str = line,
        ) -> str:
            if _inside_inline_code(current_line, match.start()):
                return match.group()
            localized = _localized_same_page_fragment(
                mapping,
                match.group("fragment"),
            )
            if localized is None:
                return match.group()
            return f"{match.group('prefix')}#{localized}"

        output.append(_SAME_PAGE_FRAGMENT_RE.sub(replace, line))
    return "".join(output)


def _localized_same_page_fragment(
    mapping: dict[str, str],
    fragment: str,
) -> str | None:
    """Resolve literal or percent-encoded source heading fragments."""
    return mapping.get(fragment) or mapping.get(vitepress_slugify(unquote(fragment)))


def _heading_anchors(markdown: str) -> list[tuple[int, str]]:
    headings: list[tuple[int, str]] = []
    seen: dict[str, int] = {}
    fence_marker: str | None = None
    for line in markdown.splitlines():
        fence = _FENCE_RE.match(line)
        if fence_marker is not None:
            if fence and fence.group(1)[0] == fence_marker:
                fence_marker = None
            continue
        if fence:
            fence_marker = fence.group(1)[0]
            continue
        heading = _HEADING_RE.match(line)
        if heading is None:
            continue
        level = len(heading.group(1))
        title = heading.group(2)
        custom = _CUSTOM_HEADING_ANCHOR_RE.search(title)
        if custom is not None:
            base = custom.group(1)
        else:
            rendered = _INLINE_LINK_RE.sub(r"\1", title)
            rendered = _INLINE_HTML_RE.sub("", rendered)
            base = vitepress_slugify(rendered)
        duplicate = seen.get(base, 0)
        seen[base] = duplicate + 1
        anchor = base if duplicate == 0 else f"{base}-{duplicate}"
        headings.append((level, anchor))
    return headings


def _inside_inline_code(line: str, position: int) -> bool:
    return line.count("`", 0, position) % 2 == 1


def _markdown_image(match: re.Match[str]) -> str:
    attributes: dict[str, str] = {
        name.lower(): value
        for name, value in cast(
            "list[tuple[str, str]]",
            _HTML_ATTRIBUTE_RE.findall(match.group()),
        )
    }
    source = attributes.get("src", "")
    if not source:
        return ""
    return f"![{attributes.get('alt', '')}]({source})"


def _strip_mdx_exports(markdown: str) -> str:
    lines = markdown.splitlines(keepends=True)
    output: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.startswith(("export const ", "export let ", "export var ", "export function ")):
            output.append(line)
            index += 1
            continue
        depth = 0
        while index < len(lines):
            current = lines[index]
            depth += current.count("{") - current.count("}")
            index += 1
            if depth <= 0 and current.rstrip().endswith((";", "}")):
                break
        output.append("\n")
    return "".join(output)


def _rollback(
    target: Path,
    staged: Path,
    backup: Path,
    state: _SwapState,
) -> None:
    try:
        if state.promoted and target.exists():
            shutil.rmtree(target)
        if state.backed_up and backup.exists():
            _ = backup.replace(target)
        if staged.exists():
            shutil.rmtree(staged)
    except OSError:
        _write_failed()


def _validation_failed() -> NoReturn:
    raise AIAgentError(
        code=ErrorCode.VALIDATION_FAILED,
        message="content root is invalid",
    )


def _write_failed() -> NoReturn:
    raise AIAgentError(
        code=ErrorCode.WRITE_FAILED,
        message="AI handbook materialization failed",
    )


if __name__ == "__main__":
    raise SystemExit(main())

# ruff: noqa: CPY001,D100,D101,D102,D103,D107,E501,FBT001,FBT002,INP001,TC003

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import httpx2

from scripts.ai.errors import AIAgentError, ErrorCode
from scripts.ai.pages import render_chinese_page, render_english_page
from scripts.ai.snapshot import RealFileOps
from scripts.ai.types import NormalizedPage, SourceManifest


def response_markdown(source_id: str, changed: bool = False) -> str:
    suffix = " changed" if changed else ""
    marker = "\n\nSynthetic permissions marker." if source_id == "claude-code/permissions" else ""
    return f"# Synthetic {source_id}\n\nSynthetic source{suffix}.{marker}\n"


def normalized_pages(
    manifest: SourceManifest, changed_id: str | None = None
) -> tuple[NormalizedPage, ...]:
    pages: list[NormalizedPage] = []
    for source in manifest.root:
        markdown = response_markdown(source.id, source.id == changed_id)
        pages.append(
            NormalizedPage(
                source=source,
                markdown=markdown,
                content_sha256=sha256(markdown.encode("utf-8")).hexdigest(),
            )
        )
    return tuple(pages)


def install_content(root: Path, pages: tuple[NormalizedPage, ...]) -> None:
    for page in pages:
        english = root / "en" / page.source.product / f"{page.source.slug}.md"
        chinese = root / "zh-CN" / page.source.product / f"{page.source.slug}.md"
        english.parent.mkdir(parents=True, exist_ok=True)
        chinese.parent.mkdir(parents=True, exist_ok=True)
        _ = english.write_bytes(render_english_page(page))
        marker = "\n\n合成权限标记。" if page.source.id == "claude-code/permissions" else ""
        _ = chinese.write_bytes(
            render_chinese_page(page, f"# 中文 {page.source.id}\n\n合成内容。{marker}\n")
        )
    install_learning(root, pages)


def install_learning(root: Path, pages: tuple[NormalizedPage, ...]) -> None:
    learning = root / "learn" / "zh-CN"
    learning.mkdir(parents=True, exist_ok=True)
    for product in ("claude-code", "codex"):
        product_name = "Claude Code" if product == "claude-code" else "Codex"
        product_pages = tuple(page for page in pages if page.source.product == product)
        lines = [
            f"# {product_name} 学习路径",
            "",
            f"适合谁阅读：希望用内部中文资料快速了解 {product_name} 的团队成员。",  # noqa: RUF001
            "",
            "## 推荐阅读顺序",
            "",
        ]
        for index, page in enumerate(product_pages, start=1):
            lines.extend(
                (
                    f"{index}. [{page.source.title}](/ai/zh-CN/{page.source.product}/{page.source.slug})",
                    f"   学习目标：了解 {page.source.title} 对应的核心主题。",  # noqa: RUF001
                )
            )
        lines.extend(("", "遇到歧义时，请切换到对应英文页核对。"))  # noqa: RUF001
        _ = (learning / f"{product}.md").write_text(
            "\n".join(lines) + "\n",
            encoding="utf-8",
        )


def transport_for(manifest: SourceManifest, changed_id: str | None = None) -> httpx2.MockTransport:
    by_url = {source.fetch_url: source for source in manifest.root}

    def handler(request: httpx2.Request) -> httpx2.Response:
        source = by_url[str(request.url)]
        markdown = response_markdown(source.id, source.id == changed_id)
        if source.fetch_format != "markdown":
            content = f'<article id="mainContent"><h1>Synthetic {source.id}</h1><p>Synthetic source{" changed" if source.id == changed_id else ""}.</p></article>'
            content_type = "text/html"
        else:
            content = markdown
            content_type = "text/markdown"
        return httpx2.Response(
            status_code=200,
            request=request,
            headers={"content-type": content_type},
            content=content.encode("utf-8"),
        )

    return httpx2.MockTransport(handler)


class FaultFileOps:
    label: str
    failed: bool
    real: RealFileOps

    def __init__(self, label: str) -> None:
        self.label = label
        self.failed = False
        self.real = RealFileOps()

    def copy_tree(self, source: Path, destination: Path, fault: str | None) -> None:
        self._fault(fault)
        self.real.copy_tree(source, destination, fault=None)

    def replace(self, source: Path, destination: Path, fault: str | None) -> None:
        self._fault(fault)
        self.real.replace(source, destination, fault=None)

    def write_bytes(self, path: Path, data: bytes, fault: str | None) -> None:
        self._fault(fault)
        self.real.write_bytes(path, data, fault=None)

    def remove(self, path: Path, fault: str | None) -> None:
        self._fault(fault)
        self.real.remove(path, fault=None)

    def _fault(self, fault: str | None) -> None:
        if fault == self.label and not self.failed:
            self.failed = True
            raise AIAgentError(code=ErrorCode.WRITE_FAILED, message="injected write failure")

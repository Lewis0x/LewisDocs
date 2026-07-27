# Copyright 2026

"""HTML parsing and rendering for fetched AI pages."""

from __future__ import annotations

from html.parser import HTMLParser
from typing import Final

from typing_extensions import override

_NORMALIZATION_ERROR: Final = "normalization failed"
_VOID_TAGS: Final = frozenset(
    {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }
)


def normalize_html_content(raw: str) -> str:
    """Parse an article and render it as canonical markdown."""
    parser = _ArticleParser()
    parser.feed(raw)
    parser.close()
    if parser.article is None:
        raise ValueError(_NORMALIZATION_ERROR)
    return finalize_markdown(_render_article(parser.article))


def finalize_markdown(raw: str) -> str:
    """Normalize line endings, surrounding whitespace, and heading spacing."""
    text = _trim_outer_blank_lines(raw.replace("\r\n", "\n").replace("\r", "\n"))
    text = _ensure_heading_gap(text)
    if not text.strip():
        raise ValueError(_NORMALIZATION_ERROR)
    return text.rstrip("\n") + "\n"


def _trim_outer_blank_lines(raw: str) -> str:
    lines = raw.split("\n")
    start, end = 0, len(lines)
    while start < end and not lines[start].strip():
        start += 1
    while end > start and not lines[end - 1].strip():
        end -= 1
    return "\n".join(lines[start:end])


def _ensure_heading_gap(raw: str) -> str:
    out: list[str] = []
    lines = raw.split("\n")
    for index, line in enumerate(lines):
        out.append(line)
        if line.startswith(("# ", "## ")) and index + 1 < len(lines) and lines[index + 1].strip():
            out.append("")
    return "\n".join(out)


def _render_article(article: _Node) -> str:
    sections = [_render_block(child, list_depth=0) for child in article.children]
    return "\n\n".join(section for section in sections if section.strip())


def _render_block(node: _Node, *, list_depth: int) -> str:  # noqa: PLR0911
    if node.tag is None:
        return node.text
    if node.tag == "h1":
        return f"# {_render_inline(node.children)}"
    if node.tag == "h2":
        return f"## {_render_inline(node.children)}"
    if node.tag == "p":
        return _render_inline(node.children)
    if node.tag in {"ul", "ol"}:
        return _render_list(node, list_depth=list_depth)
    if node.tag == "pre":
        return _render_pre(node)
    if node.tag == "table":
        return _render_table(node)
    if node.tag == "blockquote":
        return _render_blockquote(node, list_depth=list_depth)
    if node.tag in {"article", "body", "html", "main", "section", "div", "figcaption"}:
        return "\n\n".join(
            block
            for child in node.children
            if (block := _render_block(child, list_depth=list_depth)).strip()
        )
    return _render_inline(node.children)


def _render_inline(nodes: list[_Node]) -> str:
    return "".join(_render_inline_node(node) for node in nodes)


def _render_inline_node(node: _Node) -> str:  # noqa: PLR0911
    if node.tag is None:
        return node.text
    if node.tag in {"strong", "b"}:
        return f"**{_render_inline(node.children)}**"
    if node.tag in {"em", "i"}:
        return f"*{_render_inline(node.children)}*"
    if node.tag == "code":
        return f"`{_collect_raw_text(node)}`"
    if node.tag == "a":
        return f"[{_render_inline(node.children)}]({node.attrs.get('href', '')})"
    if node.tag == "img":
        return f"![{node.attrs.get('alt', '')}]({node.attrs.get('src', '')})"
    if node.tag == "br":
        return "<br>"
    return _render_inline(node.children)


def _render_list(node: _Node, *, list_depth: int) -> str:
    lines: list[str] = []
    ordered = node.tag == "ol"
    prefix = "  " * list_depth
    for index, item in enumerate((c for c in node.children if c.tag == "li"), start=1):
        marker = f"{prefix}{index if ordered else '- '}"
        marker = marker + ". " if ordered else marker
        rendered = _render_inline(item.children)
        item_lines = rendered.split("\n")
        lines.append(f"{marker}{item_lines[0]}")
        continuation = " " * len(marker)
        lines.extend(f"{continuation}{line}" for line in item_lines[1:])
    return "\n".join(lines)


def _render_pre(node: _Node) -> str:
    code_node = next((c for c in node.children if c.tag == "code"), None)
    language = ""
    if code_node is not None:
        for token in code_node.attrs.get("class", "").split():
            if token.startswith("language-"):
                language = token.removeprefix("language-")
                break
    code = _collect_raw_text(code_node or node)
    code = code.replace("\r\n", "\n").replace("\r", "\n").strip("\n")
    return f"```{language}\n{code}\n```"


def _render_table(node: _Node) -> str:
    rows = _extract_table_rows(node)
    if not rows:
        return ""
    normalized = [[_render_inline([cell]).strip() for cell in row] for row in rows]
    max_columns = max(len(row) for row in normalized)
    rows = [row + [""] * (max_columns - len(row)) for row in normalized]
    separator = "| " + " | ".join("---" for _ in rows[0]) + " |"
    lines = ["| " + " | ".join(rows[0]) + " |", separator]
    lines.extend("| " + " | ".join(row) + " |" for row in rows[1:])
    return "\n".join(lines)


def _extract_table_rows(node: _Node) -> list[list[_Node]]:
    rows: list[list[_Node]] = []
    for child in node.children:
        if child.tag == "tr":
            row = [cell for cell in child.children if cell.tag in {"td", "th"}]
            if row:
                rows.append(row)
        elif child.tag in {"thead", "tbody", "tfoot"}:
            rows.extend(_extract_table_rows(child))
    return rows


def _render_blockquote(node: _Node, *, list_depth: int) -> str:
    rendered = [_render_block(child, list_depth=list_depth + 1) for child in node.children]
    inner = "\n\n".join(part for part in rendered if part.strip())
    if not inner:
        return ""
    return "\n".join(f"> {line}" if line else ">" for line in inner.split("\n"))


def _collect_raw_text(node: _Node) -> str:
    if node.tag is None:
        return node.text
    return "".join(_collect_raw_text(child) for child in node.children)


class _Node:
    """Mutable tree node accumulated while the HTML parser visits callbacks."""

    __slots__: tuple[str, ...] = ("attrs", "children", "tag", "text")

    tag: str | None
    attrs: dict[str, str]
    text: str
    children: list[_Node]

    def __init__(
        self,
        tag: str | None,
        attrs: dict[str, str] | None = None,
        text: str = "",
    ) -> None:
        self.tag = tag
        self.attrs = {} if attrs is None else attrs
        self.text = text
        self.children = []


class _ArticleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.article: _Node | None = None
        self._stack: list[_Node] = []
        self._main_content_count: int = 0
        self._ignore_depth: int = 0

    @property
    def _in_article(self) -> bool:
        return bool(self._stack)

    @override
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {name: value for name, value in attrs if value is not None}
        if tag == "article" and attributes.get("id") == "mainContent":
            self._main_content_count += 1
            if self._main_content_count != 1:
                raise ValueError(_NORMALIZATION_ERROR)
            self.article = _Node(tag="article", attrs=attributes)
            self._stack.append(self.article)
            return
        if not self._in_article:
            return
        if self._ignore_depth > 0:
            if tag in {"script", "style"}:
                self._ignore_depth += 1
            return
        if tag in {"script", "style"}:
            self._ignore_depth = 1
            return
        node = _Node(tag=tag, attrs=attributes)
        self._stack[-1].children.append(node)
        if tag not in _VOID_TAGS:
            self._stack.append(node)

    @override
    def handle_endtag(self, tag: str) -> None:
        if not self._in_article:
            return
        if self._ignore_depth > 0:
            if tag in {"script", "style"}:
                self._ignore_depth -= 1
            return
        if not self._stack:
            raise ValueError(_NORMALIZATION_ERROR)
        current = self._stack.pop()
        if current.tag != tag:
            raise ValueError(_NORMALIZATION_ERROR)

    @override
    def handle_data(self, data: str) -> None:
        if self._in_article and self._ignore_depth == 0 and data.strip():
            self._stack[-1].children.append(_Node(tag=None, text=data))

    @override
    def close(self) -> None:
        super().close()
        if self._main_content_count != 1 or self.article is None:
            raise ValueError(_NORMALIZATION_ERROR)
        if self._stack:
            raise ValueError(_NORMALIZATION_ERROR)

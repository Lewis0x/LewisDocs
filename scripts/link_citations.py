#!/usr/bin/env python3
"""
构建后处理：把正文里的 [百科/第三方/官方/新闻/书籍 N] 引用标记自动包成
可点击链接（指向各 doc 末尾 ## 参考来源 段中给出的 URL）。

输入语义：源文档末尾有 `## 参考来源` 段，每条目格式形如
    - [百科 1] Wikipedia, "ObjectARX", https://en.wikipedia.org/wiki/ObjectARX
    - [新闻 7] Autodesk Blog, "Introducing AutoCAD 2026", 2025-03-31, https://...
    - [第三方 14] CATIA 行业使用情况（多源行业资料）   ← 无 URL，原样保留
本脚本：
  1. 扫每个 docs/*.md 末尾的"参考来源"段，构建 (kind, num) -> URL 映射
  2. 在正文（参考来源段之前的部分）扫所有 `[百科/第三方/官方/新闻/书籍 N]`
  3. 命中的换成 <a href="URL" target="_blank" rel="noreferrer">[百科 N]</a>
  4. 没 URL 的保持原样

不动 source/ 文件，只改 docs/。在 prepare-content 链路最末执行
（rewrite_links 之后；watermark 之前是构建阶段，互不影响）。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / 'docs'

KIND_PATTERN = '百科|第三方|官方|新闻|书籍'

# 正文中的引用：[百科 5] / [百科5] / [新闻 12]
CITATION_RE = re.compile(rf'\[({KIND_PATTERN})\s*(\d+)\]')

# 参考来源段里的条目：- [百科 5] xxx https://url ...
# URL 必须是 http(s)://...，到下一个空白 / 中文标点 / 行尾结束
REF_LINE_RE = re.compile(
    rf'^\s*[-*]\s+\[({KIND_PATTERN})\s*(\d+)\][^\n]*?(https?://[^\s)，。；;）]+)',
    re.MULTILINE,
)

# 参考来源段标题（每个 doc 必有的固定 H2）
REF_HEADING_RE = re.compile(r'^##\s+参考来源\s*$', re.MULTILINE)


def parse_references(text: str) -> dict[tuple[str, str], str]:
    """从 ## 参考来源 段抽取 (kind, num) -> URL。"""
    m = REF_HEADING_RE.search(text)
    if not m:
        return {}
    refs_section = text[m.end():]
    # 如果参考来源段后还有别的 ##（少见但不阻挡），截到下一个 H2
    next_h2 = re.search(r'^##\s+', refs_section, re.MULTILINE)
    if next_h2:
        refs_section = refs_section[:next_h2.start()]

    mapping: dict[tuple[str, str], str] = {}
    for ref in REF_LINE_RE.finditer(refs_section):
        kind, num, url = ref.group(1), ref.group(2), ref.group(3)
        # 去掉 URL 末尾可能的标点 / 引号
        url = url.rstrip('.,;:)）"\'》】、 \t\r\n')
        mapping[(kind, num)] = url
    return mapping


def wrap_citations(body: str, refs: dict[tuple[str, str], str]) -> tuple[str, int, int]:
    """在正文 body 中把已知 URL 的引用包成 <a> 链接。"""
    linked = 0
    skipped = 0

    def replace(m: re.Match) -> str:
        nonlocal linked, skipped
        kind, num = m.group(1), m.group(2)
        url = refs.get((kind, num))
        if url is None:
            skipped += 1
            return m.group(0)
        linked += 1
        return f'<a href="{url}" target="_blank" rel="noreferrer">[{kind} {num}]</a>'

    return CITATION_RE.sub(replace, body), linked, skipped


def process_file(fpath: Path) -> tuple[int, int, int]:
    text = fpath.read_text(encoding='utf-8')
    refs = parse_references(text)
    if not refs:
        # 没有参考来源段，跳过
        return 0, 0, 0

    # 把正文部分和参考来源段切开——不要在参考来源段内自我嵌套链接
    m = REF_HEADING_RE.search(text)
    body = text[:m.start()]
    refs_section = text[m.start():]

    new_body, linked, skipped = wrap_citations(body, refs)
    new_text = new_body + refs_section

    if new_text != text:
        fpath.write_text(new_text, encoding='utf-8')

    return len(refs), linked, skipped


def main() -> int:
    if not DOCS.exists():
        print('docs/ does not exist; run `npm run import` first', file=sys.stderr)
        return 1

    total_refs = 0
    total_linked = 0
    total_skipped = 0
    files = sorted(DOCS.rglob('*.md'))
    print(f'Scanning {len(files)} markdown files...')
    for fpath in files:
        n_refs, linked, skipped = process_file(fpath)
        if n_refs or linked or skipped:
            rel = fpath.relative_to(DOCS)
            note = f'refs={n_refs} linked={linked}'
            if skipped:
                note += f' no-url={skipped}'
            print(f'  {rel}: {note}')
        total_refs += n_refs
        total_linked += linked
        total_skipped += skipped

    print(
        f'\nDone: {total_refs} reference entries indexed, '
        f'{total_linked} citations linked, '
        f'{total_skipped} kept as plain text (no URL).'
    )
    return 0


if __name__ == '__main__':
    sys.exit(main())

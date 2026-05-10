#!/usr/bin/env python3
"""
把所有 [回链：3.4 §三 核心数据模型] 形式的纯文本引用改写为可点击 Markdown 链接。

支持的回链格式：
1. 跨文档（中文章节）  ：[回链：3.4 §三 核心数据模型]
2. 多目标             ：[回链：3.2 §六 X；3.3 §三 Y；3.4 §五 Z]
3. 文档内（阿拉伯数字）：[回链：§2.4 协作模式]
4. 带括号补充         ：[回链：3.1 §一 历史演进（2026）]

锚点算法是 @mdit-vue/shared 的 slugify 函数的 Python 直译，
保证与 VitePress 实际生成的 heading id 一致。

源码参考：
  https://github.com/mdit-vue/mdit-vue/blob/main/packages/shared/src/slugify.ts
"""
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / 'docs'

DOC_ROUTES = {
    '3.1': '/platforms/autocad',
    '3.2': '/platforms/catia',
    '3.3': '/platforms/nx',
    '3.4': '/platforms/onshape',
    '3.5': '/platforms/microstation',
    '3.6': '/platforms/solidworks',
    '3.7': '/platforms/sketchup',
    '3.8': '/platforms/freecad',
    '3.9': '/platforms/bricscad',
}

DOC_FILES = {
    '3.1': 'platforms/autocad.md',
    '3.2': 'platforms/catia.md',
    '3.3': 'platforms/nx.md',
    '3.4': 'platforms/onshape.md',
    '3.5': 'platforms/microstation.md',
    '3.6': 'platforms/solidworks.md',
    '3.7': 'platforms/sketchup.md',
    '3.8': 'platforms/freecad.md',
    '3.9': 'platforms/bricscad.md',
}


# ---------------------------------------------------------------------------
# slugify：直译 @mdit-vue/shared

# 控制字符 U+0000-U+001F；用 chr() 构造避免源码中出现真实控制字符
_R_CONTROL = re.compile('[' + chr(0) + '-' + chr(0x1F) + ']')
# 组合字符 U+0300-U+036F
_R_COMBINING = re.compile('[' + chr(0x0300) + '-' + chr(0x036F) + ']')

# rSpecial：与 @mdit-vue/shared 保持一致：ASCII 标点 + 智能引号
_SPECIAL_ASCII = (
    ' \t\r\n\f\v'                              # whitespace
    '~`!@#$%^&*()-_+=[]{}|\\;:"\',./<>?'       # ASCII punctuation
)
_SPECIAL_SMART = (
    chr(0x201C) + chr(0x201D) + chr(0x2018) + chr(0x2019)
)
_R_SPECIAL = re.compile('[' + re.escape(_SPECIAL_ASCII + _SPECIAL_SMART) + ']+')


def vitepress_slugify(text: str) -> str:
    """与 VitePress（@mdit-vue/shared）一致的 slugify。"""
    text = unicodedata.normalize('NFKD', text)
    text = _R_COMBINING.sub('', text)
    text = _R_CONTROL.sub('', text)
    text = _R_SPECIAL.sub('-', text)
    text = re.sub(r'-{2,}', '-', text)
    text = re.sub(r'^-+|-+$', '', text)
    text = re.sub(r'^(\d)', r'_\1', text)
    return text.lower()


# ---------------------------------------------------------------------------
# 找标题

# 3.x 文档：## 一、xxx / ## 二、xxx ...
_CN_HEADING = re.compile(
    r'^##\s+([一-龥]+、[^\n]+?)\s*$',
    re.MULTILINE,
)
# 文档 1（theory.md）：### N.N xxx / #### N.N.N xxx 等
_AR_HEADING = re.compile(
    r'^#{2,4}\s+(\d+(?:\.\d+)*\s+[^\n]+?)\s*$',
    re.MULTILINE,
)

_CN_DIGITS = set('零一二三四五六七八九十百千万')


def _is_cn_index(s: str) -> bool:
    return bool(s) and all(ch in _CN_DIGITS for ch in s)


def find_chinese_heading(content: str, cn_index: str) -> str | None:
    """在内容里找以 `<中文数字>、` 开头的二级标题，返回完整标题文本。"""
    target_prefix = cn_index + '、'
    for m in _CN_HEADING.finditer(content):
        heading = m.group(1).strip()
        if heading.startswith(target_prefix):
            # 校验：cn_index 之前没有其他中文数字字符
            head_idx_part = heading.split('、', 1)[0]
            if _is_cn_index(head_idx_part) and head_idx_part == cn_index:
                return heading
    return None


def find_arabic_heading(content: str, ar_index: str) -> str | None:
    """在内容里找以 `<N.N>` 开头的标题，返回完整标题文本。"""
    target_prefix = ar_index + ' '
    for m in _AR_HEADING.finditer(content):
        heading = m.group(1).strip()
        head_idx_part = heading.split(None, 1)[0] if heading else ''
        if head_idx_part == ar_index:
            return heading
    return None


# ---------------------------------------------------------------------------
# 文档加载缓存

_doc_cache: dict[str, str] = {}


def load_doc_by_id(doc_id: str) -> str:
    if doc_id in _doc_cache:
        return _doc_cache[doc_id]
    rel = DOC_FILES.get(doc_id)
    if not rel:
        return ''
    fpath = DOCS / rel
    if not fpath.exists():
        return ''
    content = fpath.read_text(encoding='utf-8')
    _doc_cache[doc_id] = content
    return content


# ---------------------------------------------------------------------------
# 解析单个回链目标

# "3.4 §三 核心数据模型"
_RE_CROSS = re.compile(
    r'^(3\.\d+)\s+§\s*([一-龥]+)\s*(.*)$'
)
# "§2.4 协作模式"
_RE_INTERNAL = re.compile(
    r'^§\s*(\d+(?:\.\d+)*)\s*(.*)$'
)


def resolve_target(target: str, current_content: str) -> str | None:
    """解析单个目标字符串，返回完整 URL（含锚点）。"""
    target = target.strip()

    m = _RE_CROSS.match(target)
    if m:
        doc_id, cn_index = m.group(1), m.group(2)
        if not _is_cn_index(cn_index):
            return None
        route = DOC_ROUTES.get(doc_id)
        if not route:
            return None
        content = load_doc_by_id(doc_id)
        if not content:
            return route
        heading = find_chinese_heading(content, cn_index)
        if not heading:
            return route
        return f'{route}#{vitepress_slugify(heading)}'

    m = _RE_INTERNAL.match(target)
    if m:
        ar_index = m.group(1)
        heading = find_arabic_heading(current_content, ar_index)
        if not heading:
            return None
        return f'#{vitepress_slugify(heading)}'

    return None


# ---------------------------------------------------------------------------
# 跳过反引号包裹的代码片段

def _is_in_inline_code(content: str, pos: int) -> bool:
    """在同一行内统计 pos 之前的反引号数量；为奇数则视为在 inline code 内。"""
    line_start = content.rfind('\n', 0, pos) + 1
    return content.count('`', line_start, pos) % 2 == 1


# ---------------------------------------------------------------------------
# 主流程

_RE_CALLBACK = re.compile(r'\[回链：([^\]]+)\]')
_SEP = '；'


def rewrite_in_file(fpath: Path) -> tuple[int, int]:
    """改写单文件中的所有回链；返回 (改写数, 跳过数)。"""
    content = fpath.read_text(encoding='utf-8')
    rewritten = 0
    skipped = 0
    pieces: list[str] = []
    last = 0

    for m in _RE_CALLBACK.finditer(content):
        pieces.append(content[last:m.start()])
        full = m.group(0)
        targets_text = m.group(1)

        if _is_in_inline_code(content, m.start()):
            pieces.append(full)
            skipped += 1
            last = m.end()
            continue

        targets = [t.strip() for t in targets_text.split(_SEP) if t.strip()]
        urls = []
        for t in targets:
            u = resolve_target(t, content)
            if u:
                urls.append((t, u))

        if not urls:
            pieces.append(full)
            skipped += 1
            last = m.end()
            continue

        # 渲染时去掉 "回链：" 前缀——读者只看到 [3.4 §三 …](url) 这样的纯引用。
        # 源文件里仍写 [回链：…]（这是给改写脚本认的语义标记），渲染输出更克制。
        if len(urls) == 1:
            target = urls[0][0]
            url = urls[0][1]
            pieces.append(f'[{target}]({url})')
        else:
            link_parts = [f'[{t}]({u})' for t, u in urls]
            pieces.append(_SEP.join(link_parts))
        rewritten += 1
        last = m.end()

    pieces.append(content[last:])
    new_content = ''.join(pieces)

    if new_content != content:
        fpath.write_text(new_content, encoding='utf-8')

    return rewritten, skipped


def main() -> int:
    if not DOCS.exists():
        print('docs/ does not exist; run `npm run import` first', file=sys.stderr)
        return 1

    files = sorted(DOCS.rglob('*.md'))
    print(f'Scanning {len(files)} markdown files...')
    total_rewritten = 0
    total_skipped = 0
    for fpath in files:
        rewritten, skipped = rewrite_in_file(fpath)
        if rewritten or skipped:
            rel = fpath.relative_to(DOCS)
            note = f'rewrote {rewritten}'
            if skipped:
                note += f', skipped {skipped}'
            print(f'  {rel}: {note}')
        total_rewritten += rewritten
        total_skipped += skipped

    print(f'\nDone: rewrote {total_rewritten} callback(s), skipped {total_skipped}')
    return 0


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""
构建后处理：
  1. 抹掉 VitePress 自动注入的 <meta name="generator" content="VitePress v..."> 指纹
     （这一步必须在构建后做——VitePress 的 transformHead 钩子只能改用户 head，
     抹不掉框架自己最后注入的 generator）
  2. 把不可见水印注入每个 dist 页面，便于事后语料溯源

水印用零宽字符（U+200B/200C/200D/2060）4 进制编码 `(page_id, build_id)`：
  '0' -> ZWSP (U+200B)
  '1' -> ZWNJ (U+200C)
  '2' -> ZWJ  (U+200D)
  '3' -> WJ   (U+2060)

每页注入到 <main> 起始位置一次，外层包一对 sentinel 注释 `<!--lwm-->...<!--/lwm-->`，
方便 scan_corpus.py 精确定位。生成的水印 + 路径映射写到
`_watermark-manifest.json`（CI 把它当 artifact 保留 90 天，**不部署上线**）。

何时人工介入：
  1. 怀疑被语料采集 → 跑 scripts/scan_corpus.py 对照 manifest
  2. 命中 → 用 manifest 反查 (page_id, build_id) 锁定具体页与构建
  3. 准备 DMCA 材料 → 见 project-docs/dmca-template.md
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / 'docs' / '.vitepress' / 'dist'
MANIFEST = DIST / '_watermark-manifest.json'

# 4 进制 → 零宽字符
ZW = ['​', '‌', '‍', '⁠']
ZW_PATTERN = re.compile(f'[{"".join(ZW)}]+')


def encode(payload: str, length_bits: int = 96) -> str:
    """把 payload 经 SHA-256 截断后编码为 length_bits/2 个零宽字符。"""
    digest = hashlib.sha256(payload.encode('utf-8')).digest()
    bits_needed = length_bits
    bytes_needed = (bits_needed + 7) // 8
    raw = digest[:bytes_needed]
    # 用 4 进制 (2 bits/char) 编码
    n_chars = bits_needed // 2
    chars = []
    for i in range(n_chars):
        bit_offset = i * 2
        byte_idx, in_byte = divmod(bit_offset, 8)
        # 取 2 bits（高位优先）
        shift = 6 - in_byte
        if shift >= 0:
            two_bits = (raw[byte_idx] >> shift) & 0b11
        else:
            two_bits = ((raw[byte_idx] << -shift) | (raw[byte_idx + 1] >> (8 + shift))) & 0b11
        chars.append(ZW[two_bits])
    return ''.join(chars)


def main() -> int:
    if not DIST.exists():
        print(f'[watermark] dist not found at {DIST}, skip', file=sys.stderr)
        return 0

    build_id = os.environ.get('GITHUB_SHA') or secrets.token_hex(8)
    timestamp = int(time.time())
    manifest: dict = {
        'build_id': build_id,
        'timestamp': timestamp,
        'pages': {},
    }

    pages = sorted(DIST.rglob('*.html'))
    if not pages:
        print(f'[watermark] no HTML files under {DIST}', file=sys.stderr)
        return 0

    injected = 0
    skipped = 0
    generator_stripped = 0
    GENERATOR_RE = re.compile(r'<meta\s+name="generator"\s+content="VitePress[^"]*"\s*/?>', re.IGNORECASE)

    for html_path in pages:
        rel = html_path.relative_to(DIST).as_posix()

        # 跳过蜜罐自己 + 404 / 任何不希望被水印干扰的
        if rel.startswith('_honeypot/') or rel == '404.html':
            skipped += 1
            continue

        text = html_path.read_text(encoding='utf-8')

        # 顺手抹 VitePress 指纹 generator meta（适用于所有 dist 页面）
        new_text, n = GENERATOR_RE.subn('', text)
        if n:
            text = new_text
            generator_stripped += n

        # Re-injection 守卫：检查 sentinel marker（`<!--lwm-->`），
        # 而不是裸 ZW 字符——VitePress 自己的 heading anchor 会注入 ZWSP，
        # 用通用 ZW 检查会误伤。
        if '<!--lwm-->' in text:
            skipped += 1
            continue

        # 生成 96 bit 水印（48 个零宽字符），payload = path|build_id
        payload = f'{rel}|{build_id}'
        watermark = encode(payload)

        # 用 sentinel HTML 注释包裹，便于 scan_corpus.py 精确定位 / 反查。
        # 包一层 <span hidden aria-hidden=true> 给截屏 / 文本提取工具一个语义钩子。
        marker = (
            f'<span hidden aria-hidden="true" style="display:none">'
            f'<!--lwm-->{watermark}<!--/lwm-->'
            f'</span>'
        )

        # ⚠️ 注入位置：必须在 Vue mount 点（`#app`）之外，否则 hydration 会失败
        # （Vue 期望 `<main>` 第一个子节点是 `.vp-doc`，遇到注释 + 零宽字符就 mismatch
        # → 客户端清空 SSR DOM 重新渲染 → 用户看到空白页 + 仅 footer "最后更新"）。
        # 安全位置 = `</body>` 之前（在 `#app` 容器之外）。
        # 折中：scraper 抓 <article>/<main> 时拿不到水印，但抓全文 / .get_text() 仍能拿到。
        new_text, count = re.subn(r'(</body\s*>)', marker + r'\1', text, count=1, flags=re.IGNORECASE)
        if count == 0:
            # Fallback：找不到 </body> 就放在文档末尾
            new_text = text + marker
            count = 1
        if count == 0:
            html_path.write_text(text, encoding='utf-8')
            skipped += 1
            continue

        html_path.write_text(new_text, encoding='utf-8')
        manifest['pages'][rel] = {
            'watermark': watermark,
            'payload': payload,
        }
        injected += 1

    MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )

    print(f'[watermark] injected {injected} page(s), skipped {skipped}, '
          f'stripped {generator_stripped} generator meta, '
          f'manifest at {MANIFEST.relative_to(ROOT)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())

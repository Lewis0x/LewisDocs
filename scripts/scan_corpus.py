#!/usr/bin/env python3
"""
水印反查工具（骨架）。

输入：怀疑被采集的语料文本（stdin / 文件 / URL）
输出：命中的 (page_path, build_id) 列表

用法：
  # 1) 从 stdin 喂文本
  cat suspicious_corpus.txt | python scripts/scan_corpus.py manifest.json

  # 2) 从 URL 拉文本
  python scripts/scan_corpus.py manifest.json --url https://example.com/page

  # 3) 批量扫文件夹
  python scripts/scan_corpus.py manifest.json --dir ./samples/

依赖：
  - 需要本地或 1Password 中保存的 _watermark-manifest.json
  - manifest 由 scripts/watermark.py 在每次构建后产出
  - GitHub Actions artifact 保留 90 天，重要构建建议另外归档

后续可扩展：
  - 接 Common Crawl / C4 / RedPajama 数据集 API
  - 接 Hugging Face datasets search
  - 自动跑 DMCA 模板填充 (project-docs/dmca-template.md)

当前版本仅实现本地匹配；远程语料库扫描是 TODO。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable

ZW = ['​', '‌', '‍', '⁠']
ZW_PATTERN = re.compile(f'[{"".join(ZW)}]+')


def find_watermarks(text: str, min_len: int = 32) -> list[str]:
    """提取文本中所有零宽字符串（≥ min_len 个连续零宽字符）。"""
    return [m.group(0) for m in ZW_PATTERN.finditer(text) if len(m.group(0)) >= min_len]


def match_against_manifest(found: Iterable[str], manifest: dict) -> list[dict]:
    """把找到的水印对照 manifest 反查页面。"""
    by_wm = {info['watermark']: (path, info['payload'])
             for path, info in manifest['pages'].items()}
    hits = []
    for wm in found:
        # 完全匹配
        if wm in by_wm:
            page, payload = by_wm[wm]
            hits.append({'watermark': wm, 'page': page, 'payload': payload, 'match': 'exact'})
            continue
        # 部分匹配（前缀）—— 防止只截了一段
        for stored, (page, payload) in by_wm.items():
            if wm.startswith(stored[:24]) or stored.startswith(wm[:24]):
                hits.append({'watermark': wm, 'page': page, 'payload': payload, 'match': 'partial'})
                break
    return hits


def scan_text(text: str, manifest: dict) -> list[dict]:
    found = find_watermarks(text)
    return match_against_manifest(found, manifest)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('manifest', help='Path to _watermark-manifest.json')
    p.add_argument('--url', help='Fetch URL and scan')
    p.add_argument('--dir', help='Scan all files under directory')
    args = p.parse_args()

    manifest = json.loads(Path(args.manifest).read_text(encoding='utf-8'))

    if args.url:
        try:
            from urllib.request import urlopen
        except ImportError:
            print('urllib not available', file=sys.stderr)
            return 1
        text = urlopen(args.url).read().decode('utf-8', errors='ignore')
        hits = scan_text(text, manifest)
    elif args.dir:
        hits = []
        for f in Path(args.dir).rglob('*'):
            if f.is_file():
                try:
                    text = f.read_text(encoding='utf-8', errors='ignore')
                except (UnicodeDecodeError, OSError):
                    continue
                hits.extend(scan_text(text, manifest))
    else:
        text = sys.stdin.read()
        hits = scan_text(text, manifest)

    if not hits:
        print('No watermark match.')
        return 0

    print(f'Found {len(hits)} match(es):')
    for h in hits:
        print(f"  - {h['match']:8s}  page={h['page']}  payload={h['payload']}")

    # TODO: 接 Common Crawl / Hugging Face datasets search
    # TODO: 命中后自动生成 DMCA 草稿（填充 project-docs/dmca-template.md）

    return 0


if __name__ == '__main__':
    sys.exit(main())

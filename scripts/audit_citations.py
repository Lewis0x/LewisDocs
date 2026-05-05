#!/usr/bin/env python3
"""
扫所有 source/3.x*.md，抽取每条引用的"声明文本 + 引用类别 + 引用编号 + URL"，
输出 audit_report.csv（用于人工核实）和 audit_report.md（带格式预览）。

用法：
    python scripts/audit_citations.py            # 全量扫描
    python scripts/audit_citations.py --doc 3.1  # 单文档
    python scripts/audit_citations.py --no-url   # 只列没 URL 的引用
    python scripts/audit_citations.py --check-urls  # 顺带做 HTTP HEAD 探活

核实流程：
    1. 跑此脚本生成 audit_report.csv
    2. 在 Excel / Sheets 打开，每行一个声明，按"verified" 列标记 OK / 错 / 改写
    3. 优先核实：[百科] 百科类（最易验证）+ [新闻] / [官方] 时间敏感的（产品发布日期）
    4. 发现错误 → 改 source 文档，重新跑脚本验证

输出 CSV 列：
    file, line, kind, num, url, claim_excerpt, has_url, status_code, verified
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
import time
import urllib.request
import urllib.error
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'source'
REPORT_CSV = ROOT / 'audit_report.csv'
REPORT_MD = ROOT / 'audit_report.md'

KIND = '百科|第三方|官方|新闻|书籍'

# 单条引用：<sup>[百科 1]</sup> 或 <sup>[百科 1][第三方 5]</sup> 或 [百科 1] 直接出现
CITATION_RE = re.compile(rf'\[({KIND})\s*(\d+)\]')

# 参考来源段条目：- [百科 5] xxx https://url（同 link_citations.py）
REF_LINE_RE = re.compile(
    rf'^\s*[-*]\s+\[({KIND})\s*(\d+)\][^\n]*?(https?://[^\s)，。；;）]+)?',
    re.MULTILINE,
)
REF_HEADING_RE = re.compile(r'^##\s+参考来源\s*$', re.MULTILINE)


def parse_references(text: str) -> tuple[dict, dict]:
    """返回 (kind,num) → URL 映射 + (kind,num) → 完整 entry 文本（用于上下文）。"""
    m = REF_HEADING_RE.search(text)
    if not m:
        return {}, {}
    refs_section = text[m.end():]
    next_h2 = re.search(r'^##\s+', refs_section, re.MULTILINE)
    if next_h2:
        refs_section = refs_section[:next_h2.start()]

    url_map: dict[tuple[str, str], str] = {}
    entry_map: dict[tuple[str, str], str] = {}
    for line in refs_section.split('\n'):
        if not line.strip().startswith(('-', '*')):
            continue
        m2 = re.search(rf'\[({KIND})\s*(\d+)\](.*?)(?:(https?://\S+))?$', line)
        if not m2:
            continue
        kind, num, body, url = m2.group(1), m2.group(2), m2.group(3).strip(), m2.group(4)
        body = body.strip(' -,，:：')
        if url:
            url = url.rstrip('.,;:)）"\'》】、 \t\r\n')
            url_map[(kind, num)] = url
        entry_map[(kind, num)] = (body or '') + ((' ' + url) if url else '')
    return url_map, entry_map


def extract_claims(text: str, url_map: dict, entry_map: dict, file_label: str):
    """为每个引用 marker 抽取所在句子作为 claim 上下文。"""
    # 切出参考来源段以前的部分（避免把参考条目本身当 claim）
    m = REF_HEADING_RE.search(text)
    body = text[:m.start()] if m else text

    out = []
    for cm in CITATION_RE.finditer(body):
        kind, num = cm.group(1), cm.group(2)
        # 找所在句子：从前面最近的句号 / 行首到后面最近的句号
        line_start = body.rfind('\n', 0, cm.start()) + 1
        line_end = body.find('\n', cm.end())
        if line_end == -1:
            line_end = len(body)
        line = body[line_start:line_end]
        # 找该 citation 在 line 内的位置
        pos_in_line = cm.start() - line_start
        # claim = line 内 citation 前后各 ~80 字
        # 先剥 HTML / markdown 噪声
        clean = re.sub(r'<[^>]+>', '', line)
        clean = re.sub(r'\[[^\]]+\]\([^)]+\)', '', clean)  # md 链接
        clean = re.sub(r'\*+', '', clean)  # 加粗 / 斜体
        clean = clean.strip()

        line_no = body.count('\n', 0, cm.start()) + 1
        url = url_map.get((kind, num), '')
        ref_entry = entry_map.get((kind, num), '')

        out.append({
            'file': file_label,
            'line': line_no,
            'kind': kind,
            'num': num,
            'url': url,
            'has_url': bool(url),
            'ref_entry': ref_entry,
            'claim': clean[:200],
            'status_code': '',
            'verified': '',
        })
    return out


def head(url: str, timeout: float = 8.0) -> str:
    """HTTP HEAD/GET 探活；返回 status code 或 error 描述。"""
    try:
        req = urllib.request.Request(
            url,
            method='HEAD',
            headers={'User-Agent': 'Mozilla/5.0 (compatible; LewisDocs-AuditBot/1.0)'},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return str(resp.status)
    except urllib.error.HTTPError as e:
        # 405 → HEAD 不被支持，改 GET
        if e.code == 405:
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    return str(resp.status)
            except Exception as e2:
                return f'GET-ERR {type(e2).__name__}'
        return str(e.code)
    except urllib.error.URLError as e:
        return f'URL-ERR {e.reason if hasattr(e, "reason") else str(e)[:40]}'
    except Exception as e:
        return f'ERR {type(e).__name__}'


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--doc', type=str, default=None, help='只扫名称匹配的源文档')
    p.add_argument('--no-url', action='store_true', help='只列出没 URL 的引用')
    p.add_argument('--check-urls', action='store_true', help='HTTP HEAD 探活每个 URL')
    p.add_argument('--throttle', type=float, default=0.3, help='URL 探活间隔（秒）')
    args = p.parse_args()

    files = sorted(SOURCE.glob('3.*.md'))
    if args.doc:
        files = [f for f in files if args.doc in f.name]
    print(f'[i] scanning {len(files)} files', file=sys.stderr)

    all_claims = []
    refs_per_doc: dict[str, dict] = {}

    for fpath in files:
        text = fpath.read_text(encoding='utf-8')
        url_map, entry_map = parse_references(text)
        label = fpath.name.replace('-V4.md', '').replace('-API设计深度剖析', '')
        refs_per_doc[label] = url_map
        claims = extract_claims(text, url_map, entry_map, label)
        if args.no_url:
            claims = [c for c in claims if not c['has_url']]
        all_claims.extend(claims)
        print(f'  {label}: {len(claims)} claim instances', file=sys.stderr)

    # URL 探活（去重后）
    if args.check_urls:
        unique_urls = sorted({c['url'] for c in all_claims if c['url']})
        print(f'[i] checking {len(unique_urls)} unique URLs (throttle={args.throttle}s)', file=sys.stderr)
        url_status: dict[str, str] = {}
        for i, u in enumerate(unique_urls, 1):
            url_status[u] = head(u)
            if i % 10 == 0 or i == len(unique_urls):
                print(f'    {i}/{len(unique_urls)}  {u[:60]} → {url_status[u]}', file=sys.stderr)
            time.sleep(args.throttle)
        for c in all_claims:
            if c['url']:
                c['status_code'] = url_status.get(c['url'], '')

    # CSV
    cols = ['file', 'line', 'kind', 'num', 'url', 'has_url', 'status_code',
            'verified', 'ref_entry', 'claim']
    with REPORT_CSV.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
        w.writeheader()
        for c in all_claims:
            w.writerow(c)
    print(f'[done] CSV: {REPORT_CSV.relative_to(ROOT)} ({len(all_claims)} rows)')

    # Markdown 报告（按 status / kind 聚合统计）
    by_kind = defaultdict(int)
    by_url_status = defaultdict(int)
    no_url = 0
    for c in all_claims:
        by_kind[c['kind']] += 1
        if c['url']:
            by_url_status[c['status_code'] or '(unchecked)'] += 1
        else:
            no_url += 1

    md_lines = [
        '# 引用核实报告',
        '',
        f'- 扫描文档：{len(files)}',
        f'- 引用 marker 总数：{len(all_claims)}',
        f'- 无 URL 引用数：{no_url}',
        '',
        '## 按引用类别',
        '',
    ]
    for k, n in sorted(by_kind.items(), key=lambda x: -x[1]):
        md_lines.append(f'- **[{k}]**：{n} 处')
    if args.check_urls:
        md_lines += ['', '## 按 URL 探活状态', '']
        for s, n in sorted(by_url_status.items(), key=lambda x: -x[1]):
            md_lines.append(f'- `{s}`：{n} 处')
    md_lines += [
        '',
        '## 抽样：前 30 条 + 所有无 URL 的',
        '',
        '> 完整列表见 `audit_report.csv`，可在 Excel 打开标注 verified 列。',
        '',
        '| 文档 | 行 | 引用 | URL 状态 | 声明摘录 |',
        '|---|---:|---|---|---|',
    ]
    sample = all_claims[:30] + [c for c in all_claims[30:] if not c['has_url']][:20]
    for c in sample:
        url_disp = '—' if not c['url'] else (
            f'[{c["status_code"]}]({c["url"]})' if c['status_code'] else f'[link]({c["url"]})'
        )
        claim = c['claim'].replace('|', '\\|').replace('\n', ' ')
        if len(claim) > 80:
            claim = claim[:77] + '…'
        md_lines.append(
            f'| {c["file"]} | {c["line"]} | [{c["kind"]} {c["num"]}] | {url_disp} | {claim} |'
        )
    REPORT_MD.write_text('\n'.join(md_lines), encoding='utf-8')
    print(f'[done] MD:  {REPORT_MD.relative_to(ROOT)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())

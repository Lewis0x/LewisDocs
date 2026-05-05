#!/usr/bin/env python3
"""
扫 source/*.md，输出 T2 候选 jargon 报告（参见 project-docs/05-annotation-methodology.md）。

用法：
    python scripts/find_jargon.py            # 扫所有源文档，输出仓库根 jargon-report.md
    python scripts/find_jargon.py --top 50   # 只看前 50 高频
    python scripts/find_jargon.py --doc 3.1  # 只扫 3.1 AutoCAD
    python scripts/find_jargon.py --min-count 2  # 至少出现 2 次

工具职责：
  - 抽出英文 jargon（单词 / 二元短语 / 大写缩写）
  - 排除：HTML 标签 / URL / 代码块 / 标题 / 表格行 / 引用上下文 / 已注释术语 / 品牌 / 通用缩写 / 常见英文小词
  - 按频次排序，输出报告供人决策

工具**不自动注释**——人决策每条候选术语的 tier。
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'source'
GLOSSARY = SOURCE / '术语表-V4.md'
REPORT = ROOT / 'jargon-report.md'

# T3 通用缩写白名单（已在 glossary 缩写表里）
T3_ABBREV = {
    'API', 'SDK', 'IDE', 'CI', 'CD', 'CICD', 'DSL', 'CLI', 'GUI', 'UI', 'UX',
    'REST', 'RPC', 'BIM', 'JSON', 'XML', 'YAML', 'HTML', 'CSS', 'JS',
    'HTTP', 'HTTPS', 'TLS', 'SSL', 'DNS', 'CDN', 'URL', 'URI',
    'LTS', 'OS', 'PC', 'IP', 'TCP', 'UDP', 'AI', 'ML', 'LLM', 'NLP', 'RAG',
    'CSG', 'CRUD', 'ORM', 'DOM', 'CRT', 'BSD', 'GPL', 'MIT', 'LGPL', 'EULA',
    'PDF', 'CSV', 'TSV', 'PNG', 'JPG', 'SVG', 'GIF', 'MP4', 'MP3',
    'EU', 'US', 'UK', 'CN', 'EN', 'ZH',
    'MVC', 'MVP', 'MVVM', 'TDD', 'BDD', 'OOP', 'FP', 'KISS', 'DRY', 'YAGNI',
    'AOT', 'JIT', 'GC', 'IPC', 'ABI', 'CPU', 'GPU', 'RAM', 'ROM',
    'SaaS', 'PaaS', 'IaaS', 'CMS', 'PWA',
    # 工业 / CAD 通用
    'CAD', 'CAM', 'CAE', 'CAI', 'PDM', 'PLM', 'ERP', 'MES', 'AEC', 'FEA',
    'ISV', 'OEM', 'SI', 'ROI', 'PR', 'QA', 'QC', 'BoM', 'BOM',
    # 文件 / 格式
    'DWG', 'DXF', 'DGN', 'PDF', 'STEP', 'IGES', 'STL', 'OBJ', 'JT', 'IFC',
    'PRT', 'CATPart', 'CATProduct', 'SLDPRT', 'SLDASM', 'SLDDRW', 'FCStd', 'SKP',
    # AutoCAD / CATIA 等具体技术词（部分已在 glossary 单独条目）
    'DWGdirect',
}

# T4 品牌 / 产品 / 公司 / 人名（不标）
T4_BRANDS = {
    # CAD 厂商 / 产品
    'AutoCAD', 'Civil', 'Architecture', 'Mechanical', 'Electrical', 'Map3D', 'Plant3D',
    'CATIA', 'NX', 'Onshape', 'MicroStation', 'SolidWorks', 'SketchUp', 'FreeCAD',
    'Revit', 'Inventor', 'Creo', 'Rhino', 'Grasshopper', 'BricsCAD', 'DraftSight',
    'LibreCAD', 'OpenSCAD', 'KiCad', 'Blender', 'Fusion',
    'iTwin', 'iModel', 'iModelHub', 'iModelBridge', 'OpenRoads', 'OpenBuildings',
    'OpenSite', 'OpenBridge', 'OpenPlant',
    # 公司
    'Bentley', 'Siemens', 'Autodesk', 'Dassault', 'PTC', 'Trimble', 'Spatial',
    'Unigraphics', 'UGS', 'EDS', 'McDonnell', 'Computervision', 'Premise', 'Belmont',
    'Ondsel', 'Apple', 'Google', 'Amazon', 'Microsoft', 'Anthropic', 'OpenAI', 'Meta',
    'Facebook', 'Linus', 'Torvalds', 'Salome', 'CADAM', 'Intergraph', 'Hirschtick',
    'Riegel', 'Mayer', 'Avions', 'IBM', 'HP', 'Mathworks', 'PostgreSQL', 'MySQL',
    'SQLite', 'MongoDB', 'Redis', 'GraphQL',
    # 操作系统 / 工具链 / 框架
    'Linux', 'Windows', 'macOS', 'iOS', 'Android', 'Office', 'Word', 'Excel',
    'Visual', 'Studio', 'VSCode', 'PyCharm', 'IntelliJ', 'Cursor', 'Claude',
    'Anaconda', 'Conda', 'Docker', 'Kubernetes', 'Electron', 'WebGL', 'OpenGL',
    'DirectX', 'Direct3D', 'Vulkan', 'Metal', 'CEF', 'Chromium',
    'Coin3D', 'CASCADE',  # 'Open CASCADE' 拆开后作为品牌词部分
    # 我们自己的工具栈
    'VitePress', 'Vue', 'Vite', 'Mermaid', 'Wrangler', 'Cloudflare', 'Pages', 'Actions',
    'MiniSearch', 'Tippy', 'Floating', 'Markdown', 'Node', 'TypeScript', 'JavaScript',
    'Python', 'Ruby', 'Java', 'Lisp', 'Scheme', 'Fortran', 'COBOL', 'Pascal', 'Perl',
    'Tcl', 'PHP', 'Go', 'Rust', 'Swift', 'Kotlin', 'Scala', 'Lua',
    # 平台 / 服务
    'GitHub', 'GitLab', 'Bitbucket', 'Git', 'NPM', 'PyPI', 'AWS', 'GCP', 'Azure',
    'Vercel', 'Netlify', 'Heroku', 'DigitalOcean', 'Render',
    'APS', 'Forge', 'Hub', 'Connected', 'Construction', 'Center',
    'ENOVIA', 'Teamcenter', 'Windchill', 'Aras',
    'Geographics', 'PowerDraft', 'JMDL',
    # AutoCAD / Bentley / 常见类库前缀
    'AcMgd', 'AcDbMgd', 'AcCoreMgd',
    'AcDbObjectId', 'AcDbObject', 'AcEdJig', 'AcEditor', 'AcApDocument',
    'AcDbBlockTable', 'AcDbBlockTableRecord', 'AcDbDictionary', 'AcDbXrecord',
    'DgnPlatform', 'DgnFile', 'DgnModel', 'DgnAttachment', 'DgnElement', 'DgnGeometry',
    'DgnPlatformNET', 'GeometryNET',
    # FeatureScript / Onshape
    'PartStudio', 'Glassworks', 'OnPy',
    # SketchUp
    'Sketchup', 'HtmlDialog',
    # Mermaid 图节点常见
    'graph',
}

# 太常见的英文小词 / 副词 / 介词（不算 jargon）
COMMON_WORDS = {
    # 冠词 / 代词 / 介词
    'a', 'an', 'and', 'or', 'the', 'is', 'are', 'be', 'to', 'of', 'in', 'on', 'at', 'for',
    'with', 'from', 'by', 'as', 'it', 'this', 'that', 'these', 'those', 'we', 'you', 'they',
    'I', 'me', 'my', 'our', 'your', 'his', 'her', 'their', 'its',
    # 数词
    'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
    'first', 'second', 'third', 'last', 'next', 'previous',
    # 形容词 / 副词
    'new', 'old', 'good', 'bad', 'big', 'small', 'fast', 'slow', 'faster', 'slower',
    'better', 'worse', 'best', 'worst', 'high', 'low', 'long', 'short',
    'open', 'close', 'closed', 'opened', 'show', 'shown', 'hide', 'hidden',
    # 助动词 / 情态
    'has', 'have', 'had', 'do', 'does', 'did', 'will', 'can', 'may', 'should',
    'must', 'shall', 'would', 'could', 'might',
    # 连词 / 副词
    'all', 'any', 'some', 'no', 'not', 'yes', 'also', 'either', 'neither', 'both',
    'between', 'because', 'while', 'when', 'where', 'how', 'why', 'what', 'which',
    'who', 'whom', 'whose', 'than', 'then', 'though', 'although', 'however',
    # 通用动词 / 名词
    'use', 'used', 'using', 'see', 'note', 'notes', 'item', 'items',
    'add', 'remove', 'set', 'get', 'put', 'send', 'receive', 'click', 'tap',
    'view', 'data', 'file', 'files', 'name', 'names', 'type', 'types',
    'class', 'classes', 'function', 'functions', 'method', 'methods', 'object', 'objects',
    'string', 'number', 'array', 'list', 'map', 'tuple', 'value', 'values',
    'key', 'keys', 'parameter', 'parameters', 'arg', 'args', 'argument', 'arguments',
    'return', 'yield', 'import', 'export', 'module', 'package', 'library',
    'app', 'apps', 'application', 'system', 'service', 'services', 'server', 'client',
    'user', 'users', 'page', 'pages', 'site', 'sites', 'web', 'mobile', 'desktop', 'cloud',
    'time', 'times', 'date', 'year', 'years', 'day', 'days', 'month', 'months',
    'group', 'groups', 'level', 'levels', 'layer', 'layers',
    'state', 'states', 'event', 'events', 'task', 'tasks', 'process', 'processes',
    'session', 'sessions', 'context', 'contexts', 'mode', 'modes',
    # CAD 领域通用名词（已在文档自然解释）
    'plugin', 'plugins', 'addin', 'addins', 'extension', 'extensions',
    'feature', 'features', 'part', 'parts', 'assembly', 'assemblies',
    'sketch', 'sketches', 'drawing', 'drawings', 'model', 'models',
    'shape', 'shapes', 'face', 'faces', 'edge', 'edges', 'vertex', 'vertices',
    'point', 'points', 'line', 'lines', 'curve', 'curves', 'surface', 'surfaces',
    'solid', 'solids', 'mesh', 'meshes', 'block', 'blocks',
    'entity', 'entities',  # AutoCAD 专有但已在 glossary AcDb 涵盖
    # 常见动作 / 流程词
    'release', 'releases', 'released', 'install', 'installed', 'installation',
    'license', 'licensed', 'licensing', 'support', 'supported', 'supports',
    'change', 'changes', 'changed', 'update', 'updated', 'updates',
    'create', 'created', 'creates', 'creating',
    'load', 'loaded', 'loading', 'save', 'saved', 'saving', 'edit', 'edited', 'editing',
    'delete', 'deleted', 'deleting', 'remove', 'removed', 'removing',
    'read', 'reads', 'reading', 'write', 'writes', 'writing', 'wrote',
    'design', 'designed', 'designs', 'designing', 'designer', 'designers',
    # 文件扩展名常见
    'arx', 'dbx', 'lsp', 'vlx', 'fas', 'dll', 'exe', 'rb', 'rbe', 'rbz',
    'mdl', 'ma',  # MicroStation file ext (lowercase)
    # 代码语言 fence tag
    'cpp', 'csharp', 'cs', 'java', 'py', 'js', 'ts', 'go', 'rs', 'rb',
    'sh', 'bash', 'zsh', 'fish', 'powershell', 'ps1', 'cmd', 'bat',
    'yaml', 'yml', 'toml', 'ini', 'conf', 'sql', 'http', 'diff', 'patch',
    'vba', 'lisp', 'scheme', 'racket', 'tcl', 'awk', 'sed', 'grep',
    'text', 'plain', 'markdown', 'md', 'rst', 'org',
    'html', 'xml', 'css', 'scss', 'less', 'json', 'jsx', 'tsx', 'vue',
    # URL 协议
    'https', 'http', 'ftp', 'ssh', 'mailto', 'file', 'tel',
    # 太短无意义
    'sup', 'div', 'span', 'br', 'hr', 'tr', 'td', 'th', 'li', 'ul', 'ol',
    'pre', 'em', 'strong', 'code', 'blockquote', 'img', 'svg',
    'href', 'src', 'alt', 'rel', 'target', 'lang', 'dir', 'role',
    # 版本号 / 工程标记
    'v1', 'v2', 'v3', 'v4', 'v5', 'v6', 'v7', 'v8', 'v9', 'v10', 'v17', 'v18',
    'R12', 'R13', 'R14', 'R15', 'R16', 'R17', 'R18', 'R19', 'R20',
    'AC1024', 'AC1027', 'AC1032', 'AC1034',
    # 常用专有词
    'Custom', 'Standard', 'Default', 'Common', 'Public', 'Private', 'Protected',
    'Static', 'Final', 'Abstract', 'Virtual', 'Override',
    'true', 'false', 'null', 'None', 'True', 'False',
    # FAQ / 章节标志
    'Q', 'A', 'V', 'W', 'X', 'Y', 'Z',
    # 形容性
    'invisible', 'visible', 'hidden', 'shown',
    # 文档元
    'TL', 'DR', 'tldr', 'TLDR', 'FAQ',
    # 引用类别（已在缩写表 / 自定义渲染）
    '类别', 'kind', 'category', 'see', 'also', 'detail', 'details',
    'eg', 'ie', 'etc',
}


def load_glossary_terms() -> set:
    """从 glossary.md 提取所有已收录术语（H3 标题 + 缩写表第一列）。"""
    if not GLOSSARY.exists():
        return set()
    text = GLOSSARY.read_text(encoding='utf-8')
    headings = re.findall(r'^###\s+(.+)$', text, re.MULTILINE)
    abbrev_table = re.findall(r'^\|\s*([A-Za-z][A-Za-z0-9/+\-]*)\s*\|', text, re.MULTILINE)
    terms = set()
    for h in headings + abbrev_table:
        h = re.sub(r'[（(].*?[）)]', '', h).strip()
        for piece in re.split(r'[/／\s]+', h):
            piece = piece.strip()
            if piece and re.match(r'^[A-Za-z]', piece):
                terms.add(piece)
                terms.add(piece.lower())
    return terms


_TERM_RE = re.compile(r'<Term[^>]*>([^<]+)</Term>')
_GLOSSARY_LINK_RE = re.compile(r'\[([^\]]+)\]\(/glossary')

def collect_already_annotated(text: str) -> set:
    out = set()
    out.update(m.group(1).strip() for m in _TERM_RE.finditer(text))
    out.update(m.group(1).strip() for m in _GLOSSARY_LINK_RE.finditer(text))
    return out


# ---------------------------------------------------------------------------
# 文本净化：扫描前剥掉 HTML / 代码 / 链接 / URL / 引用 / 表格分隔
def sanitize_text(text: str) -> str:
    """删除所有非 prose 内容，留下"作者写的中文 + 英文 jargon"。"""
    # 1. 整行：fenced code blocks（``` ... ```），整段挖掉
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    # 2. inline code `...`
    text = re.sub(r'`[^`\n]+`', '', text)
    # 3. HTML 标签（含属性、含 self-closing）
    text = re.sub(r'<[^>]+>', '', text)
    # 4. URL（含 http / https / ftp / mailto）
    text = re.sub(r'\b(?:https?|ftp|mailto|file|ssh|tel)://?\S+', '', text)
    # 5. Markdown 链接 [text](url)：去掉 url 部分，保留 text（避免误伤已注释）
    text = re.sub(r'\]\([^)]*\)', ']', text)
    # 6. 引用标记 [百科 N] [第三方 N] [官方 N] [新闻 N] [书籍 N] [回链：…]
    text = re.sub(r'\[(?:百科|第三方|官方|新闻|书籍)\s*\d+\]', '', text)
    text = re.sub(r'\[回链：[^\]]+\]', '', text)
    # 7. 表格分隔行（| --- | --- |）
    text = re.sub(r'^\|[\s\-:|]+\|$', '', text, flags=re.MULTILINE)
    # 8. 标题（# / ## / ### …）—— 整行去
    text = re.sub(r'^#{1,6}\s+.*$', '', text, flags=re.MULTILINE)
    return text


# 抽 token：连续英文 / 英文-数字（单词），可带连字符
TOKEN_RE = re.compile(
    r'\b'
    r'[A-Za-z][A-Za-z0-9]*'              # 主体
    r'(?:[\-/][A-Za-z][A-Za-z0-9]*)*'    # 可选连字符 / 斜杠延续
    r'\b'
)


def is_uppercase_acronym(token: str) -> bool:
    """全大写 + ≥ 2 字母（视为缩写候选）。"""
    return token.isupper() and len(token) >= 2


def is_jargon_candidate(token: str, glossary_terms: set, already: set) -> bool:
    """通过所有过滤的才算 T2 候选。"""
    if not token:
        return False
    # 必须含字母
    if not any(c.isalpha() for c in token):
        return False
    # 全数字 / 太短
    if len(token) < 2:
        return False
    # 全小写 + 长度 < 4：太可能是误判（如 'arx' 'cpp'）
    if token.islower() and len(token) < 4:
        return False
    # 排除常见词
    if token in COMMON_WORDS or token.lower() in COMMON_WORDS:
        return False
    # 排除品牌
    if token in T4_BRANDS or token.lower() in {b.lower() for b in T4_BRANDS}:
        return False
    # 排除 T3 缩写（已在缩写表）
    if token in T3_ABBREV:
        return False
    # 已注释 / 已在 glossary
    if token in glossary_terms or token.lower() in glossary_terms:
        return False
    if token in already:
        return False
    return True


def extract_phrases(line: str) -> list[str]:
    """单 token + 二元短语。二元短语要求两个词都通过基本审查。"""
    tokens = TOKEN_RE.findall(line)
    if not tokens:
        return []
    out = list(tokens)
    # 二元相邻短语
    for i in range(len(tokens) - 1):
        a, b = tokens[i], tokens[i + 1]
        if (
            len(a) >= 3 and len(b) >= 3
            and a.lower() not in COMMON_WORDS
            and b.lower() not in COMMON_WORDS
            and a not in T4_BRANDS and b not in T4_BRANDS
            and a[0].islower()  # phrase 首词通常小写（"clean rebuild" / "hot reload"）
        ):
            out.append(f'{a} {b}')
    return out


def scan_file(fpath: Path, glossary_terms: set) -> tuple[Counter, dict]:
    raw = fpath.read_text(encoding='utf-8')
    already = collect_already_annotated(raw)
    sanitized = sanitize_text(raw)

    counter: Counter = Counter()
    samples: dict = {}

    # 行级扫描，方便记录上下文示例（用 raw text 找上下文，sanitized 来筛词）
    raw_lines = raw.split('\n')
    sanitized_lines = sanitized.split('\n')

    for i, sline in enumerate(sanitized_lines):
        if not sline.strip():
            continue
        for token in extract_phrases(sline):
            if not is_jargon_candidate(token, glossary_terms, already):
                continue
            counter[token] += 1
            # 用 raw 行作为上下文示例（更可读）
            if token not in samples and i < len(raw_lines):
                samples[token] = raw_lines[i].strip()[:120]

    return counter, samples


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--top', type=int, default=80, help='只输出前 N 高频')
    p.add_argument('--doc', type=str, default=None, help='只扫名称匹配的源文档')
    p.add_argument('--min-count', type=int, default=2, help='最低出现次数门槛')
    args = p.parse_args()

    if not SOURCE.exists():
        print(f'source/ not found at {SOURCE}', file=sys.stderr)
        return 1

    glossary_terms = load_glossary_terms()
    print(f'[i] loaded {len(glossary_terms)} glossary terms', file=sys.stderr)

    files = sorted(SOURCE.glob('*.md'))
    if args.doc:
        files = [f for f in files if args.doc in f.name]
    print(f'[i] scanning {len(files)} files', file=sys.stderr)

    global_counter: Counter = Counter()
    per_doc_counter: dict[str, Counter] = defaultdict(Counter)
    samples: dict[str, str] = {}

    for fpath in files:
        c, s = scan_file(fpath, glossary_terms)
        for term, n in c.items():
            global_counter[term] += n
            per_doc_counter[fpath.name][term] += n
            samples.setdefault(term, s.get(term, ''))

    # 输出报告
    lines = [
        '# Jargon 候选清单',
        '',
        f'- 扫描了 {len(files)} 个源文档',
        f'- 总候选数：{len(global_counter)}（按出现频次排序）',
        f'- 已排除：T3 通用缩写、T4 品牌、glossary 已收录、源文中已注释、HTML/code/URL/citation 噪声',
        '',
        '> 用法：人工审视下表，对每条候选决定 tier（T2 单次 / T2→T1 升级 / 不标）。',
        '> 不要直接信任高频术语就一定要标——结合"判定 T2 的快速测试"判断（[方法论 §3](project-docs/05-annotation-methodology.md#3-决策树写作时用-30-秒做决定)）。',
        '',
        '| 候选术语 | 总频次 | 文档分布 | 上下文示例 |',
        '|---|---:|---|---|',
    ]
    shown = 0
    for term, n in global_counter.most_common():
        if n < args.min_count:
            break
        if shown >= args.top:
            break
        dist = sorted(
            ((doc.replace('-V4.md', '').replace('文档', 'D').replace('-API设计深度剖析', ''),
              per_doc_counter[doc][term])
             for doc in per_doc_counter if per_doc_counter[doc][term] > 0),
            key=lambda x: -x[1],
        )
        dist_str = ', '.join(f'{d}×{c}' for d, c in dist[:5])
        sample = samples.get(term, '').replace('|', '\\|').replace('\n', ' ')
        if len(sample) > 100:
            sample = sample[:97] + '…'
        lines.append(f'| `{term}` | {n} | {dist_str} | {sample} |')
        shown += 1

    REPORT.write_text('\n'.join(lines), encoding='utf-8')
    print(f'[done] {len(global_counter)} candidates, top {shown} written to {REPORT.relative_to(ROOT)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())

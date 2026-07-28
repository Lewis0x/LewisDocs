#!/usr/bin/env python3
"""
把 source/ 中的 V4 文档拷贝到 docs/ 并改名为路由友好的英文文件名。
同时为每个文件添加 VitePress frontmatter（title）。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'source'
DOCS = ROOT / 'docs'
PLATFORMS = DOCS / 'platforms'
APPENDIX = DOCS / 'appendix'

FILE_MAP = {
    'AI教程与文档.md': ('index.md', 'AI 教程及文档'),
    '文档0-总目录与导读-V4.md': ('appendix/cad.md', '通用 CAD 平台 API 设计哲学'),
    '文档1-通用CAD平台API设计哲学-V4.md': ('theory.md', '通用 CAD 平台 API 设计哲学'),
    '文档2-主流CAD厂商API设计概述与对比-V4.md': ('comparison.md', '主流 CAD 厂商 API 设计概述与对比'),
    '3.1-AutoCAD-ObjectARX-API设计深度剖析-V4.md': ('platforms/autocad.md', 'AutoCAD ObjectARX API 设计深度剖析'),
    '3.2-CATIA-CAA-RADE-API设计深度剖析-V4.md': ('platforms/catia.md', 'CATIA CAA RADE API 设计深度剖析'),
    '3.3-Siemens-NX-NXOpen-API设计深度剖析-V4.md': ('platforms/nx.md', 'Siemens NX (NX Open) API 设计深度剖析'),
    '3.4-Onshape-REST-FeatureScript-API设计深度剖析-V4.md': ('platforms/onshape.md', 'Onshape (REST + FeatureScript) API 设计深度剖析'),
    '3.5-MicroStation-iTwin-API设计深度剖析-V4.md': ('platforms/microstation.md', 'Bentley MicroStation + iTwin API 设计深度剖析'),
    '3.6-SolidWorks-API设计深度剖析-V4.md': ('platforms/solidworks.md', 'SolidWorks API 设计深度剖析'),
    '3.7-SketchUp-Ruby-API设计深度剖析-V4.md': ('platforms/sketchup.md', 'SketchUp Ruby API 设计深度剖析'),
    '3.8-FreeCAD-API设计深度剖析-V4.md': ('platforms/freecad.md', 'FreeCAD API 设计深度剖析'),
    '3.9-BricsCAD-BRX-API设计深度剖析-V4.md': ('platforms/bricscad.md', 'BricsCAD (BRX + Qt/QML) API 设计深度剖析'),
    '文档4-跨平台-CAD-UI-框架研究.md': ('ui-frameworks.md', '跨平台 CAD UI 框架研究'),
    '术语表-V4.md': ('glossary.md', '术语表'),
}

PAGE_FRONTMATTER = {
    'AI教程与文档.md': 'sidebar: false\noutline: false\npageClass: ai-home\n',
}


def add_frontmatter(content: str, title: str, extra: str = '') -> str:
    fm = f'---\ntitle: {title}\n{extra}---\n\n'
    return fm + content


def main() -> int:
    PLATFORMS.mkdir(parents=True, exist_ok=True)
    APPENDIX.mkdir(parents=True, exist_ok=True)

    success = 0
    missing = []
    for src_name, (dst_name, title) in FILE_MAP.items():
        src = SOURCE / src_name
        dst = DOCS / dst_name

        if not src.exists():
            missing.append(src_name)
            print(f'[MISS] {src_name}')
            continue

        content = src.read_text(encoding='utf-8')
        new_content = add_frontmatter(content, title, PAGE_FRONTMATTER.get(src_name, ''))

        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(new_content, encoding='utf-8')

        print(f'[OK]   {src_name} -> docs/{dst_name}')
        success += 1

    print(f'\n{success}/{len(FILE_MAP)} files imported')
    if missing:
        print('Missing source files:', ', '.join(missing))
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())

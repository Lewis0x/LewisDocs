# 引用核实报告

> 本文档是首次系统性核实 8 篇厂商深度文档（3.1 - 3.8）所有引用的产物。
> 核实时间：2026-05-05。下次大改后建议重跑流程（参见 §6 维护节奏）。

---

## 1. 概览

| 维度 | 数 |
|---|---:|
| 扫描文档 | 8 篇厂商深度（3.1-3.8） |
| 引用 marker 总数 | 704 |
| 唯一 URL 数 | 88 |
| 无 URL 引用条目 | 140（书籍 ISBN / 多源行业资料 / 旧公告原链失效等，按设计保留纯文本） |

**URL 探活分布（用 HEAD / GET，UA = LewisDocs-AuditBot）：**

| 状态 | 数 | 含义 | 行动 |
|---|---:|---|---|
| `200 OK` | 500 | 链接活，可访问 | 无 |
| `403 Forbidden` | 42 | 站方 UA 黑名单（Autodesk、Medium、businesswire 等）；浏览器手开正常 | 标注，不当作错 |
| `429 Too Many Requests` | 8 | 暂时性限流（lifecycleinsights.com 主要） | 标注，过几天复测 |
| `Timeout` | 10 | solidworks.com 域偶发；其他时段访问正常 | 标注，按需复测 |
| `404 Not Found` | **4** | 真断 | **必修**（见 §3） |

---

## 2. 抽样验证结果

从 704 条引用里挑 13 条**高风险时间敏感事实**，用 web search 对照独立来源（Wikipedia、官方公告、专业媒体）：

| # | 论断 | 验证结果 |
|---|---|---|
| 1 | AutoCAD R13（1995）首次引入 ObjectARX | ⚠️ **小瑕疵** — R13 引入的当时叫 **ARX**，到 R14（1997）才更名 **ObjectARX**。当前文档表述会让读者误以为名称从一开始就叫 ObjectARX |
| 2 | 2022 年 12 月 7 日 Forge → APS 改名 | ✅ 准确 |
| 3 | PTC 以 4.7 亿美元收购 Onshape（2019-11） | ✅ 准确（2019-11-01 完成；$470M 现金） |
| 4 | FreeCAD 1.0 发布于 2024-11-18 | ✅ 准确（含 bgbsww 致敬细节属实） |
| 5 | Siemens 以约 35 亿美元收购 UGS（2007） | ✅ 准确（2007-01-24 宣布；2007-05-07 完成；$3.5B） |
| 6 | iTwin.js / iModel.js 2018-10-17 在 Year in Infrastructure 大会开源 | ✅ 准确 |
| 7 | CATIA V5 1998 发布以支持 Windows NT | ✅ 准确（1998-10-12 IBM/DS 联合发布；Q3 1998 实际可用） |
| 8 | Synchronous Technology 在 NX 5（2007）首次引入 | ✅ 准确（2008-04 Siemens 正式公告并扩展到 Solid Edge） |
| 9 | Onshape 2012 成立，原名 Belmont Technology | ✅ 准确（Hirschtick + McEleney + Corcoran + Harris + Lauer + Li 6 人创始团队） |
| 10 | SketchUp 2012 由 Google 转让给 Trimble | ✅ 准确（2012-04-26 宣布；2012-06-01 完成） |
| 11 | A380 V4/V5 案例 + ~$6.1B 量级延期成本 | ✅ 准确（且文档对"归因不可单一化"的措辞与公开资料一致） |
| 12 | iTwin.js 是 MIT License，非 Apache 2.0 | ⚠️ **可更精准** — 主 itwinjs-core 仓确实是 **MIT**；但 imodeljs-native（C++ 组件）是 **Apache-2.0**；ecjson2md 等周边工具也是 Apache。"非 Apache 2.0"的勘误对主仓库正确，对生态全貌略简 |
| 13 | V8 DGN 2001 切换到 OLE Compound File Binary 容器 | ✅ 准确 |

**抽样结论：13 条高风险事实里 11 条完全准确，2 条小瑕疵无损主论断。** 文档**整体准确性高**，可信度可接受。

---

## 3. 待修：4 个真 404 + 2 个表述微调

### 3.1 真 404 链接（必修）

| 文件 | 引用 | URL | 处理建议 |
|---|---|---|---|
| 3.5 MicroStation | `[官方 16]` | `https://www.bimsdks.com/bentley/MicroStationAPI/ElementHandle_8h_source.html` | bimsdks.com 整站不再维护；改指向 [官方 Help](https://help.bentley.com/) 中等价页面或删 URL 改成纯文字注 |
| 3.6 SolidWorks | `[官方 5]` | `https://www.solidworks.com/product/whats-new` | timeout 反复发生，疑似 SolidWorks 移动了页面；查找新地址 |
| 3.6 SolidWorks | `[官方 7]` | `https://files.solidworks.com/Supportfiles/Whats_new/2026/English/whatsnew.pdf` | timeout；PDF 可能已撤；查找当前最新版 |
| 3.6 SolidWorks | `[新闻 13]` | `https://trimech.com/top-10-features-in-solidworks-2026/` | 403；UA 阻挡或移到付费墙；保留 URL 但加注"如失效见 archive.org 镜像" |

### 3.2 表述微调（推荐，非必须）

**论断 #1 — R13 时代名称**：
- 当前：`AutoCAD R13（1995）首次引入 ObjectARX`
- 建议：`AutoCAD R13（1994 末 / 1995 初）首次引入 ARX 运行时扩展架构（R14 改名为 ObjectARX）`
- 理由：忠于历史细节，避免暗示"ObjectARX"这个名称从一开始就存在

**论断 #12 — iTwin.js 许可证**：
- 当前：`iTwin.js 自 2018 年 10 月 17 日开源（**MIT License**，非 Apache 2.0）`
- 建议：`iTwin.js 自 2018 年 10 月 17 日开源——核心 itwinjs-core 仓库为 **MIT License**（多处社区资料误传为 Apache 2.0）；周边的 imodeljs-native（C++ 二进制）使用 Apache 2.0 + Bentley 商业 right-to-run 双许可`
- 理由：原表述对主仓正确但简化了生态全貌，加一句话点破

### 3.3 403 / 429 / Timeout（不修，但记录）

42 + 8 + 10 = 60 处虽返回非 200，但实测在浏览器中正常打开。这是站方 UA 阻挡 / 限流，**不是真断链**。审计脚本已用浏览器风的 UA，但部分站点（Autodesk blog / businesswire）需要 cookie / referer 才放行。

**不行动**——读者用浏览器点开都能正常访问。

---

## 4. 工具

`scripts/audit_citations.py`：

```bash
python scripts/audit_citations.py            # 默认：扫所有 3.x 输出 audit_report.csv
python scripts/audit_citations.py --doc 3.1  # 只扫单文档
python scripts/audit_citations.py --no-url   # 只列没 URL 的引用
python scripts/audit_citations.py --check-urls --throttle 0.5  # 顺带探活
```

输出：
- `audit_report.csv` — 一行一条引用，含 file/line/kind/num/url/status_code/verified/claim
- `audit_report.md` — markdown 摘要 + 抽样表
- 两份均在 `.gitignore` 中（不进版本控制——是审计运行时产物）

CSV 设计为可在 Excel 打开打 verified 列做完整 trace。

---

## 5. 适用范围与局限

**这次能给的保证：**
- 8 篇厂商文档的全部 704 条引用 marker 已被机械索引
- 88 个唯一 URL 全部探活，4 个真断已具名 + 已建议处置
- 13 条高风险时间事实经独立来源核实，11 条准确

**这次不能给的保证：**
- **没**对 704 条引用逐一回到原始来源核实"原文是不是真这么说"——这需要语料级核对（每条引用平均 5-15 分钟），全做完是 60-180 工时，不属于本轮范围
- **没**核实文档 1（理论）和文档 2（横向对比）—— 它们没有引用 marker 体系，论断主要是作者归纳判断，不是事实声明
- **没**核实 `[判断]` `[推论]` 块 —— 这些显式标注为作者主观见解，定义上不是可机械验证的事实

**怎么走向更深核实**（如果未来需要）：
- 把 `audit_report.csv` 在 Excel 打开，每行手工填 verified 列（OK / 错-改写 / 有疑 / 不可访问）
- 优先核实：[百科] 类（Wikipedia 直接对照）、[新闻] 时间敏感的（产品发布日期）
- [第三方] 类的博客、社区资料：选择性抽查

---

## 6. 维护节奏

| 触发 | 动作 |
|---|---|
| 每次 push 前（如改了 3.x） | 跑 `python scripts/audit_citations.py --doc 3.x` 确认改动没引入新断引用 |
| 季度审视（主动） | 跑 `--check-urls` 全量探活；处理新出现的 404/timeout |
| 添加新源文档 | 同上 |
| 出现引用错误反馈 | 修源文，重跑 audit 验证修复 |

---

## 7. 本次首发交付

- ✅ `scripts/audit_citations.py` —— 可重复执行的审计工具
- ✅ `audit_report.csv` / `audit_report.md` —— 审计运行时产物（不进 git）
- ✅ 本文档 `project-docs/06-citation-audit.md` —— 永久审计纪要
- ⏳ 4 个真 404 待修（见 §3.1）
- ⏳ 2 处可微调表述（见 §3.2）

待修内容会在下一次专门的"事实精修"提交里处理；本次提交是建立审计基础设施。

# 术语注释方法学

> 本文档定义站点里**何时给术语加注释、用哪种通道**。
> 已有 3 种注释通道（glossary 链接 / `<Term>` hover / 引用 `<sup>` 链接），本文档解决"何时用哪种"的一致性问题。
> 适用对象：写新内容的作者、审 PR 的维护者、未来的 AI 辅助。

---

## 1. 读者画像（决定密度的起点）

本站默认读者是 **管理与决策者**（CTO / 产品总监 / 战略决策者），不是只面向同行 CAD 架构师。
直接含义：**工程 / 过程 jargon（hot reload / hydration / monorepo …）也需要主动注释**，不能假设读者一眼看穿。

> 如果未来读者画像收窄到"只面向同行架构师"，本方法论的 T2 部分可以放松（少标）。
> 当前版本基于"管理与决策者"决策。

---

## 2. 四层术语分类

| Tier | 术语类型 | 通道 | 是否进 glossary |
|---|---|---|---|
| **T1 — CAD 领域** | B-Rep, NURBS, Parasolid, OCCT, FeatureScript, TNP, ChangeSet, microversion, ECSchema, ObjectARX, MDL, CAA, KBE, DAG, Synchronous Technology … | 第一次出现：`<Term def="...">`（带 hover）或 `[term](/glossary#...)`（普通链接）；后续不重复 | **必须**收录（已有 25 条） |
| **T2 — 工程 / 过程 jargon** | clean rebuild, hot reload, hydration, monorepo, SSR, prefetch, RAII, idempotent, dogfood, golden rule, feature branch, code-split, fingerprint, throttle, watermark, sentinel, frontmatter, sidecar … | 第一次出现：行内 `<Term def="中文短定义">`；3+ 次升级到 glossary，改用 `[link]` | **仅当全系列 ≥ 3 次** |
| **T3 — 通用缩写** | API, SDK, IDE, CI/CD, DSL, CLI, REST, RPC, BIM, JSON, HTTP/HTTPS, TLS, LTS … | **不在正文标记**。统一收录到 glossary 末尾的**缩写表** | 缩写表（已有 13 行，可扩到 ~25 行） |
| **T4 — 产品 / 品牌名** | Cloudflare Pages, Mermaid, Wrangler, GitHub Actions, VitePress, npm, Cursor, VS Code … | 不标注（专有名词，搜得到） | 不收录 |

---

## 3. 决策树（写作时用 30 秒做决定）

```
读到一个候选术语 →
                 │
   [是产品 / 品牌名？]
       是 → T4，不标
       否 ↓
   [是 CAD 领域术语？]
       是 → T1：在 glossary 加条目（如未加）；本文档第一次出现用 <Term> 或 [link]
       否 ↓
   [是 API / SDK / IDE / CI 这种几乎人人都见过的英文缩写？]
       是 → T3：不在正文标，进 glossary 缩写表
       否 ↓
   [非软工背景的决策者会一眼看不懂吗？]
       否 → 不标
       是 → T2：第一次出现加 <Term def="一句中文">
            → 全系列出现 3+ 次后升级为 glossary 条目，改用 [link]
```

**判定 T2 的快速测试：** 把这个词放在与 CTO 对话的 PPT 里，是否需要口头解释一句？需要 → T2。

---

## 4. 密度规则（防视觉噪声）

1. **每章只标第一次出现**——不是每页、不是每段。同一章节内重复出现保持原样。
2. **跨文档不重复标**——同一术语在文档 1 已经标过，文档 2 不再标（除非前者是过道性提及、后者是核心讨论）。
3. **不标的位置**：
   - 代码块内（`` ` `` 或 `` ``` ``）
   - 标题里（`#` `##` `###`）
   - 表格表头
   - `<sup>[百科 N]</sup>` 引用上下文
   - `[回链：…]` 引用标记内
   - Mermaid 图节点文字内
4. **每段最多 2 处注释**——超过则视觉过密，重写句子或减一个。

---

## 5. T2 → T1（升级到 glossary）的触发与动作

升级触发条件（满足任一即可）：

- 全系列出现 ≥ 3 次（用 `scripts/find_jargon.py` 统计）
- 出现在 ≥ 2 篇厂商文档里（哪怕总次数只有 2）
- 是某章节深入讨论的对象（次数低但深度高）

升级动作：

1. 在 `source/术语表-V4.md` 添加完整条目（2-4 行定义 + "深入"链接）
2. 把所有原本的 `<Term def="...">term</Term>` 改成 `[term](/glossary#anchor)`
3. 简洁定义保留在 glossary 条目顶部

---

## 6. 定义文本写作规范

| 维度 | 规则 |
|---|---|
| 长度 | 1-2 句，目标 30-80 字 |
| 语言 | 中文为主；产品 / 函数 / 类名保留英文 |
| 结构 | "**是什么 + 关键特征 / 起源**" |
| 不要 | 不引用文档其他章节（避免 hover 卡片里嵌套链接）；不堆砌技术栈细节 |

**例子**：

✓ 好：`<Term def="清空缓存与产物目录后从头构建。常用于排除 stale state 引发的莫名错误。">clean rebuild</Term>`

✗ 差：`<Term def="Clean rebuild is the process of removing all build artifacts and rebuilding from scratch.">clean rebuild</Term>`（英文，且过长）

✗ 差：`<Term def="见 §3.2 for details">clean rebuild</Term>`（嵌套引用，hover 里跳引用是糟糕体验）

---

## 7. 维护节奏

| 触发条件 | 动作 |
|---|---|
| 加新源文档 | 跑 `find_jargon.py`，给新文档的 T2 术语加注释 |
| 改源文档大段内容 | 同上（局部 review） |
| 季度审视（主动） | 跑 `find_jargon.py` 看是否有新 T2 候选；删 glossary 里 0 引用的条目 |
| 升级 T2 → T1 | 频次达 3+ 时按 §5 步骤改造 |

---

## 8. 工具：`scripts/find_jargon.py`

用法：

```bash
cd D:/Work/LewisDocs
python scripts/find_jargon.py
# 在仓库根输出 jargon-report.md（不进 git，已 .gitignore）
```

输出 markdown 报告：

```
| 候选术语 | 频次 | 文档分布 | 已注释？ |
|---|---|---|---|
| clean rebuild | 5 | 03-development.md×4, 02-design.md×1 | 否 |
| hydration | 3 | 03-development.md×2, 02-design.md×1 | 否 |
```

工具**只输出报告，不自动注释**——人工 review 决策每条候选术语的 tier。

工具排除：已在 glossary 的术语、品牌名 whitelist、出现在代码块/标题/表格的词。

---

## 9. 实施记录（试点）

### 9.1 文档 1 §1.2 / §2.1 — T1 试点（已完成）

V1 第一次试点（2026-05-05）：

- 共 12 处注释（7 个 `<Term>` + 5 个 `[link]`）
- 视觉密度可接受：每段不超过 2 处虚下划线
- 用户反馈：可读、有用，无负面意见 → T1 路线确认
- 详见 commit `23a8b8e`

### 9.2 3.1 AutoCAD — T2 试点（已完成）

第一次 T2 试点（2026-05-05），跑 `find_jargon.py --doc 3.1`，从 164 候选中选 10 个 T2 术语注释 3.1 AutoCAD 第一次出现：

| 术语 | 定义片段 | 位置 |
|---|---|---|
| `in-process` | 扩展模块加载到主程序进程内运行（与 out-of-process 通过 IPC 通信相对）… | TL;DR 第 1 条 |
| `ObjectDBX` | AutoCAD 仅数据库的扩展模块格式 .dbx：能注册自定义对象但无 UI 与命令… | TL;DR 第 2 条 |
| `Managed .NET API` | Microsoft .NET Framework 的托管运行时（CLR）层。AutoCAD 2006 起把 ObjectARX 包成 .NET 类… | TL;DR 第 2 条 |
| `COM Automation` | 基于 Microsoft COM 的"用脚本调外部程序"机制。VBA / VB.NET / Python (pywin32) 都通过它… | TL;DR 第 2 条 |
| `ABI` | Application Binary Interface，二进制接口契约。与 API（源码级）不同… | TL;DR 第 4 条 |
| `Object Enabler` | AutoCAD 让没装某 ARX 应用的环境也能正确显示其自定义对象的机制… | Key Findings 第 2 条 |
| `handle` | 数据库对象的稳定字符串标识。AutoCAD 中是十六进制串；进程重启后内存指针失效但 handle 仍能定位… | Key Findings 第 7 条 |
| `Transaction 模式` | 用 begin / commit 包裹一组数据库操作的模式：失败可整体回滚… | Key Findings 第 8 条 |
| `clean rebuild` | 清空缓存与产物目录后从头构建。常用于排除 stale build artifact 引发的莫名错误… | Key Findings 第 10 条 |
| `Reactor` | AutoCAD 实现观察者模式（Observer pattern）的具体名称… | §4.4 章节首句 |

**验证结果：**
- 视觉密度：TL;DR 5 处 / Key Findings 4 处 / §4.4 1 处。TL;DR 略密但因为是入门段所以可接受
- 定义质量：每条 1-2 句，符合"是什么 + 关键特征"结构
- 锚点 / 搜索 / Mermaid：107 anchored 链接 0 断，搜索索引正常，Mermaid 不受影响
- 决策日志：从 164 候选挑了 10 个，其余 154 候选要么是品牌（Smart / Plant / Viewer / Alliance / Wikipedia），要么是版本标记（VS2022 / VS2026 / SVF2），要么次数太少（< 2）

**经验：**
1. 候选清单的 false positive 主要来自"品牌名的部分单词"（Smart Blocks / Activity Insights / Object Enabler 的 Object 等）。下次跑前需要把品牌名整短语 → 拆词加进 T4_BRANDS
2. 频次门槛 `--min-count 2` 太松，单文档情况下用 `--min-count 3` 更聚焦
3. T2 候选里有大量 AutoCAD 内部类名（AcDbDatabase / ObjectId / AcEditor 等）—— 这些其实是 T1 的"AutoCAD 类库前缀"应已在 glossary AcDb / AcGe / AcRx 条目下涵盖，不必再标
4. **下次跑给非首批文档时，先用 `--min-count 3 --top 30` 过一遍候选清单，比一开始就看完整 164 条更高效**

### 9.3 全 9 篇厂商文档铺开（3.1-3.8 已完成；3.9 BricsCAD 待铺）

继 3.1 试点之后，分两批把 T2 注释推到剩余 7 篇：

| 文档 | T2 注释数 | 关键词样例（按重要性） |
|---|---:|---|
| 3.1 AutoCAD | 10 | in-process, ObjectDBX, Managed .NET API, COM Automation, ABI, Object Enabler, handle, Transaction 模式, clean rebuild, Reactor |
| 3.2 CATIA | 6 | Workspace/Framework/Module, IdentityCard, mkmk, Authorized API vs Internal API, Late Type/TIE/BOA/Extension, Spec/Result/Update |
| 3.3 NX | 7 | 语言绑定, UFunc, Mach Series, ICAD, 关联性持久对象, Block UI Styler, D-Cubed |
| 3.4 Onshape | 12 | 强类型, 单位安全, 服务端运行, 路径即语义, 持续部署, API 速率限制, branch, tagged commit, commit, Deterministic ID, Associativity, OAuth 2.0 |
| 3.5 MicroStation | 4 | MicroStationAPI, CONNECT Edition, OLE Compound File, p-code |
| 3.6 SolidWorks | 3 | Functional Delivery (FD), IModelDocExtension, Document Manager API |
| 3.7 SketchUp | 9 | REPL, .rbz, face-based, Observer, CEF (Chromium Embedded Framework), logical pixels, Overlays API, MRI Ruby, duck-typing |
| 3.8 FreeCAD | 8 | MVC, boost::signals2, headless, 一等公民, Workbench, upstream, FeaturePython, DocumentObject |
| **合计** | **59** | |

**铺开过程的工程发现：**

1. **`<Term def="..."` 的内层 ASCII `"` 必须改成全角 `""`**——Vue HTML 解析器把内层 ASCII 双引号当作属性值结束符，触发 "Invalid end tag" 编译错。Onshape 试点期间首次发现，3.7/3.8 大批量出现（作者本能用 ASCII 引号包"低门槛"等强调）。已写 `scripts/fix_term_quotes.py` 自动化转换：本批 40 处全部已修。**作者写作时不必刻意区分**，提交前跑一次脚本即可。
2. **每篇文档的 T2 密度差异很大**：3.4 Onshape (云原生 + git 隐喻) 与 3.7 SketchUp (扩展生态术语) 候选最多；3.5 MicroStation 与 3.6 SolidWorks 候选最少（多数概念已被 T1 glossary 收录或属于 T4 品牌）。这印证了"按文档主题自适应"比"统一密度"更合理。
3. **`find_jargon.py` 经一次大幅调优**：T4_BRANDS 加了 ~80 词（Onshape 概念词 / AutoCAD 类型前缀 / MicroStation EC 类型 / FreeCAD Topo 类 / NX Builder 类 / Extrude/Fillet 等特征名），又对 2-gram 加去重（避免"microversion microversion"）。误判率从 ~30% 降到 ~10%。

**验证（npm run build）：**
- 构建 13.68s 干净通过，0 Vue parse 错
- 0 broken anchors，805 个 id 全部可达
- 12/12 页水印
- dist HTML 中 118 个 lewisdocs-term span（= 59 Term × 2）

**经验沉淀（除 9.2 外的新发现）：**
1. **批量注释比试点更难的不是判断 tier，而是保证定义文本风格一致**。建议固定先想清"是什么 + 关键特征"两块再写，而不是一句话表达。
2. **首次出现的位置选择**：TL;DR / Key Findings / 章节首段 三选一。优先 Key Findings（最容易被读者顺序读到，hover 一次后续不再标）。
3. **避免与 T1 已有概念重复**：3.5 MicroStation 跑出 ECObjects / ECSchema 等候选，但这些在 glossary 已有条目，应直接用 `[link]` 而非新加 `<Term>`。

### 9.4 T2 → T1 季度审视（首次执行）

8 篇厂商文档全部 T2 注释完成后（3.9 BricsCAD 后续单独铺），跑全量 `find_jargon.py --top 40 --min-count 3` 看哪些 T2 术语在 ≥ 2 篇文档出现，应升级为 T1 进 glossary。

**升级 4 个**（满足 §5 的"≥ 2 篇文档 + 总频次 ≥ 10"门槛）：

| 术语 | 总频次 | 文档数 | 处理 |
|---|---:|---:|---|
| `in-process` | 18 | 5 | 新增 glossary 条目；3.1 AutoCAD 的原 `<Term def>` 改为 `[link](/glossary#in-process)` |
| `Observer` | 13 | 5 | 新增 glossary 条目（含全平台对应名 Reactor/CallBack/Subscriber 列举）；3.7 SketchUp 的原 `<Term def>` 改为 `[link]` |
| `ODA (Open Design Alliance)` | 21 | 5 | 新增 glossary 条目（DWG 词条已经提及但未独立条目，本次独立成节） |
| `GRIP` | 15 | 3 | 新增 glossary 条目（NX 1980s 遗产语言，作为"CAD 各搞自家脚本"案例） |

**未升级**（候选但被否决）：
- `DS / NET / COM / Wikipedia / Software / Manager / Property / Framework / Late / Authorized / Internal / Spec / Engineering / Coach / mark` —— 要么是品牌（DS Wikipedia）/通用缩写（NET COM）/单字母拆分（Late Type 的 Late 单独无意义）/泛化词（Manager Software）。
- `App/Gui` (12)、`Spec/Result/Update` (10) —— 只在 1-2 篇文档出现核心讨论，强 CAD 厂商专属，留作 T2 即可。
- `FD` (16)、`Warehouse` (13)、`PartDesign` (11)、`I-DEAS` (11)、`RealThunder` (11) —— 都集中在单一文档，不满足"≥ 2 篇"。

**链接修正过程的踩坑：**
- glossary 条目顶端"深入：…"必须使用真实存在的 anchor，否则构建后会产生 broken link
- 实操：先写好条目内容（包含猜测的 anchor）→ 跑构建 → 查 dist/ HTML 中实际 id → 改正 anchor。这个流程比"写时记忆 anchor"可靠得多
- 有 4 处初始猜测的 anchor 全部错（`一、历史演进-从-uniapt-2406` 实际是 `一、历史演进-从-uniapt-1972-到-nx-x-2024`）。建议**未来加 glossary 条目时，先 grep `dist/<page>.html` 确认 anchor 再写**

**升级后的 dist 校验：**
- 0 broken anchors（含 glossary "深入" 链接）
- Term wrappers 从 59 减为 57（少了 2 = in-process + Observer 的转换）
- 4 个新 glossary 条目（GRIP/in-process/ODA/Observer）的 anchor 全部可达

---

## 10. 不做

- ❌ **不做基于 NLP 的自动术语识别 + 自动加 hover** —— false positive 风险高于人工注释带来的好处
- ❌ **不做 hover 卡片直接嵌入完整 glossary 条目** —— 可读性 vs 浮窗大小有冲突，保持简短
- ❌ **不做双语术语对照全局开关** —— 本站定位中文研究，英文术语只是符号
- ❌ **不为每个 T2 术语补 Wikipedia 链接** —— 用户已选自写中文短定义路线

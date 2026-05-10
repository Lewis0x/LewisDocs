# 主流 CAD 厂商 API 设计概述与对比（全景矩阵）

> 文档 2｜通用 CAD 平台 API 设计哲学系列
>
> **本文档定位**：横向比较 9 个主流 CAD 平台的 API 设计——AutoCAD ObjectARX / CATIA CAA / NX Open / Onshape / MicroStation+iTwin / SolidWorks / SketchUp Ruby / FreeCAD / BricsCAD BRX。建立全景对比矩阵，提炼跨平台共性模式，给出选型决策框架。
>
> **与文档 3.x 的关系**：文档 3.x 系列对每个平台做单独深度剖析；本文档不重复细节，专注横向比较与归纳。读者可将本文档作为"全景导航"，需要详情时回查 3.x。

---

## 阅读约定

- 来源标注：本文档的事实陈述基于文档 3.1-3.9 系列报告
- `> **[评论]**`：本报告作者对横向比较与模式归纳的判断，非任何厂商的官方陈述
- ⚠️：勘误、强调或重要 caveat
- ⭐：本文档作者认为最具学习价值的设计模式
- 部分论断附**证据等级**标签 A/B/C，与文档 1 同标准。这是写作辅助标签，不是客观评分
- 回链格式：`[回链：3.4 §三 核心数据模型]` 表示文档 3.4 第三章

---

## 重要前置说明

本文档基于 9 个平台样本（5 个机械 CAD + 3 个 AEC/设计师 + 1 个 DWG 兼容路径），样本偏向参数化 CAD（5/9）。下文的"模式""趋势""独有设计"等归纳都是**对样本范围内的观察**，未覆盖 PTC Creo、Inventor、Solid Edge、Rhino+Grasshopper、Revit、ArchiCAD 等其他重要平台。"较罕见""较少见""广泛使用"等表述均指样本范围。

---

## TL;DR：9 个平台的一句话

| # | 平台 | 一句话定位 |
|---|---|---|
| 3.1 | **AutoCAD ObjectARX** | 30+ 年的 [in-process](/glossary#in-process) 原生 C++ SDK；六层金字塔分层服务设计师/IT/ISV/Web；Custom Entity + Object Enabler 平台经济学的经典实现 |
| 3.2 | **CATIA CAA RADE** | 严格组件 + 接口模型；编译期强制 Authorized vs Internal API 边界；Spec/Result/Update 声明式建模；面向超大型工程组织 |
| 3.3 | **Siemens NX (NX Open)** | 样本中较罕见的"Common API 四语言完全对等"；Builder + Commit 范式；Synchronous Technology 直接编辑 + 关联性维持 |
| 3.4 | **Onshape** | 样本中较少见的 web-only / cloud-native 一等公民；Git 式数据模型（branch/merge/microversion）；FeatureScript 强类型 + 单位安全的领域语言 |
| 3.5 | **MicroStation + iTwin** | "schema-first"工程哲学（ECSchema/BIS）；桌面 + 云双轨而非替代；iModel 联邦数字孪生而非单一权威 |
| 3.6 | **SolidWorks** | COM Automation 单层架构刻意简化；IModelDocExtension 接口版本化的 COM 时代范式；面向中端工程师的"上手快、深度有限" |
| 3.7 | **SketchUp Ruby** | 嵌入式脚本极简哲学的代表；17+ 类高粒度 [Observer](/glossary#observer-观察者模式)；Face-based 简化几何换性能；保守上云不破坏 Ruby 生态 |
| 3.8 | **FreeCAD** | 开源参数化 CAD 讨论中最常被引用的平台之一；App/Gui 严格 MVC 分离；Python 集成较深（FeaturePython）；22 年才到 1.0 的工程治理节奏值得关注 |
| 3.9 | **BricsCAD (BRX + Qt/QML)** | 样本中唯一以"ARX 源码兼容"为核心战略的非 Autodesk 平台；ACIS 内核（Spatial）+ ODA Drawings SDK；2021-2022 起 wxWidgets/MFC → Qt/QML 渐进迁移（约 50 人年）；Hexagon (2018+) → Octave (2025+) |

---

## 一、谱系分类：6 个分类维度

### 1.1 按行业领域分类

```
┌─────────────────────────────────────────────────────────────┐
│ 机械 CAD（高端，航空航天 + 汽车 OEM + 重型装备）              │
│ - CATIA CAA       （Dassault）                              │
│ - Siemens NX      （Siemens）                               │
│ - SolidWorks      （Dassault）                              │
│ - Onshape         （PTC）                                   │
│ - FreeCAD         （开源）                                  │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│ AEC（建筑 + 基础设施 + 市政）                                │
│ - AutoCAD         （Autodesk，2D 主导 + 3D 多用途）         │
│ - MicroStation + iTwin（Bentley，基础设施工程）             │
│ - SketchUp        （Trimble，景观/室内/概念设计）            │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│ DWG 兼容路径（与 AutoCAD 源码 / 文件格式互通）               │
│ - BricsCAD        （Hexagon → Octave，多产品线 Lite/Pro/   │
│                     BIM/Mechanical/Ultimate；ARX 源码兼容）  │
└─────────────────────────────────────────────────────────────┘
```

⚠️ 边界并非绝对——AutoCAD 也用于机械（Mechanical Toolset）；CATIA 也用于建筑（Frank Gehry 等）；BricsCAD 通过 Mechanical / BIM 模块跨入机械与 BIM 领域。但主战场清晰。

### 1.2 按 API 风格分类

```
in-process 原生 C++ SDK
├── AutoCAD ObjectARX        - C++ + .NET wrapper
├── BricsCAD BRX             - C++ + .NET（与 ARX 源码兼容，二进制隔离）⭐
├── CATIA CAA RADE           - C++ + Authorized/Internal 边界
├── MicroStationAPI          - C++ + DgnPlatformNET
└── FreeCAD (App + Workbench) - C++ + Python 双向

Common Object Model + 多语言对等
└── NX Open (Common API)     - C++/C#/Java/Python/VB.NET 自动生成绑定 ⭐

COM Automation 单层
└── SolidWorks               - VBA/C#/VB.NET/C++ via COM

REST API + 领域语言
└── Onshape                  - REST API + FeatureScript ⭐

嵌入式脚本主体
├── SketchUp Ruby            - 嵌入 MRI Ruby 解释器
└── FreeCAD Python           - 嵌入 CPython
```

### 1.3 按几何内核分类

| 内核类型 | 平台 | 特征 |
|---|---|---|
| **Parasolid**（Siemens）| NX、Solid Edge、SolidWorks（DS 旗下用 Siemens 内核）| 工业级 B-Rep，授权关系 |
| **CGM**（DS 自研，社区简称）| CATIA V5/V6/3DX | 自研，闭源，V5=V6=3DX 共享 |
| **OCCT**（Open CASCADE）| FreeCAD（开源 + 商业双轨 license）| LGPL，开源工业级中较广泛使用的选择 |
| **Onshape PartStudio Engine**（不公开）| Onshape | 基于 Parasolid（社区共识，PTC 收购前历史复杂）|
| **Face-based polygon**（无 B-Rep）| SketchUp | 平面 Face + 直线 Edge，性能极优但能力受限 |
| **DGN 几何 + SmartSolid（社区猜测基于 ACIS）**| MicroStation | 自抽象层包装 |
| **AcGe + ObjectARX 几何**| AutoCAD | 自研，2D 主、3D 简单几何 |

⭐ **CAD 业界值得注意的现象**：DS 旗下 SolidWorks 使用 Siemens 旗下 Parasolid——两个最大 PLM 厂商在中端 CAD 内核共享多年。

### 1.4 按云原生策略分类

```
完全云原生（web-only，从设计起）
└── Onshape                          - 100% 浏览器，无桌面版本

云原生 + 桌面共存（双形态）
├── iTwin Platform                   - 同代码 Web/桌面/移动三形态
└── 3DEXPERIENCE CATIA               - 桌面客户端 + 云数据后端

云镜像桌面 SDK（桌面 SDK 直接迁移到云端）
└── AutoCAD APS Design Automation    - 桌面 ObjectARX/.NET 代码云端跑

云作为 SaaS 部署模式（同一软件，不同部署）
└── NX X / NX X Essentials           - 桌面安装 + 浏览器流式（AWS）

桌面优先 + 保守云
├── SolidWorks                       - 3DEXPERIENCE Works 整合较慢
├── SketchUp + Trimble Connect       - Web 版不支持 Ruby 扩展
├── MicroStation 桌面                - 与 iTwin 协同但分开
└── FreeCAD                          - 暂无云原生计划
```

> **[评论]** 云原生策略的差异反映厂商商业定位差异：Onshape 的 100% 云原生与初创公司"无遗留客户"的优势相关；CATIA "no files" 是大厂强推；MicroStation/iTwin 的双轨是务实策略；FreeCAD 暂无云原生与开源项目的资源结构相关。

### 1.5 按商业模式分类

| 商业模式 | 平台 |
|---|---|
| 永久授权 + 订阅并行 | SolidWorks（部分）、SketchUp（部分） |
| 强制订阅（已淘汰永久授权）| AutoCAD（2017+）、SketchUp（2020+）、CATIA、NX |
| 纯订阅（云原生从开始）| Onshape |
| 开源（LGPL）| FreeCAD |
| 商业 + 开源开发者 SDK | iTwin.js（MIT）+ MicroStation 商业 |

### 1.6 按 API 兼容承诺强度分类

```
最强：编译期强制 + 多代共存
└── CATIA CAA: mkmk 校验 Authorized API；V5/V6/3DX 共享几何内核

强：多代共存 + 文档承诺
├── AutoCAD: ObjectARX/LISP/VBA/.NET/Web 五层并存 30 年
├── NX: GRIP/Open C/Common API 三代并存 50 年
└── MicroStation: MDL/C++/.NET/Python 四代并存 30+ 年

中：单层 API + 接口版本化
└── SolidWorks: COM 单层 + IModelDocExtension 模式

破坏性更新
├── Onshape: REST API 版本化（v1/v2/v3...），不强制兼容
└── FreeCAD: 0.x 长期破坏性，1.0 起承诺更稳定
```

---

## 二、对比矩阵：12 个核心维度

### 2.1 主对比表

| 维度 | AutoCAD | CATIA | NX | Onshape | MicroStation+iTwin | SolidWorks | SketchUp | FreeCAD | BricsCAD |
|---|---|---|---|---|---|---|---|---|---|
| **诞生年份** | 1982 | 1977 | 1972 (UNIAPT) | 2012 | 1985 (V1) | 1995 | 2000 | 2002 | 2002 |
| **拥有者** | Autodesk | Dassault Systèmes | Siemens | PTC | Bentley | Dassault Systèmes | Trimble | FPA（非营利）| Hexagon → Octave (2025+) |
| **主 API 语言** | C++ + .NET | C++ | C++/C#/Java/Python/VB | TypeScript REST + FeatureScript | C++/.NET/Python | COM (VBA/C#) | Ruby | Python + C++ | C++ + .NET（与 ARX 源码兼容）|
| **几何内核** | 自研 (AcGe) | 自研 (CGM) | Parasolid | Parasolid 衍生 | 自研抽象层 | Parasolid | Face-based | OCCT | ACIS（Spatial / DS）|
| **API 风格** | in-process 原生 | in-process 原生 + 严格组件 | Common API 多语言对等 | REST + 领域语言 | in-process 多代并存 | COM 单层 | 嵌入式脚本 | Python 平台基底 | in-process 原生（BRX = ARX 兼容）|
| **Custom Entity** | ✅ | ✅ (Late Type) | ✅ (Common API) | ✅ (FeatureScript) | ✅ (ECClass) | ❌ | ❌ | ✅ (FeaturePython) | ✅（与 ARX Custom Entity 兼容）|
| **强类型 schema** | ❌ | ✅ (Knowledge Adv.) | ✅ (KF) | ✅ (FeatureScript) | ⭐ ECSchema/BIS | 部分 | ❌ | 强 Property 类型 | ❌（与 ARX 同）|
| **云原生** | APS Design Automation | 3DEXPERIENCE | NX X (2024) | ⭐ 100% 云原生 | iTwin (开源) | 3DEXPERIENCE Works | Web 版不含 Ruby | 无 | Bricsys 24/7（云协作 + 轻量 Web 查看）|
| **协作模式** | 文件锁 + ACC | ENOVIA / 3DEXPERIENCE | Teamcenter | ⭐ Git 式 branching | iModel ChangeSet | PDM / 3DEXPERIENCE | 文件 + Trimble Connect | 文件 | 文件 + Bricsys 24/7 |
| **学习曲线** | 中-高 | 极高 | 高 | 中 | 高 | 中 | ⭐ 低 | 中 | 中（ARX 经验可直接复用）|
| **AI 整合（2025-2026）**| Smart Blocks (2026) | ENOVIA Aura | NX 2024 AI | 暂无明显 | 待发展 | Aura AI (2026) | AI Render (2026.1) | 无 | BricsCAD BIM AI（Hexagon 集团协同）|
| **价格档次** | 中（订阅）| 极高 | 极高 | 中（订阅）| 高 | 中 | 中 | 免费 | 中（永久授权可选 ⭐）|

### 2.2 API 入口对象对比

| 平台 | 主入口对象 | 文档对象 |
|---|---|---|
| AutoCAD | `AcApDocument`（含 Editor + Database）| `AcDbDatabase`（DWG 内存模型）|
| CATIA | `CATSession`（V5）/ `CATIA Application` | `Document`（CATPart, CATProduct, CATDrawing）|
| NX | `NXOpen.Session`（单例）| `NXOpen.Part`（.prt 文件内存模型）|
| Onshape | REST endpoint with workspace ID | document → workspace → element |
| MicroStation | `Application`（.NET）/ `mdlSystem` (MDL) | `DgnFile` → `DgnModel` → `DgnElement` |
| SolidWorks | `SldWorks.Application`（COM）| `IModelDoc2`（Part/Assembly/Drawing）|
| SketchUp | `Sketchup` 模块 + `Sketchup.active_model` | `Sketchup::Model` 含 `entities`/`materials` 等 |
| FreeCAD | `FreeCAD` 模块 + `FreeCADGui` 模块 | `App.Document` 含 DocumentObject 列表 |
| BricsCAD | `acedGetCurDwg()` (BRX C++) / `Bricscad.ApplicationServices.Application` (.NET) | `AcDbDatabase`（与 ARX 同名同结构）|

### 2.3 选择对象 / 角色化机制对比

| 平台 | 机制 | 优点 | 缺点 |
|---|---|---|---|
| AutoCAD | ObjectId + 数组传参 | 简单直观 | 无角色信息 |
| CATIA | 显式 Spec 对象 | 强类型，每角色独立 Spec | 复杂度高 |
| NX | Builder 具名属性 | 声明式，自描述 | Builder 概念学习 |
| Onshape | Query 表达式作为 feature 参数 | 可表达"选择满足条件的所有面"等 | FeatureScript 学习 |
| MicroStation | Element 选择集 + 多选机制 | 灵活 | 角色信息靠开发者维护 |
| SolidWorks | `SelectByID2` + **mark 整数** | COM 时代实用 | 散落式知识点，不直观 ⚠️ |
| SketchUp | 直接 entity 引用 + Tool 类的 InputPoint | 设计师友好 | 不适合复杂角色 |
| FreeCAD | PropertyLink / PropertyLinkSub | 显式持久化引用 | 需理解 ElementMap 机制 |
| BricsCAD | ObjectId + 数组传参（与 ARX 兼容）| ARX 同源，源码可移植 | 同 ARX：无角色信息 |

---

## 三、跨平台共性模式提炼

> **[本节适用边界（前置）]** 本节的"模式 A-F"是从 9 个样本平台归纳出的共性，反映样本中观察到的设计取向。不在样本中的平台（PTC Creo、Inventor、Rhino 等）可能存在不同模式。本节模式应被理解为**思考清单**，不是普遍规律。

### 3.1 模式 A：分层 API 服务多类开发者

样本中 8/9 平台采用某种形式的分层 API（Onshape 是例外，单层 REST + FeatureScript）。

最经典实现：AutoCAD 的"六层金字塔"[回链：3.1 §二 API 整体架构：六层金字塔]：

```
Web JavaScript API (ISV web 开发)
  ↓
AutoLISP / Visual LISP (设计师友好)
  ↓
COM Automation (VBA/Python, IT 集成)
  ↓
Managed .NET API (中端 C# 开发)
  ↓
ObjectDBX (轻量数据库扩展)
  ↓
ObjectARX (深度 C++ 扩展)
```

类似实现：

| 平台 | 分层结构 |
|---|---|
| **AutoCAD** | LISP / VBA / .NET / ObjectARX / Web JS |
| **CATIA** | Macro VBA / CAA Authorized / CAA Internal |
| **NX** | Journal / GRIP / Open C / NX Open Common API |
| **MicroStation** | Key-in / VBA / MDL / C++ / .NET / Python |
| **SolidWorks** | VBA Macro / Standalone / Add-in / Document Manager API |
| **SketchUp** | Ruby Console / Macro / Extension / C SDK |
| **FreeCAD** | Macro / Workbench Python / C++ Module |

**Onshape 例外**：单层 REST + FeatureScript，无传统的 in-process 分层。

> **[评论]** 分层 API 是 30+ 年 CAD 软件演进自然形成的——不同开发者群体（设计师、企业 IT、专业 ISV）需要不同入口。新平台决策时若想跳过分层，建议明确替代策略（如 Onshape 用 REST + FeatureScript 取代，让开发者只学一套）。

### 3.2 模式 B：声明式建模 vs 命令式建模

⭐ 在样本的参数化 CAD 平台中，从命令式到声明式是观察到的演进方向 [证据等级 B（适用范围：参数化 CAD 子集）][回链：3.2 §六 Spec/Result/Update；3.3 §三 Common Object Model；3.4 §五 FeatureScript]：

| 范式 | 代表平台 | 特征 |
|---|---|---|
| **命令式（早期）**| AutoCAD ObjectARX `add_line()`, SketchUp `entities.add_face()` | 立即执行；无参数容器 |
| **声明式 + 显式 Commit**| CATIA Spec/Result/Update; NX Builder; Onshape FeatureScript | 收集参数 → 显式提交计算；支持编辑现有 feature |

**声明式范式的演进**：

```
AutoCAD (1995)         → 命令式，create-and-go
SolidWorks (1995)      → COM SelectByID + Feature API（仍偏命令式）
CATIA (1998)           → Spec/Result/Update 三段式
NX (Common API 2000s)  → Builder + Commit
Onshape (2012)         → FeatureScript + ContextQuery 强类型
FreeCAD (FeaturePython)→ execute() 重计算回调
```

> **[评论]** 声明式范式的优势是"参数化[关联性](/glossary#关联性-associativity)"自然——用户调整参数时引擎重算，下游自动传播。命令式范式需要额外维护依赖图。**适用边界**：此趋势在参数化 CAD 中明显，对命令式 API 主体的平台（AutoCAD、SketchUp）适用性有限——这些平台的命令式 API 仍是主流且未必会被取代。新平台选择 feature API 范式时建议根据客户基础匹配。

### 3.3 模式 C：扩展数据机制的层级化

| 平台 | 扩展数据层级（从轻到重）|
|---|---|
| **AutoCAD** | XData (16K) / XRecord / Dictionary |
| **MicroStation** | Linkage / XAttribute / Item Types / **ECInstance** ⭐ |
| **CATIA** | Knowledge Parameter / Late Type |
| **NX** | Attribute Manager / Knowledge Fusion 持久对象 |
| **SolidWorks** | Custom Properties / Equation Manager / Configuration Properties |
| **SketchUp** | Attribute Dictionary（无强类型）|
| **Onshape** | Custom property + FeatureScript Map type |
| **FreeCAD** | Property System（强类型，多种 Property 类）|

⭐ **MicroStation 的 ECSchema 系统在样本中是较完整的"工程元数据"实现** [回链：3.5 §六 ECObjects / ECSchema]——支持类、关系、自定义属性、强类型、XML/JSON 序列化。

> **[评论]** 扩展数据机制的层级化反映"轻量到重量"的设计需求：(1) 简单标签 → 轻量 KV，(2) 结构化属性 → 强类型 schema，(3) 工程数据集成 → 关系建模 + 元元模型。**适用边界**：强 schema 系统对工程数据集成场景（BIM、PLM、跨工具治理）特别重要，对于设计师友好型平台或不强调跨工具数据治理的场景，简单的属性字典已足够——schema 强度应匹配数据集成需求，而不是越高越好。

### 3.4 模式 D：事件 / 观察者机制

| 平台 | 事件机制 | 颗粒度 |
|---|---|---|
| AutoCAD | Reactor（C++ 虚函数 + COM 事件）| 高（单对象事件）|
| CATIA | Event/Notification（CATBaseUnknown 事件）| 中 |
| NX | Callback + UpdateManager | 中 |
| Onshape | Webhooks（云端事件）| 低（文档级）|
| MicroStation | EventHandler + ECObject 事件 | 中-高 |
| SolidWorks | COM connection points | 中（文档级 + Feature 级）|
| SketchUp | **17+ 类 Observer** ⭐ | ⭐ 极高 |
| FreeCAD | boost::signals2 单向 | 中（DocumentObject 级）|

⭐ **SketchUp Observer 机制颗粒度在样本中较细** [回链：3.7 §五 Observer 模式]——AppObserver / ModelObserver / EntitiesObserver / EntityObserver / SelectionObserver / ToolsObserver / ViewObserver 等 17+ 类。这种细粒度事件让 SketchUp 扩展可以做精细监控，但也带来"观察者生命周期陷阱"。

### 3.5 模式 E：UI 扩展的两条路线

```
路线 A：原生 UI 扩展
├── ObjectARX：MFC/Windows native dialog
├── CATIA CAA：原生 Toolbar/Panel
├── NX Block UI Styler：声明式 UI 设计器，多语言代码生成 ⭐
├── SolidWorks Add-in：MFC/.NET/PMP（PropertyManager Page）
├── SketchUp UI module：HtmlDialog + Modus 设计系统 ⭐
└── FreeCAD：Qt + ViewProvider

路线 B：嵌入 Web UI
├── SketchUp UI::HtmlDialog：嵌入 CEF（SU 2017+）⭐
├── iTwin.js：浏览器原生（@itwin/core-frontend）
├── Onshape：浏览器原生（无桌面版）
├── AutoCAD APS Viewer：JavaScript SDK
└── 多数 CAD 提供 HtmlDialog 等价机制
```

⭐ **观察**：嵌入式 Web UI 替代或补充原生 UI 是 2010s+ 的趋势。CEF（Chromium Embedded Framework）在样本中被多个平台采用作为嵌入式 Web UI 的实现选择 [证据等级 B][回链：3.7 §六 UI::HtmlDialog]。

### 3.6 模式 F：协作模式演进

```
模式 1：文件锁（File Locking）
- 传统 CAD：一个用户改文件，其他人只读
- 适用：90s-2000s 的小团队

模式 2：Check-out/Check-in（PDM）
- ProjectWise / Vault / Teamcenter / ENOVIA
- 适用：大型组织 + 强治理

模式 3：iModel ChangeSet（Bentley）
- 类 git 的"线性 changeset 时间线 + branch/merge"
- iModelHub 强制 latest-based
- 适用：基础设施工程

模式 4：Onshape Microversion（PTC）⭐
- ⭐ 完整 git 式（branch / merge / version graph）
- 浏览器原生协作
- 适用：cloud-native CAD

模式 5：AutoCAD Connected Support Files（2026）
- 项目感知配置共享
- 不是真正的同步协作
```

⭐ **观察**：在本系列覆盖的 9 个样本中，Onshape 是较少见的实现完整 Git 式 CAD 协作的平台 [回链：3.4 §三 git 式四层数据模型]。Bentley iTwin 的 ChangeSet 接近但仍是线性。商业 CAD 主流仍是 PDM check-out/check-in。

---

## 四、各平台独有设计参考

> ⚠️ **章节定位说明**：下文所列设计是**在本系列 9 个样本平台的对比中**未观察到等价物的设计选择，不代表"在所有 CAD 平台中绝无仅有"——其他未覆盖平台（PTC Creo、Inventor、Rhino+Grasshopper 等）可能存在等价或类似设计。

下面列出每个平台**在样本中较罕见**的设计决策——其他样本平台没有等价物：

| 平台 | 在样本中较罕见的设计 | 参考 |
|---|---|---|
| **AutoCAD** | Custom Entity + Object Enabler 平台经济学（保护 ISV 算法 + 让标准用户可查看） | 3.1 §四 ObjectARX 核心机制 |
| **CATIA** | mkmk 编译期强制 Authorized vs Internal API 边界 | 3.2 §五 Authorized vs Internal API |
| **NX** | Common API 多语言完全对等（自动生成绑定保证一致性） | 3.3 §三 Common Object Model |
| **NX** | Synchronous Technology 直接编辑 + 关联性维持 | 3.3 §四 Synchronous Technology |
| **Onshape** | 完整 Git 式数据模型（branch / merge / microversion）| 3.4 §三 git 式四层数据模型 |
| **Onshape** | FeatureScript 强类型领域语言 + 单位安全 | 3.4 §五 FeatureScript |
| **MicroStation** | ECSchema/BIS 工程级元数据 schema 系统 | 3.5 §六 ECObjects / ECSchema |
| **iTwin** | iModel = SQLite + ChangeSet 联邦数字孪生（开源 MIT，⚠️ 非 Apache 2.0）| 3.5 §八 iTwin Platform |
| **SolidWorks** | IModelDocExtension 接口版本化（COM 时代的优雅范式）| 3.6 §二 API 整体架构 |
| **SolidWorks** | Document Manager API 离线读取（不启动主程序）| 3.6 §八 Document Manager API |
| **SketchUp** | 17+ 类高粒度 Observer + .rbz 友好分发 | 3.7 §五 Observer 模式；3.7 §七 扩展打包与分发 |
| **SketchUp** | Face-based 几何（无 NURBS）的极致简化 | 3.7 §四 几何模型 |
| **FreeCAD** | App/Gui 严格 MVC 分离 + boost::signals2 单向依赖 | 3.8 §二 API 整体架构 |
| **FreeCAD** | FeaturePython 让纯 Python 类作为 DocumentObject 一等公民 | 3.8 §三 Python 嵌入式哲学 |

---

## 五、跨平台演进影响：人物、收购、技术血缘

### 5.1 关键人物的跨平台影响

```
Jon Hirschtick （MIT 21 点队员、用赌博收入启动 CAD）
├── 1995 创立 SolidWorks Corp.
├── 1997 SolidWorks 被 Dassault Systèmes 以 3.1 亿美元收购
├── 2011 离开 SolidWorks
├── 2012 与多位 SolidWorks 老兵创立 Onshape ⭐ "重做"——从 PC 到云
└── 2018 Frustum 被 PTC 收购（Hirschtick 也加入）

ICAD Team 的 KBE 传承
├── 1980s ICAD（Knowledge Technologies）参数化规则建模
├── 1990s 部分团队成员加入 NX → Knowledge Fusion
├── 1990s 部分技术影响 CATIA → Knowledge Advisor
└── 设计哲学影响延续到 FreeCAD Property System、Onshape FeatureScript

Open CASCADE 与 CATIA 的法国血缘
├── 1990s Matra Datavision 开发 EUCLID-IS 内核
├── 1999 Matra 开源 EUCLID-IS → Open CASCADE Technology
└── DS（CATIA）与 Matra 在法国 CAD 行业曾是邻居——技术血缘相近
```

### 5.2 关键收购事件影响

| 时间 | 事件 | 影响 |
|---|---|---|
| 1992 | Dassault 从 IBM 收购 CADAM | CATIA 整合 2D 制图 |
| 1997 | DS 收购 SolidWorks | DS 进入中端市场 |
| 2000 | Unigraphics 收购 SDRC | NX = Unigraphics + I-DEAS 整合开始 |
| 2004 | Siemens 收购 D-Cubed | 约束求解器商业化 |
| 2005 | Dassault 收购 MatrixOne | ENOVIA V6 数据基座 |
| 2007 | Siemens 以 35 亿美元收购 UGS | NX/Solid Edge/Parasolid/Teamcenter 整合 |
| 2012 | Trimble 从 Google 收购 SketchUp | SketchUp 进入"专业化 + 订阅化"时代 |
| 2019 | PTC 以 4.7 亿美元收购 Onshape | PTC 获得云原生 CAD |

### 5.3 技术血缘交叉

```
Hirschtick 影响：
SolidWorks 1995 ─────→ Onshape 2012  （PC → Cloud "重做"）
                          ↓
                       FeatureScript 设计哲学

ICAD KBE 影响：
1980s ICAD ────┬───→ NX Knowledge Fusion
               ├───→ CATIA Knowledge Advisor
               └───→ FreeCAD Property System (思想影响)

法国 CAD 血缘：
Matra Datavision EUCLID-IS ──→ Open CASCADE Technology (1999)
                                        ↓
                                     FreeCAD 内核
                                     (与 CATIA 同源不同枝)

德国 BIM 血缘：
ECObjects (Bentley) ──→ ECSchema/BIS ──→ iModel
       ↑
       概念上影响 IFC 标准化（双向）
```

---

## 六、典型场景的选型参考

> **[本节适用边界（前置）]** 以下选型参考是基于 8 样本平台的归纳，**仅供参考**。具体决策需结合客户基础、预算、生态、合规要求等多重因素。本节使用"建议""可参考"等克制表述，避免"必须""唯一选择"等绝对化指令。

### 6.1 我要做 CAD 二次开发，选哪个平台？

```
开发者类型：业余/教育/原型
├── 偏好 GUI ──→ SketchUp Ruby（设计师友好）
└── 偏好脚本 ──→ FreeCAD Python（开源 + 强大 Python 集成）

开发者类型：专业 ISV，机械中端
├── 客户基础是 SolidWorks ──→ SolidWorks API（COM）
└── 客户要 Web ──→ Onshape REST + FeatureScript

开发者类型：专业 ISV，机械高端
├── 航空航天客户 ──→ CATIA CAA（Authorized API）
└── 汽车 + 高端装备 ──→ NX Open Common API

开发者类型：AEC + 基础设施
├── 通用 2D/3D ──→ AutoCAD ObjectARX/.NET
├── 基础设施工程 + ECSchema ──→ MicroStation + iTwin
└── 概念设计/景观 ──→ SketchUp Ruby
```

### 6.2 我要做新一代 CAD 平台，可借鉴哪些设计？

| 设计选项 | 借鉴对象 | 启示 |
|---|---|---|
| **SDK 多语言策略** | NX Common API 自动生成 ⭐ | "主对象模型 + codegen" 在样本中比手写 wrapper 更易维护 |
| **API 兼容承诺** | AutoCAD 30 年加法兼容 | 加法兼容比强制迁移更尊重 ISV |
| **声明式 feature API** | NX Builder + Commit / CATIA Spec/Result/Update | 在参数化 CAD 中比命令式更自然支持关联性 |
| **协作数据模型** | Onshape git 式 ⭐ | 完整 branch/merge 比 ChangeSet 线性更灵活 |
| **工程元数据** | MicroStation ECSchema/BIS ⭐ | 强类型 schema 在工程数据集成场景中价值显著 |
| **MVC 架构** | FreeCAD App/Gui 分离 ⭐ | 严格分离让 headless 模式天然支持 |
| **嵌入式脚本** | FreeCAD FeaturePython ⭐ | Python 可作为平台基底而非附加层 |
| **接口版本化** | SolidWorks IModelDocExtension | 不破坏老代码的 COM 时代范式 |
| **平台经济学** | AutoCAD Custom Entity + Object Enabler | 保护 ISV + 让标准用户可查看 |
| **云原生路径** | Onshape 100% 云原生 vs Bentley iTwin 联邦 | 取决于客户基础 |
| **AI 整合方向** | AutoCAD Smart Blocks / SolidWorks Auto Drawing / SketchUp AI Render | 务实路线在样本中比颠覆路线更普遍 |

⚠️ **使用本表的注意**：表中的"借鉴对象"是从样本中识别的优秀设计，但**借鉴 ≠ 照搬**——CATIA 的严格组件模型适合航空航天但对中小企业是负担；NX Common API 的多语言对等需要相应的工程团队规模支撑。借鉴时应考虑组织能力与目标客户的匹配度。

### 6.3 国产 CAD 替代路径的行业观察

> ⚠️ **章节定位说明**：本节内容**主要基于公开行业观察、经验判断与案例归纳，不构成市场研究结论**。重要决策应核对当前的市场调研报告（Gartner、IDC、艾瑞、易观等）。
>
> 本节所有论断的**证据等级统一为 C**。

针对国产 CAD 替代的行业观察（按目标平台的替代难度归纳）：

| 目标平台 | 观察到的替代难度 | 路径归纳 |
|---|---|---|
| AutoCAD（2D 制图）| 中 | 中望/浩辰/CAXA 等已较成熟，多基于 ODA Drawings SDK |
| SolidWorks（中端机械）| 中-高 | 中望 ZW3D / 华天 SINOVATION，需匹配 API 与生态 |
| SketchUp（景观/室内）| 中 | 酷家乐/三维家等本土在线工具部分替代 |
| MicroStation（基础设施）| 高 | 需要等价 ECSchema 系统，难度较大 |
| CATIA（航空航天）| 极高 | 几何内核 + CAA + Knowledge Adv. 全栈差距 |
| NX（高端机械 + 重型装备）| 极高 | Parasolid + D-Cubed + KF + 高端 CAM 全栈差距 |
| Onshape（云原生）| 高 | 需要 git 式架构 + 云基础设施 + 浏览器内核 |

> **[评论]** OCCT 在中国 CAD 国产化中是较重要的开源生态资产之一。FreeCAD 的架构经验（App/Gui 分离、Workbench、Python 集成）值得参考。但具体国产 CAD 项目的实际进展、市场份额、技术突破需以最新公开数据为准。

---

## 七、行业趋势与未来展望

> **[本节适用边界（前置）]** 本节归纳的趋势是**对 2024-2026 年现状的观察**，不是对未来必然演进的预测。CAD 业界正处于云原生、AI 整合、开源 CAD 1.x 时代的快速演进期，部分趋势在未来 3-5 年可能演变。本节所有趋势性表述应被理解为**值得关注的方向**而非已被验证的演进规律。**证据等级 B/C 不等**，下文按节具体标注。

### 7.1 趋势 A：云原生策略的多元化

2024-2026 期间，CAD 厂商的云原生策略呈现多元化：

```
路线 1：完全云原生（Onshape）
路线 2：联邦数字孪生（iTwin）
路线 3：云镜像桌面 SDK（AutoCAD APS）
路线 4：SaaS 部署模式（NX X）
路线 5：双轨保守（SolidWorks/CATIA Cloud Offer）
路线 6：保守桌面 + 云协作（SketchUp + Trimble Connect）
路线 7：暂无云原生（FreeCAD）
```

> **[评论]** 截至 2026 年初，路线 1（完全云原生）与路线 4（SaaS 部署）在新 SaaS 客户中的吸引力较强，但路线 5（双轨保守）在大型企业客户中仍占重要位置。**未来 5 年的具体路线占比无法预测**——但可观察到的现象是各厂商都在尝试不同路线而非聚合到单一路线。**[证据等级 B]**


### 7.2 趋势 B：AI 整合的务实路线

2025-2026 各 CAD 厂商的 AI 整合多瞄准"减少重复劳动" [回链：3.1 §一 历史演进；3.6 §九 SolidWorks 2026；3.7 §九 SketchUp 2025-2026]：
- AutoCAD 2026 Smart Blocks（自动 block 转换）
- SolidWorks 2026 Aura AI + 自动生成 Drawing
- SketchUp 2026.1 AI Render + AI Assistant
- NX 2024+ AI-enabled design

**观察到的整合层次**：
- 当前：自动化重复任务（出图、BOM、标注）—— 多数厂商在此层
- 当前到中期：AI 辅助直接编辑（基于 Synchronous Technology 等）—— 少数厂商进入
- 长期：生成式建模（Fusion 360 Generative Design 等已试水）—— 仍是早期阶段

> **[评论]** "未来方向"难以精确预测——本节只描述截至 2026 年初的整合层次现状。**[证据等级 B]**

### 7.3 趋势 C：Python 在 CAD 脚本生态中的位置变化

```
Python 集成程度演进观察：
1990s-2000s：Python 是少数 CAD 的脚本附加（FreeCAD 是较早的例外）
2010s：Python 成为 NX/Onshape 的一等公民
2020s：MicroStation 2024 引入官方 Python API
```

观察：在样本中，Python 集成度近年呈上升趋势。同时 Ruby 解释器升级带来 C 扩展兼容性问题（SketchUp 经历过相关调整）。

> **[评论]** "新平台不再选 Ruby" 是个推测，不应作为通用建议。语言选择应匹配目标用户群——SketchUp Ruby 的成功部分来自 Ruby 对设计师的友好性。**[证据等级 C]**

### 7.4 趋势 D：开源 CAD 的近期进展

FreeCAD 1.0（2024-11）的发布是开源 CAD 的标志性事件 [回链：3.8 §一 历史演进]。OCCT 8.0 即将发布（2026-02）。开源工具链（FreeCAD + KiCad + Blender + OpenSCAD + Onshape FeatureScript 公开标准库）正在形成更完整的设计-制造工具链。

> **[评论]** 截至 2026 年初观察，开源 CAD 在以下场景显示活跃度：(1) 教育市场，(2) 中小企业入门，(3) 中国国产化讨论的相关路径，(4) 嵌入式 + PCB + 3D 打印整合工具链。但在高端航空航天、汽车造型等场景，商业 CAD（CATIA / NX）的主流地位短期内仍将延续——具体的市场份额演进缺乏可靠的公开数据。**[证据等级 B/C]**

### 7.5 趋势 E：协作数据模型的多样化

```
传统 PDM（check-out/check-in）：
  Teamcenter / ENOVIA / ProjectWise / Vault
  ↓
线性 ChangeSet（半 git）：
  Bentley iModelHub
  ↓
完整 Git 式（branch + merge + version graph）：
  Onshape Microversion ⭐
```

> **[评论]** "未来 10 年新一代 CAD 平台是否默认采用 Git 式协作"是开放问题——Onshape 已证明可行性，但商业 CAD 巨头（DS、Siemens、Autodesk）的现有 PDM 投资量较大，转型路径与速度因企业而异。Git 式不必然是终点，可能与传统 PDM 长期共存。**[证据等级 B]**


---

## 八、几点启示

### 8.1 启示 A：API 设计反映客户基础

CAD API 设计常常反映客户基础与商业战略 [回链：3.2 §五 Authorized API；3.7 §一 历史演进；3.4 §一 历史背景]：
- **CATIA CAA 严格组件 + 编译期 API 边界**：与服务航空航天巨头的兼容承诺战略相关
- **SketchUp Ruby 极简 .rbz 分发**：与服务设计师群体的低门槛战略相关
- **NX Common API 四语言对等**：与服务多元客户、不让语言偏好限制功能的战略相关
- **SolidWorks COM 单层简化**：与服务中端工程师的"上手快优先于深度无限"战略相关
- **Onshape REST + FeatureScript**：与服务云原生新客户、没有遗留兼容包袱的战略相关
- **FreeCAD FeaturePython**：与服务开源社区、让 Python 成为基底的设计取向相关

新平台决策时**建议先明确客户基础**——技术选择常常与商业选择相耦合。**[证据等级 A]**

### 8.2 启示 B：长期兼容承诺与 ISV 投资保护相关

| 平台 | 长期 API 兼容年限 | 承诺方式 |
|---|---|---|
| AutoCAD | 30+ 年（LISP 1982 至今）| 加法兼容 |
| CATIA | 27 年（V5 1998 至今 + V6/3DX）| 编译期强制 + 内核共享 |
| NX | 50+ 年（GRIP 1980s 至今）| 加法兼容 |
| MicroStation | 30+ 年（MDL 1990s 至今）| 加法兼容 |
| SolidWorks | 30 年（COM 1995 至今）| IModelDocExtension 模式 |
| SketchUp | 24 年（Ruby 早期至今）| 持续兼容（但 Ruby 升级带破坏）|
| FreeCAD | 22 年（2002 至今，0.x 较破坏）| 1.0 起承诺更稳定 |
| Onshape | 13 年（2012 至今）| REST 版本化但不强制兼容 |

⭐ 长期兼容承诺让 ISV 投资得到保护——这与平台经济学的稳定性相关。但承诺成本极高，新平台不必模仿到极致。**[证据等级 B]**

### 8.3 启示 C：架构师的决策框架

一个 CAD 平台 API 的设计涉及多个核心决策维度。在样本归纳基础上，本系列文档 1 总结了 12 维决策框架：

1. **API 风格**：in-process C++ / COM / 托管 .NET / REST / 嵌入式脚本
2. **几何内核**：自研 / 商业授权（Parasolid/ACIS）/ 开源（OCCT）/ 简化（Face-based）
3. **多语言策略**：单语言 / 自动生成绑定 / 手工 wrapper
4. **建模范式**：命令式 / 声明式 / 声明式 + 显式 Commit
5. **扩展数据**：KV 字典 / XRecord / 强类型 Property / 关系建模 schema
6. **事件机制**：粗颗粒度 / 中颗粒度 / 极细 Observer
7. **UI 扩展**：原生 dialog / 嵌入 Web (CEF) / 多语言代码生成
8. **协作模式**：文件锁 / PDM check-out / ChangeSet / Git 式
9. **云原生策略**：100% 云 / 联邦 / 镜像桌面 / SaaS 部署 / 不上云
10. **API 兼容承诺**：编译期强制 / 加法兼容 / 接口版本化 / 不强制
11. **商业模式**：永久授权 / 订阅 / 开源 / 双轨
12. **AI 整合方向**：自动化 / 辅助编辑 / 生成式建模

⭐ **没有"最好"的选择**——每个决策需匹配客户基础、商业目标、生态阶段。详细分析见文档 1 第三部分（API 设计的元元模型）。

---

## Caveats

- **9 个平台的选择**：覆盖了机械（CATIA/NX/SolidWorks/Onshape/FreeCAD）+ AEC（AutoCAD/MicroStation/SketchUp）+ DWG 兼容路径（BricsCAD）的主流主力。**未覆盖**的重要平台包括：PTC Creo（与 Onshape 同公司但定位不同）、Autodesk Inventor、Solid Edge（与 NX 同公司）、Rhino + Grasshopper（参数化建模独门）、Revit（BIM 主流）、ArchiCAD（建筑 BIM）。本文档若有续篇可补充。
- **行业边界并非绝对**：AutoCAD 在机械（Mechanical Toolset）、CATIA 在建筑（Frank Gehry）等存在领域跨越。
- **演进观察的不确定性**：第 7 部分的趋势观察基于 2024-2026 公开信息，未来 5-10 年情况可能改变。
- **市场份额数据**：本文档未引用具体市场份额数据，所有"主流地位"判断属社区观察与行业共识。
- **国产化路径观察**：第 6.3 节的国产 CAD 替代讨论是行业观察，不是市场研究结论。重要决策应核对市场调研机构数据。
- **Hirschtick 21 点队故事**：来自 Wikipedia 与公开访谈，具体细节有不同来源。
- **Onshape 内核来源**：Onshape 不公开内核来源，社区共识是基于 Parasolid 衍生（PTC 收购前历史复杂），属推论。
- **证据等级标签局限**：A/B/C 标签是作者写作辅助自评，不是基于客观指标的评分。
- **引用精度局限**：3.x 报告的章节粒度是中文一级编号（§一/§二/§三），本文档跨文档引用最多到此粒度。

---

## 参考来源

本文档不重复引用每个事实的来源，所有事实陈述基于以下文档 3.x 系列报告：

- 文档 3.1 - AutoCAD ObjectARX API 设计深度剖析
- 文档 3.2 - CATIA CAA RADE API 设计深度剖析
- 文档 3.3 - Siemens NX (NX Open) API 设计深度剖析
- 文档 3.4 - Onshape REST + FeatureScript API 设计深度剖析
- 文档 3.5 - MicroStation + iTwin API 设计深度剖析
- 文档 3.6 - SolidWorks API 设计深度剖析
- 文档 3.7 - SketchUp Ruby API 设计深度剖析
- 文档 3.8 - FreeCAD API 设计深度剖析

各文档的详细来源标注（包括 [官方]/[新闻]/[百科]/[第三方] 等分类）见对应深度报告的"参考来源"章节。

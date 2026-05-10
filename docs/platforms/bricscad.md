---
title: BricsCAD (BRX + Qt/QML) API 设计深度剖析
---

# BricsCAD (BRX + Qt/QML) API 设计深度剖析

> 文档 3.9｜厂商深度剖析系列｜通用 CAD 平台 API 设计哲学

---

## 阅读约定

- 来源标注：本报告的事实陈述带 `<sup>[类别 N]</sup>` 标识，对应文末参考来源
- 来源类别：`[官方]`（Bricsys / Hexagon 官方文档与博客）/ `[新闻]`（媒体报道）/ `[百科]`（Wikipedia 等百科）/ `[第三方]`（社区资料、开发者博客）/ `[书籍]`
- `> **[推论]**`：基于已知事实的合理推断，非来自厂商或权威资料的直接陈述
- `> **[评论]**`：本报告作者的主观归纳、判断或行业观察
- ⚠️ **勘误**：对常见社区资料中事实错误的修正
- ⭐：本报告作者认为最具学习价值的设计模式或决策点
- 回链格式：`[回链：3.x §一/§二 ...]` 表示文档 3.x 的对应章节

---

## TL;DR

- **BricsCAD 是样本平台中唯一以"AutoCAD API 兼容"为核心战略的非 Autodesk 平台**：2002 年由 Bricsys NV 在比利时根特创立<sup>[官方 1][第三方 2]</sup>，**2018 年 10 月 23 日被 Hexagon AB 收购**<sup>[新闻 3][新闻 4]</sup>。BRX SDK（BricsCAD Runtime eXtension）与 ObjectARX 源码兼容，.NET API 与 AutoCAD .NET API 源码兼容——同一份 C++/C#/VB.NET 源码可以编译为分别面向 BricsCAD 与 AutoCAD 的两个二进制模块<sup>[官方 5]</sup>，但运行时不可互换加载。
- **几何内核：ACIS（Spatial / DS 旗下）**<sup>[官方 6][百科 7]</sup>：⚠️ 这是一个值得注意的产业事实——BricsCAD 是 Hexagon 旗下产品，但内核是 Dassault Systèmes 子公司 Spatial 提供的 ACIS。Hexagon、DS 在 PLM/CAD 领域有竞争关系，但在内核层面是商业授权关系。其他主要 ACIS 用户包括 SpaceClaim、Alibre、ANSYS、Cimatron、GstarCAD、ZWCAD、TurboCAD 等<sup>[官方 6][百科 7]</sup>。
- **Bricsys 是 ODA（Open Design Alliance）创始成员**<sup>[官方 8]</sup>：DWG 兼容性通过 ODA Drawings SDK（前称 Teigha）实现。Bricsys 团队估计自研 Drawings SDK 需 50 人年<sup>[官方 8]</sup>，所以选择持续依赖 ODA。
- **UI 架构在 2021-2022 起大规模迁移**：从原 **wxWidgets + MFC** 迁移到 **Qt/QML（+ Windows 上保留 MFC 兼容层）**<sup>[官方 9][官方 10]</sup>，初步估计完整迁移约 **50 人年**工作量，跨多个版本逐步推进。BricsCAD V24 RIBBON 命令是早期切换到 Qt/QML 的代表性模块<sup>[官方 11]</sup>。
- **产品矩阵分层清晰**：BricsCAD Lite（2D）、Pro（2D + 3D）、BIM、Mechanical、Ultimate（all-in-one）、Shape（免费 3D 概念建模）、Communicator（数据交换）、Bricsys 24/7（云协作）<sup>[官方 1][官方 12]</sup>。
- **公司规模与市场**：全球用户超 30 万、110+ 国家、14 种语言<sup>[第三方 2]</sup>。2022 年年收入约 3810 万欧元<sup>[第三方 13]</sup>。被 Hexagon 收购前 2017 年营收约 1300 万欧元<sup>[新闻 3]</sup>。
- **2025-2026 起属于 Hexagon 拆分的 Octave 子公司**<sup>[官方 14]</sup>——Hexagon 把 Asset Lifecycle Intelligence、Safety、Geospatial、Infrastructure 等业务（含 Bricsys）拆出独立公司 Octave。

---

## Key Findings

1. **BRX = BricsCAD Runtime eXtension**<sup>[官方 5]</sup>：这是 BricsCAD 的 in-process C++ SDK，与 ObjectARX 源码兼容（部分例外），是 BricsCAD 二次开发体系的基底。
2. **二进制隔离是关键边界**<sup>[官方 5]</sup>：BRX 与 ObjectARX 源码兼容但二进制不可互换——为 BricsCAD 编译的 .brx 模块不能加载到 AutoCAD，反之亦然。开发者用同一份源码 + 不同编译目标得到两套二进制。
3. **.NET API 双轨**<sup>[官方 15]</sup>：托管 API 通过 `BrxMgd.dll` + `TD_Mgd.dll` 提供，支持 C#、VB.NET、C++/CLI 混合模式 custom entity。引用 DLL 时需把 `Copy Local` 设为 `False`（与 AutoCAD .NET API 同样要求）。
4. **垂直 API 也对 .NET 暴露**<sup>[官方 15]</sup>：BIM、Civil、Sheet Metal 等专门 API 都有 .NET 入口，不只是核心 BRX。最新版本里 `BimNameSpaces` 类已从 BRX 暴露到 .NET API。
5. **ACIS 在 BricsCAD 中的版本是较新的**<sup>[第三方 16]</sup>：与 AutoCAD/Inventor 用 ShapeManager（2001 年从 ACIS 7.0 fork 后冻结）形成对比，BricsCAD 嵌入的 ACIS 版本持续跟进 Spatial 主线（社区资料显示 BricsCAD 用 ACIS 2020+ 系列）。
6. **UI 迁移是渐进式而非一刀切**<sup>[官方 9]</sup>：MFC 兼容层保留——`BcUiPanelMFC` dockable panel 让二次开发者可以在面板中嵌入 Qt 控件，不强制 ISV 立即重写所有 UI。
7. **持续依赖 ODA Drawings SDK**<sup>[官方 8]</sup>：Bricsys 是 ODA 创始成员之一，DWG 读写完全依赖 ODA 而非自研——这是"领域生态合作 + 内部精力聚焦 UX/AI/BIM"的明确战略选择。
8. **Hexagon 收购对 BricsCAD 的产品线影响**<sup>[新闻 3][新闻 17]</sup>：被 Hexagon 收购后 BricsCAD 加速 BIM 与 AI 方向的投入，BricsCAD BIM 与 Hexagon 的基建/AEC 战略契合度较高。

---

## 一、历史演进

### 1.1 起源：2002 年根特创立

Bricsys NV 于 2002 年在比利时根特（Ghent, East Flanders）创立<sup>[官方 1][第三方 2]</sup>。⚠️ 公司名 "Bricsys" 与 "BricsCAD" 中的 "Brics" **不是指 bricks（砖块）**，而是 **Building Related Interactive Computer System** 的缩写<sup>[第三方 2]</sup>。

> **[评论]** 名字本身揭示了 BricsCAD 早期的战略定位——以"建筑相关交互式计算系统"为核心，不是泛通用 CAD。这与今天 BricsCAD 在 BIM 领域的持续投入形成呼应。但它最终发展为通用 CAD 平台，覆盖 2D 制图、3D 机械、钣金、BIM 等多个领域。

### 1.2 早期：基于 IntelliCAD 内核到自主增强（2002-2010）

BricsCAD 早期版本基于 IntelliCAD Technology Consortium（ITC）的内核——这是 1990s 末若干 .dwg 兼容 CAD 厂商联合的开源式合作组织。Bricsys 通过 ITC 获得初始的 .dwg 读写与 AutoCAD 类 API 实现基础。

> **[推论]** 在 2000s 中后期，BricsCAD 逐步脱离 IntelliCAD 体系，转向更深度自研的方向。具体退出 IntelliCAD 的时间点社区资料不一，本报告未找到 Bricsys 官方对此的明确时间陈述。

### 1.3 BRX SDK 与 ACIS 内核：成熟期（2010-2018）

2010 年代初期，BricsCAD 完成了关键的工程升级：

- **BRX SDK 公开**：作为与 ObjectARX 源码兼容的 C/C++ API<sup>[官方 5]</sup>
- **ACIS 内核引入**：替换早期使用的内核选项，全面采用 ACIS<sup>[官方 6]</sup>
- **垂直产品矩阵建立**：BricsCAD Pro / Platinum（后改名为各专业版）开始分层
- **ODA 创始成员身份巩固**：通过 ODA Drawings SDK（前称 Teigha）持续保障 DWG 兼容<sup>[官方 8]</sup>

到 2017 年，Bricsys 营收约 1300 万欧元<sup>[新闻 3]</sup>，在欧洲与亚洲市场有相对稳定的份额，但北美市场仍然薄弱<sup>[新闻 17]</sup>。

### 1.4 Hexagon 收购（2018-10-23）

2018 年 10 月 23 日，Hexagon AB 在 Bricsys 年度开发者大会（伦敦）上宣布收购 Bricsys<sup>[新闻 3][新闻 17]</sup>。交易细节：

- 财务条款未公开披露
- Bricsys 2017 年营收约 1300 万欧元<sup>[新闻 3]</sup>
- 工程软件公司当时的并购倍率通常为年收入的 2-5 倍
- 被并入 Hexagon PPM 部门<sup>[官方 4][新闻 3]</sup>

> **[评论]** 这次收购在 CAD 业界相对低调，但战略意义不小——Hexagon 在测量、计量、地理空间、PPM（工厂数字化）领域有强势地位，加上 BricsCAD 后形成了"测量 + CAD + BIM + 工厂"的更完整链路。对 Bricsys 来说，被 Hexagon 收购后获得了北美市场扩展所需的渠道与资金。

### 1.5 UI 架构迁移启动（约 2021-2022）

被 Hexagon 收购后约三年，Bricsys 启动了 BricsCAD 历史上最大的工程项目——**UI 框架从 wxWidgets + MFC 迁移到 Qt/QML（+ Windows 保留 MFC 兼容层）**<sup>[官方 9][官方 10]</sup>。详见 §六。

### 1.6 BricsCAD BIM 与 AI 加速期（2022+）

收购后 BricsCAD 在 BIM 与 AI 方向显著加速：

- **BricsCAD BIM**：基于 .dwg 的 BIM 工作流，与 Autodesk Revit / Bentley OpenBuildings 形成竞争
- **AI Assist Ribbon**：基于使用习惯的下一命令推荐<sup>[官方 11]</sup>
- **Drawing Health Manager**：自动清理与质量管理
- **Parametric Blocks**：参数化块的本地化实现

### 1.7 Octave 拆分（2025-2026）

2025-2026 年间，Hexagon 正在评估把 Asset Lifecycle Intelligence、Safety、Geospatial and Infrastructure 等业务（包括 ETQ 和 Bricsys）拆分为独立子公司 **Octave**<sup>[官方 14]</sup>。

> **[推论]** 这次拆分对 BricsCAD 的影响：(1) 短期内 BricsCAD 商业策略与产品路线图保持稳定，因为是同集团内部架构调整；(2) 中长期可能强化 BricsCAD 在 AEC/基建客户的定位，因为 Octave 集中了 Hexagon 内部"软件 + 基建"相关业务；(3) 不影响与 Hexagon 测量/计量业务的协同，但治理边界会更清晰。本报告未找到 Bricsys 对此的官方表态。

### 1.8 历史时间线表

| 时间 | 事件 | 来源 |
|---|---|---|
| 2002 | Bricsys NV 在比利时根特创立 | [官方 1] |
| 2000s 早期 | BricsCAD 基于 IntelliCAD 内核起步 | [社区共识] |
| 2010 年代初 | BRX SDK 公开；ACIS 内核引入；垂直产品矩阵建立 | [官方 5][官方 6] |
| 2017 | Bricsys 营收约 1300 万欧元 | [新闻 3] |
| 2018-10-23 | Hexagon AB 收购 Bricsys；并入 Hexagon PPM | [新闻 3][新闻 4] |
| 2018+ | BricsCAD BIM、Mechanical 加速发展 | [官方 1] |
| ~2021-2022 | UI 框架开始迁移到 Qt/QML | [官方 9] |
| 2024 | BricsCAD V24 RIBBON 基于新 UI 框架 | [官方 11] |
| 2025-2026 | Hexagon 拆分 Octave，含 Bricsys | [官方 14] |

---

## 二、API 整体架构：BRX 体系

BricsCAD 的二次开发 API 体系以 **BRX**（BricsCAD Runtime eXtension）为核心，分层与 AutoCAD ObjectARX 高度对应。

### 2.1 API 层级结构

```
                    ┌─────────────────────┐
                    │  Web / 云端 API     │  (Bricsys 24/7)
                    └─────────────────────┘
                              ↑
                    ┌─────────────────────┐
                    │  COM Automation     │  (BricscadApp 等接口)
                    └─────────────────────┘
                              ↑
                    ┌─────────────────────┐
                    │  AutoLISP / DCL     │  (兼容 AutoLISP + 部分 BricsCAD 扩展)
                    └─────────────────────┘
                              ↑
                    ┌─────────────────────┐
                    │  .NET (托管 API)    │  (BrxMgd.dll + TD_Mgd.dll)
                    └─────────────────────┘
                              ↑
                    ┌─────────────────────┐
                    │  BRX (C/C++)        │  (与 ObjectARX 源码兼容)
                    └─────────────────────┘
                              ↑
                    ┌─────────────────────┐
                    │  内核：ACIS + ODA   │  (几何 + DWG)
                    └─────────────────────┘
```

### 2.2 与 ObjectARX 的"近似镜像"关系

BRX 在概念结构上与 ObjectARX 是近似镜像[3.1 §二 API 整体架构：六层金字塔](/platforms/autocad#二、api-整体架构-六层金字塔)：

| ObjectARX 层 | BRX 等价层 | 兼容程度 |
|---|---|---|
| AutoLISP / Visual LISP | AutoLISP（兼容 + BricsCAD 扩展） | 高 |
| COM Automation | COM Automation（BricscadApp 等） | 高 |
| Managed .NET | BrxMgd + TD_Mgd | 高（源码可共用） |
| ObjectARX | BRX | 高（源码可共用） |
| ObjectDBX | （无对应独立层，DWG 通过 ODA） | 不直接对应 |

⭐ **这种"近似镜像"是 BricsCAD 在样本中较罕见的设计取向**。其他平台（CATIA、NX、Onshape、SolidWorks 等）都采用与 AutoCAD 不同的 API 范式；只有 BricsCAD 选择了"以 ObjectARX 为参考，做高保真的并行体系"。

> **[评论]** 这种镜像策略的本质是商业选择，不是技术选择——BricsCAD 的目标客户是"已经使用 AutoCAD + ObjectARX 应用、但希望降低成本或寻求跨平台的用户"。如果 BricsCAD 的 API 风格与 ObjectARX 差异太大，迁移成本会让客户望而却步。这种"以兼容为核心战略"在样本中只有 BricsCAD 走得这么彻底。

### 2.3 二进制隔离

虽然源码兼容，但二进制层严格隔离<sup>[官方 5]</sup>：

```
同一份 source.cpp
├── 用 BRX SDK + Visual Studio → mymodule.brx (only loads in BricsCAD)
└── 用 ObjectARX SDK + VS      → mymodule.arx (only loads in AutoCAD)
```

⚠️ 不可能在两个平台间互换二进制——这点开发者必须明确意识到。

> **[推论]** 二进制隔离的原因：(1) 内部数据结构布局可能有差异，(2) 内核版本不同（BricsCAD 用较新 ACIS，AutoCAD 用 ShapeManager），(3) 商业边界考虑——Bricsys 不希望直接成为 ObjectARX 应用的运行时替代。

### 2.4 BRX 包含的能力分类

| 能力分类 | 说明 |
|---|---|
| 标准 ObjectARX 兼容功能 | 数据库读写、几何操作、UI 扩展、命令注册等 |
| "未文档化但流行"的 ARX 函数 | `acdbSetDbmod`、`acedPostCommand`、`acedEvaluateLisp`、`ads_queueexpr` 等 |
| COM 类型库（C++ 可调用） | BricsCAD 提供的 BricscadApp/BricscadDb 等 |
| Demand loading 机制 | 注册命令通过 AcadAppInfo 接口实现按需加载 |
| BricsCAD 特有 API | `BcUiPanelMFC`、BIM API、Civil API、Sheet Metal API |

⭐ **"未文档化但流行的 ARX 函数也兼容"是 BricsCAD 的一个细节战略**<sup>[官方 5]</sup>：很多 ObjectARX 应用依赖一些 Autodesk 未在文档里明说但实际可用的函数（如 `acedPostCommand`），如果 BricsCAD 不兼容这些"灰色 API"，迁移就会卡住。Bricsys 在文档中明确列出这些"undocumented but popular"函数也兼容，是对客户群的精准了解。

---

## 三、BRX C/C++ API 深度剖析

### 3.1 与 ObjectARX 源码兼容的工程实现

> **[推论]** Bricsys 在 BRX 中实现 ObjectARX 源码兼容的工程方式（基于公开资料的合理推断）：(1) 与 ObjectARX 同名的头文件、同名的类、同名的成员函数；(2) 内部实现指向 BricsCAD 的等价数据结构；(3) 对 ObjectARX 中"未文档化但被广泛使用"的入口做兼容封装。具体实现细节属 Bricsys 内部资产，本报告未找到完整的实现细节披露。

### 3.2 BRX 兼容的 ObjectARX 版本

BRX 在不同 BricsCAD 版本中跟进 ObjectARX 版本：

- **BRX V17**：源码兼容 ObjectARX 2015/2016（部分例外）<sup>[官方 18]</sup>
- **BRX V22+**：跟进更新的 ObjectARX 版本

> **[推论]** Bricsys 的兼容策略不是"完全跟随 Autodesk"，而是"尽可能保持源码兼容，对部分接口做选择性更新"。当 ObjectARX 引入新 API 时，BRX 会评估是否引入；当 ObjectARX 弃用某些 API 时，BRX 通常会保留更长时间以保护 ISV 投资。

### 3.3 SDK 分发策略：单独下载

⚠️ **BRX SDK 不随 BricsCAD 主程序安装**<sup>[官方 5]</sup>。开发者需要单独下载，且需要注册为 plugin 应用开发者（免费）。

> **[评论]** 这种"SDK 与运行时分离"的分发策略与 ObjectARX 一致——Autodesk 的 ObjectARX SDK 同样需要单独下载，需要注册开发者账户。Bricsys 在这点上保持了与 AutoCAD 生态的一致体验。

### 3.4 Sample 项目展示

BRX SDK 包含的示例项目<sup>[官方 5]</sup>：
- **BRX/C++ 示例**：custom entity、dockable dialog 等核心功能展示
- **同时可编译为 BRX 与 ObjectARX**：示例项目的构建配置同时支持两个目标，开发者可以验证"同源码不同二进制"的实际行为
- **C# 与 VB.NET 示例**：托管 .NET API 演示
- **C++/CLI 混合模式 custom entity**：展示混合模式开发
- **垂直 API 示例**：BIM、Civil、Sheet Metal 等专门 API 演示

### 3.5 自动化测试基础设施

⭐ Bricsys 维护了一套大型自动化测试套件持续监控 BRX 函数的行为<sup>[官方 5]</sup>，每个函数都会检查正常返回与错误返回——这是 Bricsys 保证"BRX 与 ObjectARX 行为兼容"的关键工程基础设施。

> **[评论]** 这种"以测试驱动 API 兼容"的工程文化在 CAD 平台中相对少见。多数 CAD 平台的 API 兼容是通过"加法兼容 + 文档承诺 + ISV 反馈"三件套来维护，自动化测试覆盖率不高。Bricsys 因为以兼容为核心战略，必须把测试覆盖率做到很高才能让客户敢迁移。

---

## 四、.NET API 深度剖析

### 4.1 核心程序集

BricsCAD .NET API 的核心程序集<sup>[官方 15]</sup>：

| DLL | 功能 |
|---|---|
| `BrxMgd.dll` | 核心 BRX 托管 API |
| `TD_Mgd.dll` | Teigha 几何/数据库托管 API（来自 ODA） |
| `TD_MgdBrep.dll`（可选） | BREP API 托管接口 |
| `TD_MgdDbConstraints.dll`（可选） | 2D 约束 API 托管接口 |

这些 DLL 位于 BricsCAD 安装目录。

### 4.2 关键工程细节：Copy Local = False

⚠️ 引用 `BrxMgd.dll` 与 `TD_Mgd.dll` 时**必须**把 Visual Studio 项目里的 `Copy Local` 属性设为 `False`<sup>[官方 15]</sup>。

> **[评论]** 这点与 AutoCAD .NET API 的要求一致[3.1 §三 .NET API](/platforms/autocad#三、对象模型-database-editor-document)——开发者用同一套工程实践就能在两个平台开发。Copy Local 设为 True 会导致运行时找不到正确的 DLL 加载位置（因为 BricsCAD 进程启动时已加载这些 DLL）。

其他 DLL（COM 引用、satellite DLL 等）的 Copy Local 设置可以按项目需要决定。

### 4.3 与 AutoCAD .NET API 源码兼容

⭐ **同一份 C# / VB.NET 源码可以编译为分别面向 BricsCAD 与 AutoCAD 的两个 DLL**<sup>[官方 15]</sup>。具体方式：

```csharp
// 单一 .cs 文件，引用条件化
#if BRICSCAD
    using Bricscad.ApplicationServices;
    using Teigha.DatabaseServices;
#else
    using Autodesk.AutoCAD.ApplicationServices;
    using Autodesk.AutoCAD.DatabaseServices;
#endif
```

build 配置切换 BRICSCAD 宏，引用对应的 .dll，输出对应的 .dll/.exe。

但运行时不可互换：为 BricsCAD 编译的 DLL 不能加载到 AutoCAD，反之亦然。

### 4.4 C++/CLI 混合模式 custom entity

BricsCAD .NET API 支持完整的 **C++/CLI 混合模式 custom entity** 开发<sup>[官方 15]</sup>——这与 ObjectARX 的能力对齐。开发者可以在同一项目中用 C++（性能关键部分）+ C#（UI 与业务逻辑）混合开发自定义实体。

### 4.5 垂直 API 也对 .NET 暴露

BricsCAD 的垂直产品 API 也有 .NET 入口<sup>[官方 15]</sup>：

- **BIM API**：建筑信息建模
- **Civil API**：土木工程（TIN Surface、GIS 等）
- **Sheet Metal API**：钣金设计

最新版本里更多 BRX 特有的类被暴露到 .NET API。例如 `BimNameSpaces` 类已从 BRX 暴露到 .NET API（具体版本以 release notes 为准）。

> **[推论]** 垂直 API 的 .NET 暴露是 BricsCAD 与 AutoCAD 的差异化点。AutoCAD 的垂直产品（Architecture、Civil 3D、MEP 等）也有自己的 .NET API，但 BricsCAD 把所有垂直 API 集成在同一个 .NET 命名空间体系下，对开发者更一致。

### 4.6 P/Invoke 与版本依赖

⚠️ 涉及 P/Invoke 调用的代码可能在不同 BricsCAD 版本间需要更新<sup>[官方 15][官方 19]</sup>。例如早期版本中的 BRX12.dll 在后续版本变成 BRX13.dll，依赖这些 DLL 名的 P/Invoke 签名需要相应更新。

> **[评论]** 这种"DLL 重命名"对纯托管代码影响不大（用 BrxMgd.dll 的代码继续工作），但对依赖底层 P/Invoke 的高级用户是个负担。这是 BricsCAD 兼容承诺的边界——内部实现细节会随版本演进，但公开 API 保持稳定。

---

## 五、几何内核：ACIS

### 5.1 ACIS 在 BricsCAD 中的位置

BricsCAD 使用 **3D ACIS Modeler** 作为几何内核<sup>[官方 6]</sup>。ACIS 由 Spatial Corporation（Dassault Systèmes 的子公司）开发与许可<sup>[百科 7]</sup>。

⚠️ **这是一个值得注意的产业事实**：BricsCAD 是 Hexagon 旗下产品，但内核是 DS 子公司提供的。这种"竞争对手共享内核"在样本平台中并不罕见——SolidWorks（DS 旗下）也使用 Siemens 的 Parasolid[3.6 §七 Parasolid 内核](/platforms/solidworks#七、属性管理-自定义属性与-equation-manager)——但 BricsCAD-ACIS 的关系比 SolidWorks-Parasolid 更微妙：

| 组合 | 平台所有者 | 内核所有者 | 关系 |
|---|---|---|---|
| SolidWorks + Parasolid | DS | Siemens | 两个最大 PLM 厂商内核共享 |
| BricsCAD + ACIS | Hexagon | DS（Spatial 子公司） | Hexagon 与 DS 在 PLM/CAD 部分竞争 |

> **[评论]** 这种"集团交叉授权"显示 CAD 内核市场的高度集中——除了 Parasolid（Siemens）和 ACIS（DS）这两大商业内核，可选项不多。新平台要么自研内核（CATIA CGM、AutoCAD AcGe 等）、要么用开源内核（OCCT），要么向两大商业内核之一付费授权。

### 5.2 ACIS 的历史与产业地位

ACIS 的核心信息<sup>[百科 7][官方 6]</sup>：

- **创始**：1985 年，Alan Grayer、Charles Lang、Ian Braid 在英国剑桥创立 Three-Space Ltd.（即 ACIS 的前身），与 Dick Sowar 的 Spatial Technology 合作开发 ACIS solid modeling kernel
- **首个版本**：1989 年发布
- **被 DS 收购**：2000 年左右被 Dassault Systèmes 收购，加入 Spatial Corporation
- **ACIS 名字含义**：最常见的解释是 **Alan, Charles & Ian's System**（创始人首字母）；也有源自希腊神话 Acis and Galatea 的说法

ACIS 的产业地位：

- 被 Spatial 称为 "30+ 年市场领导地位"<sup>[官方 6]</sup>，超过 350 个应用、300 万 seats
- 与 Parasolid（Siemens）并列为商业 CAD 内核两大主导
- AutoCAD 与 Inventor 使用的 **ShapeManager** 是 2001 年 Autodesk 从 ACIS 7.0 fork 出来的<sup>[百科 7]</sup>，之后冻结演进——这是 BricsCAD 用最新 ACIS 与 AutoCAD 用 ShapeManager 之间的关键差异

### 5.3 BricsCAD 中 ACIS 版本的特点

⭐ **BricsCAD 嵌入的 ACIS 版本相对较新**<sup>[第三方 16]</sup>。社区资料显示 BricsCAD 用 ACIS 2020+ 系列。这与 AutoCAD/Inventor 使用 ShapeManager（ACIS 7.0 fork，约 2001 年起冻结）形成关键对比：

```
ACIS 7.0 (2001)
   ├── Spatial 主线持续演进 ──→ ACIS 2025+ ──→ BricsCAD 嵌入版本（新）
   └── Autodesk fork = ShapeManager ──→ AutoCAD/Inventor（冻结状态）
```

> **[推论]** 这意味着 BricsCAD 在某些几何能力（特别是 Spatial 后期增加的功能如 Direct Editing、Polyhedral 整合等）上可能优于 AutoCAD——AutoCAD 的 ShapeManager 在 2001 年 fork 后未跟进 ACIS 主线的新功能。但具体到普通用户体验，差异未必明显，因为多数 CAD 操作只用核心几何功能。本报告未找到对此的系统性对比测试。

### 5.4 ACIS 用户群

主要的 ACIS 用户<sup>[官方 6][百科 7]</sup>：

| 软件 | 类别 | 备注 |
|---|---|---|
| **BricsCAD** | 通用 CAD | Hexagon 旗下 |
| **SpaceClaim** | 直接建模 | ANSYS 旗下 |
| **Alibre Design** | 中端 CAD | |
| **ANSYS、Abaqus** | 仿真 | |
| **Cimatron** | CAM | |
| **Rhinoceros** | 工业设计（部分） | |
| **GstarCAD、ZWCAD** | 通用 CAD（中国） | |
| **TurboCAD、ViacAD、SharkCad** | 入门级 CAD | |

> **[评论]** ACIS 用户群在中国市场相对活跃——GstarCAD、ZWCAD 都是中国本土 CAD 厂商。这反映出 ACIS 在"中端 CAD + 高度兼容"市场的稳定地位。Parasolid 则更多被高端 CAD（NX、SolidWorks）使用。

### 5.5 SAT 文件互通

ACIS 的原生交换格式是 **SAT（Standard ACIS Text）**<sup>[百科 7][第三方 20]</sup>。基于 ACIS 的 CAD 软件之间可以通过 SAT 文件实现 B-Rep 拓扑无损交换，比 STEP/IGES 等中性格式更精确。

⚠️ **不同 ACIS 版本之间不完全兼容**：高版本生成的 SAT 文件不能在低版本 ACIS 软件中打开。互通时建议导出到目标软件支持的最低 ACIS 版本。

---

## 六、UI 架构：从 wxWidgets/MFC 到 Qt/QML

### 6.1 历史 UI 框架（2002-2021）

BricsCAD 长期使用的 UI 框架组合<sup>[官方 9]</sup>：

- **Windows**：wxWidgets + MFC
- **Linux/macOS**：wxWidgets

这种组合在 2010s 早期是合理选择——wxWidgets 提供跨平台能力，MFC 提供 Windows 上的成熟 dialog/dockable panel 基础设施。

### 6.2 迁移决策（约 2021-2022）

约 2021-2022 年，Bricsys 决定把 UI 框架迁移到 **Qt/QML（+ Windows 上保留 MFC 兼容层）**<sup>[官方 9][官方 10]</sup>。

⭐ **初步估计完整迁移需要 50 人年工作量**<sup>[官方 9]</sup>，跨多个版本逐步推进——这是 BricsCAD 历史上最大的工程项目之一。

#### 6.2.1 选择 Qt/QML 的理由

Bricsys 在 Qt 官方案例研究中给出的选择动机<sup>[官方 10]</sup>：

| 动机 | 说明 |
|---|---|
| **跨平台一致性** | 一份代码同时支持 Windows / macOS / Linux 三个平台，不再需要为每个平台独立维护 UI 团队 |
| **像素级设计还原** | wxWidgets/MFC 时代设计师 mockup 难以像素级一致 |
| **WebAssembly 演进空间** | Qt 6 支持编译到 WASM，给"将来上 Web"留了选项 |
| **QML 声明式开发提速** | QML 语法对 UI 开发节奏比传统 C++ widget 快 |
| **优秀的官方文档** | Bricsys 评价 Qt 文档"在他们用过的框架中最好之一" |
| **商业支持** | Qt 商业 license 提供高质量与快速响应 |

### 6.3 渐进迁移策略

⚠️ **Bricsys 没有选择"一刀切重写"，而是渐进迁移**<sup>[官方 9]</sup>：

```
2021-2022      ──→ 启动迁移：选定 Qt/QML 作为新 UI 框架
2022-2023      ──→ 早期模块用 Qt/QML：Start Page、对话框等
V24 (2024)     ──→ RIBBON 命令基于新 UI 框架
V25-V26+ (2025+)──→ 持续把更多模块迁移到 Qt/QML
未来           ──→ 完全迁移到 Qt/QML（保留必要的 MFC 兼容层）
```

⭐ **MFC 兼容层不强制 ISV 立即重写**——`BcUiPanelMFC` dockable panel 让二次开发者可以在面板中嵌入 Qt 控件<sup>[官方 21]</sup>，配置 `QT5_SDK_PATH` 环境变量后，Visual Studio 项目可以编译同时使用 Qt 与 MFC 的 BRX 模块。

> **[评论]** 这是文档 1 §4 兼容工程经济学讨论的现实样本[回链：文档 1 §4 兼容承诺与工程经济学]。BricsCAD 选择"渐进迁移 + 兼容层共存"而非"一刀切"——保留 ISV 投资、避免 V25 一次性切换带来的客户流失风险，但代价是 Bricsys 内部需要长期维护两套 UI 体系。

### 6.4 Qt/QML 在 CAD 行业的位置

文档 1 §5 把 UI 扩展归纳为两条路线[回链：文档 1 §5 UI 扩展机制]：
- **路线 A 原生 UI**：dialog/widget，原生性能（典型：SolidWorks MFC、AutoCAD MFC）
- **路线 B 嵌入 Web UI**：CEF 嵌入浏览器内核（典型：SketchUp UI::HtmlDialog、AutoCAD APS Viewer）

⭐ **BricsCAD 选了"第三条路"——原生 UI 但用现代声明式框架（Qt/QML）**：

| 维度 | 路线 A 原生 widget | 路线 B 嵌入 CEF | BricsCAD：Qt/QML |
|---|---|---|---|
| UI 描述方式 | 命令式（C++ widget 代码） | 声明式（HTML/CSS） | 声明式（QML） |
| 跨平台 | Windows-centric | 完全跨平台 | 完全跨平台 |
| 进程模型 | 同进程 | 多进程（Chromium） | 同进程 |
| 内存占用 | 低 | 高（Chromium 重） | 中等 |
| 声明式深度 | 弱 | 强 | 中等（QML 不如 React） |

> **[评论]** Qt/QML 对 CAD 的适配在样本中除了 BricsCAD 还有 FreeCAD（用 Qt widget，不是 QML）[3.8 §二 API 整体架构](/platforms/freecad#二、api-整体架构-5-层-mvc)。NX 也长期用 Qt（widget 风格）。但**BricsCAD 是样本中唯一选择 Qt/QML 声明式 UI** 的——这条路让 UI 描述代码量显著减少，跨平台一致性也最强。代价是 QML 的能力边界——对于复杂的 CAD 交互（实时 3D viewport、复杂手势等），QML 仍需配合 C++ 自定义 item。

### 6.5 工程基础设施支撑

Bricsys 在 Qt 演讲中提到为这次迁移开发的工具<sup>[官方 9]</sup>：

- **QML 实时重载**：开发期改 QML 立即看到效果，不需要重启 BricsCAD
- **QML 自动化测试集成**：把 QML UI 测试集成到现有 BRX 测试基础设施
- **C++ 与 QML 通信范式**：定义清晰的"前后端"通信协议——backend（C++）保持高性能与数据访问，frontend（QML）专注 UI 表达

> **[推论]** 这套基础设施本身的工程量也不小——估计可能占 50 人年估算的相当比例。但一旦建立，加速了所有后续的 UI 模块迁移。这是文档 1 提到的"工程基础设施投资"的经典样本。

### 6.6 ISV 在 UI 迁移中的角色

⚠️ **现有 BRX ISV 不需要立即重写**<sup>[官方 21]</sup>：
- 保留 MFC 兼容 API（`BcUiPanelMFC` 等）
- 现有的 dockable panel、PropertyManager 风格 dialog 继续工作
- 想用 Qt 的 ISV 可以选择性地在面板中嵌入 Qt 控件

> **[评论]** 这种"渐进开放 + 不强制迁移"的策略保护了 ISV 投资。其他 CAD 平台在大规模 UI 重构时常常出现 ISV 流失（典型例子是 Autodesk 当年从 16-bit 迁移到 32-bit 的转型期）。

---

## 七、与 AutoCAD 的兼容承诺：详细分析

BricsCAD 的核心战略是 AutoCAD 兼容。详细看这种兼容承诺的层次：

### 7.1 文件兼容（DWG）

通过 ODA Drawings SDK 实现 DWG 读写<sup>[官方 8]</sup>：

- **支持 AutoCAD DWG 所有主要版本**：从 AutoCAD R12 到最新版本
- **AEC custom objects**：通过 ODA 的 Architecture/Civil/Mechanical SDK 支持 ACA、C3D、AcM 的 custom objects
- **DWG 写入认证**：BricsCAD 写出的 DWG 可以在 AutoCAD 中无损打开

⚠️ ⭐ **Bricsys 团队估计自研 Drawings SDK 需要 50 人年**<sup>[官方 8]</sup>——这与 UI 迁移工程量相当。这种估算也解释了为什么 BricsCAD 选择持续依赖 ODA 而不是自研。

> **[评论]** Bricsys 在 ODA showcase 中明确表态："如果我们没有 Drawings SDK，就需要一个庞大的团队专门做 .dwg 互操作。这对我们来说是不盈利的。"<sup>[官方 8]</sup>这是文档 1 §4 兼容工程经济学的另一个样本——通过共同体（ODA）分摊"事实标准但不开放"格式的逆向工程成本。

### 7.2 API 兼容（BRX 与 .NET）

如前所述，BRX 与 ObjectARX 源码兼容、.NET API 与 AutoCAD .NET API 源码兼容。覆盖度：

| API 类别 | 兼容程度 | 备注 |
|---|---|---|
| 数据库读写 | 高 | AcDbDatabase、AcDbBlockTable 等 |
| 几何对象 | 高 | AcGePoint、AcGeVector 等 |
| Custom Entity | 高 | BcDbCustomEntity 与 AcDbCustomEntity 概念对应 |
| 命令与事件 | 高 | AcEdJig、命令注册等 |
| UI 扩展 | 中 | 早期 MFC API 兼容；新 Qt API 不兼容 |
| Reactor 机制 | 高 | AcDbObjectReactor 等 |
| LISP 兼容 | 高 | 大多数 AutoLISP 函数可用 |
| 部分 undocumented 函数 | 中-高 | 选择性兼容流行的"灰色 API" |

### 7.3 行为兼容（命令与系统变量）

BricsCAD 持续做与 AutoCAD 命令、系统变量的行为对齐<sup>[官方 11]</sup>：

- 同名命令（LINE、CIRCLE、HATCH 等）行为一致
- 同名系统变量（DIMSCALE、INSUNITS 等）含义一致
- 部分 BricsCAD 特有命令（如 BIM 相关）使用不同前缀避免冲突

⚠️ ⭐ **行为兼容比文件兼容、API 兼容更难**——它涉及大量"约定俗成"的细节，比如某个命令在特定状态下的对话框文本、按 Tab 键的行为等。Bricsys 通过 §3.5 提到的自动化测试套件维护这种行为兼容。

### 7.4 不兼容的明确边界

BricsCAD 与 AutoCAD 不兼容的明确边界<sup>[官方 5]</sup>：

- **二进制模块不互换**：.brx ≠ .arx，DLL 不能跨平台加载
- **某些专有 API**：AutoCAD 的部分 API（特别是与 AutoCAD 特有功能绑定的）可能不在 BRX 中实现
- **垂直产品的 API**：BricsCAD 的 BIM、Mechanical 等垂直 API 与 AutoCAD Architecture、Mechanical 不兼容
- **新引入的 API**：AutoCAD 引入新 API 后，BRX 通常会延迟一段时间才支持

> **[评论]** "兼容到什么程度"是 BricsCAD 长期的工程权衡。完全 100% 兼容意味着永远跟在 Autodesk 后面（因为 Autodesk 定义事实），这又削弱了 BricsCAD 自身的差异化（BIM、AI 等创新方向）。Bricsys 的策略是"高保真兼容 + 选择性创新"。

---

## 八、产品矩阵与商业策略

### 8.1 BricsCAD 产品线

BricsCAD 的产品矩阵<sup>[官方 1][官方 12]</sup>：

| 产品 | 定位 | 主要能力 |
|---|---|---|
| **BricsCAD Lite** | 入门 2D | 2D 制图，基础 |
| **BricsCAD Pro** | 通用 2D + 3D | 2D 制图 + 3D 实体建模 + 可视化 |
| **BricsCAD BIM** | 建筑信息建模 | BIM 工作流 + IFC + 行业 schema |
| **BricsCAD Mechanical** | 机械与钣金 | 钣金、装配、运动学动画、BOM |
| **BricsCAD Ultimate** | 全功能 | Lite + Pro + BIM + Mechanical 合一 |
| **BricsCAD Shape** | 免费 3D 概念建模 | 简化的 3D 建模工具 |
| **BricsCAD Communicator** | 数据交换 | 多 CAD 格式互通 |
| **Bricsys 24/7** | 云协作 | 项目协作平台 |

### 8.2 商业模式：永久授权 + 订阅并行

BricsCAD 在样本中有一个独特的商业策略——**同时提供永久授权与订阅授权**<sup>[官方 1]</sup>。

| 商业模式 | BricsCAD 状态 | 对比其他平台 |
|---|---|---|
| 永久授权 | ✅ 仍提供 | AutoCAD/CATIA/NX/SolidWorks 已淘汰永久授权 |
| 订阅授权 | ✅ 提供 | 全行业通用 |
| 教育免费 | ✅ 提供 | 行业通用 |
| 免费 BricsCAD Shape | ✅ | 类似 SketchUp Free 的策略 |

⭐ **保留永久授权是 BricsCAD 在转型订阅潮中的关键差异化**[3.7 §一 订阅制转型](/platforms/sketchup#一、历史演进-从-last-software-到-trimble-ai-时代)；[3.6 §九 5 FD/年](/platforms/solidworks#九、solidworks-2026-aura-ai-与-30-周年)。AutoCAD 2017 起强制订阅、SketchUp 2020 起强制订阅、SolidWorks 通过 3DEXPERIENCE Works 推订阅——但 BricsCAD 至今仍提供永久授权选项。

> **[评论]** 这是 BricsCAD 在中小企业、价格敏感市场（包括中国市场）的核心竞争力之一。对很多客户来说，"一次买断 + 长期使用"的偏好深植于会计与采购流程，订阅模式在这类客户中阻力很大。

### 8.3 价格定位

BricsCAD 的定价策略<sup>[第三方 22]</sup>：

- **永久授权**：约 AutoCAD 永久授权时代价格的 1/4 - 1/3
- **订阅授权**：约 AutoCAD 订阅价格的 1/3 - 1/2
- **跨产品升级**：从 Lite 升级到 Pro 或 BIM，价格阶梯设计相对友好

> **[推论]** "AutoCAD 高保真兼容 + 价格优势"是 BricsCAD 商业模式的核心。这种模式对 Autodesk 形成的竞争压力随着订阅价格上涨而加大——很多原 AutoCAD 客户重新评估 BricsCAD 作为成本优化路径。

### 8.4 全球市场分布

BricsCAD 的市场地理分布<sup>[第三方 2][新闻 17]</sup>：

| 区域 | 状态 | 备注 |
|---|---|---|
| **欧洲** | 较强 | 总部在比利时，欧洲客户较多 |
| **亚洲（含中国）** | 中等 | 在日本、韩国、中国有一定渗透 |
| **北美** | 历史薄弱，被 Hexagon 收购后加强 | 收购前 2017 年北美市场份额很低 |
| **拉美** | 弱 | |
| **30 万用户、110+ 国家、14 种语言** | 全球数据 | [第三方 2] |

---

## 九、独特设计哲学提炼

> **[本节适用边界]** 本节归纳基于本系列覆盖的 9 个样本平台的对比观察。在更广 CAD 业界（PTC Creo、Inventor、Solid Edge、Rhino、Revit 等未覆盖平台）中是否罕见，需结合系列扩展进一步验证。

### 9.1 "AutoCAD API 兼容作为核心战略"

⭐ BricsCAD 是样本中**唯一**以"AutoCAD API 兼容"作为核心商业战略的非 Autodesk 平台。这种选择有几层含义：

- **不与 AutoCAD 在 API 创新上竞争**——BricsCAD 不发明全新的 API 范式（与 Onshape REST + FeatureScript 形成对比[3.4 §二 API 整体架构](/platforms/onshape#二、api-整体架构-双轨设计-rest-featurescript)），而是把"做最好的 ObjectARX 兼容运行时"作为核心
- **以质量与价格创造差异化**——更新的 ACIS 内核、更好的跨平台、更低的价格、永久授权选项
- **依赖 ODA 共同体的逆向工程成果**——而不是自研 DWG 实现

> **[评论]** 这是个很务实的战略选择。在工业软件领域，"100% 兼容主流标准 + 价格优势 + 局部创新"是相当多公司的选择（Linux 兼容 Windows、LibreOffice 兼容 MS Office、ZWCAD/GstarCAD 兼容 AutoCAD）。BricsCAD 在 CAD 领域是这种模式做得较成熟的代表。

### 9.2 "大规模 UI 框架在役迁移的工程治理"

⭐ BricsCAD 的 wxWidgets/MFC → Qt/QML 50 人年迁移是样本中**正在进行的最大 UI 工程治理样本**。值得学习的点：

1. **不停服重写** —— V24/V25/V26 持续发布、收入持续，迁移在背景中进行
2. **MFC 兼容层保留 ISV 投资** —— `BcUiPanelMFC` 让 ISV 不需要立即重写
3. **基础设施先行** —— QML 实时重载、QML 自动化测试在迁移开始时就建立
4. **明确"前后端分离"** —— C++ backend 与 QML frontend 通信范式定义清楚

> **[评论]** CAD 平台做大规模 UI 重构有失败案例（如某些产品迁移期失去主流市场）。BricsCAD 的渐进策略保留了客户基础与 ISV 生态，这是教科书级的工程治理。

### 9.3 "选择 Qt/QML 而非嵌入 Web UI"

BricsCAD 在 UI 现代化时选择 Qt/QML 而非 CEF 嵌入 Web UI（如 SketchUp、AutoCAD APS Viewer 那样）[3.7 §六 UI::HtmlDialog](/platforms/sketchup#六、ui-htmldialog-web-集成的现代化路径)：

- **保留原生性能** —— Qt 比 Chromium 进程内嵌轻得多
- **像素级设计还原** —— 桌面 CAD 仍重视 UI 的紧凑与精确
- **WebAssembly 演进可能** —— Qt 6 支持 WASM，给将来上 Web 留路

> **[评论]** 这反映 Bricsys 认为 CAD 桌面体验仍是核心，没有像 Onshape 那样押注 100% 浏览器原生路径。这是个保守但务实的判断——绝大多数 CAD 用户仍在桌面环境工作。

### 9.4 "ACIS 现代版本带来的几何能力优势"

BricsCAD 嵌入较新版本的 ACIS（2020+ 系列），相对 AutoCAD/Inventor 用 ShapeManager（ACIS 7.0 fork 后冻结）有潜在的几何能力差异。具体差异在 Direct Editing、Polyhedral 整合等领域可能有体现。

> **[推论]** 这种"内核版本优势"是 BricsCAD 的隐性竞争力——客户层面可能感知不到，但在专业 CAM/CAE 集成场景中，使用更新内核可能让 BricsCAD 与下游工具的协同更稳定。本报告未找到对此的系统性对比测试。

### 9.5 "保留永久授权"作为商业差异化

在 AutoCAD/CATIA/NX/SolidWorks 都强制订阅的趋势下，BricsCAD 保留永久授权选项是商业模式上的差异化[3.7 §九 订阅制转型](/platforms/sketchup#九、sketchup-2025–2026-新一代演进)；[3.1 §一 历史演进 2017 转型](/platforms/autocad#一、历史演进-从-r12-到-2027-的-api-时间线)。这种选择特别契合：
- 中小企业的"一次买断"采购偏好
- 价格敏感市场（中国、东南亚等）
- 政府与国企的资产折旧采购流程

> **[评论]** 这种保留可能不是永久的——随着 BricsCAD 也加入 BIM、AI、云协作等持续运营成本高的功能，订阅模式的财务合理性可能逐步占优。但短期内（5-10 年）保留永久授权是 BricsCAD 重要的客户吸引力之一。

### 9.6 "Hexagon 集团内的位置"

被 Hexagon 收购后，BricsCAD 与 Hexagon 集团其他业务（测量仪器、计量、地理空间、PPM）形成协同。这种"集团内 CAD"位置在样本中有几个对照：

| 平台 | 集团位置 | 协同能力 |
|---|---|---|
| AutoCAD | Autodesk 旗舰 | Autodesk 全栈 AEC + 制造 |
| CATIA | DS 旗舰 | DS 3DEXPERIENCE 平台 |
| NX | Siemens DI Software | Siemens 工业 4.0 |
| SolidWorks | DS 中端 | DS 3DEXPERIENCE Works |
| **BricsCAD** | **Hexagon Octave** | **测量 + CAD + BIM + 工厂数字化** |

> **[评论]** BricsCAD 在 Hexagon/Octave 集团内的位置与 SolidWorks 在 DS 集团内类似——都是"中端 CAD + 集团其他高端业务的入口产品"。这种位置让 BricsCAD 不需要单独承担全部研发投入，可以与集团测量、BIM、PPM 业务共享部分基础设施与客户关系。

---

## 十、启示与争议

> **[本节适用边界]** 以下启示是基于 BricsCAD 案例的归纳，**仅供参考**。具体决策需结合客户基础、预算、生态等多重因素。

### 10.1 启示

1. **API 兼容作为商业战略是可行路径**：BricsCAD 显示"做最好的 ObjectARX 兼容运行时"是可行的商业战略，而不是必须发明全新 API。新平台决策时建议明确"是创新还是兼容"，而不是两头摇摆。
2. **大规模 UI 重构应该渐进**：BricsCAD 50 人年的 Qt 迁移采用"渐进 + 兼容层"策略，保留 ISV 与客户。新平台决策时建议早早规划 UI 框架的演进路径，避免十年后被动重构。
3. **依赖共同体共担成本**：BricsCAD 通过 ODA 共担 DWG 兼容成本（自研需 50 人年），让内部精力聚焦 UX/AI/BIM 等差异化方向。新平台建议识别"事实标准但不开放"的格式，考虑通过共同体分摊成本。
4. **Qt/QML 在 CAD 行业的可行性**：BricsCAD 与 FreeCAD 共同显示 Qt 是 CAD 桌面 UI 的可行选择。Qt/QML 比传统 widget 更适合现代 UI 体验。
5. **保留永久授权可能是中端市场的差异化**：在订阅大潮中，永久授权对部分客户群仍是核心吸引力。新平台不必盲目跟进"全订阅"。
6. **"集团内中端 CAD"是常见结构**：BricsCAD 之于 Hexagon、SolidWorks 之于 DS 的相似定位显示这种结构的可持续性。

### 10.2 争议点

- **几何内核依赖 ACIS 的长期风险**：ACIS 由 DS 子公司 Spatial 提供，理论上 DS 可以通过商业条款影响 BricsCAD（虽然现实中没有发生）。Bricsys 是否考虑过几何内核的长期备选（自研、OCCT、C3D 等）？这是公开资料中未明确披露的战略问题。
- **UI 迁移的真实进度**：50 人年估算与实际进度的差距如何？V24 (2024) 只是 RIBBON 模块基于新框架，距离"完全 Qt/QML"还有相当距离。**长期工程项目的进度管理是 Bricsys 的持续挑战。**
- **永久授权的可持续性**：BIM、AI、云协作等功能的研发与运营持续成本不低，永久授权是否能长期支撑这些方向？
- **Hexagon/Octave 拆分对 BricsCAD 的影响**：拆分后 Octave 是否会上市？BricsCAD 的优先级是否会变化？这些都是 2025-2026 期间的开放问题。

---

## 十一、行业观察：中国市场与国产化讨论

> ⚠️ **章节定位说明**：本章内容**主要基于公开行业报告与社区观察的归纳，不构成市场研究结论**。所有"主流""主导""渗透"等表述应理解为**作者基于公开信息的观察印象**，而非基于市场调研机构的硬数据。重要决策应核对当前的市场调研报告（Gartner、IDC、艾瑞、易观等）。

在中国市场语境下，BricsCAD 的相关观察集中在三点：

- **作为国产 CAD 国际版参考的特殊价值**：BricsCAD 与中国本土的中望（ZWCAD）、浩辰（GstarCAD）走相同的商业逻辑——"AutoCAD 高保真兼容 + 价格优势"，且都基于 ODA Drawings SDK 实现 DWG 兼容，都用 ACIS 作为几何内核。BricsCAD 的工程实践（特别是 BRX 兼容深度、自动化测试覆盖、UI 渐进迁移）是中望/浩辰可参照的国际级标杆。
- **市场渗透相对有限**：BricsCAD 在中国市场的渗透弱于中望、浩辰——中国本土厂商有更深的本地化、更激进的价格、更紧密的政府/国企采购关系。但 BricsCAD 在外资在华企业、跨国设计公司、BIM 项目中有一定使用基础。
- **BIM 与 AI 方向的差异化**：BricsCAD BIM 在中国 BIM 项目中是 Revit、ArchiCAD、广联达 GTJ 之外的国际选项之一。中国本土 BIM 厂商（广联达、品茗、鸿业等）的核心壁垒是"对中国规范、定额、计价的本地化理解"，BricsCAD BIM 在这点上相对薄弱。

> **[推论]** BricsCAD 在中国 CAD 国产化讨论中的间接影响——它证明了"AutoCAD 高度兼容 + 价格优势"路线的国际可行性，给国内厂商提供商业模式参考。但中国本土厂商有自己的本地化优势，BricsCAD 难以在中国直接竞争。本报告未找到 BricsCAD 在中国市场份额的可靠量化数据。

更广的中国市场讨论与国产化路径归纳，见文档 1 附录 A：行业观察附录。

---

## Caveats

- **样本覆盖局限**：本报告基于公开资料，无法覆盖 BRX SDK 的所有内部细节（BRX 的具体源码兼容实现、内部数据结构布局、与 ObjectARX 同步的具体节奏等是 Bricsys 内部资产）。
- **"50 人年"估算**：UI 迁移 50 人年与 Drawings SDK 50 人年都是 Bricsys 公开披露的估算<sup>[官方 8][官方 9]</sup>，具体的会计口径与实际工时统计未公开。
- **ACIS 版本细节**：BricsCAD 嵌入的具体 ACIS 版本随 BricsCAD 版本演进而变化，本报告引用的 "ACIS 2020+" 是社区观察<sup>[第三方 16]</sup>，具体版本以 release notes 为准。
- **市场份额量化**：BricsCAD 全球用户超 30 万、110+ 国家是 Bricsys 公开数据<sup>[第三方 2]</sup>，但不同来源的数字差异较大；本报告未引用具体市场份额百分比。
- **2017 年营收 1300 万欧元**：来自收购公告<sup>[新闻 3]</sup>。2022 年营收 3810 万欧元的数字来自 Tracxn<sup>[第三方 13]</sup>，未经 Bricsys 官方确认。
- **Hexagon/Octave 拆分**：截至 2026 年初仍在评估或进行中<sup>[官方 14]</sup>，最终架构与时间表可能变化。
- **历史时间线模糊点**：BricsCAD 退出 IntelliCAD 体系的确切时间点社区资料不一，本报告未做精确归因。
- **行业观察附录的判断**：第十一章的中国市场内容是行业观察，不是市场研究结论。重要决策应核对市场调研机构数据。
- **回链精度局限**：本文档的章节回链遵循中文一级编号粒度（§一/§二/§三）。

---

## 参考来源

### 官方
1. [官方 1] Bricsys 公司主页 - https://www.bricsys.com/en-us/about
2. [官方 4] Hexagon 收购公告 - https://hexagon.com/company/newsroom/press-releases/2018/hexagon-construction-solutions-bricsys-acquisition
3. [官方 5] BRX API - BricsCAD V24 Developer Reference - https://developer.bricsys.com/bricscad/help/en_US/V24/DevRef/source/BRX_01.htm
4. [官方 6] What is an ACIS solid? Bricsys Blog - https://www.bricsys.com/blog/what-is-an-acis-solid-and-why-should-you-care
5. [官方 8] Bricsys ODA Member Showcase - https://www.opendesign.com/member-showcase/bricsys
6. [官方 9] Porting a Large Desktop CAD Application to Qt - Qt 资料 - https://www.qt.io/resources/videos/porting-a-large-desktop-cad-application-to-qt
7. [官方 10] Bricsys's Mission-Critical CAD Tools | Built With Qt - https://www.qt.io/bricsys-built-with-qt
8. [官方 11] What's new in BricsCAD V24 - https://bricscad.octave.com/bricscad/v24
9. [官方 12] BricsCAD product portfolio - 产品矩阵
10. [官方 14] Hexagon 公司公告 - Octave 拆分
11. [官方 15] BricsCAD .NET API documentation - Developer Reference - https://developer.bricsys.com/bricscad/help/en_US/V22/DevRef/source/dotNET_overview.htm
12. [官方 18] BRX V17 - Developer Reference - https://developer.bricsys.com/bricscad/help/en_US/V17/DevRef/source/BRX_01.htm
13. [官方 19] BricsCAD Release Notes - https://boa.bricscad.octave.com/common/releasenotes.jsp
14. [官方 21] Dockable Panel in Qt - BricsCAD Forum - https://forum.bricsys.com/discussion/38732/dockable-panel-in-qt

### 新闻
15. [新闻 3] Hexagon Acquires Bricsys - Bricsys News - https://www.bricsys.com/news/hexagon-acquires-bricsys
16. [新闻 17] Hexagon Acquires Bricsys - Digital Engineering 24/7 - https://www.digitalengineering247.com/article/hexagon-acquires-bricsys

### 百科
17. [百科 7] ACIS - Wikipedia - https://en.wikipedia.org/wiki/ACIS

### 第三方
18. [第三方 2] BricsCAD - What's the story behind the software? - MagiCAD Group - https://www.magicad.com/bricscad-whats-the-story-behind-the-software/
19. [第三方 13] Bricsys - BricsCAD - 2026 Company Profile - Tracxn
20. [第三方 16] CAD Data Interoperability around ACIS - https://www.cadinterop.com/en/formats/neutral-format/acis.html
21. [第三方 20] Geometric modeling kernel - Wikipedia 与 ScienceDirect 综合
22. [第三方 22] BricsCAD pricing 公开报道与社区资料

---

*完。*

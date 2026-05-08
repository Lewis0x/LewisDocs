# 跨平台 CAD UI 框架研究

> 文档 4｜横向研究系列｜通用 CAD 平台 API 设计哲学
>
> **本文档定位**：基于 8 个样本 CAD 平台 API 深度剖析，从 **UI 框架** 这一单一维度做横向提取。是文档 2（厂商 API 横向对比）下的"UI 框架"分册。
>
> **目标读者**：决定"我们的 CAD ISV 应用在 N 个 CAD 上怎么写 UI"的架构师；评估"我们要不要做一款 CAD，UI 怎么选"的新平台决策者。
>
> **不是**：CAD UI 设计教程、Qt / CEF 入门读物、UX 指南。

---

## 阅读约定

与本系列其余文档一致：`<sup>[类别 N]</sup>` 标来源；`> **[推论]**` 是基于事实的合理推断；`> **[评论]**` 是作者归纳；`⚠️` 是勘误或重要提示。证据等级 A（官方）/ B（行业资料）/ C（基于行业经验推断，待验证）。

---

## TL;DR

- **CAD 的 UI 不是"应用的可选层"**：参数化建模需要 <Term def="参数化 CAD 中的两段式交互模式：用户改一个尺寸 / slider，UI 实时显示重算预览（transient state）；用户点 commit / cancel 决定是否写入持久数据。NX Builder + Commit、CATIA Spec/Result/Update、FreeCAD task panel 都是此范式的具体实现。">实时预览 + commit/rollback</Term> 的两段式交互，与 3D viewport 紧密耦合，决定了 UI 框架不能简单"用最新 React + 三方组件库"了事。
- **样本中并存 5 类 UI 范式**（按 ISV 视角）：① **原生桌面 toolkit**（MFC / Qt 直接绑定）；② **.NET 托管**（WinForms / WPF / SolidWorks PMP）；③ **嵌入 Web**（CEF / WebView2 包裹 HTML/JS bundle）；④ **声明式 dialog**（NX Block UI Styler / FreeCAD task panel / CATIA Modeler dialog）；⑤ **纯 Web**（Onshape React 前端 + WebGL viewport / iTwin Viewer 组件）。
- **桌面 CAD 在 2017–2020 间集体迁移到 <Term def="Chromium Embedded Framework：把 Chromium 渲染引擎打包成 C++ 库，让原生应用嵌入完整 HTML/CSS/JS 运行时。binary ~150MB（自带 Chromium）。是桌面应用嵌入 web UI 的事实标准。">CEF</Term>**：SketchUp 2017 引入 `UI::HtmlDialog` 替代旧 WebDialog [回链：3.7 §三 现代 UI::HtmlDialog（SU 2017+）]；AutoCAD / SolidWorks 也在多个对话框嵌 Chromium。背后是"用 Web 写 ISV 插件 UI 比手写 MFC 快 10 倍"的工程现实。
- **NX Block UI Styler 是样本中唯一"开发者不写 UI 代码"的设计**：拖放定义 dialog blocks，编译器自动生成 4 种语言（C++ / C# / Python / Java）的对等 stub 代码 [回链：3.3 §二 Common API 的"四语言对等"哲学]。这是"四语言对等"在 UI 层的延伸——也是样本中唯一一个把 UI 当成"声明式资源"而非代码的 CAD。
- **Onshape 是唯一"完全没有桌面 UI 框架问题"的样本**：所有 UI 都是浏览器端 React + WebGL，用 REST 调用驱动 [回链：3.4 §三 git 式四层数据模型]；FeatureScript 驱动 feature dialogs。代价是"必须接受浏览器作为 UI 边界"——CSP、扩展冲突、版本碎片都成为 UI 风险。
- **FreeCAD 的 <Term def="FreeCAD 特色的“非弹窗对话框”模式：把对话框嵌成左侧工具栏的临时面板，参数化编辑期间 viewport 操作不被打断。Qt + Python 实现。SolidWorks PropertyManager Page (PMP) 是同类思路的商业版本。">task panel</Term>** 模式是开源 CAD 中讨论最多的设计 [回链：3.8 §三 5 层架构]：把对话框嵌成左侧工具栏临时面板，无需弹窗中断 viewport 操作。**SolidWorks PMP（PropertyManager Page）** 是同类思路的商业版本 [回链：3.6 §四 IModelDocExtension 与 PMP]。
- **CEF / <Term def="Microsoft 2020 GA 的轻量 web 嵌入控件：依赖系统 Edge runtime 而不自带 Chromium，binary ~10MB（vs CEF ~150MB+）。仅 Windows 10/11，跨平台不如 CEF。">WebView2</Term> 替代关系存在但样本中尚未观察到大规模迁移**：WebView2 binary 约 10MB（依赖系统 Edge），CEF 约 150MB+（自带 Chromium）；前者优势是体积，后者优势是版本自主可控 + 跨 OS [证据等级 C]。
- **跨多 CAD 的 ISV 几乎必选 CEF / Web 路径**：手写 N 套原生对话框是工程不可承受之重；CEF + 共享 HTML/CSS/JS bundle + 平台桥（IPC 把 CAD API 暴露给 JS）是跨 CAD 通用 UI 的事实标准。
- **ISV / 新平台的 UI 决策是 SDK 战略的一部分**：Onshape 选纯 Web → 插件作者画像偏年轻 web dev；NX Block UI 让 UI 编辑近乎零成本、四语言对等 → 大型 ISV 敢做深度集成；FreeCAD Qt + Python → 开源贡献者门槛低。

---

## Key Findings

1. **样本中除 Onshape 外，其余 7 个桌面 CAD 都有"原生 widgets + 嵌入 Web"的混合层**——纯原生 UI 与纯 Web UI 都不构成完整方案。
2. **CEF 在 SketchUp 中的引入时间点**：SU 2017 替代旧 WebDialog 提供 `UI::HtmlDialog` API [回链：3.7 §三 现代 UI::HtmlDialog（SU 2017+）]；其余样本平台 CEF 引入时间在 2017±2 年区间。
3. **NX Block UI Styler 自动生成 4 种语言代码**：C++、C#、Python、Java；不直接生成 VB.NET，但 .NET 程序集可被 VB.NET 调用 [回链：3.3 §二]。
4. **AutoCAD 的 6 层 UI 通道**：AutoLISP（最薄）→ VBA / Visual LISP IDE → COM Automation → .NET → ObjectARX C++（最深）→ Web Browser API [回链：3.1 §二 API 整体架构：六层金字塔]。
5. **CATIA UI 不是 Qt / MFC 而是自家 NLS（Nouvelle Look and Style）**：Dassault 内部开发的 UI 工具集，CAA dialog 基于此构建。第三方资料较少，是 CATIA "黑盒"特征之一 [证据等级 B]。
6. **iTwin.js Frontend 是纯 React 组件库**：Frontend / Backend / Common 三段架构中，Frontend 完全是浏览器端 React + Three.js / WebGL，与 MicroStation 桌面 UI 完全独立 [回链：3.5 §五 iTwin.js 三段架构]。
7. **SolidWorks PMP 的具体技术名**：`IPropertyManagerPage2` 接口；UI 自动嵌成左侧 Feature Manager 的子面板 [回链：3.6 §四]。
8. **FreeCAD UI 是 Qt 5 / Qt 6**：Qt Designer 生成 `.ui` XML 文件，运行时由 Gui 模块加载；FeaturePython 让 Python 类直接成为 DocumentObject 的 UI 渲染对象 [回链：3.8 §四 FeaturePython]。

---

## 一、为什么 CAD 的 UI 框架选择特殊

非 CAD 应用（办公、游戏、创意工具）的 UI 选择已有相对成熟的"业界共识"——平台原生 toolkit / Electron / 游戏引擎渲染。CAD 不一样，因为有几个**领域特有的约束**：

### 1.1 3D viewport 与 widgets 必须共存

CAD 应用的核心是"在 3D 视图里直接操作几何"，意味着：
- 大部分屏幕面积是 3D viewport（OpenGL / DirectX / WebGL 渲染）
- widgets（工具栏、属性面板、对话框）必须**叠在 viewport 之上**或**贴在 viewport 之旁**，不能遮挡用户正在编辑的几何
- viewport 与 widgets 之间需要双向数据流：选了一个 face → 属性面板自动定位到该 face；改了属性 → viewport 高亮预览

通用 UI 框架（Web Material UI / Qt Widgets）不为这种"渲染面 + widget 互动"原生设计。CAD UI 框架要么**自己造一套 widgets 与渲染层强耦合**（NX Block UI、CATIA NLS），要么**做"native widget + viewport overlay"的桥**（FreeCAD Qt + Coin3D），要么**把整个东西扔进浏览器**（Onshape React + WebGL）。

### 1.2 DPI / 缩放 / 单位精度

CAD 用户操作"亚毫米精度的 mate 距离 = 0.01mm"。在 4K 屏 + 200% 缩放下，1 像素的鼠标偏移不可接受。CAD UI 框架必须：
- 区分 <Term def="逻辑像素：抽象坐标（用于 widget 布局）；物理像素：屏幕实际像素（用于精度操作）。1 逻辑像素在 1080p 显示器上是 1 物理像素，在 4K 200% 缩放下是 2 物理像素。CAD 的精度数值必须按物理像素映射。">逻辑像素</Term> 与物理像素
- 数值输入框支持单位带宽（输入 "10mm" 自动识别）+ 表达式（"10*sin(30deg)"）

⚠️ SketchUp SU 2025 引入的 "Logical Pixels" API 就是这个问题的迟到回应 [回链：3.7 §六 SU 2025 新引入的逻辑像素]——其他 CAD 在 1990s–2000s 就解决了。

### 1.3 参数化建模的"实时预览 + commit/rollback"

参数化 CAD 的"修改一个尺寸 → 预览 → 确认 / 撤销"两段式交互，要求 UI 框架原生支持 transient state 与 commit/rollback 按钮，并能在 100ms~10s 重算期间显示进度而不冻结。

NX Builder + Commit [回链：3.3 §三 Common Object Model：Session/Part/Feature/Builder]、CATIA Spec/Result/Update [回链：3.2 §六 Spec/Result/Update：CATIA 特征建模哲学]、FreeCAD task panel——都是 CAD UI 对这种 lifecycle 的特殊支持。普通 UI 框架没有这个 lifecycle。

### 1.4 ISV 跨多 CAD 维护一份 UI

工业现实：一个 ISV（PLM 厂商、CAM 后端、仿真前端）需要支持 NX + SolidWorks + CATIA + Inventor 等 4–5 个主流 CAD。每个 CAD 写一套原生 UI 工程上不可承受——所以 ISV 几乎都选 **CEF / WebView2 + 共享 HTML / CSS / JS bundle**，把 UI 代码统一成一份 web 应用，平台桥负责把 CAD API 暴露给 JS。

SU 的 `UI::HtmlDialog` + JavaScript callback 就是这种桥的样板 [回链：3.7 §三 现代 UI::HtmlDialog（SU 2017+）]。

---

## 二、五类 UI 范式（样本平台映射）

按 ISV / 平台开发者**实际写代码**的视角，样本平台的 UI 框架可分为 5 类（不互斥，多数平台同时支持多类）：

### 2.1 原生桌面 toolkit
- **MFC**：AutoCAD ObjectARX 原生对话框 [回链：3.1 §三]、SolidWorks 早期 ActiveX
- **Qt**：FreeCAD 基础 toolkit + Qt Designer `.ui` 文件 [回链：3.8 §三]、CATIA 部分内部组件
- **专有 toolkit**：CATIA NLS、NX Block UI 底层（Qt 派生但封装严格）

特点：性能最好、与 CAD 集成最深、维护成本最高。复杂 dialog 用此层，简单 dialog 多走更高层。

### 2.2 .NET 托管 toolkit

- **WinForms**：AutoCAD .NET ObjectARX wrapper、SolidWorks Add-in、MicroStation DgnPlatformNET [回链：3.5 §四]
- **WPF**：AutoCAD 2010+ palette、MicroStation CONNECT 现代 UI
- **专有 .NET 控件**：SolidWorks <Term def="PropertyManager Page：SolidWorks 特有的“侧栏对话框”控件，开发者实现 IPropertyManagerPage2 接口；UI 自动嵌成左侧 Feature Manager 子面板。是参数化建模 commit/rollback 范式在 .NET 的实现。">PMP</Term>（PropertyManager Page）[回链：3.6 §四 IModelDocExtension 与 PMP]

特点：开发速度快于原生 C++，生态丰富（NuGet 控件库），但对 Win32 出身的老 CAD 需要 .NET wrapper 桥。

### 2.3 嵌入 Web（CEF / WebView2）

- **CEF**：SketchUp `UI::HtmlDialog` (SU 2017+) [回链：3.7 §三]、AutoCAD Web Browser API、SolidWorks 部分对话框
- **WebView2**：（样本平台中尚未大规模出现，是 CEF 的"轻量替代"）

特点：UI 代码 = 一份 HTML / CSS / JS bundle，跨多 CAD 可复用；需要平台桥把 CAD API 暴露给 JS。是跨平台 ISV 的事实标准。

### 2.4 声明式 dialog 框架

- **NX Block UI Styler**：拖放定义 blocks，编译器生成 C++ / C# / Python / Java stub [回链：3.3 §二]——样本中**唯一**"开发者不写 UI 代码"的设计
- **FreeCAD task panel**：Qt + Python 写的左侧贴边面板，参数化建模 commit/rollback 按钮原生集成 [回链：3.8 §三]
- **CATIA Modeler dialog**：CAA Object Modeler 提供的对话框组件，以 NLS 渲染 [回链：3.2 §三]

特点：减少样板代码、强制一致的 UI 风格，但 customization 自由度受限；适合"一致性 > 灵活性"的取舍。

### 2.5 纯 Web

- **Onshape**：React 前端 + WebGL viewport [回链：3.4 §三]，所有操作通过 REST 调用，FeatureScript 驱动 feature dialogs
- **iTwin Viewer**：Bentley 的 React 嵌入式组件 [回链：3.5 §五]，把 iModel 的 3D 视图 + 属性面板封成可嵌的 npm 包

特点：完全脱离桌面平台，UI 可在任何浏览器跑；代价是浏览器作为 UI 边界 + 服务端必须实时响应（Onshape REST 调用每分钟限流、需良好网络）。

---

## 三、横向矩阵

<div class="table-wide">

| 平台 | 原生 toolkit | .NET 通道 | Web 嵌入策略 | 声明式 dialog | ISV 主推路径 |
|---|---|---|---|---|---|
| **AutoCAD ObjectARX** | MFC（C++ ARX） | WinForms / WPF | Web Browser API（CEF 内嵌） | 无 | .NET + WPF |
| **CATIA CAA RADE** | NLS（专有）+ Qt 内部 | Java / Swing（ENOVIA 端） | 无（CAA dialogs 走 NLS） | CAA Modeler dialog | NLS + Modeler dialog |
| **Siemens NX** | Qt 派生（封装严格） | NX Open .NET | Web Browser API（部分） | **Block UI Styler** ⭐ | Block UI Styler |
| **Onshape** | 无桌面 | 无 | **完全 Web** | FeatureScript dialogs | React + REST |
| **MicroStation + iTwin** | MDL / Win32（旧） | DgnPlatformNET（WinForms / WPF） | iTwin Viewer（React） | 无 | iTwin.js Frontend |
| **SolidWorks** | COM（旧）+ ActiveX | WinForms / WPF + **PMP** ⭐ | 部分对话框嵌 CEF | PMP（侧栏属性页） | PMP |
| **SketchUp** | 无（Ruby 不写原生） | 无（无 .NET） | **UI::HtmlDialog（CEF）** ⭐ | Tool 类 + 自动 toolbar | HtmlDialog + Ruby Tool |
| **FreeCAD** | **Qt 5 / 6** ⭐ + Qt Designer | 无（无 .NET） | 部分（QtWebEngine） | **task panel** ⭐ | Qt + Python + task panel |

</div>

⭐ 标注 = 该平台在该范式上有显著差异化设计。

---

## 四、跨平台 ISV 的 UI 取舍

### 4.1 单 CAD 单 UI（精装修）

适用：客户基础 80%+ 集中在一个 CAD（如某 NX 重客户）。
- 直接用平台原生路径（NX Block UI / SW PMP / CATIA NLS）
- **优势**：与 CAD 视觉一致、性能最好、招聘"懂 CAD 的开发"比"懂 Web 的开发"还简单
- **劣势**：换 CAD 等于重写

### 4.2 跨 CAD 通用 UI（CEF + 共享 bundle）

适用：ISV 需要支持 3+ CAD（多见于 PLM / CAM / 仿真后端）。
- 一份 HTML / CSS / JS bundle，每个 CAD 嵌一个 CEF 实例
- 平台桥负责暴露 CAD API：JS → postMessage → 平台 native code → CAD API
- 维护成本：1 份 UI 代码 + N 份桥代码（vs N 份原生 UI 代码）

成本估算（基于行业经验，[证据等级 C]）：
- 4 CAD 平台 × 原生 UI ≈ 12 人月
- 1 CEF UI bundle + 4 桥 ≈ 5 人月（节省 ~60%）
- 后续维护：原生方案随 CAD 大版本升级；CEF 方案只动桥层

### 4.3 服务端渲染 + 桌面 wrap（Onshape + 桌面 CAD）

适用：ISV 已有 Onshape / iTwin 资产，希望复用到桌面 CAD。
- 服务端用 Onshape REST 或自建 REST API
- 桌面 CAD 端用 "browser dialog" 嵌网页
- 数据来回靠 REST 调用（高延迟、需要在线）

罕见但存在：iTwin Viewer 嵌入 MicroStation 桌面 = "把云原生 UI 嵌回原生 CAD"。

---

## 五、趋势观察

### 5.1 桌面 CAD 在 2017–2020 集体迁移 CEF

样本中可观测的时间点：
- **SketchUp 2017**（2016-Q4）：`UI::HtmlDialog` 替代旧 WebDialog [回链：3.7 §三]
- **AutoCAD 2018–2020**：Web Browser API 升级，多个对话框迁移到 HTML
- **SolidWorks 多个版本**：部分对话框（如 Sustainability 报告）嵌 CEF

驱动力：(1) 原生 UI 开发成本高；(2) ISV 要求"一份 UI 多平台跑"；(3) Web 技术栈成熟到可承担生产负载。

### 5.2 WebView2 替代 CEF 的工程考量

WebView2（Microsoft 2020 GA）vs CEF：

| 维度 | WebView2 | CEF |
|---|---|---|
| binary 体积 | ~10MB | ~150MB+ |
| Chromium 来源 | 系统 Edge runtime | 自带 |
| 跨 OS | 仅 Windows 10/11 | macOS / Linux 也有 |
| 版本控制 | 跟系统 Edge 走 | CAD 自主 |
| 安全更新 | Microsoft 推送 | CAD 自己 ship |

样本中尚未观察到大规模迁移。基于行业趋势 [证据等级 C]，2027–2030 间会有桌面 CAD 厂商把"无关键自定义需求的对话框"切到 WebView2。

### 5.3 声明式 dialog 的"自动多语言绑定"价值

NX Block UI Styler 的设计逻辑：
- 用户 GUI 工具拖放定义 dialog
- 工具产出 XML 描述
- 编译器读 XML，生成 C++ / C# / Python / Java 4 套对等的 dialog 代码

这种"declare once, generate everywhere"模式 [回链：3.3 §二] 的价值：
- 4 语言的 dialog 完全一致（不会 C# 版本多个按钮、Python 版本少一个）
- UI 修改成本 = 改 XML，不是改 4 套源代码
- ISV 客户偏好不同语言时（C++ 老团队 vs Python 新团队），开发成本完全相同

为什么没普及到其他平台：(1) 需要平台先有"四语言对等"的 SDK 哲学；(2) 工具开发成本高（Block UI Styler 是 Siemens 多年投入的产物）。

### 5.4 Web-first CAD 的 UI 风险

Onshape / iTwin Viewer 这类"完全 Web UI"的 CAD：
- **浏览器版本碎片**：Safari 14 不支持的 WebGL2 特性，Onshape 必须 polyfill
- **CSP 与扩展冲突**：客户企业的浏览器策略（如禁用 WebGL、禁第三方 cookie）会让 CAD 无法工作
- **离线无能力**：Onshape 完全在线，CATIA 桌面可离线工作

这是 Onshape vs 桌面 CAD 的根本张力 [回链：3.4 §一]。Web-first 是 SaaS 商业模式的必要选择，但牺牲了离线 + 性能极致。

---

## 六、给决策者的清单

ISV 的 UI 框架选型决策，按重要性顺序：

1. **客户群是否分布在多个 CAD？**
   - 是 → CEF + Web bundle 路线几乎必选
   - 否 → 用平台原生 / 推荐路径

2. **客户企业的桌面环境**
   - Windows 11 + 现代 Edge → WebView2 可选
   - 老 Windows / 跨 OS（含 macOS / Linux）→ 走 CEF 兜底

3. **UI 团队技术栈**
   - Web / React 团队 → CEF + React + REST
   - 老 C++ / .NET 团队 → 平台原生 + .NET wrapper
   - 多语言混合（Python 测试 + C++ 核心）→ NX 类的声明式 dialog 是理想

4. **维护周期与版本节奏**
   - 长期 (5+ 年) ISV 应用 → 避免被锁定到平台特定 dialog 框架
   - 短期 (1–2 年) 项目 → 用平台推荐路径，不投入自研抽象层

5. **预算约束**（基于 [证据等级 C] 估算）
   - 4 平台 × 原生 = 12 人月
   - 4 平台 × CEF Web = 5 人月（节省 ~60%）

6. **客户 IT 政策**
   - 客户禁用 CEF / 嵌入式浏览器 → 必须走纯原生路径
   - 客户企业 firewall 阻止 onshape.com → 不能选 Web-first CAD

---

## 七、给新平台的建议

新 CAD 平台（如某国产 CAD 创业者）在 UI 框架决策时：

1. **UI 框架是 SDK 战略的一部分，不是事后追加**
   - Onshape 选纯 Web → 插件作者画像偏年轻 web dev → 插件市场快速起量
   - NX Block UI 让 UI 编辑近乎为零成本 → 大型 ISV 客户敢投入做深度集成
   - FreeCAD Qt + Python → 开源贡献者门槛低（Python 写 task panel）

2. **如果目标是 ISV 友好，优先解决"一份 UI 多语言"问题**
   - 学 NX Block UI Styler（如有人力做工具）
   - 至少做"DSL → 多语言代码生成"的小工具

3. **不要发明专有 toolkit**（除非你是 Dassault 量级）
   - 开源 Qt 是 FreeCAD / 多个 BIM CAD 选择，社区贡献大
   - CEF / WebView2 是事实标准，跟着 Microsoft 走风险低
   - 自研 toolkit（如 CATIA NLS）需要数十年与百人 UI 团队投入，绝大多数 CAD 公司做不到

> **[评论]** 国产 CAD 厂商若想在 ISV 生态上追赶国际厂商，UI 框架决策可能比 SDK API 决策更重要——SDK 决定能力上限，UI 框架决定开发者群体规模。

---

## 八、结语

本文从样本 8 个 CAD 平台中提取的 UI 框架横向观察可总结为三句话：

1. **CAD UI 不是普通桌面 UI**——参数化 commit/rollback、3D viewport 共存、跨 CAD ISV 这三个约束让 CAD UI 成为独立子领域。
2. **CEF 是当前事实标准的"跨平台 UI"答案**，但 NX Block UI 这种"声明式 + 自动多语言"是更优雅的解法（成本是工具研发投入）。
3. **新平台的 UI 选择决定 ISV 生态形态**——Onshape Web、NX 多语言、FreeCAD Qt + Python 各自吸引不同的开发者群体，不存在"通用最佳答案"。

---

## 参考来源

本文档为本系列 8 个样本平台 API 深度剖析的横向"UI 框架"提取。主要事实回链已在正文中标注 `[回链：3.x §y]`，由 `rewrite_links.py` 自动展开为站内可点击链接。

### [百科]
- [百科 1] Wikipedia, "Chromium Embedded Framework", https://en.wikipedia.org/wiki/Chromium_Embedded_Framework
- [百科 2] Wikipedia, "Qt (software)", https://en.wikipedia.org/wiki/Qt_(software)

### [官方]
- [官方 1] Microsoft Learn, "Microsoft Edge WebView2", https://learn.microsoft.com/en-us/microsoft-edge/webview2/

### [第三方]
- [第三方 1] 本系列 8 篇厂商深度剖析（[3.1 AutoCAD](/platforms/autocad) · [3.2 CATIA](/platforms/catia) · [3.3 NX](/platforms/nx) · [3.4 Onshape](/platforms/onshape) · [3.5 MicroStation](/platforms/microstation) · [3.6 SolidWorks](/platforms/solidworks) · [3.7 SketchUp](/platforms/sketchup) · [3.8 FreeCAD](/platforms/freecad)）— 本文 UI 章节具体事实的一手来源

**证据等级说明**：
- A：来自官方文档 / 平台仓库源代码
- B：第三方权威报告 / 公开行业资料
- C：作者基于行业经验推断，需进一步验证

本文档大部分论断为 B 级（基于本系列 8 个样本平台的归纳）；带 `[证据等级 C]` 标记的论断需结合实际 CAD 团队访谈或市场调研进一步验证。

---

> **本文档版本**：2026-05-08 首版
> **关联文档**：[文档 1 通用 CAD 平台 API 设计哲学](/theory)（理论顶层） · [文档 2 厂商 API 横向对比](/comparison)（API 维度） · [厂商深度系列 3.1–3.8](/) （单平台 UI 章节深度）

---
title: 桌面应用入门
source_id: claude-code/desktop-quickstart
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/desktop-quickstart
owner: Anthropic
content_sha256: 4b152dd1f8a5b6a843e6d56b9776a1572713a01ea7ee7ac3f5b4bbeb5d7ae843
translation_of: claude-code/desktop-quickstart
translation_model: gpt-5.6
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/desktop-quickstart)

Content owner: Anthropic

> ## 文档索引
> 完整的文档索引位于：https://code.claude.com/docs/llms.txt
> 在进一步探索之前，可使用此文件发现所有可用页面。

# 桌面应用入门

> 在桌面设备上安装 Claude Code，并开始第一个编码会话

桌面应用提供带图形界面的 Claude Code，专为并排运行多个会话而设计：用于管理并行工作的侧边栏、包含集成终端和文件编辑器的拖放式布局、可视化差异审核、实时应用预览、带自动合并功能的 GitHub PR 监控，以及计划任务。无需使用终端。

<CardGroup cols={3}>
  <Card title="下载 macOS 版" icon="apple" href="https://claude.ai/api/desktop/darwin/universal/dmg/latest/redirect?utm_source=claude_code&utm_medium=docs">
    适用于 Intel 和 Apple Silicon 的通用构建
  </Card>

  <Card title="下载 Windows 版" icon="windows" href="https://claude.ai/api/desktop/win32/x64/setup/latest/redirect?utm_source=claude_code&utm_medium=docs">
    适用于 x64 处理器
  </Card>

  <Card title="获取 Linux 版 Claude（beta）" icon="linux" href="/docs/en/desktop-linux">
    适用于 Ubuntu 和 Debian 的 apt 或 .deb
  </Card>
</CardGroup>

对于 Windows ARM64，请下载 [ARM64 安装程序](https://claude.ai/api/desktop/win32/arm64/setup/latest/redirect?utm_source=claude_code\&utm_medium=docs)。在 Linux 上，请使用 apt 安装；请参阅 [Linux 上的 Claude Desktop](/docs/en/desktop-linux)。

<Note>
  Claude Code 需要 [Pro、Max、Team 或 Enterprise 订阅](https://claude.com/pricing?utm_source=claude_code\&utm_medium=docs\&utm_content=desktop_quickstart_pricing)。
</Note>

本页将引导你安装应用并开始第一个会话。如果你已经完成设置，请参阅 [使用 Claude Code Desktop](/docs/en/desktop) 获取完整参考。

桌面应用有三个标签页：

* **Chat**：不访问文件的常规对话，类似于 claude.ai。
* **Cowork**：在沙盒虚拟机中处理任务的自主后台智能体，拥有自己的环境，并会在你从事其他工作时独立运行。设备端 Cowork 会话在你的计算机上运行 VM；远程 Cowork 会话则改为在 Anthropic 管理的 VM 上运行。
* **Code**：可直接访问本地文件的交互式编码助手。你可以实时审核和批准每项更改。

Chat 和 Cowork 的内容见 [Claude 帮助中心](https://support.claude.com/)；桌面应用的安装和部署见 [Claude Desktop 支持文章](https://support.claude.com/en/collections/16163169-claude-desktop)。本页重点介绍 **Code** 标签页。

## 安装

<Steps>
  <Step title="安装并登录">
    在 macOS 和 Windows 上，请从上方链接下载安装程序并运行。在 Linux 上，请按照 [Linux 上的 Claude Desktop](/docs/en/desktop-linux)中的安装步骤操作。然后从 macOS 的 Applications 文件夹、Windows 的开始菜单或 Linux 的应用启动器启动 Claude，并使用 Anthropic 账户登录。
  </Step>

  <Step title="打开 Code 标签页">
    单击顶部中央的 **Code** 标签页。如果单击 Code 后提示升级，你需要先[订阅付费方案](https://claude.com/pricing?utm_source=claude_code\&utm_medium=docs\&utm_content=desktop_quickstart_upgrade)。如果系统提示在线登录，请完成登录并重启应用。如果看到 403 错误，请参阅[身份验证故障排除](/docs/en/desktop#403-or-authentication-errors-in-the-code-tab)。
  </Step>
</Steps>

桌面应用已包含 Claude Code。无需单独安装 Node.js 或 CLI。若要从终端使用 `claude`，请另行安装 CLI。请参阅 [CLI 入门](/docs/en/quickstart)。

## 开始第一个会话

打开 Code 标签页后，选择一个项目，并交给 Claude 一项任务。

<Steps>
  <Step title="选择环境和文件夹">
    选择 **Local**，使用你的文件直接在本机运行 Claude。单击 **Select folder**，然后选择项目目录。

    <Tip>
      请从你熟悉的小型项目开始。这是了解 Claude Code 能力的最快方式。在 Windows 上，本地会话需要安装 [Git](https://git-scm.com/downloads/win) 才能运行。大多数 Mac 默认已包含 Git。
    </Tip>

    你还可以选择：

    * **Cloud**：在 Anthropic 的云基础设施上运行会话，即使关闭应用也会继续。云端会话使用与 [Claude Code 网页版](/docs/en/claude-code-on-the-web)相同的基础设施。
    * **SSH**：通过 SSH 连接到远程计算机，例如你自己的服务器、云端 VM 或开发容器。首次连接时，Desktop 会自动在远程计算机上安装 Claude Code。
    * **WSL**（Windows）：在 [WSL 2 发行版](/docs/en/desktop-wsl)中运行会话；Claude Code、工具和 git 在 Linux 端使用原生路径执行。
  </Step>

  <Step title="选择模型">
    从发送按钮旁的下拉菜单中选择模型。有关可用模型的比较，请参阅[模型](/docs/en/model-config#available-models)。之后可以从同一下拉菜单更改模型。
  </Step>

  <Step title="告诉 Claude 要做什么">
    输入你希望 Claude 执行的任务：

    * `Find a TODO comment and fix it`
    * `Add tests for the main function`
    * `Create a CLAUDE.md with instructions for this codebase`

    [会话](/docs/en/desktop#work-in-parallel-with-sessions)是你与 Claude 围绕代码进行的对话。每个会话都会跟踪自己的上下文和更改，因此你可以处理多项任务，而不会相互干扰。
  </Step>

  <Step title="审核并接受更改">
    默认情况下，Code 标签页以 [Manual 模式](/docs/en/desktop#choose-a-permission-mode)启动；在此模式下，Claude 会提出更改，并在应用前等待你批准。你将看到：

    1. [差异视图](/docs/en/desktop#review-changes-with-diff-view)，准确显示每个文件将发生的更改
    2. 用于批准或拒绝每项更改的 Accept/Reject 按钮
    3. Claude 处理请求时的实时更新

    如果你拒绝某项更改，Claude 会询问你希望以何种不同方式继续。在你接受之前，文件不会被修改。
  </Step>
</Steps>

## 接下来做什么？

你已经完成了第一次编辑。有关 Desktop 全部功能的完整参考，请参阅 [使用 Claude Code Desktop](/docs/en/desktop)。下面是一些接下来可以尝试的操作。

**中断并引导。** 你可以随时让 Claude 改变方向。单击停止按钮可立即中断，也可以输入更正内容并按 **Enter** 发送，而不停止正在运行的操作。无论采用哪种方式，都无需等待它完成或从头开始。

**为 Claude 提供更多上下文。** 在提示框中输入 `@filename` 可将特定文件加入对话；使用附件按钮附加图像和 PDF，也可以将文件直接拖放到提示中。Claude 拥有的上下文越多，结果越好。请参阅[添加文件和上下文](/docs/en/desktop#add-files-and-context-to-prompts)。

**使用技能处理可重复任务。** 输入 `/`，或单击 **+** → **Slash commands**，浏览[内置命令](/docs/en/commands)、[自定义技能](/docs/en/skills)和插件技能。技能是可复用的提示，可在需要时调用，例如代码审核检查清单或部署步骤。

**提交前审核更改。** Claude 编辑文件后，会出现 `+12 -1` 指示器。单击它打开[差异视图](/docs/en/desktop#review-changes-with-diff-view)，逐个文件审核修改，并对特定行发表评论。Claude 会读取你的评论并修订。单击 **Review code**，让 Claude 自行评估差异并留下内联建议。

**调整你拥有的控制程度。** [权限模式](/docs/en/desktop#choose-a-permission-mode)决定 Claude 无需请求批准即可执行多少操作：

* **Manual**：默认模式。Claude 会在编辑文件或运行命令前询问。
* **Accept edits**：Claude 自动接受文件编辑，以加快迭代。
* **Plan**：Claude 提出方法但不编辑任何文件，适合在大型重构前使用。

**添加插件以获得更多能力。** 单击提示框旁的 **+** 按钮并选择 **Plugins**，浏览和安装可添加技能、智能体、MCP 服务器等内容的[插件](/docs/en/desktop#install-plugins)。

**安排你的工作区。** 将聊天、差异、终端、文件和浏览器窗格拖放为任意所需布局。使用 **Ctrl+\`** 打开终端，在会话旁运行命令；也可单击文件路径，在文件窗格中打开它。请参阅[安排工作区](/docs/en/desktop#arrange-your-workspace)。

**预览应用。** 在桌面应用中运行开发服务器时，你的应用会在 Browser 窗格中打开；该窗格也可以[打开外部网站](/docs/en/desktop#browse-external-sites)。Claude 可以查看正在运行的应用、测试端点、检查日志，并根据所见内容迭代。请参阅[预览应用](/docs/en/desktop#preview-your-app)。

**跟踪拉取请求。** 打开 PR 后，Claude Code 会监控 CI 检查结果，能够自动修复失败，并在所有检查通过后合并 PR。请参阅[监控拉取请求状态](/docs/en/desktop#monitor-pull-request-status)。

**让 Claude 按计划运行。** 设置[计划任务](/docs/en/desktop-scheduled-tasks)，让 Claude 按重复计划自动运行：每天早晨进行代码审核、每周执行依赖项审计，或从已连接工具提取信息生成简报。

**准备好后扩大规模。** 从侧边栏打开[并行会话](/docs/en/desktop#work-in-parallel-with-sessions)，同时处理多项任务，每项任务都位于自己的 Git worktree 中；打开[任务窗格](/docs/en/desktop#watch-background-tasks)，观察会话正在运行的子智能体和后台命令。打开[侧边聊天](/docs/en/desktop#ask-a-side-question-without-derailing-the-session)，在不使主任务偏离方向的情况下提问。将[长时间运行的工作发送到云端](/docs/en/desktop#run-long-running-tasks-remotely)，使其在关闭应用后仍能继续；如果任务耗时超过预期，也可以[在网页或 IDE 中继续会话](/docs/en/desktop#continue-in-another-surface)。[连接外部工具](/docs/en/desktop#extend-claude-code)，例如 GitHub、Slack 和 Linear，将工作流汇聚到一起。

## 从 CLI 转来？

Desktop 运行与 CLI 相同的引擎，并提供图形界面。你可以在同一项目上同时运行二者，它们会共享配置（CLAUDE.md 文件、MCP 服务器、hooks、技能和设置）。有关功能、对应标志以及 Desktop 中不可用内容的完整比较，请参阅 [CLI 比较](/docs/en/desktop#coming-from-the-cli)。

## 后续内容

* [使用 Claude Code Desktop](/docs/en/desktop)：权限模式、并行会话、差异视图、连接器和企业配置
* [故障排除](/docs/en/desktop#troubleshooting)：常见错误和设置问题的解决方案
* [最佳实践](/docs/en/best-practices)：编写有效提示并充分发挥 Claude Code 能力的技巧
* [常见工作流](/docs/en/common-workflows)：调试、重构、测试等教程

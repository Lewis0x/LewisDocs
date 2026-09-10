---
title: 平台和集成
source_id: claude-code/platforms
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/platforms
owner: Anthropic
content_sha256: be30c00ee12f41c09ea9f31d21f11027be15cd46f8b6c27a7e3c1899cb0ebd35
translation_of: claude-code/platforms
translation_model: gpt-5.6
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/platforms)

Content owner: Anthropic

> ## 文档索引
> 完整的文档索引位于：https://code.claude.com/docs/llms.txt
> 在进一步探索之前，可使用此文件发现所有可用页面。

# 平台和集成

> 选择在哪里运行 Claude Code，以及将其连接到哪些工具。比较 CLI、Desktop、VS Code、JetBrains、网页和移动端，以及 Chrome、Slack 和 CI/CD 等集成。

Claude Code 在所有位置运行相同的底层引擎，但每个界面都针对不同的工作方式进行了优化。本页可帮助你为工作流选择合适的平台，并连接已在使用的工具。

## 在哪里运行 Claude Code

根据你偏好的工作方式和项目所在位置选择平台。

| 平台                          | 最适合                                                                                           | 提供的功能                                                                                                                                                                              |
| :-------------------------------- | :------------------------------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [CLI](/docs/en/quickstart)             | 终端工作流、脚本、远程服务器                                                      | 完整功能集、[Agent SDK](/docs/en/headless)、macOS 上的[计算机使用](/docs/en/computer-use)（Pro 和 Max）、第三方提供商                                                               |
| [Desktop](/docs/en/desktop)            | 可视化审核、并行会话、托管设置                                                    | 差异查看器、应用预览、Pro 和 Max 上的[计算机使用](/docs/en/desktop#let-claude-use-your-computer)和 [Dispatch](/docs/en/desktop#sessions-from-dispatch)                                      |
| [VS Code](/docs/en/vs-code)            | 无需切换到终端，直接在 VS Code 内工作                                             | 内联差异、集成终端、文件上下文                                                                                                                                           |
| [JetBrains](/docs/en/jetbrains)        | 在 IntelliJ、PyCharm、WebStorm 或其他 JetBrains IDE 中工作                                | 差异查看器、选择内容共享、终端会话                                                                                                                                          |
| [网页](/docs/en/claude-code-on-the-web) | 不需要太多引导的长时间任务，或应在你离线时继续的工作 | Anthropic 托管的云端；断开连接后仍会继续                                                                                                                                   |
| [移动端](/docs/en/mobile)              | 离开计算机时启动和监控任务                                        | 通过 iOS 和 Android 版 Claude 应用使用云端会话，通过[远程控制](/docs/en/remote-control)使用本地会话，并在 Pro 和 Max 方案中通过 [Dispatch](/docs/en/desktop#sessions-from-dispatch)连接 Desktop |

对于以终端为中心的工作，CLI 是功能最完整的界面：脚本和 Agent SDK 仅在 CLI 中可用。第三方提供商也可在 [VS Code](/docs/en/vs-code#use-third-party-providers) 中使用。企业 [Desktop](/docs/en/desktop) 部署支持 Google Cloud 的 Agent Platform，Desktop 还支持[网关提供商](/docs/en/llm-gateway-connect#desktop-app)；对于 Amazon Bedrock 或 Microsoft Foundry，请使用 CLI 或 VS Code，也可使用 [3P 上的 Claude Desktop](https://claude.com/docs/third-party/claude-desktop/overview)，它会在这些提供商上运行 Code 标签页。Desktop 和 IDE 扩展以部分仅限 CLI 的功能换取可视化审核和更紧密的编辑器集成。网页版在 Anthropic 云端运行，因此断开连接后任务仍会继续。移动端是一个精简客户端，可连接到这些云端会话，或通过远程控制连接本地会话，还可以通过 Dispatch 向 Desktop 发送任务。

你可以在同一项目上混合使用不同界面。本地界面之间共享配置、项目记忆和 MCP 服务器。

## 连接你的工具

集成让 Claude 可以使用代码库之外的服务。

| 集成                          | 功能                                       | 用途                                                       |
| :----------------------------------- | :------------------------------------------------- | :--------------------------------------------------------------- |
| [Chrome](/docs/en/chrome)                 | 使用你的已登录会话控制浏览器 | 测试 Web 应用、填写表单、自动操作没有 API 的网站 |
| [GitHub Actions](/docs/en/github-actions) | 在 CI 流水线中运行 Claude                    | 自动审核 PR、问题分类、计划维护        |
| [GitLab CI/CD](/docs/en/gitlab-ci-cd)     | 为 GitLab 提供与 GitHub Actions 相同的功能                  | GitLab 上由 CI 驱动的自动化                                   |
| [Code Review](/docs/en/code-review)       | 自动审核每个 PR                     | 在人工审核前发现缺陷                                |
| [Slack](/docs/en/slack)                   | 回应频道中对 `@Claude` 的提及    | 从团队聊天将缺陷报告转化为拉取请求            |

对于此处未列出的集成，可通过 [MCP 服务器](/docs/en/mcp)和[连接器](/docs/en/desktop#connect-external-tools)连接几乎任何服务：Linear、Notion、Google Drive 或你自己的内部 API。

## 离开终端时继续工作

当你不在终端前时，Claude Code 提供了多种工作方式。它们在工作触发方式、Claude 运行位置和所需设置量方面有所不同。

|                                                | 触发方式                                                                                        | Claude 运行位置                                                                               | 设置                                                                                                                                | 最适合                                                      |
| :--------------------------------------------- | :--------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------ |
| [Dispatch](/docs/en/desktop#sessions-from-dispatch) | 从 Claude 移动应用发送任务消息                                                      | 你的计算机（Desktop）                                                                       | [将移动应用与 Desktop 配对](https://support.claude.com/en/articles/13947068)                                                  | 外出时委派工作，设置最少              |
| [远程控制](/docs/en/remote-control)           | 从 [claude.ai/code](https://claude.ai/code) 或 Claude 移动应用操控正在运行的会话 | 你的计算机（CLI 或 VS Code）                                                                | 运行 `claude remote-control`                                                                                                          | 从其他设备引导进行中的工作                 |
| [Channels](/docs/en/channels)                       | 从 Telegram 或 Discord 等聊天应用或你自己的服务器推送事件                       | 你的计算机（CLI）                                                                           | [安装 channel 插件](/docs/en/channels#quickstart)或[自行构建](/docs/en/channels-reference)                                      | 响应 CI 失败或聊天消息等外部事件 |
| [Slack](/docs/en/slack)                             | 在团队频道中提及 `@Claude`                                                            | Anthropic 云端                                                                              | [安装 Slack 应用](/docs/en/slack#setting-up-claude-code-in-slack)，并启用 [Claude Code 网页版](/docs/en/claude-code-on-the-web) | 从团队聊天创建 PR 和执行审核                                |
| [计划任务](/docs/en/scheduled-tasks)         | 设置计划                                                                                 | [CLI](/docs/en/scheduled-tasks)、[Desktop](/docs/en/desktop-scheduled-tasks)或[云端](/docs/en/routines) | 选择频率                                                                                                                     | 每日审核等重复自动化                       |

如果不确定从哪里开始，请[安装 CLI](/docs/en/quickstart)，然后在项目目录中运行。如果你不想使用终端，[Desktop](/docs/en/desktop-quickstart) 可通过图形界面提供相同的引擎。

## 相关资源

### 平台

* [CLI 快速入门](/docs/en/quickstart)：在终端中安装并运行第一条命令
* [Desktop](/docs/en/desktop)：可视化差异审核、并行会话、计算机使用和 Dispatch
* [VS Code](/docs/en/vs-code)：编辑器内的 Claude Code 扩展
* [JetBrains](/docs/en/jetbrains)：适用于 IntelliJ、PyCharm 和其他 JetBrains IDE 的扩展
* [Claude Code 网页版](/docs/en/claude-code-on-the-web)：断开连接后仍会继续运行的云端会话
* [移动端](/docs/en/mobile)：用于在离开计算机时启动和监控任务的 [iOS](https://apps.apple.com/us/app/claude-by-anthropic/id6473753684) 和 [Android](https://play.google.com/store/apps/details?id=com.anthropic.claude) 版 Claude 应用

### 集成

* [Chrome](/docs/en/chrome)：使用你的已登录会话自动执行浏览器任务
* [计算机使用](/docs/en/computer-use)：让 Claude 在 macOS 上打开应用并控制屏幕
* [GitHub Actions](/docs/en/github-actions)：在 CI 流水线中运行 Claude
* [GitLab CI/CD](/docs/en/gitlab-ci-cd)：在 GitLab 上实现同样的功能
* [Code Review](/docs/en/code-review)：自动审核每个拉取请求
* [Slack](/docs/en/slack)：从团队聊天发送任务，取回 PR

### 远程访问

* [Dispatch](/docs/en/desktop#sessions-from-dispatch)：通过手机发送任务消息，并可由此启动 Desktop 会话
* [远程控制](/docs/en/remote-control)：从手机或浏览器操控正在运行的会话
* [Channels](/docs/en/channels)：将聊天应用或你自己的服务器发出的事件推送到会话中
* [计划任务](/docs/en/scheduled-tasks)：按重复计划运行提示

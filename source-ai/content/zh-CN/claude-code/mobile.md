---
title: 在移动设备上使用 Claude Code
source_id: claude-code/mobile
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/mobile
owner: Anthropic
content_sha256: 356cb30546e3cd38167e4a69670c131c2ac9fc301a80751607b24f68189eafb5
translation_of: claude-code/mobile
translation_model: gpt-5.6
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/mobile)

Content owner: Anthropic

> ## 文档索引
> 完整的文档索引位于：https://code.claude.com/docs/llms.txt
> 在进一步探索之前，可使用此文件发现所有可用页面。

# 在移动设备上使用 Claude Code

> 通过 iOS 和 Android 版 Claude 应用，从手机启动、监控和引导 Claude Code 任务。

[iOS](https://apps.apple.com/us/app/claude-by-anthropic/id6473753684) 和 [Android](https://play.google.com/store/apps/details?id=com.anthropic.claude) 版 Claude 应用是 Claude Code 会话的客户端，并不是运行代码的地方。你可以通过手机访问在 Anthropic 托管基础设施上运行的[云端会话](#start-and-monitor-cloud-sessions)、借助[远程控制](#continue-a-local-session-with-remote-control)访问在自己计算机上运行的会话，或通过 [Dispatch](/docs/en/desktop#sessions-from-dispatch) 访问桌面应用。

<Note>
  Claude Code 没有单独的移动应用：云端会话和远程控制都位于 Claude 应用的 **Code** 标签页中，而 Dispatch 则是你在应用中通过消息交付的任务。
</Note>

## 获取应用

<Steps>
  <Step title="下载 Claude 应用">
    安装 [iOS](https://apps.apple.com/us/app/claude-by-anthropic/id6473753684) 或 [Android](https://play.google.com/store/apps/details?id=com.anthropic.claude) 版 Claude 应用。在 iPad 上，请安装同一款 iOS 应用。

    <Tip>
      在 Claude Code 会话中运行 `/mobile`，即可显示可供扫描的下载二维码。`/ios` 和 `/android` 的作用相同。
    </Tip>
  </Step>

  <Step title="登录">
    使用你在 Claude Code 中所用的同一 claude.ai 账户和组织登录。云端会话和远程控制需要 claude.ai 账户，因此无法通过 Anthropic Console API 密钥或 Amazon Bedrock 等第三方提供商访问。
  </Step>

  <Step title="打开 Code 标签页">
    在应用导航中轻触 **Code** 以访问会话，或在手机上打开 [claude.ai/code/new](https://claude.ai/code/new)，在应用中启动新的 Code 会话。如果你看不到 Code 标签页，可能是你的订阅方案或组织不包含这些功能；请参阅[按订阅方案划分的可用性](/docs/en/feature-availability#availability-by-subscription-plan)。
  </Step>
</Steps>

## 通过手机工作

你可以从应用启动云端会话、操控在计算机上运行的 Claude Code 会话，或通过消息向 Dispatch 交付任务。这三种方式使用的是同一款应用，区别在于工作实际发生的位置。

| 功能                                              | 连接对象                                 | 适用场景                                                                                                                                          |
| :--------------------------------------------------- | :-------------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Claude Code 网页版](/docs/en/claude-code-on-the-web) | Anthropic 托管基础设施上的云端会话 | 你的仓库位于 GitHub 上，并且希望任务在放下手机后继续运行。请参阅[网页版快速入门](/docs/en/web-quickstart)进行设置。 |
| [远程控制](/docs/en/remote-control)                 | 在你的计算机上运行的 Claude Code 会话      | 工作需要使用你的本地文件系统、工具或 MCP 服务器。                                                                                         |
| [Dispatch](/docs/en/desktop#sessions-from-dispatch)       | 你计算机上的桌面应用                    | 你希望通过消息交付任务，并让 Dispatch 决定如何运行。需要 Pro 或 Max 方案。                                                        |

如果计算机将处于关机状态，请使用云端会话：它们在 Anthropic 的基础设施上运行，即使笔记本电脑合上也会继续。远程控制和 Dispatch 操控的是你自己的计算机，因此计算机需要保持开机，并让 Claude Code 或桌面应用持续运行。如果计算机在远程控制会话期间进入睡眠，会话会在计算机重新上线后恢复连接。

如需更完整的比较，包括 Channels、Slack 和计划任务，请参阅[离开终端时继续工作](/docs/en/platforms#work-when-you-are-away-from-your-terminal)。

云端会话和远程控制均从 **Code** 标签页运行，下文会详细介绍。对于以应用内消息任务形式使用的 Dispatch，请参阅[来自 Dispatch 的会话](/docs/en/desktop#sessions-from-dispatch)。

### 启动和监控云端会话

Claude Code 网页版在 Anthropic 托管的云基础设施上运行任务，因此即使你放下手机，会话仍会继续。从 Code 标签页选择仓库和分支，描述任务，然后提交。会话可跨设备延续：你在笔记本电脑上启动的任务可以在手机上查看，而从手机启动的任务也会在你回到桌前时等待着你。

在应用中打开会话，可以查看进度、回答 Claude 的问题或引导它转向新的方向。你还可以要求 Claude [监视拉取请求](/docs/en/claude-code-on-the-web#auto-fix-pull-requests)，并在 CI 失败或审核评论出现时进行修复。若要连接 GitHub 并创建第一个环境，请按照[网页版快速入门](/docs/en/web-quickstart)操作；有关云端会话的全部功能，请参阅 [Claude Code 网页版](/docs/en/claude-code-on-the-web)。

### 使用远程控制继续本地会话

远程控制会将 Claude 应用连接到你计算机上运行的 Claude Code 会话，因此代码执行和文件系统访问仍留在本地，而你可以通过手机操控会话。在计算机上使用 `claude remote-control` 启动会话，或在已经打开的会话中运行 `/remote-control`。然后扫描终端可显示的会话二维码；也可以打开 Claude 应用，轻触 **Code**，并从列表中选择该会话。有关每种方式，请参阅[从其他设备连接](/docs/en/remote-control#connect-from-another-device)。

你在 Claude 应用中添加的附件也会传送到本地会话：Claude Code 会将图像或文件下载到你的计算机，并以 `@` 文件引用的形式传递给 Claude。有关要求、调用模式和故障排除，请参阅[远程控制概述](/docs/en/remote-control)。

### 接收推送通知

远程控制处于活动状态时，Claude 可以向你的手机发送推送通知，通常是在长时间运行的任务完成或需要你做出决定时。你也可以在提示中要求发送通知，例如 `notify me when the tests finish`。有关两个 `/config` 开关和通知送达问题的故障排除，请参阅[移动端推送通知](/docs/en/remote-control#mobile-push-notifications)。

当 Dispatch 启动的 Code 会话完成或需要你批准时，它会发送自己的通知；相关说明请参阅[来自 Dispatch 的会话](/docs/en/desktop#sessions-from-dispatch)。

## 限制

移动客户端涵盖了会话所需的大多数功能，但仍有一些限制：

* **仅限本地的命令**：仅在终端界面中运行的命令（例如 `/plugin` 和 `/resume`）无法从应用使用。[远程控制限制](/docs/en/remote-control#limitations)列出了可从移动端使用的命令，以及它们在行为上的差异。
* **权限模式**：云端会话的模式下拉菜单提供 Accept edits、Plan 和 Auto，远程控制会话则提供 Manual、Accept edits 和 Plan。两种情况下都无法从应用选择 Bypass permissions，也无法为远程控制会话选择 Auto。请参阅[切换权限模式](/docs/en/permission-modes#switch-permission-modes)。
* **Dispatch 方案**：Dispatch 需要 Pro 或 Max 方案，不适用于 Team 或 Enterprise。

## 相关资源

* [平台和集成](/docs/en/platforms)：比较运行 Claude Code 的所有界面
* [Claude Code 网页版](/docs/en/claude-code-on-the-web)：了解云端会话的运行方式、网络访问，以及如何在云端与终端之间转移工作
* [远程控制](/docs/en/remote-control)：从任何设备继续本地会话
* [来自 Dispatch 的会话](/docs/en/desktop#sessions-from-dispatch)：了解 Dispatch 任务如何成为桌面应用中的 Code 会话
* [Channels](/docs/en/channels)：通过 Telegram、Discord 或 iMessage 从手机向 Claude 提问，同时工作在你的计算机上运行
* [Slack 中的 Claude Code](/docs/en/slack)：通过提及 `@Claude`，从 Slack 工作区委派编码任务

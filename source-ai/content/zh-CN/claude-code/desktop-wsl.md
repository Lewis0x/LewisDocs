---
title: Claude Code Desktop 在 WSL 中
source_id: claude-code/desktop-wsl
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/desktop-wsl
owner: Anthropic
content_sha256: 71129cad01b0efe4c2bd3fa3e60617895d13189b1c063b830cf9543044dcfad3
translation_of: claude-code/desktop-wsl
translation_source: official
translation_url: https://code.claude.com/docs/zh-CN/desktop-wsl
localization_sha256: 524b79e4f52e9ae88c90483f40a8a158eab6c29495eea43b67c37bab20d4c70b
---
本页采用内容所有者发布的官方简体中文版本，并与本站对应英文版本进行结构校验。

[官方中文来源](https://code.claude.com/docs/zh-CN/desktop-wsl)

内容所有者: Anthropic

> ## Documentation Index
> Fetch the complete documentation index at: https://code.claude.com/docs/llms.txt
> Use this file to discover all available pages before exploring further.

# Claude Code Desktop 在 WSL 中

> 在 Windows 上的 WSL 2 发行版内运行 Code 会话

在 Windows 上，Code 选项卡可以在 WSL 2 发行版内运行会话，而不是在 Windows 本身上运行。会话的 Claude Code 进程、其工具和 git 都在发行版内执行，使用其 Linux 工具链和本机 Linux 路径，与您的项目所针对的环境相同。

当您的存储库位于发行版的文件系统内时，请使用 WSL 会话。从 Windows 处理这些文件会通过网络文件系统进行，这很慢并且会破坏文件监视；在发行版内运行会话可以避免两者。

<h2 id="requirements">
  要求
</h2>

* Windows 10 或 11，带有 [WSL 2](https://learn.microsoft.com/windows/wsl/install)。不支持 WSL 1。
* 至少安装一个发行版（例如 Ubuntu）。
* 在发行版内安装了 `git`。

<h2 id="start-a-wsl-session">
  启动 WSL 会话
</h2>

<Steps>
  <Step title="选择发行版">
    在 Code 选项卡中启动新会话并打开环境选择器。您安装的 WSL 2 发行版会出现在 **WSL** 部分中。选择一个。
  </Step>

  <Step title="选择文件夹">
    会话在发行版的主目录中启动。使用文件夹选择器选择项目文件夹。浏览在发行版内进行，使用 Linux 路径，如 `/home/you/project`。
  </Step>

  <Step title="信任文件夹">
    文件夹中的第一个会话会显示工作区信任对话框。信任按发行版和文件夹授予；在一个发行版中信任文件夹不适用于另一个发行版或 Windows 上的相同路径。
  </Step>
</Steps>

发行版中的第一个会话需要花费更长时间，而 Claude 在其中进行设置。您也可以从普通文件夹选择器打开 `\\wsl.localhost\...` 文件夹，它会在该发行版内重新打开。

您最近使用过的文件夹会按发行版出现在选择器中，因此重新连接到项目只需一次点击。

<h2 id="what-works-in-a-wsl-session">
  WSL 会话中的工作内容
</h2>

并行会话、侧边聊天、可视化差异审查、分支和拉取请求状态以及 worktrees 都可以工作，由发行版内的 git 和工具链支持。"在编辑器中打开"会打开通过 [Remote - WSL](https://code.visualstudio.com/docs/remote/wsl) 连接到发行版的 VS Code。

WSL 会话中还没有提供一些功能：集成终端、连接器和插件、会话分叉、文件浏览器窗格以及在编辑器中键入 `@` 时的文件建议。

<h2 id="managed-devices">
  受管设备
</h2>

在由组织管理的设备上，WSL 会话可能不可用。如果会话启动失败并显示设备受管的消息，这由您的管理员控制。管理员：请参阅部署指南中的[设置如何到达设备](/docs/zh-CN/admin-setup#decide-how-settings-reach-devices)。

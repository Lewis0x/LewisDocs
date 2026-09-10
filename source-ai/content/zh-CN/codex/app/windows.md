---
title: Windows 版 ChatGPT 桌面应用程序
source_id: codex/app/windows
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/app/windows
owner: OpenAI
content_sha256: 1a7bca0783531bf02a3ceee7dd2aff0656bb25db1dc223835e5a34c13fface56
translation_of: codex/app/windows
translation_model: k3
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/app/windows)

Content owner: OpenAI

# Windows 版 ChatGPT 桌面应用程序

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。可以通过在页面 URL 后附加 `.md` 来获取文档页面的 Markdown 版本。

[Windows 版 ChatGPT 桌面应用程序](https://get.microsoft.com/installer/download/9PLM9XGG6VKS?cid=website_cta_psi) 为您提供了一个统一的界面，用于
跨项目工作、运行并行聊天以及审查结果。
Windows 应用程序支持核心工作流，例如工作树、计划任务、Git
功能、内置浏览器、文件预览、插件和技能。
它使用 PowerShell 和
[Windows 沙盒](https://learn.chatgpt.com/docs/windows/windows-sandbox#windows-sandbox) 原生运行在 Windows 上，或者您可以将其配置为
在 [适用于 Linux 2 的 Windows 子系统 (WSL2)](#windows-subsystem-for-linux-wsl) 中运行。

<CodexScreenshot
  alt="Windows 版 ChatGPT 桌面应用程序，显示项目侧边栏、活动聊天和审查窗格"
  lightSrc="/images/codex/windows/codex-windows-light.webp"
  darkSrc="/images/codex/windows/codex-windows-dark.webp"
  variant="no-wallpaper"
  maxHeight="320px"
/>

## 下载 ChatGPT 桌面应用程序

下载适用于 Windows 的 [ChatGPT 桌面应用程序](https://get.microsoft.com/installer/download/9PLM9XGG6VKS?cid=website_cta_psi)。

然后按照 [快速入门](https://learn.chatgpt.com/docs/quickstart?setup=app) 开始使用。

有关企业安装和更新选项，请参见
[部署 Windows 应用程序](https://learn.chatgpt.com/docs/enterprise/windows-deployment)。

如果您偏好使用命令行安装路径，请运行：

```powershell
winget install --id 9PLM9XGG6VKS -s msstore
```

## 原生沙盒

当代理在 PowerShell 中运行时，Windows 上的 ChatGPT 桌面应用程序支持原生 [Windows 沙盒](https://learn.chatgpt.com/docs/windows/windows-sandbox#windows-sandbox)，并且当您在 [适用于 Linux 2 的 Windows 子系统 (WSL2)](#windows-subsystem-for-linux-wsl) 中运行代理时，会使用 Linux 沙盒。要在任一模式下应用沙盒保护，请在向 Codex 发送消息之前，选择撰写框下方的 **请求批准**。

在全访问模式下运行 Codex 意味着 Codex 不限于您的项目
  目录，并且可能会执行可能导致
  数据丢失的无意破坏性操作。保持沙盒边界并使用
  [规则](https://learn.chatgpt.com/docs/agent-configuration/rules) 进行针对性例外设置，或者将您的
  [批准策略设置为
  从不](https://learn.chatgpt.com/docs/agent-approvals-security#run-without-approval-prompts) 以便让
  Codex 在不请求提升权限的情况下尝试解决问题，
  这基于您的 [批准和安全设置](https://learn.chatgpt.com/docs/agent-approvals-security)。

## 为您的开发设置进行自定义

<section class="feature-grid">




### 首选编辑器

为 **打开** 选择一个默认应用程序，例如 Visual Studio、VS Code 或其他
编辑器。您可以针对每个项目覆盖该选择。如果您已经从 **打开** 菜单中为某个项目选择了
不同的应用程序，则该特定项目的
选择优先。




<CodexScreenshot
  alt="Windows 版 ChatGPT 桌面应用程序设置，显示 Windows 上的默认打开方式应用程序"
  lightSrc="/images/codex/windows/open-in-windows-light.webp"
  darkSrc="/images/codex/windows/open-in-windows-dark.webp"
  maxHeight={520}
  maxWidth={784}
/>

</section>

<section class="feature-grid inverse">




### 集成终端

您还可以选择默认的集成终端。根据您已安装的内容，
选项包括：

- PowerShell
- 命令提示符
- Git Bash
- WSL

此更改仅适用于新的终端会话。如果您已经打开了
集成终端，请在期望出现新的默认终端之前
重启应用程序或开始新聊天。




<CodexScreenshot
  alt="Windows 版 ChatGPT 桌面应用程序设置，显示 Windows 上的集成终端选择"
  lightSrc="/images/codex/windows/integrated-shell-light.webp"
  darkSrc="/images/codex/windows/integrated-shell-dark.webp"
  maxHeight={520}
  maxWidth={788}
/>

</section>

## 适用于 Linux 的 Windows 子系统 (WSL)

默认情况下，ChatGPT 桌面应用程序使用 Windows 原生 Codex 代理。这意味着该代理
在 PowerShell 中运行命令。该应用程序仍然可以处理位于
适用于 Linux 2 的 Windows 子系统 (WSL2) 中的项目，方法是在需要时使用 `wsl` CLI。

如果你想从 WSL 文件系统中添加项目，请点击 **添加新项目**
或按下 <kbd>Ctrl</kbd>+<kbd>O</kbd>，然后在文件
资源管理器窗口中输入 `\\wsl$\`。从那里，选择你的 Linux 发行版以及你
想要打开的文件夹。

如果你打算继续使用 Windows 原生代理，建议将项目存储在
你的 Windows 文件系统中，并通过
`/mnt/<drive>/...` 从 WSL 访问它们。这种设置比
直接从 WSL 文件系统打开项目更可靠。

如果你希望代理本身在 WSL2 中运行，请打开 **[设置](codex://settings)**，
将代理从 Windows 原生切换到 WSL，并**重启应用程序**。在重新启动之前，
更改不会生效。重启后你的项目应该保留在
原位。

Codex `0.114` 及更早版本支持 WSL1。从 Codex `0.115` 开始，Linux
沙盒移至 `bubblewrap`，因此不再支持 WSL1。

<CodexScreenshot
  alt="ChatGPT 桌面应用程序设置显示带有 Windows 原生和 WSL 选项的代理选择器"
  lightSrc="/images/codex/windows/wsl-select-light.webp"
  darkSrc="/images/codex/windows/wsl-select-dark.webp"
  maxHeight={520}
  maxWidth={786}
  class="mb-8"
/>

你可以独立于代理配置集成终端。请参阅
[为您的开发设置进行自定义](#customize-for-your-dev-setup) 以了解
终端选项。你可以将代理保留在 WSL 中，同时仍在
终端中使用 PowerShell，或者两者都使用 WSL，具体取决于你的工作流。

## 有用的开发者工具

当已经安装了一些常用的开发者工具时，Codex 效果最佳：

- **Git**：为 ChatGPT 桌面应用程序中的审查面板提供支持，并允许你检查或
  还原更改。
- **Node.js**：代理用来执行任务的常用工具，
  效率更高。
- **Python**：代理用来执行任务的常用工具，
  效率更高。
- **.NET SDK**：在你想要构建原生 Windows 应用程序时非常有用。
- **GitHub CLI**：为 ChatGPT 桌面应用程序中特定于 GitHub 的功能提供支持。

使用默认的 Windows 包管理器 `winget` 安装它们，方法是将其粘贴
到 [集成终端](https://learn.chatgpt.com/docs/integrated-terminal) 中，或者
要求 Codex 安装它们：

```powershell
winget install --id Git.Git
winget install --id OpenJS.NodeJS.LTS
winget install --id Python.Python.3.14
winget install --id Microsoft.DotNet.SDK.10
winget install --id GitHub.cli
```

安装 GitHub CLI 后，运行 `gh auth login` 以在
应用程序中启用 GitHub 功能。

如果你需要不同的 Python 或 .NET 版本，请将包 ID 更改为
你想要的版本。

## 故障排除和常见问题解答

### 以提升的权限运行命令

如果你需要 Codex 以提升的权限运行命令，请以管理员身份启动 ChatGPT
桌面应用程序本身。安装完成后，打开“开始”菜单，
找到该应用程序，然后选择 **以管理员身份运行**。Codex 代理会继承该
权限级别。

### PowerShell 执行策略阻止了命令

如果你以前从未在 PowerShell 中使用过诸如 Node.js 或 `npm` 之类的工具，
Codex 代理或集成终端可能会遇到执行策略错误。

如果 Codex 为你创建了 PowerShell 脚本，也会发生这种情况。在这种情况下，
在 PowerShell 运行它们之前，你可能需要设置一个限制较少的
执行策略。

错误可能如下所示：

```text
npm.ps1 cannot be loaded because running scripts is disabled on this system.
```

常见的解决方法是将执行策略设置为 `RemoteSigned`：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned
```

有关详细信息和其他选项，请查阅微软的
[执行策略指南](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_execution_policies)
然后再更改策略。

### Windows 上的本地环境脚本

如果你的 [本地环境](https://learn.chatgpt.com/docs/environments/local-environment) 使用跨平台
命令，例如 `npm` 脚本，你可以保留一个共享的设置脚本或
适用于每个平台的操作集。

如果你需要 Windows 特有的行为，请创建 Windows 特有的设置脚本或
Windows 特有的操作。

操作在你集成终端使用的环境中运行。参见
[为您的开发设置进行自定义](#customize-for-your-dev-setup)。

本地设置脚本在代理环境中运行：如果代理使用 WSL，则在 WSL 中运行，
否则在 PowerShell 中运行。

### 与 WSL 共享配置、身份验证和会话

Windows 应用使用与 Windows 上的原生 Codex 相同的 Codex 主目录：
`%USERPROFILE%\.codex`。

如果你还在 WSL 中运行 Codex CLI，CLI 默认使用 Linux 主
目录，因此它不会自动与 Windows 应用共享配置、缓存的
身份验证或会话历史。

要共享它们，请使用以下方法之一：

- 将 WSL `~/.codex` 与文件系统上的 `%USERPROFILE%\.codex` 同步。
- 通过设置 `CODEX_HOME` 将 WSL 指向 Windows Codex 主目录：

```bash
export CODEX_HOME=/mnt/c/Users/<windows-user>/.codex
```

如果你希望在每次 shell 中都有此设置，请将其添加到你的 WSL shell 配置文件中，例如
`~/.bashrc` 或 `~/.zshrc`。

### Git 功能不可用

如果你没有在 Windows 上原生安装 Git，应用将无法使用某些
功能。请在 PowerShell 或 `cmd.exe` 中使用 `winget install Git.Git` 进行安装。

### 从 `\\wsl$` 打开的项目未检测到 Git

目前，如果你想将 Windows 原生代理与一个同样
可从 WSL 访问的项目一起使用，最可靠的变通方法是将项目
存储在原生 Windows 驱动器上，并通过 `/mnt/<drive>/...` 在 WSL 中访问它。

### `Cmder` 未在打开对话框中列出

如果 `Cmder` 已安装但未在 Codex 的打开对话框中显示，请将其添加到
Windows 开始菜单：右键点击 `Cmder` 并选择 **添加到开始菜单**，然后
重启 Codex 或重新启动计算机。

---
title: 沙盒
source_id: codex/sandboxing
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/sandboxing
owner: OpenAI
content_sha256: da5ce60b80ed7c4eed2820bf3d9732b10a268cdf24d70941713266066fe53d09
translation_of: codex/sandboxing
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/sandboxing)

Content owner: OpenAI

# 沙盒

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。通过在页面 URL 后附加 `.md`，可以获取文档页面的 Markdown 版本。

沙盒是一个边界，它允许智能体自主行动，而无需赋予其
对您机器的不受限制的访问权限。当本地聊天在
**ChatGPT 桌面应用程序**、**Codex CLI** 或 **IDE 扩展**中运行命令时，这些命令将在
一个受限的环境中运行，而不是默认以完全访问权限运行。

该环境定义了智能体可以自行执行的操作，例如它可以修改哪些文件
以及命令是否可以使用网络。当任务停留在
这些边界内时，智能体可以继续执行而无需暂停以等待确认。当
它需要超出这些边界时，审批流程将接管。

沙盒和审批是协同工作的不同控制手段。
  沙盒定义了技术边界。审批策略决定了智能体何时必须
  停下并在跨越这些边界之前进行询问。

## 沙盒的作用

沙盒适用于生成的命令，而不仅仅是内置文件
操作。如果智能体运行 `git`、包管理器或测试运行器等工具，
这些命令将继承相同的沙盒边界。

Codex 在每个操作系统上使用平台原生强制执行。其具体实现因
macOS、Linux、WSL2 和原生 Windows 而异，但其核心理念在不同平台上
是一致的：为智能体提供一个有界的工作空间，以便日常任务能够在
明确的限制内自主运行。

## 为什么这很重要

沙盒减少了审批疲劳。智能体无需要求您确认每个
低风险命令，而是可以在您已批准的边界内读取文件、进行编辑并运行日常项目
命令。

它还为智能体工作提供了更清晰的信任模型。您不仅仅是在
信任智能体的意图；您是在信任智能体正在
强制限制内运行。这使得让智能体独立工作变得更加容易，
同时仍然知道它何时会停下来寻求帮助。

## 入门指南

默认权限模式会自动应用沙盒机制。

### 前提条件

在 **macOS** 上，沙盒功能开箱即用，使用内置的 Seatbelt
框架。

在 **Windows** 上，当你在 PowerShell 中运行时，Codex 使用原生的 [Windows
沙盒](https://learn.chatgpt.com/docs/windows/windows-sandbox#windows-sandbox)，而在 WSL2 中运行时，则使用
Linux 沙盒实现。

在 **Linux 和 WSL2** 上，首先使用你的包管理器安装 `bubblewrap`：

<Tabs
  id="codex-sandboxing-prerequisites"
  param="sandbox-os"
  tabs={[
    { id: "ubuntu-debian", label: "Ubuntu/Debian" },
    { id: "fedora", label: "Fedora" },
  ]}
>
  



```bash
sudo apt install bubblewrap
```

  



```bash
sudo dnf install bubblewrap
```

  

</Tabs>

Codex 会使用它在 `bwrap` 上找到的第一个 `PATH` 可执行文件。如果没有 `bwrap`
可执行文件，Codex 会回退到内置的辅助程序，但该辅助程序
需要支持创建非特权用户命名空间。安装
提供 `bwrap` 的发行版软件包可以使此设置保持可靠。

当缺少 `bwrap` 或辅助程序
无法创建所需的用户命名空间时，Codex 会显示启动警告。在限制此
AppArmor 设置的发行版上，建议加载 `bwrap` AppArmor 配置文件，以便 `bwrap` 可以
继续工作，而无需全局禁用该限制。

**Ubuntu AppArmor 注意事项：** 在 Ubuntu 25.04 上，从
  Ubuntu 的软件仓库安装 `bubblewrap` 应该无需额外的 AppArmor 设置即可工作。该
  `bwrap-userns-restrict` 配置文件随 `apparmor` 软件包一起提供，位于
  `/etc/apparmor.d/bwrap-userns-restrict`。

在 Ubuntu 24.04 上，安装 `bubblewrap` 后，Codex 可能仍会警告无法创建所需的用户
命名空间。复制并加载额外的配置文件：

```bash
sudo apt update
sudo apt install apparmor-profiles apparmor-utils
sudo install -m 0644 \
  /usr/share/apparmor/extra-profiles/bwrap-userns-restrict \
  /etc/apparmor.d/bwrap-userns-restrict
sudo apparmor_parser -r /etc/apparmor.d/bwrap-userns-restrict
```

`apparmor_parser -r` 会将配置文件加载到内核中而无需重新启动。你
也可以重新加载所有 AppArmor 配置文件：

```bash
sudo systemctl reload apparmor.service
```

如果该配置文件不可用或无法解决问题，你可以禁用
AppArmor 非特权用户命名空间限制，方法是使用：

```bash
sudo sysctl -w kernel.apparmor_restrict_unprivileged_userns=0
```



## 权限工作原理



使用你界面的权限控制来更改 Codex 处理本地
操作的方式。

批准决定了 Codex 在执行操作之前何时暂停，而沙盒
决定了命令可以访问哪些文件和网络资源。当一个
批准提供不同的范围时，例如批准一次或批准整个会话，
请选择允许任务继续的最窄范围。保持将项目
边界作为默认值；使用独立的项目或工作树，而不是
扩大跨不相关仓库的访问权限.







在 ChatGPT 桌面应用中，使用撰写框下方的权限控制。
根据你的配置，菜单可以包括 **请求批准**、
用于符合条件的批准请求的 **替我批准**、**完全访问**，以及命名的或
自定义的权限配置文件。

<PermissionModeSelectorDemo client:load />







<a id="configure-defaults"></a>



## 配置默认值

为了每次启动时都保持相同的行为，请在 `config.toml` 中设置默认值。
[配置基础](https://learn.chatgpt.com/docs/config-file/config-basic) 解释了其工作原理，而
[配置参考](https://learn.chatgpt.com/docs/config-file/config-reference) 记录了以下各项的确切键：
`sandbox_mode`、`approval_policy`、`approvals_reviewer` 和
`sandbox_workspace_write.writable_roots`。使用这些设置来决定代理默认拥有多少
自主权、它可以写入哪些目录、何时
应暂停以等待批准，以及由谁来审查符合条件的批准请求。

从宏观层面来看，常见的沙盒模式有：

- `read-only`：代理可以检查文件，但未经批准不能编辑文件或运行
  命令。
- `workspace-write`：代理可以读取文件、在工作区内进行编辑，并在该边界内运行
常规本地命令。这是本地工作的默认低阻力
模式。
- `danger-full-access`：代理在无沙盒限制的情况下运行。这会移除
文件系统和网络边界，仅当您希望
代理以完全访问权限执行操作时才应使用。

常见的批准策略有：

- `untrusted`：代理在运行不属于其受信任集合的
  命令之前会进行询问。
- `on-request`：代理默认在沙盒内工作，并在需要
  超出该边界时进行询问。
- `never`：代理不会因批准提示而停止。

当批准是交互式的时候，您还可以通过以下方式选择由谁来审查它们：
`approvals_reviewer`：

- `user`：批准提示会显示给用户。这是默认设置。
- `auto_review`：符合条件的批准提示会发送给审查代理（参见
  [自动审查](https://learn.chatgpt.com/docs/sandboxing/auto-review)）。

完全访问权限意味着将 `sandbox_mode = "danger-full-access"` 与
`approval_policy = "never"` 结合使用。相比之下，风险较低的本地自动化
预设是将 `sandbox_mode = "workspace-write"` 与
`approval_policy = "on-request"` 结合使用，或者使用匹配的 CLI 标志
`--sandbox workspace-write --ask-for-approval on-request`。然后，您可以保留
`approvals_reviewer = "user"` 用于手动批准，或者设置
`approvals_reviewer = "auto_review"` 用于自动批准审查。

如果您需要代理在多个目录中工作，可写根目录允许您
扩展它可以修改的位置，而无需完全移除沙盒。如果
您需要更宽或更窄的信任边界，请调整默认沙盒模式
和批准策略，而不是依赖于一次性例外。

当工作流需要特定例外时，请使用 [规则](https://learn.chatgpt.com/docs/agent-configuration/rules)。规则
允许您在沙盒外部允许、提示或禁止命令前缀，这通常
比广泛扩大访问权限更合适。有关特定于 IDE 的设置
入口点，请参见 [Codex IDE 扩展设置](https://learn.chatgpt.com/docs/developer-settings?surface=ide)。

自动审查（如果可用）不会更改沙盒边界。它是
针对该边界的批准请求的一种可能的 `approvals_reviewer`，例如
沙盒提升、阻止的网络访问，或仍然需要
批准的副作用工具调用。沙盒内已允许的操作运行
时无需额外审查。有关审查者生命周期、触发器类型、拒绝
语义和配置详情，请参见
[自动审查](https://learn.chatgpt.com/docs/sandboxing/auto-review)。

平台详细信息位于特定于平台的文档中。有关原生 Windows 设置、
行为和故障排除，请参见 [Windows](https://learn.chatgpt.com/docs/windows/windows-sandbox)。有关管理员
要求以及沙盒和批准的组织级约束，请参见
[代理批准与安全](https://learn.chatgpt.com/docs/agent-approvals-security)。

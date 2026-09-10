---
title: JetBrains IDE
source_id: claude-code/jetbrains
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/jetbrains
owner: Anthropic
content_sha256: 920527f367773607ee2c88ec6f9c5982be894b8eae9ee9ea0fad8ccb7630c3a0
translation_of: claude-code/jetbrains
translation_model: gpt-5.6
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/jetbrains)

Content owner: Anthropic

> ## 文档索引
> 完整的文档索引位于：https://code.claude.com/docs/llms.txt
> 在进一步探索之前，可使用此文件发现所有可用页面。

# JetBrains IDE

> 在 IntelliJ、PyCharm、WebStorm 等 JetBrains IDE 中使用 Claude Code

Claude Code 通过专用插件与 JetBrains IDE 集成，提供交互式差异查看、选择内容上下文共享等功能。

## 支持的 IDE

Claude Code 插件适用于大多数 JetBrains IDE，包括：

* IntelliJ IDEA
* PyCharm
* Android Studio
* WebStorm
* PhpStorm
* GoLand

## 功能

* **快速启动**：使用 `Cmd+Esc`（Mac）或 `Ctrl+Esc`（Windows/Linux）直接从编辑器打开 Claude Code，也可单击 UI 中的 Claude Code 按钮
* **差异查看**：代码更改可以直接显示在 IDE 差异查看器中，而不是终端中
* **选择内容上下文**：IDE 中的当前选择内容或标签页会自动与 Claude Code 共享。[`Read` 拒绝规则](/docs/en/permissions#read-and-edit)会阻止共享匹配的文件
* **文件引用快捷键**：使用 `Cmd+Option+K`（Mac）或 `Alt+Ctrl+K`（Linux/Windows）插入 `@src/auth.ts#L1-99` 等文件引用
* **诊断共享**：工作过程中，IDE 中的 lint 和语法错误等诊断错误会自动与 Claude 共享

## 安装

插件会在 IDE 的集成终端中运行 `claude` 命令并与之连接。它本身不捆绑 CLI，因此需要安装这两个部分：

<Steps>
  <Step title="安装 Claude Code CLI">
    如果尚未安装，请按照[快速入门](/docs/en/quickstart)安装 CLI。当 `claude` 不在 PATH 中时，插件会显示“Cannot launch Claude Code”通知。
  </Step>

  <Step title="安装 JetBrains 插件">
    从 JetBrains Marketplace 安装 [Claude Code 插件](https://plugins.jetbrains.com/plugin/27310-claude-code-beta-)，然后重启 IDE。
  </Step>
</Steps>

如果 `claude` 安装在 IDE 无法找到的位置，请在插件的 [Claude command 设置](#general-settings)中设置完整路径。

Claude Code 适用于任何付费 Claude 订阅（Pro、Max、Team 或 Enterprise）或 Claude Console 账户，无需 API 密钥。首次运行 `claude` 时，系统会提示你[登录](/docs/en/authentication#log-in-to-claude-code)。

<Note>
  安装插件后，可能需要彻底重启 IDE 才会生效。
</Note>

## 用法

### 从 IDE 使用

在 IDE 的集成终端中运行 `claude`，所有集成功能都会启用。

### 从外部终端使用

在任意外部终端中使用 `/ide` 命令，将 Claude Code 连接到 JetBrains IDE 并启用所有功能：

```bash theme={null}
claude
```

```text theme={null}
/ide
```

连接成功后，Claude Code 会显示类似 `Connected to IntelliJ IDEA.` 的消息进行确认。如果 Claude Code 检测到正在运行但尚未安装插件的 IDE，`/ide` 会为你安装插件，并要求重启 IDE。

如果希望 Claude 访问与 IDE 相同的文件，请从与 IDE 项目根目录相同的目录启动 Claude Code。

## 配置

### Claude Code 设置

通过 Claude Code 设置配置 IDE 集成：

1. 运行 `claude`
2. 输入 `/config` 命令
3. 将 **Diff tool** 设置为 `auto`，以在 IDE 中显示差异；或设置为 `terminal`，使其保留在终端中

只有当 Claude Code 连接到 IDE 时，**Diff tool** 条目才会出现在 `/config` 中，因此请从 JetBrains 终端运行 `claude`，或先从外部终端运行 [`/ide`](/docs/en/commands)。有关底层设置，请参阅 [`diffTool`](/docs/en/settings#global-config-settings)。

### 插件设置

前往 **Settings → Tools → Claude Code \[Beta]** 配置 Claude Code 插件：

#### 常规设置

* **Claude command**：指定用于运行 Claude 的自定义命令，例如 `claude`、`/usr/local/bin/claude` 或 `npx @anthropic-ai/claude-code`
* **Suppress notification for Claude command not found**：跳过未找到 Claude 命令的通知
* **Enable using Option+Enter for multi-line prompts**：仅限 macOS。启用后，Option+Enter 会在 Claude Code 提示中插入新行。如果 Option 键意外被捕获，请禁用此项。需要重启终端。
* **Enable automatic updates**：自动检查和安装插件更新，重启后应用

<Tip>
  WSL 用户：将 `wsl -d Ubuntu -- bash -lic "claude"` 设置为 Claude command（将 `Ubuntu` 替换为你的 WSL 发行版名称）
</Tip>

#### ESC 键配置

如果 ESC 键无法中断 JetBrains 终端中的 Claude Code 操作：

1. 前往 **Settings → Tools → Terminal**
2. 选择以下任一方式：
   * 取消选中“Move focus to the editor with Escape”，或
   * 单击“Configure terminal keybindings”，然后删除“Switch focus to Editor”快捷键
3. 应用更改

这样 ESC 键就能正确中断 Claude Code 操作。

## 特殊配置

### 远程开发

<Warning>
  使用 JetBrains Remote Development 时，必须通过 **Settings → Plugin (Host)** 在远程主机上安装插件，而不是安装在本地客户端计算机上。
</Warning>

### WSL 配置

如果你在 WSL2 上将 Claude Code 与 JetBrains IDE 配合使用，并看到“No available IDEs detected”，通常是由于 WSL2 的 NAT 网络或 Windows Firewall 阻止了 WSL2 与 Windows 主机上运行的 IDE 之间的连接。WSL1 直接使用主机网络，因此不受影响。

#### 允许 WSL2 流量通过 Windows Firewall

这是推荐的修复方法，因为它会保留现有的 WSL2 网络模式。

<Steps>
  <Step title="查找 WSL2 IP 地址">
    在 WSL shell 中运行：

    ```bash theme={null}
    hostname -I
    ```

    记下子网：取地址的前两个部分，后面加上 `.0.0/16`。例如，如果地址为 `172.21.123.45`，则子网为 `172.21.0.0/16`。
  </Step>

  <Step title="创建防火墙规则">
    以管理员身份打开 PowerShell 并运行以下命令，调整 IP 范围以匹配你的子网：

    ```powershell theme={null}
    New-NetFirewallRule -DisplayName "Allow WSL2 Internal Traffic" -Direction Inbound -Protocol TCP -Action Allow -RemoteAddress 172.21.0.0/16 -LocalAddress 172.21.0.0/16
    ```
  </Step>

  <Step title="重启 IDE 和 Claude Code">
    关闭并重新打开二者，使新规则生效。
  </Step>
</Steps>

#### 将 WSL2 切换为镜像网络

镜像网络需要 Windows 11 22H2 或更高版本。如果使用 Windows 10，请改用上面的防火墙规则。

将以下内容添加到 Windows 用户目录中的 `.wslconfig`：

```ini theme={null}
[wsl2]
networkingMode=mirrored
```

然后在 PowerShell 中使用 `wsl --shutdown` 重启 WSL。

## 故障排除

### 插件不工作

如果已安装插件，但 IDE 中未出现 Claude Code 功能：

* 确保从项目根目录运行 Claude Code
* 检查 JetBrains 插件是否已在 IDE 设置中启用
* 彻底重启 IDE（可能需要执行多次）
* 对于 Remote Development，请确保插件已安装在远程主机上

### 未检测到 IDE

如果 `/ide` 命令显示“No available IDEs detected”：

* 验证插件已安装并启用
* 彻底重启 IDE
* 如果你原本期望不运行 `/ide` 就自动连接，请检查是否从 IDE 的集成终端启动了 `claude`
* WSL 用户请参阅上面的 [WSL 配置](#wsl-configuration)

### 找不到命令

如果单击 Claude 图标后显示“command not found”：

1. 在终端中运行 `claude --version`，验证 Claude Code 是否已安装
2. 在插件设置中配置 Claude command 路径
3. WSL 用户请使用配置部分提到的 WSL 命令格式

## 安全注意事项

当 Claude Code 在 JetBrains IDE 中以 [`acceptEdits` 权限模式](/docs/en/permission-modes#auto-approve-file-edits-with-acceptedits-mode)运行时，它可能能够修改 IDE 会自动执行的 IDE 配置文件。这可能会增加以 `acceptEdits` 模式运行 Claude Code 的风险，并可能绕过 Claude Code 对 Bash 执行的权限提示。

在 JetBrains IDE 中运行时，请考虑：

* 对编辑使用手动批准模式
* 格外注意只将 Claude 用于受信任的提示
* 了解 Claude Code 有权修改哪些文件

有关 IDE 之外的 Claude Code 安装或登录问题，请参阅[安装和登录故障排除](/docs/en/troubleshoot-install)。

### 内置 IDE MCP 服务器

插件处于活动状态时，会运行一个供 CLI 自动连接的本地 MCP 服务器。CLI 正是通过它在 IDE 的原生差异查看器中打开差异、读取当前选择内容以用于 `@` 提及，并将检查诊断引入对话。

该服务器名为 `ide`，并且不会显示在 `/mcp` 中，因为没有需要配置的内容。不过，如果你的组织使用 [`PreToolUse` hook](/docs/en/hooks#pretooluse) 将 MCP 工具加入允许列表，就需要知道它的存在。

**选择内容和已打开文件的上下文。** 连接期间，CLI 会在你发送的每个提示中包含当前编辑器选择内容和活动文件路径，作为上下文。发生这种情况时，会话记录会显示一行 `⧉ Selected N lines from <file>`。若要排除 `.env` 等敏感文件，请为其路径添加 [`Read` 拒绝规则](/docs/en/permissions#read-and-edit)。匹配的拒绝规则会阻止该文件的所选文本和已打开文件通知传送给 Claude。

**传输和身份验证。** 服务器侦听由操作系统分配的临时端口，该端口不可配置。传输使用未加密的 `ws://`；在环回接口上，任何能够捕获流量的进程也能从锁文件读取令牌，因此 TLS 无法增加针对本地攻击者的保护。每次 IDE 启动都会生成新的随机身份验证令牌，将其写入 `~/.claude/ide/<port>.lock` 锁文件；CLI 必须将它作为 `X-Claude-Code-Ide-Authorization` 标头提供，才能连接。如果设置了 `CLAUDE_CONFIG_DIR`，锁文件会改为写入 `$CLAUDE_CONFIG_DIR/ide/`。

**向模型公开的工具。** 服务器托管多个工具，但只有一个对模型可见。其余工具是 CLI 用于自身 UI 的内部 RPC，例如打开差异和读取选择内容；它们会在工具列表送达 Claude 之前被滤除。

| 工具名称（hook 所见） | 功能                                                                                                          | 只读 |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------------- | --------- |
| `mcp__ide__getDiagnostics`   | 返回 IDE 的检查诊断，即编辑器中显示的错误和警告。可选择将范围限定到一个文件。 | 是       |

JetBrains 插件不会向模型公开代码执行工具。

**侦听接口。** 服务器绑定到哪个网络接口，由 **Settings → Tools → Claude Code \[Beta] → Networking (Advanced)** 下的 **Accept connections from all network interfaces** 控制。禁用该设置时，服务器仅侦听 `127.0.0.1`，其他主机无法访问。启用后，可从本地网络访问该端口。此设置适用于 CLI 无法通过环回接口访问 IDE 的情况，例如采用默认 NAT 网络的 WSL2，或远程 IDE 设置；有关这种场景，请参阅 [WSL 配置](#wsl-configuration)。

<Warning>
  启用 **Accept connections from all network interfaces** 会使本地网络可以访问 IDE MCP 端口。连接仍需要锁文件中的身份验证令牌，但由于传输使用未加密的 `ws://`，启用该设置时，会话流量和令牌都会以明文穿过网络。只有在环回接口确实无法工作时才启用。对于 WSL2，优先使用[镜像网络](#switch-wsl2-to-mirrored-networking)，使 Windows 环回接口与 Linux VM 共享，并让套接字继续留在环回接口上。
</Warning>

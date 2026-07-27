---
title: 快速上手
source_id: claude-code/quickstart
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/quickstart
owner: Anthropic
content_sha256: cf01823d70f5c9eb0187e98a447a76f9153ab1472d2c8e2a582d38c98962d18d
translation_of: claude-code/quickstart
translation_model: k3
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/quickstart)

Content owner: Anthropic

> ## 文档索引
> 在以下地址获取完整的文档索引：https://code.claude.com/docs/llms.txt
> 使用此文件可在深入探索之前发现所有可用页面。

# 快速上手

> 欢迎使用 Claude Code！

本快速上手指南将带你在几分钟内使用 AI 驱动的编码辅助。读完之后，你将了解如何使用 Claude Code 完成常见的开发任务。

## 开始之前

请确保你具备：

* 一个已打开的终端或命令提示符
  * 如果你从未使用过终端，请查看[终端指南](/docs/en/terminal-guide)
* 一个要处理的代码项目
* 一个 [Claude 订阅](https://claude.com/pricing?utm_source=claude_code\&utm_medium=docs\&utm_content=quickstart_prereq)（Pro、Max、Team 或 Enterprise）、[Claude Console](https://console.anthropic.com/) 账户，或通过[受支持的云服务提供商](/docs/en/third-party-integrations)获得的访问权限

<Note>
  本指南涵盖终端 CLI。Claude Code 也可在 [Web](https://claude.ai/code) 上使用，还有[桌面应用](/docs/en/desktop)、[VS Code](/docs/en/vs-code) 和 [JetBrains IDE](/docs/en/jetbrains) 插件、[Slack](/docs/en/slack) 集成，以及通过 [GitHub Actions](/docs/en/github-actions) 和 [GitLab](/docs/en/gitlab-ci-cd) 实现的 CI/CD 集成。参见[所有界面](/docs/en/overview#use-claude-code-everywhere)。
</Note>

## 第 1 步：安装 Claude Code

要安装 Claude Code，请使用以下方法之一：

<Tabs>
  <Tab title="原生安装（推荐）">
    **macOS、Linux、WSL：**

    ```bash theme={null}
    curl -fsSL https://claude.ai/install.sh | bash
    ```

    **Windows PowerShell：**

    ```powershell theme={null}
    irm https://claude.ai/install.ps1 | iex
    ```

    **Windows CMD：**

    ```batch theme={null}
    curl -fsSL https://claude.ai/install.cmd -o install.cmd && install.cmd && del install.cmd
    ```

    如果你看到 `The token '&&' is not a valid statement separator`，说明你正在使用 PowerShell，而不是 CMD。如果你看到 `'irm' is not recognized as an internal or external command`，说明你正在使用 CMD，而不是 PowerShell。当你使用 PowerShell 时，提示符会显示 `PS C:\`；当你使用 CMD 时，则显示不带 `C:\` 的 `PS`。

    如果安装命令失败并出现 `syntax error near unexpected token '<'`、`403` 或其他 curl 错误，请参阅[安装故障排查](/docs/en/troubleshoot-install#find-your-error)，将错误与相应的修复方法对应起来，并了解其他安装方法。

    建议在原生 Windows 上安装 [Git for Windows](https://git-scm.com/downloads/win)，以便 Claude Code 可以使用 Bash 工具。如果未安装 Git for Windows，Claude Code 将改用 PowerShell 作为 shell 工具。WSL 环境不需要 Git for Windows。

    <Info>
      原生安装会在后台自动更新，让你始终使用最新版本。
    </Info>
  </Tab>

  <Tab title="Homebrew">
    ```bash theme={null}
    brew install --cask claude-code
    ```

    Homebrew 提供两个 cask。`claude-code` 跟踪稳定发布通道，通常落后约一周，并会跳过存在重大回归的版本。`claude-code@latest` 跟踪最新通道，新版本一经发布即可获得。

    <Info>
      Homebrew 安装不会自动更新。根据你安装的 cask，运行 `brew upgrade claude-code` 或 `brew upgrade claude-code@latest` 以获取最新功能和安全修复。
    </Info>
  </Tab>

  <Tab title="WinGet">
    ```powershell theme={null}
    winget install Anthropic.ClaudeCode
    ```

    <Info>
      WinGet 安装不会自动更新。定期运行 `winget upgrade Anthropic.ClaudeCode` 以获取最新功能和安全修复。
    </Info>
  </Tab>
</Tabs>

你还可以在 Debian、Fedora、RHEL 和 Alpine 上使用 [apt、dnf 或 apk](/docs/en/setup#install-with-linux-package-managers) 进行安装。

要确认安装成功，请运行：

```bash theme={null}
claude --version
```

该命令会打印版本号，后跟 `(Claude Code)`。

## 第 2 步：登录你的账户

Claude Code 需要账户才能使用。使用 `claude` 命令启动交互式会话，首次使用时会提示你登录：

```bash theme={null}
claude
```

对于 Claude 订阅或 Console 账户，请按照提示在浏览器中完成身份验证。如需稍后切换账户或重新认证，请在运行中的会话内输入 `/login`：

```text theme={null}
/login
```

你可以使用以下任意账户类型登录：

* [Claude Pro、Max、Team 或 Enterprise](https://claude.com/pricing?utm_source=claude_code\&utm_medium=docs\&utm_content=quickstart_login)（推荐）
* [Claude Console](https://console.anthropic.com/)（使用预付费额度的 API 访问）。首次登录时，Console 会自动创建一个“Claude Code”工作区，用于集中进行成本跟踪。
* [Amazon Bedrock、Google Cloud 的 Agent Platform 或 Microsoft Foundry](/docs/en/third-party-integrations)（企业云服务提供商）
* 如果你的组织部署了自托管的 [Claude 应用网关](/docs/en/claude-apps-gateway)：管理员会预先配置网关 URL，`/login` 会直接打开 **Cloud gateway** 界面，供你使用企业 SSO 登录

登录后，你的凭据将被存储，无需再次登录。

## 第 3 步：开始你的第一个会话

在任意项目目录中打开终端并启动 Claude Code：

```bash theme={null}
cd /path/to/your/project
claude
```

将 `/path/to/your/project` 替换为你想要处理的项目路径。

你将看到 Claude Code 提示符，上方会显示版本、当前模型和工作目录。输入 `/help` 查看可用命令，或输入 `/resume` 继续之前的对话。

<Tip>
  登录后（第 2 步），你的凭据将存储在系统中。更多信息请参阅[凭据管理](/docs/en/authentication#credential-management)。
</Tip>

## 第 4 步：提出你的第一个问题

让我们从了解你的代码库开始。试试以下命令之一：

```text theme={null}
what does this project do?
```

Claude 会分析你的文件并提供摘要。你也可以提出更具体的问题：

```text theme={null}
what technologies does this project use?
```

```text theme={null}
where is the main entry point?
```

```text theme={null}
explain the folder structure
```

你还可以询问 Claude 自身的能力：

```text theme={null}
what can Claude Code do?
```

```text theme={null}
how do I create custom skills in Claude Code?
```

```text theme={null}
can Claude Code work with Docker?
```

<Note>
  Claude Code 会根据需要读取你的项目文件。你无需手动添加上下文。
</Note>

## 第 5 步：完成你的第一次代码修改

现在让 Claude Code 进行一些实际的编码工作。试试一个简单的任务：

```text theme={null}
add a hello world function to the main file
```

Claude Code 将会：

1. 找到相应的文件
2. 向你展示拟议的更改
3. 根据你的权限模式，在修改文件之前请求你的批准
4. 执行编辑

<Note>
  Claude Code 是否在修改文件前询问，取决于你的[权限模式](/docs/en/permission-modes)。在默认模式下，Claude 会在每次更改前请求批准。按 `Shift+Tab` 可在各模式之间循环切换：`acceptEdits` 会自动批准文件编辑，`plan` 让 Claude 只提出更改而不进行编辑。某些账户还有 `auto` 模式，它会运行后台安全检查并阻止有风险的操作，只有在反复被阻止后才会回到提示模式。
</Note>

## 第 6 步：在 Claude Code 中使用 Git

Claude Code 让 Git 操作变得像对话一样简单：

```text theme={null}
what files have I changed?
```

```text theme={null}
commit my changes with a descriptive message
```

你还可以通过提示执行更复杂的 Git 操作：

```text theme={null}
create a new branch called feature/quickstart
```

```text theme={null}
show me the last 5 commits
```

```text theme={null}
help me resolve merge conflicts
```

## 第 7 步：修复 bug 或添加功能

Claude 擅长调试和功能实现。

用自然语言描述你想要的内容：

```text theme={null}
add input validation to the user registration form
```

或者修复现有问题：

```text theme={null}
there's a bug where users can submit empty forms - fix it
```

Claude Code 将会：

* 定位相关代码
* 理解上下文
* 实现解决方案
* 在可用的情况下运行测试

## 第 8 步：尝试其他常见工作流

与 Claude 协作有多种方式：

**重构代码**

```text theme={null}
refactor the authentication module to use async/await instead of callbacks
```

**编写测试**

```text theme={null}
write unit tests for the calculator functions
```

**更新文档**

```text theme={null}
update the README with installation instructions
```

**代码审查**

```text theme={null}
review my changes and suggest improvements
```

<Tip>
  像与一位乐于助人的同事交谈一样与 Claude 交流。描述你想要实现的目标，它会帮助你达成。
</Tip>

## 常用命令

以下是日常使用中最重要的命令。Shell 命令在你的终端中运行，用于启动或恢复 Claude Code。会话命令在 Claude Code 启动后于其内部运行。

**Shell 命令**

| 命令             | 作用                                           | 示例                             |
| ------------------- | ------------------------------------------------------ | ----------------------------------- |
| `claude`            | 启动交互模式                                 | `claude`                            |
| `claude "task"`     | 运行一次性任务                                    | `claude "fix the build error"`      |
| `claude -p "query"` | 运行一次性查询，然后退出                           | `claude -p "explain this function"` |
| `claude -c`         | 继续当前目录中最近的对话 | `claude -c`                         |
| `claude -r`         | 恢复之前的对话                         | `claude -r`                         |

**会话命令**

| 命令                 | 作用               | 示例  |
| ----------------------- | -------------------------- | -------- |
| `/clear`                | 清除对话历史 | `/clear` |
| `/help`                 | 显示可用命令    | `/help`  |
| `/exit` 或按两次 Ctrl+D | 退出 Claude Code           | `/exit`  |

完整的 shell 命令列表请参阅 [CLI 参考](/docs/en/cli-reference)，完整的会话命令列表请参阅[命令参考](/docs/en/commands)。

## 给新手的专业建议

更多内容请参阅[最佳实践](/docs/en/best-practices)和[常见工作流](/docs/en/common-workflows)。

<AccordionGroup>
  <Accordion title="提出具体的请求">
    不要这样说：“修复这个 bug”

    试试这样说：“修复登录 bug，即用户输入错误凭据后会看到空白屏幕的问题”
  </Accordion>

  <Accordion title="使用分步说明">
    将复杂任务拆分为多个步骤：

    ```text theme={null}
    1. 创建一个新的用户资料数据库表
    2. 创建一个用于获取和更新用户资料的 API 端点
    3. 构建一个允许用户查看和编辑其信息的网页
    ```
  </Accordion>

  <Accordion title="让 Claude 先进行探索">
    在进行更改之前，先让 Claude 理解你的代码：

    ```text theme={null}
    分析数据库架构
    ```

    ```text theme={null}
    构建一个仪表板，展示我们英国客户最常退货的产品
    ```
  </Accordion>

  <Accordion title="使用快捷键节省时间">
    * 输入 `/` 查看所有命令和技能
    * 使用 Tab 键进行命令补全
    * 按 ↑ 查看命令历史
    * 按 `Shift+Tab` 循环切换权限模式
  </Accordion>
</AccordionGroup>

## 接下来做什么？

现在你已经掌握了基础知识，来探索更多高级功能：

<CardGroup cols={2}>
  <Card title="Claude Code 的工作原理" icon="microchip" href="/docs/en/how-claude-code-works">
    了解智能体循环、内置工具以及 Claude Code 如何与你的项目交互
  </Card>

  <Card title="最佳实践" icon="star" href="/docs/en/best-practices">
    通过有效的提示和项目设置获得更好的结果
  </Card>

  <Card title="常见工作流" icon="graduation-cap" href="/docs/en/common-workflows">
    常见任务的分步指南
  </Card>

  <Card title="扩展 Claude Code" icon="puzzle-piece" href="/docs/en/features-overview">
    使用 CLAUDE.md、技能、钩子、MCP 等进行自定义
  </Card>
</CardGroup>

## 获取帮助

* **在 Claude Code 中**：输入 `/help` 或询问“如何……”
* **文档**：你就在这里！浏览其他指南
* **社区**：加入我们的 [Discord](https://www.anthropic.com/discord) 获取技巧和支持

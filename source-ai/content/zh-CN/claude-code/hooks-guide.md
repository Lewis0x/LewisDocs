---
title: 使用钩子自动化操作
source_id: claude-code/hooks-guide
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/hooks-guide
owner: Anthropic
content_sha256: 0a1604ca6fd16351f98848159451d2b450ffd66767dec6347d877ae24987512d
translation_of: claude-code/hooks-guide
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/hooks-guide)

Content owner: Anthropic

> ## 文档索引
> 在以下位置获取完整的文档索引： https://code.claude.com/docs/llms.txt
> 在进一步探索之前，请使用此文件来发现所有可用页面。

# 使用钩子自动化操作

> 在 Claude Code 编辑文件、完成任务或需要输入时，自动运行 shell 命令。格式化代码、发送通知、验证命令并执行项目规则。

钩子是在 Claude Code 生命周期的特定时刻执行的用户定义 shell 命令。它们提供对 Claude Code 行为的确定性控制，确保某些操作始终发生，而不是依赖于 LLM 选择运行它们。使用钩子来执行项目规则、自动化重复任务，并将 Claude Code 与您现有的工具集成。

对于需要判断而非确定性规则的决定，您还可以使用 [基于提示的钩子](#prompt-based-hooks) 或 [基于代理的钩子](#agent-based-hooks)，它们使用 Claude 模型来评估条件。

有关扩展 Claude Code 的其他方法，请参阅 [技能](/docs/en/skills)（用于为 Claude 提供额外指令和可执行命令）、[子代理](/docs/en/sub-agents)（用于在隔离环境中运行任务）以及 [插件](/docs/en/plugins)（用于打包扩展以在项目间共享）。

<Tip>
  本指南涵盖了常见用例和入门方法。有关完整的事件模式、JSON 输入/输出格式以及异步钩子和 MCP 工具钩子等高级功能，请参见 [钩子参考](/docs/en/hooks)。
</Tip>

## 设置你的第一个 hook

要创建一个 hook, 请将一个 `hooks` 块添加到 [settings file](#configure-hook-location). 本演练将创建一个桌面通知 hook, 这样每当 Claude 等待您的输入时, 您就会收到提醒, 而无需一直盯着终端.

<Steps>
  <Step title="将钩子添加到您的设置中">
    打开 `~/.claude/settings.json` 并添加一个 `Notification` 钩子。如果该文件不 存在，创建它。下面的示例针对 macOS 使用 `osascript`；请参阅 [在 Claude 需要输入时获取通知](#get-notified-when-claude-needs-input) 以了解 Linux 和 Windows 命令。

```json theme={null}
    {
      "hooks": {
        "Notification": [
          {
            "matcher": "",
            "hooks": [
              {
                "type": "command",
                "command": "osascript -e 'display notification \"Claude Code needs your attention\" with title \"Claude Code\"'"
              }
            ]
          }
        ]
      }
    }
    ```

    如果你的设置文件中已经存在 `hooks` 键，请将 `Notification` 作为现有事件键的同级添加，而不是替换整个对象。每个事件名称都是单个 `hooks` 对象内的一个键：

    ```json theme={null}
    {
      "hooks": {
        "PostToolUse": [
          {
            "matcher": "Edit|Write",
            "hooks": [{ "type": "command", "command": "jq -r '.tool_input.file_path' | xargs npx prettier --write" }]
          }
        ],
        "Notification": [
          {
            "matcher": "",
            "hooks": [{ "type": "command", "command": "osascript -e 'display notification \"Claude Code needs your attention\" with title \"Claude Code\"'" }]
          }
        ]
      }
    }
    ```

    您也可以通过在 CLI 中描述您的需求，让 Claude 为您编写钩子。
  </Step>

  <Step title="验证配置">
    输入 `/hooks` 以打开钩子浏览器。您将看到所有可用钩子事件的列表，每个配置了钩子的事件旁边都会显示一个计数。选择 `Notification` 以确认您的新钩子出现在列表中。选择该钩子会显示其详细信息：事件、匹配器、类型、源文件和命令。
  </Step>

  <Step title="测试钩子">
    按 `Esc` 返回 CLI。让 Claude 做一些需要权限的事情，然后切换离开终端。您应该会收到一个桌面通知。
  </Step>
</Steps>

<Tip>
  `/hooks` 菜单是只读的。要添加、修改或移除钩子，请直接编辑您的设置 JSON 或让 Claude 进行更改。
</Tip>

## 您可以自动化的内容

钩子允许您在 Claude Code 生命周期的关键点运行代码：在编辑后格式化文件、在命令执行前阻止它们、在 Claude 需要输入时发送通知、在会话开始时注入上下文等等。有关钩子事件的完整列表，请参阅 [钩子参考](/docs/en/hooks#hook-lifecycle)。

每个示例都包含一个即用型的配置块，您可以将其添加到 [设置文件](#configure-hook-location) 中。

关于运行独立模型审查并将发现结果反馈到会话的生产环境示例，请参阅 [`security-guidance` 插件如何与 Claude Code 集成 ](/docs/en/security-guidance#how-the-plugin-integrates-with-claude-code)。

### 当 Claude 需要输入时接收通知

每当 Claude 完成工作并需要您的输入时获取桌面通知，这样您就可以切换到其他任务，而无需不断检查终端。

此钩子使用 `Notification` 事件，该事件在 Claude 等待输入或权限时触发。下面的每个选项卡都使用了平台原生的通知命令。将此添加到 `~/.claude/settings.json`：

<Tabs>
  <Tab title="macOS">
    ```json theme={null}
    {
      "hooks": {
        "Notification": [
          {
            "matcher": "",
            "hooks": [
              {
                "type": "command",
                "command": "osascript -e 'display notification \"Claude Code 需要您的关注\" with title \"Claude Code\"'"
              }
            ]
          }
        ]
      }
    }
    ```

    <Accordion title="如果没有出现通知">
      `osascript` 通过内置的“脚本编辑器”应用路由通知。如果“脚本编辑器”没有通知权限，该命令会静默失败，并且 macOS 不会提示您授予权限。在终端中运行一次此命令，使“脚本编辑器”出现在您的通知设置中：

      ```bash theme={null}
      osascript -e 'display notification "test"'
      ```

      此时还不会出现任何内容。打开 **系统设置 > 通知**，在列表中找到 **脚本编辑器**，然后打开 **允许通知**。再次运行该命令以确认测试通知出现。
    </Accordion>
  </Tab>

  <Tab title="Linux">
    ```json theme={null}
    {
      "hooks": {
        "Notification": [
          {
            "matcher": "",
            "hooks": [
              {
                "type": "command",
                "command": "notify-send 'Claude Code' 'Claude Code 需要您的关注'"
              }
            ]
          }
        ]
      }
    }
    ```
  </Tab>

  <Tab title="Windows (PowerShell)">
    ```json theme={null}
    {
      "hooks": {
        "Notification": [
          {
            "matcher": "",
            "hooks": [
              {
                "type": "command",
                "command": "powershell.exe -Command \"[System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms'); [System.Windows.Forms.MessageBox]::Show('Claude Code 需要您的关注', 'Claude Code')\""
              }
            ]
          }
        ]
      }
    }
    ```
  </Tab>
</Tabs>

空的 `matcher` 会在所有通知类型上触发。若要仅在特定事件上触发，请将其设置为以下值之一：

| 匹配器                | 触发时机                                                                                               |
| :--------------------- | :------------------------------------------------------------------------------------------------------- |
| `permission_prompt`    | Claude 需要您批准工具使用                                                                   |
| `idle_prompt`          | Claude 已完成并等待您的下一个提示                                                          |
| `auth_success`         | 身份验证完成                                                                                 |
| `elicitation_dialog`   | MCP 服务器打开引导表单                                                                  |
| `elicitation_complete` | MCP 引导表单已提交或取消                                                        |
| `elicitation_response` | MCP 引导响应已发送回服务器                                                   |
| `agent_needs_input`    | 后台会话开始等待您的输入。仅在 [agent view](/docs/en/agent-view) 打开时触发 |
| `agent_completed`      | 后台会话完成或失败。仅在 [agent view](/docs/en/agent-view) 打开时触发            |

`agent_needs_input` 和 `agent_completed` 匹配器需要 Claude Code v2.1.198 或更高版本。

输入 `/hooks` 并选择 `Notification` 以确认钩子已注册。有关完整的事件架构，请参见 [通知参考](/docs/en/hooks#notification)。

### 编辑后自动格式化代码

在 Claude 编辑的每个文件上自动运行 [Prettier](https://prettier.io/)，从而保持格式一致而无需手动干预。

此钩子使用带有 `PostToolUse` 匹配器的 `Edit|Write` 事件，因此它仅在文件编辑工具之后运行。该命令使用 [`jq`](https://jqlang.org/) 提取已编辑文件的路径并将其传递给 Prettier。将此添加到项目根目录中的 `.claude/settings.json`：

```json theme={null}
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path' | xargs npx prettier --write"
          }
        ]
      }
    ]
  }
}
```

在 Claude Code v2.1.191 或更高版本中，您也可以将匹配器写为 `Edit,Write`，因为在这些版本中 `|` 和 `,` 对于工具名称匹配器来说是可互换的列表分隔符。

<Note>
  本页的 Bash 示例使用 `jq` 进行 JSON 解析。在 macOS 上使用 `brew install jq` 安装，在 Debian 和 Ubuntu 上使用 `apt-get install jq`，或查看 [`jq` 下载](https://jqlang.org/download/)。
</Note>

### 阻止编辑受保护的文件

阻止 Claude 修改敏感文件，如 `.env`、`package-lock.json` 或 `.git/` 中的任何内容。Claude 会收到解释编辑为何被阻止的反馈，以便它可以调整其方法。

此示例使用一个单独的脚本文件供钩子调用。该脚本根据受保护模式列表检查目标文件路径，并以退出码 2 退出以阻止编辑。

<Steps>
  <Step title="创建钩子脚本">
    将其保存到 `.claude/hooks/protect-files.sh`：

    ```bash theme={null}
    #!/bin/bash
    # protect-files.sh

    INPUT=$(cat)
    FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

    PROTECTED_PATTERNS=(".env" "package-lock.json" ".git/")

    for pattern in "${PROTECTED_PATTERNS[@]}"; do
      if [[ "$FILE_PATH" == *"$pattern"* ]]; then
        echo "Blocked: $FILE_PATH matches protected pattern '$pattern'" >&2
        exit 2
      fi
    done

    exit 0
    ```
  </Step>

  <Step title="在 macOS 和 Linux 上使脚本可执行">
    钩子脚本必须是可执行的，Claude Code 才能运行它们：

    ```bash theme={null}
    chmod +x .claude/hooks/protect-files.sh
    ```
  </Step>

  <Step title="注册钩子">
    向 `PreToolUse` 添加一个 `.claude/settings.json` 钩子，在任何 `Edit` 或 `Write` 工具调用之前运行该脚本：

    ```json theme={null}
    {
      "hooks": {
        "PreToolUse": [
          {
            "matcher": "Edit|Write",
            "hooks": [
              {
                "type": "command",
                "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/protect-files.sh"
              }
            ]
          }
        ]
      }
    }
    ```
  </Step>
</Steps>

### 压缩后重新注入上下文

当 Claude 的上下文窗口填满时，压缩会总结对话以释放空间。这可能会丢失重要细节。使用带有 `SessionStart` 匹配器的 `compact` 钩子，可以在每次压缩后重新注入关键上下文。

你的命令写入 stdout 的任何文本都会添加到 Claude 的上下文中。此示例提醒 Claude 项目约定和最近的工作。将此添加到项目根目录的 `.claude/settings.json` 中：

```json theme={null}
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "compact",
        "hooks": [
          {
            "type": "command",
            "command": "echo 'Reminder: use Bun, not npm. Run bun test before committing. Current sprint: auth refactor.'"
          }
        ]
      }
    ]
  }
}
```

你可以将 `echo` 替换为任何产生动态输出的命令，例如 `git log --oneline -5` 以显示最近的提交。要在每次会话开始时注入上下文，请考虑改用 [CLAUDE.md](/docs/en/memory)。有关环境变量，请参见参考中的 [`CLAUDE_ENV_FILE`](/docs/en/hooks#persist-environment-variables)。

### 审计配置更改

跟踪会话期间设置或技能文件何时更改。当外部进程或编辑器修改配置文件时，`ConfigChange` 事件会触发，因此你可以记录更改以符合合规性或阻止未经授权的修改。

此示例将每次更改附加到审计日志中。将此添加到 `~/.claude/settings.json`：

```json theme={null}
{
  "hooks": {
    "ConfigChange": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "jq -c '{timestamp: now | todate, source: .source, file: .file_path}' >> ~/claude-config-audit.log"
          }
        ]
      }
    ]
  }
}
```

匹配器按配置类型进行过滤：`user_settings`、`project_settings`、`local_settings`、`policy_settings` 或 `skills`。要阻止更改生效，请以退出码 2 退出或返回 `{"decision": "block"}`。有关完整的输入架构，请参见 [ConfigChange 参考](/docs/en/hooks#configchange)。

### 当目录或文件发生改变时重新加载环境

有些项目会根据你所在的目录设置不同的环境变量。像 [direnv](https://direnv.net/) 这样的工具会在你的 shell 中自动执行此操作，但 Claude 的 Bash 工具无法自行获取这些更改。

将 `SessionStart` 钩子与 `CwdChanged` 钩子配对可以解决此问题。`SessionStart` 会为你启动时所在的目录加载变量，而 `CwdChanged` 会在 Claude 每次更改目录时重新加载这些变量。两者都会写入 `CLAUDE_ENV_FILE`，而 Claude Code 会在每条 Bash 命令之前将其作为脚本前导执行。将以下内容添加到 `~/.claude/settings.json`：

```json theme={null}
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "direnv export bash > \"$CLAUDE_ENV_FILE\""
          }
        ]
      }
    ],
    "CwdChanged": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "direnv export bash > \"$CLAUDE_ENV_FILE\""
          }
        ]
      }
    ]
  }
}
```

在每个包含 `direnv allow` 的目录中运行一次 `.envrc`，以便允许 direnv 加载它。如果您使用 devbox 或 nix 而不是 direnv，使用 `devbox shellenv` 或 `devbox global shellenv` 代替 `direnv export bash`，同样的模式也能生效。

若要对特定文件而不是对每次目录更改做出反应，请使用 `FileChanged` 并配合 `matcher` 列出要监视的文件名，以 `|` 分隔。在构建监视列表时，Claude Code 会将此值拆分为字面文件名，而不是将其作为正则表达式进行求值。请参阅 [FileChanged](/docs/en/hooks#filechanged) 了解当文件更改时，相同的值如何同样过滤运行哪些钩子组。此示例监视工作目录中的 `.envrc` 和 `.env`：

```json theme={null}
{
  "hooks": {
    "FileChanged": [
      {
        "matcher": ".envrc|.env",
        "hooks": [
          {
            "type": "command",
            "command": "direnv export bash > \"$CLAUDE_ENV_FILE\""
          }
        ]
      }
    ]
  }
}
```

请参阅 [CwdChanged](/docs/en/hooks#cwdchanged) 和 [FileChanged](/docs/en/hooks#filechanged) 参考条目以获取输入模式、`watchPaths` 输出，以及 `CLAUDE_ENV_FILE` 详情。

### 自动批准特定的权限提示

跳过您总是允许的工具调用的批准对话框。此示例自动批准 `ExitPlanMode`，这是 Claude 在完成计划展示并要求继续时调用的工具，因此您不会在每次计划准备就绪时都收到提示。

与上面的退出代码示例不同，自动批准需要您的钩子（hook）向标准输出写入一个 JSON 决策。当 `PermissionRequest` 即将显示权限对话框时，Claude Code 钩子会触发，并返回 `"behavior": "allow"` 来代表您回答该提示。

匹配器将钩子的作用域仅限制在 `ExitPlanMode`，因此不会影响其他提示。将此添加到 `~/.claude/settings.json` 中：

```json theme={null}
{
  "hooks": {
    "PermissionRequest": [
      {
        "matcher": "ExitPlanMode",
        "hooks": [
          {
            "type": "command",
            "command": "echo '{\"hookSpecificOutput\": {\"hookEventName\": \"PermissionRequest\", \"decision\": {\"behavior\": \"allow\"}}}'"
          }
        ]
      }
    ]
  }
}
```

当钩子批准时，Claude Code 会退出计划模式，并恢复您进入计划模式之前处于活动状态的任何权限模式。记录会在原本出现对话框的地方显示“Allowed by PermissionRequest hook”。钩子路径始终保留当前对话：它无法像对话框那样清除上下文并开始新的实现会话。

要改为设置特定的权限模式，您的钩子输出可以包含一个带有 `updatedPermissions` 条目的 `setMode` 数组。`mode` 值是任何权限模式，例如 `default`、`acceptEdits` 或 `bypassPermissions`，而 `destination: "session"` 仅将其应用于当前会话。

<Note>
  `bypassPermissions` 仅在会话启动时已经可以使用绕过模式的情况下适用：设置中的 `--dangerously-skip-permissions`、`--permission-mode bypassPermissions`、`--allow-dangerously-skip-permissions` 或 `permissions.defaultMode: "bypassPermissions"`，并且未被 [`permissions.disableBypassPermissionsMode`](/docs/en/permissions#managed-settings) 禁用。它永远不会持久化为 `defaultMode`。
</Note>

要将当前会话切换为 `acceptEdits`，您的钩子会将此 JSON 写入标准输出：

```json theme={null}
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "decision": {
      "behavior": "allow",
      "updatedPermissions": [
        { "type": "setMode", "mode": "acceptEdits", "destination": "session" }
      ]
    }
  }
}
```

请尽可能缩小匹配器的范围。在 `.*` 上进行匹配或将匹配器留空会自动批准所有权限提示，包括文件写入和 shell 命令。请参阅 [PermissionRequest 参考](/docs/en/hooks#permissionrequest-decision-control) 以获取完整的决策字段集合。

## 钩子如何工作

钩子事件在 Claude Code 中的特定生命周期节点触发。当一个事件触发时，所有匹配的钩子将并行运行，并且相同的钩子命令会自动去重。下表显示了每个事件及其触发时机：

| 事件                 | 触发时机                                                                                                                                          |
| :-------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `SessionStart`        | 当会话开始或恢复时                                                                                                                       |
| `Setup`               | 当你使用 Claude Code 启动 `--init-only` 时，或在 `--init` 模式下使用 `--maintenance` 或 `-p` 时。用于在 CI 或脚本中进行一次性准备             |
| `UserPromptSubmit`    | 当你提交提示词时，在 Claude 处理它之前                                                                                                   |
| `UserPromptExpansion` | 当用户输入的命令展开为提示词时，在它到达 Claude 之前。可以阻止展开                                                     |
| `PreToolUse`          | 在工具调用执行之前。可以阻止它                                                                                                              |
| `PermissionRequest`   | 当权限对话框出现时                                                                                                                       |
| `PermissionDenied`    | 当工具调用被自动模式分类器拒绝时。返回 `{retry: true}` 告诉模型它可以重试被拒绝的工具调用                     |
| `PostToolUse`         | 在工具调用成功之后                                                                                                                             |
| `PostToolUseFailure`  | 在工具调用失败之后                                                                                                                                |
| `PostToolBatch`       | 在一整批并行工具调用完成之后，在下一次模型调用之前                                                                         |
| `Notification`        | 当 Claude Code 发送通知时                                                                                                                  |
| `MessageDisplay`      | 在显示助手消息文本时                                                                                                              |
| `SubagentStart`       | 当生成子代理时                                                                                                                             |
| `SubagentStop`        | 当子代理完成时                                                                                                                               |
| `TaskCreated`         | 当通过 `TaskCreate` 创建任务时                                                                                                          |
| `TaskCompleted`       | 当任务被标记为已完成时                                                                                                               |
| `Stop`                | 当 Claude 完成响应时                                                                                                                        |
| `StopFailure`         | 当由于 API 错误导致轮次结束时。输出和退出代码将被忽略                                                                               |
| `TeammateIdle`        | 当一个 [agent team](/docs/en/agent-teams) 队友即将进入空闲状态时                                                                                     |
| `InstructionsLoaded`  | 当 CLAUDE.md 或 `.claude/rules/*.md` 文件被加载到上下文中时。在会话开始时以及会话期间延迟加载文件时触发         |
| `ConfigChange`        | 当会话期间配置文件发生更改时                                                                                                     |
| `CwdChanged`          | 当工作目录更改时，例如当 Claude 执行 `cd` 命令时。适用于使用 direnv 等工具进行响应式环境管理 |
| `FileChanged`         | 当受监视的文件在磁盘上发生更改时。`matcher` 字段指定要监视的文件名                                                            |
| `WorktreeCreate`      | 当通过 `--worktree`、`isolation: "worktree"` 或为后台会话创建工作树时。替换默认的 git 行为                 |
| `WorktreeRemove`      | 当在会话退出时移除工作树、子代理完成或您删除后台会话时                                    |
| `PreCompact`          | 在上下文压缩之前                                                                                                                              |
| `PostCompact`         | 在上下文压缩完成后                                                                                                                     |
| `Elicitation`         | 当 MCP 服务器在工具调用期间请求用户输入时                                                                                              |
| `ElicitationResult`   | 在用户响应 MCP 请求后、将响应发回服务器之前                                                                                                                            |
| `SessionEnd`          | 当会话终止时                                                                                                                              |

每个钩子都有一个 `type` 来决定其运行方式。大多数钩子使用 `"type": "command"`，它会运行一个 shell 命令。还有另外四种类型可用：

* `"type": "http"`: 将事件数据 POST 到 URL。请参见 [HTTP hooks](#http-hooks)。
* `"type": "mcp_tool"`: 在已连接的 MCP 服务器上调用工具。请参见 [MCP tool hooks](/docs/en/hooks#mcp-tool-hook-fields)。
* `"type": "prompt"`: 单轮 LLM 评估。请参见 [Prompt-based hooks](#prompt-based-hooks)。
* `"type": "agent"`: 具有工具访问权限的多轮验证。Agent hooks 处于实验阶段，可能会发生变化。请参见 [Agent-based hooks](#agent-based-hooks)。

### 合并多个钩子的结果

当多个钩子匹配同一个事件时，每个钩子的命令都会运行完毕，然后 Claude Code 才会合并结果。一个钩子返回 `deny` 并不会阻止同级钩子的执行。不要依赖一个钩子的 `deny` 来抑制另一个钩子的副作用。

所有匹配的钩子完成后，Claude Code 会合并它们的输出。对于 `PreToolUse` 权限决定，应用最严格的回答，其顺序依次为 `deny`、`defer`、`ask`、`allow`。来自 `additionalContext` 的文本会被每个钩子保留并一起传递给 Claude。

下面的示例在 `PreToolUse` 上注册了两个 `Bash` 钩子。第一个将每个命令追加到日志文件并退出 0。第二个运行一个脚本，当命令包含 `rm -rf` 时，该脚本以退出码 2 退出以拒绝执行：

```json theme={null}
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r .tool_input.command >> ~/.claude/bash.log"
          },
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/block-rm-rf.sh"
          }
        ]
      }
    ]
  }
}
```

当 Claude 尝试运行 `rm -rf /tmp/build` 时，两个钩子并行执行。日志记录钩子将命令写入 `~/.claude/bash.log` 并退出 0，这表示未做出任何决定。护栏钩子以退出码 2 退出，拒绝该工具调用。拒绝具有优先权，因此 Claude Code 会阻止该命令并向 Claude 显示护栏的标准错误输出。由于日志记录钩子已经运行，因此日志条目仍然会被写入。

### 读取输入并返回输出

钩子通过标准输入、标准输出、标准错误和退出码与 Claude Code 通信。当事件触发时，Claude Code 会将特定于事件的数据作为 JSON 传递到脚本的标准输入。您的脚本读取该数据，执行其操作，然后通过退出码告诉 Claude Code 接下来要做什么。

#### 钩子输入

每个事件都包含通用字段（如 `session_id` 和 `cwd`），但每种事件类型会添加不同的数据。例如，当 Claude 运行 Bash 命令时，`PreToolUse` 钩子会在标准输入上接收到类似以下的内容：

```json theme={null}
{
  "session_id": "abc123",          // unique ID for this session
  "cwd": "/Users/sarah/myproject", // working directory when the event fired
  "hook_event_name": "PreToolUse", // which event triggered this hook
  "tool_name": "Bash",             // the tool Claude is about to use
  "tool_input": {                  // the arguments Claude passed to the tool
    "command": "npm test"          // for Bash, this is the shell command
  }
}
```

您的脚本可以解析该 JSON 并根据这些字段中的任何一个采取行动。相反，`UserPromptSubmit` 钩子会获取 `prompt` 文本，`SessionStart` 钩子会获取一个 `source`，内容为 `startup`、`resume`、`clear`、`compact` 或 `fork`，以此类推。请参阅参考文档中的 [通用输入字段](/docs/en/hooks#common-input-fields) 以了解共享字段，并参阅每个事件的部分以了解特定于事件的架构。

#### 钩子输出

您的脚本通过写入标准输出或标准错误并以特定代码退出的方式，告诉 Claude Code 接下来要做什么。以下 `PreToolUse` 钩子会阻止命令：

```bash theme={null}
#!/bin/bash
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command')

if echo "$COMMAND" | grep -q "drop table"; then
  echo "Blocked: dropping tables is not allowed" >&2  # stderr becomes Claude's feedback
  exit 2                                               # exit 2 = block the action
fi

exit 0  # exit 0 = no decision; the normal permission flow applies
```

退出码决定了接下来发生的事情：

* **退出 0**：钩子报告无异议，操作正常进行。对于 `PreToolUse` 钩子，这并不会批准工具调用：正常的 [权限流程](/docs/en/permissions) 仍然适用。对于 `UserPromptSubmit`、`UserPromptExpansion` 和 `SessionStart` 钩子，您写入标准输出的任何内容都会添加到 Claude 的上下文中。
* **退出 2**：操作被阻止。将原因写入标准错误，Claude 会将其作为反馈接收以便进行调整。某些事件无法被阻止：对于 `SessionStart`、`Setup`、`Notification` 等，退出码 2 会向用户显示标准错误并继续执行。完整列表请参见 [各事件的退出码 2 行为](/docs/en/hooks#exit-code-2-behavior-per-event)。
* **任何其他退出码**：操作继续进行。记录会显示一个 `<hook name> hook error` 通知，后跟标准错误输出的第一行；完整的标准错误输出会进入 [调试日志](/docs/en/hooks#debug-hooks)。

#### 结构化 JSON 输出

退出码只能让你阻止或保持沉默。若要获得更多控制权，请改为退出 0 并向标准输出打印一个 JSON 对象。

<Note>
  使用退出 2 以通过 stderr 消息阻止，或使用退出 0 结合 JSON 进行结构化控制。请勿混用：当你退出 2 时，Claude Code 会忽略 JSON。
</Note>

例如，一个 `PreToolUse` 钩子可以拒绝工具调用并告诉 Claude 原因，或者将其升级给用户进行审批：

```json theme={null}
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Use rg instead of grep for better performance"
  }
}
```

借助 `"deny"`，Claude Code 会取消工具调用并将 `permissionDecisionReason` 反馈给 Claude。这些 `permissionDecision` 值特定于 `PreToolUse`：

* `"allow"`: 跳过交互式权限提示。拒绝和询问规则，包括企业管理的拒绝列表，仍然适用，连接器工具 [你的组织设置为 `ask`](/docs/en/mcp#organization-controls-on-connector-tools) 和标记为 [`requiresUserInteraction`](/docs/en/mcp#require-approval-for-a-specific-tool) 的 MCP 工具的提示也同样适用
* `"deny"`: 取消工具调用并将原因发送给 Claude
* `"ask"`: 正常向用户显示权限提示

第四个值 `"defer"` 可在 [非交互模式](/docs/en/headless) 中通过 `-p` 标志使用。它会退出进程 保留了工具调用，以便 Agent SDK 包装器可以收集输入并恢复执行。请参阅 [推迟工具调用以供稍后使用](/docs/en/hooks#defer-a-tool-call-for-later) 中的 参考。

返回 `"allow"` 会跳过交互式提示，但不会覆盖 [permission rules](/docs/en/permissions#manage-permissions)。如果拒绝规则与工具调用匹配，即使您的钩子返回 `"allow"`，该调用也会被阻止。如果询问规则匹配，用户仍会收到提示，连接器工具 [your organization set to `ask`](/docs/en/mcp#organization-controls-on-connector-tools) 以及标记为 [`requiresUserInteraction`](/docs/en/mcp#require-approval-for-a-specific-tool) 的 MCP 工具也是如此。这意味着来自任何设置范围（包括 [managed settings](/docs/en/settings#settings-files)）的拒绝规则，始终优先于钩子批准。

其他事件使用不同的决策模式。例如，`PostToolUse` 和 `Stop` 钩子使用顶级 `decision: "block"` 字段，而 `PermissionRequest` 使用 `hookSpecificOutput.decision.behavior`。请参阅参考文档中的 [summary table](/docs/en/hooks#decision-control) 以获取按事件划分的完整明细。

对于 `UserPromptSubmit` 钩子，请改用 `hookSpecificOutput.additionalContext` 将文本注入 Claude 的上下文。将 `additionalContext` 嵌套在 `hookSpecificOutput` 内部；如果您将其放在 JSON 的顶层，Claude Code 会静默忽略它。例如，此输出将当前分支状态添加到每个提示中：

```json theme={null}
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "Current branch: release-42. Deploy freeze until Friday."
  }
}
```

请参阅 [UserPromptSubmit decision control](/docs/en/hooks#userpromptsubmit-decision-control) 以了解完整的输出结构，包括阻止提示和设置会话标题。

带有 `type: "prompt"` 的钩子处理输出的方式不同: 请参阅 [基于提示词的钩子](#prompt-based-hooks).

### 带有匹配器的过滤器钩子

如果没有匹配器，钩子会在其事件每次发生时触发。匹配器允许你缩小这个范围。例如，如果你只想在文件编辑后而不是在每次工具调用后运行格式化程序，请在你的 `PostToolUse` 钩子中添加一个匹配器：

```json theme={null}
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": "prettier --write ..." }
        ]
      }
    ]
  }
}
```

`"Edit|Write"` 匹配器仅在 Claude 使用 `Edit` 或 `Write` 工具时触发，而不是在使用 `Bash`、`Read` 或任何其他工具时触发。{/* min-version: 2.1.191 */}在 Claude Code v2.1.191 或更高版本中，逗号以相同的方式分隔备选项，因此 `"Edit, Write"` 是等效的。有关如何评估普通名称和正则表达式，请参见 [匹配器模式](/docs/en/hooks#matcher-patterns)。

<Note>
  Claude 也可以通过 `Bash` 工具运行 shell 命令来创建或修改文件。如果你的钩子必须检测每一次文件更改（例如用于合规性扫描或审计日志记录），请添加一个 [`Stop`](/docs/en/hooks#stop) 钩子，每轮扫描一次工作树。如果需要每次调用都进行覆盖，则还需匹配 `Bash`，并让你的脚本使用 `git status --porcelain` 列出已修改和未跟踪的文件。
</Note>

每个事件类型都匹配特定的字段：

| 事件                                                                                                                                                           | 匹配器过滤的内容                                              | 匹配器值示例                                                                                                                                                              |
| :-------------------------------------------------------------------------------------------------------------------------------------------------------------- | :-------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PermissionRequest`, `PermissionDenied`                                                                      | 工具名称                                                             | `Bash`, `Edit\|Write`, `mcp__.*`                                                                                                                                                    |
| `SessionStart`                                                                                                                                                  | 会话是如何启动的                                               | `startup`, `resume`, `clear`, `compact`, `fork`                                                                                                                                     |
| `Setup`                                                                                                                                                         | 哪个 CLI 标志触发了设置                                        | `init`, `maintenance`                                                                                                                                                               |
| `SessionEnd`                                                                                                                                                    | 会话为什么结束                                                 | `clear`, `resume`, `logout`, `prompt_input_exit`, `bypass_permissions_disabled`, `other`                                                                                            |
| `Notification`                                                                                                                                                  | 通知类型                                                     | `permission_prompt`, `idle_prompt`, `auth_success`, `elicitation_dialog`, `elicitation_complete`, `elicitation_response`, `agent_needs_input`, `agent_completed`                    |
| `SubagentStart`                                                                                                                                                 | 代理类型                                                            | `general-purpose`, `Explore`, `Plan`, 或自定义代理名称                                                                                                                         |
| `PreCompact`, `PostCompact`                                                                                                                                     | 触发压缩的原因                                             | `manual`, `auto`                                                                                                                                                                    |
| `SubagentStop`                                                                                                                                                  | 代理类型                                                            | 与 `SubagentStart` 相同的值                                                                                                                                                      |
| `ConfigChange`                                                                                                                                                  | 配置来源                                                  | `user_settings`, `project_settings`, `local_settings`, `policy_settings`, `skills`                                                                                                  |
| `StopFailure`                                                                                                                                                   | 错误类型                                                            | `rate_limit`, `overloaded`, `authentication_failed`, `oauth_org_not_allowed`, `billing_error`, `invalid_request`, `model_not_found`, `server_error`, `max_output_tokens`, `unknown` |
| `InstructionsLoaded`                                                                                                                                            | 加载原因                                                           | `session_start`, `nested_traversal`, `path_glob_match`, `include`, `compact`                                                                                                        |
| `Elicitation`                                                                                                                                                   | MCP服务器名称                                                       | 您配置的MCP服务器名称                                                                                                                                                    |
| `ElicitationResult`                                                                                                                                             | MCP服务器名称                                                       | 与 `Elicitation` 相同的值                                                                                                                                                        |
| `FileChanged`                                                                                                                                                   | 要监视的字面文件名（见 [FileChanged](/docs/en/hooks#filechanged)） | `.envrc\|.env`                                                                                                                                                                      |
| `UserPromptExpansion`                                                                                                                                           | 命令名称                                                          | 您的技能或命令名称                                                                                                                                                         |
| `UserPromptSubmit`, `PostToolBatch`, `Stop`, `TeammateIdle`, `TaskCreated`, `TaskCompleted`, `WorktreeCreate`, `WorktreeRemove`, `CwdChanged`, `MessageDisplay` | 不支持匹配器                                                    | 每次发生时总是触发                                                                                                                                                    |

下面的选项卡展示了针对不同事件类型的更多匹配器。

<Tabs>
  <Tab title="记录每个 Bash 命令">
    仅匹配 `Bash` 工具调用并将每个命令记录到文件中。`PostToolUse` 事件在命令完成后触发，因此 `tool_input.command` 包含了运行的内容。钩子（hook）通过标准输入（stdin）以 JSON 格式接收事件数据，`jq -r '.tool_input.command'` 仅提取命令字符串，然后 `>>` 将其追加到日志文件中：

    ```json theme={null}
    {
      "hooks": {
        "PostToolUse": [
          {
            "matcher": "Bash",
            "hooks": [
              {
                "type": "command",
                "command": "jq -r '.tool_input.command' >> ~/.claude/command-log.txt"
              }
            ]
          }
        ]
      }
    }
    ```
  </Tab>

  <Tab title="匹配 MCP 工具">
    MCP 工具使用与内置工具不同的命名约定：`mcp__<server>__<tool>`，其中 `<server>` 是 MCP 服务器名称，`<tool>` 是它提供的工具。例如，`mcp__github__search_repositories` 或 `mcp__filesystem__read_file`。来自 [插件捆绑的服务器](/docs/en/mcp#plugin-provided-mcp-servers) 的工具改用带作用域的服务器段，例如 `mcp__plugin_my-plugin_db__query`。使用正则表达式匹配器可以定位来自特定服务器的所有工具，或者使用类似 `mcp__.*__write.*` 的模式进行跨服务器匹配。请参见参考资料中的 [匹配 MCP 工具](/docs/en/hooks#match-mcp-tools) 获取完整示例列表。

    下面的命令使用 `jq` 从钩子的 JSON 输入中提取工具名称，并将其写入标准错误（stderr）。写入 stderr 可以保持标准输出（stdout）整洁以便进行 JSON 输出，并将消息发送到 [调试日志](/docs/en/hooks#debug-hooks)：

    ```json theme={null}
    {
      "hooks": {
        "PreToolUse": [
          {
            "matcher": "mcp__github__.*",
            "hooks": [
              {
                "type": "command",
                "command": "echo \"GitHub tool called: $(jq -r '.tool_name')\" >&2"
              }
            ]
          }
        ]
      }
    }
    ```
  </Tab>

  <Tab title="会话结束时清理">
    `SessionEnd` 事件支持基于会话结束原因的匹配器。此钩子仅在 `clear` 原因下触发（即当您运行 `/clear` 时设置），而在正常退出时不触发：

    ```json theme={null}
    {
      "hooks": {
        "SessionEnd": [
          {
            "matcher": "clear",
            "hooks": [
              {
                "type": "command",
                "command": "rm -f /tmp/claude-scratch-*.txt"
              }
            ]
          }
        ]
      }
    }
    ```
  </Tab>
</Tabs>

有关完整的匹配器语法，请参见 [钩子参考](/docs/en/hooks#configuration)。

#### 使用 `if` 字段按工具名称和参数进行过滤

`if` 字段使用 [permission rule syntax](/docs/en/permissions) 一起来按工具名称和参数过滤钩子，因此只有当工具调用匹配时才会生成钩子进程。这超越了 `matcher`，后者仅在组级别按工具名称进行过滤。

例如，此配置仅在 Claude 使用 `git` 命令而不是所有 Bash 命令时运行钩子：

```json theme={null}
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "if": "Bash(git *)",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/check-git-policy.sh"
          }
        ]
      }
    ]
  }
}
```

您的钩子命令是否运行取决于您的 `if` 模式的结构以及 Claude 正在调用的 Bash 命令：

| `if` 模式       | Bash 命令           | 钩子运行？ | 原因                                                                                                 |
| :----------------- | :--------------------- | :--------- | :-------------------------------------------------------------------------------------------------- |
| `Bash(git *)`      | `git push`             | 是        | 命令名称匹配                                                                                |
| `Bash(git *)`      | `npm test && git push` | 是        | 检查每个子命令；`git push` 匹配                                                      |
| `Bash(git *)`      | `echo $(git log)`      | 是        | 检查 `$()` 和反引号内的命令；`git log` 匹配                                  |
| `Bash(git *)`      | `echo $(date)`         | 否         | 没有子命令匹配 `git *`                                                                       |
| `Bash(git push *)` | `echo $(date)`         | 是        | 指定了除命令名称外更多内容的模式仍会在 `$()`、反引号或 `$VAR` 上运行钩子 |

当无法解析 Bash 命令时，过滤器也会故障放行，无论模式如何都会运行您的钩子。由于该过滤器是尽力而为的，请使用 [permission system](/docs/en/permissions) 而非钩子来强制执行严格的允许或拒绝。

`if` 字段接受与权限规则相同的模式：`"Bash(git *)"`、`"Edit(*.ts)"` 等等。要匹配多个工具名称，请使用独立的处理器，每个处理器都有自己的 `if` 值，或者在支持管道交替的 `matcher` 级别进行匹配。

`if` 仅适用于工具事件：`PreToolUse`、`PostToolUse`、`PostToolUseFailure`、`PermissionRequest` 和 `PermissionDenied`。将其添加到任何其他事件会阻止钩子运行。

### 配置钩子位置

添加钩子的位置决定了它的作用域：

| 位置                                                   | 作用域                              | 可共享                                  |
| :--------------------------------------------------------- | :--------------------------------- | :----------------------------------------- |
| `~/.claude/settings.json`                                  | 您的所有项目                  | 否，仅限本地机器                  |
| `.claude/settings.json`                                    | 单个项目                     | 是，可以提交到代码库          |
| `.claude/settings.local.json`                              | 单个项目                     | 否，当 Claude Code 创建它时会被 gitignore |
| 托管策略设置                                    | 全组织范围                  | 是，由管理员控制                      |
| [Plugin](/docs/en/plugins) `hooks/hooks.json`                   | 当插件启用时             | 是，与插件捆绑在一起               |
| [Skill](/docs/en/skills) 或 [agent](/docs/en/sub-agents) frontmatter | 当技能或代理处于活动状态时 | 是，定义在组件文件中         |

在 [ 中运行 `/hooks`](/docs/en/hooks#the-%2Fhooks-menu)Claude Code 以浏览按事件分组的所有已配置钩子。

要禁用钩子，请在您的设置文件中设置 `"disableAllHooks": true`。除非在那里也设置了 `disableAllHooks`，否则在托管设置中配置的钩子仍会运行。

如果您在 Claude Code 运行时直接编辑设置文件，文件监视器通常会自动获取钩子更改。

## 基于提示的钩子

对于需要判断而非确定性规则的决策，请使用 `type: "prompt"` 钩子。Claude Code 不运行 shell 命令，而是将您的提示和钩子的输入数据发送给 Claude 模型（默认为 Haiku）来做出决策。如果需要更强的能力，您可以使用 `model` 字段指定不同的模型。

模型的唯一任务是以 JSON 格式返回是/否决策：

* `"ok": true`：操作继续
* `"ok": false`：发生什么取决于事件：
  * `Stop` 和 `SubagentStop`：`reason` 被反馈给 Claude 以便它继续工作
  * `PreToolUse`：工具调用被拒绝；默认情况下回合结束并且拒绝 `reason` 作为警告行出现在聊天中。在钩子上设置 `continueOnBlock: true` 以将 `reason` 作为工具错误返回给 Claude，以便它可以调整并继续。 {/* min-version: 2.1.210 */}在 v2.1.210 之前，拒绝 `reason` 作为工具错误返回给 Claude 并且回合继续
  * `PostToolUse`：默认情况下回合结束并且 `reason` 作为警告行出现在聊天中。设置 `continueOnBlock: true` 以将 `reason` 反馈给 Claude 并改为继续回合
  * `PostToolBatch`、`UserPromptSubmit` 和 `UserPromptExpansion`：回合结束并且 `reason` 作为警告行出现在聊天中

此示例使用 `Stop` 钩子来询问模型是否所有请求的任务都已完成。如果模型返回 `"ok": false`，Claude 继续工作并使用 `reason` 作为其下一条指令：

```json theme={null}
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Check if all tasks are complete. If not, respond with {\"ok\": false, \"reason\": \"what remains to be done\"}."
          }
        ]
      }
    ]
  }
}
```

有关完整的配置选项，请参阅参考中的 [基于提示的钩子](/docs/en/hooks#prompt-based-hooks)。

## 基于代理的钩子

<Warning>
  代理钩子是实验性的。其行为和配置可能会在未来的版本中发生变化。对于生产工作流，建议使用 [命令钩子](/docs/en/hooks#command-hook-fields)。
</Warning>

当验证需要检查文件或运行命令时，请使用 `type: "agent"` 钩子。与仅进行一次 LLM 调用的提示词钩子不同，代理钩子会生成一个子代理，该子代理可以读取文件、搜索代码并使用其他工具来验证条件，然后再返回决策。

代理钩子使用与提示词钩子相同的 `"ok"` / `"reason"` 响应格式，但默认超时时间更长，为 60 秒，并且最多可进行 50 轮工具使用。提示词中的 `$ARGUMENTS` 占位符将被替换为该钩子的 JSON 输入。请参阅 [提示词和代理钩子字段](/docs/en/hooks#prompt-and-agent-hook-fields)。

此示例验证测试是否通过，然后才允许 Claude 停止：

```json theme={null}
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "agent",
            "prompt": "Verify that all unit tests pass. Run the test suite and check the results. $ARGUMENTS",
            "timeout": 120
          }
        ]
      }
    ]
  }
}
```

当仅凭钩子输入数据就足以做出决策时，请使用提示词钩子。当您需要根据代码库的实际状态验证某些内容时，请使用代理钩子。

有关完整的配置选项，请参阅参考文档中的 [基于代理的钩子](/docs/en/hooks#agent-based-hooks)。

## HTTP 钩子

使用 `type: "http"` 钩子将事件数据 POST 到 HTTP 端点，而不是运行 shell 命令。该端点接收与命令钩子在 stdin 上接收到的相同的 JSON，并通过 HTTP 响应正文使用相同的 JSON 格式返回结果。

当你希望由 Web 服务器、云函数或外部服务来处理钩子逻辑时，HTTP 钩子非常有用：例如，一个记录整个团队工具使用事件的共享审计服务。

此示例将每次工具使用情况都 POST 到本地日志记录服务：

```json theme={null}
{
  "hooks": {
    "PostToolUse": [
      {
        "hooks": [
          {
            "type": "http",
            "url": "http://localhost:8080/hooks/tool-use",
            "headers": {
              "Authorization": "Bearer $MY_TOKEN"
            },
            "allowedEnvVars": ["MY_TOKEN"]
          }
        ]
      }
    ]
  }
}
```

该端点应使用与命令钩子相同的 [output format](/docs/en/hooks#json-output) 返回 JSON 响应体。要阻止工具调用，请返回带有相应 `hookSpecificOutput` 字段的 2xx 响应。仅靠 HTTP 状态码无法阻止操作。

标头值支持使用 `$VAR_NAME` 或 `${VAR_NAME}` 语法进行环境变量插值。仅 `allowedEnvVars` 数组中列出的变量会被解析；所有其他 `$VAR` 引用保持为空。

有关完整的配置选项和响应处理，请参阅参考文档中的 [HTTP hooks](/docs/en/hooks#http-hook-fields)。

## 限制与故障排除

### 限制

在设计钩子时请牢记这些限制：

* 命令钩子仅通过标准输出、标准错误和退出代码进行通信。它们无法触发 `/` 命令或工具调用。通过 `additionalContext` 返回的文本将作为系统提醒注入，Claude 会将其读取为纯文本。HTTP 钩子则通过响应正文进行通信。

* 钩子超时时间因类型而异。使用 `timeout` 字段以秒为单位覆盖单个钩子的超时时间。

  * `command`、`http`、`mcp_tool`：10 分钟。`UserPromptSubmit` 将这些时间缩短至 30 秒，而 `MessageDisplay` 将其缩短至 10 秒。

  * `prompt`：30 秒。

  * `agent`：60 秒。
* `PostToolUse` 钩子无法撤销操作，因为工具已经执行完毕。
* `PermissionRequest` 钩子不会在 [非交互模式](/docs/en/headless) 中触发，当带有 `-p` 标志时。请使用 `PreToolUse` 钩子 用于自动化的权限决策。
* `Stop` 钩子在 Claude 完成响应时触发，而不仅仅是在任务完成时触发。它们不会在用户中断时触发。API 错误会触发 [StopFailure](/docs/en/hooks#stopfailure) 来替代。
* 当多个 `PreToolUse` 钩子返回 [`updatedInput`](/docs/en/hooks#pretooluse) 来重写工具的参数时，最后完成的那个会生效。由于钩子是并行运行的，其顺序是不确定的。请避免让多个钩子修改同一个工具的输入。

### 钩子与权限模式

`PreToolUse` 钩子在任何权限模式检查之前触发，在每个 [permission mode](/docs/en/permission-modes) 中，包括 `dontAsk`。返回 `permissionDecision: "deny"` 的钩子即使在 `bypassPermissions` 模式下或使用 `--dangerously-skip-permissions` 时也会阻止工具。这允许您强制执行用户无法通过更改其权限模式来绕过的策略。

反之则不然：返回 `"allow"` 的钩子不会绕过设置中的拒绝规则，并且它不能抑制针对 [您的组织设置为 `ask`](/docs/en/mcp#organization-controls-on-connector-tools) 的连接器工具或标记为 [`requiresUserInteraction`](/docs/en/mcp#require-approval-for-a-specific-tool) 的 MCP 工具的提示。钩子可以收紧限制，但不能放宽到超出权限规则允许的范围。

### 钩子未触发

钩子已配置但从未执行。

* 运行 `/hooks` 并确认钩子出现在正确的事件下
* 检查匹配器模式是否与工具名称完全匹配。匹配器区分大小写
* 验证您触发的是否是正确的事件类型：`PreToolUse` 在工具执行之前触发，`PostToolUse` 在之后触发
* 如果在非交互模式下使用 `PermissionRequest` 标志的 `-p` 钩子，请改用 `PreToolUse`

### 输出中的钩子错误

您在记录中看到类似“PreToolUse hook error: ...”的消息。

* 您的脚本意外地以非零代码退出。通过管道传递示例 JSON 来手动测试它：
  ```bash theme={null}
  echo '{"tool_name":"Bash","tool_input":{"command":"ls"}}' | ./my-hook.sh
  echo $?  # 检查退出代码
  ```
* 如果您看到“command not found”，请使用绝对路径或 `${CLAUDE_PROJECT_DIR}` 来引用脚本。为了完全避免 Shell 引号问题，请添加 `"args": []` 以切换到 [exec form](/docs/en/hooks#exec-form-and-shell-form)，这将直接生成脚本而无需 Shell
* 如果您看到“jq: command not found”，请安装 `jq` 或使用 Python/Node.js 进行 JSON 解析
* 如果脚本根本没有运行，请使其可执行：`chmod +x ./my-hook.sh`

### `/hooks` 显示未配置钩子

您编辑了设置文件，但钩子并未出现在菜单中。

* 文件编辑通常会自动获取。如果几秒钟后仍未出现，可能是文件监视器错过了更改：重启您的会话以强制重新加载。
* 验证您的 JSON 是否有效：不允许使用尾随逗号和注释
* 确认设置文件位于正确的位置：`.claude/settings.json` 用于项目钩子，`~/.claude/settings.json` 用于全局钩子

### Stop 钩子达到阻塞上限

Claude 继续工作而不是停止，然后以警告结束该轮，提示 Stop 钩子连续阻塞次数过多。

Claude Code 会在 Stop 钩子连续阻塞八次且没有进展后覆盖它。您的钩子脚本需要检查是否已经触发了延续。从 JSON 输入中解析 `stop_hook_active` 字段，如果它是 `true` 则提前退出：

```bash theme={null}
#!/bin/bash
INPUT=$(cat)
if [ "$(echo "$INPUT" | jq -r '.stop_hook_active')" = "true" ]; then
  exit 0  # Allow Claude to stop
fi
# ... rest of your hook logic

```

如果您的钩子确实需要超过八次迭代才能收敛，请使用 [`CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`](/docs/en/env-vars) 提高上限。

### JSON 验证失败

即使你的 hook 脚本输出了有效的 JSON，Claude Code 依然显示 JSON 解析错误。

当 Claude Code 运行 shell 形式的命令 hook（即没有 `args` 的 hook）时，它默认在 macOS 和 Linux 上启动 `sh -c`，或在 Windows 上启动 Git Bash。这个 shell 是非交互式的，但 Git Bash 和某些配置（例如 `BASH_ENV` 指向 `~/.bashrc`）仍会加载你的配置文件。如果该配置文件包含无条件的 `echo` 语句，这些输出将被前置到你的 hook 的 JSON 中：

```text theme={null}
Shell ready on arm64
{"decision": "block", "reason": "Not allowed"}
```

Claude Code 会尝试将其作为 JSON 解析并失败。要解决此问题，请将 shell 配置文件中的 echo 语句进行包裹，使它们仅在交互式 shell 中运行：

```bash theme={null}
# In ~/.zshrc or ~/.bashrc

if [[ $- == *i* ]]; then
  echo "Shell ready"
fi
```

`$-` 变量包含 shell 标志，而 `i` 表示交互式。Hook 在非交互式 shell 中运行，因此 echo 会被跳过。

### 调试技巧

通过 `Ctrl+O` 切换的记录视图会为每个触发的钩子显示一行摘要：成功时保持静默，阻塞错误显示标准错误输出，非阻塞错误显示 `<hook name> hook error` 通知并附带标准错误输出的第一行。

要获取完整的执行细节（包括哪些钩子匹配、其退出代码、标准输出和标准错误输出），请阅读调试日志。使用 Claude Code 启动 `claude --debug-file /tmp/claude.log` 以写入到已知路径，然后在另一个终端中 `tail -f /tmp/claude.log`。如果在启动时没有带该标志，请在会话中途运行 `/debug` 以启用日志记录并查找日志路径。

## 了解更多

* [Hooks 参考](/docs/en/hooks): 完整的事件模式, JSON 输出格式, 异步钩子, 以及 MCP 工具钩子
* [安全注意事项](/docs/en/hooks#security-considerations): 在共享或生产环境中部署钩子之前进行审查
* [Bash 命令验证器示例](https://github.com/anthropics/claude-code/blob/main/examples/hooks/bash_command_validator_example.py): 完整的参考实现

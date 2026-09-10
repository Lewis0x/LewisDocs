---
title: 自定义你的状态栏
source_id: claude-code/statusline
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/statusline
owner: Anthropic
content_sha256: b91075f60f99d3da6a96296bf7ceb7c9fb8f27723adc143a212a3b4e60ae0f84
translation_of: claude-code/statusline
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/statusline)

Content owner: Anthropic

> ## 文档索引
> 在以下地址获取完整的文档索引：https://code.claude.com/docs/llms.txt
> 在进一步探索之前，使用此文件来发现所有可用页面。

# 自定义你的状态栏

> 配置自定义状态栏，以在 Claude Code 中监控上下文窗口使用情况、成本和 git 状态

状态栏是位于 Claude Code 底部的可自定义栏，它会运行你配置的任何 shell 脚本。它通过 stdin 接收 JSON 会话数据，并显示脚本输出的任何内容，让你可以持续、一目了然地查看上下文使用情况、成本、git 状态或任何你想跟踪的信息。

在以下情况下，状态栏非常有用：

* 想在工作时监控上下文窗口的使用情况
* 需要跟踪会话成本
* 跨多个会话工作并需要区分它们
* 希望 git 分支和状态始终可见

状态栏在内置页脚徽章上方单独一行渲染，不会取代它们。如果想在对话中出现 ID 时向页脚添加可点击的链接徽章，而无需编写脚本，请改为配置 [`footerLinksRegexes`](/docs/en/settings#footer-link-badges)。

这是一个 [多行状态行](#display-multiple-lines) 的示例，第一行显示 git 信息，第二行显示带颜色编码的上下文栏。

<Frame>
  <img src="https://mintcdn.com/claude-code/nibzesLaJVh4ydOq/images/statusline-multiline.png?fit=max&auto=format&n=nibzesLaJVh4ydOq&q=85&s=60f11387658acc9ff75158ae85f2ac87" alt="多行状态行：第一行显示模型名称、目录、git 分支，第二行显示上下文使用进度条以及成本和时长" width="776" height="212" data-path="images/statusline-multiline.png" />
</Frame>

本页将介绍 [设置基本状态行](#set-up-a-status-line)，讲解 [数据如何流动](#how-status-lines-work)——从 Claude Code 到你的脚本，列出 [所有可显示的字段](#available-data)，并针对 git 状态、成本跟踪和进度条等常见模式提供 [即用示例](#examples)。

## 设置状态栏

使用 [`/statusline` 命令](#use-the-%2Fstatusline-command) 让 Claude Code 为你生成脚本，或者 [手动创建脚本](#manually-configure-a-status-line) 并将其添加到你的设置中。

### 使用 /statusline 命令

`/statusline` 命令接受用自然语言描述的指令,说明你想要显示的内容。Claude Code 会在 `~/.claude/` 中生成一个脚本文件,并自动更新你的设置:

```text theme={null}
/statusline 显示模型名称和上下文百分比，并带有进度条
```

如果 Claude Code 在设置过程中请求权限,请批准文件编辑提示。

### 手动配置状态行

在你的用户设置（`~/.claude/settings.json`，其中 `~` 是你的主目录）或 [项目设置](/docs/en/settings#settings-files) 中添加一个 `statusLine` 字段。将 `type` 设置为 `"command"`，并将 `command` 指向一个脚本路径或内联 shell 命令。有关创建脚本的完整演练，请参阅 [逐步构建状态行](#build-a-status-line-step-by-step)。

```json theme={null}
{
  "statusLine": {
    "type": "command",
    "command": "~/.claude/statusline.sh",
    "padding": 2
  }
}
```

`command` 字段在 shell 中运行，因此你也可以使用内联命令代替脚本文件。此示例使用 `jq` 解析 JSON 输入并显示模型名称和上下文百分比：

```json theme={null}
{
  "statusLine": {
    "type": "command",
    "command": "jq -r '\"[\\(.model.display_name)] \\(.context_window.used_percentage // 0)% context\"'"
  }
}
```

可选的 `padding` 字段会为状态行内容添加额外的水平间距（以字符计）。默认为 `0`。该内边距是在界面内置间距之外额外添加的，因此它控制的是相对缩进，而不是与终端边缘的绝对距离。

可选的 `refreshInterval` 字段会每 N 秒重新运行你的命令，作为 [事件驱动更新](#how-status-lines-work) 之外的补充。最小值为 `1`。当你的状态行显示基于时间的数据（例如时钟），或当后台子代理在主会话空闲时更改 git 状态时，请设置此字段。不设置则仅在事件发生时运行。

可选的 `hideVimModeIndicator` 字段会抑制提示符下方内置的 `-- INSERT --` 文本。请将此设置为 `true`，当你的脚本自行渲染 [`vim.mode`](#available-data) 时，该模式就不会重复显示。

### 禁用状态行

运行 `/statusline` 并要求它移除或清除你的状态行（例如，`/statusline delete`、`/statusline clear`、`/statusline remove it`）。你也可以手动从 settings.json 中删除 `statusLine` 字段。

## 逐步构建状态行

本演练通过手动创建一个显示当前模型、工作目录和上下文窗口使用百分比的状态行，展示底层发生的过程。

<Note>使用描述你想要的效果来运行 [`/statusline`](#use-the-%2Fstatusline-command)，会自动为你完成所有这些配置。</Note>

这些示例使用 Bash 脚本，适用于 macOS 和 Linux。在 Windows 上，请参阅 [Windows 配置](#windows-configuration) 获取 PowerShell 和 Git Bash 示例。

<Frame>
  <img src="https://mintcdn.com/claude-code/nibzesLaJVh4ydOq/images/statusline-quickstart.png?fit=max&auto=format&n=nibzesLaJVh4ydOq&q=85&s=696445e59ca0059213250651ad23db6b" alt="显示模型名称、目录和上下文百分比的状态行" width="726" height="164" data-path="images/statusline-quickstart.png" />
</Frame>

<Steps>
  <Step title="创建一个读取 JSON 并打印输出的脚本">
    Claude Code 通过 stdin 向你的脚本发送 JSON 数据。该脚本使用 [`jq`](https://jqlang.org/)（一个你可能需要安装的命令行 JSON 解析器）来提取模型名称、目录和上下文百分比，然后打印格式化的一行。

    将其保存到 `~/.claude/statusline.sh`（其中 `~` 是你的主目录，例如 macOS 上的 `/Users/username` 或 Linux 上的 `/home/username`）：

    ```bash theme={null}
    #!/bin/bash
    # Read JSON data that Claude Code sends to stdin
    input=$(cat)

    # Extract fields using jq
    MODEL=$(echo "$input" | jq -r '.model.display_name')
    DIR=$(echo "$input" | jq -r '.workspace.current_dir')
    # The "// 0" provides a fallback if the field is null
    PCT=$(echo "$input" | jq -r '.context_window.used_percentage // 0' | cut -d. -f1)

    # Output the status line - ${DIR##*/} extracts just the folder name
    echo "[$MODEL] 📁 ${DIR##*/} | ${PCT}% context"
    ```
  </Step>

  <Step title="使其可执行">
    将脚本标记为可执行，以便你的 shell 可以运行它：

    ```bash theme={null}
    chmod +x ~/.claude/statusline.sh
    ```
  </Step>

  <Step title="添加到设置">
    告诉 Claude Code 将你的脚本作为状态栏运行。将此配置添加到 `~/.claude/settings.json`，它把 `type` 设置为 `"command"`（意思是“运行此 shell 命令”），并将 `command` 指向你的脚本：

    ```json theme={null}
    {
      "statusLine": {
        "type": "command",
        "command": "~/.claude/statusline.sh"
      }
    }
    ```

    你的状态栏会显示在界面底部。设置会自动重新加载，但更改要到下次与 Claude Code 交互时才会显示。
  </Step>
</Steps>

## 状态栏的工作原理

Claude Code 运行你的脚本，并通过 stdin 将 [JSON 会话数据](#available-data) 传递给它。你的脚本读取 JSON，提取所需内容，并将文本打印到 stdout。Claude Code 会显示脚本打印的任何内容。

**何时更新**

你的脚本在会话启动时运行一次，包括恢复会话时。之后，它会在以下情况再次运行：

* 新的助手消息到达
* `/compact` 完成
* 权限模式更改
* Vim 模式切换
* [`refreshInterval`](#manually-configure-a-status-line) 计时器到期（如果你设置了的话）

{/* min-version: 2.1.216 */}在 v2.1.216 之前，恢复会话会导致命令快速连续运行两次，因此第一个结果可能会在被替换前闪烁一下。

Claude Code 以 300ms 的防抖处理更新，因此快速变化会被合并，脚本在变化停止后只运行一次。如果在脚本仍在运行时触发了新的更新，Claude Code 会取消正在运行的脚本。如果你编辑了脚本，更改会在下次更新触发重新运行时显示。

当主会话空闲时（例如协调器在等待后台子代理时），事件驱动的触发器可能会沉寂。为了在空闲期间让基于时间或外部来源的片段保持最新，可以设置 [`refreshInterval`](#manually-configure-a-status-line)，使命令也按固定计时器重新运行。

**脚本可以输出什么**

* **多行**：每个 `echo` 或 `print` 语句显示为单独的一行。参见[多行示例](#display-multiple-lines)。
* **颜色**：使用 [ANSI 转义码](https://en.wikipedia.org/wiki/ANSI_escape_code#Colors)，例如 `\033[32m` 表示绿色（终端必须支持）。参见[git 状态示例](#git-status-with-colors)。
* **链接**：使用 [OSC 8 转义序列](https://en.wikipedia.org/wiki/ANSI_escape_code#OSC) 使文本可点击（macOS 上 Cmd+点击，Windows/Linux 上 Ctrl+点击）。需要支持超链接的终端，如 iTerm2、Kitty 或 WezTerm。参见[可点击链接示例](#clickable-links)。

**根据终端调整输出大小**

Claude Code 会捕获脚本的输出而不是将其直接连接到终端，因此 `tput cols` 和语言级别的宽度检测无法从脚本内部读取终端大小。{/* min-version: 2.1.153 */}请改为读取 `COLUMNS` 和 `LINES` 环境变量。Claude Code 在运行脚本之前会将这些变量设置为当前终端尺寸。需要 Claude Code v2.1.153 或更高版本。

<Note>状态栏在本地运行，不消耗 API token。它在某些 UI 交互期间会暂时隐藏，包括自动补全建议、帮助菜单和权限提示。</Note>

## 可用数据

Claude Code 通过标准输入(stdin)向你的脚本发送以下 JSON 字段:

| 字段                                                                            | 描述                                                                                                                                                                                                         |
| -------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `model.id`, `model.display_name`                                                 | 当前模型标识符和显示名称                                                                                                                                                                                                         |
| `cwd`, `workspace.current_dir`                                                   | 当前工作目录。两个字段包含相同的值；为了与 `workspace.project_dir` 保持一致，优先使用 `workspace.current_dir`。                                                                                                                                                                                |
| `workspace.project_dir`                                                          | 启动 Claude Code 时所在的目录,如果会话期间工作目录发生变化,该目录可能与 `cwd` 不同                                                                                                                                                                                                         |
| `workspace.added_dirs`                                                           | 通过 `/add-dir` 或 `--add-dir` 添加的额外目录。如果未添加任何目录,则为空数组                                                                                                                                                                                                         |
| `workspace.git_worktree`                                                         | 当当前目录位于使用 `git worktree add` 创建的链接工作树(linked worktree)内时的 Git 工作树名称。在主工作树中不存在。与仅适用于 `worktree.*` 会话的 `--worktree` 不同,该字段对任何 Git 工作树都会被填充                                                                                       |
| `workspace.repo.host`, `workspace.repo.owner`, `workspace.repo.name`             | 从 `origin` 远程地址解析出的仓库标识,例如 `"github.com"`、`"anthropics"`、`"claude-code"`。在 Git 仓库之外或未配置 `origin` 远程地址时不存在                                                                                                                                       |
| `cost.total_cost_usd`                                                            | 以美元计算的会话预估费用,在客户端计算。可能与你实际的账单不同。 {/* min-version: 2.1.211 */}当 `/clear` 开始新会话时重置为 \$0                                                                                                                                                              |
| `cost.total_duration_ms`                                                         | 自会话开始以来的总墙钟时间，以毫秒计                                                                                                                                                                                                                                                                 |
| `cost.total_api_duration_ms`                                                     | 等待 API 响应所花费的总时间，以毫秒计                                                                                                                                                                                                                                                                       |
| `cost.total_lines_added`, `cost.total_lines_removed`                             | 更改的代码行数                                                                                                                                                                                                                                                                                                                                                                  |
| `context_window.total_input_tokens`, `context_window.total_output_tokens`        | 当前上下文窗口中的 token 计数，来自最近一次 API 响应。输入包括缓存读取和写入。{/* min-version: 2.1.132 */}在 v2.1.132 之前，这些是会话累计总数                                                                                                                         |
| `context_window.context_window_size`                                             | 上下文窗口的最大 token 数。默认为 200000，支持扩展上下文的模型为 1000000。                                                                                                                                                                                                                           |
| `context_window.used_percentage`                                                 | 预计算的上下文窗口已用百分比                                                                                                                                                                                                                                                                                 |
| `context_window.remaining_percentage`                                            | 预计算的上下文窗口剩余百分比                                                                                                                                                                                                                                                                                    |
| `context_window.current_usage`                                                   | 上次 API 调用的 token 计数，如 [上下文窗口字段](#context-window-fields) 中所述                                                                                                                                                                                                                                |
| `exceeds_200k_tokens`                                                            | 最近一次 API 响应的总 token 计数（输入、缓存和输出 token 合计）是否超过 200k。无论实际上下文窗口大小如何，这都是固定阈值。                                                                                                                                     |
| `fast_mode`                                                                      | 会话是否启用 [快速模式](/docs/en/fast-mode)                                                                                                                                                                                                                                                                    |
| `effort.level`                                                                   | 当前的推理力度（`low`、`medium`、`high`、`xhigh` 或 `max`)。反映实时会话值，包括会话中途的 `/effort` 更改。Ultracode 不是一个独立的级别，会报告为 `xhigh`。当当前模型不支持 effort 参数时不存在                                                   |
| `thinking.enabled`                                                               | 是否为会话启用了扩展思考                                                                                                                                                                                                                                                                             |
| `rate_limits.five_hour.used_percentage`, `rate_limits.seven_day.used_percentage` | 已消耗的 5 小时或 7 天速率限制的百分比，从 0 到 100                                                                                                                                                                                                                                                                             |
| `rate_limits.five_hour.resets_at`, `rate_limits.seven_day.resets_at`             | 5 小时或 7 天速率限制窗口重置时的 Unix 纪元秒数                                                                                                                                                                                                                                                                             |
| `session_id`                                                                     | 唯一的会话标识符                                                                                                                                                                                                                                                                             |
| `session_name`                                                                   | 会话名称。使用通过 `--name` 标志或 `/rename` 设置的自定义名称（如果存在），否则使用 AI 生成的会话标题。[默认显示名称](/docs/en/sessions#name-your-sessions)（如 `my-app-3f`）不会填充此字段。当会话既没有自定义名称也没有 AI 生成的标题时不存在 |
| `prompt_id`                                                                      | 标识当前正在处理的用户提示的 UUID。与 OpenTelemetry 事件上的 [`prompt.id` 属性匹配](/docs/en/monitoring-usage#event-correlation-attributes)。在首次用户输入之前不存在。{/* min-version: 2.1.196 */}需要 Claude Code v2.1.196 或更高版本                                                |
| `transcript_path`                                                                | 对话记录文件的路径                                                                                                                                                                                                                                                                             |
| `version`                                                                        | Claude Code 版本                                                                                                                                                                                                                                                                             |
| `output_style.name`                                                              | 当前输出样式的名称                                                                                                                                                                                                                                                                                                                                                                 |
| `vim.mode`                                                                       | 当前 vim 模式 (`NORMAL`, `INSERT`, `VISUAL`, 或 `VISUAL LINE`) 当 [vim 模式](/docs/en/interactive-mode#vim-editor-mode) 已启用                  |
| `agent.name`                                                                     | 使用 `--agent` 标志运行或配置代理设置时的代理名称                                                                                                                                                                                                                                                     |
| `pr.number`, `pr.url`                                                            | 为当前分支打开拉取请求。与底部状态栏中的 PR 徽章相对应。在未找到 PR、不在 git 仓库中，或 PR 已合并或关闭时不显示                                                                                                                                               |
| `pr.review_state`                                                                | 待处理 PR 的审查状态：`approved`、`pending`、`changes_requested` 或 `draft`。即使存在 `pr`，也可能独立缺失                                                                                                                                                                                      |
| `worktree.name`                                                                  | 活动工作树的名称。仅在 `--worktree` 会话期间存在                                                                                                                                                                                                                                                                                |
| `worktree.path`                                                                  | 工作树目录的绝对路径                                                                                                                                                                                                                                                                                                                |
| `worktree.branch`                                                                | 工作树的 Git 分支名称（例如 `"worktree-my-feature"`）。基于钩子（hook）的工作树中不存在                                                                                                                                                                                                         |
| `worktree.original_cwd`                                                          | Claude 进入 worktree 之前所在的目录                                                                                                                                                                                                                                                                         |
| `worktree.original_branch`                                                       | 进入 worktree 之前检出的 Git 分支。对于基于 hook 的 worktree 此字段不存在                                                                                                                                                                                                         |

<Accordion title="完整 JSON 架构">
  你的状态栏命令会通过 stdin 收到以下 JSON 结构：

  ```json theme={null}
  {
    "cwd": "/current/working/directory",
    "session_id": "abc123...",
    "session_name": "my-session",
    "prompt_id": "550e8400-e29b-41d4-a716-446655440000",
    "transcript_path": "/path/to/transcript.jsonl",
    "model": {
      "id": "claude-opus-5",
      "display_name": "Opus"
    },
    "workspace": {
      "current_dir": "/current/working/directory",
      "project_dir": "/original/project/directory",
      "added_dirs": [],
      "git_worktree": "feature-xyz",
      "repo": {
        "host": "github.com",
        "owner": "anthropics",
        "name": "claude-code"
      }
    },
    "version": "2.1.90",
    "output_style": {
      "name": "default"
    },
    "cost": {
      "total_cost_usd": 0.01234,
      "total_duration_ms": 45000,
      "total_api_duration_ms": 2300,
      "total_lines_added": 156,
      "total_lines_removed": 23
    },
    "context_window": {
      "total_input_tokens": 15500,
      "total_output_tokens": 1200,
      "context_window_size": 200000,
      "used_percentage": 8,
      "remaining_percentage": 92,
      "current_usage": {
        "input_tokens": 8500,
        "output_tokens": 1200,
        "cache_creation_input_tokens": 5000,
        "cache_read_input_tokens": 2000
      }
    },
    "exceeds_200k_tokens": false,
    "fast_mode": false,
    "effort": {
      "level": "high"
    },
    "thinking": {
      "enabled": true
    },
    "rate_limits": {
      "five_hour": {
        "used_percentage": 23.5,
        "resets_at": 1738425600
      },
      "seven_day": {
        "used_percentage": 41.2,
        "resets_at": 1738857600
      }
    },
    "vim": {
      "mode": "NORMAL"
    },
    "agent": {
      "name": "security-reviewer"
    },
    "pr": {
      "number": 1234,
      "url": "https://github.com/anthropics/claude-code/pull/1234",
      "review_state": "pending"
    },
    "worktree": {
      "name": "my-feature",
      "path": "/path/to/.claude/worktrees/my-feature",
      "branch": "worktree-my-feature",
      "original_cwd": "/path/to/project",
      "original_branch": "main"
    }
  }
  ```

  **可能不存在的字段**（不在 JSON 中出现）：

  * `session_name`：当使用 `--name` 或 `/rename` 设置了自定义名称时出现，或在 AI 生成的会话标题存在后出现。默认显示名称（如 `my-app-3f`）不会填充它
  * `prompt_id`：仅在第一次用户输入之后出现
  * `workspace.git_worktree`：仅当当前目录位于已链接的 git worktree 内时出现
  * `workspace.repo`：仅在配置了 `origin` 远程仓库的 git 仓库内出现
  * `effort`：仅当当前模型支持推理力度参数时出现
  * `vim`：仅在启用 vim 模式时出现
  * `agent`：仅在以 `--agent` 标志运行或配置了代理设置时出现
  * `pr`：仅在当前分支找到开放的 PR 时出现，并在 PR 合并或关闭后移除。`pr.review_state` 可能独立缺失
  * `worktree`：仅在 `--worktree` 会话期间出现。当存在时，对于基于 hook 的 worktree，`branch` 和 `original_branch` 也可能缺失
  * `rate_limits`：仅对 Claude.ai 订阅用户（Pro/Max）在会话中第一次 API 响应之后出现。每个窗口（`five_hour`、`seven_day`）可能独立缺失。使用 `jq -r '.rate_limits.five_hour.used_percentage // empty'` 来优雅地处理缺失情况。

  **可能为 `null` 的字段**：

  * `context_window.current_usage`：在会话中第一次 API 调用之前为 `null`，并且在 `/compact` 之后再次如此，直到下一次 API 调用重新填充它
  * `context_window.used_percentage`、`context_window.remaining_percentage`：在会话早期可能为 `null`

  在脚本中使用条件访问处理缺失字段，并使用回退默认值处理 null 值。
</Accordion>

### 上下文窗口字段

`context_window` 对象描述了最近一次 API 响应的实时上下文窗口。自 v2.1.132 起，`total_input_tokens` 和 `total_output_tokens` 反映当前上下文使用情况，而不是累计的会话总量。

* **组合总量**（`total_input_tokens`、`total_output_tokens`）：当前上下文窗口中的 token 数。`total_input_tokens` 是 `input_tokens`、`cache_creation_input_tokens` 和 `cache_read_input_tokens` 的总和；`total_output_tokens` 是最近一次响应的输出 token 数。两者在第一次 API 响应之前均为 `0`。
* **按组件用量**（`current_usage`）：按类别细分的相同 token 计数。当你需要将缓存命中与新鲜输入分开时使用它。

`current_usage` 对象包含：

* `input_tokens`：当前上下文中的输入 token
* `output_tokens`：生成的输出 token
* `cache_creation_input_tokens`：写入缓存的 token
* `cache_read_input_tokens`：从缓存读取的 token

有关缓存字段的含义及其计费方式，请参阅[检查缓存性能](/docs/en/prompt-caching#check-cache-performance)。

`used_percentage` 字段仅根据输入 token 计算：`input_tokens + cache_creation_input_tokens + cache_read_input_tokens`。它不包括 `output_tokens`。

如果你根据 `current_usage` 手动计算上下文百分比，请使用相同的仅输入公式以匹配 `used_percentage`。

`current_usage` 对象在会话中第一次 API 调用之前为 `null`，并且在 `/compact` 之后立即再次如此，直到下一次 API 调用重新填充它。

## 示例

这些示例展示了常见的状态行模式。要使用任何示例：

1. 将脚本保存到文件，如 `~/.claude/statusline.sh`（或 `.py`/`.js`）
2. 使其可执行：`chmod +x ~/.claude/statusline.sh`
3. 将路径添加到你的[设置](#manually-configure-a-status-line)

Bash 示例使用 [`jq`](https://jqlang.org/) 来解析 JSON。Python 和 Node.js 内置了 JSON 解析功能。

### 上下文窗口使用情况

显示当前模型和上下文窗口使用情况，并附带可视化进度条。每个脚本从 stdin 读取 JSON，提取 `used_percentage` 字段，并构建一个 10 字符的进度条，其中实心块（▓）表示使用量：

<Frame>
  <img src="https://mintcdn.com/claude-code/nibzesLaJVh4ydOq/images/statusline-context-window-usage.png?fit=max&auto=format&n=nibzesLaJVh4ydOq&q=85&s=15b58ab3602f036939145dde3165c6f7" alt="状态栏显示模型名称以及带百分比的进度条" width="448" height="152" data-path="images/statusline-context-window-usage.png" />
</Frame>

<CodeGroup>
  ```bash Bash theme={null}
  #!/bin/bash
  # Read all of stdin into a variable
  input=$(cat)

  # Extract fields with jq, "// 0" provides fallback for null
  MODEL=$(echo "$input" | jq -r '.model.display_name')
  PCT=$(echo "$input" | jq -r '.context_window.used_percentage // 0' | cut -d. -f1)

  # Build progress bar: printf -v creates a run of spaces, then
  # ${var// /▓} replaces each space with a block character
  BAR_WIDTH=10
  FILLED=$((PCT * BAR_WIDTH / 100))
  EMPTY=$((BAR_WIDTH - FILLED))
  BAR=""
  [ "$FILLED" -gt 0 ] && printf -v FILL "%${FILLED}s" && BAR="${FILL// /▓}"
  [ "$EMPTY" -gt 0 ] && printf -v PAD "%${EMPTY}s" && BAR="${BAR}${PAD// /░}"

  echo "[$MODEL] $BAR $PCT%"
  ```

  ```python Python theme={null}
  #!/usr/bin/env python3
  import json, sys

  # json.load reads and parses stdin in one step
  data = json.load(sys.stdin)
  model = data['model']['display_name']
  # "or 0" handles null values
  pct = int(data.get('context_window', {}).get('used_percentage', 0) or 0)

  # String multiplication builds the bar
  filled = pct * 10 // 100
  bar = '▓' * filled + '░' * (10 - filled)

  print(f"[{model}] {bar} {pct}%")
  ```

  ```javascript Node.js theme={null}
  #!/usr/bin/env node
  // Node.js reads stdin asynchronously with events
  let input = '';
  process.stdin.on('data', chunk => input += chunk);
  process.stdin.on('end', () => {
      const data = JSON.parse(input);
      const model = data.model.display_name;
      // Optional chaining (?.) safely handles null fields
      const pct = Math.floor(data.context_window?.used_percentage || 0);

      // String.repeat() builds the bar
      const filled = Math.floor(pct * 10 / 100);
      const bar = '▓'.repeat(filled) + '░'.repeat(10 - filled);

      console.log(`[${model}] ${bar} ${pct}%`);
  });
  ```
</CodeGroup>

### 带颜色的 Git 状态

显示带有颜色编码指示器的 Git 分支，用于表示已暂存和已修改的文件。此脚本使用 [ANSI 转义码](https://en.wikipedia.org/wiki/ANSI_escape_code#Colors) 作为终端颜色：`\033[32m` 为绿色，`\033[33m` 为黄色，`\033[0m` 重置为默认。

<Frame>
  <img src="https://mintcdn.com/claude-code/nibzesLaJVh4ydOq/images/statusline-git-context.png?fit=max&auto=format&n=nibzesLaJVh4ydOq&q=85&s=e656f34f90d1d9a1d0e220988914345f" alt="显示模型、目录、git 分支以及已暂存和已修改文件的颜色指示器的状态行" width="742" height="178" data-path="images/statusline-git-context.png" />
</Frame>

每个脚本都会检查当前目录是否为 Git 仓库，统计已暂存和已修改的文件数量，并显示颜色编码指示器：

<CodeGroup>
  ```bash Bash theme={null}
  #!/bin/bash
  input=$(cat)

  MODEL=$(echo "$input" | jq -r '.model.display_name')
  DIR=$(echo "$input" | jq -r '.workspace.current_dir')

  GREEN='\033[32m'
  YELLOW='\033[33m'
  RESET='\033[0m'

  if git rev-parse --git-dir > /dev/null 2>&1; then
      BRANCH=$(git branch --show-current 2>/dev/null)
      STAGED=$(git diff --cached --numstat 2>/dev/null | wc -l | tr -d ' ')
      MODIFIED=$(git diff --numstat 2>/dev/null | wc -l | tr -d ' ')

      GIT_STATUS=""
      [ "$STAGED" -gt 0 ] && GIT_STATUS="${GREEN}+${STAGED}${RESET}"
      [ "$MODIFIED" -gt 0 ] && GIT_STATUS="${GIT_STATUS}${YELLOW}~${MODIFIED}${RESET}"

      echo -e "[$MODEL] 📁 ${DIR##*/} | 🌿 $BRANCH $GIT_STATUS"
  else
      echo "[$MODEL] 📁 ${DIR##*/}"
  fi
  ```

  ```python Python theme={null}
  #!/usr/bin/env python3
  import json, sys, subprocess, os

  data = json.load(sys.stdin)
  model = data['model']['display_name']
  directory = os.path.basename(data['workspace']['current_dir'])

  GREEN, YELLOW, RESET = '\033[32m', '\033[33m', '\033[0m'

  try:
      subprocess.check_output(['git', 'rev-parse', '--git-dir'], stderr=subprocess.DEVNULL)
      branch = subprocess.check_output(['git', 'branch', '--show-current'], text=True).strip()
      staged_output = subprocess.check_output(['git', 'diff', '--cached', '--numstat'], text=True).strip()
      modified_output = subprocess.check_output(['git', 'diff', '--numstat'], text=True).strip()
      staged = len(staged_output.split('\n')) if staged_output else 0
      modified = len(modified_output.split('\n')) if modified_output else 0

      git_status = f"{GREEN}+{staged}{RESET}" if staged else ""
      git_status += f"{YELLOW}~{modified}{RESET}" if modified else ""

      print(f"[{model}] 📁 {directory} | 🌿 {branch} {git_status}")
  except:
      print(f"[{model}] 📁 {directory}")
  ```

  ```javascript Node.js theme={null}
  #!/usr/bin/env node
  const { execSync } = require('child_process');
  const path = require('path');

  let input = '';
  process.stdin.on('data', chunk => input += chunk);
  process.stdin.on('end', () => {
      const data = JSON.parse(input);
      const model = data.model.display_name;
      const dir = path.basename(data.workspace.current_dir);

      const GREEN = '\x1b[32m', YELLOW = '\x1b[33m', RESET = '\x1b[0m';

      try {
          execSync('git rev-parse --git-dir', { stdio: 'ignore' });
          const branch = execSync('git branch --show-current', { encoding: 'utf8' }).trim();
          const staged = execSync('git diff --cached --numstat', { encoding: 'utf8' }).trim().split('\n').filter(Boolean).length;
          const modified = execSync('git diff --numstat', { encoding: 'utf8' }).trim().split('\n').filter(Boolean).length;

          let gitStatus = staged ? `${GREEN}+${staged}${RESET}` : '';
          gitStatus += modified ? `${YELLOW}~${modified}${RESET}` : '';

          console.log(`[${model}] 📁 ${dir} | 🌿 ${branch} ${gitStatus}`);
      } catch {
          console.log(`[${model}] 📁 ${dir}`);
      }
  });
  ```
</CodeGroup>

### 成本和耗时跟踪

跟踪会话的 API 成本和已用时间。`cost.total_cost_usd` 字段累积当前会话中所有 API 调用的估算成本。`cost.total_duration_ms` 字段测量自会话开始以来的总耗时，而 `cost.total_api_duration_ms` 仅跟踪等待 API 响应所花费的时间。

每个脚本将成本格式化为货币，并将毫秒转换为分钟和秒：

<Frame>
  <img src="https://mintcdn.com/claude-code/nibzesLaJVh4ydOq/images/statusline-cost-tracking.png?fit=max&auto=format&n=nibzesLaJVh4ydOq&q=85&s=e3444a51fe6f3440c134bd5f1f08ad29" alt="显示模型名称、会话成本和时长的状态行" width="588" height="180" data-path="images/statusline-cost-tracking.png" />
</Frame>

<CodeGroup>
  ```bash Bash theme={null}
  #!/bin/bash
  input=$(cat)

  MODEL=$(echo "$input" | jq -r '.model.display_name')
  COST=$(echo "$input" | jq -r '.cost.total_cost_usd // 0')
  DURATION_MS=$(echo "$input" | jq -r '.cost.total_duration_ms // 0')

  COST_FMT=$(printf '$%.2f' "$COST")
  DURATION_SEC=$((DURATION_MS / 1000))
  MINS=$((DURATION_SEC / 60))
  SECS=$((DURATION_SEC % 60))

  echo "[$MODEL] 💰 $COST_FMT | ⏱️ ${MINS}m ${SECS}s"
  ```

  ```python Python theme={null}
  #!/usr/bin/env python3
  import json, sys

  data = json.load(sys.stdin)
  model = data['model']['display_name']
  cost = data.get('cost', {}).get('total_cost_usd', 0) or 0
  duration_ms = data.get('cost', {}).get('total_duration_ms', 0) or 0

  duration_sec = duration_ms // 1000
  mins, secs = duration_sec // 60, duration_sec % 60

  print(f"[{model}] 💰 ${cost:.2f} | ⏱️ {mins}m {secs}s")
  ```

  ```javascript Node.js theme={null}
  #!/usr/bin/env node
  let input = '';
  process.stdin.on('data', chunk => input += chunk);
  process.stdin.on('end', () => {
      const data = JSON.parse(input);
      const model = data.model.display_name;
      const cost = data.cost?.total_cost_usd || 0;
      const durationMs = data.cost?.total_duration_ms || 0;

      const durationSec = Math.floor(durationMs / 1000);
      const mins = Math.floor(durationSec / 60);
      const secs = durationSec % 60;

      console.log(`[${model}] 💰 $${cost.toFixed(2)} | ⏱️ ${mins}m ${secs}s`);
  });
  ```
</CodeGroup>

### 显示多行

您的脚本可以输出多行，以创建更丰富的显示。每个 `echo` 语句都会在状态区域生成单独的一行。

<Frame>
  <img src="https://mintcdn.com/claude-code/nibzesLaJVh4ydOq/images/statusline-multiline.png?fit=max&auto=format&n=nibzesLaJVh4ydOq&q=85&s=60f11387658acc9ff75158ae85f2ac87" alt="多行状态行：第一行显示模型名称、目录、git 分支，第二行显示上下文使用进度条以及成本和时长" width="776" height="212" data-path="images/statusline-multiline.png" />
</Frame>

此示例结合了多种技术：基于阈值的颜色（70% 以下为绿色，70-89% 为黄色，90% 及以上为红色）、进度条以及 git 分支信息。每个 `print` 或 `echo` 语句都会创建单独的一行：

<CodeGroup>
  ```bash Bash theme={null}
  #!/bin/bash
  input=$(cat)

  MODEL=$(echo "$input" | jq -r '.model.display_name')
  DIR=$(echo "$input" | jq -r '.workspace.current_dir')
  COST=$(echo "$input" | jq -r '.cost.total_cost_usd // 0')
  PCT=$(echo "$input" | jq -r '.context_window.used_percentage // 0' | cut -d. -f1)
  DURATION_MS=$(echo "$input" | jq -r '.cost.total_duration_ms // 0')

  CYAN='\033[36m'; GREEN='\033[32m'; YELLOW='\033[33m'; RED='\033[31m'; RESET='\033[0m'

  # Pick bar color based on context usage
  if [ "$PCT" -ge 90 ]; then BAR_COLOR="$RED"
  elif [ "$PCT" -ge 70 ]; then BAR_COLOR="$YELLOW"
  else BAR_COLOR="$GREEN"; fi

  FILLED=$((PCT / 10)); EMPTY=$((10 - FILLED))
  printf -v FILL "%${FILLED}s"; printf -v PAD "%${EMPTY}s"
  BAR="${FILL// /█}${PAD// /░}"

  MINS=$((DURATION_MS / 60000)); SECS=$(((DURATION_MS % 60000) / 1000))

  BRANCH=""
  git rev-parse --git-dir > /dev/null 2>&1 && BRANCH=" | 🌿 $(git branch --show-current 2>/dev/null)"

  echo -e "${CYAN}[$MODEL]${RESET} 📁 ${DIR##*/}$BRANCH"
  COST_FMT=$(printf '$%.2f' "$COST")
  echo -e "${BAR_COLOR}${BAR}${RESET} ${PCT}% | ${YELLOW}${COST_FMT}${RESET} | ⏱️ ${MINS}m ${SECS}s"
  ```

  ```python Python theme={null}
  #!/usr/bin/env python3
  import json, sys, subprocess, os

  data = json.load(sys.stdin)
  model = data['model']['display_name']
  directory = os.path.basename(data['workspace']['current_dir'])
  cost = data.get('cost', {}).get('total_cost_usd', 0) or 0
  pct = int(data.get('context_window', {}).get('used_percentage', 0) or 0)
  duration_ms = data.get('cost', {}).get('total_duration_ms', 0) or 0

  CYAN, GREEN, YELLOW, RED, RESET = '\033[36m', '\033[32m', '\033[33m', '\033[31m', '\033[0m'

  bar_color = RED if pct >= 90 else YELLOW if pct >= 70 else GREEN
  filled = pct // 10
  bar = '█' * filled + '░' * (10 - filled)

  mins, secs = duration_ms // 60000, (duration_ms % 60000) // 1000

  try:
      branch = subprocess.check_output(['git', 'branch', '--show-current'], text=True, stderr=subprocess.DEVNULL).strip()
      branch = f" | 🌿 {branch}" if branch else ""
  except:
      branch = ""

  print(f"{CYAN}[{model}]{RESET} 📁 {directory}{branch}")
  print(f"{bar_color}{bar}{RESET} {pct}% | {YELLOW}${cost:.2f}{RESET} | ⏱️ {mins}m {secs}s")
  ```

  ```javascript Node.js theme={null}
  #!/usr/bin/env node
  const { execSync } = require('child_process');
  const path = require('path');

  let input = '';
  process.stdin.on('data', chunk => input += chunk);
  process.stdin.on('end', () => {
      const data = JSON.parse(input);
      const model = data.model.display_name;
      const dir = path.basename(data.workspace.current_dir);
      const cost = data.cost?.total_cost_usd || 0;
      const pct = Math.floor(data.context_window?.used_percentage || 0);
      const durationMs = data.cost?.total_duration_ms || 0;

      const CYAN = '\x1b[36m', GREEN = '\x1b[32m', YELLOW = '\x1b[33m', RED = '\x1b[31m', RESET = '\x1b[0m';

      const barColor = pct >= 90 ? RED : pct >= 70 ? YELLOW : GREEN;
      const filled = Math.floor(pct / 10);
      const bar = '█'.repeat(filled) + '░'.repeat(10 - filled);

      const mins = Math.floor(durationMs / 60000);
      const secs = Math.floor((durationMs % 60000) / 1000);

      let branch = '';
      try {
          branch = execSync('git branch --show-current', { encoding: 'utf8', stdio: ['pipe', 'pipe', 'ignore'] }).trim();
          branch = branch ? ` | 🌿 ${branch}` : '';
      } catch {}

      console.log(`${CYAN}[${model}]${RESET} 📁 ${dir}${branch}`);
      console.log(`${barColor}${bar}${RESET} ${pct}% | ${YELLOW}$${cost.toFixed(2)}${RESET} | ⏱️ ${mins}m ${secs}s`);
  });
  ```
</CodeGroup>

### 可点击链接

此示例创建一个指向 GitHub 仓库的可点击链接。它读取 git 远程 URL，使用 `sed` 将 SSH 格式转换为 HTTPS，并将仓库名称包裹在 OSC 8 转义码中。按住 Cmd（macOS）或 Ctrl（Windows/Linux）并点击即可在浏览器中打开链接。

<Frame>
  <img src="https://mintcdn.com/claude-code/nibzesLaJVh4ydOq/images/statusline-links.png?fit=max&auto=format&n=nibzesLaJVh4ydOq&q=85&s=4bcc6e7deb7cf52f41ab85a219b52661" alt="显示指向 GitHub 仓库的可点击链接的状态行" width="726" height="198" data-path="images/statusline-links.png" />
</Frame>

每个脚本都会获取 git 远程 URL，将 SSH 格式转换为 HTTPS，并将仓库名称包裹在 OSC 8 转义码中。Bash 版本使用 `printf '%b'`，它在不同 shell 中比 `echo -e` 更可靠地解释反斜杠转义：

<CodeGroup>
  ```bash Bash theme={null}
  #!/bin/bash
  input=$(cat)

  MODEL=$(echo "$input" | jq -r '.model.display_name')

  # Convert git SSH URL to HTTPS
  REMOTE=$(git remote get-url origin 2>/dev/null | sed 's/git@github.com:/https:\/\/github.com\//' | sed 's/\.git$//')

  if [ -n "$REMOTE" ]; then
      REPO_NAME=$(basename "$REMOTE")
      # OSC 8 format: \e]8;;URL\a then TEXT then \e]8;;\a
      # printf %b interprets escape sequences reliably across shells
      printf '%b' "[$MODEL] 🔗 \e]8;;${REMOTE}\a${REPO_NAME}\e]8;;\a\n"
  else
      echo "[$MODEL]"
  fi
  ```

  ```python Python theme={null}
  #!/usr/bin/env python3
  import json, sys, subprocess, re, os

  data = json.load(sys.stdin)
  model = data['model']['display_name']

  # Get git remote URL
  try:
      remote = subprocess.check_output(
          ['git', 'remote', 'get-url', 'origin'],
          stderr=subprocess.DEVNULL, text=True
      ).strip()
      # Convert SSH to HTTPS format
      remote = re.sub(r'^git@github\.com:', 'https://github.com/', remote)
      remote = re.sub(r'\.git$', '', remote)
      repo_name = os.path.basename(remote)
      # OSC 8 escape sequences
      link = f"\033]8;;{remote}\a{repo_name}\033]8;;\a"
      print(f"[{model}] 🔗 {link}")
  except:
      print(f"[{model}]")
  ```

  ```javascript Node.js theme={null}
  #!/usr/bin/env node
  const { execSync } = require('child_process');
  const path = require('path');

  let input = '';
  process.stdin.on('data', chunk => input += chunk);
  process.stdin.on('end', () => {
      const data = JSON.parse(input);
      const model = data.model.display_name;

      try {
          let remote = execSync('git remote get-url origin', { encoding: 'utf8', stdio: ['pipe', 'pipe', 'ignore'] }).trim();
          // Convert SSH to HTTPS format
          remote = remote.replace(/^git@github\.com:/, 'https://github.com/').replace(/\.git$/, '');
          const repoName = path.basename(remote);
          // OSC 8 escape sequences
          const link = `\x1b]8;;${remote}\x07${repoName}\x1b]8;;\x07`;
          console.log(`[${model}] 🔗 ${link}`);
      } catch {
          console.log(`[${model}]`);
      }
  });
  ```
</CodeGroup>

### 速率限制用量

在状态栏中显示 Claude.ai 订阅的速率限制用量。`rate_limits` 对象包含 `five_hour`(5 小时滚动窗口)和 `seven_day`(每周)窗口。每个窗口提供 `used_percentage`(0-100)和 `resets_at`(窗口重置时的 Unix 纪元秒数)。

此字段仅在首次 API 响应之后对 Claude.ai 订阅用户(Pro/Max)显示。每个脚本都能优雅地处理该字段缺失的情况:

<CodeGroup>
  ```bash Bash theme={null}
  #!/bin/bash
  input=$(cat)

  MODEL=$(echo "$input" | jq -r '.model.display_name')
  # "// empty" produces no output when rate_limits is absent
  FIVE_H=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
  WEEK=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty')

  LIMITS=""
  [ -n "$FIVE_H" ] && LIMITS="5h: $(printf '%.0f' "$FIVE_H")%"
  [ -n "$WEEK" ] && LIMITS="${LIMITS:+$LIMITS }7d: $(printf '%.0f' "$WEEK")%"

  [ -n "$LIMITS" ] && echo "[$MODEL] | $LIMITS" || echo "[$MODEL]"
  ```

  ```python Python theme={null}
  #!/usr/bin/env python3
  import json, sys

  data = json.load(sys.stdin)
  model = data['model']['display_name']

  parts = []
  rate = data.get('rate_limits', {})
  five_h = rate.get('five_hour', {}).get('used_percentage')
  week = rate.get('seven_day', {}).get('used_percentage')

  if five_h is not None:
      parts.append(f"5h: {five_h:.0f}%")
  if week is not None:
      parts.append(f"7d: {week:.0f}%")

  if parts:
      print(f"[{model}] | {' '.join(parts)}")
  else:
      print(f"[{model}]")
  ```

  ```javascript Node.js theme={null}
  #!/usr/bin/env node
  let input = '';
  process.stdin.on('data', chunk => input += chunk);
  process.stdin.on('end', () => {
      const data = JSON.parse(input);
      const model = data.model.display_name;

      const parts = [];
      const fiveH = data.rate_limits?.five_hour?.used_percentage;
      const week = data.rate_limits?.seven_day?.used_percentage;

      if (fiveH != null) parts.push(`5h: ${Math.round(fiveH)}%`);
      if (week != null) parts.push(`7d: ${Math.round(week)}%`);

      console.log(parts.length ? `[${model}] | ${parts.join(' ')}` : `[${model}]`);
  });
  ```
</CodeGroup>

### 缓存开销大的操作

你的状态行脚本在会话活跃期间会频繁运行。像 `git status` 或 `git diff` 这样的命令可能很慢, 尤其是在大型仓库中。此示例将 git 信息缓存到临时文件中, 并且每 5 秒才刷新一次。

缓存文件名需要在同一会话内的多次状态行调用之间保持稳定, 但在不同会话之间保持唯一, 这样不同仓库中的并发会话就不会读到彼此的 git 状态缓存。基于进程的标识符如 `$$`、`os.getpid()` 或 `process.pid` 每次调用都会变化, 从而使缓存失效。请改用 JSON 输入中的 `session_id`: 它在会话的整个生命周期内保持稳定, 并且每个会话唯一。

每个脚本在运行 git 命令之前, 会检查缓存文件是否缺失或超过 5 秒:

<CodeGroup>
  ```bash Bash theme={null}
  #!/bin/bash
  input=$(cat)

  MODEL=$(echo "$input" | jq -r '.model.display_name')
  DIR=$(echo "$input" | jq -r '.workspace.current_dir')
  SESSION_ID=$(echo "$input" | jq -r '.session_id')

  CACHE_FILE="/tmp/statusline-git-cache-$SESSION_ID"
  CACHE_MAX_AGE=5  # seconds

  cache_is_stale() {
      [ ! -f "$CACHE_FILE" ] || \
      # stat -c %Y (Linux) or stat -f %m (macOS) prints the file's last-modified
      # time. The Linux form must run first: on Linux, the macOS form prints a
      # filesystem report to stdout before failing, and that output would be
      # captured by the command substitution and break the arithmetic.
      [ $(($(date +%s) - $(stat -c %Y "$CACHE_FILE" 2>/dev/null || stat -f %m "$CACHE_FILE" 2>/dev/null || echo 0))) -gt $CACHE_MAX_AGE ]
  }

  if cache_is_stale; then
      if git rev-parse --git-dir > /dev/null 2>&1; then
          BRANCH=$(git branch --show-current 2>/dev/null)
          STAGED=$(git diff --cached --numstat 2>/dev/null | wc -l | tr -d ' ')
          MODIFIED=$(git diff --numstat 2>/dev/null | wc -l | tr -d ' ')
          echo "$BRANCH|$STAGED|$MODIFIED" > "$CACHE_FILE"
      else
          echo "||" > "$CACHE_FILE"
      fi
  fi

  IFS='|' read -r BRANCH STAGED MODIFIED < "$CACHE_FILE"

  if [ -n "$BRANCH" ]; then
      echo "[$MODEL] 📁 ${DIR##*/} | 🌿 $BRANCH +$STAGED ~$MODIFIED"
  else
      echo "[$MODEL] 📁 ${DIR##*/}"
  fi
  ```

  ```python Python theme={null}
  #!/usr/bin/env python3
  import json, sys, subprocess, os, time

  data = json.load(sys.stdin)
  model = data['model']['display_name']
  directory = os.path.basename(data['workspace']['current_dir'])
  session_id = data['session_id']

  CACHE_FILE = f"/tmp/statusline-git-cache-{session_id}"
  CACHE_MAX_AGE = 5  # seconds

  def cache_is_stale():
      if not os.path.exists(CACHE_FILE):
          return True
      return time.time() - os.path.getmtime(CACHE_FILE) > CACHE_MAX_AGE

  if cache_is_stale():
      try:
          subprocess.check_output(['git', 'rev-parse', '--git-dir'], stderr=subprocess.DEVNULL)
          branch = subprocess.check_output(['git', 'branch', '--show-current'], text=True).strip()
          staged = subprocess.check_output(['git', 'diff', '--cached', '--numstat'], text=True).strip()
          modified = subprocess.check_output(['git', 'diff', '--numstat'], text=True).strip()
          staged_count = len(staged.split('\n')) if staged else 0
          modified_count = len(modified.split('\n')) if modified else 0
          with open(CACHE_FILE, 'w') as f:
              f.write(f"{branch}|{staged_count}|{modified_count}")
      except:
          with open(CACHE_FILE, 'w') as f:
              f.write("||")

  with open(CACHE_FILE) as f:
      branch, staged, modified = f.read().strip().split('|')

  if branch:
      print(f"[{model}] 📁 {directory} | 🌿 {branch} +{staged} ~{modified}")
  else:
      print(f"[{model}] 📁 {directory}")
  ```

  ```javascript Node.js theme={null}
  #!/usr/bin/env node
  const { execSync } = require('child_process');
  const fs = require('fs');
  const path = require('path');

  let input = '';
  process.stdin.on('data', chunk => input += chunk);
  process.stdin.on('end', () => {
      const data = JSON.parse(input);
      const model = data.model.display_name;
      const dir = path.basename(data.workspace.current_dir);
      const sessionId = data.session_id;

      const CACHE_FILE = `/tmp/statusline-git-cache-${sessionId}`;
      const CACHE_MAX_AGE = 5; // seconds

      const cacheIsStale = () => {
          if (!fs.existsSync(CACHE_FILE)) return true;
          return (Date.now() / 1000) - fs.statSync(CACHE_FILE).mtimeMs / 1000 > CACHE_MAX_AGE;
      };

      if (cacheIsStale()) {
          try {
              execSync('git rev-parse --git-dir', { stdio: 'ignore' });
              const branch = execSync('git branch --show-current', { encoding: 'utf8' }).trim();
              const staged = execSync('git diff --cached --numstat', { encoding: 'utf8' }).trim().split('\n').filter(Boolean).length;
              const modified = execSync('git diff --numstat', { encoding: 'utf8' }).trim().split('\n').filter(Boolean).length;
              fs.writeFileSync(CACHE_FILE, `${branch}|${staged}|${modified}`);
          } catch {
              fs.writeFileSync(CACHE_FILE, '||');
          }
      }

      const [branch, staged, modified] = fs.readFileSync(CACHE_FILE, 'utf8').trim().split('|');

      if (branch) {
          console.log(`[${model}] 📁 ${dir} | 🌿 ${branch} +${staged} ~${modified}`);
      } else {
          console.log(`[${model}] 📁 ${dir}`);
      }
  });
  ```
</CodeGroup>

### Windows 配置

在 Windows 上,Claude Code 在安装了 Git Bash 时通过 Git Bash 运行状态行命令,在未安装 Git Bash 时通过 PowerShell 运行。

Git Bash 会将未加引号的反斜杠视为转义字符,因此像 `C:\Users\username\script.mjs` 这样的 Windows 风格路径在到达脚本运行器时分隔符会被移除,导致命令失败且没有可见错误。请在 `command` 字符串中使用正斜杠书写文件路径,如下面的示例所示。`~` 简写同样有效,并会扩展为你的 Windows 主目录。

要将 PowerShell 脚本作为状态行运行,请通过 `powershell` 调用它。无论 Claude Code 将命令路由到 Git Bash 还是 PowerShell,这种方式都有效:

<CodeGroup>
  ```json settings.json theme={null}
  {
    "statusLine": {
      "type": "command",
      "command": "powershell -NoProfile -File C:/Users/username/.claude/statusline.ps1"
    }
  }
  ```

  ```powershell statusline.ps1 theme={null}
  $input_json = $input | Out-String | ConvertFrom-Json
  $cwd = $input_json.cwd
  $model = $input_json.model.display_name
  $used = $input_json.context_window.used_percentage
  $dirname = Split-Path $cwd -Leaf

  if ($used) {
      Write-Host "$dirname [$model] ctx: $used%"
  } else {
      Write-Host "$dirname [$model]"
  }
  ```
</CodeGroup>

或者,在安装了 Git Bash 时,直接运行 Bash 脚本:

<CodeGroup>
  ```json settings.json theme={null}
  {
    "statusLine": {
      "type": "command",
      "command": "~/.claude/statusline.sh"
    }
  }
  ```

  ```bash statusline.sh theme={null}
  #!/usr/bin/env bash
  input=$(cat)
  cwd=$(echo "$input" | grep -o '"cwd":"[^"]*"' | cut -d'"' -f4)
  model=$(echo "$input" | grep -o '"display_name":"[^"]*"' | cut -d'"' -f4)
  dirname="${cwd##*[/\\]}"
  echo "$dirname [$model]"
  ```
</CodeGroup>

## 子代理状态行

`subagentStatusLine` 设置会为提示符下方代理面板中显示的每个 [子代理](/docs/en/sub-agents) 渲染自定义行主体。使用它可将默认的 `name · description · token count` 行替换为你自己的格式。

```json theme={null}
{
  "subagentStatusLine": {
    "type": "command",
    "command": "~/.claude/subagent-statusline.sh"
  }
}
```


该命令在每个刷新节拍运行一次，并通过 stdin 接收一个包含所有可见子代理行的单个 JSON 对象。输入包括 [基础钩子字段](/docs/en/hooks#common-input-fields)、一个带有可用行宽度的 `columns` 字段，以及一个 `tasks` 数组。每个任务都有 `id`、`name`、`type`、`status`、`description`、`label`、`startTime`、`model`、`effort`、`contextWindowSize`、`tokenCount`、`tokenSamples` 和 `cwd`。

每个任务的 `model` 字段是该任务运行时解析出的模型 ID。`contextWindowSize` 是该模型的上下文窗口大小（以 token 计），其计算方式与主状态行的 `context_window.context_window_size` 相同，因此你可以从 `tokenCount` 渲染逐行百分比。这两个字段都需要 Claude Code v2.1.205 或更高版本，并且对于模型尚未解析的任务会被省略。

每个任务的 `effort` 字段是为该子代理设置的推理力度，位于其 [定义前置元数据](/docs/en/sub-agents#supported-frontmatter-fields) 中或在单次调用上。该值要么是力度级别字符串 `low`、`medium`、`high`、`xhigh` 或 `max` 之一，要么是数字令牌预算。该字段按所写内容报告配置值：如果模型不支持该级别，实际应用的 Claude Code 力度可能不同。该字段需要 Claude Code v2.1.214 或更高版本，并且 当子代理继承会话的努力级别时，该设置不存在。

对于要覆盖的每一行，向 stdout 写入一行 JSON，格式为 `{"id": "<task id>", "content": "<row body>"}`。`content` 字符串将按原样渲染，包括 ANSI 颜色和 OSC 8 超链接。省略任务的 `id` 可保留该行的默认渲染；输出空的 `content` 字符串则隐藏该行。

适用于 `statusLine` 的相同信任和 `disableAllHooks` 门槛同样适用于此处。插件可以在其 [`settings.json`](/docs/en/plugins-reference#standard-plugin-layout) 中附带一个默认的 `subagentStatusLine`。

## 提示

* **使用模拟输入进行测试**：`echo '{"model":{"display_name":"Opus"},"workspace":{"current_dir":"/home/user/project"},"context_window":{"used_percentage":25},"session_id":"test-session-abc"}' | ./statusline.sh`
* **保持输出简短**：状态栏宽度有限，过长的输出可能会被截断或显示混乱
* **缓存耗时操作**：在活动会话期间脚本会频繁运行，因此像 `git status` 这样的命令可能会导致卡顿。请参阅[缓存示例](#cache-expensive-operations)了解如何处理此问题。

像 [ccstatusline](https://github.com/sirmalloc/ccstatusline) 和 [starship-claude](https://github.com/martinemde/starship-claude) 这样的社区项目提供了带有主题和附加功能的预构建配置。

## 故障排查

**状态栏未显示**

* 确认你的脚本具有可执行权限：`chmod +x ~/.claude/statusline.sh`
* 检查你的脚本输出到 stdout，而不是 stderr
* 手动运行你的脚本以验证它能产生输出
* 在安装了 Git Bash 的 Windows 上，`command` 路径中的反斜杠很可能在脚本运行前被当作转义字符消耗掉了。请在路径中使用正斜杠。参见 [Windows 配置](#windows-configuration)。
* 如果你的设置中 `disableAllHooks` 被设为 `true`，状态栏也会被禁用。移除此设置或将其设为 `false` 以重新启用。
* 运行 `claude --debug` 可记录会话中首次状态栏调用的退出码和 stderr
* 让 Claude 读取你的设置文件并直接执行 `statusLine` 命令以暴露错误

**状态栏显示 `--` 或空值**

* 在首个 API 响应完成之前，字段可能为 `null`
* 在脚本中使用回退值处理 null，例如在 jq 中使用 `// 0`
* 如果多条消息后值仍为空，请重启 Claude Code

**上下文百分比显示异常值**

* 使用 `used_percentage` 可获得最简单且准确的上下文状态
* 由于计算时机不同，上下文百分比可能与 `/context` 的输出不一致

**OSC 8 链接无法点击**

* 确认你的终端支持 OSC 8 超链接（iTerm2、Kitty、WezTerm）

* Terminal.app 不支持可点击链接

* 如果链接文本可见但无法点击，可能是 Claude Code 未检测到你的终端支持超链接。这通常影响 Windows Terminal 及其他不在自动检测列表中的模拟器。在启动 Claude Code 之前设置 `FORCE_HYPERLINK` 环境变量以覆盖检测结果：

  ```bash theme={null}
  FORCE_HYPERLINK=1 claude
  ```

  在 PowerShell 中，先在当前会话中设置该变量：

  ```powershell theme={null}
  $env:FORCE_HYPERLINK = "1"; claude
  ```

* 根据配置不同，SSH 和 tmux 会话可能会剥离 OSC 序列

* 如果转义序列显示为 `\e]8;;` 之类的字面文本，请使用 `printf '%b'` 代替 `echo -e`，以获得更可靠的转义处理

**转义序列导致的显示故障**

* 复杂的转义序列（ANSI 颜色、OSC 8 链接）若与其他 UI 更新重叠，偶尔会导致输出乱码
* 如果看到损坏的文本，请尝试将脚本简化为纯文本输出
* 带转义码的多行状态栏比单行纯文本更容易出现渲染问题

**需要工作区信任**

* 只有当你为当前目录接受了工作区信任对话框后，状态栏命令才会运行。由于 `statusLine` 会执行 shell 命令，它与钩子及其他执行 shell 的设置一样需要信任确认。
* 如果你尚未为此文件夹接受 [工作区信任对话框](/docs/en/security)，状态栏将保持空白，且 `claude --debug` 会记录 `Status line command skipped: workspace trust not accepted`。重启 Claude Code 并接受信任对话框以启用它。

**脚本错误或挂起**

* 以非零退出码退出或不产生输出的脚本会导致状态栏空白
* 缓慢的脚本会阻塞状态栏更新，直到其完成。请保持脚本快速以避免输出过期。
* 如果在慢速脚本运行期间触发了新的更新，正在执行中的脚本会被取消
* 在配置之前，先使用模拟输入独立测试你的脚本

**通知与状态栏共享同一行**

* MCP 服务器错误和自动更新等系统通知会显示在状态栏所在行的右侧。上下文不足警告等临时通知也会在此区域轮换显示。
* 启用详细模式会在此区域添加一个 token 计数器
* 在较窄的终端中，这些通知可能会截断你的状态栏输出

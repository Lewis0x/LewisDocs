---
title: 管理会话
source_id: claude-code/sessions
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/sessions
owner: Anthropic
content_sha256: 1e233018d07944587f6609b9c9be35164334e1c1f0aff29c4fefb719ab1d0ce9
translation_of: claude-code/sessions
translation_model: k3
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/sessions)

Content owner: Anthropic

> ## 文档索引
> 在以下地址获取完整的文档索引：https://code.claude.com/docs/llms.txt
> 使用此文件在进一步探索之前发现所有可用页面。

# 管理会话

> 命名、恢复、分支以及在 Claude Code 对话之间切换。涵盖 `--continue`、`--resume`、`--from-pr`、`/resume` 选择器、会话命名、导出记录以及记录的存储位置。

会话是绑定到项目目录的已保存对话。Claude Code 在你工作时将其保存在本地，因此你可以从中断的地方继续，可以分支尝试不同的方法，或在任务之间切换。

[桌面应用](/docs/en/desktop#work-in-parallel-with-sessions)、[Claude Code网页版](/docs/en/claude-code-on-the-web) 以及 [VS Code 扩展](/docs/en/vs-code#resume-past-conversations) 各自维护自己的会话历史。本页介绍 CLI。

## 恢复会话

会话在你工作时持续保存到[本地记录文件](#export-and-locate-session-data)，因此你可以在退出或运行 `/clear` 之后返回某个会话。使用以下入口：

| 命令                        | 作用                                                                      |
| :-------------------------- | :------------------------------------------------------------------------ |
| `claude --continue`         | 恢复当前目录中最近的会话                                                |
| `claude --resume`           | 打开[会话选择器](#use-the-session-picker)                                |
| `claude --resume <name>`    | 直接恢复指定名称的会话                                                  |
| `claude --from-pr <number>` | 打开会话选择器，筛选出与该拉取请求关联的会话                          |
| `/resume`                   | 从活动会话内部切换到另一个对话                                          |

使用 [`claude -p`](/docs/en/headless) 或 [Agent SDK](/docs/en/agent-sdk/overview) 创建的会话不会出现在会话选择器中，但你仍然可以通过将其会话 ID 传递给 `claude --resume <session-id>` 来恢复它。请从会话启动时所在的目录运行此命令：会话 ID 查找的范围限定为当前项目目录及其 git 工作树，因此在其他地方创建的会话会报告 `No conversation found with session ID: <session-id>`。

### 恢复的会话会还原什么

恢复的会话会还原对话以及保存在其中的状态：

* 对话历史：完整历史，包括工具调用和结果。
* 模型：会话会继续使用它原来使用的模型。如果模型已退役或不被 `availableModels` 允许，或者启动时通过 `--model` 标志或 `ANTHROPIC_MODEL` 系列环境变量指定了模型，或者提供商使用特定于提供商的部署 ID（例如 [Amazon Bedrock、Google Cloud 的 Agent Platform 和 Microsoft Foundry](/docs/en/third-party-integrations)），则不会还原模型；有关解析顺序，请参阅 [模型配置](/docs/en/model-config#setting-your-model)。
* 代理：使用 [`--agent`](/docs/en/sub-agents#invoke-subagents-explicitly) 或 `agent` 设置启动的会话会继续作为该代理运行，并保留其系统提示、工具限制和模型。恢复时传递 `--agent` 可选择不同的代理。{/* min-version: 2.1.216 */}Claude Code 会在两个位置查找代理：会话的原始目录（前提是你已 [信任该工作区](/docs/en/permissions#project-allow-rules-and-workspace-trust)），然后是你从中恢复的目录，因此当你从另一个目录恢复时，项目范围的代理仍会加载。如果 Claude Code 在这两个位置都找不到该代理，会话将使用默认工具和系统提示恢复，并且 显示一个 [警告，指明该代理的名称](/docs/en/errors#session-agent-no-longer-available)。
* 权限模式：会话所处的模式。`plan` 和 `bypassPermissions` 永远不会被恢复；[绕过权限](/docs/en/permission-modes#skip-all-checks-with-bypasspermissions-mode) 必须在启动时通过其启动标志之一或 `permissions.defaultMode: "bypassPermissions"` 在 [设置](/docs/en/settings#permission-settings) 中再次启用。`auto` 仅在您的账户仍满足 [自动模式要求](/docs/en/permission-modes#eliminate-prompts-with-auto-mode) 时才会恢复。传入 `--permission-mode` 可覆盖恢复的模式。
* 活跃目标：会话结束时仍处于活跃状态的 [目标](/docs/en/goal#resume-with-an-active-goal) 会被延续；其轮次计数、计时器和令牌消耗基准将被重置。
* 计划任务：[尚未过期的任务](/docs/en/scheduled-tasks#limitations) 会被恢复。后台 Bash 任务和监控任务不会被恢复。

并非原始启动时的所有配置标志都会被恢复。如果会话依赖于 `--mcp-config`、`--settings`、`--plugin-dir`、`--fallback-model` 或通过 `--add-dir` 添加的目录，请在恢复时再次传入它们；会话中途通过 `/add-dir` 添加的目录也不会被恢复，不过会话选择器仍会使用它们来定位会话。标准设置文件（例如 `settings.json` 和 `settings.local.json`）会在启动时重新读取，因此其中包含的配置无需再次传入。

### 会话选择器的查找位置

Claude Code按项目目录存储会话。默认情况下，会话选择器显示：

* 来自当前工作树的会话，包括[后台会话](/docs/en/agent-view)，它们在列表中标记为`bg`
* 在其他地方启动但通过`/add-dir`添加了当前目录的会话

使用`Ctrl+W`可扩展到仓库的所有工作树，或使用`Ctrl+A`可扩展到本机上的每个项目。

{/* min-version: 2.1.211 */}首个提示是[`/loop`](/docs/en/scheduled-tasks#run-a-prompt-repeatedly-with-%2Floop)命令的会话不会出现在选择器中；在对话后期运行`/loop`不会隐藏该会话。在 v2.1.211 之前，在对话早期运行`/loop`会使该会话从选择器中永久隐藏。

{/* min-version: 2.1.169 */}从 v2.1.169 起，使用[`/cd`](/docs/en/commands)移动会话会将其重新定位到新目录的项目存储中，因此之后会出现在该目录的选择器中。{/* min-version: 2.1.196 */}自 v2.1.196 起，已移动的会话即使在崩溃或强制退出后也不会出现在旧目录的选择器中。在更早的版本中，当旧路径包含特殊字符（如下划线）时，非正常退出后它还可能重新出现在旧目录的列表中。

从同一仓库的另一个工作树中选择会话会在原地恢复它。从不相关项目中选择会话则会将`cd`和恢复命令复制到你的剪贴板。

按名称恢复会在当前仓库及其工作树范围内解析。两种形式都会查找精确匹配并直接恢复，即使它位于不同的工作树中：

| 命令                  | 精确匹配      | 名称有歧义                                                              |
| :----------------------- | :--------------- | :-------------------------------------------------------------------------- |
| `claude --resume <name>` | 直接恢复 | 打开会话选择器，并将该名称预填为搜索词          |
| `/resume <name>`         | 直接恢复 | 报告错误；不带参数运行`/resume`以打开会话选择器 |

## 为你的会话命名

为会话起一个描述性的名称，以便在会话选择器中找到它们，并能按名称恢复。当你并行处理多个任务时，这一点尤为重要。

| 时机                    | 如何设置名称                                                                                                                                                |
| :---------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 启动时              | `claude -n auth-refactor`                                                                                                                                          |
| 会话期间        | `/rename auth-refactor`。该名称还会显示在提示栏上                                                                                                   |
| 在会话选择器中 | 高亮一个会话并按下 `Ctrl+R`                                                                                                                             |
| 接受计划时          | 在 [计划模式](/docs/en/permission-modes#analyze-before-you-edit-with-plan-mode) 中接受计划时，除非你已经设置过名称，否则会根据计划内容为会话命名 |

会话命名后，可使用 `claude --resume <name>` 或 `/resume <name>` 返回它。关于名称解析在多个工作树（worktree）中的行为，请参阅[恢复会话](#resume-a-session)。

{/* min-version: 2.1.196 */}你从未命名过的交互式会话在启动时仍会获得一个默认显示名称。需要 Claude Code v2.1.196 或更高版本。该默认名称由工作目录名称加上一个双字符后缀组成，例如 `my-app-3f`，并用于在运行中会话的列表中标识该会话，比如 [agent 视图](/docs/en/agent-view) 和 `claude agents --json` 输出。

默认名称不是恢复句柄：`claude --resume <name>`、`/resume <name>` 以及会话选择器只匹配你设置的名称。为会话命名会替换默认名称。

如果你没有为会话命名，Claude Code 会为它生成一个会话标题：对你的第一条提示的简短摘要，由发往小型/快速模型（通常是 Haiku 级别的模型）的后台请求生成。使用 `--name` 或 `/rename` 为会话命名会替换生成的标题。在未设置名称时，你会在 [会话选择器](#use-the-session-picker) 和状态栏的 [`session_name`](/docs/en/statusline) 字段中看到生成的标题；与默认显示名称一样，它不是恢复句柄。

## 使用会话选择器

在会话中运行 `/resume`，或不带参数运行 `claude --resume`，即可打开交互式会话选择器。使用这些键盘快捷键来导航、搜索和加宽列表：

| 快捷键                                          | 操作                                                                                                                                                       |
| :------------------------------------------------ | :----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `↑` / `↓`                                         | 在会话之间导航                                                                                                                                    |
| `→` / `←`                                         | 展开或折叠分组的会话                                                                                                                          |
| `Enter`                                           | 恢复高亮显示的会话                                                                                                                               |
| `Space`                                           | 预览会话内容。`Ctrl+V` 在不把它捕获为粘贴的终端上也可用                                                                 |
| `Ctrl+R`                                          | 重命名高亮显示的会话                                                                                                                               |
| `/` 或除 `Space` 以外的任何可打印字符 | 进入搜索模式并筛选会话。粘贴 GitHub、GitHub Enterprise、GitLab 或 Bitbucket 拉取或合并请求 URL，以查找创建它的会话 |
| `Ctrl+A`                                          | 显示此机器上所有项目的会话。再次按下可返回当前仓库                                                             |
| `Ctrl+W`                                          | 显示当前仓库所有工作树的会话。再次按下可返回当前工作树。仅在多工作树仓库中显示         |
| `Ctrl+B`                                          | 筛选为来自当前 git 分支的会话。再次按下可显示所有分支                                                                             |
| `Esc`                                             | 退出会话选择器或搜索模式                                                                                                                       |

每一行会显示会话名称（如果你设置过），否则显示 AI 生成的会话标题、对话摘要或第一条提示，并连同距上次活动的时间、git 分支和文件大小一起显示。用 `Ctrl+A` 加宽到所有项目后，还可查看每个会话的项目路径。

使用 `/branch` 或 `--fork-session` 创建的会话会获得自己的会话 ID，并显示为单独的行。当选择器为同一会话找到多个条目时，会将它们分组到单独一行下。按 `→` 可展开一个分组。

如果 Claude Code 无法加载你从 `claude --resume` 选择器中选择的会话，它会打印 [`Failed to resume the conversation`](/docs/en/errors#failed-to-resume-the-conversation) 并附带一条用于重试的命令，然后以代码 1 退出。在会话内的 `/resume` 选择器中，Claude Code 会报告失败，而你当前的对话会继续运行。

## 分支会话

分支会创建迄今为止对话的副本，并将你切换到该副本中，同时保留原始会话不变。使用它可以在不丢失原有路径的情况下尝试不同的方法。

在会话内部，运行 `/branch`，可附带一个可选名称：

```text theme={null}
/branch try-streaming-approach
```

如果省略名称，Claude Code 会以对话中的第一条提示为新分支命名。自 v2.1.198 起，这一规则同样适用于 [压缩](/docs/en/how-claude-code-works#when-context-fills-up) 之后；早期版本则会回退到字面名称 `Branched conversation`，而不会越过压缩摘要去查找最初的提示。

在命令行中，将 `--continue` 或 `--resume` 与 `--fork-session` 结合使用：

```bash theme={null}
claude --continue --fork-session
```

`/branch` 的确认信息会打印两个会话 ID：你现在所在的新分支和原始会话。原始会话在磁盘上保持不变，并仍保留在会话选择器中；可通过 `/resume <original-name>` 或将其 ID 传给 `/resume` 返回。

`/branch` 会复制转录内容，并将正在运行的 Claude Code 进程切换为写入该副本。这一区别决定了分支会继承什么：

| 状态                                                                                                                                                                    | `/branch` 之后                                                                                                                                                                                                 |
| :----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 对话历史                                                                                                                                                     | 复制到分支中，截至你运行 `/branch` 的时间点                                                                                                                                                        |
| "允许本会话"的权限授予                                                                                                                               | 会延续；分支运行在同一进程中，因此你现有的授权仍然有效。如果使用 `--fork-session` 分叉到单独的进程，新进程启动时没有这些授权，你需要在那里重新批准 |
| 进行中的 [后台子代理](/docs/en/sub-agents#run-subagents-in-foreground-or-background) 和 [后台 Bash 命令](/docs/en/interactive-mode#background-bash-commands) | 继续运行。它们的输出会出现在你切换到的新分支中，而不是原始会话中                                                                                                             |

如果你在两个终端中恢复同一会话而不进行分叉，来自两边的消息会交错进入同一份转录。如需在单个会话内基于检查点回退，请参阅 [检查点](/docs/en/checkpointing)。

## 在会话中管理上下文

这些命令可在不离开会话的情况下控制上下文窗口中的内容：

* **`/clear`**：以空上下文重新开始。Claude Code 会保存之前的对话；可以使用 `/resume` 恢复它，或者在同一个 Claude Code 进程中，{/* min-version: 2.1.191 */}从 [回溯菜单中的上一会话条目](/docs/en/checkpointing#rewind-past-a-cleared-conversation) 恢复。在新对话中会保留你通过 `--name` 或 `/rename` 设置的名称，但不会保留 AI 生成的会话标题
* **`/compact [instructions]`**：用摘要替换历史记录，可选地聚焦于你指定的内容
* **`/context`**：显示当前占用上下文的内容

有关压缩如何与 CLAUDE.md、技能和规则交互的信息，请参阅 [上下文窗口指南](/docs/en/context-window)。有关何时清除与何时压缩的策略，请参阅 [最佳实践](/docs/en/best-practices#manage-your-session)。

## 导出和查找会话数据

运行 `/export` 打开一个菜单，让你可以将当前对话复制到剪贴板或将其保存为纯文本文件，其中消息和工具输出会呈现为可读的文本。传入文件名可跳过菜单并直接写入该文件。

### 从脚本访问对话

`/export` 会生成供人阅读的渲染 transcript。下面的接口会生成供脚本解析的结构化数据：一次运行的 JSON 结果、会话 transcript 文件的路径，或实时流 事件。根据触发脚本的条件来选择：

* **运行 Claude 一次并捕获结果**：调用 `claude -p` 并使用 [`--output-format json` 或 `stream-json`](/docs/en/headless#get-structured-output)，以将非交互式运行的结果、会话 ID、用量和成本捕获为结构化 JSON。
* **向现有会话提问**: 将会话 ID 传递给 [`claude -p --resume`](/docs/en/headless#continue-conversations) 以发送后续提示（例如摘要请求），并捕获结构化响应。
* **响应会话事件**: 读取 `transcript_path` 字段，该字段是 [hooks](/docs/en/hooks#common-input-fields) 和 [status line commands](/docs/en/statusline#available-data) 接收的输入。`SessionEnd` 钩子可以在会话结束时归档对话记录。
* **将 Claude 嵌入 TypeScript 或 Python 应用**: 使用 [Agent SDK](/docs/en/agent-sdk/overview) 以编程方式接收每条消息。

下面的示例使用第二个接口。它向一个现有会话发送后续提示，并使用 `jq` 读取答案：

```bash theme={null}
claude -p --resume <session-id> --output-format json "summarize what we changed" | jq -r '.result'
```

### 对话记录的存储位置

默认情况下,对话记录以 JSONL 格式存储在 `~/.claude/projects/<project>/<session-id>.jsonl`,其中 `<project>` 是你的工作目录路径,非字母数字字符会被替换为 `-`。每一行都是一个 JSON 对象,代表一条消息、一次工具调用或一个元数据条目。该条目格式是 Claude Code 的内部格式,会在版本之间变化,因此直接解析这些文件的脚本在任何版本发布时都可能失效。要基于会话数据进行开发,请改用 `/export` 或 [脚本接口](#access-conversations-from-scripts)。

存储位置、保留时长和写入行为都是可配置的:

| 目的                                        | 设置                                                    | 位置                      |
| ------------------------------------------- | ------------------------------------------------------ | ------------------------- |
| 将存储移出 `~/.claude`                | [`CLAUDE_CONFIG_DIR`](/docs/en/env-vars)                    | 环境变量                  |
| 更改 30 天保留期限                          | [`cleanupPeriodDays`](/docs/en/settings#available-settings) | `settings.json`           |
| 在所有模式下禁止写入对话记录               | [`CLAUDE_CODE_SKIP_PROMPT_HISTORY`](/docs/en/env-vars)      | 环境变量                  |
| 仅对单次非交互运行禁止写入                 | [`--no-session-persistence`](/docs/en/cli-reference)        | 与 `claude -p` 搭配使用的 CLI 标志 |

## 另请参阅

这些页面涵盖相关的会话与并行机制:

* [Worktrees](/docs/en/worktrees): 在独立分支上运行隔离的并行会话
* [Checkpointing](/docs/en/checkpointing): 将代码和对话回退到较早的时间点
* [Context window](/docs/en/context-window): 什么会占用上下文,什么能在压缩后保留
* [Non-interactive mode](/docs/en/headless): `claude -p` 下的会话行为

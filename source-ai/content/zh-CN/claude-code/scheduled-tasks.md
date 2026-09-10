---
title: 按计划运行提示词
source_id: claude-code/scheduled-tasks
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/scheduled-tasks
owner: Anthropic
content_sha256: 52a93b2edf260e6a466fac0a2b94ef822268eee4dadbf230d31626f9166b2310
translation_of: claude-code/scheduled-tasks
translation_model: k3
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/scheduled-tasks)

Content owner: Anthropic

> ## 文档索引
> 在以下地址获取完整的文档索引：https://code.claude.com/docs/llms.txt
> 使用此文件可在进一步探索之前发现所有可用页面。

# 按计划运行提示词

> 使用 /loop 和 cron 调度工具，在 Claude Code 会话中重复运行提示词、轮询状态或设置一次性提醒。

计划任务让 Claude 按时间间隔自动重新运行提示词。用它们来轮询部署、照看 PR、跟进长时间运行的构建，或提醒自己稍后在会话中做某事。如果要在事件发生时做出反应而不是轮询，请参阅 [Channels](/docs/en/channels)：你的 CI 可以直接将失败推送到会话中。如果希望会话一轮接一轮地持续工作直到满足某个条件，而不是按间隔运行，请参阅 [`/goal`](/docs/en/goal)。

任务是会话范围的：它们存在于当前对话中，并在你开始新对话时停止。使用 `--resume` 或 `--continue` 恢复会话时，会带回任何尚未[过期](#seven-day-expiry)的任务：即在过去 7 天内创建的重复任务，或计划时间尚未过去的一次性任务。如需独立于任何会话而存在的调度，请使用 [Routines](/docs/en/routines) 在 Anthropic 管理的基础设施上创建例程，设置 [Desktop 计划任务](/docs/en/desktop-scheduled-tasks)，或使用 [GitHub Actions](/docs/en/github-actions)。

## 比较调度选项

Claude Code 提供三种方式来调度重复或一次性的工作：

|                            | [Cloud](/docs/en/routines)          | [Desktop](/docs/en/desktop-scheduled-tasks) | [`/loop`](/docs/en/scheduled-tasks)      |
| :------------------------- | :----------------------------- | :------------------------------------- | :---------------------------------- |
| 运行位置                    | Anthropic 云端                | 你的机器                           | 你的机器                        |
| 需要机器开机        | 否                             | 是                                    | 是                                 |
| 需要打开的会话      | 否                             | 否                                     | 是                                 |
| 重启后持久保留 | 是                            | 是                                    | 如果未过期，在 `--resume` 时恢复 |
| 访问本地文件      | 否（全新克隆）               | 是                                    | 是                                 |
| MCP 服务器                | 按任务配置的连接器 | [配置文件](/docs/en/mcp)和连接器 | 继承自会话               |
| 权限提示         | 无（自主运行）         | 可按任务配置                  | 继承自会话               |
| 可自定义的计划      | 通过 CLI 中的 `/schedule`     | 是                                    | 是                                 |
| 最小间隔           | 1 小时                         | 1 分钟                               | 1 分钟                            |

<Tip>
  对于应当在不依赖你的机器的情况下可靠运行的工作，使用**云任务**。当需要访问本地文件和工具时，使用 **Desktop 任务**。在会话期间进行快速轮询时，使用 **`/loop`**。
</Tip>

## 使用 /loop 重复运行提示

当会话保持打开时，`/loop` [捆绑技能](/docs/en/commands) 是重复运行提示的最快方式。间隔和提示都是可选的，你提供的内容决定了循环的行为方式。

| 你提供的内容          | 示例                     | 会发生什么                                                                                                  |
| :------------------------ | :-------------------------- | :------------------------------------------------------------------------------------------------------------ |
| 间隔和提示       | `/loop 5m check the deploy` | 你的提示按 [固定计划](#run-on-a-fixed-interval) 运行                                              |
| 仅提示               | `/loop check the deploy`    | 你的提示按每次迭代时 [Claude 选择的间隔](#let-claude-choose-the-interval) 运行              |
| 仅间隔，或都不提供 | `/loop`                     | 运行 [内置维护提示](#run-the-built-in-maintenance-prompt)，或运行你的 `loop.md`（如果存在） |

你也可以将技能作为提示传入，例如 `/loop 20m /review-pr 1234`，以便每次迭代重新运行该技能。{/* min-version: 2.1.196 */}从 v2.1.196 起，计划触发只会运行 Claude [被允许自行调用](/docs/en/skills#control-who-invokes-a-skill) 的技能。以下内容会以纯文本形式传给 Claude，而不会执行：

* 内置命令，例如 `/permissions`、`/model` 或 `/clear`
* 标记为 [`disable-model-invocation: true`](/docs/en/skills#frontmatter-reference) 的技能，包括捆绑的 `/verify` 和 `/code-review` 技能。
* 因 [`skillOverrides`](/docs/en/skills#override-skill-visibility-from-settings) 设置或 `Skill` [deny 规则](/docs/en/skills#restrict-claude’s-skill-access) 而对 Claude 隐藏的技能
* [MCP 提示](/docs/en/mcp#use-mcp-prompts-as-commands)，例如 `/mcp__github__list_prs`

### 按固定间隔运行

当你提供间隔时，Claude 会将其转换为 cron 表达式，调度任务，并确认运行频率和任务 ID。

```text theme={null}
/loop 5m check if the deployment finished and tell me what happened
```

间隔可以作为裸标记（如 `30m`）放在提示之前，也可以作为子句（如 `every 2 hours`）跟在提示之后。支持的单位有：`s` 表示秒，`m` 表示分钟，`h` 表示小时，`d` 表示天。

由于 cron 的粒度为一分钟，秒数会向上取整到最近的分钟。无法映射为整洁 cron 步长的间隔（例如 `7m` 或 `90m`）会被取整到最近的可映射间隔，Claude 会告诉你它选择了哪个值。

### 让 Claude 选择间隔

当你省略间隔时，Claude 会动态选择一个间隔，而不是按固定 cron 计划运行。每次迭代后，它会根据观察到的情况在一分钟到一小时之间选择一个延迟：当构建即将完成或 PR 处于活跃状态时等待较短，没有待处理事项时等待较长。所选延迟及其原因会在每次迭代结束时打印出来。

下面的示例检查 CI 和评审评论，当 PR 安静下来后，Claude 会在迭代之间等待更长时间：

```text theme={null}
/loop check whether CI passed and address any review comments
```

当你请求动态的 `/loop` 计划时，Claude 可能会直接使用 [Monitor 工具](/docs/en/tools-reference#monitor-tool)。Monitor 运行一个后台脚本并将每行输出流式传回，这完全避免了轮询，通常比按间隔重新运行提示更节省 token 且响应更快。

动态调度的循环会像其他任务一样出现在你的 [计划任务列表](#manage-scheduled-tasks) 中，因此你可以用同样的方式列出或取消它。[抖动规则](#jitter) 对它不适用，但 [七天过期](#seven-day-expiry) 适用：循环会在你启动七天后自动结束。

<Note>
  在 Amazon Bedrock、AWS 上的 Claude Platform、Google Cloud 的 Agent Platform 和 Microsoft Foundry 上，不带间隔的提示会改为按固定的 10 分钟计划运行。
</Note>

### 运行内置的维护提示

当你省略提示时，Claude 会使用内置的维护提示，而不是你提供的提示。在每次迭代中，它会按顺序依次处理以下事项：

* 继续对话中任何未完成的工作
* 处理当前分支的拉取请求：评审评论、失败的 CI 运行、合并冲突
* 在没有其他待处理事项时，运行清理工作，例如查找 bug 或简化代码

Claude 不会在该范围之外启动新的工作项，并且推送或删除等不可逆操作只有在延续对话记录中已授权的事项时才会执行。

```text theme={null}
/loop
```

不带参数的 `/loop` 会以[动态选择的时间间隔](#let-claude-choose-the-interval)运行此提示。添加一个时间间隔，例如 `/loop 15m`，即可改为按固定计划运行。若要用你自己的默认提示替换内置提示，请参阅[使用 loop.md](#customize-the-default-prompt-with-loop-md)自定义默认提示。

<Note>
  在 Amazon Bedrock、AWS 上的 Claude 平台、Google Cloud 的 Agent 平台和 Microsoft Foundry 上，不带提示的 `/loop` 会打印用法信息，而不是运行维护提示。
</Note>

### 使用 loop.md 自定义默认提示词

`loop.md` 文件会用你自己的指令替换内置的维护提示词。它为不带参数的 `/loop` 定义单一的默认提示词，而不是一份独立的计划任务列表，并且只要你在命令行中提供了提示词，该文件就会被忽略。若要在此基础上安排额外的提示词，请使用 `/loop <prompt>` 或 [直接询问 Claude](#manage-scheduled-tasks)。

Claude 会在两个位置查找该文件，并使用找到的第一个。

| 路径                | 作用范围                                                            |
| :------------------ | :--------------------------------------------------------------- |
| `.claude/loop.md`   | 项目级别。当两个文件都存在时优先使用。           |
| `~/.claude/loop.md` | 用户级别。适用于任何未定义自己文件的项目。 |

该文件是纯 Markdown，没有必需的结构。就像直接输入 `/loop` 提示词一样编写它。下面的示例用于保持发布分支的健康：

```markdown title=".claude/loop.md" theme={null}
Check the `release/next` PR. If CI is red, pull the failing job log,
diagnose, and push a minimal fix. If new review comments have arrived,
address each one and resolve the thread. If everything is green and
quiet, say so in one line.
```

对 `loop.md` 的编辑会在下一次迭代时生效，因此你可以在循环运行期间优化指令。当两个位置都不存在 `loop.md` 时，循环会回退到内置的维护提示词。请保持文件简洁：超过 25,000 字节的内容会被截断。

<Note>
  在 Amazon Bedrock、AWS 上的 Claude Platform、Google Cloud 的 Agent Platform 以及 Microsoft Foundry 上，`loop.md` 不会被读取，且不带提示词的 `/loop` 会改为打印用法信息。
</Note>

### 停止循环

要在`/loop`等待下一次迭代时将其停止，请按`Esc`。这会清除待处理的唤醒，使循环不会再次触发。你通过[直接询问 Claude](#manage-scheduled-tasks)安排的任务不受`Esc`影响，并会一直保留到你删除它们。

在[自定步调模式](#let-claude-choose-the-interval)中，Claude 也可以在任务完成后自行结束循环。Claude 会调用[`ScheduleWakeup`工具](/docs/en/tools-reference)并传入`stop: true`，立即取消待处理的唤醒。如果某次迭代结束时既没有重新安排也没有停止，Claude Code会安排一个约 20 分钟后的兜底唤醒，并在该次迭代仍未重新安排时结束循环。在 v2.1.202 之前，不重新安排是 Claude 能自行结束循环的唯一方式。

固定间隔的循环会一直运行，直到你停止它们，或[七天流逝](#seven-day-expiry)。

## 设置一次性提醒

对于一次性提醒，请用自然语言描述您想要的内容，而不是使用 `/loop`。Claude 会安排一个单次触发的任务，该任务在运行后会自行删除。

```text theme={null}
remind me at 3pm to push the release branch
```

```text theme={null}
in 45 minutes, check whether the integration tests passed
```

Claude 使用 cron 表达式将触发时间固定到特定的分钟和小时，并确认触发时间。

## 管理定时任务

用自然语言要求 Claude 列出或取消任务，或者直接引用底层工具。

```text theme={null}
what scheduled tasks do I have?
```

```text theme={null}
cancel the deploy check job
```

在底层，Claude 使用以下工具：

| 工具         | 用途                                                                                                         |
| :----------- | :-------------------------------------------------------------------------------------------------------------- |
| `CronCreate` | 安排一个新任务。接受 5 个字段的 cron 表达式、要运行的提示，以及是重复执行还是仅触发一次。 |
| `CronList`   | 列出所有定时任务及其 ID、计划和提示。                                                |
| `CronDelete` | 按 ID 取消任务。                                                                                            |

每个定时任务都有一个 8 字符的 ID，您可以将其传递给 `CronDelete`。一个会话最多可以同时容纳 50 个定时任务。

## 定时任务如何运行

调度器每秒检查一次到期任务，并以低优先级将其加入队列。定时提示在您的回合之间触发，而不是在 Claude 正在回复时触发。如果任务到期时 Claude 正忙，提示会等待当前回合结束。

所有时间都按您的本地时区解释。像 `0 9 * * *` 这样的 cron 表达式表示您运行 Claude Code 所在地的上午 9 点，而不是 UTC。

### 抖动

为避免所有会话在同一时钟时刻同时请求 API，调度器会为触发时间添加一个确定性偏移：

* 重复任务最多可能比计划时间晚 30 分钟触发（对于运行频率高于每小时的任务，最多为间隔的一半）。计划在 `:00` 运行的每小时任务可能在直到 `:30` 之间的任何时间触发。
* 计划在整点或半点的一次性任务最多可能提前 90 秒触发。

偏移量源自任务 ID，因此同一任务总是获得相同的偏移。如果精确时间很重要，请选择不是 `:00` 或 `:30` 的分钟，例如用 `3 9 * * *` 代替 `0 9 * * *`，这样一次性抖动就不会适用。

### 七天过期

重复任务会在创建 7 天后自动过期。任务会最后触发一次，然后自行删除。这限制了被遗忘的循环可以运行的时长。如果您需要重复任务持续更长时间，请在过期前取消并重新创建它，或者使用 [Routines](/docs/en/routines) 或 [Desktop scheduled tasks](/docs/en/desktop-scheduled-tasks) 进行持久化调度。

## Cron 表达式参考

`CronCreate` 接受标准的 5 字段 cron 表达式：`minute hour day-of-month month day-of-week`。所有字段都支持通配符（`*`）、单个值（`5`）、步长（`*/15`）、范围（`1-5`）和逗号分隔列表（`1,15,30`）。

| 示例        | 含义                      |
| :------------- | :--------------------------- |
| `*/5 * * * *`  | 每 5 分钟              |
| `0 * * * *`    | 每小时整点       |
| `7 * * * *`    | 每小时的第 7 分钟 |
| `0 9 * * *`    | 每天当地时间上午 9 点       |
| `0 9 * * 1-5`  | 工作日当地时间上午 9 点        |
| `30 14 15 3 *` | 3 月 15 日当地时间下午 2:30     |

星期字段使用 `0` 或 `7` 表示星期日，到 `6` 表示星期六。不支持 `L`、`W`、`?` 等扩展语法，也不支持 `MON` 或 `JAN` 等名称别名。

当日期（day-of-month）和星期（day-of-week）两个字段同时被约束时，只要任一字段匹配，日期即匹配。这遵循标准的 vixie-cron 语义。

## 禁用计划任务

在环境中设置 `CLAUDE_CODE_DISABLE_CRON=1` 可完全禁用调度器。cron 工具和 `/loop` 将不可用，任何已安排的任务也会停止触发。有关禁用标志的完整列表，请参阅 [环境变量](/docs/en/env-vars)。

## 限制

会话范围的调度存在固有约束：

* 任务仅在 Claude Code 运行且空闲时触发。关闭终端或让会话退出会停止任务触发。[将会话转入后台](/docs/en/agent-view#from-inside-a-session) 会将 `/loop` 任务转移到后台会话，该会话在没有终端的情况下继续运行。
* 错过的触发不会补发。如果任务的计划时间在 Claude 忙于长时间运行的请求期间过去，它只会在 Claude 空闲时触发一次，而不是每个错过的间隔各触发一次。
* 开始新对话会清除所有会话范围的任务。使用 `claude --resume` 或 `claude --continue` 恢复会话时，会还原尚未过期的任务：创建后七天内的周期性任务，以及计划时间尚未到达的一次性任务。后台 Bash 和监控任务在恢复时永远不会被还原。
* {/* min-version: 2.1.216 */}Claude Code 将计划任务列表存储在项目的 `.claude` 目录中，当该目录或其中的任务文件是符号链接时，调度任务会失败并报错。在 v2.1.216 之前，Claude Code 会通过链接写入文件。

对于需要无人值守运行的 cron 驱动自动化：

* [Routines](/docs/en/routines)：按计划、通过 API 调用或在 GitHub 事件时运行在 Anthropic 管理的基础设施上
* [GitHub Actions](/docs/en/github-actions)：在 CI 中使用 `schedule` 触发器
* [桌面计划任务](/docs/en/desktop-scheduled-tasks)：在您的本地机器上运行

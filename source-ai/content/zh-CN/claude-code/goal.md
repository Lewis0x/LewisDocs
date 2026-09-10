---
title: 让 Claude 持续朝目标工作
source_id: claude-code/goal
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/goal
owner: Anthropic
content_sha256: 56a76edc6bf3e8e52f184385c7223a075d520b0565ad8a3eb5b07d04b811e076
translation_of: claude-code/goal
translation_model: gpt-5.6
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/goal)

Content owner: Anthropic

> ## 文档索引
> 完整的文档索引位于：https://code.claude.com/docs/llms.txt
> 在进一步探索之前，可使用此文件发现所有可用页面。

# 让 Claude 持续朝目标工作

> 使用 /goal 设置完成条件，Claude 就会跨多个轮次持续工作，直到满足该条件。

<Note>
  `/goal` 需要 Claude Code v2.1.139 或更高版本。
</Note>

`/goal` 命令用于设置完成条件；Claude 会持续朝该条件工作，无需你为每一步发送提示。每个轮次结束后，一个小型快速模型会检查条件是否成立。如果不成立，Claude 会启动下一轮，而不是将控制权交还给你。满足条件后，目标会自动清除。

目标适用于具有可验证结束状态的大型工作：

* 将模块迁移到新 API，直到每个调用点都能编译且测试通过
* 实现设计文档，直到满足所有验收标准
* 将大型文件拆分为职责集中的模块，直到每个模块都低于大小预算
* 处理带标签的问题积压，直到队列为空

## 比较让会话持续运行的方式

有三种方法可以让当前会话在提示之间持续运行。应根据什么事件触发下一轮来选择：

| 方法                                                            | 下一轮开始时机      | 停止时机                                      |
| :------------------------------------------------------------------ | :------------------------- | :---------------------------------------------- |
| `/goal`                                                             | 上一轮结束时 | 模型确认条件已满足           |
| [`/loop`](/docs/en/scheduled-tasks#run-a-prompt-repeatedly-with-%2Floop) | 经过一个时间间隔时    | 你将其停止，或 Claude 认定工作已完成 |
| [Stop hook](/docs/en/hooks-guide#prompt-based-hooks)                     | 上一轮结束时 | 由你自己的脚本或提示决定               |

`/goal` 和 Stop hook 都会在每轮结束后触发。`/goal` 是会话范围的快捷方式：输入一个条件，它就只在当前会话中生效。Stop hook 位于设置文件中，会应用于其作用域内的每个会话，并且可以运行脚本来进行确定性检查，也可以运行提示来交由模型评估。

[Auto 模式](/docs/en/auto-mode-config)本身只会批准单个轮次中的工具调用，不会启动新轮次。当 Claude 判断工作完成时，它就会停止。`/goal` 增加了一个单独的评估器，在每个轮次后检查你的条件，因此完成与否由一个全新的模型决定，而不是由执行工作的模型决定。两者相辅相成：Auto 模式移除每次工具调用的提示，而 `/goal` 移除每个轮次之间的提示。

<Tip>
  上述方法都让当前会话持续运行。你也可以安排独立于任何已打开会话的工作，例如夜间测试或晨间分类处理。有关云端 routines 和桌面计划任务，请参阅[计划选项](/docs/en/scheduled-tasks#compare-scheduling-options)。
</Tip>

## 使用 `/goal`

每个会话可以有一个活动目标。根据参数的不同，同一命令可用于设置、检查和清除目标。

### 设置目标

运行 `/goal`，后面跟上你希望满足的条件。如果已有活动目标，新目标会将其替换。

```text theme={null}
/goal all tests in test/auth pass and the lint step is clean
```

设置目标会立即启动一个轮次，并将条件本身作为指令。你不需要再发送单独的提示。目标处于活动状态时，`◎ /goal active` 指示器会显示目标已运行的时长。

目标不会改变权限。在默认权限模式下，对于设置尚未允许的工具调用（例如上面的测试命令），Claude 仍会事先询问。若要让目标轮次无人值守地运行，请将 `/goal` 与 [Auto 模式](/docs/en/auto-mode-config)配合使用。

每轮结束后，评估器都会返回一条简短理由，说明条件为何已经满足或尚未满足。最新理由会显示在状态视图和会话记录中，供你了解 Claude 下一步正在朝什么方向工作。

<Note>
  目标会一直运行，直到满足条件或你运行 `/goal clear`。不带参数运行 `/goal`，可查看目前消耗的轮次数和令牌数。
</Note>

### 编写有效的条件

[评估器](#how-evaluation-works)会根据 Claude 已在对话中呈现的内容判断你的条件。它不会独立运行命令或读取文件，因此条件应写成可由 Claude 自身输出证明的形式。“`test/auth` 中的所有测试都通过”是有效条件，因为 Claude 会运行这些测试，而结果会出现在会话记录中，供评估器读取。

能够经受多个轮次检验的条件通常包含：

* **一个可衡量的结束状态**：测试结果、构建退出代码、文件数量或空队列
* **明确的检查方式**：Claude 应如何证明结果，例如“`npm test` 以 0 退出”或“`git status` 干净”
* **重要的约束**：执行过程中不得发生的变化，例如“不得修改任何其他测试文件”

条件最长可达 4,000 个字符。

若要限制目标的运行时长，可在条件中加入轮次或时间条款，例如 `or stop after 20 turns`。Claude 会在每轮中报告相对于该条款的进度，评估器则根据对话进行判断。

### 检查状态

不带参数运行 `/goal`，可查看当前状态。

```text theme={null}
/goal
```

如果目标处于活动状态，状态会显示：

* 条件
* 已运行时长
* 已评估的轮次数
* 当前令牌消耗量
* 评估器给出的最新理由

首次评估运行后，才会显示轮次计数和最新理由。

如果没有活动目标，但当前会话中此前有目标已达成，状态会显示已达成的条件及其持续时间、轮次计数和令牌消耗量。

### 清除目标

在满足条件前运行 `/goal clear`，可移除活动目标。

```text theme={null}
/goal clear
```

Claude 会输出 `Goal cleared:`，后面跟上条件，以确认清除；如果没有活动目标，则输出 `No goal set`。

`stop`、`off`、`reset`、`none` 和 `cancel` 都可作为 `clear` 的别名。运行 `/clear` 开始新对话也会移除所有活动目标。

### 恢复带有活动目标的会话

如果会话结束时目标仍处于活动状态，那么使用 `--resume` 或 `--continue` 恢复该会话时，目标也会恢复。条件会保留，但轮次计数、计时器和令牌消耗基线都会在恢复时重置。已经达成或清除的目标不会恢复。

### 以非交互方式运行

`/goal` 可用于[非交互模式](/docs/en/headless)、[桌面应用](/docs/en/desktop)，也可通过[远程控制](/docs/en/remote-control)使用。使用 `-p` 设置目标，会在一次调用中运行循环直至完成：

```bash theme={null}
claude -p "/goal CHANGELOG.md has an entry for every PR merged this week"
```

使用默认文本输出时，在满足条件前不会输出任何内容，因此运行多个轮次的目标看起来可能像是卡住了。添加 `--output-format stream-json --verbose` 可在循环运行时逐条输出消息。

按 Ctrl+C 可在条件满足前中断进程，停止非交互目标。

## 评估的工作原理

`/goal` 是对会话范围[基于提示的 Stop hook](/docs/en/hooks#prompt-based-hooks)的封装。每当 Claude 完成一个轮次，条件和截至当前的对话都会发送给你所配置的[小型快速模型](/docs/en/model-config)，默认模型为 Haiku。该模型会返回“是”或“否”的决定以及一条简短理由。“否”会让 Claude 继续工作，并将理由作为下一轮的指导；“是”则会清除目标，并在会话记录中记下一条已达成记录。

评估器在会话所配置的提供商上运行。它不会调用工具，因此只能根据 Claude 已在对话中呈现的内容进行判断。

<Note>
  评估令牌按提供商所配置的小型快速模型计费，与主要轮次的消耗相比通常可以忽略不计。
</Note>

## 要求

`/goal` 只能在你已接受信任对话框的工作区中运行，因为评估器属于 hook 系统。在以下情况下，`/goal` 也不可用：在任一设置层级设定了 [`disableAllHooks`](/docs/en/hooks#disable-or-remove-hooks)，或在托管设置中设定了 [`allowManagedHooksOnly`](/docs/en/settings#hook-configuration)。每种情况下，命令都会说明原因，而不会静默地不执行任何操作。

## 另请参阅

* [使用 `/loop` 重复运行提示](/docs/en/scheduled-tasks#run-a-prompt-repeatedly-with-%2Floop)：按时间间隔重新运行，而不是持续运行到条件成立
* [基于提示的 hook](/docs/en/hooks-guide#prompt-based-hooks)：需要自定义评估逻辑时，编写自己的 Stop hook
* [Auto 模式](/docs/en/auto-mode-config)：自动批准工具调用，使每个目标轮次都能无人值守地运行
* [计划方式比较](/docs/en/scheduled-tasks#compare-scheduling-options)：按计划运行工作，不依赖任何已打开的会话

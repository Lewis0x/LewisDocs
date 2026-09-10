---
title: 在 Claude Code Desktop 中安排重复任务
source_id: claude-code/desktop-scheduled-tasks
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/desktop-scheduled-tasks
owner: Anthropic
content_sha256: 082e005d0ce6445b6d59bf5f78a72f37621fdc9a2822b446a20c84a60eaae8ff
translation_of: claude-code/desktop-scheduled-tasks
translation_model: gpt-5.6
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/desktop-scheduled-tasks)

Content owner: Anthropic

> ## 文档索引
> 在以下地址获取完整的文档索引：https://code.claude.com/docs/llms.txt
> 使用此文件可在深入探索之前发现所有可用页面。

# 在 Claude Code Desktop 中安排重复任务

> 在 Claude Code Desktop 中设置计划任务，让 Claude 按固定周期自动运行，以执行每日代码审查、依赖项审计或晨间简报。

计划任务会按照你选择的时间和频率自动启动新会话。可将其用于每日代码审查、依赖项更新检查，或从日历和收件箱提取信息的晨间简报等重复工作。

桌面应用的 **Routines** 页面允许你创建本地计划任务和远程[例行任务](/docs/en/routines)。本地任务在你的机器上运行，可以直接访问文件和工具，但只有应用处于打开状态且计算机未休眠时才会触发。即使计算机已经关闭，远程例行任务也会在 Anthropic 管理的云基础设施上运行，还可以由 API 调用或 GitHub 事件触发。本页面介绍本地计划任务；有关远程例行任务及其触发选项，请参阅 [Routines](/docs/en/routines)。

## 比较计划选项

Claude Code 提供三种安排重复或一次性工作的方式：

| | [云端](/docs/en/routines) | [Desktop](/docs/en/desktop-scheduled-tasks) | [`/loop`](/docs/en/scheduled-tasks) |
| :--- | :--- | :--- | :--- |
| 运行位置 | Anthropic 云端 | 你的机器 | 你的机器 |
| 要求机器开机 | 否 | 是 | 是 |
| 要求会话打开 | 否 | 否 | 是 |
| 重启后仍然存在 | 是 | 是 | 如果未过期，会在 `--resume` 时恢复 |
| 访问本地文件 | 否（全新克隆） | 是 | 是 |
| MCP 服务器 | 按任务配置的连接器 | [配置文件](/docs/en/mcp)和连接器 | 从会话继承 |
| 权限提示 | 无（自主运行） | 按任务配置 | 从会话继承 |
| 可自定义计划 | 通过 CLI 中的 `/schedule` | 是 | 是 |
| 最短间隔 | 1 小时 | 1 分钟 | 1 分钟 |

<Tip>
  对于即使机器未运行也应可靠执行的工作，请使用**云端任务**。需要访问本地文件和工具时，请使用 **Desktop 任务**。需要在会话中快速轮询时，请使用 **`/loop`**。
</Tip>

<Note>
  默认情况下，计划任务会针对工作目录的当前状态运行，包括未提交的更改。创建任务时启用 worktree 开关，可为每次运行提供各自隔离的 Git worktree，其工作方式与[并行会话](/docs/en/desktop#work-in-parallel-with-sessions)相同。
</Note>

## 创建计划任务

点击侧边栏中的 **Routines**，然后点击 **New routine** 并选择 **Local**。配置以下字段：

| 字段 | 说明 |
| --- | --- |
| Name | 任务的标识符。它会转换为小写 kebab-case，并用作磁盘上的文件夹名称。在你的所有任务中必须唯一。 |
| Description | 任务列表中显示的简短摘要。 |
| Instructions | 任务运行时 Claude 应执行的操作。编写方式与在提示框中编写任何消息相同。说明输入区包含权限模式和模型选择器；其下方可选择工作文件夹，以及是否在隔离的 worktree 中运行。 |
| Schedule | 任务运行频率。请参阅下文的[计划选项](#schedule-options)。 |

保存任务前必须指定文件夹。如果你尚未信任该文件夹，Desktop 会在保存前提示你信任它。

你也可以通过在任意会话中描述需求来创建任务。例如，“设置一个每天早上 9 点运行的每日代码审查”会创建重复任务，而“明天下午 3 点提醒我检查部署”会创建触发后自行禁用的一次性任务。

## 计划选项

从 Schedule 控件中选择一个预设：

* **Manual**：无计划，仅在点击 **Run now** 时运行。适合保存按需触发的提示词
* **Hourly**：每小时运行
* **Daily**：显示时间选择器，默认为当地时间上午 9:00
* **Weekdays**：与 Daily 相同，但跳过周六和周日
* **Weekly**：显示时间选择器和星期选择器

对于选择器未提供的间隔，例如每 15 分钟、每月第一天，或在未来特定时间运行一次，请在任意 Desktop 会话中让 Claude 设置计划。请使用自然语言，例如“安排一个每 6 小时运行所有测试的任务”。

## 计划任务如何运行

计划任务在你的机器上运行。应用打开时，Desktop 每分钟检查一次计划，并在任务到期时启动全新会话，与当前打开的任何手动会话无关。每项任务在计划时间后都会有几分钟的小幅延迟，以错开 API 流量。延迟是确定性的：同一任务始终以相同的偏移量启动。

任务触发时，你会收到桌面通知，侧边栏的 **Scheduled** 部分下会出现新会话。打开它可以查看 Claude 执行的内容、审查更改或响应权限提示。该会话的工作方式与其他会话相同：Claude 可以编辑文件、运行命令、创建提交和打开拉取请求。

任务只会在桌面应用正在运行且计算机处于唤醒状态时运行。如果计算机在计划时间处于休眠状态，该次运行会被跳过。若要防止空闲休眠，请在 Settings 的 **Desktop app → General** 下启用 **Keep computer awake**。合上笔记本电脑上盖仍会使其休眠。对于需要在计算机关闭时仍然运行，或应由 API 调用或 GitHub 事件触发的任务，请改为创建远程[例行任务](/docs/en/routines)。

## 错过的运行

应用启动或计算机唤醒时，Desktop 会检查每项任务在过去七天内是否错过任何运行。如果有，它会只针对最近错过的时间启动一次补偿运行，并丢弃更早的所有运行。错过六天的每日任务在唤醒时只运行一次。补偿运行开始时，Desktop 会显示通知。

编写提示词时请记住这一点。如果计算机整天处于休眠状态，原定上午 9 点运行的任务可能在晚上 11 点才执行。如果时间很重要，请在提示词本身加入约束，例如：“只审查今天的提交。如果已经过了下午 5 点，请跳过审查，只发布一份错过内容的摘要。”

## 计划任务的权限

每项任务都有自己的权限模式，你可以在创建或编辑任务时设置。`~/.claude/settings.json` 中的允许规则也适用于计划任务会话。如果任务在[手动模式](/docs/en/desktop#choose-a-permission-mode)下运行，并且需要运行没有权限的工具，该次运行会停滞，直到你批准。会话会留在侧边栏中，以便你稍后响应。

为避免停滞，请在创建任务后点击 **Run now**，留意权限提示，并为每项提示选择“always allow”。该任务今后的运行会自动批准相同工具，不再提示。你可以从任务详情页面审查并撤销这些批准。

你的组织[设置为 `ask` 的连接器工具](/docs/en/mcp#organization-controls-on-connector-tools)，以及标有 [`requiresUserInteraction`](/docs/en/mcp#require-approval-for-a-specific-tool) 的 MCP 工具，每次调用都会提示，并且不提供始终允许选项。调用这些工具的运行每次都会停滞。

## 管理计划任务

点击 **Routines** 列表中的任务，打开其详情页面。你可以在此处：

* **Run now**：立即启动任务，无需等待下一个计划时间
* **Status**：在 Active 与 Paused 之间切换，以暂停或恢复计划运行，而无需删除任务
* **Edit**：更改说明、计划、文件夹或其他设置
* **Review history**：查看过去的每次运行，包括跳过的运行。将鼠标悬停在跳过的条目上可查看原因：计算机处于休眠状态、上一次运行仍在进行，或其他计划任务已在运行。点击 **Show more** 可加载更早的条目。
* **Review allowed permissions**：从 **Always allowed** 面板查看和撤销为该任务保存的工具批准
* **Delete**：移除任务，并归档它创建的所有会话。确认对话框中会显示 **Also delete files on disk** 复选框；勾选后还会移除任务的 `SKILL.md` 文件和 `~/.claude/scheduled-tasks/` 中的相关数据。

你也可以在任意 Desktop 会话中让 Claude 列出、创建、编辑和暂停任务。例如，“暂停我的 dependency-audit 任务”或“显示我的计划任务”。若要删除任务，请使用其详情页面上的 **Delete** 按钮。

计划任务还可以在运行中的会话内使用 `update_scheduled_task` MCP 工具修改自己的计划或提示词。这让任务可以根据发现重新安排自身，例如检测到已创建发布分支时，将代码审查重新安排到更早时间运行。

若要在磁盘上编辑任务的提示词，请打开 `~/.claude/scheduled-tasks/<task-name>/SKILL.md`（如果设置了 [`CLAUDE_CONFIG_DIR`](/docs/en/env-vars)，则位于该目录下）。该文件使用 YAML frontmatter 存放 `name` 和 `description`，正文则是提示词。更改会在下次运行时生效。计划、文件夹、模型和启用状态不在此文件中：请通过 Edit 表单更改它们，或让 Claude 更改。

## 相关资源

* [Routines](/docs/en/routines)：即使计算机已关闭，也能按照计划、通过 API 调用或响应 GitHub 事件，在 Anthropic 管理的基础设施上运行任务
* [按计划运行提示词](/docs/en/scheduled-tasks)：在 CLI 中使用 `/loop` 进行会话作用域的计划安排
* [Claude Code GitHub Actions](/docs/en/github-actions)：在 CI 中而不是你的机器上按计划运行 Claude
* [使用 Claude Code Desktop](/docs/en/desktop)：完整的 Desktop 应用指南

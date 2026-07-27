---
title: 创建自定义子代理
source_id: claude-code/subagents
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/sub-agents
owner: Anthropic
content_sha256: e23dc2afb5dfd1c48e305a77b7d787080afa818f5f560ece265c45a7057ca118
translation_of: claude-code/subagents
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/sub-agents)

Content owner: Anthropic

> ## 文档索引
> 在以下位置获取完整的文档索引：https://code.claude.com/docs/llms.txt
> 在进一步探索之前，请使用此文件来发现所有可用页面。

# 创建自定义子代理

> 在 Claude Code 中创建和使用专门的 AI 子代理，以实现针对特定任务的工作流和改进的上下文管理。

子代理是处理特定类型任务的专门 AI 助手。当某个附带任务可能产生大量搜索结果、日志或文件内容，导致您的主对话不堪重负，且这些内容您不会再引用时，请使用子代理：子代理会在其自己的上下文中完成该工作，并仅返回摘要。当您不断使用相同的指令生成同一类工作者时，就可以定义一个自定义子代理。

每个子代理都在其自己的上下文窗口中运行，并配有自定义的系统提示、特定的工具访问权限和独立的权限。当 Claude 遇到与某个子代理描述相匹配的任务时，它会将该任务委派给该子代理，由子代理独立工作并返回结果。要了解上下文节省的实际效果，[上下文窗口可视化](/docs/en/context-window) 将带您浏览一个由子代理在其独立窗口中处理研究的会话。

<Note>
  子代理在单个会话内工作。要并行运行多个独立的会话并从一个地方进行监控，请参阅 [后台代理](/docs/en/agent-view)。对于需要相互通信的会话，请参阅 [代理团队](/docs/en/agent-teams)。
</Note>

子代理可以帮助您：

* **保留上下文**：通过将探索和实现排除在主对话之外
* **强制约束**：通过限制子代理可使用的工具
* **重用配置**：通过用户级别的子代理跨项目实现
* **专门化行为**：通过针对特定领域的聚焦系统提示词实现
* **控制成本**：通过将任务路由到更快、更便宜的模型（如 Haiku）实现

Claude 使用每个子代理的描述来决定何时委派任务。创建子代理时，请撰写清晰的描述，以便 Claude 知道何时使用它。

Claude Code 包含几个内置的子代理，例如 Explore、Plan 和 general-purpose。您还可以创建自定义子代理来处理特定任务。

## 内置子智能体

Claude Code 包含内置的子智能体，Claude 会在适当的时候自动使用它们。每个子智能体都会继承父对话的权限，并带有额外的工具限制。

Explore 和 Plan 会跳过你的 CLAUDE.md 文件以及父会话的 git 状态，以保持研究过程的快速和低成本。所有其他内置和 [自定义子智能体](#configure-subagents) 都会加载这两者。关于传递给子智能体的完整内容明细，请参见 [启动时加载的内容](#what-loads-at-startup)。

<Tabs>
  <Tab title="Explore">
    一个快速、只读的智能体，专门针对搜索和分析代码库进行了优化。

    * **模型**：继承自主对话，在 Claude API 上以 Opus 为上限，因此 Explore 绝不会在比您当前会话所选模型更昂贵的模型上运行
    * **工具**：只读工具；写入和编辑被禁用
    * **目的**：文件发现、代码搜索、代码库探索

    {/* min-version: 2.1.198 */}自 v2.1.198 起，Explore 继承主对话的模型，而不是始终在 Haiku 上运行。在 Claude API 上，继承的模型以 Opus 为上限：处于更高级别的主对话将在 Opus 上运行 Explore，而处于 Sonnet 或 Haiku 的主对话将在相同模型上运行 Explore。在任何其他提供商上，例如 [Amazon Bedrock, Google Cloud's Agent Platform, Microsoft Foundry, or Claude Platform on AWS](/docs/en/third-party-integrations)，Explore 将直接继承主对话的模型。

    一个 [用户或项目子代理](#choose-the-subagent-scope) 名为 `Explore` 会覆盖内置项并保留其自己的 `model` 字段，因此请使用 `model: haiku` 定义一个，以便将探索保持在成本较低的模型上。

    当 Claude 需要在不进行更改的情况下搜索或理解代码库时，它会委托给 Explore。这会将探索结果排除在您的主对话上下文之外。

    当调用 Explore 时，Claude 会指定一个彻底程度级别：**quick** 用于针对性查找，**medium** 用于平衡探索，或 **very thorough** 用于全面分析。
  </Tab>

  <Tab title="Plan">
    一个在 [plan mode](/docs/en/permission-modes#analyze-before-you-edit-with-plan-mode) 期间使用的研究代理，用于在提出计划之前收集上下文。

    * **模型**：继承自主对话
    * **工具**：只读工具；Write 和 Edit 被禁用
    * **目的**：用于规划的代码库研究

    当你处于计划模式且 Claude 需要理解你的代码库时，它会将研究任务委托给 Plan 子代理，以便探索输出保留在单独的上下文窗口中，而主对话保持只读。
  </Tab>

  <Tab title="General-purpose">
    一个功能强大的代理，用于需要探索和操作的复杂、多步骤任务。

    * **模型**：继承自主对话
    * **工具**：所有 [available to subagents](#available-tools) 子代理可用的工具
    * **目的**：复杂研究、多步骤操作、代码修改

    当任务需要同时进行探索和修改、需要复杂推理来解释结果，或需要多个依赖步骤时，Claude 会将其委托给通用代理。
  </Tab>

  <Tab title="Other">
    Claude Code 包含用于特定任务的额外辅助代理。这些通常会被自动调用，因此你无需直接使用它们。

    | 代理             | 模型  | Claude 何时使用它                                      |
    | :---------------- | :----- | :------------------------------------------------------- |
    | statusline-setup  | Sonnet | 当你运行 `/statusline` 来配置你的状态栏时 |
    | claude-code-guide | Haiku  | 当你询问有关 Claude Code 功能的问题时        |
  </Tab>
</Tabs>

内置子代理在交互式会话中默认已注册。要限制它们：

* 要阻止特定的内置类型，请将其添加到 `permissions.deny` 中，如 [禁用特定子代理](#disable-specific-subagents) 所示。
* 要防止 Claude 委派给任何子代理，请拒绝 `Agent` 工具本身，使用 [`permissions.deny`](/docs/en/permissions#tool-specific-permission-rules)。
* {/* min-version: 2.1.198 */}要仅移除内置的 `Explore` 和 `Plan` 子代理，请设置 [`CLAUDE_CODE_DISABLE_EXPLORE_PLAN_AGENTS=1`](/docs/en/env-vars)。Claude 将直接读取和浏览文件，而不是委派给它们。需要 Claude Code v2.1.198 或更高版本。
* 在 [非交互模式](/docs/en/headless) 和 [Agent SDK](/docs/en/agent-sdk/overview) 中，设置 [`CLAUDE_AGENT_SDK_DISABLE_BUILTIN_AGENTS=1`](/docs/en/env-vars) 以移除所有内置类型并仅提供您自己的类型。

除了这些内置子代理之外，您还可以使用自定义提示词、工具限制、权限模式、钩子和技能来创建您自己的子代理。以下部分展示了如何开始使用和自定义子代理。

## 快速入门：创建您的第一个子代理

子代理是带有 YAML frontmatter 的 Markdown 文件。要创建一个子代理，请让 Claude 为您编写，或者 [自己编写文件](#write-subagent-files)。

{/* min-version: 2.1.198 */}从 v2.1.198 版本开始，`/agents` 命令不再打开交互式创建向导；运行它会打印一条提醒，要求您询问 Claude 或直接编辑 `.claude/agents/`。子代理文件、frontmatter 字段以及 `.claude/agents/` 和 `~/.claude/agents/` 的位置保持不变；仅移除了终端向导。

本演练将创建一个用户级的子代理，用于审查代码并提出改进建议。

<Steps>
  <Step title="要求 Claude 创建子代理">
    在 Claude Code 中，描述您想要的子代理以及保存它的位置：

    ```text wrap theme={null}
    在 ~/.claude/agents/ 中创建一个个人代码改进子代理，它会扫描
    文件，并建议在可读性、性能和最佳
    实践方面的改进。它应该解释每个问题，展示当前代码，并
    提供改进后的版本。将其设为只读，并让它使用 Sonnet。
    ```

    Claude 编写该文件时包含一个 `name`、一个 `description`、一个 `tools` 列表、一个 `model` 和一个系统提示词。
  </Step>

  <Step title="审查文件">
    打开 `~/.claude/agents/code-improver.md` 并确认 frontmatter 是否符合您的要求。结果如下所示：

    ```markdown theme={null}
    ---
    name: code-improver
    description: 扫描文件，并建议在可读性、性能和最佳实践方面的改进。在编写或修改代码后使用。
    tools: Read, Grep, Glob
    model: sonnet
    ---

    你是一个代码改进专家。对于你发现的每个问题，请解释
    该问题，展示当前代码，并提供一个改进后的版本。
    ```

    由于该文件位于 `~/.claude/agents/` 中，因此该子代理在您机器上的每个项目中都可用。要将其范围限定在单个项目中，请将其移动到该项目的 `.claude/agents/` 目录。[选择子代理范围](#choose-the-subagent-scope) 对两者进行了比较。
  </Step>

  <Step title="试一试">
    要求 Claude 委派给新的子代理：

    ```text wrap theme={null}
    使用 code-improver 代理来建议此项目中的改进
    ```

    Claude 委派给您的新子代理，该子代理会扫描代码库并返回改进建议。

    如果 Claude 找不到新的子代理，请重启 Claude Code 并重试。这种情况仅在会话开始前 `~/.claude/agents/` 不存在时发生，因为运行中的会话无法检测到新创建的 `agents` 目录。
  </Step>
</Steps>

您现在拥有了一个子代理，可以在您机器上的任何项目中使用它来分析代码库并提出改进建议。

您也可以手动编写子代理文件，通过 CLI 标志定义它们，或通过插件分发它们。以下部分涵盖了所有配置选项。

<Note>
  在 Claude Code v2.1.197 及更早版本中，`/agents` 会打开一个交互式向导，其中包含列出实时子代理的 **Running** 选项卡，以及用于创建、编辑和删除它们的 **Library** 选项卡。 {/* max-version: 2.1.197 */}
</Note>

## 配置子代理

子代理的文件位置决定了它对谁可用，而其前置元数据决定了它能做什么。本节涵盖子代理文件的存放位置以及它们支持的每个字段。

### 选择子代理作用域

根据作用域将子代理文件存储在不同位置。当多个子代理共享相同名称时，Claude Code 会使用来自较高优先级位置的那个。

| 位置                     | 作用域                   | 优先级    | 如何创建                                 |
| :--------------------------- | :---------------------- | :---------- | :-------------------------------------------- |
| 托管设置             | 全组织范围       | 1 (最高) | 通过 [managed settings](/docs/en/settings) 部署 |
| `--agents` CLI 标记          | 当前会话         | 2           | 启动时传递 JSON Claude Code          |
| `.claude/agents/`            | 当前项目         | 3           | 询问 Claude，或手动创建文件       |
| `~/.claude/agents/`          | 你的所有项目       | 4           | 询问 Claude，或手动创建文件       |
| 插件的 `agents/` 目录 | 启用插件的地方 | 5 (最低)  | 随 [plugins](/docs/en/plugins) 一起安装         |

**项目子代理** (`.claude/agents/`) 非常适合针对特定代码库的子代理。将它们纳入版本控制，以便您的团队可以共同使用和改进它们。

项目子代理是通过从当前工作目录向上遍历来发现的，因此从那里到仓库根目录之间的每个 `.claude/agents/` 都会被扫描。 {/* min-version: 2.1.178 */}从 v2.1.178 开始，当这些嵌套目录中有多个定义了相同的 `name` 时，Claude Code 会使用最接近工作目录的定义。

通过 `--add-dir` 添加的目录也会被扫描：添加目录内的 `.claude/agents/` 文件夹会与项目子代理一起加载。请参阅 [Additional directories](/docs/en/permissions#additional-directories-grant-file-access-not-configuration) 了解还有哪些其他配置类型会从 `--add-dir` 加载。要在不使用 `--add-dir` 的情况下跨项目共享子代理，请使用 `~/.claude/agents/` 或 [plugin](/docs/en/plugins)。

**用户子代理** (`~/.claude/agents/`) 是在您的所有项目中可用的个人子代理。

Claude Code 会递归扫描 `.claude/agents/` 和 `~/.claude/agents/`，因此您可以将定义组织到诸如 `agents/review/` 或 `agents/research/` 之类的子文件夹中。子目录路径不会影响子代理的识别或调用方式，因为其身份仅来源于 `name` 前置元数据字段。

保持 `name` 的值在整个树结构中唯一：如果同一个 `.claude/agents/` 目录（包括其子文件夹）下的两个文件声明了相同的名称，Claude Code 将只加载其中一个，该选择由文件系统读取顺序而非文档记载的优先级决定。如上所述，在嵌套的项目目录中，最接近工作目录的定义优先。 {/* min-version: 2.1.205 */}[`/doctor`](/docs/en/commands#all-commands) 安装检查程序会报告同一目录中共享相同名称的文件，并建议重命名或移除其中多余的文件，只保留一个。在 v2.1.205 之前，`/doctor` 会打开一个诊断屏幕，列出重复项并显示当前生效的定义。

插件 `agents/` 目录也会被递归扫描。与项目作用域和用户作用域不同，插件 `agents/` 目录内的子文件夹会成为 [作用域标识符](#invoke-subagents-explicitly) 的一部分：在插件 `agents/review/security.md` 中位于 `my-plugin` 的文件将注册为 `my-plugin:review:security`。

**CLI 定义的子代理**在启动 Claude Code 时作为 JSON 传递。它们仅存在于该会话中并且不会保存到磁盘，这使它们对于快速测试或自动化脚本非常有用。您可以在单个 `--agents` 调用中定义多个子代理：

<Tabs>
  <Tab title="macOS, Linux, WSL">
    ```bash theme={null}
    claude --agents '{
      "code-reviewer": {
        "description": "专家代码审查员。代码更改后主动使用。",
        "prompt": "你是一名资深代码审查员。关注代码质量、安全性和最佳实践。",
        "tools": ["Read", "Grep", "Glob", "Bash"],
        "model": "sonnet"
      },
      "debugger": {
        "description": "调试错误和测试失败的专家。",
        "prompt": "你是一名专家级调试员。分析错误、找出根本原因并提供修复方案。"
      }
    }'
    ```
  </Tab>

  <Tab title="Windows PowerShell">
    ```powershell theme={null}
    claude --agents @'
    {
      "code-reviewer": {
        "description": "专家代码审查员。代码更改后主动使用。",
        "prompt": "你是一名资深代码审查员。关注代码质量、安全性和最佳实践。",
        "tools": ["Read", "Grep", "Glob", "Bash"],
        "model": "sonnet"
      },
      "debugger": {
        "description": "调试错误和测试失败的专家。",
        "prompt": "你是一名专家级调试员。分析错误、找出根本原因并提供修复方案。"
      }
    }
    '@
    ```
  </Tab>
</Tabs>

`--agents` 标志接受带有与基于文件的子代理相同的 [frontmatter](#supported-frontmatter-fields) 字段的 JSON：`description`、`prompt`、`tools`、`disallowedTools`、`model`、`permissionMode`、`mcpServers`、`hooks`、`maxTurns`、`skills`、`initialPrompt`、`memory`、`effort`、`background`、`isolation` 和 `color`。将 `prompt` 用于系统提示词，等同于基于文件的子代理中的 markdown 正文。

**托管子代理**由组织管理员部署。将 markdown 文件放在 `.claude/agents/` 中的 [managed settings directory](/docs/en/settings#settings-files) 内部，使用与项目和用户子代理相同的 frontmatter 格式。托管定义优先于具有相同名称的项目和用户子代理。

**插件子代理**来自您已安装的 [plugins](/docs/en/plugins)。它们会与您的自定义子代理一起自动加载，并以其作用域名称出现在 @-提及的预先输入中。有关创建插件子代理的详细信息，请参见 [plugin components reference](/docs/en/plugins-reference#agents)。

<Note>
  出于安全原因，插件子代理不支持 `hooks`、`mcpServers` 或 `permissionMode` frontmatter 字段。从插件加载代理时会忽略这些字段。如果您需要它们，请将代理文件复制到 `.claude/agents/` 或 `~/.claude/agents/`。您还可以在 [ 或 `permissions.allow` 中向 ](/docs/en/settings#permission-settings)`settings.json``settings.local.json` 添加规则，但这些规则适用于整个会话，而不仅仅是插件子代理。
</Note>

来自任何这些作用域的子代理定义也可供 [agent teams](/docs/en/agent-teams#use-subagent-definitions-for-teammates) 使用：在生成队友时，您可以引用子代理类型，队友将使用其 `tools` 和 `model`，并将定义的正文作为附加指令附加到队友的系统提示词中。有关哪些 frontmatter 字段适用于该路径的信息，请参见 [agent teams](/docs/en/agent-teams#use-subagent-definitions-for-teammates)。

### 编写子代理文件

子代理文件使用 YAML frontmatter 进行配置，随后是 Markdown 格式的系统提示词：

<Note>
  Claude Code 监视 `~/.claude/agents/` 和 `.claude/agents/`。当您在磁盘上添加或编辑子代理文件，或者要求 Claude 为您编写一个时，Claude Code 会在几秒钟内检测到更改，下一次委派将使用更新后的定义，无需重启。

  有两种情况仍需要重启：

  * 监视器仅涵盖会话启动时已存在的目录，因此在新 `agents` 目录中创建某个作用域的第一个代理文件后，需要重启才能加载。
  * 使用 `--disable-slash-commands` 启动的会话根本不监视这些目录。
</Note>

```markdown theme={null}
---
name: code-reviewer
description: Reviews code for quality and best practices
tools: Read, Glob, Grep
model: sonnet
---

You are a code reviewer. When invoked, analyze the code and provide
specific, actionable feedback on quality, security, and best practices.
```

frontmatter 定义子代理的元数据和配置。正文成为指导子代理行为的系统提示词。子代理仅接收此系统提示词以及工作目录等基本环境细节，而不是完整的 Claude Code 系统提示词。

在 [非交互模式](/docs/en/headless) 下，[`--append-subagent-system-prompt`](/docs/en/cli-reference#cli-flags) 标志会将您提供的文本追加到每个子代理（包括嵌套子代理）系统提示词的末尾。需要 Claude Code v2.1.205 或更高版本。

子代理在主对话的当前工作目录中启动。在子代理内部，`cd` 命令不会在 Bash 或 PowerShell 工具调用之间持久化，也不会影响主对话的工作目录。要改为给子代理提供一个仓库的独立副本，请设置 [`isolation: worktree`](#supported-frontmatter-fields)。

{/* min-version: 2.1.203 */}带有 `isolation: worktree` 的子代理会在其工作树中运行其 Bash 和 PowerShell 命令。如果某个命令的工作目录解析为您的主检出版本（例如，因为工作树目录在子代理运行时被删除了），则该命令将失败并报错。在 v2.1.203 之前，此类命令可以在主检出版本中运行。

{/* min-version: 2.1.210 */}此工作目录检查涵盖包含您启动 Claude Code 时所在目录的整个仓库。当您的会话在其自身链接的 [工作树](/docs/en/worktrees) 中运行时，该检查也涵盖该工作树链接自的主检出版本。在 v2.1.210 之前，该检查仅涵盖启动目录本身。如果某个命令的工作目录解析到同一仓库中的其他位置（例如，当您从 monorepo 子目录启动 Claude Code 时，仓库根目录即为其他位置），该命令会在那里运行而不是失败。

{/* min-version: 2.1.216 */}对于 Bash 命令，Claude Code 还会检查命令本身：任何将 git 重定向到主检出版本的命令都会失败并报错，无论它使用 `git -C`、`--git-dir`、`GIT_DIR` 或 `GIT_WORK_TREE` 变量，还是首先 `cd` 到主检出版本中。过于复杂而无法检查的命令也会失败，并提示错误，告诉 Claude 将其拆分为独立的纯命令。此检查仅适用于 Bash；PowerShell 命令仅进行工作目录检查。

#### 支持的 frontmatter 字段

以下字段可用于 YAML frontmatter。只有 `name` 和 `description` 是必需的。

| 字段             | 必需 | 描述                                                                                                                                                                                                                                                                                                                                                            |
| :---------------- | :------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`            | 是      | 使用小写字母和连字符的唯一标识符。[Hooks](/docs/en/hooks#subagentstart) 接收此值为 `agent_type`。文件名不需要匹配                                                                                                                                                                                                         |
| `description`     | 是      | Claude 何时应委派给此子代理                                                                                                                                                                                                                                                                                                                           |
| `tools`           | 否       | [Tools](#available-tools) 子代理可以使用的工具。如果省略，则继承子代理可用的每个工具。如果列表中没有条目解析为工具，则子代理通常 [启动失败](/docs/en/errors#agent-would-be-spawned-with-zero-tools) 并出现命名条目的错误。要将技能预加载到上下文中，请使用 `skills` 字段，而不是在此处列出 `Skill` |
| `disallowedTools` | 否       | 要拒绝的工具，从继承或指定的列表中移除                                                                                                                                                                                                                                                                                                                |
| `model`           | 否       | 要使用的 [Model](#choose-a-model)：`sonnet`、`opus`、`haiku`、`fable`、完整的模型 ID（例如，`claude-opus-5`）或 `inherit`。默认为 `inherit`                                                                                                                                                                                                               |
| `permissionMode`  | 否       | [Permission mode](#permission-modes)：`default`、`acceptEdits`、`auto`、`dontAsk`、`bypassPermissions`、`plan`，或 {/* min-version: 2.1.200 */}`manual` 作为 `default` 的别名。`manual` 别名需要 Claude Code v2.1.200 或更高版本。对于 [plugin subagents](#choose-the-subagent-scope) 会被忽略                                                               |
| `maxTurns`        | 否       | 子代理停止前的最大代理轮数                                                                                                                                                                                                                                                                                                              |
| `skills`          | 否       | [技能](/docs/en/skills) 在启动时预加载到子代理的上下文中。注入的是完整的技能内容，而不仅仅是描述。子代理仍然可以通过技能工具调用未列出的项目、用户和插件技能                                                                                                                                      |
| `mcpServers`      | 否       | [MCP 服务器](/docs/en/mcp) 可供此子代理使用。每个条目要么是引用已配置服务器的服务器名称（例如，`"slack"`），要么是一个内联定义，以服务器名称为键，以完整的 [MCP 服务器配置](/docs/en/mcp#installing-mcp-servers) 为值。对于 [插件子代理](#choose-the-subagent-scope) 将被忽略                               |
| `hooks`           | 否       | [生命周期钩子](#define-hooks-for-subagents) 作用于此子代理。对于 [插件子代理](#choose-the-subagent-scope) 将被忽略                                                                                                                                                                                                                                     |
| `memory`          | 否       | [持久内存范围](#enable-persistent-memory): `user`、`project` 或 `local`。启用跨会话学习                                                                                                                                                                                                                                                    |
| `background`      | 否       | 设置为 `true` 以始终将此子代理作为 [后台任务](#run-subagents-in-foreground-or-background) 运行，即使 Claude 立即需要其结果。未设置时，由 Claude 选择，并且 {/* min-version: 2.1.198 */}从 v2.1.198 版本开始，它默认在后台运行子代理                                                                                  |
| `effort`          | 否       | 此子代理处于活动状态时的努力程度。覆盖会话的努力程度。默认值：继承自会话。选项：`low`、`medium`、`high`、`xhigh`、`max`；可用级别取决于模型                                                                                                                                                                  |
| `isolation`       | 否       | 设置为 `worktree` 以在临时 [git worktree](/docs/en/worktrees) 中运行子代理，为其提供一个默认从你的 [默认分支](/docs/en/worktrees#choose-the-base-branch) 而非父会话的 `HEAD` 分支出来的仓库隔离副本。如果子代理未进行任何更改，工作树将被自动清理                               |
| `color`           | 否       | 子代理在任务列表和记录中的显示颜色。接受 `red`、`blue`、`green`、`yellow`、`purple`、`orange`、`pink` 或 `cyan`                                                                                                                                                                                                                        |
| `initialPrompt`   | 否       | 当此代理作为主会话代理运行时（通过 `--agent` 或 `agent` 设置），自动作为第一轮用户对话提交。[命令](/docs/en/commands) 和 [技能](/docs/en/skills) 将被处理。添加到任何用户提供的提示词之前                                                                                                                                    |

### 选择一个模型

该 `model` 字段控制子智能体使用的 [AI模型](/docs/en/model-config):

* **模型别名**: 使用可用别名之一: `sonnet`, `opus`, `haiku`, 或 `fable`
* **完整模型 ID**: 使用完整模型 ID, 例如 `claude-opus-5` 或 `claude-sonnet-5`. 接受与 `--model` 标志相同的值
* **inherit**: 使用与主对话相同的模型
* **Omitted**: 默认为 `inherit` 并使用与主对话相同的模型

当 Claude 调用子智能体时, 它还可以为该特定调用传递一个 `model` 参数. Claude Code 按以下顺序解析子智能体的模型:

1. 该 [`CLAUDE_CODE_SUBAGENT_MODEL`](/docs/en/model-config#environment-variables) 环境变量, 当设置为模型别名或模型 ID 时
2. 每次调用的 `model` 参数
3. 子智能体定义的 `model` 前置元数据
4. 主对话的模型

{/* min-version: 2.1.196 */}自 v2.1.196 起，将 `CLAUDE_CODE_SUBAGENT_MODEL` 设置为 `inherit` 与其保持未设置的效果相同：解析将继续遵循每次调用的 `model` 参数，然后是 frontmatter。在早期版本中，`inherit` 会强制子代理使用主对话的模型，并忽略这两个来源。

Claude Code 会将环境变量、每次调用的参数以及 frontmatter 值与您组织的 [`availableModels`](/docs/en/model-config#restrict-model-selection) 允许列表进行核对。它会跳过解析为被排除模型的值，转而在继承的模型上运行子代理。

{/* min-version: 2.1.211 */}每次调用的 `model` 参数在子代理被 [恢复或发送后续消息](#resume-subagents)时同样适用，因此子代理会保持使用该模型。在 v2.1.211 版本之前，恢复操作会丢弃每次调用的值，子代理会恢复为其定义中的 `model` 字段，或者在没有该字段的情况下，使用主对话的模型。

{/* min-version: 2.1.198 */}从 v2.1.198 开始，子智能体也会继承主对话的 [extended thinking](/docs/en/model-config#extended-thinking) 配置：如果在您的会话中开启了思考，则子智能体也会开启；如果关闭，则保持关闭。没有针对每个子智能体的独立思考设置。在 v2.1.198 之前，无论主对话的设置如何，子智能体在运行时都会禁用扩展思考。

### 控制子智能体的能力

您可以通过工具访问、权限模式和条件规则来控制子智能体可以执行的操作。

#### 可用工具

子代理继承主对话中可用的 [内置工具](/docs/en/tools-reference) 和 MCP 工具，并受两个过滤器限制：第一个过滤器从每个子代理中移除一小组工具，第二个过滤器缩减在 [后台](#run-subagents-in-foreground-or-background) 运行的子代理（这是默认设置）的内置工具集。[分支](#fork-the-current-conversation) 跳过这两个过滤器，接收主对话的完整工具池。第一个过滤器会移除这些工具，即使它们列在 `tools` 字段中：

* `Agent`，当子代理处于 [深度限制](#let-subagents-spawn-their-own-subagents) 时；在 [分支](#fork-the-current-conversation) 中，该工具仍保留在列表中，但会返回错误而不是生成新代理
* `AskUserQuestion`
* `EndConversation`，它只能结束主对话；参见 [EndConversation 工具行为](/docs/en/tools-reference#endconversation-tool-behavior)
* `EnterPlanMode`
* `ExitPlanMode`，除非子代理的 [`permissionMode`](#permission-modes) 为 `plan`
* `ScheduleWakeup`
* `TaskOutput`
* `WaitForMcpServers`
* `Workflow`

第二个过滤器适用于在后台运行的子代理。除了 `Agent` 和 `ExitPlanMode`（无论子代理在哪里运行都遵循第一个过滤器的条件）之外，后台子代理保留所有 MCP 工具，但仅保留这些内置工具：`Read`、`Grep`、`Glob`、`Bash`、`PowerShell`、`Edit`、`Write`、`NotebookEdit`、`WebFetch`、`WebSearch`、`TodoWrite`、`Skill`、`ToolSearch`、`EnterWorktree`、`ExitWorktree`、`Monitor`、`TaskStop`、`SendMessage` 和 `Artifact`。Claude Code 会从后台子代理中移除所有其他内置工具，无论是继承的还是列在 `tools` 字段中的，因此相同的定义在前台和后台可能解析为不同的工具。除非移除后导致 `tools` 列表 [解析为空](/docs/en/errors#agent-would-be-spawned-with-zero-tools)，否则移除操作不会报告错误。

[代理团队](/docs/en/agent-teams) 中的队友还保留任务工具和 cron 工具：`TaskCreate`、`TaskGet`、`TaskList`、`TaskUpdate`、`CronCreate`、`CronDelete` 和 `CronList`。

要限制工具，请使用 `tools` 字段作为允许列表，或使用 `disallowedTools` 字段作为拒绝列表。此示例使用 `tools` 仅允许 Read、Grep、Glob 和 Bash。该子代理无法编辑文件、写入文件或使用任何 MCP 工具：

```yaml theme={null}
---
name: safe-researcher
description: Research agent with restricted capabilities
tools: Read, Grep, Glob, Bash
---
```

此示例使用 `disallowedTools` 继承子代理的工具池，但不包括 Write 和 Edit。该子代理保留 Bash、MCP 工具及其工具池的其余部分：

```yaml theme={null}
---
name: no-writes
description: Inherits the available tools except file writes
disallowedTools: Write, Edit
---
```

如果两者都设置了，则先应用 `disallowedTools`，然后根据剩余的池解析 `tools`。同时列在两者中的工具会被移除。

当 `tools` 列表中没有任何条目能解析为工具时，例如因为每个条目都拼写错误或指定了子代理不可用的工具，Claude Code 通常会拒绝启动子代理，并且 Agent 工具会返回一个错误，指出无法解析的条目；参见 [Agent 将以零工具生成](/docs/en/errors#agent-would-be-spawned-with-zero-tools) 了解该消息及如何修复每个条目。{/* min-version: 2.1.208 */}在 v2.1.208 之前，该子代理会在没有工具的情况下启动，并可能返回空结果或令人困惑的结果。

这两个字段除了接受精确的工具名称外，还接受 MCP 服务器级别的模式：`mcp__<server>` 或 `mcp__<server>__*` 会授予或移除指定服务器中的所有工具。在 `disallowedTools` 中，`mcp__*` 还会从任何服务器中移除所有 MCP 工具。此示例会移除 `github` MCP 服务器中的所有工具，同时保留其他服务器的工具和其工具池中的内置工具：

```yaml theme={null}
---
name: local-only
description: Inherits every tool except those from the github MCP server
disallowedTools: mcp__github
---
```

#### 限制可以生成哪些子代理

当一个代理使用 `claude --agent` 作为主线程运行时，它可以使用 Agent 工具生成子代理。为了限制它可以生成的子代理类型，请在 `Agent(agent_type)` 字段中使用 `tools` 语法。

<Note>在版本 2.1.63 中，Task 工具被重命名为 Agent。设置和代理定义中现有的 `Task(...)` 引用仍然作为别名工作。</Note>

```yaml theme={null}
---
name: coordinator
description: Coordinates work across specialized agents
tools: Agent(worker, researcher), Read, Bash
---
```

这是一个允许列表：只有 `worker` 和 `researcher` 子代理可以被生成。如果代理尝试生成任何其他类型，请求将失败，并且代理在其提示词中只能看到允许的类型。要阻止特定代理同时允许所有其他代理，请改用 [`permissions.deny`](#disable-specific-subagents)。

要允许不受限制地生成任何子代理，请使用不带括号的 `Agent`：

```yaml theme={null}
tools: Agent, Read, Bash
```

如果您完全从 `Agent` 列表中省略 `tools`，代理将无法使用 Agent 工具生成任何子代理。

`Agent(agent_type)` 允许列表语法仅适用于使用 `claude --agent` 作为主线程运行的代理。在子代理定义中，在 `Agent` 中列出 `tools` 允许该子代理在 [深度限制](#let-subagents-spawn-their-own-subagents) 允许的情况下生成自己的子代理，但括号内的任何类型列表都将被忽略。

#### 将 MCP 服务器范围限定于子代理

使用 `mcpServers` 字段可以让子代理访问主对话中不可用的 [MCP](/docs/en/mcp) 服务器。此处定义的内联服务器在子代理启动时连接，并在其完成时断开。字符串引用共享父会话的连接。

<Note>
  `mcpServers` 字段适用于代理文件可以运行的两种上下文：

  * 作为子代理，通过 Agent 工具或 @-提及 生成
  * 作为主会话，通过 [`--agent`](#invoke-subagents-explicitly) 或 `agent` 设置启动

  当代理作为主会话时，内联服务器定义将在启动时与来自 [`.mcp.json`](/docs/en/mcp) 和设置文件的服务器一起连接。
</Note>

列表中的每个条目要么是内联服务器定义，要么是引用已在您的会话中配置的 MCP 服务器的字符串：

```yaml theme={null}
---
name: browser-tester
description: Tests features in a real browser using Playwright
mcpServers:
  # Inline definition: scoped to this subagent only
  - playwright:
      type: stdio
      command: npx
      args: ["-y", "@playwright/mcp@latest"]
  # Reference by name: reuses an already-configured server
  - github
---

Use the Playwright tools to navigate, screenshot, and interact with pages.
```

内联定义使用与 `.mcp.json` 服务器条目相同的模式，以服务器名称为键，并支持 `stdio`、`http`、`sse` 和 `ws` 类型。

为了将 MCP 服务器完全排除在主对话之外，并避免其工具描述消耗那里的上下文，请在此处内联定义它，而不是在 `.mcp.json` 中。子代理获得这些工具；父对话则不会。

从 v2.1.153 版本开始，适用于主会话的 MCP 限制也涵盖了子代理 frontmatter 中声明的服务器：

* [`--strict-mcp-config`](/docs/en/cli-reference) 和 [`--bare`](/docs/en/cli-reference)
* [企业管理的 MCP 配置](/docs/en/managed-mcp)
* [`allowedMcpServers` 和 `deniedMcpServers` 策略](/docs/en/managed-mcp#policy-based-control-with-allowlists-and-denylists)

当其中一个阻止了某个服务器时，Claude Code 会跳过它，并显示一条警告，指明被阻止的服务器。

托管设置的限制适用于每个子代理，无论它是如何定义的。`--strict-mcp-config` 不会过滤您通过 `--agents` 或 SDK `agents` 选项内联传递的服务器，因为这些是显式的调用者输入。

#### 权限模式

`permissionMode` 字段控制子代理如何处理权限提示。子代理从主对话继承权限上下文，并可以覆盖该模式，除非如以下所述由父模式优先执行。

| 模式                | 行为                                                                                                                                                                                                                                                                                                                        |
| :------------------ | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `default`           | 带提示的标准权限检查                                                                                                                                                                                                                                                                                       |
| `acceptEdits`       | 自动接受工作目录或 `additionalDirectories` 中路径的文件编辑和常见文件系统命令                                                                                                                                                                                                             |
| `auto`              | [自动模式](/docs/en/permission-modes#eliminate-prompts-with-auto-mode)：后台分类器审查命令和受保护目录的写入                                                                                                                                                                                     |
| `dontAsk`           | 自动拒绝权限提示。明确允许的工具仍然有效；`AskUserQuestion`、连接器工具 [您的组织设置为 `ask`](/docs/en/mcp#organization-controls-on-connector-tools)，以及标记为 [`requiresUserInteraction`](/docs/en/mcp#require-approval-for-a-specific-tool) 的 MCP 工具，即使您已允许它们，也会被拒绝 |
| `bypassPermissions` | 跳过权限提示                                                                                                                                                                                                                                                                                                         |
| `plan`              | 计划模式（只读探索）                                                                                                                                                                                                                                                                                               |

<Warning>
  请谨慎使用 `bypassPermissions`。它会跳过权限提示，允许子代理在未经批准的情况下执行操作，包括写入 `.git`、`.config/git`、`.claude`、`.vscode`、`.idea`、`.husky`、`.cargo`、`.devcontainer`、`.yarn` 和 `.mvn`。

  明确的 [`ask` 规则](/docs/en/permissions#manage-permissions)、连接器工具 [您的组织设置为 `ask`](/docs/en/mcp#organization-controls-on-connector-tools)、标记为 [`requiresUserInteraction`](/docs/en/mcp#require-approval-for-a-specific-tool) 的 MCP 工具，以及删除根目录和主目录（如 `rm -rf /`）仍然会提示。详情请参阅 [权限模式](/docs/en/permission-modes#skip-all-checks-with-bypasspermissions-mode)。
</Warning>

如果父级使用 `bypassPermissions` 或 `acceptEdits`，则此设置优先且无法被覆盖。如果父级使用 [自动模式](/docs/en/permission-modes#eliminate-prompts-with-auto-mode)，则子代理会继承自动模式，并且其前言中的任何 `permissionMode` 都将被忽略：分类器将使用与父会话相同的阻止和允许规则来评估子代理的工具调用。

#### 预加载技能到子代理中

使用 `skills` 字段在启动时将技能内容注入到子代理的上下文中。这为子代理提供了领域知识，而无需其在执行期间发现并加载技能。

```yaml theme={null}
---
name: api-developer
description: Implement API endpoints following team conventions
skills:
  - api-conventions
  - error-handling-patterns
---

Implement API endpoints. Follow the conventions and patterns from the preloaded skills.
```

每个所列技能的完整内容都会在启动时注入到子代理的上下文中。此字段控制预加载哪些技能，而不是子代理可以访问哪些技能：没有它，子代理仍然可以发现并 在执行期间通过 Skill 工具调用项目、用户和插件技能。为了防止子代理调用 完全禁用技能，将 `Skill` 从 [`tools`](#available-tools) 列表中省略，或将其添加到 `disallowedTools`.

你无法预加载设置了 [`disable-model-invocation: true`](/docs/en/skills#control-who-invokes-a-skill) 的技能，因为预加载是从 Claude 可以调用的同一套技能中提取的。{/* min-version: 2.1.215 */}这包括内置的 `/verify` 和 `/code-review` 技能：只有你能运行它们，所以它们也无法被预加载。

如果列出的技能缺失或被禁用，Claude Code 将跳过它并记录一条警告到调试日志中。

<Note>
  这是 [在子代理中运行技能](/docs/en/skills#run-skills-in-a-subagent) 的逆向操作。在子代理中使用 `skills` 时，由子代理控制系统提示词并加载技能内容。在技能中使用 `context: fork` 时，技能内容会被注入到你指定的代理中。两者都使用相同的底层系统。
</Note>

#### 启用持久记忆

`memory` 字段为子代理提供了一个跨对话持久存在的目录。子代理使用此目录随着时间推移积累知识，例如代码库模式、调试洞察和架构决策。

```yaml theme={null}
---
name: code-reviewer
description: Reviews code for quality and best practices
memory: user
---

You are a code reviewer. As you review code, update your agent memory with
patterns, conventions, and recurring issues you discover.
```

根据记忆应用范围的广泛程度选择作用域：

| 作用域     | 位置                                      | 使用场景                                                                                   |
| :-------- | :-------------------------------------------- | :----------------------------------------------------------------------------------------- |
| `user`    | `~/.claude/agent-memory/<name-of-agent>/`     | 子代理应记住跨所有项目的经验                                 |
| `project` | `.claude/agent-memory/<name-of-agent>/`       | 子代理的知识是项目特定的并可通过版本控制共享             |
| `local`   | `.claude/agent-memory-local/<name-of-agent>/` | 子代理的知识是项目特定的但不应提交到版本控制 |

子代理记忆是 [自动记忆](/docs/en/memory#auto-memory) 的一部分：如果你使用 `autoMemoryEnabled` 设置或 `CLAUDE_CODE_DISABLE_AUTO_MEMORY` 关闭了自动记忆，`memory` 字段将不起作用，并且子代理在启动时将不包含记忆指令或下文所述的记忆工具访问权限。

当记忆被启用时：

* 子代理的系统提示包含了读写记忆目录的指令。
* 子代理的系统提示还包含了记忆目录中 `MEMORY.md` 的前 200 行或 25KB（以先达到者为准），并带有指示：如果超出此限制，则需整理 `MEMORY.md`。
* 读取、写入和编辑工具会自动启用，以便子代理能够管理其记忆文件。

##### 持久记忆提示

* `project` 是推荐的默认范围。它通过版本控制使子代理的知识可共享。
* 在开始工作前，要求子代理查阅其记忆：“审查这个 PR，并检查你的记忆中是否有过往见过的模式。”
* 在完成任务后，要求子代理更新其记忆：“现在你已经完成了，把你学到的东西保存到你的记忆中。”随着时间的推移，这将建立一个知识库，使子代理更高效。
* 将记忆指令直接包含在子代理的 markdown 文件中，以便它主动维护自己的知识库：

  ```markdown theme={null}
      当你发现代码路径、模式、库
      位置和关键架构决策时，更新你的代理记忆。这能积累制度性
      知识跨越多次对话。写下关于你发现了什么
      以及在哪里的简明笔记。
  ```

#### 带钩子的条件规则

为了对工具的使用进行更动态的控制，请使用 `PreToolUse` 钩子在实际执行操作之前对其进行验证。当您需要允许工具的某些操作同时阻止其他操作时，这非常有用。

此示例创建了一个仅允许只读数据库查询的子代理。在执行每条 Bash 命令之前，`PreToolUse` 钩子会运行在 `command` 中指定的脚本：

```yaml theme={null}
---
name: db-reader
description: Execute read-only database queries
tools: Bash
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-readonly-query.sh"
---
```

Claude Code [将钩子输入作为 JSON 传递](/docs/en/hooks#pretooluse-input) 通过标准输入传递给钩子命令。验证脚本读取此 JSON，提取 Bash 命令，并 [以退出代码 2 退出](/docs/en/hooks#exit-code-2-behavior-per-event) 以阻止写操作：

```bash theme={null}
#!/bin/bash
# ./scripts/validate-readonly-query.sh

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Block SQL write operations (case-insensitive)

if echo "$COMMAND" | grep -iE '\b(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE)\b' > /dev/null; then
  echo "Blocked: Only SELECT queries are allowed" >&2
  exit 2
fi

exit 0
```

参见 [钩子输入](/docs/en/hooks#pretooluse-input) 获取完整的输入架构，并参见 [退出代码](/docs/en/hooks#exit-code-output) 了解退出代码如何影响行为。在 Windows 上，请使用 PowerShell 编写钩子脚本，并将 `shell: powershell` 添加到钩子条目中，如 [在 PowerShell 中运行钩子](/docs/en/hooks#windows-powershell-tool) 所示。

#### 禁用特定子代理

你可以通过将特定子代理添加到 `deny` 数组（在你的 [settings](/docs/en/settings#permission-settings) 中）来防止 Claude 使用它们。请使用以下格式 `Agent(subagent-name)` 其中 `subagent-name` 匹配子代理的名称字段。

```json theme={null}
{
  "permissions": {
    "deny": ["Agent(Explore)", "Agent(my-custom-agent)"]
  }
}
```

这对于内置和自定义子代理均适用。您也可以使用 `--disallowedTools` CLI 标志：

```bash theme={null}
claude --disallowedTools "Agent(Explore)"
```

有关权限规则的更多详细信息，请参阅 [权限文档](/docs/en/permissions#tool-specific-permission-rules)。

### 为子代理定义钩子

子代理可以定义在子代理生命周期内运行的 [钩子](/docs/en/hooks)。配置钩子有两种方式：

* **在子代理的 frontmatter 中**：定义仅在该子代理处于活动状态时运行的钩子
* **在 `settings.json` 中**：定义在子代理启动或停止时在主会话中运行的钩子

#### 子代理前置元数据中的钩子

直接在子代理的 markdown 文件中定义钩子。这些钩子仅在该特定子代理处于活动状态时运行，并在其完成时被清理。

<Note>
  当代理通过 Agent 工具或 @ 提及被生成为子代理时，以及当代理通过 [`--agent`](#invoke-subagents-explicitly) 或 `agent` 设置作为主会话运行时，前置元数据钩子会触发。在主会话的情况下，它们与 [`settings.json`](/docs/en/hooks) 中定义的任何钩子一起运行。
</Note>

支持所有 [钩子事件](/docs/en/hooks#hook-events)。子代理最常见的事件包括：

| 事件         | 匹配器输入   | 触发时机                                                           |
| :------------ | :------------ | :------------------------------------------------------------------ |
| `PreToolUse`  | 工具名称      | 在子代理使用工具之前                                               |
| `PostToolUse` | 工具名称      | 在子代理使用工具之后                                               |
| `Stop`        | (无)          | 当子代理完成时（在运行时转换为 `SubagentStop`）                 |

此示例使用 `PreToolUse` 钩子验证 Bash 命令，并在文件编辑后使用 `PostToolUse` 运行 linter：

```yaml theme={null}
---
name: code-reviewer
description: Review code changes with automatic linting
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-command.sh $TOOL_INPUT"
  PostToolUse:
    - matcher: "Edit|Write"
      hooks:
        - type: command
          command: "./scripts/run-linter.sh"
---
```

当代理作为子代理被调用时，前置元数据中的 `Stop` 钩子会自动转换为 `SubagentStop` 事件。

#### 用于子代理事件的项目级钩子

在 `settings.json` 中配置钩子，以响应主会话中的子代理生命周期事件。

| 事件           | 匹配器输入   | 触发时机                    |
| :-------------- | :-------------- | :------------------------------- |
| `SubagentStart` | 代理类型名称 | 当子代理开始执行时 |
| `SubagentStop`  | 代理类型名称 | 当子代理完成时        |

这两个事件都支持匹配器来按名称定位特定的代理类型。匹配器的值是用于项目级和用户级子代理的代理 frontmatter `name`，或者是插件作用域标识符比如 `my-plugin:db-agent` 用于 [插件子代理](/docs/en/plugins)。作用域名称包含一个冒号，因此 它被作为 [未锚定的正则表达式](/docs/en/hooks#matcher-patterns) 进行评估；请使用 `^` 和 `$` 对其进行锚定，如 `^my-plugin:db-agent$` 所示，以仅匹配该代理。

此示例仅在 `db-agent` 子代理启动时运行设置脚本，并在任何子代理停止时运行清理脚本：

```json theme={null}
{
  "hooks": {
    "SubagentStart": [
      {
        "matcher": "db-agent",
        "hooks": [
          { "type": "command", "command": "./scripts/setup-db-connection.sh" }
        ]
      }
    ],
    "SubagentStop": [
      {
        "hooks": [
          { "type": "command", "command": "./scripts/cleanup-db-connection.sh" }
        ]
      }
    ]
  }
}
```

像 `db-agent` 这样的带连字符的匹配器在 Claude Code v2.1.195 或更高版本中会精确匹配。在早期版本中，它被作为未锚定的正则表达式进行求值，并且也会对包含它的任何代理类型触发，例如 `prod-db-agent`；在这些版本中请将其锚定为 `^db-agent$`。

有关完整的钩子配置格式，请参见 [Hooks](/docs/en/hooks)。

## 使用子代理

### 了解自动委派

Claude 会根据您请求中的任务描述、子智能体配置中的 `description` 字段以及当前上下文自动委派任务。为了鼓励主动委派，请在子智能体的描述字段中包含“主动使用”等短语。

### 显式调用子代理

当自动委派不够用时，您可以自行请求子代理。有三种模式可以从一次性建议升级到会话级别的默认设置：

* **自然语言**：在提示词中指明子代理；由 Claude 决定是否进行委派
* **@-提及**：保证子代理针对单个任务运行
* **会话级别**：整个会话通过 `--agent` 标志或 `agent` 设置来使用该子代理的系统提示词、工具限制和模型

对于自然语言，没有特殊的语法。指明子代理的名称，Claude 通常就会进行委派：

```text wrap theme={null}
Use the test-runner subagent to fix failing tests
Have the code-reviewer subagent look at my recent changes
```

**@-提及子代理。** 输入 `@` 并从提示列表中选取子代理，方式与您 @-提及 文件相同。这确保了由特定的子代理运行，而不是将选择权留给 Claude：

```text wrap theme={null}
@"code-reviewer (agent)" look at the auth changes
```

您的完整信息仍会发送给 Claude，它会根据您的要求编写子代理的任务提示。@-提及 控制的是 Claude 调用哪个子代理，而不是它接收什么提示。

由已启用的 [plugin](/docs/en/plugins) 提供的子代理会以其作用域名称出现在预先输入列表中，例如 `my-plugin:code-reviewer` 或 `my-plugin:review:security` 当插件 [organizes agents into subfolders](#choose-the-subagent-scope)。当前在会话中运行的已命名后台子代理也会出现在预先输入列表中，并在名称旁边显示其状态。

你也可以在不使用选择器的情况下手动输入提及：本地子代理使用 `@agent-<name>`，或者插件子代理使用 `@agent-` 并在其后加上作用域名称，例如 `@agent-my-plugin:code-reviewer`。当你输入这种格式时，自动补全会显示匹配的文件而不是代理。提交时，代理提及依然会被解析。

**将整个会话作为子代理运行。** 传入 [`--agent <name>`](/docs/en/cli-reference) 来启动一个会话，在该会话中，主线程本身将承担该子代理的系统提示词、工具限制和模型：

```bash theme={null}
claude --agent code-reviewer
```

子代理的系统提示词将完全替换默认的 Claude Code 系统提示词，就像 [`--system-prompt`](/docs/en/cli-reference) 所做的那样。`CLAUDE.md` 文件和项目记忆仍然通过正常的消息流加载。代理名称将在启动标头中显示为 `@<name>`，以便你确认其已激活。

这适用于内置和自定义子代理，并且在你恢复会话时该选择会保持不变：Claude Code 会连同对话一起恢复代理的系统提示词、工具限制和模型。{/* min-version: 2.1.216 */}如果你在恢复时代理已不存在，会话将继续使用默认工具和系统提示词，并显示一条 [指出该代理名称的警告](/docs/en/errors#session-agent-no-longer-available)。

对于插件提供的子代理，你可以仅传入代理名称，Claude Code 会找到它：

```bash theme={null}
claude --agent security-reviewer
```

如果多个插件提供了同名代理，请传入作用域名称以消除歧义：

```bash theme={null}
claude --agent my-plugin:security-reviewer
```

如果插件将其代理放置在其 `agents/` 目录的子文件夹中，请在作用域名称中包含该子文件夹，例如 `claude --agent my-plugin:review:security`。

要使其成为项目中每个会话的默认设置，请在 `agent` 中设置 `.claude/settings.json`：

```json theme={null}
{
  "agent": "code-reviewer"
}
```

如果两者都存在，CLI 标志会覆盖该设置。

### 在前台或后台运行子代理

子代理可以在前台或后台运行：

* **前台子代理**会阻塞主对话，直到完成。权限提示在出现时会直接传递给您。
* **后台子代理**会并发运行，您可以继续工作。 {/* min-version: 2.1.186 */}从 v2.1.186 版本开始，当后台子代理遇到需要权限的工具调用时，该提示会显示在您的主会话中，并指出请求权限的子代理名称。批准即可让子代理继续运行，或者按 Esc 键拒绝该次工具调用而无需停止子代理。在 v2.1.186 版本之前，后台子代理会自动拒绝任何原本会弹出提示的工具调用。

{/* min-version: 2.1.198 */}从 v2.1.198 版本开始，子代理默认在后台运行。当 Claude 在继续之前需要结果时，会在前台运行子代理。后台子代理运行时所使用的[内置工具集更小](#available-tools)（对话分支除外），并且它们会在您的主会话中显示每一条权限提示。

{/* min-version: 2.1.211 */}后台子代理的结果会在后续的轮次中作为完成通知送达 Claude。Claude 在报告子代理的结果之前会等待该通知，如果您先询问进度，它会报告子代理仍在运行。在 v2.1.211 版本之前，Claude 有时会报告尚未完成的后台子代理的结果。

您也可以自行控制这一点：

* 要求 Claude 在后台或前台运行任务
* 按 **Ctrl+B** 将正在运行的任务转入后台

{/* min-version: 2.1.208 */}已完成的后台子代理会保留在 [`/tasks`](/docs/en/commands) 的列表中，标记为已完成并排列在正在运行的任务下方，直到会话清理其任务列表。当子代理完成时，其详情视图保持打开状态。失败或被您停止的子代理会离开列表。在 v2.1.208 版本之前，已完成的子代理在完成的那一刻就会离开列表，并且其详情视图会关闭。

要禁用所有后台任务功能，请将 `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS` 环境变量设置为 `1`。参见 [环境变量](/docs/en/env-vars)。

当 [`CLAUDE_CODE_FORK_SUBAGENT`](#fork-the-current-conversation) 设置为 `1` 时，每个子代理都在后台运行，并且 frontmatter 的 `background` 字段无效，因为 fork 模式会从 `run_in_background` 工具中移除 `Agent` 参数。`CLAUDE_CODE_DISABLE_BACKGROUND_TASKS` 优先于 fork 模式，并使子代理保持在前台运行。

### 子代理中的 API 错误

{/* min-version: 2.1.199 */}从 v2.1.199 版本开始，如果子代理的运行因 API 错误（如用量限制或重复的服务器错误）而终止，它会将失败情况报告给 Claude，而不是将错误文本当作子代理的发现返回。Claude 接收到的内容取决于子代理运行的位置：

* **前台**：如果速率限制、过载或服务器错误中断了已经产生文本输出的子代理，Agent 工具会返回该部分输出，并附带一条说明，指出子代理已被中断且未完成其任务。 {/* min-version: 2.1.200 */}如果子代理未产生任何输出，或者其唯一输出是工具调用，则会以 [`Agent terminated early due to an API error`](/docs/en/errors#agent-terminated-early-due-to-an-api-error) 失败，并附带错误详情。在 v2.1.199 版本中，如果速率限制、过载或服务器错误中断了仅有工具调用形式（tool-calls-only shape）的子代理，则会返回仅包含中断说明的空的部分结果。
* **后台**：子代理会被标记为失败，并且在其结束时 Claude 收到的消息会指明 API 错误并包含子代理的最后一次输出，这样部分工作就不会丢失。

一旦底层的 API 错误清除，请要求 Claude 重试任务或 [恢复子代理](#resume-subagents)。

### 子代理输出扫描

Claude Code 会在 Claude 阅读之前扫描每个子代理的最终报告。子代理可能阅读了你从未审查的文件、网页或命令输出，来自这些来源的文本可能携带针对主对话的指令。扫描绝不会删除或重写任何内容；它会做出两种你可能会在报告中注意到的更改：

* **反斜杠插入**：扫描会将反斜杠插入到模仿 Claude Code 自身输出的文本中，例如 `<system-reminder>` 标签，或者以 `Human:` 或 `Assistant:` 开头的行，以便将模仿内容读取为普通文本，而不是被误认为对话的一部分。
* **标记行**：当报告模仿类似 `[harness: subagent output matched instruction-shaped pattern(s):` 的标签，或提及诸如 `<system-reminder>` 或 `bypassPermissions` 的权限设置时，扫描会添加一行以 `--dangerously-skip-permissions` 开头的行。提及权限设置会加上标记行，但文本本身保持原样。

扫描不会判断内容是否恶意，也不会改变报告中指令所能执行的操作：报告引导 Claude 发出的工具调用仍然会经过会话的 [权限检查](/docs/en/permissions) 和 [沙盒机制](/docs/en/sandboxing)。它不能替代 [限制子代理可以访问的内容](#control-subagent-capabilities)。

<Note>
  子代理输出扫描需要 Claude Code v2.1.210 或更高版本。
</Note>

### 常见模式

#### 隔离高吞吐量操作

子代理最有效的用途之一是隔离会产生大量输出的操作。运行测试、获取文档或处理日志文件可能会消耗大量上下文。通过将这些任务委派给子代理，冗长的输出将保留在子代理的上下文中，而只有相关的摘要返回到您的主对话中。

```text wrap theme={null}
Use a subagent to run the test suite and report only the failing tests with their error messages
```

#### 运行并行研究

对于独立的调查任务，生成多个子代理同时工作：

```text wrap theme={null}
Research the authentication, database, and API modules in parallel using separate subagents
```

每个子代理独立探索其领域，然后 Claude 综合这些发现。当研究路径互不依赖时，这种方法效果最好。

<Warning>
  当子代理完成时，其结果会返回到您的主对话中。运行多个子代理且每个子代理都返回详细结果可能会消耗大量上下文。
</Warning>

对于需要持续并行处理或超出上下文窗口的任务，[代理团队](/docs/en/agent-teams) 会为每个工作者提供其独立的上下文。

#### 链式子代理

对于多步骤的工作流程，要求 Claude 按顺序使用子代理。每个子代理完成其任务并将结果返回给 Claude，然后 Claude 将相关上下文传递给下一个子代理。

```text wrap theme={null}
Use the code-reviewer subagent to find performance issues, then use the optimizer subagent to fix them
```

### 在子代理和主对话之间做出选择

在以下情况下使用 **主对话**：

* 任务需要频繁的来回交互或迭代优化
* 多个阶段共享大量上下文，例如规划、实现和测试
* 您正在进行快速、有针对性的修改
* 延迟很重要。子代理从头开始，可能需要时间来收集上下文

在以下情况下使用 **子代理**：

* 任务产生了您在主上下文中不需要的冗长输出
* 您想要强制执行特定的工具限制或权限
* 工作是独立的并且可以返回摘要

当您想要在主对话上下文而不是孤立的子代理上下文中运行可重用的提示词或工作流时，请考虑使用 [技能](/docs/en/skills)。

对于针对对话中已有内容的快速提问，请使用 [`/btw`](/docs/en/interactive-mode#side-questions-with-%2Fbtw) 而不是子代理。它能看到您的完整上下文，但没有工具访问权限，并且答案会被丢弃，而不是添加到历史记录中。

### 让子代理生成它们自己的子代理

默认情况下，子代理可以生成自己的子代理，最多可深达主会话下方的三个层级。在达到深度限制时，Claude Code 不会将 `Agent` 工具提供给除 [fork](#fork-the-current-conversation) 之外的任何子代理，因此处于限制层级的子代理将自行完成其委派的工作并返回一份摘要。处于限制层级的 fork 会在其继承的工具列表中保留 `Agent`，但该工具会返回错误而不是生成子代理。

嵌套子代理适合处理那些本身可拆分为并行子任务的委派任务，例如审查子代理针对每项发现结果分派一个验证器，从而使中间输出永远不会进入您的主对话。只有顶层子代理的摘要会返回给您。

{/* min-version: 2.1.217 */}要更改限制，请将 [`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`](/docs/en/env-vars) 设置为您希望在主对话下方拥有的子代理层数。例如，在 [`settings.json`](/docs/en/settings) 中的此条目将嵌套限制为两层：

```json theme={null}
{
  "env": {
    "CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH": "2"
  }
}
```

使用此值，您的子代理可以委派给它们自己的第二层，而该第二层无法进一步委派。设置 `1` 以关闭嵌套。

嵌套子代理的配置方式与顶级子代理相同，并从相同的 [scopes](#choose-the-subagent-scope) 解析。为了在开启嵌套时防止某个子代理生成，例如应该保持只读的审查者，请省略 `Agent` 从其 [`tools`](#available-tools) 列表中，或者将其添加到 `disallowedTools`。

提示词输入下方的子代理面板显示了完整的树状结构：每一行显示后代的 `(+N)` 计数，并且 {/* min-version: 2.1.193 */}从 v2.1.193 版本开始，展开某一行会显示该子代理的同级和直接子级，以及返回 `main` 的路径。

<Note>
  早期版本使用了不同的默认值：

  * **v2.1.172 到 v2.1.216**：子代理默认可以嵌套，最深可达五层，并且该限制无法更改。
  * **v2.1.217 到 v2.1.218**：该限制默认为一，因此除非你主动提高限制，否则子代理无法生成自己的子代理；{/* min-version: 2.1.219 */}v2.1.219 将默认值提高到了三。
</Note>

### 会话子代理限制

三个独立的限制控制着子代理的使用，每个都有各自的变量：此限制限制了整个会话期间生成的总代理数，[并发子代理限制](#concurrent-subagent-limit)用于在运行数量过多时阻止 Claude 继续生成，而[深度限制](#let-subagents-spawn-their-own-subagents)则限制了子代理嵌套的深度。

默认情况下，Claude 每个会话最多可生成 200 个子代理。要提高此限制，请将[`CLAUDE_CODE_MAX_SUBAGENTS_PER_SESSION`](/docs/en/env-vars)设置为任意正整数；该限制没有上限，但无法关闭。需要Claude Code v2.1.212 或更高版本。

Claude 使用 Agent 工具生成的每个子代理都会计入此限制：嵌套的子代理、[分叉](#fork-the-current-conversation)以及后台子代理，包括[工作流](/docs/en/workflows)的代理使用 Agent 工具生成的子代理。你自己使用`/subtask`启动的会话内分叉也会计入：它消耗相同的预算，尽管该限制仅阻止 Claude 使用 Agent 工具生成的子代理，因此在 Claude 达到限制后，你自己的`/subtask`仍会启动。你使用`/fork`创建的会话不计入其中；它作为具有自己预算的独立后台会话运行。在 v2.1.212 之前，会话内分叉命名为`/fork`。工作流脚本使用`agent()`生成的代理不计入其中；工作流有各自的每次运行限制。已完成的子代理仍然会被计入。

当 Claude 达到此限制时，Agent 工具将失败并返回`Subagent spawn limit reached`，并且该错误会提示 Claude 直接使用其自带工具完成剩余工作。

运行[`/clear`](/docs/en/commands#all-commands)以重置计数并使用完整预算开启新的对话。如果清除后仍然存在可生成子代理的工作（例如正在运行的工作流），则计数会结转保留。

### 并发子代理限制

默认情况下，当会话中运行着 20 个子代理时，使用 Agent 工具生成另一个子代理会失败并返回`Concurrent subagent limit reached`，并且该错误会提示 Claude 不要重试。当运行计数降至限制以下时，生成将再次成功。要更改此限制，请将[`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`](/docs/en/env-vars)设置为任意正整数。激活了[ultracode](/docs/en/model-config#adjust-effort-level)的会话可豁免：该限制不适用于此类会话。需要Claude Code v2.1.217 或更高版本。

该限制仅阻止 Claude 使用 Agent 工具生成的子代理，但其他运行占用相同的槽位：

* 你使用[`/subtask`](#fork-the-current-conversation)启动的会话内分叉在其运行期间会占用一个槽位，且永远不会被此限制阻止。
* [恢复已完成的子代理](#resume-subagents)会直接获取一个新的槽位而无需检查限制，因此恢复操作可能会导致运行计数超过该限制。

其他功能运行的代理（例如[工作流](/docs/en/workflows)代理和[代理团队](/docs/en/agent-teams)队友）遵循它们各自的限制。而[会话子代理限制](#session-subagent-limit)则单独限制了 Claude 在整个会话期间生成的总数。

### 管理子代理上下文

#### 启动时加载的内容

每个子代理都会以一个全新、隔离的上下文窗口启动。它看不到你的对话历史记录、你已经调用过的技能，或是 Claude 已经读取过的文件。Claude 会撰写一条总结任务的委派消息，子代理便从这条消息开始工作。唯一的例外是 [fork](#fork-the-current-conversation)，它会继承父对话，而不是从零开始。

非分支子代理的初始上下文包含：

* **系统提示词**：代理自身的提示词加上 Claude Code 追加的环境详情，而不是完整的 Claude Code 系统提示词。自定义子代理在 [markdown body](#write-subagent-files) 或 `prompt` 字段中定义它们的提示词。内置代理具有预定义的提示词。
* **任务消息**：Claude 在交接工作时撰写的委派提示词。
* **CLAUDE.md 文件**：主对话加载的 [CLAUDE.md 层级结构](/docs/en/memory#how-claude-md-files-load) 的每一级，包括 `~/.claude/CLAUDE.md`、项目规则、`CLAUDE.local.md` 和受管理的策略文件。内置的 Explore 和 Plan 代理会跳过此项。
* **Git 状态**：在父会话开始时截取的快照。当工作目录不是 Git 仓库或 [`includeGitInstructions`](/docs/en/settings#available-settings) 为 `false` 时，此项缺失。无论如何，Explore 和 Plan 代理都会跳过此项。
* **预加载技能**：在代理的 [`skills` field](#preload-skills-into-subagents) 中命名的任何技能的完整内容。内置代理不会预加载技能。
* **同级名册**：一个系统提醒，列出了 `main` 和会话中的所有其他已命名的智能体，每一个都是一个有效的 `to` 值，用于 [`SendMessage`](#resume-subagents)。 {/* min-version: 2.1.206 */}需要 Claude Code v2.1.206 或更高版本。 只有当子智能体的工具包含 `SendMessage` 且至少有一个其他智能体拥有名称时，该名册才会出现，无论是在生成它时 Claude 为其命名，还是它作为 [智能体团队](/docs/en/agent-teams) 队友运行。 它是在子智能体启动时拍摄的快照，所以 后来命名的代理不会出现。

Explore 和 Plan 是仅有的省略 CLAUDE.md 和 git status 的子代理。没有 frontmatter 字段或针对每个代理的设置来更改哪些代理会跳过它们。

主对话会读取带有完整 CLAUDE.md 上下文的 Explore 和 Plan 结果，因此大多数规则不需要传达给子代理本身。如果某条规则必须传达，例如“忽略 `vendor/` 目录”，请在委派时给 Claude 的提示中重新表述它。

某些主对话状态永远不会传达给非分叉子代理：

* **输出风格**: 子代理运行其自身的系统提示词, 所以你的 [输出风格](/docs/en/output-styles) 不会塑造其响应, 除非在一个 [分支](#fork-the-current-conversation).
* **自动记忆**: 主对话的 [自动记忆](/docs/en/memory#auto-memory) 未被加载. 要赋予子代理其自身的持久记忆, 使用 [`memory` 字段](#enable-persistent-memory).
* **上下文窗口大小**: 子代理的上下文窗口由其自身的模型决定大小, 而非父级. 委派给一个具有较小窗口的模型会给予该子代理较小的窗口.

#### 恢复子代理

每次调用子代理都会创建一个带有全新上下文的新实例。为了继续现有子代理的工作而不是从头开始，请让 Claude 恢复它。

恢复的子代理会保留其完整的对话历史记录，包括所有先前的工具调用、结果和推理。子代理会准确地从它停止的地方继续，而不是重新开始。

当子代理完成时，Claude 会收到它的代理 ID。内置的 Explore 和 Plan 代理是一次性的，不返回代理 ID，因此它们无法被恢复；当您需要继续工作时，请使用 `general-purpose` 或自定义子代理。

Claude 使用 `SendMessage` 工具，并将代理的 ID 或名称作为 `to` 字段来恢复它。`SendMessage` 不需要启用 [agent teams](/docs/en/agent-teams)；只有结构化的团队协议消息（例如 `shutdown_request` 和 `plan_approval_response`）才需要。

要恢复子代理，请让 Claude 继续之前的工作：

```text wrap theme={null}
Use the code-reviewer subagent to review the authentication module
[Agent completes]

Continue that code review and now analyze the authorization logic
[Claude resumes the subagent with full context from previous conversation]
```

收到 `SendMessage` 的已完成子代理会在后台自动恢复，而无需新的 `Agent` 调用。这同样适用于 Claude 使用 `TaskStop` 工具停止的子代理。

{/* min-version: 2.1.191 */}从 v2.1.191 版本开始，您自己停止的子代理（通过在 `x` 中使用 `/tasks` 或在 SDK `stop_task` 请求中停止）不会自动恢复。`SendMessage` 调用会返回一个拒绝消息，告诉 Claude 代理已被取消。在子代理面板的该子代理记录中输入内容以自行恢复它，这会清除停止状态，以便后续的 `SendMessage` 调用可以再次自动恢复它。

恢复会在同一 ID 下启动代理的新运行，因此之前已失败或完成的子代理会在任务列表和 Agent SDK 的任务事件中再次显示为正在运行。在 v2.1.205 之前，当恢复的运行正在工作时，它会继续显示其先前的失败或完成状态。

{/* min-version: 2.1.199 */}从 v2.1.199 版开始，`SendMessage` 会检查某个名称是否仍然指向它在对话早先访问过的同一代理。如果有较新的代理占用了该名称，例如重用了该名称的重新生成的后台代理，Claude Code 将拒绝发送，而不是将其传递给错误的代理，并且错误会报告该名称现在指向哪个代理，以便 Claude 可以重新定向。要在较早的代理仍在运行时访问它，Claude 会使用它生成该代理时收到的代理 ID 对其进行寻址。此检查的范围仅限于当前对话，并在 `/clear` 时重置。

{/* min-version: 2.1.198 */}从 v2.1.198 版开始，子代理将来自启动它的代理的消息视为常规任务指令，包括任务中途的路线纠正，并在其自身的权限设置内对其采取行动。无论消息是由谁发送的，仍有两条限制适用：来自任何代理的消息都不算作您对挂起的权限提示的批准，并且任何代理消息都不能更改子代理的权限设置、`CLAUDE.md` 或配置。只有权限系统或您自己的消息才能授予批准。

如果您想显式地引用它，也可以向 Claude 索要代理 ID，或者在 `~/.claude/projects/{project}/{sessionId}/subagents/` 的记录文件中找到 ID。每份记录都存储为 `agent-{agentId}.jsonl`。

子代理记录独立于主对话持久保存：

* **主对话压缩**：当主对话压缩时，子代理记录不受影响。它们存储在单独的文件中。
* **会话持久化**：子代理的记录会在其会话中持久保存。你可以 [恢复子代理](#resume-subagents) 在重启 Claude Code 后通过恢复同一会话。
* **自动清理**：转录文本会基于 `cleanupPeriodDays` 设置进行清理，默认为 30 天。

#### 自动压缩

子代理支持使用与主对话相同的逻辑进行自动压缩。压缩在相同条件下触发，`CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` 也适用于子代理。有关覆盖何时生效的信息，请参见 [环境变量](/docs/en/env-vars)。

压缩事件记录在子代理对话记录文件中：

```json theme={null}
{
  "type": "system",
  "subtype": "compact_boundary",
  "compactMetadata": {
    "trigger": "auto",
    "preTokens": 167189
  }
}
```

`preTokens` 值显示在压缩发生之前使用了多少 token。

## 分叉当前对话

<Note>
  {/* min-version: 2.1.212 */}使用 `/subtask` 运行分叉子代理，需要 Claude Code v2.1.212 或更高版本。当 [代理视图关闭](/docs/en/agent-view#turn-off-agent-view) 时，`/subtask` 不可用，`/fork` 会启动分叉子代理；否则 `/fork` 将整个会话复制到新的 [后台会话](/docs/en/agent-view#from-inside-a-session) 中。

  {/* min-version: 2.1.161 */}在 v2.1.212 之前，分叉子代理命令为 `/fork`。该功能在 v2.1.161 或更高版本中默认启用；在 v2.1.117 到 v2.1.160 版本中，需要将 [`CLAUDE_CODE_FORK_SUBAGENT`](/docs/en/env-vars) 环境变量设置为 `1`，除非服务端灰度发布已启用该功能。

  让 Claude 自身生成分叉是实验性功能，可能会在未来的版本中发生变化。此功能也可能作为分阶段推出的一部分在交互式会话中启用。
</Note>

分支（fork）是一种子代理，它会继承迄今为止的整个对话，而不是从头开始。这取消了子代理通常会提供的输入隔离：分支可以看到与主会话相同的系统提示、工具、模型和消息历史记录，因此你可以交办一个次要任务给它，而无需重新解释情况。分支自身的工具调用仍然不会出现在你的对话中，并且只会返回其最终结果，因此你的主上下文窗口保持整洁。当一个命名的子代理需要太多背景信息才能发挥作用时，或者当你想要从同一起点并行尝试多种方法时，请使用分支。

无论分阶段推出情况如何，要控制分支模式，请将 [`CLAUDE_CODE_FORK_SUBAGENT`](/docs/en/env-vars) 设置为 `1` 以显式启用它，或设置为 `0` 以禁用它。该变量在交互模式下以及通过 SDK 或 `claude -p` 均受支持。

启用分支模式会在两个方面改变 Claude Code：

* Claude 可以通过显式请求 `fork` 子代理类型来生成一个分支。当 Claude 没有请求特定类型时，它仍然会获得 [general-purpose](#built-in-subagents) 子代理，而诸如 Explore 之类的命名子代理仍会像以前一样生成。
* 每个子代理都在 [background](#run-subagents-in-foreground-or-background) 中运行，无论它是分支还是命名的子代理。将 `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS` 设置为 `1` 以保持子代理同步。

你可以自己启动一个分支，在 `/subtask` 后面跟上一个任务，无论是否设置了变量。在 v2.1.161 到 v2.1.211 版本中，该命令是 `/fork`。Claude Code 根据任务的前几个词为分支命名。以下示例将对话分支出去以起草测试用例，同时你可以继续在主会话中进行实现：

```text wrap theme={null}
/subtask draft unit tests for the parser changes so far
```

该分支出现在你提示词下方的面板中，并在后台运行，而你可以继续工作。当它完成时，其结果将作为一条消息发送到你的主会话中。下一节将介绍用于在分支运行时进行监视和引导的面板控制功能。

### 观察并引导运行中的分支

运行中的分支会显示在提示词输入框下方的面板中，主会话占一行，每个分支各占一行。使用以下按键与面板交互：

| 按键       | 操作                                                             |
| :-------- | :----------------------------------------------------------------- |
| `↑` / `↓` | 在行之间移动                                                  |
| `Enter`   | 打开选定分支的对话记录并发送后续消息 |
| `x`       | 关闭已完成的分支或停止正在运行的分支                      |
| `Esc`     | 将焦点返回到提示词输入框                                   |

在打开分支或子代理的对话记录时，后续消息和 [skills](/docs/en/skills) 会发送给该代理，但内置命令仍会在您的主会话中运行。{/* min-version: 2.1.199 */}自 v2.1.199 起，在该视图中输入 `/model` 或 `/fast` 会显示一条提示，说明它更改的是主会话的模型或快速模式，而不是所查看代理的模型或快速模式，而不是静默运行。

### 分支与命名子代理有何不同

分支在创建时会继承主会话当时拥有的所有内容。命名子代理则从其自身的定义开始。

|                         | 分支                             | 命名子代理                                                                                                    |
| :---------------------- | :------------------------------- | :---------------------------------------------------------------------------------------------------------------- |
| 上下文                 | 完整的对话历史        | 带有您传递的提示词的全新上下文                                                                            |
| 系统提示词和工具 | 与主会话相同             | 来自子代理的 [definition file](#write-subagent-files), [filtered for background runs](#available-tools)    |
| 模型                   | 与主会话相同             | 来自子代理的 `model` 字段                                                                                 |
| 权限             | 提示在您的终端中显示 | [Prompts surface in your main session](#run-subagents-in-foreground-or-background) 当在后台运行时 |
| 提示词缓存            | 与主会话共享         | 独立缓存                                                                                                    |

由于分支的系统提示词和工具定义与父级相同，它的首次请求会重用父级的 [prompt cache](/docs/en/prompt-caching#subagents-and-the-cache)。这使得对于需要相同上下文的任务，创建分支比启动一个全新的子代理成本更低。

当 Claude 通过 Agent 工具创建分支时，它可以传递 `isolation: "worktree"`，以便将分支的文件编辑写入单独的 git worktree（工作树），而不是您的检出版本中。

### 限制

设置 `CLAUDE_CODE_FORK_SUBAGENT=1` 会在交互式会话、[non-interactive mode](/docs/en/headless) 和 Agent SDK 中启用分支模式；将其设置为 `0` 会禁用所有位置的分支模式，包括任何服务器端的发布。分支无法继续创建分支。

## 示例子代理

这些示例展示了构建子代理的有效模式。您可以将它们作为起点，或者使用 Claude 生成自定义版本。

<Tip>
  **最佳实践：**

  * **设计专注的子代理：**每个子代理应该擅长一个特定的任务
  * **编写详细的描述：**Claude 使用描述来决定何时进行委托
  * **限制工具访问：**仅授予必要权限以确保安全和专注
  * **提交到版本控制：**与您的团队共享项目子代理
</Tip>

### 代码审查员

一个只读子代理，审查代码而不修改它。此示例展示了如何设计一个具有受限工具访问权限的专注型子代理，不包含 Edit 和 Write 工具，并使用详细的提示来指定具体要查找什么以及如何格式化输出。

```markdown theme={null}
---
name: code-reviewer
description: Expert code review specialist. Proactively reviews code for quality, security, and maintainability. Use immediately after writing or modifying code.
tools: Read, Grep, Glob, Bash
model: inherit
---

You are a senior code reviewer ensuring high standards of code quality and security.

When invoked:
1. Run git diff to see recent changes
2. Focus on modified files
3. Begin review immediately

Review checklist:
- Code is clear and readable
- Functions and variables are well-named
- No duplicated code
- Proper error handling
- No exposed secrets or API keys
- Input validation implemented
- Good test coverage
- Performance considerations addressed

Provide feedback organized by priority:
- Critical issues (must fix)
- Warnings (should fix)
- Suggestions (consider improving)

Include specific examples of how to fix issues.
```

### 调试器

一个既能分析又能修复问题的子代理。与代码审查员不同，此子代理包含 Edit，因为修复 Bug 需要修改代码。该提示提供了从诊断到验证的清晰工作流程。

```markdown theme={null}
---
name: debugger
description: Debugging specialist for errors, test failures, and unexpected behavior. Use proactively when encountering any issues.
tools: Read, Edit, Bash, Grep, Glob
---

You are an expert debugger specializing in root cause analysis.

When invoked:
1. Capture error message and stack trace
2. Identify reproduction steps
3. Isolate the failure location
4. Implement minimal fix
5. Verify solution works

Debugging process:
- Analyze error messages and logs
- Check recent code changes
- Form and test hypotheses
- Add strategic debug logging
- Inspect variable states

For each issue, provide:
- Root cause explanation
- Evidence supporting the diagnosis
- Specific code fix
- Testing approach
- Prevention recommendations

Focus on fixing the underlying issue, not the symptoms.
```

### 数据科学家

一个用于数据分析工作的领域专用子代理。此示例展示了如何为典型编码任务之外的专业化工作流程创建子代理。它显式设置了 `model: sonnet` 以进行更强大的分析。

```markdown theme={null}
---
name: data-scientist
description: Data analysis expert for SQL queries, BigQuery operations, and data insights. Use proactively for data analysis tasks and queries.
tools: Bash, Read, Write
model: sonnet
---

You are a data scientist specializing in SQL and BigQuery analysis.

When invoked:
1. Understand the data analysis requirement
2. Write efficient SQL queries
3. Use BigQuery command line tools (bq) when appropriate
4. Analyze and summarize results
5. Present findings clearly

Key practices:
- Write optimized SQL queries with proper filters
- Use appropriate aggregations and joins
- Include comments explaining complex logic
- Format results for readability
- Provide data-driven recommendations

For each analysis:
- Explain the query approach
- Document any assumptions
- Highlight key findings
- Suggest next steps based on data

Always ensure queries are efficient and cost-effective.
```

### 数据库查询验证器

一个允许 Bash 访问但验证命令以仅允许只读 SQL 查询的子代理。此示例展示了如何使用 `PreToolUse` 钩子进行条件验证，当您需要比 `tools` 字段所提供的更精细的控制时。

```markdown theme={null}
---
name: db-reader
description: Execute read-only database queries. Use when analyzing data or generating reports.
tools: Bash
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-readonly-query.sh"
---

You are a database analyst with read-only access. Execute SELECT queries to answer questions about the data.

When asked to analyze data:
1. Identify which tables contain the relevant data
2. Write efficient SELECT queries with appropriate filters
3. Present results clearly with context

You cannot modify data. If asked to INSERT, UPDATE, DELETE, or modify schema, explain that you only have read access.
```

Claude Code [以 JSON 格式传递钩子输入](/docs/en/hooks#pretooluse-input) 通过 stdin 传递给钩子命令。验证脚本读取此 JSON，提取正在执行的命令，并将其与 SQL 写操作列表进行检查。如果检测到写操作，脚本 [以退出码 2 退出](/docs/en/hooks#exit-code-2-behavior-per-event) 以阻止执行，并通过 stderr 向 Claude 返回错误消息。

在项目中的任意位置创建验证脚本。该路径必须与钩子配置中的 `command` 字段匹配：

```bash theme={null}
#!/bin/bash
# Blocks SQL write operations, allows SELECT queries

# Read JSON input from stdin

INPUT=$(cat)

# Extract the command field from tool_input using jq

COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

if [ -z "$COMMAND" ]; then
  exit 0
fi

# Block write operations (case-insensitive)

if echo "$COMMAND" | grep -iE '\b(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE|REPLACE|MERGE)\b' > /dev/null; then
  echo "Blocked: Write operations not allowed. Use SELECT queries only." >&2
  exit 2
fi

exit 0
```

在 macOS 和 Linux 上，将脚本设置为可执行：

```bash theme={null}
chmod +x ./scripts/validate-readonly-query.sh
```

在 Windows 上，使用 PowerShell 编写验证脚本，并在钩子条目中添加 `shell: powershell`。参见 [在 PowerShell 中运行钩子](/docs/en/hooks#windows-powershell-tool)。

钩子通过 stdin 接收 JSON，其中 Bash 命令位于 `tool_input.command` 中。退出码 2 会阻止操作并将错误消息反馈给 Claude。参见 [钩子](/docs/en/hooks#exit-code-output) 了解退出码的详细信息，参见 [钩子输入](/docs/en/hooks#pretooluse-input) 了解完整的输入模式。

## 后续步骤

既然您已经了解了子代理，可以探索以下相关功能：

* [使用插件分发子代理](/docs/en/plugins) 以在团队或项目之间共享子代理
* [以编程方式运行 Claude Code](/docs/en/headless) 使用 Agent SDK 进行 CI/CD 和自动化
* [使用 MCP 服务器](/docs/en/mcp) 让子代理访问外部工具和数据

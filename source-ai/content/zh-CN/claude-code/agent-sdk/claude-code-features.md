---
title: 在 SDK 中使用 Claude Code 功能
source_id: claude-code/agent-sdk/claude-code-features
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/agent-sdk/claude-code-features
owner: Anthropic
content_sha256: 70e0525878ffb62188f4b47aba4bdfa086be5add0079d2e70b3d0049de58ac1d
translation_of: claude-code/agent-sdk/claude-code-features
translation_model: k3
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/agent-sdk/claude-code-features)

Content owner: Anthropic

> ## 文档索引
> 在此获取完整的文档索引：https://code.claude.com/docs/llms.txt
> 在进一步探索之前，使用此文件来发现所有可用页面。

# 在 SDK 中使用 Claude Code 功能

> 将项目指令、技能、钩子和其他 Claude Code 功能加载到你的 SDK 智能体中。

Agent SDK 与 Claude Code 构建在相同的基础之上，这意味着你的 SDK 智能体可以访问相同的基于文件系统的功能：项目指令（`CLAUDE.md` 和规则）、技能、钩子等。

当你省略 `settingSources` 时，`query()` 会读取与 Claude Code CLI 相同的文件系统设置：用户、项目和本地设置、CLAUDE.md 文件，以及 `.claude/` 技能、智能体和命令。要在没有这些内容的情况下运行，请传递 `settingSources: []`，这会将智能体限制为你以编程方式配置的内容。无论此选项如何，托管策略设置和全局 `~/.claude.json` 配置都会被读取。参见 [settingSources 不控制的内容](#what-settingsources-does-not-control)。

有关每个功能的作用以及何时使用它的概念性概述，参见 [扩展 Claude Code](/docs/en/features-overview)。

## 使用 settingSources 控制文件系统设置

设置来源选项（Python 中的 [`setting_sources`](/docs/en/agent-sdk/python#claudeagentoptions)，TypeScript 中的 [`settingSources`](/docs/en/agent-sdk/typescript#settingsource)）控制 SDK 加载哪些基于文件系统的设置。传递显式列表以选择特定的来源，或传递空数组以禁用用户、项目和本地设置。

此示例通过将 `settingSources` 设置为 `["user", "project"]` 来同时加载用户级和项目级设置：

<CodeGroup>
  ```python Python theme={null}
  from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, ResultMessage
  import asyncio


  async def main():
      async for message in query(
          prompt="Help me refactor the auth module",
          options=ClaudeAgentOptions(
              # "user" loads from ~/.claude/, "project" loads from ./.claude/ in cwd.
              # Together they give the agent access to CLAUDE.md, skills, hooks, and
              # permissions from both locations.
              setting_sources=["user", "project"],
              allowed_tools=["Read", "Edit", "Bash"],
          ),
      ):
          if isinstance(message, AssistantMessage):
              for block in message.content:
                  if hasattr(block, "text"):
                      print(block.text)
          if isinstance(message, ResultMessage) and message.subtype == "success":
              print(f"\nResult: {message.result}")


  asyncio.run(main())
  ```

  ```typescript TypeScript theme={null}
  import { query } from "@anthropic-ai/claude-agent-sdk";

  for await (const message of query({
    prompt: "Help me refactor the auth module",
    options: {
      // "user" loads from ~/.claude/, "project" loads from ./.claude/ in cwd.
      // Together they give the agent access to CLAUDE.md, skills, hooks, and
      // permissions from both locations.
      settingSources: ["user", "project"],
      allowedTools: ["Read", "Edit", "Bash"]
    }
  })) {
    if (message.type === "assistant") {
      for (const block of message.message.content) {
        if (block.type === "text") console.log(block.text);
      }
    }
    if (message.type === "result" && message.subtype === "success") {
      console.log(`\nResult: ${message.result}`);
    }
  }
  ```
</CodeGroup>

运行时，助手的响应会打印到标准输出，运行完成后会打印一行最终结果。

每个来源从特定位置加载设置，其中 `<cwd>` 是你通过 `cwd` 选项传递的工作目录，如果未设置则为进程的当前目录。有关完整的类型定义，参见 [`SettingSource`](/docs/en/agent-sdk/typescript#settingsource)（TypeScript）或 [`SettingSource`](/docs/en/agent-sdk/python#settingsource)（Python）。

| 来源      | 加载内容                                                                                   | 位置                                                                                                                                                                            |
| :---------- | :---------------------------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `"project"` | 项目级 CLAUDE.md、`.claude/rules/*.md`、项目技能、项目钩子、项目 `settings.json` | `<cwd>/.claude/` 用于 `settings.json` 和钩子；`<cwd>` 及其每个父目录用于 CLAUDE.md 和规则；`<cwd>` 及其向上至仓库根目录的每个父目录用于技能 |
| `"user"`    | 用户级 CLAUDE.md、`~/.claude/rules/*.md`、用户技能、用户设置                              | `~/.claude/`                                                                                                                                                                        |
| `"local"`   | CLAUDE.local.md、`.claude/settings.local.json`                                                  | `<cwd>/.claude/` 用于 `settings.local.json`；`<cwd>` 及其每个父目录用于 CLAUDE.local.md                                                                                  |

省略 `settingSources` 等同于 `["user", "project", "local"]`。

`cwd` 选项决定 SDK 在何处查找项目级输入。CLAUDE.md 和规则从 `<cwd>` 及其每个父目录加载。技能从 `<cwd>` 及其向上至仓库根目录的每个父目录加载。项目 `settings.json` 和钩子仅从 `<cwd>/.claude/` 加载，不回退到父目录。

### settingSources 不控制的内容

`settingSources` 涵盖用户设置、项目设置和本地设置。无论其值如何，以下输入始终会被读取：

| 输入                                                              | 行为                                                                                                                                                                                                         | 禁用方式                                                                                                                                                                         |
| :----------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 托管策略设置                                            | 端点托管的策略（例如 MDM plist、注册表策略或托管设置文件）从主机加载。[服务器托管设置](/docs/en/server-managed-settings) 在会话通过组织 OAuth 登录或直接配置的 API 密钥进行身份验证时，于[符合条件的配置](/docs/en/server-managed-settings#platform-availability)上获取 | 端点策略：从主机移除托管设置文件、plist 或注册表策略。服务器托管设置：由您的组织管理员控制；无法从 SDK 禁用 |
| `~/.claude.json` 全局配置                                     | 始终读取                                                                                                                                                                                                         | 在 `env` 中使用 `CLAUDE_CONFIG_DIR` 重新定位                                                                                                                                         |
| 位于 `~/.claude/projects/<project>/memory/` 的自动记忆              | 在会话开始时加载到系统提示中。智能体使用标准的 `Write` 和 `Edit` 工具（而非专用记忆工具）向其中写入新记忆，因此必须启用这些工具，智能体才能保存记忆                                                                                                                                    | 在设置中设置 `autoMemoryEnabled: false`，或在 `env` 中设置 `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`                                                                                        |
| [claude.ai MCP 连接器](/docs/en/mcp#use-mcp-servers-from-claude-ai) | 当会话通过您的 claude.ai 登录进行身份验证时加载。当 `CLAUDE_CODE_OAUTH_TOKEN` 持有来自 [`claude setup-token`](/docs/en/authentication#generate-a-long-lived-token) 的令牌时不会加载，该令牌只能发出模型请求。传递 `mcpServers: {}` 不会抑制连接器                                                                  | 在设置中设置 `strictMcpConfig: true`、[`disableClaudeAiConnectors: true`](/docs/en/mcp#disable-claude-ai-connectors)，或在 `env` 中设置 `ENABLE_CLAUDEAI_MCP_SERVERS=false`                |

<Warning>
  不要依赖默认的 `query()` 选项来实现多租户隔离。因为无论 `settingSources` 如何设置,上述输入都会被读取,因此 SDK 进程可能会获取主机级别的配置和按目录划分的记忆。对于多租户部署,请在每个租户自己的文件系统中运行,并设置 `settingSources: []`，同时在 `env` 中设置 `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`。[服务器托管的设置](/docs/en/server-managed-settings) 会在进程使用组织凭据进行身份验证时获取;文件系统隔离不会移除它们。请参阅 [安全部署](/docs/en/agent-sdk/secure-deployment)。
</Warning>

## 项目指令(CLAUDE.md 和规则)

`CLAUDE.md` 文件和 `.claude/rules/*.md` 文件为你的智能体提供关于项目的持久上下文:编码规范、构建命令、架构决策和指令。当 `settingSources` 包含 `"project"` 时(如上面的示例所示),SDK 会在会话开始时将这些文件加载到上下文中。然后,智能体会遵循你的项目规范,而无需你在每次提示中重复说明。

### CLAUDE.md 加载位置

| 级别                 | 位置                                                                      | 加载时机                                                                                         |
| :-------------------- | :---------------------------------------------------------------------------- | :-------------------------------------------------------------------------------------------------- |
| 项目(根目录)        | `<cwd>/CLAUDE.md` 或 `<cwd>/.claude/CLAUDE.md`                                | `settingSources` 包含 `"project"`                                                               |
| 项目规则         | `<cwd>/.claude/rules/*.md` 和每个父目录中的 `.claude/rules/*.md` | `settingSources` 包含 `"project"`                                                               |
| 项目(父目录) | `cwd` 之上的目录中的 `CLAUDE.md` 文件                                  | `settingSources` 包含 `"project"`,在会话开始时加载                                      |
| 项目(子目录)  | `cwd` 的子目录中的 `CLAUDE.md` 文件                                  | `settingSources` 包含 `"project"`,当智能体读取该子树中的文件时按需加载 |
| 本地                 | `<cwd>/CLAUDE.local.md` 和每个父目录中的 `CLAUDE.local.md`       | `settingSources` 包含 `"local"`                                                                 |
| 用户                  | `~/.claude/CLAUDE.md`                                                         | `settingSources` 包含 `"user"`                                                                  |
| 用户规则            | `~/.claude/rules/*.md`                                                        | `settingSources` 包含 `"user"`                                                                  |

所有级别都是叠加的:如果项目级和用户级的 CLAUDE.md 文件同时存在,智能体会同时看到两者。各级别之间没有硬性的优先级规则;如果指令冲突,结果取决于 Claude 如何解读它们。请编写不冲突的规则,或者在更具体的文件中明确说明优先级("这些项目指令覆盖任何冲突的用户级默认设置")。

<Tip>
  你也可以通过 `systemPrompt` 直接注入上下文,而不使用 CLAUDE.md 文件。请参阅 [修改系统提示](/docs/en/agent-sdk/modifying-system-prompts)。当你希望在交互式 Claude Code 会话和你的 SDK 智能体之间共享相同的上下文时,请使用 CLAUDE.md。
</Tip>

有关如何组织和构建 CLAUDE.md 内容,请参阅 [管理 Claude 的记忆](/docs/en/memory)。

## 技能

技能是为您的智能体提供专业知识和可调用工作流的 Markdown 文件。与 `CLAUDE.md`（每次会话都会加载）不同，技能按需加载。智能体在启动时接收技能描述，并在相关时加载完整内容。

技能通过 `settingSources` 从文件系统中发现。当省略 `query()` 上的 `skills` 选项时，发现的用户和项目技能将被启用，且 Skill 工具可用，与 CLI 行为一致。要控制启用哪些技能，请将 `skills` 传递为 `"all"`、技能名称列表，或传递 `[]` 以禁用全部。当设置了 `skills` 时，SDK 会自动将 Skill 工具添加到 `allowedTools`。如果您还传递了显式的 `tools` 列表，请在该列表中包含 `"Skill"`，以便 Claude 能够调用技能。

<CodeGroup>
  ```python Python theme={null}
  from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage
  import asyncio


  # Skills in .claude/skills/ are discovered automatically
  # when settingSources includes "project"
  async def main():
      async for message in query(
          prompt="Review this PR using our code review checklist",
          options=ClaudeAgentOptions(
              setting_sources=["user", "project"],
              skills="all",
              allowed_tools=["Read", "Grep", "Glob"],
          ),
      ):
          if isinstance(message, ResultMessage) and message.subtype == "success":
              print(message.result)


  asyncio.run(main())
  ```

  ```typescript TypeScript theme={null}
  import { query } from "@anthropic-ai/claude-agent-sdk";

  // Skills in .claude/skills/ are discovered automatically
  // when settingSources includes "project"
  for await (const message of query({
    prompt: "Review this PR using our code review checklist",
    options: {
      settingSources: ["user", "project"],
      skills: "all",
      allowedTools: ["Read", "Grep", "Glob"]
    }
  })) {
    if (message.type === "result" && message.subtype === "success") {
      console.log(message.result);
    }
  }
  ```
</CodeGroup>

<Note>
  技能必须作为文件系统工件（`.claude/skills/<name>/SKILL.md`）创建。SDK 没有用于注册技能的编程 API。完整详情请参阅 [SDK 中的 Agent 技能](/docs/en/agent-sdk/skills)。
</Note>

有关创建和使用技能的更多信息，请参阅 [SDK 中的 Agent 技能](/docs/en/agent-sdk/skills)。

## 钩子

SDK 支持两种定义钩子的方式，并且它们会并存运行：

* **文件系统钩子：** 在 `settings.json` 中定义的 shell 命令，当 `settingSources` 包含相关来源时加载。这些就是你为 [交互式 Claude Code 会话](/docs/en/hooks-guide) 配置的同一批钩子。
* **程序化钩子：** 直接传递给 `query()` 的回调函数。它们在你的应用程序进程中运行，并可返回结构化决策。请参阅[使用钩子控制执行](/docs/en/agent-sdk/hooks)。

两种类型都会在同一个钩子生命周期中执行。如果你已经在项目的 `.claude/settings.json` 中配置了钩子，并且设置了 `settingSources: ["project"]`，那么这些钩子会在 SDK 中自动运行，无需额外配置。

钩子回调接收工具输入并返回一个决策字典。返回 `{}` 表示允许该工具继续执行。要阻止执行，请返回一个带有 `permissionDecision: "deny"` 和 `permissionDecisionReason` 的 `hookSpecificOutput` 对象。该原因会作为工具结果发送给 Claude。顶层 `decision` 和 `reason` 字段对 `PreToolUse` 已弃用。完整回调签名和返回类型请参阅[钩子指南](/docs/en/agent-sdk/hooks)。

<CodeGroup>
  ```python Python theme={null}
  from claude_agent_sdk import query, ClaudeAgentOptions, HookMatcher, ResultMessage
  import asyncio


  # PreToolUse hook callback. Positional args:
  #   input_data: HookInput dict with tool_name, tool_input, hook_event_name
  #   tool_use_id: str | None, the ID of the tool call being intercepted
  #   context: HookContext, reserved for future abort-signal support
  async def audit_bash(input_data, tool_use_id, context):
      command = input_data.get("tool_input", {}).get("command", "")
      if "rm -rf" in command:
          return {
              "hookSpecificOutput": {
                  "hookEventName": "PreToolUse",
                  "permissionDecision": "deny",
                  "permissionDecisionReason": "Destructive command blocked",
              }
          }
      return {}  # Empty dict: allow the tool to proceed


  # Filesystem hooks from .claude/settings.json run automatically
  # when settingSources loads them. You can also add programmatic hooks:
  async def main():
      async for message in query(
          prompt="Refactor the auth module",
          options=ClaudeAgentOptions(
              setting_sources=["project"],  # Loads hooks from .claude/settings.json
              hooks={
                  "PreToolUse": [
                      HookMatcher(matcher="Bash", hooks=[audit_bash]),
                  ]
              },
          ),
      ):
          if isinstance(message, ResultMessage) and message.subtype == "success":
              print(message.result)


  asyncio.run(main())
  ```

  ```typescript TypeScript theme={null}
  import { query, type HookInput, type HookJSONOutput } from "@anthropic-ai/claude-agent-sdk";

  // PreToolUse hook callback. HookInput is a discriminated union on
  // hook_event_name, so narrowing on it gives TypeScript the right
  // tool_input shape for this event.
  const auditBash = async (input: HookInput): Promise<HookJSONOutput> => {
    if (input.hook_event_name !== "PreToolUse") return {};
    const toolInput = input.tool_input as { command?: string };
    if (toolInput.command?.includes("rm -rf")) {
      return {
        hookSpecificOutput: {
          hookEventName: "PreToolUse",
          permissionDecision: "deny",
          permissionDecisionReason: "Destructive command blocked",
        },
      };
    }
    return {}; // Empty object: allow the tool to proceed
  };

  // Filesystem hooks from .claude/settings.json run automatically
  // when settingSources loads them. You can also add programmatic hooks:
  for await (const message of query({
    prompt: "Refactor the auth module",
    options: {
      settingSources: ["project"], // Loads hooks from .claude/settings.json
      hooks: {
        PreToolUse: [{ matcher: "Bash", hooks: [auditBash] }]
      }
    }
  })) {
    if (message.type === "result" && message.subtype === "success") {
      console.log(message.result);
    }
  }
  ```
</CodeGroup>

### 何时使用哪种钩子类型

| 钩子类型                                 | 适用场景                                                                                                                                                                                                                                                                                                                                                                                             |
| :---------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **文件系统** (`settings.json`)          | 在 CLI 和 SDK 会话之间共享钩子。支持 `"command"`（shell 脚本）、`"http"`（POST 到某个端点）、`"mcp_tool"`（调用已连接 MCP 服务器的工具）、`"prompt"`（LLM 评估提示词）以及 `"agent"`（生成验证子智能体）。这些钩子会在主智能体及其生成的任何子智能体中触发。 |
| **程序化**（`query()` 中的回调） | 特定于应用程序的逻辑、结构化决策以及进程内集成。这些钩子同样会在子智能体内部触发。钩子输入（即回调的第一个参数）带有 `agent_id` 和 `agent_type` 字段，用于标识触发钩子的智能体。                                                          |

<Note>
  TypeScript SDK 支持比 Python 更多的钩子事件，包括 `SessionStart`、`SessionEnd`、`TeammateIdle` 和 `TaskCompleted`。完整的事件兼容性表请参阅 [钩子指南](/docs/en/agent-sdk/hooks)。
</Note>

有关程序化钩子的完整详细信息，请参阅 [使用钩子控制执行](/docs/en/agent-sdk/hooks)。有关文件系统钩子的语法，请参阅 [钩子](/docs/en/hooks)。

## 选择合适的功能

Agent SDK 为你提供了多种扩展智能体行为的方式。如果你不确定该用哪一种，下面的表格将常见目标映射到对应的方法。

| 你想要……                                                                                    | 使用                                           | SDK 接口                                                                                                                                                    |
| :------------------------------------------------------------------------------------------------ | :-------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 设置你的智能体始终遵循的项目约定                                                 | [CLAUDE.md](/docs/en/memory)                       | `settingSources: ["project"]` 会自动加载它                                                                                                           |
| 为智能体提供在相关时才加载的参考资料                                          | [技能（Skills）](/docs/en/agent-sdk/skills)                | `settingSources` + `skills` 选项                                                                                                                             |
| 运行可复用的工作流（部署、审查、发布）                                                 | [用户可调用的技能](/docs/en/agent-sdk/skills) | `settingSources` + `skills` 选项                                                                                                                             |
| 将一个隔离的子任务委派给全新的上下文（调研、审查）                                | [子智能体（Subagents）](/docs/en/agent-sdk/subagents)          | `agents` 参数 + `allowedTools: ["Agent"]`                                                                                                                 |
| 协调多个 Claude Code 实例，共享任务列表并进行智能体间直接消息传递 | [智能体团队](/docs/en/agent-teams)                | 不通过 SDK 选项直接配置。智能体团队是一个 CLI 功能，其中一个会话担任团队负责人，协调各个独立成员之间的工作 |
| 在工具调用上运行确定性逻辑（审计、拦截、转换）                                   | [钩子（Hooks）](/docs/en/agent-sdk/hooks)                  | `hooks` 参数配合回调函数，或通过 `settingSources` 加载的 shell 脚本                                                                                 |
| 让 Claude 以结构化工具方式访问外部服务                                         | [MCP](/docs/en/agent-sdk/mcp)                      | `mcpServers` 参数                                                                                                                                         |

<Tip>
  **子智能体与智能体团队的对比：** 子智能体是短暂且隔离的：全新对话、单个任务、向父级返回摘要。智能体团队则协调多个独立的 Claude Code 实例，它们共享任务列表并直接互相发送消息。智能体团队是一个 CLI 功能。详情请参阅 [子智能体会继承什么](/docs/en/agent-sdk/subagents#what-subagents-inherit) 和 [智能体团队对比](/docs/en/agent-teams#compare-with-subagents)。
</Tip>

你启用的每一项功能都会占用智能体的上下文窗口。有关每项功能的开销以及这些功能如何协同叠加，请参阅 [扩展 Claude Code](/docs/en/features-overview#understand-context-costs)。

## 相关资源

* [扩展 Claude Code](/docs/en/features-overview): 所有扩展功能的概念概览，包含对比表和上下文成本分析
* [SDK 中的技能](/docs/en/agent-sdk/skills): 以编程方式使用技能的完整指南
* [子智能体](/docs/en/agent-sdk/subagents): 定义并调用用于隔离子任务的子智能体
* [钩子](/docs/en/agent-sdk/hooks): 在关键执行点拦截并控制智能体行为
* [权限](/docs/en/agent-sdk/permissions): 使用模式、规则和回调控制工具访问
* [系统提示](/docs/en/agent-sdk/modifying-system-prompts): 在不使用 CLAUDE.md 文件的情况下注入上下文

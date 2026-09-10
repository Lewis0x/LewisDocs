---
title: SDK 中的子代理
source_id: claude-code/agent-sdk/subagents
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/agent-sdk/subagents
owner: Anthropic
content_sha256: 565414be8c07f131a16054c785e56c1d4d1189ebb386c84f17a558859bc28c98
translation_of: claude-code/agent-sdk/subagents
translation_model: k3
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/agent-sdk/subagents)

Content owner: Anthropic

> ## 文档索引
> 在此获取完整的文档索引：https://code.claude.com/docs/llms.txt
> 使用此文件在进一步探索之前发现所有可用的页面。

# SDK 中的子代理

> 定义并调用子代理，以在 Claude Agent SDK 应用中隔离上下文、并行运行任务并应用专门的指令。

子代理是主代理可以生成的独立代理实例，用于处理专注的子任务。
使用它们可以隔离上下文、并行运行多个分析，并应用专门的指令，而无需增加主代理的提示内容。

本指南介绍如何使用 `agents` 参数在 SDK 中定义和使用子代理。

## 概述

你可以通过三种方式创建子代理：

* **以编程方式**：在你的 `query()` 选项中使用 `agents` 参数。参见 [TypeScript](/docs/en/agent-sdk/typescript#agentdefinition) 和 [Python](/docs/en/agent-sdk/python#agentdefinition) 参考文档
* **基于文件系统**：在 `.claude/agents/` 目录中以 markdown 文件形式定义代理。参见 [以文件形式定义子代理](/docs/en/sub-agents)
* **内置通用型**：Claude 可以随时通过 Agent 工具调用内置的 `general-purpose` 子代理，而无需你定义任何内容

本指南重点介绍编程方式，这是 SDK 应用的推荐做法。

当你定义子代理后，Claude 会根据每个子代理的 `description` 字段决定是否调用它们。编写清晰的描述来说明何时使用该子代理，Claude 就会自动委派适当的任务。你也可以在提示中按名称显式请求某个子代理，例如“使用 code-reviewer 代理来……”。

## 使用子代理的好处

### 上下文隔离

每个子代理都在自己全新的会话中运行。中间的工具调用和结果都保留在子代理内部；只有它的最终消息会返回给父代理。参见 [子代理继承的内容](#what-subagents-inherit)，了解子代理上下文中确切包含的内容。

**示例：** 一个 `research-assistant` 子代理可以探索数十个文件，而这些内容都不会累积到主会话中。父代理收到的是简洁的摘要，而不是子代理读取的每个文件。

### 并行化

多个子代理可以并发运行，因此独立的子任务在最慢的一个所需的时间内完成，而不是所有任务时间的总和。

**示例：** 在代码审查期间，你可以同时运行 `style-checker`、`security-scanner` 和 `test-coverage` 子代理，而不是按顺序运行。

### 专门的指令和知识

每个子代理都可以拥有量身定制的系统提示，包含特定的专业知识、最佳实践和约束条件。

**示例：** 一个 `database-migration` 子代理可以掌握关于 SQL 最佳实践、回滚策略和数据完整性检查的详细知识，而这些内容放在主代理的指令中只会是不必要的干扰。

### 工具限制

子代理可以被限制为只能使用特定工具，从而降低意外操作的风险。

**示例：** 一个 `doc-reviewer` 子代理可能只能访问 Read 和 Grep 工具，确保它可以进行分析，但绝不会意外修改你的文档文件。

## 创建子代理

### 以编程方式定义（推荐）

使用 `agents` 参数直接在代码中定义子代理。Claude 通过 `Agent` 工具调用子代理，因此在 `allowedTools` 中包含 `Agent` 可以自动批准子代理调用，而无需权限提示。

本页的大多数示例仅打印最终结果。要确认 Claude 是委派给了子代理而非直接回答，请参阅 [检测子代理调用](#detect-subagent-invocation)。

此示例创建两个子代理：一个具有只读访问权限的代码审查员和一个可以执行命令的测试运行器。

<CodeGroup>
  ```python Python theme={null}
  import asyncio
  from claude_agent_sdk import query, ClaudeAgentOptions, AgentDefinition


  async def main():
      async for message in query(
          prompt="Review the authentication module for security issues",
          options=ClaudeAgentOptions(
              # Auto-approve these tools, including Agent for subagent invocation
              allowed_tools=["Read", "Grep", "Glob", "Agent"],
              agents={
                  "code-reviewer": AgentDefinition(
                      # description tells Claude when to use this subagent
                      description="Expert code review specialist. Use for quality, security, and maintainability reviews.",
                      # prompt defines the subagent's behavior and expertise
                      prompt="""You are a code review specialist with expertise in security, performance, and best practices.

  When reviewing code:
  - Identify security vulnerabilities
  - Check for performance issues
  - Verify adherence to coding standards
  - Suggest specific improvements

  Be thorough but concise in your feedback.""",
                      # tools restricts what the subagent can do (read-only here)
                      tools=["Read", "Grep", "Glob"],
                      # model overrides the default model for this subagent
                      model="sonnet",
                  ),
                  "test-runner": AgentDefinition(
                      description="Runs and analyzes test suites. Use for test execution and coverage analysis.",
                      prompt="""You are a test execution specialist. Run tests and provide clear analysis of results.

  Focus on:
  - Running test commands
  - Analyzing test output
  - Identifying failing tests
  - Suggesting fixes for failures""",
                      # Bash access lets this subagent run test commands
                      tools=["Bash", "Read", "Grep"],
                  ),
              },
          ),
      ):
          if hasattr(message, "result"):
              print(message.result)


  asyncio.run(main())
  ```

  ```typescript TypeScript theme={null}
  import { query } from "@anthropic-ai/claude-agent-sdk";

  for await (const message of query({
    prompt: "Review the authentication module for security issues",
    options: {
      // Auto-approve these tools, including Agent for subagent invocation
      allowedTools: ["Read", "Grep", "Glob", "Agent"],
      agents: {
        "code-reviewer": {
          // description tells Claude when to use this subagent
          description:
            "Expert code review specialist. Use for quality, security, and maintainability reviews.",
          // prompt defines the subagent's behavior and expertise
          prompt: `You are a code review specialist with expertise in security, performance, and best practices.

  When reviewing code:
  - Identify security vulnerabilities
  - Check for performance issues
  - Verify adherence to coding standards
  - Suggest specific improvements

  Be thorough but concise in your feedback.`,
          // tools restricts what the subagent can do (read-only here)
          tools: ["Read", "Grep", "Glob"],
          // model overrides the default model for this subagent
          model: "sonnet"
        },
        "test-runner": {
          description:
            "Runs and analyzes test suites. Use for test execution and coverage analysis.",
          prompt: `You are a test execution specialist. Run tests and provide clear analysis of results.

  Focus on:
  - Running test commands
  - Analyzing test output
  - Identifying failing tests
  - Suggesting fixes for failures`,
          // Bash access lets this subagent run test commands
          tools: ["Bash", "Read", "Grep"]
        }
      }
    }
  })) {
    if ("result" in message) console.log(message.result);
  }
  ```
</CodeGroup>

### AgentDefinition 配置

| 字段             | 类型                                                        | 必填 | 描述                                                                                                                                                                                                         |
| :---------------- | :---------------------------------------------------------- | :------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `description`     | `string`                                                    | 是      | 何时使用此代理的自然语言描述                                                                                                                                                                           |
| `prompt`          | `string`                                                    | 是      | 定义代理角色和行为的系统提示词                                                                                                                                                                         |
| `tools`           | `string[]`                                                  | 否       | 允许的工具名称数组。如果省略，则继承子代理可用的[所有工具](/docs/en/sub-agents#available-tools)                                                                                                            |
| `disallowedTools` | `string[]`                                                  | 否       | 要从代理工具集中移除的工具名称数组。也接受 MCP 服务器级模式：`mcp__server` 或 `mcp__server__*` 移除该服务器的所有工具，`mcp__*` 移除来自任何服务器的所有 MCP 工具 |
| `model`           | `string`                                                    | 否       | 此代理的模型覆盖。接受别名，如 `'fable'`、`'opus'`、`'sonnet'`、`'haiku'`、`'inherit'`，或完整的模型 ID。如果省略，则默认使用主模型                                                           |
| `skills`          | `string[]`                                                  | 否       | 启动时预加载到代理上下文中的技能名称列表。未列出的技能仍可通过 Skill 工具调用                                                                                                      |
| `memory`          | `'user' \| 'project' \| 'local'`                            | 否       | 此代理的记忆来源                                                                                                                                                                                                     |
| `mcpServers`      | `(string \| object)[]`                                      | 否       | 此代理可用的 MCP 服务器，按名称或内联配置指定                                                                                                                                                                    |
| `initialPrompt`   | `string`                                                    | 否       | 当此代理作为主线程代理运行时，作为第一个用户回合自动提交。当该代理作为子代理调用时将被忽略                                                                                             |
| `maxTurns`        | `number`                                                    | 否       | 代理停止前的最大自主回合数                                                                                                                                                                           |
| `background`      | `boolean`                                                   | 否       | 调用时将以此代理作为非阻塞后台任务运行                                                                                                                                                                    |
| `effort`          | `'low' \| 'medium' \| 'high' \| 'xhigh' \| 'max' \| number` | 否       | 此代理的推理力度级别                                                                                                                                                                                            |
| `permissionMode`  | `PermissionMode`                                            | 否       | 此代理内工具执行的权限模式                                                                                                                                                                             |

在 Python SDK 中，多单词字段名（如 `disallowedTools` 和 `mcpServers`）保留其 camelCase 拼写以匹配传输格式，而不是遵循 Python 的 snake\_case 约定。详情请参阅 [`AgentDefinition` 参考文档](/docs/en/agent-sdk/python#agentdefinition)。

在 Claude Code v2.1.198 中，两项子代理行为发生了变化：

* 子代理默认在后台运行。省略 [`run_in_background`](/docs/en/agent-sdk/typescript) 输入的 Agent 工具调用会启动一个后台子代理，而当 Claude 需要在继续之前获取结果时会设置 `run_in_background: false`。在 v2.1.198 之前，省略 `run_in_background` 会同步运行子代理。将 `background` 字段设置为 `true` 可强制特定代理进行后台执行，无论 Claude 请求什么。
* 子代理继承主会话的扩展思考配置。在早期版本中，无论主会话的设置如何，子代理内部的扩展思考都会被禁用。

<Note>
  {/* min-version: 2.1.219 */}默认情况下，子代理可以生成自己的子代理，最多可达主对话之下三层。{/* min-version: 2.1.217 */}要更改此限制，请将 [`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`](/docs/en/env-vars) 设置为你希望在主对话之下允许的子代理层数，或设置为 `1` 以关闭嵌套；请参阅[嵌套子代理](/docs/en/sub-agents#let-subagents-spawn-their-own-subagents)。

  早期版本使用不同的默认值：

  * **v2.1.172 至 v2.1.216**：子代理默认可以嵌套，最多五层，且该限制无法更改。
  * **v2.1.217 至 v2.1.218**：该限制默认为一，因此子代理无法生成自己的子代理，除非你提高该限制；{/* min-version: 2.1.219 */}v2.1.219 将默认值提高到三。
</Note>

### 基于文件系统的定义（替代方案）

你也可以在 `.claude/agents/` 目录中以 Markdown 文件的形式定义子代理。有关此方法的详细信息，请参阅[Claude Code 子代理文档](/docs/en/sub-agents)。以编程方式定义的代理优先于同名的基于文件系统的代理。

<Note>
  即使不定义自定义子代理，Claude 也可以生成内置的 `general-purpose` 子代理。这对于委托研究或探索任务非常有用，而无需创建专门的代理。在 `allowedTools` 中包含 `Agent`，这些调用即可自动批准，无需权限提示。
</Note>

## 子代理继承的内容

子代理的上下文窗口从头开始，不包含父对话，但也并非为空。你从父代理传递给子代理的唯一内容是 Agent 工具的提示字符串，因此请将子代理所需的任何文件路径、错误消息或决策直接包含在该提示中。

{/* min-version: 2.1.206 */}拥有 [`SendMessage`](/docs/en/tools-reference) 工具的子代理会以会话中运行的其他具名代理的列表开始，因此它知道可以向哪些名称发送消息。Claude Code 会自动将该列表添加到子代理的第一个回合中。[fork](/docs/en/sub-agents#fork-the-current-conversation) 不会获得该列表，因为它继承的是父对话。该列表需要 Claude Code v2.1.206 或更高版本。

| 子代理接收的内容                                                                                                                 | 子代理不接收的内容                                       |
| :------------------------------------------------------------------------------------------------------------------------------------ | :----------------------------------------------------------------- |
| 它自己的系统提示（`AgentDefinition.prompt`）以及 Agent 工具的提示                                                          | 父代理的对话历史或工具结果                  |
| 项目的 CLAUDE.md（通过 [`settingSources`](/docs/en/agent-sdk/claude-code-features#control-filesystem-settings-with-settingsources) 加载） | 预加载的技能内容，除非在 `AgentDefinition.skills` 中列出 |
| 工具定义（继承自父代理或 `tools` 中的子集，[针对后台运行进行了过滤](/docs/en/sub-agents#available-tools)）     | 父代理的系统提示                                         |

<Note>
  父代理将子代理的最终消息作为 Agent 工具结果接收，但可能会在自己的响应中对其进行总结。要在面向用户的响应中逐字保留子代理的输出，请在提示或传递给主 `query()` 调用的 `systemPrompt` 选项中包含相应的指令。

  {/* min-version: 2.1.210 */}在 v2.1.210 及更高版本中，Claude Code 会在父代理读取最终消息之前[扫描该消息中具有指令形态的模式](/docs/en/sub-agents#subagent-output-scanning)。该扫描以不同方式处理三种模式：

  * **控制标签模仿**：Claude Code 会就地中和仅由框架发出的标签，例如 `<system-reminder>` 块。它在开始尖括号后插入一个反斜杠，不删除任何内容。
  * **权限配置提及**：Claude Code 会按原样保留对权限配置的引用，例如 `.claude/settings.json`、`bypassPermissions` 或 `--dangerously-skip-permissions`。
  * **回合标记**：以 `Human:` 或 `Assistant:` 开头的行会在冒号前加上反斜杠，这样消息就无法模仿对话回合的边界。

  对于控制标签或权限配置匹配，Claude Code 会在前面添加一行 `[harness: ...]` 标记行，指明匹配到的模式；回合标记匹配则不会添加该标记行。这些就是扫描所做的唯一修改：它绝不会删除或改写子代理的文本。
</Note>

{/* min-version: 2.1.199 */}导致子代理提前终止的 API 错误（例如速率限制）永远不会作为其结果返回。如果速率限制、过载或服务器错误中断了已经产生文本输出的前台子代理，Agent 工具会返回该部分输出，并附注子代理未完成。{/* min-version: 2.1.200 */}未产生任何输出的子代理，或唯一输出是工具调用而没有文本的子代理，会以一条错误消息失败，`Agent terminated early due to an API error`，后跟错误详情。有关前台和后台行为，请参阅 [子代理中的 API 错误](/docs/en/sub-agents#api-errors-in-subagents)。

此部分输出处理需要 Claude Code v2.1.199 或更高版本。在 v2.1.199 中，速率限制、过载或服务器错误会使仅含工具调用的形态留下一个仅包含中断附注的空部分结果。

## 调用子代理

### 自动调用

Claude 会根据任务和每个子代理的 `description` 自动决定何时调用子代理。例如，如果你定义了一个描述为“查询调优的性能优化专家”的 `performance-optimizer` 子代理，当你的提示提到优化查询时，Claude 就会调用它。

编写清晰、具体的描述，以便 Claude 将任务匹配到正确的子代理。

### 显式调用

要保证 Claude 使用特定的子代理，请在提示中按名称提及它：

```text theme={null}
"Use the code-reviewer agent to check the authentication module"
```

这会绕过自动匹配，直接调用指定的子代理。

### 动态代理配置

你可以根据运行时条件动态创建代理定义。此示例创建一个具有不同严格级别的安全审查器，并为严格审查使用更强大的模型。

<CodeGroup>
  ```python Python theme={null}
  import asyncio
  from claude_agent_sdk import query, ClaudeAgentOptions, AgentDefinition


  # Factory function that returns an AgentDefinition
  # This pattern lets you customize agents based on runtime conditions
  def create_security_agent(security_level: str) -> AgentDefinition:
      is_strict = security_level == "strict"
      return AgentDefinition(
          description="Security code reviewer",
          # Customize the prompt based on strictness level
          prompt=f"You are a {'strict' if is_strict else 'balanced'} security reviewer...",
          tools=["Read", "Grep", "Glob"],
          # Key insight: use a more capable model for high-stakes reviews
          model="opus" if is_strict else "sonnet",
      )


  async def main():
      # The agent is created at query time, so each request can use different settings
      async for message in query(
          prompt="Review this PR for security issues",
          options=ClaudeAgentOptions(
              allowed_tools=["Read", "Grep", "Glob", "Agent"],
              agents={
                  # Call the factory with your desired configuration
                  "security-reviewer": create_security_agent("strict")
              },
          ),
      ):
          if hasattr(message, "result"):
              print(message.result)


  asyncio.run(main())
  ```

  ```typescript TypeScript theme={null}
  import { query, type AgentDefinition } from "@anthropic-ai/claude-agent-sdk";

  // Factory function that returns an AgentDefinition
  // This pattern lets you customize agents based on runtime conditions
  function createSecurityAgent(securityLevel: "basic" | "strict"): AgentDefinition {
    const isStrict = securityLevel === "strict";
    return {
      description: "Security code reviewer",
      // Customize the prompt based on strictness level
      prompt: `You are a ${isStrict ? "strict" : "balanced"} security reviewer...`,
      tools: ["Read", "Grep", "Glob"],
      // Key insight: use a more capable model for high-stakes reviews
      model: isStrict ? "opus" : "sonnet"
    };
  }

  // The agent is created at query time, so each request can use different settings
  for await (const message of query({
    prompt: "Review this PR for security issues",
    options: {
      allowedTools: ["Read", "Grep", "Glob", "Agent"],
      agents: {
        // Call the factory with your desired configuration
        "security-reviewer": createSecurityAgent("strict")
      }
    }
  })) {
    if ("result" in message) console.log(message.result);
  }
  ```
</CodeGroup>

## 检测子代理调用

Claude 通过 Agent 工具调用子代理。要检测子代理何时被调用，请检查 `tool_use` 块中 `name` 是否为 `"Agent"`。来自子代理上下文内部的消息包含 `parent_tool_use_id` 字段。

<Note>
  该工具名称在 Claude Code v2.1.63 中从 `"Task"` 更名为 `"Agent"`。当前的 SDK 版本在 `tool_use` 块中发出 `"Agent"`，但在 `system:init` 工具列表和 `result.permission_denials[].tool_name` 中仍使用 `"Task"`。在 `block.name` 中同时检查这两个值可确保跨 SDK 版本的兼容性。
</Note>

消息结构在不同 SDK 之间有所不同。在 Python 中，你通过 `message.content` 直接访问内容块。在 TypeScript 中，`SDKAssistantMessage` 包装了 Claude API 消息，因此你通过 `message.message.content` 访问内容。

此示例遍历流式消息，记录子代理何时被调用以及后续消息何时源自该子代理的执行上下文。

<CodeGroup>
  ```python Python theme={null}
  import asyncio
  from claude_agent_sdk import query, ClaudeAgentOptions, AgentDefinition, ToolUseBlock


  async def main():
      async for message in query(
          prompt="Use the code-reviewer agent to review this codebase",
          options=ClaudeAgentOptions(
              allowed_tools=["Read", "Glob", "Grep", "Agent"],
              agents={
                  "code-reviewer": AgentDefinition(
                      description="Expert code reviewer.",
                      prompt="Analyze code quality and suggest improvements.",
                      tools=["Read", "Glob", "Grep"],
                  )
              },
          ),
      ):
          # Check for subagent invocation. Match both names: older SDK
          # versions emitted "Task", current versions emit "Agent".
          if hasattr(message, "content") and message.content:
              for block in message.content:
                  if isinstance(block, ToolUseBlock) and block.name in (
                      "Task",
                      "Agent",
                  ):
                      print(f"Subagent invoked: {block.input.get('subagent_type')}")

          # Check if this message is from within a subagent's context
          if hasattr(message, "parent_tool_use_id") and message.parent_tool_use_id:
              print("  (running inside subagent)")

          if hasattr(message, "result"):
              print(message.result)


  asyncio.run(main())
  ```

  ```typescript TypeScript theme={null}
  import { query } from "@anthropic-ai/claude-agent-sdk";

  for await (const message of query({
    prompt: "Use the code-reviewer agent to review this codebase",
    options: {
      allowedTools: ["Read", "Glob", "Grep", "Agent"],
      agents: {
        "code-reviewer": {
          description: "Expert code reviewer.",
          prompt: "Analyze code quality and suggest improvements.",
          tools: ["Read", "Glob", "Grep"]
        }
      }
    }
  })) {
    const msg = message as any;

    // Check for subagent invocation. Match both names: older SDK versions
    // emitted "Task", current versions emit "Agent".
    for (const block of msg.message?.content ?? []) {
      if (block.type === "tool_use" && (block.name === "Task" || block.name === "Agent")) {
        console.log(`Subagent invoked: ${block.input.subagent_type}`);
      }
    }

    // Check if this message is from within a subagent's context
    if (msg.parent_tool_use_id) {
      console.log("  (running inside subagent)");
    }

    if ("result" in message) {
      console.log(message.result);
    }
  }
  ```
</CodeGroup>

## 恢复子代理

你可以恢复一个子代理，让它从上次中断的地方继续，而不是重新开始。已恢复的子代理会保留其完整对话历史，包括所有先前的工具调用、结果和推理。

当子代理完成时，Agent 工具结果会包含一个含有 `agentId: <id>` 的文本块。内置的 [`Explore` 和 `Plan` 代理](/docs/en/sub-agents#built-in-subagents) 是一次性的，不会返回 `agentId`，因此在需要恢复时，请使用自定义代理或 `general-purpose`。要以编程方式恢复子代理：

1. **捕获会话 ID**：在第一次查询期间从消息中提取 `session_id`
2. **提取代理 ID**：从 Agent 工具结果文本中解析 `agentId`
3. **恢复会话**：在第二次查询的选项中传递 `resume: sessionId`，并在提示中包含代理 ID

<Note>
  你必须恢复同一个会话才能访问子代理的记录。默认情况下，每次 `query()` 调用都会启动一个新会话，因此请传递 `resume: sessionId` 以在同一会话中继续。

  使用自定义代理时，请在两次查询的 `agents` 参数中传递相同的代理定义。
</Note>

下面的示例定义了一个自定义 `endpoint-finder` 代理。第一次查询运行它，并从 Agent 工具结果中捕获会话 ID 和代理 ID，然后第二次查询恢复会话，提出一个需要第一次分析上下文的后续问题。

<CodeGroup>
  ```python Python theme={null}
  import asyncio
  import re
  from claude_agent_sdk import query, ClaudeAgentOptions, AgentDefinition, ToolResultBlock

  AGENTS = {
      "endpoint-finder": AgentDefinition(
          description="Locates and catalogs API endpoints in a codebase.",
          prompt="You find and document API endpoints. Report each endpoint's path, method, and handler.",
          tools=["Read", "Grep", "Glob"],
      )
  }


  def extract_agent_id(block: ToolResultBlock) -> str | None:
      """Extract agentId from an Agent tool result's text content."""
      parts = block.content if isinstance(block.content, list) else [{"text": block.content}]
      for part in parts:
          if match := re.search(r"agentId:\s*([\w-]+)", part.get("text") or ""):
              return match.group(1)
      return None


  async def main():
      agent_id = None
      session_id = None

      # First invocation - run the endpoint-finder subagent
      try:
          async for message in query(
              prompt="Use the endpoint-finder agent to find all API endpoints in this codebase",
              options=ClaudeAgentOptions(allowed_tools=["Read", "Grep", "Glob", "Agent"], agents=AGENTS),
          ):
              # Capture session_id from ResultMessage (needed to resume this session)
              if hasattr(message, "session_id"):
                  session_id = message.session_id
              # Search tool results for the agentId trailer
              for block in getattr(message, "content", None) or []:
                  if isinstance(block, ToolResultBlock):
                      agent_id = extract_agent_id(block) or agent_id
              # Print the final result
              if hasattr(message, "result"):
                  print(message.result)
      except Exception as error:
          # A single-shot query() raises after yielding an error result,
          # so session_id and agent_id have already been captured by the loop above.
          print(f"Session ended with an error: {error}")

      # Second invocation - resume and ask follow-up
      if agent_id and session_id:
          async for message in query(
              prompt=f"Resume agent {agent_id} and list the top 3 most complex endpoints",
              options=ClaudeAgentOptions(
                  allowed_tools=["Read", "Grep", "Glob", "Agent"], agents=AGENTS, resume=session_id
              ),
          ):
              if hasattr(message, "result"):
                  print(message.result)
      else:
          print("No agentId found in the first query, so there is no subagent to resume.")


  asyncio.run(main())
  ```

  ```typescript TypeScript theme={null}
  import { query, type SDKMessage } from "@anthropic-ai/claude-agent-sdk";

  const agents = {
    "endpoint-finder": {
      description: "Locates and catalogs API endpoints in a codebase.",
      prompt: "You find and document API endpoints. Report each endpoint's path, method, and handler.",
      tools: ["Read", "Grep", "Glob"]
    }
  };

  // Stringify content to search for agentId without traversing nested block types
  function extractAgentId(message: SDKMessage): string | undefined {
    if (message.type !== "assistant" && message.type !== "user") return undefined;
    const content = JSON.stringify(message.message.content);
    const match = content.match(/agentId:\s*([\w-]+)/);
    return match?.[1];
  }

  let agentId: string | undefined;
  let sessionId: string | undefined;

  // First invocation - run the endpoint-finder subagent
  try {
    for await (const message of query({
      prompt: "Use the endpoint-finder agent to find all API endpoints in this codebase",
      options: { allowedTools: ["Read", "Grep", "Glob", "Agent"], agents }
    })) {
      // Capture session_id from ResultMessage (needed to resume this session)
      if ("session_id" in message) sessionId = message.session_id;
      // Search message content for the agentId (appears in Agent tool results)
      const extractedId = extractAgentId(message);
      if (extractedId) agentId = extractedId;
      // Print the final result
      if ("result" in message) console.log(message.result);
    }
  } catch (error) {
    // A single-shot query() throws after yielding an error result,
    // so sessionId and agentId have already been captured by the loop above.
    console.error(`Session ended with an error: ${error}`);
  }

  // Second invocation - resume and ask follow-up
  if (agentId && sessionId) {
    for await (const message of query({
      prompt: `Resume agent ${agentId} and list the top 3 most complex endpoints`,
      options: { allowedTools: ["Read", "Grep", "Glob", "Agent"], agents, resume: sessionId }
    })) {
      if ("result" in message) console.log(message.result);
    }
  } else {
    console.log("No agentId found in the first query, so there is no subagent to resume.");
  }
  ```
</CodeGroup>

子代理的转录记录独立于主对话持久保存：

* **主对话压缩**：当主对话被压缩时，子代理的转录记录不受影响。它们存储在单独的文件中。
* **会话持久性**：子代理的转录记录在其会话内持久保存。你可以通过恢复同一会话，在重启 Claude Code 之后恢复某个子代理。
* **自动清理**：转录记录会根据 `cleanupPeriodDays` 设置进行清理，该设置默认为 30 天。

## 工具限制

使用 `tools` 字段来限制子代理可以执行的操作：

* **省略 `tools`**：子代理将获得子代理可用的所有[工具](/docs/en/sub-agents#available-tools)
* **列出工具**：子代理仅获得这些工具。例如，一个绝不应编辑文件的代码审查器会获得 `["Read", "Grep", "Glob"]`

你遗漏的工具根本不会出现在子代理的会话中：Claude 在没有它的情况下工作，不会出现权限提示或错误。

此示例创建一个只读分析代理，它可以检查代码，但不能修改文件或运行命令。

<CodeGroup>
  ```python Python theme={null}
  import asyncio
  from claude_agent_sdk import query, ClaudeAgentOptions, AgentDefinition


  async def main():
      async for message in query(
          prompt="Analyze the architecture of this codebase",
          options=ClaudeAgentOptions(
              allowed_tools=["Read", "Grep", "Glob", "Agent"],
              agents={
                  "code-analyzer": AgentDefinition(
                      description="Static code analysis and architecture review",
                      prompt="""You are a code architecture analyst. Analyze code structure,
  identify patterns, and suggest improvements without making changes.""",
                      # Read-only tools: no Edit, Write, or Bash access
                      tools=["Read", "Grep", "Glob"],
                  )
              },
          ),
      ):
          if hasattr(message, "result"):
              print(message.result)


  asyncio.run(main())
  ```

  ```typescript TypeScript theme={null}
  import { query } from "@anthropic-ai/claude-agent-sdk";

  for await (const message of query({
    prompt: "Analyze the architecture of this codebase",
    options: {
      allowedTools: ["Read", "Grep", "Glob", "Agent"],
      agents: {
        "code-analyzer": {
          description: "Static code analysis and architecture review",
          prompt: `You are a code architecture analyst. Analyze code structure,
  identify patterns, and suggest improvements without making changes.`,
          // Read-only tools: no Edit, Write, or Bash access
          tools: ["Read", "Grep", "Glob"]
        }
      }
    }
  })) {
    if ("result" in message) console.log(message.result);
  }
  ```
</CodeGroup>

### 常见工具组合

| 用例           | 工具                                   | 描述                                                        |
| :----------------- | :-------------------------------------- | :----------------------------------------------------------------- |
| 只读分析 | `Read`、`Grep`、`Glob`                  | 可以检查代码，但不能修改或执行                         |
| 测试执行     | `Bash`、`Read`、`Grep`                  | 可以运行命令并分析输出                                |
| 代码修改  | `Read`、`Edit`、`Write`、`Grep`、`Glob` | 完整的读/写访问权限，但不能执行命令                   |
| 完全访问        | 所有工具                               | 继承子代理可用的工具（省略 `tools` 字段） |

## 通过动态工作流进行扩展

子代理适用于每轮少量的委派任务。对于需要协调数十到数百个代理的运行，请使用 `Workflow` 工具，它将编排移入运行时脚本中，由运行时在对话上下文之外执行。请参阅[动态工作流](/docs/en/workflows)，了解工作流与逐轮子代理委派有何不同。

`Workflow` 工具在 TypeScript Agent SDK v0.3.149 及更高版本中可用。在 `allowedTools` 中包含 `Workflow` 可自动批准工作流运行。工具输入和输出模式列在 [TypeScript 参考](/docs/en/agent-sdk/typescript#workflow) 中。

## 故障排除

### Claude 未委派给子代理

如果 Claude 直接完成任务而不是委派给你的子代理：

* **检查 Agent 调用是否已获批准**：在 `allowedTools` 中包含 `Agent` 以自动批准子代理调用。如果没有它，Agent 调用会落到你的 `canUseTool` 回调，或者在 `dontAsk` 模式下被拒绝
* **使用明确的提示**：在提示中按名称提及子代理，例如“使用 code-reviewer 代理来……”
* **编写清晰的描述**：准确说明何时使用该子代理，以便 Claude 能适当地匹配任务

### 基于文件系统的代理未加载

Claude Code 会监视 `~/.claude/agents/` 和 `.claude/agents/`，并在几秒内拾取新的或编辑过的代理文件，无需重启。如果某个定义始终不出现，请排查以下原因：

* **新的 `agents` 目录**：监视器仅覆盖会话启动时已存在的目录，因此新目录中的第一个文件需要重启会话。这是最常见的原因。
* **无效的 frontmatter 或重复的 `name`**：检查文件的 YAML，以及是否已有代理使用了该 `name`。
* **`--disable-slash-commands`**：使用此标志启动的会话不会监视这些目录，加载新文件始终需要重启。
* **同名的程序化代理**：传递给 `query()` 的 `agents` 会覆盖同名的文件系统代理。

有关文件格式，请参阅[如何编写子代理文件](/docs/en/sub-agents#write-subagent-files)。

### Windows 上的长提示失败

在 Windows 上，提示非常长的子代理可能因命令行长度限制 8191 个字符而失败。请保持提示简洁，或对复杂指令使用基于文件系统的代理。

## 相关文档

* [Claude Code 子代理](/docs/en/sub-agents)：全面的子代理文档，包括基于文件系统的定义
* [动态工作流](/docs/en/workflows)：从脚本编排多个子代理，处理单个对话无法完成的大型任务
* [SDK 概述](/docs/en/agent-sdk/overview)：Claude Agent SDK 入门

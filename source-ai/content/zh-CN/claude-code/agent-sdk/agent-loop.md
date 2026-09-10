---
title: 代理循环的工作原理
source_id: claude-code/agent-sdk/agent-loop
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/agent-sdk/agent-loop
owner: Anthropic
content_sha256: 716cd8c2c01a9bb32e4b697f722028f3a3f13ec10b970ebdf78f1eb75adfca60
translation_of: claude-code/agent-sdk/agent-loop
translation_model: k3
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/agent-sdk/agent-loop)

Content owner: Anthropic

> ## 文档索引
> 在以下地址获取完整的文档索引：https://code.claude.com/docs/llms.txt
> 在进一步探索之前，使用此文件发现所有可用页面。

# 代理循环的工作原理

> 了解为你的 SDK 代理提供支持的消息生命周期、工具执行、上下文窗口和架构。

Agent SDK 让你能够将 Claude Code 的自主代理循环嵌入到你自己的应用程序中。该 SDK 是一个独立软件包，可让你以编程方式控制工具、权限、成本上限和输出。使用它无需安装 Claude Code CLI。

当您启动一个代理时，SDK 会运行 [驱动 Claude Code 的相同执行循环](/docs/en/how-claude-code-works#the-agentic-loop)：Claude 评估您的提示，调用工具来执行操作， 接收结果，并重复这一过程直到任务完成。本页将解释该循环内部发生了什么，以便你高效地构建、调试和优化你的智能体。

## 循环一览

每个代理会话都遵循相同的循环:

<img src="https://mintcdn.com/claude-code/ikqp3_70mqIahteV/images/agent-loop-diagram.svg?fit=max&auto=format&n=ikqp3_70mqIahteV&q=85&s=1c6e8f28d80dba14a7287419656f1237" alt="代理循环示意图:你的提示进入代理循环,Claude 在其中进行评估,要么请求工具调用(其结果反馈回下一轮评估),要么返回最终答案" width="720" height="212" data-path="images/agent-loop-diagram.svg" />

1. **接收提示。** Claude 接收你的提示,以及系统提示、工具定义和对话历史。SDK 产生一个 [`SystemMessage`](#message-types)，其子类型为 `"init"`，其中包含会话元数据。
2. **评估并响应。** Claude 评估当前状态并决定如何进行。它可以用文本响应、请求一个或多个工具调用,或两者兼有。SDK 产生一个 [`AssistantMessage`](#message-types),其中包含文本和任何工具调用请求。
3. **执行工具。** SDK 运行每个被请求的工具并收集结果。每组工具结果都会反馈给 Claude 以进行下一步决策。你可以使用 [hooks](/docs/en/agent-sdk/hooks) 在工具调用运行之前拦截、修改或阻止它们。
4. **重复。** 第 2 步和第 3 步作为一个循环重复进行。每个完整的循环是一个回合。Claude 持续调用工具并处理结果,直到产生一个没有工具调用的响应。
5. **返回结果。** SDK 产出一个最终的 [`AssistantMessage`](#message-types)，其中包含文本响应（无工具调用），随后是一个 [`ResultMessage`](#message-types)，包含最终文本、token 用量、成本和会话 ID。

一个简单的问题（"这里有哪些文件？"）可能只需要一两次调用 `Glob` 并返回结果的回合。一个复杂任务（"重构 auth 模块并更新测试"）可以在多个回合中链式调用数十次工具，读取文件、编辑代码并运行测试，Claude 会根据每个结果调整其方法。

## 回合与消息

一个回合是循环内的一次往返：Claude 生成包含工具调用的输出，SDK 执行这些工具，结果自动反馈给 Claude。这一过程不会把控制权交还给您的代码。回合持续进行，直到 Claude 生成不含工具调用的输出，此时循环结束并交付最终结果。

设想一个完整会话可能是什么样子，假设提示词为"修复 auth.ts 中失败的测试"。

首先，SDK 将您的提示词发送给 Claude，并产生一个包含会话元数据的 [`SystemMessage`](#message-types)。然后循环开始：

1. **第 1 回合：** Claude 调用 `Bash` 来运行 `npm test`。SDK 产生一个包含该工具调用的 [`AssistantMessage`](#message-types)，执行该命令，然后产生一个包含输出（三个失败）的 [`UserMessage`](#message-types)。
2. **第 2 回合：** Claude 对 `auth.ts` 和 `auth.test.ts` 调用 `Read`。SDK 返回文件内容并产生一个 `AssistantMessage`。
3. **第 3 回合：** Claude 调用 `Edit` 来修复 `auth.ts`，然后调用 `Bash` 重新运行 `npm test`。三个测试全部通过。SDK 产生一个 `AssistantMessage`。
4. **最后一个回合：** Claude 生成不含工具调用的纯文本响应："已修复认证 bug，三个测试现在全部通过。" SDK 产生一个包含此文本的最终 `AssistantMessage`，然后产生一个包含相同文本以及成本和用量信息的 [`ResultMessage`](#message-types)。

这就是四个回合：三个包含工具调用，一个最终的纯文本响应。

您可以使用 `max_turns` / `maxTurns` 来限制循环，它只计算使用工具的回合。例如，在上面的循环中，`max_turns=2` 会在编辑步骤之前停止循环。您还可以使用 `max_budget_usd` / `maxBudgetUsd` 基于支出阈值来限制回合数。

如果不设限制，循环会一直运行到 Claude 自行完成为止，这对于范围明确的任务来说没问题，但对于开放式提示词（"改进这个代码库"）可能会运行很久。为生产环境的智能体设置预算是不错的默认做法。有关选项参考，请参阅下文的 [轮次与预算](#turns-and-budget)。

## 消息类型

随着循环运行，SDK 会产生一个消息流。每条消息都带有一个类型，告诉你它来自循环的哪个阶段。五种核心类型是：

* **`SystemMessage`：** 会话生命周期事件。`subtype` 字段用于区分它们：

  * `"init"`：本次运行的会话元数据。当 `SessionStart` 或 `Setup` 钩子在会话启动期间运行时，其 [钩子生命周期消息](/docs/en/agent-sdk/typescript#sdkhookstartedmessage) 会在 `init` 消息之前到达
  * `"compact_boundary"`：在 [压缩](#automatic-compaction) 之后触发
  * `"informational"`：来自循环的纯文本状态横幅
  * `"worker_shutting_down"`：循环将在当前回合之后结束，因为宿主正在退出或远程控制已断开连接

  在 TypeScript 中，除 `"init"` 之外的每个子类型都是 [`SDKMessage` 联合类型](/docs/en/agent-sdk/typescript#sdkmessage) 中自己的类型，而不是 `SDKSystemMessage` 的子类型。
* **`AssistantMessage`：** 在每次 Claude 响应（包括最终的纯文本响应）之后发出。包含该回合的文本内容块和工具调用块。
* **`UserMessage`：** 在每次工具执行之后发出，携带发送回 Claude 的工具结果内容。对于你在循环中推送的任何用户输入也会发出。
* **`StreamEvent`：** 仅在启用部分消息时发出。包含原始 API 流式事件（文本增量、工具输入块）。参见 [流式响应](/docs/en/agent-sdk/streaming-output)。
* **`ResultMessage`：** 标记智能体循环的结束。包含最终文本结果、token 用量、费用和会话 ID。检查 `subtype` 字段以确定任务是成功还是达到了限制。少量尾随系统事件（例如 `prompt_suggestion`）可能在它之后到达，因此请迭代流直至完成，而不是在结果处中断。参见 [处理结果](#handle-the-result)。

这五种类型覆盖了完整的智能体循环生命周期。两个 SDK 还会产生可观测性事件，例如速率限制状态和任务通知，这些事件不是驱动循环所必需的。完整列表请参见 [Python 消息类型参考](/docs/en/agent-sdk/python#message-types) 和 [TypeScript 消息类型参考](/docs/en/agent-sdk/typescript#message-types)。

### 处理消息

你处理哪些消息取决于你要构建的内容：

* **仅最终结果：** 处理 `ResultMessage` 以获取输出、成本以及任务是成功还是达到了限制。
* **进度更新：** 处理 `AssistantMessage` 以查看 Claude 每轮正在做什么，包括它调用了哪些工具。
* **实时流式传输：** 启用部分消息（Python 中为 `include_partial_messages`，TypeScript 中为 `includePartialMessages`）以实时获取 `StreamEvent` 消息。请参阅 [实时流式传输响应](/docs/en/agent-sdk/streaming-output)。

如何检查消息类型取决于 SDK：

* **Python：** 使用 `isinstance()` 对照从 `claude_agent_sdk` 导入的类来检查消息类型（例如，`isinstance(message, ResultMessage)`）。
* **TypeScript：** 检查 `type` 字符串字段（例如，`message.type === "result"`）。`AssistantMessage` 和 `UserMessage` 将原始 API 消息包装在 `.message` 字段中，因此内容块位于 `message.message.content`，而不是 `message.content`。

<Accordion title="Example: Check message types and handle results">
  <CodeGroup>
    ```python Python theme={null}
    import asyncio
    from claude_agent_sdk import query, AssistantMessage, ResultMessage


    async def main():
        try:
            async for message in query(prompt="Summarize this project"):
                if isinstance(message, AssistantMessage):
                    print(f"Turn completed: {len(message.content)} content blocks")
                if isinstance(message, ResultMessage):
                    if message.subtype == "success":
                        print(message.result)
                    else:
                        print(f"Stopped: {message.subtype}")
        except Exception as error:
            # A single-shot query() raises after yielding an error result. If the
            # failure was an error result, the error subtype branches above have
            # already run; connection or process failures yield no result message.
            print(f"Session ended with an error: {error}")


    asyncio.run(main())
    ```

    ```typescript TypeScript theme={null}
    import { query } from "@anthropic-ai/claude-agent-sdk";

    try {
      for await (const message of query({ prompt: "Summarize this project" })) {
        if (message.type === "assistant") {
          console.log(`Turn completed: ${message.message.content.length} content blocks`);
        }
        if (message.type === "result") {
          if (message.subtype === "success") {
            console.log(message.result);
          } else {
            console.log(`Stopped: ${message.subtype}`);
          }
        }
      }
    } catch (error) {
      // A single-shot query() throws after yielding an error result. If the
      // failure was an error result, the error subtype branches above have
      // already run; connection or process failures yield no result message.
      console.log(`Session ended with an error: ${error}`);
    }
    ```
  </CodeGroup>
</Accordion>

## 工具执行

工具使你的智能体能够采取行动。没有工具，Claude 只能用文本回复。有了工具，Claude 可以读取文件、运行命令、搜索代码以及与外部服务交互。

### 内置工具

SDK 包含了与 Claude Code 相同的工具：

| 类别            | 工具                                                           | 作用                                                                |
| :------------------ | :-------------------------------------------------------------- | :-------------------------------------------------------------------------- |
| **文件操作** | `Read`, `Edit`, `Write`                                         | 读取、修改和创建文件                                              |
| **搜索**          | `Glob`, `Grep`                                                  | 按模式查找文件，使用正则表达式搜索内容                            |
| **执行**       | `Bash`                                                          | 运行 shell 命令、脚本和 git 操作                                 |
| **网络**             | `WebSearch`, `WebFetch`                                         | 搜索网页、抓取并解析页面                                       |
| **发现**       | `ToolSearch`                                                    | 按需动态查找和加载工具，而不是预加载所有工具 |
| **编排**   | `Agent`, `Skill`, `AskUserQuestion`, `TaskCreate`, `TaskUpdate` | 生成子代理、调用技能、询问用户、跟踪任务                   |

除了内置工具之外，你还可以：

* **连接外部服务**，通过 [MCP 服务器](/docs/en/agent-sdk/mcp)（数据库、浏览器、API）
* **定义自定义工具**，通过 [自定义工具处理器](/docs/en/agent-sdk/custom-tools)
* **加载项目技能**，通过 [设置来源](/docs/en/agent-sdk/claude-code-features)，实现可复用的工作流

### 工具权限

Claude 根据任务决定调用哪些工具，但由你控制这些调用是否允许执行。你可以自动批准特定工具、完全阻止其他工具，或者要求对所有工具进行审批。以下三个选项共同决定哪些工具可以运行：

* **`allowed_tools` / `allowedTools`** 自动批准列出的工具。一个只读代理，如果其允许工具列表中包含 `["Read", "Glob", "Grep"]`，则无需提示即可运行这些工具。未列出的工具仍然可用，但需要权限。
* **`disallowed_tools` / `disallowedTools`** 阻止列出的工具，无论其他设置如何。有关工具运行前规则检查的顺序，请参阅 [权限](/docs/en/agent-sdk/permissions)。
* **`permission_mode` / `permissionMode`** 控制未被允许或拒绝规则覆盖的工具的行为。有关可用模式，请参阅 [权限模式](#permission-mode)。

你还可以使用类似 `"Bash(npm *)"` 的规则来限定单个工具，以仅允许特定命令。有关完整的规则语法，请参阅 [权限](/docs/en/agent-sdk/permissions)。

当工具被拒绝时，Claude 会收到一条拒绝消息作为工具结果，并通常会尝试其他方法或报告无法继续。

### 并行工具执行

当 Claude 在单个回合中请求多个工具调用时，两个 SDK 都可以根据工具的类型并发或顺序运行它们。只读工具（如 `Read`、`Glob`、`Grep` 以及标记为只读的 MCP 工具）可以并发运行。会修改状态的工具（如 `Edit`、`Write` 和 `Bash`）则顺序运行以避免冲突。

自定义工具默认为顺序执行。要为自定义工具启用并行执行，请在其注解中设置 `readOnlyHint`。[TypeScript](/docs/en/agent-sdk/typescript#tool) 和 [Python](/docs/en/agent-sdk/python#tool) 两个 SDK 都使用来自 MCP SDK 的这个字段名。

## 控制循环的运行方式

你可以限制循环的轮次数量、花费上限、Claude 推理的深度，以及工具在运行前是否需要批准。所有这些都是 [`ClaudeAgentOptions`](/docs/en/agent-sdk/python#claudeagentoptions)（Python）/ [`Options`](/docs/en/agent-sdk/typescript#options)（TypeScript）上的字段。

### 轮次与预算

| 选项                                         | 控制内容             | 默认值  |
| :--------------------------------------------- | :--------------------------- | :------- |
| 最大轮次（`max_turns` / `maxTurns`）           | 工具调用的最大往返次数 | 无限制 |
| 最大预算（`max_budget_usd` / `maxBudgetUsd`） | 停止前的最大花费 | 无限制 |

当达到任一限制时，SDK 会返回一个 `ResultMessage`，带有相应的错误子类型（`error_max_turns` 或 `error_max_budget_usd`）。有关如何检查这些子类型，请参阅 [处理结果](#handle-the-result)；有关语法，请参阅 [`ClaudeAgentOptions`](/docs/en/agent-sdk/python#claudeagentoptions) / [`Options`](/docs/en/agent-sdk/typescript#options)。

预算上限涵盖 [子代理](/docs/en/agent-sdk/subagents)：它们的花费计入总额。{/* min-version: 2.1.217 */}一旦花费达到上限，再生成新的子代理将失败并报 `Budget limit reached`，同时 Claude Code 会停止所有仍在后台运行的子代理。这些上限强制执行行为需要 Claude Code v2.1.217 或更高版本。

使用 [流式输入](/docs/en/agent-sdk/streaming-vs-single-mode) 时，如果你在某一轮仍在运行时发送消息，而该轮在达到最大轮次限制时结束，该消息会保持排队状态，并以自己的最大轮次限制开始自己的新一轮。在 v2.1.205 之前，在一轮的最后一次迭代到达的消息可能会被并入正在结束的那一轮并丢失，永远无法到达模型。

### 投入程度

`effort` 选项控制 Claude 应用的推理量。较低的投入程度每轮使用更少的 token，并降低成本。并非所有模型都支持 effort 参数。请参阅 [投入程度](https://platform.claude.com/docs/en/build-with-claude/effort) 了解哪些模型支持该参数。

| 级别      | 行为                          | 适用场景                                                                  |
| :--------- | :-------------------------------- | :------------------------------------------------------------------------ |
| `"low"`    | 最少推理，快速响应 | 文件查找、列出目录                                         |
| `"medium"` | 均衡推理                | 常规编辑、标准任务                                             |
| `"high"`   | 深入分析                 | 重构、调试                                                      |
| `"xhigh"`  | 扩展推理深度          | 编程和智能体任务；推荐用于 Fable 5、Opus 4.7+ 和 Sonnet 5 |
| `"max"`    | 最大推理深度           | 需要深度分析的多步骤问题                               |

如果不设置 `effort`，两个 SDK 都会将该参数留为未设置，并遵从模型的默认行为。

<Note>
  `effort` 是在每次响应中以延迟和 token 成本换取推理深度。[扩展思考](https://platform.claude.com/docs/en/build-with-claude/extended-thinking) 是一项独立的功能，会在输出中生成可见的思维链块。二者相互独立：你可以在启用扩展思考的情况下设置 `effort: "low"`，也可以在不启用扩展思考的情况下设置 `effort: "max"`。
</Note>

对于执行简单、范围明确任务（如列出文件或运行单个 grep）的代理，使用较低强度，以降低成本和延迟。在顶层 `query()` 选项中设置 `effort` 可用于整个会话，也可以针对每个子代理，使用 [`AgentDefinition`](/docs/en/agent-sdk/subagents#agentdefinition-configuration) 上的 `effort` 字段来覆盖会话级别。

### 权限模式

权限模式选项（Python 中为 `permission_mode`，TypeScript 中为 `permissionMode`）控制代理在使用工具前是否请求批准：

| 模式                  | 行为                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| :-------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `"default"`           | 未被允许规则覆盖的工具会触发你的批准回调；没有回调则意味着拒绝                                                                                                                                                                                                         |
| `"acceptEdits"`       | 自动批准文件编辑和常见的文件系统命令（`mkdir`、`touch`、`mv`、`cp` 等）；其他 Bash 命令遵循默认规则                                                                                                                                                                                                         |
| `"plan"`              | Claude 在不编辑源文件的情况下进行探索和规划；文件编辑永远不会被自动批准，而是通过你的 `canUseTool` 回调进行提示                                                                                                                                                                                                         |
| `"dontAsk"`           | 从不提示。由 [permission rules](/docs/en/settings#permission-settings) 预先批准的工具会运行；其他一切均被拒绝。`AskUserQuestion`、[您的组织设置为 `ask`](/docs/en/mcp#organization-controls-on-connector-tools) 的连接器工具，以及标记为 [`requiresUserInteraction`](/docs/en/mcp#require-approval-for-a-specific-tool) 的 MCP 工具，即使您已允许也会被拒绝                                                                                                                                                       |
| `"auto"`              | 使用模型分类器来批准或拒绝权限提示。有关可用性和行为，请参见 [自动模式](/docs/en/permission-modes#eliminate-prompts-with-auto-mode)                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `"bypassPermissions"` | 运行所有允许的工具而不再询问，但被显式 [`ask` 规则](/docs/en/settings#permission-settings) 匹配的工具、[您的组织设置为 `ask`](/docs/en/mcp#organization-controls-on-connector-tools) 的连接器工具，以及需要用户交互的工具除外；优先级顺序请参见 [权限如何评估](/docs/en/agent-sdk/permissions#how-permissions-are-evaluated)。在 Unix 上以 root 身份运行时无法使用。仅在代理的操作不会影响您所关心系统的隔离环境中使用 |

对于交互式应用，请使用 `"default"` 并配合工具批准回调来显示批准提示。对于开发机器上的自主代理，`"acceptEdits"` 会自动批准文件编辑和常见的文件系统命令（`mkdir`、`touch`、`mv`、`cp` 等），同时仍通过允许规则限制其他 `Bash` 命令。请将 `"bypassPermissions"` 保留用于 CI、容器或其他隔离环境。完整详情请参阅 [权限](/docs/en/agent-sdk/permissions)。

### 模型

如果未设置 `model`，SDK 将使用 Claude Code 的默认值，该默认值取决于你的身份验证方式和订阅。请显式设置它（例如 `model="claude-sonnet-5"`），以固定使用特定模型，或使用更小的模型来构建更快速、更低成本的代理。可用的 ID 请参阅 [models](https://platform.claude.com/docs/en/about-claude/models)。

## 上下文窗口

上下文窗口是在一次会话期间可供 Claude 使用的信息总量。它不会在会话内的各轮之间重置。所有内容都会累积：系统提示、工具定义、对话历史、工具输入和工具输出。跨轮保持不变的内容（系统提示、工具定义、CLAUDE.md）会自动 [prompt cached](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)，这会降低重复前缀的成本和延迟。关于自定义系统提示或 `append` 文本如何影响跨会话的缓存复用，请参阅 [修改系统提示](/docs/en/agent-sdk/modifying-system-prompts#improve-prompt-caching-across-users-and-machines)。

### 什么会消耗上下文

以下是各组件在 SDK 中对上下文的影响方式：

| 来源                     | 加载时机                                                                  | 影响                                                                                                                                                                                                                                                                                                                                                 |
| :----------------------- | :------------------------------------------------------------------------ | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **系统提示词**           | 每次请求                                                                  | 固定的少量开销，始终存在                                                                                                                                                                                                                                                                                                                             |
| **CLAUDE.md 文件**        | 会话开始时，通过 [`settingSources`](/docs/en/agent-sdk/claude-code-features) | 每次请求都包含完整内容（但经过提示缓存，因此只有第一次请求承担全部开销）                                                                                                                                                                                                                                                             |
| **工具定义**             | 每次请求；MCP 模式默认延迟加载                                            | 内置工具模式每次请求都会加载。[工具搜索](/docs/en/agent-sdk/mcp#mcp-tool-search) 默认延迟加载 MCP 工具模式，但在 Google Cloud 的 Agent Platform 或非第一方 `ANTHROPIC_BASE_URL` 上会回退为预先加载。完整对照表请参阅 [配置工具搜索](/docs/en/agent-sdk/tool-search#configure-tool-search) |
| **对话历史**             | 随轮次累积                                                                | 每轮都会增长：提示、响应、工具输入、工具输出                                                                                                                                                                                                                                                                                                         |
| **技能描述**             | 会话开始时，通过设置来源加载                                              | 简短摘要；完整内容仅在被调用时加载                                                                                                                                                                                                                                                                                                                   |

大型工具输出会消耗大量上下文。读取大文件或运行输出冗长的命令可能在单轮中消耗数千个令牌。上下文会跨轮累积，因此包含大量工具调用的长会话比短会话积累的上下文要多得多。

### 自动压缩

当上下文窗口接近其限制时，SDK 会自动压缩对话：它会总结较早的历史记录以释放空间，同时保留你最近的交流和关键决策。发生这种情况时，SDK 会在流中发出一条带有 `type: "system"` 和 `subtype: "compact_boundary"` 的消息（在 Python 中这是一个 `SystemMessage`；在 TypeScript 中它是一个单独的 `SDKCompactBoundaryMessage` 类型）。

压缩会用摘要替换较早的消息，因此对话早期的具体指令可能不会被保留。持久性规则应放在 CLAUDE.md 中（通过 [`settingSources`](/docs/en/agent-sdk/claude-code-features) 加载），而不是放在初始提示中，因为 CLAUDE.md 内容会在每次请求时重新注入。

你可以通过以下几种方式自定义压缩行为：

* **在 CLAUDE.md 中编写摘要指令：** 压缩器会像读取其他上下文一样读取你的 CLAUDE.md，因此你可以在其中加入一个部分，告诉它在摘要时保留哪些内容。该部分的标题是自由形式的（不是魔法字符串）；压缩器根据意图进行匹配。
* **`PreCompact` 钩子：** 在压缩发生之前运行自定义逻辑，例如归档完整的对话记录。该钩子接收一个 `trigger` 字段（`manual` 或 `auto`）。参见 [钩子](/docs/en/agent-sdk/hooks)。
* **手动压缩：** 将 `/compact` 作为提示字符串发送以按需触发压缩。以这种方式发送的命令是 SDK 输入，而不是仅限 CLI 的快捷方式。参见 [SDK 中的命令](/docs/en/agent-sdk/slash-commands)。

<Accordion title="示例：CLAUDE.md 中的摘要指令">
  在项目的 CLAUDE.md 中添加一节，告诉压缩器要保留哪些内容。标题名称没有特殊含义；使用任何清晰的标签即可。

  ```markdown CLAUDE.md theme={null}
  # Summary instructions

  When summarizing this conversation, always preserve:
  - The current task objective and acceptance criteria
  - File paths that have been read or modified
  - Test results and error messages
  - Decisions made and the reasoning behind them
  ```
</Accordion>

### 保持上下文高效

适用于长期运行智能体的几种策略：

* **为子任务使用子智能体。** 每个子智能体都会从全新对话开始（没有先前的消息历史，但会加载其自己的系统提示和项目级上下文，例如 CLAUDE.md）。它看不到父级的回合，并且只有其最终响应会作为工具结果返回给父级。主代理的上下文只增加该摘要，而不是完整的子任务记录。详见 [子代理继承什么](/docs/en/agent-sdk/subagents#what-subagents-inherit)。
* **谨慎选择工具。** 每个工具定义都会占用上下文空间。使用 `tools` 字段（位于 [`AgentDefinition`](/docs/en/agent-sdk/subagents#agentdefinition-configuration)）将子代理限制在它们所需的最小工具集内。
* **关注 MCP 服务器成本。** [MCP 工具搜索](/docs/en/agent-sdk/mcp#mcp-tool-search) 默认会延迟加载 MCP 工具模式定义，并按需加载它们。当工具搜索关闭、运行在 Google Cloud 的 Agent Platform 上，或位于非第一方的 `ANTHROPIC_BASE_URL` 之后时，每个 MCP 服务器都会将其所有工具模式定义添加到每个请求中，因此少数拥有大量工具的服务器可能会在代理执行任何工作之前消耗大量上下文。
* **对常规任务使用较低强度。** 对于只需要读取文件或列出目录的代理，将 [effort](#effort-level) 设置为 `"low"`。这会减少令牌用量和成本。

有关各功能上下文成本的详细明细，请参阅 [了解上下文成本](/docs/en/features-overview#understand-context-costs)。

## 会话与连续性

与 SDK 的每次交互都会创建或继续一个会话。从 `ResultMessage.session_id`（两个 SDK 中均可用）捕获会话 ID，以便稍后恢复。TypeScript SDK 还将其作为 init `SystemMessage` 上的直接字段公开；在 Python 中，它嵌套在 `SystemMessage.data` 中。

恢复时，先前轮次的完整上下文会被还原：已读取的文件、已执行的分析以及已采取的操作。你还可以分叉一个会话，在不修改原始会话的情况下分支到不同的方法。

有关恢复、继续和分叉模式的完整指南，请参阅 [会话管理](/docs/en/agent-sdk/sessions)。要跨无状态容器或无服务器主机恢复会话，请传递 [`session_store` / `sessionStore` 适配器](/docs/en/agent-sdk/session-storage)，以便转录被镜像到你自己的后端，并且任何主机都可以恢复它们。Claude Code 子进程仍会先写入本地磁盘；如果本地副本需要是临时的，请在 `options.env` 中将 `CLAUDE_CONFIG_DIR` 指向临时目录。

<Note>
  在 Python 中，`ClaudeSDKClient` 会在多次调用之间自动处理会话 ID。详情请参阅 [Python SDK 参考](/docs/en/agent-sdk/python#choosing-between-query-and-claudesdkclient)。
</Note>

## 处理结果

当循环结束时，`ResultMessage` 会告诉你发生了什么，并给出输出。`subtype` 字段（在两个 SDK 中都可用）是检查终止状态的主要方式。

| 结果子类型                        | 发生了什么                                                                                                                                                                           | `result` 字段是否可用？ |
| :------------------------------------ | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :-----------------------: |
| `success`                             | Claude 正常完成了任务                                                                                                                                                       |            是            |
| `error_max_turns`                     | 在完成前达到 `maxTurns` 限制                                                                                                                                               |             否            |
| `error_max_budget_usd`                | 在完成前达到 `maxBudgetUsd` 限制                                                                                                                                           |             否            |
| `error_during_execution`              | 错误中断了循环（例如 API 失败或请求被取消）                                                                                                        |             否            |
| `error_max_structured_output_retries` | 在配置的重试次数限制内未生成任何有效的结构化输出：每次尝试均未通过验证，或模型回退撤回了已完成的输出且没有成功的重试 |             否            |

`result` 字段(最终文本输出)仅存在于 `success` 变体上,因此在读取它之前务必检查子类型。所有结果子类型都携带 `total_cost_usd`、`usage`、`num_turns` 和 `session_id`,因此即使在出错之后,你也可以跟踪成本并恢复会话。在 Python 中,`total_cost_usd` 和 `usage` 被类型化为可选值,在某些错误路径上可能为 `None`，因此在格式化它们之前要进行防护。有关解读 `usage` 字段的详细信息，请参阅 [跟踪成本与用量](/docs/en/agent-sdk/cost-tracking)。

<Note>
  当查询以错误结果结束时：

  * 单次 `query()` 调用会生成最终结果消息，然后抛出一个包含失败文本的错误，例如 `Reached maximum number of turns`。此抛出是有意为之——如果你的代码需要在它之后继续执行，请将循环包裹在 try 块中。底层的 Claude Code 进程也会以非零退出码退出。
  * 流式输入会话会保持存活，你可以继续发送消息。
</Note>

结果还包含一个 `stop_reason` 字段（TypeScript 中为 `string | null`，Python 中为 `str | None`），用于指示模型在最后一轮停止生成的原因。常见的值有 `end_turn`（模型正常完成）、`max_tokens`（达到输出 token 上限）和 `refusal`（模型拒绝了请求）。在错误结果子类型上，`stop_reason` 携带循环结束前最后一次助手响应中的值。要检测拒绝情况，请检查 `stop_reason === "refusal"`（TypeScript）或 `stop_reason == "refusal"`（Python）。完整类型请参阅 [`SDKResultMessage`](/docs/en/agent-sdk/typescript#sdkresultmessage)（TypeScript）或 [`ResultMessage`](/docs/en/agent-sdk/python#resultmessage)（Python）。

## 钩子（Hooks）

[Hooks](/docs/en/agent-sdk/hooks) 是在循环中特定时间点触发的回调：工具运行之前、工具返回之后、代理完成时，等等。一些常用的钩子有：

| 钩子                             | 触发时机                       | 常见用途                                |
| :------------------------------- | :---------------------------------- | :----------------------------------------- |
| `PreToolUse`                     | 工具执行之前              | 校验输入、阻止危险命令  |
| `PostToolUse`                    | 工具返回之后                | 审计输出、触发副作用        |
| `UserPromptSubmit`               | 提示词发送时               | 向提示词注入额外上下文     |
| `Stop`                           | 代理完成时             | 校验结果、保存会话状态    |
| `SubagentStart` / `SubagentStop` | 子代理生成或完成时 | 跟踪并汇总并行任务结果  |
| `PreCompact`                     | 上下文压缩之前           | 在摘要前归档完整对话记录 |

钩子在你的应用程序进程中运行，而不是在代理的上下文窗口内运行，因此它们不会消耗上下文。钩子还可以使循环短路：拒绝某个工具调用的 `PreToolUse` 钩子会阻止该工具执行，而 Claude 会收到拒绝消息。

两个 SDK 都支持上述所有事件。TypeScript SDK 包含一些 Python 尚不支持的额外事件。完整的事件列表、各 SDK 的可用性以及完整的回调 API，请参阅 [使用钩子控制执行](/docs/en/agent-sdk/hooks)。

## 综合运用

本示例将本页的关键概念组合成一个修复失败测试的代理。它为代理配置了允许的工具（自动批准，使代理能够自主运行）、项目设置，以及对轮次和推理力度的安全限制。在循环运行时，它会捕获会话 ID 以便可能恢复，处理最终结果，并打印总成本。

由于单次 `query()` 调用在产生错误结果后会抛出异常，因此循环被包裹在 try 块中，以便在达到限制时脚本能够干净地退出。

<CodeGroup>
  ```python Python theme={null}
  import asyncio
  from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage


  async def run_agent():
      session_id = None

      try:
          async for message in query(
              prompt="Find and fix the bug causing test failures in the auth module",
              options=ClaudeAgentOptions(
                  allowed_tools=[
                      "Read",
                      "Edit",
                      "Bash",
                      "Glob",
                      "Grep",
                  ],  # Listing tools here auto-approves them (no prompting)
                  setting_sources=[
                      "project"
                  ],  # Load CLAUDE.md, skills, hooks from current directory
                  max_turns=30,  # Prevent runaway sessions
                  effort="high",  # Thorough reasoning for complex debugging
              ),
          ):
              # Handle the final result
              if isinstance(message, ResultMessage):
                  session_id = message.session_id  # Save for potential resumption

                  if message.subtype == "success":
                      print(f"Done: {message.result}")
                  elif message.subtype == "error_max_turns":
                      # Agent ran out of turns. Resume with a higher limit.
                      print(f"Hit turn limit. Resume session {session_id} to continue.")
                  elif message.subtype == "error_max_budget_usd":
                      print("Hit budget limit.")
                  else:
                      print(f"Stopped: {message.subtype}")
                  if message.total_cost_usd is not None:
                      print(f"Cost: ${message.total_cost_usd:.4f}")
      except Exception as error:
          # A single-shot query() raises after yielding an error result. If the
          # failure was an error result, the error subtype branches above have
          # already run; connection or process failures yield no result message.
          print(f"Session ended with an error: {error}")


  asyncio.run(run_agent())
  ```

  ```typescript TypeScript theme={null}
  import { query } from "@anthropic-ai/claude-agent-sdk";

  let sessionId: string | undefined;

  try {
    for await (const message of query({
      prompt: "Find and fix the bug causing test failures in the auth module",
      options: {
        allowedTools: ["Read", "Edit", "Bash", "Glob", "Grep"], // Listing tools here auto-approves them (no prompting)
        settingSources: ["project"], // Load CLAUDE.md, skills, hooks from current directory
        maxTurns: 30, // Prevent runaway sessions
        effort: "high" // Thorough reasoning for complex debugging
      }
    })) {
      // Save the session ID to resume later if needed
      if (message.type === "system" && message.subtype === "init") {
        sessionId = message.session_id;
      }

      // Handle the final result
      if (message.type === "result") {
        if (message.subtype === "success") {
          console.log(`Done: ${message.result}`);
        } else if (message.subtype === "error_max_turns") {
          // Agent ran out of turns. Resume with a higher limit.
          console.log(`Hit turn limit. Resume session ${sessionId} to continue.`);
        } else if (message.subtype === "error_max_budget_usd") {
          console.log("Hit budget limit.");
        } else {
          console.log(`Stopped: ${message.subtype}`);
        }
        console.log(`Cost: $${message.total_cost_usd.toFixed(4)}`);
      }
    }
  } catch (error) {
    // A single-shot query() throws after yielding an error result. If the
    // failure was an error result, the error subtype branches above have
    // already run; connection or process failures yield no result message.
    console.log(`Session ended with an error: ${error}`);
  }
  ```
</CodeGroup>

## 后续步骤

既然你已经理解了这个循环,接下来可以根据你要构建的内容选择方向:

* **还没有运行过代理?** 从 [快速入门](/docs/en/agent-sdk/quickstart) 开始,安装 SDK 并查看一个端到端运行的完整示例。
* **准备接入你的项目?** [加载 CLAUDE.md、技能和文件系统钩子](/docs/en/agent-sdk/claude-code-features),让代理自动遵循你的项目约定。
* **正在构建交互式 UI?** 启用[流式传输](/docs/en/agent-sdk/streaming-output),在循环运行时展示实时文本和工具调用。
* **需要更严格地控制代理能做什么?** 使用[权限](/docs/en/agent-sdk/permissions)锁定工具访问,并使用[钩子](/docs/en/agent-sdk/hooks)在工具调用执行前进行审计、阻止或转换。
* **运行耗时或昂贵的任务?** 将隔离的工作交给[子代理](/docs/en/agent-sdk/subagents),以保持主上下文精简。
* **部署为服务?** 查看[托管 Agent SDK](/docs/en/agent-sdk/hosting)获取容器和无服务器指南,以及[会话存储](/docs/en/agent-sdk/session-storage)将会话持久化到你自己的后端。

关于代理循环的更宏观概念(非 SDK 特定),请参阅[Claude Code 的工作原理](/docs/en/how-claude-code-works)。关于在 Claude Code 中设计循环的实用指南,从基于轮次到基于目标和主动式循环,请参阅博客上的[循环工程:循环入门](https://claude.com/blog/getting-started-with-loops)。

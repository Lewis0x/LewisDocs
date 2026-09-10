---
title: 处理批准和用户输入
source_id: claude-code/agent-sdk/user-input
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/agent-sdk/user-input
owner: Anthropic
content_sha256: 91cbe97f95e3d88100bf4f038c27926e8f917384bac46c0951b179a4abb350f5
translation_of: claude-code/agent-sdk/user-input
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/agent-sdk/user-input)

Content owner: Anthropic

> ## 文档索引
> 在此处获取完整的文档索引：https://code.claude.com/docs/llms.txt
> 在深入探索之前，使用此文件来发现所有可用页面。

# 处理批准和用户输入

> 向用户展示 Claude 的批准请求和澄清问题，然后将他们的决定返回给 SDK。

在执行任务时，Claude 有时需要与用户确认。在删除文件之前它可能需要权限，或者需要询问为新项目使用哪个数据库。您的应用程序需要向用户展示这些请求，以便 Claude 能够根据他们的输入继续执行。

Claude 在两种情况下请求用户输入：当它需要**使用工具的权限**（例如删除文件或运行命令）时，以及当它有**澄清问题**（通过 `AskUserQuestion` 工具）时。这两者都会触发您的 `canUseTool` 回调，该回调会暂停执行，直到您返回响应。这与 Claude 完成并等待您的下一条消息的正常对话轮次不同。

对于澄清问题，Claude 会生成问题和选项。您的角色是将它们展示给用户并返回他们的选择。您不能在此流程中添加您自己的问题；如果您需要亲自向用户询问某些内容，请在您的应用程序逻辑中单独进行。

回调可以无限期保持待处理状态。执行将保持暂停，直到您的回调返回，并且 SDK 仅在查询本身被取消时才取消等待。如果用户可能需要比您的进程合理运行时间更长的时间来响应，请返回 [`defer`钩子决策](/docs/en/hooks#defer-a-tool-call-for-later)，这使得进程可以退出并稍后从持久化会话中恢复。

本指南向您展示如何检测每种类型的请求并做出适当的响应。

## 检测 Claude 何时需要输入

在您的查询选项中传入一个 `canUseTool` 回调。每当 Claude 需要用户输入时，就会触发该回调，并接收工具名称和输入作为参数：

<CodeGroup>
  ```python Python theme={null}
  async def handle_tool_request(tool_name, input_data, context):
      # Prompt user and return allow or deny
      ...


  options = ClaudeAgentOptions(can_use_tool=handle_tool_request)
  ```

  ```typescript TypeScript theme={null}
  async function handleToolRequest(toolName, input, options) {
    // options includes { signal: AbortSignal, suggestions?: PermissionUpdate[] }
    // Prompt user and return allow or deny
  }

  const options = { canUseTool: handleToolRequest };
  ```
</CodeGroup>

此回调在两种情况下触发：

1. **工具需要批准**：Claude 想要使用未被 [permission rule](/docs/en/agent-sdk/permissions) 或权限模式自动批准的工具。检查该工具的 `tool_name`（例如 `"Bash"`、`"Write"`）。
2. **Claude 提出问题**：Claude 调用 `AskUserQuestion` 工具。检查是否 `tool_name == "AskUserQuestion"` 以进行不同的处理。如果指定了 `tools` 数组，请包含 `AskUserQuestion` 以使其生效。详情请参见 [Handle clarifying questions](#handle-clarifying-questions)。

<Warning>
  **对于自动批准的工具，回调永远不会触发。** 在 [permission evaluation flow](/docs/en/agent-sdk/permissions#how-permissions-are-evaluated) 中较早发生的任何批准、允许规则或诸如 `acceptEdits` 或 `bypassPermissions` 之类的模式，都会在查询 `canUseTool` 之前解析该调用。如果你在 `allowed_tools` 中单独列出一个工具，则对该工具的 `canUseTool` 检查永远不会运行，除非询问规则或 `plan` 模式将调用路由回提示符。对于必须应用于每个工具调用的逻辑，请使用 [`PreToolUse` hook](/docs/en/agent-sdk/hooks)，它会在流程的其余部分之前执行，并且可以允许、拒绝或修改请求。

`AskUserQuestion`, 标记为 [`requiresUserInteraction`](/docs/en/mcp#require-approval-for-a-specific-tool) 的 MCP 工具, 以及连接器工具 [你的组织设置为 `ask`](/docs/en/mcp#organization-controls-on-connector-tools) 即使在匹配允许规则时也会到达回调。在 `dontAsk` 模式下，这些调用会被拒绝，而不是调用回调。
</Warning>

你也可以使用 [`PermissionRequest` 钩子](/docs/en/agent-sdk/hooks#available-hooks) 在 Claude 等待批准时发送外部通知（Slack、电子邮件、推送）。

## 处理工具批准请求

一旦你在查询选项中传入了 `canUseTool` 回调，当 Claude 想要使用权限流中之前没有任何内容批准过的工具时，它就会触发。你的回调会接收三个参数：

| 参数                            | 描述                                                                                                                                                                                                                                                                                                                           |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `toolName`                          | Claude 想要使用的工具名称（例如，`"Bash"`, `"Write"`, `"Edit"`）                                                                                                                                                                                                                                                        |
| `input`                             | Claude 传递给工具的参数。内容因工具而异。                                                                                                                                                                                                                                                                  |
| `options` (TS) / `context` (Python) | 额外上下文，包括可选的 `suggestions`（提议的 `PermissionUpdate` 条目以避免重复提示）和取消信号。在 TypeScript 中，`signal` 是一个 `AbortSignal`；在 Python 中，signal 字段保留供将来使用。关于 Python，请参见 [`ToolPermissionContext`](/docs/en/agent-sdk/python#toolpermissioncontext)。 |

`input` 对象包含特定于工具的参数。常见示例：

| 工具    | 输入字段                            |
| ------- | --------------------------------------- |
| `Bash`  | `command`, `description`, `timeout`     |
| `Write` | `file_path`, `content`                  |
| `Edit`  | `file_path`, `old_string`, `new_string` |
| `Read`  | `file_path`, `offset`, `limit`          |

有关完整的输入架构，请参见 SDK 参考：[Python](/docs/en/agent-sdk/python#tool-input%2Foutput-types) | [TypeScript](/docs/en/agent-sdk/typescript#tool-input-types)。

你可以向用户展示这些信息，以便他们决定是允许还是拒绝该操作，然后返回相应的响应。

以下示例要求 Claude 创建和删除一个测试文件。当 Claude 尝试每个操作时，回调会将工具请求打印到终端，并提示输入 y/n 进行批准。

<CodeGroup>
  ```python Python theme={null}
  import asyncio

  from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query
  from claude_agent_sdk.types import (
      HookMatcher,
      PermissionResultAllow,
      PermissionResultDeny,
      ToolPermissionContext,
  )


  async def can_use_tool(
      tool_name: str, input_data: dict, context: ToolPermissionContext
  ) -> PermissionResultAllow | PermissionResultDeny:
      # Display the tool request
      print(f"\nTool: {tool_name}")
      if tool_name == "Bash":
          print(f"Command: {input_data.get('command')}")
          if input_data.get("description"):
              print(f"Description: {input_data.get('description')}")
      else:
          print(f"Input: {input_data}")

      # Get user approval
      response = input("Allow this action? (y/n): ")

      # Return allow or deny based on user's response
      if response.lower() == "y":
          # Allow: tool executes with the original (or modified) input
          return PermissionResultAllow(updated_input=input_data)
      else:
          # Deny: tool doesn't execute, Claude sees the message
          return PermissionResultDeny(message="User denied this action")


  # Required workaround: dummy hook keeps the stream open for can_use_tool
  async def dummy_hook(input_data, tool_use_id, context):
      return {"continue_": True}


  async def prompt_stream():
      yield {
          "type": "user",
          "message": {
              "role": "user",
              "content": "Create a test file in /tmp and then delete it",
          },
      }


  async def main():
      async for message in query(
          prompt=prompt_stream(),
          options=ClaudeAgentOptions(
              can_use_tool=can_use_tool,
              hooks={"PreToolUse": [HookMatcher(matcher=None, hooks=[dummy_hook])]},
          ),
      ):
          if isinstance(message, ResultMessage) and message.subtype == "success":
              print(message.result)


  asyncio.run(main())
  ```

  ```typescript TypeScript theme={null}
  import { query } from "@anthropic-ai/claude-agent-sdk";
  import * as readline from "readline";

  // Helper to prompt user for input in the terminal
  function prompt(question: string): Promise<string> {
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });
    return new Promise((resolve) =>
      rl.question(question, (answer) => {
        rl.close();
        resolve(answer);
      })
    );
  }

  for await (const message of query({
    prompt: "Create a test file in /tmp and then delete it",
    options: {
      canUseTool: async (toolName, input) => {
        // Display the tool request
        console.log(`\nTool: ${toolName}`);
        if (toolName === "Bash") {
          console.log(`Command: ${input.command}`);
          if (input.description) console.log(`Description: ${input.description}`);
        } else {
          console.log(`Input: ${JSON.stringify(input, null, 2)}`);
        }

        // Get user approval
        const response = await prompt("Allow this action? (y/n): ");

        // Return allow or deny based on user's response
        if (response.toLowerCase() === "y") {
          // Allow: tool executes with the original (or modified) input
          return { behavior: "allow", updatedInput: input };
        } else {
          // Deny: tool doesn't execute, Claude sees the message
          return { behavior: "deny", message: "User denied this action" };
        }
      }
    }
  })) {
    if ("result" in message) console.log(message.result);
  }
  ```
</CodeGroup>

<Note>
  在 Python 中，`can_use_tool` 需要 [streaming mode](/docs/en/agent-sdk/streaming-vs-single-mode)。当您通过 `query(prompt=generator)` 或 `ClaudeSDKClient.connect(prompt=async_iterable)` 传递有限的消息流时，SDK 会在最后一条消息之后、权限回调被调用之前关闭输入流，除非已注册的钩子或进程内 MCP 服务器保持其打开。上面的示例使用返回 `{"continue_": True}` 的 `PreToolUse` 钩子使其保持打开。在没有提示的情况下连接并通过 `ClaudeSDKClient.query()` 发送消息会自行保持流打开，且不需要钩子。
</Note>

此示例使用 `y/n` 流程，其中除 `y` 之外的任何输入都被视为拒绝。在实践中，您可以构建一个更丰富的 UI，允许用户修改请求、提供反馈或完全重定向 Claude。有关您可以响应的所有方式，请参见 [响应工具请求](#respond-to-tool-requests)。

### 响应工具请求

您的回调返回两种响应类型之一：

| 响应  | Python                                     | TypeScript                            |
| --------- | ------------------------------------------ | ------------------------------------- |
| **允许** | `PermissionResultAllow(updated_input=...)` | `{ behavior: "allow", updatedInput }` |
| **拒绝**  | `PermissionResultDeny(message=...)`        | `{ behavior: "deny", message }`       |

当允许时，工具使用 Claude 请求的输入运行，除非您返回修改后的输入，即 TypeScript 中的 `updatedInput` 或 Python 中的 `updated_input`。{/* min-version: 2.1.207 */}在 v2.1.207 之前，Claude Code 会拒绝省略 `updatedInput` 的允许结果，并以验证错误拒绝工具调用。

当拒绝时，请提供一条消息说明原因。Claude 会看到此消息并可能调整其方法。

<CodeGroup>
  ```python Python theme={null}
  from claude_agent_sdk.types import PermissionResultAllow, PermissionResultDeny

  # Allow the tool to execute
  return PermissionResultAllow(updated_input=input_data)

  # Block the tool
  return PermissionResultDeny(message="User rejected this action")
  ```

  ```typescript TypeScript theme={null}
  // Allow the tool to execute
  return { behavior: "allow", updatedInput: input };

  // Block the tool
  return { behavior: "deny", message: "User rejected this action" };
  ```
</CodeGroup>

除了允许或拒绝之外，您还可以修改工具的输入或提供上下文，以帮助 Claude 调整其方法：

* **批准**：让工具按 Claude 的请求执行
* **带修改的批准**：在执行前修改输入（例如，清理路径，添加约束）
* **批准并记住**：回显建议的权限规则，以便下次匹配的调用跳过提示
* **拒绝**：阻止工具并告诉 Claude 原因
* **建议替代方案**：阻止但引导 Claude 转向用户想要的内容
* **完全重定向**：使用 [streaming input](/docs/en/agent-sdk/streaming-vs-single-mode) 向 Claude 发送全新的指令

<Tabs>
  <Tab title="批准">
    用户按原样批准该操作。从回调中原样传递 `input`，工具将完全按 Claude 的请求执行。

    <CodeGroup>
      ```python Python theme={null}
      async def can_use_tool(tool_name, input_data, context):
          print(f"Claude wants to use {tool_name}")
          approved = await ask_user("Allow this action?")

          if approved:
              return PermissionResultAllow(updated_input=input_data)
          return PermissionResultDeny(message="User declined")
      ```

      ```typescript TypeScript theme={null}
      canUseTool: async (toolName, input) => {
        console.log(`Claude wants to use ${toolName}`);
        const approved = await askUser("Allow this action?");

        if (approved) {
          return { behavior: "allow", updatedInput: input };
        }
        return { behavior: "deny", message: "User declined" };
      };
      ```
    </CodeGroup>
  </Tab>

  <Tab title="批准并修改">
    用户同意，但希望先修改请求。你可以在工具执行前更改输入。Claude 会看到结果，但不会被告知你更改了任何内容。适用于清理参数、添加约束或限定访问范围。

    <CodeGroup>
      ```python Python theme={null}
      async def can_use_tool(tool_name, input_data, context):
          if tool_name == "Bash":
              # User approved, but scope all commands to sandbox
              sandboxed_input = {**input_data}
              sandboxed_input["command"] = input_data["command"].replace(
                  "/tmp", "/tmp/sandbox"
              )
              return PermissionResultAllow(updated_input=sandboxed_input)
          return PermissionResultAllow(updated_input=input_data)
      ```

      ```typescript TypeScript theme={null}
      canUseTool: async (toolName, input) => {
        if (toolName === "Bash") {
          // User approved, but scope all commands to sandbox
          const sandboxedInput = {
            ...input,
            command: input.command.replace("/tmp", "/tmp/sandbox")
          };
          return { behavior: "allow", updatedInput: sandboxedInput };
        }
        return { behavior: "allow", updatedInput: input };
      };
      ```
    </CodeGroup>
  </Tab>

  <Tab title="批准并记住">
    用户同意并且不想再被询问此类调用。第三个回调参数携带 `suggestions`，这是一个现成的 [`PermissionUpdate`](/docs/en/agent-sdk/typescript#permissionupdate) 条目的数组。在 `updatedPermissions` 中回传一个即可应用它。具有 `localSettings` 目标的建议会将规则写入 `.claude/settings.local.json`，以便未来的会话在遇到匹配的调用时跳过提示。

    Python 示例需要 `claude-agent-sdk` 0.1.80 或更高版本。

    <CodeGroup>
      ```python Python theme={null}
      async def can_use_tool(tool_name, input_data, context):
          choice = await ask_user(f"Allow {tool_name}?", ["once", "always", "no"])

          if choice == "always":
              persist = [
                  s for s in context.suggestions if s.destination == "localSettings"
              ]
              return PermissionResultAllow(
                  updated_input=input_data, updated_permissions=persist
              )
          if choice == "once":
              return PermissionResultAllow(updated_input=input_data)
          return PermissionResultDeny(message="User declined")
      ```

      ```typescript TypeScript theme={null}
      canUseTool: async (toolName, input, { suggestions = [] }) => {
        const choice = await askUser(`Allow ${toolName}?`, ["once", "always", "no"]);

        if (choice === "always") {
          const persist = suggestions.filter(
            (s) => s.destination === "localSettings"
          );
          return {
            behavior: "allow",
            updatedInput: input,
            updatedPermissions: persist
          };
        }
        if (choice === "once") {
          return { behavior: "allow", updatedInput: input };
        }
        return { behavior: "deny", message: "User declined" };
      };
      ```
    </CodeGroup>
  </Tab>

  <Tab title="拒绝">
    用户不希望发生此操作。阻止工具并提供一条解释原因的消息。Claude 会看到此消息并可能尝试其他方法。

    <CodeGroup>
      ```python Python theme={null}
      async def can_use_tool(tool_name, input_data, context):
          approved = await ask_user(f"Allow {tool_name}?")

          if not approved:
              return PermissionResultDeny(message="User rejected this action")
          return PermissionResultAllow(updated_input=input_data)
      ```

      ```typescript TypeScript theme={null}
      canUseTool: async (toolName, input) => {
        const approved = await askUser(`Allow ${toolName}?`);

        if (!approved) {
          return {
            behavior: "deny",
            message: "User rejected this action"
          };
        }
        return { behavior: "allow", updatedInput: input };
      };
      ```
    </CodeGroup>
  </Tab>

  <Tab title="建议替代方案">
    用户不想要此特定操作，但有其他想法。阻止该工具并在你的消息中包含指导。Claude 会阅读此内容，并根据你的反馈决定如何进行。

    <CodeGroup>
      ```python Python theme={null}
      async def can_use_tool(tool_name, input_data, context):
          if tool_name == "Bash" and "rm" in input_data.get("command", ""):
              # User doesn't want to delete, suggest archiving instead
              return PermissionResultDeny(
                  message="User doesn't want to delete files. They asked if you could compress them into an archive instead."
              )
          return PermissionResultAllow(updated_input=input_data)
      ```

      ```typescript TypeScript theme={null}
      canUseTool: async (toolName, input) => {
        if (toolName === "Bash" && input.command.includes("rm")) {
          // User doesn't want to delete, suggest archiving instead
          return {
            behavior: "deny",
            message:
              "User doesn't want to delete files. They asked if you could compress them into an archive instead."
          };
        }
        return { behavior: "allow", updatedInput: input };
      };
      ```
    </CodeGroup>
  </Tab>

  <Tab title="完全重定向">
    对于完全的方向改变（不仅仅是提示），请使用 [流式输入](/docs/en/agent-sdk/streaming-vs-single-mode) 直接向 Claude 发送新指令。这会绕过当前的工具请求，并给 Claude 提供全新的需要遵循的指令。
  </Tab>
</Tabs>

## 处理澄清问题

当 Claude 在处理一个有多种有效方法的任务时需要更多指导，它会调用 `AskUserQuestion` 工具。这会触发你的 `canUseTool` 回调，并将 `toolName` 设置为 `AskUserQuestion`。输入包含 Claude 以多项选择形式提出的问题，你需要将其展示给用户并返回他们的选择。

<Tip>
  澄清问题在 [`plan` 模式](/docs/en/agent-sdk/permissions#plan-mode-plan) 中尤为常见，Claude 会在提出计划之前探索代码库并提出问题。这使得计划模式成为交互式工作流的理想选择，此时你希望 Claude 在进行更改之前收集需求。
</Tip>

以下步骤展示了如何处理澄清问题：

<Steps>
  <Step title="传递一个 canUseTool 回调">
    在你的查询选项中传递一个 `canUseTool` 回调。默认情况下，`AskUserQuestion` 是可用的。如果你指定了一个 `tools` 数组来限制 Claude 的功能（例如，一个只读代理只有 `Read`、`Glob` 和 `Grep`），请在该数组中包含 `AskUserQuestion`。否则，Claude 将无法提出澄清问题：

    <CodeGroup>
      ```python Python theme={null}
      async for message in query(
          prompt="Analyze this codebase",
          options=ClaudeAgentOptions(
              # Include AskUserQuestion in your tools list
              tools=["Read", "Glob", "Grep", "AskUserQuestion"],
              can_use_tool=can_use_tool,
          ),
      ):
          print(message)
      ```

      ```typescript TypeScript theme={null}
      for await (const message of query({
        prompt: "Analyze this codebase",
        options: {
          // Include AskUserQuestion in your tools list
          tools: ["Read", "Glob", "Grep", "AskUserQuestion"],
          canUseTool: async (toolName, input) => {
            // Handle clarifying questions here
          }
        }
      })) {
        console.log(message);
      }
      ```
    </CodeGroup>
  </Step>

  <Step title="检测 AskUserQuestion">
    在你的回调中，检查 `toolName` 是否等于 `AskUserQuestion`，以将其与其他工具区别处理：

    <CodeGroup>
      ```python Python theme={null}
      async def can_use_tool(tool_name: str, input_data: dict, context):
          if tool_name == "AskUserQuestion":
              # Your implementation to collect answers from the user
              return await handle_clarifying_questions(input_data)
          # Handle other tools normally
          return await prompt_for_approval(tool_name, input_data)
      ```

      ```typescript TypeScript theme={null}
      canUseTool: async (toolName, input) => {
        if (toolName === "AskUserQuestion") {
          // Your implementation to collect answers from the user
          return handleClarifyingQuestions(input);
        }
        // Handle other tools normally
        return promptForApproval(toolName, input);
      };
      ```
    </CodeGroup>
  </Step>

  <Step title="解析问题输入">
    该输入在一个 `questions` 数组中包含 Claude 的问题。每个问题都有一个 `question`（要显示的文本）、`options`（选项）和 `multiSelect`（是否允许进行多项选择）：

    ```json theme={null}
    {
      "questions": [
        {
          "question": "How should I format the output?",
          "header": "Format",
          "options": [
            { "label": "Summary", "description": "Brief overview" },
            { "label": "Detailed", "description": "Full explanation" }
          ],
          "multiSelect": false
        },
        {
          "question": "Which sections should I include?",
          "header": "Sections",
          "options": [
            { "label": "Introduction", "description": "Opening context" },
            { "label": "Conclusion", "description": "Final summary" }
          ],
          "multiSelect": true
        }
      ]
    }
    ```

    有关完整的字段描述，请参见 [Question format](#question-format)。
  </Step>

  <Step title="从用户处收集答案">
    向用户展示问题并收集他们的选择。您如何执行此操作取决于您的应用程序：终端提示、Web 表单、移动对话框等。
  </Step>

  <Step title="将答案返回给 Claude">
    构建 `answers` 对象作为记录，其中每个键是 `question` 文本，每个值是所选选项的 `label`：

    | 来自问题对象                                     | 用作 |
    | ------------------------------------------------------------ | ------ |
    | `question` 字段（例如，`"How should I format the output?"`） | 键    |
    | 所选选项的 `label` 字段（例如，`"Summary"`）          | 值  |

    对于多选问题，传递一个标签数组或使用 `", "` 连接它们。如果您 [支持自由文本输入](#support-free-text-input)，请使用用户的自定义文本作为值。

    <CodeGroup>
      ```python Python theme={null}
      return PermissionResultAllow(
          updated_input={
              "questions": input_data.get("questions", []),
              "answers": {
                  "How should I format the output?": "Summary",
                  "Which sections should I include?": ["Introduction", "Conclusion"],
              },
          }
      )
      ```

      ```typescript TypeScript theme={null}
      return {
        behavior: "allow",
        updatedInput: {
          questions: input.questions,
          answers: {
            "How should I format the output?": "Summary",
            "Which sections should I include?": "Introduction, Conclusion"
          }
        }
      };
      ```
    </CodeGroup>
  </Step>
</Steps>

### Question format

输入在一个 `questions` 数组中包含 Claude 生成的问题。每个问题都有以下字段：

| 字段         | 描述                                                                                                                            |
| ------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `question`    | 要显示的完整问题文本                                                                                                      |
| `header`      | 问题的简短标签（最多 12 个字符）                                                                                       |
| `options`     | 包含 2-4 个选项的数组，每个选项都有 `label` 和 `description`。TypeScript：可选 `preview`（参见 [下文](#option-previews-typescript)) |
| `multiSelect` | 如果为 `true`，用户可以选择多个选项                                                                                           |

您的回调接收到的结构：

```json theme={null}
{
  "questions": [
    {
      "question": "How should I format the output?",
      "header": "Format",
      "options": [
        { "label": "Summary", "description": "Brief overview of key points" },
        { "label": "Detailed", "description": "Full explanation with examples" }
      ],
      "multiSelect": false
    }
  ]
}
```

#### 选项预览 (TypeScript)

`toolConfig.askUserQuestion.previewFormat` 为每个选项添加一个 `preview` 字段，以便您的应用程序可以在标签旁边显示可视化模型。如果不进行此设置，Claude 将不会生成预览，且该字段将不存在。

| `previewFormat` | `preview` 包含                                                                                            |
| :-------------- | :------------------------------------------------------------------------------------------------------------ |
| 未设置（默认） | 字段不存在。Claude 不生成预览。                                                           |
| `"markdown"`    | ASCII 艺术和围栏代码块                                                                              |
| `"html"`        | 一个带样式的 `<div>` 片段（在回调运行前，SDK 会拒绝 `<script>`、`<style>` 和 `<!DOCTYPE>`） |

该格式适用于会话中的所有问题。Claude 会在视觉比较有帮助的选项（如布局选择、配色方案）上包含 `preview`，并在无帮助的选项（如是/否确认、纯文本选择）上省略它。在渲染前检查 `undefined`。

```typescript theme={null}
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "Help me choose a card layout",
  options: {
    toolConfig: {
      askUserQuestion: { previewFormat: "html" }
    },
    canUseTool: async (toolName, input) => {
      // input.questions[].options[].preview is an HTML string or undefined
      return { behavior: "allow", updatedInput: input };
    }
  }
})) {
  // ...
}
```

带有 HTML 预览的选项：

```json theme={null}
{
  "label": "Compact",
  "description": "Title and metric value only",
  "preview": "<div style=\"padding:12px;border:1px solid #ddd;border-radius:8px\"><div style=\"font-size:12px;color:#666\">Active users</div><div style=\"font-size:28px;font-weight:600\">1,284</div></div>"
}
```

### 响应格式

返回一个 `answers` 对象，将每个问题的 `question` 字段映射到所选选项的 `label`：

| 字段       | 描述                                                                          |
| ----------- | ------------------------------------------------------------------------------------ |
| `questions` | 传递原始问题数组（工具处理所必需）             |
| `answers`   | 键为问题文本、值为所选标签的对象                   |
| `response`  | 用户键入的可选自由格式回复，而非回答结构化问题 |

对于多选问题，传递一个标签数组或使用 `", "` 连接它们。对于诸如“其他”选项等针对单个问题的自由文本，请将用户的文本放在 `answers[question]` 中，如 [支持自由文本输入](#support-free-text-input) 所示。仅当您的 UI 允许用户关闭问题卡片并输入不属于任何特定问题答案的通用回复时，才设置 `response`。设置 `response` 后，Claude 将收到“用户回复：…”而不是按问题划分的答案列表。

```json theme={null}
{
  "questions": [
    // ...
  ],
  "answers": {
    "How should I format the output?": "Summary",
    "Which sections should I include?": ["Introduction", "Conclusion"]
  }
}
```

#### 支持自由文本输入

Claude 的预定义选项并不总能涵盖用户的需求。若要让用户键入他们自己的答案：

* 在 Claude 的选项之后显示一个接受文本输入的额外“其他”选项
* 使用用户的自定义文本作为答案值（而不是“其他”一词）

有关完整的实现，请参阅下方的 [完整示例](#complete-example)。

### 完整示例

当需要用户输入才能继续时，Claude 会提出澄清问题。例如，当被要求帮助决定移动应用程序的技术栈时，Claude 可能会询问跨平台与原生、后端偏好或目标平台。这些问题有助于 Claude 做出符合用户偏好的决策，而不是猜测。

此示例在终端应用程序中处理这些问题。以下是每个步骤中发生的情况：

1. **路由请求**：`canUseTool` 回调检查工具名称是否为 `"AskUserQuestion"` 并路由到专用处理程序
2. **显示问题**：处理程序循环遍历 `questions` 数组，并打印带有编号选项的每个问题
3. **收集输入**：用户可以输入数字来选择选项，或直接输入自由文本（例如，“jquery”、“i don't know”）
4. **映射答案**：代码检查输入是数字（使用选项的标签）还是自由文本（直接使用文本）
5. **返回给 Claude**：响应包含原始的 `questions` 数组和 `answers` 映射

将 TypeScript 版本另存为 `ask.ts` 并使用 `npx tsx ask.ts` 运行，或者将 Python 版本另存为 `ask.py` 并使用 `python ask.py` 运行。

<CodeGroup>
  ```python Python theme={null}
  import asyncio

  from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query
  from claude_agent_sdk.types import HookMatcher, PermissionResultAllow


  def parse_response(response: str, options: list) -> str:
      """Parse user input as option number(s) or free text."""
      try:
          indices = [int(s.strip()) - 1 for s in response.split(",")]
          labels = [options[i]["label"] for i in indices if 0 <= i < len(options)]
          return ", ".join(labels) if labels else response
      except ValueError:
          return response


  async def handle_ask_user_question(input_data: dict) -> PermissionResultAllow:
      """Display Claude's questions and collect user answers."""
      answers = {}

      for q in input_data.get("questions", []):
          print(f"\n{q['header']}: {q['question']}")

          options = q["options"]
          for i, opt in enumerate(options):
              print(f"  {i + 1}. {opt['label']} - {opt['description']}")
          if q.get("multiSelect"):
              print("  (Enter numbers separated by commas, or type your own answer)")
          else:
              print("  (Enter a number, or type your own answer)")

          response = input("Your choice: ").strip()
          answers[q["question"]] = parse_response(response, options)

      return PermissionResultAllow(
          updated_input={
              "questions": input_data.get("questions", []),
              "answers": answers,
          }
      )


  async def can_use_tool(
      tool_name: str, input_data: dict, context
  ) -> PermissionResultAllow:
      # Route AskUserQuestion to our question handler
      if tool_name == "AskUserQuestion":
          return await handle_ask_user_question(input_data)
      # Auto-approve other tools for this example
      return PermissionResultAllow(updated_input=input_data)


  async def prompt_stream():
      yield {
          "type": "user",
          "message": {
              "role": "user",
              "content": "Help me decide on the tech stack for a new mobile app",
          },
      }


  # Required workaround: dummy hook keeps the stream open for can_use_tool
  async def dummy_hook(input_data, tool_use_id, context):
      return {"continue_": True}


  async def main():
      async for message in query(
          prompt=prompt_stream(),
          options=ClaudeAgentOptions(
              can_use_tool=can_use_tool,
              hooks={"PreToolUse": [HookMatcher(matcher=None, hooks=[dummy_hook])]},
          ),
      ):
          if isinstance(message, ResultMessage) and message.subtype == "success":
              print(message.result)


  asyncio.run(main())
  ```

  ```typescript TypeScript theme={null}
  import { query } from "@anthropic-ai/claude-agent-sdk";
  import * as readline from "readline/promises";

  // Helper to prompt user for input in the terminal
  async function prompt(question: string): Promise<string> {
    const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
    const answer = await rl.question(question);
    rl.close();
    return answer;
  }

  // Parse user input as option number(s) or free text
  function parseResponse(response: string, options: any[]): string {
    const indices = response.split(",").map((s) => parseInt(s.trim()) - 1);
    const labels = indices
      .filter((i) => !isNaN(i) && i >= 0 && i < options.length)
      .map((i) => options[i].label);
    return labels.length > 0 ? labels.join(", ") : response;
  }

  // Display Claude's questions and collect user answers
  async function handleAskUserQuestion(input: any) {
    const answers: Record<string, string> = {};

    for (const q of input.questions) {
      console.log(`\n${q.header}: ${q.question}`);

      const options = q.options;
      options.forEach((opt: any, i: number) => {
        console.log(`  ${i + 1}. ${opt.label} - ${opt.description}`);
      });
      if (q.multiSelect) {
        console.log("  (Enter numbers separated by commas, or type your own answer)");
      } else {
        console.log("  (Enter a number, or type your own answer)");
      }

      const response = (await prompt("Your choice: ")).trim();
      answers[q.question] = parseResponse(response, options);
    }

    // Return the answers to Claude (must include original questions)
    return {
      behavior: "allow",
      updatedInput: { questions: input.questions, answers }
    };
  }

  async function main() {
    for await (const message of query({
      prompt: "Help me decide on the tech stack for a new mobile app",
      options: {
        canUseTool: async (toolName, input) => {
          // Route AskUserQuestion to our question handler
          if (toolName === "AskUserQuestion") {
            return handleAskUserQuestion(input);
          }
          // Auto-approve other tools for this example
          return { behavior: "allow", updatedInput: input };
        }
      }
    })) {
      if ("result" in message) console.log(message.result);
    }
  }

  main();
  ```
</CodeGroup>

## 局限性

* **子代理**：`AskUserQuestion`目前无法在通过 Agent 工具生成的子代理中使用
* **问题限制**：每次`AskUserQuestion`调用支持 1-4 个问题，每个问题有 2-4 个选项

## 获取用户输入的其他方式

`canUseTool`回调和`AskUserQuestion`工具涵盖了大多数审批和澄清场景，但 SDK 还提供了其他获取用户输入的方式：

### 流式输入

在您需要以下操作时，请使用 [流式输入](/docs/en/agent-sdk/streaming-vs-single-mode)：

* **在任务执行中途中断代理**：在 Claude 工作时发送取消信号或改变方向
* **提供额外上下文**：无需等待 Claude 询问，直接添加其所需的信息
* **构建聊天界面**：让用户在长时间运行的操作中发送后续消息

流式输入非常适合会话式 UI，用户可以在整个执行过程中与代理进行交互，而不仅仅是在审批检查点。

### 自定义工具

在以下情况使用 [自定义工具](/docs/en/agent-sdk/custom-tools)：

* **收集结构化输入**：构建超出 `AskUserQuestion` 多选格式的表单、向导或多步骤工作流
* **集成外部审批系统**：连接到现有的工单、工作流或审批平台
* **实现特定领域的交互**：创建量身定制的工具以满足应用程序的需求，例如代码审查界面或部署检查清单

自定义工具让您能够完全控制交互，但与使用内置的 `canUseTool` 回调相比，需要更多的实现工作。

## 相关资源

* [配置权限](/docs/en/agent-sdk/permissions)：设置权限模式和规则
* [使用钩子控制执行](/docs/en/agent-sdk/hooks)：在代理生命周期的关键点运行自定义代码
* [TypeScript SDK 参考](/docs/en/agent-sdk/typescript#canusetool)：完整的 canUseTool API 文档

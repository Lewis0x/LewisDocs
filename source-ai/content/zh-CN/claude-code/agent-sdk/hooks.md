---
title: 使用钩子拦截并控制代理行为
source_id: claude-code/agent-sdk/hooks
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/agent-sdk/hooks
owner: Anthropic
content_sha256: df572790d39a7200dc3cf91f7f2329aaf293731b922bcf1e1bcb4013e4055627
translation_of: claude-code/agent-sdk/hooks
translation_model: k3
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/agent-sdk/hooks)

Content owner: Anthropic

> ## 文档索引
> 获取完整文档索引：https://code.claude.com/docs/llms.txt
> 在进一步探索之前，使用此文件发现所有可用页面。

# 使用钩子拦截并控制代理行为

> 在关键执行点使用钩子拦截并自定义代理行为

钩子是响应代理事件而运行你的代码的回调函数，例如工具被调用、会话开始或执行停止。使用钩子，你可以：

* **阻止危险操作**在执行前发生，例如破坏性 shell 命令或未经授权的文件访问
* **记录并审计**每次工具调用，用于合规、调试或分析
* **转换输入和输出**以净化数据、注入凭据或重定向文件路径
* **要求人工批准**敏感操作，例如数据库写入或 API 调用
* **跟踪会话生命周期**以管理状态、清理资源或发送通知

本指南介绍钩子如何工作以及如何配置它们，并提供常见模式的示例，例如阻止工具、修改输入和转发通知。

## 钩子如何工作

<Steps>
  <Step title="事件触发">
    代理执行期间发生某些事情，SDK 触发一个事件：工具即将被调用（`PreToolUse`）、工具返回了结果（`PostToolUse`）、子代理启动或停止、代理空闲，或执行完成。请参阅[完整事件列表](#available-hooks)。
  </Step>

  <Step title="SDK 收集已注册的钩子">
    SDK 检查为该事件类型注册的钩子。这包括你在 `options.hooks` 中传入的回调钩子，以及当相应的 [`settingSources`](/docs/en/agent-sdk/typescript#settingsource) 或 [`setting_sources`](/docs/en/agent-sdk/python#settingsource) 条目启用时来自设置文件的 shell 命令钩子；默认 `query()` 选项会启用它。
  </Step>

  <Step title="匹配器过滤运行哪些钩子">
    如果钩子具有 [`matcher`](#matchers) 模式（例如 `"Write|Edit"`），SDK 会将其与事件目标进行测试（例如工具名称）。没有匹配器的钩子会为该类型的每个事件运行。
  </Step>

  <Step title="回调函数执行">
    每个匹配钩子的[回调函数](#callback-functions)都会接收关于正在发生情况的输入：工具名称、其参数、会话 ID 以及其他特定于事件的详细信息。
  </Step>

  <Step title="你的回调返回决定">
    在执行任何操作（日志记录、API 调用、验证）之后，你的回调返回一个[输出对象](#outputs)，告诉代理该做什么：允许操作、阻止它、修改输入，或将上下文注入对话。
  </Step>
</Steps>

以下示例将这些步骤组合在一起。它注册一个 `PreToolUse` 钩子（步骤 1），并带有 `"Write|Edit"` 匹配器（步骤 3），因此回调仅在文件写入工具时触发。触发时，回调接收工具的输入（步骤 4），检查文件路径是否指向 `.env` 文件，并返回 `permissionDecision: "deny"` 以阻止操作（步骤 5）：

<CodeGroup>
  ```python Python theme={null}
  import asyncio
  from claude_agent_sdk import (
      AssistantMessage,
      ClaudeSDKClient,
      ClaudeAgentOptions,
      HookMatcher,
      ResultMessage,
  )


  # Define a hook callback that receives tool call details
  async def protect_env_files(input_data, tool_use_id, context):
      # Extract the file path from the tool's input arguments
      file_path = input_data["tool_input"].get("file_path", "")
      file_name = file_path.split("/")[-1]

      # Block the operation if targeting a .env file
      if file_name == ".env":
          return {
              "hookSpecificOutput": {
                  "hookEventName": input_data["hook_event_name"],
                  "permissionDecision": "deny",
                  "permissionDecisionReason": "Cannot modify .env files",
              }
          }

      # Return empty object to allow the operation
      return {}


  async def main():
      options = ClaudeAgentOptions(
          hooks={
              # Register the hook for PreToolUse events
              # The matcher filters to only Write and Edit tool calls
              "PreToolUse": [HookMatcher(matcher="Write|Edit", hooks=[protect_env_files])]
          }
      )

      async with ClaudeSDKClient(options=options) as client:
          await client.query("Create a .env file with the standard local development database configuration")
          async for message in client.receive_response():
              # Filter for assistant and result messages
              if isinstance(message, (AssistantMessage, ResultMessage)):
                  print(message)


  asyncio.run(main())
  ```

  ```typescript TypeScript theme={null}
  import { query, HookCallback, PreToolUseHookInput } from "@anthropic-ai/claude-agent-sdk";

  // Define a hook callback with the HookCallback type
  const protectEnvFiles: HookCallback = async (input, toolUseID, { signal }) => {
    // Cast input to the specific hook type for type safety
    const preInput = input as PreToolUseHookInput;

    // Cast tool_input to access its properties (typed as unknown in the SDK)
    const toolInput = preInput.tool_input as Record<string, unknown>;
    const filePath = toolInput?.file_path as string;
    const fileName = filePath?.split("/").pop();

    // Block the operation if targeting a .env file
    if (fileName === ".env") {
      return {
        hookSpecificOutput: {
          hookEventName: preInput.hook_event_name,
          permissionDecision: "deny",
          permissionDecisionReason: "Cannot modify .env files"
        }
      };
    }

    // Return empty object to allow the operation
    return {};
  };

  for await (const message of query({
    prompt: "Create a .env file with the standard local development database configuration",
    options: {
      hooks: {
        // Register the hook for PreToolUse events
        // The matcher filters to only Write and Edit tool calls
        PreToolUse: [{ matcher: "Write|Edit", hooks: [protectEnvFiles] }]
      }
    }
  })) {
    // Filter for assistant and result messages
    if (message.type === "assistant" || message.type === "result") {
      console.log(message);
    }
  }
  ```
</CodeGroup>

当你运行任一脚本时，Claude 会尝试创建 `.env` 文件，钩子会拒绝该工具调用，Claude 的最终回复会解释它无法创建 `.env` 文件。

## 可用的钩子

SDK 为代理执行的不同阶段提供钩子。部分钩子在两个 SDK 中都可用，而其他钩子仅适用于 TypeScript。

| 钩子事件                                             | Python SDK | TypeScript SDK | 触发时机                                                                                                                        | 示例用例                                                            |
| ------------------------------------------------------ | ---------- | -------------- | --------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| `PreToolUse`                                           | 是        | 是            | 工具调用请求（可阻止或修改）                                                                                                 | 阻止危险的 shell 命令                                              |
| `PostToolUse`                                          | 是        | 是            | 工具执行结果                                                                                                                   | 将所有文件更改记录到审计日志                                         |
| `PostToolUseFailure`                                   | 是        | 是            | 工具执行失败                                                                                                                  | 处理或记录工具错误                                                   |
| `PostToolBatch`                                        | 否         | 是            | 整批工具调用完成解析，每批一次，在下一次模型调用之前                                                          | 为整个批次注入一次约定                                 |
| `UserPromptSubmit`                                     | 是        | 是            | 用户提示提交                                                                                                                  | 向提示中注入额外的上下文                                      |
| [`UserPromptExpansion`](/docs/en/hooks#userpromptexpansion) | 否         | 是            | 用户输入的命令或 MCP 提示在到达 Claude 之前展开为提示。当 Claude 自己调用技能时不会触发 | 阻止命令被直接调用，或在输入技能时添加上下文 |
| `MessageDisplay`                                       | 否         | 是            | 包含文本的助手消息完成，每条消息一次，包含完整的消息文本                                                   | 在不改变记录的情况下对显示的文本进行脱敏或重新格式化       |
| `Stop`                                                 | 是        | 是            | 代理执行停止                                                                                                                    | 在退出前保存会话状态                                              |
| `StopFailure`                                          | 否         | 是            | 回合以 API 错误而非正常停止结束                                                                                | 记录失败或发送警报                                                 |
| `SubagentStart`                                        | 是        | 是            | 子代理初始化                                                                                                                 | 跟踪并行任务的生成                                                |
| `SubagentStop`                                         | 是        | 是            | 子代理完成                                                                                                                     | 汇总并行任务的结果                                       |
| `PreCompact`                                           | 是        | 是            | 会话压缩请求                                                                                                         | 在总结前归档完整记录                                  |
| `PostCompact`                                          | 否         | 是            | 会话压缩完成                                                                                                       | 记录生成的摘要                                                   |
| `PermissionRequest`                                    | 是        | 是            | 即将显示权限对话框                                                                                                    | 自定义权限处理                                                  |
| `PermissionDenied`                                     | 否         | 是            | 自动模式分类器拒绝工具调用                                                                                             | 记录分类器拒绝情况或告知模型可以重试                       |
| `SessionStart`                                         | 否         | 是            | 会话初始化                                                                                                                  | 初始化日志和遥测                                            |
| `SessionEnd`                                           | 否         | 是            | 会话终止                                                                                                                     | 清理临时资源                                                |
| `Notification`                                         | 是        | 是            | 代理状态消息                                                                                                                   | 向 Slack 或 PagerDuty 发送代理状态更新                             |
| `Setup`                                                | 否         | 是            | 会话设置/维护                                                                                                               | 运行初始化任务                                                    |
| `TeammateIdle`                                         | 否         | 是            | 队友变为空闲                                                                                                                   | 重新分配工作或发出通知                                                     |
| `TaskCreated`                                          | 否         | 是            | 通过 `TaskCreate` 工具创建任务                                                                                             | 强制执行任务命名规范                                             |
| `TaskCompleted`                                        | 否         | 是            | 后台任务完成                                                                                                               | 汇总并行任务的结果                                       |
| `Elicitation`                                          | 否         | 是            | MCP 服务器在任务中途请求用户输入                                                                                              | 以编程方式响应 MCP 输入请求                              |
| `ElicitationResult`                                    | 否         | 是            | 用户响应 MCP 引出请求                                                                                                   | 在响应返回服务器之前修改或阻止它                |
| `ConfigChange`                                         | 否         | 是            | 配置文件发生更改                                                                                                              | 动态重新加载设置                                                 |
| `InstructionsLoaded`                                   | 否         | 是            | `CLAUDE.md` 或规则文件被加载到上下文中                                                                                      | 审计哪些指令文件被加载                                          |
| `WorktreeCreate`                                       | 否         | 是            | 创建 Git 工作树                                                                                                                    | 跟踪隔离的工作区                                                   |
| `WorktreeRemove`                                       | 否         | 是            | 移除 Git 工作树                                                                                                                    | 清理工作区资源                                                |
| `CwdChanged`                                           | 否         | 是            | 会话期间工作目录发生更改                                                                                          | 按目录重新加载环境变量                                  |
| `FileChanged`                                          | 否         | 是            | 被监视的文件被修改、创建或删除                                                                                         | 项目文件更改时重新加载配置                              |

## 配置钩子

要配置钩子，请将其传入代理选项的 `hooks` 字段（Python 中为 `ClaudeAgentOptions`，TypeScript 中为 `options` 对象）。此代码片段假设你已经定义了一个钩子回调，例如上面示例中 Python 的 `protect_env_files` 或 TypeScript 的 `protectEnvFiles`：

<CodeGroup>
  ```python Python theme={null}
  options = ClaudeAgentOptions(
      hooks={"PreToolUse": [HookMatcher(matcher="Bash", hooks=[my_callback])]}
  )

  async with ClaudeSDKClient(options=options) as client:
      await client.query("Your prompt")
      async for message in client.receive_response():
          print(message)
  ```

  ```typescript TypeScript theme={null}
  for await (const message of query({
    prompt: "Your prompt",
    options: {
      hooks: {
        PreToolUse: [{ matcher: "Bash", hooks: [myCallback] }]
      }
    }
  })) {
    console.log(message);
  }
  ```
</CodeGroup>

`hooks` 选项在 Python 中是字典，在 TypeScript 中是对象，其中：

* **键**：[钩子事件名称](#available-hooks) 例如 `'PreToolUse'`、`'PostToolUse'` 和 `'Stop'`
* **值**：[匹配器](#matchers) 的数组，每个匹配器包含一个可选的过滤模式和你的 [回调函数](#callback-functions)

### 匹配器

使用匹配器来过滤回调何时触发。`matcher` 字段根据钩子事件类型匹配不同的值。例如，基于工具的钩子针对工具名称进行匹配，而 `Notification` 钩子针对通知类型进行匹配。有关每种事件类型的完整匹配器值列表，请参阅[Claude Code钩子参考](/docs/en/hooks#matcher-patterns)。

SDK 匹配器遵循与[设置文件中的匹配器](/docs/en/hooks#matcher-patterns)相同的规则。仅包含字母、数字、`_`、`-`、空格、`,` 和 `|` 的匹配器将作为精确字符串进行比较，备选值由 `|` 或 `,` 及可选的周围空格分隔，因此 `Write|Edit` 和 `Write, Edit` 各自精确匹配那两个工具，而 `code-reviewer` 仅匹配该代理类型。匹配器为 `*`、空字符串或完全省略匹配器时，将匹配该事件的每次发生。

包含任何其他字符的匹配器将作为非锚定正则表达式求值，因此 `^mcp__` 匹配每个 MCP 工具，`Edit.*` 同时匹配 `Edit` 和 `NotebookEdit`。当需要整串匹配时，将正则表达式包裹在 `^` 和 `$` 中。

像 `mcp__memory` 或 `mcp__brave-search` 这样的匹配器只包含精确匹配字符，因此会作为精确字符串进行比较，不会匹配任何工具；请使用 `mcp__memory__.*` 来匹配该服务器的所有工具。

精确匹配集中的连字符需要 v2.1.195 或更高版本的 Claude Code 运行时。在早期版本中，像 `code-reviewer` 这样带连字符的名称将作为非锚定正则表达式求值，必须锚定为 `^code-reviewer$` 才能精确匹配。

`StopFailure` 和 `FileChanged` 使用更窄的精确匹配集，仅包含字母、数字、`_` 和 `|`。在这两个事件的匹配器中出现连字符、空格或逗号会使其保持在正则表达式路径上，且只有 `|` 分隔备选值，因此应写作 `rate_limit|overloaded`，而不是 `rate_limit, overloaded`。`FileChanged` 还额外使用其匹配器来构建字面文件名的监视列表；请参阅[钩子参考中的 FileChanged](/docs/en/hooks#filechanged)。

| 选项      | 类型             | 默认值       | 描述                                                                                                                                                                                                                                                                                                                                                              |
| --------- | ---------------- | ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `matcher` | `string`         | `undefined` | 按照上述比较规则与事件的过滤字段匹配的模式。对于工具钩子,这是工具名称。内置工具包括 `Bash`、`Read`、`Write`、`Edit`、`Glob`、`Grep`、`WebFetch`、`Agent` 等(完整列表请参阅 [工具输入类型](/docs/en/agent-sdk/typescript#tool-input-types))。MCP 工具使用 `mcp__<server>__<action>` 模式。|
| `hooks`   | `HookCallback[]` | -           | 必填。模式匹配时要执行的回调函数数组                                                                                                                                                                                                                                                                                                                                |
| `timeout` | `number`         | `undefined` | 超时时间(秒)。省略时应用每个事件的默认值:大多数事件为 10 分钟,`UserPromptSubmit` 为 30 秒。少数事件以更短的限制运行,例如 `MessageDisplay` 为 10 秒                                                                                                                                                                      |

尽可能使用 `matcher` 模式来针对特定工具。带有 `'Bash'` 的匹配器仅对 Bash 命令运行,而省略该模式则会让回调在事件的每次出现时都运行。

对于基于工具的钩子,匹配器仅按工具名称过滤,而不按文件路径或其他参数过滤。要按文件路径过滤,请在回调中检查 `tool_input.file_path`。

<Tip>
  **发现工具名称:** 请参阅 [工具输入类型](/docs/en/agent-sdk/typescript#tool-input-types) 获取内置工具名称的完整列表,或者添加一个没有匹配器的钩子来记录会话中发出的所有工具调用。

  **MCP 工具命名:** MCP 工具始终以 `mcp__` 开头,后跟服务器名称和操作:`mcp__<server>__<action>`。例如,如果你配置了一个名为 `playwright` 的服务器,其工具将命名为 `mcp__playwright__browser_screenshot`、`mcp__playwright__browser_click` 等等。服务器名称来自你在 `mcpServers` 配置中使用的键。
</Tip>

### 回调函数

#### 输入

每个钩子回调接收三个参数：

* **输入数据：** 包含事件详情的类型化对象。每种钩子类型都有自己的输入结构。例如，`PreToolUseHookInput` 包含 `tool_name` 和 `tool_input`，而 `NotificationHookInput` 包含 `message`。完整的类型定义请参阅 [TypeScript](/docs/en/agent-sdk/typescript#hookinput) 和 [Python](/docs/en/agent-sdk/python#hookinput) SDK 参考。
  * 所有钩子输入都共享 `session_id`、`cwd` 和 `hook_event_name`。
  * `agent_id` 和 `agent_type` 在钩子于子代理内部触发时被填充。在 TypeScript 中，它们位于基础钩子输入上，对所有钩子类型可用。在 Python 中，它们是 `PreToolUse`、`PostToolUse`、`PostToolUseFailure` 和 `PermissionRequest` 上的可选字段，也是 `SubagentStart` 和 `SubagentStop` 上的必填字段。
* **工具使用 ID**（`str | None` / `string | undefined`）：用于关联同一工具调用的 `PreToolUse` 和 `PostToolUse` 事件。
* **上下文：** 在 TypeScript 中，包含一个用于取消的 `signal` 属性（`AbortSignal`）。在 Python 中，此参数保留供将来使用。

#### 输出

你的回调会返回一个包含两类字段的对象：

* **顶层字段**在每个事件上的作用都相同：`systemMessage` 向用户显示一条消息，而 `continue`（Python 中为 `continue_`）决定代理在此钩子之后是否继续运行。
* **`hookSpecificOutput`** 控制当前操作。其中的字段取决于钩子事件类型。对于 `PreToolUse` 钩子，你可以在这里设置 `permissionDecision`（`"allow"`、`"deny"`、`"ask"` 或 `"defer"`）、`permissionDecisionReason` 和 `updatedInput`。返回 `"defer"` 会结束查询，以便你稍后[恢复它](/docs/en/hooks#defer-a-tool-call-for-later)。对于 `PostToolUse` 钩子，你可以设置 `additionalContext` 以向工具结果追加信息。要在 Claude 看到工具输出之前替换它，请设置 `updatedToolOutput`，它在两个 SDK 中都适用于任何工具。较早的 `updatedMCPToolOutput` 字段仅替换 MCP 工具输出，且已弃用。

返回 `{}` 可允许操作按原样继续。SDK 回调钩子使用与 [Claude Code shell 命令钩子](/docs/en/hooks#json-output) 相同的 JSON 输出格式，其中记录了每个字段和特定于事件的选项。有关 SDK 类型定义，请参阅 [TypeScript](/docs/en/agent-sdk/typescript#synchookjsonoutput) 和 [Python](/docs/en/agent-sdk/python#synchookjsonoutput) SDK 参考。

<Note>
  当多个钩子或权限规则同时适用时,`deny` 的优先级高于 `defer`,而后者的优先级又高于 `ask`，其优先级高于 `allow`。如果任何钩子返回 `deny`，则无论其他钩子如何，该操作都会被阻止。
</Note>

#### 异步输出

默认情况下，代理会等待你的钩子返回后再继续执行。如果你的钩子执行的是副作用操作，例如日志记录或发送 webhook，并且不需要影响代理的行为，你可以改为返回异步输出。这会告诉代理立即继续执行，而无需等待钩子完成。在此代码片段中，Python 中的 `send_to_logging_service` 和 TypeScript 中的 `sendToLoggingService` 代表你定义的任何日志函数：

<CodeGroup>
  ```python Python theme={null}
  async def async_hook(input_data, tool_use_id, context):
      # Start a background task, then return immediately
      asyncio.create_task(send_to_logging_service(input_data))
      return {"async_": True, "asyncTimeout": 30000}
  ```

  ```typescript TypeScript theme={null}
  const asyncHook: HookCallback = async (input, toolUseID, { signal }) => {
    // Start a background task, then return immediately
    sendToLoggingService(input).catch(console.error);
    return { async: true, asyncTimeout: 30000 };
  };
  ```
</CodeGroup>

| 字段          | 类型     | 描述                                                                                                    |
| -------------- | -------- | -------------------------------------------------------------------------------------------------------------- |
| `async`        | `true`   | 表示异步模式。代理不再等待，直接继续执行。在 Python 中，使用 `async_` 以避免与保留关键字冲突。 |
| `asyncTimeout` | `number` | 后台操作的可选超时时间（毫秒）                                                  |

<Note>
  异步输出无法阻止、修改或向操作中注入上下文，因为代理已经继续执行了。仅将它们用于日志记录、指标或通知等副作用操作。
</Note>

## 示例

本节中的几个示例仅展示了回调函数。要运行其中一个示例，请在选项的 `hooks` 字段中将该回调注册到匹配的事件下，如[配置钩子](#configure-hooks)所示。

### 修改工具输入

本示例拦截 Write 工具调用, 并重写 `file_path` 参数以在其前面添加 `/sandbox`, 从而将所有文件写入重定向到沙盒目录。回调返回包含修改后路径的 `updatedInput` 以及 `permissionDecision: 'allow'`, 以自动批准重写后的操作:

<CodeGroup>
  ```python Python theme={null}
  async def redirect_to_sandbox(input_data, tool_use_id, context):
      if input_data["hook_event_name"] != "PreToolUse":
          return {}

      if input_data["tool_name"] == "Write":
          original_path = input_data["tool_input"].get("file_path", "")
          return {
              "hookSpecificOutput": {
                  "hookEventName": input_data["hook_event_name"],
                  "permissionDecision": "allow",
                  "updatedInput": {
                      **input_data["tool_input"],
                      "file_path": f"/sandbox{original_path}",
                  },
              }
          }
      return {}
  ```

  ```typescript TypeScript theme={null}
  const redirectToSandbox: HookCallback = async (input, toolUseID, { signal }) => {
    if (input.hook_event_name !== "PreToolUse") return {};

    const preInput = input as PreToolUseHookInput;
    const toolInput = preInput.tool_input as Record<string, unknown>;
    if (preInput.tool_name === "Write") {
      const originalPath = toolInput.file_path as string;
      return {
        hookSpecificOutput: {
          hookEventName: preInput.hook_event_name,
          permissionDecision: "allow",
          updatedInput: {
            ...toolInput,
            file_path: `/sandbox${originalPath}`
          }
        }
      };
    }
    return {};
  };
  ```
</CodeGroup>

<Note>
  使用 `updatedInput` 时, 你还必须包含 `permissionDecision: 'allow'` 以自动批准修改后的输入, 或包含 `permissionDecision: 'ask'` 以将其展示给用户。使用 `'defer'` 时, `updatedInput` 会被忽略。始终返回一个新对象, 而不是修改原始的 `tool_input`。
</Note>

### 添加上下文并阻止工具

此示例阻止对 `/etc` 目录的写入，并向模型和用户解释原因：

* `permissionDecision: 'deny'` 停止工具调用。
* `permissionDecisionReason` 告诉模型原因，使其避免重试。
* `systemMessage` 向用户显示发生的情况。

<CodeGroup>
  ```python Python theme={null}
  async def block_etc_writes(input_data, tool_use_id, context):
      file_path = input_data["tool_input"].get("file_path", "")

      if file_path.startswith("/etc"):
          return {
              # Top-level field: message shown to the user
              "systemMessage": "Remember: system directories like /etc are protected.",
              # hookSpecificOutput: block the operation
              "hookSpecificOutput": {
                  "hookEventName": input_data["hook_event_name"],
                  "permissionDecision": "deny",
                  "permissionDecisionReason": "Writing to /etc is not allowed",
              },
          }
      return {}
  ```

  ```typescript TypeScript theme={null}
  const blockEtcWrites: HookCallback = async (input, toolUseID, { signal }) => {
    const preInput = input as PreToolUseHookInput;
    const toolInput = preInput.tool_input as Record<string, unknown>;
    const filePath = toolInput?.file_path as string;

    if (filePath?.startsWith("/etc")) {
      return {
        // Top-level field: message shown to the user
        systemMessage: "Remember: system directories like /etc are protected.",
        // hookSpecificOutput: block the operation
        hookSpecificOutput: {
          hookEventName: preInput.hook_event_name,
          permissionDecision: "deny",
          permissionDecisionReason: "Writing to /etc is not allowed"
        }
      };
    }
    return {};
  };
  ```
</CodeGroup>

### 自动批准特定工具

默认情况下，代理在使用某些工具前可能会请求权限。此示例通过返回 `permissionDecision: 'allow'` 自动批准只读文件系统工具（Read、Glob、Grep），让它们无需用户确认即可运行，而所有其他工具仍受正常权限检查约束：

<CodeGroup>
  ```python Python theme={null}
  async def auto_approve_read_only(input_data, tool_use_id, context):
      if input_data["hook_event_name"] != "PreToolUse":
          return {}

      read_only_tools = ["Read", "Glob", "Grep"]
      if input_data["tool_name"] in read_only_tools:
          return {
              "hookSpecificOutput": {
                  "hookEventName": input_data["hook_event_name"],
                  "permissionDecision": "allow",
                  "permissionDecisionReason": "Read-only tool auto-approved",
              }
          }
      return {}
  ```

  ```typescript TypeScript theme={null}
  const autoApproveReadOnly: HookCallback = async (input, toolUseID, { signal }) => {
    if (input.hook_event_name !== "PreToolUse") return {};

    const preInput = input as PreToolUseHookInput;
    const readOnlyTools = ["Read", "Glob", "Grep"];
    if (readOnlyTools.includes(preInput.tool_name)) {
      return {
        hookSpecificOutput: {
          hookEventName: preInput.hook_event_name,
          permissionDecision: "allow",
          permissionDecisionReason: "Read-only tool auto-approved"
        }
      };
    }
    return {};
  };
  ```
</CodeGroup>

### 注册多个钩子

当事件触发时，所有匹配的钩子会并行运行。对于权限决策，采用最严格的结果：单个 `deny` 就会阻止工具调用，无论其他钩子返回什么。由于完成顺序是不确定的，请将每个钩子编写为独立运行，而不是依赖另一个钩子先运行。

下面的示例为每次工具调用注册了三个独立的检查：

<CodeGroup>
  ```python Python theme={null}
  options = ClaudeAgentOptions(
      hooks={
          "PreToolUse": [
              HookMatcher(hooks=[authorization_check]),
              HookMatcher(hooks=[input_validator]),
              HookMatcher(hooks=[audit_logger]),
          ]
      }
  )
  ```

  ```typescript TypeScript theme={null}
  const options = {
    hooks: {
      PreToolUse: [
        { hooks: [authorizationCheck] },
        { hooks: [inputValidator] },
        { hooks: [auditLogger] }
      ]
    }
  };
  ```
</CodeGroup>

### 使用多工具匹配器进行过滤

使用多工具匹配器在相关工具之间共享一个回调。此示例注册了三个具有不同作用域的匹配器：

* 以管道符分隔的精确列表（`Write|Edit|NotebookEdit`）仅对文件修改工具触发 `file_security_hook`。
* 正则表达式（`^mcp__`）对任何名称以 `mcp__` 开头的 MCP 工具触发 `mcp_audit_hook`。
* 省略匹配器则对每次工具调用触发 `global_logger`，无论名称如何。

<CodeGroup>
  ```python Python theme={null}
  options = ClaudeAgentOptions(
      hooks={
          "PreToolUse": [
              # Match file modification tools
              HookMatcher(matcher="Write|Edit|NotebookEdit", hooks=[file_security_hook]),
              # Match all MCP tools
              HookMatcher(matcher="^mcp__", hooks=[mcp_audit_hook]),
              # Match everything (no matcher)
              HookMatcher(hooks=[global_logger]),
          ]
      }
  )
  ```

  ```typescript TypeScript theme={null}
  const options = {
    hooks: {
      PreToolUse: [
        // Match file modification tools
        { matcher: "Write|Edit|NotebookEdit", hooks: [fileSecurityHook] },

        // Match all MCP tools
        { matcher: "^mcp__", hooks: [mcpAuditHook] },

        // Match everything (no matcher)
        { hooks: [globalLogger] }
      ]
    }
  };
  ```
</CodeGroup>

### 跟踪子代理活动

使用 `SubagentStop` 钩子来监控子代理何时完成其工作。请参阅 [TypeScript](/docs/en/agent-sdk/typescript#hookinput) 和 [Python](/docs/en/agent-sdk/python#hookinput) SDK 参考中的完整输入类型。此示例在每次子代理完成时记录摘要：

<CodeGroup>
  ```python Python theme={null}
  async def subagent_tracker(input_data, tool_use_id, context):
      # Log subagent details when it finishes
      print(f"[SUBAGENT] Completed: {input_data['agent_id']}")
      print(f"  Transcript: {input_data['agent_transcript_path']}")
      print(f"  Tool use ID: {tool_use_id}")
      print(f"  Stop hook active: {input_data.get('stop_hook_active')}")
      return {}


  options = ClaudeAgentOptions(
      hooks={"SubagentStop": [HookMatcher(hooks=[subagent_tracker])]}
  )
  ```

  ```typescript TypeScript theme={null}
  import { HookCallback, SubagentStopHookInput } from "@anthropic-ai/claude-agent-sdk";

  const subagentTracker: HookCallback = async (input, toolUseID, { signal }) => {
    // Cast to SubagentStopHookInput to access subagent-specific fields
    const subInput = input as SubagentStopHookInput;

    // Log subagent details when it finishes
    console.log(`[SUBAGENT] Completed: ${subInput.agent_id}`);
    console.log(`  Transcript: ${subInput.agent_transcript_path}`);
    console.log(`  Tool use ID: ${toolUseID}`);
    console.log(`  Stop hook active: ${subInput.stop_hook_active}`);
    return {};
  };

  const options = {
    hooks: {
      SubagentStop: [{ hooks: [subagentTracker] }]
    }
  };
  ```
</CodeGroup>

### 从钩子中发起 HTTP 请求

钩子可以执行异步操作，比如 HTTP 请求。请在钩子内部捕获错误，而不是让它们向外传播，因为未处理的异常可能会中断代理。

这个示例在每个工具完成后发送一个 webhook，记录哪个工具运行了以及运行时间。钩子会捕获错误，因此失败的 webhook 不会中断代理：

<CodeGroup>
  ```python Python theme={null}
  import asyncio
  import json
  import urllib.request
  from datetime import datetime


  def _send_webhook(tool_name):
      """Synchronous helper that POSTs tool usage data to an external webhook."""
      data = json.dumps(
          {
              "tool": tool_name,
              "timestamp": datetime.now().isoformat(),
          }
      ).encode()
      req = urllib.request.Request(
          "https://api.example.com/webhook",
          data=data,
          headers={"Content-Type": "application/json"},
          method="POST",
      )
      urllib.request.urlopen(req)


  async def webhook_notifier(input_data, tool_use_id, context):
      # Only fire after a tool completes (PostToolUse), not before
      if input_data["hook_event_name"] != "PostToolUse":
          return {}

      try:
          # Run the blocking HTTP call in a thread to avoid blocking the event loop
          await asyncio.to_thread(_send_webhook, input_data["tool_name"])
      except Exception as e:
          # Log the error but don't raise. A failed webhook shouldn't stop the agent
          print(f"Webhook request failed: {e}")

      return {}
  ```

  ```typescript TypeScript theme={null}
  import { query, HookCallback, PostToolUseHookInput } from "@anthropic-ai/claude-agent-sdk";

  const webhookNotifier: HookCallback = async (input, toolUseID, { signal }) => {
    // Only fire after a tool completes (PostToolUse), not before
    if (input.hook_event_name !== "PostToolUse") return {};

    try {
      await fetch("https://api.example.com/webhook", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tool: (input as PostToolUseHookInput).tool_name,
          timestamp: new Date().toISOString()
        }),
        // Pass signal so the request cancels if the hook times out
        signal
      });
    } catch (error) {
      // Handle cancellation separately from other errors
      if (error instanceof Error && error.name === "AbortError") {
        console.log("Webhook request cancelled");
      }
      // Don't re-throw. A failed webhook shouldn't stop the agent
    }

    return {};
  };

  // Register as a PostToolUse hook
  for await (const message of query({
    prompt: "Refactor the auth module",
    options: {
      hooks: {
        PostToolUse: [{ hooks: [webhookNotifier] }]
      }
    }
  })) {
    console.log(message);
  }
  ```
</CodeGroup>

### 将通知转发到 Slack

使用 `Notification` 钩子接收来自代理的系统通知,并将其转发到外部服务。通知会因以下事件类型触发:

* `permission_prompt` 当 Claude 需要权限时
* `idle_prompt` 当 Claude 等待输入时
* `auth_success` 当身份验证完成时
* `elicitation_dialog`、`elicitation_complete` 和 `elicitation_response` 用于用户提示引导流程

每条通知都包含一个带有人类可读描述的 `message` 字段,以及一个可选的 `title`。

此示例将每条通知转发到 Slack 频道。它需要一个 [Slack 传入 webhook URL](https://docs.slack.dev/messaging/sending-messages-using-incoming-webhooks/),你可以通过向 Slack 工作区添加应用并启用传入 webhook 来创建它:

<CodeGroup>
  ```python Python theme={null}
  import asyncio
  import json
  import urllib.request

  from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, HookMatcher


  def _send_slack_notification(message):
      """Synchronous helper that sends a message to Slack via incoming webhook."""
      data = json.dumps({"text": f"Agent status: {message}"}).encode()
      req = urllib.request.Request(
          "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
          data=data,
          headers={"Content-Type": "application/json"},
          method="POST",
      )
      urllib.request.urlopen(req)


  async def notification_handler(input_data, tool_use_id, context):
      try:
          # Run the blocking HTTP call in a thread to avoid blocking the event loop
          await asyncio.to_thread(_send_slack_notification, input_data.get("message", ""))
      except Exception as e:
          print(f"Failed to send notification: {e}")

      # Return empty object. Notification hooks don't modify agent behavior
      return {}


  async def main():
      options = ClaudeAgentOptions(
          hooks={
              # Register the hook for Notification events (no matcher needed)
              "Notification": [HookMatcher(hooks=[notification_handler])],
          },
      )

      async with ClaudeSDKClient(options=options) as client:
          await client.query("Analyze this codebase")
          async for message in client.receive_response():
              print(message)


  asyncio.run(main())
  ```

  ```typescript TypeScript theme={null}
  import { query, HookCallback, NotificationHookInput } from "@anthropic-ai/claude-agent-sdk";

  // Define a hook callback that sends notifications to Slack
  const notificationHandler: HookCallback = async (input, toolUseID, { signal }) => {
    // Cast to NotificationHookInput to access the message field
    const notification = input as NotificationHookInput;

    try {
      // POST the notification message to a Slack incoming webhook
      await fetch("https://hooks.slack.com/services/YOUR/WEBHOOK/URL", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: `Agent status: ${notification.message}`
        }),
        // Pass signal so the request cancels if the hook times out
        signal
      });
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") {
        console.log("Notification cancelled");
      } else {
        console.error("Failed to send notification:", error);
      }
    }

    // Return empty object. Notification hooks don't modify agent behavior
    return {};
  };

  // Register the hook for Notification events (no matcher needed)
  for await (const message of query({
    prompt: "Analyze this codebase",
    options: {
      hooks: {
        Notification: [{ hooks: [notificationHandler] }]
      }
    }
  })) {
    console.log(message);
  }
  ```
</CodeGroup>

## 修复常见问题

### 钩子未触发

* 确认钩子事件名称正确且区分大小写（`PreToolUse`，而非 `preToolUse`）
* 检查你的匹配器模式是否与工具名称完全一致
* 确保钩子位于 `options.hooks` 中正确的事件类型下
* 对于支持匹配器的非工具钩子（如 `Notification` 和 `SubagentStop`），匹配器匹配的是不同的字段，而 `Stop` 完全忽略匹配器（参见 [匹配器模式](/docs/en/hooks#matcher-patterns)）
* 当代理达到 [`max_turns`](/docs/en/agent-sdk/python#claudeagentoptions) 限制时，钩子可能不会触发，因为会话在钩子执行之前就已结束

### 匹配器未按预期过滤

匹配器只匹配工具名称，不匹配文件路径或其他参数。要按文件路径过滤，请在钩子内部检查 `tool_input.file_path`：

```typescript theme={null}
const myHook: HookCallback = async (input, toolUseID, { signal }) => {
  const preInput = input as PreToolUseHookInput;
  const toolInput = preInput.tool_input as Record<string, unknown>;
  const filePath = toolInput?.file_path as string;
  if (!filePath?.endsWith(".md")) return {}; // Skip non-markdown files
  // Process markdown files...
  return {};
};
```

### 钩子超时

* 在 `HookMatcher` 配置中增大 `timeout` 值
* 使用第三个回调参数中的 `AbortSignal`，在 TypeScript 中优雅地处理取消

{/* min-version: 2.1.208 */}超过超时的 `UserPromptSubmit` 或 [`UserPromptExpansion`](/docs/en/hooks#userpromptexpansion) 回调会以超时消息阻止该提示，但会话会继续。在回调挂起时中断查询会取消挂起的工具调用。在 v2.1.208 之前，这些事件上的回调超时会使查询以 `error_during_execution` 结束，并且在挂起的 `PreToolUse` 回调期间中断可能会让工具调用继续执行。

{/* min-version: 2.1.210 */}超出超时时间的 `PreToolUse` 回调会阻塞工具调用，Claude 会收到一个指明超时的错误结果。如果另一个 `PreToolUse` 钩子返回了明确的拒绝，Claude 会收到该拒绝结果。在 v2.1.210 之前，Claude Code 会将超时报告给 Claude，就好像用户拒绝了工具调用一样，因此无人值守的会话会停止并等待输入。

### 工具被意外阻止

* 检查所有 `PreToolUse` 钩子的 `permissionDecision: 'deny'` 返回值
* 为你的钩子添加日志，查看它们返回的 `permissionDecisionReason` 内容
* 确认匹配器模式不会过于宽泛：空匹配器会匹配所有工具

### 修改后的输入未生效

* 确保 `updatedInput` 位于 `hookSpecificOutput` 内部，而不是顶层：

  ```typescript theme={null}
  return {
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "allow",
      updatedInput: { command: "new command" }
    }
  };
  ```

* 返回 `permissionDecision: 'allow'` 以自动批准修改后的输入，或返回 `'ask'` 以将其展示给用户审批

* 在 `hookSpecificOutput` 中包含 `hookEventName`，以标识该输出对应的钩子类型

### Python 中不可用的会话钩子

`SessionStart` 和 `SessionEnd` 可以在 TypeScript 中注册为 SDK 回调钩子,但在 Python SDK 中不可用,因为它的 `HookEvent` 类型省略了它们。在 Python 中,它们只能作为[shell 命令钩子](/docs/en/hooks#hook-events)使用,这些钩子定义在诸如 `.claude/settings.json` 之类的设置文件中。要从 SDK 应用程序加载 shell 命令钩子,请使用 [`setting_sources`](/docs/en/agent-sdk/python#settingsource) 或 [`settingSources`](/docs/en/agent-sdk/typescript#settingsource) 包含相应的设置源:

<CodeGroup>
  ```python Python theme={null}
  options = ClaudeAgentOptions(
      setting_sources=["project"],  # Loads .claude/settings.json including hooks
  )
  ```

  ```typescript TypeScript theme={null}
  const options = {
    settingSources: ["project"] // Loads .claude/settings.json including hooks
  };
  ```
</CodeGroup>

如果要改为以 Python SDK 回调的方式运行初始化逻辑,请将来自 `client.receive_response()` 的第一条消息作为触发条件。

### 子代理权限提示倍增

当生成多个子代理时，每个子代理都可能单独请求权限。子代理不会自动继承父代理的权限。为避免重复的提示，请使用 `PreToolUse` 钩子来自动批准特定工具，或配置适用于子代理会话的权限规则。

### 子代理导致的递归钩子循环

一个生成子代理的 `UserPromptSubmit` 钩子，如果这些子代理又触发了相同的钩子，就可能造成无限循环。为防止这种情况：

* 在生成之前，检查钩子输入中是否有子代理指示标记
* 使用共享变量或会话状态来追踪你是否已经处于子代理内部
* 将钩子的作用域限定为仅对顶级代理会话运行

### systemMessage 未出现在输出中

`systemMessage` 字段是向用户显示消息，而不是向模型显示。默认情况下，SDK 仅在 `SessionStart` 和 `Setup` 钩子时才会在消息流中呈现钩子输出，因此来自任何其他钩子事件的消息不会出现，除非你设置 `includeHookEvents`（Python 中为 `include_hook_events`）。如果要向模型传递上下文，请返回 [`additionalContext`](/docs/en/hooks#add-context-for-claude)。

如果你需要可靠地向应用程序呈现钩子决策，请单独记录它们或使用专用的输出通道。

## 相关资源

* [Claude Code 钩子参考](/docs/en/hooks)：完整的 JSON 输入/输出模式、事件文档和匹配器模式
* [Claude Code 钩子指南](/docs/en/hooks-guide)：shell 命令钩子示例和演练
* [TypeScript SDK 参考](/docs/en/agent-sdk/typescript)：钩子类型、输入/输出定义和配置选项
* [Python SDK 参考](/docs/en/agent-sdk/python)：钩子类型、输入/输出定义和配置选项
* [权限](/docs/en/agent-sdk/permissions)：控制你的代理可以做什么
* [自定义工具](/docs/en/agent-sdk/custom-tools)：构建工具以扩展代理能力

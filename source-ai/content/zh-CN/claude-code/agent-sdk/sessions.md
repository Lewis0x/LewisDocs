---
title: 使用会话
source_id: claude-code/agent-sdk/sessions
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/agent-sdk/sessions
owner: Anthropic
content_sha256: 89e991b777429220e0eb6ef74656c4b89c6303eaf81b78afe4e8066d4f982e87
translation_of: claude-code/agent-sdk/sessions
translation_source: official
translation_url: https://code.claude.com/docs/zh-CN/agent-sdk/sessions
localization_sha256: 3e97cb004384bf078372b296b7ccdd0d911749845e21dc288d17d528afb45b69
---
本页采用内容所有者发布的官方简体中文版本，并与本站对应英文版本进行结构校验。

[官方中文来源](https://code.claude.com/docs/zh-CN/agent-sdk/sessions)

内容所有者: Anthropic

> ## Documentation Index
> Fetch the complete documentation index at: https://code.claude.com/docs/llms.txt
> Use this file to discover all available pages before exploring further.

# 使用会话

> 会话如何保持代理对话历史记录，以及何时使用 continue、resume 和 fork 返回到之前的运行。

会话是 SDK 在代理工作时积累的对话历史记录。它包含您的提示、代理进行的每个工具调用、每个工具结果和每个响应。SDK 会自动将其写入磁盘，以便您稍后可以返回到它。

返回到会话意味着代理具有之前的完整上下文：它已经读取的文件、它已经执行的分析、它已经做出的决定。您可以提出后续问题、从中断中恢复或分支以尝试不同的方法。

<Note>
  会话保持**对话**，而不是文件系统。要快照和还原代理所做的文件更改，请使用[文件检查点](/docs/zh-CN/agent-sdk/file-checkpointing)。
</Note>

本指南涵盖如何为您的应用选择正确的方法、自动跟踪会话的 SDK 接口、如何捕获会话 ID 以及手动使用 `resume` 和 `fork` 的方法，以及关于在主机之间恢复会话需要了解的内容。

<h2 id="choose-an-approach">
  选择一种方法
</h2>

您需要多少会话处理取决于应用的形状。当您发送应该共享上下文的多个提示时，会话管理就会发挥作用。在单个 `query()` 调用中，代理已经根据需要进行了尽可能多的轮次，权限提示和 `AskUserQuestion` 是[在循环中处理的](/docs/zh-CN/agent-sdk/user-input)（它们不会结束调用）。

| 您正在构建的内容                        | 使用什么                                                                                                          |
| :------------------------------ | :------------------------------------------------------------------------------------------------------------ |
| 一次性任务：单个提示，无后续                  | 无需额外操作。一个 `query()` 调用可以处理它。                                                                                  |
| 在一个进程中进行多轮聊天                    | [`ClaudeSDKClient`（Python）或 `continue: true`（TypeScript）](#automatic-session-management)。SDK 为您跟踪会话，无需 ID 处理。 |
| 在进程重启后从中断处继续                    | `continue_conversation=True`（Python）/ `continue: true`（TypeScript）。恢复目录中最近的会话，无需 ID。                          |
| 恢复特定的过去会话（不是最近的）                | 捕获会话 ID 并将其传递给 `resume`。                                                                                      |
| 尝试替代方法而不丢失原始方法                  | Fork 会话。                                                                                                      |
| 无状态任务，不希望任何内容写入磁盘（仅 TypeScript） | 设置 [`persistSession: false`](/docs/zh-CN/agent-sdk/typescript#options)。会话仅在调用期间存在于内存中。Python 始终保持到磁盘。              |

<h3 id="continue-resume-and-fork">
  Continue、resume 和 fork
</h3>

Continue、resume 和 fork 是您在 `query()` 上设置的选项字段（Python 中的 [`ClaudeAgentOptions`](/docs/zh-CN/agent-sdk/python#claudeagentoptions)，TypeScript 中的 [`Options`](/docs/zh-CN/agent-sdk/typescript#options)）。

**Continue** 和 **resume** 都会选择现有会话并添加到其中。区别在于它们如何找到该会话：

* **Continue** 在当前目录中查找最近的会话。您无需跟踪任何内容。当您的应用一次运行一个对话时效果很好。
* **Resume** 采用特定的会话 ID。您跟踪 ID。当您有多个会话（例如，多用户应用中每个用户一个）或想要返回到不是最近的会话时需要。

**Fork** 不同：它创建一个新会话，从原始会话历史记录的副本开始。原始会话保持不变。使用 fork 尝试不同的方向，同时保持返回的选项。

<h2 id="automatic-session-management">
  自动会话管理
</h2>

两个 SDK 都提供了一个接口，可以跨调用为您跟踪会话状态，因此您无需手动传递 ID。将这些用于单个进程中的多轮对话。

<h3 id="python-claudesdkclient">
  Python：`ClaudeSDKClient`
</h3>

[`ClaudeSDKClient`](/docs/zh-CN/agent-sdk/python#claudesdkclient) 在内部处理会话 ID。每次调用 `client.query()` 都会自动继续同一会话。调用 [`client.receive_response()`](/docs/zh-CN/agent-sdk/python#claudesdkclient) 以迭代当前查询的消息。使用客户端作为异步上下文管理器，以便为您处理连接设置和拆卸，或手动调用 `connect()` 和 `disconnect()`。

此示例针对同一 `client` 运行两个查询。第一个要求代理分析一个模块；第二个要求它重构该模块。因为两个调用都通过同一客户端实例进行，第二个查询具有来自第一个查询的完整上下文，无需任何显式 `resume` 或会话 ID：

```python Python theme={null}
import asyncio
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    ResultMessage,
    TextBlock,
)


def print_response(message):
    """Print only the human-readable parts of a message."""
    if isinstance(message, AssistantMessage):
        for block in message.content:
            if isinstance(block, TextBlock):
                print(block.text)
    elif isinstance(message, ResultMessage):
        cost = (
            f"${message.total_cost_usd:.4f}"
            if message.total_cost_usd is not None
            else "N/A"
        )
        print(f"[done: {message.subtype}, cost: {cost}]")


async def main():
    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Edit", "Glob", "Grep"],
    )

    async with ClaudeSDKClient(options=options) as client:
        # First query: client captures the session ID internally
        await client.query("Analyze the auth module")
        async for message in client.receive_response():
            print_response(message)

        # Second query: automatically continues the same session
        await client.query("Now refactor it to use JWT")
        async for message in client.receive_response():
            print_response(message)


asyncio.run(main())
```

有关何时使用 `ClaudeSDKClient` 与独立 `query()` 函数的详细信息，请参阅 [Python SDK 参考](/docs/zh-CN/agent-sdk/python#choosing-between-query-and-claudesdkclient)。

<h3 id="typescript-continue-true">
  TypeScript：`continue: true`
</h3>

TypeScript SDK 没有像 Python 的 `ClaudeSDKClient` 那样的会话保持客户端对象。相反，在每个后续 `query()` 调用上传递 `continue: true`，SDK 会在当前目录中选择最近的会话。无需 ID 跟踪。

此示例进行两个单独的 `query()` 调用。第一个创建一个新会话；第二个设置 `continue: true`，这告诉 SDK 在磁盘上查找并恢复最近的会话。代理具有来自第一个调用的完整上下文：

```typescript TypeScript theme={null}
import { query } from "@anthropic-ai/claude-agent-sdk";

// First query: creates a new session
for await (const message of query({
  prompt: "Analyze the auth module",
  options: { allowedTools: ["Read", "Glob", "Grep"] }
})) {
  if (message.type === "result" && message.subtype === "success") {
    console.log(message.result);
  }
}

// Second query: continue: true resumes the most recent session
for await (const message of query({
  prompt: "Now refactor it to use JWT",
  options: {
    continue: true,
    allowedTools: ["Read", "Edit", "Write", "Glob", "Grep"]
  }
})) {
  if (message.type === "result" && message.subtype === "success") {
    console.log(message.result);
  }
}
```

<Note>
  实验性的 [V2 会话 API](/docs/zh-CN/agent-sdk/typescript-v2-preview)（提供了带有 `send` / `stream` 模式的 `createSession()`）已在 TypeScript Agent SDK 0.3.142 中移除。使用 `query()` 函数和本页面上描述的会话选项。
</Note>

<h2 id="use-session-options-with-query">
  将会话选项与 `query()` 一起使用
</h2>

<h3 id="capture-the-session-id">
  捕获会话 ID
</h3>

Resume 和 fork 需要会话 ID。从结果消息上的 `session_id` 字段读取它（Python 中的 [`ResultMessage`](/docs/zh-CN/agent-sdk/python#resultmessage)，TypeScript 中的 [`SDKResultMessage`](/docs/zh-CN/agent-sdk/typescript#sdkresultmessage)），该字段存在于每个结果上，无论成功还是错误。在 TypeScript 中，ID 也可以作为初始化 `SystemMessage` 上的直接字段更早获得；在 Python 中，它嵌套在 `SystemMessage.data` 内。

<CodeGroup>
  ```python Python theme={null}
  import asyncio
  from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage


  async def main():
      session_id = None

      async for message in query(
          prompt="Analyze the auth module and suggest improvements",
          options=ClaudeAgentOptions(
              allowed_tools=["Read", "Glob", "Grep"],
          ),
      ):
          if isinstance(message, ResultMessage):
              session_id = message.session_id
              if message.subtype == "success":
                  print(message.result)

      print(f"Session ID: {session_id}")
      return session_id


  session_id = asyncio.run(main())
  ```

  ```typescript TypeScript theme={null}
  import { query } from "@anthropic-ai/claude-agent-sdk";

  let sessionId: string | undefined;

  for await (const message of query({
    prompt: "Analyze the auth module and suggest improvements",
    options: { allowedTools: ["Read", "Glob", "Grep"] }
  })) {
    if (message.type === "result") {
      sessionId = message.session_id;
      if (message.subtype === "success") {
        console.log(message.result);
      }
    }
  }

  console.log(`Session ID: ${sessionId}`);
  ```
</CodeGroup>

<h3 id="resume-by-id">
  按 ID 恢复
</h3>

将会话 ID 传递给 `resume` 以返回到该特定会话。代理从会话中断的任何地方继续，具有完整的上下文。恢复的常见原因：

* **跟进已完成的任务。** 代理已经分析了某些内容；现在您希望它根据该分析采取行动，而无需重新读取文件。
* **从限制中恢复。** 第一次运行以 `error_max_turns` 或 `error_max_budget_usd` 结束（请参阅[处理结果](/docs/zh-CN/agent-sdk/agent-loop#handle-the-result)）；使用更高的限制恢复。
* **重启您的进程。** 您在关闭前捕获了 ID，并希望恢复对话。

此示例使用后续提示恢复[捕获会话 ID](#capture-the-session-id) 中的会话。因为您正在恢复，代理已经在上下文中具有先前的分析：

<CodeGroup>
  ```python Python theme={null}
  # Earlier session analyzed the code; now build on that analysis
  async for message in query(
      prompt="Now implement the refactoring you suggested",
      options=ClaudeAgentOptions(
          resume=session_id,
          allowed_tools=["Read", "Edit", "Write", "Glob", "Grep"],
      ),
  ):
      if isinstance(message, ResultMessage) and message.subtype == "success":
          print(message.result)
  ```

  ```typescript TypeScript theme={null}
  import { query } from "@anthropic-ai/claude-agent-sdk";

  const sessionId = "..."; // The ID you captured in the previous example

  // Earlier session analyzed the code; now build on that analysis
  for await (const message of query({
    prompt: "Now implement the refactoring you suggested",
    options: {
      resume: sessionId,
      allowedTools: ["Read", "Edit", "Write", "Glob", "Grep"]
    }
  })) {
    if (message.type === "result" && message.subtype === "success") {
      console.log(message.result);
    }
  }
  ```
</CodeGroup>

您应该看到一个基于早期分析而构建的响应，而不是从头开始。这证实了代理恢复了会话，其先前的上下文保持完整。

<Tip>
  如果 `resume` 调用返回新会话而不是预期的历史记录，最常见的原因是不匹配的 `cwd`。会话存储在 `~/.claude/projects/<encoded-cwd>/*.jsonl` 下，或者如果您设置了 `CLAUDE_CONFIG_DIR` 环境变量，则存储在 `$CLAUDE_CONFIG_DIR/projects/<encoded-cwd>/*.jsonl` 下，其中 `<encoded-cwd>` 是绝对工作目录，每个非字母数字字符都被替换为 `-`（所以 `/Users/me/proj` 变成 `-Users-me-proj`）。如果您的 resume 调用从不同的目录运行，SDK 会在错误的位置查找。会话文件也需要存在于当前机器上。
</Tip>

要在机器之间或在无服务器环境中恢复会话，请使用 [`SessionStore` 适配器](/docs/zh-CN/agent-sdk/session-storage)将记录镜像到共享存储。

<h3 id="fork-to-explore-alternatives">
  Fork 以探索替代方案
</h3>

Forking 创建一个新会话，从原始会话历史记录的副本开始，但从该点开始分支。fork 获得自己的会话 ID；原始的 ID 和历史记录保持不变。您最终会得到两个独立的会话，可以分别恢复。

<Note>
  Forking 分支对话历史记录，而不是文件系统。如果 forked 代理编辑文件，这些更改是真实的，对在同一目录中工作的任何会话都可见。要分支和还原文件更改，请使用[文件检查点](/docs/zh-CN/agent-sdk/file-checkpointing)。
</Note>

此示例基于[捕获会话 ID](#capture-the-session-id)：您已经在 `session_id` 中分析了一个身份验证模块，并希望探索 OAuth2 而不丢失 JWT 焦点线程。第一个块 forks 会话并捕获 fork 的 ID（`forked_id`）；第二个块恢复原始 `session_id` 以继续沿着 JWT 路径。您现在有两个会话 ID 指向两个单独的历史记录：

<CodeGroup>
  ```python Python theme={null}
  # Fork: branch from session_id into a new session
  forked_id = None
  async for message in query(
      prompt="Instead of JWT, outline how OAuth2 would work for the auth module",
      options=ClaudeAgentOptions(
          resume=session_id,
          fork_session=True,
          max_turns=5,
      ),
  ):
      if isinstance(message, ResultMessage):
          forked_id = message.session_id  # The fork's ID, distinct from session_id
          if message.subtype == "success":
              print(message.result)

  print(f"Forked session: {forked_id}")

  # Original session is untouched; resuming it continues the JWT thread
  async for message in query(
      prompt="Continue with the JWT approach",
      options=ClaudeAgentOptions(resume=session_id),
  ):
      if isinstance(message, ResultMessage) and message.subtype == "success":
          print(message.result)
  ```

  ```typescript TypeScript theme={null}
  import { query } from "@anthropic-ai/claude-agent-sdk";

  const sessionId = "..."; // The ID you captured in the previous example

  // Fork: branch from sessionId into a new session
  let forkedId: string | undefined;

  for await (const message of query({
    prompt: "Instead of JWT, outline how OAuth2 would work for the auth module",
    options: {
      resume: sessionId,
      forkSession: true,
      maxTurns: 5
    }
  })) {
    if (message.type === "system" && message.subtype === "init") {
      forkedId = message.session_id; // The fork's ID, distinct from sessionId
    }
    if (message.type === "result" && message.subtype === "success") {
      console.log(message.result);
    }
  }

  console.log(`Forked session: ${forkedId}`);

  // Original session is untouched; resuming it continues the JWT thread
  for await (const message of query({
    prompt: "Continue with the JWT approach",
    options: { resume: sessionId }
  })) {
    if (message.type === "result" && message.subtype === "success") {
      console.log(message.result);
    }
  }
  ```
</CodeGroup>

您应该看到 `forkedId` 与原始会话 ID 不同。恢复原始会话仍然继续 JWT 线程，这证实了 fork 没有修改原始历史记录。

<h2 id="resume-across-hosts">
  跨主机恢复
</h2>

会话文件是创建它们的机器的本地文件。要在不同的主机上恢复会话（CI 工作者、临时容器、无服务器），您有两个选项：

* **移动会话文件。** 从第一次运行中保持 `~/.claude/projects/<encoded-cwd>/<session-id>.jsonl`，并在调用 `resume` 之前将其恢复到新主机上的相同路径。`cwd` 必须匹配。
* **不依赖会话恢复。** 捕获您需要的结果（分析输出、决定、文件差异）作为应用状态，并将其传递到新会话的提示中。这通常比在周围运送记录文件更强大。

两个 SDK 都公开了用于枚举磁盘上的会话和读取其消息的函数：TypeScript 中的 [`listSessions()`](/docs/zh-CN/agent-sdk/typescript#listsessions) 和 [`getSessionMessages()`](/docs/zh-CN/agent-sdk/typescript#getsessionmessages)，Python 中的 [`list_sessions()`](/docs/zh-CN/agent-sdk/python#list_sessions) 和 [`get_session_messages()`](/docs/zh-CN/agent-sdk/python#get_session_messages)。使用它们来构建自定义会话选择器、清理逻辑或记录查看器。

两个 SDK 也公开了用于查找和改变单个会话的函数：Python 中的 [`get_session_info()`](/docs/zh-CN/agent-sdk/python#get_session_info)、[`rename_session()`](/docs/zh-CN/agent-sdk/python#rename_session) 和 [`tag_session()`](/docs/zh-CN/agent-sdk/python#tag_session)，以及 TypeScript 中的 [`getSessionInfo()`](/docs/zh-CN/agent-sdk/typescript#getsessioninfo)、[`renameSession()`](/docs/zh-CN/agent-sdk/typescript#renamesession) 和 [`tagSession()`](/docs/zh-CN/agent-sdk/typescript#tagsession)。使用它们按标签组织会话或给它们人类可读的标题。

<h2 id="related-resources">
  相关资源
</h2>

* [代理循环如何工作](/docs/zh-CN/agent-sdk/agent-loop)：了解会话中的轮次、消息和上下文累积
* [文件检查点](/docs/zh-CN/agent-sdk/file-checkpointing)：快照和还原代理在会话中所做的文件更改
* [Python `ClaudeAgentOptions`](/docs/zh-CN/agent-sdk/python#claudeagentoptions)：Python 的完整会话选项参考
* [TypeScript `Options`](/docs/zh-CN/agent-sdk/typescript#options)：TypeScript 的完整会话选项参考

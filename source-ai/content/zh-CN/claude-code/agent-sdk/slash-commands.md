---
title: SDK 中的斜杠命令
source_id: claude-code/agent-sdk/slash-commands
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/agent-sdk/slash-commands
owner: Anthropic
content_sha256: 4f4392bd7ea22c63173b9183261f0cecab0323fe5e0bfddd17af3fe926b1ecb9
translation_of: claude-code/agent-sdk/slash-commands
translation_model: k3
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/agent-sdk/slash-commands)

Content owner: Anthropic

> ## 文档索引
> 在此获取完整的文档索引：https://code.claude.com/docs/llms.txt
> 在进一步探索之前，请使用此文件来发现所有可用的页面。

# SDK 中的斜杠命令

> 了解如何使用斜杠命令通过 SDK 控制 Claude Code 会话

斜杠命令提供了一种使用以 `/` 开头的特殊命令来控制 Claude Code 会话的方式。这些命令可以通过 SDK 发送，以执行诸如压缩上下文、列出上下文使用情况或调用自定义命令等操作。只有无需交互式终端即可运行的命令才能通过 SDK 调度；`system/init` 消息会列出你的会话中可用的命令。

## 发现可用的斜杠命令

Claude Agent SDK 在系统初始化消息中提供了有关可用斜杠命令的信息。在会话开始时访问此信息：

<CodeGroup>
  ```typescript TypeScript theme={null}
  import { query } from "@anthropic-ai/claude-agent-sdk";

  for await (const message of query({
    prompt: "Hello Claude",
    options: { maxTurns: 1 }
  })) {
    if (message.type === "system" && message.subtype === "init") {
      console.log("Available slash commands:", message.slash_commands);
      // Includes built-in commands plus bundled skills, for example:
      // ["clear", "compact", "context", "usage", "code-review", "verify", ...]
    }
  }
  ```

  ```python Python theme={null}
  import asyncio
  from claude_agent_sdk import query, ClaudeAgentOptions, SystemMessage


  async def main():
      async for message in query(prompt="Hello Claude", options=ClaudeAgentOptions(max_turns=1)):
          if isinstance(message, SystemMessage) and message.subtype == "init":
              print("Available slash commands:", message.data["slash_commands"])
              # Includes built-in commands plus bundled skills, for example:
              # ["clear", "compact", "context", "usage", "code-review", "verify", ...]


  asyncio.run(main())
  ```
</CodeGroup>

## 发送斜杠命令

在提示字符串中包含斜杠命令即可发送它们,就像普通文本一样。作用于对话历史的命令(例如 `/compact`)需要有先前的消息才能工作,因此下面的示例先提出一个问题,然后将命令作为同一会话的后续内容发送:

<CodeGroup>
  ```typescript TypeScript theme={null}
  import { query } from "@anthropic-ai/claude-agent-sdk";

  // Build up conversation history first
  try {
    for await (const message of query({
      prompt: "What does the README in this directory cover?",
      options: { maxTurns: 2 }
    })) {
      if (message.type === "result" && message.subtype === "success") {
        console.log(message.result);
      }
    }
  } catch (error) {
    // A single-shot query() throws after yielding an error result,
    // so the follow-up query below still runs.
    console.error(`Session ended with an error: ${error}`);
  }

  // Send a slash command as a follow-up to the same conversation
  for await (const message of query({
    prompt: "/compact",
    options: { continue: true, maxTurns: 1 }
  })) {
    if (message.type === "result") {
      console.log("Command executed, result subtype:", message.subtype);
      // Example output: Command executed, result subtype: success
    }
  }
  ```

  ```python Python theme={null}
  import asyncio
  from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage


  async def main():
      # Build up conversation history first
      try:
          async for message in query(
              prompt="What does the README in this directory cover?",
              options=ClaudeAgentOptions(max_turns=2),
          ):
              if isinstance(message, ResultMessage) and message.subtype == "success":
                  print(message.result)
      except Exception as error:
          # A single-shot query() raises after yielding an error result,
          # so the follow-up query below still runs.
          print(f"Session ended with an error: {error}")

      # Send a slash command as a follow-up to the same conversation
      async for message in query(
          prompt="/compact",
          options=ClaudeAgentOptions(continue_conversation=True, max_turns=1),
      ):
          if isinstance(message, ResultMessage):
              print("Command executed, result subtype:", message.subtype)
              # Example output: Command executed, result subtype: success


  asyncio.run(main())
  ```
</CodeGroup>

<Note>
  查询可能以错误结果结束,例如在工作完成之前就达到了 `maxTurns` / `max_turns` 限制。此时最终结果消息带有 `is_error: true`,并且其错误子类型为 `error_max_turns` 而不是 `success`。

  在产生该最终结果消息之后,SDK 会抛出错误,因为 CLI 进程以非零代码退出。

  如果你的命令可能触及该限制,请在 TypeScript 中用 `try`/`catch` 包裹循环,或在 Python 中用 `try`/`except` 包裹,如 [单条消息输入](/docs/en/agent-sdk/streaming-vs-single-mode#single-message-input) 所示,或者将 `maxTurns` 设置得足够高以便工作能够完成。在 Python 中,捕获 `Exception`:SDK 会将错误结果作为普通的 `Exception` 呈现。
</Note>

## 常用斜杠命令

### `/compact` - 压缩对话历史

`/compact` 命令通过总结较早的消息来减小对话历史的大小，同时保留重要的上下文。压缩需要一个已有对话，其中至少包含两次先前的交流才能进行总结。此示例先进行一段对话，然后压缩它并读取报告结果的 `compact_boundary` 系统消息：

<CodeGroup>
  ```typescript TypeScript theme={null}
  import { query } from "@anthropic-ai/claude-agent-sdk";

  // Compaction needs existing history, so have a conversation first
  try {
    for await (const message of query({
      prompt: "Explain what this project does",
      options: { maxTurns: 2 }
    })) {
      if (message.type === "result" && message.subtype === "success") {
        console.log(message.result);
      }
    }
  } catch (error) {
    // A single-shot query() throws after yielding an error result,
    // so the follow-up query below still runs.
    console.error(`Session ended with an error: ${error}`);
  }

  // Compact the same conversation
  for await (const message of query({
    prompt: "/compact",
    options: { continue: true, maxTurns: 1 }
  })) {
    if (message.type === "system" && message.subtype === "compact_boundary") {
      console.log("Compaction completed");
      console.log("Pre-compaction tokens:", message.compact_metadata.pre_tokens);
      console.log("Trigger:", message.compact_metadata.trigger);
      // Example output:
      // Compaction completed
      // Pre-compaction tokens: 1842
      // Trigger: manual
    }
  }
  ```

  ```python Python theme={null}
  import asyncio
  from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage, SystemMessage


  async def main():
      # Compaction needs existing history, so have a conversation first
      try:
          async for message in query(
              prompt="Explain what this project does",
              options=ClaudeAgentOptions(max_turns=2),
          ):
              if isinstance(message, ResultMessage) and message.subtype == "success":
                  print(message.result)
      except Exception as error:
          # A single-shot query() raises after yielding an error result,
          # so the follow-up query below still runs.
          print(f"Session ended with an error: {error}")

      # Compact the same conversation
      async for message in query(
          prompt="/compact",
          options=ClaudeAgentOptions(continue_conversation=True, max_turns=1),
      ):
          if isinstance(message, SystemMessage) and message.subtype == "compact_boundary":
              print("Compaction completed")
              print("Pre-compaction tokens:", message.data["compact_metadata"]["pre_tokens"])
              print("Trigger:", message.data["compact_metadata"]["trigger"])
              # Example output:
              # Compaction completed
              # Pre-compaction tokens: 1842
              # Trigger: manual


  asyncio.run(main())
  ```
</CodeGroup>

<Note>
  `compact_boundary` 消息仅在压缩实际运行时才会到达。当没有内容可总结时，`/compact` 会报告原因而不是抛出异常：运行仍以 `success` 结果结束，不会发出 `compact_boundary` 消息，并且结果文本会携带该消息，例如在单次简短交流之后的 `Not enough messages to compact.`。全新的一次性 `query()` 调用以空上下文开始，因此请在已有先前轮次的会话中使用此模式，例如在 [流式输入模式](/docs/en/agent-sdk/streaming-vs-single-mode) 中，或在恢复会话时使用。
</Note>

### `/clear` - 重置对话上下文

`/clear` 命令将对话重置为空上下文，因此后续提示将在没有任何先前对话历史的情况下开始。之前的对话仍保留在磁盘上，可以通过将其会话 ID 传递给 [`resume` 选项](/docs/en/agent-sdk/sessions#resume-by-id) 来返回。

这在 [流式输入模式](/docs/en/agent-sdk/streaming-vs-single-mode) 中很有用，在该模式下你通过单个连接发送多个提示。对于一次性的 `query()` 调用，每次调用本身就从空上下文开始，因此发送 `/clear` 没有实际效果；请改为启动一个新的 `query()`。

<Note>
  SDK 中的 `/clear` 需要 Claude Code v2.1.117 或更高版本。在早期版本中，它会从 `slash_commands` 中被省略。
</Note>

## 创建自定义斜杠命令

除了使用内置斜杠命令外，你还可以创建自己的自定义命令，这些命令可通过 SDK 使用。自定义命令定义为特定目录中的 Markdown 文件，类似于子代理的配置方式。

<Note>
  `.claude/commands/` 目录是旧版格式。推荐的格式是 `.claude/skills/<name>/SKILL.md`，它支持相同的斜杠命令调用（`/name`），并支持 Claude 的自主调用。有关当前格式，请参阅 [技能](/docs/en/agent-sdk/skills)。CLI 继续支持这两种格式，下面的示例对于 `.claude/commands/` 仍然准确。
</Note>

### 文件位置

自定义斜杠命令根据其作用域存储在指定的目录中：

* **项目命令**：`.claude/commands/` - 仅在当前项目中可用（旧版；建议使用 `.claude/skills/`）
* **个人命令**：`~/.claude/commands/` - 在你的所有项目中可用（旧版；建议使用 `~/.claude/skills/`）

### 文件格式

每个自定义命令都是一个 Markdown 文件，其中：

* 文件名（不含 `.md` 扩展名）成为命令名称
* 文件内容定义命令的功能
* 可选的 YAML frontmatter 提供配置

#### 基本示例

如果你的项目中不存在 `.claude/commands` 目录，请创建它，然后创建 `.claude/commands/refactor.md`：

```markdown theme={null}
Refactor the selected code to improve readability and maintainability.
Focus on clean code principles and best practices.
```

这将创建 `/refactor` 命令，你可以通过 SDK 使用它。

#### 带 Frontmatter 的示例

创建 `.claude/commands/security-check.md`：

```markdown theme={null}
---
allowed-tools: Read, Grep, Glob
description: Run security vulnerability scan
model: claude-opus-4-8
---

Analyze the codebase for security vulnerabilities including:
- SQL injection risks
- XSS vulnerabilities
- Exposed credentials
- Insecure configurations
```

### 在 SDK 中使用自定义命令

在文件系统中定义后，自定义命令会自动通过 SDK 提供：

<CodeGroup>
  ```typescript TypeScript theme={null}
  import { query } from "@anthropic-ai/claude-agent-sdk";

  // Use a custom command
  try {
    for await (const message of query({
      prompt: "/refactor src/auth/login.ts",
      options: { maxTurns: 3 }
    })) {
      if (message.type === "assistant") {
        console.log("Refactoring suggestions:", message.message);
      }
    }
  } catch (error) {
    // A single-shot query() throws after yielding an error result,
    // so the second query below still runs.
    console.error(`Session ended with an error: ${error}`);
  }

  // Custom commands appear in the slash_commands list
  for await (const message of query({
    prompt: "Hello",
    options: { maxTurns: 1 }
  })) {
    if (message.type === "system" && message.subtype === "init") {
      console.log("Available commands:", message.slash_commands);
      // Includes built-in commands plus bundled skills and your custom commands, for example:
      // ["clear", "compact", "context", "usage", "code-review", "verify", "refactor", "security-check", ...]
    }
  }
  ```

  ```python Python theme={null}
  import asyncio
  from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, SystemMessage


  async def main():
      # Use a custom command
      try:
          async for message in query(
              prompt="/refactor src/auth/login.py", options=ClaudeAgentOptions(max_turns=3)
          ):
              if isinstance(message, AssistantMessage):
                  for block in message.content:
                      if hasattr(block, "text"):
                          print("Refactoring suggestions:", block.text)
      except Exception as error:
          # A single-shot query() raises after yielding an error result,
          # so the second query below still runs.
          print(f"Session ended with an error: {error}")

      # Custom commands appear in the slash_commands list
      async for message in query(prompt="Hello", options=ClaudeAgentOptions(max_turns=1)):
          if isinstance(message, SystemMessage) and message.subtype == "init":
              print("Available commands:", message.data["slash_commands"])
              # Includes built-in commands plus bundled skills and your custom commands, for example:
              # ["clear", "compact", "context", "usage", "code-review", "verify", "refactor", "security-check", ...]


  asyncio.run(main())
  ```
</CodeGroup>

### 高级功能

#### 参数和占位符

自定义命令支持使用占位符的动态参数：

创建 `.claude/commands/fix-issue.md`：

```markdown theme={null}
---
argument-hint: [issue-number] [priority]
description: Fix a GitHub issue
---

Fix issue #$0 with priority $1.
Check the issue description and implement the necessary changes.
```

在 SDK 中使用：

<CodeGroup>
  ```typescript TypeScript theme={null}
  import { query } from "@anthropic-ai/claude-agent-sdk";

  // Pass arguments to custom command
  try {
    for await (const message of query({
      prompt: "/fix-issue 123 high",
      options: { maxTurns: 5 }
    })) {
      // Command will process with $0="123" and $1="high"
      if (message.type === "result" && message.subtype === "success") {
        console.log("Issue fixed:", message.result);
      }
    }
  } catch (err) {
    // The run ends with an error when it reaches the maxTurns limit
    console.error("Session ended with an error:", err);
  }
  ```

  ```python Python theme={null}
  import asyncio
  from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage


  async def main():
      # Pass arguments to custom command
      try:
          async for message in query(prompt="/fix-issue 123 high", options=ClaudeAgentOptions(max_turns=5)):
              # Command will process with $0="123" and $1="high"
              if isinstance(message, ResultMessage):
                  print("Issue fixed:", message.result)
      except Exception as error:
          # The run ends with an error when it reaches the max_turns limit
          print(f"Session ended with an error: {error}")


  asyncio.run(main())
  ```
</CodeGroup>

#### Bash 命令执行

自定义命令可以执行 bash 命令并包含其输出：

创建 `.claude/commands/git-commit.md`：

```markdown theme={null}
---
allowed-tools: Bash(git add *), Bash(git status *), Bash(git commit *)
description: Create a git commit
---

## Context

- Current status: !`git status`
- Current diff: !`git diff HEAD`

## Task

Create a git commit with appropriate message based on the changes.
```

#### 文件引用

使用 `@` 前缀包含文件内容：

创建 `.claude/commands/review-config.md`：

```markdown theme={null}
---
description: Review configuration files
---

Review the following configuration files for issues:
- Package config: @package.json
- TypeScript config: @tsconfig.json
- Environment config: @.env

Check for security issues, outdated dependencies, and misconfigurations.
```

### 使用命名空间组织

将命令组织到子目录中，以获得更好的结构：

```bash theme={null}
.claude/commands/
├── frontend/
│   ├── component.md      # Creates /component (project:frontend)
│   └── style-check.md     # Creates /style-check (project:frontend)
├── backend/
│   ├── api-test.md        # Creates /api-test (project:backend)
│   └── db-migrate.md      # Creates /db-migrate (project:backend)
└── review.md              # Creates /review (project)
```

子目录会出现在命令描述中，但不影响命令名称本身。

### 实用示例

#### 拉取请求审查命令

创建 `.claude/commands/review-pr.md`：

```markdown theme={null}
---
allowed-tools: Read, Grep, Glob, Bash(git diff *)
description: Comprehensive code review
---

## Changed Files

!`git diff --name-only HEAD~1`

## Detailed Changes

!`git diff HEAD~1`

## Review Checklist

Review the above changes for:
1. Code quality and readability
2. Security vulnerabilities
3. Performance implications
4. Test coverage
5. Documentation completeness

Provide specific, actionable feedback organized by priority.
```

<Note>
  Claude Code 包含内置的 `code-review` 和 `verify` 技能。如果你将自定义命令命名为与其中之一相同，例如 `.claude/commands/code-review.md`，你的命令会遮蔽内置技能，并且 `slash_commands` 只列出该名称一次。
</Note>

#### 测试运行器命令

创建 `.claude/commands/test.md`：

```markdown theme={null}
---
allowed-tools: Bash, Read, Edit
argument-hint: [test-pattern]
description: Run tests with optional pattern
---

Run tests matching pattern: $ARGUMENTS

1. Detect the test framework (Jest, pytest, etc.)
2. Run tests with the provided pattern
3. If tests fail, analyze and fix them
4. Re-run to verify fixes
```

通过 SDK 使用这些命令：

<CodeGroup>
  ```typescript TypeScript theme={null}
  import { query } from "@anthropic-ai/claude-agent-sdk";

  // Run code review
  try {
    for await (const message of query({
      prompt: "/review-pr",
      options: { maxTurns: 3 }
    })) {
      // Process review feedback
    }
  } catch (error) {
    // A single-shot query() throws after yielding an error result,
    // so the second query below still runs.
    console.error(`Session ended with an error: ${error}`);
  }

  // Run specific tests
  for await (const message of query({
    prompt: "/test auth",
    options: { maxTurns: 5 }
  })) {
    // Handle test results
  }
  ```

  ```python Python theme={null}
  import asyncio
  from claude_agent_sdk import query, ClaudeAgentOptions


  async def main():
      # Run code review
      try:
          async for message in query(prompt="/review-pr", options=ClaudeAgentOptions(max_turns=3)):
              # Process review feedback
              pass
      except Exception as error:
          # A single-shot query() raises after yielding an error result,
          # so the second query below still runs.
          print(f"Session ended with an error: {error}")

      # Run specific tests
      async for message in query(prompt="/test auth", options=ClaudeAgentOptions(max_turns=5)):
          # Handle test results
          pass


  asyncio.run(main())
  ```
</CodeGroup>

## 另请参阅

* [斜杠命令](/docs/en/skills) - 完整的斜杠命令文档
* [SDK 中的子代理](/docs/en/agent-sdk/subagents) - 类似的基于文件系统的子代理配置
* [TypeScript SDK 参考](/docs/en/agent-sdk/typescript) - 完整的 API 文档
* [SDK 概述](/docs/en/agent-sdk/overview) - 通用 SDK 概念
* [CLI 参考](/docs/en/cli-reference) - 命令行界面

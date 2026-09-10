---
title: TypeScript SDK V2 会话 API（已移除）
source_id: claude-code/agent-sdk/typescript-v2-preview
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/agent-sdk/typescript-v2-preview
owner: Anthropic
content_sha256: 9299fb45b5fc6be56a7efbc6167f73dbea4d9c73db575ddf624297566b17b328
translation_of: claude-code/agent-sdk/typescript-v2-preview
translation_model: gpt-5.6
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/agent-sdk/typescript-v2-preview)

Content owner: Anthropic

> ## 文档索引
> 在以下地址获取完整的文档索引：https://code.claude.com/docs/llms.txt
> 使用此文件可在深入探索之前发现所有可用页面。

# TypeScript SDK V2 会话 API（已移除）

> 已移除的 V2 TypeScript Agent SDK 会话 API 参考，介绍多轮对话中基于会话的发送/流式传输模式。

<Warning>
  V2 会话 API 已不再受支持。TypeScript Agent SDK 0.3.142 移除了 `unstable_v2_createSession`、`unstable_v2_resumeSession`、`unstable_v2_prompt`，以及 `SDKSession` 和 `SDKSessionOptions` 类型。

  若要迁移，请使用 [`query()` API](/docs/en/agent-sdk/typescript) 及其接受的[会话选项](/docs/en/agent-sdk/sessions)。多轮对话请传入 `AsyncIterable<SDKUserMessage>`，继续已保存的会话则使用 `options.resume`。如果你维护的是 Agent SDK 0.2.x 或更早版本上的代码，本页面可留作参考。
</Warning>

V2 曾是一个实验性会话 API，不再需要异步生成器和 yield 协调。它不要求跨轮次管理生成器状态，而是让每个轮次成为单独的 `send()`/`stream()` 循环。API 表面缩减为三个概念：

* `createSession()` / `resumeSession()`：开始或继续对话
* `session.send()`：发送消息
* `session.stream()`：获取响应

## 安装

Agent SDK 0.2.x 是最后一个包含 V2 接口的版本。软件包版本从 0.2.x 直接跃升至 0.3.142，所以上述移除版本与下方安装固定版本描述的是同一边界。若要安装最后一个兼容 V2 的版本，请固定主版本和次版本：

```bash theme={null}
npm install @anthropic-ai/claude-agent-sdk@0.2
```

<Note>
  SDK 会将适用于你平台的原生 Claude Code 二进制文件作为可选依赖捆绑，因此无需单独安装 Claude Code。
</Note>

## 快速入门

### 一次性提示词

对于无需维持会话的简单单轮查询，请使用 `unstable_v2_prompt()`。此示例会发送一道数学问题并记录答案：

```typescript theme={null}
import { unstable_v2_prompt } from "@anthropic-ai/claude-agent-sdk";

const result = await unstable_v2_prompt("What is 2 + 2?", {
  model: "claude-opus-4-7"
});
if (result.subtype === "success") {
  console.log(result.result);
}
```

<details>
  <summary>查看 V1 中的相同操作</summary>

  ```typescript theme={null}
  import { query } from "@anthropic-ai/claude-agent-sdk";

  const q = query({
    prompt: "What is 2 + 2?",
    options: { model: "claude-opus-4-7" }
  });

  for await (const msg of q) {
    if (msg.type === "result" && msg.subtype === "success") {
      console.log(msg.result);
    }
  }
  ```
</details>

### 基本会话

对于超出单条提示词的交互，请创建会话。V2 将发送和流式接收分成不同步骤：

* `send()` 分派消息
* `stream()` 将响应流式传回

这种明确的分离方式更便于在轮次之间添加逻辑，例如先处理响应再发送后续消息。

以下示例会创建会话、向 Claude 发送“Hello!”，并输出文本响应。它使用 [`await using`](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-2.html#using-declarations-and-explicit-resource-management)（TypeScript 5.2+），以便在代码块退出时自动关闭会话。你也可以手动调用 `session.close()`。

```typescript theme={null}
import { unstable_v2_createSession } from "@anthropic-ai/claude-agent-sdk";

await using session = unstable_v2_createSession({
  model: "claude-opus-4-7"
});

await session.send("Hello!");
for await (const msg of session.stream()) {
  // Filter for assistant messages to get human-readable output
  if (msg.type === "assistant") {
    const text = msg.message.content
      .filter((block) => block.type === "text")
      .map((block) => block.text)
      .join("");
    console.log(text);
  }
}
```

<details>
  <summary>查看 V1 中的相同操作</summary>

  在 V1 中，输入和输出都通过同一个异步生成器流动。对于基本提示词，两者看起来相似，但添加多轮逻辑时需要重构为使用输入生成器。

  ```typescript theme={null}
  import { query } from "@anthropic-ai/claude-agent-sdk";

  const q = query({
    prompt: "Hello!",
    options: { model: "claude-opus-4-7" }
  });

  for await (const msg of q) {
    if (msg.type === "assistant") {
      const text = msg.message.content
        .filter((block) => block.type === "text")
        .map((block) => block.text)
        .join("");
      console.log(text);
    }
  }
  ```
</details>

### 多轮对话

会话会在多次交互间保留上下文。若要继续对话，请在同一个会话上再次调用 `send()`。Claude 会记住之前的轮次。

此示例先提出一道数学问题，然后提出引用前一答案的后续问题：

```typescript theme={null}
import { unstable_v2_createSession } from "@anthropic-ai/claude-agent-sdk";

await using session = unstable_v2_createSession({
  model: "claude-opus-4-7"
});

// Turn 1
await session.send("What is 5 + 3?");
for await (const msg of session.stream()) {
  // Filter for assistant messages to get human-readable output
  if (msg.type === "assistant") {
    const text = msg.message.content
      .filter((block) => block.type === "text")
      .map((block) => block.text)
      .join("");
    console.log(text);
  }
}

// Turn 2
await session.send("Multiply that by 2");
for await (const msg of session.stream()) {
  if (msg.type === "assistant") {
    const text = msg.message.content
      .filter((block) => block.type === "text")
      .map((block) => block.text)
      .join("");
    console.log(text);
  }
}
```

<details>
  <summary>查看 V1 中的相同操作</summary>

  ```typescript theme={null}
  import { query } from "@anthropic-ai/claude-agent-sdk";

  // Must create an async iterable to feed messages
  async function* createInputStream() {
    yield {
      type: "user",
      session_id: "",
      message: { role: "user", content: [{ type: "text", text: "What is 5 + 3?" }] },
      parent_tool_use_id: null
    };
    // Must coordinate when to yield next message
    yield {
      type: "user",
      session_id: "",
      message: { role: "user", content: [{ type: "text", text: "Multiply by 2" }] },
      parent_tool_use_id: null
    };
  }

  const q = query({
    prompt: createInputStream(),
    options: { model: "claude-opus-4-7" }
  });

  for await (const msg of q) {
    if (msg.type === "assistant") {
      const text = msg.message.content
        .filter((block) => block.type === "text")
        .map((block) => block.text)
        .join("");
      console.log(text);
    }
  }
  ```
</details>

### 恢复会话

如果你拥有先前交互的会话 ID，可以稍后恢复它。这适用于长期运行的工作流，或需要在应用重新启动后保留对话的情况。

此示例会创建会话、存储其 ID、关闭会话，然后恢复对话：

```typescript theme={null}
import {
  unstable_v2_createSession,
  unstable_v2_resumeSession,
  type SDKMessage
} from "@anthropic-ai/claude-agent-sdk";

// Helper to extract text from assistant messages
function getAssistantText(msg: SDKMessage): string | null {
  if (msg.type !== "assistant") return null;
  return msg.message.content
    .filter((block) => block.type === "text")
    .map((block) => block.text)
    .join("");
}

// Create initial session and have a conversation
const session = unstable_v2_createSession({
  model: "claude-opus-4-7"
});

await session.send("Remember this number: 42");

// Get the session ID from any received message
let sessionId: string | undefined;
for await (const msg of session.stream()) {
  sessionId = msg.session_id;
  const text = getAssistantText(msg);
  if (text) console.log("Initial response:", text);
}

console.log("Session ID:", sessionId);
session.close();

// Later: resume the session using the stored ID
await using resumedSession = unstable_v2_resumeSession(sessionId!, {
  model: "claude-opus-4-7"
});

await resumedSession.send("What number did I ask you to remember?");
for await (const msg of resumedSession.stream()) {
  const text = getAssistantText(msg);
  if (text) console.log("Resumed response:", text);
}
```

<details>
  <summary>查看 V1 中的相同操作</summary>

  ```typescript theme={null}
  import { query } from "@anthropic-ai/claude-agent-sdk";

  // Create initial session
  const initialQuery = query({
    prompt: "Remember this number: 42",
    options: { model: "claude-opus-4-7" }
  });

  // Get session ID from any message
  let sessionId: string | undefined;
  for await (const msg of initialQuery) {
    sessionId = msg.session_id;
    if (msg.type === "assistant") {
      const text = msg.message.content
        .filter((block) => block.type === "text")
        .map((block) => block.text)
        .join("");
      console.log("Initial response:", text);
    }
  }

  console.log("Session ID:", sessionId);

  // Later: resume the session
  const resumedQuery = query({
    prompt: "What number did I ask you to remember?",
    options: {
      model: "claude-opus-4-7",
      resume: sessionId
    }
  });

  for await (const msg of resumedQuery) {
    if (msg.type === "assistant") {
      const text = msg.message.content
        .filter((block) => block.type === "text")
        .map((block) => block.text)
        .join("");
      console.log("Resumed response:", text);
    }
  }
  ```
</details>

### 清理

会话可以手动关闭，也可以使用 [`await using`](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-2.html#using-declarations-and-explicit-resource-management) 自动关闭；这是 TypeScript 5.2+ 中用于自动清理资源的功能。如果你使用较旧的 TypeScript 版本或遇到兼容性问题，请改用手动清理。

**自动清理（TypeScript 5.2+）：**

```typescript theme={null}
import { unstable_v2_createSession } from "@anthropic-ai/claude-agent-sdk";

await using session = unstable_v2_createSession({
  model: "claude-opus-4-7"
});
// Session closes automatically when the block exits
```

**手动清理：**

```typescript theme={null}
import { unstable_v2_createSession } from "@anthropic-ai/claude-agent-sdk";

const session = unstable_v2_createSession({
  model: "claude-opus-4-7"
});
// ... use the session ...
session.close();
```

## API 参考

### `unstable_v2_createSession()`

为多轮对话创建新会话。

```typescript theme={null}
function unstable_v2_createSession(options: {
  model: string;
  // Additional options supported
}): SDKSession;
```

### `unstable_v2_resumeSession()`

按 ID 恢复现有会话。

```typescript theme={null}
function unstable_v2_resumeSession(
  sessionId: string,
  options: {
    model: string;
    // Additional options supported
  }
): SDKSession;
```

### `unstable_v2_prompt()`

适用于单轮查询的一次性便捷函数。

```typescript theme={null}
function unstable_v2_prompt(
  prompt: string,
  options: {
    model: string;
    // Additional options supported
  }
): Promise<SDKResultMessage>;
```

### SDKSession 接口

```typescript theme={null}
interface SDKSession {
  readonly sessionId: string;
  send(message: string | SDKUserMessage): Promise<void>;
  stream(): AsyncGenerator<SDKMessage, void>;
  close(): void;
}
```

## 功能可用性

V2 会话 API 并不支持 V1 的所有功能。以下功能需要使用 [V1 SDK](/docs/en/agent-sdk/typescript)：

* 会话分叉（`forkSession` 选项）
* 某些高级流式输入模式

## 另请参阅

* [TypeScript SDK 参考（V1）](/docs/en/agent-sdk/typescript) - 完整的 V1 SDK 文档
* [SDK 概述](/docs/en/agent-sdk/overview) - SDK 一般概念
* [GitHub 上的 V2 示例](https://github.com/anthropics/claude-agent-sdk-demos/tree/main/hello-world-v2) - 可运行的代码示例

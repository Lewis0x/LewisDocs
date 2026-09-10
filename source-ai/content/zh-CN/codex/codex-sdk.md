---
title: Codex SDK
source_id: codex/codex-sdk
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/codex-sdk
owner: OpenAI
content_sha256: 9296e3140d7a6ae534ce8e0ffb7fb31b0c3cccf14978d2c29064ddbd57892fe1
translation_of: codex/codex-sdk
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/codex-sdk)

Content owner: OpenAI

# Codex SDK

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。可以通过在页面 URL 后面附加 `.md` 来获取文档页面的 Markdown 版本。

如果你通过 Codex CLI、IDE 扩展或 Codex 云端使用 Codex，你还可以通过编程方式控制它。

当你需要执行以下操作时，请使用 SDK：

- 将 Codex 作为 CI/CD 流水线的一部分进行控制
- 创建你自己的代理，使其能够与 Codex 协作以执行复杂的工程任务
- 将 Codex 构建到你自己的内部工具和工作流中
- 在你自己的应用程序中集成 Codex

将 Codex SDK 用于专注于编程的 Codex 线程。如果 Codex 是更广泛的编排工作流中的一个专家角色，请[将 Codex CLI 作为 MCP 服务器运行，并使用 Agents SDK 进行编排](https://learn.chatgpt.com/docs/mcp-server)。

## TypeScript 库

TypeScript 库提供了一种从应用程序内部控制 Codex 的方法，它比非交互模式更加全面和灵活。

在服务端使用该库；它需要 Node.js 18 或更高版本。

### 安装

要开始使用，请使用 `npm` 安装 Codex SDK：

```bash
npm install @openai/codex-sdk
```

### 用法

与 Codex 开启一个线程，并使用你的提示词运行它。

```ts


const codex = new Codex();
const thread = codex.startThread();
const result = await thread.run(
  "Make a plan to diagnose and fix the CI failures"
);

console.log(result.finalResponse);
```

再次调用 `run()` 以在同一线程上继续，或者通过提供线程 ID 来恢复过去的线程。

```ts
// running the same thread
const result = await thread.run("Implement the plan");

console.log(result.finalResponse);

// resuming past thread

const threadId = "<thread-id>";
const thread2 = codex.resumeThread(threadId);
const result2 = await thread2.run("Pick up where you left off");

console.log(result2.finalResponse);
```

有关更多详细信息，请查看 [TypeScript 仓库](https://github.com/openai/codex/tree/main/sdk/typescript)。

## Python 库

Python SDK 通过 JSON-RPC 控制本地 Codex 应用服务器。它需要 Python 3.10 或更高版本。已发布的 SDK 构建包含锁定的 Codex CLI 运行时依赖项。

### 安装

要安装 SDK，请运行：

```bash
pip install openai-codex
```

已发布的 SDK 构建会自动使用其锁定的运行时。仅当你特意想要针对特定的本地 Codex 可执行文件运行时，才传递 `CodexConfig(codex_bin=...)`。

在 Python SDK 处于测试阶段时，`pip install openai-codex` 会选择最新的
已发布的测试版构建。在存在稳定的 SDK 版本后，请使用
`pip install --pre openai-codex` 来选择加入更新的预发布构建。

### 用法

启动 Codex，创建一个线程，并运行提示词：

```python
from openai_codex import Codex, Sandbox

with Codex() as codex:
    thread = codex.thread_start(
        model="gpt-5.4",
        sandbox=Sandbox.workspace_write,
    )
    result = thread.run("Make a plan to diagnose and fix the CI failures")
    print(result.final_response)
```

当你的应用程序已经是异步时，请使用 `AsyncCodex`：

```python
import asyncio

from openai_codex import AsyncCodex


async def main() -> None:
    async with AsyncCodex() as codex:
        thread = await codex.thread_start(model="gpt-5.4")
        result = await thread.run("Implement the plan")
        print(result.final_response)


asyncio.run(main())
```

### 沙盒预设

在创建线程或更改其文件系统
以供后续轮次访问时，请使用相同的 `Sandbox` 预设：

```python
from openai_codex import Codex, Sandbox

with Codex() as codex:
    thread = codex.thread_start(sandbox=Sandbox.workspace_write)
    thread.run("Make the requested change.")
    review = thread.run("Review the diff only.", sandbox=Sandbox.read_only)
```

可用的预设：

- `Sandbox.read_only`：读取文件，但不允许写入。
- `Sandbox.workspace_write`：读取文件，并在工作区及配置的可写根目录内进行写入。
- `Sandbox.full_access`：在没有文件系统访问限制的情况下运行。

当你省略 `sandbox=` 时，应用服务器会使用其配置的默认值。传给
`run(...)` 或 `turn(...)` 的沙盒将应用于该轮次以及随后的轮次
在该线程上。

有关更多详细信息，请查看 [Python 仓库](https://github.com/openai/codex/tree/main/sdk/python)。

---
title: 将会话持久化到外部存储
source_id: claude-code/agent-sdk/session-storage
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/agent-sdk/session-storage
owner: Anthropic
content_sha256: f9841faface9ddcfd8f04125454fed5beefff06cabcc16cb5259576c2111f132
translation_of: claude-code/agent-sdk/session-storage
translation_model: k3
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/agent-sdk/session-storage)

Content owner: Anthropic

> ## 文档索引
> 在以下地址获取完整的文档索引：https://code.claude.com/docs/llms.txt
> 在进一步探索之前，使用此文件来发现所有可用的页面。

# 将会话持久化到外部存储

> 将会话记录镜像到 S3、Redis 或您自己的后端，以便任何主机都可以恢复它们。

默认情况下，SDK 将会话记录写入本地文件系统上 `~/.claude/projects/` 下的 JSONL 文件。`SessionStore` 适配器允许您将这些记录镜像到自己的后端（如 S3、Redis 或数据库），从而可以在另一台主机上恢复在某台主机上创建的会话。

使用会话存储的常见原因：

* **多主机部署。** 无服务器函数、自动扩缩的工作进程和 CI 运行器不共享文件系统。共享存储允许任何副本恢复任何会话。
* **持久性。** 本地容器是短暂的。由 S3 或数据库支持的存储可以在重启和重新部署后存活。
* **合规与审计。** 将记录保存在您已经管理的存储中，并使用您自己的保留规则、加密和访问控制。

## `SessionStore` 接口

`SessionStore` 是一个具有两个必需方法 `append` 和 `load` 以及四个可选方法的对象。SDK 在查询期间调用 `append` 来写入记录条目，并调用 `load` 来读取它们以进行恢复。

<CodeGroup>
  ```typescript TypeScript theme={null}
  // Exported from @anthropic-ai/claude-agent-sdk as
  // SessionStore, SessionKey, SessionStoreEntry, SessionSummaryEntry.

  type SessionKey = {
    projectKey: string;
    sessionId: string;
    subpath?: string;
  };

  type SessionStore = {
    // Required
    append(key: SessionKey, entries: SessionStoreEntry[]): Promise<void>;
    load(key: SessionKey): Promise<SessionStoreEntry[] | null>;

    // Optional
    listSessions?(
      projectKey: string,
    ): Promise<Array<{ sessionId: string; mtime: number }>>;
    listSessionSummaries?(projectKey: string): Promise<SessionSummaryEntry[]>;
    delete?(key: SessionKey): Promise<void>;
    listSubkeys?(key: {
      projectKey: string;
      sessionId: string;
    }): Promise<string[]>;
  };

  type SessionSummaryEntry = {
    sessionId: string;
    mtime: number;
    data: Record<string, unknown>;
  };
  ```

  ```python Python theme={null}
  # Exported from claude_agent_sdk as
  # SessionStore, SessionKey, SessionStoreEntry, SessionSummaryEntry.

  class SessionKey(TypedDict):
      project_key: str
      session_id: str
      subpath: NotRequired[str]

  class SessionStore(Protocol):
      # Required
      async def append(
          self, key: SessionKey, entries: list[SessionStoreEntry]
      ) -> None: ...
      async def load(self, key: SessionKey) -> list[SessionStoreEntry] | None: ...

      # Optional — omit or raise NotImplementedError
      async def list_sessions(
          self, project_key: str
      ) -> list[SessionStoreListEntry]: ...
      async def list_session_summaries(
          self, project_key: str
      ) -> list[SessionSummaryEntry]: ...
      async def delete(self, key: SessionKey) -> None: ...
      async def list_subkeys(self, key: SessionListSubkeysKey) -> list[str]: ...

  class SessionSummaryEntry(TypedDict):
      session_id: str
      mtime: int
      data: dict[str, Any]
  ```
</CodeGroup>

`SessionKey` 对应一份记录。`projectKey` 是工作目录的稳定、文件系统安全的编码，`sessionId` 是会话 UUID，而当条目属于子代理记录或辅助记录文件而非主对话时，会设置 `subpath`。请将 `subpath` 视为不透明的键后缀；它遵循磁盘上的布局，例如 `subagents/agent-<id>`。当 `subpath` 未定义时，该键指向主记录。

| 方法                 | 必需 | 调用时机                                                                                                                                                                                                         |
| :--------------------- | :------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `append`               | 是      | 在每批转录条目写入本地之后调用。条目是 JSON 安全对象，在本地 JSONL 中每行一个。                                                                                                                                                                                |
| `load`                 | 是      | 当设置了 `resume` 时，在子进程启动前调用；当列表从 `listSessionSummaries` 回退时，每个会话调用一次。如果会话未知，返回 `null`。                                                                                                                                     |
| `listSessions`         | 否       | 由 `listSessions({ sessionStore })` 调用，也由带 `continue: true` 的 `query()`/`startup()` 调用。如果未定义，`continue: true` 会抛出异常；除非实现了 `listSessionSummaries`，否则 `listSessions({ sessionStore })` 也会抛出异常。                                                                                  |
| `listSessionSummaries` | 否       | 由 `listSessions({ sessionStore })` 调用，用于在一次调用中读取所有会话的元数据。请在 `append` 内维护这些摘要。如果未定义，列表会回退为 `listSessions` 加上逐会话的 `load`。                                                                                                  |
| `delete`               | 否       | 由 `deleteSession({ sessionStore })` 调用。删除主键（没有 `subpath`）必须级联到该会话的所有子键，并同时移除该会话的摘要条目，使已删除会话不再出现在 `listSessionSummaries` 中。如果未定义，删除为空操作，这适合仅追加型后端。 |
| `listSubkeys`          | 否       | 在恢复期间调用，用于发现子代理转录。如果未定义，只恢复主转录。                                                                                                                                                                                                      |

在 `SessionSummaryEntry` 中，`mtime` 是辅助记录的存储写入时间，并且必须与 `listSessions` 返回的 `mtime` 值共享同一时钟源。`data` 是 SDK 拥有的不透明状态；请逐字持久化，不要解释它。

通过调用导出的 `foldSessionSummary` 辅助函数（Python 中为 `fold_session_summary`），在 `append` 内对每个批次构建条目。跳过键带有 `subpath` 的批次；子代理转录不得计入主会话摘要。折叠操作永不设置 `mtime`：在持久化时加盖时间戳，TypeScript 中通过 `options.mtime` 参数，Python 中通过覆盖返回条目上的字段。同一会话的并发 `append` 调用可能在辅助记录上竞争，因此请用事务、比较并交换或每会话锁来串行化“读取-折叠-写入”；折叠操作本身是纯函数。

## 快速入门

SDK 附带一个用于开发和测试的 `InMemorySessionStore`。下面的示例在附加了存储的情况下运行查询，从结果消息中捕获会话 ID，然后在第二个 `query()` 调用中从存储恢复。第二个调用传入相同的存储实例加上 `resume`，因此 SDK 会从存储中加载会话记录，而不是从本地文件系统加载：

<CodeGroup>
  ```typescript TypeScript theme={null}
  import { query, InMemorySessionStore } from "@anthropic-ai/claude-agent-sdk";

  const store = new InMemorySessionStore();

  let sessionId: string | undefined;
  try {
    for await (const message of query({
      prompt: "List the TypeScript files under src/",
      options: { sessionStore: store },
    })) {
      if (message.type === "result") {
        sessionId = message.session_id;
      }
    }
  } catch (error) {
    // A single-shot query() throws after yielding an error result. If the
    // failure was an error result, sessionId was already captured by the loop
    // above; connection or process failures yield no result message.
    console.error(`Session ended with an error: ${error}`);
  }

  // Resume from the store. The agent has full context from the first call.
  for await (const message of query({
    prompt: "Summarize what those files do",
    options: { sessionStore: store, resume: sessionId },
  })) {
    if (message.type === "result" && message.subtype === "success") {
      console.log(message.result);
    }
  }
  ```

  ```python Python theme={null}
  import asyncio
  from claude_agent_sdk import (
      ClaudeAgentOptions,
      InMemorySessionStore,
      ResultMessage,
      query,
  )

  store = InMemorySessionStore()


  async def main():
      session_id = None
      try:
          async for message in query(
              prompt="List the Python files under src/",
              options=ClaudeAgentOptions(session_store=store),
          ):
              if isinstance(message, ResultMessage):
                  session_id = message.session_id
      except Exception as error:
          # A single-shot query() raises after yielding an error result. If the
          # failure was an error result, session_id was already captured by the
          # loop above; connection or process failures yield no result message.
          print(f"Session ended with an error: {error}")

      # Resume from the store. The agent has full context from the first call.
      async for message in query(
          prompt="Summarize what those files do",
          options=ClaudeAgentOptions(session_store=store, resume=session_id),
      ):
          if isinstance(message, ResultMessage) and message.subtype == "success":
              print(message.result)


  asyncio.run(main())
  ```
</CodeGroup>

第二个查询会打印出第一个查询所得文件的摘要，这表明代理已携带存储中的完整上下文恢复。

## 编写你自己的适配器

针对你的后端实现 `append` 和 `load`。如果你希望 `listSessions()`、单调用元数据读取、`deleteSession()` 以及子代理恢复能够基于该存储工作，还需添加 `listSessions`、`listSessionSummaries`、`delete` 和 `listSubkeys`。

传递给 `append` 的条目类型为 `SessionStoreEntry`（一个 `{ type: string; ... }` 对象）。将它们视为不透明的、JSON 安全的值：按顺序持久化它们，并从 `load` 以相同顺序返回它们。`load` 必须返回与所追加内容深度相等的条目；不要求字节级相等的序列化，因此像 Postgres `jsonb` 这样会重排对象键的后端也是可以接受的。

## 参考实现

TypeScript SDK 仓库在 [`examples/session-stores/`](https://github.com/anthropics/claude-agent-sdk-typescript/tree/main/examples/session-stores) 下包含了适用于 S3、Redis 和 Postgres 的可运行参考适配器。它们不会发布到 npm;请将你需要的 `src/` 文件复制到你的项目中,并安装相应的后端客户端。

| 适配器                                                                                                                        | 后端客户端       | 存储模型                                                                |
| :----------------------------------------------------------------------------------------------------------------------------- | :------------------- | :--------------------------------------------------------------------------- |
| [`S3SessionStore`](https://github.com/anthropics/claude-agent-sdk-typescript/tree/main/examples/session-stores/s3)             | `@aws-sdk/client-s3` | 每个 `append()` 对应一个 JSONL 部分文件;`load()` 列出、排序并拼接。 |
| [`RedisSessionStore`](https://github.com/anthropics/claude-agent-sdk-typescript/tree/main/examples/session-stores/redis)       | `ioredis`            | 每个转录对应一个 `RPUSH`/`LRANGE` 列表,外加一个有序集合会话索引。       |
| [`PostgresSessionStore`](https://github.com/anthropics/claude-agent-sdk-typescript/tree/main/examples/session-stores/postgres) | `pg`                 | `jsonb` 表中每个条目占一行,按 `BIGSERIAL` 排序。                |

每个适配器接收一个预先配置好的客户端实例,因此你可以控制凭据、TLS、区域和连接池。例如,使用 S3 时:

```typescript TypeScript theme={null}
import { query } from "@anthropic-ai/claude-agent-sdk";
import { S3Client } from "@aws-sdk/client-s3";
import { S3SessionStore } from "./S3SessionStore"; // copied from examples/session-stores/s3

const store = new S3SessionStore({
  bucket: "my-claude-sessions",
  prefix: "transcripts",
  client: new S3Client({ region: "us-east-1" }),
});

for await (const message of query({
  prompt: "Hello!",
  options: { sessionStore: store },
})) {
  if (message.type === "result" && message.subtype === "success") {
    console.log(message.result);
  }
}

// Later, possibly on a different host:
for await (const message of query({
  prompt: "Continue where we left off",
  options: { sessionStore: store, resume: "previous-session-id" },
})) {
  // ...
}
```

### 验证你的适配器

两个 SDK 都附带一个一致性测试套件,用于断言 `append`、`load` 以及可选方法必须满足的行为契约。当可选方法未实现时,相应的测试会自动跳过。

在 TypeScript 中,将示例目录中的 [`shared/conformance.ts`](https://github.com/anthropics/claude-agent-sdk-typescript/blob/main/examples/session-stores/shared/conformance.ts) 复制到你的测试套件中。在 Python 中,该套件随包一起发布:

```python Python theme={null}
import pytest
from claude_agent_sdk.testing import run_session_store_conformance


@pytest.mark.asyncio
async def test_my_store_conformance():
    await run_session_store_conformance(MyRedisStore)  # Your adapter class
```

## 行为说明

### 双写架构

存储是镜像,而非替代品。Claude Code 子进程始终先写入本地磁盘;然后 SDK 将每个批次转发给 `append()`。如果你希望本地副本是临时的,请通过 `options.env` 将 `CLAUDE_CONFIG_DIR` 指向一个临时目录。

由于镜像依赖于本地写入,如果你在 TypeScript SDK 中同时使用 `sessionStore` 和 `persistSession: false`,SDK 会抛出异常。如果你将存储与文件检查点功能结合使用——TypeScript 中的 `enableFileCheckpointing` 或 Python 中的 `enable_file_checkpointing`——两个 SDK 也都会抛出异常,因为文件历史备份 blob 是直接写入本地磁盘的,不会被镜像到存储中。

### 镜像写入是尽力而为的

如果 `append()` 被拒绝,SDK 会以短暂的退避间隔最多再重试该批次两次,即总共最多尝试三次。超时的调用不会被重试,因为原始调用可能仍会成功到达。如果批次仍然失败,错误会被记录,一条 `{ type: "system", subtype: "mirror_error" }` 消息会被发送到迭代器中,该批次被丢弃,查询继续进行。本地转录已经持久化在磁盘上,因此存储中断不会打断代理,也不会在本地丢失数据。如果你需要检测存储数据丢失,请监控 `mirror_error`。由于重试的批次可能会重新投递已经到达的条目,请在你的 `append()` 实现中按 `entry.uuid` 去重。

### `getSessionMessages` 返回压缩后的消息链

`getSessionMessages({ sessionStore })` 返回代理在恢复会话时会看到的链接消息链。自动压缩之后,较早的轮次会被摘要替换,因此一个存储中保存了 503 条原始条目的会话,从 `getSessionMessages` 可能只返回 18 条消息。如需完整的原始历史记录,包括压缩前的轮次和元数据条目,请直接调用 `store.load(key)`。

### `forkSession` 不是字节级复制

`forkSession({ sessionStore })` 会读取源条目，重写每个 `sessionId` 字段并重新映射消息 UUID，然后将转换后的条目追加到新键下。适配器级别的复制或 `CopyObject` 快捷方式会生成仍引用旧会话 ID 的转录文件，因此 SDK 不会使用这种方式。

### 子代理转录

子代理转录会镜像到 `subpath: "subagents/agent-<id>"` 下。`listSubagents({ sessionStore })` 要求适配器实现 `listSubkeys`；`getSubagentMessages({ sessionStore })` 在可用时会使用它，但在其未定义时会回退到直接子路径。恢复操作也会调用 `listSubkeys` 来还原子代理文件；没有它，只有主转录文件会被物化。

### 保留策略

SDK 绝不会自行从你的存储中删除数据。保留是适配器的职责：根据你的合规要求实现 TTL、S3 生命周期策略或计划清理。`CLAUDE_CONFIG_DIR` 下的本地转录文件由 `cleanupPeriodDays` 设置独立清理。

## 支持于

以下 TypeScript SDK 函数接受 `sessionStore` 选项，并在提供该选项时针对存储而非本地文件系统进行操作：

* [`query()`](/docs/en/agent-sdk/typescript#query)
* [`startup()`](/docs/en/agent-sdk/typescript#startup)
* [`listSessions()`](/docs/en/agent-sdk/typescript#listsessions)
* [`getSessionInfo()`](/docs/en/agent-sdk/typescript#getsessioninfo)
* [`getSessionMessages()`](/docs/en/agent-sdk/typescript#getsessionmessages)
* [`renameSession()`](/docs/en/agent-sdk/typescript#renamesession)
* [`tagSession()`](/docs/en/agent-sdk/typescript#tagsession)
* [`deleteSession()`](/docs/en/agent-sdk/typescript)
* [`forkSession()`](/docs/en/agent-sdk/typescript)
* [`listSubagents()`](/docs/en/agent-sdk/typescript)
* [`getSubagentMessages()`](/docs/en/agent-sdk/typescript)

在 Python SDK 中，将 `session_store` 设置到 [`ClaudeAgentOptions`](/docs/en/agent-sdk/python#claudeagentoptions) 中以运行 `query()` 针对一个存储。其余每个操作都有一个由存储支持的 Python 函数，该函数将存储作为参数： `list_sessions_from_store()`, `get_session_info_from_store()`, `get_session_messages_from_store()`, `list_subagents_from_store()`, `get_subagent_messages_from_store()`, `rename_session_via_store()`, `tag_session_via_store()`, `delete_session_via_store()`, 和 `fork_session_via_store()`. `startup()` 没有 Python 等价项. [Python SDK 参考](/docs/en/agent-sdk/python#functions) 中记录的独立函数（例如 `list_sessions()`）会读取本地会话文件。

## 相关资源

* [使用会话](/docs/en/agent-sdk/sessions)：无需自定义存储即可继续、恢复和分叉
* [托管 SDK](/docs/en/agent-sdk/hosting)：多主机环境的部署模式
* [TypeScript `Options`](/docs/en/agent-sdk/typescript#options)：完整选项参考
* [`examples/session-stores/`](https://github.com/anthropics/claude-agent-sdk-typescript/tree/main/examples/session-stores)：可运行的 S3、Redis 和 Postgres 参考适配器

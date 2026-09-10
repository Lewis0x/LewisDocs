---
title: Agent SDK 参考 - TypeScript
source_id: claude-code/agent-sdk/typescript
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/agent-sdk/typescript
owner: Anthropic
content_sha256: d6d9403ca6e6a0c2254b4a2215eba98863f8133cd68f78423b8df33cf302ac57
translation_of: claude-code/agent-sdk/typescript
translation_model: k3
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/agent-sdk/typescript)

Content owner: Anthropic

> ## 文档索引
> 获取完整的文档索引：https://code.claude.com/docs/llms.txt
> 使用此文件在进一步探索之前发现所有可用页面。

# Agent SDK 参考 - TypeScript

> TypeScript Agent SDK 的完整 API 参考，包括所有函数、类型和接口。

<script src="/docs/components/typescript-sdk-type-links.js" defer />

## 安装

```bash theme={null}
npm install @anthropic-ai/claude-agent-sdk
```

<Note>
  SDK 将适用于您平台的原生 Claude Code 二进制文件作为可选依赖（例如 `@anthropic-ai/claude-agent-sdk-darwin-arm64`）捆绑在一起。您无需单独安装 Claude Code。SDK 版本跟随捆绑的 Claude Code 版本：SDK v0.3.191 捆绑 Claude Code v2.1.191，因此本页面上要求某个 Claude Code 版本的功能需要具有相同补丁号或更高版本的 SDK 发行版。如果您的包管理器跳过可选依赖，SDK 会抛出 `Native CLI binary for <platform> not found`；此时请将 [`pathToClaudeCodeExecutable`](#options) 设置为单独安装的 `claude` 二进制文件。
</Note>

### 编译为单个可执行文件

当您使用 `bun build --compile` 将应用程序编译为单文件可执行文件时，SDK 无法在运行时解析捆绑的 CLI 二进制文件。`require.resolve` 在编译后可执行文件的 `$bunfs` 虚拟文件系统内不起作用，因此 SDK 会抛出 `Native CLI binary for <platform> not found`。

要解决此问题，请将平台二进制文件作为文件资产嵌入，在启动时使用 `extractFromBunfs()` 将其提取到真实路径，并将该路径传递给 [`pathToClaudeCodeExecutable`](#options)。

`extractFromBunfs()` 辅助函数需要 `@anthropic-ai/claude-agent-sdk` v0.3.144 或更高版本。下面的示例针对 Apple Silicon 上的 macOS 构建：

```typescript theme={null}
import binPath from "@anthropic-ai/claude-agent-sdk-darwin-arm64/claude" with { type: "file" };
import { extractFromBunfs } from "@anthropic-ai/claude-agent-sdk/extract";
import { query } from "@anthropic-ai/claude-agent-sdk";

const cliPath = extractFromBunfs(binPath);

for await (const message of query({
  prompt: "Hello",
  options: { pathToClaudeCodeExecutable: cliPath },
})) {
  console.log(message);
}
```

`extractFromBunfs()` 将嵌入的二进制文件从编译后可执行文件的虚拟文件系统复制到每个用户的临时目录，并返回真实路径。在编译后的可执行文件之外，它会原样返回输入路径，因此相同的代码无需修改即可在开发中运行。

每个编译后的可执行文件仅嵌入单个平台的二进制文件。请让导入的平台包与您的 `--target` 匹配：

* 要进行交叉编译，请安装不匹配的平台包，例如 `npm install @anthropic-ai/claude-agent-sdk-linux-x64 --force`。
* 在 Windows 上，二进制文件的子路径为 `claude.exe`，例如 `@anthropic-ai/claude-agent-sdk-win32-x64/claude.exe`。

## 函数

### `query()`

与 Claude Code 交互的主要函数。创建一个异步生成器，在消息到达时将其流式传输。

```typescript theme={null}
function query({
  prompt,
  options
}: {
  prompt: string | AsyncIterable<SDKUserMessage>;
  options?: Options;
}): Query;
```

#### 参数

| 参数 | 类型                                                             | 描述                                                       |
| :-------- | :--------------------------------------------------------------- | :---------------------------------------------------------------- |
| `prompt`  | `string \| AsyncIterable<`[`SDKUserMessage`](#sdkusermessage)`>` | 输入提示，可以是字符串或用于流式模式的异步可迭代对象 |
| `options` | [`Options`](#options)                                            | 可选配置对象（见下方的 Options 类型）            |

#### 返回值

返回一个 [`Query`](#query-object) 对象，该对象扩展了 `AsyncGenerator<`[`SDKMessage`](#sdkmessage)`, void>` 并带有附加方法。

### `startup()`

通过在提示可用之前启动 CLI 子进程并完成初始化握手来预热 CLI 子进程。返回的 [`WarmQuery`](#warmquery) 句柄稍后接受提示并将其写入已就绪的进程，因此第一个 `query()` 调用无需在该次调用中承担子进程启动和初始化开销即可兑现。

```typescript theme={null}
function startup(params?: {
  options?: Options;
  initializeTimeoutMs?: number;
}): Promise<WarmQuery>;
```

#### 参数

| 参数                  | 类型                  | 描述                                                                                                                                                                         |
| :-------------------- | :-------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `options`             | [`Options`](#options) | 可选的配置对象。与传递给 `query()` 的 `options` 参数相同                                                                                                     |
| `initializeTimeoutMs` | `number`              | 等待子进程初始化的最长时间（毫秒）。默认为 `60000`。如果初始化未能及时完成，Promise 将以超时错误拒绝 |

#### 返回值

返回一个 `Promise<`[`WarmQuery`](#warmquery)`>`，一旦子进程完成启动并完成其初始化握手，该 Promise 即会兑现。

#### 示例

尽早调用 `startup()`，例如在应用启动时调用，然后在提示词准备就绪后对返回的句柄调用 `.query()`。这会将子进程的启动和初始化移出关键路径。

```typescript theme={null}
import { startup } from "@anthropic-ai/claude-agent-sdk";

// Pay startup cost upfront
const warm = await startup({ options: { maxTurns: 3 } });

// Later, when a prompt is ready, this is immediate
for await (const message of warm.query("What files are here?")) {
  console.log(message);
}
```

### `tool()`

为与 SDK MCP 服务器配合使用而创建类型安全的 MCP 工具定义。

```typescript theme={null}
function tool<Schema extends AnyZodRawShape>(
  name: string,
  description: string,
  inputSchema: Schema,
  handler: (args: InferShape<Schema>, extra: unknown) => Promise<CallToolResult>,
  extras?: { annotations?: ToolAnnotations; searchHint?: string; alwaysLoad?: boolean }
): SdkMcpToolDefinition<Schema>;
```

#### 参数

| 参数          | 类型                                                                                                   | 描述                                                                                                                                                                                                                                                                                                            |
| :------------ | :----------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `name`        | `string`                                                                                               | 工具的名称                                                                                                                                                                                                                                                                                                      |
| `description` | `string`                                                                                               | 对工具功能的描述                                                                                                                                                                                                                                                                                                |
| `inputSchema` | `Schema extends AnyZodRawShape`                                                                        | 定义工具输入参数的 Zod 模式（同时支持 Zod 3 和 Zod 4）                                                                                                                                                                                                                                                        |
| `handler`     | `(args, extra) => Promise<`[`CallToolResult`](#calltoolresult)`>`                                      | 执行工具逻辑的异步函数                                                                                                                                                                                                                                                                   |
| `extras`      | `{ annotations?: `[`ToolAnnotations`](#toolannotations)`; searchHint?: string; alwaysLoad?: boolean }` | 可选的附加项。`annotations` 向客户端提供 MCP 行为提示。`searchHint` 是当[工具搜索](/docs/en/agent-sdk/tool-search)激活时，在延迟工具列表中显示的一行能力描述短语。`alwaysLoad: true` 将此工具的完整模式保留在初始提示中，而不是延迟加载 |

#### `ToolAnnotations`

重新导出自 `@modelcontextprotocol/sdk/types.js`。所有字段均为可选提示；客户端不应依赖它们做出安全决策。

| 字段             | 类型      | 默认值     | 描述                                                                                                                                          |
| :---------------- | :-------- | :---------- | :--------------------------------------------------------------------------------------------------------------------------------------------------- |
| `title`           | `string`  | `undefined` | 工具的人类可读标题                                                                                                                    |
| `readOnlyHint`    | `boolean` | `false`     | 如果为 `true`，则该工具不会修改其环境                                                                                                  |
| `destructiveHint` | `boolean` | `true`      | 如果为 `true`，则该工具可能执行破坏性更新（仅当 `readOnlyHint` 为 `false` 时才有意义）                                                 |
| `idempotentHint`  | `boolean` | `false`     | 如果为 `true`，则使用相同参数重复调用不会产生额外影响（仅当 `readOnlyHint` 为 `false` 时才有意义）                         |
| `openWorldHint`   | `boolean` | `true`      | 如果为 `true`，则该工具与外部实体交互（例如网络搜索）。如果为 `false`，则该工具的作用域是封闭的（例如记忆工具） |

```typescript theme={null}
import { tool } from "@anthropic-ai/claude-agent-sdk";
import { z } from "zod";

const searchTool = tool(
  "search",
  "Search the web",
  { query: z.string() },
  async ({ query }) => {
    return { content: [{ type: "text", text: `Results for: ${query}` }] };
  },
  { annotations: { readOnlyHint: true, openWorldHint: true } }
);
```

### `createSdkMcpServer()`

创建一个与您的应用程序在同一进程中运行的 MCP 服务器实例。

```typescript theme={null}
function createSdkMcpServer(options: {
  name: string;
  version?: string;
  instructions?: string;
  tools?: Array<SdkMcpToolDefinition<any>>;
  alwaysLoad?: boolean;
}): McpSdkServerConfigWithInstance;
```

#### 参数

| 参数              | 类型                          | 描述                                                                                                                                                                                          |
| :--------------------- | :---------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `options.name`         | `string`                      | MCP 服务器的名称                                                                                                                                                                           |
| `options.version`      | `string`                      | 可选版本字符串                                                                                                                                                                              |
| `options.instructions` | `string`                      | 可选服务器指令，从 `initialize` 返回，并作为 MCP 指令块呈现给模型                                                                                      |
| `options.tools`        | `Array<SdkMcpToolDefinition>` | 使用 [`tool()`](#tool) 创建的工具定义数组                                                                                                                                             |
| `options.alwaysLoad`   | `boolean`                     | 当 `true` 时，此服务器的每个工具都保留在初始提示中，绝不会延迟到[工具搜索](/docs/en/agent-sdk/tool-search)之后。可与按工具 `alwaysLoad` 在 [`tool()`](#tool) 中结合使用 |

### `listSessions()`

发现并列出带有轻量元数据的过往会话。可按项目目录筛选，或列出所有项目中的会话。

```typescript theme={null}
function listSessions(options?: ListSessionsOptions): Promise<SDKSessionInfo[]>;
```

#### 参数

| 参数                  | 类型      | 默认值     | 描述                                                                        |
| :------------------------- | :-------- | :---------- | :--------------------------------------------------------------------------------- |
| `options.dir`              | `string`  | `undefined` | 要列出会话的目录。省略时，返回所有项目的会话 |
| `options.limit`            | `number`  | `undefined` | 要返回的最大会话数                                               |
| `options.includeWorktrees` | `boolean` | `true`      | 当 `dir` 位于 git 仓库内时，包含来自所有 worktree 路径的会话    |

#### 返回类型： `SDKSessionInfo`

| 属性       | 类型                  | 描述                                                                 |
| :------------- | :-------------------- | :-------------------------------------------------------------------------- |
| `sessionId`    | `string`              | 唯一会话标识符（UUID）                                            |
| `summary`      | `string`              | 显示标题：自定义标题、自动生成的摘要或第一条提示        |
| `lastModified` | `number`              | 自纪元以来的最后修改时间（毫秒）                              |
| `fileSize`     | `number \| undefined` | 会话文件大小（字节）。仅对本地 JSONL 存储填充          |
| `customTitle`  | `string \| undefined` | 用户设置的会话标题（通过 `/rename`）                                      |
| `firstPrompt`  | `string \| undefined` | 会话中第一条有意义的用户提示                                 |
| `gitBranch`    | `string \| undefined` | 会话结束时的 Git 分支                                        |
| `cwd`          | `string \| undefined` | 会话的工作目录                                           |
| `tag`          | `string \| undefined` | 用户设置的会话标签（参见 [`tagSession()`](#tagsession)）                    |
| `createdAt`    | `number \| undefined` | 自纪元以来的创建时间（毫秒），取自第一条记录的时间戳 |

#### 示例

打印项目的最近 10 个会话。结果按 `lastModified` 降序排序，因此第一项是最新的。省略 `dir` 可跨所有项目搜索。

```typescript theme={null}
import { listSessions } from "@anthropic-ai/claude-agent-sdk";

const sessions = await listSessions({ dir: "/path/to/project", limit: 10 });

for (const session of sessions) {
  console.log(`${session.summary} (${session.sessionId})`);
}
```

### `getSessionMessages()`

从过去的会话记录中读取用户和助手消息。

```typescript theme={null}
function getSessionMessages(
  sessionId: string,
  options?: GetSessionMessagesOptions
): Promise<SessionMessage[]>;
```

#### 参数

| 参数        | 类型     | 默认值     | 描述                                                                   |
| :--------------- | :------- | :---------- | :---------------------------------------------------------------------------- |
| `sessionId`      | `string` | 必填    | 要读取的会话 UUID（参见 `listSessions()`）                                   |
| `options.dir`    | `string` | `undefined` | 用于查找会话的项目目录。省略时，搜索所有项目 |
| `options.limit`  | `number` | `undefined` | 返回的最大消息数                                          |
| `options.offset` | `number` | `undefined` | 从开头跳过的消息数                                     |

#### 返回类型： `SessionMessage`

| 属性             | 类型                    | 描述                                                                                                                                                                                                                                                                                                                                                            |
| :------------------- | :---------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `type`               | `"user" \| "assistant"` | 消息角色                                                                                                                                                                                                                                                                                                                                                            |
| `uuid`               | `string`                | 唯一消息标识符                                                                                                                                                                                                                                                                                                                                                      |
| `session_id`         | `string`                | 此消息所属的会话                                                                                                                                                                                                                                                                                                                                                    |
| `message`            | `unknown`               | 来自转录的原始消息负载                                                                                                                                                                                                                                                                                                                                              |
| `parent_tool_use_id` | `string \| null`        | 对于子代理消息，为生成它的 `Agent` 工具调用的 `tool_use_id`。主会话消息和旧会话为 `null`                                                                                                                                                                           |
| `parent_agent_id`    | `string \| null`        | 对于来自 [嵌套子代理](/docs/en/sub-agents#let-subagents-spawn-their-own-subagents) 的消息，为生成它的子代理的 `agentId`。主会话消息、顶级子代理消息以及旧会话为 `null`。{/* min-version: 2.1.202 */}需要 Claude Code v2.1.202 或更高版本 |

#### 示例

```typescript theme={null}
import { listSessions, getSessionMessages } from "@anthropic-ai/claude-agent-sdk";

const [latest] = await listSessions({ dir: "/path/to/project", limit: 1 });

if (latest) {
  const messages = await getSessionMessages(latest.sessionId, {
    dir: "/path/to/project",
    limit: 20
  });

  for (const msg of messages) {
    console.log(`[${msg.type}] ${msg.uuid}`);
  }
}
```

### `getSessionInfo()`

按 ID 读取单个会话的元数据，而无需扫描完整项目目录。

```typescript theme={null}
function getSessionInfo(
  sessionId: string,
  options?: GetSessionInfoOptions
): Promise<SDKSessionInfo | undefined>;
```

#### 参数

| 参数     | 类型     | 默认值     | 描述                                                            |
| :------------ | :------- | :---------- | :--------------------------------------------------------------------- |
| `sessionId`   | `string` | 必填    | 要查找的会话 UUID                                         |
| `options.dir` | `string` | `undefined` | 项目目录路径。省略时，搜索所有项目目录 |

返回 [`SDKSessionInfo`](#return-type-sdksessioninfo)，如果未找到会话则返回 `undefined`。

### `renameSession()`

通过追加自定义标题条目来重命名会话。重复调用是安全的；以最新的标题为准。

```typescript theme={null}
function renameSession(
  sessionId: string,
  title: string,
  options?: SessionMutationOptions
): Promise<void>;
```

#### 参数

| 参数     | 类型     | 默认值     | 描述                                                            |
| :------------ | :------- | :---------- | :--------------------------------------------------------------------- |
| `sessionId`   | `string` | 必填    | 要重命名的会话的 UUID                                          |
| `title`       | `string` | 必填    | 新标题。去除首尾空白后必须非空                 |
| `options.dir` | `string` | `undefined` | 项目目录路径。省略时，搜索所有项目目录 |

### `tagSession()`

为会话添加标签。传入 `null` 可清除标签。重复调用是安全的；以最近一次设置的标签为准。

```typescript theme={null}
function tagSession(
  sessionId: string,
  tag: string | null,
  options?: SessionMutationOptions
): Promise<void>;
```

#### 参数

| 参数     | 类型             | 默认值     | 描述                                                            |
| :------------ | :--------------- | :---------- | :--------------------------------------------------------------------- |
| `sessionId`   | `string`         | 必填    | 要打标签的会话的 UUID                                             |
| `tag`         | `string \| null` | 必填    | 标签字符串，或传入 `null` 以清除                                         |
| `options.dir` | `string`         | `undefined` | 项目目录路径。省略时，搜索所有项目目录 |

### `resolveSettings()`

使用与 CLI 相同的合并引擎解析给定目录的有效 Claude Code 设置，而无需启动 Claude CLI。在调用 `query()` 之前，可用它检查该调用将看到的配置。

<Note>
  此函数处于 alpha 阶段，其 API 在稳定之前可能发生变化。为与 CLI 启动保持一致，它会读取 MDM 来源，包括 macOS plist 和 Windows HKLM/HKCU，但不会执行管理员配置的 `policyHelper` 子进程。`permissions.defaultMode` 字段按原样从所有层级（包括项目设置）返回。CLI 在采用升级的权限模式之前所应用的信任过滤器在此不会应用。
</Note>

```typescript theme={null}
function resolveSettings(
  options?: ResolveSettingsOptions
): Promise<ResolvedSettings>;
```

#### 参数

`resolveSettings()` 接受一个选项对象。所有字段均为可选。

| 参数                       | 类型                                  | 默认值         | 描述                                                                                                                                                                                                         |
| :------------------------------ | :------------------------------------ | :-------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `options.cwd`                   | `string`                              | `process.cwd()` | 作为解析项目设置和本地设置的基准目录                                                                                                                                                                                                         |
| `options.settingSources`        | [`SettingSource`](#settingsource)`[]` | 所有来源     | 要加载的文件系统来源。传入 `[]` 可跳过用户、项目和本地设置。[端点托管的策略](/docs/en/settings#settings-files) 在所有情况下都会加载。服务器托管的设置在宿主传入时取自 `serverManagedSettings`，否则从 CLI 的磁盘缓存中读取;快照不会从网络获取它们 |
| `options.managedSettings`       | `Settings`                            | `undefined`     | 由嵌入宿主提供的策略层设置。遵循与 [`managedSettings` 在 `Options`](#options) 中相同的规则,不同之处在于 `resolveSettings()` 不会执行已配置的 [`policyHelper`](/docs/en/settings#compute-managed-settings-with-a-policy-helper),因此快照可以包含实时会话会丢弃的设置                        |
| `options.serverManagedSettings` | `Settings`                            | `undefined`     | 来自 `/api/claude_code/settings` 的服务器托管设置负载。非限制性键会未经筛选地透传                                                                                                                                                                                                         |

#### 返回类型: `ResolvedSettings`

`resolveSettings()` 返回一个描述合并后设置以及每个键来源的对象。

| 属性     | 类型                                                | 描述                                                            |
| :----------- | :-------------------------------------------------- | :--------------------------------------------------------------------- |
| `effective`  | `Settings`                                          | 按优先级顺序应用所有启用的来源后的合并设置 |
| `provenance` | `Partial<Record<keyof Settings, ProvenanceEntry>>`  | 对于 `effective` 中的每个顶级键,哪个来源提供了该值 |
| `sources`    | `Array<{ source, settings, path?, policyOrigin? }>` | 每个来源的原始设置,按优先级从低到高排序     |

#### 示例

下面的示例解析某个项目目录的设置,并打印控制清理周期的来源。

```typescript theme={null}
import { resolveSettings } from "@anthropic-ai/claude-agent-sdk";

const { effective, provenance } = await resolveSettings({
  cwd: "/path/to/project",
  settingSources: ["user", "project", "local"],
});

console.log(`Cleanup period: ${effective.cleanupPeriodDays} days`);
console.log(`Set by: ${provenance.cleanupPeriodDays?.source}`);
```

## 类型

### `Options`

`query()` 函数的配置对象。

| 属性                          | 类型                                                                                                     | 默认值                                     | 描述                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| :-------------------------------- | :------------------------------------------------------------------------------------------------------- | :------------------------------------------ | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `abortController`                 | `AbortController`                                                                                        | `new AbortController()`                     | 用于取消操作的控制器                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `additionalDirectories`           | `string[]`                                                                                               | `[]`                                        | Claude 可以访问的其他目录                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| `agent`                           | `string`                                                                                                 | `undefined`                                 | 主线程的代理名称。该代理必须在 `agents` 选项或设置中定义                                                                                                                                                                                                         |
| `agents`                          | `Record<string, [`AgentDefinition`](#agentdefinition)>`                                                  | `undefined`                                 | 以编程方式定义子代理                                                                                                                                                                                                         |
| `agentProgressSummaries`          | `boolean`                                                                                                | `false`                                     | 当 `true` 时,为子代理生成单行进度摘要,并通过 [`task_progress`](#sdktaskprogressmessage) 事件的 `summary` 字段转发。适用于前台和后台子代理                                                                                                                                                                                                         |
| `allowDangerouslySkipPermissions` | `boolean`                                                                                                | `false`                                     | 启用绕过权限。使用 `permissionMode: 'bypassPermissions'` 时必需                                                                                                                                                                                                         |
| `allowedTools`                    | `string[]`                                                                                               | `[]`                                        | 无需提示即可自动批准的工具。这不会将 Claude 限制为仅使用这些工具;未列出的工具将回退到 `permissionMode` 和 `canUseTool`。使用 `disallowedTools` 来阻止工具。请参阅 [权限](/docs/en/agent-sdk/permissions#allow-and-deny-rules)                                                                                                                                                                                                         |
| `betas`                           | [`SdkBeta`](#sdkbeta)`[]`                                                                                | `[]`                                        | 启用 Beta 功能                                            |
| `canUseTool`                      | [`CanUseTool`](#canusetool)                                                                              | `undefined`                                 | 自定义权限函数，仅当 [permission flow](/docs/en/agent-sdk/permissions#how-permissions-are-evaluated) 进入提示流程时被调用。对于通过 `allowedTools`、允许规则或 `permissionMode` 自动批准的调用，不会调用此函数。`AskUserQuestion`，连接器工具 [您的组织设置为 `ask`](/docs/en/mcp#organization-controls-on-connector-tools)，以及被标记为 [`requiresUserInteraction`](/docs/en/mcp#require-approval-for-a-specific-tool) 的 MCP 工具，即使您已允许它们也会到达该函数；在 `dontAsk` 模式下这些请求会被拒绝。请参阅 [`CanUseTool`](#canusetool) 了解详情 |
| `continue`                        | `boolean`                                                                                                | `false`                                     | 继续最近的对话                                                                                                                                                                                                         |
| `cwd`                             | `string`                                                                                                 | `process.cwd()`                             | 当前工作目录                                                                                                                                                                                                         |
| `debug`                           | `boolean`                                                                                                | `false`                                     | 启用 Claude Code 进程的调试模式                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `debugFile`                       | `string`                                                                                                 | `undefined`                                 | 将调试日志写入指定文件路径。隐式启用调试模式                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| `disallowedTools`                 | `string[]`                                                                                               | `[]`                                        | 要拒绝的工具。裸名称（如 `"Bash"`）会将该工具从 Claude 的上下文中移除。带作用域的规则（如 `"Bash(rm *)"`）会保留该工具可用，并在所有权限模式（包括 `bypassPermissions`）下拒绝匹配的调用。请参阅 [权限](/docs/en/agent-sdk/permissions#allow-and-deny-rules)                                                                                                                                                                                                                                                                                                                                                                                         |
| `effort`                          | `'low' \| 'medium' \| 'high' \| 'xhigh' \| 'max'`                                                        | 模型默认值                               | 控制 Claude 在响应中投入的努力程度。与自适应思考配合使用，以引导思考深度。请参阅 [调整努力级别](/docs/en/model-config#adjust-effort-level)                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `enableFileCheckpointing`         | `boolean`                                                                                                | `false`                                     | 启用文件更改跟踪以支持回退。请参阅 [文件检查点](/docs/en/agent-sdk/file-checkpointing)                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `env`                             | `Record<string, string \| undefined>`                                                                    | `process.env`                               | 环境变量。设置后，此值将替换子进程环境，而不是与 `process.env` 合并，因此请传入 `{ ...process.env, YOUR_VAR: 'value' }` 以保留继承的变量（如 `PATH`）。有关此模式的示例，请参阅 [处理缓慢或停滞的 API 响应](#handle-slow-or-stalled-api-responses)；有关底层 CLI 读取的变量，请参阅 [环境变量](/docs/en/env-vars)。设置 `CLAUDE_AGENT_SDK_CLIENT_APP` 以在 User-Agent 标头中标识您的应用                                                                                                        |
| `executable`                      | `'bun' \| 'deno' \| 'node'`                                                                              | 自动检测                               | 要使用的 JavaScript 运行时                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| `executableArgs`                  | `string[]`                                                                                               | `[]`                                        | 传递给可执行文件的参数                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| `extraArgs`                       | `Record<string, string \| null>`                                                                         | `{}`                                        | 附加参数                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| `fallbackModel`                   | `string`                                                                                                 | `undefined`                                 | 主模型失败时使用的模型                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| `forkSession`                     | `boolean`                                                                                                | `false`                                     | 当使用 `resume` 恢复时，分叉到新的会话 ID，而不是继续原会话                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `forwardSubagentText`             | `boolean`                                                                                                | `false`                                     | 将子代理的文本和思考块作为助手和用户消息转发，并设置 `parent_tool_use_id`，以便消费者可以渲染嵌套的对话记录。默认情况下，仅发出子代理的 `tool_use` 和 `tool_result` 块                                                                                                                                                                                                                                                                                                                                                                  |
| `hooks`                           | `Partial<Record<`[`HookEvent`](#hookevent)`, `[`HookCallbackMatcher`](#hookcallbackmatcher)`[]>>`        | `{}`                                        | 事件的 Hook 回调                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `includeHookEvents`               | `boolean`                                                                                                | `false`                                     | 在消息流中为每个 hook 事件包含 hook 生命周期事件，即 [`SDKHookStartedMessage`](#sdkhookstartedmessage)、[`SDKHookProgressMessage`](#sdkhookprogressmessage) 和 [`SDKHookResponseMessage`](#sdkhookresponsemessage)。`SessionStart` 和 `Setup` hook 的生命周期事件始终会被包含，无需此选项                                                                                                                                                                                                                                                    |
| `includePartialMessages`          | `boolean`                                                                                                | `false`                                     | 包含部分消息事件                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `loadTimeoutMs`                   | `number`                                                                                                 | `60000`                                     | *Alpha.* 恢复物化期间每次 `sessionStore.load()` 和 `sessionStore.listSubkeys()` 调用的超时时间（毫秒）。如果适配器未在此时间窗口内完成，查询将失败而不是挂起。当未设置 `sessionStore` 时忽略此项                                                                                                                                                                                                                                                                                                                                    |
| `managedSettings`                 | `Settings`                                                                                               | `undefined`                                 | 宿主进程提供给所生成会话的策略层级设置。在部署了管理员托管设置的机器上，Claude Code 会忽略这些设置，除非管理员最高优先级的托管来源设置了 `parentSettingsBehavior: 'merge'`，并且在配置了 [`policyHelper`](/docs/en/settings#compute-managed-settings-with-a-policy-helper) 时绝不合并它们。合并后的值会经过仅限制性过滤器；[限制父级设置](/docs/en/claude-apps-gateway#restrict-parent-settings) 涵盖了过滤器允许的内容及 `allowManaged*Only` 锁                          |
| `maxBudgetUsd`                    | `number`                                                                                                 | `undefined`                                 | 当客户端成本估算达到此美元金额时停止查询。与 `total_cost_usd` 使用相同的估算值进行比较；有关准确性注意事项，请参阅 [跟踪成本和使用情况](/docs/en/agent-sdk/cost-tracking)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `maxThinkingTokens`               | `number`                                                                                                 | `undefined`                                 | *已弃用：* 请改用 `thinking`。思考过程的最大令牌数                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `maxTurns`                        | `number`                                                                                                 | `undefined`                                 | 最大代理轮次（工具调用往返）                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `mcpServers`                      | `Record<string, [`McpServerConfig`](#mcpserverconfig)>`                                                  | `{}`                                        | MCP 服务器配置                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `model`                           | `string`                                                                                                 | 默认来自 CLI                            | Claude 模型别名或完整模型名称。查看 [已接受的取值和特定于提供方的 ID](/docs/en/model-config#available-models)                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| `onElicitation`                   | `(request: ElicitationRequest, options: { signal: AbortSignal }) => Promise<ElicitationResult>`          | `undefined`                                 | 用于处理 MCP 征询请求的回调。当 MCP 服务器请求用户输入且没有钩子先处理时调用。未提供时，未处理的征询请求会自动被拒绝                                                                                                                                                                                                                                                                                                                                                                                             |
| `outputFormat`                    | `{ type: 'json_schema', schema: JSONSchema }`                                                            | `undefined`                                 | 定义代理结果的输出格式。详见 [结构化输出](/docs/en/agent-sdk/structured-outputs)。                                                                                                                                                                                                                                                                                                                                                                                   |
| `outputStyle`                     | `string`                                                                                                 | `undefined`                        | 不是 `Options` 字段。请在内联 [`settings`](/docs/en/settings) 对象或设置文件中设置 `outputStyle`。请参阅 [激活输出样式](/docs/en/agent-sdk/modifying-system-prompts#activate-an-output-style)                     |
| `pathToClaudeCodeExecutable`      | `string`                                                                                                 | 从捆绑的原生二进制文件自动解析    | Claude Code 可执行文件的路径。仅当安装期间跳过可选依赖项或您的平台不在受支持集合中时才需要                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `permissionMode`                  | [`PermissionMode`](#permissionmode)                                                                      | `'default'`                                 | 会话的权限模式                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| `permissionPromptToolName`        | `string`                                                                                                 | `undefined`                                 | 用于权限提示的 MCP 工具名称                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `persistSession`                  | `boolean`                                                                                                | `true`                                      | 当 `false` 时，禁用会话到磁盘的持久化。会话之后无法恢复                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `planModeInstructions`            | `string`                                                                                                 | `undefined`                                 | 计划模式的自定义工作流指令。当 `permissionMode` 为 `'plan'` 时，此字符串将替换默认的计划模式工作流主体。CLI 仍会用只读强制执行前言和 ExitPlanMode 协议页脚将其包装                                                                                                                                                                                                                                                                                                                                                         |
| `plugins`                         | [`SdkPluginConfig`](#sdkpluginconfig)`[]`                                                                | `[]`                                        | 从本地路径加载自定义插件。详情请参阅 [插件](/docs/en/agent-sdk/plugins)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| `promptSuggestions`               | `boolean`                                                                                                | `false`                                     | 启用提示建议。每轮结束后发出一条 `prompt_suggestion` 消息，包含预测的下一个用户提示                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `resume`                          | `string`                                                                                                 | `undefined`                                 | 要恢复的会话 ID                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `resumeSessionAt`                 | `string`                                                                                                 | `undefined`                                 | 在特定消息 UUID 处恢复会话                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| `sandbox`                         | [`SandboxSettings`](#sandboxsettings)                                                                    | `undefined`                                 | 以编程方式配置沙箱行为。详见 [沙箱设置](#sandboxsettings)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `sessionId`                       | `string`                                                                                                 | 自动生成                              | 为会话使用特定 UUID，而不是自动生成一个                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| `sessionStore`                    | [`SessionStore`](/docs/en/agent-sdk/session-storage#the-sessionstore-interface)                               | `undefined`                                 | 将会话记录镜像到外部后端，以便任何主机都可以恢复它们。请参阅 [将会话持久化到外部存储](/docs/en/agent-sdk/session-storage)                                                                                                                                                                                                         |
| `sessionStoreFlush`               | `'batched' \| 'eager'`                                                                                   | `'batched'`                                 | *Alpha 版。* `sessionStore` 的刷新模式。当未设置 `sessionStore` 时会被忽略                                                                                                                                                                                                         |
| `settings`                        | `string \| Settings`                                                                                     | `undefined`                                 | 内联的 [settings](/docs/en/settings) 对象或设置文件的路径。在 [优先级顺序](/docs/en/settings#settings-precedence) 中填充标志设置层。可在运行时通过 [`applyFlagSettings()`](#applyflagsettings) 更改                                                                                                                                                                                                         |
| `settingSources`                  | [`SettingSource`](#settingsource)`[]`                                                                    | CLI 默认值（所有来源）                  | 控制加载哪些文件系统设置。传入 `[]` 可禁用用户、项目和本地设置。[端点托管的策略](/docs/en/settings#settings-files) 无论如何都会加载；当会话在 [符合条件的配置](/docs/en/server-managed-settings#platform-availability) 上使用组织凭据进行身份验证时，将获取服务器托管的设置。请参阅 [使用 Claude Code 功能](/docs/en/agent-sdk/claude-code-features#what-settingsources-does-not-control)                                                                                                                            |
| `skills`                          | `string[] \| 'all'`                                                                                      | `undefined`                                 | 会话可用的技能。传入 `'all'` 可启用每个已发现的技能，或传入技能名称列表。设置后，SDK 会自动将 Skill 工具添加到 `allowedTools`。如果您还传入 `tools`，请在该列表中包含 `'Skill'`。请参阅 [技能](/docs/en/agent-sdk/skills) |
| `spawnClaudeCodeProcess`          | `(options: SpawnOptions) => SpawnedProcess`                                                              | `undefined`                                 | 用于生成 Claude Code 进程的自定义函数。用于在虚拟机、容器或远程环境中运行 Claude Code                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| `stderr`                          | `(data: string) => void`                                                                                 | `undefined`                                 | stderr 输出的回调                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| `strictMcpConfig`                 | `boolean`                                                                                                | `false`                                     | 仅使用 `mcpServers` 中传入的服务器，忽略项目 `.mcp.json`、用户设置、插件提供的 MCP 服务器以及 [claude.ai 连接器](/docs/en/mcp#use-mcp-servers-from-claude-ai)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| `systemPrompt`                    | `string \| { type: 'preset'; preset: 'claude_code'; append?: string; excludeDynamicSections?: boolean }` | `undefined` （最小提示）                | 系统提示配置。传入字符串以使用自定义提示，或传入 `{ type: 'preset', preset: 'claude_code' }` 以使用 Claude Code 的系统提示。使用预设对象形式时，添加 `append` 以附加额外指令进行扩展，并设置 `excludeDynamicSections: true` 将每会话上下文移入第一条用户消息，以便[跨机器更好地复用提示缓存](/docs/en/agent-sdk/modifying-system-prompts#improve-prompt-caching-across-users-and-machines)                                                                                                                  |
| `taskBudget`                      | `{ total: number }`                                                                                      | `undefined`                                 | *Alpha。* API 端的任务令牌预算。设置后，模型会被告知其剩余令牌预算，以便其合理安排工具使用节奏并在达到上限前收尾                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| `thinking`                        | [`ThinkingConfig`](#thinkingconfig)                                                                      | `{ type: 'adaptive' }` 用于受支持的模型 | 控制 Claude 的思考/推理行为。有关选项，请参见 [`ThinkingConfig`](#thinkingconfig)                                                                                                                                                                                                         |
| `title`                           | `string`                                                                                                 | `undefined`                                 | 会话的显示标题。当通过 `resume` 或 `continue` 恢复时，被恢复会话的持久化标题优先；使用 [`renameSession()`](#renamesession) 可重命名现有会话                                                                                                                                                                                                         |
| `toolAliases`                     | `Record<string, string>`                                                                                 | `undefined`                                 | 将内置工具名称映射到 MCP 工具名称，以便 Claude 调用你的 MCP 实现来替代内置工具。例如，`{ Bash: 'mcp__workspace__bash' }`                                                                                                                                                                                                         |
| `toolConfig`                      | [`ToolConfig`](#toolconfig)                                                                              | `undefined`                                 | 内置工具行为的配置。详情请参见 [`ToolConfig`](#toolconfig)                                                                                                                                                                                                         |
| `tools`                           | `string[] \| { type: 'preset'; preset: 'claude_code' }`                                                  | `undefined`                                 | 工具配置。传入工具名称数组，或使用预设以获取 Claude Code 的默认工具                                                                                                                                                                                                         |

#### 处理缓慢或停滞的 API 响应

CLI 子进程会读取多个控制 API 超时和停滞检测的环境变量。通过 `env` 选项传递它们：

```typescript theme={null}
const result = query({
  prompt: "Analyze this code",
  options: {
    env: {
      ...process.env,
      API_TIMEOUT_MS: "120000",
      CLAUDE_CODE_MAX_RETRIES: "2",
      CLAUDE_ASYNC_AGENT_STALL_TIMEOUT_MS: "120000",
    },
  },
});
```

* `API_TIMEOUT_MS`：Anthropic 客户端的单次请求超时，单位为毫秒。默认值为 `600000`。适用于主循环和所有子代理。
* `CLAUDE_CODE_MAX_RETRIES`：API 最大重试次数。默认值为 `10`，上限为 `15`。每次重试都有自己的 `API_TIMEOUT_MS` 时间窗口，因此最坏情况下的耗时大约为 `API_TIMEOUT_MS × (CLAUDE_CODE_MAX_RETRIES + 1)` 加上退避时间。对于需要等待更长时间故障的无人值守运行，请设置 `CLAUDE_CODE_RETRY_WATCHDOG=1`：它会无限期重试容量错误，并且 {/* min-version: 2.1.199 */}自 Claude Code v2.1.199 起，将其他临时错误的默认值提高到 `300`，并移除了该变量的上限。
* `CLAUDE_ASYNC_AGENT_STALL_TIMEOUT_MS`：针对使用 `run_in_background` 启动的子代理的停滞看门狗。默认值为 `600000`。每个流事件都会重置计时；发生停滞时，它会中止子代理，将任务标记为失败，并将错误连同任何部分结果一起上报给父级。不适用于同步子代理。
* `CLAUDE_ENABLE_STREAM_WATCHDOG` 配合 `CLAUDE_STREAM_IDLE_TIMEOUT_MS`：当响应头已到达但响应体停止流式传输时中止请求。该看门狗默认对所有提供商启用；设置 `CLAUDE_ENABLE_STREAM_WATCHDOG=0` 可禁用它。`CLAUDE_STREAM_IDLE_TIMEOUT_MS` 默认值为 `300000`，并以该值作为下限。被中止的请求会进入正常的重试流程。

### `Query` 对象

由 `query()` 函数返回的接口。

```typescript theme={null}
interface Query extends AsyncGenerator<SDKMessage, void> {
  interrupt(): Promise<SDKControlInterruptResponse | undefined>;
  rewindFiles(
    userMessageId: string,
    options?: { dryRun?: boolean }
  ): Promise<RewindFilesResult>;
  setPermissionMode(mode: PermissionMode): Promise<void>;
  setModel(model?: string): Promise<void>;
  setMaxThinkingTokens(maxThinkingTokens: number | null): Promise<void>;
  applyFlagSettings(settings: { [K in keyof Settings]?: Settings[K] | null }): Promise<void>;
  initializationResult(): Promise<SDKControlInitializeResponse>;
  reinitialize(): Promise<SDKControlInitializeResponse>;
  supportedCommands(): Promise<SlashCommand[]>;
  supportedModels(): Promise<ModelInfo[]>;
  supportedAgents(): Promise<AgentInfo[]>;
  mcpServerStatus(): Promise<McpServerStatus[]>;
  accountInfo(): Promise<AccountInfo>;
  reconnectMcpServer(serverName: string): Promise<void>;
  toggleMcpServer(serverName: string, enabled: boolean): Promise<void>;
  setMcpServers(servers: Record<string, McpServerConfig>): Promise<McpSetServersResult>;
  streamInput(stream: AsyncIterable<SDKUserMessage>): Promise<void>;
  stopTask(taskId: string): Promise<void>;
  close(): void;
}
```

#### 方法

| 方法                                 | 描述                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| :------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `interrupt()`                          | 中断查询。仅在流式输入模式下可用。{/* min-version: 2.1.205 */}当 CLI 在 [`SDKSystemMessage.capabilities`](#sdksystemmessage) 中通告 `interrupt_receipt_v1` 能力时，解析为一个 [`SDKControlInterruptResponse`](#sdkcontrolinterruptresponse)，其中列出了在中断后存活的排队消息。在 v2.1.205 之前的 CLI 上解析为 `undefined`                                                                         |
| `rewindFiles(userMessageId, options?)` | 将文件恢复到指定用户消息时的状态。传递 `{ dryRun: true }` 以预览更改。需要 `enableFileCheckpointing: true`。请参阅 [文件检查点](/docs/en/agent-sdk/file-checkpointing)                                                                                                                                                                                                                                                                |
| `setPermissionMode()`                  | 更改权限模式（仅在流式输入模式下可用）                                                                                                                                                                                                                                                                                                                                                                                                         |
| `setModel()`                           | 更改模型（仅在流式输入模式下可用）                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `setMaxThinkingTokens()`               | *已弃用：* 请改用 `thinking` 选项。更改最大思考令牌数。传入 `null` 会将思考重置为会话默认值：清除会话中途的覆盖设置，并且对于已禁用思考的会话，思考将保持关闭状态                                                                                                                                                                                                                                    |
| `applyFlagSettings(settings)`          | 在运行时将设置合并到会话的标志设置层（仅在流式输入模式下可用）。参见 [`applyFlagSettings()`](#applyflagsettings)                                                                                                                                                                                                                                                                                                                                                                                                          |
| `initializationResult()`               | 返回完整的初始化结果，包括支持的命令、模型、账户信息和输出样式配置                                                                                                                                                                                                                                                                                                                                                                                                         |
| `reinitialize()`                       | {/* min-version: 2.1.195 */}向正在运行的 CLI 重新发送 `initialize` 控制请求，并返回最新结果而非缓存的首次连接结果。在传输中断后使用它，例如在断开连接后重新附加到会话，以便待处理的权限请求能够再次到达你的 `canUseTool` 回调。请使回调按请求 ID 保持幂等，因为响应丢失的请求会被重新派发。需要 Claude Code v2.1.195 或更高版本 |
| `supportedCommands()`                  | 返回可用的斜杠命令                                                                                                                                                                                                                                                                                                                                                                                                                              |
| `supportedModels()`                    | 返回带显示信息的可用模型                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| `supportedAgents()`                    | 返回可用子代理，格式为 [`AgentInfo`](#agentinfo)`[]`                                                                                                                                                                                                                                                                                                                                                                                                         |
| `mcpServerStatus()`                    | 返回已连接 MCP 服务器的状态                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| `accountInfo()`                        | 返回账户信息                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| `reconnectMcpServer(serverName)`       | 按名称重新连接 MCP 服务器                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| `toggleMcpServer(serverName, enabled)` | 按名称启用或禁用 MCP 服务器                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| `setMcpServers(servers)`               | 动态替换此会话的 MCP 服务器集合。返回哪些服务器被添加和移除，以及任何错误。{/* min-version: 2.1.210 */}该调用会保留它未命名的插件提供的服务器；命名某个插件提供的服务器则会替换它。Promise 会在新添加的 stdio、HTTP 和 SSE 服务器连接或失败后解析，因此来自已连接服务器的工具可在下一轮使用。                                                                             |
| `streamInput(stream)`                  | 将输入消息流式传输到查询,以进行多轮对话                                                                                                                                                                                                                                                                                                                                                                                                              |
| `stopTask(taskId)`                     | 按 ID 停止正在运行的后台任务                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| `close()`                              | 关闭查询并终止底层进程。强制结束查询并清理所有资源                                                                                                                                                                                                                                                                                                                                                                  |

#### `applyFlagSettings()`

在不重启查询的情况下更改正在运行会话上的 [settings](/docs/en/settings)。当某个没有专用设置器的配置项需要在会话中途更改时,请使用它,例如在代理读取不受信任的输入后收紧 `permissions`。`setModel()` 和 `setPermissionMode()` 是这两个键的专用设置器;`applyFlagSettings()` 是通用形式,接受设置键的任意子集,在此处传递 `model` 的行为与 `setModel()` 相同。

只有部分键会在会话中途生效:

* **在下一轮生效**:`effortLevel`、`ultracode`、`permissions`、`hooks`、`skillOverrides`、`fastMode`、`agent`。切换 `agent` 还会在下一轮应用该代理的模型覆盖、钩子(hooks)和系统提示词。
* **在当前轮次中生效**:`model`。{/* min-version: 2.1.212 */}如果你在 Claude 处理某一轮次时切换 `model`,Claude 正在生成的响应会在旧模型上完成,而该轮次的其余部分——从 Claude Code 对模型的下一次调用开始——将使用新模型。子代理保留其自己的模型。在 v2.1.212 之前,轮次中切换会等待到下一轮才生效。
* **在会话中途无效**:系统提示词选项。这些选项在启动时解析一次,因此即使调用成功,正在运行的会话仍会保留原始值。要更改它们,请启动新会话。

`effortLevel` 接受一个 [effort level](/docs/en/model-config#adjust-effort-level) 名称。它还接受 `"ultracode"`,该值会以 `xhigh` effort 运行会话并开启 [ultracode](/docs/en/workflows#let-claude-decide-with-ultracode)。`Settings` 类型声明的 `effortLevel` 不包含该值,因此在 TypeScript 中请传递等效的 `{ ultracode: true }`。{/* min-version: 2.1.203 */}`ultracode` 值需要 Claude Code v2.1.203 或更高版本,并且仅被 `applyFlagSettings()` 接受,设置文件中的 `effortLevel` 键不接受该值。

这些值会被写入 flag-settings(标志设置)层,即 `query()` 的内联 `settings` 选项在启动时填充的同一层。标志设置在 [settings precedence order](/docs/en/settings#settings-precedence) 中接近顶端:它们覆盖用户、项目和本地设置,只有托管策略设置可以覆盖它们。这与 [页面内优先级章节](#settings-precedence) 所称的编程选项属于同一层级。

连续调用会对顶层键进行浅合并。第二次调用传入 `{ permissions: {...} }` 时，会整体替换上一次调用中的整个 `permissions` 对象，而不是对其进行深合并。若要清除标志层中的某个键并回退到优先级较低的来源，请为该键传入 `null`。传入 `undefined` 没有任何效果，因为 JSON 序列化会将其丢弃。

仅在流式输入模式下可用，与 `setModel()` 和 `setPermissionMode()` 的限制相同。

下面的示例在会话中途切换活动模型，然后清除覆盖设置，使模型回退到用户或项目设置中指定的值。

```typescript theme={null}
const q = query({ prompt: messageStream });

// Override the model for the rest of the session
await q.applyFlagSettings({ model: "claude-opus-4-6" });

// Later: clear the override and fall back to lower-precedence settings
await q.applyFlagSettings({ model: null });
```

<Note>
  `applyFlagSettings()` 仅适用于 TypeScript。Python SDK 没有暴露等效方法。
</Note>

### `WarmQuery`

由 [`startup()`](#startup) 返回的句柄。子进程已经生成并完成初始化，因此对此句柄调用 `query()` 会将提示直接写入一个已就绪的进程，没有任何启动延迟。

```typescript theme={null}
interface WarmQuery extends AsyncDisposable {
  query(prompt: string | AsyncIterable<SDKUserMessage>): Query;
  close(): void;
}
```

#### 方法

| 方法          | 描述                                                                                                               |
| :-------------- | :------------------------------------------------------------------------------------------------------------------------ |
| `query(prompt)` | 向预热的子进程发送提示并返回一个 [`Query`](#query-object)。每个 `WarmQuery` 只能调用一次 |
| `close()`       | 在不发送提示的情况下关闭子进程。用于丢弃不再需要的预热查询                  |

`WarmQuery` 实现了 `AsyncDisposable`，因此可以与 `await using` 一起使用以实现自动清理。

### `SDKControlInitializeResponse`

`initializationResult()` 的返回类型。包含会话初始化数据。

```typescript theme={null}
type SDKControlInitializeResponse = {
  commands: SlashCommand[];
  agents: AgentInfo[];
  output_style: string;
  available_output_styles: string[];
  models: ModelInfo[];
  account: AccountInfo;
  fast_mode_state?: "off" | "cooldown" | "on";
};
```

当客户端向已在运行的会话发送 `initialize` 时，控制响应包装器还会携带一个可选的 `pending_permission_requests` 数组。该字段位于响应包装器本身上，而不在上述的 `SDKControlInitializeResponse` 负载中。每个条目都是一条完整的 `control_request` 消息，其 `{ type: "control_request", request_id, request }` 结构与会话运行期间为权限请求流式发送的结构相同。

这些是在客户端连接之前发出、且仍在等待回复的请求。SDK 会为你读取该数组，并将每个条目分派给你的 [`canUseTool`](#canusetool) 回调，这与 [`reinitialize()`](#query-object) 在传输中断后触发的重投递相同。请以幂等方式处理重复的请求 ID，因为某个条目可能会重复回调在连接断开前已经接收过的请求。

### `SDKControlInterruptResponse`

中断回执：在 [`SDKSystemMessage.capabilities`](#sdksystemmessage) 中声明了 `interrupt_receipt_v1` 能力的 CLI 上，[`interrupt()`](#query-object) 解析得到的值。要求 Claude Code v2.1.205 或更高版本。更早的 CLI 会以空的成功负载响应中断，因此 `interrupt()` 解析为 `undefined`。

```typescript theme={null}
type SDKControlInterruptResponse = {
  still_queued: string[];
};
```

`still_queued` 列出了在中断后仍然存活的用户消息的 UUID：仍在队列中的消息，加上任何已被取出准备用于下一轮但中止操作尚未能触及的批次。除非你先取消，否则每一条都会在中断之后作为独立的一轮运行。使用该回执来决定是否需要重发任何内容；重发已在列表中的消息会产生重复的一轮。

解读该列表时请注意以下事项：

* 只有入队时带有 UUID 的消息才会出现。空数组并不意味着没有其他内容会运行。
* 仅列出主线程消息。发往子代理的消息不在范围内。
* 该列表可能包含你的客户端从未发送过的 UUID，例如 [定时任务](/docs/en/scheduled-tasks) 触发器。对于你不认识的 UUID，应忽略它们，而不是将其视为错误。

回执是在中断被处理的那一刻拍摄的快照，并且在干净的中断中，它先于被中断那一轮的 [`SDKResultMessage`](#sdkresultmessage) 到达。请读取回执，而不是在该结果之后再检查队列：循环会立即开始下一个排队的轮次，因此你在结果之后检查到的队列已经发生了变化。

### `AgentDefinition`

以编程方式定义的子代理的配置。

```typescript theme={null}
type AgentDefinition = {
  description: string;
  tools?: string[];
  disallowedTools?: string[];
  prompt: string;
  model?: string;
  mcpServers?: AgentMcpServerSpec[];
  skills?: string[];
  initialPrompt?: string;
  maxTurns?: number;
  background?: boolean;
  memory?: "user" | "project" | "local";
  effort?: "low" | "medium" | "high" | "xhigh" | "max" | number;
  permissionMode?: PermissionMode;
  criticalSystemReminder_EXPERIMENTAL?: string;
};
```

| 字段                                 | 必填 | 描述                                                                                                                                                                                                                    |
| :------------------------------------ | :------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `description`                         | 是      | 关于何时使用此代理的自然语言描述                                                                                                                                                                             |
| `tools`                               | 否       | 允许使用的工具名称数组。如果省略，则继承所有 [子代理可用的工具](/docs/en/sub-agents#available-tools)。要将技能预加载到代理的上下文中，请使用 `skills` 字段，而不是在此处列出 `'Skill'`       |
| `disallowedTools`                     | 否       | 要显式禁止此代理使用的工具名称数组。也接受 MCP 服务器级别的模式：`mcp__server` 或 `mcp__server__*` 会移除该服务器的所有工具，`mcp__*` 会移除任何服务器的所有 MCP 工具 |
| `prompt`                              | 是      | 该代理的系统提示词                                                                                                                                                                                                           |
| `model`                               | 否       | 此代理的模型覆盖。接受别名，例如 `'fable'`、`'opus'`、`'sonnet'`、`'haiku'`、`'inherit'`，或完整的模型 ID。如果省略或为 `'inherit'`，则使用主模型                                                |
| `mcpServers`                          | 否       | 此代理的 MCP 服务器规范                                                                                                                                                                                           |
| `skills`                              | 否       | 要预加载到代理上下文中的技能名称数组                                                                                                                                                                             |
| `initialPrompt`                       | 否       | 当此代理作为主线程代理运行时，自动作为第一个用户轮次提交                                                                                                                                                |
| `maxTurns`                            | 否       | 停止前的最大代理轮次（API 往返）数                                                                                                                                                                  |
| `background`                          | 否       | 调用时将此代理作为非阻塞后台任务运行                                                                                                                                                                      |
| `memory`                              | 否       | 此代理的内存来源：`'user'`、`'project'` 或 `'local'`                                                                                                                                                                  |
| `effort`                              | 否       | 此代理的推理努力程度。接受命名级别或整数                                                                                                                                                         |
| `permissionMode`                      | 否       | 此代理内工具执行的权限模式。参见 [`PermissionMode`](#permissionmode)                                                                                                                                      |
| `criticalSystemReminder_EXPERIMENTAL` | 否       | 实验性：添加到系统提示中的关键提醒                                                                                                                                                                         |

### `AgentMcpServerSpec`

指定子代理可用的 MCP 服务器。可以是服务器名称（引用父级 `mcpServers` 配置中服务器的字符串），也可以是将服务器名称映射到配置的内联服务器配置记录。

```typescript theme={null}
type AgentMcpServerSpec = string | Record<string, McpServerConfigForProcessTransport>;
```

其中 `McpServerConfigForProcessTransport` 为 `McpStdioServerConfig | McpSSEServerConfig | McpHttpServerConfig | McpSdkServerConfig`。

### `SettingSource`

控制 SDK 从哪些基于文件系统的配置来源加载设置。

```typescript theme={null}
type SettingSource = "user" | "project" | "local";
```

| 值       | 描述                                     | 位置                      |
| :---------- | :---------------------------------------------- | :---------------------------- |
| `'user'`    | 全局用户设置                            | `~/.claude/settings.json`     |
| `'project'` | 共享项目设置（受版本控制）    | `.claude/settings.json`       |
| `'local'`   | 本地项目设置（不受版本控制） | `.claude/settings.local.json` |

#### 默认行为

当省略 `settingSources` 或设为 `undefined` 时，`query()` 会加载与 Claude Code CLI 相同的文件系统设置：用户级、项目级和本地级。[端点管理的策略](/docs/en/settings#settings-files) 在所有情况下都会被加载；当会话使用组织凭据在[符合条件的配置](/docs/en/server-managed-settings#platform-availability)上进行身份验证时，会获取服务器管理的设置。有关无论此选项如何都会被读取的输入以及如何禁用它们，请参阅[settingSources 不控制的内容](/docs/en/agent-sdk/claude-code-features#what-settingsources-does-not-control)。

#### 为什么使用 settingSources

**禁用文件系统设置：**

```typescript theme={null}
// Do not load user, project, or local settings from disk
const result = query({
  prompt: "Analyze this code",
  options: { settingSources: [] }
});
```

**显式加载所有文件系统设置：**

```typescript theme={null}
const result = query({
  prompt: "Analyze this code",
  options: {
    settingSources: ["user", "project", "local"] // Load all settings
  }
});
```

**仅加载特定的设置来源：**

```typescript theme={null}
// Load only project settings, ignore user and local
const result = query({
  prompt: "Run CI checks",
  options: {
    settingSources: ["project"] // Only .claude/settings.json
  }
});
```

**测试和 CI 环境：**

```typescript theme={null}
// Ensure consistent behavior in CI by excluding local settings
const result = query({
  prompt: "Run tests",
  options: {
    settingSources: ["project"], // Only team-shared settings
    permissionMode: "bypassPermissions"
  }
});
```

**仅限 SDK 的应用程序：**

```typescript theme={null}
// Define everything programmatically.
// Pass [] to opt out of filesystem setting sources.
const result = query({
  prompt: "Review this PR",
  options: {
    settingSources: [],
    agents: {
      /* ... */
    },
    mcpServers: {
      /* ... */
    },
    allowedTools: ["Read", "Grep", "Glob"]
  }
});
```

**加载 CLAUDE.md 项目说明：**

```typescript theme={null}
// Load project settings to include CLAUDE.md files
const result = query({
  prompt: "Add a new feature following project conventions",
  options: {
    systemPrompt: {
      type: "preset",
      preset: "claude_code" // Use Claude Code's system prompt
    },
    settingSources: ["project"], // Loads CLAUDE.md from project directory
    allowedTools: ["Read", "Write", "Edit"]
  }
});
```

#### 设置优先级

当加载多个来源时，设置将按以下优先级合并（从高到低）：

1. 本地设置（`.claude/settings.local.json`）
2. 项目设置（`.claude/settings.json`）
3. 用户设置（`~/.claude/settings.json`）

诸如 `agents`、`allowedTools` 和 `settings` 之类的编程选项会覆盖用户级、项目级和本地级文件系统设置。托管策略设置的优先级高于编程选项。

### `PermissionMode`

```typescript theme={null}
type PermissionMode =
  | "default" // Standard permission behavior
  | "acceptEdits" // Auto-accept file edits
  | "bypassPermissions" // Bypass permission checks; explicit ask rules still prompt
  | "plan" // Planning mode - explore without editing
  | "dontAsk" // Don't prompt for permissions, deny if not pre-approved
  | "auto"; // Model classifier approves or denies permission prompts
```

### `CanUseTool`

用于控制工具使用情况的自定义权限函数类型。

该函数是交互式权限提示的 SDK 替代方案：只有当[权限评估流程](/docs/en/agent-sdk/permissions#how-permissions-are-evaluated)解析为提示时才会调用它。已被 `allowedTools` 条目、设置允许规则或权限模式（如 `acceptEdits` 或 `bypassPermissions`）批准的工具调用永远不会触发它。若要拦截每个工具调用，请改用 [`PreToolUse` 钩子](/docs/en/agent-sdk/hooks)。

`AskUserQuestion`、标记为 [`requiresUserInteraction`](/docs/en/mcp#require-approval-for-a-specific-tool) 的 MCP 工具，以及[你的组织设置为 `ask`](/docs/en/mcp#organization-controls-on-connector-tools) 的连接器工具，即使有匹配的允许规则，也会到达该函数。在 `dontAsk` 模式下，这些调用会被直接拒绝，而不调用该函数。

```typescript theme={null}
type CanUseTool = (
  toolName: string,
  input: Record<string, unknown>,
  options: {
    signal: AbortSignal;
    suggestions?: PermissionUpdate[];
    blockedPath?: string;
    decisionReason?: string;
    toolUseID: string;
    agentID?: string;
    requestId: string;
  }
) => Promise<PermissionResult | null>;
```

| 选项           | 类型                                        | 描述                                                                                                                                                                                                                                                                                                                                                                                                  |
| :--------------- | :------------------------------------------ | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `signal`         | `AbortSignal`                               | 如果应该中止该操作，则会发出信号                                                                                                                                                                                                                                                                                                                                                          |
| `suggestions`    | [`PermissionUpdate`](#permissionupdate)`[]` | 建议的权限更新，这样用户就不会再收到此工具的提示。Bash 提示包含一个带有 `localSettings` [destination](#permissionupdatedestination) 的建议，因此在 `updatedPermissions` 中返回它会把规则写入 `.claude/settings.local.json` 并跨会话持久保留。|
| `blockedPath`    | `string`                                    | 触发权限请求的文件路径（如果适用）                                                                                                                                                                                                                                                                                                                                                                   |
| `decisionReason` | `string`                                    | 说明触发此权限请求的原因                                                                                                                                                                                                                                                                                                                                                                                   |
| `toolUseID`      | `string`                                    | 助手消息中此特定工具调用的唯一标识符                                                                                                                                                                                                                                                                                                                                                           |
| `agentID`        | `string`                                    | 如果在子代理内运行，则为该子代理的 ID                                                                                                                                                                                                                                                                                                                                                                                    |
| `requestId`      | `string`                                    | `control_request` 封套的 `request_id`。你的应用程序在 SDK 之外发送的 `control_response`（例如签名的 HTTP POST）必须回显此值，以便 Claude Code 进程可以将回复与请求匹配                                                                                   |

回调通常通过返回一个 [`PermissionResult`](#permissionresult) 来解析请求，SDK 会将其作为 `control_response` 写回其传输通道。仅当你的应用程序已经通过自己的渠道为此请求发送了 `control_response`（并回显 `requestId`）时，才返回 `null`；此时 SDK 会跳过向传输通道写入响应。在任何其他情况下返回 `null` 都会导致工具调用无限期阻塞，因为永远不会发送任何 `control_response`，而权限提示不会超时。

`requestId` 选项和 `null` 返回值需要 Claude Code v2.1.199 或更高版本。

### `PermissionResult`

权限检查的结果。

```typescript theme={null}
type PermissionResult =
  | {
      behavior: "allow";
      updatedInput?: Record<string, unknown>;
      updatedPermissions?: PermissionUpdate[];
      toolUseID?: string;
    }
  | {
      behavior: "deny";
      message: string;
      interrupt?: boolean;
      toolUseID?: string;
    };
```

### `ToolConfig`

内置工具行为的配置。

```typescript theme={null}
type ToolConfig = {
  askUserQuestion?: {
    previewFormat?: "markdown" | "html";
  };
};
```

| 字段                           | 类型                   | 描述                                                                                                                                                                   |
| :------------------------------ | :--------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `askUserQuestion.previewFormat` | `'markdown' \| 'html'` | 选择加入 `preview` 字段，位于 [`AskUserQuestion`](/docs/en/agent-sdk/user-input#question-format) 选项上，并设置其内容格式。未设置时，Claude 不会发出预览 |

### `McpServerConfig`

MCP 服务器的配置。

```typescript theme={null}
type McpServerConfig =
  | McpStdioServerConfig
  | McpSSEServerConfig
  | McpHttpServerConfig
  | McpSdkServerConfigWithInstance;
```

#### `McpStdioServerConfig`

```typescript theme={null}
type McpStdioServerConfig = {
  type?: "stdio";
  command: string;
  args?: string[];
  env?: Record<string, string>;
};
```

#### `McpSSEServerConfig`

```typescript theme={null}
type McpSSEServerConfig = {
  type: "sse";
  url: string;
  headers?: Record<string, string>;
};
```

#### `McpHttpServerConfig`

```typescript theme={null}
type McpHttpServerConfig = {
  type: "http";
  url: string;
  headers?: Record<string, string>;
};
```

#### `McpSdkServerConfigWithInstance`

```typescript theme={null}
type McpSdkServerConfigWithInstance = {
  type: "sdk";
  name: string;
  instance: McpServer;
};
```

#### `McpClaudeAIProxyServerConfig`

```typescript theme={null}
type McpClaudeAIProxyServerConfig = {
  type: "claudeai-proxy";
  url: string;
  id: string;
};
```

### `SdkPluginConfig`

在 SDK 中加载插件的配置。

```typescript theme={null}
type SdkPluginConfig = {
  type: "local";
  path: string;
  skipMcpDiscovery?: boolean;
};
```

| 字段              | 类型      | 描述                                                                                                                                                                                                   |
| :----------------- | :-------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `type`             | `'local'` | 必须为 `'local'`（目前仅支持本地插件）                                                                                                                                                    |
| `path`             | `string`  | 插件目录的绝对路径或相对路径                                                                                                                                                             |
| `skipMcpDiscovery` | `boolean` | 当为 `true` 时，SDK 会从该插件加载技能、钩子、代理和命令，但不会读取其 `.mcp.json` 或清单 `mcpServers`。当你的应用拥有该插件的 MCP 连接时，请设置此项。 |

**示例：**

```typescript theme={null}
plugins: [
  { type: "local", path: "./my-plugin" },
  { type: "local", path: "/absolute/path/to/plugin" }
];
```

有关创建和使用插件的完整信息，请参阅 [插件](/docs/en/agent-sdk/plugins)。

## 消息类型

### `SDKMessage`

查询可能返回的所有消息的联合类型。

```typescript theme={null}
type SDKMessage =
  | SDKAssistantMessage
  | SDKUserMessage
  | SDKUserMessageReplay
  | SDKResultMessage
  | SDKSystemMessage
  | SDKPartialAssistantMessage
  | SDKCompactBoundaryMessage
  | SDKStatusMessage
  | SDKLocalCommandOutputMessage
  | SDKHookStartedMessage
  | SDKHookProgressMessage
  | SDKHookResponseMessage
  | SDKPluginInstallMessage
  | SDKToolProgressMessage
  | SDKAuthStatusMessage
  | SDKTaskNotificationMessage
  | SDKTaskStartedMessage
  | SDKTaskProgressMessage
  | SDKTaskUpdatedMessage
  | SDKBackgroundTasksChangedMessage
  | SDKThinkingTokensMessage
  | SDKSessionStateChangedMessage
  | SDKWorkerShuttingDownMessage
  | SDKCommandsChangedMessage
  | SDKNotificationMessage
  | SDKFilesPersistedEvent
  | SDKToolUseSummaryMessage
  | SDKMemoryRecallMessage
  | SDKRateLimitEvent
  | SDKElicitationCompleteMessage
  | SDKPermissionDeniedMessage
  | SDKPromptSuggestionMessage
  | SDKAPIRetryMessage
  | SDKMirrorErrorMessage
  | SDKInformationalMessage
  | SDKConversationResetMessage;
```

### `SDKAssistantMessage`

助手响应消息。

```typescript theme={null}
type SDKAssistantMessage = {
  type: "assistant";
  uuid: UUID;
  session_id: string;
  message: BetaMessage; // From Anthropic SDK
  parent_tool_use_id: string | null;
  error?: SDKAssistantMessageError;
  timestamp?: string;
};
```

`message` 字段是来自 Anthropic SDK 的 [`BetaMessage`](https://platform.claude.com/docs/en/api/messages/create)。它包含诸如 `id`、`content`、`model`、`stop_reason` 和 `usage` 之类的字段。

`SDKAssistantMessageError` 是以下之一：`'authentication_failed'`、`'oauth_org_not_allowed'`、`'billing_error'`、`'rate_limit'`、`'overloaded'`、`'invalid_request'`、`'model_not_found'`、`'server_error'`、`'max_output_tokens'` 或 `'unknown'`。`'model_not_found'` 表示所选模型不存在，或对你的账户或部署不可用。`'overloaded'` 表示 API 返回了 529，因为服务器已满负荷，这与 `'rate_limit'` 不同，后者是针对你的配额的 429。

`timestamp` 是消息内容在产生它的进程上完成生成的 ISO 8601 时间。该值来自那台机器的时钟，因此仅用于显示，不要按它对消息排序。一个 API 回合可以产生多个共享同一 `message.id` 的助手消息，每个消息都有自己的 `timestamp`。当该字段缺失时，回退到你收到消息的时间。

### `SDKUserMessage`

用户输入消息。

```typescript theme={null}
type SDKUserMessage = {
  type: "user";
  uuid?: UUID;
  session_id?: string;
  message: MessageParam; // From Anthropic SDK
  parent_tool_use_id: string | null;
  isSynthetic?: boolean;
  shouldQuery?: boolean;
  tool_use_result?: unknown;
  origin?: SDKMessageOrigin;
};
```

将 `shouldQuery` 设置为 `false`，可将消息附加到转录中而不触发助手回合。该消息会被保留，并合并到下一条会触发回合的用户消息中。用它来注入上下文，例如你在带外运行的命令的输出，而无需为此消耗一次模型调用。

在携带 `tool_result` 块的消息上，`tool_use_result` 是工具的结构化输出对象，而不是发送给模型的文本。它的结构取决于匹配的 `tool_use` 块所命名的工具，因此该字段的类型为 `unknown`；内置结构列在 [Tool Output Types](#tool-output-types) 下。

对于 `Agent` 工具，`tool_use_result` 是 [`AgentOutput`](#agent-2)。在 `completed` 结果上，`content` 保存子代理的报告，不含 Claude Code 附加到 `tool_result` 文本上的代理 ID 和用量尾部，因此请从 `tool_use_result` 渲染，而不是解析那段文本。

### `SDKUserMessageReplay`

带必需 UUID 的重放用户消息。

```typescript theme={null}
type SDKUserMessageReplay = {
  type: "user";
  uuid: UUID;
  session_id: string;
  message: MessageParam;
  parent_tool_use_id: string | null;
  isSynthetic?: boolean;
  tool_use_result?: unknown;
  origin?: SDKMessageOrigin;
  isReplay: true;
};
```

从会话外部注入的用户回合，即其 [`origin`](#sdkmessageorigin) 种类为 `peer` 或 `channel` 的回合，无论它是在活动回合期间送达的，还是在会话空闲时开启了新回合，都会作为重放到达流中。{/* min-version: 2.1.207 */}在 v2.1.207 之前，会话空闲时送达的注入回合不会在流上产生任何消息，只有在你重新读取转录时才会出现。

### `SDKResultMessage`

最终结果消息。

```typescript theme={null}
type SDKResultMessage =
  | {
      type: "result";
      subtype: "success";
      uuid: UUID;
      session_id: string;
      duration_ms: number;
      duration_api_ms: number;
      is_error: boolean;
      api_error_status?: number | null;
      num_turns: number;
      result: string;
      stop_reason: string | null;
      ttft_ms?: number;
      ttft_stream_ms?: number;
      total_cost_usd: number;
      usage: NonNullableUsage;
      modelUsage: { [modelName: string]: ModelUsage };
      permission_denials: SDKPermissionDenial[];
      structured_output?: unknown;
      deferred_tool_use?: { id: string; name: string; input: Record<string, unknown> };
      terminal_reason?: TerminalReason;
      fast_mode_state?: FastModeState;
      origin?: SDKMessageOrigin;
    }
  | {
      type: "result";
      subtype:
        | "error_max_turns"
        | "error_during_execution"
        | "error_max_budget_usd"
        | "error_max_structured_output_retries";
      uuid: UUID;
      session_id: string;
      duration_ms: number;
      duration_api_ms: number;
      is_error: boolean;
      num_turns: number;
      stop_reason: string | null;
      total_cost_usd: number;
      usage: NonNullableUsage;
      modelUsage: { [modelName: string]: ModelUsage };
      permission_denials: SDKPermissionDenial[];
      errors: string[];
      terminal_reason?: TerminalReason;
      fast_mode_state?: FastModeState;
      origin?: SDKMessageOrigin;
    };
```

结果上的多个字段携带了超出 `subtype` 之外的诊断细节：

* `api_error_status`：终止该会话的 API 错误的 HTTP 状态码。当该轮次在没有 API 错误的情况下结束时，此字段缺失或为 `null`。
* `ttft_ms`：首个 token 的时间（毫秒），在第一条完整助手消息到达时测量。仅在成功分支上存在。
* `ttft_stream_ms`：从响应流打开到第一个 `message_start` 流事件的时间（毫秒）。低于 `ttft_ms`；两者之间的差值是流式传输第一条消息所花费的时间。仅在成功分支上存在。
* `terminal_reason`：循环结束的原因。为 `"completed"`、`"max_turns"`、`"tool_deferred"`、`"aborted_streaming"`、`"aborted_tools"`、`"hook_stopped"`、`"stop_hook_prevented"`、`"background_requested"`、`"blocking_limit"`、`"rapid_refill_breaker"`、`"prompt_too_long"`、`"image_error"`、`"model_error"`、`"api_error"`、`"malformed_tool_use_exhausted"`、`"budget_exhausted"`、`"structured_output_retry_exhausted"`、`"tool_deferred_unavailable"` 或 `"turn_setup_failed"` 之一。
* `fast_mode_state`：为 `"on"`、`"off"` 或 `"cooldown"` 之一。

`origin` 字段转发触发此结果的用户消息的 [`SDKMessageOrigin`](#sdkmessageorigin)。当后台任务完成且 SDK 注入合成的后续轮次时，生成的 `SDKResultMessage` 携带 `origin: { kind: "task-notification" }`。检查此字段以区分响应你提示的结果与为后台任务后续轮次发出的结果，以便你可以路由或抑制后者。对于在任何用户轮次之前发出的结果（例如启动错误），此字段缺失。

当 `PreToolUse` 钩子返回 `permissionDecision: "defer"` 时，结果具有 `stop_reason: "tool_deferred"`，且 `deferred_tool_use` 携带待定工具的 `id`、`name` 和 `input`。读取此字段以在你自己的 UI 中呈现该请求，然后使用相同的 `session_id` 恢复以继续。有关完整往返流程，请参阅 [将工具调用推迟到稍后](/docs/en/hooks#defer-a-tool-call-for-later)。

### `SDKSystemMessage`

系统初始化消息。

```typescript theme={null}
type SDKSystemMessage = {
  type: "system";
  subtype: "init";
  uuid: UUID;
  session_id: string;
  agents?: string[];
  apiKeySource: ApiKeySource;
  betas?: string[];
  claude_code_version: string;
  cwd: string;
  tools: string[];
  mcp_servers: {
    name: string;
    status: string;
  }[];
  model: string;
  permissionMode: PermissionMode;
  slash_commands: string[];
  output_style: string;
  skills: string[];
  plugins: { name: string; path: string }[];
  capabilities?: string[];
};
```

{/* min-version: 2.1.205 */}

`capabilities` 数组列出了此 CLI 实现的协议行为，因此你可以进行功能检测，而不是比较 `claude_code_version` 字符串。它是一个开放集合：忽略你不认识的值，并检查你所依赖行为的特定能力。该字段需要 Claude Code v2.1.205 或更高版本，在更早的 CLI 上不存在。

| 能力             | 含义                                                                                                                                                                     |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `interrupt_receipt_v1` | [`interrupt()`](#query-object) 以一个 [`SDKControlInterruptResponse`](#sdkcontrolinterruptresponse) 回执解析，该回执列出在中断后存活的排队消息 |

### `SDKPartialAssistantMessage`

流式部分消息（仅当 `includePartialMessages` 为 true 时）。`parent_tool_use_id` 字段始终为 `null`：流事件仅为主会话发出。对于子代理归属，请使用携带 `parent_tool_use_id` 的完整消息，或启用 [`forwardSubagentText`](#options) 以将子代理文本和思考作为完整消息接收。

```typescript theme={null}
type SDKPartialAssistantMessage = {
  type: "stream_event";
  event: BetaRawMessageStreamEvent; // From Anthropic SDK
  parent_tool_use_id: string | null;
  uuid: UUID;
  session_id: string;
  ttft_ms?: number; // Time to first token in ms, present only on message_start events
};
```

### `SDKCompactBoundaryMessage`

指示会话压缩边界的消息。

```typescript theme={null}
type SDKCompactBoundaryMessage = {
  type: "system";
  subtype: "compact_boundary";
  uuid: UUID;
  session_id: string;
  compact_metadata: {
    trigger: "manual" | "auto";
    pre_tokens: number;
  };
};
```

### `SDKInformationalMessage`

由循环发出的通用文本横幅。承载非错误状态行、诸如某个 `UserPromptSubmit` 钩子阻止原因之类的钩子反馈，以及命令输出。在给定的 `level` 上将 `content` 渲染为纯文本。

```typescript theme={null}
type SDKInformationalMessage = {
  type: "system";
  subtype: "informational";
  content: string;
  level: "info" | "notice" | "suggestion" | "warning";
  tool_use_id?: string;
  prevent_continuation?: boolean;
  uuid: UUID;
  session_id: string;
};
```

### `SDKWorkerShuttingDownMessage`

在工作器正常拆除时发出，以便远程客户端能够显示工作器退出的原因，而不是等待心跳超时。该 `reason` 是由宿主 CLI 设置的简短 snake\_case 字符串，例如 `"host_exit"` 或 `"remote_control_disabled"`。仅在实时流式传输时对此采取行动。恢复的会话会重放此消息的过往实例，因此在这种情况下应忽略它们。

```typescript theme={null}
type SDKWorkerShuttingDownMessage = {
  type: "system";
  subtype: "worker_shutting_down";
  reason: string;
  uuid: UUID;
  session_id: string;
};
```

### `SDKPluginInstallMessage`

插件安装进度事件。当设置了 [`CLAUDE_CODE_SYNC_PLUGIN_INSTALL`](/docs/en/env-vars) 时发出，因此你的 Agent SDK 应用可以在首个回合之前跟踪市场插件安装。`started` 和 `completed` 状态界定了整体安装过程。`installed` 和 `failed` 状态报告各个市场并包含 `name`。

```typescript theme={null}
type SDKPluginInstallMessage = {
  type: "system";
  subtype: "plugin_install";
  status: "started" | "installed" | "failed" | "completed";
  name?: string;
  error?: string;
  uuid: UUID;
  session_id: string;
};
```

### `SDKPermissionDeniedMessage`

当权限系统在无交互提示的情况下自动拒绝某个工具调用时发出的流事件。使用它可在拒绝发生时在你的 UI 中渲染该拒绝，而不是只观察随后到来的 `is_error` 工具结果。交互式询问路径会通过 [`canUseTool`](#canusetool) 回调单独到达你的应用。由 `PreToolUse` 钩子发出的拒绝不会通过此事件报告。

此事件需要 Claude Code v2.1.136 或更高版本。

```typescript theme={null}
type SDKPermissionDeniedMessage = {
  type: "system";
  subtype: "permission_denied";
  tool_name: string;
  tool_use_id: string;
  agent_id?: string;
  decision_reason_type?: string;
  decision_reason?: string;
  message: string;
  uuid: UUID;
  session_id: string;
};
```

| 字段                  | 类型     | 描述                                                                                                              |
| ---------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------ |
| `tool_name`            | `string` | 被拒绝的工具名称                                                                                         |
| `tool_use_id`          | `string` | 此拒绝所回应的 `tool_use` 块的 ID                                                                           |
| `agent_id`             | `string` | 当被拒绝的调用源自某个子代理内部时的子代理 ID。镜像 `can_use_tool` 上的字段，用于宿主侧路由 |
| `decision_reason_type` | `string` | 作出决定的组件的判别符，例如 `"rule"`、`"mode"`、`"classifier"` 或 `"asyncAgent"`              |
| `decision_reason`      | `string` | 来自作出决定的组件的人类可读原因（如有）                                                        |
| `message`              | `string` | 在 `tool_result` 中返回给模型的拒绝消息                                                             |

### `SDKPermissionDenial`

关于被拒绝的工具使用的信息。

```typescript theme={null}
type SDKPermissionDenial = {
  tool_name: string;
  tool_use_id: string;
  tool_input: Record<string, unknown>;
};
```

### `SDKMessageOrigin`

用户角色消息的来源。它在 [`SDKUserMessage`](#sdkusermessage) 上作为 `origin` 字段出现，并被转发到相应的 [`SDKResultMessage`](#sdkresultmessage)，因此你可以判断是什么触发了某一回合。

```typescript theme={null}
type SDKMessageOrigin =
  | { kind: "human" }
  | { kind: "channel"; server: string }
  | {
      kind: "peer";
      from: string;
      name?: string;
      senderTaskId?: string;
      body?: string;
    }
  | { kind: "task-notification" }
  | { kind: "coordinator" }
  | { kind: "auto-continuation" };
```

| `kind`              | 含义                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `human`             | 来自最终用户的直接输入。如果你的应用将用户输入的内容作为用户消息转发，请将其 `origin` 显式设置为 `{ kind: "human" }`：{/* min-version: 2.1.210 */}Claude Code 会将没有 `origin` 的用户消息视为未归因，并且需要人工输入提示的检查（例如 [`ultracode` 工作流关键字](/docs/en/workflows#ask-for-a-workflow-in-your-prompt)）不会接受它。在 v2.1.210 之前，Claude Code 会将用户消息中缺失的 `origin` 视为人工输入。                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `channel`           | 到达 [channel](/docs/en/channels) 的消息。`server` 是源 MCP 服务器名称。                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| `peer`              | 来自另一个智能体的消息。对于进程内 [teammate](/docs/en/agent-teams) 通过 `SendMessage` 发送给 `main` 的情况，`from` 是队友名称，`senderTaskId` 是其任务 ID。对于跨会话对等方（例如另一个本地 Claude Code 进程），`from` 是发送方地址，且 `senderTaskId` 不存在。{/* min-version: 2.1.205 */}`name` 和 `body` 需要 Claude Code v2.1.205 或更高版本。`name` 是发送方显示名称，由 Claude Code 规范化：它会剥离 Unicode 控制、格式、代理项以及行或段落分隔符码位，然后裁剪结果，并用省略号将其限制为 64 个码位。`body` 是剥离对等信封后的解码消息正文，与模型所见内容逐字节一致。对于队友消息，`body` 始终存在；对于跨会话对等方，仅当该回合恰好是由 Claude Code 形成的一个对等信封时才存在。渲染 `name` 和 `body`，而不要重新解析消息文本。|
| `task-notification` | 在后台任务完成后注入的合成回合。请参阅 [`SDKTaskNotificationMessage`](#sdktasknotificationmessage)。                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `coordinator`       | 来自[agent 团队](/docs/en/agent-teams)中团队协调员的消息。                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| `auto-continuation` | 当会话在没有新的用户输入的情况下继续时注入的合成回合，例如触发后续提示的命令结果。                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |

## 钩子类型

有关使用钩子的综合指南（包含示例和常见模式），请参阅[钩子指南](/docs/en/agent-sdk/hooks)。

### `HookEvent`

可用的钩子事件。

```typescript theme={null}
type HookEvent =
  | "PreToolUse"
  | "PostToolUse"
  | "PostToolUseFailure"
  | "PostToolBatch"
  | "Notification"
  | "UserPromptSubmit"
  | "UserPromptExpansion"
  | "SessionStart"
  | "SessionEnd"
  | "Stop"
  | "SubagentStart"
  | "SubagentStop"
  | "PreCompact"
  | "PermissionRequest"
  | "Setup"
  | "TeammateIdle"
  | "TaskCompleted"
  | "ConfigChange"
  | "WorktreeCreate"
  | "WorktreeRemove"
  | "MessageDisplay";
```

### `HookCallback`

钩子回调函数类型。

```typescript theme={null}
type HookCallback = (
  input: HookInput, // Union of all hook input types
  toolUseID: string | undefined,
  options: { signal: AbortSignal }
) => Promise<HookJSONOutput>;
```

### `HookCallbackMatcher`

带有可选匹配器的钩子配置。

```typescript theme={null}
interface HookCallbackMatcher {
  matcher?: string;
  hooks: HookCallback[];
  timeout?: number; // Timeout in seconds for all hooks in this matcher
}
```

### `HookInput`

所有钩子输入类型的联合类型。

```typescript theme={null}
type HookInput =
  | PreToolUseHookInput
  | PostToolUseHookInput
  | PostToolUseFailureHookInput
  | PostToolBatchHookInput
  | NotificationHookInput
  | UserPromptSubmitHookInput
  | SessionStartHookInput
  | SessionEndHookInput
  | StopHookInput
  | SubagentStartHookInput
  | SubagentStopHookInput
  | PreCompactHookInput
  | PermissionRequestHookInput
  | SetupHookInput
  | TeammateIdleHookInput
  | TaskCompletedHookInput
  | ConfigChangeHookInput
  | WorktreeCreateHookInput
  | WorktreeRemoveHookInput
  | MessageDisplayHookInput;
```

### `BaseHookInput`

所有钩子输入类型都扩展的基础接口。

```typescript theme={null}
type BaseHookInput = {
  session_id: string;
  transcript_path: string;
  cwd: string;
  prompt_id?: string;
  permission_mode?: string;
  effort?: { level: string };
  agent_id?: string;
  agent_type?: string;
};
```

`prompt_id` 字段是一个 UUID，用于标识当前正在处理的用户提示。它与 OpenTelemetry 事件上的 [`prompt.id` 属性](/docs/en/monitoring-usage#event-correlation-attributes)相匹配，并且在首次用户输入之前不存在。需要 Claude Code v2.1.196 或更高版本。

#### `PreToolUseHookInput`

```typescript theme={null}
type PreToolUseHookInput = BaseHookInput & {
  hook_event_name: "PreToolUse";
  tool_name: string;
  tool_input: unknown;
  tool_use_id: string;
};
```

#### `PostToolUseHookInput`

```typescript theme={null}
type PostToolUseHookInput = BaseHookInput & {
  hook_event_name: "PostToolUse";
  tool_name: string;
  tool_input: unknown;
  tool_response: unknown;
  tool_use_id: string;
  duration_ms?: number;
};
```

#### `PostToolUseFailureHookInput`

```typescript theme={null}
type PostToolUseFailureHookInput = BaseHookInput & {
  hook_event_name: "PostToolUseFailure";
  tool_name: string;
  tool_input: unknown;
  tool_use_id: string;
  error: string;
  is_interrupt?: boolean;
  duration_ms?: number;
};
```

#### `PostToolBatchHookInput`

在批次中的每个工具调用都完成之后、下一次模型请求之前触发一次。`tool_response` 携带模型所看到的序列化 `tool_result` 内容；其形态与 `PostToolUseHookInput` 的结构化 `Output` 对象不同。

```typescript theme={null}
type PostToolBatchHookInput = BaseHookInput & {
  hook_event_name: "PostToolBatch";
  tool_calls: PostToolBatchToolCall[];
};

type PostToolBatchToolCall = {
  tool_name: string;
  tool_input: unknown;
  tool_use_id: string;
  tool_response?: unknown;
};
```

#### `NotificationHookInput`

```typescript theme={null}
type NotificationHookInput = BaseHookInput & {
  hook_event_name: "Notification";
  message: string;
  title?: string;
  notification_type: string;
};
```

#### `UserPromptSubmitHookInput`

```typescript theme={null}
type UserPromptSubmitHookInput = BaseHookInput & {
  hook_event_name: "UserPromptSubmit";
  prompt: string;
};
```

#### `SessionStartHookInput`

```typescript theme={null}
type SessionStartHookInput = BaseHookInput & {
  hook_event_name: "SessionStart";
  source: "startup" | "resume" | "clear" | "compact";
  agent_type?: string;
  model?: string;
};
```

#### `SessionEndHookInput`

```typescript theme={null}
type SessionEndHookInput = BaseHookInput & {
  hook_event_name: "SessionEnd";
  reason: ExitReason; // String from EXIT_REASONS array
};
```

#### `StopHookInput`

```typescript theme={null}
type StopHookInput = BaseHookInput & {
  hook_event_name: "Stop";
  stop_hook_active: boolean;
  last_assistant_message?: string;
  background_tasks?: BackgroundTaskSummary[];
  session_crons?: SessionCronSummary[];
};
```

#### `SubagentStartHookInput`

```typescript theme={null}
type SubagentStartHookInput = BaseHookInput & {
  hook_event_name: "SubagentStart";
  agent_id: string;
  agent_type: string;
};
```

#### `SubagentStopHookInput`

```typescript theme={null}
type SubagentStopHookInput = BaseHookInput & {
  hook_event_name: "SubagentStop";
  stop_hook_active: boolean;
  agent_id: string;
  agent_transcript_path: string;
  agent_type: string;
  last_assistant_message?: string;
  background_tasks?: BackgroundTaskSummary[];
  session_crons?: SessionCronSummary[];
};

type BackgroundTaskSummary = {
  id: string;
  type: string;
  status: string;
  description: string;
  command?: string;
  agent_type?: string;
  server?: string;
  tool?: string;
  name?: string;
};

type SessionCronSummary = {
  id: string;
  schedule: string;
  recurring: boolean;
  prompt: string;
};
```

#### `PreCompactHookInput`

```typescript theme={null}
type PreCompactHookInput = BaseHookInput & {
  hook_event_name: "PreCompact";
  trigger: "manual" | "auto";
  custom_instructions: string | null;
};
```

#### `PermissionRequestHookInput`

```typescript theme={null}
type PermissionRequestHookInput = BaseHookInput & {
  hook_event_name: "PermissionRequest";
  tool_name: string;
  tool_input: unknown;
  permission_suggestions?: PermissionUpdate[];
};
```

#### `SetupHookInput`

```typescript theme={null}
type SetupHookInput = BaseHookInput & {
  hook_event_name: "Setup";
  trigger: "init" | "maintenance";
};
```

#### `TeammateIdleHookInput`

```typescript theme={null}
type TeammateIdleHookInput = BaseHookInput & {
  hook_event_name: "TeammateIdle";
  teammate_name: string;
  /** @deprecated since v2.1.178. Carries the session-derived team name; will be removed. */
  team_name: string;
};
```

#### `TaskCompletedHookInput`

```typescript theme={null}
type TaskCompletedHookInput = BaseHookInput & {
  hook_event_name: "TaskCompleted";
  task_id: string;
  task_subject: string;
  task_description?: string;
  teammate_name?: string;
  /** @deprecated since v2.1.178. Carries the session-derived team name; will be removed. */
  team_name?: string;
};
```

#### `ConfigChangeHookInput`

```typescript theme={null}
type ConfigChangeHookInput = BaseHookInput & {
  hook_event_name: "ConfigChange";
  source:
    | "user_settings"
    | "project_settings"
    | "local_settings"
    | "policy_settings"
    | "skills";
  file_path?: string;
};
```

#### `WorktreeCreateHookInput`

```typescript theme={null}
type WorktreeCreateHookInput = BaseHookInput & {
  hook_event_name: "WorktreeCreate";
  name: string;
};
```

#### `WorktreeRemoveHookInput`

```typescript theme={null}
type WorktreeRemoveHookInput = BaseHookInput & {
  hook_event_name: "WorktreeRemove";
  worktree_path: string;
};
```

#### `MessageDisplayHookInput`

```typescript theme={null}
type MessageDisplayHookInput = BaseHookInput & {
  hook_event_name: "MessageDisplay";
  turn_id: string;
  message_id: string;
  index: number;
  final: boolean;
  delta: string;
};
```

### `HookJSONOutput`

钩子返回值。

```typescript theme={null}
type HookJSONOutput = AsyncHookJSONOutput | SyncHookJSONOutput;
```

#### `AsyncHookJSONOutput`

```typescript theme={null}
type AsyncHookJSONOutput = {
  async: true;
  asyncTimeout?: number;
};
```

#### `SyncHookJSONOutput`

```typescript theme={null}
type SyncHookJSONOutput = {
  continue?: boolean;
  suppressOutput?: boolean;
  stopReason?: string;
  decision?: "approve" | "block";
  systemMessage?: string;
  reason?: string;
  hookSpecificOutput?:
    | {
        hookEventName: "PreToolUse";
        permissionDecision?: "allow" | "deny" | "ask" | "defer";
        permissionDecisionReason?: string;
        updatedInput?: Record<string, unknown>;
        additionalContext?: string;
      }
    | {
        hookEventName: "UserPromptSubmit";
        additionalContext?: string;
      }
    | {
        hookEventName: "SessionStart";
        additionalContext?: string;
      }
    | {
        hookEventName: "Setup";
        additionalContext?: string;
      }
    | {
        hookEventName: "SubagentStart";
        additionalContext?: string;
      }
    | {
        hookEventName: "PostToolUse";
        additionalContext?: string;
        updatedToolOutput?: unknown;
        /** @deprecated Use `updatedToolOutput`, which works for all tools. */
        updatedMCPToolOutput?: unknown;
      }
    | {
        hookEventName: "PostToolUseFailure";
        additionalContext?: string;
      }
    | {
        hookEventName: "PostToolBatch";
        additionalContext?: string;
      }
    | {
        hookEventName: "Notification";
        additionalContext?: string;
      }
    | {
        hookEventName: "PermissionRequest";
        decision:
          | {
              behavior: "allow";
              updatedInput?: Record<string, unknown>;
              updatedPermissions?: PermissionUpdate[];
            }
          | {
              behavior: "deny";
              message?: string;
              interrupt?: boolean;
            };
      };
};
```

## 工具输入类型

所有内置 Claude Code 工具的输入模式文档。这些类型从 `@anthropic-ai/claude-agent-sdk` 导出，可用于类型安全的工具交互。

### `ToolInputSchemas`

所有工具输入类型的联合，从 `@anthropic-ai/claude-agent-sdk` 导出。

```typescript theme={null}
type ToolInputSchemas =
  | AgentInput
  | AskUserQuestionInput
  | BashInput
  | TaskOutputInput
  | EnterWorktreeInput
  | ExitPlanModeInput
  | FileEditInput
  | FileReadInput
  | FileWriteInput
  | GlobInput
  | GrepInput
  | ListMcpResourcesInput
  | McpInput
  | MonitorInput
  | NotebookEditInput
  | ReadMcpResourceInput
  | SubscribeMcpResourceInput
  | SubscribePollingInput
  | TaskCreateInput
  | TaskGetInput
  | TaskListInput
  | TaskStopInput
  | TaskUpdateInput
  | TodoWriteInput
  | UnsubscribeMcpResourceInput
  | UnsubscribePollingInput
  | WebFetchInput
  | WebSearchInput
  | WorkflowInput;
```

### Agent

**工具名称：** `Agent`（之前为 `Task`，仍作为别名被接受）

<Note>
  {/* min-version: 2.1.212 */}`mode` 字段已弃用，并在 Claude Code v2.1.212 或更高版本中被忽略：子代理[继承父会话的权限模式](/docs/en/agent-sdk/permissions#available-modes)，子代理定义的 [`permissionMode`](#agentdefinition) 可以覆盖它，除非父级使用 `bypassPermissions`、`acceptEdits` 或 `auto`。
</Note>

```typescript theme={null}
type AgentInput = {
  description: string;
  prompt: string;
  subagent_type?: string;
  model?: "sonnet" | "opus" | "haiku" | "fable";
  run_in_background?: boolean;
  name?: string;
  mode?: "acceptEdits" | "auto" | "bypassPermissions" | "default" | "dontAsk" | "plan";
  isolation?: "worktree" | "remote";
};
```

启动一个新代理以自主处理复杂的多步骤任务。

### AskUserQuestion

**工具名称：** `AskUserQuestion`

```typescript theme={null}
type AskUserQuestionInput = {
  questions: Array<{
    question: string;
    header: string;
    options: Array<{ label: string; description: string; preview?: string }>;
    multiSelect: boolean;
  }>;
};
```

在执行过程中向用户提出澄清问题。有关使用详情，请参阅[处理审批和用户输入](/docs/en/agent-sdk/user-input#handle-clarifying-questions)。

### Bash

**工具名称：** `Bash`

```typescript theme={null}
type BashInput = {
  command: string;
  timeout?: number; // milliseconds, max 600000; higher values are clamped to the max
  description?: string;
  run_in_background?: boolean;
  dangerouslyDisableSandbox?: boolean;
};
```

执行 Bash 命令，支持可选的超时和后台执行。工作目录在命令之间保持持久；但 shell 状态（如导出的环境变量）不会持久。

### Monitor

**工具名称：** `Monitor`

```typescript theme={null}
type MonitorInput = {
  command?: string;
  ws?: {
    url: string;
    protocols?: string[];
  };
  description: string;
  timeout_ms?: number;
  persistent?: boolean;
};
```

运行后台源并将每个事件传递给 Claude，使其无需轮询即可做出反应：`command` 运行脚本并为每行标准输出生成一个事件，`ws` 打开 WebSocket 并为每个文本帧生成一个事件。必须且只能提供 `command` 或 `ws` 之一。{/* min-version: 2.1.195 */}`ws` 源需要 Claude Code v2.1.195 或更高版本。

对于日志跟踪等会话时长的监视，请设置 `persistent: true`。当 Monitor 运行命令时，它遵循与 Bash 相同的权限规则；WebSocket 监视会单独提示审批。有关行为和提供商可用性，请参阅 [Monitor 工具参考](/docs/en/tools-reference#monitor-tool)。

### TaskOutput

**工具名称：** `TaskOutput`

```typescript theme={null}
type TaskOutputInput = {
  task_id: string;
  block: boolean;
  timeout: number;
};
```

检索正在运行或已完成的后台任务的输出。

### Edit

**工具名称：** `Edit`

```typescript theme={null}
type FileEditInput = {
  file_path: string;
  old_string: string;
  new_string: string;
  replace_all?: boolean;
};
```

在文件中执行精确的字符串替换。

### Read

**工具名称：** `Read`

```typescript theme={null}
type FileReadInput = {
  file_path: string;
  offset?: number;
  limit?: number;
  pages?: string;
};
```

从本地文件系统读取文件，包括文本、图像、PDF 和 Jupyter 笔记本。使用 `pages` 指定 PDF 页面范围（例如 `"1-5"`）。

### Write

**工具名称：** `Write`

```typescript theme={null}
type FileWriteInput = {
  file_path: string;
  content: string;
};
```

将文件写入本地文件系统，如果已存在则覆盖。

### Glob

**工具名称：** `Glob`

```typescript theme={null}
type GlobInput = {
  pattern: string;
  path?: string;
};
```

快速的文件模式匹配，适用于任何规模的代码库。

### Grep

**工具名称：** `Grep`

```typescript theme={null}
type GrepInput = {
  pattern: string;
  path?: string;
  glob?: string;
  type?: string;
  output_mode?: "content" | "files_with_matches" | "count";
  "-i"?: boolean;
  "-n"?: boolean;
  "-B"?: number;
  "-A"?: number;
  "-C"?: number;
  context?: number;
  head_limit?: number;
  offset?: number;
  multiline?: boolean;
};
```

基于 ripgrep 构建的强大搜索工具，支持正则表达式。

### TaskStop

**工具名称：** `TaskStop`

```typescript theme={null}
type TaskStopInput = {
  task_id?: string;
  shell_id?: string; // Deprecated: use task_id
};
```

按 ID 停止正在运行的后台任务或 shell。{/* min-version: 2.1.198 */}自 v2.1.198 起，`task_id` 还接受通过代理 ID 或名称指定的代理团队成员或命名后台代理。

### NotebookEdit

**工具名称：** `NotebookEdit`

```typescript theme={null}
type NotebookEditInput = {
  notebook_path: string;
  cell_id?: string;
  new_source: string;
  cell_type?: "code" | "markdown";
  edit_mode?: "replace" | "insert" | "delete";
};
```

编辑 Jupyter 笔记本文件中的单元格。

### WebFetch

**工具名称：** `WebFetch`

```typescript theme={null}
type WebFetchInput = {
  url: string;
  prompt: string;
};
```

从 URL 获取内容并使用 AI 模型进行处理。

### WebSearch

**工具名称：** `WebSearch`

```typescript theme={null}
type WebSearchInput = {
  query: string;
  allowed_domains?: string[];
  blocked_domains?: string[];
};
```

搜索网络并返回格式化的结果。

### 工作流（Workflow）

**工具名称：** `Workflow`

```typescript theme={null}
type WorkflowInput = {
  script?: string;
  name?: string;
  scriptPath?: string;
  args?: unknown;
  resumeFromRunId?: string;
};
```

运行一个 [动态工作流](/docs/en/workflows)：一个脚本，它在后台编排多个子代理并返回一个合并后的结果。`Workflow` 工具在 Agent SDK v0.3.149 及更高版本中可用。`script`、`name` 或 `scriptPath` 中至少需要提供一个。

| 字段             | 类型      | 描述                                                                                                                                                                                                                                                                          |
| ----------------- | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `script`          | `string`  | 内联工作流脚本。必须以字面量 `export const meta = { name, description }` 开头，后跟使用 `agent()`、`parallel()`、`pipeline()` 和 `phase()` 的脚本主体。`meta` 中可选的 `phases` 数组可在进度视图中将代理分组到命名阶段下 |
| `name`            | `string`  | 内置工作流的名称或保存在 `.claude/workflows/` 中的工作流名称。将被解析为脚本                                                                                                                                                                                               |
| `scriptPath`      | `string`  | 磁盘上工作流脚本文件的路径。优先于 `script` 和 `name`。每次调用都会持久化其脚本并在结果中返回该路径，因此你可以编辑该文件并使用相同的 `scriptPath` 重新调用以进行迭代                                            |
| `args`            | `unknown` | 作为全局变量 `args` 暴露给脚本的输入值，用于参数化命名工作流，例如一个研究问题或一个文件路径列表。数组和对象应以实际的 JSON 值传递，而不是 JSON 编码的字符串                                                           |
| `resumeFromRunId` | `string`  | 要恢复的先前 `Workflow` 调用的运行 ID。输入未变化的已完成 `agent()` 调用将返回缓存结果；只有发生变化或新增的调用才会实际运行。仅限同一会话                                                                                                      |

### TodoWrite

**工具名称：** `TodoWrite`

```typescript theme={null}
type TodoWriteInput = {
  todos: Array<{
    content: string;
    status: "pending" | "in_progress" | "completed";
    activeForm: string;
  }>;
};
```

创建并管理用于跟踪进度的结构化任务列表。

<Note>
  从 TypeScript Agent SDK 0.3.142 起，`TodoWrite` 默认被禁用。请改用 `TaskCreate`、`TaskGet`、`TaskUpdate` 和 `TaskList`。请参阅 [迁移到 Task 工具](/docs/en/agent-sdk/todo-tracking#migrate-to-task-tools) 以更新你的监控代码，或设置 `CLAUDE_CODE_ENABLE_TASKS=0` 以恢复使用 `TodoWrite`。
</Note>

### TaskCreate

**工具名称：** `TaskCreate`

```typescript theme={null}
type TaskCreateInput = {
  subject: string;
  description: string;
  activeForm?: string;
  metadata?: Record<string, unknown>;
};
```

创建单个任务并返回其分配的 ID。

### TaskUpdate

**工具名称：** `TaskUpdate`

```typescript theme={null}
type TaskUpdateInput = {
  taskId: string;
  status?: "pending" | "in_progress" | "completed" | "deleted";
  subject?: string;
  description?: string;
  activeForm?: string;
  addBlocks?: string[];
  addBlockedBy?: string[];
  owner?: string;
  metadata?: Record<string, unknown>;
};
```

按 ID 修补单个任务。将 `status` 设为 `"deleted"` 可将其删除。

### TaskGet

**工具名称：** `TaskGet`

```typescript theme={null}
type TaskGetInput = {
  taskId: string;
};
```

返回单个任务的完整详情，如果找不到该 ID 则返回 `null`。

### TaskList

**工具名称：** `TaskList`

```typescript theme={null}
type TaskListInput = {};
```

返回当前列表中所有任务的快照。

### ExitPlanMode

**工具名称：** `ExitPlanMode`

```typescript theme={null}
type ExitPlanModeInput = {
  /** Deprecated: no longer used. */
  allowedPrompts?: Array<{
    tool: "Bash";
    prompt: string;
  }>;
};
```

退出计划模式。`allowedPrompts` 字段已被弃用并被忽略；Claude Code 仍然接受它，以便现有的调用方和记录能够通过验证。在 v2.1.205 之前，它会请求基于提示的 Bash 权限来实现该计划。

### ListMcpResources

**工具名称：** `ListMcpResourcesTool`

```typescript theme={null}
type ListMcpResourcesInput = {
  server?: string;
};
```

列出已连接服务器上可用的 MCP 资源。

### ReadMcpResource

**工具名称：** `ReadMcpResourceTool`

```typescript theme={null}
type ReadMcpResourceInput = {
  server: string;
  uri: string;
};
```

从服务器读取特定的 MCP 资源。

### EnterWorktree

**工具名称：** `EnterWorktree`

```typescript theme={null}
type EnterWorktreeInput = {
  name?: string;
  path?: string;
};
```

创建并进入一个临时 git worktree，用于隔离工作。传入 `path` 可切换到现有的 worktree，而不是创建新的。首次进入时，目标必须是当前仓库的已注册 worktree，或者在多仓库工作区中，是嵌套在其中的某个仓库的 worktree；在 worktree 会话内部时，目标必须位于该会话仓库的 `.claude/worktrees/` 之下。`name` 和 `path` 互斥。

## 工具输出类型

所有内置 Claude Code 工具输出模式的文档。这些类型从 `@anthropic-ai/claude-agent-sdk` 导出，代表每个工具返回的实际响应数据。

### `ToolOutputSchemas`

所有工具输出类型的联合。

```typescript theme={null}
type ToolOutputSchemas =
  | AgentOutput
  | AskUserQuestionOutput
  | BashOutput
  | EnterWorktreeOutput
  | ExitPlanModeOutput
  | FileEditOutput
  | FileReadOutput
  | FileWriteOutput
  | GlobOutput
  | GrepOutput
  | ListMcpResourcesOutput
  | MonitorOutput
  | NotebookEditOutput
  | ReadMcpResourceOutput
  | TaskCreateOutput
  | TaskGetOutput
  | TaskListOutput
  | TaskStopOutput
  | TaskUpdateOutput
  | TodoWriteOutput
  | WebFetchOutput
  | WebSearchOutput
  | WorkflowOutput;
```

### 代理

**工具名称：** `Agent`（此前为 `Task`，仍可作为别名接受）

```typescript theme={null}
type AgentOutput =
  | {
      status: "completed";
      agentId: string;
      agentType?: string;
      content: Array<{ type: "text"; text: string; citations?: unknown[] | null }>;
      resolvedModel?: string;
      modelsUsed?: string[];
      totalToolUseCount: number;
      totalDurationMs: number;
      totalTokens: number;
      usage: {
        input_tokens: number;
        output_tokens: number;
        cache_creation_input_tokens: number | null;
        cache_read_input_tokens: number | null;
        server_tool_use: {
          web_search_requests: number;
          web_fetch_requests: number;
        } | null;
        service_tier: string | null;
        cache_creation: {
          ephemeral_1h_input_tokens: number;
          ephemeral_5m_input_tokens: number;
        } | null;
        inference_geo?: string | null;
        speed?: string | null;
        iterations?: unknown;
      };
      toolStats?: {
        readCount: number;
        searchCount: number;
        bashCount: number;
        editFileCount: number;
        linesAdded: number;
        linesRemoved: number;
        otherToolCount: number;
        frameCount?: number;
      };
      prompt: string;
      worktreePath?: string;
      worktreeBranch?: string;
    }
  | {
      status: "async_launched";
      isAsync?: true;
      agentId: string;
      description: string;
      resolvedModel?: string;
      modelsUsed?: string[];
      prompt: string;
      outputFile: string;
      canReadOutputFile?: boolean;
    }
  | {
      status: "remote_launched";
      taskId: string;
      sessionUrl: string;
      description: string;
      prompt: string;
      outputFile: string;
    };
```

返回子代理的结果。根据 `status` 字段进行区分：`"completed"` 表示已完成的任务，`"async_launched"` 表示后台任务，`"remote_launched"` 表示 Claude Code 已分派到远程云端会话的任务，其中 `sessionUrl` 链接到该会话，`taskId` 用于标识该任务。

`completed` 和 `async_launched` 变体上的 `resolvedModel` 字段标明了子代理实际运行的模型，当 [`availableModels`](/docs/en/model-config#restrict-model-selection) 或其他覆盖配置适用时，它可能与请求的 `model` 输入不同。 {/* min-version: 2.1.174 */}此字段需要 Claude Code v2.1.174 或更高版本。 {/* min-version: 2.1.212 */}在 `async_launched` 上，它指定当任务移至后台时正在使用的模型。

`modelsUsed` 按顺序列出子代理使用的模型。该字段仅在运行中途发生模型切换时出现，且当运行切换回某个模型时，该模型会再次出现在列表中。在 `async_launched` 上，该列表涵盖转入后台之前使用的模型。{/* min-version: 2.1.212 */}`modelsUsed` 字段和 `resolvedModel` 的后台行为都需要 Claude Code v2.1.212 或更高版本。

在 `completed` 变体上，当子代理在隔离的 git worktree 中运行时，`worktreePath` 会被设置；当 Claude Code 创建了该 worktree 时，`worktreeBranch` 会指明该 worktree 的分支名称。`usage.service_tier` 携带 API 为子代理请求报告的服务层级字符串。

在 v2.1.207 之前，发布的类型更为狭窄。它省略了 `worktreePath`、`worktreeBranch`、`citations`、`toolStats.frameCount`，以及 `inference_geo`、`speed` 和 `iterations` 这些使用字段，并将 `service_tier` 的类型标注为 `"standard" | "priority" | "batch"`。类型中标记为可选的字段，在由早期版本记录的结果中可能不存在。

### AskUserQuestion

**工具名称：**`AskUserQuestion`

```typescript theme={null}
type AskUserQuestionOutput = {
  questions: Array<{
    question: string;
    header: string;
    options: Array<{ label: string; description: string; preview?: string }>;
    multiSelect: boolean;
  }>;
  answers: Record<string, string>;
  response?: string;
};
```

返回提出的问题以及用户的回答。当用户输入了自由形式的回复而不是回答结构化问题时，会设置 `response`；当该字段存在时，Claude 收到的是 “The user responded: …”，而不是逐题的答案列表。

### Bash

**工具名称：** `Bash`

```typescript theme={null}
type BashOutput = {
  stdout: string;
  stderr: string;
  rawOutputPath?: string;
  interrupted: boolean;
  isImage?: boolean;
  backgroundTaskId?: string;
  backgroundedByUser?: boolean;
  timedOutAfterMs?: number;
  backgroundCwdHint?: string;
  dangerouslyDisableSandbox?: boolean;
  returnCodeInterpretation?: string;
  structuredContent?: unknown[];
  persistedOutputPath?: string;
  persistedOutputSize?: number;
};
```

返回按 stdout/stderr 拆分的命令输出。后台命令包含一个 `backgroundTaskId`。

{/* min-version: 2.1.210 */}`timedOutAfterMs` 是以毫秒为单位的超时时间，当命令达到超时并转入后台（而非显式以后台方式启动）时设置。当被转入后台的命令包含目录切换内建命令（如 `cd`、`pushd`、`popd` 或 `chdir`）时，会设置 `backgroundCwdHint`，并注明会话工作目录未发生变化。这两个字段均要求 Claude Code v2.1.210 或更高版本。

### Monitor

**工具名称：** `Monitor`

```typescript theme={null}
type MonitorOutput = {
  taskId: string;
  timeoutMs: number;
  persistent?: boolean;
};
```

返回正在运行的监视器的后台任务 ID。可将此 ID 与 `TaskStop` 配合使用，以提前取消监视。

### Edit

**工具名称：** `Edit`

```typescript theme={null}
type FileEditOutput = {
  filePath: string;
  oldString: string;
  newString: string;
  originalFile: string;
  structuredPatch: Array<{
    oldStart: number;
    oldLines: number;
    newStart: number;
    newLines: number;
    lines: string[];
  }>;
  userModified: boolean;
  replaceAll: boolean;
  gitDiff?: {
    filename: string;
    status: "modified" | "added";
    additions: number;
    deletions: number;
    changes: number;
    patch: string;
  };
};
```

返回编辑操作的结构化差异（diff）。

### Read

**工具名称：** `Read`

```typescript theme={null}
type FileReadOutput =
  | {
      type: "text";
      file: {
        filePath: string;
        content: string;
        numLines: number;
        startLine: number;
        totalLines: number;
      };
    }
  | {
      type: "image";
      file: {
        base64: string;
        type: "image/jpeg" | "image/png" | "image/gif" | "image/webp";
        originalSize: number;
        dimensions?: {
          originalWidth?: number;
          originalHeight?: number;
          displayWidth?: number;
          displayHeight?: number;
        };
      };
    }
  | {
      type: "notebook";
      file: {
        filePath: string;
        cells: unknown[];
      };
    }
  | {
      type: "pdf";
      file: {
        filePath: string;
        base64: string;
        originalSize: number;
      };
    }
  | {
      type: "parts";
      file: {
        filePath: string;
        originalSize: number;
        count: number;
        outputDir: string;
      };
    };
```

以适合文件类型的格式返回文件内容。根据 `type` 字段进行区分。

### Write

**工具名称：** `Write`

```typescript theme={null}
type FileWriteOutput = {
  type: "create" | "update";
  filePath: string;
  content: string;
  structuredPatch: Array<{
    oldStart: number;
    oldLines: number;
    newStart: number;
    newLines: number;
    lines: string[];
  }>;
  originalFile: string | null;
  gitDiff?: {
    filename: string;
    status: "modified" | "added";
    additions: number;
    deletions: number;
    changes: number;
    patch: string;
  };
};
```

返回包含结构化差异信息的写入结果。

### Glob

**工具名称：** `Glob`

```typescript theme={null}
type GlobOutput = {
  durationMs: number;
  numFiles: number;
  filenames: string[];
  truncated: boolean;
  totalMatches?: number;
  countIsComplete?: boolean;
};
```

返回匹配 glob 模式的文件路径，按修改时间排序。

{/* min-version: 2.1.191 */}`totalMatches` 和 `countIsComplete` 要求 Claude Code v2.1.191 或更高版本。`totalMatches` 报告截断前匹配文件的数量。当 `countIsComplete` 为 false 时，`totalMatches` 是一个下界，因为底层搜索截断了其自身的输出。

### Grep

**工具名称：** `Grep`

```typescript theme={null}
type GrepOutput = {
  mode?: "content" | "files_with_matches" | "count";
  numFiles: number;
  filenames: string[];
  content?: string;
  numLines?: number;
  numMatches?: number;
  totalFiles?: number;
  totalLines?: number;
  appliedLimit?: number;
  appliedOffset?: number;
};
```

返回搜索结果。其结构因 `mode` 而异：文件列表、带匹配项的内容或匹配计数。在 `count` 模式下，`numFiles` 和 `numMatches` 是整个结果集的总数，而非分页切片。{/* min-version: 2.1.208 */}在 v2.1.208 之前，截断所列条目的 `head_limit` 或 `offset` 也会截断这些总数。

{/* min-version: 2.1.208 */}`totalFiles` 要求 Claude Code v2.1.208 或更高版本，并报告在 `files_with_matches` 模式下 `head_limit` 和 `offset` 分页之前的结果总数。{/* min-version: 2.1.210 */}`totalLines` 要求 Claude Code v2.1.210 或更高版本，并报告在 `content` 模式下分页之前的总行数。

### TaskStop

**工具名称：** `TaskStop`

```typescript theme={null}
type TaskStopOutput = {
  message: string;
  task_id: string;
  task_type: string;
  command?: string;
};
```

停止后台任务后返回确认信息。

### NotebookEdit

**工具名称：** `NotebookEdit`

```typescript theme={null}
type NotebookEditOutput = {
  new_source: string;
  cell_id?: string;
  cell_type: "code" | "markdown";
  language: string;
  edit_mode: string;
  error?: string;
  notebook_path: string;
  original_file: string;
  updated_file: string;
};
```

返回笔记本编辑的结果，包含原始和更新后的文件内容。

### WebFetch

**工具名称：** `WebFetch`

```typescript theme={null}
type WebFetchOutput = {
  bytes: number;
  code: number;
  codeText: string;
  result: string;
  durationMs: number;
  url: string;
};
```

返回获取的内容以及 HTTP 状态和元数据。

### WebSearch

**工具名称：** `WebSearch`

```typescript theme={null}
type WebSearchOutput = {
  query: string;
  results: Array<
    | {
        tool_use_id: string;
        content: Array<{ title: string; url: string }>;
      }
    | string
  >;
  durationSeconds: number;
};
```

返回来自网页的搜索结果。

### 工作流

**工具名称：** `Workflow`

```typescript theme={null}
type WorkflowOutput = {
  status: "async_launched";
  taskId: string;
  runId?: string;
  summary?: string;
  transcriptDir?: string;
  scriptPath?: string;
  error?: string;
};
```

在工具接受调用后立即返回。最终结果稍后作为任务完成送达。在将运行视为已启动之前，请检查 `error`：未通过语法检查的脚本会返回 `status: "async_launched"` 并设置 `error`，且永远不会运行。

| 字段           | 类型               | 描述                                                                                                                     |
| --------------- | ------------------ | ------------------------------------------------------------------------------------------------------------------------------- |
| `status`        | `"async_launched"` | 工具已接受该调用。这是该字段唯一的取值                                                        |
| `taskId`        | `string`           | 该运行的后台任务标识符                                                                                          |
| `runId`         | `string`           | 工作流运行标识符，在后续调用中作为 `resumeFromRunId` 传入                                                      |
| `summary`       | `string`           | 对该工作流功能的一行描述                                                                                  |
| `transcriptDir` | `string`           | 执行期间写入子代理转录的目录                                                               |
| `scriptPath`    | `string`           | 本次运行持久化工作流脚本的路径。编辑后作为 `scriptPath` 传回即可重新运行而无需重发脚本 |
| `error`         | `string`           | 当脚本未通过语法检查时设置。存在时，尽管状态为 `async_launched`，运行并未启动             |

### TodoWrite

**工具名称：** `TodoWrite`

```typescript theme={null}
type TodoWriteOutput = {
  oldTodos: Array<{
    content: string;
    status: "pending" | "in_progress" | "completed";
    activeForm: string;
  }>;
  newTodos: Array<{
    content: string;
    status: "pending" | "in_progress" | "completed";
    activeForm: string;
  }>;
};
```

返回先前和更新后的任务列表。

<Note>
  自 TypeScript Agent SDK 0.3.142 起，`TodoWrite` 默认禁用。请改用 `TaskCreate`、`TaskGet`、`TaskUpdate` 和 `TaskList`。请参阅 [迁移到任务工具](/docs/en/agent-sdk/todo-tracking#migrate-to-task-tools) 以更新您的监控代码，或设置 `CLAUDE_CODE_ENABLE_TASKS=0` 以恢复使用 `TodoWrite`。
</Note>

### TaskCreate

**工具名称：** `TaskCreate`

```typescript theme={null}
type TaskCreateOutput = {
  task: {
    id: string;
    subject: string;
  };
};
```

返回创建的任务及其分配的 ID。

### TaskUpdate

**工具名称：** `TaskUpdate`

```typescript theme={null}
type TaskUpdateOutput = {
  success: boolean;
  taskId: string;
  updatedFields: string[];
  error?: string;
  statusChange?: {
    from: string;
    to: string;
  };
};
```

返回更新结果，包括哪些字段发生了更改。

### TaskGet

**工具名称：** `TaskGet`

```typescript theme={null}
type TaskGetOutput = {
  task: {
    id: string;
    subject: string;
    description: string;
    status: "pending" | "in_progress" | "completed";
    blocks: string[];
    blockedBy: string[];
  } | null;
};
```

返回完整的任务记录，或在找不到 ID 时返回 `null`。

### TaskList

**工具名称：** `TaskList`

```typescript theme={null}
type TaskListOutput = {
  tasks: Array<{
    id: string;
    subject: string;
    status: "pending" | "in_progress" | "completed";
    owner?: string;
    blockedBy: string[];
  }>;
};
```

返回当前列表中所有任务的快照。

### ExitPlanMode

**工具名称：** `ExitPlanMode`

```typescript theme={null}
type ExitPlanModeOutput = {
  plan: string | null;
  isAgent: boolean;
  filePath?: string;
  hasTaskTool?: boolean;
  awaitingLeaderApproval?: boolean;
  requestId?: string;
};
```

返回退出计划模式后的计划状态。

### ListMcpResources

**工具名称：** `ListMcpResourcesTool`

```typescript theme={null}
type ListMcpResourcesOutput = Array<{
  uri: string;
  name: string;
  mimeType?: string;
  description?: string;
  server: string;
}>;
```

返回可用 MCP 资源的数组。

### ReadMcpResource

**工具名称：** `ReadMcpResourceTool`

```typescript theme={null}
type ReadMcpResourceOutput = {
  contents: Array<{
    uri: string;
    mimeType?: string;
    text?: string;
  }>;
};
```

返回所请求 MCP 资源的内容。

### EnterWorktree

**工具名称：** `EnterWorktree`

```typescript theme={null}
type EnterWorktreeOutput = {
  worktreePath: string;
  worktreeBranch?: string;
  message: string;
};
```

返回有关 git worktree 的信息。

## 权限类型

### `PermissionUpdate`

用于更新权限的操作。

```typescript theme={null}
type PermissionUpdate =
  | {
      type: "addRules";
      rules: PermissionRuleValue[];
      behavior: PermissionBehavior;
      destination: PermissionUpdateDestination;
    }
  | {
      type: "replaceRules";
      rules: PermissionRuleValue[];
      behavior: PermissionBehavior;
      destination: PermissionUpdateDestination;
    }
  | {
      type: "removeRules";
      rules: PermissionRuleValue[];
      behavior: PermissionBehavior;
      destination: PermissionUpdateDestination;
    }
  | {
      type: "setMode";
      mode: PermissionMode;
      destination: PermissionUpdateDestination;
    }
  | {
      type: "addDirectories";
      directories: string[];
      destination: PermissionUpdateDestination;
    }
  | {
      type: "removeDirectories";
      directories: string[];
      destination: PermissionUpdateDestination;
    };
```

### `PermissionBehavior`

```typescript theme={null}
type PermissionBehavior = "allow" | "deny" | "ask";
```

### `PermissionUpdateDestination`

```typescript theme={null}
type PermissionUpdateDestination =
  | "userSettings" // Global user settings
  | "projectSettings" // Per-directory project settings
  | "localSettings" // Local project settings
  | "session" // Current session only
  | "cliArg"; // CLI argument
```

### `PermissionRuleValue`

```typescript theme={null}
type PermissionRuleValue = {
  toolName: string;
  ruleContent?: string;
};
```

## 其他类型

### `ApiKeySource`

```typescript theme={null}
type ApiKeySource = "user" | "project" | "org" | "temporary" | "oauth";
```

### `SdkBeta`

可通过 `betas` 选项启用的可用 beta 功能。更多信息请参阅 [Beta headers](https://platform.claude.com/docs/en/api/beta-headers)。

```typescript theme={null}
type SdkBeta = "context-1m-2025-08-07";
```

<Warning>
  `context-1m-2025-08-07` beta 已于 2026 年 4 月 30 日停用。在 Claude Sonnet 4.5 或 Sonnet 4 中传递此值不会产生任何效果，超出标准 200k token 上下文窗口的请求将返回错误。如需使用 1M token 上下文窗口，请迁移至 [Claude Sonnet 5、Claude Sonnet 4.6、Claude Opus 4.6、Claude Opus 4.7 或 Claude Opus 4.8](https://platform.claude.com/docs/en/about-claude/models/overview)，这些模型以标准定价提供 1M 上下文，无需 beta 标头。
</Warning>

### `SlashCommand`

关于可用斜杠命令的信息。

```typescript theme={null}
type SlashCommand = {
  name: string;
  description: string;
  argumentHint: string;
  aliases?: string[];
};
```

### `ModelInfo`

关于可用模型的信息。

```typescript theme={null}
type ModelInfo = {
  value: string;
  resolvedModel?: string;
  displayName: string;
  description: string;
  supportsEffort?: boolean;
  supportedEffortLevels?: ("low" | "medium" | "high" | "xhigh" | "max")[];
  supportsAdaptiveThinking?: boolean;
  supportsFastMode?: boolean;
  supportsAutoMode?: boolean;
};
```

| 字段                      | 类型                                                               | 描述                                                                                                                                                                                                                                                                                                           |
| :------------------------- | :----------------------------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `value`                    | `string`                                                           | 在 API 调用中传递的模型标识符                                                                                                                                                                                                                                                                                 |
| `resolvedModel`            | `string \| undefined`                                              | 此条目的 `value` 所解析到的规范线上模型 ID。诸如 `sonnet` 之类的别名条目会解析为诸如 `claude-sonnet-5` 之类的显式模型 ID，因此宿主可以将存储的显式模型 ID 与涵盖它的别名条目进行匹配。{/* min-version: 2.1.197 */}需要 Claude Code v2.1.197 或更高版本。 |
| `displayName`              | `string`                                                           | 人类可读的显示名称                                                                                                                                                                                                                                                                                           |
| `description`              | `string`                                                           | 模型能力的描述                                                                                                                                                                                                                                                                               |
| `supportsEffort`           | `boolean \| undefined`                                             | 此模型是否支持努力级别                                                                                                                                                                                                                                                                             |
| `supportedEffortLevels`    | `("low" \| "medium" \| "high" \| "xhigh" \| "max")[] \| undefined` | 此模型接受的努力级别                                                                                                                                                                                                         |
| `supportsAdaptiveThinking` | `boolean \| undefined`                                             | 此模型是否支持自适应思考，即由 Claude 决定何时思考以及思考多少                                                                                                                                                                                                        |
| `supportsFastMode`         | `boolean \| undefined`                                             | 此模型是否支持快速模式                                                                                                                                                                                                         |
| `supportsAutoMode`         | `boolean \| undefined`                                             | 此模型是否支持自动模式                                                                                                                                                                                                         |

### `AgentInfo`

关于可通过 Agent 工具调用的可用子代理的信息。

```typescript theme={null}
type AgentInfo = {
  name: string;
  description: string;
  model?: string;
};
```

| 字段         | 类型                  | 描述                                                          |
| :------------ | :-------------------- | :------------------------------------------------------------------- |
| `name`        | `string`              | 代理类型标识符（例如 `"Explore"`、`"general-purpose"`）       |
| `description` | `string`              | 何时使用此代理的描述                                |
| `model`       | `string \| undefined` | 此代理使用的模型别名。如果省略，则继承父级的模型 |

### `McpServerStatus`

已连接 MCP 服务器的状态。

```typescript theme={null}
type McpServerStatus = {
  name: string;
  status: "connected" | "failed" | "needs-auth" | "pending" | "disabled";
  serverInfo?: {
    name: string;
    version: string;
  };
  error?: string;
  config?: McpServerStatusConfig;
  scope?: string;
  tools?: {
    name: string;
    description?: string;
    annotations?: {
      readOnly?: boolean;
      destructive?: boolean;
      openWorld?: boolean;
    };
  }[];
};
```

### `McpServerStatusConfig`

由 `mcpServerStatus()` 报告的 MCP 服务器配置。这是所有 MCP 服务器传输类型的联合。

```typescript theme={null}
type McpServerStatusConfig =
  | McpStdioServerConfig
  | McpSSEServerConfig
  | McpHttpServerConfig
  | McpSdkServerConfig
  | McpClaudeAIProxyServerConfig;
```

有关每种传输类型的详细信息，请参阅 [`McpServerConfig`](#mcpserverconfig)。

### `AccountInfo`

已认证用户的账户信息。

```typescript theme={null}
type AccountInfo = {
  email?: string;
  organization?: string;
  subscriptionType?: string;
  tokenSource?: string;
  apiKeySource?: string;
};
```

### `ModelUsage`

在结果消息中返回的按模型统计的使用数据。`costUSD` 值是客户端估算值。有关计费注意事项，请参阅 [跟踪成本和使用量](/docs/en/agent-sdk/cost-tracking)。

```typescript theme={null}
type ModelUsage = {
  inputTokens: number;
  outputTokens: number;
  cacheReadInputTokens: number;
  cacheCreationInputTokens: number;
  webSearchRequests: number;
  costUSD: number;
  contextWindow: number;
  maxOutputTokens: number;
};
```

### `ConfigScope`

```typescript theme={null}
type ConfigScope = "local" | "user" | "project";
```

### `NonNullableUsage`

[`Usage`](#usage) 的一个版本，其中所有可为空的字段均变为不可为空。

```typescript theme={null}
type NonNullableUsage = {
  [K in keyof Usage]: NonNullable<Usage[K]>;
};
```

### `Usage`

令牌用量统计。这是来自 `@anthropic-ai/sdk` 的 `BetaUsage` 类型。

```typescript theme={null}
type Usage = {
  input_tokens: number;
  output_tokens: number;
  cache_creation_input_tokens: number | null;
  cache_read_input_tokens: number | null;
  cache_creation: {
    ephemeral_5m_input_tokens: number;
    ephemeral_1h_input_tokens: number;
  } | null;
  server_tool_use: BetaServerToolUsage | null;
  service_tier: "standard" | "priority" | "batch" | null;
  speed: "standard" | "fast" | null;
  inference_geo: string | null;
  iterations: BetaIterationsUsage | null;
};
```

`BetaServerToolUsage` 和 `BetaIterationsUsage` 在 `@anthropic-ai/sdk` 中定义。

### `CallToolResult`

MCP 工具结果类型（来自 `@modelcontextprotocol/sdk/types.js`）。`structuredContent` 是一个 JSON 对象，可以与 `content` 一起返回，包括图像块。请参阅 [返回结构化数据](/docs/en/agent-sdk/custom-tools#return-structured-data)。

```typescript theme={null}
type CallToolResult = {
  content: Array<{
    type: "text" | "image" | "audio" | "resource" | "resource_link";
    // Additional fields vary by type
  }>;
  structuredContent?: Record<string, unknown>;
  isError?: boolean;
};
```

### `ThinkingConfig`

控制 Claude 的思考/推理行为。优先于已弃用的 `maxThinkingTokens`。

```typescript theme={null}
type ThinkingDisplay = "summarized" | "omitted";

type ThinkingConfig =
  | { type: "adaptive"; display?: ThinkingDisplay } // The model determines when and how much to reason (Opus 4.6+)
  | { type: "enabled"; budgetTokens?: number; display?: ThinkingDisplay } // Fixed thinking token budget
  | { type: "disabled" }; // No extended thinking
```

可选的 `display` 字段控制思考文本以 `"summarized"` 还是 `"omitted"` 形式返回。在 Claude Opus 4.7 及更高版本上,API 默认为 `"omitted"`,因此请设置 `"summarized"` 以在 `thinking` 块中接收思考内容。

### `SpawnedProcess`

用于自定义进程生成的接口(与 `spawnClaudeCodeProcess` 选项一起使用)。`ChildProcess` 已满足此接口。

```typescript theme={null}
interface SpawnedProcess {
  stdin: Writable;
  stdout: Readable;
  readonly killed: boolean;
  readonly exitCode: number | null;
  kill(signal: NodeJS.Signals): boolean;
  on(
    event: "exit",
    listener: (code: number | null, signal: NodeJS.Signals | null) => void
  ): void;
  on(event: "error", listener: (error: Error) => void): void;
  once(
    event: "exit",
    listener: (code: number | null, signal: NodeJS.Signals | null) => void
  ): void;
  once(event: "error", listener: (error: Error) => void): void;
  off(
    event: "exit",
    listener: (code: number | null, signal: NodeJS.Signals | null) => void
  ): void;
  off(event: "error", listener: (error: Error) => void): void;
}
```

### `SpawnOptions`

传递给自定义 spawn 函数的选项。

```typescript theme={null}
interface SpawnOptions {
  command: string;
  args: string[];
  cwd?: string;
  env: Record<string, string | undefined>;
  signal: AbortSignal;
}
```

<Note>
  `signal` 字段告知你的 spawn 函数何时销毁进程。将其作为 `signal` 选项传递给 Node 的 `spawn()`,或将其传递给你的 VM 或容器销毁处理器。

  当 [`Options.abortController`](#options) 中止时,此信号不会立即触发。SDK 首先关闭进程的 stdin 并等待约两秒,以便 CLI 干净地关闭,然后中止此信号。若想在调用者中止的那一刻做出反应,请监听你自己的 `Options.abortController.signal`,你的 spawn 函数可以从其外层作用域引用它。
</Note>

### `McpSetServersResult`

`setMcpServers()` 操作的结果。

```typescript theme={null}
type McpSetServersResult = {
  added: string[];
  removed: string[];
  errors: Record<string, string>;
};
```

### `RewindFilesResult`

`rewindFiles()` 操作的结果。

```typescript theme={null}
type RewindFilesResult = {
  canRewind: boolean;
  error?: string;
  filesChanged?: string[];
  insertions?: number;
  deletions?: number;
};
```

### `SDKStatusMessage`

状态更新消息(例如,压缩中)。

```typescript theme={null}
type SDKStatusMessage = {
  type: "system";
  subtype: "status";
  status: "compacting" | null;
  permissionMode?: PermissionMode;
  uuid: UUID;
  session_id: string;
};
```

### `SDKTaskNotificationMessage`

当后台任务完成、失败或被停止时的通知。后台任务包括 `run_in_background` Bash 命令、[Monitor](#monitor) 监视以及后台子代理。

```typescript theme={null}
type SDKTaskNotificationMessage = {
  type: "system";
  subtype: "task_notification";
  task_id: string;
  tool_use_id?: string;
  status: "completed" | "failed" | "stopped";
  output_file: string;
  summary: string;
  usage?: {
    total_tokens: number;
    tool_uses: number;
    duration_ms: number;
  };
  uuid: UUID;
  session_id: string;
};
```

### `SDKToolUseSummaryMessage`

对话中工具使用情况的摘要。

```typescript theme={null}
type SDKToolUseSummaryMessage = {
  type: "tool_use_summary";
  summary: string;
  preceding_tool_use_ids: string[];
  uuid: UUID;
  session_id: string;
};
```

### `SDKHookStartedMessage`

当钩子开始执行时发出。

Claude Code 会立即将此消息、[`SDKHookProgressMessage`](#sdkhookprogressmessage) 以及 [`SDKHookResponseMessage`](#sdkhookresponsemessage) 传递到消息流中,包括在会话启动期间 `SessionStart` 或 `Setup` 钩子仍在运行时。Claude Code v2.1.169 至 v2.1.203 会在 `SessionStart` 或 `Setup` 钩子完成后以单批次方式传递这些消息;v2.1.204 恢复了实时传递。

```typescript theme={null}
type SDKHookStartedMessage = {
  type: "system";
  subtype: "hook_started";
  hook_id: string;
  hook_name: string;
  hook_event: string;
  uuid: UUID;
  session_id: string;
};
```

### `SDKHookProgressMessage`

在钩子运行期间发出,包含 stdout/stderr 输出。

```typescript theme={null}
type SDKHookProgressMessage = {
  type: "system";
  subtype: "hook_progress";
  hook_id: string;
  hook_name: string;
  hook_event: string;
  stdout: string;
  stderr: string;
  output: string;
  uuid: UUID;
  session_id: string;
};
```

### `SDKHookResponseMessage`

当一个钩子执行完毕时发出。

```typescript theme={null}
type SDKHookResponseMessage = {
  type: "system";
  subtype: "hook_response";
  hook_id: string;
  hook_name: string;
  hook_event: string;
  output: string;
  stdout: string;
  stderr: string;
  exit_code?: number;
  outcome: "success" | "error" | "cancelled";
  uuid: UUID;
  session_id: string;
};
```

### `SDKToolProgressMessage`

在工具执行期间周期性发出，以指示进度。

```typescript theme={null}
type SDKToolProgressMessage = {
  type: "tool_progress";
  tool_use_id: string;
  tool_name: string;
  parent_tool_use_id: string | null;
  elapsed_time_seconds: number;
  task_id?: string;
  uuid: UUID;
  session_id: string;
};
```

### `SDKAuthStatusMessage`

在身份验证流程期间触发。

```typescript theme={null}
type SDKAuthStatusMessage = {
  type: "auth_status";
  isAuthenticating: boolean;
  output: string[];
  error?: string;
  uuid: UUID;
  session_id: string;
};
```

### `SDKTaskStartedMessage`

当后台任务开始时触发。对于后台 Bash 命令和 [Monitor](#monitor) 监视，`task_type` 字段为 `"local_bash"`；对于子代理为 `"local_agent"`，或为 `"remote_agent"`。

```typescript theme={null}
type SDKTaskStartedMessage = {
  type: "system";
  subtype: "task_started";
  task_id: string;
  tool_use_id?: string;
  description: string;
  task_type?: string;
  uuid: UUID;
  session_id: string;
};
```

### `SDKTaskProgressMessage`

在子代理或后台任务运行期间定期发出。`summary` 字段仅在启用 [`agentProgressSummaries`](#options) 时才会填充。

```typescript theme={null}
type SDKTaskProgressMessage = {
  type: "system";
  subtype: "task_progress";
  task_id: string;
  tool_use_id?: string;
  description: string;
  subagent_type?: string;
  usage: {
    total_tokens: number;
    tool_uses: number;
    duration_ms: number;
  };
  last_tool_name?: string;
  summary?: string;
  uuid: UUID;
  session_id: string;
};
```

### `SDKTaskUpdatedMessage`

当后台任务的状态发生变化时触发，例如从 `running` 转变为 `completed` 时。将 `patch` 合并到以 `task_id` 为键的本地任务映射中。`end_time` 字段是以毫秒为单位的 Unix 纪元时间戳，可与 `Date.now()` 进行比较。

```typescript theme={null}
type SDKTaskUpdatedMessage = {
  type: "system";
  subtype: "task_updated";
  task_id: string;
  patch: {
    status?: "pending" | "running" | "completed" | "failed" | "killed";
    description?: string;
    end_time?: number;
    total_paused_ms?: number;
    error?: string;
    is_backgrounded?: boolean;
  };
  uuid: UUID;
  session_id: string;
};
```

### `SDKBackgroundTasksChangedMessage`

每当活动后台任务集合发生变化时发出：任务启动、完成、被终止，或前台代理转为后台运行。`tasks` 数组是完整的活动集合。请用每个负载替换任何缓存的集合，而不是将 `task_started` 和 `task_notification` 事件配对，这样下一次成员变更可以纠正你遗漏的任何事件。

相对于那些按任务发出的事件的顺序未指定，因此不要将两个流关联起来。

启动时不发出任何内容。每当会话的 CLI 进程启动或重启时重置为空集合，并让下一次成员变更重新填充它。

{/* min-version: 2.1.203 */}需要 Claude Code v2.1.203 或更高版本。

```typescript theme={null}
type SDKBackgroundTasksChangedMessage = {
  type: "system";
  subtype: "background_tasks_changed";
  tasks: {
    task_id: string;
    task_type: string;
    description: string;
  }[];
  uuid: UUID;
  session_id: string;
};
```

### `SDKThinkingTokensMessage`

当 Claude 生成思考块（包括已遮蔽（redacted）的思考块）时发出，携带迄今为止已生成的思考令牌的滚动估计值。`estimated_tokens` 是当前思考块的累计总数，`estimated_tokens_delta` 是此帧携带的增量。用于进度显示。顶层代理循环的最终计数是结果消息的 `usage.output_tokens`，它[不包括子代理令牌](/docs/en/agent-sdk/cost-tracking#get-the-total-cost-of-a-query)；如需整棵树的统计，请使用 [`modelUsage`](#modelusage)。

{/* min-version: 2.1.153 */}需要 Claude Code v2.1.153 或更高版本。

```typescript theme={null}
type SDKThinkingTokensMessage = {
  type: "system";
  subtype: "thinking_tokens";
  estimated_tokens: number;
  estimated_tokens_delta: number;
  uuid: UUID;
  session_id: string;
};
```

### `SDKFilesPersistedEvent`

当文件检查点持久化到磁盘时发出。

```typescript theme={null}
type SDKFilesPersistedEvent = {
  type: "system";
  subtype: "files_persisted";
  files: { filename: string; file_id: string }[];
  failed: { filename: string; error: string }[];
  processed_at: string;
  uuid: UUID;
  session_id: string;
};
```

### `SDKRateLimitEvent`

当会话遇到速率限制时发出。

```typescript theme={null}
type SDKRateLimitEvent = {
  type: "rate_limit_event";
  rate_limit_info: {
    status: "allowed" | "allowed_warning" | "rejected";
    resetsAt?: number;
    utilization?: number;
    errorCode?: "credits_required";
    canUserPurchaseCredits?: boolean;
    hasChargeableSavedPaymentMethod?: boolean;
  };
  uuid: UUID;
  session_id: string;
};
```

{/* min-version: 2.1.181 */}当 `errorCode` 为 `"credits_required"` 时，拒绝来自 claude.ai 订阅，其包含的用量已耗尽，在用户购买用量额度之前会话无法继续。`canUserPurchaseCredits` 指示已认证用户是否可以为该账户购买额度，`hasChargeableSavedPaymentMethod` 指示是否有已保存的支付方式存档。在非额度必需的速率限制事件中，这三个字段均不存在。需要 Claude Code v2.1.181 或更高版本。

### `SDKLocalCommandOutputMessage`

本地斜杠命令的输出（例如 `/voice` 或 `/usage`）。在转录中显示为助手风格的文本。

```typescript theme={null}
type SDKLocalCommandOutputMessage = {
  type: "system";
  subtype: "local_command_output";
  content: string;
  uuid: UUID;
  session_id: string;
};
```

### `SDKCommandsChangedMessage`

当可用命令集合在会话中途发生变化时发出，例如当代理进入子目录时发现技能。`commands` 数组是完整的更新列表，因此请用此负载替换任何缓存的命令列表。再次调用 `supportedCommands()` 并不等效：该方法返回初始化时捕获的快照，不反映会话中途的变化。

```typescript theme={null}
type SDKCommandsChangedMessage = {
  type: "system";
  subtype: "commands_changed";
  commands: SlashCommand[];
  uuid: UUID;
  session_id: string;
};
```

### `SDKPromptSuggestionMessage`

启用 `promptSuggestions` 后每轮结束后发出。包含预测的下一个用户提示。

```typescript theme={null}
type SDKPromptSuggestionMessage = {
  type: "prompt_suggestion";
  suggestion: string;
  uuid: UUID;
  session_id: string;
};
```

### `SDKConversationResetMessage`

当会话的对话被替换但会话未结束时发出，例如在 `/clear` 之后、退出计划模式时，或开始新对话时。在 `new_conversation_id` 下挂载空转录并丢弃任何缓存的会话标题。

```typescript theme={null}
type SDKConversationResetMessage = {
  type: "conversation_reset";
  new_conversation_id: UUID;
  uuid: UUID;
  session_id: string;
};
```

{/* min-version: 2.1.203 */}SDK 发布的类型声明在 Claude Code v2.1.203 及更高版本中声明了 `SDKConversationResetMessage`。在 v2.1.203 之前，`SDKMessage` 引用了该类型但未声明它，因此在禁用 `skipLibCheck` 时，对 `type === "conversation_reset"` 的窄化无法通过类型检查。

### `AbortError`

用于中止操作的自定义错误类。

```typescript theme={null}
class AbortError extends Error {}
```

## 沙盒配置

### `SandboxSettings`

沙盒行为的配置。使用此配置以编程方式启用命令沙盒并配置网络限制。

```typescript theme={null}
type SandboxSettings = {
  enabled?: boolean;
  failIfUnavailable?: boolean;
  autoAllowBashIfSandboxed?: boolean;
  excludedCommands?: string[];
  allowUnsandboxedCommands?: boolean;
  network?: SandboxNetworkConfig;
  filesystem?: SandboxFilesystemConfig;
  ignoreViolations?: Record<string, string[]>;
  enableWeakerNestedSandbox?: boolean;
  ripgrep?: { command: string; args?: string[] };
};
```

| 属性                        | 类型                                                  | 默认值      | 描述                                                                                                                                                                                                                                  |
| :-------------------------- | :---------------------------------------------------- | :---------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `enabled`                   | `boolean`                                             | `false`     | 为命令执行启用沙盒模式                                                                                                                                                                                                                |
| `failIfUnavailable`         | `boolean`                                             | `true`      | 如果 `enabled` 为 `true` 但沙盒无法启动,则在启动时停止。设置为 `false` 以回退到非沙盒执行并在 stderr 上输出警告                                                                                       |
| `autoAllowBashIfSandboxed`  | `boolean`                                             | `true`      | 启用沙盒时自动批准 bash 命令                                                                                                                                                                                                          |
| `excludedCommands`          | `string[]`                                            | `[]`        | 始终绕过沙盒限制的命令(例如 `['docker']`)。这些命令自动以非沙盒方式运行,无需模型参与                                                                                                          |
| `allowUnsandboxedCommands`  | `boolean`                                             | `true`      | 允许模型请求在沙盒外运行命令。当为 `true` 时,模型可以在工具输入中设置 `dangerouslyDisableSandbox`,这将回退到 [权限系统](#permissions-fallback-for-unsandboxed-commands) |
| `network`                   | [`SandboxNetworkConfig`](#sandboxnetworkconfig)       | `undefined` | 特定于网络的沙盒配置                                                                                                                                                                                                                  |
| `filesystem`                | [`SandboxFilesystemConfig`](#sandboxfilesystemconfig) | `undefined` | 特定于文件系统的读/写限制沙盒配置                                                                                                                                                                                                     |
| `ignoreViolations`          | `Record<string, string[]>`                            | `undefined` | 要忽略的违规类别到模式的映射(例如 `{ file: ['/tmp/*'], network: ['localhost'] }`)                                                                                                                                           |
| `enableWeakerNestedSandbox` | `boolean`                                             | `false`     | 启用较弱的嵌套沙盒以实现兼容性                                                                                                                                                                                                        |
| `ripgrep`                   | `{ command: string; args?: string[] }`                | `undefined` | 用于沙盒环境的自定义 ripgrep 二进制配置                                                                                                                                                                            |

<Note>
  沙盒依赖于平台支持，在 Linux 上还依赖于 `bubblewrap` 和 `socat` 等工具。当 `enabled` 为 `true` 且沙盒无法启动时，`query()` 会报告一条 `result` 消息，其中包含 `subtype: "error_during_execution"` 以及 `errors` 中的原因。对于单条消息的 `query()` 调用，SDK 会在产生该错误结果后抛出异常，因此请将循环包裹在 try 块中以便跳过它继续执行。有关错误契约，请参阅[Handle the result](/docs/en/agent-sdk/agent-loop#handle-the-result)。

  若要改为在非沙盒模式下运行，请设置 `failIfUnavailable: false`。
</Note>

#### 使用示例

```typescript theme={null}
import { query } from "@anthropic-ai/claude-agent-sdk";

try {
  for await (const message of query({
    prompt: "Build and test my project",
    options: {
      sandbox: {
        enabled: true,
        autoAllowBashIfSandboxed: true,
        network: {
          allowLocalBinding: true
        }
      }
    }
  })) {
    if ("result" in message) console.log(message.result);
  }
} catch (error) {
  // A single-shot query() throws after yielding an error result,
  // such as when the sandbox can't start (failIfUnavailable defaults to true).
  console.log(`Session ended with an error: ${error}`);
}
```

<Warning>
  **Unix 套接字安全：** `allowUnixSockets` 选项可能会授予对强大系统服务的访问权限。例如，允许 `/var/run/docker.sock` 实际上等同于通过 Docker API 授予对主机系统的完全访问权限，从而绕过沙盒隔离。请仅允许严格必要的 Unix 套接字，并了解每个套接字的安全影响。
</Warning>

### `SandboxNetworkConfig`

沙盒模式的网络特定配置。当父级 [`SandboxSettings`](#sandboxsettings) 中的 `enabled` 为 `true` 时，这些设置适用于沙盒化的 Bash 命令。它们不限制 WebFetch 工具，该工具改用 [permission rules](/docs/en/permissions#webfetch)。

```typescript theme={null}
type SandboxNetworkConfig = {
  allowedDomains?: string[];
  deniedDomains?: string[];
  allowManagedDomainsOnly?: boolean;
  allowLocalBinding?: boolean;
  allowUnixSockets?: string[];
  allowAllUnixSockets?: boolean;
  httpProxyPort?: number;
  socksProxyPort?: number;
};
```

| 属性                      | 类型       | 默认值      | 描述                                                                                                                                                                                                                 |
| :------------------------ | :--------- | :---------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `allowedDomains`          | `string[]` | `[]`        | 沙盒进程可访问的域名                                                                                                                                                                                                       |
| `deniedDomains`           | `string[]` | `[]`        | 沙盒进程不可访问的域名。优先级高于 `allowedDomains`                                                                                                                                                                    |
| `allowManagedDomainsOnly` | `boolean`  | `false`     | 仅限托管设置。当在 [托管设置](/docs/en/permissions#managed-settings) 中设置时，仅会生效来自托管设置的 `allowedDomains` 条目，而来自用户、项目或本地设置的条目将被忽略。通过 SDK 选项设置时无效 |
| `allowLocalBinding`       | `boolean`  | `false`     | 允许进程绑定到本地端口（例如，用于开发服务器）                                                                                                                                                                                                 |
| `allowUnixSockets`        | `string[]` | `[]`        | 进程可访问的 Unix 套接字路径（例如，Docker 套接字）                                                                                                                                                                                              |
| `allowAllUnixSockets`     | `boolean`  | `false`     | 允许访问所有 Unix 套接字                                                                                                                                                                                                         |
| `httpProxyPort`           | `number`   | `undefined` | 用于网络请求的 HTTP 代理端口                                                                                                                                                                                                         |
| `socksProxyPort`          | `number`   | `undefined` | 用于网络请求的 SOCKS 代理端口                                                                                                                                                                                                        |

<Note>
  内置沙盒代理根据请求的主机名强制执行 `allowedDomains`，并且不会终止或检查 TLS 流量，因此诸如 [域名前置（domain fronting）](https://en.wikipedia.org/wiki/Domain_fronting) 之类的技术可能会绕过它。详情请参阅 [沙盒安全限制](/docs/en/sandboxing#security-limitations)，配置 TLS 终止代理请参阅 [安全部署](/docs/en/agent-sdk/secure-deployment#traffic-forwarding)。
</Note>

### `SandboxFilesystemConfig`

沙盒模式的文件系统特定配置。

```typescript theme={null}
type SandboxFilesystemConfig = {
  allowWrite?: string[];
  denyWrite?: string[];
  denyRead?: string[];
};
```

| 属性         | 类型       | 默认值 | 描述                                        |
| :----------- | :--------- | :------ | :------------------------------------------ |
| `allowWrite` | `string[]` | `[]`    | 允许写入访问的文件路径模式 |
| `denyWrite`  | `string[]` | `[]`    | 拒绝写入访问的文件路径模式  |
| `denyRead`   | `string[]` | `[]`    | 拒绝读取访问的文件路径模式  |

### 非沙盒命令的权限回退

启用 `allowUnsandboxedCommands` 后，模型可以通过在工具输入中设置 `dangerouslyDisableSandbox: true` 来请求在沙盒外运行命令。这些请求会回退到现有的权限系统，这意味着你的 `canUseTool` 处理程序会被调用，从而允许你实现自定义授权逻辑。在下面的示例中，`isCommandAuthorized` 代表你定义的授权检查。

<Note>
  **`excludedCommands` 与 `allowUnsandboxedCommands`：**

  * `excludedCommands`：一个静态命令列表，始终自动绕过沙盒（例如 `['docker']`）。模型对此没有控制权。
  * `allowUnsandboxedCommands`：让模型在运行时决定是否通过在工具输入中设置 `dangerouslyDisableSandbox: true` 来请求非沙盒执行。
</Note>

```typescript theme={null}
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "Deploy my application",
  options: {
    sandbox: {
      enabled: true,
      allowUnsandboxedCommands: true // Model can request unsandboxed execution
    },
    permissionMode: "default",
    canUseTool: async (tool, input) => {
      // Check if the model is requesting to bypass the sandbox
      if (tool === "Bash" && input.dangerouslyDisableSandbox) {
        // The model is requesting to run this command outside the sandbox
        console.log(`Unsandboxed command requested: ${input.command}`);

        if (isCommandAuthorized(input.command)) {
          return { behavior: "allow" as const, updatedInput: input };
        }
        return {
          behavior: "deny" as const,
          message: "Command not authorized for unsandboxed execution"
        };
      }
      return { behavior: "allow" as const, updatedInput: input };
    }
  }
})) {
  if ("result" in message) console.log(message.result);
}
```

此模式使你能够：

* **审计模型请求：** 记录模型请求非沙盒执行的情况
* **实现允许列表：** 仅允许特定命令在沙盒外运行
* **添加审批工作流：** 对特权操作要求显式授权

<Warning>
  使用 `dangerouslyDisableSandbox: true` 运行的命令具有完全的系统访问权限。请确保你的 `canUseTool` 处理程序仔细验证这些请求。

  如果 `permissionMode` 设置为 `bypassPermissions` 且启用了 `allowUnsandboxedCommands`，则模型可以在没有审批提示的情况下自主执行沙盒外的命令（显式的 [`ask` 规则](/docs/en/agent-sdk/permissions#how-permissions-are-evaluated) 仍会强制要求审批）。这种组合实际上允许模型悄无声息地逃离沙盒隔离。
</Warning>

## 另请参阅

* [SDK 概述](/docs/en/agent-sdk/overview) - 通用 SDK 概念
* [Python SDK 参考](/docs/en/agent-sdk/python) - Python SDK 文档
* [CLI 参考](/docs/en/cli-reference) - 命令行界面
* [常见工作流](/docs/en/common-workflows) - 分步指南

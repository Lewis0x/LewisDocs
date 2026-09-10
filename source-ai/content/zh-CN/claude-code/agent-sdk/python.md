---
title: Agent SDK 参考 - Python
source_id: claude-code/agent-sdk/python
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/agent-sdk/python
owner: Anthropic
content_sha256: 917ac55c62b67fee3d7b781ee491f8e6aedaf62994b45ae6d34b271e59f382f6
translation_of: claude-code/agent-sdk/python
translation_model: k3
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[官方来源](https://code.claude.com/docs/en/agent-sdk/python)

内容所有者: Anthropic

> ## 文档索引
> 获取完整的文档索引：https://code.claude.com/docs/llms.txt
> 在进一步探索之前，使用此文件发现所有可用页面。

# Agent SDK 参考 - Python

> Python Agent SDK 的完整 API 参考，包括所有函数、类型和类。

## 安装

将软件包安装到虚拟环境中。在较新的 Debian、Ubuntu 和 Homebrew Python 安装上，针对系统 Python 运行 `pip install` 会因 `error: externally-managed-environment` 而失败。

```bash theme={null}
python3 -m venv .venv
source .venv/bin/activate
pip install claude-agent-sdk
```

关于 uv、Windows PowerShell 和 API 密钥设置，请参阅 [Agent SDK 概述中的入门指南](/docs/en/agent-sdk/overview#get-started)。

## 在 `query()` 和 `ClaudeSDKClient` 之间选择

Python SDK 提供了两种与 Claude Code 交互的方式：

### 快速比较

| 功能                 | `query()`                                      | `ClaudeSDKClient`                  |
| :------------------ | :--------------------------------------------- | :--------------------------------- |
| **会话**             | 默认创建新会话                                | 复用同一会话                      |
| **对话**             | 单次交换                                      | 同一上下文中的多次交换            |
| **连接**             | 自动管理                                      | 手动控制                          |
| **流式输入**         | ✅ 支持                                       | ✅ 支持                            |
| **中断**             | ❌ 不支持                                     | ✅ 支持                            |
| **钩子**             | ✅ 支持                                       | ✅ 支持                            |
| **自定义工具**       | ✅ 支持                                       | ✅ 支持                            |
| **继续聊天**         | 通过 `continue_conversation` 或 `resume` 手动进行 | ✅ 自动                            |
| **使用场景**        | 一次性任务                                  | 持续性对话           |

### 何时使用 `query()`（一次性任务）

**最适合：**

* 不需要对话历史的一次性问题
* 不需要先前交流上下文的独立任务
* 简单的自动化脚本
* 当你希望每次都有全新开始时

### 何时使用 `ClaudeSDKClient`（连续对话）

**最适合：**

* **延续对话** - 当你需要 Claude 记住上下文时
* **后续问题** - 基于先前的回复继续推进
* **交互式应用** - 聊天界面、REPL
* **响应驱动逻辑** - 当下一步操作取决于 Claude 的响应时
* **会话控制** - 显式管理对话生命周期

## 函数

<Note>本页中的签名块以及裸露的 `async for` / `async with` 片段均为示意。要运行它们，请将主体包裹在 `async def main(): ...` 中并调用 `asyncio.run(main())`。</Note>

### `query()`

默认情况下，每次与 Claude Code 交互都会创建一个新会话。返回一个异步迭代器，并在消息到达时逐条产出。每次调用 `query()` 都会全新开始，不保留先前交互的记忆，除非你传入 `continue_conversation=True` 或 `resume` 到 [`ClaudeAgentOptions`](#claudeagentoptions) 中。参见 [会话](/docs/en/agent-sdk/sessions)。

```python theme={null}
async def query(
    *,
    prompt: str | AsyncIterable[dict[str, Any]],
    options: ClaudeAgentOptions | None = None,
    transport: Transport | None = None
) -> AsyncIterator[Message]
```

#### 参数

| 参数   | 类型                         | 描述                                                                |
| :---------- | :--------------------------- | :------------------------------------------------------------------------- |
| `prompt`    | `str \| AsyncIterable[dict]` | 作为字符串或用于流式模式的异步可迭代对象的输入提示          |
| `options`   | `ClaudeAgentOptions \| None` | 可选配置对象（如果为 None，则默认为 `ClaudeAgentOptions()`） |
| `transport` | `Transport \| None`          | 用于与 CLI 进程通信的可选自定义传输           |

#### 返回值

返回一个 `AsyncIterator[Message]`，用于生成对话中的消息。

#### 示例 - 带选项

```python theme={null}
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions


async def main():
    options = ClaudeAgentOptions(
        system_prompt="You are an expert Python developer",
        permission_mode="acceptEdits",
    )

    async for message in query(prompt="Create a Python web server", options=options):
        print(message)


asyncio.run(main())
```

### `tool()`

用于以类型安全的方式定义 MCP 工具的装饰器。

```python theme={null}
def tool(
    name: str,
    description: str,
    input_schema: type | dict[str, Any],
    annotations: ToolAnnotations | None = None
) -> Callable[[Callable[[Any], Awaitable[dict[str, Any]]]], SdkMcpTool[Any]]
```

#### 参数

| 参数      | 类型                                            | 描述                                                         |
| :------------- | :---------------------------------------------- | :------------------------------------------------------------------ |
| `name`         | `str`                                           | 工具的唯一标识符                                      |
| `description`  | `str`                                           | 工具功能的可读描述                    |
| `input_schema` | `type \| dict[str, Any]`                        | 定义工具输入参数的架构（见下文）             |
| `annotations`  | [`ToolAnnotations`](#toolannotations)` \| None` | 可选的 MCP 工具注解，向客户端提供行为提示 |

#### 输入架构选项

1. **简单类型映射**（推荐）：

   ```python theme={null}
   {"text": str, "count": int, "enabled": bool}
   ```

2. **JSON Schema 格式**（用于复杂验证）：
   ```python theme={null}
   {
       "type": "object",
       "properties": {
           "text": {"type": "string"},
           "count": {"type": "integer", "minimum": 0},
       },
       "required": ["text"],
   }
   ```

#### 返回值

一个装饰器函数，它包装工具实现并返回一个 `SdkMcpTool` 实例。

#### 示例

```python theme={null}
from claude_agent_sdk import tool
from typing import Any


@tool("greet", "Greet a user", {"name": str})
async def greet(args: dict[str, Any]) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": f"Hello, {args['name']}!"}]}
```

#### `ToolAnnotations`

重新导出自 `mcp.types`（也可通过 `from claude_agent_sdk import ToolAnnotations` 获取）。所有字段都是可选提示；客户端不应依赖它们做出安全决策。

| 字段             | 类型           | 默认值 | 描述                                                                                                                                          |
| :---------------- | :------------- | :------ | :--------------------------------------------------------------------------------------------------------------------------------------------------- |
| `title`           | `str \| None`  | `None`  | 工具的可读标题                                                                                                                    |
| `readOnlyHint`    | `bool \| None` | `False` | 如果为 `True`，则该工具不会修改其环境                                                                                                  |
| `destructiveHint` | `bool \| None` | `True`  | 如果为 `True`，则该工具可能执行破坏性更新（仅在 `readOnlyHint` 为 `False` 时有意义）                                                 |
| `idempotentHint`  | `bool \| None` | `False` | 如果为 `True`，则使用相同参数的重复调用没有额外效果（仅在 `readOnlyHint` 为 `False` 时有意义）                         |
| `openWorldHint`   | `bool \| None` | `True`  | 如果为 `True`，则该工具与外部实体交互（例如网络搜索）。如果为 `False`，则该工具的作用域是封闭的（例如内存工具） |

```python theme={null}
from claude_agent_sdk import tool, ToolAnnotations
from typing import Any


@tool(
    "search",
    "Search the web",
    {"query": str},
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
)
async def search(args: dict[str, Any]) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": f"Results for: {args['query']}"}]}
```

### `create_sdk_mcp_server()`

创建一个在您的 Python 应用程序内运行的进程内 MCP 服务器。

```python theme={null}
def create_sdk_mcp_server(
    name: str,
    version: str = "1.0.0",
    tools: list[SdkMcpTool[Any]] | None = None
) -> McpSdkServerConfig
```

#### 参数

| 参数 | 类型                            | 默认值   | 描述                                           |
| :-------- | :------------------------------ | :-------- | :---------------------------------------------------- |
| `name`    | `str`                           | -         | 服务器的唯一标识符                      |
| `version` | `str`                           | `"1.0.0"` | 服务器版本字符串                                 |
| `tools`   | `list[SdkMcpTool[Any]] \| None` | `None`    | 使用 `@tool` 装饰器创建的工具函数列表 |

#### 返回值

返回一个 `McpSdkServerConfig` 对象，可传递给 `ClaudeAgentOptions.mcp_servers`。

#### 示例

```python theme={null}
from claude_agent_sdk import tool, create_sdk_mcp_server, ClaudeAgentOptions


@tool("add", "Add two numbers", {"a": float, "b": float})
async def add(args):
    return {"content": [{"type": "text", "text": f"Sum: {args['a'] + args['b']}"}]}


@tool("multiply", "Multiply two numbers", {"a": float, "b": float})
async def multiply(args):
    return {"content": [{"type": "text", "text": f"Product: {args['a'] * args['b']}"}]}


calculator = create_sdk_mcp_server(
    name="calculator",
    version="2.0.0",
    tools=[add, multiply],  # Pass decorated functions
)

# Use with Claude

options = ClaudeAgentOptions(
    mcp_servers={"calc": calculator},
    allowed_tools=["mcp__calc__add", "mcp__calc__multiply"],
)
```

### `list_sessions()`

列出带元数据的历史会话。可按项目目录筛选，或列出所有项目中的会话。同步执行；立即返回。

```python theme={null}
def list_sessions(
    directory: str | None = None,
    limit: int | None = None,
    offset: int = 0,
    include_worktrees: bool = True
) -> list[SDKSessionInfo]
```

#### 参数

| 参数           | 类型          | 默认值 | 描述                                                                                      |
| :------------------ | :------------ | :------ | :----------------------------------------------------------------------------------------------- |
| `directory`         | `str \| None` | `None`  | 要列出会话的目录。省略时，返回所有项目中的会话               |
| `limit`             | `int \| None` | `None`  | 返回的最大会话数                                                             |
| `offset`            | `int`         | `0`     | 从排序结果开头跳过的会话数。与 `limit` 配合用于分页 |
| `include_worktrees` | `bool`        | `True`  | 当 `directory` 位于 git 仓库中时，包含来自所有 worktree 路径的会话            |

#### 返回类型：`SDKSessionInfo`

| 属性        | 类型          | 描述                                                          |
| :-------------- | :------------ | :------------------------------------------------------------------- |
| `session_id`    | `str`         | 唯一会话标识符                                            |
| `summary`       | `str`         | 显示标题：自定义标题、自动生成的摘要或第一条提示 |
| `last_modified` | `int`         | 自纪元以来以毫秒计的最后修改时间                       |
| `file_size`     | `int \| None` | 会话文件大小（字节）（远程存储后端为 `None`）      |
| `custom_title`  | `str \| None` | 用户设置的会话标题                                               |
| `first_prompt`  | `str \| None` | 会话中第一条有意义的用户提示                          |
| `git_branch`    | `str \| None` | 会话结束时的 Git 分支                                 |
| `cwd`           | `str \| None` | 会话的工作目录                                    |
| `tag`           | `str \| None` | 用户设置的会话标签（参见 [`tag_session()`](#tag_session)）           |
| `created_at`    | `int \| None` | 自纪元以来以毫秒计的会话创建时间                    |

#### 示例

打印某个项目最近的 10 个会话。结果按 `last_modified` 降序排序，因此第一项是最新的。省略 `directory` 可跨所有项目搜索。

```python theme={null}
from claude_agent_sdk import list_sessions

for session in list_sessions(directory="/path/to/project", limit=10):
    print(f"{session.summary} ({session.session_id})")
```

### `get_session_messages()`

检索历史会话中的消息。同步执行；立即返回。

```python theme={null}
def get_session_messages(
    session_id: str,
    directory: str | None = None,
    limit: int | None = None,
    offset: int = 0
) -> list[SessionMessage]
```

#### 参数

| 参数    | 类型          | 默认值  | 描述                                                       |
| :----------- | :------------ | :------- | :---------------------------------------------------------------- |
| `session_id` | `str`         | 必填 | 要检索消息的会话 ID                           |
| `directory`  | `str \| None` | `None`   | 要查找的项目目录。省略时，搜索所有项目 |
| `limit`      | `int \| None` | `None`   | 返回的最大消息数                              |
| `offset`     | `int`         | `0`      | 从开头跳过的消息数                         |

#### 返回类型：`SessionMessage`

| 属性             | 类型                           | 描述               |
| :------------------- | :----------------------------- | :------------------------ |
| `type`               | `Literal["user", "assistant"]` | 消息角色              |
| `uuid`               | `str`                          | 唯一消息标识符 |
| `session_id`         | `str`                          | 会话标识符        |
| `message`            | `Any`                          | 原始消息内容       |
| `parent_tool_use_id` | `None`                         | 保留以供将来使用   |

#### 示例

```python theme={null}
from claude_agent_sdk import list_sessions, get_session_messages

sessions = list_sessions(limit=1)
if sessions:
    messages = get_session_messages(sessions[0].session_id)
    for msg in messages:
        print(f"[{msg.type}] {msg.uuid}")
```

### `get_session_info()`

按 ID 读取单个会话的元数据，无需扫描完整项目目录。同步执行；立即返回。

```python theme={null}
def get_session_info(
    session_id: str,
    directory: str | None = None,
) -> SDKSessionInfo | None
```

#### 参数

| 参数    | 类型          | 默认值  | 描述                                                            |
| :----------- | :------------ | :------- | :--------------------------------------------------------------------- |
| `session_id` | `str`         | 必填 | 要查找的会话的 UUID                                         |
| `directory`  | `str \| None` | `None`   | 项目目录路径。省略时，搜索所有项目目录 |

返回 [`SDKSessionInfo`](#return-type-sdksessioninfo)，如果未找到会话则返回 `None`。

#### 示例

查找单个会话的元数据，无需扫描项目目录。当你已有上一次运行获得的会话 ID 时很有用。

```python theme={null}
from claude_agent_sdk import get_session_info

info = get_session_info("550e8400-e29b-41d4-a716-446655440000")
if info:
    print(f"{info.summary} (branch: {info.git_branch}, tag: {info.tag})")
```

### `rename_session()`

通过追加自定义标题条目来重命名会话。重复调用是安全的；以最新的标题为准。同步执行。

```python theme={null}
def rename_session(
    session_id: str,
    title: str,
    directory: str | None = None,
) -> None
```

#### 参数

| 参数    | 类型          | 默认值  | 描述                                                            |
| :----------- | :------------ | :------- | :--------------------------------------------------------------------- |
| `session_id` | `str`         | 必填 | 要重命名的会话的 UUID                                          |
| `title`      | `str`         | 必填 | 新标题。去除空白字符后不得为空                |
| `directory`  | `str \| None` | `None`   | 项目目录路径。省略时，搜索所有项目目录 |

如果 `session_id` 不是有效的 UUID 或 `title` 为空，则抛出 `ValueError`；如果找不到会话，则抛出 `FileNotFoundError`。

#### 示例

重命名最近的会话，以便日后更容易找到。新标题会在后续读取时出现在 [`SDKSessionInfo.custom_title`](#return-type-sdksessioninfo) 中。

```python theme={null}
from claude_agent_sdk import list_sessions, rename_session

sessions = list_sessions(directory="/path/to/project", limit=1)
if sessions:
    rename_session(sessions[0].session_id, "Refactor auth module")
```

### `tag_session()`

为会话添加标签。传入 `None` 可清除标签。重复调用是安全的；以最新的标签为准。同步执行。

```python theme={null}
def tag_session(
    session_id: str,
    tag: str | None,
    directory: str | None = None,
) -> None
```

#### 参数

| 参数    | 类型          | 默认值  | 描述                                                            |
| :----------- | :------------ | :------- | :--------------------------------------------------------------------- |
| `session_id` | `str`         | 必填 | 要标记的会话的 UUID                                             |
| `tag`        | `str \| None` | 必填 | 标签字符串，或 `None` 以清除。存储前进行 Unicode 清理       |
| `directory`  | `str \| None` | `None`   | 项目目录路径。省略时，搜索所有项目目录 |

如果 `session_id` 不是有效的 UUID，或 `tag` 在清理后为空，则抛出 `ValueError`；如果找不到会话，则抛出 `FileNotFoundError`。

#### 示例

标记一个会话，然后在后续读取中按该标签筛选。传入 `None` 可清除现有标签。

```python theme={null}
from claude_agent_sdk import list_sessions, tag_session

# Tag the most recent session

sessions = list_sessions(directory="/path/to/project", limit=1)
if sessions:
    tag_session(sessions[0].session_id, "needs-review")

# Later: find all sessions with that tag

for session in list_sessions(directory="/path/to/project"):
    if session.tag == "needs-review":
        print(session.summary)
```

## 类

### `ClaudeSDKClient`

**在多次交换中维护一个对话会话。** 这相当于 TypeScript SDK 的 `query()` 函数在内部的工作方式的 Python 版本——它会创建一个可以继续对话的客户端对象。

#### 关键特性

* **会话连续性**：在多次 `query()` 调用之间维护对话上下文
* **同一对话**：会话会保留先前的消息
* **中断支持**：可以在任务执行中途停止
* **显式生命周期**：由你控制会话何时开始和结束
* **响应驱动流程**：可以对响应作出反应并发送后续消息
* **自定义工具和钩子**：支持自定义工具（使用 `@tool` 装饰器创建）和钩子

```python theme={null}
class ClaudeSDKClient:
    def __init__(self, options: ClaudeAgentOptions | None = None, transport: Transport | None = None)
    async def connect(self, prompt: str | AsyncIterable[dict] | None = None) -> None
    async def query(self, prompt: str | AsyncIterable[dict], session_id: str = "default") -> None
    async def receive_messages(self) -> AsyncIterator[Message]
    async def receive_response(self) -> AsyncIterator[Message]
    async def interrupt(self) -> None
    async def set_permission_mode(self, mode: str) -> None
    async def set_model(self, model: str | None = None) -> None
    async def rewind_files(self, user_message_id: str) -> None
    async def get_mcp_status(self) -> McpStatusResponse
    async def reconnect_mcp_server(self, server_name: str) -> None
    async def toggle_mcp_server(self, server_name: str, enabled: bool) -> None
    async def stop_task(self, task_id: str) -> None
    async def get_server_info(self) -> dict[str, Any] | None
    async def disconnect(self) -> None
```

#### 方法

| 方法                                    | 描述                                                                                                                                                       |
| :---------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `__init__(options)`                       | 使用可选配置初始化客户端                                                                                                                 |
| `connect(prompt)`                         | 使用可选的初始提示或消息流连接到 Claude                                                                                               |
| `query(prompt, session_id)`               | 以流式模式发送新请求                                                                                                                              |
| `receive_messages()`                      | 以异步迭代器接收来自 Claude 的所有消息                                                                                                             |
| `receive_response()`                      | 接收消息，直到并包含 ResultMessage                                                                                                              |
| `interrupt()`                             | 发送中断信号（仅在流式模式下有效）                                                                                                              |
| `set_permission_mode(mode)`               | 更改当前会话的权限模式                                                                                                                |
| `set_model(model)`                        | 更改当前会话的模型。传入 `None` 可重置为默认值                                                                                         |
| `rewind_files(user_message_id)`           | 将文件恢复到指定用户消息时的状态。需要 `enable_file_checkpointing=True`。请参阅[文件检查点](/docs/en/agent-sdk/file-checkpointing) |
| `get_mcp_status()`                        | 获取所有已配置 MCP 服务器的状态。返回 [`McpStatusResponse`](#mcpstatusresponse)                                                                   |
| `reconnect_mcp_server(server_name)`       | 重新连接失败或已断开连接的 MCP 服务器                                                                                                 |
| `toggle_mcp_server(server_name, enabled)` | 在会话期间启用或禁用 MCP 服务器。禁用会移除其工具                                                                                          |
| `stop_task(task_id)`                      | 停止正在运行的后台任务。消息流中随后会出现一个状态为 `"stopped"` 的 [`TaskNotificationMessage`](#tasknotificationmessage)                     |
| `get_server_info()`                       | 获取服务器信息，包括会话 ID 和能力                                                                                                      |
| `disconnect()`                            | 断开与 Claude 的连接                                                                                                                                            |

#### 上下文管理器支持

客户端可以用作异步上下文管理器，以自动管理连接：

```python theme={null}
import asyncio
from claude_agent_sdk import ClaudeSDKClient


async def main():
    async with ClaudeSDKClient() as client:
        await client.query("Hello Claude")
        async for message in client.receive_response():
            print(message)


asyncio.run(main())
```

> **重要提示：** 在迭代消息时，避免使用 `break` 提前退出，因为这可能导致 asyncio 清理问题。相反，应让迭代自然完成，或使用标志来跟踪何时找到所需内容。

#### 示例 - 继续对话

```python theme={null}
import asyncio
from claude_agent_sdk import ClaudeSDKClient, AssistantMessage, TextBlock, ResultMessage


async def main():
    async with ClaudeSDKClient() as client:
        # First question
        await client.query("What's the capital of France?")

        # Process response
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude: {block.text}")

        # Follow-up question - the session retains the previous context
        await client.query("What's the population of that city?")

        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude: {block.text}")

        # Another follow-up - still in the same conversation
        await client.query("What are some famous landmarks there?")

        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude: {block.text}")


asyncio.run(main())
```

#### 示例 - 使用 ClaudeSDKClient 进行流式输入

```python theme={null}
import asyncio
from claude_agent_sdk import ClaudeSDKClient


async def message_stream():
    """Generate messages dynamically."""
    yield {
        "type": "user",
        "message": {"role": "user", "content": "Analyze the following data:"},
    }
    await asyncio.sleep(0.5)
    yield {
        "type": "user",
        "message": {"role": "user", "content": "Temperature: 25°C, Humidity: 60%"},
    }
    await asyncio.sleep(0.5)
    yield {
        "type": "user",
        "message": {"role": "user", "content": "What patterns do you see?"},
    }


async def main():
    async with ClaudeSDKClient() as client:
        # Stream input to Claude
        await client.query(message_stream())

        # Process response
        async for message in client.receive_response():
            print(message)

        # Follow-up in same session
        await client.query("Should we be concerned about these readings?")

        async for message in client.receive_response():
            print(message)


asyncio.run(main())
```

#### 示例 - 使用中断

```python theme={null}
import asyncio
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, ResultMessage


async def interruptible_task():
    options = ClaudeAgentOptions(allowed_tools=["Bash"], permission_mode="acceptEdits")

    async with ClaudeSDKClient(options=options) as client:
        # Start a long-running task
        await client.query("Count from 1 to 100 slowly, using the bash sleep command")

        # Let it run for a bit
        await asyncio.sleep(2)

        # Interrupt the task
        await client.interrupt()
        print("Task interrupted!")

        # Drain the interrupted task's messages (including its ResultMessage)
        async for message in client.receive_response():
            if isinstance(message, ResultMessage):
                print(f"Interrupted task finished with subtype={message.subtype!r}")
                # subtype is "error_during_execution" for interrupted tasks

        # Send a new command
        await client.query("Just say hello instead")

        # Now receive the new response
        async for message in client.receive_response():
            if isinstance(message, ResultMessage) and message.subtype == "success":
                print(f"New result: {message.result}")


asyncio.run(interruptible_task())
```

<Note>
  **中断后的缓冲区行为：** `interrupt()` 发送停止信号，但不会清除消息缓冲区。被中断任务已生成的消息（包括其 `ResultMessage`，带有 `subtype="error_during_execution"`）仍保留在流中。在读取新查询的响应之前，必须使用 `receive_response()` 将它们排空。如果在 `interrupt()` 之后立即发送新查询并只调用一次 `receive_response()`，你将收到被中断任务的消息，而不是新查询的响应。
</Note>

#### 示例 - 高级权限控制

```python theme={null}
import asyncio
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
from claude_agent_sdk.types import (
    PermissionResultAllow,
    PermissionResultDeny,
    ToolPermissionContext,
)


async def custom_permission_handler(
    tool_name: str, input_data: dict, context: ToolPermissionContext
) -> PermissionResultAllow | PermissionResultDeny:
    """Custom logic for tool permissions."""

    # Block writes to system directories
    if tool_name == "Write" and input_data.get("file_path", "").startswith("/system/"):
        return PermissionResultDeny(
            message="System directory write not allowed", interrupt=True
        )

    # Redirect sensitive file operations
    if tool_name in ["Write", "Edit"] and "config" in input_data.get("file_path", ""):
        safe_path = f"./sandbox/{input_data['file_path']}"
        return PermissionResultAllow(
            updated_input={**input_data, "file_path": safe_path}
        )

    # Allow everything else
    return PermissionResultAllow(updated_input=input_data)


async def main():
    # Don't also list the gated tools in allowed_tools: allow rules approve calls before can_use_tool runs
    options = ClaudeAgentOptions(can_use_tool=custom_permission_handler)

    async with ClaudeSDKClient(options=options) as client:
        await client.query("Update the system config file")

        async for message in client.receive_response():
            # Will use sandbox path instead
            print(message)


asyncio.run(main())
```

## 类型

<Note>
  **`@dataclass` 与 `TypedDict`：** 此 SDK 使用两种类型。使用 `@dataclass` 装饰的类（如 `ResultMessage`、`AgentDefinition`、`TextBlock`）在运行时是对象实例，支持属性访问：`msg.result`。使用 `TypedDict` 定义的类（如 `ThinkingConfigEnabled`、`McpStdioServerConfig`、`SyncHookJSONOutput`）在运行时是**普通字典**，需要键访问：`config["budget_tokens"]`，而不是 `config.budget_tokens`。`ClassName(field=value)` 调用语法对两者都适用，但只有 dataclass 会生成具有属性的对象。
</Note>

### `SdkMcpTool`

使用 `@tool` 装饰器创建的 SDK MCP 工具的定义。

```python theme={null}
@dataclass
class SdkMcpTool(Generic[T]):
    name: str
    description: str
    input_schema: type[T] | dict[str, Any]
    handler: Callable[[T], Awaitable[dict[str, Any]]]
    annotations: ToolAnnotations | None = None
```

| 属性           | 类型                                       | 描述                                                                                                     |
| :------------- | :----------------------------------------- | :--------------------------------------------------------------------------------------------------------- |
| `name`         | `str`                                      | 工具的唯一标识符                                                                                         |
| `description`  | `str`                                      | 人类可读的描述                                                                                           |
| `input_schema` | `type[T] \| dict[str, Any]`                | 用于输入验证的模式（Schema）                                                                             |
| `handler`      | `Callable[[T], Awaitable[dict[str, Any]]]` | 处理工具执行的异步函数                                                                                   |
| `annotations`  | `ToolAnnotations \| None`                  | 可选的 MCP 工具注解（例如 `readOnlyHint`、`destructiveHint`、`openWorldHint`）。来自 `mcp.types` |

### `Transport`

自定义传输实现的抽象基类。使用它通过自定义通道与 Claude 进程通信（例如，通过远程连接而不是本地子进程）。

<Warning>
  这是一个低级别的内部 API。该接口可能在未来版本中发生变化。自定义实现必须更新以匹配任何接口变更。
</Warning>

```python theme={null}
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any


class Transport(ABC):
    @abstractmethod
    async def connect(self) -> None: ...

    @abstractmethod
    async def write(self, data: str) -> None: ...

    @abstractmethod
    def read_messages(self) -> AsyncIterator[dict[str, Any]]: ...

    @abstractmethod
    async def close(self) -> None: ...

    @abstractmethod
    def is_ready(self) -> bool: ...

    @abstractmethod
    async def end_input(self) -> None: ...
```

| 方法                | 描述                                                                      |
| :---------------- | :-------------------------------------------------------------------------- |
| `connect()`       | 连接传输并准备通信                                                        |
| `write(data)`     | 向传输写入原始数据（JSON + 换行符）                                       |
| `read_messages()` | 异步迭代器，产出解析后的 JSON 消息                                        |
| `close()`         | 关闭连接并清理资源                                                        |
| `is_ready()`      | 如果传输可以收发数据则返回 `True`                              |
| `end_input()`     | 关闭输入流（例如，为子进程传输关闭 stdin）                                |

导入：`from claude_agent_sdk import Transport`

### `ClaudeAgentOptions`

Claude Code 查询的配置数据类。

```python theme={null}
@dataclass
class ClaudeAgentOptions:
    tools: list[str] | ToolsPreset | None = None
    allowed_tools: list[str] = field(default_factory=list)
    system_prompt: str | SystemPromptPreset | SystemPromptFile | None = None
    mcp_servers: dict[str, McpServerConfig] | str | Path = field(default_factory=dict)
    strict_mcp_config: bool = False
    permission_mode: PermissionMode | None = None
    continue_conversation: bool = False
    resume: str | None = None
    session_id: str | None = None
    max_turns: int | None = None
    max_budget_usd: float | None = None
    disallowed_tools: list[str] = field(default_factory=list)
    model: str | None = None
    fallback_model: str | None = None
    betas: list[SdkBeta] = field(default_factory=list)
    output_format: dict[str, Any] | None = None
    permission_prompt_tool_name: str | None = None
    cwd: str | Path | None = None
    cli_path: str | Path | None = None
    settings: str | None = None
    add_dirs: list[str | Path] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    extra_args: dict[str, str | None] = field(default_factory=dict)
    max_buffer_size: int | None = None
    debug_stderr: Any = sys.stderr  # Deprecated
    stderr: Callable[[str], None] | None = None
    can_use_tool: CanUseTool | None = None
    hooks: dict[HookEvent, list[HookMatcher]] | None = None
    user: str | None = None
    include_partial_messages: bool = False
    include_hook_events: bool = False
    fork_session: bool = False
    agents: dict[str, AgentDefinition] | None = None
    setting_sources: list[SettingSource] | None = None
    skills: list[str] | Literal["all"] | None = None
    sandbox: SandboxSettings | None = None
    plugins: list[SdkPluginConfig] = field(default_factory=list)
    max_thinking_tokens: int | None = None  # Deprecated: use thinking instead
    thinking: ThinkingConfig | None = None
    effort: EffortLevel | None = None
    enable_file_checkpointing: bool = False
    session_store: SessionStore | None = None
    session_store_flush: SessionStoreFlushMode = "batched"
    load_timeout_ms: int = 60_000
    task_budget: TaskBudget | None = None
```

| 属性                      | 类型                                                                                  | 默认值                            | 描述                                                                                                                                                                                                         |
| :---------------------------- | :------------------------------------------------------------------------------------ | :--------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `tools`                       | `list[str] \| ToolsPreset \| None`                                                    | `None`                             | 工具配置。使用 `{"type": "preset", "preset": "claude_code"}` 可获得 Claude Code 的默认工具                                                                                                                                                                                                         |
| `allowed_tools`               | `list[str]`                                                                           | `[]`                               | 无需提示即可自动批准的工具。这不会将 Claude 限制为仅使用这些工具；未列出的工具将交由 `permission_mode` 和 `can_use_tool` 处理。使用 `disallowed_tools` 可阻止工具。参见 [权限](/docs/en/agent-sdk/permissions#allow-and-deny-rules)                                                                                                                                                                                                         |
| `system_prompt`               | `str \| SystemPromptPreset \| SystemPromptFile \| None`                               | `None`                             | 系统提示配置。传入字符串以使用自定义提示，传入 `{"type": "preset", "preset": "claude_code"}` 以使用 Claude Code 的系统提示（可选 `"append"`），或传入 `{"type": "file", "path": "..."}` 以从磁盘加载大型提示。参见 [`SystemPromptPreset`](#systempromptpreset) 和 [`SystemPromptFile`](#systempromptfile)                                                                                                                                                                                                         |
| `mcp_servers`                 | `dict[str, McpServerConfig] \| str \| Path`                                           | `{}`                               | MCP 服务器配置或配置文件路径                                                                                                                                                                                                         |
| `strict_mcp_config`           | `bool`                                                                                | `False`                            | 当 `True` 时，仅使用传入 `mcp_servers` 的服务器，并忽略项目 `.mcp.json`、用户设置、插件提供的 MCP 服务器以及 [claude.ai 连接器](/docs/en/mcp#use-mcp-servers-from-claude-ai)。映射到 CLI `--strict-mcp-config` 标志                                                                                                                                                                                                         |
| `permission_mode`             | `PermissionMode \| None`                                                              | `None`                             | 工具使用的权限模式                                                                                                                                                                                                         |
| `continue_conversation`       | `bool`                                                                                | `False`                            | 继续最近的对话                                                                                                                                                                                                         |
| `resume`                      | `str \| None`                                                                         | `None`                             | 要恢复的会话 ID                                                                                                                                                                                                         |
| `session_id`                  | `str \| None`                                                                         | `None`                             | 使用指定的会话 ID 而不是自动生成的 ID。必须是有效的 UUID。不能与 `continue_conversation` 或 `resume` 组合使用，除非同时设置了 `fork_session`                                                                                                                                                                                                                                                                                                                                                                                               |
| `max_turns`                   | `int \| None`                                                                         | `None`                             | 最大智能体轮次（工具使用往返次数）                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| `max_budget_usd`              | `float \| None`                                                                       | `None`                             | 当客户端成本估算达到此美元值时停止查询。与 `total_cost_usd` 所依据的同一估算值进行比较；有关准确性注意事项，请参阅 [跟踪成本和使用情况](/docs/en/agent-sdk/cost-tracking)                                                                                                                                                                                                                                                                                                                                                                                       |
| `disallowed_tools`            | `list[str]`                                                                           | `[]`                               | 要拒绝的工具。像 `"Bash"` 这样的裸名称会将该工具从 Claude 的上下文中移除。像 `"Bash(rm *)"` 这样的作用域规则会保留该工具可用，并在每种权限模式下（包括 `bypassPermissions`）拒绝匹配的调用。请参阅 [权限](/docs/en/agent-sdk/permissions#allow-and-deny-rules)                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `enable_file_checkpointing`   | `bool`                                                                                | `False`                            | 启用文件更改跟踪以支持回退。请参阅 [文件检查点](/docs/en/agent-sdk/file-checkpointing)                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `model`                       | `str \| None`                                                                         | `None`                             | Claude 模型别名或完整模型名称。请参阅[接受的值和特定于提供商的 ID](/docs/en/model-config#available-models)                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| `fallback_model`              | `str \| None`                                                                         | `None`                             | 主模型失败时使用的备用模型                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `betas`                       | `list[SdkBeta]`                                                                       | `[]`                               | 要启用的 Beta 功能。有关可用选项，请参阅[`SdkBeta`](#sdkbeta)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| `output_format`               | `dict[str, Any] \| None`                                                              | `None`                             | 结构化响应的输出格式（例如 `{"type": "json_schema", "schema": {...}}`）。详情请参阅[结构化输出](/docs/en/agent-sdk/structured-outputs)                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `permission_prompt_tool_name` | `str \| None`                                                                         | `None`                             | 用于权限提示的 MCP 工具名称                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `cwd`                         | `str \| Path \| None`                                                                 | `None`                             | 当前工作目录                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| `cli_path`                    | `str \| Path \| None`                                                                 | `None`                             | Claude Code CLI 可执行文件的自定义路径                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `settings`                    | `str \| None`                                                                         | `None`                             | 设置文件路径                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| `add_dirs`                    | `list[str \| Path]`                                                                   | `[]`                               | Claude 可访问的附加目录                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| `env`                         | `dict[str, str]`                                                                      | `{}`                               | 合并到继承的进程环境之上的环境变量。底层 CLI 读取的变量请参阅 [环境变量](/docs/en/env-vars)，超时相关变量请参阅 [处理缓慢或停滞的 API 响应](#handle-slow-or-stalled-api-responses)                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `extra_args`                  | `dict[str, str \| None]`                                                              | `{}`                               | 要直接传递给 CLI 的附加 CLI 参数                                                                                                                                                                                                         |
| `max_buffer_size`             | `int \| None`                                                                         | `None`                             | 缓冲 CLI stdout 时的最大字节数                                                                                                                                                                                                         |
| `debug_stderr`                | `Any`                                                                                 | `sys.stderr`                       | *已弃用* - 用于调试输出的类文件对象。请改用 `stderr` 回调                                                                                                                                                                                                         |
| `stderr`                      | `Callable[[str], None] \| None`                                                       | `None`                             | 用于处理 CLI stderr 输出的回调函数                                                                                                                                                                                                         |
| `can_use_tool`                | [`CanUseTool`](#canusetool) ` \| None`                                                | `None`                             | 工具权限回调,仅当 [权限流程](/docs/en/agent-sdk/permissions#how-permissions-are-evaluated) 落到提示时才调用。对于由 `allowed_tools`、allow 规则或 `permission_mode` 自动批准的调用不会调用。`AskUserQuestion`,连接器工具 [你的组织设置为 `ask`](/docs/en/mcp#organization-controls-on-connector-tools),以及标记为 [`requiresUserInteraction`](/docs/en/mcp#require-approval-for-a-specific-tool) 的 MCP 工具即使已被允许也会到达它;在 `dontAsk` 模式下这些会被直接拒绝。详见 [`CanUseTool`](#canusetool) |
| `hooks`                       | `dict[HookEvent, list[HookMatcher]] \| None`                                          | `None`                             | 用于拦截事件的钩子配置                                                                                                                                                                                                         |
| `user`                        | `str \| None`                                                                         | `None`                             | 用户标识符                                                                                                                                                                                                         |
| `include_partial_messages`    | `bool`                                                                                | `False`                            | 包含部分消息流事件。启用后，将生成 [`StreamEvent`](#streamevent) 消息                                                                                                                                                                                                         |
| `include_hook_events`         | `bool`                                                                                | `False`                            | 在消息流中以 `HookEventMessage` 对象的形式包含钩子生命周期事件                                                                                                                                                                                                         |
| `fork_session`                | `bool`                                                                                | `False`                            | 使用 `resume` 恢复时，分叉到一个新的会话 ID，而不是继续原有会话                                                                                                                                                                                                         |
| `agents`                      | `dict[str, AgentDefinition] \| None`                                                  | `None`                             | 以编程方式定义的子代理                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| `plugins`                     | `list[SdkPluginConfig]`                                                               | `[]`                               | 从本地路径加载自定义插件。详见 [插件](/docs/en/agent-sdk/plugins)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| `sandbox`                     | [`SandboxSettings`](#sandboxsettings) ` \| None`                                      | `None`                             | 以编程方式配置沙盒行为。详见 [沙盒设置](#sandboxsettings)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `setting_sources`             | `list[SettingSource] \| None`                                                         | `None`（CLI 默认值：所有来源）| 控制加载哪些文件系统设置。传入 `[]` 可禁用用户、项目和本地设置。端点管理的策略始终都会加载；当会话在[符合条件的配置](/docs/en/server-managed-settings#platform-availability)上使用组织凭据进行身份验证时，会获取服务器管理的设置。参见 [使用 Claude Code 功能](/docs/en/agent-sdk/claude-code-features#what-settingsources-does-not-control)                                                                                                                                                           |
| `skills`                      | `list[str] \| Literal["all"] \| None`                                                 | `None`                             | 会话可用的技能。传入 `"all"` 可启用每个已发现的技能，或传入技能名称列表。设置后，SDK 会自动将 Skill 工具添加到 `allowed_tools`。如果你还传入 `tools`，请在该列表中包含 `"Skill"`。参见 [技能](/docs/en/agent-sdk/skills)                                                                                                                                                                                                                                                                                                                       |
| `max_thinking_tokens`         | `int \| None`                                                                         | `None`                             | *已弃用* - 思考块的最大令牌数。请改用 `thinking`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| `thinking`                    | [`ThinkingConfig`](#thinkingconfig) ` \| None`                                        | `None`                             | 控制扩展思考行为。优先级高于 `max_thinking_tokens`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `effort`                      | [`EffortLevel`](#effortlevel) ` \| None`                                              | `None`                             | 思考深度的努力级别。参见 [调整努力级别](/docs/en/model-config#adjust-effort-level)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `session_store`               | [`SessionStore`](/docs/en/agent-sdk/session-storage#the-sessionstore-interface) ` \| None` | `None`                             | 将会话记录镜像到外部后端，以便任何主机都可以恢复它们。参见 [将会话持久化到外部存储](/docs/en/agent-sdk/session-storage)                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| `session_store_flush`         | `Literal["batched", "eager"]`                                                         | `"batched"`                        | 何时将镜像的记录条目刷新到 `session_store`。`"batched"` 每轮刷新一次或在缓冲区填满时刷新；`"eager"` 在每一帧之后触发后台刷新。当 `session_store` 为 `None` 时忽略                                                                                                                                                                                                                                                                                                                                                                            |
| `load_timeout_ms`             | `int`                                                                                 | `60000`                            | 在 resume 物化期间对 `session_store.load()` 和 `list_subkeys()` 的单次调用超时，单位为毫秒                                                                                                                                                                                                         |
| `task_budget`                 | `TaskBudget \| None`                                                                  | `None`                             | API 侧的 token 预算。作为 `output_config.task_budget` 随 `task-budgets-2026-03-13` beta 标头发送。传入 `{"total": <int>}`。                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |

#### 处理缓慢或停滞的 API 响应

CLI 子进程会读取多个控制 API 超时和停滞检测的环境变量。通过 `ClaudeAgentOptions.env` 传递它们：

```python theme={null}
from claude_agent_sdk import ClaudeAgentOptions

options = ClaudeAgentOptions(
    env={
        "API_TIMEOUT_MS": "120000",
        "CLAUDE_CODE_MAX_RETRIES": "2",
        "CLAUDE_ASYNC_AGENT_STALL_TIMEOUT_MS": "120000",
    },
)
```

* `API_TIMEOUT_MS`：Anthropic 客户端的单次请求超时，单位为毫秒。默认 `600000`。适用于主循环和所有子代理。
* `CLAUDE_CODE_MAX_RETRIES`：API 最大重试次数。默认 `10`，上限为 `15`。每次重试都有自己的 `API_TIMEOUT_MS` 时间窗口，因此最坏情况下的挂钟时间约为 `API_TIMEOUT_MS × (CLAUDE_CODE_MAX_RETRIES + 1)` 加上退避时间。对于在较长时间服务中断期间需要持续等待的无人值守运行，请设置 `CLAUDE_CODE_RETRY_WATCHDOG=1`：它会无限期重试容量错误，并且 {/* min-version: 2.1.199 */}自 Claude Code v2.1.199 起，将其他瞬时错误的默认值提高到 `300`，并移除此变量的上限。
* `CLAUDE_ASYNC_AGENT_STALL_TIMEOUT_MS`：使用 `run_in_background` 启动的子代理的停滞看门狗。默认 `600000`。每收到一个流事件即重置；发生停滞时，它会中止子代理，将任务标记为失败，并将错误连同任何部分结果上报给父代理。不适用于同步子代理。
* `CLAUDE_ENABLE_STREAM_WATCHDOG` 与 `CLAUDE_STREAM_IDLE_TIMEOUT_MS`：当响应头已到达但响应体停止流式传输时中止请求。该看门狗对所有提供商默认启用；将 `CLAUDE_ENABLE_STREAM_WATCHDOG=0` 设置为禁用。`CLAUDE_STREAM_IDLE_TIMEOUT_MS` 默认为 `300000`，并被钳制到该最小值。被中止的请求会进入正常的重试路径。

### `OutputFormat`

结构化输出验证的配置。将其作为 `dict` 传递给 `ClaudeAgentOptions` 上的 `output_format` 字段：

```python theme={null}
# Expected dict shape for output_format

{
    "type": "json_schema",
    "schema": {...},  # Your JSON Schema definition
}
```

| 字段    | 必填 | 描述                                        |
| :------- | :------- | :------------------------------------------------- |
| `type`   | 是      | 对于 JSON Schema 验证必须为 `"json_schema"` |
| `schema` | 是      | 用于输出验证的 JSON Schema 定义       |

### `SystemPromptPreset`

使用 Claude Code 的预设系统提示词并附加可选内容的配置。

```python theme={null}
class SystemPromptPreset(TypedDict):
    type: Literal["preset"]
    preset: Literal["claude_code"]
    append: NotRequired[str]
    exclude_dynamic_sections: NotRequired[bool]
```

| 字段                      | 必填 | 描述                                                                                                                                                                                                         |
| :------------------------- | :------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `type`                     | 是      | 必须为 `"preset"` 才能使用预设系统提示词                                                                                                                                                                                                         |
| `preset`                   | 是      | 必须为 `"claude_code"` 才能使用 Claude Code 的系统提示词                                                                                                                                                                                                         |
| `append`                   | 否       | 要追加到预设系统提示词的附加指令                                                                                                                                                                                                         |
| `exclude_dynamic_sections` | 否       | 将工作目录、git 仓库标志和自动记忆路径等每个会话的上下文从系统提示词移入第一条用户消息。可提高跨用户和跨机器的提示词缓存复用率。参见 [修改系统提示词](/docs/en/agent-sdk/modifying-system-prompts#improve-prompt-caching-across-users-and-machines) |

### `SystemPromptFile`

从文件加载自定义系统提示词（而非以字符串形式传入）的配置。SDK 会将其映射到 CLI 的 [`--system-prompt-file`](/docs/en/cli-reference#system-prompt-flags) 标志。当提示词较大时请使用文件形式：SDK 会以字符串形式将 `system_prompt` 传给 CLI 子进程的 argv，在 SDK 发送任何 API 请求之前，它受操作系统命令行长度限制的约束。在 Linux 上，单个参数超过约 128 KB 会在进程启动时以 `Argument list too long` 失败。在 Windows 上，整个命令行上限约为 32 KB，因此字符串形式会在更低的阈值处失败。

```python theme={null}
class SystemPromptFile(TypedDict):
    type: Literal["file"]
    path: str
```

| 字段  | 必填 | 描述                                   |
| :----- | :------- | :-------------------------------------------- |
| `type` | 是      | 必须为 `"file"` 才能从磁盘加载提示词 |
| `path` | 是      | 包含系统提示词的文件路径   |

### `SettingSource`

控制 SDK 从哪些基于文件系统的配置源加载设置。

```python theme={null}
SettingSource = Literal["user", "project", "local"]
```

| 值       | 描述                                     | 位置                      |
| :---------- | :---------------------------------------------- | :---------------------------- |
| `"user"`    | 全局用户设置                            | `~/.claude/settings.json`     |
| `"project"` | 共享项目设置（纳入版本控制）    | `.claude/settings.json`       |
| `"local"`   | 本地项目设置（不纳入版本控制） | `.claude/settings.local.json` |

#### 默认行为

当省略 `setting_sources` 或为 `None` 时，`query()` 加载与 Claude Code CLI 相同的文件系统设置：用户、项目和本地。端点托管策略在所有情况下都会加载；当会话使用组织凭据在[符合条件的配置](/docs/en/server-managed-settings#platform-availability)上进行身份验证时，会获取服务器托管设置。有关无论此选项如何都会被读取的输入以及如何禁用它们，请参阅 [settingSources 不控制的内容](/docs/en/agent-sdk/claude-code-features#what-settingsources-does-not-control)。

#### 为什么使用 setting\_sources

**禁用文件系统设置：**

```python theme={null}
# Do not load user, project, or local settings from disk

import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions


async def main():
    async for message in query(
        prompt="Analyze this code",
        options=ClaudeAgentOptions(
            setting_sources=[]
        ),
    ):
        print(message)


asyncio.run(main())
```

<Note>
  在 Python SDK 0.1.59 及更早版本中，空列表被视为与省略该选项相同，因此 `setting_sources=[]` 不会禁用文件系统设置。如果需要空列表生效，请升级到更新的版本。TypeScript SDK 不受影响。
</Note>

**显式加载所有文件系统设置：**

```python theme={null}
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions


async def main():
    async for message in query(
        prompt="Analyze this code",
        options=ClaudeAgentOptions(
            setting_sources=["user", "project", "local"]
        ),
    ):
        print(message)


asyncio.run(main())
```

**仅加载特定的设置来源：**

```python theme={null}
# Load only project settings, ignore user and local

import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions


async def main():
    async for message in query(
        prompt="Run CI checks",
        options=ClaudeAgentOptions(
            setting_sources=["project"]  # Only .claude/settings.json
        ),
    ):
        print(message)


asyncio.run(main())
```

**测试和 CI 环境：**

```python theme={null}
# Ensure consistent behavior in CI by excluding local settings

import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions


async def main():
    async for message in query(
        prompt="Run tests",
        options=ClaudeAgentOptions(
            setting_sources=["project"],  # Only team-shared settings
            permission_mode="bypassPermissions",
        ),
    ):
        print(message)


asyncio.run(main())
```

**仅限 SDK 的应用程序：**

```python theme={null}
# Define everything programmatically.

# Pass [] to opt out of filesystem setting sources.

import asyncio
from claude_agent_sdk import AgentDefinition, ClaudeAgentOptions, query


async def main():
    async for message in query(
        prompt="Review this PR",
        options=ClaudeAgentOptions(
            setting_sources=[],
            agents={
                "code-reviewer": AgentDefinition(
                    description="Reviews code changes",
                    prompt="You are a code reviewer. Report issues in the diff.",
                ),
            },
            allowed_tools=["Read", "Grep", "Glob"],
        ),
    ):
        print(message)


asyncio.run(main())
```

**加载 CLAUDE.md 项目指令：**

```python theme={null}
# Load project settings to include CLAUDE.md files

import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions


async def main():
    async for message in query(
        prompt="Add a new feature following project conventions",
        options=ClaudeAgentOptions(
            system_prompt={
                "type": "preset",
                "preset": "claude_code",  # Use Claude Code's system prompt
            },
            setting_sources=["project"],  # Loads CLAUDE.md from project
            allowed_tools=["Read", "Write", "Edit"],
        ),
    ):
        print(message)


asyncio.run(main())
```

#### 设置优先级

当加载多个来源时，设置按以下优先级合并（从高到低）：

1. 本地设置（`.claude/settings.local.json`）
2. 项目设置（`.claude/settings.json`）
3. 用户设置（`~/.claude/settings.json`）

诸如 `agents` 和 `allowed_tools` 之类的编程选项会覆盖用户、项目和本地文件系统设置。托管策略设置优先于编程选项。

### `AgentDefinition`

以编程方式定义的子代理的配置。

```python theme={null}
@dataclass
class AgentDefinition:
    description: str
    prompt: str
    tools: list[str] | None = None
    disallowedTools: list[str] | None = None
    model: str | None = None
    skills: list[str] | None = None
    memory: Literal["user", "project", "local"] | None = None
    mcpServers: list[str | dict[str, Any]] | None = None
    initialPrompt: str | None = None
    maxTurns: int | None = None
    background: bool | None = None
    effort: EffortLevel | int | None = None
    permissionMode: PermissionMode | None = None
```

| 字段             | 必需 | 描述                                                                                                                                                                                                         |
| :---------------- | :------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `description`     | 是      | 关于何时使用此代理的自然语言描述                                                                                                                                                                           |
| `prompt`          | 是      | 该代理的系统提示词                                                                                                                                                                                                        |
| `tools`           | 否       | 允许的工具名称数组。如果省略，则继承子代理可用的所有[工具](/docs/en/sub-agents#available-tools)                                                                                                            |
| `disallowedTools` | 否       | 要从代理的工具集中移除的工具名称数组。也接受 MCP 服务器级别的模式：`mcp__server` 或 `mcp__server__*` 移除该服务器中的所有工具，`mcp__*` 移除任何服务器中的所有 MCP 工具 |
| `model`           | 否       | 此代理的模型覆盖。接受诸如 `"sonnet"`、`"opus"`、`"haiku"` 或 `"inherit"` 之类的别名，或完整的模型 ID。如果省略，则使用主模型                                                                     |
| `skills`          | 否       | 启动时要预加载到代理上下文中的技能名称列表。未列出的技能仍可通过 Skill 工具调用                                                                                                      |
| `memory`          | 否       | 此代理的记忆来源：`"user"`、`"project"` 或 `"local"`                                                                                                                                                                |
| `mcpServers`      | 否       | 此代理可用的 MCP 服务器。每个条目是一个服务器名称或内联的 `{name: config}` 字典                                                                                                                              |
| `initialPrompt`   | 否       | 当此代理作为主线程代理运行时，作为第一个用户回合自动提交                                                                                                                                              |
| `maxTurns`        | 否       | 代理停止前的最大代理回合数                                                                                                                                                                           |
| `background`      | 否       | 调用时将代理作为非阻塞后台任务运行                                                                                                                                                                    |
| `effort`          | 否       | 此代理的推理努力级别。接受命名级别或整数。请参阅 [`EffortLevel`](#effortlevel)                                                                                                                    |
| `permissionMode`  | 否       | 在此代理中控制工具执行的权限模式。参见 [`PermissionMode`](#permissionmode)                                                                                                                                    |

<Note>
  `AgentDefinition` 字段名使用 camelCase，例如 `disallowedTools`、`permissionMode` 和 `maxTurns`。这些名称直接映射到与 TypeScript SDK 共享的线路格式。这与 `ClaudeAgentOptions` 不同，后者对相应的顶层字段（如 `disallowed_tools` 和 `permission_mode`）使用 Python snake\_case。由于 `AgentDefinition` 是一个 dataclass，传入 snake\_case 关键字会在构造时引发 `TypeError`。
</Note>

### `PermissionMode`

用于控制工具执行的权限模式。

```python theme={null}
PermissionMode = Literal[
    "default",  # Standard permission behavior
    "acceptEdits",  # Auto-accept file edits
    "plan",  # Planning mode - explore without editing
    "dontAsk",  # Deny anything not pre-approved instead of prompting
    "bypassPermissions",  # Bypass permission checks; explicit ask rules still prompt (use with caution)
    "auto",  # Model classifier approves or denies permission prompts
]
```

### `EffortLevel`

用于引导思考深度的努力级别。

```python theme={null}
EffortLevel = Literal[
    "low",  # Minimal thinking, fastest responses
    "medium",  # Moderate thinking
    "high",  # Deep reasoning
    "xhigh",  # Extended reasoning; falls back to "high" on models that don't support it
    "max",  # Maximum effort
]
```

### `CanUseTool`

工具权限回调函数的类型别名。

```python theme={null}
CanUseTool = Callable[
    [str, dict[str, Any], ToolPermissionContext], Awaitable[PermissionResult]
]
```

回调接收：

* `tool_name`：被调用工具的名称
* `input_data`：工具的输入参数
* `context`：包含附加信息的 `ToolPermissionContext`

返回一个 `PermissionResult`（`PermissionResultAllow` 或 `PermissionResultDeny` 之一）。

该回调是 SDK 对交互式权限提示的替代：它仅在 [权限评估流程](/docs/en/agent-sdk/permissions#how-permissions-are-evaluated) 判定为需要提示时才被调用。已被 `allowed_tools` 条目、设置中的允许规则或权限模式（如 `acceptEdits` 或 `bypassPermissions`）批准的工具调用绝不会触发它。要拦截每一次工具调用，请改用 [`PreToolUse` 钩子](/docs/en/agent-sdk/hooks)。

`AskUserQuestion`、标记为 [`requiresUserInteraction`](/docs/en/mcp#require-approval-for-a-specific-tool) 的 MCP 工具，以及 [你的组织设置为 `ask`](/docs/en/mcp#organization-controls-on-connector-tools) 的连接器工具，即使有匹配的允许规则也会到达该回调。在 `dontAsk` 模式下，这些调用将被拒绝，而不会调用该回调。

### `ToolPermissionContext`

传递给工具权限回调的上下文信息。

```python theme={null}
@dataclass
class ToolPermissionContext:
    signal: Any | None = None  # Future: abort signal support
    suggestions: list[PermissionUpdate] = field(default_factory=list)
    tool_use_id: str | None = None
    agent_id: str | None = None
    blocked_path: str | None = None
    decision_reason: str | None = None
    title: str | None = None
    display_name: str | None = None
    description: str | None = None
```

| 字段             | 类型                     | 描述                                                                                                                                                                                                         |
| :---------------- | :----------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `signal`          | `Any \| None`            | 保留用于未来的中止信号支持                                                                                                                                                                                                    |
| `suggestions`     | `list[PermissionUpdate]` | 来自 CLI 的权限更新建议。Bash 提示包含一个带有 `localSettings` 目标的建议，因此在 `updated_permissions` 中返回它会将规则写入 `.claude/settings.local.json` 并跨会话持久化。 |
| `tool_use_id`     | `str \| None`            | 此提示对应的特定工具调用的标识符。交付给 `can_use_tool` 时始终填充                                                                                                                                  |
| `agent_id`        | `str \| None`            | 当调用来自子代理时的子代理 ID；主代理为 `None`                                                                                                                                                            |
| `blocked_path`    | `str \| None`            | 触发权限请求的文件路径（如适用）。例如，当 Bash 命令尝试访问允许目录之外的路径时                                                                                       |
| `decision_reason` | `str \| None`            | 触发此权限请求的原因。当钩子返回 `"ask"` 时，从 PreToolUse 钩子的 `permissionDecisionReason` 转发                                                                                                  |
| `title`           | `str \| None`            | 完整的权限提示句子，例如 `Claude wants to read foo.txt`。存在时用作主要提示文本                                                                                                                        |
| `display_name`    | `str \| None`            | 工具操作的短名词短语，例如 `Read file`，适合按钮标签                                                                                                                                                      |
| `description`     | `str \| None`            | 权限 UI 的人类可读副标题                                                                                                                                                                                               |

### `PermissionResult`

权限回调结果的联合类型。

```python theme={null}
PermissionResult = PermissionResultAllow | PermissionResultDeny
```

### `PermissionResultAllow`

表示应允许该工具调用的结果。

```python theme={null}
@dataclass
class PermissionResultAllow:
    behavior: Literal["allow"] = "allow"
    updated_input: dict[str, Any] | None = None
    updated_permissions: list[PermissionUpdate] | None = None
```

| 字段                 | 类型                             | 默认值   | 描述                               |
| :-------------------- | :------------------------------- | :-------- | :---------------------------------------- |
| `behavior`            | `Literal["allow"]`               | `"allow"` | 必须为 "allow"                           |
| `updated_input`       | `dict[str, Any] \| None`         | `None`    | 用于替代原始输入的修改后输入 |
| `updated_permissions` | `list[PermissionUpdate] \| None` | `None`    | 要应用的权限更新               |

### `PermissionResultDeny`

表示应拒绝该工具调用的结果。

```python theme={null}
@dataclass
class PermissionResultDeny:
    behavior: Literal["deny"] = "deny"
    message: str = ""
    interrupt: bool = False
```

| 字段       | 类型              | 默认值  | 描述                                |
| :---------- | :---------------- | :------- | :----------------------------------------- |
| `behavior`  | `Literal["deny"]` | `"deny"` | 必须为 "deny"                             |
| `message`   | `str`             | `""`     | 解释工具被拒绝原因的消息 |
| `interrupt` | `bool`            | `False`  | 是否中断当前执行 |

### `PermissionUpdate`

以编程方式更新权限的配置。

```python theme={null}
@dataclass
class PermissionUpdate:
    type: Literal[
        "addRules",
        "replaceRules",
        "removeRules",
        "setMode",
        "addDirectories",
        "removeDirectories",
    ]
    rules: list[PermissionRuleValue] | None = None
    behavior: Literal["allow", "deny", "ask"] | None = None
    mode: PermissionMode | None = None
    directories: list[str] | None = None
    destination: (
        Literal["userSettings", "projectSettings", "localSettings", "session"] | None
    ) = None
```

| 字段         | 类型                                      | 描述                                     |
| :------------ | :---------------------------------------- | :---------------------------------------------- |
| `type`        | `Literal[...]`                            | 权限更新操作的类型         |
| `rules`       | `list[PermissionRuleValue] \| None`       | add/replace/remove 操作的规则         |
| `behavior`    | `Literal["allow", "deny", "ask"] \| None` | 基于规则的操作的行为              |
| `mode`        | `PermissionMode \| None`                  | setMode 操作的模式                      |
| `directories` | `list[str] \| None`                       | 添加/移除目录操作的目录 |
| `destination` | `Literal[...] \| None`                    | 权限更新的应用位置            |

### `PermissionRuleValue`

在权限更新中添加、替换或移除的规则。

```python theme={null}
@dataclass
class PermissionRuleValue:
    tool_name: str
    rule_content: str | None = None
```

### `ToolsPreset`

使用 Claude Code 默认工具集的预设工具配置。

```python theme={null}
class ToolsPreset(TypedDict):
    type: Literal["preset"]
    preset: Literal["claude_code"]
```

### `ThinkingConfig`

控制扩展思考行为。由三种配置组成的联合类型:

```python theme={null}
ThinkingDisplay = Literal["summarized", "omitted"]


class ThinkingConfigAdaptive(TypedDict):
    type: Literal["adaptive"]
    display: NotRequired[ThinkingDisplay]


class ThinkingConfigEnabled(TypedDict):
    type: Literal["enabled"]
    budget_tokens: int
    display: NotRequired[ThinkingDisplay]


class ThinkingConfigDisabled(TypedDict):
    type: Literal["disabled"]


ThinkingConfig = ThinkingConfigAdaptive | ThinkingConfigEnabled | ThinkingConfigDisabled
```

| 变体    | 字段                             | 描述                                  |
| :--------- | :--------------------------------- | :------------------------------------------- |
| `adaptive` | `type`, `display`                  | Claude 自适应地决定何时思考      |
| `enabled`  | `type`, `budget_tokens`, `display` | 使用特定的令牌预算启用思考 |
| `disabled` | `type`                             | 禁用思考                             |

可选的 `display` 字段控制思考文本以 `"summarized"` 还是 `"omitted"` 形式返回。在 Claude Opus 4.7 及更高版本上,API 默认值为 `"omitted"`,因此请设置 `"summarized"` 以在 [`ThinkingBlock`](#thinkingblock) 输出中接收思考内容。

由于这些是 `TypedDict` 类,它们在运行时就是普通的字典。既可以将它们构造为字典字面量,也可以像调用构造函数一样调用该类;两种方式都会生成一个 `dict`。请使用 `config["budget_tokens"]` 而非 `config.budget_tokens` 访问字段:

```python theme={null}
from claude_agent_sdk import ClaudeAgentOptions, ThinkingConfigEnabled

# Option 1: dict literal (recommended, no import needed)

options = ClaudeAgentOptions(thinking={"type": "enabled", "budget_tokens": 20000})

# Option 2: constructor-style (returns a plain dict)

config = ThinkingConfigEnabled(type="enabled", budget_tokens=20000)
print(config["budget_tokens"])  # 20000
# config.budget_tokens would raise AttributeError

```

### `TaskBudget`

以令牌为单位的 API 端任务预算，与 `ClaudeAgentOptions` 中的 `task_budget` 字段一起使用。

```python theme={null}
class TaskBudget(TypedDict):
    total: int
```

| 字段   | 类型  | 描述                     |
| :------ | :---- | :------------------------------ |
| `total` | `int` | 任务的总令牌预算 |

由于这是一个 `TypedDict`，请将其作为普通字典传递，例如 `ClaudeAgentOptions(task_budget={"total": 50000})`。

### `SdkBeta`

SDK Beta 功能的字面量类型。

```python theme={null}
SdkBeta = Literal["context-1m-2025-08-07"]
```

与 `ClaudeAgentOptions` 中的 `betas` 字段一起使用，以启用 Beta 功能。

<Warning>
  `context-1m-2025-08-07` Beta 已于 2026 年 4 月 30 日停用。对 Claude Sonnet 4.5 或 Sonnet 4 传递此标头不会产生任何效果，且超出标准 20 万令牌上下文窗口的请求将返回错误。要使用 100 万令牌的上下文窗口，请迁移到 [Claude Sonnet 5、Claude Sonnet 4.6、Claude Opus 4.6、Claude Opus 4.7 或 Claude Opus 4.8](https://platform.claude.com/docs/en/about-claude/models/overview)，这些模型按标准定价包含 100 万上下文，无需 Beta 标头。
</Warning>

### `McpSdkServerConfig`

使用 `create_sdk_mcp_server()` 创建的 SDK MCP 服务器的配置。

```python theme={null}
class McpSdkServerConfig(TypedDict):
    type: Literal["sdk"]
    name: str
    instance: Any  # MCP Server instance
```

### `McpServerConfig`

MCP 服务器配置的联合类型。

```python theme={null}
McpServerConfig = (
    McpStdioServerConfig | McpSSEServerConfig | McpHttpServerConfig | McpSdkServerConfig
)
```

#### `McpStdioServerConfig`

```python theme={null}
class McpStdioServerConfig(TypedDict):
    type: NotRequired[Literal["stdio"]]  # Optional for backwards compatibility
    command: str
    args: NotRequired[list[str]]
    env: NotRequired[dict[str, str]]
```

#### `McpSSEServerConfig`

```python theme={null}
class McpSSEServerConfig(TypedDict):
    type: Literal["sse"]
    url: str
    headers: NotRequired[dict[str, str]]
```

#### `McpHttpServerConfig`

```python theme={null}
class McpHttpServerConfig(TypedDict):
    type: Literal["http"]
    url: str
    headers: NotRequired[dict[str, str]]
```

### `McpServerStatusConfig`

由 [`get_mcp_status()`](#methods) 报告的 MCP 服务器配置。这是所有 [`McpServerConfig`](#mcpserverconfig) 传输变体的联合，外加一个仅供输出的 `claudeai-proxy` 变体，用于通过 claude.ai 代理的服务器。

```python theme={null}
McpServerStatusConfig = (
    McpStdioServerConfig
    | McpSSEServerConfig
    | McpHttpServerConfig
    | McpSdkServerConfigStatus
    | McpClaudeAIProxyServerConfig
)
```

`McpSdkServerConfigStatus` 是 [`McpSdkServerConfig`](#mcpsdkserverconfig) 的可序列化形式，仅包含 `type`（`"sdk"`）和 `name`（`str`）字段；进程内的 `instance` 被省略。`McpClaudeAIProxyServerConfig` 具有 `type`（`"claudeai-proxy"`）、`url`（`str`）和 `id`（`str`）字段。

### `McpStatusResponse`

来自 [`ClaudeSDKClient.get_mcp_status()`](#methods) 的响应。将服务器状态列表包装在 `mcpServers` 键下。

```python theme={null}
class McpStatusResponse(TypedDict):
    mcpServers: list[McpServerStatus]
```

### `McpServerStatus`

已连接 MCP 服务器的状态，包含在 [`McpStatusResponse`](#mcpstatusresponse) 中。

```python theme={null}
class McpServerStatus(TypedDict):
    name: str
    status: McpServerConnectionStatus  # "connected" | "failed" | "needs-auth" | "pending" | "disabled"
    serverInfo: NotRequired[McpServerInfo]
    error: NotRequired[str]
    config: NotRequired[McpServerStatusConfig]
    scope: NotRequired[str]
    tools: NotRequired[list[McpToolInfo]]
```

| 字段        | 类型                                                         | 描述                                                                                                                                                                   |
| :----------- | :----------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`       | `str`                                                        | 服务器名称                                                                                                                                                                   |
| `status`     | `str`                                                        | 取值之一：`"connected"`、`"failed"`、`"needs-auth"`、`"pending"` 或 `"disabled"`                                                                                                |
| `serverInfo` | `dict` （可选）                                            | 服务器名称和版本（`{"name": str, "version": str}`）                                                                                                                     |
| `error`      | `str` （可选）                                             | 服务器连接失败时的错误消息                                                                                                                                 |
| `config`     | [`McpServerStatusConfig`](#mcpserverstatusconfig) （可选） | 服务器配置。与 [`McpServerConfig`](#mcpserverconfig)（stdio、SSE、HTTP 或 SDK）结构相同，另加一个用于通过 claude.ai 连接的服务器的 `claudeai-proxy` 变体 |
| `scope`      | `str` （可选）                                             | 配置作用域                                                                                                                                                           |
| `tools`      | `list` （可选）                                            | 此服务器提供的工具，每个工具带有 `name`、`description` 和 `annotations` 字段                                                                                      |

### `SdkPluginConfig`

在 SDK 中加载插件的配置。

```python theme={null}
class SdkPluginConfig(TypedDict):
    type: Literal["local"]
    path: str
```

| 字段  | 类型               | 描述                                                |
| :----- | :----------------- | :--------------------------------------------------------- |
| `type` | `Literal["local"]` | 必须为 `"local"`（目前仅支持本地插件） |
| `path` | `str`              | 插件目录的绝对或相对路径          |

**示例：**

```python theme={null}
plugins = [
    {"type": "local", "path": "./my-plugin"},
    {"type": "local", "path": "/absolute/path/to/plugin"},
]
```

有关创建和使用插件的完整信息，请参阅 [插件](/docs/en/agent-sdk/plugins)。

## 消息类型

### `Message`

所有可能消息的联合类型。

```python theme={null}
Message = (
    UserMessage
    | AssistantMessage
    | SystemMessage
    | ResultMessage
    | StreamEvent
    | RateLimitEvent
)
```

### `UserMessage`

用户输入消息。

```python theme={null}
@dataclass
class UserMessage:
    content: str | list[ContentBlock]
    uuid: str | None = None
    parent_tool_use_id: str | None = None
    tool_use_result: dict[str, Any] | None = None
```

| 字段                | 类型                        | 描述                                           |
| :------------------- | :-------------------------- | :---------------------------------------------------- |
| `content`            | `str \| list[ContentBlock]` | 以文本或内容块形式表示的消息内容             |
| `uuid`               | `str \| None`               | 唯一消息标识符                             |
| `parent_tool_use_id` | `str \| None`               | 如果此消息是工具结果响应，则为工具调用 ID |
| `tool_use_result`    | `dict[str, Any] \| None`    | 工具结果数据（如适用）                        |

### `AssistantMessage`

带有内容块的助手响应消息。

```python theme={null}
@dataclass
class AssistantMessage:
    content: list[ContentBlock]
    model: str
    parent_tool_use_id: str | None = None
    error: AssistantMessageError | None = None
    usage: dict[str, Any] | None = None
    message_id: str | None = None
    stop_reason: str | None = None
    session_id: str | None = None
    uuid: str | None = None
```

| 字段                | 类型                                                         | 描述                                                                    |
| :------------------- | :----------------------------------------------------------- | :----------------------------------------------------------------------------- |
| `content`            | `list[ContentBlock]`                                         | 响应中的内容块列表                                         |
| `model`              | `str`                                                        | 生成响应的模型                                              |
| `parent_tool_use_id` | `str \| None`                                                | 如果这是嵌套响应，则为工具调用 ID                                       |
| `error`              | [`AssistantMessageError`](#assistantmessageerror) ` \| None` | 如果响应遇到错误，则为错误类型                                |
| `usage`              | `dict[str, Any] \| None`                                     | 每条消息的 token 使用量（与 [`ResultMessage.usage`](#resultmessage) 相同的键） |
| `message_id`         | `str \| None`                                                | API 消息 ID。同一轮的多条消息共享相同的 ID              |
| `stop_reason`        | `str \| None`                                                | 来自 API 的停止原因（例如 `end_turn`、`tool_use`）                         |
| `session_id`         | `str \| None`                                                | 此消息所属会话的 ID                                      |
| `uuid`               | `str \| None`                                                | 会话记录内的唯一消息标识符                        |

### `AssistantMessageError`

助手消息可能的错误类型。

```python theme={null}
AssistantMessageError = Literal[
    "authentication_failed",
    "billing_error",
    "rate_limit",
    "invalid_request",
    "server_error",
    "max_output_tokens",
    "unknown",
]
```

### `SystemMessage`

带有元数据的系统消息。

```python theme={null}
@dataclass
class SystemMessage:
    subtype: str
    data: dict[str, Any]
```

### `ResultMessage`

包含成本和用量信息的最终结果消息。

```python theme={null}
@dataclass
class ResultMessage:
    subtype: str
    duration_ms: int
    duration_api_ms: int
    is_error: bool
    num_turns: int
    session_id: str
    stop_reason: str | None = None
    total_cost_usd: float | None = None
    usage: dict[str, Any] | None = None
    result: str | None = None
    structured_output: Any = None
    model_usage: dict[str, ModelUsage] | None = None
    permission_denials: list[Any] | None = None
    deferred_tool_use: DeferredToolUse | None = None
    errors: list[str] | None = None
    api_error_status: int | None = None
    uuid: str | None = None
    terminal_reason: str | None = None
```

`subtype` 字段决定了哪些其他字段会被填充。它是 `"success"`、`"error_during_execution"`、`"error_max_turns"`、`"error_max_budget_usd"` 或 `"error_max_structured_output_retries"` 之一。Python 数据类将所有变体展平为同一种结构，因此，对于返回的子类型不适用的字段均为 `None`。

有几个字段携带了关于对话如何结束的诊断细节：

* `is_error`：当对话以错误状态结束时为 `True`。在 `error_*` 子类型上始终为 `True`。在 `subtype="success"` 上，当最终模型请求失败时为 `True`，这意味着代理循环已完成，但最后一次 API 调用返回了错误。
* `api_error_status`：终止性 API 错误的 HTTP 状态码。当回合在没有此类错误的情况下结束时为 `None`。仅在 `subtype="success"` 上填充。
* `result`：`subtype="success"` 时最终助手消息的文本，或在 `error_*` 子类型上为 `None`。当 `subtype="success"` 且 `is_error=True` 时，如果可用，此处保存 API 错误字符串，但也可能为空，因此请检查 `api_error_status` 以及之前的 `AssistantMessage` 内容以获取详细信息。
* `errors`：循环级错误字符串，例如达到最大回合数的消息。仅在 `error_*` 子类型上填充。
* `terminal_reason`：查询循环终止的原因，例如 `"completed"`、`"max_turns"` 或 `"aborted_streaming"`。值为 `"aborted_streaming"` 或 `"aborted_tools"` 表示该回合被中断取消。当 CLI 未报告终止原因时为 `None`，例如使用较旧版本的 CLI 时。有关值的完整列表，请参阅 [`SDKResultMessage`](/docs/en/agent-sdk/typescript#sdkresultmessage)。

`usage` 字典在存在时包含以下键：

| 键                           | 类型  | 描述                                                                                                                                                                                   |
| ----------------------------- | ----- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `input_tokens`                | `int` | 顶层代理循环消耗的输入 token。[不包括子代理 token](/docs/en/agent-sdk/cost-tracking#get-the-total-cost-of-a-query)；请使用 `model_usage` 进行整棵树的统计。 |
| `output_tokens`               | `int` | 顶层代理循环生成的输出 token。不包括子代理 token。                                                                                                         |
| `cache_creation_input_tokens` | `int` | 用于创建新缓存条目的 token。                                                                                                                                                      |
| `cache_read_input_tokens`     | `int` | 从现有缓存条目读取的 token。                                                                                                                                                      |

`model_usage` 字典将模型名称映射到各模型的用量。每个值都是一个 `ModelUsage` TypedDict，其键使用 camelCase，因为该值是从底层 CLI 进程原样传递的。通过 `from claude_agent_sdk.types import ModelUsage` 导入。这些键为：

| 键                        | 类型    | 描述                                                                                                                                                              |
| -------------------------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `inputTokens`              | `int`   | 此模型的输入 token 数。                                                                                                                                             |
| `outputTokens`             | `int`   | 此模型的输出 token 数。                                                                                                                                            |
| `cacheReadInputTokens`     | `int`   | 此模型的缓存读取 token 数。                                                                                                                                        |
| `cacheCreationInputTokens` | `int`   | 此模型的缓存创建 token 数。                                                                                                                                    |
| `webSearchRequests`        | `int`   | 此模型发起的网页搜索请求数。                                                                                                                                  |
| `costUSD`                  | `float` | 此模型的估算费用（以美元计），在客户端计算。有关计费注意事项，请参阅 [跟踪费用和用量](/docs/en/agent-sdk/cost-tracking)。                                 |
| `contextWindow`            | `int`   | 此模型的上下文窗口大小。                                                                                                                                      |
| `maxOutputTokens`          | `int`   | 此模型的最大输出 token 数限制。                                                                                                                               |
| `canonicalModel`           | `str`   | 用于定价查询的规范模型 ID。可能与作为条目键名的原始模型字符串不同，例如特定于提供商的 ID 或别名。并非总是存在。 |
| `provider`                 | `str`   | 提供此模型的 API 提供商，例如 `firstParty`、`bedrock`、`vertex`、`foundry`、`anthropicAws`、`mantle` 或 `gateway`。并非总是存在。                   |

### `StreamEvent`

流式传输期间用于部分消息更新的流事件。仅当 `include_partial_messages=True` 在 `ClaudeAgentOptions` 中时才接收。通过 `from claude_agent_sdk.types import StreamEvent` 导入。

```python theme={null}
@dataclass
class StreamEvent:
    uuid: str
    session_id: str
    event: dict[str, Any]  # The raw Claude API stream event
    parent_tool_use_id: str | None = None
```

| 字段                | 类型             | 描述                                                                                                                                                         |
| :------------------- | :--------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `uuid`               | `str`            | 此事件的唯一标识符                                                                                                                                    |
| `session_id`         | `str`            | 会话标识符                                                                                                                                                  |
| `event`              | `dict[str, Any]` | 原始 Claude API 流事件数据                                                                                                                                |
| `parent_tool_use_id` | `str \| None`    | 始终为 `None`。流事件仅针对主会话发出。对于子代理归因，请使用完整消息，例如 [`AssistantMessage`](#assistantmessage) |

### `RateLimitEvent`

当速率限制状态更改时发出（例如，从 `"allowed"` 变为 `"allowed_warning"`）。使用它在用户达到硬性限制之前发出警告，或在状态为 `"rejected"` 时退避。

```python theme={null}
@dataclass
class RateLimitEvent:
    rate_limit_info: RateLimitInfo
    uuid: str
    session_id: str
```

| 字段             | 类型                              | 描述              |
| :---------------- | :-------------------------------- | :----------------------- |
| `rate_limit_info` | [`RateLimitInfo`](#ratelimitinfo) | 当前速率限制状态 |
| `uuid`            | `str`                             | 唯一事件标识符  |
| `session_id`      | `str`                             | 会话标识符       |

### `RateLimitInfo`

由 [`RateLimitEvent`](#ratelimitevent) 携带的速率限制状态。

```python theme={null}
RateLimitStatus = Literal["allowed", "allowed_warning", "rejected"]
RateLimitType = Literal[
    "five_hour", "seven_day", "seven_day_opus", "seven_day_sonnet", "overage"
]


@dataclass
class RateLimitInfo:
    status: RateLimitStatus
    resets_at: int | None = None
    rate_limit_type: RateLimitType | None = None
    utilization: float | None = None
    overage_status: RateLimitStatus | None = None
    overage_resets_at: int | None = None
    overage_disabled_reason: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)
```

| 字段                     | 类型                      | 描述                                                                                           |
| :------------------------ | :------------------------ | :---------------------------------------------------------------------------------------------------- |
| `status`                  | `RateLimitStatus`         | 当前状态。`"allowed_warning"` 表示接近限制;`"rejected"` 表示已达到限制 |
| `resets_at`               | `int \| None`             | 速率限制窗口重置的 Unix 时间戳                                                      |
| `rate_limit_type`         | `RateLimitType \| None`   | 适用的速率限制窗口                                                                       |
| `utilization`             | `float \| None`           | 已消耗的速率限制比例(0.0 到 1.0)                                                      |
| `overage_status`          | `RateLimitStatus \| None` | 按量付费超额使用的状态(如适用)                                                  |
| `overage_resets_at`       | `int \| None`             | 超额窗口重置的 Unix 时间戳                                                         |
| `overage_disabled_reason` | `str \| None`             | 当状态为 `"rejected"` 时,超额不可用的原因                                                 |
| `raw`                     | `dict[str, Any]`          | 来自 CLI 的完整原始字典,包括上面未建模的字段                                        |

### `TaskStartedMessage`

当后台任务启动时发出。后台任务是指在主轮次之外跟踪的任何内容:后台运行的 Bash 命令、[Monitor](#monitor) 监视、通过 Agent 工具生成的子代理,或远程代理。`task_type` 字段会告诉你是哪一种。此命名与 `Task`-到-`Agent` 工具重命名无关。

```python theme={null}
@dataclass
class TaskStartedMessage(SystemMessage):
    task_id: str
    description: str
    uuid: str
    session_id: str
    tool_use_id: str | None = None
    task_type: str | None = None
```

| 字段         | 类型          | 描述                                                                                                                 |
| :------------ | :------------ | :-------------------------------------------------------------------------------------------------------------------------- |
| `task_id`     | `str`         | 任务的唯一标识符                                                                                              |
| `description` | `str`         | 任务的描述                                                                                                     |
| `uuid`        | `str`         | 唯一消息标识符                                                                                                   |
| `session_id`  | `str`         | 会话标识符                                                                                                          |
| `tool_use_id` | `str \| None` | 关联的工具使用 ID                                                                                                      |
| `task_type`   | `str \| None` | 后台任务的类型:`"local_bash"` 表示后台 Bash 和 Monitor 监视,`"local_agent"`,或 `"remote_agent"` |

### `TaskUsage`

后台任务的 token 和计时数据。

```python theme={null}
class TaskUsage(TypedDict):
    total_tokens: int
    tool_uses: int
    duration_ms: int
```

### `TaskProgressMessage`

为正在运行的后台任务定期发出进度更新。

```python theme={null}
@dataclass
class TaskProgressMessage(SystemMessage):
    task_id: str
    description: str
    usage: TaskUsage
    uuid: str
    session_id: str
    tool_use_id: str | None = None
    last_tool_name: str | None = None
```

| 字段            | 类型          | 描述                         |
| :--------------- | :------------ | :---------------------------------- |
| `task_id`        | `str`         | 任务的唯一标识符      |
| `description`    | `str`         | 当前状态描述          |
| `usage`          | `TaskUsage`   | 该任务目前的 token 使用量    |
| `uuid`           | `str`         | 唯一消息标识符           |
| `session_id`     | `str`         | 会话标识符                  |
| `tool_use_id`    | `str \| None` | 关联的工具使用 ID              |
| `last_tool_name` | `str \| None` | 任务最后使用的工具名称 |

### `TaskNotificationMessage`

当后台任务完成、失败或被停止时发出。后台任务包括 `run_in_background` Bash 命令、Monitor 监视和后台子代理。

```python theme={null}
@dataclass
class TaskNotificationMessage(SystemMessage):
    task_id: str
    status: TaskNotificationStatus  # "completed" | "failed" | "stopped"
    output_file: str
    summary: str
    uuid: str
    session_id: str
    tool_use_id: str | None = None
    usage: TaskUsage | None = None
```

| 字段         | 类型                     | 描述                                      |
| :------------ | :----------------------- | :----------------------------------------------- |
| `task_id`     | `str`                    | 任务的唯一标识符                   |
| `status`      | `TaskNotificationStatus` | 为 `"completed"`、`"failed"` 或 `"stopped"` 之一 |
| `output_file` | `str`                    | 任务输出文件的路径                     |
| `summary`     | `str`                    | 任务结果摘要                       |
| `uuid`        | `str`                    | 唯一消息标识符                        |
| `session_id`  | `str`                    | 会话标识符                               |
| `tool_use_id` | `str \| None`            | 关联的工具使用 ID                           |
| `usage`       | `TaskUsage \| None`      | 任务的最终 token 使用量                   |

## 内容块类型

### `ContentBlock`

所有内容块的联合类型。

```python theme={null}
ContentBlock = TextBlock | ThinkingBlock | ToolUseBlock | ToolResultBlock
```

### `TextBlock`

文本内容块。

```python theme={null}
@dataclass
class TextBlock:
    text: str
```

### `ThinkingBlock`

思考内容块（适用于具备思考能力的模型）。

```python theme={null}
@dataclass
class ThinkingBlock:
    thinking: str
    signature: str
```

### `ToolUseBlock`

工具使用请求块。

```python theme={null}
@dataclass
class ToolUseBlock:
    id: str
    name: str
    input: dict[str, Any]
```

### `ToolResultBlock`

工具执行结果块。

```python theme={null}
@dataclass
class ToolResultBlock:
    tool_use_id: str
    content: str | list[dict[str, Any]] | None = None
    is_error: bool | None = None
```

## 错误类型

### `ClaudeSDKError`

所有 SDK 错误的基异常类。

```python theme={null}
class ClaudeSDKError(Exception):
    """Base error for Claude SDK."""
```

### `CLINotFoundError`

当未安装或找不到 Claude Code CLI 时抛出。

```python theme={null}
class CLINotFoundError(CLIConnectionError):
    def __init__(
        self, message: str = "Claude Code not found", cli_path: str | None = None
    ):
        """
        Args:
            message: Error message (default: "Claude Code not found")
            cli_path: Optional path to the CLI that was not found
        """
```

### `CLIConnectionError`

当连接 Claude Code 失败时抛出。

```python theme={null}
class CLIConnectionError(ClaudeSDKError):
    """Failed to connect to Claude Code."""
```

### `ProcessError`

当 Claude Code 进程失败时抛出。

```python theme={null}
class ProcessError(ClaudeSDKError):
    def __init__(
        self, message: str, exit_code: int | None = None, stderr: str | None = None
    ):
        self.exit_code = exit_code
        self.stderr = stderr
```

### `CLIJSONDecodeError`

当 JSON 解析失败时抛出。

```python theme={null}
class CLIJSONDecodeError(ClaudeSDKError):
    def __init__(self, line: str, original_error: Exception):
        """
        Args:
            line: The line that failed to parse
            original_error: The original JSON decode exception
        """
        self.line = line
        self.original_error = original_error
```

## 钩子类型

有关使用钩子的综合指南，包括示例和常见模式，请参阅 [钩子指南](/docs/en/agent-sdk/hooks)。

### `HookEvent`

受支持的钩子事件类型。

```python theme={null}
HookEvent = Literal[
    "PreToolUse",  # Called before tool execution
    "PostToolUse",  # Called after tool execution
    "PostToolUseFailure",  # Called when a tool execution fails
    "UserPromptSubmit",  # Called when user submits a prompt
    "Stop",  # Called when stopping execution
    "SubagentStop",  # Called when a subagent stops
    "PreCompact",  # Called before message compaction
    "Notification",  # Called for notification events
    "SubagentStart",  # Called when a subagent starts
    "PermissionRequest",  # Called when a permission decision is needed
]
```

<Note>
  TypeScript SDK 支持 Python 中尚未提供的其他钩子事件。有关各 SDK 的支持情况，请参阅 [钩子可用性表](/docs/en/agent-sdk/hooks#available-hooks)。
</Note>

### `HookCallback`

钩子回调函数的类型定义。

```python theme={null}
HookCallback = Callable[[HookInput, str | None, HookContext], Awaitable[HookJSONOutput]]
```

参数：

* `input`：基于 `hook_event_name` 的强类型钩子输入，使用可辨识联合（参见 [`HookInput`](#hookinput)）
* `tool_use_id`：可选的工具使用标识符（用于工具相关的钩子）
* `context`：包含附加信息的钩子上下文

返回一个 [`HookJSONOutput`](#hookjsonoutput)，可能包含：

* `decision`：`"block"` 以阻止该操作
* `systemMessage`：向用户显示的警告消息
* `hookSpecificOutput`：特定于钩子的输出数据

### `HookContext`

传递给钩子回调的上下文信息。

```python theme={null}
class HookContext(TypedDict):
    signal: Any | None  # Future: abort signal support
```

### `HookMatcher`

用于将钩子匹配到特定事件或工具的配置。

```python theme={null}
@dataclass
class HookMatcher:
    matcher: str | None = (
        None  # Tool name or pattern to match (e.g., "Bash", "Write|Edit")
    )
    hooks: list[HookCallback] = field(
        default_factory=list
    )  # List of callbacks to execute
    timeout: float | None = (
        None  # Timeout in seconds. When omitted, the per-event default applies
    )
```

### `HookInput`

所有钩子输入类型的联合类型。实际类型取决于 `hook_event_name` 字段。

```python theme={null}
HookInput = (
    PreToolUseHookInput
    | PostToolUseHookInput
    | PostToolUseFailureHookInput
    | UserPromptSubmitHookInput
    | StopHookInput
    | SubagentStopHookInput
    | PreCompactHookInput
    | NotificationHookInput
    | SubagentStartHookInput
    | PermissionRequestHookInput
)
```

### `BaseHookInput`

所有钩子输入类型中都存在的基础字段。

```python theme={null}
class BaseHookInput(TypedDict):
    session_id: str
    transcript_path: str
    cwd: str
    permission_mode: NotRequired[str]
```

| 字段             | 类型             | 描述                         |
| :---------------- | :--------------- | :---------------------------------- |
| `session_id`      | `str`            | 当前会话标识符          |
| `transcript_path` | `str`            | 会话转录文件的路径 |
| `cwd`             | `str`            | 当前工作目录           |
| `permission_mode` | `str`（可选）| 当前权限模式             |

### `PreToolUseHookInput`

`PreToolUse` 钩子事件的输入数据。

```python theme={null}
class PreToolUseHookInput(BaseHookInput):
    hook_event_name: Literal["PreToolUse"]
    tool_name: str
    tool_input: dict[str, Any]
    tool_use_id: str
    agent_id: NotRequired[str]
    agent_type: NotRequired[str]
```

| 字段             | 类型                    | 描述                                                        |
| :---------------- | :---------------------- | :----------------------------------------------------------------- |
| `hook_event_name` | `Literal["PreToolUse"]` | 始终为 "PreToolUse"                                                |
| `tool_name`       | `str`                   | 即将执行的工具名称                              |
| `tool_input`      | `dict[str, Any]`        | 工具的输入参数                                      |
| `tool_use_id`     | `str`                   | 本次工具调用的唯一标识符                                |
| `agent_id`        | `str` (可选)        | 子代理标识符，当钩子在子代理内部触发时存在 |
| `agent_type`      | `str` (可选)        | 子代理类型，当钩子在子代理内部触发时存在       |

### `PostToolUseHookInput`

`PostToolUse` 钩子事件的输入数据。

```python theme={null}
class PostToolUseHookInput(BaseHookInput):
    hook_event_name: Literal["PostToolUse"]
    tool_name: str
    tool_input: dict[str, Any]
    tool_response: Any
    tool_use_id: str
    agent_id: NotRequired[str]
    agent_type: NotRequired[str]
```

| 字段             | 类型                     | 描述                                                        |
| :---------------- | :----------------------- | :----------------------------------------------------------------- |
| `hook_event_name` | `Literal["PostToolUse"]` | 始终为 "PostToolUse"                                               |
| `tool_name`       | `str`                    | 被执行的工具名称                                 |
| `tool_input`      | `dict[str, Any]`         | 使用的输入参数                                    |
| `tool_response`   | `Any`                    | 工具执行的响应                                   |
| `tool_use_id`     | `str`                    | 此工具调用的唯一标识符                                |
| `agent_id`        | `str` （可选）         | 子代理标识符，当钩子在子代理内部触发时存在 |
| `agent_type`      | `str` （可选）         | 子代理类型，当钩子在子代理内部触发时存在       |

### `PostToolUseFailureHookInput`

`PostToolUseFailure` 钩子事件的输入数据。当工具执行失败时调用。

```python theme={null}
class PostToolUseFailureHookInput(BaseHookInput):
    hook_event_name: Literal["PostToolUseFailure"]
    tool_name: str
    tool_input: dict[str, Any]
    tool_use_id: str
    error: str
    is_interrupt: NotRequired[bool]
    agent_id: NotRequired[str]
    agent_type: NotRequired[str]
```

| 字段             | 类型                            | 描述                                                        |
| :---------------- | :------------------------------ | :----------------------------------------------------------------- |
| `hook_event_name` | `Literal["PostToolUseFailure"]` | 始终为 "PostToolUseFailure"                                        |
| `tool_name`       | `str`                           | 失败的工具名称                                       |
| `tool_input`      | `dict[str, Any]`                | 使用的输入参数                                    |
| `tool_use_id`     | `str`                           | 此次工具使用的唯一标识符                                |
| `error`           | `str`                           | 执行失败的错误消息                            |
| `is_interrupt`    | `bool` (可选)               | 失败是否由中断引起                     |
| `agent_id`        | `str` (可选)                | 子代理标识符，当钩子在子代理内部触发时存在 |
| `agent_type`      | `str` (可选)                | 子代理类型，当钩子在子代理内部触发时存在       |

### `UserPromptSubmitHookInput`

`UserPromptSubmit` 钩子事件的输入数据。

```python theme={null}
class UserPromptSubmitHookInput(BaseHookInput):
    hook_event_name: Literal["UserPromptSubmit"]
    prompt: str
```

| 字段             | 类型                          | 描述                 |
| :---------------- | :---------------------------- | :-------------------------- |
| `hook_event_name` | `Literal["UserPromptSubmit"]` | 始终为 "UserPromptSubmit"   |
| `prompt`          | `str`                         | 用户提交的提示词 |

### `StopHookInput`

`Stop` 钩子事件的输入数据。

```python theme={null}
class StopHookInput(BaseHookInput):
    hook_event_name: Literal["Stop"]
    stop_hook_active: bool
```

| 字段              | 类型              | 描述                     |
| :----------------- | :---------------- | :------------------------------ |
| `hook_event_name`  | `Literal["Stop"]` | 始终为 "Stop"                   |
| `stop_hook_active` | `bool`            | 停止钩子是否处于激活状态 |

### `SubagentStopHookInput`

`SubagentStop` 钩子事件的输入数据。

```python theme={null}
class SubagentStopHookInput(BaseHookInput):
    hook_event_name: Literal["SubagentStop"]
    stop_hook_active: bool
    agent_id: str
    agent_transcript_path: str
    agent_type: str
```

| 字段                   | 类型                      | 描述                            |
| :---------------------- | :------------------------ | :------------------------------------- |
| `hook_event_name`       | `Literal["SubagentStop"]` | 始终为 "SubagentStop"                  |
| `stop_hook_active`      | `bool`                    | 停止钩子是否处于激活状态        |
| `agent_id`              | `str`                     | 子代理的唯一标识符     |
| `agent_transcript_path` | `str`                     | 子代理转录文件的路径 |
| `agent_type`            | `str`                     | 子代理的类型                   |

### `PreCompactHookInput`

`PreCompact` 钩子事件的输入数据。

```python theme={null}
class PreCompactHookInput(BaseHookInput):
    hook_event_name: Literal["PreCompact"]
    trigger: Literal["manual", "auto"]
    custom_instructions: str | None
```

| 字段                 | 类型                        | 描述                        |
| :-------------------- | :-------------------------- | :--------------------------------- |
| `hook_event_name`     | `Literal["PreCompact"]`     | 始终为 "PreCompact"                |
| `trigger`             | `Literal["manual", "auto"]` | 触发压缩的原因      |
| `custom_instructions` | `str \| None`               | 用于压缩的自定义指令 |

### `NotificationHookInput`

`Notification` 钩子事件的输入数据。

```python theme={null}
class NotificationHookInput(BaseHookInput):
    hook_event_name: Literal["Notification"]
    message: str
    title: NotRequired[str]
    notification_type: str
```

| 字段               | 类型                      | 描述                  |
| :------------------ | :------------------------ | :--------------------------- |
| `hook_event_name`   | `Literal["Notification"]` | 始终为 "Notification"        |
| `message`           | `str`                     | 通知消息内容 |
| `title`             | `str` （可选）          | 通知标题           |
| `notification_type` | `str`                     | 通知类型         |

### `SubagentStartHookInput`

`SubagentStart` 钩子事件的输入数据。

```python theme={null}
class SubagentStartHookInput(BaseHookInput):
    hook_event_name: Literal["SubagentStart"]
    agent_id: str
    agent_type: str
```

| 字段             | 类型                       | 描述                        |
| :---------------- | :------------------------- | :--------------------------------- |
| `hook_event_name` | `Literal["SubagentStart"]` | 始终为 "SubagentStart"             |
| `agent_id`        | `str`                      | 子代理的唯一标识符 |
| `agent_type`      | `str`                      | 子代理的类型               |

### `PermissionRequestHookInput`

`PermissionRequest` 钩子事件的输入数据。允许钩子以编程方式处理权限决策。

```python theme={null}
class PermissionRequestHookInput(BaseHookInput):
    hook_event_name: Literal["PermissionRequest"]
    tool_name: str
    tool_input: dict[str, Any]
    permission_suggestions: NotRequired[list[Any]]
    agent_id: NotRequired[str]
    agent_type: NotRequired[str]
```

| 字段                    | 类型                           | 描述                                                        |
| :----------------------- | :----------------------------- | :----------------------------------------------------------------- |
| `hook_event_name`        | `Literal["PermissionRequest"]` | 始终为 "PermissionRequest"                                         |
| `tool_name`              | `str`                          | 请求权限的工具名称                             |
| `tool_input`             | `dict[str, Any]`               | 工具的输入参数                                      |
| `permission_suggestions` | `list[Any]` （可选）         | CLI 建议的权限更新                          |
| `agent_id`               | `str` （可选）               | 子代理标识符，当钩子在子代理内部触发时存在 |
| `agent_type`             | `str` （可选）               | 子代理类型，当钩子在子代理内部触发时存在       |

### `HookJSONOutput`

钩子回调返回值的联合类型。

```python theme={null}
HookJSONOutput = AsyncHookJSONOutput | SyncHookJSONOutput
```

#### `SyncHookJSONOutput`

带有控制和决策字段的同步钩子输出。

```python theme={null}
class SyncHookJSONOutput(TypedDict):
    # Control fields
    continue_: NotRequired[bool]  # Whether to proceed (default: True)
    suppressOutput: NotRequired[bool]  # Hide stdout from transcript
    stopReason: NotRequired[str]  # Message when continue is False

    # Decision fields
    decision: NotRequired[Literal["block"]]
    systemMessage: NotRequired[str]  # Warning message for user
    reason: NotRequired[str]  # Feedback for Claude

    # Hook-specific output
    hookSpecificOutput: NotRequired[HookSpecificOutput]
```

<Note>
  在 Python 代码中使用 `continue_`（带下划线）。它会在发送给 CLI 时自动转换为 `continue`。
</Note>

#### `HookSpecificOutput`

一个包含钩子事件名称和事件特定字段的 `TypedDict`。其结构取决于 `hookEventName` 的值。有关每个钩子事件可用字段的完整详细信息，请参阅 [使用钩子控制执行](/docs/en/agent-sdk/hooks#outputs)。

事件特定输出类型的判别联合。`hookEventName` 字段决定哪些字段有效。

```python theme={null}
class PreToolUseHookSpecificOutput(TypedDict):
    hookEventName: Literal["PreToolUse"]
    permissionDecision: NotRequired[Literal["allow", "deny", "ask", "defer"]]
    permissionDecisionReason: NotRequired[str]
    updatedInput: NotRequired[dict[str, Any]]
    additionalContext: NotRequired[str]


class PostToolUseHookSpecificOutput(TypedDict):
    hookEventName: Literal["PostToolUse"]
    additionalContext: NotRequired[str]
    updatedToolOutput: NotRequired[Any]
    updatedMCPToolOutput: NotRequired[Any]  # Deprecated: use updatedToolOutput, which works for all tools


class PostToolUseFailureHookSpecificOutput(TypedDict):
    hookEventName: Literal["PostToolUseFailure"]
    additionalContext: NotRequired[str]


class UserPromptSubmitHookSpecificOutput(TypedDict):
    hookEventName: Literal["UserPromptSubmit"]
    additionalContext: NotRequired[str]


class NotificationHookSpecificOutput(TypedDict):
    hookEventName: Literal["Notification"]
    additionalContext: NotRequired[str]


class SubagentStartHookSpecificOutput(TypedDict):
    hookEventName: Literal["SubagentStart"]
    additionalContext: NotRequired[str]


class PermissionRequestHookSpecificOutput(TypedDict):
    hookEventName: Literal["PermissionRequest"]
    decision: dict[str, Any]


HookSpecificOutput = (
    PreToolUseHookSpecificOutput
    | PostToolUseHookSpecificOutput
    | PostToolUseFailureHookSpecificOutput
    | UserPromptSubmitHookSpecificOutput
    | NotificationHookSpecificOutput
    | SubagentStartHookSpecificOutput
    | PermissionRequestHookSpecificOutput
)
```

#### `AsyncHookJSONOutput`

延迟钩子执行的异步钩子输出。

```python theme={null}
class AsyncHookJSONOutput(TypedDict):
    async_: Literal[True]  # Set to True to defer execution
    asyncTimeout: NotRequired[int]  # Timeout in milliseconds
```

<Note>
  在 Python 代码中使用 `async_`（带下划线）。它会在发送给 CLI 时自动转换为 `async`。
</Note>

### 钩子使用示例

此示例注册了两个钩子：一个用于阻止像 `rm -rf /` 这样的危险 bash 命令，另一个用于记录所有工具使用情况以进行审计。安全钩子仅对 Bash 命令运行（通过 `matcher`），而日志记录钩子对所有工具运行。

```python theme={null}
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, HookMatcher, HookContext
from typing import Any


async def validate_bash_command(
    input_data: dict[str, Any], tool_use_id: str | None, context: HookContext
) -> dict[str, Any]:
    """Validate and potentially block dangerous bash commands."""
    if input_data["tool_name"] == "Bash":
        command = input_data["tool_input"].get("command", "")
        if "rm -rf /" in command:
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": "Dangerous command blocked",
                }
            }
    return {}


async def log_tool_use(
    input_data: dict[str, Any], tool_use_id: str | None, context: HookContext
) -> dict[str, Any]:
    """Log all tool usage for auditing."""
    print(f"Tool used: {input_data.get('tool_name')}")
    return {}


options = ClaudeAgentOptions(
    hooks={
        "PreToolUse": [
            HookMatcher(
                matcher="Bash", hooks=[validate_bash_command], timeout=120
            ),  # 2 min for validation
            HookMatcher(
                hooks=[log_tool_use]
            ),  # Applies to all tools (per-event default timeout)
        ],
        "PostToolUse": [HookMatcher(hooks=[log_tool_use])],
    }
)

async def main():
    async for message in query(prompt="Analyze this codebase", options=options):
        print(message)


asyncio.run(main())
```

## 工具输入/输出类型

所有内置 Claude Code 工具的输入/输出模式文档。虽然 Python SDK 没有将这些导出为类型，但它们代表了消息中工具输入和输出的结构。

### 代理（Agent）

**工具名称：**`Agent`。之前的名称 `Task` 仍作为别名被接受，并且 init [`SystemMessage`](#systemmessage) 中的 `tools` 列表将此工具报告为 `Task` 以实现向后兼容。

**输入：**

```python theme={null}
{
    "description": str,  # A short (3-5 word) description of the task
    "prompt": str,  # The task for the agent to perform
    "subagent_type": str | None,  # The type of specialized agent to use
    "model": "sonnet" | "opus" | "haiku" | "fable" | None,  # Model override for this agent
    "run_in_background": bool | None,  # Agents run in the background by default; set to False to run synchronously
    "name": str | None,  # Name for the spawned agent
    "team_name": str | None,  # Deprecated; ignored
    "mode": "acceptEdits" | "auto" | "bypassPermissions" | "default" | "dontAsk" | "plan" | None,  # Deprecated; ignored. Subagents inherit the parent session's permission mode; agent-definition frontmatter may override it
    "isolation": "worktree" | "remote" | None,  # Isolation mode for the agent's changes
}
```

启动一个新的智能体，以自主处理复杂的多步骤任务。

**输出 (状态: `"completed"`):**

```python theme={null}
{
    "status": "completed",
    "agentId": str,  # ID of the agent that ran
    "agentType": str | None,  # The subagent type that handled the task
    "content": [  # Result content blocks
        {
            "type": "text",
            "text": str,
            "citations": list | None,
        }
    ],
    "resolvedModel": str | None,  # Model the subagent started on
    "modelsUsed": list[str] | None,  # Models used in order, with consecutive repeats collapsed
    "totalToolUseCount": int,  # Number of tool calls the agent made
    "totalDurationMs": int,  # Execution duration in milliseconds
    "totalTokens": int,  # Total tokens used
    "usage": {  # Token usage statistics
        "input_tokens": int,
        "output_tokens": int,
        "cache_creation_input_tokens": int | None,
        "cache_read_input_tokens": int | None,
        "server_tool_use": {"web_search_requests": int, "web_fetch_requests": int} | None,
        "service_tier": str | None,
        "cache_creation": {"ephemeral_1h_input_tokens": int, "ephemeral_5m_input_tokens": int} | None,
        "inference_geo": str | None,
        "speed": str | None,
        "iterations": Any | None,
    },
    "toolStats": {  # Aggregate tool activity for the run
        "readCount": int,
        "searchCount": int,
        "bashCount": int,
        "editFileCount": int,
        "linesAdded": int,
        "linesRemoved": int,
        "otherToolCount": int,
        "frameCount": int | None,
    } | None,
    "prompt": str,  # The prompt the agent ran
    "worktreePath": str | None,  # Present for worktree-isolated runs
    "worktreeBranch": str | None,  # Present for worktree-isolated runs
}
```

**输出 (状态: `"async_launched"`):**

```python theme={null}
{
    "status": "async_launched",
    "isAsync": bool | None,  # True on background launches
    "agentId": str,  # ID of the launched agent
    "description": str,  # The task description
    "resolvedModel": str | None,  # Model in use at the backgrounding transition
    "modelsUsed": list[str] | None,  # Models used before backgrounding, in order, with consecutive repeats collapsed
    "prompt": str,  # The prompt the agent runs
    "outputFile": str,  # File path where the agent's output is written
    "canReadOutputFile": bool | None,  # Whether the output file can be read directly
}
```

**输出 (状态: `"remote_launched"`):**

```python theme={null}
{
    "status": "remote_launched",
    "taskId": str,  # ID of the remote task
    "sessionUrl": str,  # Link to the remote cloud session
    "description": str,  # The task description
    "prompt": str,  # The prompt the agent runs
    "outputFile": str,  # File path where the agent's output is written
}
```

返回子代理的结果。输出根据 `status` 字段进行区分：`"completed"` 表示已完成的任务，`"async_launched"` 表示后台任务，`"remote_launched"` 表示 Claude Code 已分派到远程云会话的任务，其中 `sessionUrl` 链接到该会话，`taskId` 用于标识它。工作区隔离的运行会在 `completed` 变体上包含 `worktreePath` 和 `worktreeBranch`。

在 `completed` 变体上，`resolvedModel` 表示子代理启动时所用的模型，当 [`availableModels`](/docs/en/model-config#restrict-model-selection) 或其他覆盖规则生效时，可能与请求的 `model` 输入不同。{/* min-version: 2.1.174 */}此字段需要 Claude Code v2.1.174 或更高版本。在 `async_launched` 变体上，`resolvedModel` 表示代理移动到后台时正在使用的模型，因此在后台化之前发生的模型切换会反映在那里。两个变体上的 `modelsUsed` 字段按使用顺序列出所用模型，并折叠连续重复；仅当运行中途切换模型时才设置。{/* min-version: 2.1.212 */}`modelsUsed` 以及后台化时的 `resolvedModel` 行为需要 Claude Code v2.1.212 或更高版本。

### AskUserQuestion

**工具名称：** `AskUserQuestion`

在执行过程中向用户提出澄清性问题。有关使用详情，请参阅 [处理批准和用户输入](/docs/en/agent-sdk/user-input#handle-clarifying-questions)。

**输入：**

```python theme={null}
{
    "questions": [  # Questions to ask the user (1-4 questions)
        {
            "question": str,  # The complete question to ask the user
            "header": str,  # Very short label displayed as a chip/tag (max 12 chars)
            "options": [  # The available choices (2-4 options)
                {
                    "label": str,  # Display text for this option (1-5 words)
                    "description": str,  # Explanation of what this option means
                    "preview": str | None,  # Preview content rendered when the option is focused
                }
            ],
            "multiSelect": bool,  # Set to true to allow multiple selections
        }
    ],
    "answers": dict[str, str] | None,
    # User answers populated by the permission system. Multi-select
    # answers are a comma-joined string of the selected labels; a
    # list of labels is accepted on input and coerced to that form
    "annotations": dict[str, dict] | None,
    # Per-question annotations from the user, keyed by question text.
    # Each value can carry "preview" (the selected option's preview
    # content) and "notes" (free-text notes on the selection)
    "metadata": dict | None,  # Analytics metadata, such as {"source": "remember"}; not displayed to the user
}
```

**输出：**

```python theme={null}
{
    "questions": [  # The questions that were asked
        {
            "question": str,
            "header": str,
            "options": [{"label": str, "description": str, "preview": str | None}],
            "multiSelect": bool,
        }
    ],
    "answers": dict[str, str],  # Maps question text to answer string
    # Multi-select answers are comma-separated
    "response": str | None,
    # Freeform reply typed instead of answering the questions; when set,
    # Claude receives "The user responded: ..." in place of the answer list
    "annotations": dict[str, dict] | None,  # Per-question "preview" and "notes" from the user's selections
    "afkTimeoutMs": int | None,  # Set when the dialog auto-resolved after this many milliseconds of user inactivity; absent when the user answered
}
```

### Bash

**工具名称：** `Bash`

**输入：**

```python theme={null}
{
    "command": str,  # The command to execute
    "timeout": int | None,  # Optional timeout in milliseconds (max 600000; higher values are clamped to the max)
    "description": str | None,  # Clear, concise description (5-10 words)
    "run_in_background": bool | None,  # Set to true to run in background
}
```

**输出：**

```python theme={null}
{
    "output": str,  # Combined stdout and stderr output
    "exitCode": int,  # Exit code of the command
    "killed": bool | None,  # Whether command was killed due to timeout
    "shellId": str | None,  # Shell ID for background processes
}
```

### Monitor

**工具名称：** `Monitor`

运行后台数据源并将每个事件传递给 Claude，使其无需轮询即可做出反应：`command` 运行脚本并按每行 stdout 发出一个事件，`ws` 打开 WebSocket 并按每个文本帧发出一个事件。必须且只能提供 `command` 或 `ws` 之一。

当 Monitor 运行命令时，它遵循与 Bash 相同的权限规则；WebSocket 监听会单独提示批准。 {/* min-version: 2.1.195 */}`ws` 数据源需要 Claude Code v2.1.195 或更高版本。有关行为和提供商可用性，请参阅 [Monitor 工具参考](/docs/en/tools-reference#monitor-tool)。

**输入：**

```python theme={null}
{
    "command": str | None,  # Shell script; each stdout line is an event, exit ends the watch
    "ws": dict | None,  # WebSocket source: {"url": str, "protocols": list[str] | None}; each text frame is an event
    "description": str,  # Short description shown in notifications
    "timeout_ms": int | None,  # Kill after this deadline (default 300000, max 3600000)
    "persistent": bool | None,  # Run for the lifetime of the session; stop with TaskStop
}
```

**输出：**

```python theme={null}
{
    "taskId": str,  # ID of the background monitor task
    "timeoutMs": int,  # Timeout deadline in milliseconds (0 when persistent)
    "persistent": bool | None,  # True when running until TaskStop or session end
}
```

### Edit

**工具名称：** `Edit`

**输入：**

```python theme={null}
{
    "file_path": str,  # The absolute path to the file to modify
    "old_string": str,  # The text to replace
    "new_string": str,  # The text to replace it with
    "replace_all": bool | None,  # Replace all occurrences (default False)
}
```

**输出：**

```python theme={null}
{
    "message": str,  # Confirmation message
    "replacements": int,  # Number of replacements made
    "file_path": str,  # File path that was edited
}
```

### Read

**工具名称：** `Read`

**输入：**

```python theme={null}
{
    "file_path": str,  # The absolute path to the file to read
    "offset": int | None,  # The line number to start reading from
    "limit": int | None,  # The number of lines to read
}
```

**输出（文本文件）：**

```python theme={null}
{
    "content": str,  # File contents with line numbers
    "total_lines": int,  # Total number of lines in file
    "lines_returned": int,  # Lines actually returned
}
```

**输出（图像）：**

```python theme={null}
{
    "image": str,  # Base64 encoded image data
    "mime_type": str,  # Image MIME type
    "file_size": int,  # File size in bytes
}
```

### Write

**工具名称：** `Write`

**输入：**

```python theme={null}
{
    "file_path": str,  # The absolute path to the file to write
    "content": str,  # The content to write to the file
}
```

**输出：**

```python theme={null}
{
    "message": str,  # Success message
    "bytes_written": int,  # Number of bytes written
    "file_path": str,  # File path that was written
}
```

### Glob

**工具名称：** `Glob`

**输入：**

```python theme={null}
{
    "pattern": str,  # The glob pattern to match files against
    "path": str | None,  # The directory to search in (defaults to cwd)
}
```

**输出：**

```python theme={null}
{
    "matches": list[str],  # Array of matching file paths
    "count": int,  # Number of matches found
    "search_path": str,  # Search directory used
}
```

### Grep

**工具名称：** `Grep`

**输入：**

```python theme={null}
{
    "pattern": str,  # The regular expression pattern
    "path": str | None,  # File or directory to search in
    "glob": str | None,  # Glob pattern to filter files
    "type": str | None,  # File type to search
    "output_mode": str | None,  # "content", "files_with_matches", or "count"
    "-i": bool | None,  # Case insensitive search
    "-n": bool | None,  # Show line numbers
    "-B": int | None,  # Lines to show before each match
    "-A": int | None,  # Lines to show after each match
    "-C": int | None,  # Lines to show before and after
    "head_limit": int | None,  # Limit output to first N lines/entries
    "multiline": bool | None,  # Enable multiline mode
}
```

**输出（content 模式）：**

```python theme={null}
{
    "matches": [
        {
            "file": str,
            "line_number": int | None,
            "line": str,
            "before_context": list[str] | None,
            "after_context": list[str] | None,
        }
    ],
    "total_matches": int,
}
```

**输出（files\_with\_matches 模式）：**

```python theme={null}
{
    "files": list[str],  # Files containing matches
    "count": int,  # Number of files with matches
}
```

### NotebookEdit

**工具名称：** `NotebookEdit`

**输入：**

```python theme={null}
{
    "notebook_path": str,  # Absolute path to the Jupyter notebook
    "cell_id": str | None,  # The ID of the cell to edit
    "new_source": str,  # The new source for the cell
    "cell_type": "code" | "markdown" | None,  # The type of the cell
    "edit_mode": "replace" | "insert" | "delete" | None,  # Edit operation type
}
```

**输出：**

```python theme={null}
{
    "message": str,  # Success message
    "edit_type": "replaced" | "inserted" | "deleted",  # Type of edit performed
    "cell_id": str | None,  # Cell ID that was affected
    "total_cells": int,  # Total cells in notebook after edit
}
```

### 网页抓取

**工具名称：** `WebFetch`

**输入：**

```python theme={null}
{
    "url": str,  # The URL to fetch content from
    "prompt": str,  # The prompt to run on the fetched content
}
```

**输出：**

```python theme={null}
{
    "bytes": int,  # Size of the fetched content in bytes
    "code": int,  # HTTP response code
    "codeText": str,  # HTTP response code text
    "result": str,  # Processed result from applying the prompt to the content
    "durationMs": int,  # Time to fetch and process the content, in milliseconds
    "url": str,  # URL that was fetched
}
```

### 网络搜索

**工具名称：** `WebSearch`

**输入：**

```python theme={null}
{
    "query": str,  # The search query to use
    "allowed_domains": list[str] | None,  # Only include results from these domains
    "blocked_domains": list[str] | None,  # Never include results from these domains
}
```

**输出：**

```python theme={null}
{
    "query": str,  # The search query
    "results": list[str | {"tool_use_id": str, "content": list[{"title": str, "url": str}]}],
    "durationSeconds": float,  # Search duration in seconds
}
```

### TodoWrite

**工具名称：** `TodoWrite`

<Note>
  自 Claude Code v2.1.142 起，`TodoWrite` 默认已禁用。请改用 `TaskCreate`、`TaskGet`、`TaskUpdate` 和 `TaskList`。请参阅 [迁移到 Task 工具](/docs/en/agent-sdk/todo-tracking#migrate-to-task-tools) 以更新您的监控代码，或设置 `CLAUDE_CODE_ENABLE_TASKS=0` 以恢复为 `TodoWrite`。
</Note>

**输入：**

```python theme={null}
{
    "todos": [
        {
            "content": str,  # The task description
            "status": "pending" | "in_progress" | "completed",  # Task status
            "activeForm": str,  # Active form of the description
        }
    ]
}
```

**输出：**

```python theme={null}
{
    "message": str,  # Success message
    "stats": {"total": int, "pending": int, "in_progress": int, "completed": int},
}
```

### TaskCreate

**工具名称：** `TaskCreate`

**输入：**

```python theme={null}
{
    "subject": str,  # Short task title
    "description": str,  # Detailed task body
    "activeForm": str | None,  # Present-tense label shown while in progress
    "metadata": dict | None,  # Arbitrary caller metadata
}
```

**输出：**

```python theme={null}
{
    "task": {"id": str, "subject": str},  # Created task with assigned ID
}
```

### TaskUpdate

**工具名称：** `TaskUpdate`

**输入：**

```python theme={null}
{
    "taskId": str,  # ID of the task to patch
    "status": Literal["pending", "in_progress", "completed", "deleted"] | None,
    "subject": str | None,
    "description": str | None,
    "activeForm": str | None,
    "addBlocks": list[str] | None,  # Task IDs this task now blocks
    "addBlockedBy": list[str] | None,  # Task IDs that now block this task
    "owner": str | None,
    "metadata": dict | None,
}
```

**输出：**

```python theme={null}
{
    "success": bool,
    "taskId": str,
    "updatedFields": list[str],  # Names of fields that changed
    "error": str | None,
    "statusChange": {"from": str, "to": str} | None,
}
```

### TaskGet

**工具名称：** `TaskGet`

**输入：**

```python theme={null}
{
    "taskId": str,  # ID of the task to read
}
```

**输出：**

```python theme={null}
{
    "task": {
        "id": str,
        "subject": str,
        "description": str,
        "status": Literal["pending", "in_progress", "completed"],
        "blocks": list[str],
        "blockedBy": list[str],
    } | None,  # None when the ID is not found
}
```

### TaskList

**工具名称：** `TaskList`

**输入：**

```python theme={null}
{}
```

**输出：**

```python theme={null}
{
    "tasks": [
        {
            "id": str,
            "subject": str,
            "status": Literal["pending", "in_progress", "completed"],
            "owner": str | None,
            "blockedBy": list[str],
        }
    ],
}
```

### TaskOutput

**工具名称：** `TaskOutput`。之前的名称 `BashOutput` 仍作为别名被接受。

<Note>`TaskOutput` 已弃用；建议优先在任务的输出文件路径上使用 `Read`。{/* min-version: 2.1.83 */}自 Claude Code v2.1.83 起弃用。以下 schema 对于遇到该工具的钩子和权限处理程序仍然有效。</Note>

**输入：**

```python theme={null}
{
    "task_id": str,  # The task ID to get output from
    "block": bool,  # Whether to wait for completion (default True)
    "timeout": int,  # Max wait time in ms (default 30000)
}
```

**输出：**

```python theme={null}
{
    "retrieval_status": "success" | "timeout" | "not_ready",  # Whether the output was retrieved
    "task": dict | None,  # Task details: task_id, task_type, status, description, output, plus type-specific fields such as exitCode
}
```

### TaskStop

**工具名称：** `TaskStop`。之前的名称 `KillShell` 和 `KillBash` 仍作为别名被接受。

**输入：**

```python theme={null}
{
    "task_id": str | None,  # The ID of the background task to stop
    "shell_id": str | None,  # Deprecated: use task_id instead
}
```

**输出：**

```python theme={null}
{
    "message": str,  # Status message about the operation
    "task_id": str,  # The ID of the task that was stopped
    "task_type": str,  # The type of the task that was stopped
    "command": str | None,  # The command or description of the stopped task
}
```

### ExitPlanMode

**工具名称：** `ExitPlanMode`

**输入：**

```python theme={null}
{
    "plan": str  # The plan to run by the user for approval
}
```

**输出：**

```python theme={null}
{
    "message": str,  # Confirmation message
    "approved": bool | None,  # Whether user approved the plan
}
```

### ListMcpResources

**工具名称：** `ListMcpResourcesTool`

**输入：**

```python theme={null}
{
    "server": str | None  # Optional server name to filter resources by
}
```

**输出：**

```python theme={null}
{
    "resources": [
        {
            "uri": str,
            "name": str,
            "description": str | None,
            "mimeType": str | None,
            "server": str,
        }
    ],
    "total": int,
}
```

### ReadMcpResource

**工具名称：** `ReadMcpResourceTool`

**输入：**

```python theme={null}
{
    "server": str,  # The MCP server name
    "uri": str,  # The resource URI to read
}
```

**输出：**

```python theme={null}
{
    "contents": [
        {"uri": str, "mimeType": str | None, "text": str | None, "blob": str | None}
    ],
    "server": str,
}
```

## ClaudeSDKClient 的高级功能

### 构建持续对话界面

```python theme={null}
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
)
import asyncio


class ConversationSession:
    """Maintains a single conversation session with Claude."""

    def __init__(self, options: ClaudeAgentOptions | None = None):
        self.client = ClaudeSDKClient(options)
        self.turn_count = 0

    async def start(self):
        await self.client.connect()
        print("Starting conversation session. Claude will remember context.")
        print(
            "Commands: 'exit' to quit, 'interrupt' to stop current task, 'new' for new session"
        )

        while True:
            user_input = input(f"\n[Turn {self.turn_count + 1}] You: ")

            if user_input.lower() == "exit":
                break
            elif user_input.lower() == "interrupt":
                await self.client.interrupt()
                print("Task interrupted!")
                continue
            elif user_input.lower() == "new":
                # Disconnect and reconnect for a fresh session
                await self.client.disconnect()
                await self.client.connect()
                self.turn_count = 0
                print("Started new conversation session (previous context cleared)")
                continue

            # Send message - the session retains all previous messages
            await self.client.query(user_input)
            self.turn_count += 1

            # Process response
            print(f"[Turn {self.turn_count}] Claude: ", end="")
            async for message in self.client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            print(block.text, end="")
            print()  # New line after response

        await self.client.disconnect()
        print(f"Conversation ended after {self.turn_count} turns.")


async def main():
    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Write", "Bash"], permission_mode="acceptEdits"
    )
    session = ConversationSession(options)
    await session.start()


# Example conversation:

# Turn 1 - You: "Create a file called hello.py"

# Turn 1 - Claude: "I'll create a hello.py file for you..."

# Turn 2 - You: "What's in that file?"

# Turn 2 - Claude: "The hello.py file I just created contains..." (remembers!)

# Turn 3 - You: "Add a main function to it"

# Turn 3 - Claude: "I'll add a main function to hello.py..." (knows which file!)

asyncio.run(main())
```

### 使用钩子修改行为

```python theme={null}
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    HookMatcher,
    HookContext,
)
import asyncio
from typing import Any


async def pre_tool_logger(
    input_data: dict[str, Any], tool_use_id: str | None, context: HookContext
) -> dict[str, Any]:
    """Log all tool usage before execution."""
    tool_name = input_data.get("tool_name", "unknown")
    print(f"[PRE-TOOL] About to use: {tool_name}")

    # You can modify or block the tool execution here
    if tool_name == "Bash" and "rm -rf" in str(input_data.get("tool_input", {})):
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": "Dangerous command blocked",
            }
        }
    return {}


async def post_tool_logger(
    input_data: dict[str, Any], tool_use_id: str | None, context: HookContext
) -> dict[str, Any]:
    """Log results after tool execution."""
    tool_name = input_data.get("tool_name", "unknown")
    print(f"[POST-TOOL] Completed: {tool_name}")
    return {}


async def user_prompt_modifier(
    input_data: dict[str, Any], tool_use_id: str | None, context: HookContext
) -> dict[str, Any]:
    """Add context to user prompts."""
    original_prompt = input_data.get("prompt", "")

    # Add a timestamp as additional context for Claude to see
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": f"[Submitted at {timestamp}] Original prompt: {original_prompt}",
        }
    }


async def main():
    options = ClaudeAgentOptions(
        hooks={
            "PreToolUse": [
                HookMatcher(hooks=[pre_tool_logger]),
                HookMatcher(matcher="Bash", hooks=[pre_tool_logger]),
            ],
            "PostToolUse": [HookMatcher(hooks=[post_tool_logger])],
            "UserPromptSubmit": [HookMatcher(hooks=[user_prompt_modifier])],
        },
        allowed_tools=["Read", "Write", "Bash"],
    )

    async with ClaudeSDKClient(options=options) as client:
        await client.query("List files in current directory")

        async for message in client.receive_response():
            # Hooks will automatically log tool usage
            pass


asyncio.run(main())
```

### 实时进度监控

```python theme={null}
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    ToolUseBlock,
    ToolResultBlock,
    TextBlock,
)
import asyncio


async def monitor_progress():
    options = ClaudeAgentOptions(
        allowed_tools=["Write", "Bash"], permission_mode="acceptEdits"
    )

    async with ClaudeSDKClient(options=options) as client:
        await client.query("Create 5 Python files with different sorting algorithms")

        # Monitor progress in real-time
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, ToolUseBlock):
                        if block.name == "Write":
                            file_path = block.input.get("file_path", "")
                            print(f"Creating: {file_path}")
                    elif isinstance(block, ToolResultBlock):
                        print("Completed tool execution")
                    elif isinstance(block, TextBlock):
                        print(f"Claude says: {block.text[:100]}...")

        print("Task completed!")


asyncio.run(monitor_progress())
```

## 用法示例

### 基本文件操作（使用 query）

```python theme={null}
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, ToolUseBlock
import asyncio


async def create_project():
    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Write", "Bash"],
        permission_mode="acceptEdits",
    )

    async for message in query(
        prompt="Create a Python project structure with setup.py", options=options
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, ToolUseBlock):
                    print(f"Using tool: {block.name}")


asyncio.run(create_project())
```

### 错误处理

```python theme={null}
import asyncio

from claude_agent_sdk import query, CLINotFoundError, ProcessError, CLIJSONDecodeError


async def main():
    try:
        async for message in query(prompt="Hello"):
            print(message)
    except CLINotFoundError:
        print(
            "Claude Code CLI not found. Try reinstalling: pip install --force-reinstall claude-agent-sdk"
        )
    except ProcessError as e:
        print(f"Process failed with exit code: {e.exit_code}")
    except CLIJSONDecodeError as e:
        print(f"Failed to parse response: {e}")


asyncio.run(main())
```

### 使用客户端的流式模式

```python theme={null}
from claude_agent_sdk import ClaudeSDKClient
import asyncio


async def interactive_session():
    async with ClaudeSDKClient() as client:
        # Send initial message
        await client.query("What's the weather like?")

        # Process responses
        async for msg in client.receive_response():
            print(msg)

        # Send follow-up
        await client.query("Tell me more about that")

        # Process follow-up response
        async for msg in client.receive_response():
            print(msg)


asyncio.run(interactive_session())
```

### 在 ClaudeSDKClient 中使用自定义工具

```python theme={null}
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    tool,
    create_sdk_mcp_server,
    AssistantMessage,
    TextBlock,
)
import asyncio
from typing import Any


# Define custom tools with @tool decorator

@tool("calculate", "Perform mathematical calculations", {"expression": str})
async def calculate(args: dict[str, Any]) -> dict[str, Any]:
    try:
        result = eval(args["expression"], {"__builtins__": {}})
        return {"content": [{"type": "text", "text": f"Result: {result}"}]}
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error: {str(e)}"}],
            "is_error": True,
        }


@tool("get_time", "Get current time", {})
async def get_time(args: dict[str, Any]) -> dict[str, Any]:
    from datetime import datetime

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {"content": [{"type": "text", "text": f"Current time: {current_time}"}]}


async def main():
    # Create SDK MCP server with custom tools
    my_server = create_sdk_mcp_server(
        name="utilities", version="1.0.0", tools=[calculate, get_time]
    )

    # Configure options with the server
    options = ClaudeAgentOptions(
        mcp_servers={"utils": my_server},
        allowed_tools=["mcp__utils__calculate", "mcp__utils__get_time"],
    )

    # Use ClaudeSDKClient for interactive tool usage
    async with ClaudeSDKClient(options=options) as client:
        await client.query("What's 123 * 456?")

        # Process calculation response
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"Calculation: {block.text}")

        # Follow up with time query
        await client.query("What time is it now?")

        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"Time: {block.text}")


asyncio.run(main())
```

## 沙箱配置

### `SandboxSettings`

沙盒行为的配置。使用此配置以编程方式启用命令沙盒并配置网络限制。

```python theme={null}
class SandboxSettings(TypedDict, total=False):
    enabled: bool
    autoAllowBashIfSandboxed: bool
    excludedCommands: list[str]
    allowUnsandboxedCommands: bool
    network: SandboxNetworkConfig
    ignoreViolations: SandboxIgnoreViolations
    enableWeakerNestedSandbox: bool
```

| 属性                        | 类型                                                  | 默认值 | 描述                                                                                                                                                                                                                          |
| :-------------------------- | :---------------------------------------------------- | :------ | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `enabled`                   | `bool`                                                | `False` | 为命令执行启用沙盒模式                                                                                                                                                                                                          |
| `autoAllowBashIfSandboxed`  | `bool`                                                | `True`  | 启用沙盒时自动批准 bash 命令                                                                                                                                                                                                     |
| `excludedCommands`          | `list[str]`                                           | `[]`    | 始终绕过沙盒限制的命令（例如 `["docker"]`）。这些命令会自动在非沙盒环境中运行，无需模型参与                                                                                                                       |
| `allowUnsandboxedCommands`  | `bool`                                                | `True`  | 允许模型请求在沙盒外运行命令。当为 `True` 时，模型可以在工具输入中设置 `dangerouslyDisableSandbox`，这将回退到 [权限系统](#permissions-fallback-for-unsandboxed-commands) |
| `network`                   | [`SandboxNetworkConfig`](#sandboxnetworkconfig)       | `None`  | 特定于网络的沙盒配置                                                                                                                                                                                                            |
| `ignoreViolations`          | [`SandboxIgnoreViolations`](#sandboxignoreviolations) | `None`  | 配置要忽略哪些沙盒违规                                                                                                                                                                                                          |
| `enableWeakerNestedSandbox` | `bool`                                                | `False` | 启用较弱的嵌套沙盒以保证兼容性                                                                                                                                                                                                   |

<Note>
  沙盒依赖于平台支持，在 Linux 上还依赖于 `bubblewrap` 和 `socat` 等工具。默认情况下，当 `enabled` 为 `True` 但沙盒无法启动时，命令会在非沙盒环境中运行，并在 stderr 上输出警告。此默认值与 TypeScript SDK 不同，在后者中 `failIfUnavailable` 默认为 `true`。

  在你的沙盒设置中设置 `"failIfUnavailable": True` 以改为停止。该键尚未在 `SandboxSettings` 上声明，但 SDK 会将其转发给 Claude Code，而后者会遵循它。随后 `query()` 会报告一个 `subtype="error_during_execution"` 的 `ResultMessage`，并将原因放在 `errors` 中。由于这是一次性的 `query()` 调用，SDK 会在产出该错误结果后抛出异常，因此请将循环包裹在 try 块中以便继续执行。有关错误约定，请参阅 [处理结果](/docs/en/agent-sdk/agent-loop#handle-the-result)。
</Note>

#### 使用示例

```python theme={null}
import asyncio

from claude_agent_sdk import query, ClaudeAgentOptions, SandboxSettings

sandbox_settings: SandboxSettings = {
    "enabled": True,
    "autoAllowBashIfSandboxed": True,
    "network": {"allowLocalBinding": True},
}


async def main():
    try:
        async for message in query(
            prompt="Build and test my project",
            options=ClaudeAgentOptions(sandbox=sandbox_settings),
        ):
            print(message)
    except Exception as error:
        # A single-shot query() raises after yielding an error result,
        # such as when failIfUnavailable is set and the sandbox can't start.
        print(f"Session ended with an error: {error}")


asyncio.run(main())
```

<Warning>
  **Unix socket 安全性**：`allowUnixSockets` 选项可能会授予对强大系统服务的访问权限。例如，允许 `/var/run/docker.sock` 实际上等同于通过 Docker API 授予对主机系统的完全访问权限，从而绕过沙箱隔离。请仅允许严格必需的 Unix socket，并了解每一项的安全影响。
</Warning>

### `SandboxNetworkConfig`

沙盒模式的特定网络配置。这些设置适用于沙盒化的 Bash 命令，当 `enabled` 为 `True` 且位于父级 [`SandboxSettings`](#sandboxsettings) 中时。它们不会限制 WebFetch 工具，该工具改用 [权限规则](/docs/en/permissions#webfetch)。

```python theme={null}
class SandboxNetworkConfig(TypedDict, total=False):
    allowedDomains: list[str]
    deniedDomains: list[str]
    allowManagedDomainsOnly: bool
    allowUnixSockets: list[str]
    allowAllUnixSockets: bool
    allowLocalBinding: bool
    allowMachLookup: list[str]
    httpProxyPort: int
    socksProxyPort: int
```

| 属性                      | 类型        | 默认值 | 描述                                                                                                                                                     |
| :------------------------ | :---------- | :------ | :----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `allowedDomains`          | `list[str]` | `[]`    | 沙箱进程可以访问的域名                                                                                                                                  |
| `deniedDomains`           | `list[str]` | `[]`    | 沙箱进程无法访问的域名。优先级高于 `allowedDomains`                                                                                              |
| `allowManagedDomainsOnly` | `bool`      | `False` | 仅限托管设置：在托管设置中设置时，忽略来自非托管设置来源的 `allowedDomains`。通过 SDK 选项设置时无效。 |
| `allowUnixSockets`        | `list[str]` | `[]`    | 进程可以访问的 Unix 套接字路径（例如 Docker 套接字）                                                                                                  |
| `allowAllUnixSockets`     | `bool`      | `False` | 允许访问所有 Unix 套接字                                                                                                                              |
| `allowLocalBinding`       | `bool`      | `False` | 允许进程绑定到本地端口（例如用于开发服务器）                                                                                                          |
| `allowMachLookup`         | `list[str]` | `[]`    | 仅限 macOS：允许使用的 XPC/Mach 服务名称。支持尾部通配符                                                                              |
| `httpProxyPort`           | `int`       | `None`  | 用于网络请求的 HTTP 代理端口                                                                                                                   |
| `socksProxyPort`          | `int`       | `None`  | 用于网络请求的 SOCKS 代理端口                                                                                                                  |

<Note>
  内置沙箱代理根据请求的主机名强制执行网络允许列表，并且不会终止或检查 TLS 流量，因此诸如 [域名前置](https://en.wikipedia.org/wiki/Domain_fronting) 之类的技术有可能绕过它。详情请参阅 [沙箱安全限制](/docs/en/sandboxing#security-limitations)，有关配置 TLS 终止代理的信息请参阅 [安全部署](/docs/en/agent-sdk/secure-deployment#traffic-forwarding)。
</Note>

### `SandboxIgnoreViolations`

用于忽略特定沙箱违规行为的配置。

```python theme={null}
class SandboxIgnoreViolations(TypedDict, total=False):
    file: list[str]
    network: list[str]
```

| 属性  | 类型        | 默认值 | 描述                                 |
| :-------- | :---------- | :------ | :------------------------------------------ |
| `file`    | `list[str]` | `[]`    | 要忽略违规行为的文件路径模式 |
| `network` | `list[str]` | `[]`    | 要忽略违规行为的网络模式   |

### 非沙箱命令的权限回退

启用 `allowUnsandboxedCommands` 后，模型可以通过在工具输入中设置 `dangerouslyDisableSandbox: True` 来请求在沙箱外运行命令。这些请求会回退到现有的权限系统，这意味着你的 `can_use_tool` 处理程序将被调用，从而允许你实现自定义授权逻辑。

<Note>
  **`excludedCommands` 与 `allowUnsandboxedCommands` 的对比：**

  * `excludedCommands`：一个静态的命令列表，其中的命令始终自动绕过沙箱（例如 `["docker"]`）。模型对此没有控制权。
  * `allowUnsandboxedCommands`：允许模型在运行时通过在工具输入中设置 `dangerouslyDisableSandbox: True` 来决定是否请求非沙箱执行。
</Note>

```python theme={null}
import asyncio
from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    HookMatcher,
    PermissionResultAllow,
    PermissionResultDeny,
    ToolPermissionContext,
)


def is_command_authorized(command: str | None) -> bool:
    # Replace with your own authorization logic
    return False



async def can_use_tool(
    tool: str, input: dict, context: ToolPermissionContext
) -> PermissionResultAllow | PermissionResultDeny:
    # Check if the model is requesting to bypass the sandbox
    if tool == "Bash" and input.get("dangerouslyDisableSandbox"):
        # The model is requesting to run this command outside the sandbox
        print(f"Unsandboxed command requested: {input.get('command')}")

        if is_command_authorized(input.get("command")):
            return PermissionResultAllow()
        return PermissionResultDeny(
            message="Command not authorized for unsandboxed execution"
        )
    return PermissionResultAllow()


# Required: dummy hook keeps the stream open for can_use_tool

async def dummy_hook(input_data, tool_use_id, context):
    return {"continue_": True}


async def prompt_stream():
    yield {
        "type": "user",
        "message": {"role": "user", "content": "Deploy my application"},
    }


async def main():
    async for message in query(
        prompt=prompt_stream(),
        options=ClaudeAgentOptions(
            sandbox={
                "enabled": True,
                "allowUnsandboxedCommands": True,  # Model can request unsandboxed execution
            },
            permission_mode="default",
            can_use_tool=can_use_tool,
            hooks={"PreToolUse": [HookMatcher(matcher=None, hooks=[dummy_hook])]},
        ),
    ):
        print(message)


asyncio.run(main())
```

此模式使你能够：

* **审计模型请求**：记录模型请求非沙箱执行的情况
* **实现允许列表**：仅允许特定命令在非沙箱环境中运行
* **添加审批工作流**：对特权操作要求显式授权

<Warning>
  以 `dangerouslyDisableSandbox: True` 运行的命令拥有完整的系统访问权限。请确保你的 `can_use_tool` 处理程序仔细验证这些请求。

  如果 `permission_mode` 设置为 `bypassPermissions` 且 `allow_unsandboxed_commands` 已启用，模型可以在没有批准提示的情况下自主地在沙箱外执行命令（显式的 [`ask` 规则](/docs/en/agent-sdk/permissions#how-permissions-are-evaluated) 仍会强制提示）。这种组合实际上允许模型悄无声息地逃离沙箱隔离。
</Warning>

## 另请参阅

* [SDK 概述](/docs/en/agent-sdk/overview) - 通用 SDK 概念
* [TypeScript SDK 参考](/docs/en/agent-sdk/typescript) - TypeScript SDK 文档
* [CLI 参考](/docs/en/cli-reference) - 命令行界面
* [常见工作流](/docs/en/common-workflows) - 分步指南

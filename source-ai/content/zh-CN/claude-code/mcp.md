---
title: 通过 MCP 将 Claude Code 连接到工具
source_id: claude-code/mcp
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/mcp
owner: Anthropic
content_sha256: acbac522302deea325064f84d476630b59429b78da33a60d946493358c60d0f5
translation_of: claude-code/mcp
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/mcp)

Content owner: Anthropic

> ## 文档索引
> 获取完整的文档索引，请访问： https://code.claude.com/docs/llms.txt
> 在进一步探索之前，请使用此文件来发现所有可用页面。

# 通过 MCP 将 Claude Code 连接到工具

> 了解如何使用模型上下文协议将 Claude Code 连接到您的工具。

Claude Code 可以通过 [模型上下文协议 (MCP)](https://modelcontextprotocol.io/introduction) 连接到数百个外部工具和数据源，这是一个用于 AI 工具集成的开源标准。MCP 服务器让 Claude Code 能够访问您的工具、数据库和 API。

当您发现自己从其他工具（如问题追踪器或监控仪表板）复制数据到聊天中时，就可以连接服务器。连接后，Claude 可以直接读取并对该系统进行操作，而无需依赖您粘贴的内容。

如果您是第一次连接服务器，请从 [MCP 快速入门](/docs/en/mcp-quickstart) 开始，了解逐步操作指南。本页面是完整的参考文档。

## 使用 MCP 可以做什么

连接 MCP 服务器后，您可以要求 Claude Code 执行以下操作：

* **实现问题追踪器中的功能**：“添加 JIRA 问题 ENG-4521 中描述的功能，并在 GitHub 上创建 PR。”
* **分析监控数据**：“检查 Sentry 和 Statsig，查看 ENG-4521 中描述的功能的使用情况。”
* **查询数据库**：“基于我们的 PostgreSQL 数据库，查找使用过 ENG-4521 功能的 10 位随机用户的电子邮件。”
* **整合设计**：“根据 Slack 上发布的新 Figma 设计，更新我们的标准邮件模板”
* **自动化工作流程**：“在 Gmail 中创建草稿，邀请这 10 位用户参加有关新功能的反馈会议。”
* **响应外部事件**：MCP 服务器还可以充当一个 [频道](/docs/en/channels)，将消息推送到您的会话中，这样 Claude 就能在您离开时对 Telegram 消息、Discord 聊天或 Webhook 事件做出反应。

## 查找并构建 MCP 服务器

在 [Anthropic 目录](https://claude.ai/directory) 中浏览经过审核的连接器。目录连接器使用与 Claude Code 相同的 MCP 基础设施，因此您可以使用 `claude mcp add` 添加那里列出的任何远程服务器。

<Warning>
  在连接之前，请验证您是否信任每个服务器。获取外部内容的服务器可能会使您面临 [提示词注入风险](/docs/en/security#protect-against-prompt-injection)。
</Warning>

要构建您自己的服务器，请参阅 [MCP 服务器指南](https://modelcontextprotocol.io/docs/develop/build-server) 了解协议基础知识，以及 [Claude 连接器构建文档](https://claude.com/docs/connectors/building) 了解身份验证、测试和目录提交。

您还可以使用官方的 [`mcp-server-dev` 插件](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/mcp-server-dev) 让 Claude 为您搭建服务器。

<Steps>
  <Step title="安装插件">
    在 Claude Code 会话中，运行：

    ```
    /plugin install mcp-server-dev@claude-plugins-official
    ```

    如果 Claude Code 报告 `Marketplace "claude-plugins-official" not found`，请使用 `/plugin marketplace add anthropics/claude-plugins-official` 添加市场。如果报告在市场中找不到该插件，说明您的本地副本已过期：请使用 `/plugin marketplace update claude-plugins-official` 刷新它。然后重试安装。安装完成后，运行 `/reload-plugins` 在当前会话中激活它。
  </Step>

  <Step title="运行构建技能">
    ```
    /mcp-server-dev:build-mcp-server
    ```

    Claude 会询问您的用例，并为您搭建远程 HTTP 或本地 stdio 服务器。
  </Step>
</Steps>

## 安装 MCP 服务器

MCP 服务器可以通过多种方式进行配置，具体取决于您的需求：

### 选项 1：添加远程 HTTP 服务器

HTTP 服务器是连接到远程 MCP 服务器的推荐选项。这是针对云服务支持最广泛的传输方式。

```bash theme={null}
# Basic syntax

claude mcp add --transport http <name> <url>

# Real example: Connect to Notion

claude mcp add --transport http notion https://mcp.notion.com/mcp

# Example with Bearer token

claude mcp add --transport http secure-api https://api.example.com/mcp \
  --header "Authorization: Bearer your-token"
```

在 `.mcp.json`、`~/.claude.json` 或 `claude mcp add-json` 中通过 JSON 配置 MCP 服务器时，`type` 字段接受 `streamable-http` 作为 `http` 的别名。MCP 规范为此传输方式使用 `streamable-http` 名称，因此从服务器文档复制的配置无需修改即可使用。

具有 `url` 但没有 `type` 的 JSON 条目是一个配置错误，因为 Claude Code 会将没有 `type` 的条目读取为 stdio 服务器。Claude Code 会跳过该服务器并报告 `MCP server "<name>" has a "url" but no "type"; add "type": "http" (or "sse" / "ws") to this entry`。在 v2.1.202 之前，Claude Code 曾将这种错误配置报告为 `command: expected string, received undefined`。

### 选项 2：添加远程 SSE 服务器

<Warning>
  SSE（服务器发送事件）传输方式已被弃用。请在可用的情况下改用 HTTP 服务器。
</Warning>

```bash theme={null}
# Basic syntax

claude mcp add --transport sse <name> <url>

# Real example: Connect to Asana

claude mcp add --transport sse asana https://mcp.asana.com/sse

# Example with authentication header

claude mcp add --transport sse private-api https://api.company.com/sse \
  --header "X-API-Key: your-key-here"
```

### 选项 3：添加本地 stdio 服务器

Stdio 服务器作为你机器上的本地进程运行。它们非常适合需要直接系统访问权限或自定义脚本的工具。

Claude Code 将生成的服务器环境中的 `CLAUDE_PROJECT_DIR` 设置为项目根目录，因此你的服务器可以解析项目相对路径，而无需依赖工作目录。这与钩子在其 `CLAUDE_PROJECT_DIR` 变量中接收到的目录相同。在你的服务器进程内部读取它，例如在 Node 中使用 `process.env.CLAUDE_PROJECT_DIR` 或在 Python 中使用 `os.environ["CLAUDE_PROJECT_DIR"]`。

`CLAUDE_PROJECT_DIR` 是稳定的项目根目录，当您在会话期间添加或删除工作目录时，它不会发生改变。将自身文件系统访问限制在一系列允许目录内的服务器，应该转而实现 MCP `roots/list` 请求。Claude Code 响应 `roots/list`，包含会话的启动目录加上每个 [附加工作目录](/docs/en/permissions#working-directories)，即您通过 `--add-dir`、`/add-dir` 或 `additionalDirectories` 设置所授予的目录。Claude Code 会在该集合发生更改时发送 `notifications/roots/list_changed`。在 v2.1.203 之前，`roots/list` 仅返回启动目录，并且 Claude Code 不会发送 `notifications/roots/list_changed`。

此变量设置在服务器的环境中，而不是 Claude Code 自己的环境中，因此在项目作用域的 `${VAR}` 条目的 `command` 或 `args` 中，或者在 `.mcp.json` 中的本地或用户作用域服务器条目中，通过 `~/.claude.json` 展开来引用它时，需要一个默认值，例如 `${CLAUDE_PROJECT_DIR:-.}`。插件提供的 MCP 配置直接替换 `${CLAUDE_PROJECT_DIR}` 并且不需要该默认值。

```bash theme={null}
# Basic syntax

claude mcp add [options] <name> -- <command> [args...]

# Real example: Add Airtable server

claude mcp add --env AIRTABLE_API_KEY=YOUR_KEY --transport stdio airtable \
  -- npx -y airtable-mcp-server
```

<Note>
  **重要提示：使用 `--` 分隔服务器参数**

对于 stdio 服务器，`--`（双横线）将 Claude 自身的选项（例如 `--transport`、`--env` 和 `--scope`）与运行服务器的命令及参数分隔开来。在 `--` 之后的所有内容都将原封不动地传递给服务器。

  例如：

  * `claude mcp add --transport stdio myserver -- npx server` → 运行 `npx server`
  * `claude mcp add --env KEY=value --transport stdio myserver -- python server.py --port 8080` → 运行 `python server.py --port 8080` 并在环境中带有 `KEY=value`

  如果没有 `--`，Claude Code 会尝试将服务器的标志（如上面的 `--port`）解析为自身的选项。

  `--env` 接受多个 `KEY=value` 对。如果服务器名称直接跟在 `--env` 之后，CLI 会将该名称读取为另一个对并拒绝执行，因此请如上面的示例所示，在 `--env` 和服务器名称之间至少放置一个其他选项。
</Note>

### 选项 4：添加远程 WebSocket 服务器

WebSocket 服务器保持持久的双向连接，这非常适合主动向 Claude 推送事件的远程 MCP 服务器。当您的服务器仅响应请求时，请改用 HTTP，因为 HTTP 支持 OAuth 和 `claude mcp add --transport` 标志，而 WebSocket 两者都不支持。

在 `.mcp.json` 中或使用 `claude mcp add-json` 配置 WebSocket 服务器：

```bash theme={null}
claude mcp add-json events-server \
  '{"type":"ws","url":"wss://mcp.example.com/socket","headers":{"Authorization":"Bearer YOUR_TOKEN"}}'
```

`type: "ws"` 条目接受与 `url` 相同的 `headers`、`headersHelper`、`timeout`、`alwaysLoad` 和 `http` 字段。身份验证仅限标头，因此请在 `headers` 中传入静态令牌，或者在连接时使用 [`headersHelper`](#use-dynamic-headers-for-custom-authentication) 生成一个。`claude mcp add --transport` 标志不接受 `ws`。

### 管理您的服务器

配置完成后，您可以使用以下命令管理您的 MCP 服务器：

```bash theme={null}
# List all configured servers

claude mcp list

# Get details for a specific server

claude mcp get github

# Remove a server

claude mcp remove github

# (within Claude Code) Check server status

/mcp
```

来自 `.mcp.json` 且正在等待您批准的项目级服务器会在 `claude mcp list` 和 `claude mcp get <name>` 中显示为 ``⏸ Pending approval (run `claude` to approve)``. Run `claude` interactively to review and approve them. `claude mcp get <name>` shows rejected servers as `✘ Rejected (see disabledMcpjsonServers in settings)`。

从 v2.1.196 版本开始，`claude mcp list` 和 `claude mcp get` 仅从尚未提交到代码库的设置文件中读取 `.mcp.json` 批准，直到您在其中运行 `claude` 并接受工作区信任对话框来信任该工作区。克隆的代码库无法批准其自身的服务器：提交到项目 [ 中的 `enableAllProjectMcpServers``enabledMcpjsonServers` 或 ](/docs/en/settings#available-settings)`.claude/settings.json` 在不受信任的文件夹中将被忽略，并且服务器将保持在 `⏸ Pending approval` 状态，而不是被连接并进行健康检查。

在不受信任的文件夹中，来自以下来源的批准仍然适用：

* 您的用户 `~/.claude/settings.json`
* 托管设置
* 通过 `--settings` 传递的设置

在未跟踪的 `.claude/settings.local.json` 中的批准也会生效，但前提是您接受了该文件夹或其某个父目录的信任对话框：Claude Code 会运行 git 来检查该文件是否被跟踪，并且该检查仅在受信任的文件夹中运行。在您从未信任的文件夹中，该文件的批准会等待信任对话框，除非该文件夹是您自己的配置主目录：您的主目录，或者您将其 `.claude` 设置为 [`CLAUDE_CONFIG_DIR`](/docs/en/env-vars) 的目录。在 v2.1.207 版本之前，未跟踪的 `.claude/settings.local.json` 会在您从未信任的文件夹中批准服务器。

任何设置文件中的 `disabledMcpjsonServers` 条目仍然会拒绝该服务器。

`/mcp` 面板在每个已连接的服务器旁边显示工具数量，并标记那些宣告了工具能力但未暴露任何工具的服务器。

配置中带有空的 `url` 的远程服务器显示为 `not configured` 在 `/mcp` 中，在 `claude mcp list` 中，以及在 [`/plugin`](/docs/en/plugins) 中 经理，而 Claude Code 并不试图 以连接到它。插件可以包含这样的占位符条目，供您稍后配置连接器，这样 Claude Code 就不会将其报告为错误或设置问题。`/mcp` 中的服务器详细视图显示为 `No URL configured for this server`；设置该条目的 `url` 以连接它。在 v2.1.208 之前，Claude Code 会将空的 `url` 报告为配置问题 与 重新连接的提示。

如果您的请求需要来自仍在后台连接的服务器的工具，Claude 会在继续之前等待该服务器。在启用了 [tool search](#scale-with-mcp-tool-search) 的情况下（这是默认设置），等待将发生在 `ToolSearch` 调用内部。在没有工具搜索的配置中，例如 Google Cloud 的 Agent Platform、自定义的 `ANTHROPIC_BASE_URL` 或 `ENABLE_TOOL_SEARCH=false`，Claude 会改用 `WaitForMcpServers` 工具。

某些服务器名称保留给 Claude Code 的内置服务器：`workspace`、`claude-in-chrome`、`computer-use`、`Claude Preview` 和 `Claude Browser`。如果您的配置定义了具有保留名称的服务器，Claude Code 会在加载时跳过它，并显示一条警告要求您重命名。`claude mcp add` 会拒绝保留名称并报错。

`Claude Preview` 和 `Claude Browser` 都命名了 [Claude Code 桌面应用程序的预览窗格](/docs/en/desktop#preview-your-app) 所使用的内置服务器。在 v2.1.205 之前，`Claude Browser` 并未被保留，因此用户配置的服务器可以使用该名称进行注册。

### 禁用服务器而不删除它

在 `/mcp` 面板中关闭服务器，可以阻止 Claude Code 连接到它，同时不会丢失其配置。Claude Code 仍然会在 `/mcp` 中列出该服务器，但标记为已禁用。

当您切换服务器时，Claude Code 会将您的选择按项目记录在 `~/.claude.json` 中，并放在涵盖互不相交的服务器集合的两个列表之一中：

* `disabledMcpServers`：一个用于用户配置的服务器、插件服务器、claude.ai 连接器以及默认开启的内置服务器的退出列表。 Claude Code 不会连接到您在此处列出的服务器。当您使用每个项目的 `/mcp` 开关禁用 claude.ai 连接器时（如 [Disable claude.ai connectors](#disable-claude-ai-connectors) 中所述），Claude Code 会按照其显示名称将其写入此列表，例如 `claude.ai Slack`。
* `enabledMcpServers`：一个用于默认关闭的内置服务器的选择启用列表，例如 `computer-use`。Claude Code 仅在您将其列于此处时才连接到默认关闭的服务器。

Claude Code 会确切地为每个服务器查阅这两个列表之一，因此任何一个列表都不会覆盖另一个。如果您将常规服务器添加到 `enabledMcpServers`，或者将默认关闭的内置服务器添加到 `disabledMcpServers`，Claude Code 会忽略该条目。

`disabledMcpServers` 和 `enabledMcpServers` 与 [`enabledMcpjsonServers` 和 `disabledMcpjsonServers`](/docs/en/settings#available-settings) 无关，后者控制对项目的 `.mcp.json` 文件中定义的服务器的批准。

### 动态工具更新

Claude Code 支持 MCP `list_changed` 通知，允许 MCP 服务器动态更新其可用的工具、提示和资源，而无需您断开并重新连接。当 MCP 服务器发送 `list_changed` 通知时，Claude Code 会自动刷新来自该服务器的可用功能。

如果刷新请求失败，Claude Code 会保留服务器先前发现的工具、提示和资源，直到随后的刷新成功。在 v2.1.214 版本之前，刷新期间发生的短暂错误会将服务器的工具、提示和资源替换为空列表。

### 自动重连

如果HTTP或SSE服务器在会话中途中断连接，Claude Code会自动以指数退避方式重连：最多尝试五次，首次延迟一秒，之后每次倍增。重连进行时，服务器在`/mcp`中显示为挂起状态。五次尝试失败后，服务器将被标记为失败，您可以从`/mcp`手动重试。Stdio服务器是本地进程，不会自动重连。

当HTTP或SSE服务器在启动时初始连接失败时，适用相同的退避机制。自v2.1.121版本起，Claude Code对于5xx响应、连接被拒绝或超时等瞬时错误，会最多重试初始连接三次，如果仍无法连接则将服务器标记为失败。身份验证错误和未找到错误不会重试，因为它们需要更改配置才能解决。

当已配置的服务器连接失败时，Claude Code会告知Claude哪个服务器失败及其连接错误，包括在未找到匹配工具的`ToolSearch`结果中，因此Claude会在其响应中报告连接失败。需要[工具搜索](#scale-with-mcp-tool-search)，该功能默认启用。在没有工具搜索的配置中，如自定义`ANTHROPIC_BASE_URL`、`ENABLE_TOOL_SEARCH=false`或不支持工具搜索的模型，以及在Amazon Bedrock、Google Cloud的Agent Platform和Microsoft Foundry上，Claude Code不会向Claude报告失败的服务器连接。在v2.1.205之前，Claude Code不会将连接错误传递给Claude，Claude可能会像从未配置过失败服务器的工具那样进行响应。

自v2.1.191版本起，在成功连接后运行的能力发现请求，如`tools/list`、`prompts/list`和`resources/list`，也会以较短退避时间最多重试三次瞬时网络和服务器错误。身份验证错误、4xx响应和请求超时不会重试。

### 使用通道推送消息

MCP 服务器也可以直接将消息推送到您的会话中，以便 Claude 能够对 CI 结果、监控警报或聊天消息等外部事件做出反应。要启用此功能，您的服务器需要声明 `claude/channel` 功能，并在启动时使用 `--channels` 标志选择加入。请参阅 [Channels](/docs/en/channels) 以使用官方支持的通道，或参阅 [Channels reference](/docs/en/channels-reference) 来构建您自己的通道。

<Tip>
  提示：

  * 使用 `-s` 或 `--scope` 标志指定配置的存储位置：
    * `local` (默认)：仅在当前项目中对您可用。旧版本将此作用域称为 `project`
    * `project`：通过 `.mcp.json` 文件与项目中的所有人共享
    * `user`：在所有项目中对您可用。旧版本将此作用域称为 `global`
  * 使用 `-e` 或 `--env` 标志设置环境变量（例如，`-e KEY=value`）
  * `--transport` 和 `--header` 标志也接受 `-t` 和 `-H` 简写形式
  * 使用 `MCP_TIMEOUT` 环境变量配置 MCP 服务器启动超时（例如，`MCP_TIMEOUT=10000 claude` 设置 10 秒超时）
  * 通过在该服务器的 `timeout` 条目中添加以毫秒为单位的 `.mcp.json` 字段来设置特定服务器的工具执行超时，例如 `"timeout": 600000` 表示十分钟。这会仅针对该服务器覆盖 `MCP_TOOL_TIMEOUT` 环境变量
  * Claude Code 在 MCP 工具输出超过 10,000 个 token 时会显示警告，并默认将输出限制为 25,000 个 token。要提高该限制，请设置 `MAX_MCP_OUTPUT_TOKENS` 环境变量（例如，`MAX_MCP_OUTPUT_TOKENS=50000`）；警告阈值是固定的。请参阅 [MCP output limits and warnings](#mcp-output-limits-and-warnings)
  * 使用 `/mcp` 与需要 OAuth 2.0 身份验证的远程服务器进行身份验证
</Tip>

特定服务器的 `timeout` 是每次工具调用的硬性挂钟时间限制，来自服务器的进度通知不会延长此限制。低于 1000 的值将被忽略并回落到 `MCP_TOOL_TIMEOUT`，如果未设置该变量，则回落到其大约 28 小时的默认值。对于 HTTP、SSE 或 [claude.ai connector](/docs/en/mcp#use-mcp-servers-from-claude-ai) 服务器，还有第二个按请求计算的计时器，涵盖从每个请求开始直到服务器响应第一个字节的这段时间。除非您设置了特定服务器的 `timeout` 或 `MCP_TOOL_TIMEOUT`，否则该计时器为 60 秒；将其中任何一个设置为 60 秒或更高会将按请求计算的计时器提升到该值，较低的值不会缩短它，并且未设置 `MCP_TOOL_TIMEOUT` 时的 28 小时默认值永远不会对其产生影响。Stdio 和 WebSocket 服务器没有按请求计算的计时器。{/* min-version: 2.1.162 */}在 v2.1.162 之前，低于 1000 的值会被向下取整为一秒。

至少为 1000 的特定服务器 `timeout` 还作为下文所述空闲超时时间的下限：Claude Code 从来不会在特定服务器 `timeout` 设定的时间之前因空闲而中止该服务器的工具调用。需要 Claude Code v2.1.203 或更高版本。

如果在空闲时间窗口内，对 MCP 服务器的工具调用没有发送任何响应和进度通知，则会报错并中止，而不是等待达到挂钟时间限制。空闲超时需要 Claude Code v2.1.187 或更高版本。{/* min-version: 2.1.203 */}它适用于除 IDE 服务器和 SDK 进程内服务器之外的所有服务器类型。HTTP、SSE、WebSocket 和 [claude.ai connector](#use-mcp-servers-from-claude-ai) 服务器的空闲时间窗口默认为五分钟，而 stdio 服务器默认为 30 分钟。在 v2.1.203 之前，stdio 服务器不受空闲超时限制。

设置以毫秒为单位的 [`CLAUDE_CODE_MCP_TOOL_IDLE_TIMEOUT`](/docs/en/env-vars) 环境变量以更改空闲时间窗口，或将其设置为 `0` 以禁用此检查。

这些超时时间限制的是调用可以运行多长时间，而不一定限制它会阻塞会话多长时间：在 Claude Code v2.1.212 或更高版本上，运行超过两分钟的主对话调用会首先移至后台任务。参见 [Automatic backgrounding of long tool calls](#automatic-backgrounding-of-long-tool-calls)。

### 长工具调用的自动后台处理

主对话中运行超过两分钟仍在执行的 MCP 工具调用会移至后台任务，而不是阻塞会话。Claude 会立即收到任务 ID 并继续工作，结果将在调用结束时作为任务通知到达。自动后台处理需要 Claude Code v2.1.212 或更高版本。

该任务出现在 [`/tasks`](/docs/en/commands#all-commands) 中，你也可以在其中停止它，并且在退出会话后它不会保留。在后台运行调用时，单次调用的限制仍然适用：由每个服务器的 `timeout` 或 [`MCP_TOOL_TIMEOUT`](/docs/en/env-vars) 设置的挂钟时间限制，以及由 [`CLAUDE_CODE_MCP_TOOL_IDLE_TIMEOUT`](/docs/en/env-vars) 设置的空闲超时时间。

以毫秒为单位设置 [`CLAUDE_CODE_MCP_AUTO_BACKGROUND_MS`](/docs/en/env-vars) 环境变量以更改阈值，或者将其设置为 `0` 以关闭自动后台处理。将 `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS` 设置为 `1` 也会将其关闭，同时关闭的还有所有其他后台任务功能。

某些调用永远不会移动到后台：

* 来自 [subagents](/docs/en/sub-agents) 的调用; Claude Code 仅将主对话调用转为后台处理
* 对 IDE 服务器的调用
* 在 [non-interactive mode](/docs/en/headless) 中的调用, 除非 `CLAUDE_AUTO_BACKGROUND_TASKS` 被设置为 `1`, 因为一次性运行可以在结果到达之前结束

等待打开的 [elicitation dialog](#respond-to-mcp-elicitation-requests) 的调用在对话框打开时不会被转为后台处理; 服务器是因为你的输入而阻塞, 而不是由于缓慢, 所以 Claude Code 会推迟该操作直到对话框关闭.

### 插件提供的 MCP 服务器

[插件](/docs/en/plugins) 可以捆绑 MCP 服务器，这些服务器在您启用插件时提供工具和集成功能。插件 MCP 服务器的工作方式与用户配置的服务器完全相同。

**插件 MCP 服务器的工作原理**：

* 插件在插件根目录的 `.mcp.json` 中定义 MCP 服务器，或者以内联方式定义在 `plugin.json` 中
* 当您启用插件时，Claude Code 会自动启动其 MCP 服务器
* Claude Code 与手动配置的 MCP 工具一起提供插件 MCP 工具
* 您可以通过安装或卸载插件来添加和删除插件服务器，而不是使用 `/mcp` 命令。您仍然可以 [关闭已安装的插件服务器](#disable-a-server-without-removing-it) 在 `/mcp` 中，这会停止 Claude Code 连接到它，而无需移除插件

**示例插件 MCP 配置**：

在 `.mcp.json` 的插件根目录下：

```json theme={null}
{
  "mcpServers": {
    "database-tools": {
      "command": "${CLAUDE_PLUGIN_ROOT}/servers/db-server",
      "args": ["--config", "${CLAUDE_PLUGIN_ROOT}/config.json"],
      "env": {
        "DB_URL": "${DB_URL}"
      }
    }
  }
}
```

或者内联在 `plugin.json` 中:

```json theme={null}
{
  "name": "my-plugin",
  "mcpServers": {
    "plugin-api": {
      "command": "${CLAUDE_PLUGIN_ROOT}/servers/api-server",
      "args": ["--port", "8080"]
    }
  }
}
```

**插件 MCP 功能**:

* **自动生命周期**：服务器在以下时间点连接和断开：
  * 在会话启动时，Claude Code 会自动连接已启用插件的服务器
  * 如果在会话期间启用或禁用插件，请运行 `/reload-plugins` 以连接或断开其 MCP 服务器
  * 在 [Web 会话](/docs/en/claude-code-on-the-web) 中，对尚未连接的插件服务器进行 MCP 调用（例如在空闲会话刚刚唤醒时），会按需启动该服务器并等待其连接。 {/* min-version: 2.1.211 */}在 v2.1.211 版本之前，Web 会话中的插件服务器仅在下一条消息开始一轮对话时才会重新连接，因此在空闲会话唤醒后的 MCP 调用在此之前都会失败
* **路径占位符**：`${CLAUDE_PLUGIN_ROOT}` 解析为插件的安装目录，`${CLAUDE_PLUGIN_DATA}` 解析为其 [持久化状态](/docs/en/plugins-reference#persistent-data-directory) 目录，而 `${CLAUDE_PROJECT_DIR}` 解析为稳定的项目根目录。替换适用于：
  * `stdio` 服务器：`command`, `args`, `env`
  * `http`, `sse`, 和 `ws` 服务器：`url`, `headers`, 和 `headersHelper`. {/* min-version: 2.1.195 */}在 v2.1.195 版本之前，`headersHelper` 会将占位符作为字面字符串直接传递
* **用户环境访问**：可访问与手动配置的服务器相同的环境变量
* **多种传输类型**：支持 stdio、SSE、HTTP 和 WebSocket 传输，尽管各服务器的传输支持可能有所不同

**查看插件 MCP 服务器**：

```bash theme={null}
# Within Claude Code, see all MCP servers including plugin ones

/mcp
```

插件服务器会显示在列表中，并带有指示其来自插件的标记。

**插件 MCP 工具名称**：

来自插件内置 MCP 服务器的工具，其可调用名称中同时包含插件名称和服务器键。完整格式为 `mcp__plugin_<plugin-name>_<server-name>__<tool-name>`，其中 `A-Z`、`a-z`、`0-9`、`_` 和 `-` 之外的任何字符都将被替换为 `_`。对于名为 `database-tools` 的插件中内置的 `my-plugin` 服务器，`query` 工具可通过以下方式调用：

```
mcp__plugin_my-plugin_database-tools__query
```

在 [权限规则](/docs/en/permissions)、技能的 `allowed-tools` 列表、[子代理的 `tools` 字段](/docs/en/sub-agents#available-tools) 或 [钩子匹配器](/docs/en/hooks#match-mcp-tools) 中引用该工具时，请使用此全名。针对纯服务器键编写的钩子匹配器（例如 `mcp__database-tools__.*`）对于插件内置的服务器永远不会触发。

服务器本身使用作用域名称 `plugin:<plugin-name>:<server-name>` 进行注册，例如 `plugin:my-plugin:database-tools`。在需要提供已配置服务器名称的地方（例如 [`mcp_tool` 钩子的 `server` 字段](/docs/en/hooks#mcp-tool-hook-fields)）使用该名称。

**插件 MCP 服务器的优势**：

* **打包分发**：工具和服务器封装在一起
* **自动设置**：无需手动配置 MCP
* **团队一致性**：安装插件后，每个人都能获得相同的工具

有关将 MCP 服务器与插件捆绑的详细信息，请参阅 [插件组件参考](/docs/en/plugins-reference#mcp-servers)。

## MCP 安装作用域

MCP 服务器可以在三个作用域进行配置。您选择的作用域将控制该服务器在哪些项目中加载，以及配置是否与您的团队共享。管理员还可以通过 [托管配置](#managed-mcp-configuration) 在企业级部署服务器。

| 作用域                     | 加载范围             | 与团队共享         | 存储位置                   |
| ------------------------- | -------------------- | ------------------------ | --------------------------- |
| [本地](#local-scope)     | 仅当前项目 | 否                       | `~/.claude.json`            |
| [项目](#project-scope) | 仅当前项目 | 是，通过版本控制 | `.mcp.json` 在项目根目录 |
| [用户](#user-scope)       | 您的所有项目    | 否                       | `~/.claude.json`            |

### 本地作用域

本地作用域是默认设置。本地作用域的服务器仅在您添加它的项目中加载，并且对您保持私有。Claude Code 将其存储在该项目路径下的 `~/.claude.json` 中，因此相同的服务器不会出现在您的其他项目中。对于个人开发服务器、实验性配置，或包含您不希望放入版本控制中的凭据的服务器，请使用本地作用域。

<Note>
  MCP 服务器的“本地作用域”概念不同于常规的本地设置。MCP 本地作用域的服务器存储在 `~/.claude.json`（您的主目录）中，而常规的本地设置使用 `.claude/settings.local.json`（在项目目录中）。有关设置文件位置的详细信息，请参阅 [设置](/docs/en/settings#settings-files)。
</Note>

```bash theme={null}
# Add a local-scoped server (default)

claude mcp add --transport http stripe https://mcp.stripe.com

# Explicitly specify local scope

claude mcp add --transport http stripe --scope local https://mcp.stripe.com
```

该命令将服务器写入 `~/.claude.json` 内当前项目的条目中。以下示例显示了从 `/path/to/your/project` 运行它时的结果：

```json theme={null}
{
  "projects": {
    "/path/to/your/project": {
      "mcpServers": {
        "stripe": {
          "type": "http",
          "url": "https://mcp.stripe.com"
        }
      }
    }
  }
}
```

### 项目作用域

项目作用域的服务器通过将配置存储在项目根目录下的 `.mcp.json` 文件中，从而实现团队协作。此文件旨在被检入版本控制，确保所有团队成员都能访问相同的 MCP 工具和服务。当您添加项目作用域的服务器时，Claude Code 会自动创建或更新此文件，并使用适当的配置结构。

```bash theme={null}
# Add a project-scoped server

claude mcp add --transport http paypal --scope project https://mcp.paypal.com/mcp
```

生成的 `.mcp.json` 文件遵循标准化格式：

```json theme={null}
{
  "mcpServers": {
    "shared-server": {
      "command": "/path/to/server",
      "args": [],
      "env": {}
    }
  }
}
```

出于安全原因，Claude Code 在使用来自 `.mcp.json` 文件的项目作用域服务器之前会提示确认。如果您需要重置这些确认选择，请使用 `claude mcp reset-project-choices` 命令。

### 用户作用域

用户作用域的服务器存储在 `~/.claude.json` 中，并提供跨项目的可访问性，使其在您机器上的所有项目中可用，同时对您的用户帐户保持私有。此作用域非常适合个人实用程序服务器、开发工具或您在不同项目中经常使用的服务。

```bash theme={null}
# Add a user server

claude mcp add --transport http hubspot --scope user https://mcp.hubspot.com/anthropic
```

### 作用域层级与优先级

当同一服务器在多个位置定义时，Claude Code 只会连接它一次，并使用来自最高优先级来源的定义。来自该来源的整个服务器条目都会被使用；字段不会跨作用域合并。

1. 本地作用域
2. 项目作用域
3. 用户作用域
4. [插件提供的服务器](/docs/en/plugins)
5. [claude.ai 连接器](#use-mcp-servers-from-claude-ai)

这三个作用域通过名称匹配重复项。插件和连接器通过端点匹配，因此指向与上述服务器相同的 URL 或命令的插件或连接器将被视为重复项。

### 在 `.mcp.json` 中的环境变量展开

Claude Code 支持 `.mcp.json` 文件中的环境变量展开，允许团队共享配置，同时保持对机器特定路径和敏感值（如 API 密钥）的灵活性。

**支持的语法：**

* `${VAR}`: 展开为环境变量 `VAR` 的值
* `${VAR:-default}`: 如果已设置，则展开为 `VAR`，否则使用 `default`

**展开位置：**
环境变量可以在以下位置展开：

* `command`: 服务器可执行文件路径
* `args`: 命令行参数
* `env`: 传递给服务器的环境变量
* `url`: 用于 HTTP 服务器类型
* `headers`: 用于 HTTP 服务器身份验证

**带有变量展开的示例：**

```json theme={null}
{
  "mcpServers": {
    "api-server": {
      "type": "http",
      "url": "${API_BASE_URL:-https://api.example.com}/mcp",
      "headers": {
        "Authorization": "Bearer ${API_KEY}"
      }
    }
  }
}
```

如果引用的环境变量未设置且没有默认值，配置仍会加载：Claude Code 会在 `claude mcp list` 输出中报告该服务器缺少变量的警告，并按原样使用未展开的 `${VAR}` 文本。请设置该变量或添加 `:-default` 后备值，以便服务器以您预期的值启动。

## 实用示例

### 示例：使用 Sentry 监控错误

```bash theme={null}
claude mcp add --transport http sentry https://mcp.sentry.dev/mcp
```

使用您的 Sentry 账号进行身份验证：

```text theme={null}
/mcp
```

然后调试生产环境问题：

```text theme={null}
What are the most common errors in the last 24 hours?
```

```text theme={null}
Show me the stack trace for error ID abc123
```

```text theme={null}
Which deployment introduced these new errors?
```

### 示例：连接到 GitHub 进行代码审查

GitHub 的远程 MCP 服务器使用作为标头传递的 GitHub 个人访问令牌进行身份验证。要获取令牌，请打开您的 [GitHub 令牌设置](https://github.com/settings/personal-access-tokens)，生成一个新的细粒度令牌，并授予其访问您希望 Claude 处理的代码仓库的权限，然后添加该服务器：

```bash theme={null}
claude mcp add --transport http github https://api.githubcopilot.com/mcp/ \
  --header "Authorization: Bearer YOUR_GITHUB_PAT"
```

将 `YOUR_GITHUB_PAT` 替换为您的个人访问令牌。`claude mcp add` 命令会在不验证凭据的情况下保存配置，因此此处接受占位符值，但稍后服务器将无法连接。要验证连接，请运行 `/mcp` 并检查服务器是否显示 `connected`。凭据错误的服务器将显示 `failed`。

然后开始使用 GitHub：

```text theme={null}
Review PR #456 and suggest improvements
```

```text theme={null}
Create a new issue for the bug we just found
```

```text theme={null}
Show me all open PRs assigned to me
```

### 示例：查询您的 PostgreSQL 数据库

```bash theme={null}
claude mcp add --transport stdio db -- npx -y @bytebase/dbhub \
  --dsn "postgresql://readonly:pass@prod.db.com:5432/analytics"
```

然后以自然语言查询您的数据库：

```text theme={null}
What's our total revenue this month?
```

```text theme={null}
Show me the schema for the orders table
```

```text theme={null}
Find customers who haven't made a purchase in 90 days
```

## 与远程 MCP 服务器进行身份验证

许多基于云的 MCP 服务器需要身份验证。Claude Code 支持 OAuth 2.0 以确保安全连接。

当服务器以 Claude Code 或 `401 Unauthorized` 响应时，`403 Forbidden` 会将远程服务器标记为需要身份验证。对于您尚未登录的服务器，任何一种状态码都会在 `/mcp` 中对其进行标记，以便您可以完成 OAuth 流程。

当对您已登录的 OAuth 服务器的请求返回 `401 Unauthorized` 时，Claude Code 会刷新存储的令牌，重新连接，并重试该请求一次。仅当该重试也失败时，它才会在 `/mcp` 中标记该服务器。在 v2.1.206 之前，如果由于网络错误等暂时性原因导致令牌刷新失败，即使在刷新令牌仍然有效的情况下，也会将 OAuth 服务器标记为在会话的剩余时间内需要身份验证。

从 v2.1.195 开始，当由于服务器拒绝存储的刷新令牌而导致令牌刷新失败时，Claude Code 会立即显示指向 `/mcp` 的通知。那里连接的服务器菜单提供了“重新进行身份验证”选项，因此您可以在下一次工具调用失败之前再次登录。

返回指向其授权服务器的 `WWW-Authenticate` 标头的自定义服务器，将获得与任何其他远程服务器相同的自动发现功能。

当一个或多个已配置的服务器需要身份验证时，Claude Code 也会显示一条启动通知，因此您无需打开 `/mcp` 来发现哪些服务器需要登录。该通知需要 Claude Code v2.1.193 或更高版本。{/* min-version: 2.1.218 */}它仅计算您可以从 Claude Code 登录的服务器。在 v2.1.218 之前，它还会计算在 claude.ai 中未连接的 [claude.ai 连接器](#use-mcp-servers-from-claude-ai)，而这些连接器只能从 claude.ai 设置中进行连接。

在非交互模式下，没有 `/mcp` 面板，因此 Claude Code 无法为您运行 OAuth 流程。从 v2.1.196 开始，当已配置的服务器在 `claude -p` 或 Agent SDK 运行期间需要身份验证，并且启用了 [工具搜索](#scale-with-mcp-tool-search)（这是默认设置）时，Claude Code 会告知 Claude，在您授权之前该服务器的工具不可用。然后，Claude 可以说出需要登录的服务器名称，而不是像未配置该服务器那样进行响应。请通过 `/mcp` 或 `claude mcp login <name>` 的交互式会话完成登录。

如果您为服务器配置了 `headers.Authorization` 而服务器拒绝了该标头，Claude Code 会将连接报告为失败，而不是回退到 OAuth。请检查令牌对于该 MCP 端点是否有效，或者移除该标头以使用 OAuth 流程。

<Steps>
  <Step title="添加需要身份验证的服务器">
    例如：

    ```bash theme={null}
    claude mcp add --transport http sentry https://mcp.sentry.dev/mcp
    ```
  </Step>

  <Step title="在 Claude Code 中使用 /mcp 命令">
    在 Claude Code 中，使用以下命令：

    ```text theme={null}
    /mcp
    ```

    然后在浏览器中按照步骤登录。
  </Step>
</Steps>

<Tip>
  提示：

  * 身份验证令牌将被安全存储并自动刷新
  * 在 `/mcp` 菜单中使用“清除身份验证”以撤销访问权限
  * 如果您的浏览器没有自动打开，请复制提供的 URL 并手动打开
  * 如果浏览器在身份验证后重定向失败并出现连接错误，请将浏览器地址栏中的完整回调 URL 粘贴到 Claude Code 中出现的 URL 提示中
  * OAuth 身份验证适用于 HTTP 服务器
</Tip>

### 从命令行进行身份验证

从 v2.1.186 版本开始，`claude mcp login <name>` 会直接在您的 shell 中运行已配置服务器的 OAuth 流程，因此您无需在会话内打开 `/mcp` 面板。

```bash theme={null}
claude mcp login sentry
```

若要在之后清除存储的凭据，请运行 `claude mcp logout <name>`。

从 v2.1.191 版本开始，该命令会检测本地何时没有可用的浏览器（例如在 SSH 会话期间或在没有显示服务器的 Linux 上），并打印授权 URL，而不是尝试打开浏览器。在本地计算机上打开该 URL，然后将浏览器地址栏中的完整重定向 URL 粘贴回提示符处。该命令在粘贴步骤中需要一个交互式终端，因此请使用 `ssh -t` 进行连接。传入 `--no-browser` 可强制显示 URL 提示，即使在检测到本地浏览器时也是如此。

```bash theme={null}
claude mcp login sentry --no-browser
```

### 使用固定的 OAuth 回调端口

某些 MCP 服务器需要预先注册特定的重定向 URI。默认情况下，Claude Code 会为 OAuth 回调选择一个随机可用端口。使用 `--callback-port` 来固定端口，使其与格式为 `http://localhost:PORT/callback` 的预注册重定向 URI 相匹配。

您可以单独使用 `--callback-port`（通过动态客户端注册），也可以将其与 `--client-id`（带有预配置的凭据）结合使用。

```bash theme={null}
# Fixed callback port with dynamic client registration

claude mcp add --transport http \
  --callback-port 8080 \
  my-server https://mcp.example.com/mcp
```

### 使用预配置的 OAuth 凭据

某些 MCP 服务器不支持通过动态客户端注册进行自动 OAuth 设置。如果你看到类似"不兼容的认证服务器：不支持动态客户端注册"的错误，说明该服务器需要预配置的凭据。Claude Code 也支持使用客户端 ID 元数据文档（CIMD）而非动态客户端注册的服务器，并会自动发现这些服务器。如果自动发现失败，请先通过服务器的开发者门户注册一个 OAuth 应用，然后在添加服务器时提供凭据。

<Steps>
  <Step title="在服务器上注册 OAuth 应用">
    通过服务器的开发者门户创建应用，并记下你的客户端 ID 和客户端密钥。

    许多服务器还需要重定向 URI。如果需要，选择一个端口并以 `http://localhost:PORT/callback` 格式注册重定向 URI。在下一步中使用相同的端口配合 `--callback-port`。
  </Step>

  <Step title="使用你的凭据添加服务器">
    选择以下方法之一。用于 `--callback-port` 的端口可以是任何可用端口。它需要与你上一步注册的重定向 URI 匹配。

    <Tabs>
      <Tab title="claude mcp add">
        使用 `--client-id` 传入你的应用客户端 ID。`--client-secret` 标志会通过掩码输入提示输入密钥：

        ```bash theme={null}
        claude mcp add --transport http \
          --client-id your-client-id --client-secret --callback-port 8080 \
          my-server https://mcp.example.com/mcp
        ```
      </Tab>

      <Tab title="claude mcp add-json">
        在 JSON 配置中包含 `oauth` 对象，并将 `--client-secret` 作为单独的标志传入：

        ```bash theme={null}
        claude mcp add-json my-server \
          '{"type":"http","url":"https://mcp.example.com/mcp","oauth":{"clientId":"your-client-id","callbackPort":8080}}' \
          --client-secret
        ```
      </Tab>

      <Tab title="claude mcp add-json（仅回调端口）">
        使用 `--callback-port` 而不提供客户端 ID，以在使用动态客户端注册时固定端口：

        ```bash theme={null}
        claude mcp add-json my-server \
          '{"type":"http","url":"https://mcp.example.com/mcp","oauth":{"callbackPort":8080}}'
        ```
      </Tab>

      <Tab title="CI / 环境变量">
        通过环境变量设置密钥以跳过交互式提示：

        ```bash theme={null}
        MCP_CLIENT_SECRET=your-secret claude mcp add --transport http \
          --client-id your-client-id --client-secret --callback-port 8080 \
          my-server https://mcp.example.com/mcp
        ```
      </Tab>
    </Tabs>
  </Step>

  <Step title="在 Claude Code 中认证">
    在 `/mcp` 中运行 Claude Code 并按照浏览器登录流程操作。
  </Step>
</Steps>

<Tip>
  提示：

  * 客户端密钥安全地存储在你的系统钥匙串（macOS）或凭据文件中，而不是你的配置中
  * 如果服务器使用没有密钥的公共 OAuth 客户端，仅使用 `--client-id` 而不需要 `--client-secret`
  * `--callback-port` 可以与 `--client-id` 一起使用或不一起使用
  * 这些标志仅适用于 HTTP 和 SSE 传输。它们对 stdio 服务器没有影响
  * 使用 `claude mcp get <name>` 验证服务器是否已配置 OAuth 凭据
</Tip>

### 覆盖 OAuth 元数据发现

将 Claude Code 指向特定的 OAuth 授权服务器元数据 URL，以绕过默认的发现链。当 MCP 服务器的标准端点出错，或者当您想通过内部代理路由发现时，请设置 `authServerMetadataUrl`。默认情况下，Claude Code 首先检查 `/.well-known/oauth-protected-resource` 处的 RFC 9728 保护资源元数据，然后回退到 `/.well-known/oauth-authorization-server` 处的 RFC 8414 授权服务器元数据。

在 `authServerMetadataUrl` 中服务器配置的 `oauth` 对象内设置 `.mcp.json`：

```json theme={null}
{
  "mcpServers": {
    "my-server": {
      "type": "http",
      "url": "https://mcp.example.com/mcp",
      "oauth": {
        "authServerMetadataUrl": "https://auth.example.com/.well-known/openid-configuration"
      }
    }
  }
}
```

该 URL 必须使用 `https://`。元数据 URL 的 `scopes_supported` 会覆盖上游服务器通告的范围。

### 限制 OAuth 范围

设置 `oauth.scopes` 以固定 Claude Code 在授权流期间请求的范围。当上游授权服务器通告的范围超出了您想要授予的范围时，这是将 MCP 服务器限制为安全团队批准的子集的受支持方法。该值是一个以空格分隔的单一字符串，与 RFC 6749 §3.3 中的 `scope` 参数格式相匹配。

```json theme={null}
{
  "mcpServers": {
    "slack": {
      "type": "http",
      "url": "https://mcp.slack.com/mcp",
      "oauth": {
        "scopes": "channels:read chat:write search:read"
      }
    }
  }
}
```

`oauth.scopes` 优先于 `authServerMetadataUrl` 和服务器在 `/.well-known` 处发现范围。将其留空（不设置）可让 MCP 服务器确定请求的范围集。

从 v2.1.196 开始，当未设置 `oauth.scopes` 时，Claude Code 会请求由服务器的 `WWW-Authenticate` 标头或其受保护资源元数据提供的范围，并在两者均未提供时不发送 `scope` 参数。它不再从自动发现的授权服务器元数据中请求完整的 `scopes_supported` 目录。请求该目录会导致通告仅限管理员或模板范围的标识提供程序以 `invalid_scope` 错误拒绝授权请求。从配置的 `authServerMetadataUrl` 获取的元数据仍会提供其 `scopes_supported` 作为请求的范围。

如果授权服务器在 `offline_access` 中通告了 `scopes_supported`，Claude Code 会将其附加到固定的范围中，以便无需重新进行浏览器登录即可刷新访问令牌。

如果服务器稍后在工具调用时返回 403 `insufficient_scope`，Claude Code 会使用相同的固定范围重新进行身份验证。当您需要的工具需要固定集合之外的范围时，请扩大 `oauth.scopes`。

### 使用动态标头进行自定义身份验证

如果你的 MCP 服务器使用 OAuth 以外的身份验证方案（例如 Kerberos、短期令牌或内部 SSO），请在连接时使用 `headersHelper` 生成请求标头。Claude Code 会运行该命令，并将其输出合并到连接标头中。

```json theme={null}
{
  "mcpServers": {
    "internal-api": {
      "type": "http",
      "url": "https://mcp.internal.example.com",
      "headersHelper": "/opt/bin/get-mcp-auth-headers.sh"
    }
  }
}
```

该命令也可以是内联的：

```json theme={null}
{
  "mcpServers": {
    "internal-api": {
      "type": "http",
      "url": "https://mcp.internal.example.com",
      "headersHelper": "echo '{\"Authorization\": \"Bearer '\"$(get-token)\"'\"}'"
    }
  }
}
```

**要求：**

* 该命令必须将一个由字符串键值对组成的 JSON 对象写入标准输出
* 该命令在 shell 中运行，具有 10 秒超时限制，从会话的当前工作目录执行。请为脚本使用绝对路径或 `PATH` 上的命令
* 动态标头会覆盖任何同名的静态 `headers`

该辅助程序在每次连接（包括会话开始和重新连接）时都会重新运行。没有缓存机制，因此你的脚本需要自行处理任何令牌重用。

自 v2.1.193 起，如果工具调用返回 `401 Unauthorized` 或 `403 Forbidden`，Claude Code 会自动重新运行该辅助程序，使用新的标头重新连接，并重试该调用一次。只有在重试也失败的情况下，Claude Code 才会在 `/mcp` 中将该服务器标记为需要身份验证。

Claude Code 在执行辅助程序时会设置以下环境变量：

| 变量                      | 值                                                                                                        |
| :---------------------------- | :----------------------------------------------------------------------------------------------------------- |
| `CLAUDE_CODE_MCP_SERVER_NAME` | MCP 服务器的名称                                                                                   |
| `CLAUDE_CODE_MCP_SERVER_URL`  | MCP 服务器的 URL                                                                                    |
| `CLAUDE_PLUGIN_ROOT`          | 插件的根目录。仅当 [plugin](/docs/en/plugins-reference#mcp-servers) 提供服务器时设置 |

使用这些来编写一个服务于多个 MCP 服务器的单一辅助脚本。

对于插件提供的服务器，该辅助脚本也会在运行时将其工作目录设置为插件根目录，因此相对 `headersHelper` 路径会在插件目录内解析，而不是基于会话的工作目录。需要 Claude Code v2.1.195 或更高版本。

插件提供的 `headersHelper` 无法引用该插件的 [`${user_config.*}`](/docs/en/plugins-reference#user-configuration) 值，因为该命令通过 shell 运行。Claude Code 会报告服务器配置错误并提示 [error](/docs/en/errors#plugin-command-references-user-config)，并且不会替换该值。请改为将 `${user_config.KEY}` 放在服务器的 `headers` 字段中（该字段不会被 shell 解析），或者让辅助脚本从其自身环境或配置文件中读取该值。在 v2.1.207 版本之前，`headersHelper` 会替换 `${user_config.*}` 的值。

<Note>
  `headersHelper` 会执行任意 shell 命令。当在项目或本地作用域中定义时，它只会在您接受工作区信任对话框后才会运行。
</Note>

## 从 JSON 配置添加 MCP 服务器

如果您有 MCP 服务器的 JSON 配置，您可以直接添加它：

<Steps>
  <Step title="从 JSON 添加 MCP 服务器">
    ```bash theme={null}
    # 基本语法
    claude mcp add-json <name> '<json>'

    # 示例：使用 JSON 配置添加 HTTP 服务器
    claude mcp add-json weather-api '{"type":"http","url":"https://api.weather.com/mcp","headers":{"Authorization":"Bearer token"}}'

    # 示例：使用 JSON 配置添加 stdio 服务器
    claude mcp add-json local-weather '{"type":"stdio","command":"/path/to/weather-cli","args":["--api-key","abc123"],"env":{"CACHE_DIR":"/tmp"}}'

    # 示例：添加带有预配置 OAuth 凭据的 HTTP 服务器
    claude mcp add-json my-server '{"type":"http","url":"https://mcp.example.com/mcp","oauth":{"clientId":"your-client-id","callbackPort":8080}}' --client-secret
    ```
  </Step>

  <Step title="验证服务器是否已添加">
    ```bash theme={null}
    claude mcp get weather-api
    ```
  </Step>
</Steps>

<Tip>
  提示：

  * 确保在您的 shell 中正确转义了 JSON
  * JSON 必须符合 MCP 服务器配置模式
  * 您可以使用 `--scope user` 将服务器添加到您的用户配置，而不是特定于项目的配置
</Tip>

## 从 Claude Desktop 导入 MCP 服务器

如果您已经在 Claude Desktop 中配置了 MCP 服务器，您可以导入它们：

<Steps>
  <Step title="从 Claude Desktop 导入服务器">
    ```bash theme={null}
    # 基本语法
    claude mcp add-from-claude-desktop
    ```
  </Step>

  <Step title="选择要导入的服务器">
    运行命令后，您将看到一个交互式对话框，允许您选择要导入的服务器。
  </Step>

  <Step title="验证服务器是否已导入">
    ```bash theme={null}
    claude mcp list
    ```
  </Step>
</Steps>

通过 `claude mcp` 命令添加的服务器名称只能包含字母、数字、连字符和下划线。Claude Desktop 并未应用此限制，因此名称中包含任何其他字符（例如空格）的 Claude Desktop 服务器无法被导入。导入操作会报告其拒绝的每个名称，并且仍会导入您选择的其他服务器。在 v2.1.205 之前，第一个无效名称会导致导入停止，并且所有选定的服务器都不会被添加。

<Tip>
  提示：

  * 此功能仅在 macOS 和 Windows Subsystem for Linux (WSL) 上有效
  * 它会从这些平台上 Claude Desktop 配置文件的标准位置读取文件
  * 使用 `--scope user` 标志将服务器添加到您的用户配置中
  * 当名称仅包含字母、数字、连字符和下划线时，导入的服务器会保留与 Claude Desktop 中相同的名称。Claude Code 会报告名称包含任何其他字符的服务器并跳过它
  * 如果已存在同名服务器，它们将获得一个数字后缀（例如，`server_1`）
</Tip>

## 使用来自 claude.ai 的 MCP 服务器

如果你已登录 Claude Code 并使用 [claude.ai](https://claude.ai) 账户，你在 claude.ai 中添加的 MCP 服务器（称为 [connectors](https://claude.com/docs/connectors)）将在 Claude Code 中自动可用：

<Steps>
  <Step title="在 claude.ai 中配置 MCP 服务器">
    在 [claude.ai/customize/connectors](https://claude.ai/customize/connectors) 添加服务器。在团队版和企业版中，只有管理员可以添加服务器。
  </Step>

  <Step title="验证 MCP 服务器">
    在 claude.ai 中完成任何所需的身份验证步骤。
  </Step>

  <Step title="在 Claude Code 中查看和管理服务器">
    在 Claude Code 中，使用命令：

    ```text theme={null}
    /mcp
    ```

    来自 claude.ai 的服务器会出现在列表中，并带有指示它们来自 claude.ai 的标记。
  </Step>
</Steps>

从 v2.1.161 版本开始，你从未登录过的连接器会被折叠到 claude.ai 部分末尾的 `Show unused connectors` 行之后，这样组织提供的列表就不会填满面板。选择该行即可展开它们。你之前登录过的连接器即使在当前需要重新验证时也会保持可见。

仅当你活动的 [authentication method](/docs/en/authentication#authentication-precedence) 是 claude.ai 订阅登录时，才会获取来自 claude.ai 的连接器。当 `ANTHROPIC_API_KEY`、`ANTHROPIC_AUTH_TOKEN`、`apiKeyHelper` 或第三方提供商（如 Amazon Bedrock 或 Google Cloud 的 Agent Platform）处于活动状态时，即使你之前运行过 `/login`，也不会加载它们。当 `CLAUDE_CODE_OAUTH_TOKEN` 持有来自 [`claude setup-token`](/docs/en/authentication#generate-a-long-lived-token) 的令牌时，也不会加载它们，因为该令牌只能发出模型请求。

如果 `/mcp` 未列出你添加的连接器，请运行 `/status` 以确认当前活动的身份验证方法，取消设置该环境变量或删除 `apiKeyHelper` 设置，然后运行 `/login` 以选择你的 claude.ai 账户。

你在 Claude Code 中添加的服务器比指向相同 URL 的 claude.ai 连接器具有 [precedence](#scope-hierarchy-and-precedence)。发生这种情况时，`/mcp` 会将该连接器列为隐藏状态，并显示如果你想要使用该连接器该如何删除重复项。

一些 Anthropic 托管的连接器（例如 Microsoft 365、Gmail 和 Google Calendar）不支持从 Claude Code 进行本地 OAuth，因为上游身份提供商仅接受 claude.ai 注册的重定向 URL。从 v2.1.162 版本开始，在 `/mcp` 中对这些主机之一进行身份验证会显示一条消息，引导你改为在 claude.ai 的“设置 → 连接器”中进行连接。在那里连接后，该连接器将自动出现在 Claude Code 中。

### 连接器工具上的组织控制

你的组织可以在 [claude.ai connectors](https://claude.com/docs/connectors) 上设置逐工具控制。Claude Code 在启动时读取这些设置并在本地强制执行它们。运行 `/mcp` 以查看连接器上的每个工具应用了哪个设置。

* **设置为 `ask` 的工具**：Claude Code 会在每次调用时提示，原因为 `Your organization requires approval for this tool`。即使在 `acceptEdits`、`auto` 和 `bypassPermissions` [permission modes](/docs/en/permissions#permission-modes) 中也会出现该提示，并且绝不提供记住选择的选项。与该工具匹配的 [Allow rules](/docs/en/permissions) 也不会跳过提示。在从不提示的 `dontAsk` 模式下，Claude Code 会改为拒绝调用。
* **设置为 `blocked` 的工具**：Claude Code 会在 Claude 看到该工具之前将其过滤掉，因此它永远不会出现在工具列表中。

强制执行这些控制需要 Claude Code v2.1.129 或更高版本。早期版本会忽略这些设置并应用标准权限流程。

### 禁用 claude.ai 连接器

要在 Claude Code 中禁用 claude.ai MCP 服务器，请在任何设置范围内将 [`disableClaudeAiConnectors`](/docs/en/settings#available-settings) 设置为 `true`：

```json theme={null}
{
  "disableClaudeAiConnectors": true
}
```

此设置使用 any-source-true（任意来源为真）语义：任何设置来源中的 `true` 都具有优先权。已签入的项目 `.claude/settings.json` 可以使存储库退出云连接器，但项目级别的 `false` 无法重新启用被用户或策略级别的 `true` 禁用的连接器。通过 `--mcp-config` 显式传递的服务器不受影响。

您也可以将 `ENABLE_CLAUDEAI_MCP_SERVERS` 环境变量设置为 `false`，这对当前 shell 会话具有相同的效果：

```bash theme={null}
ENABLE_CLAUDEAI_MCP_SERVERS=false claude
```

要阻止单个 claude.ai 连接器而不是全部，可以按名称或 URL 模式将它们添加到 [`deniedMcpServers`](/docs/en/managed-mcp) 中。例如，`serverName` 条目为 `"claude.ai Slack"` 时将阻止 Slack 连接器。要仅为当前项目开启或关闭连接器，请使用 `/mcp` 面板。

<Note>
  这些客户端设置管理本地 Claude Code 会话。在 [Claude Code 在网页端](/docs/en/claude-code-on-the-web) 会话中，claude.ai 连接器由远程主机提供并作为显式的 `--mcp-config` 条目到达，因此 `disableClaudeAiConnectors` 在那里不适用。连接器 URL 也会通过会话代理进行重写，因此针对供应商 URL 的 `deniedMcpServers` `serverUrl` 模式将无法匹配。请从您的 claude.ai 组织设置中管理云会话可以使用的连接器。
</Note>

## 将 Claude Code 用作 MCP 服务器

您可以将 Claude Code 本身用作其他应用程序可以连接的 MCP 服务器：

```bash theme={null}
# Start Claude as a stdio MCP server

claude mcp serve
```

您可以在 Claude Desktop 中使用此功能，方法是将此配置添加到 claude\_desktop\_config.json 中：

```json theme={null}
{
  "mcpServers": {
    "claude-code": {
      "type": "stdio",
      "command": "claude",
      "args": ["mcp", "serve"],
      "env": {}
    }
  }
}
```

<Warning>
  **配置可执行文件路径**：`command` 字段必须引用 Claude Code 可执行文件。如果 `claude` 命令不在您系统的 PATH 中，您将需要指定该可执行文件的完整路径。

  要查找完整路径：

  ```bash theme={null}
  which claude
  ```

  然后在您的配置中使用完整路径：

  ```json theme={null}
  {
    "mcpServers": {
      "claude-code": {
        "type": "stdio",
        "command": "/full/path/to/claude",
        "args": ["mcp", "serve"],
        "env": {}
      }
    }
  }
  ```

  如果没有正确的可执行文件路径，您将会遇到类似 `spawn claude ENOENT` 的错误。
</Warning>

<Tip>
  提示：

  * 该服务器提供对 Claude 工具（如 View、Edit、LS 等）的访问。
  * 在 Claude Desktop 中，尝试让 Claude 读取目录中的文件、进行编辑等。
  * 此 MCP 服务器仅将 Claude Code 的工具公开给您的 MCP 客户端，因此您自己的客户端负责实现对各个工具调用的用户确认。
</Tip>

## MCP 输出限制与警告

当 MCP 工具产生大量输出时，Claude Code 会帮助管理 token 用量，以防止过多的内容占据您的对话上下文：

* **输出警告阈值**：当任何 MCP 工具的输出超过 10,000 个 token 时，Claude Code 会显示警告
* **可配置限制**：您可以使用 `MAX_MCP_OUTPUT_TOKENS` 环境变量来调整允许的最大 MCP 输出 token 数
* **默认限制**：默认最大值为 25,000 个 token
* **作用范围**：该环境变量适用于未声明自身限制的工具。设置了 [`anthropic/maxResultSizeChars`](#raise-the-limit-for-a-specific-tool) 的工具会对文本内容使用该值，无论 `MAX_MCP_OUTPUT_TOKENS` 设置为多少。返回图像数据的工具仍受 `MAX_MCP_OUTPUT_TOKENS` 约束

要提高产生大量输出的工具的限制：

```bash theme={null}
export MAX_MCP_OUTPUT_TOKENS=50000
claude
```

这在处理以下 MCP 服务器时特别有用：

* 查询大型数据集或数据库
* 生成详细的报告或文档
* 处理大量日志文件或调试信息

### 提高特定工具的限制

如果您正在构建 MCP 服务器，可以通过在工具的 `_meta["anthropic/maxResultSizeChars"]` 响应条目中设置 `tools/list`，来允许单个工具返回超过默认持久化到磁盘阈值的结果。Claude Code 会将该工具的阈值提高到所标注的值，上限为 500,000 个字符。

这对于返回本质上较大但必要输出的工具非常有用，例如数据库架构或完整的文件树。如果没有该标注，超过默认阈值的结果会被持久化到磁盘，并在对话中替换为文件引用。

```json theme={null}
{
  "name": "get_schema",
  "description": "Returns the full database schema",
  "_meta": {
    "anthropic/maxResultSizeChars": 200000
  }
}
```

该标注独立于 `MAX_MCP_OUTPUT_TOKENS` 应用于文本内容，因此用户无需为声明了该标注的工具提高环境变量的值。返回图像数据的工具仍受 token 限制约束。

<Warning>
  如果您经常在无法控制的特定 MCP 服务器上遇到输出警告，可以考虑提高 `MAX_MCP_OUTPUT_TOKENS` 限制。您也可以要求服务器作者添加 `anthropic/maxResultSizeChars` 标注或对其响应进行分页。该标注对返回图像内容的工具无效；对于这些工具，提高 `MAX_MCP_OUTPUT_TOKENS` 是唯一的选择。
</Warning>

## 带有根级组合器的工具输入模式

一些 MCP 服务器将工具的输入模式声明为 JSON Schema 联合类型，在模式顶层使用 `anyOf`、`oneOf` 或 `allOf`。Claude API 不接受在模式根节点使用这些关键字。但可以接受嵌套在 `properties` 内部的组合器，Claude Code 会将其原样发送。

从 Claude Code v2.1.195 开始，带有根级组合器的工具仍然可用。在将工具发送到 API 之前，Claude Code 会将模式展平为单个对象，并在工具描述前添加一句话，告知 Claude 哪些参数组是关联的：

* `allOf`：来自每个分支的属性会被合并，每个分支的 `required` 列表仍然适用
* `anyOf` 和 `oneOf`：来自每个分支的属性会被合并，每个分支的 `required` 列表会在工具描述中说明，而不是由模式强制执行

您的服务器会收到 Claude 选择的参数，因此请继续在服务器端验证参数组合。

当 Claude Code 无法生成 API 可接受的模式时，或者在未接收到启用该重写的远程配置的部署环境中（例如离线机器），它会跳过该工具，在服务器日志中记录原因，并保留该服务器的其他可用工具。v2.1.195 之前的版本会跳过所有输入模式中包含根级 `anyOf`、`oneOf` 或 `allOf` 的工具。

## 要求特定工具的批准

如果您正在构建 MCP 服务器，可以通过在工具的 `_meta["anthropic/requiresUserInteraction"]` 响应条目中将 `true` 设置为 `tools/list`，将工具标记为每次调用都需要明确批准。该值必须是 JSON 布尔值 `true`；任何其他值都将被忽略。

Claude Code 在每次调用时都会显示该工具的权限提示，即使在 `acceptEdits`、`auto` 和 `bypassPermissions` [权限模式](/docs/en/permissions#permission-modes) 中也是如此，并且不为其提供“不再询问”选项。与该工具匹配的 [允许规则](/docs/en/permissions#permission-rule-syntax) 也不会跳过提示。在从不提示的 `dontAsk` 模式中，Claude Code 会拒绝调用。

提示必须触达真人。在带有 [`--permission-prompt-tool`](/docs/en/cli-reference#cli-flags) 的非交互模式下，来自提示工具的针对已标记工具的 `allow` 结果将转换为拒绝，并附带消息 `MCP tool requires user interaction; not supported via --permission-prompt-tool`。Agent SDK 的 [`canUseTool` 回调](/docs/en/agent-sdk/permissions) 确实会接收这些调用并可以批准它们，因为您的 SDK 应用程序理应将其展示给用户。

将此用于那些权限提示本身即是目的的工具，例如同意或访问授权步骤，在这些步骤中，自动批准将意味着没有任何人类实际同意过。同一服务器中的其他工具保持其正常的权限行为。

以下 `tools/list` 条目将一个工具标记为始终需要批准。

```json theme={null}
{
  "name": "grant_access",
  "description": "Requests access to a protected resource",
  "_meta": {
    "anthropic/requiresUserInteraction": true
  }
}
```

`anthropic/requiresUserInteraction` 注解需要 Claude Code v2.1.199 或更高版本。早期版本会忽略它并应用标准权限流程。

某些界面（例如 [Remote Control](/docs/en/remote-control) 以及基于 [Agent SDK](/docs/en/agent-sdk/overview) 构建的应用程序）通常允许您通过一键操作批准工具调用。对于使用此注解标记的工具，Claude Code 会保留一键操作，转而显示该工具的完整权限提示，因此批准仍然来自回答提示的人，而不是一键点击。

Claude Code 对于只有终端对话框才能完整呈现的任何权限请求（例如带有安全警告或远程界面无法显示的始终允许选项的请求），也会以相同方式保留一键批准。您可以在终端对话框中回答该请求，而不是从 Remote Control 中回答。需要 Claude Code v2.1.214 或更高版本。

## 响应 MCP elicitation 请求

MCP 服务器可以使用 elicitation 在任务执行期间向您请求结构化输入。当服务器需要它自己无法获取的信息时，Claude Code 会显示一个交互式对话框，并将您的响应传回服务器。您这边不需要任何配置：当服务器请求时，elicitation 对话框会自动出现。

服务器可以通过两种方式请求输入：

* **表单模式**：Claude Code 显示一个带有由服务器定义的表单字段的对话框（例如，用户名和密码提示）。填写字段并提交。
* **URL 模式**：Claude Code 打开浏览器 URL 进行身份验证或批准。在浏览器中完成流程，然后在 CLI 中确认。

要在不显示对话框的情况下自动响应 elicitation 请求，请使用 [`Elicitation` 钩子](/docs/en/hooks#elicitation)。

如果您正在构建使用 elicitation 的 MCP 服务器，请参阅 [MCP elicitation 规范](https://modelcontextprotocol.io/docs/learn/client-concepts#elicitation) 以获取协议详细信息和架构示例。

## 使用 MCP 资源

MCP 服务器可以公开资源，您可以使用 @ 提及来引用这些资源，这与引用文件的方式类似。

### 引用 MCP 资源

<Steps>
  <Step title="列出可用资源">
    在你的提示词中输入 `@`，查看来自所有已连接 MCP 服务器的可用资源。资源将与文件一起出现在自动补全菜单中。
  </Step>

  <Step title="引用特定资源">
    使用格式 `@server:protocol://resource/path` 来引用资源：

    ```text theme={null}
    你能分析 @github:issue://123 并提出修复建议吗？
    ```

    ```text theme={null}
    请查阅位于 @docs:file://api/authentication 的 API 文档
    ```
  </Step>

  <Step title="多个资源引用">
    你可以在单个提示词中引用多个资源：

    ```text theme={null}
    将 @postgres:schema://users 与 @docs:file://database/user-model 进行比较
    ```
  </Step>
</Steps>

<Tip>
  提示：

  * 资源在被引用时会自动获取并作为附件包含
  * 资源路径在 @ 提及的自动补全中支持模糊搜索
  * Claude Code 会在服务器支持时自动提供列出和读取 MCP 资源的工具
  * 资源可以包含 MCP 服务器提供的任何类型的内容（文本、JSON、结构化数据等）
</Tip>

## 通过 MCP 工具搜索进行扩展

工具搜索通过将工具定义推迟到 Claude 需要它们时加载，从而保持较低的 MCP 上下文使用量。会话开始时仅加载工具名称和服务器指令，因此添加更多 MCP 服务器对你的上下文窗口的影响微乎其微。Claude Code 没有强加固定的单服务器工具上限；实际的限制是你的上下文窗口预算。

### 工作原理

默认情况下，工具搜索处于启用状态。MCP 工具会被推迟加载，而不是预先加载到上下文中，当任务需要时，Claude 会使用搜索工具来发现相关的工具。只有 Claude 实际使用的工具才会进入上下文。从你的角度来看，MCP 工具的工作方式与以前完全一样。

如果你更喜欢基于阈值的加载，请设置 `ENABLE_TOOL_SEARCH=auto`，以便在它们适合上下文窗口的 10% 范围内时预先加载 schema，而仅推迟溢出的部分。有关所有选项，请参见 [配置工具搜索](#configure-tool-search)。

### 写给 MCP 服务器作者

如果你正在构建 MCP 服务器，那么在启用工具搜索后，服务器指令字段会变得更有用。服务器指令可帮助 Claude 了解何时搜索你的工具，这与 [skills](/docs/en/skills) 的工作方式类似。

添加清晰、具有描述性的服务器指令来解释：

* 你的工具处理哪类任务
* Claude 何时应该搜索你的工具
* 你的服务器提供的关键功能

Claude Code 会分别将工具描述和服务器指令截断至各 2KB。请保持它们简洁以避免被截断，并将关键细节放在开头。

### 配置工具搜索

工具搜索默认启用：MCP 工具会被延迟并按需发现。Claude Code 在 Google Cloud 的 Agent Platform 上默认禁用它。当 `ANTHROPIC_BASE_URL` 指向非第一方主机时，它也会被禁用，因为大多数代理不会转发 `tool_reference` 块。显式设置 `ENABLE_TOOL_SEARCH` 可覆盖任一回退。

设置 [`CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS`](/docs/en/env-vars) 会保持工具搜索关闭，并且 `ENABLE_TOOL_SEARCH` 无法覆盖它。该变量会移除 `defer_loading` 工具定义和 `tool_reference` 内容块所需的 beta 标头。

工具搜索需要支持 `tool_reference` 块的模型：Claude Sonnet 4.5、Claude Haiku 4.5、Claude Opus 4.5 及更高版本的模型。有关当前列表，请参见 [API 文档中的模型兼容性](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool#model-compatibility)。在 Google Cloud 的 Agent Platform 上，Claude Sonnet 4.5 及更高版本和 Claude Opus 4.5 及更高版本支持工具搜索。

使用 `ENABLE_TOOL_SEARCH` 环境变量控制工具搜索行为：

| 值    | 行为                                                                                                                                                                                                                                                                 |
| :------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| (未设置)  | 所有 MCP 工具均被延迟并按需加载。在 Google Cloud 的 Agent Platform 上或当 `ANTHROPIC_BASE_URL` 为非第一方主机时，回退为预先加载                                                                                                       |
| `true`   | 所有 MCP 工具均被延迟。Claude Code 即使在 Google Cloud 的 Agent Platform 上以及通过代理也会发送 beta 标头。对于早于 Sonnet 4.5 或 Opus 4.5 的 Google Cloud Agent Platform 模型，或不支持 `tool_reference` 块的代理，请求将会失败 |
| `auto`   | 阈值模式：如果工具适合上下文窗口的 10%，则预先加载，否则延迟加载                                                                                                                                                                      |
| `auto:N` | 具有自定义百分比的阈值模式，其中 `N` 为 0-100。例如，`auto:5` 表示 5%                                                                                                                                                                                |
| `false`  | 所有 MCP 工具均预先加载，无延迟                                                                                                                                                                                                                                |

```bash theme={null}
# Use a custom 5% threshold

ENABLE_TOOL_SEARCH=auto:5 claude

# Disable tool search entirely

ENABLE_TOOL_SEARCH=false claude
```

或者在您的 [settings.json `env` 字段中设置该值](/docs/en/settings#available-settings)。

您还可以专门禁用 `ToolSearch` 工具：

```json theme={null}
{
  "permissions": {
    "deny": ["ToolSearch"]
  }
}
```

### 使服务器免于延迟

如果服务器的工具应始终对 Claude 可见而无需搜索步骤，请在该服务器的配置中将 `alwaysLoad` 设置为 `true`。然后，在会话开始时，来自该服务器的每个工具都会加载到上下文中，而不管 `ENABLE_TOOL_SEARCH` 设置如何。对于 Claude 每轮都需要的一小部分工具请使用此功能，因为每个预先加载的工具都会消耗原本可用于您的对话的上下文。

以下 `.mcp.json` 条目使一个 HTTP 服务器免于延迟，而其他服务器保持延迟状态：

```json theme={null}
{
  "mcpServers": {
    "core-tools": {
      "type": "http",
      "url": "https://mcp.example.com/mcp",
      "alwaysLoad": true
    }
  }
}
```

`alwaysLoad` 字段在所有服务器类型上均可用，并且需要 Claude Code v2.1.121 或更高版本。MCP 服务器也可以通过在工具的 `"anthropic/alwaysLoad": true` 对象中包含 `_meta` 来将单个工具标记为始终加载，这仅对该工具产生相同的效果。

设置 `alwaysLoad: true` 也会在服务器连接之前阻止启动，上限为标准的 5 秒连接超时。尽管 MCP 启动默认是 [非阻塞的](/docs/en/env-vars)，但这仍然适用，因为在构建第一个提示时必须存在这些工具。其他服务器继续在后台连接。

## 将 MCP 提示作为命令使用

MCP 服务器可以公开提示，这些提示在 Claude Code 中可作为命令使用。

### 执行 MCP 提示

<Steps>
  <Step title="发现可用提示">
    输入 `/` 以查看所有可用命令，包括来自 MCP 服务器的命令。MCP 提示以 `/mcp__servername__promptname` 格式显示。
  </Step>

  <Step title="执行不带参数的提示">
    ```text theme={null}
    /mcp__github__list_prs
    ```
  </Step>

  <Step title="执行带参数的提示">
    许多提示接受参数。在命令后以空格分隔传递它们：

    ```text theme={null}
    /mcp__github__pr_review 456
    ```

    ```text theme={null}
    /mcp__jira__create_issue "Bug in login flow" high
    ```
  </Step>
</Steps>

<Tip>
  提示：

  * MCP 提示是从已连接的服务器中动态发现的
  * 参数根据提示定义的参数进行解析
  * 提示结果直接注入到对话中
  * 服务器和提示名称被标准化，空格转换为下划线
</Tip>

## 托管的 MCP 配置

对于需要对用户可以连接哪些 MCP 服务器进行集中控制的组织，请参见 [托管的 MCP 配置](/docs/en/managed-mcp)。它涵盖了使用 `managed-mcp.json` 部署固定的服务器集，使用 `allowedMcpServers` 和 `deniedMcpServers` 限制服务器，以及当服务器被阻止时用户看到的内容。

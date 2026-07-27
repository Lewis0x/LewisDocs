---
title: Model Context Protocol
source_id: codex/mcp
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/extend/mcp
owner: OpenAI
content_sha256: 09d64df2d691d3f4f8262a78961a7f21e24957426c610ba441a32b343ff23f6f
translation_of: codex/mcp
translation_model: k3
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/extend/mcp)

Content owner: OpenAI

# Model Context Protocol

模型上下文协议（MCP）将模型与工具和上下文连接起来。使用它可以让
ChatGPT 或 Codex 访问第三方文档，或让它
与浏览器或 Figma 等开发者工具交互。

ChatGPT 网页版可以使用插件提供的远程 MCP 支持的工具。本地 Codex
客户端也可以直接连接 MCP 服务器并共享其配置。

<a id="supported-mcp-features"></a>



ChatGPT 桌面应用、Codex CLI 和 IDE 扩展支持 MCP 服务器，并
为同一 Codex 主机共享 MCP 配置。

下面列出的受支持服务器功能适用于在 Codex
主机上配置的 MCP 服务器。托管的插件工具可能具有不同的功能。

## 支持的 MCP 功能

- **STDIO 服务器**：作为本地进程运行的服务器（由命令启动）。
  - 环境变量
- **可流式 HTTP 服务器**：通过地址访问的服务器。
  - Bearer 令牌身份验证
  - OAuth 身份验证
  - 适用于受信任第一方服务器的 ChatGPT 会话身份验证
- **服务器指令**：Codex 读取初始化期间返回的 MCP `instructions` 字段，并将其与服务器工具一起用作服务器范围的指导。

如果你为 Codex 构建或维护 MCP 服务器，请使用 `instructions` 来处理适用于整个服务器的跨工具工作流、约束和速率限制。保持前 512 个字符自包含，以便在 Codex 决定如何使用服务器时最重要的指导可用。

## 将 Codex 连接到 MCP 服务器

Codex 将 MCP 配置与其他 Codex 配置设置一起存储在 `config.toml` 中。默认情况下这是 `~/.codex/config.toml`，但你也可以使用 `.codex/config.toml` 将 MCP 服务器限定到某个项目（仅限受信任的项目）。

ChatGPT 桌面应用、Codex CLI 和 IDE 扩展共享此配置。
配置好 MCP 服务器后，你可以在这些客户端之间切换而无需
重新设置。





### 在 ChatGPT 桌面应用中配置

1. 打开**设置**，然后选择 **MCP 服务器**。
2. 选择**添加服务器**。
3. 输入名称，选择 **STDIO** 或**可流式 HTTP**，并提供
   服务器的命令或 URL。
4. 保存服务器，然后选择**重启**。

服务器列表显示哪些服务器已启用以及哪些需要 OAuth。当
OAuth 服务器需要登录时，选择**身份验证**。在编辑器中，输入 `/mcp`
可查看已连接的服务器。











### 使用 config.toml 配置

如需更细粒度的控制，请编辑 `~/.codex/config.toml` 或项目范围的
`.codex/config.toml`。请参阅 [配置参考](https://learn.chatgpt.com/docs/config-file/config-reference)
以获取每个受支持 MCP 选项的可搜索列表。

在配置文件中使用 `[mcp_servers.<server-name>]` 表配置每个 MCP 服务器。



<a id="stdio-servers"></a>



#### STDIO 服务器

- `command`（必需）：启动服务器的命令。
- `args`（可选）：传递给服务器的参数。
- `env`（可选）：为服务器设置的环境变量。
- `env_vars`（可选）：允许并转发的环境变量。
- `cwd`（可选）：启动服务器的工作目录。
- `experimental_environment`（可选）：设置为 `remote` 以在可用的
  远程执行器环境中通过该环境启动 stdio 服务器。

`env_vars` 可以包含普通变量名或带有来源的对象：

```toml
env_vars = ["LOCAL_TOKEN", { name = "REMOTE_TOKEN", source = "remote" }]
```

字符串条目和 `source = "local"` 从 Codex 的本地环境读取。
`source = "remote"` 从远程执行器环境读取，并需要
远程 MCP stdio。



<a id="streamable-http-servers"></a>



#### 可流式 HTTP 服务器

- `url`（必填）：服务器地址。
- `auth`（可选）：在配置的 bearer 令牌和授权标头之后尝试的身份验证方式。使用 `oauth`（默认值）表示使用已存储的 MCP OAuth 凭据。使用 `chatgpt` 表示为可信的第一方 ChatGPT 来源使用当前 ChatGPT 会话，并以已存储的 OAuth 作为后备。
- `bearer_token_env_var`（可选）：在 `Authorization` 中发送的 bearer 令牌的环境变量名称。
- `http_headers`（可选）：标头名称到静态值的映射。
- `env_http_headers`（可选）：标头名称到环境变量名称的映射（值从环境中提取）。

如果没有凭据来源可解析，Codex 可以在不进行身份验证的情况下连接到服务器。单独运行 `codex mcp login <server-name>` 以启动 MCP OAuth 登录。

#### 其他配置选项

- `startup_timeout_sec`（可选）：服务器启动的超时时间（秒）。默认值：`10`。
- `tool_timeout_sec`（可选）：服务器运行工具的超时时间（秒）。默认值：`60`。
- `enabled`（可选）：设置 `false` 可在不删除服务器的情况下禁用它。
- `required`（可选）：设置 `true` 可在此已启用的服务器无法初始化时使启动失败。
- `enabled_tools`（可选）：工具允许列表。
- `disabled_tools`（可选）：工具拒绝列表（在 `enabled_tools` 之后应用）。
- `default_tools_approval_mode`（可选）：来自此服务器的工具的默认审批行为。支持的值为 `auto`、`prompt`、`writes` 和 `approve`。`writes` 模式会对未标记为只读的工具进行提示。
- `tools.<tool>.approval_mode`（可选）：按工具覆盖审批行为。

如果你的 OAuth 提供商需要固定的回调端口，请在 `mcp_oauth_callback_port` 中设置顶层 `config.toml`。如果未设置，Codex 会绑定到一个临时端口。

如果你的 MCP OAuth 流程必须使用特定的回调 URL（例如远程 Devbox 入口 URL 或自定义回调路径），请设置 `mcp_oauth_callback_url`。Codex 会将此值用作基础回调 URL，然后附加特定于服务器的回调 ID，以生成登录期间发送的 OAuth `redirect_uri`。请在你的 OAuth 提供商处注册完整派生的 `redirect_uri`，包括附加的回调 ID 以及任何已配置的路径、查询或端口，而不是仅注册没有该后缀的基础主机或路径。本地回调 URL（例如 `localhost`）绑定在本地接口上；非本地回调 URL 绑定在 `0.0.0.0` 上，以便回调可以到达主机。

如果 MCP 服务器公布了 `scopes_supported`，Codex 会在 OAuth 登录期间优先使用这些服务器公布的范围。否则，Codex 会回退到 `config.toml` 中配置的范围。

#### config.toml 示例

```toml
[mcp_servers.context7]
command = "npx"
args = ["-y", "@upstash/context7-mcp"]
env_vars = ["LOCAL_TOKEN"]

[mcp_servers.context7.env]
MY_ENV_VAR = "MY_ENV_VALUE"
```

```toml
# Optional MCP OAuth callback overrides (used by `codex mcp login`)

mcp_oauth_callback_port = 5555
mcp_oauth_callback_url = "https://devbox.example.internal/callback"
```

```toml
[mcp_servers.figma]
url = "https://mcp.figma.com/mcp"
bearer_token_env_var = "FIGMA_OAUTH_TOKEN"
http_headers = { "X-Figma-Region" = "us-east-1" }
```

```toml
[mcp_servers.chrome_devtools]
url = "http://localhost:3000/mcp"
enabled_tools = ["open", "screenshot"]
disabled_tools = ["screenshot"] # applied after enabled_tools
default_tools_approval_mode = "prompt"
startup_timeout_sec = 20
tool_timeout_sec = 45
enabled = true

[mcp_servers.chrome_devtools.tools.open]
approval_mode = "approve"
```

### 插件提供的 MCP 服务器

已安装的插件可以在其插件清单中捆绑 MCP 服务器。这些服务器由插件启动，因此用户配置不会设置它们的传输命令。用户配置仍可在 `plugins.<plugin>.mcp_servers.<server>` 下控制开关状态和工具策略。

```toml
[plugins."sample@test".mcp_servers.sample]
enabled = true
default_tools_approval_mode = "prompt"
enabled_tools = ["read", "search"]

[plugins."sample@test".mcp_servers.sample.tools.search]
approval_mode = "approve"
```

## 常用 MCP 服务器示例

MCP 服务器的列表在不断增长。以下是一些常见的：

- [OpenAI Docs MCP](https://developers.openai.com/learn/docs-mcp)：搜索和阅读 OpenAI 开发者文档。
- [Context7](https://github.com/upstash/context7)：连接最新的开发者文档。
- Figma [Local](https://developers.figma.com/docs/figma-mcp-server/local-server-installation/) 和 [Remote](https://developers.figma.com/docs/figma-mcp-server/remote-server-installation/)：访问你的 Figma 设计。
- [Playwright](https://www.npmjs.com/package/@playwright/mcp)：使用 Playwright 控制和检查浏览器。
- [Chrome Developer Tools](https://github.com/ChromeDevTools/chrome-devtools-mcp/)：控制和检查 Chrome。
- [Sentry](https://docs.sentry.io/product/sentry-mcp/#codex)：访问 Sentry 日志。
- [GitHub](https://github.com/github/github-mcp-server)：管理超出 `git` 支持范围的 GitHub 功能（例如拉取请求和议题）。

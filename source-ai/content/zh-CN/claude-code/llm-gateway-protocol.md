---
title: 网关协议参考
source_id: claude-code/llm-gateway-protocol
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/llm-gateway-protocol
owner: Anthropic
content_sha256: 4fa26b575a2e55a255247886c4fc1e2f0644a79aedfcb4ae07e330dba9818fc8
translation_of: claude-code/llm-gateway-protocol
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/llm-gateway-protocol)

Content owner: Anthropic

> ## 文档索引
> 获取完整文档索引，地址：https://code.claude.com/docs/llms.txt
> 在进一步探索之前，请使用此文件发现所有可用页面。

# 网关协议参考

> Claude Code 与 LLM 网关之间的 API 契约：端点、需要转发的请求头和请求体字段、字段被剥离时的功能降级、用于成本跟踪的归因请求头，以及模型发现。

本页记录了 Claude Code 发送给网关的请求，包括它调用的端点、网关必须转发的请求头和请求体字段，以及不转发时哪些功能会停止工作。本页面向正在配置网关产品以与 Claude Code 协同工作的运维人员。

正在运行的 [Claude 应用网关](/docs/en/claude-apps-gateway) 会在 `GET /protocol` 提供此契约的机器可读版本，涵盖相同的转发要求，以及 Claude 应用网关特有的 SSO 登录、托管设置下发和遥测端点。Claude 应用网关与 CLI 运行自同一个 `claude` 二进制文件，因此 [Claude 应用网关快速入门](/docs/en/claude-apps-gateway#quickstart) 是获取一个可拉取规范的运行实例的最短路径。

<Note>
  * 要为您的组织部署现有或第三方网关，请参阅 [部署 LLM 网关](/docs/en/llm-gateway-rollout)
  * 如果您是使用所获凭据将 Claude Code 认证到网关的个人开发者，请参阅 [将 Claude Code 连接到 LLM 网关](/docs/en/llm-gateway-connect)
</Note>

本页涵盖：

* [API 格式](#api-formats) 以及每种格式需要提供的端点
* [请求头](#request-headers)：哪些必须到达上游，哪些可由您的网关消费
* [系统提示署名块](#system-prompt-attribution-block) 及其与提示缓存的交互
* [功能透传](#feature-pass-through)：请求头或请求体字段被剥离时会破坏什么
* [模型发现](#model-discovery)

本页使用两个术语描述网关对每个请求头和请求体字段的处理方式：

* **原样转发**：逐字节传递给上游
* **消费**：网关可以读取它用于路由、归因或追踪，且无需转发

任何未标记为原样转发的内容，都可以由您自行消费或忽略。

## API 格式

网关必须向 Claude Code 客户端至少暴露以下 API 格式之一。Claude Code 使用哪种格式由客户端的配置决定：下表 Selected by 列中的变量会指示 Claude Code 以该格式连接到你的网关。Google Cloud's Agent Platform 是 Google Cloud 的 Claude 端点，前身为 Vertex AI；其变量名称保留了 `VERTEX` 的拼写。

| 格式                                   | 选定方式                                                   | 端点                                                                | 原样转发                                                                                        |
| :--------------------------------------- | :------------------------------------------------------------ | :----------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------- |
| Anthropic Messages                       | `ANTHROPIC_BASE_URL`                                          | `/v1/messages`, `/v1/messages/count_tokens` (可选)                   | `anthropic-beta` 和 `anthropic-version` 请求头                                                 |
| Amazon Bedrock InvokeModel               | `ANTHROPIC_BEDROCK_BASE_URL` 搭配 `CLAUDE_CODE_USE_BEDROCK=1` | `/model/{model}/invoke`, `/model/{model}/invoke-with-response-stream`    | `anthropic_beta` 和 `anthropic_version` 请求体字段                                             |
| Google Cloud's Agent Platform rawPredict | `ANTHROPIC_VERTEX_BASE_URL` 搭配 `CLAUDE_CODE_USE_VERTEX=1`   | `:rawPredict`, `:streamRawPredict`, `count-tokens:rawPredict` (可选) | `anthropic-beta` 和 `anthropic-version` 请求头，以及 `anthropic_version` 请求体字段 |

### Foundry 和 AWS 上的 Claude Platform

Microsoft Foundry 和 [Claude Platform on AWS](/docs/en/claude-platform-on-aws) 实现了 Anthropic Messages 格式。Claude Code 通过它们各自的变量 `ANTHROPIC_FOUNDRY_BASE_URL` 和 `ANTHROPIC_AWS_BASE_URL` 路由到它们，但前置其中任一方的网关都实现上表中的 Anthropic Messages 行。前置 AWS 上 Claude Platform 的网关还必须转发 `anthropic-workspace-id` 请求头，[该平台要求每个请求都携带它](/docs/en/claude-platform-on-aws)。

### 可选端点和启动流量

令牌计数端点是唯一可选的端点：当它们缺失时，Claude Code 会在本地估算上下文使用量。推理请求发送到 `/v1/messages?beta=true`，因此应匹配路径而非完整 URL。Google Cloud's Agent Platform 的方法后缀附加在发布者模型路径之后，例如 `/projects/{project}/locations/{location}/publishers/anthropic/models/{model}:streamRawPredict`。

网关还会看到可以放心拒绝而不会破坏任何功能的尽力而为的启动流量：一个 `HEAD /` 连通性探测，以及在 Amazon Bedrock 格式网关上的一个 `GET /inference-profiles?type=SYSTEM_DEFINED` 请求。

[fast mode](/docs/en/fast-mode) 可用性检查永远不会出现在网关日志中：它直接调用 `api.anthropic.com` 而不是遵循 `ANTHROPIC_BASE_URL`，因此在阻止直接出站到 `api.anthropic.com` 的网络上，fast mode 可能会报告连通性错误，而通过网关的推理仍在正常工作。[WebFetch domain safety check](/docs/en/data-usage#webfetch-domain-safety-check) 也会直接调用 `api.anthropic.com`。[在代理和 LLM 网关后使用 fast mode](/docs/en/fast-mode#use-fast-mode-behind-proxies-and-llm-gateways) 介绍了可恢复它的变量。

### 流式传输

推理响应必须以流式传输。Claude Code 会在服务器发送事件到达时立即消费它们，因此在转发之前缓冲完整响应的网关会导致客户端停滞。

### 与上游的格式不匹配

客户端使用哪种格式决定了你的网关会接收到什么。常见的故障模式是：客户端发送给网关的格式与网关背后的上游提供商所接受的格式不匹配。

* 当客户端使用 Amazon Bedrock 或 Google Cloud 的 Agent Platform 格式时，Claude Code 仅发送这些提供商所接受的完整能力集合的子集
* 当客户端使用 Anthropic Messages 格式时，Claude Code 会发送完整的功能集，即使你的网关转发到 Amazon Bedrock 或 Google Cloud 的 Agent Platform 上游

弥合这一差异是你网关的职责。[功能透传](#feature-pass-through) 描述了当它不这样做时会出现什么问题。

## 请求标头

Claude Code 在 API 请求中包含这些标头。标头名称在传输时不区分大小写。原样转发 `anthropic-version` 和 `anthropic-beta`， 加上 `anthropic-workspace-id`,当上游是 [Claude 平台,在 AWS](/docs/en/claude-platform-on-aws)；其余部分网关可用于路由、归因和 追踪，并且无需转发。

| 标头                          | 描述                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| :------------------------------ | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Authorization`, `x-api-key`    | 开发者的网关凭据，根据其设置了哪个 [凭据变量](/docs/en/llm-gateway-connect#set-the-credential-variable)，可放在一个或两个标头中                                                                                                                                                                                                                                                                                  |
| `anthropic-version`             | API 版本，当前为 `2023-06-01`。Amazon Bedrock 和 Google Cloud 的 Agent Platform 格式请求还会在请求体中携带 `anthropic_version` 字段，其值是提供方方言字符串，而不是此标头的值                                                                                                                                                                                                                          |
| `anthropic-beta`                | 请求的逗号分隔能力值。原样转发该请求头；不要仅允许个别值，因为该集合会随 Claude Code 版本而变化。当开发者使用 claude.ai 登录进行身份验证时（在设置了 `ANTHROPIC_BASE_URL` 而未设置网关凭据变量时可能发生），此请求头还会携带上游所需的 OAuth 能力，若将其剥离，这些请求将失败并返回 `401` |
| `x-claude-code-session-id`      | 当前 Claude Code 会话的唯一标识符。使用它可以聚合来自同一会话的所有请求，而无需解析请求体                                                                                                                                                                                                                                                                                                                              |
| `x-claude-code-agent-id`        | 发出请求的 [子代理](/docs/en/sub-agents) 的标识符,仅出现在 Claude Code 在会话内部派生的代理所发出的请求中。将其与会话 ID 一起使用,可将成本归因于并行代理                                                                                                                                                                                                         |
| `x-claude-code-parent-agent-id` | 发起请求代理的生成方代理的标识符，仅对嵌套代理存在 |

子代理 ID 在每次生成时都会重新创建。作为 [agent team](/docs/en/agent-teams) 具名成员的队友代理，会在多次重新连接中复用基于名称的稳定 ID。在这两种情况下，该 ID 都标识一个代理，而不是一个人或设备，因此不要将代理 ID 标头当作用户标识符。

如果您的开发人员设置了 `ANTHROPIC_CUSTOM_HEADERS`，这些标头也会出现在请求中。

### 以开放列表转发

将标头和请求体字段视为开放列表，而非封闭列表。Claude Code 会随着版本发布获得新能力，这些能力以新的 `anthropic-beta` 值、新的请求体字段，以及偶尔出现的新的 `anthropic-*` 或 `x-claude-code-*` 标头的形式到来。

当转发到 Anthropic 格式的上游时，将 `anthropic-*` 请求标头和请求体字段原样传递，而不是仅允许你今天看到的那些。一个固定于已观察列表的网关会剥离下一个功能的标头或字段，并在引入该功能的版本上将其破坏。

例外情况是非 Anthropic 上游，例如 Amazon Bedrock 或 Google Cloud 的 Agent Platform，此时弥合架构差异是网关的职责；参见 [功能透传](#feature-pass-through)。

## 系统提示署名块

Claude Code 会在系统提示前附加一个简短的署名块，其中包含客户端版本和从对话派生的指纹。当该块原封不动地作为第一个系统块到达时，`api.anthropic.com` 端点会在处理前将其剥离，因此它不会影响第一方提示缓存。任何其他上游都会将其作为提示的一部分接收。

剥离是基于位置的，因此只有当网关原样转发 `system` 数组时才有效。要在不丢失其他系统内容的情况下将该块排除在提示之外：

* 将 `system` 数组按原样转发，保持该块位于首位：在其前面追加另一个系统块、对数组重新排序或将其转换为单个字符串都会破坏剥离机制，导致该块到达模型并进入提示缓存键。
* 将该块保留在其自己的数组条目中：端点会将任何以归属标头开头的合并块整体视为归属内容，并丢弃合并到其中的所有内容，包括系统提示的其余部分。
* 如果您的网关必须重塑系统内容，请设置 [`CLAUDE_CODE_ATTRIBUTION_HEADER=0`](/docs/en/env-vars)，使 Claude Code 省略该块。Anthropic 和云服务提供商的 Claude 端点会读取该块用于归属，因此应在客户端省略它，而不是在网关中剥离或移动它。

未经修改直接到达端点的请求不受影响。

{/* min-version: 2.1.181 */}从 Claude Code v2.1.181 开始，当请求通过自定义基础 URL 路由时，该块在会话的整个生命周期内保持稳定，因此在网关上基于完整请求体构建的提示缓存无需禁用即可正常工作。在 v2.1.181 之前，该块包含按请求生成的令牌；在这些版本上，如果您的网关实现了此类缓存，请设置 `CLAUDE_CODE_ATTRIBUTION_HEADER=0`。

## 功能透传

Claude Code 将 `ANTHROPIC_BASE_URL` 网关视为 Anthropic 格式的端点，并向其发送它发给 `api.anthropic.com` 的 beta 标头和请求体字段，但有一小部分为直连保留的诊断信息和默认值除外，例如下文介绍的细粒度工具流式传输默认值。该集合的内容随版本而变化，因此不要依赖其具体内容。

添加请求体字段的功能会将这些字段与某个 beta 标头配对，二者一起传输。如果网关在传递请求体的同时剥离了标头，或将 Anthropic 格式的请求体转发给使用不同 schema 的上游，就会产生硬性的 `400` 错误；只有当两部分同时缺失时，该功能才会安静地关闭。为内容检查而重写或编辑请求体的网关，会以与剥离相同的方式破坏这种配对，因此请在不做修改的前提下进行检查。下表注明了各项功能偏离该配对规则的情况。

细粒度工具流式传输是直连默认值之一：每当请求经由自定义基础 URL 路由时，它默认关闭，只有当开发者设置 [`CLAUDE_CODE_ENABLE_FINE_GRAINED_TOOL_STREAMING=1`](/docs/en/env-vars) 时，网关才会收到它。

| 功能                                                                                                                                                                                                         | 标头与正文对                                                                                                                                                                                        | 损坏时的症状                                                                                                                      | 补救措施                                                                                                            |
| :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------- |
| [自适应推理](/docs/en/model-config#adjust-effort-level)                                                                                                                                                                                       | 无 beta 标头。 Claude Code 对 Claude 4.6 及更高版本发送 `thinking: {"type": "adaptive"}`，并将其无法识别的模型名称（如网关别名）视为接收该字段的当前模型 | `400` 当上游模型构建不接受该字段时，命名 `thinking` 字段或 `adaptive` 标签                                  | 升级上游版本。在 Opus 4.6 和 Sonnet 4.6 上，开发者可以改为设置 `CLAUDE_CODE_DISABLE_ADAPTIVE_THINKING=1` |
| [上下文管理](https://platform.claude.com/docs/en/build-with-claude/context-editing)                                                                                                                                                      | 上下文管理 beta 标头与 `context_management` 正文字段配对                                                                                                                               | `400` 与 `Extra inputs are not permitted`。当网关接受 Anthropic 格式的请求但将其转发到 Amazon Bedrock 时很常见 | 两者都转发，或 [`CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS=1`](/docs/en/env-vars)                                            |
| [扩展上下文](https://platform.claude.com/docs/en/build-with-claude/context-windows#context-window-sizes-by-model)和[交错思考](https://platform.claude.com/docs/en/build-with-claude/extended-thinking#interleaved-thinking) | 仅 Beta 标头，无请求体字段                                                                                                                                                                            | 当标头被剥离时静默不可用；上游永远不会看到该能力请求                                         | 逐字转发 `anthropic-beta`                                                                                      |
| Beta [工具字段](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)                                                                                                                                                       | 与工具相关的 Beta 标头与工具模式字段（如 `strict` 和 `defer_loading`）配对                                                                                                                 | 当请求体在未携带其标头的情况下通过时，`400` 会指出未被识别的工具模式字段                                          | 两者都转发，或 `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS=1`                                                            |
| [Effort（努力程度）](https://platform.claude.com/docs/en/build-with-claude/effort)和[结构化输出](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)                                                                        | `output_config` 请求体字段承载努力程度、结构化输出格式和任务预算设置；每一项都与各自的 Beta 标头配对                                                                      | `400` 会指出 `output_config`，在 Amazon Bedrock 和 Google Cloud 的 Agent Platform 上游中通常是 `Extra inputs are not permitted`      | 将该字段及其标头一起转发                                                                             |
| [Token 计数](https://platform.claude.com/docs/en/build-with-claude/token-counting)                                                                                                                                                           | 无 Beta 配对；使用 `count_tokens` 端点                                                                                                                                                           | Claude Code 回退为在本地估算上下文用量                                                                               | 如果需要精确计数，请暴露该端点                                                                           |

`ANTHROPIC_DEFAULT_*_MODEL_SUPPORTED_CAPABILITIES` [变量](/docs/en/model-config)仅在提供商配置中声明模型能力：`CLAUDE_CODE_USE_BEDROCK`、`CLAUDE_CODE_USE_VERTEX`、`CLAUDE_CODE_USE_FOUNDRY` 和 [`CLAUDE_CODE_USE_MANTLE`](/docs/en/amazon-bedrock#use-the-mantle-endpoint)。它们在 `ANTHROPIC_BASE_URL` 网关之后不起作用。

### 自动重试与错误转发

Claude Code 会在某些上游拒绝后自动重试，并在会话的剩余部分禁用被拒绝的能力。对 `thinking` 字段的拒绝、对[思考签名](https://platform.claude.com/docs/en/build-with-claude/extended-thinking)的拒绝，以及对会话中途系统消息的拒绝，都会以这种方式恢复。上下文管理和工具模式字段的拒绝不会重试；这些 `400` 错误会传达给开发者。

重试逻辑基于上游错误的措辞进行匹配，因此请不加修改地转发错误响应体。即使保留了状态码，将上游错误包装在自己信封中的网关也会破坏恢复路径。

### 禁用预发布功能

`CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS=1` 阻止 Claude Code 向每个提供商发送预发布功能及其正文字段，包括上下文管理和 beta 工具字段。它不影响自适应推理（由模型而非 beta 选择），也绝不会抑制订阅认证所需的 OAuth 功能。

Claude Code 发送的功能集合会随版本不断增长。有关当前的 beta 标头字符串，请参阅 [beta 标头参考](https://platform.claude.com/docs/en/api/beta-headers)；请针对新的 Claude Code 版本测试你的网关，而不是固定到观察到的列表。

## 模型发现

当 `ANTHROPIC_BASE_URL` 指向暴露 Anthropic Messages 格式的网关时，Claude Code 可以在启动时查询网关的 `/v1/models` 端点，并将返回的模型添加到 `/model` 选择器中。

开发者通过设置 [`CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY=1`](/docs/en/env-vars) 来启用它，可以在自己的环境中设置，也可以通过托管设置。发现功能默认关闭，这样由共享 API 密钥支持的网关就不会向每个用户暴露该密钥可访问的所有模型。这需要 Claude Code v2.1.129 或更高版本。

### 发现何时运行

发现功能仅适用于 Anthropic Messages 格式。在以下情况下不会运行：

* 设置了任何 `CLAUDE_CODE_USE_*` 提供商变量，即使 `ANTHROPIC_BASE_URL` 也已设置
* `ANTHROPIC_BASE_URL` 未设置或指向 `api.anthropic.com`
* 非必要流量已被禁用，无论是通过 [`CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`](/docs/en/env-vars) 还是组织策略

### 请求与响应

请求是 `GET /v1/models?limit=1000`，超时时间为 3 秒，任何重定向都被视为失败，因此凭据不会泄露给重定向目标。响应缓慢或重定向 `/v1/models`（即使是 `http` 到 `https`）的网关会使发现功能静默失败；请直接在配置的基础 URL 上提供该端点。

发现请求恰好发送一个凭据标头：

* `ANTHROPIC_AUTH_TOKEN` 作为持有者令牌（bearer token），当它被设置时
* 否则发送解析出的 API 密钥，包括 [`apiKeyHelper`](/docs/en/llm-gateway-connect#rotate-credentials-with-apikeyhelper) 值，放在 `x-api-key` 标头中

这与推理请求不同，推理请求会在两个标头中都发送辅助值。对 `/v1/models` 进行身份验证的网关必须为辅助部署接受 `x-api-key`。来自 `ANTHROPIC_CUSTOM_HEADERS` 的任何标头也会一并包含。

Claude Code 从响应 `data` 数组中的每个条目读取 `id` 和可选的 `display_name`，并忽略 `id` 不以 `claude` 或 `anthropic` 开头的条目：

```json theme={null}
{
  "data": [
    { "id": "claude-sonnet-4-6", "display_name": "Claude Sonnet 4.6" },
    { "id": "claude-opus-4-8" }
  ]
}
```

### 选择器条目与缓存

选择器是开发者在 Claude Code 中运行 `/model` 时打开的交互式模型列表。每个发现的条目都标记为"来自网关"，并在提供时使用 `display_name`。[`availableModels` 托管设置](/docs/en/settings#available-settings) 限制了发现可以添加的内容。

当发现的 ID 与选择器中已有的行完全匹配，或者发现的 ID 和现有 ID 都解析为 [Fable](/docs/en/model-config#work-with-fable-5) 时，该发现的 ID 会被跳过。{/* min-version: 2.1.197 */}自 Claude Code v2.1.197 起，当发现的显式 ID 与内置条目都解析为同一模型时，它也会折叠进该内置条目。内置行以别名（如 `sonnet`）为键，因此该别名当前解析到的模型的显式发现 ID（如 `claude-sonnet-5`）会折叠进 `sonnet` 行，而别名未解析到的 ID（如 `claude-sonnet-4-6`）仍会在内置条目旁边添加自己的"来自网关"行。

结果会缓存到 `~/.claude/cache/gateway-models.json`（在 Windows 上为 `%USERPROFILE%\.claude\cache\gateway-models.json`），并在每次启动时刷新。如果请求失败或网关未实现 `/v1/models`，选择器会回退到上一次启动时的缓存列表或内置模型列表。如果你的网关使用与发现过滤器不匹配的别名提供 Claude 模型，开发者可以使用 [模型配置](/docs/en/model-config) 变量手动添加这些别名。

## 相关资源

有关网关文档集的其余部分和底层 API 参考：

* [网关概述](/docs/en/gateways)：什么是网关，以及如何在 Claude 应用网关和其他产品之间做出选择
* [其他 LLM 网关](/docs/en/llm-gateway)：如何部署组织自行运行的网关，以及它如何与 claude.ai 订阅交互
* [为你的组织部署 LLM 网关](/docs/en/llm-gateway-rollout)：使用此契约的管理员清单
* [将 Claude Code 连接到 LLM 网关](/docs/en/llm-gateway-connect)：面向开发者的配置和故障排除表
* [Beta 标头参考](https://platform.claude.com/docs/en/api/beta-headers)：当前的 `anthropic-beta` 值集合
* [Messages API](https://platform.claude.com/docs/en/api/messages)：Anthropic 格式网关所实现的 API 格式

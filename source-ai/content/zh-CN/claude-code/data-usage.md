---
title: 数据使用
source_id: claude-code/data-usage
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/data-usage
owner: Anthropic
content_sha256: 716ab8bb72232372eaf66b1e7fd2b725f6fa4ca2bf55415842e89929772dcc7e
translation_of: claude-code/data-usage
translation_model: k3
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/data-usage)

Content owner: Anthropic

> ## 文档索引
> 获取完整的文档索引，请访问：https://code.claude.com/docs/llms.txt
> 在进一步探索之前，请使用此文件来发现所有可用页面。

# 数据使用

> 了解 Anthropic 关于 Claude 的数据使用政策

## 数据政策

### 数据训练政策

**消费者用户（免费、Pro 和 Max 套餐）**：
我们允许您选择是否授权使用您的数据来改进未来的 Claude 模型。当此设置开启时，我们将使用来自免费、Pro 和 Max 账户的数据来训练新模型（包括您从这些账户使用 Claude Code 时产生的数据）。

**商业用户**：（Team 和 Enterprise 套餐、API、第三方平台以及 Claude Gov）维持现有政策：Anthropic 不会使用在商业条款下发送到 Claude Code 的代码或提示词来训练生成式模型，除非客户选择向我们提供其数据用于模型改进（例如，[开发者合作伙伴计划](https://support.claude.com/en/articles/11174108-about-the-development-partner-program)）。

### 开发者合作伙伴计划

如果您明确选择加入向我们提供训练材料的方式，例如通过 [开发者合作伙伴计划](https://support.claude.com/en/articles/11174108-about-the-development-partner-program)，我们可能会使用所提供的这些材料来训练我们的模型。组织管理员可以为其组织明确选择加入开发者合作伙伴计划。请注意，此计划仅适用于 Anthropic 第一方 API，不适用于 Amazon Bedrock 或 Google Cloud 的 Agent Platform 用户。

### 使用 `/feedback` 命令提交反馈

如果您选择使用 `/feedback` 命令向我们发送有关 Claude Code 的反馈，我们可能会使用您的反馈来改进我们的产品和服务。通过 `/feedback` 或通过 `/bug` 和 `/share`（通过相同路径报告）共享的对话记录将保留 5 年。

### 会话质量调查

当您在 Claude Code 中看到"Claude 在本次会话中表现如何？"的提示时，回复此调查（包括选择"忽略"）仅记录您的评分。我们不会收集或存储任何对话记录、输入、输出或其他会话数据作为评分提示本身的一部分。与点赞/点踩反馈或 `/feedback` 报告不同，此会话质量调查是一个简单的产品满意度指标。

在评分提示之后，您可能会看到一个单独的后续询问："Anthropic 可以查看您的会话记录以帮助我们改进 Claude Code 吗？"这是与评分不同的可选第二步：

* **是**：将您的对话记录、任何子代理记录以及磁盘上的原始会话日志文件上传到 Anthropic。已知的 API 密钥和令牌模式在上传前会被脱敏处理。源代码、文件内容和其他对话内容将原样上传。共享的记录最多保留 6 个月。在 Amazon Bedrock、Google Cloud 的 Agent Platform、Microsoft Foundry 以及已登录的 [Claude 应用网关](/docs/en/claude-apps-gateway) 会话中，选择"是"会将相同的数据写入 `~/.claude/feedback-bundles/` 下的本地归档，而不是上传；除非您转发该文件，否则不会有任何内容离开您的机器。
* **否**：拒绝且不发送任何内容
* **不再询问**：拒绝并阻止此后续提示在未来会话中出现

除非您明确选择**是**，否则不会上传任何内容。具有 [零数据保留](/docs/en/zero-data-retention) 的组织，或产品反馈被组织政策禁用的组织，或设置了 `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` 的组织，永远不会看到此后续提示。您对此调查的回复（包括在评分提示后提交的会话记录）不会影响您的数据训练偏好，也不能用于训练我们的 AI 模型。

要禁用这些调查，请设置 `CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY=1`。当设置了 `DISABLE_TELEMETRY`、`DO_NOT_TRACK` 或 `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` 时，调查也会被禁用。阻止非必要流量但通过自己的 [OpenTelemetry 收集器](/docs/en/monitoring-usage) 捕获调查回复的组织，可以通过设置 `CLAUDE_CODE_ENABLE_FEEDBACK_SURVEY_FOR_OTEL=1` 来选择重新启用调查。然后，调查仅将评分记录到已配置的收集器中。对话记录共享的后续操作以及所有其他发往 Anthropic 的反馈流量将保持禁用状态。为了控制频率而不是禁用，请将您的设置文件中的 [`feedbackSurveyRate`](/docs/en/settings#available-settings) 设置为 `0` 到 `1` 之间的概率。

### 数据保留

Anthropic 根据您的账户类型和偏好保留 Claude Code 数据。

**消费端用户（免费版、Pro 和 Max 套餐）**：

* 允许将其数据用于模型改进的用户：5 年保留期，以支持模型开发和安全性改进
* 不允许将其数据用于模型改进的用户：30 天保留期
* 隐私设置可以随时在 [claude.ai/settings/data-privacy-controls](https://claude.ai/settings/data-privacy-controls) 更改。

**商业用户（团队版、企业版和 API）**：

* 标准版：30 天保留期
* [零数据保留](/docs/en/zero-data-retention)：对于符合资格的账户，适用于 Claude for Enterprise 的 Claude Code。ZDR 不包含在标准的企业版套餐中；在确认资格后，您的客户团队会按组织将其启用
* 本地缓存：Claude Code 客户端默认会在 `~/.claude/projects/` 下以明文形式将会话记录本地存储 30 天，以实现会话恢复。可以使用 `cleanupPeriodDays` 调整此期限。有关存储内容和清除方法，请参见 [应用程序数据](/docs/en/claude-directory#application-data)。

您可以随时删除网络上的单个 Claude Code 会话。删除会话将永久删除该会话的事件数据。有关如何删除会话的说明，请参阅 [删除会话](/docs/en/claude-code-on-the-web#delete-sessions)。

在我们的 [隐私中心](https://privacy.anthropic.com/) 了解有关数据保留做法的更多信息。

了解完整详情，请审阅我们的 [商业服务条款](https://www.anthropic.com/legal/commercial-terms)（面向团队版、企业版和 API 用户）或 [消费者条款](https://www.anthropic.com/legal/consumer-terms)（面向免费版、Pro 和 Max 用户）以及 [隐私政策](https://www.anthropic.com/legal/privacy)。

## 数据访问

对于所有第一方用户，您可以了解有关 [本地 Claude Code](#local-claude-code-data-flow-and-dependencies) 和 [远程 Claude Code](#cloud-execution-data-flow-and-dependencies) 记录了哪些数据的更多信息。[远程控制](/docs/en/remote-control) 会话遵循本地数据流，因为所有执行都在您的机器上进行；在连接期间，会话记录也会存储在 Anthropic 服务器上，以便跨设备同步对话，如 [连接与安全](/docs/en/remote-control#connection-and-security) 中所述。请注意，对于远程 Claude Code，Claude 会访问您发起 Claude Code 会话的代码库。Claude 不会访问您已连接但尚未启动会话的代码库。

## 本地 Claude Code：数据流与依赖关系

下图展示了 Claude Code 在安装和正常运行期间如何连接到外部服务。实线表示必需的连接，而虚线表示可选的或由用户发起的数据流。

<img src="https://mintcdn.com/claude-code/YR4DRZyI3CdsXkiT/images/claude-code-data-flow.svg?fit=max&auto=format&n=YR4DRZyI3CdsXkiT&q=85&s=2846ea92cfc2297b8620c31c82b482ad" alt="展示 Claude Code 外部连接的图表：安装/更新连接到分发服务器，用户请求连接到 Anthropic 的 Console 身份验证和 public-api，可选的遥测流将指标和错误报告传送到 Anthropic 和第三方服务。使用 /feedback 发送的反馈会发送到 Google Cloud Storage，并可选择创建 GitHub issue" width="720" height="520" data-path="images/claude-code-data-flow.svg" />

Claude Code 在本地运行。为了与 LLM 交互，Claude Code 会通过网络发送数据。此数据包括所有用户提示词和模型输出，在传输过程中通过 TLS 1.2+ 加密。Claude Code 兼容大多数流行的 VPN 和 LLM 代理。

静态加密取决于您的模型提供商：

| 提供商                      | 静态加密                                                                                                                                                                                                                                                                                                                                                                                                                      |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Anthropic API                 | 基础设施级磁盘加密 (AES-256)。启用 [零数据保留](/docs/en/zero-data-retention) 以实现无服务端持久化。                                                                                                                                                                                                                                                                                                   |
| Amazon Bedrock                | 使用 AWS 托管密钥的 AES-256。可通过 AWS KMS 使用客户托管密钥。                                                                                                                                                                                                                                                                                                                                                             |
| Google Cloud's Agent Platform | Google 托管的加密密钥。支持 CMEK。                                                                                                                                                                                                                                                                                                                                                                                         |
| Microsoft Foundry             | 取决于部署的 [托管选项](https://platform.claude.com/docs/en/build-with-claude/claude-in-microsoft-foundry#hosting-options)。对于 Hosted on Azure 部署，提示词和补全内容保留在 Azure 内；只有使用情况元数据和被 Anthropic 安全系统标记的内容会传输至 Anthropic。对于 Hosted on Anthropic 部署，请求会路由至具有 AES-256 磁盘加密的 Anthropic 基础设施。 |

Claude Code 基于 Anthropic 的 API 构建。有关 API 安全控制（包括 API 日志记录程序）的详细信息，请参阅 [Anthropic 信任中心](https://trust.anthropic.com) 中的合规性文档。

### 云端执行：数据流和依赖项

当使用 [网页版 Claude Code](/docs/en/claude-code-on-the-web)时，会话将在 Anthropic 管理的虚拟机中运行，而不是在本地运行。在云环境中：

* **代码和数据存储：** 您的仓库将被克隆到隔离的虚拟机中。代码和会话数据受您账户类型的保留和使用政策约束（参见上文的保留数据部分）
* **凭据：** GitHub 身份验证通过安全代理处理；您的 GitHub 凭据永远不会进入沙盒
* **网络流量：** 所有出站流量都经过安全代理，以进行审计日志记录和防止滥用
* **会话数据：** 提示词、代码更改和输出遵循与本地 Claude Code 使用相同的数据政策

有关云端执行的安全详细信息，请参见 [安全性](/docs/en/security#cloud-execution-security)。

## 遥测服务

Claude Code 会发送两种类型的操作遥测数据：使用量指标和错误报告。您可以通过下方的环境变量分别关闭它们，或者通过设置 `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` 一次性禁用所有非必要的流量。

**指标**：延迟、可靠性和使用模式，通过 TLS 发送给 Anthropic 和第三方日志基础设施。指标绝不包含您的代码、提示词或文件路径。设置 `DISABLE_TELEMETRY=1` 以选择退出。

**错误报告**：来自 Claude Code 自身内部的错误消息和堆栈跟踪，通过 TLS 发送给第三方错误跟踪服务。在任何数据离开您的机器之前，Claude Code 会对已知的密钥、文件路径、电子邮件地址和其他个人信息的模式进行脱敏处理。设置 `DISABLE_ERROR_REPORTING=1` 以选择退出。

错误报告仅在满足以下所有条件时才会开启：

* 您使用 Claude Pro 或 Max 订阅登录
* 您正在运行 Claude Code v2.1.198 或更高版本
* 您正在直接连接到 Claude API
* 您的组织没有零数据保留协议或 HIPAA 协议

当您运行 `/feedback` 命令时，包含代码的对话历史记录副本将被发送给 Anthropic。`/bug` 和 `/share` 命令通过相同的路径提交。在提交之前，您可以选择包含多少历史记录：仅当前会话（这是默认设置），或者同一项目过去 24 小时或 7 天内的其他会话。数据在传输过程中通过 TLS 加密，并存储在 Google Cloud Storage 中，该服务默认对静态存储数据进行加密。可选地，会在公开仓库中创建一个 GitHub issue。要选择退出，请将 `DISABLE_FEEDBACK_COMMAND` 环境变量设置为 `1`。

当您使用第三方提供商（例如 Amazon Bedrock 或 Google Cloud 的 Agent Platform），或者没有配置 Anthropic 凭据时，`/feedback` 会将报告写入到 `~/.claude/feedback-bundles/` 下的本地存档中，而不是发送给 Anthropic。在写入存档之前，已知的 API 密钥和令牌模式会被脱敏处理。在您将该文件发送给您的 Anthropic 客户代表或将其附加到支持请求之前，任何内容都不会离开您的机器。

## 各 API 提供商的默认行为

默认情况下，在使用 Amazon Bedrock、Google Cloud 的 Agent Platform、Microsoft Foundry 或 AWS 上的 Claude Platform 时，错误报告、遥测和 Bug 报告功能是禁用的。会话质量调查和 WebFetch 域名安全检查是例外情况，无论使用哪个提供商都会运行。在已登录的 [Claude 应用网关](/docs/en/claude-apps-gateway) 会话中，发往 Anthropic 的使用分析、错误报告和调查评分会被网关凭证本身禁用，且没有设置可以重新启用它们。您可以通过设置 `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` 来一次性选择退出所有非必要流量（包括调查）。此变量不会影响 WebFetch 检查或官方插件市场的自动安装；它们各自有自己的退出选项：`skipWebFetchPreflight` 在 [设置](/docs/en/settings) 中用于 WebFetch，以及 `CLAUDE_CODE_DISABLE_OFFICIAL_MARKETPLACE_AUTOINSTALL` 用于插件市场。以下是完整的默认行为：

| 服务                              | Claude API                                                                                            | Google Cloud 的 Agent Platform API                                                      | Amazon Bedrock API                                                                     | Microsoft Foundry API                                                                  | AWS 上的 Claude Platform                                                                 |
| ------------------------------------ | ----------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| **指标**                          | 默认开启。<br />`DISABLE_TELEMETRY=1` 以禁用。                                                    | 默认关闭。<br />`CLAUDE_CODE_USE_VERTEX` 必须为 1。                                  | 默认关闭。<br />`CLAUDE_CODE_USE_BEDROCK` 必须为 1。                                 | 默认关闭。<br />`CLAUDE_CODE_USE_FOUNDRY` 必须为 1。                                 | 默认关闭。<br />`CLAUDE_CODE_USE_ANTHROPIC_AWS` 必须为 1。                           |
| **错误报告**                    | 对于 v2.1.198+ 上的 Pro 和 Max 登录为开启，否则为关闭。<br />`DISABLE_ERROR_REPORTING=1` 以禁用。 | 默认关闭。<br />`CLAUDE_CODE_USE_VERTEX` 必须为 1。                                  | 默认关闭。<br />`CLAUDE_CODE_USE_BEDROCK` 必须为 1。                                 | 默认关闭。<br />`CLAUDE_CODE_USE_FOUNDRY` 必须为 1。                                 | 默认关闭。<br />`CLAUDE_CODE_USE_ANTHROPIC_AWS` 必须为 1。                           |
| **Claude API (`/feedback` 报告)** | 默认开启。<br />`DISABLE_FEEDBACK_COMMAND=1` 以禁用。                                             | 默认关闭。<br />`CLAUDE_CODE_USE_VERTEX` 必须为 1。                                  | 默认关闭。<br />`CLAUDE_CODE_USE_BEDROCK` 必须为 1。                                 | 默认关闭。<br />`CLAUDE_CODE_USE_FOUNDRY` 必须为 1。                                 | 默认关闭。<br />`CLAUDE_CODE_USE_ANTHROPIC_AWS` 必须为 1。                           |
| **会话质量调查**          | 默认开启。<br />`CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY=1` 以禁用。                                  | 默认开启。<br />`CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY=1` 以禁用。                   | 默认开启。<br />`CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY=1` 以禁用。                   | 默认开启。<br />`CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY=1` 以禁用。                   | 默认开启。<br />`CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY=1` 以禁用。                   |
| **WebFetch 域名安全检查**     | 默认开启。<br />`skipWebFetchPreflight: true` 在 [设置](/docs/en/settings) 中禁用。                | 默认开启。<br />`skipWebFetchPreflight: true` 在 [设置](/docs/en/settings) 中禁用。 | 默认开启。<br />`skipWebFetchPreflight: true` 在 [设置](/docs/en/settings) 中禁用。 | 默认开启。<br />`skipWebFetchPreflight: true` 在 [设置](/docs/en/settings) 中禁用。 | 默认开启。<br />`skipWebFetchPreflight: true` 在 [设置](/docs/en/settings) 中禁用。 |

所有环境变量都可以检入到 `settings.json`（见 [设置参考](/docs/en/settings)）。

自 v2.1.126 起，当宿主平台设置 `CLAUDE_CODE_PROVIDER_MANAGED_BY_HOST` 时，Google Cloud 的 Agent Platform、Amazon Bedrock 和 Microsoft Foundry 的指标默认开启，并遵循标准的 `DISABLE_TELEMETRY` 选择退出机制。在这些提供商上，错误报告和 `/feedback` 报告默认保持关闭状态。

### WebFetch 域名安全检查

在获取 URL 之前，WebFetch 工具会将请求的主机名发送给 `api.anthropic.com`，以便根据 Anthropic 维护的安全阻止列表进行检查。仅发送主机名，而不发送完整的 URL、路径或页面内容。结果将按主机名缓存五分钟。

无论您使用哪种模型提供商，此检查都会运行，并且不受 `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` 的影响。如果您的网络阻止了 `api.anthropic.com`，WebFetch 请求将会失败，直到您将该域名加入白名单，或者设置 `skipWebFetchPreflight: true` 于 [设置](/docs/en/settings) 中。禁用此检查意味着 WebFetch 会尝试检索任何 URL 而不查阅黑名单，因此如果您需要限制 Claude 可以访问哪些域名，请将其与 [`WebFetch` 权限规则](/docs/en/permissions#webfetch) 结合使用。

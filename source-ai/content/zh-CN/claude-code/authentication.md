---
title: 身份验证
source_id: claude-code/authentication
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/authentication
owner: Anthropic
content_sha256: 43d151845b84e4aeca9f374a64d081aac2f5b1ea190bc10b4d318832ea2878f7
translation_of: claude-code/authentication
translation_model: k3
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/authentication)

Content owner: Anthropic

> ## 文档索引
> 在以下地址获取完整的文档索引:https://code.claude.com/docs/llms.txt
> 在进一步探索之前,使用此文件来发现所有可用的页面。

# 身份验证

> 登录 Claude Code 并为个人、团队和组织配置身份验证。

Claude Code 根据你的设置支持多种身份验证方法。个人用户可以使用 Claude.ai 帐户登录,而团队可以使用 Claude for Teams 或 Enterprise、Claude Console,或 Amazon Bedrock、Google Cloud 的 Agent Platform、Microsoft Foundry 等云提供商。

## 登录 Claude Code

在[安装 Claude Code](/docs/en/setup#install-claude-code) 之后,在终端中运行 `claude`。首次启动时,Claude Code 会打开一个浏览器窗口供你登录。

如果浏览器没有自动打开,请按 `c` 将登录 URL 复制到剪贴板,然后将其粘贴到浏览器中。

如果你登录后浏览器显示登录码而不是重定向回来,请在终端的 `Paste code here if prompted` 提示符处粘贴该代码。当浏览器无法访问 Claude Code 的本地回调服务器时会发生这种情况,这在 WSL2、SSH 会话和容器中很常见。

登录完成后,终端会显示 `Login successful` 并提示你按 `Enter` 继续。

你可以使用以下任何一种帐户类型进行身份验证:

* **Claude Pro 或 Max 订阅**:使用你的 Claude.ai 帐户登录。在 [claude.com/pricing](https://claude.com/pricing?utm_source=claude_code\&utm_medium=docs\&utm_content=authentication_pro_max) 订阅。
* **Claude for Teams 或 Enterprise**:使用你的团队管理员邀请你的 Claude.ai 帐户登录。
* **Claude Console**:使用你的 Console 凭据登录。你的管理员必须先[邀请你](#claude-console-authentication)。
* **云提供商**:如果你的组织使用 [Amazon Bedrock](/docs/en/amazon-bedrock)、[Google Cloud 的 Agent Platform](/docs/en/google-vertex-ai) 或 [Microsoft Foundry](/docs/en/microsoft-foundry),请在运行 `claude` 之前设置所需的环境变量,或在登录提示符处选择 **3rd-party platform**(第三方平台),这将启动针对 Bedrock 和 Vertex AI 的交互式设置向导。无需浏览器登录。
* **云网关**:如果你的组织运行自托管的 [Claude apps gateway](/docs/en/claude-apps-gateway),请通过 `/login` 使用企业 SSO 登录。网关颁发的令牌是该会话的唯一凭据。

管理员可以限制接受哪些登录方法和组织;请参阅[限制登录到你的组织](#restrict-login-to-your-organization)。

要注销并重新进行身份验证,请在 Claude Code 提示符处输入 `/logout`。注销还会重置你的首次启动设置状态,因此下次运行 `claude` 时,它会再次引导你完成登录和设置。

如果你在登录时遇到问题,请参阅[身份验证故障排除](/docs/en/troubleshoot-install#login-and-authentication)。

## 设置团队身份验证

对于团队和组织,你可以通过以下方式之一配置 Claude Code 访问权限:

* [Claude for Teams 或 Enterprise](#claude-for-teams-or-enterprise),推荐大多数团队使用
* [Claude Console](#claude-console-authentication)
* [Claude apps gateway](/docs/en/claude-apps-gateway),一个自托管网关,使用你的 IdP 让开发人员登录,并将推理路由到你配置的云提供商
* [Amazon Bedrock](/docs/en/amazon-bedrock)
* [Google Cloud 的 Agent Platform](/docs/en/google-vertex-ai)
* [Microsoft Foundry](/docs/en/microsoft-foundry)

### Claude for Teams or Enterprise

[Claude for Teams](https://claude.com/pricing?utm_source=claude_code\&utm_medium=docs\&utm_content=authentication_teams#team-&-enterprise) 和 [Claude for Enterprise](https://anthropic.com/contact-sales?utm_source=claude_code\&utm_medium=docs\&utm_content=authentication_enterprise) 为使用 Claude Code 的组织提供最佳体验。团队成员可以同时访问 Claude Code 和网页版 Claude，并享有集中计费与团队管理功能。

* **Claude for Teams**：自助服务方案，包含协作功能、管理工具和计费管理。最适合小型团队。
* **Claude for Enterprise**：增加了 SSO、域名捕获、基于角色的权限、合规 API，以及组织范围的 Claude Code 配置托管策略设置。最适合具有安全与合规要求的大型组织。

<Steps>
  <Step title="订阅">
    订阅 [Claude for Teams](https://claude.com/pricing?utm_source=claude_code\&utm_medium=docs\&utm_content=authentication_teams_step#team-&-enterprise)，或联系销售了解 [Claude for Enterprise](https://anthropic.com/contact-sales?utm_source=claude_code\&utm_medium=docs\&utm_content=authentication_enterprise_step)。
  </Step>

  <Step title="邀请团队成员">
    从管理控制面板邀请团队成员。
  </Step>

  <Step title="安装并登录">
    团队成员安装 Claude Code 并使用其 Claude.ai 账户登录。
  </Step>
</Steps>

### Claude Console 身份验证

对于偏好基于 API 计费的组织，可以通过 Claude Console 设置访问权限。

<Steps>
  <Step title="创建或使用 Claude Console 账户">
    使用你现有的 Claude Console 账户，或创建一个新账户。
  </Step>

  <Step title="添加用户">
    可以通过以下任一方式添加用户：

    * 在 Claude Console 内批量邀请用户：Settings -> Members -> Invite
    * [设置 SSO](https://support.claude.com/en/articles/13132885-setting-up-single-sign-on-sso)
  </Step>

  <Step title="分配角色">
    邀请用户时，分配以下角色之一：

    * **Claude Code** 角色：用户只能创建 Claude Code API 密钥
    * **Developer** 角色：用户可以创建任何类型的 API 密钥
  </Step>

  <Step title="用户完成设置">
    每位受邀用户需要：

    * 接受 Claude Console 邀请
    * [查看系统要求](/docs/en/setup#system-requirements)
    * [安装 Claude Code](/docs/en/setup#install-claude-code)
    * 使用 Claude Console 账户凭据登录
  </Step>
</Steps>

### 云服务提供商身份验证

对于使用 Amazon Bedrock、Google Cloud 的 Agent Platform 或 Microsoft Foundry 的团队：

<Steps>
  <Step title="按照提供商的设置指南操作">
    参阅 [Amazon Bedrock 文档](/docs/en/amazon-bedrock)、[Google Cloud 的 Agent Platform 文档](/docs/en/google-vertex-ai)或 [Microsoft Foundry 文档](/docs/en/microsoft-foundry)。
  </Step>

  <Step title="分发配置">
    向用户分发环境变量以及生成云凭据的说明。阅读更多关于如何[在此处管理配置](/docs/en/settings)的内容。
  </Step>

  <Step title="安装 Claude Code">
    用户可以[安装 Claude Code](/docs/en/setup#install-claude-code)。
  </Step>
</Steps>

### 限制登录到你的组织

若要要求开发者会话通过特定的 Anthropic 组织进行身份验证，请设置 [`forceLoginMethod` 和 `forceLoginOrgUUID`](/docs/en/settings#available-settings)，设置位置为[托管设置](/docs/en/settings#settings-files)。将 `forceLoginOrgUUID` 设置为你的组织 ID，该 ID 显示在 [claude.ai 管理员设置](https://claude.ai/admin-settings/organization)（适用于 Claude for Teams 或 Enterprise 组织），或显示在 [platform.claude.com/settings/organization](https://platform.claude.com/settings/organization)（适用于 Console 组织）。设置这两个配置键后，Claude Code 会将登录限制为列出的组织，并在启动时退出（如果活动凭据属于其他组织）。

开发者可以通过多种途径登录：终端的 `/login` 流程、[VS Code 扩展](/docs/en/vs-code)、Agent SDK、`claude setup-token`、`/install-github-app`，以及面向通过云网关路由的组织的 [gateway](/docs/en/claude-apps-gateway) 登录。在 Claude Code v2.1.212 或更高版本中，每条途径都会强制执行 `forceLoginMethod`；而在 v2.1.212 之前，只有终端登录会强制执行这两个键中的任意一个。这些途径在 `forceLoginOrgUUID` 的强制执行方式上有所不同：

* **终端、VS Code 扩展和 Agent SDK 登录**：同时强制使用两个配置键
* **`claude setup-token` 和 `/install-github-app`**：仅强制使用 `forceLoginMethod`，这样它们可以在其他组织中颁发令牌
* **[Gateway](/docs/en/claude-apps-gateway) 登录**：由 `forceLoginMethod: "gateway"` 选择，而不是受它限制，并且不会针对 Anthropic 组织进行身份验证，因此 `forceLoginOrgUUID` 不适用；请使用你的网关身份提供商来限制访问

通过你的设备管理工具部署这些配置键。[服务器托管设置](/docs/en/server-managed-settings) 只能触达已通过身份验证登录到你组织的账户，因此无法重定向开发者的首次登录。如果你的组织也分发服务器托管设置，请在两处都设置这些配置键：托管设置来源 [不会合并](/docs/en/server-managed-settings#settings-precedence)，并且缓存的服务器托管设置会完全替换设备托管文件。

这些配置键还会阻止通过 `ANTHROPIC_API_KEY`、`ANTHROPIC_AUTH_TOKEN` 或 `apiKeyHelper` 进行身份验证的会话，因为无法为环境凭据验证组织成员身份。诸如 Amazon Bedrock 等云提供商会话是针对你的云提供商进行身份验证的，不会被阻止；请通过你的云 IAM 策略来限制这些会话。有关完整行为，请参阅设置参考中的 [`forceLoginOrgUUID`](/docs/en/settings#available-settings)。在 v2.1.146 之前，此固定仅适用于登录流程，不会阻止 API 密钥凭据。

## 凭据管理

Claude Code 安全地管理你的身份验证凭据:

* **存储位置**:
  * 在 macOS 上,凭据存储在加密的 macOS 钥匙串中。
  * 在 Linux 上,凭据存储在 `~/.claude/.credentials.json` 中,文件权限为 `0600`。
  * 在 Windows 上,凭据存储在 `%USERPROFILE%\.claude\.credentials.json` 中,并继承你的用户配置文件目录的访问控制,默认情况下将该文件限制为你的用户账户。
  * 如果你在 Linux 或 Windows 上设置了 `CLAUDE_CONFIG_DIR` 环境变量,则 `.credentials.json` 文件将位于该目录下。
  * Claude Code 通过 `/login` 和 `/logout` 管理 `.credentials.json`。若要通过自定义 API 端点路由请求,请改为设置 [`ANTHROPIC_BASE_URL`](/docs/en/env-vars) 环境变量。
* **支持的身份验证类型**:Claude.ai 凭据、Claude API 凭据、Microsoft Foundry Auth、Bedrock Auth、Vertex Auth 以及 [Claude apps gateway](/docs/en/claude-apps-gateway) 会话令牌。
* **自定义凭据脚本**:可以配置 [`apiKeyHelper`](/docs/en/settings#available-settings) 设置来运行一个返回 API 密钥的 shell 脚本。
* **刷新间隔**:默认情况下,`apiKeyHelper` 会在 5 分钟后或收到 HTTP 401 响应时被调用。设置 `CLAUDE_CODE_API_KEY_HELPER_TTL_MS` 环境变量可自定义刷新间隔。
* **缓慢辅助程序提示**:如果 `apiKeyHelper` 返回密钥的时间超过 10 秒,Claude Code 会在提示栏中显示一条警告提示,并显示已用时间。如果你经常看到这样的提示,请检查你的凭据脚本是否可以优化。
* **辅助程序失败**:{/* min-version: 2.1.208 */}当脚本以错误退出、超时或未输出任何内容时,请求会在三次尝试内以 [`Your apiKeyHelper script is failing`](/docs/en/errors#your-apikeyhelper-script-is-failing) 失败。在 v2.1.208 之前,辅助程序失败会在大约十次静默重试后表现为通用的 401 错误。

`apiKeyHelper`、`ANTHROPIC_API_KEY` 和 `ANTHROPIC_AUTH_TOKEN` 适用于 CLI 及封装它的各种界面,包括 VS Code 扩展、Agent SDK 和 GitHub Actions。Claude Desktop 和云端会话不会调用 `apiKeyHelper` 或读取这些环境变量:它们使用 OAuth,但运行 [第三方推理配置](/docs/en/llm-gateway-connect#desktop-app) 的桌面会话除外,这些会话使用该配置的凭据进行身份验证。

### 续订即将过期的登录

当你使用 `/login` 创建的登录距离过期不超过三天时，Claude Code 会在启动时显示警告：`Your login expires in 3 days · run /login to renew`。需要 Claude Code v2.1.203 或更高版本。{/* min-version: 2.1.217 */}在 v2.1.217 之前，警告会在过期前五天出现。

运行 `/login` 进行续订。该警告仅为提示信息，绝不会阻止请求：在登录实际过期之前，身份验证会一直正常工作。登录有效期本身并未改变；v2.1.203 新增的只是提前警告。

{/* min-version: 2.1.206 */}一旦存储的登录过期且无法刷新，每个请求都会失败并报错 [`Login expired · Please run /login`](/docs/en/errors#login-expired)，直到你重新登录。在 v2.1.206 之前，过期的登录会表现为模型错误。

{/* min-version: 2.1.210 */}你可以在请求失败之前检查此状态：[`/status`](/docs/en/commands) 会显示一行 `Login`，内容为 `Expired — log in again`，并附上它为过期登录保存的组织和邮箱。该行仅在已保存的 claude.ai 或 Claude Console 登录是活动凭据时出现。该行需要 Claude Code v2.1.210 或更高版本。

警告仅在 claude.ai 或 Claude Console 登录是活动凭据时出现，而在云提供商、`ANTHROPIC_API_KEY`、`ANTHROPIC_AUTH_TOKEN` 或 `apiKeyHelper` 提供凭据时不会出现。

提前续订对于无人值守运行的会话最为重要。在凭据过期后，一个存活时间超过登录有效期的 [代理视图中的后台会话](/docs/en/agent-view) 或 [远程控制](/docs/en/remote-control) 会话会停止推进，并且在你重新登录之前无法恢复。

### 身份验证优先级

当存在多个凭据时，Claude Code 按以下顺序选择一个：

1. 云提供商凭据，当设置了 `CLAUDE_CODE_USE_BEDROCK`、`CLAUDE_CODE_USE_VERTEX` 或 `CLAUDE_CODE_USE_FOUNDRY` 时。设置方法请参阅 [第三方集成](/docs/en/third-party-integrations)。
2. `ANTHROPIC_AUTH_TOKEN` 环境变量。作为 `Authorization: Bearer` 标头发送。当通过使用持有者令牌而非 Anthropic API 密钥进行身份验证的 [LLM 网关或代理](/docs/en/llm-gateway) 路由时，请使用此项。
3. `ANTHROPIC_API_KEY` 环境变量。作为 `X-Api-Key` 标头发送。使用来自 [Claude Console](https://platform.claude.com) 的密钥直接访问 Anthropic API 时，请使用此项。在交互模式下，系统会提示你一次以批准或拒绝该密钥，你的选择会被记住。以后如需更改，请使用 `/config` 中的“Use custom API key”（使用自定义 API 密钥）开关。该开关仅在环境中设置了 `ANTHROPIC_API_KEY` 时出现。在非交互模式（`-p`）下，只要密钥存在就始终会被使用。
4. [`apiKeyHelper`](/docs/en/settings#available-settings) 脚本输出。用于动态或轮换凭据，例如从保险库获取的短期令牌。
5. `CLAUDE_CODE_OAUTH_TOKEN` 环境变量。由 [`claude setup-token`](#generate-a-long-lived-token) 生成的长效 OAuth 令牌。用于无法使用浏览器登录的 CI 流水线和脚本。
6. 来自 `/login` 的订阅 OAuth 凭据。这是 Claude Pro、Max、Team 和 Enterprise 用户的默认选项。

已登录的 [Claude apps gateway](/docs/en/claude-apps-gateway) 会话不在此列表之内：它是类似 Amazon Bedrock 或 Google Cloud Agent Platform 的提供商选择，并且优先级高于它们。当存在网关会话时，即使设置了 `CLAUDE_CODE_USE_BEDROCK`、`CLAUDE_CODE_USE_VERTEX` 或 `CLAUDE_CODE_USE_FOUNDRY`，CLI 也会使用网关令牌进行身份验证，上述持有者令牌、API 密钥和 `apiKeyHelper` 条目均不会被使用。

如果你拥有有效的 Claude 订阅，但环境中也设置了 `ANTHROPIC_API_KEY`，那么 API 密钥一经批准就会优先生效。如果该密钥属于已禁用或过期的组织，可能会导致身份验证失败。运行 `unset ANTHROPIC_API_KEY` 可回退到你的订阅，并查看 `/status` 以确认当前生效的是哪种方式。`Login method` 行显示你的订阅账户，而使用 API 密钥时会出现 `API key` 行。

[Claude Code on the Web](/docs/en/claude-code-on-the-web) 始终使用你的订阅凭据。如果你在沙盒环境中设置 `ANTHROPIC_API_KEY` 或 `ANTHROPIC_AUTH_TOKEN`，它不会覆盖你的订阅凭据。

### 生成长期有效的令牌

对于 CI 流水线、脚本或其他无法进行交互式浏览器登录的环境，请使用 `claude setup-token` 生成一年期 OAuth 令牌：

```bash theme={null}
claude setup-token
```

该命令会打开与 `/login` 相同的浏览器授权流程，你在浏览器中批准访问后，令牌会打印到终端。它不会将令牌保存到任何位置；请复制该令牌，并在需要身份验证的位置将其设置为 `CLAUDE_CODE_OAUTH_TOKEN` 环境变量：

```bash theme={null}
export CLAUDE_CODE_OAUTH_TOKEN=your-token
```

此令牌使用你的 Claude 订阅进行身份验证，并需要 Pro、Max、Team 或 Enterprise 套餐。它只能发起模型请求，因此无法建立 [远程控制](/docs/en/remote-control) 会话，也无法获取 [claude.ai 连接器](/docs/en/mcp#use-mcp-servers-from-claude-ai)。你在本地配置的 MCP 服务器仍可正常工作。

[裸模式](/docs/en/headless#start-faster-with-bare-mode) 不会读取 `CLAUDE_CODE_OAUTH_TOKEN`。如果你的脚本传递了 `--bare`，请改用 `ANTHROPIC_API_KEY` 或 `apiKeyHelper` 进行身份验证。

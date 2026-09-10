---
title: Claude 应用网关部署与运维
source_id: claude-code/claude-apps-gateway-deploy
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/claude-apps-gateway-deploy
owner: Anthropic
content_sha256: c549e8d9219d64c281c13e2a41f27a4bcd6380295a8541a887a4a24cd8f9e361
translation_of: claude-code/claude-apps-gateway-deploy
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/claude-apps-gateway-deploy)

Content owner: Anthropic

> ## 文档索引
> 在以下位置获取完整的文档索引：https://code.claude.com/docs/llms.txt
> 在进一步探索之前，请使用此文件来发现所有可用页面。

# Claude 应用网关部署与运维

> 将网关注册到您的 IdP，构建容器，部署在 Kubernetes 或 Cloud Run 上，并进行运维：健康检查、密钥轮换、升级和安全性。

本页面涵盖了运行 [Claude apps gateway](/docs/en/claude-apps-gateway)的运维方面：在您的身份提供商中注册 OAuth 客户端，将网关部署为容器，并进行日常运行。有关网关启动时读取的 `gateway.yaml` 文件中的每个选项，请参见 [配置参考](/docs/en/claude-apps-gateway-config)。

生产部署按顺序分为四个步骤，以下各节与之对应。前两个步骤是您需要做出选择的地方；后两个是运行后可供查阅的参考资料。

1. [设置您的身份提供商](#identity-provider-setup)：注册 OAuth 客户端并查看有关 Okta、Entra 和 Google 的各 IdP 注意事项
2. [部署网关](#deployment)：构建固定版本的容器镜像，并在 Kubernetes、Cloud Run 或您自己的平台上运行它。本节还涵盖成本、绕过、多网关和无服务器决策
3. [设置运维](#operations)：日志、健康探针、宕机行为、密钥轮换和升级。供您设置监控和运行手册时参考
4. [审查安全态势](#security)：数据流向何处、威胁模型和合规性解答。供安全审查时参考

如果在此过程中登录或启动失败，请直接前往 [故障排除](#troubleshooting)，该部分是根据您看到的错误进行索引的。

<Note>
  **在您的私有网络上部署。** Claude Code 仅连接到地址为私有的网关。这是一个安全防护措施，因为受信任的网关可以推送在开发人员机器上运行命令的设置。将您部署的网关置于内部负载均衡器或 VPN 之后，并为其提供一个仅解析为私有 IP 的主机名。

  Anthropic 运营的公共网关端点是例外情况：`/login` 通过 `https://` 接受它们。这是一小部分由 Anthropic 自己运营的固定网关；它们不是您可以选择或配置的部署选项。该列表已编译到 Claude Code 中，因此任何配置都无法向其中添加主机名，并且您托管的任何网关都不符合此豁免条件。 {/* min-version: 2.1.206 */}在 v2.1.206 之前，`/login` 像拒绝任何其他公共地址一样拒绝这些端点。
</Note>

## 身份提供商设置

注册一个机密 OAuth/OpenID Connect (OIDC) Web 应用程序，使用单个重定向 URI `https://<gateway>/oauth/callback`，并将其分配给应具有网关访问权限的用户或组。

任何兼容 OIDC 的 IdP 均可使用：Okta、Microsoft Entra ID、Google Workspace、Keycloak、Dex、PingFederate 等。IdP 必须满足三个要求：

* 在生产环境中通过 HTTPS 提供 `/.well-known/openid-configuration`；网关接受 [`http://` 签发者](/docs/en/claude-apps-gateway-config#oidc)，而回环签发者还需要 `CLAUDE_GATEWAY_ALLOW_LOOPBACK=1`
* 支持授权码流程。PKCE（代码交换证明密钥）默认开启；对于不支持它的 IdP，使用 `oidc.use_pkce: false` 禁用它
* 在 id\_token 中返回 `email` 和可选的 `groups`，或者通过 userinfo 端点使用 `oidc.userinfo_fallback: true` 提供它们

对于私有 PKI，设置 `oidc.ca_cert_pem`。

部分提供商对电子邮件和组声明的处理方式有所不同：

* **Okta**：位于 `https://example.okta.com` 的组织授权服务器返回一个精简的 id\_token，其中省略了 `email` 和 `groups`，因此每当您将其用作 `issuer` 时，请设置 `oidc.userinfo_fallback: true`。自定义授权服务器（例如 `https://example.okta.com/oauth2/default`）在 id\_token 中包含 `email` 和可选的 `groups`，会直接发出它们，无需回退。Okta 仅当在 `oidc.scopes` 中请求了 `groups` 范围且应用程序的组声明过滤器允许时，才会发出 `groups`；`userinfo_fallback` 无法填充未向 IdP 请求的声明。
* **Microsoft Entra ID**：`issuer` = `https://login.microsoftonline.com/<tenant-id>/v2.0`。Entra 发出的是组对象 ID 而非名称，因此请在 `managed.policies.match.groups` 中使用 GUID，或使用应用程序角色获取人类可读的名称。如果您的租户在 `roles` 下而非 `groups` 下发出角色，请设置 `oidc.groups_claim: roles`。
* **Google Workspace**：`issuer` = `https://accounts.google.com`。Google 的 id\_token 不包含组。要以 Google 作为 IdP 使用基于组的 `allowed_groups` 或 `managed.policies`，请配置 [`oidc.google_groups`](/docs/en/claude-apps-gateway-config#oidc)，它通过 Admin SDK Directory API 使用具有全域委派权限的服务帐号来查找每个用户的组。若不进行此配置，请使用 `oidc.allowed_email_domains` 进行成员资格控制，使用 `managed.policies.match.email_domain` 进行策略分配。Google 还会忽略标准的 `offline_access` 范围。对于刷新令牌，请设置 `oidc.scopes: [openid, profile, email]` 和 `oidc.extra_auth_params: { access_type: offline, prompt: consent }`。

有关上述未涵盖的身份提供商的支持，请参阅 [故障排除](#troubleshooting)。

<Warning>
  刷新令牌允许网关静默续订开发者的会话，无需将开发者重定向回浏览器。它们还驱动取消配置流程，因为当 IdP 禁用某个用户时，下次刷新将失败，会话将在 `ttl_hours` 内结束。网关默认请求 `offline_access` 以获取刷新令牌。如果您的 IdP 要求对离线访问进行明确同意，请配置 OAuth 客户端以允许它。

  如果您的 IdP 完全无法发出刷新令牌，网关仍然可以工作，但没有静默续订功能，因此开发者在其会话过期时需要重新进行浏览器登录。为了避免每小时都发生这种情况，请将 [`session.ttl_hours`](/docs/en/claude-apps-gateway-config#session) 提高到 `8` 或 `12`。权衡之处在于取消配置的延迟增加，因为如果没有刷新令牌，被禁用的用户将持续拥有访问权限，直到较长的 TTL 到期。
</Warning>

## 部署

网关是一个单一的 Linux 二进制文件。由于副本是无状态的，并且 Postgres 是共享协调层，因此它可以进行水平扩展。按照您在环境中运行无状态服务的方式来运行它即可。本节的其余部分说明了该镜像的需求，并附带了针对 Kubernetes 和 Cloud Run 的简短说明。

网关被设计为在您的网络内部运行，因为它持有您的上游凭据，并充当推理的单一出口点。它可以运行在您的开发人员和您的 IdP 能够通过 HTTPS 访问的任何地方；请像对待持有生产凭据的任何其他服务一样对待它。

除了运行位置之外，还有几个决定会影响部署：

* **成本**：网关没有单独的许可证或按席位收费；它是 `claude` 二进制文件的一部分。您需要通过现有的云或 Anthropic 承诺支付推理费用，外加容器和遥测收集器的计算资源费用。
* **绕过**：网关并未强制要求访问模型的唯一路由必须经过它。拥有自身凭证的开发者仍然可以直接调用提供商，因此关闭该路径是一项网络策略决策，例如阻止除网关外发往 `api.anthropic.com` 的出口流量。阻止该出口流量还会破坏 [WebFetch 域名安全检查](/docs/en/data-usage#webfetch-domain-safety-check), 这会从每台开发者的机器上调用 `api.anthropic.com` ；在托管策略中设置 `skipWebFetchPreflight: true` 以禁用它。
* **多网关**：每个网关都是一个具有自身配置的独立部署。CLI 会按网关主机名存储其信任指纹和凭据，因此不同团队可以连接到不同的网关而互不冲突。要服务多个 OIDC 颁发者，请运行独立的实例。
* **无服务器**：Cloud Run 可用；设置 `min-instances: 1` 以避免冷 OIDC 发现。Lambda 和 Cloud Functions 不行，因为网关是一个长期运行的 HTTP 服务器。

这里的每个生产拓扑都会在纯 HTTP 副本前面放置一个 L7 代理，例如 Ingress、Cloud Run 的前端或 ALB。将 [`listen.trusted_proxies`](/docs/en/claude-apps-gateway-config#listen) 设置为代理的源范围，以便网关从 `X-Forwarded-For` 读取客户端 IP。网关仅在 TCP 对等端受信任时才会处理该标头；[Google Cloud 实战示例](/docs/en/claude-apps-gateway-on-gcp) 包含针对每种拓扑的具体值。如果没有受信任的代理，每个请求似乎都来自代理的 IP，这会使得按 IP 的速率限制合并到一个共享桶中，并在审计事件中记录代理的 IP。

### 容器镜像

围绕标准 `claude` 版本中的原生 Claude Code 二进制文件构建你自己的镜像：

1. 从固定版本的发布中下载适用于您的镜像架构的 Linux 构建版本；请参阅 [安装特定版本](/docs/en/setup#install-a-specific-version) 以获取下载 URL。
2. 根据该发布的 GPG 签名的 `manifest.json` 对其进行验证，如 [二进制完整性与代码签名](/docs/en/setup#binary-integrity-and-code-signing) 中所述。
3. 将其复制到构建上下文中。

如果您的构建无法访问发布主机，请将发布版本镜像同步到您的内部镜像仓库，并锁定您的机群所运行的版本。

除了二进制之外，镜像需要：

* **一个基于 glibc 的镜像**：glibc 构建版本的唯一动态依赖项是 glibc 库。基于 Musl 的镜像需要 `linux-x64-musl` 或 `linux-arm64-musl` 构建版本以及额外的包；请参见 [Alpine Linux 设置](/docs/en/setup#alpine-linux-and-musl-based-distributions)。
* **一个可写的状态目录**：网关以任何用户身份运行，但最小化镜像没有可写的家目录。将 `CLAUDE_CONFIG_DIR` 设置为可写路径，例如 `/tmp/.claude`。
* **容器命令**：`claude gateway --config /etc/claude/gateway.yaml`，配置文件以只读方式挂载，密钥通过环境变量提供；网关监听 `listen.port`，默认为 `8080`。

### Kubernetes

像任何无状态服务一样，将网关作为 Deployment 运行：

* 从 ConfigMap 挂载配置并从 Secret 挂载机密；通过 `${file:/path/to/secret}` 或作为环境变量在 YAML 中引用机密
* 在 Ingress 处终止 TLS 并将 `listen.public_url` 设置为 Ingress 主机名
* 将就绪探针指向 `GET /readyz`，并将存活探针指向 `GET /healthz`

<Note>
  **工作负载身份**

相较于静态密钥，优先使用平台的工作负载身份：对于 AWS 上的 Amazon Bedrock 和 Claude Platform 使用 EKS 上的 IRSA，对于 Google Cloud 的 Agent Platform 使用 GKE 上的工作负载身份，对于 Microsoft Foundry 使用 AKS 上的工作负载身份。在上游块中设置 `auth: {}`，或为 Microsoft Foundry 设置 `use_azure_ad: true`，网关将通过该提供商的默认凭证链获取 Pod 的身份。对于跨云配对，例如 GKE 上的 Amazon Bedrock 上游，请在 upstream 的 `auth` 块中设置显式凭证。该 [`upstreams` 参考](/docs/en/claude-apps-gateway-config#upstreams) 包含各平台的设置详情。
</Note>

### Cloud Run

按如下方式配置该服务：

* 保持 `listen.port` 为其默认值 `8080`，这与 Cloud Run 的默认 `PORT` 相匹配，或者设置 `port: ${PORT}`
* 将 `public_url` 设置为外部可访问的源。对于生产环境，这通常是内部负载均衡器的主机名，因为 `/login` [拒绝公共地址](/docs/en/claude-apps-gateway#prerequisites)，并且 `*.run.app` URL 会解析为公共地址，因此单独的 Cloud Run URL 仅适用于 `curl` 或浏览器冒烟测试。例外情况是 `*.run.app` 通过 Private Service Connect 和 Cloud DNS 私有区域进行私有解析的网络；在这种拓扑结构中，Cloud Run URL 是一个有效的 `public_url`。[Google Cloud 实战示例](/docs/en/claude-apps-gateway-on-gcp#deploy-the-gateway) 涵盖了这两种情况。
* 将配置作为密钥卷挂载
* 设置 `min-instances: 1` 以避免首次请求时进行冷启动 OIDC 发现

<Note>
  有关涵盖 Cloud Run 或 GKE、Cloud SQL 和 Secret Manager 的 Google Cloud 完整实战示例，请参见 [在 Google Cloud 上部署](/docs/en/claude-apps-gateway-on-gcp)。
</Note>

### 将网关 URL 推送到开发者计算机

一旦网关开始提供服务，请通过托管设置（通过 MDM 或直接写入特定操作系统的 `managed-settings.json`），将 `forceLoginMethod`、`forceLoginGatewayUrl` 和 `parentSettingsBehavior: "merge"` 推送到每位开发者的计算机上。如果没有此操作，`/login` 将显示标准帐户选择器，且没有网关选项。参见 [客户端托管设置](/docs/en/claude-apps-gateway-config#client-side-managed-settings) 用于文件路径和 Claude Desktop `bootstrapUrl` 等效配置。

## 运维

一旦网关开始处理流量，日常操作就是读取其日志、探测其健康状况，并按您的计划轮换其密钥。以下小节将涵盖上述每一项，以及 Postgres 保存的内容以及升级和回滚的行为。

### 日志

网关向 stderr 写入两个流，两者均兼容 JSON 格式：

* **审计事件**：每个与安全相关的事件对应单行 JSON。将 stderr 通过管道传输到您的日志聚合器。触发的事件包括 `config.load`、`session.mint`、`session.refresh`、`device.authorize`、`device.verify`、`auth.denied`、`access.denied`、`inference`、`managed.serve`、`desktop_bootstrap.serve`、`desktop_bootstrap.denied`、`spend.blocked` 和 `admin.denied`。字段因事件而异：
  * 成功的生成与刷新事件包含 `sub`、`email`、`client_ip` 和结果
  * `auth.denied` 和 `access.denied` 包含原因和客户端 IP，以及 `auth.denied` 的请求路径，因为在这些拒绝发生时尚不存在用户身份
  * `inference` 记录是哪个上游服务了该请求以及响应状态
  * `desktop_bootstrap.denied` 记录被拒绝的 Claude Desktop 引导获取请求及其原因（`not_configured`、`policy_not_opted_in` 或 `no_policy_matched`）以及用户身份
  * `admin.denied` 记录被拒绝的管理 API 身份验证尝试及其原因（`invalid_key` 或 `no_credentials`）、客户端 IP、方法和路径，但不包含提供的密钥材料
* **操作日志**：带有 `[gateway]` 前缀的易读行，用于启动、警告和上游错误。`CLAUDE_GATEWAY_LOG_LEVEL` 环境变量控制详细程度，接受 `info`、`warn` 或 `error`，默认为 `info`。它不影响审计事件，审计事件始终会触发。

### 健康状态

网关将 `GET /healthz` 用作存活探针，将 `GET /readyz` 用作就绪探针；`/readyz` 验证存储是否可达。两者均免受 `access_control.allow_cidrs` 限制，因此探针在处于锁定状态的监听器上仍能继续工作。

`/.well-known/oauth-authorization-server` 处的 OAuth 发现文档仅在配置加载、OIDC 发现、上游客户端构建和 Postgres 迁移全部成功后才返回 `200`，因此它也可兼作端到端的启动检查。

运行中的网关还会在 `<public_url>/protocol` 处提供其接受的路径和请求格式的描述，并与您正在运行的版本相匹配。其内容在不同版本间不稳定。

### 宕机行为

如果 Postgres 宕机，网关本身会继续为已登录的开发者提供服务，但新的登录将会失败。开发者是否确实能继续工作取决于您的编排器如何处理就绪状态：

* **现有会话**：Bearer 令牌使用 JWT 密钥在本地进行验证，会话刷新不会访问存储，并且网关进程仍然可以提供推理服务
* **新登录**：在 Postgres 恢复之前会失败，因为设备流程及其速率限制计数器存在于 Postgres 中
* **[支出限额执行](/docs/en/claude-apps-gateway-spend-limits#postgres-availability)**：在宕机期间默认失效放行，因此推理仍可继续；如果您宁愿阻止运行也不愿在未计量的情况下运行，可将其切换为失效闭锁
* **就绪状态**：`/readyz` 在宕机期间报告未就绪，因此基于就绪状态控制流量的编排器会立即将所有副本从轮换中移除。在该拓扑结构中，所有的流量（包括网关仍能提供的推理服务）都会在负载均衡器上失败，直到 Postgres 恢复。`/healthz` 上的存活探针会继续通过，因此副本不会重启。如果您希望已登录的开发者在存储宕机期间能够继续工作，请将就绪探针指向 `/healthz`；代价是新的登录会在仍然报告就绪的副本上失败。

如果您的 IdP 宕机，现有会话将持续工作直到 `ttl_hours`，并且新的登录和刷新将会失败。如果您的 IdP 经常有维护窗口，请设置更长的 `ttl_hours`。

### JWT 密钥轮换

分三步轮换签名密钥，以使现有会话保持有效：

1. 生成一个新密钥。将其添加到 `session.jwt_secret` 数组的前面。
2. 滚动部署。新令牌使用新密钥签名；旧令牌仍然可以通过验证。
3. 在 `ttl_hours` 加上余量之后，移除旧密钥并再次滚动。

轮换也是在会话过期前强制其退出的唯一方法：Bearer 令牌针对 JWT 密钥进行本地验证，因此不存在按会话撤销。直接替换密钥，而不将旧密钥保留在数组中，会立即使所有尚未过期的会话失效。对于单个人员离职，请在您的 IdP 中取消配置该用户；他们的会话将在 `ttl_hours` 内结束。

### Postgres

网关包含五个表，均由其启动时的迁移创建：

| 表              | 内容                                                                      | 保留期                                                       |
| ------------------ | ----------------------------------------------------------------------------- | --------------------------------------------------------------- |
| `kv`               | 设备授权（10 分钟 TTL）和速率限制计数器                         | 每行 TTL                                                     |
| `spend`            | 每个主体本期截至目前的花费计数器，单位为分                         | `admin.spend_retention_months`，默认 13                      |
| `spend_limits`     | 配置的花费上限                                                         | 直到通过 API 删除                                       |
| `admin_audit`      | 管理 API 变更记录                                                      | `admin.audit_retention_days`，默认 365                       |
| `principal_emails` | 每个主体最后记录的电子邮件、显示名称和 IdP 组。包含 PII。 | `admin.identity_retention_days` 自上次活动起，默认 90 |

一个 30 秒的循环会使超过 TTL 的 `kv` 行过期，而每小时一次的清理会强制执行花费表上的保留时间窗口，因此没有任何东西会无限制地增长。如果没有配置 [支出限额](/docs/en/claude-apps-gateway-spend-limits)，则只会写入 `kv`。如果您的安全策略禁止应用程序角色执行 DDL，请使用管理员角色预创建这些表和 `_migrations`，并授予应用角色对每个对象的 `SELECT, INSERT, UPDATE, DELETE` 权限。

在使用支出限额的情况下，丢失数据库意味着丢失花费跟踪和上限，而不仅仅是开发人员需要重新登录，因此请定期进行备份。为了立即清除已离职的开发人员而不必等待保留期到期，请直接运行 `DELETE FROM principal_emails WHERE principal = '<sub>'`；这将删除唯一包含其电子邮件、姓名和组的表。`spend` 和 `admin_audit` 行仅引用化名的 OIDC `sub`。

### 升级

副本是无状态的，因此随时进行滚动重启都是安全的。网关在启动时运行模式迁移，这意味着部署新二进制文件会自动迁移数据库。如果数据库角色无法运行 DDL，请预创建模式，包括种子化到当前版本的 `_migrations` 表；否则启动时尝试 `CREATE TABLE` 将会失败。

迁移是仅追加的，因此回滚到了解较少迁移的先前二进制文件是安全的；它会忽略额外的行。回滚还会根据较旧二进制文件的模式重新验证 YAML，因此如果配置采用了较新版本引入的键，在较旧版本上启动将会失败。请在回滚之前移除新的键。

因为您在自己的镜像中固定了网关的版本，所以新的 Claude Code 版本中的修复（包括安全修复）只有在您更新固定版本并重新部署时才会到达您的部署环境。请将网关纳入与其他持有生产凭据的服务相同的修补节奏中。

## 安全

本部分解答了安全审查中提出的问题：哪些数据会流经网关以及流向何处，该设计可防御哪些攻击，以及哪些答案应包含在合规调查问卷中。

### 数据流

| 数据                                                                                              | 路径                                                         | 由网关发送至 Anthropic                   |
| ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ | -------------------------------------------------- |
| 推理（提示词、补全）                                                                  | CLI → 网关 → 您的上游                                | 仅当 Anthropic API 是已配置的上游时 |
| 遥测（OTLP 指标，加上 [选择启用的日志和追踪](/docs/en/claude-apps-gateway-config#telemetry)) | CLI → 网关 → 您的收集器                               | 从不                                              |
| 身份（电子邮件、组、sub）                                                                     | IdP → 网关 → JWT → CLI；CLI 将其加盖到 OTLP 导出中 | 从不                                              |
| 托管设置                                                                                  | 您的网关 YAML → CLI                                      | 从不                                              |
| 审计日志                                                                                         | 网关 stderr → 您的聚合器                             | 从不                                              |

### 威胁模型摘要

网关位于您的网络边界内，但单个开发者的笔记本电脑并不被视为受信任的。设计通过以下三种方式考虑到了这一点：

* 开发者持有的是短期的 JWT，而不是原始的上游密钥。CLI 到网关的这一段使用 RFC 8628 设备授权，并且网关与 IdP 的授权码交换在默认配置下运行 PKCE，因此截获的 IdP 授权码是无用的。
* 设备验证页面强制执行同源 POST 和基于每个 IP 的速率限制，符合 RFC 8628 §5.1 的规定。参见 [用户代码暴力破解抗性](#user-code-brute-force-resistance)。
* 出站请求会经过服务器端请求伪造（SSRF）防护，该防护会解析 DNS，默认阻止链路本地地址、云元数据地址以及环回地址，并将连接固定到已解析的 IP，因此受操作者影响的 URL（如 IdP 和 OTLP 目标）无法被重定向到云元数据端点。RFC 1918 私有地址范围被故意允许，因为 IdP 和 OTLP 收集器通常位于私有 IP 上。若要在本地开发中针对环回 IdP 或收集器进行测试，请在网关环境中设置 `CLAUDE_GATEWAY_ALLOW_LOOPBACK=1`；在生产环境中请勿设置。

如果您添加了自己的出口控制，则每当网关使用实例元数据凭证（例如工作负载身份）时，它都必须能够访问元数据服务器。

有两项威胁不在范围之内，因为它们是您需要保护的基础设施：

* **被入侵的网关主机**：该主机既持有上游凭证，又向每个连接的开发者分发 [托管设置](/docs/en/claude-apps-gateway-config#managed)，因此对网关配置的控制权相当于对您 MDM（移动设备管理）的控制权。对于具有 Shell 功能的设置，CLI 的一次性批准对话框限制了静默更改，但不能替代主机安全。
* **恶意的 OIDC 提供商**：提供商签署网关信任的 id\_tokens，因此它可以断言任何身份。审查和保护您的 IdP 是您的责任。

### 用户代码暴力破解抗性

开发者在 `/device` 验证页面上输入的 `user_code` 是从 20 个字符的字母表中提取的 8 个字符，这会产生 20⁸ 或大约 2.56×10¹⁰ 种组合，并且它会在 10 分钟后过期。

网关对设备授权端点应用基于 IP 的速率限制，可通过 [`rate_limits`](/docs/en/claude-apps-gateway-config#http-tuning) 进行配置。如果有许多开发者从单个共享的企业 NAT 地址登录，请提高限制上限。这些限制仅适用于登录流程，而不适用于推理。

### 合规态势

* **数据驻留**：网关自身的数据平面不会向 Anthropic 发送任何内容，除非配置了以 Anthropic API 作为上游；在此情况下，您现有的数据处理协议将适用于推理路径。遥测、审计、身份和设置仅会发送到您配置的目的地。
* **宿主进程流量**：宿主进程是 Claude Code CLI，它可以将启动分析数据和更新检查发送给 Anthropic。对于严格控制出站流量的部署，请在网关的容器环境中设置 `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1`。
* **客户端分析**：CLI 在登录到网关时会禁用其自身的使用情况分析，并且在第三方 API 接口上默认关闭错误报告。
* **客户端计算机**：除非设置了 `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` 和 `skipWebFetchPreflight: true`，否则开发者的 CLI 仍会将 WebFetch 主机名检查和版本检查发送给 Anthropic。请参阅 [数据使用](/docs/en/data-usage)。
* **调查评分**：网关凭证会禁用绑定到 Anthropic 的评分接收器，因此评分不会被发送给 Anthropic。
* **对话记录共享**：在调查的对话记录共享提示中选择“是”，会在 `~/.claude/feedback-bundles/` 下写入一个本地文件，而不是上传给 Anthropic。
* **客户端更新**：更新检查独立于网关流量。通过您自己的分发渠道锁定版本，如果笔记本电脑绝对不能获取发布版本，请设置 `DISABLE_UPDATES`。`DISABLE_AUTOUPDATER` 仅停止后台更新，而 `claude update` 仍然有效。
* **TLS**：在生产环境中通过 HTTPS 提供 `public_url` 服务，可以通过 `listen.tls` 从网关自身的监听器提供，或者在设置了 `listen.public_url` 的纯 HTTP 副本前方的 TLS 终结入口处提供。网关不会拒绝纯 HTTP。IdP 在生产环境中必须提供 HTTPS 服务，并且 Postgres 支持 `?sslmode=require`。在您的入口处设置 `Strict-Transport-Security`。
* **漏洞披露**：遵循 [报告安全问题](/docs/en/security#reporting-security-issues)

## 故障排除

如有疑问和反馈，请使用 [Claude Code 支持](https://support.claude.com/en/collections/14445694-claude-code)，或者在 [Claude Code GitHub 仓库](https://github.com/anthropics/claude-code/issues) 中提交问题。报告问题时，请包括：

* **网关问题**：相关时间窗口内的网关 stderr，你的已脱敏的 `gateway.yaml`，网关版本（显示在 `/` 的着陆页和 `/managed/settings` 的 `x-cc-gateway-version` 响应头中），以及最近的变更
* **登录问题**：开发者运行 `claude --debug-file ./claude-debug.txt`，复现问题，并发送该文件以及相同时间窗口内的网关审计日志
* **推理问题**：请求的模型、配置的上游，以及该请求的网关审计日志（记录了是由哪个上游提供服务以及响应状态）

网关的 stderr 包含审计事件流，审计日志记录开发者身份，调试文件记录来自开发者机器的 hook 和 MCP 服务器输出。在发布到公开问题之前，请检查并对这些内容进行脱敏处理。

| 症状                                                                                                                                                                     | 原因                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | 修复                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 开发者的 `/login` 显示标准账户选择器，而不是 **Cloud gateway** 屏幕                                                                            | `forceLoginMethod` 或 `forceLoginGatewayUrl` 未在该机器的托管设置中设置                                                                                                                                                                                                                                                                                                                                                                                                                                                         | 将 [托管设置文件](/docs/en/claude-apps-gateway#set-the-gateway-url) 部署到设备；`/login` 会从中读取网关 URL                                                                                                                                                                                                                                                                                                |
| Claude Desktop 报告无法获取其引导配置                                                                                                 | `/user/bootstrap` 返回 404：与用户匹配的策略不包含 `desktop` 键，或者没有策略匹配。网关的审计日志将每次拒绝记录为 `desktop_bootstrap.denied` 并附带原因。                                                                                                                                                                                                                                                                                                                                    | 在与用户匹配的策略或 `match: {}` 基础层中添加一个 `desktop` 块；一个空的 `desktop: {}` 就足够了。请参阅 [Claude Desktop 覆盖层](/docs/en/claude-apps-gateway-config#claude-desktop-overlay)。                                                                                                                                                                                                                      |
| 启动时显示 `Gateway login is configured in managed settings, but this Claude Code build does not include Cloud gateway support.`                                         | 安装的 Claude Code 构建版本早于网关支持                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | 让开发者将 Claude Code 更新到包含 Cloud gateway 支持的版本                                                                                                                                                                                                                                                                                                                                                  |
| CLI `/login`: `Gateway hosts must be on your organization's private network; <host> resolves to the public (or unrecognized) address <ip>`                                  | 网关主机名解析为至少一个公共 IP 地址。Claude Code 检查每个解析到的地址，并要求每一个都是私有地址。常见原因是双栈名称中有一个地址族解析为公共地址，包括返回公共范围 AAAA 地址的 AWS 内部双栈负载均衡器。{/* min-version: 2.1.206 */}Anthropic 运营的公共网关端点免除此检查，并且 `/login` 通过 `https://` 接受它们。在 v2.1.206 之前，`/login` 会像对待任何其他公共地址一样拒绝它们 | 让网关名称在开发者机器上仅解析为私有地址。对于双栈名称，请丢弃公共范围记录或提供一个单独的仅限内部的 DNS 名称。参见 [私有网络前提条件](/docs/en/claude-apps-gateway#prerequisites)。                                                                                                                                                                           |
| CLI `/login`: `Gateway login requires a direct connection and does not support connecting through an HTTP proxy`                                                            | 一个 `HTTPS_PROXY` 或 `HTTP_PROXY` 应用于网关主机，并且代理的主机名解析为公共地址。允许其主机仅解析为私有地址的代理，并且不会触发此错误                                                                                                                                                                                                                                                                                                                                | 将网关主机添加到开发者机器上的 `NO_PROXY` 中以便直接连接，或者使用主机名解析为私有地址的代理                                                                                                                                                                                                                                                                                  |
| CLI `/login`: `Could not resolve gateway host <host>`                                                                                                                       | 机器无法解析网关的内部 DNS 名称，通常是因为它不在企业网络上                                                                                                                                                                                                                                                                                                                                                                                                                                     | 让开发者连接到您的网络或 VPN，然后重试 `/login`                                                                                                                                                                                                                                                                                                                                                                  |
| 启动退出并报配置验证错误，指明 `store.postgres_url`                                                                                                       | 未配置 Postgres；网关需要 Postgres                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | 设置 `store.postgres_url`。对于本地开发，请使用一次性容器：`docker run --rm -p 5432:5432 -e POSTGRES_HOST_AUTH_METHOD=trust postgres`.                                                                                                                                                                                                                                                                                 |
| 启动退出：`requires the native binary`                                                                                                                                    | 在 Node 下运行而不是原生二进制文件                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | 安装 Claude Code，使用其中一种 [独立安装方法](/docs/en/setup)                                                                                                                                                                                                                                                                                                                                                             |
| 启动在 `config.load` 之后退出并报 OIDC 发现错误                                                                                                                 | `oidc.issuer` 无法访问，或者 TLS 证书链不受信任                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | 检查是否可以从 Pod 访问发行者并提供 `/.well-known/openid-configuration`。设置 `ca_cert_pem` 用于私有 PKI。                                                                                                                                                                                                                                                                                                           |
| 启动时退出并出现 Postgres 权限错误                                                                                                                                 | App 角色缺少 `CREATE TABLE`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | 使用管理员角色预先创建模式并向 App 角色授予 DML 权限，或者在执行新迁移的启动过程中临时授予 DDL 权限                                                                                                                                                                                                                                                                                                    |
| `/oauth/callback` 显示“无法完成登录”                                                                                                                    | 邮箱域名被拒绝、id\_token 验证失败，或者 `email_verified` 显式为 `false`，网关将始终拒绝且无法覆盖                                                                                                                                                                                                                                                                                                                                                                                                   | 检查 `allowed_email_domains` 以及 IdP 是否返回了经过验证的 `email` 声明。对于 `email_verified: false`，请修复 IdP 侧的验证。如果您的 IdP 在不同的声明名称下发送电子邮件，请设置 `oidc.email_claim`。                                                                                                                                                                                                              |
| 日志： `token exchange failed: id_token missing email claim`                                                                                                                  | IdP 默认不在 id\_token 中包含 `email`。此拒绝仅在设置了 `allowed_email_domains` 时触发；若未设置，缺失的电子邮件将生成一个无电子邮件的会话                                                                                                                                                                                                                                                                                                                                                              | 配置 IdP 以在 id\_token 中发出 `email`。Okta：将 `email` 添加到自定义授权服务器的 ID 令牌声明中。Entra：在应用注册上添加 `email` 作为可选声明。PingFederate：启用一个会发出 `email` 的 OpenID Connect 策略。如果 IdP 从 userinfo 端点提供 `email` 但不将其包含在 id\_token 中（例如 Okta 组织授权服务器），请设置 `oidc.userinfo_fallback: true`。 |
| 每个 Amazon Bedrock 请求都返回 502；日志显示 `Could not load credentials from any providers`                                                                         | 在 EC2 上，IMDSv2 默认为 1 的跳数限制阻止了来自容器内部的实例元数据请求。启动和 `/readyz` 仍然通过，因为 AWS SDK 在第一次请求时解析实例凭证，而不是在构建客户端时解析                                                                                                                                                                                                                                                                                                          | 使用 `aws ec2 modify-instance-metadata-options --instance-id <id> --http-put-response-hop-limit 2` 提高跳数限制，或在启动模板中进行设置。此更改适用于实例上的每个容器。在可用的情况下优先使用 ECS 任务角色，它们从 ECS 容器凭证端点读取凭证并完全避免此更改，或者将更改应用于专用网关实例以限制暴露。    |
| IdP 错误：未知或不支持的 scope                                                                                                                                     | IdP 拒绝其无法识别的 scope                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | 将 `oidc.scopes` 精确设置为您的 IdP 接受的列表；它必须包含 `openid`。默认值为 `openid profile email offline_access`。                                                                                                                                                                                                                                                                                                 |
| 设置 `oidc.scopes` 后，会话不会静默续订                                                                                                                   | `offline_access` 已从覆盖配置中被丢弃                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | 如果您的 IdP 支持，请将 `offline_access` 加回。如果没有刷新令牌，开发人员每隔 `session.ttl_hours` 就需要重新运行一次浏览器登录。                                                                                                                                                                                                                                                                                              |
| 浏览器显示“此请求来自其他站点并已被阻止”                                                                                                         | 跨站点表单 POST，作为 CSRF 保护被阻止。对于嵌入式或代理页面是预期行为                                                                                                                                                                                                                                                                                                                                                                                                                                                           | 直接打开验证链接                                                                                                                                                                                                                                                                                                                                                                                                     |
| Chrome 阻止了“批准”按钮，提示“拒绝发送表单数据……违反了……内容安全策略指令：form-action”，但同一页面在 Safari 或 Firefox 中可以正常工作 | Chrome 会对整个重定向链强制执行 `form-action`。您的 IdP 会重定向到第二个未加入白名单的主机。                                                                                                                                                                                                                                                                                                                                                                                                                | 将重定向链中的每个额外源添加到 `oidc.form_action_origins` 中。在“批准”页面上打开 Chrome 开发者工具 → 控制台，查看哪个源被阻止。                                                                                                                                                                                                                                                                     |
| 登录在 IdP 处完成，但回调失败，在 Chrome 中出现 CSP 错误，或在 Safari 中提示“此登录链接已过期”                                                | IdP 通过 `response_mode=form_post` 返回了代码，该方式通过 POST 跨域自动提交到 `/oauth/callback`。Chrome 在严格的 CSP 下会阻止此操作；Safari 允许提交，但回调仅读取查询字符串。                                                                                                                                                                                                                                                                                                           | 确保您的 IdP 遵循 `response_mode=query`，网关会显式请求此项，因此回调是普通重定向                                                                                                                                                                                                                                                                                                              |
| 登录在本地可行但在 ALB 后面失败                                                                                                                                 | `public_url` 未设置，因此 IdP 获取到的内部 `http://` 源为 `redirect_uri`                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | 将 `listen.public_url` 设置为外部 `https://` 源                                                                                                                                                                                                                                                                                                                                                                               |
| 开发者反复看到信任提示                                                                                                                                  | TLS 证书按副本或按请求轮换                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | 在入口处使用稳定的证书，或者仅终止一次 TLS 并在内部通过纯 HTTP 运行副本                                                                                                                                                                                                                                                                                                                                     |
| CLI `/login`：“无法验证网关的 TLS 证书”或 `SELF_SIGNED_CERT_IN_CHAIN`                                                                               | 网关的 TLS 证书链由不在 CLI 主机信任存储中的私有 CA 签名                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | Claude Code 在原生二进制文件和 Node 22.15 或更高版本上默认读取操作系统信任存储；[`CLAUDE_CODE_CERT_STORE`](/docs/en/network-config#ca-certificate-store) 控制此行为。如果 CA 已安装到操作系统信任存储中，请确保开发者使用的是最新的运行时。否则，在启动之前将 `NODE_EXTRA_CA_CERTS` 设置为 CA 证书 PEM。首次连接的指纹提示仍然适用。              |

## 相关

* [Claude 应用网关概述](/docs/en/claude-apps-gateway)：快速入门和开发者连接
* [配置参考](/docs/en/claude-apps-gateway-config)：每个 `gateway.yaml` 选项

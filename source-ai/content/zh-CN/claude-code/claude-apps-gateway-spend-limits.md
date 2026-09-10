---
title: Claude 应用网关支出限制
source_id: claude-code/claude-apps-gateway-spend-limits
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/claude-apps-gateway-spend-limits
owner: Anthropic
content_sha256: 870ddf46c8650164e152da46b608d1deaa0c9e976051a80d1f491010f902ee4b
translation_of: claude-code/claude-apps-gateway-spend-limits
translation_source: official
translation_url: https://code.claude.com/docs/zh-CN/claude-apps-gateway-spend-limits
localization_sha256: 7ed2a2189a63a89ec8a80a3981c7d04636ef40e9501387aa82cee52c1f45e43d
---
本页采用内容所有者发布的官方简体中文版本，并与本站对应英文版本进行结构校验。

[官方中文来源](https://code.claude.com/docs/zh-CN/claude-apps-gateway-spend-limits)

内容所有者: Anthropic

> ## Documentation Index
> Fetch the complete documentation index at: https://code.claude.com/docs/llms.txt
> Use this file to discover all available pages before exploring further.

# Claude 应用网关支出限制

> 通过 Claude 应用网关为每个开发者按天、周或月设置支出上限。使用 Admin API 设置限制，网关在每个请求上实时执行这些限制。

支出限制限制了每个开发者在给定的一天、一周或一个月内通过你的 [Claude 应用网关](/docs/zh-CN/claude-apps-gateway) 可以花费的金额。当开发者超过他们的上限时，网关在他们的下一个请求上返回 `429`，并阻止他们直到该周期重置或管理员提高上限。使用支出限制为每个开发者、团队或整个组织设置一个共享凭证的上限。

Claude 应用网关通过一个共享的上游凭证转发所有推理，因此你的提供商的账单将所有内容归属于该凭证，而不是单个开发者。没有按开发者的限制，一个失控的代理群可能会花费组织的整个承诺。支出限制是网关在该共享账单之上的按开发者视图和断路器。

<h2 id="set-a-cap">
  设置上限
</h2>

配置了 [`admin:`](/docs/zh-CN/claude-apps-gateway-config#admin) 块在 `gateway.yaml` 中后，网关在 `/v1/organizations/spend_limits` 处提供一个 admin API，并在每个推理请求上实时执行上限。上限本身通过该 API 设置，而不是在 `gateway.yaml` 中；每个 `POST /v1/organizations/spend_limits` 请求从 `{scope, amount, period}` 创建或替换一个上限。该 API 镜像了 Anthropic 的公共 [Admin API](https://platform.claude.com/docs/en/manage-claude/admin-api) 支出限制端点的线路形状，因此针对该契约编写的 HTTP 客户端可以通过更改其基础 URL 来针对网关。

此请求为每个开发者设置了一个组织范围的默认值，每月 \$500：

```bash theme={null}
curl -sS https://claude-gateway.internal.example.com/v1/organizations/spend_limits \
  -H "x-api-key: $GATEWAY_ADMIN_WRITE_KEY" \
  -H "Content-Type: application/json" \
  -d '{"scope": {"type": "organization"}, "amount": "50000", "period": "monthly"}'
```

此请求在 `contractors` 组的每个成员上分层了一个更严格的每天 \$100 的上限：

```bash theme={null}
curl -sS https://claude-gateway.internal.example.com/v1/organizations/spend_limits \
  -H "x-api-key: $GATEWAY_ADMIN_WRITE_KEY" \
  -H "Content-Type: application/json" \
  -d '{"scope": {"type": "rbac_group", "rbac_group_id": "contractors"}, "amount": "10000", "period": "daily"}'
```

| 字段           | 值                                    | 描述                                                                                                                                                                                                                                                             |
| ------------ | ------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `scope.type` | `user`, `rbac_group`, `organization` | `user` 通过其 OpenID Connect (OIDC) `sub`（你的身份提供商分配的稳定用户 ID）针对一个开发者；将其作为 `scope.user_id` 传递。`rbac_group` 通过名称针对一个 [IdP 组](/docs/zh-CN/claude-apps-gateway-config#managed)；将其作为 `scope.rbac_group_id` 传递。`organization` 是组织范围的默认值。网关接受所有三个；Anthropic 的公共 `POST` 目前仅限用户。 |
| `amount`     | USD 美分的整数字符串，或 `null`                | `null` 是无限制的。`"0"` 是零上限，它阻止每个请求。                                                                                                                                                                                                                               |
| `period`     | `daily`, `weekly`, `monthly`         | 一个作用域可以为每个时期保持一个上限，每个都独立执行：如果开发者超过其中任何一个，他们就会被阻止。                                                                                                                                                                                                              |

组或组织上限是每个成员继承的按座位默认值，而不是共享池。每个时期，开发者的有效上限按以下顺序解决：按用户覆盖，然后是其组上限中最严格的，然后是组织默认值，然后是无限制。[`admin.group_limit_mode: max`](/docs/zh-CN/claude-apps-gateway-config#admin) 将多组平局打破翻转为最不严格的。

<h3 id="authenticate-to-the-admin-api">
  向 admin API 进行身份验证
</h3>

发送以下之一：

* 一个 `x-api-key` 标头，匹配 [`admin.write_keys`](/docs/zh-CN/claude-apps-gateway-config#admin) 中的一个密钥以获得完全访问权限，或 `admin.read_keys` 以获得仅 `GET` 访问权限。每个密钥都有一个 `id`，在审计日志中显示为 `admin-key:<id>`，因此为 Terraform、CI 和每个自动化提供自己的密钥。
* 一个网关承载令牌，其 `groups` 声明包括 [`admin.admin_groups`](/docs/zh-CN/claude-apps-gateway-config#admin) 中的一个。这是完全访问权限，审计为 `oidc:<sub>`，因此对人类管理员更好。

<h2 id="how-enforcement-works">
  执行如何工作
</h2>

在每个 `/v1/messages` 请求上，网关在一个 Postgres 查询中解决开发者的上限和期间至今的支出。如果他们超过任何上限，请求返回 `429`，`error.type: billing_error` 和标头 `x-should-retry: false`。消息是 `spend limit reached`，后跟你的 [`admin.blocked_message`](/docs/zh-CN/claude-apps-gateway-config#admin)（如果设置）。

`/v1/messages/count_tokens` 是豁免的。令牌计数是免费的，因此无论上限状态如何都会运行。

在每个响应之后，使用计量器从响应中读取令牌计数，当它流向客户端时，以 USD 列表价格对其进行定价，并为所有三个时期桶增加 Postgres 计数器。计量器是流上的单个读取器，因此客户端的字节不受影响，计量失败不会破坏响应。

支出限制从 USD 列表价格的令牌计数估计支出；它们是断路器，而不是发票。对于权威计费，请根据你的提供商自己的使用报告进行协调，例如 Anthropic 使用和成本 Admin API、Amazon Bedrock 上的调用日志或 Google Cloud 上的 Cloud Monitoring。

定价使用与 Claude Code CLI 用于自己的成本显示相同的表，具有跨 Anthropic、Amazon Bedrock (`us.anthropic.…-v1:0`)、Google Cloud 的 Agent Platform (`claude-…@date`) 和 Microsoft Foundry ID 形式的相同模型 ID 规范化。表无法放置的模型 ID（例如 Microsoft Foundry 部署名称或推理配置文件 ARN）以未知模型默认层 \$5/\$25 每百万输入/输出令牌的价格定价，而不是零，因此无法识别的 ID 无法通过不计量来绕过上限。网关在启动时和运行时每个 ID 一次警告模型何时通过回退定价。

客户端中止也被计费。上游仅在流的终端帧中报告输出令牌，因此中止的流不会携带它们。计量器从流式内容大小保持保守的下限估计，大约每令牌四个字符，并在终端使用帧缺失时计费。完整流始终计费上游报告的计数。没有这个，一个受限的开发者可以流式输出并在结束前立即中止每个请求，花费而不被计数。

<h3 id="postgres-availability">
  Postgres 可用性
</h3>

预检查使用两秒超时查询 Postgres。如果存储无法访问或超时，执行默认情况下失败打开：请求继续，网关记录警告。设置 [`enforcement.fail_closed_on_error: true`](/docs/zh-CN/claude-apps-gateway-config#enforcement) 改为失败关闭，它返回相同的 `429 billing_error`，消息为 `spend limit unavailable`。失败打开防止存储中断成为推理中断；失败关闭保证没有无计量支出。

<h2 id="admin-api-reference">
  Admin API 参考
</h2>

下面的端点在 `/v1/organizations/spend_limits` 下提供。

| 方法和路径                                          | 描述                                             |
| ---------------------------------------------- | ---------------------------------------------- |
| `GET /v1/organizations/spend_limits`           | 列出配置的上限。查询：`?limit=&after_id=&before_id=`。     |
| `POST /v1/organizations/spend_limits`          | 为 `{scope, period}` 创建或替换上限。                   |
| `GET /v1/organizations/spend_limits/{id}`      | 通过其 `spl_` 前缀 ID 获取一个上限。                       |
| `DELETE /v1/organizations/spend_limits/{id}`   | 删除一个上限。返回 `{type: "spend_limit_deleted", id}`。 |
| `GET /v1/organizations/spend_limits/effective` | 每个主体每个时期的已解决上限和至今支出。                           |
| `GET /v1/organizations/spend_limits/audit`     | 管理员变更跟踪，最新优先。查询：`?limit=`。                     |

约定镜像 Anthropic 的 Admin API：

* 每个对象上的 `type`
* `spl_` 前缀 ID
* 金额为 USD 美分的整数字符串；`POST` 拒绝任何其他 `currency`，返回 `400`
* `{type: "error", error: {type, message}, request_id}` 错误信封
* 每个管理员响应上的 `request-id` 响应标头，成功或错误，匹配正文的 `request_id`

每个变更在同一事务中向 `admin_audit` 写入前/后行，归属于 `admin-key:<id>` 或 `oidc:<sub>`。

网关仅提供支出限制端点。其他 Admin API 表面，例如 `spend_limit_increase_requests` 队列，不是网关 Admin API 的一部分。

<h3 id="/effective">
  `/effective`
</h3>

`GET /v1/organizations/spend_limits/effective` 返回 Anthropic 的 `SpendSummary` 模式：每行是一个主体的一个时期，具有已解决的上限、期间至今的支出和一个 `actor` 对象。网关特定的差异：

* `user_id` 是 OIDC `sub`。
* `actor.name` 和 `actor.email_address` 是 `null`，直到主体通过网关的第一个推理请求。网关没有用户目录；它从每个用户自己的会话 JWT 记录最后看到的值。
* 每行还携带一个 `groups` 数组，主体的最后看到的 IdP 组。这是一个网关扩展，因此管理员 UI 可以显示应用的每个上限层；Anthropic 形状的客户端忽略它。
* 没有 `user_ids[]` 过滤器，它列出有记录支出的主体，因为网关无法枚举所有组织成员。

组源上限根据那些最后看到的组解决，具有与执行使用的相同 `group_limit_mode` 平局打破，因此查看器显示实际应用的上限。

| 查询参数             | 描述                                              |
| ---------------- | ----------------------------------------------- |
| `user_ids[]`     | 可重复。按 OIDC `sub` 过滤到特定主体。                       |
| `period[]`       | 可重复。过滤到 `daily`、`weekly` 或 `monthly` 行。         |
| `sort`           | `spend_desc` 首先列出最高支出者。需要恰好一个 `period[]`。       |
| `q`              | 对 OIDC `sub`、最后看到的电子邮件和最后看到的显示名称的不区分大小写的子字符串过滤。 |
| `limit` / `page` | 页面大小（1–1000，默认 20）和前一个响应的 `next_page` 中的不透明游标。  |

<Warning>
  `q=` 和 `user_ids[]=` 乘坐 GET 查询字符串，因此任何前置代理或负载均衡器在其访问日志中捕获它们。如果你的 PII 日志策略很严格，请在那里清理这些参数。
</Warning>

<h3 id="/audit">
  `/audit`
</h3>

返回支出限制变更跟踪：谁更改了哪个上限、前/后快照和可选原因，最新优先。`has_more` 是精确的。此端点遵循本地 Admin API 约定，而不是第一方线路形状。

<h3 id="pagination">
  分页
</h3>

原始列表按 `after_id` 和 `before_id` 分页，它们是互斥的 `spl_…` ID；结果按创建排序，`has_more` 反映遍历方向。`/effective` 按传回的不透明 `next_page` 令牌分页为 `?page=`，主体按升序排序，因此在记录支出时页面保持稳定。`limit` 在两者上都是 1–1000，默认 20。

<h2 id="data-lifecycle">
  数据生命周期
</h2>

网关保持四个支出相关的表；每小时扫描执行保留窗口：

| 表                  | 内容                                 | 保留                                                                                       |
| ------------------ | ---------------------------------- | ---------------------------------------------------------------------------------------- |
| `spend`            | 按主体期间至今的计数器（美分）                    | [`admin.spend_retention_months`](/docs/zh-CN/claude-apps-gateway-config#admin)，默认 13          |
| `spend_limits`     | 配置的上限                              | 直到通过 API 删除                                                                              |
| `admin_audit`      | 变更跟踪                               | [`admin.audit_retention_days`](/docs/zh-CN/claude-apps-gateway-config#admin)，默认 365           |
| `principal_emails` | 每个主体的最后看到的电子邮件、显示名称和 IdP 组。包含 PII。 | [`admin.identity_retention_days`](/docs/zh-CN/claude-apps-gateway-config#admin) 自上次活动以来，默认 90 |

`identity_retention_days` 故意比 `spend_retention_months` 短：一个已取消配置的身份停止刷新并老化，而其匿名支出计数器保持用于年度报告。

当开发者离开时，通过 `DELETE /v1/organizations/spend_limits/{id}` 删除任何按用户上限；他们的支出和身份行按上面的保留窗口老化。要立即擦除一个人，用于离职或数据主体访问请求 (DSAR)，直接针对网关数据库运行 `DELETE FROM principal_emails WHERE principal = '<sub>'`。这删除了唯一保存其电子邮件、名称和组的表。`spend` 和 `admin_audit` 行仅引用伪匿名 OIDC `sub`，并按其自己的窗口老化。

<h2 id="related">
  相关
</h2>

* [`admin` 和 `enforcement` 配置](/docs/zh-CN/claude-apps-gateway-config#admin)：启用 admin API 和调整保留
* [部署指南](/docs/zh-CN/claude-apps-gateway-deploy#postgres)：Postgres 模式和备份指导

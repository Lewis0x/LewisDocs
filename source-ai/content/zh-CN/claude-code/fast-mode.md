---
title: 使用快速模式加速响应
source_id: claude-code/fast-mode
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/fast-mode
owner: Anthropic
content_sha256: 32b81e9abee5d60854d9b64272552a5e6047ced2f4442bf5449f30ec75c4251e
translation_of: claude-code/fast-mode
translation_model: k3
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/fast-mode)

Content owner: Anthropic

> ## 文档索引
> 在以下位置获取完整的文档索引：https://code.claude.com/docs/llms.txt
> 在进一步探索之前，请使用此文件来发现所有可用的页面。

# 使用快速模式加速响应

> 通过切换快速模式，在 Claude Code 中获取更快的 Opus 响应。

<Note>
  快速模式目前处于 [研究预览版](#research-preview)。其功能、定价和可用性可能会根据反馈发生变化。
</Note>

快速模式是 Claude Opus 的一种高速配置，在每 token 成本更高的情况下，该模式可使模型速度提升至 2.5 倍。当您需要为快速迭代或实时调试等交互式工作提高速度时，请使用 `/fast` 将其开启；当成本比延迟更重要时，请将其关闭。

快速模式并不是一个不同的模型。它使用 Claude Opus 并采用了优先考虑速度而非成本效益的不同 API 配置。您将获得相同的质量和功能，但响应速度更快。快速模式在 Opus 5 和 Opus 4.8 上受支持。它在 Sonnet、Haiku 或其他模型上不可用。

Claude Code 在其决定是否开启快速模式的所有地方：即 `/fast` 切换开关、双向模型切换以及会话启动时，都将 Opus 4.7 视为快速模式模型。API 会拒绝由此产生的快速模式请求，而不是以标准速度为其提供服务。请切换到 Opus 5 或 Opus 4.8 以保持加速效果。Opus 4.7 的快速模式已于 2026 年 6 月 25 日弃用，并于 2026 年 7 月 24 日移除。

需要了解的内容：

* 使用 `/fast` 在 Claude Code CLI 中开启快速模式。VS Code 扩展不支持快速模式。
* 在 Opus 5 和 Opus 4.8 上，快速模式每 MTok 输入/输出的定价为 \$10/\$50。
* 可供订阅计划 (Pro/Max/Team/Enterprise) 上的所有 Claude Code 用户和 Claude Console 使用。
* 对于订阅计划 (Pro/Max/Team/Enterprise) 上的 Claude Code 用户，快速模式仅可通过使用额度使用，不包含在订阅速率限制内。

## 切换快速模式

通过以下任一方式切换快速模式：

* 输入 `/fast` 并按下 Tab 键以开启或关闭
* 设置 `"fastMode": true` 于你的 [用户设置文件](/docs/en/settings)

默认情况下，您在交互式会话中开启的快速模式会跨会话保持有效。 {/* min-version: 2.1.205 */}在 [非交互模式](/docs/en/headless)下，使用 `-p` 标志时，`/fast` 仅在以其 [`--settings`](/docs/en/cli-reference#cli-flags) 值启用快速模式来启动的会话中工作，例如 `claude -p --settings '{"fastMode": true}'`；该开关随后仅应用于该会话，且不会保存为您的默认设置，并且在任何其他非交互式会话中，该命令会报告快速模式不可用。您可以将快速模式配置为每次会话重置。 有关详细信息，请参见 [要求每次会话选择开启](#要求每次会话选择开启)。

为了获得最佳的成本效益，请在会话开始时启用快速模式，而不是在对话中途切换。有关详细信息，请参见 [了解成本权衡](#了解成本权衡)。

当您启用快速模式时：

* 如果您正在使用其他模型，Claude Code 会自动切换到 Opus
* 您会看到一条确认消息：“快速模式开启”
* 当快速模式处于激活状态时，提示词旁边会出现一个小 `↯` 图标
* 随时再次运行 `/fast` 以检查快速模式是开启还是关闭

当您再次使用 `/fast` 禁用快速模式时，您仍将保持在 Opus 模型上。模型不会恢复为您之前的模型。要切换到其他模型，请使用 `/model`。

当您切换到不支持快速模式的模型时，Claude Code 会关闭快速模式，但在 Opus 4.7 上除外，在该模型上快速模式会保持开启状态，并且 API 会拒绝请求。{/* min-version: 2.1.208 */}当您保存的快速模式偏好为开启时，切换回受支持的 Opus 模型会再次将其开启，这也是新会话默认启动的相同偏好；如果会话保存的偏好为关闭，模型切换绝不会开启快速模式。如果配置了 [每次会话选择开启](#要求每次会话选择开启)，则切换回该模型时不会再次开启快速模式；请运行 `/fast` 以重新启用它。在 v2.1.208 之前，切换回原模型后快速模式会保持关闭状态，直到您再次运行 `/fast`。

{/* min-version: 2.1.218 */}每当模型切换开启或关闭快速模式时，Claude Code 都会显示 `Fast mode ON` 或 `Fast mode OFF` 确认信息，并且在快速模式开启时会出现 `↯` 图标。无论您是通过 `/model`、通过 [`/config model=<model>`](/docs/en/settings)，还是从通过 [远程控制](/docs/en/remote-control) 连接的设备进行切换，都是如此；在 v2.1.218 之前，通过 `/config model=<model>` 或 Remote Control 进行的切换会在没有确认信息的情况下更改快速模式。

Opus 5 是 Claude Code v2.1.219 及更高版本中快速模式的默认选项。在 v2.1.219 之前，v2.1.154 到 v2.1.218 版本中快速模式默认为 Opus 4.8，在 v2.1.142 到 v2.1.153 版本中默认为 Opus 4.7。

## 了解成本权衡

快速模式的单 token 定价高于标准 Opus：

| 模型    | 输入 (MTok) | 输出 (MTok) |
| -------- | ------------ | ------------- |
| Opus 5   | \$10         | \$50          |
| Opus 4.8 | \$10         | \$50          |

在整个 1M token 上下文窗口中，快速模式的定价是固定的。如需对比标准 Opus 费率，请参阅 [Claude 定价参考](https://platform.claude.com/docs/en/about-claude/pricing)。

在对话中首次启用快速模式时，您需要为整个对话上下文支付完整的快速模式未缓存输入 token 价格。您在对话中的位置越深，费用就越高，因此从一开始就启用快速模式成本更低。此费用每次对话仅收取一次，因此稍后关闭再打开快速模式不会重复收费。有关机制，请参见 [快速模式如何与提示缓存交互](/docs/en/prompt-caching#turning-on-fast-mode)。

## 决定何时使用快速模式

快速模式最适合响应延迟比成本更重要的交互式工作：

* 对代码更改进行快速迭代
* 实时调试会话
* 时间紧迫且期限严格的工作

标准模式更适合：

* 速度不太重要的长期自主任务
* 批处理或 CI/CD 流水线
* 对成本敏感的工作负载

### 快速模式与努力水平

快速模式和努力水平都会影响响应速度，但方式不同：

| 设置                    | 影响                                                                             |
| ---------------------- | -------------------------------------------------------------------------------- |
| **快速模式**            | 相同的模型质量，更低的延迟，更高的成本                                             |
| **较低的努力水平**       | 更少的思考时间，更快的响应，在复杂任务上质量可能较低                               |

您可以结合两者：在处理简单任务以追求最快速度时，将快速模式与较低的 [努力水平](/docs/en/model-config#adjust-effort-level) 结合使用。

## 要求

快速模式需要满足以下所有条件：

* **仅限 Anthropic API 或订阅**：快速模式可通过 Anthropic Console API 以及使用使用额度的 Claude 订阅计划使用。在 Amazon Bedrock、Google Cloud 的 Agent Platform、Microsoft Foundry 或 AWS 上的 Claude Platform 上不可用。
* **开启使用额度**：您的账户必须开启使用额度，这允许对超出您计划包含的使用量进行计费。对于个人账户，请在您的 [Console 计费设置](https://platform.claude.com/settings/billing) 中开启此功能。对于团队版和企业版，管理员必须为组织开启使用额度。

<Note>
  快速模式的使用量直接从使用额度中扣除，即使您的计划中还有剩余使用量也是如此。这意味着快速模式令牌不会计入您计划的包含使用量，而是从第一个令牌开始按快速模式费率收费。
</Note>

* **团队版和企业版的所有者启用**：对于团队版和企业版组织，默认情况下禁用快速模式。所有者必须明确 [启用快速模式](#enable-fast-mode-for-your-organization)，用户才能访问它。

<Note>
  如果您的组织尚未启用快速模式，`/fast` 命令将显示“快速模式已被您的组织禁用”。如果您的组织的 [`availableModels`](/docs/en/model-config#restrict-model-selection) 允许列表排除了快速模式 Opus 模型，`/fast` 将被拒绝，并提示“不在您组织的允许模型中”。例外情况是已经在支持快速模式的允许 Opus 模型上运行的会话：`/fast` 会在您当前的模型上启用快速模式，而不是切换模型。
</Note>

### 为您的组织启用快速模式

在哪里启用快速模式取决于您的组织使用的是哪种产品：

* **Console**（API 客户端）：管理员在 [Claude Code 首选项](https://platform.claude.com/claude-code/preferences) 中启用它
* **Claude AI**（团队版和企业版）：所有者在 [管理设置 > Claude Code](https://claude.ai/admin-settings/claude-code) 启用它

另一种完全禁用快速模式的选项是设置 `CLAUDE_CODE_DISABLE_FAST_MODE=1`。请参阅 [环境变量](/docs/en/env-vars)。

### 在代理和 LLM 网关后使用快速模式

在提供快速模式之前，Claude Code 会通过直接向 `api.anthropic.com` 发送请求来检查您组织的快速模式可用性。此检查不遵循 [`ANTHROPIC_BASE_URL`](/docs/en/llm-gateway-connect#set-the-base-url-and-credential)，因此在将 Claude 流量通过 [LLM 网关](/docs/en/llm-gateway) 进行路由并阻止直接出站访问 `api.anthropic.com` 的网络上，即使推理请求有效，该检查也会失败。该检查确实使用已配置的 [HTTP 代理](/docs/en/network-config#proxy-configuration)，因此只有在即使通过代理也无法访问 `api.anthropic.com` 时，网络阻止才会导致检查失败。

当检查失败时，`/fast` 会报告“由于网络连接问题，快速模式不可用”，并且请求以标准速度运行，即使您的组织已启用快速模式也是如此。过去成功的检查会从其缓存结果中继续工作，因此被阻止的检查主要影响新安装。

当检查到达 `api.anthropic.com` 但提供了 Anthropic 拒绝的凭证时，在开放网络上也会出现相同的连接消息。解析出的密钥为网关颁发凭证的会话（保存在 [`ANTHROPIC_API_KEY`](/docs/en/llm-gateway-connect#set-the-base-url-and-credential) 中或由 [`apiKeyHelper`](/docs/en/settings#available-settings) 生成）会使用该密钥发送检查，被拒绝的请求将被报告为连接失败。

要恢复快速模式，请在网络阻止是原因的情况下将直接出站访问 `api.anthropic.com` 列入白名单，或者设置与检查失败方式相匹配的变量：

* `CLAUDE_CODE_SKIP_FAST_MODE_NETWORK_ERRORS=1` 会将失败的检查视为可用，并且仍然会遵循“已被您的组织禁用”的响应。当您的网络拒绝连接，或者当 Anthropic 拒绝网关凭证时使用它；将列入白名单对凭证情况没有帮助，因为没有发生任何阻止。
* `CLAUDE_CODE_SKIP_FAST_MODE_ORG_CHECK=1` 会完全跳过检查。当您的网络拦截请求而不是拒绝请求时使用它。

两种网关配置会报告“快速模式已被您的组织禁用”而不是连接消息，即使您的组织已启用快速模式：

* 单独使用 [`ANTHROPIC_AUTH_TOKEN`](/docs/en/llm-gateway-connect#set-the-base-url-and-credential) 进行身份验证的会话将跳过检查：在没有 claude.ai 登录或 Anthropic API 密钥，并且没有缓存的成功检查的情况下，Claude Code 会直接将快速模式视为已被您的组织禁用，而无需发送请求。
* 拦截检查并以其自己的页面进行响应的代理（例如返回 HTTP 200 阻止页面的 TLS 检查代理）会被解读为表示您的组织已禁用快速模式的响应。

在这两种情况下，请设置 `CLAUDE_CODE_SKIP_FAST_MODE_ORG_CHECK=1` 来恢复快速模式。`CLAUDE_CODE_SKIP_FAST_MODE_NETWORK_ERRORS` 不适用于这两种情况中的任何一种，因为它仅绕过失败的检查，而这两者都会产生禁用响应。将直接出站列入白名单对持有者令牌情况没有帮助，因为它根本不会发送请求。

这些变量仅影响客户端检查。当您的组织禁用了快速模式时，无论是否设置了这些变量，API 都会拒绝快速模式请求。

设置 `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` 也会抑制可用性检查。在没有先前缓存的成功检查的情况下，`/fast` 会报告“快速模式当前不可用”；在该配置中，两个跳过变量也会恢复快速模式。

### 要求每次会话选择开启

默认情况下，用户在交互式会话中开启的快速模式会跨会话保留：在未来的会话中它将保持开启状态。要更改此设置，请将 `fastModePerSessionOptIn` 设置为 `true` 于任何 [设置文件](/docs/en/settings#settings-files) 中，这将导致每个会话在启动时关闭快速模式，并要求用户使用 `/fast` 显式启用它。所有者在 [团队版](https://claude.com/pricing?utm_source=claude_code\&utm_medium=docs\&utm_content=fast_mode_teams#team-&-enterprise) 或 [企业版](https://anthropic.com/contact-sales?utm_source=claude_code\&utm_medium=docs\&utm_content=fast_mode_enterprise) 计划中可以通过 [服务器管理的设置](/docs/en/server-managed-settings) 在全组织范围内进行部署。

```json theme={null}
{
  "fastModePerSessionOptIn": true
}
```

这对于控制用户运行多个并发会话的组织的成本非常有用。当需要速度时，用户仍然可以使用 `/fast` 启用快速模式，但它会在每个新会话开始时重置。用户的快速模式偏好设置仍会被保存，因此移除此设置会恢复默认的持久行为。

## 处理速率限制

快速模式的速率限制独立于标准 Opus。所有支持的 Opus 模型共享同一个快速模式速率限制池：在任何一个模型上的使用量都会从相同的限制中扣除。当您触发快速模式速率限制或用完使用额度时：

1. 快速模式自动回退到标准速度
2. `↯` 图标变灰以指示冷却时间
3. 您将以标准速度和定价继续工作
4. 当冷却时间到期时，快速模式会自动重新启用

要手动禁用快速模式而不是等待冷却时间，请再次运行 `/fast`。

## 研究预览

快速模式是一项研究预览功能。这意味着：

* 该功能可能会根据反馈发生变化
* 可用性和定价可能会有所调整
* 底层 API 配置可能会演进

通过您常用的 Anthropic 支持渠道报告问题或反馈。

## 另请参阅

* [模型配置](/docs/en/model-config)：切换模型并调整努力等级
* [有效管理成本](/docs/en/costs)：跟踪 token 使用情况并降低成本
* [状态栏配置](/docs/en/statusline)：显示模型和上下文信息

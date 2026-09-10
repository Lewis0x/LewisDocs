---
title: 使用顾问工具升级处理困难决策
source_id: claude-code/advisor
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/advisor
owner: Anthropic
content_sha256: ff20de2bfe61f9fff5df0c6b8b4bd66fb7622733bdfe7b236a021cf188117f62
translation_of: claude-code/advisor
translation_model: k3
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/advisor)

Content owner: Anthropic

> ## 文档索引
> 在此处获取完整的文档索引：https://code.claude.com/docs/llms.txt
> 在进一步探索之前，使用此文件来发现所有可用页面。

# 使用顾问工具升级处理困难决策

> 将您的主模型与一个更强大的顾问模型配对，Claude 会在任务的关键时刻向其咨询。

<Note>
  顾问工具是实验性功能，需要 Anthropic API。它在 Amazon Bedrock、AWS 上的 Claude 平台、Google Cloud 的 Agent 平台或 Microsoft Foundry 上不可用。其行为、定价和可用性可能会发生变化。
</Note>

顾问工具让 Claude 能在任务的关键时刻咨询第二个（通常更强大的）模型，例如在确定方案之前、遇到反复出现的错误时，或在宣布任务完成之前。顾问会接收完整的对话内容，包括每一次工具调用及其结果，并返回 Claude 在继续之前会采纳的指导。

顾问作为 [server tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool) 在 Anthropic 的基础设施上于服务端运行，订阅账户和按 API 计费的账户均可使用。您可以选择哪个模型充当顾问，而由 Claude 决定何时调用它。

本页介绍如何启用顾问、接受哪些模型配对、咨询期间 Claude 会显示什么，以及顾问用量如何计费。

## 何时使用顾问

顾问适合冗长的多步骤任务，其中大多数轮次都是常规操作，但计划质量决定最终结果。典型例子包括大规模重构、错误反复出现的调试会话，以及您希望在 Claude 宣布完成之前进行独立检查的任务。

对于几乎没有规划空间的短任务，或每一轮都需要最强模型的工作，它带来的价值较小。对于这些情况，请改为 [switch the main model](/docs/en/model-config#setting-your-model)，或参阅 [how the advisor compares with opusplan and subagents](#compare-with-related-features) 了解其他获取第二意见的方式。

## 启用顾问

您可以通过三种方式设置顾问模型：

* **`/advisor` 命令**：在会话中途设置或更改顾问，并将其保存为默认值
* **`advisorModel` 设置**：在您的 [settings file](/docs/en/settings) 中配置持久默认值
* **`--advisor` 标志**：在启动时为单个会话设置顾问

如果其中任何一种方式设置了顾问模型，那么对于主模型 [supports it](#choose-an-advisor-model) 的会话，顾问将被启用，并且会话开始后会显示 `Advisor Tool (experimental) is on and may use more tokens · /advisor` 通知。要停止使用它，请参阅 [Turn the advisor off](#turn-the-advisor-off)。

<Note>
  {/* min-version: 2.1.210 */}Claude Code 不提供 Fable 5 作为顾问。对于拥有 [Fable 5 access](/docs/en/model-config#work-with-fable-5) 的组织，`/advisor` 选择器会将其列为一个变暗、不可选的行，标记为 `Fable 5 (temporarily unavailable)`，并且 Claude Code 会拒绝 `/advisor fable` 和 `--advisor fable`。Fable 5 作为主模型不受影响。

  一项远程配置的发布控制决定 Fable 5 何时恢复为顾问选项。
</Note>

### 使用 `/advisor` 命令

不带参数运行 `/advisor` 可打开一个列出可用顾问模型的选择器，或者直接传入模型：

```
/advisor opus
```

该命令会以 `Advisor set to` 后跟顾问模型名称进行确认。您的选择会保存到用户设置中的 `advisorModel`，并跨会话持久保留。

如果您组织的 [`availableModels`](/docs/en/model-config#restrict-model-selection) 允许列表排除了已保存的顾问模型，则在您使用 `/advisor` 选择一个允许的模型之前，顾问不会被调用。如果您当前的主模型不支持顾问，该选择仍会被保存，并在您通过 [](#choose-an-advisor-model)[ 切换到 `/model`compatible main model](/docs/en/model-config#setting-your-model) 时激活。

### 在设置中设置 `advisorModel`

要在不打开会话的情况下将顾问配置为默认值，请在您的设置文件中进行设置：

```json theme={null}
{
  "advisorModel": "opus"
}
```

### 使用 `--advisor` 标志

要为单个会话设置顾问而不更改已保存的设置，请使用该标志启动：

```bash theme={null}
claude --advisor opus
```

该标志在该会话中优先于 `advisorModel` 设置，并且不会列在 `claude --help` 中。如果会话的主模型不支持顾问，或者所请求的顾问模型被贵组织的 [`availableModels`](/docs/en/model-config#restrict-model-selection) 允许列表排除，则会以错误退出。

## 选择顾问模型

顾问的能力必须至少与主模型相当。Fable 5 满足能力检查，但[尚未作为顾问提供](#enable-the-advisor)，因此下表中的 Fable 条目将在推出恢复其作为选项后适用。每个主模型可接受的顾问为：

| 主模型                                         | 可接受的顾问                  | 备注                                                                                                                                                                         |
| ----------------------------------------------- | ---------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Haiku 4.5                                       | Fable、Opus、Sonnet          | Haiku 可以调用顾问，但不能充当顾问                                                                                                                              |
| Sonnet 4.6                                      | Fable、Opus、Sonnet          |                                                                                                                                                                               |
| Sonnet 5                                        | Fable、Opus、Sonnet 5        | Sonnet 4.6 顾问会被拒绝                                                                                                                                              |
| Opus 4.6                                        | Fable、Opus、Sonnet 5        | Sonnet 5 和 Opus 4.6 被评为能力相当，因此 Opus 4.6 主模型可接受 Sonnet 5 顾问                                                                           |
| Opus 4.7 或更高版本                              | Fable，以及 Opus 4.7 或更高版本 | Opus 4.7 及更高版本的 Opus 模型被评为能力相当，因此其中任何一个都可接受另一个作为顾问。Opus 4.7 主模型搭配 Opus 4.6 或 Sonnet 5 顾问会被拒绝 |
| Fable 5 ({/* min-version: 2.1.170 */}v2.1.170+) | Fable                        | Opus 或 Sonnet 顾问会被拒绝。Fable 未作为顾问提供，因此 Fable 5 主模型在没有顾问的情况下运行                                                           |

无论 Fable 5 充当主模型还是顾问，都需要 Claude Code v2.1.170 或更高版本以及 Fable 5 访问权限。

将顾问设置为 `opus` 或 `sonnet`，或者在推出恢复其作为选项后设置为 `fable`。这些别名解析为每个模型的最新版本。您还可以传递完整的模型 ID，例如 `claude-opus-5`。

子代理继承配置的顾问，并针对其自身模型应用相同的配对检查。

Claude Code 在发送请求之前验证配对：

* 如果顾问的能力低于主模型，则不会将顾问附加到主模型的请求中。`/advisor` 命令输出和通知会显示这一点。自身模型满足配对条件的子代理仍可使用该顾问。
* 如果主模型或顾问是 Claude Code 无法识别的模型，则不会附加顾问。

### 常见模型搭配

任何被接受的搭配都可行。使用 Fable 5 作为顾问的搭配在 Fable 5 [重新成为顾问选项](#enable-the-advisor) 后适用。这些组合以不同方式在成本与能力之间取得平衡：

| 搭配                          | 适用场景                                                                                                                                                                 |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Sonnet 主模型 + Opus 顾问    | Sonnet 处理常规工作，并将规划、模糊的失败情况和完成检查上报给 Opus                                                                                                  |
| Sonnet 主模型 + Fable 顾问   | 在决策点获取 Fable 5 的指导，而无需全程运行 Fable 5。需要 v2.1.170 或更高版本以及 Fable 5 访问权限                                                                  |
| Haiku 主模型 + Opus 顾问     | 最低成本的主模型搭配强大的规划能力。预期成本高于单独使用 Haiku，但低于将主模型切换为 Sonnet 或 Opus                                                                |
| Opus 主模型 + Opus 顾问      | 由第二个 Opus 审查第一个 Opus。适用于高风险任务，此时独立检查比成本更重要                                                                                          |
| Fable 主模型 + Fable 顾问    | Fable 5 可用时（v2.1.170+）能力最强的搭配。Fable 比 Opus 和 Sonnet 高一个层级，因此它是 Fable 主模型唯一被接受的顾问                                               |
| Sonnet 主模型 + Sonnet 顾问  | 用于捕捉常规疏漏的低成本第二意见                                                                                                                                    |

## Claude 何时咨询顾问

Claude 自行决定何时调用顾问。它倾向于在确定方案之前、错误反复出现时以及宣布任务完成之前进行咨询，但具体时机由模型驱动，而非基于规则。

你可以在提示中请求咨询，就像请求任何其他工具一样，例如 `consult the advisor before you continue`。没有设置可以限制或强制顾问调用；如果你希望 Claude 在任务中更多或更少地咨询，请在指令中说明。

## 会话期间你看到的内容

当 Claude 调用顾问时，调用进行期间转录中会显示一行带有顾问模型名称的 `Advising`。结果返回时，该行会确认顾问已审查对话。按 `Ctrl+O` 可展开并阅读顾问的完整指导。

Claude 通常会遵循顾问的指导，但当自身证据与某项具体主张相矛盾时会做出调整：如果推荐的步骤在尝试时失败，或文件内容与建议不符，Claude 会指出冲突，而不是无条件地遵循指导。

顾问始终接收完整对话，且时机由 Claude 控制。如需更多控制或不同的配置，请参阅 [顾问与子代理及 opusplan 的对比](#compare-with-related-features)。

## 成本

每次顾问调用都会将对话发送给顾问模型，因此除主模型的用量外，还会按顾问模型的费率消耗 token。使用 API 计费时，顾问 token 按顾问模型的输入和输出费率收费。在订阅计划中，顾问用量会计入你计划的用量限额。

Claude 在决策点而非每一轮都调用顾问，因此将更快的主模型与更强的顾问搭配，通常比全程运行更强的模型成本更低。顾问用量会计入 [`/usage`](/docs/en/costs#track-your-costs) 显示的会话总计中。

有关顾问 token 如何在 API 响应中报告，请参阅 Claude API 文档中的 [用量与计费](https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool#usage-and-billing)。

## 对提示缓存的影响

在会话中途启用或禁用 advisor 不会使主模型的 [提示缓存](/docs/en/prompt-caching)失效。与[更改模型或推理强度级别](/docs/en/prompt-caching#actions-that-invalidate-the-cache)不同，切换 `/advisor` 会保持缓存前缀完整，advisor 返回的指导也会在后续轮次中作为对话记录的一部分被缓存。

advisor 模型自身对对话的读取不会被缓存。每次 advisor 调用都会重新处理完整的对话记录，调用之间没有任何复用。

## 要求

顾问工具需要满足以下所有条件：

* **仅限 Anthropic API**：顾问是服务器端执行的工具。它在 Amazon Bedrock、AWS 上的 Claude Platform、Google 上不可用 Cloud 的 Agent Platform 或 Microsoft Foundry。通过配置了 [LLM 网关](/docs/en/llm-gateway) 的 `ANTHROPIC_BASE_URL`，可用性取决于网关是否将请求原封不动地转发到 Anthropic API。
* **支持的主模型**：Opus 4.6 或更高版本、Sonnet 4.6 或更高版本，或 Haiku 4.5。{/* min-version: 2.1.170 */}Fable 5 在 Claude Code v2.1.170 或更高版本上也符合条件，但 Fable 5 主[仅接受 Fable 顾问](#choose-an-advisor-model)，且 Fable [不作为顾问提供](#enable-the-advisor)，因此 Fable 5 会话会在没有顾问的情况下运行，直到推广将其作为 选项。

## 关闭顾问

要停止使用顾问并清除已保存的 `advisorModel`，请运行 `/advisor off` 或在 `/advisor` 选择器中选择 **No advisor**：

```
/advisor off
```

要完全禁用顾问工具，请设置 `CLAUDE_CODE_DISABLE_ADVISOR_TOOL=1`。`/advisor` 命令将不可用，任何已配置的 `advisorModel` 都会被忽略。`--advisor` 标志仍被接受但不起作用；传递该标志的现有脚本将继续正常运行而不会报错。请参阅 [环境变量](/docs/en/env-vars)。

## 与相关功能比较

顾问工具是结合多种模型优势的几种方式之一。请根据你希望另一个模型何时介入来进行选择。

| 方式                                                        | 更强模型的运行时机                                                                                                                 | 启动方式                                     |
| ----------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| 顾问工具                                                    | 在任务进行中的决策节点                                                                                                             | Claude 在需要指导时调用                    |
| [`opusplan`](/docs/en/model-config#opusplan-model-setting)       | 在计划模式下，当 [被 `availableModels`](/docs/en/model-config#restrict-model-selection) 允许时运行，然后切换到 Sonnet 执行 | 你进入计划模式                            |
| [子代理](/docs/en/sub-agents#choose-a-model) 并设置 `model`        | 贯穿整个委派的子任务                                                                                                                 | Claude 进行委派，或由你调用该子代理       |
| [`/model`](/docs/en/model-config#setting-your-model)             | 用于所有后续轮次                                                                                                                     | 你切换模型                                  |

## 另请参阅

* [模型配置](/docs/en/model-config)：切换模型、设置努力级别，并使用 `opusplan`
* [有效管理成本](/docs/en/costs)：跨模型跟踪令牌使用情况
* [Claude API 中的 Advisor 工具](https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool)：了解底层服务器工具，或直接从 Messages API 使用它
* [Advisor 策略](https://claude.com/blog/the-advisor-strategy)：为什么将快速主模型与更强的 advisor 配对会奏效

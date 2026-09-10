---
title: 治理
source_id: codex/enterprise/governance
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/enterprise/governance
owner: OpenAI
content_sha256: 4acb2b298e85d1f2a7b3b8149283720ef34ce39d4743258d766de76873f096d9
translation_of: codex/enterprise/governance
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/enterprise/governance)

Content owner: OpenAI

# 治理

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。可以通过在页面 URL 后附加 `.md` 来获取文档页面的 Markdown 版本。

Codex 活动的治理涵盖交互式分析、程序化
报告、相关的 ChatGPT 使用控制以及审计记录。请选择
与问题相符的界面；分析和合规数据的
用途不同。

<a id="governance-and-observability"></a>
<a id="ways-to-track-codex-usage"></a>

| 如果你需要                                          | 从这里开始                                                                |
| ------------------------------------------------------- | ------------------------------------------------------------------------- |
| 了解 ChatGPT 的采用情况                      | [工作区分析](https://learn.chatgpt.com/docs/enterprise/workspace-analytics)              |
| 以交互方式审查 Codex 采用情况和活动        | [Codex 分析](#analytics-dashboard)                                   |
| 将聚合的 Codex 报告加载到另一个系统中     | [分析 API](https://learn.chatgpt.com/docs/enterprise/analytics-api)                          |
| 导出记录以供审计或调查               | [合规 API](https://learn.chatgpt.com/docs/enterprise/compliance-api)                        |
| 审查依赖套餐的 ChatGPT 工作区额度控制 | [ChatGPT 使用限制和支出控制](https://learn.chatgpt.com/docs/enterprise/usage-limits) |

## 打开管理界面

- 打开 [工作区分析](https://chatgpt.com/admin/usage) 以获取交互式
  工作区报告。[工作区分析指南](https://help.openai.com/en/articles/10875114-workspace-analytics-for-chatgpt-enterprise-and-edu)
  介绍了当前的角色和视图。
- 打开经过身份验证的 [Codex 分析 API 参考](https://chatgpt.com/codex/cloud/settings/apireference)
  当你需要定期的、程序化的报告时。
- 打开经过身份验证的 [管理 API 参考](https://chatgpt.com/admin/api-reference)
  和 [合规平台指南](https://help.openai.com/en/articles/9261474-compliance-api-for-chatgpt-enterprise-edu-and-chatgpt-for-teachers)
  以进行审计和调查集成。

例如，使用工作区分析进行快速采用情况检查，使用 分析
API 将聚合的 Codex 报告加载到商业智能系统中，
并使用合规 API 将可审计记录发送到 SIEM 或电子
取证工作流。

## 分析仪表板

<a id="dashboard-views"></a>
<a id="data-export"></a>

ChatGPT 提供全工作区范围的分析，用于广泛的采用和参与度评估。
Codex 分析专注于 Codex 活动。两者都是交互式报告
界面，而不是原始审计日志。

使用 [工作区分析](https://learn.chatgpt.com/docs/enterprise/workspace-analytics) 来对比
这两种体验，并找到它们当前由所有者维护的来源。你也可以
直接打开 [工作区分析](https://chatgpt.com/admin/usage)。不要
根据仪表板标签或下载的报告字段建立持久的报告
契约；这些可能会随着产品的发展而改变。

## 相关的 ChatGPT 使用控制

ChatGPT 工作区使用控制与分析是分开的，并且
不配置功能权限。根据套餐的不同，符合条件的 Codex 活动
可能会消耗 ChatGPT 工作区额度，达到限制上限可能会暂停对
符合条件的功能的访问。这些控制不会设置通用的 Codex 限制或管理
平台 API 账单。

请参见 [ChatGPT 使用限制和支出控制](https://learn.chatgpt.com/docs/enterprise/usage-limits)
以了解持久边界和当前的帮助中心来源。

## 分析 API

<a id="what-it-measures"></a>
<a id="endpoints"></a>
<a id="usage"></a>
<a id="code-review-activity"></a>
<a id="user-engagement-with-code-review"></a>
<a id="how-it-works"></a>
<a id="common-use-cases"></a>

使用 分析 API 进行程序化的、聚合的 Codex 报告。它
适用于数据仓库、商业智能系统和不应依赖
交互式仪表板的内部报告。

经过身份验证的 API 参考权威地规定了访问要求、路由、模式、
字段、报告窗口和分页。请参见
[分析 API](https://learn.chatgpt.com/docs/enterprise/analytics-api) 以获取概念集成
边界和规范参考链接。

## 合规 API

<a id="what-it-measures-1"></a>
<a id="what-you-can-export"></a>
<a id="activity-logs"></a>
<a id="metadata-for-audit-and-investigation"></a>
<a id="common-use-cases-1"></a>
<a id="what-it-does-not-provide"></a>

将合规 API 用于需要
可审计记录的安全、法律和治理工作流。它不是一个采纳度或生产力仪表板。

经过身份验证的 API 参考权威地规定了事件覆盖范围、架构、权限、
过滤器、保留策略和请求行为。请参阅
[合规 API](https://learn.chatgpt.com/docs/enterprise/compliance-api) 以了解概念性
集成边界和规范参考链接。

<a id="recommended-pattern"></a>

对于跨这些界面的推出排序和验证，请使用
[管理员部署指南](https://learn.chatgpt.com/docs/enterprise/admin-setup)。

## 相关文档

- [管理员部署指南](https://learn.chatgpt.com/docs/enterprise/admin-setup)
- [工作区分析](https://learn.chatgpt.com/docs/enterprise/workspace-analytics)
- [分析 API](https://learn.chatgpt.com/docs/enterprise/analytics-api)
- [合规 API](https://learn.chatgpt.com/docs/enterprise/compliance-api)

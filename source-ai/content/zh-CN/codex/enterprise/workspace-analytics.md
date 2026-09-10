---
title: 工作空间分析
source_id: codex/enterprise/workspace-analytics
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/enterprise/workspace-analytics
owner: OpenAI
content_sha256: a5df1bcb8fd870a78fff55a592a5c94781a20c14dcca6396cedfe94773193d85
translation_of: codex/enterprise/workspace-analytics
translation_model: k3
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/enterprise/workspace-analytics)

Content owner: OpenAI

# 工作空间分析

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。可以通过在页面 URL 后附加 `.md` 来获取文档页面的 Markdown 版本。

使用 ChatGPT 工作空间分析来了解广泛的工作空间采用情况。使用 Codex
分析来进行专注于 Codex 的报告。使用 Analytics API 进行编程式
聚合，并使用 Compliance API 获取可审计记录。

这些报告界面不会授予产品访问权限或设置运行时策略。参见
[角色与工作空间权限](https://learn.chatgpt.com/docs/enterprise/roles-and-workspace-permissions)
以了解管理边界。

## 选择报告界面

| 界面                         | 用途                                                        | 约定来源                                                                                           |
| --------------------------- | ------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| ChatGPT 工作空间分析         | 交互式、全工作空间的采用和参与度报告                         | [工作空间分析帮助中心指南](https://help.openai.com/en/articles/10875114)                 |
| Codex 分析                   | 专注于 Codex 采用和活动的交互式报告                         | 经过身份验证的 [Codex 分析仪表板](https://admin.openai.com/analytics/codex)                  |
| Analytics API               | 编程式、聚合的 Codex 报告                                  | 经过身份验证的 [Codex Analytics API 参考](https://chatgpt.com/codex/cloud/settings/apireference) |
| Compliance API              | 审计、安全、法律和调查记录                                 | 经过身份验证的 [Admin API 参考](https://chatgpt.com/admin/api-reference)                         |

## 查看 ChatGPT 工作空间分析

ChatGPT 工作空间分析提供了支持的工作空间功能的采用和
参与度的交互式视图。可用性、角色、仪表板
部分、新鲜度、隐私行为和导出格式可能会发生变化。使用
[面向 ChatGPT Enterprise 和 Edu 的工作空间分析](https://help.openai.com/en/articles/10875114)
以获取当前的覆盖范围和操作流程。

将下载的报告视为可识别的组织数据。
应用组织的访问、存储和保留策略，而不是
假设导出数据与聚合的
仪表板具有相同的隐私特征。

## 查看 Codex 分析

经过身份验证的 [Codex 分析仪表板](https://admin.openai.com/analytics/codex)
专注于 Codex 报告。将其用于交互式探索，而不是作为稳定的
数据模式约定。仪表板类别、字段、过滤器和导出格式可以
独立于此页面进行更改。

对于自动化报告，请使用 [Analytics API](https://learn.chatgpt.com/docs/enterprise/analytics-api)
并遵循其经过身份验证的参考文档。对于可审计记录，请使用
[Compliance API](https://learn.chatgpt.com/docs/enterprise/compliance-api)。

## 解读报告数据

请牢记这些边界：

- ChatGPT 工作空间分析和 Codex 分析涵盖不同的产品
  范围。
- 聚合分析和审计记录服务于不同目的并具有
  独立的契约。
- 分析描述了活动；它不授予访问权限或更改运行时
  权限。
- [ChatGPT 使用限制和支出控制](https://learn.chatgpt.com/docs/enterprise/usage-limits) 是
  独立的、依赖于计划的工作空间边界。

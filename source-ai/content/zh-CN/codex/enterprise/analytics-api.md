---
title: 分析 API
source_id: codex/enterprise/analytics-api
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/enterprise/analytics-api
owner: OpenAI
content_sha256: 3bfcbe67a34f78aad75e117a4ea5fdd5d14e11ec64e3c1483b239629628661f7
translation_of: codex/enterprise/analytics-api
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/enterprise/analytics-api)

Content owner: OpenAI

# 分析 API

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。通过在页面 URL 后附加 `.md` 可以获取文档页面的 Markdown 版本。

Codex 分析 API 为
ChatGPT 工作区提供聚合的 Codex 使用情况和活动指标。

经过身份验证的 [Codex 分析 API 参考文档](https://chatgpt.com/codex/cloud/settings/apireference)
是有关当前访问要求、路由、请求和
响应模式、指标、时间语义以及分页的唯一事实来源。

## 何时使用分析 API

当您需要执行以下操作时，分析 API 非常适用：

- 自动化定期的 Codex 报告。
- 将聚合的 Codex 指标与内部组织数据结合。
- 为已批准的受众构建受控的报告层。
- 避免将集成与交互式仪表板耦合。

它不是原始的审计日志接口。请使用
[Compliance API](https://learn.chatgpt.com/docs/enterprise/compliance-api) 来处理工作流所需的
可审计的活动记录。

## 确认管理边界

分析 API 结果的范围限定于 ChatGPT 工作区，但请求
使用 Platform 组织 API 密钥进行身份验证。该密钥的组织必须
与该工作区关联的组织相匹配。

经过身份验证的参考文档包含当前的密钥配置、范围要求、
路由、模式、字段、时间语义和分页行为。此页面
不会重复该契约。

## 相关文档

- [工作区分析](https://learn.chatgpt.com/docs/enterprise/workspace-analytics)
- [管理员发布指南](https://learn.chatgpt.com/docs/enterprise/admin-setup)
- [治理](https://learn.chatgpt.com/docs/enterprise/governance)
- [合规 API](https://learn.chatgpt.com/docs/enterprise/compliance-api)

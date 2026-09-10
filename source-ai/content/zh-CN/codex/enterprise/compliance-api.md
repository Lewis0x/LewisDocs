---
title: 合规 API 和审计事件
source_id: codex/enterprise/compliance-api
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/enterprise/compliance-api
owner: OpenAI
content_sha256: 10c0f400f0f79a4a62f609df4f2427fd228c79ca9b796e333a3e914fc711e9d2
translation_of: codex/enterprise/compliance-api
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/enterprise/compliance-api)

Content owner: OpenAI

# 合规 API 和审计事件

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。可以通过在页面 URL 后附加 `.md` 来获取文档页面的 Markdown 版本。

将合规 API 用于需要可审计记录的安全、法务、治理和调查
工作流。请使用分析而非合规记录，
来衡量采用情况和趋势。

经过身份验证的 [管理 API 参考](https://chatgpt.com/admin/api-reference)
是当前访问要求、事件覆盖范围、路由、
模式、筛选器、保留和请求行为的真实来源。

有关可用合规面和常见集成
模式的概述，请参见 [合规平台指南](https://help.openai.com/en/articles/9261474-compliance-api-for-chatgpt-enterprise-edu-and-chatgpt-for-teachers)。

## 何时使用合规 API

当您需要执行以下操作时，合规 API 非常适用：

- 将支持的记录导出到审计或调查系统。
- 应用组织的保留和法务保留流程。
- 将 Codex 活动与其他安全或身份数据相关联。
- 支持已批准的安全、法务或治理调查。

它不是生产力仪表板。不要用它来推断代码质量或
个人绩效。请使用 [工作区分析](https://learn.chatgpt.com/docs/enterprise/workspace-analytics)
或 [分析 API](https://learn.chatgpt.com/docs/enterprise/analytics-api) 来报告采用情况。

## 开始使用

1. 打开 [管理 API 参考](https://chatgpt.com/admin/api-reference) 并
   确认您的管理员角色可以访问所需的合规
   资源。
2. 使用仅追加的合规日志流进行持续收集。请查阅
   经过身份验证的参考文档，以了解当前支持的资源和检索
   模式。
3. 测试摄入到非生产环境的安全信息和事件
   管理 (SIEM) 系统或数据湖。该
   [合规平台指南](https://help.openai.com/en/articles/9261474-compliance-api-for-chatgpt-enterprise-edu-and-chatgpt-for-teachers)
   链接到了当前的 API 文档和快速入门笔记本。
4. 安排持续收集，并对导出的记录应用您组织的访问、
   保留和法务保留控制。不要假设
   源保留窗口能替代您组织的保留策略。

例如，安全团队可以将不可变的合规事件流式传输到其
SIEM 中进行调查，或将这些事件路由到已批准的电子
发现工作流。请使用经过身份验证的参考文档来获取当前的路由和
模式，而不是从本指南中复制端点契约。

## 确认管理边界

合规范围遵循 ChatGPT 工作区和当前身份验证参考中所代表的
产品。平台 API 组织数据遵循
其自身的 API 数据和管理控制。

经过身份验证的参考文档拥有当前的路由、事件覆盖范围、模式、
筛选器、保留行为、权限要求和请求机制。
本页面不会重复该契约。

## 相关文档

- [工作区分析](https://learn.chatgpt.com/docs/enterprise/workspace-analytics)
- [管理员推广指南](https://learn.chatgpt.com/docs/enterprise/admin-setup)
- [治理](https://learn.chatgpt.com/docs/enterprise/governance)
- [分析 API](https://learn.chatgpt.com/docs/enterprise/analytics-api)

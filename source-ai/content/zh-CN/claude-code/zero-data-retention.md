---
title: 零数据保留
source_id: claude-code/zero-data-retention
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/zero-data-retention
owner: Anthropic
content_sha256: 987003e69d73fb0de7161e222a7d660d42d839b9aaba073dea2074e6d20f127b
translation_of: claude-code/zero-data-retention
translation_model: k3
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/zero-data-retention)

Content owner: Anthropic

> ## 文档索引
> 在以下地址获取完整的文档索引：https://code.claude.com/docs/llms.txt
> 使用此文件可在深入探索之前发现所有可用页面。

# 零数据保留

> 了解面向 Claude Code 的零数据保留（ZDR），此功能向符合条件的 Claude for Enterprise 账户提供；内容包括适用范围、禁用的功能，以及如何申请启用。

面向 Claude Code 的零数据保留（ZDR）适用于符合条件的 Claude for Enterprise 账户。启用 ZDR 后，Claude Code 会话期间生成的提示词和模型响应会被实时处理，并且 Anthropic 不会在返回响应后存储它们，但为遵守法律或打击滥用而需要保留的情况除外。

<Note>
  ZDR 不包含在标准 Claude for Enterprise 计划中，也无法从管理员设置中启用。它适用于符合条件的账户，且需要 Anthropic 单独启用。如果你的组织需要 ZDR，请[联系销售团队](https://www.anthropic.com/contact-sales?utm_source=claude_code\&utm_medium=docs\&utm_content=zero_data_retention_request)或你的 Anthropic 客户团队，以确认资格。
</Note>

Claude for Enterprise 上的 ZDR 使企业客户能够在使用 Claude Code 时实现零数据保留，并可使用管理功能：

* 按用户设置成本控制
* [分析](/docs/en/analytics)仪表板
* [服务器托管设置](/docs/en/server-managed-settings)
* 审计日志

Claude for Enterprise 上面向 Claude Code 的 ZDR 仅适用于 Anthropic 的直连平台。对于部署在 Amazon Bedrock、Google Cloud Agent Platform 或 Microsoft Foundry 上的 Claude，请参阅相应平台的数据保留政策。

## ZDR 适用范围

ZDR 涵盖 Claude for Enterprise 上的 Claude Code 推理。

<Warning>
  ZDR 按组织启用。每个新组织都需要由你的 Anthropic 客户团队单独启用 ZDR。ZDR 不会自动应用于同一账户下创建的新组织。请联系你的客户团队，为任何新组织启用 ZDR。
</Warning>

### 将 Claude Code 流量路由到你的 ZDR 组织

ZDR 适用于向已启用 ZDR 的组织进行身份验证的请求。如果开发者使用个人账户登录 Claude Code，或使用来自其他组织的 API 密钥，这些会话不在 ZDR 的覆盖范围内。若要将登录限制到你的 ZDR 组织，请部署 `forceLoginMethod` 和 `forceLoginOrgUUID` 托管设置；请参阅[将登录限制到你的组织](/docs/en/authentication#restrict-login-to-your-organization)。

### ZDR 涵盖的内容

ZDR 涵盖通过 Claude for Enterprise 上的 Claude Code 发起的模型推理调用。当你在终端中使用 Claude Code 时，Anthropic 不会保留你发送的提示词和 Claude 生成的响应。这适用于 ZDR 组织可以使用的每个模型。某些模型要求保留数据，因此无法在 ZDR 下使用；请参阅 [ZDR 下的模型可用性](#model-availability-under-zdr)。

### ZDR 不涵盖的内容

即使组织已启用 ZDR，其覆盖范围也不会扩展到以下内容。这些功能遵循[标准数据保留政策](/docs/en/data-usage#data-retention)：

| 功能 | 详情 |
| --- | --- |
| claude.ai 上的 Chat | 通过 Claude for Enterprise Web 界面进行的 Chat 对话不在 ZDR 的覆盖范围内。 |
| Cowork | Cowork 会话不在 ZDR 的覆盖范围内。 |
| Claude Code Analytics | 不存储提示词或模型响应，但会收集生产力元数据，例如账户电子邮件和用量统计。ZDR 组织无法使用贡献指标；[分析仪表板](/docs/en/analytics)仅显示用量指标。 |
| 用户与席位管理 | 账户电子邮件和席位分配等管理数据按照标准政策保留。 |
| 第三方集成 | 由第三方工具、MCP 服务器或其他外部集成处理的数据不在 ZDR 的覆盖范围内。请单独审查这些服务的数据处理做法。 |

## ZDR 下禁用的功能

为 Claude for Enterprise 上的 Claude Code 组织启用 ZDR 后，某些需要存储提示词或补全内容的功能会在后端级别自动禁用：

| 功能 | 原因 |
| --- | --- |
| [Claude Code Web](/docs/en/claude-code-on-the-web) | 需要在服务器端存储对话历史记录。 |
| 桌面应用中的[云会话](/docs/en/desktop#cloud-sessions) | 需要包含提示词和补全内容的持久会话数据。 |
| [Artifacts](/docs/en/artifacts) | 需要在 Anthropic 运营的基础设施上存储已发布的页面内容。 |
| 提交反馈（`/feedback`、`/bug`、`/share`） | 提交反馈会将对话数据发送给 Anthropic。 |
| [Remote Control](/docs/en/remote-control) | 在 Anthropic 服务器上存储会话记录，以便跨设备同步对话。 |

无论客户端如何显示，这些功能都会在后端被阻止。如果你在 Claude Code 终端启动期间看到某项禁用的功能，尝试使用它会返回错误，指明组织政策不允许该操作。

未来的功能如果需要存储提示词或补全内容，也可能被禁用。

### ZDR 下的模型可用性

已启用零数据保留的组织无法使用 Claude Fable 5。此模型类别[要求保留数据](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention#model-specific-data-retention-requirements)，因此无法处理来自 ZDR 组织的请求。对于 ZDR 组织，该模型要么不会出现在 `/model` 选择器中，要么显示为禁用状态，并附有需要禁用 ZDR 的提示；无论客户端配置如何，服务器都会拒绝对该模型的请求。

其他模型在 ZDR 下仍然可用。Fable 5 不是默认模型，而 `best` 别名会在 Fable 5 可用时解析为该模型；对于无法使用 Fable 5 的组织（包括 ZDR 组织），该别名会解析为 Opus。

## 政策违规情况下的数据保留

即使启用了 ZDR，Anthropic 仍可能在法律要求或处理《使用政策》违规行为时保留数据。如果某个会话被标记为违反政策，Anthropic 可能会保留相关输入和输出最长 2 年，这与 Anthropic 的标准 ZDR 政策一致。

## 申请 ZDR

若要为 Claude for Enterprise 上的 Claude Code 申请 ZDR，请[联系销售团队](https://www.anthropic.com/contact-sales?utm_source=claude_code\&utm_medium=docs\&utm_content=zero_data_retention_request)或你的 Anthropic 客户团队。你的客户团队将在内部提交申请，Anthropic 确认资格后会进行审查，并在你的组织中启用 ZDR。所有启用操作都会记录在审计日志中。

如果你目前通过按用量付费的 API 密钥使用 Claude Code 的 ZDR，可以迁移到 Claude for Enterprise，在保持 Claude Code 零数据保留的同时获得管理功能。请联系你的客户团队协调迁移。

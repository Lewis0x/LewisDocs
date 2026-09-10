---
title: 法律与合规
source_id: claude-code/legal-and-compliance
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/legal-and-compliance
owner: Anthropic
content_sha256: d8814ea0d3a0ae8294d2e274ace1c5f7ab09353bae9da78a5050308828b4100f
translation_of: claude-code/legal-and-compliance
translation_model: gpt-5.6
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/legal-and-compliance)

Content owner: Anthropic

> ## 文档索引
> 在以下地址获取完整的文档索引：https://code.claude.com/docs/llms.txt
> 使用此文件可在深入探索之前发现所有可用页面。

# 法律与合规

> Claude Code 的法律协议、合规认证和安全信息。

## 法律协议

### 许可条款

你对 Claude Code 的使用受以下条款约束：

* [商业条款](https://www.anthropic.com/legal/commercial-terms) - 适用于 Team、Enterprise 和 Claude API 用户
* [消费者服务条款](https://www.anthropic.com/legal/consumer-terms) - 适用于 Free、Pro 和 Max 用户

### 商业协议

无论你是直接使用 Claude API（第一方），还是通过 Amazon Bedrock 或 Google Cloud Agent Platform（第三方）访问，你现有的商业协议都将适用于 Claude Code 的使用，除非双方另有约定。

## 合规

### 医疗保健合规（BAA）

如果客户已与我们签署商业伙伴协议（BAA）并希望使用 Claude Code，那么只要该客户已签署 BAA 且启用了[零数据保留（ZDR）](/docs/en/zero-data-retention)，BAA 就会自动扩展至涵盖 Claude Code。BAA 将适用于该客户通过 Claude Code 传输的 API 流量。ZDR 按组织启用，因此每个组织都必须单独启用 ZDR 才能纳入 BAA 的覆盖范围。

## 使用政策

### 可接受使用

Claude Code 的使用受 [Anthropic 使用政策](https://www.anthropic.com/legal/aup)约束。Pro 和 Max 计划所宣传的使用上限以个人正常使用 Claude Code 和 Agent SDK 为前提。

### 身份验证和凭据使用

Claude Code 使用 OAuth 令牌或 API 密钥向 Anthropic 的服务器进行身份验证。这些身份验证方法的用途不同：

* **OAuth 身份验证**仅供 Claude Free、Pro、Max、Team 和 Enterprise 订阅计划的购买者使用，旨在支持 Claude Code 及其他 Anthropic 原生应用的正常使用。有关登录步骤，请参阅[登录你的 Claude 账户](https://support.claude.com/en/articles/13189465-logging-in-to-your-claude-account)；有关 Claude Code 如何执行 OAuth 身份验证，请参阅[身份验证](/docs/en/authentication)。
* 构建与 Claude 功能交互的产品或服务的**开发者**，包括使用 [Agent SDK](/docs/en/agent-sdk/overview) 的开发者，应通过 [Claude Console](https://platform.claude.com/) 或受支持的云服务提供商使用 API 密钥进行身份验证。Anthropic 不允许第三方开发者提供 Claude.ai 登录，也不允许其代表用户通过 Free、Pro 或 Max 计划的凭据路由请求。

Anthropic 保留采取措施执行这些限制的权利，并可能在不事先通知的情况下采取此类措施。

如果你对自己的用例可采用哪些身份验证方法有疑问，请[联系销售团队](https://www.anthropic.com/contact-sales?utm_source=claude_code\&utm_medium=docs\&utm_content=legal_compliance_contact_sales)。

## 安全与信任

### 信任与安全

你可以在 [Anthropic 信任中心](https://trust.anthropic.com)和[透明度中心](https://www.anthropic.com/transparency)找到更多信息。

### 安全漏洞报告

Anthropic 通过 HackerOne 管理安全计划。[使用此表单报告漏洞](https://hackerone.com/4f1f16ba-10d3-4d09-9ecc-c721aad90f24/embedded_submissions/new)。

***

© Anthropic PBC。保留所有权利。使用须遵守适用的 Anthropic 服务条款。

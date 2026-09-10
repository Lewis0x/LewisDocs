---
title: 其他 LLM 网关
source_id: claude-code/llm-gateway
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/llm-gateway
owner: Anthropic
content_sha256: e77e458089836ea04a710510e2710c000599f0c08c12cc75b686ad8a0a8f795a
translation_of: claude-code/llm-gateway
translation_model: gpt-5.6
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/llm-gateway)

Content owner: Anthropic

> ## 文档索引
> 在以下地址获取完整的文档索引：https://code.claude.com/docs/llms.txt
> 使用此文件可在深入探索之前发现所有可用页面。

# 其他 LLM 网关

> 通过组织已在运行的 LLM 网关路由 Claude Code。涵盖将 Claude Code 连接到网关、在组织内推广网关，以及 Claude Code 会向网关发送哪些内容。

本节介绍如何使用组织已在运行的网关产品，而非 [Claude apps gateway](/docs/en/claude-apps-gateway)。要了解网关是什么、它如何位于 Claude Code 与提供商之间，以及如何在 Claude apps gateway 和其他产品之间进行选择，请参阅[网关概述](/docs/en/gateways)。

<Note>
  * 如果你是连接现有网关的开发者：[将 Claude Code 连接到网关](/docs/en/llm-gateway-connect)
  * 如果你是在组织内推广网关的管理员：[部署并分发网关](/docs/en/llm-gateway-rollout)
  * 如果你正在配置网关产品，请参阅[网关协议参考](/docs/en/llm-gateway-protocol)
</Note>

任何公开[受支持 API 格式](/docs/en/llm-gateway-protocol#api-formats)的网关都可以使用。Anthropic 不为第三方网关产品背书，也不维护或审计这些产品；同时不支持通过任何网关将 Claude Code 路由到非 Claude 模型。请按照网关自身的文档进行部署，然后通过[下方的推广步骤](#roll-out-a-gateway)完成 Claude Code 端的配置。

## 网关提供的功能

网关为组织提供一个统一的位置来管理：

* **凭据**：提供商密钥保留在服务器端；开发者改为持有网关凭据
* **使用情况跟踪**：无论由哪个提供商处理请求，都能将使用量归属到具体开发者或团队
* **成本控制**：在一个位置执行预算和速率限制
* **审计日志**：记录每个模型请求以满足合规要求
* **提供商切换**：在网关配置中更改提供商，无需改动开发者的计算机

除提供商切换之外，以上所有功能都适用于上游为 Anthropic API 或[云服务提供商](/docs/en/third-party-integrations)的情况。要在不重新配置开发者计算机的情况下切换提供商，还需要网关无论面对何种上游都公开一个统一的 [Anthropic 格式端点](/docs/en/llm-gateway-protocol#api-formats)；公开提供商自有格式的网关会使客户端配置与该提供商绑定。

相应的权衡是，网关会成为由组织运营的基础设施。Claude Code 每个版本都会增加新功能，如果网关不转发这些功能，对应特性就会失效，因此网关产品需要随着 Claude Code 的演进持续更新。[网关协议参考](/docs/en/llm-gateway-protocol)说明了需要转发的内容。

## 推广网关

当你准备在组织内推广 LLM 网关时，无论选择哪种网关产品，步骤顺序都相同：

1. 部署网关并向其提供你的服务商凭据，使它能够对所转发的请求进行身份验证。
2. 为每位开发者签发网关凭据，以便将使用量归属到具体开发者，并能在人员离职时撤销单个凭据。
3. 通过[托管设置文件](/docs/en/settings#settings-files)和你的机密信息工具分发配置，使每台计算机都能收到基础 URL 和凭据。两者都分发后，开发者无需进行任何配置。如果尚未建立设置分发机制，开发者可按照[连接页面](/docs/en/llm-gateway-connect)自行设置变量。
4. 让每位开发者[在 Claude Code 中检查配置](/docs/en/llm-gateway-connect#check-for-an-existing-configuration)，以便在他们开始依赖网关之前暴露分发问题。

[在组织内推广 LLM 网关](/docs/en/llm-gateway-rollout)逐步讲解了整个流程，并展示了每一步需要分发的配置文件。网关只是组织设置的一部分；有关政策执行、使用情况可见性和数据处理决策，请参阅[为组织设置 Claude Code](/docs/en/admin-setup)。

## 订阅与网关

当[网关凭据变量](/docs/en/llm-gateway-connect#set-the-credential-variable)或 `apiKeyHelper` 生效时，不会使用开发者的 claude.ai 订阅：该凭据会取代当前会话的订阅登录，订阅的使用上限也不适用。此类流量按令牌计费，费用由网关所转发凭据的所有者承担，例如组织的 Anthropic Console 账户；如果网关路由到 Amazon Bedrock、Google Cloud Agent Platform 或 Microsoft Foundry，则由相应账户承担。

[`ANTHROPIC_BASE_URL`](/docs/en/llm-gateway-connect#set-the-base-url-and-credential) 是将 Claude Code 指向网关的变量。仅设置该变量而不设置网关凭据，并不会取代订阅。请求仍通过网关路由，但已保存的 claude.ai 登录仍是有效凭据，因此其使用上限和计费仍然适用。将此类流量转发给 Anthropic 的网关必须转发 `anthropic-beta` 中的 OAuth capability；请参阅[请求标头参考](/docs/en/llm-gateway-protocol#request-headers)。

## 相关页面

* [网关概述](/docs/en/gateways)：网关如何工作，以及如何在 Claude apps gateway 和其他产品之间进行选择
* [Claude apps gateway](/docs/en/claude-apps-gateway)：Anthropic 的自托管网关，提供 SSO 登录和 OTLP 遥测
* [将 Claude Code 连接到 LLM 网关](/docs/en/llm-gateway-connect)：在自己的计算机上设置基础 URL 和凭据，包括各使用界面的配置方法和故障排查表
* [在组织内推广 LLM 网关](/docs/en/llm-gateway-rollout)：管理员用于部署网关、签发开发者凭据和分发托管设置的检查清单
* [网关协议参考](/docs/en/llm-gateway-protocol)：Claude Code 向网关发送的内容，面向网关配置操作人员，涵盖端点、需要转发的标头和功能透传

---
title: 群组和预配
source_id: codex/enterprise/groups-and-provisioning
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/enterprise/groups-and-provisioning
owner: OpenAI
content_sha256: e21e38ef291936fc8e70a4eecd04242d7650f524a5e42e0c1a531f8914c4388f
translation_of: codex/enterprise/groups-and-provisioning
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/enterprise/groups-and-provisioning)

Content owner: OpenAI

# 群组和预配

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。可以通过在页面 URL 后附加 `.md` 来获取文档页面的 Markdown 版本。

群组为一组成员组织 ChatGPT 工作区访问权限，并且可以承载
自定义角色。群组成员身份与已连接系统中的本地运行时策略和
权限是分开的。

有关完整的控制模型，请参见
[角色和工作区权限](https://learn.chatgpt.com/docs/enterprise/roles-and-workspace-permissions)。

## 比较成员身份来源

每个群组都有一个权威的成员身份来源：

| 群组类型                  | 成员身份来源                       | 适用情况                                                                        |
| ------------------------- | ----------------------------------- | -------------------------------------------------------------------------------- |
| 手动管理                  | ChatGPT 工作区管理                  | 群组规模较小、临时性，或不通过目录同步管理                                        |
| 身份提供者管理            | 通过 SCIM 的您的身份提供者          | 成员身份应遵循组织的目录和成员移除流程                                          |

手动和身份提供者管理的群组可以共存。对于同步的
群组，身份提供者是成员身份来源；后续的预配
更新可以覆盖工作区侧的更改。帮助中心负责当前 SCIM 的
行为、支持的属性和设置步骤。

## 了解访问边界

SCIM 预配工作区成员身份和群组分配。它不授予
GitHub、Google Drive、Slack 或其他已连接系统中的权限。它也
不能替代本地运行时要求或平台 API 组织访问权限。

工作区 RBAC 和本地运行时要求是分开的控制系统。一个
群组可能与两者都相关，但不要从工作区群组顺序推断托管要求匹配
或优先规则。使用
[托管配置](https://learn.chatgpt.com/docs/enterprise/managed-configuration) 了解记录在案的交付和
本地优先规则。

## 使用当前的设置程序

工作区管理细节可能会更改。请使用这些来源获取当前的 UI
步骤、可用性和限制：

- [管理成员、席位类型、角色和访问权限](https://help.openai.com/en/articles/8266401-managing-members-seat-types-roles-and-access-in-chatgpt-enterprise)
- [管理群组](https://help.openai.com/en/articles/9083985-group-permissions-in-gpts)
- [SCIM 集成常见问题解答](https://help.openai.com/en/articles/10011769-openai-platform-scim-integration-faq)
- [管理工作区设置](https://help.openai.com/en/articles/8411955)

## 相关文档

- [身份验证](https://learn.chatgpt.com/docs/auth)
- [角色和工作区权限](https://learn.chatgpt.com/docs/enterprise/roles-and-workspace-permissions)
- [托管配置](https://learn.chatgpt.com/docs/enterprise/managed-configuration)
- [管理员上线指南](https://learn.chatgpt.com/docs/enterprise/admin-setup)

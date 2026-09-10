---
title: 工作区模型可用性
source_id: codex/enterprise/workspace-model-availability
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/enterprise/workspace-model-availability
owner: OpenAI
content_sha256: cfbab9bb05f1549ced4758d168721c8a21035860a7821ea04e789ba43e180c92
translation_of: codex/enterprise/workspace-model-availability
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/enterprise/workspace-model-availability)

Content owner: OpenAI

# 工作区模型可用性

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。可以通过在页面 URL 后附加 `.md` 来获取文档页面的 Markdown 版本。

模型可用性取决于产品界面和身份验证边界。
ChatGPT 工作区模型设置并不是以下环境中 Codex 的通用模型开关：
ChatGPT 桌面应用、Codex CLI、IDE 扩展、Codex 云端或平台 API。

有关完整的管理模型，请参见
[角色与工作区权限](https://learn.chatgpt.com/docs/enterprise/roles-and-workspace-permissions)。

## 确定模型边界

| 产品或身份验证边界                                                         | 模型访问权限取决于                                                                                  | 当前来源                                                                                                                |
| ------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| ChatGPT 工作区                                                                          | 工作区套餐、成员访问权限、工作区设置以及支持的角色权限                 | [ChatGPT 企业版和教育版模型与限制](https://help.openai.com/en/articles/11165333-chatgpt-enterprise-models-limits) |
| 通过 ChatGPT 登录的 ChatGPT 桌面应用、Codex CLI 和 IDE 扩展中的 Codex        | 特定客户端支持的模型以及登录的 ChatGPT 身份可用的访问权限    | [Codex 模型](https://learn.chatgpt.com/docs/models) 和当前工作区指南                                                                  |
| Codex 云端                                                                                | 托管 Codex 工作流支持的模型以及登录的 ChatGPT 身份可用的访问权限 | [Codex 模型](https://learn.chatgpt.com/docs/models) 和 [Codex 云端](https://learn.chatgpt.com/docs/cloud)                                                                 |
| 使用 API 密钥身份验证的 ChatGPT 桌面应用、Codex CLI 和 IDE 扩展中的 Codex | 与该密钥关联的 OpenAI API 组织和项目                                       | [身份验证](https://learn.chatgpt.com/docs/auth) 和 [OpenAI API 平台](https://platform.openai.com/docs/overview)                        |

请检查用户实际使用的界面的当前来源。不要
复制模型目录或假设某个 ChatGPT 模型选择器设置会对 ChatGPT
桌面应用、Codex CLI、IDE 扩展、Codex 云端和
API 平台中的 Codex 产生相同的效果。

## 将访问权限与运行时权限分开

模型访问权限决定了经过身份验证的用户在受支持的
界面上是否可以使用某模型。本地权限配置文件和托管要求
决定了本地运行开始后代理可以执行的操作，例如它可以更改哪些文件或
可以访问哪些网络目标。

权限配置文件无法授予模型访问权限。模型访问权限也无法削弱
适用于某次运行的沙盒、批准策略、网络控制或源系统
权限。

## 排查模型访问权限问题

如果用户无法选择预期的模型：

- 确认产品界面和登录方法。
- 确认使用的是哪个 ChatGPT 工作区，或平台 API 的哪个组织和项目。
- 审查该身份验证边界的当前访问控制。
- 检查所选的本地客户端或 Codex 云端是否支持该模型。

## 当前来源

- [ChatGPT 企业版和教育版模型与限制](https://help.openai.com/en/articles/11165333-chatgpt-enterprise-models-limits)
- [管理工作区设置](https://help.openai.com/en/articles/8411955)
- [基于角色的访问控制](https://help.openai.com/en/articles/11750701-rbac)
- [Codex 模型](https://learn.chatgpt.com/docs/models)
- [按套餐划分的 Codex 功能可用性](https://learn.chatgpt.com/docs/pricing#feature-availability)
- [身份验证](https://learn.chatgpt.com/docs/auth)

## 相关文档

- [管理员部署指南](https://learn.chatgpt.com/docs/enterprise/admin-setup)
- [群组与预配](https://learn.chatgpt.com/docs/enterprise/groups-and-provisioning)
- [角色与工作区权限](https://learn.chatgpt.com/docs/enterprise/roles-and-workspace-permissions)
- [托管配置](https://learn.chatgpt.com/docs/enterprise/managed-configuration)

---
title: 角色和工作区权限
source_id: codex/enterprise/roles-and-workspace-permissions
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/enterprise/roles-and-workspace-permissions
owner: OpenAI
content_sha256: fe76d64669574f0cca8bcc307a7d3fa0141ec86ff404df0c0a3e0bb2d9903572
translation_of: codex/enterprise/roles-and-workspace-permissions
translation_model: k3
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/enterprise/roles-and-workspace-permissions)

Content owner: OpenAI

# 角色和工作区权限

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。可以通过在页面 URL 后附加 `.md` 来获取文档页面的 Markdown 版本。

管理跨越六个控制边界。在一个边界授予访问权限
并不会在另一个边界授予访问权限。请将此页面用作标准映射，
然后访问链接的源以获取当前设置和程序。

在工作区设置中，**Codex Local** 是用于某些本地
访问和访问令牌控件的分组标签，而不是单独的产品或客户端。单个
组内的控件可以具有不同的作用域。当前的 **允许成员
使用 Codex Local** 工作区权限涵盖了在 ChatGPT 桌面
应用、Codex CLI 和 IDE 扩展中的本地使用。托管配置是一个独立的层，
用于约束这些客户端中所涵盖功能的受支持运行时行为。功能和
实际要求可能因客户端和版本而异。

## 了解控制边界

| 边界          | 控制的内容                                                                                                                                                                                      | 不控制的内容                                                                          | 当前来源                                                                                                                                                                                           |
| ----------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ChatGPT 工作区 | 成员资格、席位、内置管理角色，以及对受支持的工作区功能的基于角色的访问权限                                                                                               | 本地代理权限、平台 API 组织访问权限，或连接服务中的权限 | [ChatGPT 工作区访问权限](https://help.openai.com/en/articles/8266401-managing-members-seat-types-roles-and-access-in-chatgpt-enterprise) 和 [RBAC](https://help.openai.com/en/articles/11750701-rbac) |
| 本地客户端     | ChatGPT 桌面应用、Codex CLI 和 IDE 扩展中涵盖功能的运行时行为，包括批准、文件系统和网络访问、权限配置文件以及允许的集成 | ChatGPT 席位、功能或模型授权，或对外部数据的访问权限                         | [托管配置](https://learn.chatgpt.com/docs/enterprise/managed-configuration) 和 [权限](https://learn.chatgpt.com/docs/permissions)                                                                                                   |
| Codex 云端       | 使用托管 Codex 工作流及向用户提供的云环境的资格                                                                                                       | 本地运行时策略或由源系统授予的仓库权限                    | [云环境](https://learn.chatgpt.com/docs/environments/cloud-environment)                                                                                                                                              |
| 平台 API      | 用于 API 身份验证工作的组织和项目成员资格、API 密钥、模型访问权限、使用情况和账单                                                                                            | ChatGPT 工作区成员资格、本地客户端访问权限或 Codex 云端访问权限                         | [OpenAI API 平台](https://platform.openai.com/docs/overview)                                                                                                                                         |
| 插件           | 插件的可用性和安装、捆绑技能、连接器访问权限以及支持的连接器操作                                                                                               | 已连接服务中的授权或更广泛的本地和云端运行时权限            | [插件控制](https://learn.chatgpt.com/docs/enterprise/apps-and-connectors)                                                                                                                                                 |
| 已连接的系统 | 经过身份验证的账户在源系统中可以访问哪些存储库、文件、消息和操作                                                                                            | ChatGPT 工作区、插件、Codex 云端或平台 API 权限                              | 已连接服务的管理和访问控制                                                                                                                                               |

请求必须通过适用于它的每个边界。例如，工作区
访问权限可以使插件可用，但已连接的服务仍然决定
登录账户可以读取哪些数据。本地权限配置文件可以限制
在受支持的本地客户端中运行，但它无法授予工作区功能或
模型。

## 分配工作区访问权限

ChatGPT 工作区管理将产品访问权限与管理
权限分离开来。工作区套餐和成员的席位决定了哪些产品
界面可用。内置的工作区角色决定了谁可以管理
工作区。基于角色的访问控制 (RBAC) 决定了哪些受支持的
功能可供成员使用。

管理员可以通过群组分配自定义角色，并且成员可以接收
来自多个群组的访问权限。由于可用席位、角色和权限会
随产品和套餐的更新而变化，请使用帮助中心获取当前的
权限列表和设置步骤：

- [管理成员、席位类型、角色和访问权限](https://help.openai.com/en/articles/8266401-managing-members-seat-types-roles-and-access-in-chatgpt-enterprise)
- [配置基于角色的访问控制](https://help.openai.com/en/articles/11750701-rbac)
- [管理群组](https://help.openai.com/en/articles/9083985-group-permissions-in-gpts)

## 应用本地运行时策略

本地运行时策略限制了 ChatGPT 桌面
应用、Codex CLI 和 IDE 扩展中涵盖的功能。云端管理的附加要求
取决于支持的 ChatGPT 登录和套餐资格。权限配置文件
和托管要求可以限制命令、文件系统访问、网络
访问、审批及其他本地运行时行为。它们不会改变
用户的席位、工作区角色、模型权限或外部
系统中的权限。

用户可以选择内置或自定义权限配置文件，前提是本地策略
允许。管理员可以通过受支持的托管配置渠道
分发默认设置和要求。请参阅 [权限](https://learn.chatgpt.com/docs/permissions)
了解配置文件行为，并参阅 [托管配置](https://learn.chatgpt.com/docs/enterprise/managed-configuration)
了解要求、交付和优先级。

## 相关文档

- [管理员上线指南](https://learn.chatgpt.com/docs/enterprise/admin-setup)
- [组和预配](https://learn.chatgpt.com/docs/enterprise/groups-and-provisioning)
- [工作区模型可用性](https://learn.chatgpt.com/docs/enterprise/workspace-model-availability)
- [访问令牌](https://learn.chatgpt.com/docs/enterprise/access-tokens)
- [托管配置](https://learn.chatgpt.com/docs/enterprise/managed-configuration)
- [身份验证](https://learn.chatgpt.com/docs/auth)

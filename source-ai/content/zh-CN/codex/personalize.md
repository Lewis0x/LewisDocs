---
title: 个性化 ChatGPT
source_id: codex/personalize
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/personalize
owner: OpenAI
content_sha256: 7d2586251daad108229deb8fc0dbc538247c2315de3526baff8f5442046f44dd
translation_of: codex/personalize
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/personalize)

Content owner: OpenAI

# 个性化 ChatGPT

> 完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。可以通过在页面 URL 后附加 `.md` 来获取文档页面的 Markdown 版本。

个性化 ChatGPT，使其回复和工作风格更好地符合您的
偏好。您可以控制启用哪些个性化功能，并可以
随时在 ChatGPT 桌面应用程序设置中进行更改。

## 选择一种性格

在以下位置选择 **友好**、**务实** 或 **无** 作为默认性格
**设置 > 个性化**。性格会改变 ChatGPT 的沟通方式；
它不会改变模型能够做什么。

## 添加自定义指令

使用自定义指令来设定您希望 ChatGPT 在所有
聊天中遵循的偏好，例如您偏好的回复风格。在 Codex 中，这些个人
指令存储在您的全局 `AGENTS.md` 文件中。项目和
代码库也可以提供它们自己的指令。

[了解 `AGENTS.md` 指令是如何工作的](https://learn.chatgpt.com/docs/agent-configuration/agents-md)。

## 使用记忆延续上下文

[记忆](https://learn.chatgpt.com/docs/customization/memories) 允许 ChatGPT 将早期聊天中的有用上下文
带入未来的工作中。它们可以包括稳定的偏好、重复的工作流程、
项目规范以及其他您原本需要重复的上下文。

记忆与所需的项目指导是分开的。请将必须始终适用的指令保留在
`AGENTS.md` 或签入的项目文档中。

## 使用 Chronicle 添加最近的屏幕上下文

[Chronicle](https://learn.chatgpt.com/docs/customization/chronicle) 是一项可选的研究预览版，可以
用最近的屏幕上下文来增强记忆。它适用于符合条件的
macOS 桌面应用程序中的 ChatGPT Pro 订阅者，并且需要屏幕录制
和辅助功能权限。

查看 Chronicle 的隐私、安全、存储和速率限制注意事项
在启用它之前。您可以随时暂停或禁用 Chronicle。

## 管理个性化

打开 [**设置**](codex://settings) 以更新您的性格、自定义
指令、记忆和其他可用的个性化控制。请参见
[ChatGPT 桌面应用程序设置](https://learn.chatgpt.com/docs/reference/settings) 以获取
日常偏好的概述。

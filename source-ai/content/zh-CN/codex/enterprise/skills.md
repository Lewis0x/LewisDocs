---
title: 技能控制
source_id: codex/enterprise/skills
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/enterprise/skills
owner: OpenAI
content_sha256: 63c1bc39bbbeef83e2014509ebee7da4a755e8aec619b32094f905f655268fb1
translation_of: codex/enterprise/skills
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/enterprise/skills)

Content owner: OpenAI

# 技能控制

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。通过在页面 URL 后附加 `.md`，可以获取文档页面的 Markdown 版本。

技能是由指令和支持资源组成的可重用工作流。
ChatGPT 工作区技能，被覆盖的本地功能所使用的文件系统技能
（在 ChatGPT 桌面应用、Codex CLI 或 IDE 扩展中），以及
打包这些技能的插件具有独立的生命周期和访问控制。

有关完整的管理模型，请参见
[角色与工作区权限](https://learn.chatgpt.com/docs/enterprise/roles-and-workspace-permissions)。

<a id="distinguish-the-distribution-models"></a>

## 技能分发与管理

| 分发模型                | 用途                                                                                                | 管理边界                                                                                       |
| ----------------------- | ---------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| ChatGPT 工作区技能      | 通过受支持的 ChatGPT 工作区功能共享或安装已批准的工作流                                              | ChatGPT 工作区技能权限和生命周期控制                                                          |
| 本地文件系统技能       | 从仓库、用户、管理员或打包的系统位置加载已安装的工作流                                              | 文件系统分发、本地客户端配置和运行时权限                                                      |
| 插件                    | 将一个或多个技能与可选的连接器、MCP 服务器、钩子和展示元数据打包在一起                              | 插件可用性和安装，加上对每个打包功能的单独控制                                                |

ChatGPT 工作区技能分发、本地文件系统技能安装和
特定于界面的插件安装是独立的路径。移动技能不会
转移 ChatGPT 工作区所有权、共享、角色分配、插件
安装状态或连接器授权。

插件可在 Web 端的 ChatGPT Work、ChatGPT 桌面应用中的 ChatGPT Work 和 Codex
中使用，也可以通过 Codex CLI 插件浏览器使用。它们
在 Chat、IDE 扩展或移动端不可用。
那些受支持的界面从一个由 ChatGPT 和 Codex 共享的通用目录中
提取公共插件。

## 所有权控制

请参见 [构建技能](https://learn.chatgpt.com/docs/build-skills) 了解文件系统位置和编写，
[ChatGPT 中的技能](https://help.openai.com/en/articles/20001066-skills-in-chatgpt)
了解当前工作区流程，以及 [构建插件](https://developers.openai.com/plugins/build/plugins) 了解
插件打包。

ChatGPT 工作区控制不会安装本地文件系统技能或插件。
文件系统分发不会分配 ChatGPT 工作区所有权或角色。
插件安装不会授予对连接器、MCP 服务器或
已连接服务的访问权限。请通过拥有相应功能的控制界面
配置各项功能。

## 相关文档

- [技能与插件](https://learn.chatgpt.com/docs/skills-and-plugins)
- [插件](https://learn.chatgpt.com/docs/plugins)
- [构建技能](https://learn.chatgpt.com/docs/build-skills)
- [构建插件](https://developers.openai.com/plugins/build/plugins)
- [管理员推广指南](https://learn.chatgpt.com/docs/enterprise/admin-setup)
- [插件控制](https://learn.chatgpt.com/docs/enterprise/apps-and-connectors)

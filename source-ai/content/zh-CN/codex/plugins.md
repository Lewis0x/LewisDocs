---
title: 插件
source_id: codex/plugins
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/plugins
owner: OpenAI
content_sha256: 0c830703fd76a00931619e4ebbc2aabe9506281da52571e64dd119147c285897
translation_of: codex/plugins
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/plugins)

Content owner: OpenAI

# 插件

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。可以通过在页面 URL 后附加 `.md` 来获取文档页面的 Markdown 版本。

## 概述

插件在 ChatGPT 和 Codex 中将功能打包成可重用的工作流。它们
可以包含技能、连接器，或两者兼有。这两个产品都使用一个通用插件
目录，因此可以从它们支持的
界面中发现相同的公开插件。

插件在 Web 端的 ChatGPT Work 以及 ChatGPT 桌面应用程序中的 ChatGPT Work 或
Codex 中可用。Codex
CLI 也有一个用于 Codex 环境的插件浏览器。插件在
Chat、IDE 扩展或移动端中不可用。



在 ChatGPT 桌面应用程序中，选择 ChatGPT 并在切换器中打开 Work，或者选择
Codex。然后打开**插件**以浏览、安装和使用插件。已安装的
插件可以为新聊天添加技能、连接器和 MCP 工具。









扩展 ChatGPT 和 Codex 的功能，例如：

- 安装 Codex Security 插件以扫描授权代码并确认
  可能存在的漏洞发现。
- 安装 Gmail 插件以使用 Gmail。
- 安装 Google Drive 插件以跨 Drive、Docs、Sheets 和
  Slides 进行工作。
- 安装 Slack 插件以总结频道或起草回复。

一个插件可以包含以下一个或多个部分：

- **技能：**针对特定类型工作的可重用指令。ChatGPT 和
  Codex 可以在需要时加载它们，以便遵循正确的步骤并使用
  适用于任务的正确参考资料或辅助脚本。
- **连接器：**连接到 GitHub、Slack 或 Google Drive 等工具，以便
  ChatGPT 和 Codex 可以从这些工具读取信息并在其中
  采取行动。连接器公开工具，并可以选择包含自定义 UI。
- **MCP 服务器：**让 ChatGPT 和 Codex 访问更多工具或
  共享信息的服务，这些信息通常来自本地项目之外的系统。它们是
  连接器背后的服务。它们定义工具、强制执行身份验证、返回
  结构化数据，并针对外部系统执行操作。
- **浏览器扩展：**插件的工作流所需的浏览器
  能力。
- **钩子：**在配置的生命周期节点运行的命令。在启用
  插件钩子之前，请对其进行审查和信任。
- **计划任务模板：**循环任务的可重用
  起点（在提供计划任务功能的情况下）。

您可以通过发布插件到市场源来共享插件，例如
项目或团队的仓库市场。请参见 [构建插件](https://developers.openai.com/plugins/build/plugins)
以获取市场设置、打包和分发指南。

如果您正在构建集成，请从
[构建 MCP 服务器](https://developers.openai.com/plugins/build/mcp-server) 开始。
如果插件需要自定义 UI，请使用
[可选 UI 指南](https://developers.openai.com/plugins/build/chatgpt-ui)。

## 使用和安装插件

<a id="plugin-directory-in-the-codex-app"></a>



### 通用插件目录

ChatGPT 和 Codex 使用相同的公开插件目录。要浏览和安装
受支持的图形界面中的插件：

- 在 Web 端，在切换器中打开 Work 并打开**插件**。
- 在 ChatGPT 桌面应用程序中，选择 ChatGPT 并在切换器中打开 Work，或者选择
  Codex。然后打开**插件**。



<CodexScreenshot
  alt="ChatGPT 桌面应用程序中的插件目录"
  lightSrc="/images/codex/plugins/directory.webp"
  darkSrc="/images/codex/plugins/directory-dark.webp"
/>





插件目录将插件组织到不同的选项卡中：

- **OpenAI：**由 OpenAI 构建的插件。
- **您的工作区名称：**由您的工作区提供的插件。
- **个人：**个人市场插件，包括**我创建的**和
  **与我共享的**部分（当这些插件可用时）。

使用单独的**已安装**行来查看您已安装的插件。

### 安装并使用插件

一旦您打开插件目录：

<WorkflowSteps>

1. 搜索或浏览插件，然后打开其详细信息。
2. 选择加号按钮以安装该插件。
3. 如果插件需要连接器，请在提示时进行连接。一些插件
   会在安装过程中要求您进行身份验证。其他插件则会等到您第一次
   使用它们时才要求。
4. 安装完成后，开启一个新的对话，并要求 ChatGPT 或 Codex 使用
   该插件。

</WorkflowSteps>

安装插件后，您可以直接在提示词窗口中使用它：





<CodexScreenshot
  alt="插件页面上的已安装插件"
  lightSrc="/images/codex/plugins/plugin-github-invoke.png"
  darkSrc="/images/codex/plugins/plugin-github-invoke-dark.png"
/>







  

    
直接描述任务

    

      提出您想要的结果，例如“总结今天未读的 Gmail
      会话”或“从 Google Drive 中提取最新的发布说明。”
    

    

      当您希望 ChatGPT 为任务选择正确的已安装工具时，请使用此方法。
    

  


  

    
选择特定插件

    

      键入 `@` 以显式调用插件或其捆绑技能之一。
    

    

      当您想要具体指定 ChatGPT 应使用哪个插件或技能时，请使用此方法。参见 [技能与插件](https://learn.chatgpt.com/docs/skills-and-plugins)。
    







<a id="api-key-availability"></a>



### API 密钥可用性

如果您[使用 OpenAI API
密钥登录 Codex](https://learn.chatgpt.com/docs/auth#sign-in-with-an-api-key)，您可以在 Codex CLI 和 ChatGPT 桌面应用程序中的 Codex 中浏览、安装和管理
受支持的 OpenAI 精选插件。由于某些插件的连接流程需要不受支持的 OAuth 功能，因此无法通过 API 密钥身份验证来使用这些插件。请在
[平台使用页面](https://platform.openai.com/usage) 上查看插件使用情况。



### 权限和数据共享的工作方式





当插件功能通过 Codex 主机运行时，将应用主机的[沙盒和
批准策略](https://learn.chatgpt.com/docs/agent-approvals-security)。
与外部服务的连接使用该服务自身的身份验证和
访问控制。



- 安装后开始新对话或 CLI 会话时，捆绑技能将变为可用。
- 如果插件包含连接器，当前产品可能会在设置期间或首次使用时提示您安装
  或登录这些连接器。
- 如果插件包含 MCP 服务器，在您使用它们之前可能需要额外设置或
  身份验证。
- 当 ChatGPT 通过捆绑连接器发送数据时，将适用该服务的条款和隐私
  政策。

### 移除插件

要移除插件，请从受支持的插件浏览器中打开它，并在该操作可用时选择
**卸载插件**。工作区安装的或
默认插件可能不提供该操作；您的
工作区管理员会对其进行控制。

卸载插件会从该 ChatGPT 或 Codex
环境中移除插件包，但捆绑的连接器会保持连接状态，直到您在
ChatGPT 中管理它们。

## 构建您自己的插件

如果您想创建、测试或分发您自己的插件，请参阅
[构建插件](https://developers.openai.com/plugins/build/plugins)。该页面涵盖了本地脚手架、
手动市场设置、工作区共享、插件清单和打包
指南。

如果您的插件包含服务器支持的功能，请参阅
[构建 MCP 服务器](https://developers.openai.com/plugins/build/mcp-server)。
MCP 工具无需自定义 UI 即可工作，或者在视觉界面有助于工作流程时返回 UI。

当您的插件准备好接受审查时，请参阅
[提交插件](https://developers.openai.com/plugins/deploy/submission) 以了解 OpenAI 平台提交
流程、所需权限、审查材料、MCP 检查和测试用例
要求。

## 插件指南

- [录制与回放](https://learn.chatgpt.com/docs/extend/record-and-replay)：向 ChatGPT 展示一次工作流
  并将其转化为可重复使用的技能。
- [Codex 安全插件](https://learn.chatgpt.com/docs/security/plugin)：扫描授权代码，
  确认发现的问题，并准备经过审查的修复程序。

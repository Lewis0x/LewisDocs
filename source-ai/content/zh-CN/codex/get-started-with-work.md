---
title: 开始使用 ChatGPT Work
source_id: codex/get-started-with-work
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/get-started-with-work
owner: OpenAI
content_sha256: 373c10620448f4aeef2d83e863541b3ba21e1bf1dc5d77dd224f1f002a0d537a
translation_of: codex/get-started-with-work
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/get-started-with-work)

Content owner: OpenAI

# 开始使用 ChatGPT Work

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。可以通过在页面 URL 后附加 `.md` 来获取文档页面的 Markdown 版本。

<VideoPlayer src="https://cdn.openai.com/devhub/superapp-video-v1.mp4" />

<a id="introducing-work-mode"></a>

## ChatGPT Work 简介

ChatGPT Work 是一种将实际工作委派给 ChatGPT 的方式。

当你想要获得答案、解释、进行头脑风暴或简短草稿时，请使用聊天。
当你希望 ChatGPT 完成具有明确结果的任务时，请使用 ChatGPT Work，例如一个
简报、演示文稿、分析、定期更新、工作流，或者你可以审查和
使用的文件。了解更多关于 [同时使用聊天和 ChatGPT Work](https://learn.chatgpt.com/docs/use-chatgpt) 的信息。

ChatGPT Work 可以使用你的文件、插件和批准的工具来检索信息，
创建完成的文件、运行工作流，并完成准备好供你
审查的工作。你可以跟踪进度、回答问题、更改方向，并
批准重要操作。

在 [桌面应用程序](https://learn.chatgpt.com/docs/app) 上，当这些工具可用时，ChatGPT Work 还可以使用本地文件、应用程序和
浏览器。

如果你曾使用 Codex 进行非编码工作，你可以留在 Codex 或使用
ChatGPT Work 作为替代。ChatGPT Work 为你提供相同的核心功能，并
提供专为日常工作设计的体验。

## 首先尝试什么

<VideoPlayer src="https://cdn.openai.com/devhub/videos-learn/selectnoonboarding.mp4" />

首先，切换到 **Work**。然后选择你的第一个任务。
好的任务具有明确的结果、一些源材料以及你可以
审查的输出。

### 选择本地或云端工作

在桌面应用程序中，打开标有 **本地工作** 的编辑器控件。如果
**Cloud** 作为一个选项出现，当你希望 ChatGPT Work 保持
运行（在你关闭应用程序或关闭计算机之后），或者当你想要
从网络或移动应用程序继续聊天时，请选择它。当
任务需要你计算机上的文件或应用程序时，请保持选择 **本地工作**。

对于随着时间推移研究或检查网站的定期任务，云端也很有用，
因为它们的运行不依赖于你的计算机处于唤醒状态。

以下是你可以开始尝试的三个常见用例：

### 创建演示文稿

使用 ChatGPT Work 将笔记、文档、研究或会议材料转化为结构化的
演示文稿。

<CodexScreenshot
  alt="在 ChatGPT Work 中创建的演示文稿"
  lightSrc="/codex/get-started-with-work/create-presentation.webp"
  darkSrc="/codex/get-started-with-work/create-presentation.webp"
  maxHeight={520}
  class="my-6 p-4 md:p-8"
/>

<PromptComponent
  openInCodex
  actionsPlacement="header"
  label="示例提示词"
  prompt={`Review the attached source materials and create an eight-slide presentation for [audience]. Focus on the main themes, include supporting evidence, and flag anything that needs human review. Return a draft for my review.`}
/>

### 创建比较电子表格

使用 ChatGPT Work 将笔记、文件或研究转化为一个比较
选项并帮助你做出决定的电子表格。

<CodexScreenshot
  alt="在 ChatGPT Work 中创建的比较电子表格"
  lightSrc="/codex/get-started-with-work/comparison-spreadsheet.webp"
  darkSrc="/codex/get-started-with-work/comparison-spreadsheet.webp"
  maxHeight={520}
  class="my-6 p-4 md:p-8"
/>

<PromptComponent
  openInCodex
  actionsPlacement="header"
  label="示例提示词"
  prompt={`Create a spreadsheet comparing the options for [decision]. Use the attached notes and source materials. Include the most important criteria, score each option, flag risks or missing information, and add a summary tab with a recommendation and next steps.`}
/>

### 设置定期更新

当你希望 ChatGPT Work 随着时间的推移重复、监控或刷新某些内容时，
请使用计划任务。

<CodexScreenshot
  alt="在 ChatGPT Work 中计划的定期更新"
  lightSrc="/codex/get-started-with-work/recurring-update.webp"
  darkSrc="/codex/get-started-with-work/recurring-update.webp"
  maxHeight={520}
  class="my-6 p-4 md:p-8"
/>

<PromptComponent
  openInCodex
  actionsPlacement="header"
  label="示例提示词"
  prompt={`Every Monday morning, review new updates from @Slack and @Google Drive for [project]. Refresh the meeting agenda with decisions, blockers, owners, and open questions. Send me a draft before sharing it.`}
/>

了解更多关于 [计划任务](https://learn.chatgpt.com/docs/automations?surface=app) 的信息。

<a id="best-practices-for-using-work"></a>
<a id="best-practices-for-using-work-mode"></a>

## 使用 ChatGPT Work 的最佳实践

当您希望 ChatGPT 完成任务、创建文件或管理长期工作
时，请使用 ChatGPT Work。它非常适合以下任务：

- 使用多个来源、插件、工具或步骤。
- 手动完成需要花费大量时间。
- 生成您将审查、编辑或重复使用的输出。
- 需要随着时间的推移进行重复、监控或更新。

为了获得更好的结果，请告知 ChatGPT 您需要的结果、要使用的来源或插件、
需要遵循的任何约束、理想的效果，以及何时停止以供
审查或批准。

**与其这样：** 为我制作一个关于我们客户研究的演示文稿。

<PromptComponent
  openInCodex
  actionsPlacement="header"
  label="提示词示例"
  prompt={`Review the attached interview notes and survey results. Create an eight-slide presentation for the product leadership meeting. Focus on the three most common customer problems, include supporting evidence, separate findings from recommendations, and flag any claims that are not well supported. Use @Google Drive for the source docs. Return a draft for my review before treating it as final.`}
/>

了解更多关于 [为 ChatGPT Work 编写提示词](https://learn.chatgpt.com/docs/prompting#prompting-for-work)的信息。

## 添加插件以获取更多上下文和更好的输出

<CodexScreenshot
  alt="ChatGPT Work 中的插件库"
  lightSrc="/codex/get-started-with-work/plugins.webp"
  darkSrc="/codex/get-started-with-work/plugins.webp"
  maxHeight={520}
  class="my-6 p-4 md:p-8"
/>

插件将 ChatGPT Work 连接到您团队使用的工具，例如 Slack、Google Drive、
SharePoint、电子邮件、日历、客户关系管理系统和
项目跟踪器。

- 在左侧边栏中选择 **插件** 以查看插件库。
- 安装与您的工作最相关的插件。
- 要将 ChatGPT 指向特定工具，请在提示词中输入 `@` 和插件名称。

了解更多关于 [插件](https://learn.chatgpt.com/docs/plugins)的信息。

<a id="use-work-mode-efficiently"></a>

## 高效使用 ChatGPT Work

ChatGPT Work 最适合涉及多个步骤、来源或
工具的重要任务，或需要完成交付物的任务。更长或更复杂的任务可能会使用
更多额度，因为 ChatGPT 会为您做更多的事情。请关注
已完成结果的价值，而不是提示词的数量。

通过设定有用的界限来保持任务专注。例如：“仅使用
这些来源”、“比较前五个选项”或“在发送任何内容之前停止
”。

对于快速提问、简短重写以及您
只需要建议的决策，请改用聊天（Chat）。

了解更多关于 [高效工作](https://learn.chatgpt.com/docs/prompting#prompting-for-work)的信息。

## 更多用例

探索常见团队和任务的实际 ChatGPT Work 工作流。

<CodexCollectionList
  slugs={[
    "productivity-and-collaboration",
    "business-operations",
    "data-science",
    "finance",
    "sales",
    "life-sciences",
    "education",
  ]}
/>

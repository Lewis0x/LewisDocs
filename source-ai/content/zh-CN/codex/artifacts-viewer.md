---
title: 处理文件
source_id: codex/artifacts-viewer
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/artifacts-viewer
owner: OpenAI
content_sha256: db0ff3a369f56c899a2d8f6dee916501dd9220a49245b2647ef002671895dcc2
translation_of: codex/artifacts-viewer
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/artifacts-viewer)

Content owner: OpenAI

# 处理文件

> 完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。可以通过在页面 URL 后附加 `.md` 来获取文档页面的 Markdown 版本。

当任务需要生成文件时，请向 ChatGPT 提供源数据、预期的文件类型、
结构以及对任务至关重要的审查标准。预览和审查
工具取决于您所使用的界面。



ChatGPT 桌面应用程序可以在聊天旁边预览生成的文档、演示文稿、
电子表格和 PDF 文件。使用注释指向
预览的特定部分并请求针对性的修改。











<CodexScreenshot
  alt="ChatGPT 桌面应用程序显示生成的演示文稿预览"
  lightSrc="/images/codex/app/artifact-viewer-light.webp"
  darkSrc="/images/codex/app/artifact-viewer-dark.webp"
  maxHeight="420px"
  variant="no-wallpaper"
  class="my-8"
/>



## 创建文件以供审查

对于电子表格和演示文稿，请描述您期望的工作表、列、图表、
幻灯片部分和检查内容。要求 ChatGPT 说明它将
输出保存在哪里以及它是如何检查结果的。

<a id="refine-files-with-annotations"></a>



<a id="review-and-refine-files"></a>



## 使用注释完善文件

注释让您能够指向文件的特定部分并告诉 ChatGPT
需要更改什么。可用于代码、Markdown
文件和网站的相同注释工作流程也适用于文档、电子表格和
演示文稿。

例如，您可以：

- 选择网站上的导航栏，并要求 ChatGPT 更改其字体。
- 突出显示投资论点中的某项声明并要求提供其来源。
- 标记幻灯片上的图表并要求提供更清晰的标签。

ChatGPT 会将所选区域作为您请求的上下文，因此您可以完善
文件，而无需重新开始或更改您已经喜欢的部分。
在初稿完成且工作需要
审查和迭代时，注释特别有用。





## 审查和完善文件

在任务运行时使用聊天侧边栏。它可以展示代理的计划、
来源、生成的文件和聊天摘要，以便您可以引导工作、
检查生成的文件并请求再次处理。

要求 ChatGPT 说明每个文件的保存位置以及它是如何验证
结果的。使用预览检查输出，然后针对需要再次处理的
结构、数据、布局或验证提供有针对性的反馈。



## 相关文档

- [图像生成](https://learn.chatgpt.com/docs/image-generation)

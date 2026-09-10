---
title: 图像输入
source_id: codex/image-inputs
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/image-inputs
owner: OpenAI
content_sha256: 62baa8a6c719b4095038864c9c3df1139beaeacda9dbb5493ce32189b72f3d98
translation_of: codex/image-inputs
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/image-inputs)

Content owner: OpenAI

# 图像输入

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。可以通过在页面 URL 后附加 `.md` 来获取文档页面的 Markdown 版本。

当任务依赖于视觉上下文时，请将图像添加到提示中，例如错误
屏幕截图、界面设计、架构图或现有资源。解释
ChatGPT 应该检查什么以及您想要什么结果；不要仅依赖图像
来传达任务。



按住 <kbd>Shift</kbd> 键的同时将图像拖动到提示编辑器中，以将其
作为上下文包含在内。您也可以让 ChatGPT 检查您系统上的图像，或者使用
屏幕截图工具来验证另一个应用程序中的工作。









## 围绕图像编写提示

说出图像显示的内容，指出重要的区域，并说明输出
和约束条件。如果您附加了多张图像，请识别每一张并解释
ChatGPT 应该如何比较它们。

例如：

```text
Compare this checkout screen with the design. Fix spacing and typography only;
do not change behavior. Verify the result with a new screenshot.
```

## 使用正确的图像功能

当您希望 ChatGPT 检查视觉参考时，请使用图像输入。使用
[图像生成](https://learn.chatgpt.com/docs/image-generation) 当您希望 ChatGPT
创建或编辑图像时。

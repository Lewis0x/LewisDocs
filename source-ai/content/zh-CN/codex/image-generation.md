---
title: 图像生成
source_id: codex/image-generation
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/image-generation
owner: OpenAI
content_sha256: f63c879b03b44827dcb530ec62d90722503fe0527ba4d646fba23e296cc2eea7
translation_of: codex/image-generation
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/image-generation)

Content owner: OpenAI

# 图像生成

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。文档页面的 Markdown 版本可通过在页面 URL 后附加 `.md` 来获取。

要求 ChatGPT 生成或编辑图像。将图像生成用于 UI 素材、
横幅、背景、插图、精灵表和占位符等您想
与代码一起或在 ChatGPT 聊天中创建的内容。



从应用的消息撰写框中请求图像。当您希望
ChatGPT 转换现有素材或将其用作视觉指导时，请添加参考图像。










## 生成或编辑图像

用自然语言描述图像。当您希望
ChatGPT 转换或扩展现有素材时，请添加参考图像。



在您的提示词中包含 `$imagegen` 以明确
调用图像生成技能。

内置图像生成使用 `gpt-image-2`，并计入您的通用
Codex 使用限制。平均而言，图像生成消耗包含限制的速度比
不带图像生成的类似轮次快 3–5 倍，具体取决于图像质量
和大小。对于较大批次，请在您的环境中设置 `OPENAI_API_KEY`，并要求
ChatGPT 通过 API 生成图像，以便适用 API 定价。



## 编写有效的图像提示词

一个有用的图像提示词通常只有一到三个清晰的句子。描述
决定结果是否成功的细节：

- 解释图像的用途或目标受众。
- 指出主要对象和正在发生的事情。
- 描述背景、构图和视觉风格。
- 在重要时添加取景、尺寸、光照、颜色或材质。
- 说明约束条件，包括图像不得包含的任何内容。

首选具体的视觉语言而非宽泛的反应。例如，描述
光线的来源，而不是要求“美丽的灯光”。重复任何
必须保持不变的要求。

<PromptComponent
  actionsPlacement="header"
  label="Example prompt"
  maxHeightClass="max-h-64"
  prompt={`Create a clean editorial illustration for an employee onboarding guide. Show a person organizing a project at a desk with a laptop, notebook, and simple progress checklist. Use soft daylight from a window on the left, restrained colors, and a modern, approachable style. Keep the background minimal. Do not include logos, text, or futuristic imagery.`}
/>

## 优化结果

从核心想法开始，然后进行小的、有针对性的修改。一次调整一个
元素，以便构图和其他重要细节不会偏移。
您也可以选择图像的特定区域并描述该
区域的更改。

编辑现有图像时，请准确说明应更改的内容以及必须
保持不变的内容。

<PromptComponent
  actionsPlacement="header"
  label="Example prompt"
  prompt={`Edit the attached image. Replace only the mug with a small potted plant. Preserve the person, desk layout, lighting, colors, crop, and every other detail exactly. Do not add text or logos.`}
/>

对于更广泛的修改，请保持反馈直接且可操作：使图像
更亮、降低色彩饱和度、简化背景，或者在改变
风格的同时保持构图。

## 使用多张参考图像

当一张图像定义内容而另一张
定义风格、布局或其他视觉方向时，使用一小组参考图像。按
顺序识别每张图像，并解释图像之间的关系。组合元素时，使用空间术语，例如
前景、背景、左侧和右侧。

<PromptComponent
  actionsPlacement="header"
  label="Example prompt"
  prompt={`Image 1 is the product photo to edit. Image 2 is the style reference. Keep the product, camera angle, layout, and objects from image 1, but apply the clean line work, muted palette, and soft shadows from image 2. Keep the product centered and leave the upper-right corner clear for later copy.`}
/>

## 向图像添加文本

保持图像中的文本简短并准确指定。将确切文本放在
引号中，保留您想要的大小写，并描述其字体
样式、大小、颜色和位置。对于不常见的名称，当准确性
至关重要时，请拼出字母。说明是否允许任何其他文本。

<PromptComponent
  actionsPlacement="header"
  label="Example prompt"
  prompt={`Add only the title “SPRING WORKSHOP” in large, bold, white sans-serif letters, centered in the top third of the image. Keep the title on one line. Do not add any other text or change the underlying image.`}
/>

## 创建信息图表和密集布局

图像生成可帮助起草解说图、海报、标注图、
时间轴和其他信息丰富的视觉效果。描述信息
层级和布局，保持标签简洁，并要求清晰的文本渲染。
对于密集文案或对生产至关重要的排版，请审查每一个字词，并在需要时
在设计工具中完成该素材。

## 其他注意事项

- **谨慎使用肖像。** 在描绘真实人物时，请提供
  适当的参考照片，并确认您已获得使用
  其肖像的许可。
- **要求原创处理。** 请求通用或原创的设计，
  而不是模仿特定的品牌、产品、艺术家或艺术品。
- **署名是可选的。** 您无需为生成的图像注明 OpenAI 出处，
  但当该背景信息有用时，您可以解释该资产是如何制作的。
- **遵守适用政策。** 请根据您的
  组织指南和 [OpenAI 的使用
  政策](https://openai.com/policies/usage-policies/) 使用图像。



## 相关文档



- [Codex 定价](https://learn.chatgpt.com/docs/pricing#image-generation-usage-limits)
- [图像输入](https://learn.chatgpt.com/docs/image-inputs)
- [图像生成 API 指南](https://developers.openai.com/api/docs/guides/image-generation)
- [处理文件](https://learn.chatgpt.com/docs/artifacts-viewer)
- [使用 ChatGPT 创建图像](https://openai.com/academy/image-generation/)

[图像生成图库



      <Images />
    
    探索更多图像生成提示词和结果。](https://developers.openai.com/api/docs/guides/image-generation?gallery=open)

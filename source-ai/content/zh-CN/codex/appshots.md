---
title: 应用截图
source_id: codex/appshots
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/appshots
owner: OpenAI
content_sha256: ee5c8829b5876cc2c3a34c6965ba2527d9e41524cb7e514d8d015c8ce050c498
translation_of: codex/appshots
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/appshots)

Content owner: OpenAI

# 应用截图

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。可以通过在页面 URL 后附加 `.md` 来获取文档页面的 Markdown 版本。

应用截图允许您将最前方的应用程序窗口发送到 ChatGPT 的聊天中。当您
正在电脑上的另一个应用程序中积极工作，并希望
为 ChatGPT 提供当前上下文以便它能帮助您完成任务时，请使用它们。

应用截图可在 macOS 上的 ChatGPT 桌面应用程序中使用。同时按下两个
  Command 键，或您自定义的应用截图快捷键即可截取一张。

## 应用截图会捕获什么

应用截图仅捕获最前方的窗口。它可能包含：

- 可见窗口的图像。
- 该窗口中的可用文本，包括可见文本以及应用程序在
  可见滚动区域之外提供的文本。

将应用截图添加到聊天后，其行为类似于附件。ChatGPT 会
将应用截图本地存储在会话文件中，就像您手动附加的
文件或图像一样。

## 何时使用应用截图

当 ChatGPT 需要来自 Mac 应用程序的上下文才能执行操作时，请使用应用截图。

示例：

- 分享 API 参考页面，并要求 ChatGPT 编写使用该 API 的脚本。
- 分享电子邮件或日历视图，并要求 ChatGPT 起草下一步操作。
- 分享图像编辑器、设计或预览窗口，并要求 ChatGPT 修改
  相关资产或代码。
- 分享错误、设置面板或应用程序状态，这些内容往往展示起来比
  描述更容易。

## 截取应用截图

1. 将要共享的应用程序窗口置于最前方。
2. 按下两个 Command 键，或者在 ChatGPT
   设置中配置的自定义快捷键。
3. 如果 ChatGPT 提示，请允许 macOS 权限。
4. 要求 ChatGPT 使用应用截图执行任务。

<Illustration description="带有应用截图附件和后续提示的 ChatGPT 聊天撰写器">
  <AppshotsComposerIllustration ariaLabel="带有应用截图附件和后续提示的 ChatGPT 聊天撰写器" />
</Illustration>

默认情况下，ChatGPT 会为应用截图开启一个新的聊天。如果您在过去 60 秒内与某个
聊天进行过交互，ChatGPT 则会将应用截图添加到该最近的
聊天中。连续截取的应用截图会被添加到同一个聊天中。

您可以在应用程序设置中更改应用截图的快捷键。

## 权限与安全

ChatGPT 在截取应用截图前可能会要求权限：

- **屏幕与系统音频录制**允许 ChatGPT 捕获
  最前方窗口的图像。
- **辅助功能**允许 ChatGPT 读取最前方窗口中的可用文本。

截取应用截图会与 ChatGPT 共享捕获的图像和可用文本。
请避免截取敏感内容的应用截图，除非任务需要
该内容。

请像检查与 ChatGPT 共享的屏幕截图和文档那样
检查应用截图。

## 限制与故障排除

应用截图可在 macOS 上的 ChatGPT 桌面应用程序中使用。如果您在 CLI 中恢复一个
已经包含应用截图的聊天，该附件将是聊天
历史记录的一部分，但 CLI 无法创建新的应用截图。

对于某些应用程序和网站（包括 Google 文档、Gmail、Google 表格和
Google 幻灯片），ChatGPT 可能只会收到可见的屏幕截图，而无法收到
完整的文档或屏幕外的文本。在 ChatGPT Work 或 Codex 中，ChatGPT 可以使用
匹配的已安装插件来访问相关的应用程序内容，并协助处理您的
请求。

如果应用截图不起作用：

1. 打开**系统设置 > 隐私与安全性**。
2. 检查 Codex Computer Use 的**屏幕与系统音频录制**和**辅助功能**
   权限。
3. 重启应用程序并重试。

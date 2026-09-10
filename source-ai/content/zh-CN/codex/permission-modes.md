---
title: 权限
source_id: codex/permission-modes
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/permission-modes
owner: OpenAI
content_sha256: 9e0130d1c6283d3bb8f82b10f358877d20051dd301faa07df79d5335ca3d4ef1
translation_of: codex/permission-modes
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/permission-modes)

Content owner: OpenAI

# 权限

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。可以通过在页面 URL 后附加 `.md` 来获取文档页面的 Markdown 版本。

{/* vale Microsoft.FirstPerson = NO */}

## 权限模式

权限控制 ChatGPT（在桌面应用程序中）和 Codex（在 CLI 或 IDE 中）如何处理本地操作，例如编辑文件、运行命令和使用互联网。您选择的模式设定了边界
规定了 ChatGPT 可以自主执行的操作以及需要审查的操作。

对于大多数工作，请从**请求批准**开始。它允许 ChatGPT 在
当前工作区中工作，并在越过该边界之前暂停。

在下方选择不同的模式，以了解每种模式的工作原理。

<PermissionModeSelectorDemo client:load />

## 启用模式

首次使用 ChatGPT 桌面应用程序时，您需要在应用程序设置中启用模式。

**请求批准**始终可用。要添加**代我批准**（在设置中称为
**自动审查**）或**完全访问**到权限菜单，请打开
ChatGPT 桌面应用程序中的**设置 > 常规**，然后在
**权限**下开启该模式。启用模式会使其在菜单中可用；它并不会
选择该模式或更改现有的聊天。

<Illustration description="显示默认权限、自动审查和完全访问权限的权限可见性控制。">
  <PermissionModeSettingsIllustration ariaLabel="显示默认权限、自动审查和完全访问权限的权限可见性控制。" />
</Illustration>

可用的模式可能取决于您的本地配置以及您
  组织的要求。不允许的模式将显示为禁用状态。

## 权限的工作原理

两个控制项协同工作：

- **沙盒**定义了 ChatGPT 可以访问哪些文件和网络资源。
- **批准**决定了 ChatGPT 何时在执行操作之前暂停或将
  请求发送到自动审查。

更改审查请求的人员不会扩展沙盒。例如，
**代我批准**与**请求批准**保持相同的工作区边界；
它将越过该边界的请求发送给自动审查。

使用 ChatGPT 桌面应用程序或
IDE 扩展中输入框下方的权限控制。

<Illustration description="选择了“代我批准”的批准模式菜单。">
  <PermissionModeComposerIllustration ariaLabel="选择了“代我批准”的批准模式菜单。" />
</Illustration>

在 CLI 中，输入 `/permissions`。有关技术详细信息，请参见
[沙盒](https://learn.chatgpt.com/docs/sandboxing), [自动审查](https://learn.chatgpt.com/docs/sandboxing/auto-review), 或
[权限配置文件](https://learn.chatgpt.com/docs/permissions)。

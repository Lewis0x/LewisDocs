---
title: 设置
source_id: codex/app/settings
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/app/settings
owner: OpenAI
content_sha256: 752ef1cabf6dc2384093e720aa822e0ceb78d1d710293ad7e60a521f83e774a3
translation_of: codex/app/settings
translation_model: k3
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/app/settings)

Content owner: OpenAI

# 设置

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。可以通过在页面 URL 后附加 `.md` 来获取文档页面的 Markdown 版本。

使用设置面板来个性化应用并管理日常偏好设置。
从应用菜单中打开 [**设置**](codex://settings) 或按下

macOS 上的 <kbd>Cmd</kbd>+<kbd>,</kbd> 或 Windows 上的 <kbd>Ctrl</kbd>+<kbd>,</kbd>。

## 通用

要求使用 <kbd>Cmd</kbd>+<kbd>Enter</kbd> 进行多行提示，或开启
**运行时防止休眠**，以便在您离开时本地聊天仍能继续。
在**后续操作行为**下，选择在 ChatGPT 工作时发送的消息
是引导当前运行还是等待下一次运行。

## 个人资料

使用**个人资料**查看活动洞察、终身令牌、峰值令牌、
连续记录、最长任务和令牌活动。您还可以更新您的个人资料
详情，例如您的头像、显示名称和用户名，并保存包含使用情况
摘要的个人资料卡片。分享个人资料卡片适用于消费者
ChatGPT 计划。

符合条件的用户还可以从个人资料菜单发送 Codex 邀请。在符合条件的个人
计划中选择**邀请朋友**，或在符合条件的 Business
工作区中选择**邀请同事**。请参见
[邀请朋友和同事](https://learn.chatgpt.com/docs/pricing#invite-friends-and-coworkers) 以了解
当前的奖励、限制和资格条件。

## 键盘快捷键

打开**键盘快捷键**以查看命令、更改绑定，或将自定义
快捷键重置为默认值。使用搜索字段按命令
名称查找快捷键，或切换到按键搜索并按下组合键以查找
使用该组合键的命令。

## 通知

选择何时显示回合完成通知，以及应用是否应请求
通知权限。

## 外观

在**设置**中，您可以通过选择基础主题、
调整强调色、背景和前景色以及更改 UI 和
代码字体来更改应用外观。您还可以与朋友分享您的自定义主题。

<CodexScreenshot
  alt="ChatGPT 桌面应用外观设置，显示主题选择、颜色控制和字体选项"
  lightSrc="/images/codex/app/theme-selection-light.webp"
  darkSrc="/images/codex/app/theme-selection-dark.webp"
  maxHeight="720px"
  class="mb-8"
/>

## 宠物



  

    宠物是应用的可选动画伴侣。在**设置 > 宠物**中，
    选择内置或自定义宠物，然后使用 `/pet`、**唤醒宠物**或
    **收起宠物**来控制浮动覆盖层。

    请参见 [宠物](https://learn.chatgpt.com/docs/pets?surface=app) 以了解宠物状态、
    跨聊天的活动跟踪，或创建您自己的宠物。


  <CodexPetsDemo client:load />



<a id="browser-use"></a>

## 浏览器

使用这些设置来安装或启用内置的浏览器插件、设置
[Chrome 扩展程序](https://learn.chatgpt.com/docs/chrome-extension)，并管理允许和阻止的
网站。除非您已允许，否则 ChatGPT 在使用网站前会先询问。移除
被阻止的站点会让 ChatGPT 在浏览器中使用它之前再次询问。

请参见 [内置浏览器](https://learn.chatgpt.com/docs/browser?surface=app) 以了解浏览器预览、评论和
Computer Use 工作流。

## Computer Use

检查您的 Computer Use 设置，以在设置完成后查看桌面应用访问权限和相关
偏好设置。在 macOS 上，通过更新 macOS“隐私与安全性”设置中的“屏幕
录制”或“辅助功能”权限来撤销系统级访问权限。

## 个性化

选择**友好**、**务实**或**无**作为您的默认个性。使用
**无**可禁用个性指令。您可以随时更新此设置。

您还可以添加自己的自定义指令。编辑自定义指令会更新您的
[个人指令，位置在 `AGENTS.md`](https://learn.chatgpt.com/docs/agent-configuration/agents-md)。

## 建议提示

使用上下文感知建议来呈现后续问题和您可能想要恢复的任务，当您
启动或返回 ChatGPT 时。

## 记忆

在可用时启用“记忆”，让 ChatGPT 将过去对话中的有用上下文带入
到未来的工作中。有关设置、存储以及单个对话的控制，请参阅 [记忆](https://learn.chatgpt.com/docs/customization/memories)

<a id="archived-tasks"></a>

## 已归档的对话

**已归档的对话**部分列出了带有日期和项目
上下文的已归档对话。使用**取消归档**来恢复对话。

<a id="keep-an-app-task-near-your-work"></a>
<a id="keep-an-app-chat-near-your-work"></a>
<a id="keep-a-task-near-your-work"></a>

## 在您的工作旁保留对话

在 ChatGPT 桌面应用中，将活动对话弹出到单独窗口，并将其放置
在您的浏览器、编辑器或设计预览旁边。当您希望在另一个应用中工作时让
对话保持可见，请开启**始终置顶**。

<CodexScreenshot
  alt="ChatGPT 桌面应用对话显示在浮动弹出窗口中"
  lightSrc="/images/codex/app/popover-light.webp"
  darkSrc="/images/codex/app/popover-dark.webp"
  maxHeight="400px"
  class="my-8"
/>

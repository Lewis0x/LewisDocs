---
title: ChatGPT 语音
source_id: codex/features/voice
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/features/voice
owner: OpenAI
content_sha256: b836efaf18f1a8a6ded868b8704a3b5b6592ca3165d1045ec9ede44cebf1ff91
translation_of: codex/features/voice
translation_model: k3
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/features/voice)

Content owner: OpenAI

# ChatGPT 语音

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。可以通过在页面 URL 后附加 `.md` 来获取文档页面的 Markdown 版本。

ChatGPT 语音由 GPT-Live 提供支持，允许你在 ChatGPT 桌面应用的 Chat、Work 和 Codex 中通过交谈探讨想法并协调
任务。无需切换回打字，即可开始工作、检查
进度或改变方向。

ChatGPT 语音可在 ChatGPT 桌面应用中供 ChatGPT Plus、
Pro、Business、Edu 和 Enterprise 套餐使用。Enterprise 和 Edu 的可用性
始于为期两周的抢先体验期，之后该功能将默认
可用。你还可以通过
[iOS 上的 Remote](https://learn.chatgpt.com/docs/remote-connections#set-up-mobile-access) 在将手机与
桌面主机配对后使用 ChatGPT 语音。可用性还取决于发布状态和
工作区设置。请参见 [功能可用性](https://learn.chatgpt.com/docs/pricing#feature-availability)。

<Illustration description="带有麦克风和扬声器控件的交互式 ChatGPT 语音对话。">
  <CodexVoiceAgentIllustration />
</Illustration>

## 开始交谈

1. 在 ChatGPT 桌面应用中打开一个新的空白聊天或任务。
2. 在发送消息前，选择**开始新语音聊天**。
3. 首次开始语音聊天时，请允许麦克风访问，选择一个
   声音，并在 macOS 上查看屏幕上下文。
4. 开始交谈。完成后选择**结束**。

要使用 ChatGPT 语音，聊天或任务必须以语音模式开始。以其他
模式开始的聊天或任务将提供语音听写功能。要恢复之前的语音
聊天，请将其打开并选择**开始语音聊天**。

你可以在**设置 > 语音 > 语音聊天快捷键**中设置快捷方式。

## 进行对话

ChatGPT 语音支持自然的轮流交谈。你可以在回复期间打断 ChatGPT、
提出后续问题或改变方向。如果 ChatGPT 开始工作，
请继续交谈以检查进度或引导任务。

## 委派和协调工作

ChatGPT 语音可以为较长的任务启动单独的线程，检查现有线程，
并发送后续指令。它将进度、阻碍和结果带回
你的语音对话中，以便你可以在工作继续进行时继续交谈。

例如：

- “审查今天的发布简报并总结需要批准的决定。”
- “启动一个 Codex 任务来运行测试，并调查任何未通过的内容。”
- “检查活动任务并总结任何阻碍进度的因素。”

ChatGPT 语音遵循相同的 [权限](https://learn.chatgpt.com/docs/permission-modes)，如同
它在 ChatGPT 桌面应用的 Chat、Work 和 Codex 中指导的任务一样。

## 向 ChatGPT 展示你所看到的

在 macOS 上，在**设置 > 语音**中开启**屏幕上下文**，然后说，“看
一下这个。” ChatGPT 可以截取
你最前面的窗口的 [应用快照](https://learn.chatgpt.com/docs/appshots#permissions-and-safety)，并
将其用作上下文。你的组织可以禁用此功能。

应用快照可以包含窗口的图像和可访问的文本，包括可见
滚动区域之外的内容。macOS 可能会请求**屏幕和系统音频
录制**和**辅助功能**权限。避免共享包含
敏感信息的窗口，包括可见滚动区域之外的文本。

## ChatGPT 语音与语音听写

使用 ChatGPT 语音与 ChatGPT 进行实时对话。当你只想在发送前将语音
转换为提示文本时，请使用[语音
听写](https://learn.chatgpt.com/docs/prompting#use-voice-dictation)。

## 限制与故障排除

在 ChatGPT 桌面应用中，同一时间只能有一个语音聊天处于活动状态。
语音对话使用单独的、取决于订阅计划的额度，该额度以滚动
五小时的时间窗口进行衡量。通过语音启动的任务会继续使用你的 Codex 使用
预算。当你达到任一限制时，ChatGPT 会通知你。请参阅[语音定价和
限制](https://learn.chatgpt.com/docs/pricing#chatgpt-voice-in-desktop)。

如果你无法启动语音聊天，请确认你的
订阅计划、发布状态和工作区支持 ChatGPT 语音。然后检查麦克风权限以及是否有
语音聊天已经在其他应用窗口中处于活动状态。如果屏幕上下文不可
用，请检查**设置 > 语音**、应用快照权限以及你的
组织的限制。

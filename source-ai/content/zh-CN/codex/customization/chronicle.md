---
title: Chronicle
source_id: codex/customization/chronicle
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/customization/chronicle
owner: OpenAI
content_sha256: d2ae746965e071f87ee0c29103ba8c5d921a012d42f6c06bf00640d38f556d43
translation_of: codex/customization/chronicle
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/customization/chronicle)

Content owner: OpenAI

# Chronicle

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。可以通过在页面 URL 后附加 `.md` 来获取文档页面的 Markdown 版本。

Chronicle 处于 **选择性加入的研究预览版**。它仅适用于
  macOS 上的 ChatGPT Pro 订阅者。在启用之前，请查看[隐私与
  安全](#privacy-and-security)部分以了解详情并理解
  当前的风险。

Chronicle 使用您屏幕上的上下文来增强 Codex 记忆。当您
提示 Codex 时，这些记忆可以帮助它理解您一直在做什么，从而
减少您重新陈述上下文的需要。

Chronicle 在 macOS 上的 ChatGPT 桌面应用程序中作为选择性加入的研究预览版提供。
它需要 macOS 屏幕录制和辅助功能权限。在
启用之前，请注意 Chronicle 会快速消耗速率限制，增加
提示注入的风险，并在您的设备上未加密地存储记忆。

## Chronicle 的帮助方式

我们设计 Chronicle 是为了减少您必须重新陈述的上下文量
在您使用 Codex 时。通过使用最近的屏幕上下文来改进记忆
构建，Chronicle 可以帮助 Codex 理解您所指的是什么，识别
正确的信息源以供使用，并掌握您所依赖的工具和工作流。

<section class="feature-grid mt-4">




### 使用屏幕上的内容

借助 Chronicle，Codex 可以理解您当前正在查看的内容，从而节省
您的时间并减少上下文切换。




<ChronicleThreadDemo client:load scenario="screen" />

</section>

<section class="feature-grid inverse">




### 填补缺失的上下文

无需精心制作您的上下文并从零开始。Chronicle 让
Codex 填补您上下文中的空白。




<ChronicleThreadDemo client:load scenario="project" />

</section>

<section class="feature-grid">




### 记住工具和工作流

无需向 Codex 解释要使用哪些工具来执行您的工作。Codex
会在您工作时学习，从长远来看可以节省您的时间。




<ChronicleThreadDemo client:load scenario="tools" />

</section>

在这些情况下，Codex 使用 Chronicle 提供额外的上下文。当有
其他信息源更适合该任务时，例如阅读特定文件、Slack 线程、
Google 文档、仪表板或拉取请求，Codex 会使用 Chronicle 识别
信息源，然后直接使用该信息源。

## 启用 Chronicle

1. 在 ChatGPT 桌面应用程序中打开设置。
2. 转到**个性化**并确保启用了**记忆**。
3. 在记忆设置下方打开**Chronicle**。
4. 查看同意对话框并选择**继续**。
5. 出现提示时，授予 macOS 屏幕录制和辅助功能权限。
6. 设置完成后，选择**试用一下**或开始新聊天。

如果 macOS 报告屏幕录制或辅助功能权限被拒绝，
请打开系统设置 &gt; 隐私与安全性 &gt; 屏幕录制或
辅助功能，并启用 ChatGPT。如果权限受到 macOS 或
您的组织的限制，Chronicle 将在解除限制并且
ChatGPT 获得所需权限后启动。

## 随时暂停或禁用 Chronicle

您可以控制 Chronicle 何时使用屏幕上下文生成记忆。使用
ChatGPT 菜单栏图标选择**暂停 Chronicle**或**恢复 Chronicle**。在
会议前或在查看不希望
Codex 用作上下文的敏感内容时暂停 Chronicle。要禁用 Chronicle，请返回**设置 &gt;
个性化 &gt; 记忆**并关闭**Chronicle**。

您还可以控制在特定聊天中是否使用记忆。[了解
更多信息](https://learn.chatgpt.com/docs/customization/memories#control-memories-per-chat)。

## 速率限制

Chronicle 通过在后台运行沙盒代理来工作，以从
捕获的屏幕图像生成记忆。这些代理目前会消耗速率限制
非常快。

## 隐私和安全

Chronicle 使用屏幕捕获，其中可能包含您的屏幕上可见的
敏感信息。它无法访问您的麦克风或系统音频。
请勿使用 Chronicle 记录会议或与他人的通讯，除非
已获得他们的同意。在查看不希望被记住的内容时，请暂停 Chronicle
。

### Chronicle 将我的数据存储在哪里？

屏幕捕获是短暂的，只会临时保存在您的
计算机上。临时屏幕捕获文件可能出现在
`$TMPDIR/chronicle/screen_recording/` 下，当 Chronicle 运行时。屏幕捕获
如果超过 6 小时，将在 Chronicle 运行时被删除。

Chronicle 生成的记忆与其他 Codex 记忆一样：
它们是未加密的 markdown 文件，如有需要您可以读取和修改。您也可以
要求 Codex 搜索它们。如果您想让 Codex 忘记某些内容，您可以
删除文件夹内的相应文件，或选择性地编辑 markdown
文件以移除您想要移除的信息。您不应手动
添加新信息。生成的 Chronicle 记忆会本地存储在您的
计算机上的 `$CODEX_HOME/memories_extensions/chronicle/` 下（通常是
`~/.codex/memories_extensions/chronicle`）。



  <Alert
    client:load
    color="danger"
    variant="soft"
    description="您的屏幕捕获和记忆的这两个目录可能包含敏感信息。请确保不要与他人共享内容，并注意计算机上的其他程序也可以访问这些文件。"
  />



### 哪些数据会与 OpenAI 共享？

Chronicle 在本地捕获屏幕上下文，然后定期使用 Codex 将
最近的活动总结为记忆。为了生成这些记忆，Chronicle
会启动一个可以访问此屏幕上下文的临时 Codex 会话。该
会话可能会处理选定的屏幕截图帧、从截图中提取的 OCR 文本、
时间信息，以及相关时间窗口的
本地文件路径。

用于生成记忆的屏幕捕获会临时存储在您的设备上。它们会在我们的
服务器上进行处理以生成记忆，随后本地存储在设备上。我们不会
在处理后将截图存储在我们的服务器上，除非法律有此要求，
也不会将其用于训练。

生成的记忆是本地存储在以下位置的 Markdown 文件：
`$CODEX_HOME/memories_extensions/chronicle/`。当 Codex 在未来的
会话中使用记忆时，相关的记忆内容可能会作为该
会话的上下文被包含在内，如果您的 ChatGPT 设置允许，还可能用于
改进我们的模型。[了解更多](https://help.openai.com/en/articles/7730893-data-controls-faq)。

## 提示词注入风险

使用 Chronicle 会增加受到屏幕内容提示词注入攻击的风险。
例如，如果您浏览包含恶意代理指令的网站，Codex 可能会
遵循这些指令。

## 故障排除

### 如何启用 Chronicle？

如果您没有看到 Chronicle 设置，请确保您使用的是包含 Chronicle 的 ChatGPT 桌面应用程序
版本，并且您已在“设置”
&gt; 个性化”中启用了“记忆”。

Chronicle 目前仅适用于 macOS 上的 ChatGPT Pro 订阅者。

如果设置未完成：

1. 确认 ChatGPT 具有屏幕录制和辅助功能权限。
2. 退出并重新打开 ChatGPT 桌面应用程序。
3. 打开 **设置 > 个性化** 并检查 Chronicle 状态。

### 哪个模型用于生成 Chronicle 记忆？

Chronicle 使用与您的其他 [记忆](https://learn.chatgpt.com/docs/customization/memories) 相同的模型。如果您
未配置特定模型，它将使用您的默认 Codex 模型。要选择
特定模型，请更新 `consolidation_model` 于您的
[配置](https://learn.chatgpt.com/docs/config-file/config-basic) 中。

```toml
[memories]
consolidation_model = "gpt-5.4-mini"
```

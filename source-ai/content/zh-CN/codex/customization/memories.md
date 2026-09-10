---
title: 记忆
source_id: codex/customization/memories
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/customization/memories
owner: OpenAI
content_sha256: 6d94568780d6cccd7dfd0a7106bafadd8519759780ee1f68d4d8f6722b1a9e52
translation_of: codex/customization/memories
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/customization/memories)

Content owner: OpenAI

# 记忆

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。通过在页面 URL 后附加 `.md`，可以获取文档页面的 Markdown 版本。

记忆功能让 ChatGPT 和 Codex 能够将先前工作中的有用上下文带入
未来的工作中。
ChatGPT 网页版使用 ChatGPT 记忆，而本地 Codex 客户端则使用单独的本地
记忆存储和控制机制。



将所需的团队指导保留在 `AGENTS.md` 或签入的文档中。将
记忆视为一个有用的回忆层，而不是作为必须始终应用的规则的
唯一来源。





在 ChatGPT 桌面应用程序中，使用 `/memories` 来选择某个聊天是否可以使用
本地记忆或为未来的记忆做出贡献。当你需要开启或关闭该功能时，请从
**设置 > 个性化** 中管理此功能。













[Chronicle](https://learn.chatgpt.com/docs/customization/chronicle) 是一项仅限桌面版的功能，可帮助
Codex 从你的屏幕中恢复最近的工作上下文，以积累记忆。



<a id="how-memories-work"></a>
<a id="memory-storage"></a>
<a id="control-memories-per-thread"></a>
<a id="control-memories-per-chat"></a>
<a id="control-memories-per-task"></a>
<a id="review-memories"></a>



## 本地 Codex 记忆的工作原理

在你启用记忆功能后，Codex 可以将符合条件的先前
聊天中的有用上下文转化为本地记忆文件。Codex 会跳过活动的或短暂的会话，
对生成的记忆字段中的机密信息进行脱敏处理，并在
后台更新记忆，而不是在每次聊天结束时立即更新。

聊天结束时，记忆可能不会立即更新。Codex 会一直等待，直到
某个聊天空闲了足够长的时间，以避免总结仍在
进行中的工作。

当你的 Codex 剩余速率限制
百分比低于配置的阈值时，记忆生成过程也会跳过后台处理，这样当你接近限制时，Codex 就不会消耗
配额。

## 本地记忆存储

Codex 将记忆存储在你的 Codex 主目录下。默认情况下，那是
`~/.codex`。参见 [配置和状态位置](https://learn.chatgpt.com/docs/config-file/config-advanced#config-and-state-locations)
以了解 Codex 如何使用 `CODEX_HOME`。

主要的记忆文件位于 `~/.codex/memories/` 下，并包含摘要、
持久条目、最近的输入，以及来自先前聊天的支持性证据。

将这些文件视为生成的状态。你可以在故障排除时检查它们，
或者在共享你的 Codex 主目录之前检查它们，但不要依赖手动编辑它们作为
你的主要控制面板。

<a id="control-local-memories-per-task"></a>

## 按聊天控制本地记忆

在 ChatGPT 桌面应用程序和 Codex TUI 中，使用 `/memories` 来控制
当前聊天的记忆行为。聊天级别的选项让你决定当前
聊天是否可以使用现有记忆，以及 Codex 是否可以使用该聊天来
生成未来的记忆。

聊天级别的选择不会更改你的全局记忆设置。

## 查看本地记忆

不要在记忆中存储机密信息。Codex 会对生成的记忆
字段中的机密信息进行脱敏，但在共享你的 Codex 主
目录或生成的记忆产物之前，你仍应检查记忆文件。

<a id="enable-memories"></a>
<a id="configuration"></a>

## 配置本地记忆

本地 Codex 记忆默认是关闭的。在 ChatGPT 桌面应用程序中，打开
**设置 > 个性化**，并开启**启用记忆**。

对于基于配置的设置，请将功能标志添加到 `config.toml`：

```toml
[features]
memories = true
```

有关配置文件位置和与记忆相关的完整设置列表，请参见
[配置基础](https://learn.chatgpt.com/docs/config-file/config-basic) 和[配置
参考](https://learn.chatgpt.com/docs/config-file/config-reference)。

常见的特定于记忆的设置包括：

- `memories.generate_memories`：控制新创建的聊天是否可以
  存储为记忆生成输入。
- `memories.use_memories`：控制 Codex 是否将现有记忆注入到
  未来的会话中。
- `memories.disable_on_external_context`：当 `true` 时，将使用了
  外部上下文（如 MCP 工具调用、网络搜索或工具搜索）的聊天排除在
  记忆生成之外。较早的 `memories.no_memories_if_mcp_or_web_search` 键
  仍被接受作为别名。
- `memories.min_rate_limit_remaining_percent`：控制在开始记忆生成之前所需的最低剩余
  Codex 速率限制百分比。
- `memories.extract_model`：覆盖用于每次聊天记忆
  提取的模型。
- `memories.consolidation_model`：覆盖用于全局记忆
  整合的模型。

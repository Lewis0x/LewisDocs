---
title: 集成终端
source_id: codex/integrated-terminal
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/integrated-terminal
owner: OpenAI
content_sha256: 62608576a5171563d98019ac88925600f3c5cb2022a56e6c72b89a156209a9cd
translation_of: codex/integrated-terminal
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/integrated-terminal)

Content owner: OpenAI

# 集成终端

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。可以通过在页面 URL 后追加 `.md` 来获取文档页面的 Markdown 版本。

ChatGPT 桌面应用中的每个聊天都包含一个终端，其作用域为其当前项目或
工作树。从应用右上角的终端图标打开它，或者
按下 <kbd>Ctrl</kbd>+<kbd>`</kbd>。

<CodexScreenshot
  alt="在 ChatGPT 聊天下方打开的集成终端抽屉"
  lightSrc="/images/codex/app/integrated-terminal-light.webp"
  darkSrc="/images/codex/app/integrated-terminal-dark.webp"
  maxHeight="400px"
  class="my-8"
/>

## 运行并验证您的项目

使用终端验证更改、运行脚本和执行 Git 操作
而无需切换应用。ChatGPT 可以读取当前终端输出，因此它可以
检查正在运行的开发服务器，或参考失败的构建，同时
与您协作。

常用命令包括：

- `git status`
- `git pull --rebase`
- `pnpm test` 或 `npm test`
- `pnpm run lint` 或另一个特定于项目的检查

## 创建可复用的操作

如果您经常运行某个命令，可以在您的 [本地环境](https://learn.chatgpt.com/docs/environments/local-environment#actions) 中定义一个操作。
操作在 ChatGPT 桌面应用中显示为快捷方式，并在集成
终端中运行。

<kbd>Cmd</kbd>+<kbd>K</kbd> 打开应用命令面板；它不会清空
终端。要清空终端，请按 <kbd>Ctrl</kbd>+<kbd>L</kbd>。

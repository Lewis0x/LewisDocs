---
title: CLI 自定义
source_id: codex/cli-customization
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/cli-customization
owner: OpenAI
content_sha256: f6c100c19ad3527ae718a6965f2a209ae3ee7a1542e49bea78441a2a95e5f9ac
translation_of: codex/cli-customization
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/cli-customization)

Content owner: OpenAI

# CLI 自定义

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。可以通过在页面 URL 后附加 `.md` 来获取文档页面的 Markdown 版本。

Codex CLI 提供了针对终端的特定选项，用于控制交互式会话的外观
以及您输入命令和提示的方式。

## 语法高亮和主题

终端 UI (TUI) 会对围栏 Markdown 代码块和文件
差异进行语法高亮。运行 `/theme` 打开主题选择器，预览主题，并将您的
选择保存到 `$CODEX_HOME/config.toml` 中的 `tui.theme`。

要添加自定义主题，请将 `.tmTheme` 文件放置在 `$CODEX_HOME/themes` 中，然后
从主题选择器中选择它。

## Shell 补全

生成用于 Bash、Z shell、Fish 或 PowerShell 的补全脚本：

```bash
codex completion zsh
```

从您的 shell 配置中加载该脚本。对于 Z shell，请添加：

```bash
eval "$(codex completion zsh)"
```

如果 Z shell 报告 `command not found: compdef`，请初始化其补全系统，
然后再加载 Codex 补全：

```bash
autoload -Uz compinit && compinit
eval "$(codex completion zsh)"
```

重启 shell，输入 `codex`，然后按 <kbd>Tab</kbd> 键验证补全。

## 提示词编辑器

对于较长的提示词，请在撰写框中按 <kbd>Ctrl</kbd>+<kbd>G</kbd> 打开
由 `VISUAL` 配置的编辑器，或者在未设置 `VISUAL` 时使用 `EDITOR`。保存
并关闭编辑器，以便在发送前将文本返回到撰写框。

有关交互式键盘控件以及完整的命令和选项列表，请参见
[命令](https://learn.chatgpt.com/docs/developer-commands?surface=cli#cli-interactive-shortcuts)。

---
title: 自定义提示词
source_id: codex/custom-prompts
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/custom-prompts
owner: OpenAI
content_sha256: 603423825c9cce8da5357f8ed627ff3fe153bca5033c40661f1d2b07924b9428
translation_of: codex/custom-prompts
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/custom-prompts)

Content owner: OpenAI

# 自定义提示词

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。可以通过在页面 URL 后附加 `.md` 来获取文档页面的 Markdown 版本。

自定义提示词已弃用。使用 [skills](https://learn.chatgpt.com/docs/build-skills) 来获取可重用的
  Codex 可以显式或隐式调用的指令。

自定义提示词（已弃用）允许您将 Markdown 文件转换为可重用的提示词，您可以在 Codex CLI 和 Codex IDE 扩展中将其作为斜杠命令调用。

自定义提示词需要显式调用，并且位于您的本地 Codex 主目录中（例如，`~/.codex`），因此它们不会通过您的代码库共享。如果您想共享提示词（或希望 Codex 隐式调用它），[use skills](https://learn.chatgpt.com/docs/build-skills)。

1. 创建提示词目录：

```bash
   mkdir -p ~/.codex/prompts
```

2. 使用可重用的指导创建 `~/.codex/prompts/draftpr.md`：

```markdown
   ---
   description: Prep a branch, commit, and open a draft PR
   argument-hint: [FILES=<paths>] [PR_TITLE="<title>"]
   ---

   Create a branch named `dev/<feature_name>` for this work.
   If files are specified, stage them first: $FILES.
   Commit the staged changes with a clear message.
   Open a draft PR on the same branch. Use $PR_TITLE when supplied; otherwise write a concise summary yourself.
```

3. 重启 Codex 以便其加载新提示词（重启您的 CLI 会话，如果正在使用 IDE 扩展，请重新加载它）。

预期结果：在斜杠命令菜单中输入 `/prompts:draftpr` 会显示您的自定义命令，其中包含来自前置元数据的描述，并提示文件和 PR 标题是可选的。

## 添加元数据和参数

Codex 会在下次会话启动时读取提示词元数据并解析占位符。

- **描述：** 显示在弹窗中命令名称下方。在 YAML 前置元数据中将其设置为 `description:`。
- **参数提示：** 使用 `argument-hint: KEY=<value>` 记录预期参数。
- **位置占位符：** `$1` 到 `$9` 会根据您在命令后提供的以空格分隔的参数进行展开。`$ARGUMENTS` 包含所有这些参数。
- **命名占位符：** 使用类似 `$FILE` 或 `$TICKET_ID` 的大写名称，并以 `KEY=value` 的形式提供值。用引号括起包含空格的值（例如，`FOCUS="loading state"`）。
- **字面美元符号：** 编写 `$$` 以在展开的提示词中输出单个 `$`。

编辑提示词文件后，请重启 Codex 或打开新的聊天窗口以加载更新。Codex 会忽略提示词目录中的非 Markdown 文件。

## 调用和管理自定义命令

1. 在 Codex（CLI 或 IDE 扩展）中，输入 `/` 打开斜杠命令菜单。
2. 输入 `prompts:` 或提示词名称，例如 `/prompts:draftpr`。
3. 提供所需参数：

```text
   /prompts:draftpr FILES="src/pages/index.astro src/lib/api.ts" PR_TITLE="Add hero animation"
```

4. 按 Enter 键发送展开后的指令（不需要时可跳过任何一个参数）。

预期结果：Codex 会展开 `draftpr.md` 的内容，将占位符替换为您提供的参数，然后将结果作为消息发送。

通过编辑或删除 `~/.codex/prompts/` 下的文件来管理提示词。Codex 仅扫描该文件夹中的顶级 Markdown 文件，因此请将每个自定义提示词直接放在 `~/.codex/prompts/` 下，而不是子目录中。

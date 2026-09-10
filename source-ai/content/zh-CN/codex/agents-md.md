---
title: 使用 AGENTS.md 自定义指令
source_id: codex/agents-md
product: codex
lang: zh-CN
canonical_url: https://learn.chatgpt.com/docs/agent-configuration/agents-md
owner: OpenAI
content_sha256: 4a81af9eeb7597184d295ff7f142478855b0b09100d8b75c2ae1058b3dd3203f
translation_of: codex/agents-md
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://learn.chatgpt.com/docs/agent-configuration/agents-md)

Content owner: OpenAI

# 使用 AGENTS.md 自定义指令

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。通过在页面 URL 后附加 `.md`，可以获取文档页面的 Markdown 版本。

Codex 在进行任何工作之前会读取 `AGENTS.md` 文件。通过将全局指导与项目特定的覆盖相结合，无论您打开哪个存储库，都可以在一致的期望下开始每项任务。

## Codex 如何发现指导

Codex 在启动时会构建一个指令链（每次运行一次；在 TUI 中，这通常意味着每次启动会话一次）。发现过程遵循以下优先顺序：

1. **全局范围：** 在您的 Codex 主目录中（默认为 `~/.codex`，除非您设置了 `CODEX_HOME`），如果存在 `AGENTS.override.md`，Codex 会读取它。否则，Codex 会读取 `AGENTS.md`。Codex 仅使用此级别下的第一个非空文件。
2. **项目范围：** 从项目根目录（通常是 Git 根目录）开始，Codex 会一直向下查找直到您的当前工作目录。如果 Codex 找不到项目根目录，它只会检查当前目录。在路径上的每个目录中，它会依次检查 `AGENTS.override.md`，然后是 `AGENTS.md`，最后是 `project_doc_fallback_filenames` 中的任何备用名称。Codex 在每个目录中最多包含一个文件。
3. **合并顺序：** Codex 从根目录开始向下拼接文件，并用空行将它们连接起来。离当前目录越近的文件会覆盖之前的指导，因为它们在合并后的提示词中出现得更晚。

Codex 会跳过空文件，并在合并后的大小达到 `project_doc_max_bytes` 定义的限制（默认为 32 KiB）时停止添加文件。有关这些调节参数的详细信息，请参见 [项目指令发现](https://learn.chatgpt.com/docs/config-file/config-advanced#project-instructions-discovery)。当达到上限时，请提高限制或将指令拆分到嵌套目录中。

## 创建全局指导

在您的 Codex 主目录中创建持久默认设置，以便每个存储库都能继承您的工作协议。

1. 确保该目录存在：

```bash
   mkdir -p ~/.codex
```

2. 创建 `~/.codex/AGENTS.md` 并包含可重用的偏好设置：

```md
   # ~/.codex/AGENTS.md

   ## Working agreements

   - Always run `npm test` after modifying JavaScript files.
   - Prefer `pnpm` when installing dependencies.
   - Ask for confirmation before adding new production dependencies.
```

3. 在任何地方运行 Codex 以确认它加载了该文件：

```bash
   codex --ask-for-approval never "Summarize the current instructions."
```

   预期：Codex 在提出工作建议之前会引用 `~/.codex/AGENTS.md` 中的内容。

当您需要临时的全局覆盖而不删除基础文件时，请使用 `~/.codex/AGENTS.override.md`。移除该覆盖即可恢复共享指导。

## 分层项目说明

仓库级文件让 Codex 了解项目规范，同时仍然继承您的全局默认设置。

1. 在您的仓库根目录中，添加一个涵盖基本设置的 `AGENTS.md`：

```md
   # AGENTS.md

   ## Repository expectations

   - Run `npm run lint` before opening a pull request.
   - Document public utilities in `docs/` when you change behavior.
```

2. 当特定团队需要不同的规则时，请在嵌套目录中添加覆盖配置。例如，在 `services/payments/` 内部创建 `AGENTS.override.md`：

```md
   # services/payments/AGENTS.override.md

   ## Payments service rules

   - Use `make test-payments` instead of `npm test`.
   - Never rotate API keys without notifying the security channel.
```

3. 从 payments 目录启动 Codex：

```bash
   codex --cd services/payments --ask-for-approval never "List the instruction sources you loaded."
```

   预期：Codex 首先报告全局文件，其次是仓库根目录的 `AGENTS.md`，最后是 payments 覆盖配置。

一旦到达您的当前目录，Codex 就会停止搜索，因此请将覆盖配置放置在尽可能靠近专门工作的位置。

以下是添加了全局文件和特定于 payments 的覆盖配置后的示例仓库：

<FileTree
  class="mt-4"
  tree={[
    {
      name: "AGENTS.md",
      comment: "仓库预期",
      highlight: true,
    },
    {
      name: "services/",
      open: true,
      children: [
        {
          name: "payments/",
          open: true,
          children: [
            {
              name: "AGENTS.md",
              comment: "被忽略，因为存在覆盖配置",
            },
            {
              name: "AGENTS.override.md",
              comment: "支付服务规则",
              highlight: true,
            },
            { name: "README.md" },
          ],
        },
        {
          name: "search/",
          children: [{ name: "AGENTS.md" }, { name: "…", placeholder: true }],
        },
      ],
    },
  ]}
/>

## 添加代码审查规则

对于 [GitHub 中的 Codex 代码审查](https://learn.chatgpt.com/docs/third-party/github#customize-what-codex-reviews)，
请在最靠近规则所约束代码的 `AGENTS.md` 中添加 `## Code Review Rules` 部分，
将仓库范围的检查放在根目录，并将特定于服务的
检查放在嵌套文件中。

```md
## Code Review Rules

### Experiment cohorts

- Do not filter treatment comparisons on post-exposure behavior, including conversion or retention.
  Safe path: build cohorts from assignment or exposure; report conversion as an outcome.
```

保持规则简明扼要，解释需要标记的行为以及任何安全路径或
例外情况，并将格式化和 lint 检查留给 CI。请参阅 [自定义 Codex 审查
的内容](https://learn.chatgpt.com/docs/third-party/github#customize-what-codex-reviews) 以获取
设置和规则编写指南。

## 自定义备用文件名

如果您的仓库已经使用了不同的文件名（例如 `TEAM_GUIDE.md`），请将其添加到备用列表中，以便 Codex 将其视为指令文件。

1. 编辑您的 Codex 配置：

```toml
   # ~/.codex/config.toml
   project_doc_fallback_filenames = ["TEAM_GUIDE.md", ".agents.md"]
   project_doc_max_bytes = 65536
```

2. 重启 Codex 或运行新命令，以便加载更新后的配置。

现在，Codex 会按以下顺序检查每个目录：`AGENTS.override.md`、`AGENTS.md`、`TEAM_GUIDE.md`、`.agents.md`。不在此列表中的文件名将被忽略，不作为说明文件进行发现。更大的字节限制允许在截断前提供更多的组合指导。

有了备用列表后，Codex 会将备用文件视为说明：

<FileTree
  class="mt-4"
  tree={[
    {
      name: "TEAM_GUIDE.md",
      comment: "通过备用列表检测到",
      highlight: true,
    },
    {
      name: ".agents.md",
      comment: "根目录中的备用文件",
    },
    {
      name: "support/",
      open: true,
      children: [
        {
          name: "AGENTS.override.md",
          comment: "覆盖备用指导",
          highlight: true,
        },
        {
          name: "playbooks/",
          children: [{ name: "…", placeholder: true }],
        },
      ],
    },
  ]}
/>

当您想要使用不同的配置档案（例如特定于项目的自动化用户）时，请设置 `CODEX_HOME` 环境变量：

```bash
CODEX_HOME=$(pwd)/.codex codex exec "List active instruction sources"
```

预期：输出列出了相对于自定义 `.codex` 目录的文件。

## 验证您的设置

- 从仓库根目录运行 `codex --ask-for-approval never "Summarize the current instructions."`。Codex 应该按优先级顺序回显来自全局和项目文件的指导。
- 使用 `codex --cd subdir --ask-for-approval never "Show which instruction files are active."` 来确认嵌套的覆盖项替换了更广泛的规则。
- 要审查 Codex 加载了哪些指令文件，请选择使用 `codex -c log_dir=./.codex-log` 生成纯文本 TUI 日志并检查 `./.codex-log/codex-tui.log`，或者如果启用了会话日志记录，请检查最近的 `session-*.jsonl` 文件。
- 如果指令看起来已过时，请在目标目录中重新启动 Codex。Codex 在每次运行时（以及在每次 TUI 会话开始时）都会重建指令链，因此无需手动清除缓存。

## 排查发现问题

- **未加载任何内容：** 验证您是否在预期的仓库中，并且 `codex status` 报告了您期望的工作区根目录。确保指令文件包含内容；Codex 会忽略空文件。
- **出现了错误的指导：** 在目录树的更高层级或您的 Codex 主目录下查找 `AGENTS.override.md`。重命名或移除该覆盖项以回退到常规文件。
- **Codex 忽略了备用名称：** 确认您在 `project_doc_fallback_filenames` 中列出的名称没有拼写错误，然后重新启动 Codex 以使更新后的配置生效。
- **指令被截断：** 提高 `project_doc_max_bytes` 的值，或者将大型文件拆分到嵌套目录中，以保持关键指导的完整性。
- **配置文件混淆：** 在启动 Codex 之前运行 `echo $CODEX_HOME`。非默认值会将 Codex 指向与您所编辑的不同的主目录。

## 后续步骤

- 访问官方 [AGENTS.md](https://agents.md) 网站获取更多信息。
- 查看 [提示 Codex](https://learn.chatgpt.com/docs/prompting)，了解与持久指导配合良好的对话模式。

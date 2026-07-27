---
title: 带有 AGENTS.md 的自定义指令
source_id: codex/agents-md
product: codex
lang: zh-CN
canonical_url: https://learn.chatgpt.com/docs/agent-configuration/agents-md
owner: OpenAI
content_sha256: b4c2d6f542b544fb02ec932aa2ab3285039918bde8fa33a712e5031005025f17
translation_of: codex/agents-md
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://learn.chatgpt.com/docs/agent-configuration/agents-md)

Content owner: OpenAI

# 带有 AGENTS.md 的自定义指令

Codex 在执行任何工作之前会读取 `AGENTS.md` 文件。通过将全局指导与项目特定的覆盖配置分层组合，无论您打开哪个存储库，您都可以在一致的期望下开始每项任务。

## Codex 如何发现指导

Codex 在启动时会构建一个指令链（每次运行一次；在 TUI 中，这通常意味着每次启动的会话一次）。发现遵循以下优先级顺序：

1. **全局范围：** 在您的 Codex 主目录中（默认为 `~/.codex`，除非您设置了 `CODEX_HOME`），如果 `AGENTS.override.md` 存在，Codex 会读取它。否则，Codex 会读取 `AGENTS.md`。Codex 仅使用此级别下的第一个非空文件。
2. **项目范围：** 从项目根目录（通常是 Git 根目录）开始，Codex 会一直向下遍历到您的当前工作目录。如果 Codex 找不到项目根目录，它只会检查当前目录。在路径上的每个目录中，它会检查 `AGENTS.override.md`，然后是 `AGENTS.md`，接着是 `project_doc_fallback_filenames` 中的任何回退名称。Codex 在每个目录中最多包含一个文件。
3. **合并顺序：** Codex 从根目录向下连接文件，并用空行将它们分隔。越靠近您当前目录的文件越会覆盖之前的指导，因为它们出现在合并后的提示词中的位置更靠后。

Codex 会跳过空文件，并且在合并后的大小达到 `project_doc_max_bytes` 定义的限制（默认为 32 KiB）时停止添加文件。有关这些调节参数的详细信息，请参阅 [项目指令发现](https://learn.chatgpt.com/docs/config-file/config-advanced#project-instructions-discovery)。当达到上限时，请提高限制或跨嵌套目录拆分指令。

## 创建全局指导

在您的 Codex 主目录中创建持久默认设置，以便每个存储库都能继承您的工作协议。

1. 确保该目录存在：

   ```bash
   mkdir -p ~/.codex
   ```

2. 使用可重用的首选项创建 `~/.codex/AGENTS.md`：

   ```md
   # ~/.codex/AGENTS.md

   ## 工作协议

   - 修改 JavaScript 文件后始终运行 `npm test`。
   - 安装依赖项时首选 `pnpm`。
   - 添加新的生产环境依赖项之前请求确认。
   ```

3. 在任何地方运行 Codex 以确认它加载了该文件：

   ```bash
   codex --ask-for-approval never "总结当前的指令。"
   ```

   预期结果：Codex 在提出工作建议之前引用 `~/.codex/AGENTS.md` 中的项目。

当您需要临时全局覆盖而不删除基础文件时，请使用 `~/.codex/AGENTS.override.md`。移除覆盖以恢复共享指导。

## 分层项目指令

仓库级文件使 Codex 了解项目规范，同时仍然继承您的全局默认设置。

1. 在您的仓库根目录中，添加一个涵盖基本设置的 `AGENTS.md`：

   ```md
   # AGENTS.md

   ## 仓库期望

   - 在开启拉取请求之前运行 `npm run lint`。
   - 当您更改行为时，请在 `docs/` 中记录公共实用程序。
   ```

2. 当特定团队需要不同的规则时，在嵌套目录中添加覆盖。例如，在 `services/payments/` 内部创建 `AGENTS.override.md`：

   ```md
   # services/payments/AGENTS.override.md

   ## 支付服务规则

   - 使用 `make test-payments` 代替 `npm test`。
   - 切勿在不通知安全渠道的情况下轮换 API 密钥。
   ```

3. 从 payments 目录启动 Codex：

   ```bash
   codex --cd services/payments --ask-for-approval never "列出您加载的指令源。"
   ```

   预期：Codex 首先报告全局文件，其次是仓库根目录的 `AGENTS.md`，最后是 payments 覆盖。

一旦到达您的当前目录，Codex 就会停止搜索，因此请将覆盖放置在尽可能靠近专门工作的位置。

以下是添加全局文件和特定于 payments 的覆盖后的示例仓库：

<FileTree
  class="mt-4"
  tree={[
    {
      name: "AGENTS.md",
      comment: "仓库期望",
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
              comment: "由于存在覆盖而被忽略",
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
在最接近以下代码的 `## Code Review Rules` 中添加 `AGENTS.md` 部分：
受规则约束的代码。将仓库范围的检查放在根目录中，将特定于服务的
检查放在嵌套文件中。

```md
## Code Review Rules

### Experiment cohorts

- Do not filter treatment comparisons on post-exposure behavior, including conversion or retention.
  Safe path: build cohorts from assignment or exposure; report conversion as an outcome.
```

保持规则简明扼要，解释需要标记的行为以及任何安全路径或
例外情况，并将格式化和 lint 检查留给 CI。请参阅 [自定义 Codex
审查的内容](https://learn.chatgpt.com/docs/third-party/github#customize-what-codex-reviews) 以获取
设置和规则编写指南。

## 自定义备用文件名

如果你的仓库已经使用了不同的文件名（例如 `TEAM_GUIDE.md`），请将其添加到备用列表中，以便 Codex 将其视为指令文件。

1. 编辑你的 Codex 配置：

   ```toml
   # ~/.codex/config.toml
   project_doc_fallback_filenames = ["TEAM_GUIDE.md", ".agents.md"]
   project_doc_max_bytes = 65536
   ```

2. 重启 Codex 或运行一个新命令，以便加载更新后的配置。

现在 Codex 会按以下顺序检查每个目录：`AGENTS.override.md`、`AGENTS.md`、`TEAM_GUIDE.md`、`.agents.md`。不在此列表中的文件名在指令发现时将被忽略。更大的字节限制允许在截断前包含更多的组合指南。

有了备用列表后，Codex 会将这些备用文件视为指令：

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
          comment: "覆盖备用指南",
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

当你需要不同的配置文件时，例如特定于项目的自动化用户，请设置 `CODEX_HOME` 环境变量：

```bash
CODEX_HOME=$(pwd)/.codex codex exec "List active instruction sources"
```

预期：输出列出相对于自定义 `.codex` 目录的文件。

## 验证你的设置

- 从仓库根目录运行 `codex --ask-for-approval never "Summarize the current instructions."`。Codex 应该按优先级顺序回显全局和项目文件中的指南。
- 使用 `codex --cd subdir --ask-for-approval never "Show which instruction files are active."` 确认嵌套的覆盖是否替换了更广泛的规则。
- 要审核 Codex 加载了哪些指令文件，请选择使用 `codex -c log_dir=./.codex-log` 生成纯文本 TUI 日志并检查 `./.codex-log/codex-tui.log`，或者如果启用了会话日志记录，请检查最近的 `session-*.jsonl` 文件。
- 如果指令看起来过时，请在目标目录中重启 Codex。Codex 在每次运行时（以及在每个 TUI 会话开始时）都会重建指令链，因此无需手动清除缓存。

## 排查发现的问题

- **未加载任何内容：** 验证你处于预期的仓库中，并且 `codex status` 报告了你所期望的工作区根目录。确保指令文件包含内容；Codex 会忽略空文件。
- **出现错误的指南：** 在目录树的更上层或 Codex 主目录下寻找 `AGENTS.override.md`。重命名或删除覆盖文件以回退到常规文件。
- **Codex 忽略了备用名称：** 确认你在 `project_doc_fallback_filenames` 中列出的名称没有拼写错误，然后重启 Codex 以使更新后的配置生效。
- **指令被截断：** 提高 `project_doc_max_bytes` 或将大文件拆分到嵌套目录中，以保持关键指南的完整。
- **配置文件混淆：** 在启动 Codex 之前运行 `echo $CODEX_HOME`。非默认值会将 Codex 指向与你编辑的目录不同的主目录。

## 后续步骤

- 访问官方 [AGENTS.md](https://agents.md) 网站了解更多信息。
- 查阅 [提示 Codex](https://learn.chatgpt.com/docs/prompting)，了解与持久化指南搭配良好的对话模式。

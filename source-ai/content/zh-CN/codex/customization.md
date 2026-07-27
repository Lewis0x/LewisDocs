---
title: 自定义
source_id: codex/customization
product: codex
lang: zh-CN
canonical_url: https://learn.chatgpt.com/docs/customization/overview
owner: OpenAI
content_sha256: 9d2b2def40c26ae1f7ccc4ac54a2de210f56e7a694a183b3a8d67d9a1e18d5b4
translation_of: codex/customization
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://learn.chatgpt.com/docs/customization/overview)

Content owner: OpenAI

# 自定义

自定义是让你能根据团队的工作方式来配置 Codex 的方法。

在 Codex 中，自定义来源于几个协同工作的层：

- **项目指南 (`AGENTS.md`)** 用于持久化指令
- **[记忆](https://learn.chatgpt.com/docs/customization/memories)** 用于从先前工作中学习的有用上下文
- **技能** 用于可重用的工作流和领域专业知识
- **[MCP](https://learn.chatgpt.com/docs/extend/mcp)** 用于访问外部工具和共享系统
- **[子代理](https://learn.chatgpt.com/docs/agent-configuration/subagents)** 用于将工作委托给专门的子代理

它们是互补的，而不是竞争的。`AGENTS.md` 塑造行为，记忆
传递本地上下文，技能封装可重复的过程，而
[MCP](https://learn.chatgpt.com/docs/extend/mcp) 将 Codex 连接到本地工作区之外的系统。

## AGENTS 指南

`AGENTS.md` 为 Codex 提供持久的指南，它会伴随你的仓库，并在代理开始工作之前应用。请保持其简短。

将其用于你希望 Codex 每次在仓库中都遵循的规则，例如：

- 构建和测试命令
- 审查期望
- 仓库特定约定
- 目录特定指令

当代理对你的代码库做出错误的假设时，在 `AGENTS.md` 中纠正它们，并要求代理更新 `AGENTS.md`，以便修复得以持久保留。将其视为一个反馈循环。

**更新 `AGENTS.md`：** 从仅包含重要指令开始。将反复出现的审查反馈代码化，将指南放在适用的最近目录中，并在你纠正某些内容时告诉代理更新 `AGENTS.md`，以便未来的会话继承此修复。

### 何时更新 `AGENTS.md`

- **重复的错误**：如果代理反复犯相同的错误，请添加一条规则。
- **阅读过多**：如果它找到了正确的文件但阅读了太多文档，请添加路由指南（优先处理哪些目录/文件）。
- **反复出现的 PR 反馈**：如果你不止一次留下了相同的反馈，请将其代码化。
- **在 GitHub 中**：在拉取请求评论中，使用请求标记 `@codex`（例如，`@codex add this to AGENTS.md`）以将更新委托给云端聊天。
- **自动化偏差检查**：使用 [定时任务](https://learn.chatgpt.com/docs/automations) 运行定期检查（例如，每天），以寻找指南空白并建议要添加到 `AGENTS.md` 中的内容。

将 `AGENTS.md` 与强制执行这些规则的基础设施配对使用：预提交钩子、代码检查器和类型检查器会在你发现问题之前捕捉它们，从而让系统在防止重复错误方面变得更加智能。

Codex 可以从多个位置加载指南：Codex 主目录中的全局文件（对于作为开发者的你）以及团队可以签入的仓库特定文件。距离工作目录越近的文件优先级越高。
使用全局文件来塑造 Codex 与你的沟通方式（例如，审查风格、详细程度和默认设置），并让仓库文件专注于团队和代码库规则。

<FileTree
  class="mt-4"
  tree={[
    {
      name: "~/.codex/",
      open: true,
      children: [
        { name: "AGENTS.md", comment: "全局（对于作为开发者的你）" },
      ],
    },
    {
      name: "repo-root/",
      open: true,
      children: [
        { name: "AGENTS.md", comment: "仓库特定（对于你的团队）" },
      ],
    },
  ]}
/>

[使用 AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md) 的自定义指令

## 技能

技能为 Codex 提供用于可重复工作流的可重用能力。
技能通常是可重用工作流的最佳选择，因为它们支持更丰富的指令、脚本和引用，同时在不同任务间保持可重用性。
技能会被加载并且对智能体可见（至少它们的元数据是可见的），因此 Codex 可以隐式地发现并选择它们。这使得丰富的工作流保持可用，而不会在一开始就让上下文变得臃肿。

使用技能文件夹在本地编写和迭代工作流。如果插件
对于该工作流已经存在，请先安装它以重用经过验证的设置。当
您想要在团队间分发自己的工作流或将其与
连接器捆绑时，请将其打包为 [plugin](https://learn.chatgpt.com/docs/build-plugins)。技能仍然是
编写格式；插件是可安装的分发单元。

技能通常是一个 `SKILL.md` 文件加上可选的脚本、引用和资产。

<FileTree
  class="mt-4"
  tree={[
    {
      name: "my-skill/",
      open: true,
      children: [
        { name: "SKILL.md", comment: "必需：指令 + 元数据" },
        { name: "scripts/", comment: "可选：可执行代码" },
        { name: "references/", comment: "可选：文档" },
        { name: "assets/", comment: "可选：模板，资源" },
      ],
    },
  ]}
/>

技能目录可以包含一个 `scripts/` 文件夹，其中带有 Codex 作为工作流一部分调用的 CLI 脚本（例如，填充数据或运行验证）。当工作流需要外部系统（问题追踪器、设计工具、文档服务器）时，请将技能与 [MCP](https://learn.chatgpt.com/docs/extend/mcp) 配对。

示例 `SKILL.md`：

```md
---
name: commit
description: Stage and commit changes in semantic groups. Use when the user wants to commit, organize commits, or clean up a branch before pushing.
---

1. Do not run `git add .`. Stage files in logical groups by purpose.
2. Group into separate commits: feat → test → docs → refactor → chore.
3. Write concise commit messages that match the change scope.
4. Keep each commit focused and reviewable.
```

在以下情况使用技能：

- 可重复的工作流（发布步骤、审查例程、文档更新）
- 团队特定的专业知识
- 需要示例、引用或辅助脚本的过程

技能可以是全局的（位于您的用户目录中，供您作为开发者使用）或特定于代码仓库的（签入到 `.agents/skills` 中，供您的团队使用）。当工作流适用于该项目时，请将仓库技能放在 `.agents/skills` 中；对于您希望在所有仓库中使用的技能，请使用您的用户目录。

| 层级  | 全局               | 仓库                                           |
| :----- | :------------------- | :--------------------------------------------- |
| AGENTS | `~/.codex/AGENTS.md` | `AGENTS.md` 位于仓库根目录或嵌套目录中 |
| Skills | `~/.agents/skills`   | `.agents/skills` 位于仓库中                       |

Codex 对技能采用渐进式披露：

- 它从用于发现的元数据开始（`name`，`description`）
- 它仅在技能被选中时加载 `SKILL.md`
- 它仅在需要时读取引用或运行脚本

技能可以被显式调用，并且当任务与技能描述匹配时，Codex 也可以隐式地选择它们。清晰的技能描述能提高触发的可靠性。

[构建技能](https://learn.chatgpt.com/docs/build-skills)

## MCP

MCP（模型上下文协议）是将 Codex 连接到外部工具和上下文提供程序的标准方式。
它对于团队依赖的远程托管系统（如 Figma、Linear、GitHub 或内部知识服务）特别有用。

当 Codex 需要存在于本地仓库之外的功能（例如问题追踪器、设计工具、浏览器或共享文档系统）时，请使用 MCP。

理解它的一种方式：

- **宿主**：Codex
- **客户端**：Codex 内部的 MCP 连接
- **服务器**：外部工具或上下文提供程序

MCP 服务器可以暴露：

- **工具**（动作）
- **资源**（可读数据）
- **提示**（可重用的提示模板）

这种分离有助于您推断信任和能力边界。有些服务器主要提供上下文，而另一些则暴露强大的动作。

在实践中，MCP 与技能配对使用时通常最有用：

- 技能定义工作流并命名要使用的 MCP 工具

[模型上下文协议](https://learn.chatgpt.com/docs/extend/mcp)

## 子代理

您可以创建具有不同角色的不同代理，并提示它们以不同方式使用工具。例如，一个代理可能运行特定的测试命令和配置，而另一个代理则使用 MCP 服务器获取生产日志以进行调试。每个子代理都保持专注，并为其工作使用合适的工具。

[子代理](https://learn.chatgpt.com/docs/agent-configuration/subagents)

## 技能 + MCP 结合使用

技能与 MCP 的结合将一切融为一体：技能定义了可重复的工作流，而 MCP 将它们连接到外部工具和系统。
如果某个技能依赖于 MCP，请在 `agents/openai.yaml` 中声明该依赖项，以便 Codex 能够自动安装并连接它（参见 [构建技能](https://learn.chatgpt.com/docs/build-skills)）。

## 下一步

按以下顺序进行构建：

1. [带有 AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md) 的自定义指令，以便 Codex 遵循您的仓库规范。添加 pre-commit 钩子和 linter 来强制执行这些规则。
2. 当已经存在可重用的工作流时，安装 [插件](https://learn.chatgpt.com/docs/plugins)。否则，创建一个 [技能](https://learn.chatgpt.com/docs/build-skills)，并在需要共享时将其打包为插件。
3. [MCP](https://learn.chatgpt.com/docs/extend/mcp) 用于当工作流需要外部系统（如 Linear、GitHub、文档服务器、设计工具）时。
4. [子代理](https://learn.chatgpt.com/docs/agent-configuration/subagents) 用于当您准备好将繁杂或专业化的任务委托给子代理时。

---
title: SDK 中的 Agent Skills
source_id: claude-code/agent-sdk/skills
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/agent-sdk/skills
owner: Anthropic
content_sha256: ac4b7534b167e83d746c590020d9c2ce30634bcc75223e55e72f0fad2a3fbbed
translation_of: claude-code/agent-sdk/skills
translation_model: k3
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/agent-sdk/skills)

Content owner: Anthropic

> ## 文档索引
> 在此获取完整的文档索引：https://code.claude.com/docs/llms.txt
> 在进一步探索之前，请使用此文件发现所有可用页面。

# SDK 中的 Agent Skills

> 在 Claude Agent SDK 中使用 Agent Skills 为 Claude 扩展专门的能力

## 概述

Agent Skills 为 Claude 扩展了专门的能力，Claude 会在相关时自主调用它们。Skills 打包为 `SKILL.md` 文件，其中包含指令、描述以及可选的支持资源。

有关 Skills 的全面信息，包括优势、架构和编写指南，请参阅 [Agent Skills 概述](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)。

## Skills 如何与 SDK 协同工作

在使用 Claude Agent SDK 时，Skills 具有以下特点：

1. **定义为文件系统产物**：在特定目录中创建为 `SKILL.md` 文件（`.claude/skills/`）
2. **从文件系统加载**：Skills 从由 `settingSources`（TypeScript）或 `setting_sources`（Python）控制的文件系统位置加载
3. **自动发现**：加载文件系统设置后，Skill 元数据会在启动时从用户目录和项目目录中被发现；完整内容在触发时加载
4. **由模型调用**：Claude 会根据上下文自主选择何时使用它们
5. **通过 `skills` 选项进行过滤**：已发现的 skills 默认启用。可以传入 skill 名称列表、`"all"` 或 `[]` 来控制会话中哪些可用

与子代理（可以通过编程方式定义）不同，Skills 必须作为文件系统产物创建。SDK 不提供以编程方式注册 Skills 的 API。

<Note>
  Skills 通过文件系统设置来源被发现。使用默认的 `query()` 选项时，SDK 会加载用户和项目来源，因此位于 `~/.claude/skills/`、`<cwd>/.claude/skills/` 以及 `<cwd>` 的任何父目录中直至仓库根目录的 `.claude/skills/` 中的 skills 都可用。如果你显式设置了 `settingSources`，请包含 `'user'` 或 `'project'` 以保留 skill 发现功能，或使用 [`plugins` 选项](/docs/en/agent-sdk/plugins) 从特定路径加载 skills。
</Note>

## 在 SDK 中使用技能

在 `query()` 上设置 `skills` 选项，以控制会话中可用的技能。省略时，发现的技能会被启用且技能工具可用，与 CLI 行为一致。传入 `"all"` 可启用所有发现的技能，传入技能名称列表则仅启用指定技能，传入 `[]` 则全部禁用。设置 `skills` 后，SDK 会自动将技能工具添加到 `allowedTools`。如果你同时传入了显式的 `tools` 列表，请在该列表中包含 `"Skill"`，以便 Claude 能调用技能。

配置完成后，Claude 会自动从文件系统发现技能，并在与用户请求相关时调用它们。

<CodeGroup>
  ```python Python theme={null}
  import asyncio
  from claude_agent_sdk import query, ClaudeAgentOptions


  async def main():
      options = ClaudeAgentOptions(
          cwd="/path/to/project",  # Project with .claude/skills/
          setting_sources=["user", "project"],  # Load Skills from filesystem
          skills="all",  # Enable every discovered Skill
          allowed_tools=["Read", "Write", "Bash"],
      )

      async for message in query(
          prompt="Help me process this PDF document", options=options
      ):
          print(message)


  asyncio.run(main())
  ```

  ```typescript TypeScript theme={null}
  import { query } from "@anthropic-ai/claude-agent-sdk";

  for await (const message of query({
    prompt: "Help me process this PDF document",
    options: {
      cwd: "/path/to/project", // Project with .claude/skills/
      settingSources: ["user", "project"], // Load Skills from filesystem
      skills: "all", // Enable every discovered Skill
      allowedTools: ["Read", "Write", "Bash"]
    }
  })) {
    console.log(message);
  }
  ```
</CodeGroup>

要仅启用特定技能，请传入它们的名称。名称与 `SKILL.md` 中的 `name` 字段或技能的目录名匹配。对于插件提供的技能，请使用 `plugin:skill`。

<CodeGroup>
  ```python Python theme={null}
  options = ClaudeAgentOptions(skills=["pdf", "docx"])
  ```

  ```typescript TypeScript theme={null}
  const options = { skills: ["pdf", "docx"] };
  ```
</CodeGroup>

`skills` 选项是上下文过滤器，而非沙箱。未列出的技能对模型隐藏并被技能工具拒绝，但其文件仍保留在磁盘上，可通过 Read 和 Bash 访问。

## 技能位置

技能根据你的 `settingSources`/`setting_sources` 配置从文件系统目录加载：

* **项目技能**（`.claude/skills/`）：通过 git 与团队共享——当 `setting_sources` 包含 `"project"` 时加载
* **用户技能**（`~/.claude/skills/`）：跨所有项目的个人技能——当 `setting_sources` 包含 `"user"` 时加载
* **插件技能**：随已安装的 Claude Code 插件捆绑

## 创建技能

技能以目录形式定义，其中包含一个带有 YAML frontmatter 和 Markdown 内容的 `SKILL.md` 文件。`description` 字段决定 Claude 何时调用你的技能。

**示例目录结构**：

```bash theme={null}
.claude/skills/processing-pdfs/
└── SKILL.md
```

有关创建技能的完整指南，包括 SKILL.md 结构、多文件技能和示例，请参阅：

* [Claude Code 中的 Agent Skills](/docs/en/skills)：带示例的完整指南
* [Agent Skills 最佳实践](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)：编写指南与命名约定

## 工具限制

<Note>
  SKILL.md 中的 `allowed-tools` 前置元数据字段仅在直接使用 Claude Code CLI 时受支持。**通过 SDK 使用 Skills 时它不适用**。

  使用 SDK 时，请通过查询配置中的主 `allowedTools` 选项来控制工具访问。
</Note>

要在 SDK 应用程序中控制 Skills 的工具访问，请使用 `allowedTools` 预先批准特定工具。如果没有 `canUseTool` 回调，任何不在列表中的工具请求都会被拒绝：

<Note>
  以下代码片段中假定已包含第一个示例中的导入语句。
</Note>

<CodeGroup>
  ```python Python theme={null}
  options = ClaudeAgentOptions(
      setting_sources=["user", "project"],  # Load Skills from filesystem
      skills="all",
      allowed_tools=["Read", "Grep", "Glob"],
  )

  async for message in query(prompt="Analyze the codebase structure", options=options):
      print(message)
  ```

  ```typescript TypeScript theme={null}
  for await (const message of query({
    prompt: "Analyze the codebase structure",
    options: {
      settingSources: ["user", "project"], // Load Skills from filesystem
      skills: "all",
      allowedTools: ["Read", "Grep", "Glob"],
      permissionMode: "dontAsk" // Deny anything not in allowedTools
    }
  })) {
    console.log(message);
  }
  ```
</CodeGroup>

## 发现可用的 Skills

要查看你的 SDK 应用程序中有哪些可用的 Skills，只需询问 Claude：

<CodeGroup>
  ```python Python theme={null}
  options = ClaudeAgentOptions(
      setting_sources=["user", "project"],  # Load Skills from filesystem
      skills="all",
  )

  async for message in query(prompt="What Skills are available?", options=options):
      print(message)
  ```

  ```typescript TypeScript theme={null}
  for await (const message of query({
    prompt: "What Skills are available?",
    options: {
      settingSources: ["user", "project"], // Load Skills from filesystem
      skills: "all"
    }
  })) {
    console.log(message);
  }
  ```
</CodeGroup>

Claude 会根据你当前的工作目录和已安装的插件列出可用的 Skills。

## 测试 Skills

通过提出与 Skill 描述相匹配的问题来测试 Skills：

<CodeGroup>
  ```python Python theme={null}
  options = ClaudeAgentOptions(
      cwd="/path/to/project",
      setting_sources=["user", "project"],  # Load Skills from filesystem
      skills="all",
      allowed_tools=["Read", "Bash"],
  )

  async for message in query(prompt="Extract text from invoice.pdf", options=options):
      print(message)
  ```

  ```typescript TypeScript theme={null}
  for await (const message of query({
    prompt: "Extract text from invoice.pdf",
    options: {
      cwd: "/path/to/project",
      settingSources: ["user", "project"], // Load Skills from filesystem
      skills: "all",
      allowedTools: ["Read", "Bash"]
    }
  })) {
    console.log(message);
  }
  ```
</CodeGroup>

如果描述与你的请求匹配，Claude 会自动调用相关的 Skill。

## 故障排除

### 找不到技能

**检查 settingSources 配置**：技能是通过 `user` 和 `project` 设置源发现的。如果你显式设置了 `settingSources`/`setting_sources` 并省略了这些源，技能将不会被加载：

<CodeGroup>
  ```python Python theme={null}
  # Skills not loaded: setting_sources excludes user and project
  options = ClaudeAgentOptions(setting_sources=[], skills="all")

  # Skills loaded: user and project sources included
  options = ClaudeAgentOptions(
      setting_sources=["user", "project"],
      skills="all",
  )
  ```

  ```typescript TypeScript theme={null}
  // Skills not loaded: settingSources excludes user and project
  const options = {
    settingSources: [],
    skills: "all"
  };

  // Skills loaded: user and project sources included
  const options = {
    settingSources: ["user", "project"],
    skills: "all"
  };
  ```
</CodeGroup>

有关 `settingSources`/`setting_sources` 的更多详细信息，请参阅 [TypeScript SDK 参考](/docs/en/agent-sdk/typescript#settingsource) 或 [Python SDK 参考](/docs/en/agent-sdk/python#settingsource)。

**检查工作目录**：SDK 会从 `cwd` 选项指定的目录以及向上至仓库根目录的每个父目录中的 `.claude/skills/` 加载技能。确保 `cwd` 指向包含 `.claude/skills/` 的目录或其子目录，并且在同一仓库内：

<CodeGroup>
  ```python Python theme={null}
  # Ensure your cwd points to the directory containing .claude/skills/
  options = ClaudeAgentOptions(
      cwd="/path/to/project",  # .claude/skills/ here or in a parent directory
      setting_sources=["user", "project"],  # Loads skills from these sources
      skills="all",
  )
  ```

  ```typescript TypeScript theme={null}
  // Ensure your cwd points to the directory containing .claude/skills/
  const options = {
    cwd: "/path/to/project", // .claude/skills/ here or in a parent directory
    settingSources: ["user", "project"], // Loads skills from these sources
    skills: "all"
  };
  ```
</CodeGroup>

有关完整模式，请参阅上文“在 SDK 中使用技能”部分。

**验证文件系统位置**：

```bash theme={null}
# Check project Skills

ls .claude/skills/*/SKILL.md

# Check personal Skills

ls ~/.claude/skills/*/SKILL.md
```

### 技能未被使用

**检查 `skills` 选项**：如果你传递了 `skills` 列表，请确认其中包含该技能的名称。传递 `[]` 会禁用所有技能。

**检查描述**：确保描述具体并包含相关关键字。有关编写有效描述的指南，请参阅 [代理技能最佳实践](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#writing-effective-descriptions)。

### 其他故障排除

有关常规技能故障排除（YAML 语法、调试等），请参阅 [Claude Code 技能故障排除部分](/docs/en/skills#troubleshooting)。

## 相关文档

### 技能指南

* [在 Claude Code 中使用代理技能](/docs/en/skills)：包含创建、示例和故障排除的完整技能指南
* [代理技能概述](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)：概念概述、优势和架构
* [代理技能最佳实践](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)：编写有效技能的指南
* [代理技能手册](https://platform.claude.com/cookbook/skills-notebooks-01-skills-introduction)：技能示例和模板

### SDK 资源

* [SDK 中的子代理](/docs/en/agent-sdk/subagents)：具有编程选项的类似基于文件系统的代理
* [SDK 中的斜杠命令](/docs/en/agent-sdk/slash-commands)：用户调用的命令
* [SDK 概述](/docs/en/agent-sdk/overview)：SDK 通用概念
* [TypeScript SDK 参考](/docs/en/agent-sdk/typescript)：完整的 API 文档
* [Python SDK 参考](/docs/en/agent-sdk/python)：完整的 API 文档

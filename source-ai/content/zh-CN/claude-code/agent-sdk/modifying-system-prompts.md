---
title: 修改系统提示词
source_id: claude-code/agent-sdk/modifying-system-prompts
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/agent-sdk/modifying-system-prompts
owner: Anthropic
content_sha256: 99eed2b8e57e645c5ce12fd537d6e637209827cb452678cc1c472c6bb3aed0c6
translation_of: claude-code/agent-sdk/modifying-system-prompts
translation_model: k3
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/agent-sdk/modifying-system-prompts)

Content owner: Anthropic

> ## 文档索引
> 在以下地址获取完整的文档索引：https://code.claude.com/docs/llms.txt
> 在进一步探索之前，使用此文件发现所有可用页面。

# 修改系统提示词

> 在 `claude_code` 预设和自定义系统提示词之间进行选择，并使用 CLAUDE.md、输出样式、追加内容或完全自定义的提示词来自定义行为。

系统提示词定义了 Claude 的行为、能力和响应风格。对于 CLI 或类似 IDE 的编码工具，从 `claude_code` 预设开始，这类工具中有人工监督并引导工作。对于具有不同界面、身份或权限模型的智能体，请编写你自己的提示词。

本页涵盖：

* [系统提示词的工作原理](#how-system-prompts-work)，并附有决策表，用于在预设、带 `append` 的预设和自定义提示词之间进行选择
* [自定义智能体行为](#customize-agent-behavior)，使用 CLAUDE.md 文件、输出样式、`append` 或自定义字符串
* [比较四种方法](#compare-the-four-approaches)，从持久性、作用范围和保留内容方面进行比较
* [组合多种方法](#combine-approaches)，将自定义方法叠加在一起

## 系统提示词的工作原理

系统提示词是一组初始指令，它塑造了 Claude 在整个对话过程中的行为方式。Agent SDK 有三个起点：

* **最小默认值**：当你在 TypeScript 中不设置 `systemPrompt` 或在 Python 中不设置 `system_prompt` 时，SDK 使用一个最小提示词，它涵盖工具调用，但省略了 Claude Code 的编码指南、响应风格和项目上下文。这与 `claude -p` 不同，后者默认使用完整的 Claude Code 提示词。如果你正在从 CLI 迁移并希望行为保持一致，请设置 `claude_code` 预设。
* **`claude_code` 预设**：Claude Code CLI 使用的完整系统提示词，包含工具使用说明、代码风格和格式指南、响应语气和冗长度规则、安全与防护指令，以及有关工作目录和环境的上下文。在 TypeScript 中设置 `systemPrompt: { type: "preset", preset: "claude_code" }` 或在 Python 中设置 `system_prompt={"type": "preset", "preset": "claude_code"}`，可选地配合 `append` 在末尾添加你自己的指令。
* **自定义字符串**：你自己编写的提示词。SDK 只发送你提供的内容。

### 确定一个起点

决定性因素是你的智能体与 Claude Code 的相似程度：一个在代码仓库中运行的编程智能体，由人类观看流式输出并引导工作。你的产品与此相差越远，你就越应该编写自己的提示词。

| 你正在构建                                                                                              | 使用                                | 你将获得                                                                                                                  |
| :----------------------------------------------------------------------------------------------------------- | :--------------------------------- | :---------------------------------------------------------------------------------------------------------------------------- |
| 一个 CLI 或类似 IDE 的编程工具，由人类观看并引导，且 Claude Code 的默认设置正是你想要的 | `claude_code` 预设               | 完整的 Claude Code 提示词：工具指导、安全规则、适合终端的响应、仓库约定感知              |
| 同类型的工具，外加产品特定规则，如编码标准、输出格式或领域上下文   | `claude_code` 预设配合 `append` | 以上所有内容，并将你的指令附加在预设之后。不会移除任何内容，因此这是风险最低的自定义方式 |
| 具有不同界面、身份或权限模型的智能体，或非编程智能体                      | 自定义提示词字符串               | 只有你编写的内容。你需要负责替换你的智能体仍然需要的工具指导和安全指令   |
| 一个没有智能体人格的精简工具调用循环，所有行为都由你在用户提示词中提供             | 不使用 `systemPrompt` 选项           | 最小默认值：仅支持工具调用，别无其他                                                                    |

“与 Claude Code 不同”通常意味着以下情况之一：

* **不同的界面**：输出不是由触发它的人在终端中阅读的。聊天 UI、结构化输出的消费方以及非编程自动化各自都需要一个与其输出呈现和审查方式相匹配的提示词。无人值守的编程自动化，例如修复 lint 错误或审查 diff 的 CI 任务，仍然适合该预设，因为该预设正是为这类工作本身而编写的。
* **不同的身份**：智能体不应以 Claude Code 的身份示人。支持机器人、数据分析助手或任何特定领域的智能体都需要自己的名称、范围和人格。
* **不同的权限模型**：智能体自主运行，无需人类逐步批准，或者只操作一组狭窄的资源。Claude Code 的提示词假设有一个人在循环中，并可以访问完整的工具集。
* **非编程任务**：Claude Code 的提示词大部分是编程指导。对于研究、内容或运维类智能体，这些指导会与你实际需要的指令相互冲突。

[对比表](#compare-the-four-approaches) 展示了每种自定义方法所保留的内容。

## 自定义智能体行为

输出样式、`append` 和自定义提示词字符串各自直接改变系统提示词。CLAUDE.md 走的是另一条路径：SDK 读取它，并将其内容作为项目上下文注入对话，而不是注入系统提示词，因此它会与你选择的任何系统提示词一起塑造行为。[技能](/docs/en/agent-sdk/skills)、[钩子](/docs/en/agent-sdk/hooks) 和 [权限](/docs/en/agent-sdk/permissions) 也会在系统提示词之外塑造行为，并在它们各自的页面中介绍。

### CLAUDE.md 项目级指令文件

CLAUDE.md 文件为 Claude 提供持久的项目上下文和指令。SDK 会将其内容注入到对话中，而不是注入到系统提示中，因此它们可与任何系统提示配置配合使用。关于 CLAUDE.md 中应写什么、放在哪里，以及如何编写有效的指令，请参阅 [Claude 如何记住你的项目](/docs/en/memory)。本节介绍 SDK 特有的内容：CLAUDE.md 如何加载。

当启用匹配的设置来源时，SDK 会读取 CLAUDE.md：`'project'` 从工作目录加载 `CLAUDE.md` 或 `.claude/CLAUDE.md`，而 `'user'` 加载 `~/.claude/CLAUDE.md`。默认的 `query()` 选项会同时启用这两个来源，因此 CLAUDE.md 会自动加载。如果你在 TypeScript 中显式设置 `settingSources` 或在 Python 中显式设置 `setting_sources`，请包含你需要的来源。CLAUDE.md 的加载由设置来源控制，而不是由 `claude_code` 预设控制。

#### 使用 SDK 加载 CLAUDE.md

要加载 CLAUDE.md，请将 `settingSources` 设置为包含你的 CLAUDE.md 所在的级别。下面的示例在 `claude_code` 预设之外加载了项目级 CLAUDE.md，这样 Claude 既拥有完整的编码智能体提示，也拥有你项目的约定：

<CodeGroup>
  ```typescript TypeScript theme={null}
  import { query } from "@anthropic-ai/claude-agent-sdk";

  const messages = [];

  for await (const message of query({
    prompt: "Add a new React component for user profiles",
    options: {
      systemPrompt: {
        type: "preset",
        preset: "claude_code" // Use Claude Code's system prompt
      },
      settingSources: ["project"] // Loads CLAUDE.md from project
    }
  })) {
    messages.push(message);
  }

  // Now Claude has access to your project guidelines from CLAUDE.md
  ```

  ```python Python theme={null}
  from claude_agent_sdk import query, ClaudeAgentOptions

  messages = []

  async for message in query(
      prompt="Add a new React component for user profiles",
      options=ClaudeAgentOptions(
          system_prompt={
              "type": "preset",
              "preset": "claude_code",  # Use Claude Code's system prompt
          },
          setting_sources=["project"],  # Loads CLAUDE.md from project
      ),
  ):
      messages.append(message)

  # Now Claude has access to your project guidelines from CLAUDE.md
  ```
</CodeGroup>

CLAUDE.md 在项目的所有会话中持久存在，通过 git 与你的团队共享，并且无需更改代码即可被自动发现。如果你传递一个空的 `settingSources` 数组，它将不会被加载。

### 用于持久配置的输出样式

输出样式是用于修改 Claude 系统提示的已保存配置。它们以 markdown 文件的形式存储，可以跨会话和项目重复使用。

#### 创建输出样式

输出样式是一个 markdown 文件，带有用于元数据的 [frontmatter](/docs/en/output-styles#frontmatter)，其后是提示内容。将其保存到 `~/.claude/output-styles/` 可作为在每个项目中都可用的用户级样式，或保存到仓库中的 `.claude/output-styles/` 作为可提交并与团队共享的项目级样式。

默认情况下，自定义输出样式会用你自己的指令替换 `claude_code` 预设的软件工程指令。若要保留这些指令并在其上叠加你自己的指令，请在 frontmatter 中设置 `keep-coding-instructions: true`。当你的智能体仍在执行软件工程工作时，请保留它们；当你要完全替换其角色时，请将其省略。

下面的示例定义了一个代码审查角色，它保留了编码指令，因为审查代码仍然受益于 Claude Code 的安全性和代码质量指导。将其保存为 `~/.claude/output-styles/code-reviewer.md` 即可跨项目使用：

```markdown ~/.claude/output-styles/code-reviewer.md theme={null}
---
name: Code Reviewer
description: Thorough code review assistant
keep-coding-instructions: true
---

You are an expert code reviewer.

For every code submission:
1. Check for bugs and security issues
2. Evaluate performance
3. Suggest improvements
4. Rate code quality (1-10)
```

#### 激活输出样式

创建完成后，可通过以下方式激活输出样式：

* **CLI**：运行 `/config` 并选择一个输出样式
* **设置**：在 `.claude/settings.local.json` 中设置 `outputStyle`
* **TypeScript SDK**：在传递给 `query()` 的内联 `settings` 对象中设置 `outputStyle`，或将 `settings` 指向设置了该字段的设置文件。`outputStyle` 不是 `Options` 的顶层字段：

  ```typescript theme={null}
  const options = { settings: { outputStyle: "Explanatory" } };
  ```

Python SDK 没有以编程方式选择输出样式的选项。对于无法写入 `.claude/settings.local.json` 的纯代码部署场景，请改用 `append` 或自定义提示字符串。

**SDK 用户须知：** 当你在选项中包含 `settingSources: ['user']` 或 `settingSources: ['project']`（TypeScript）/ `setting_sources=["user"]` 或 `setting_sources=["project"]`（Python）时，输出样式会被加载。

### 向 `claude_code` 预设追加内容

你可以使用 Claude Code 预设并结合 `append` 属性，在保留所有内置功能的同时添加自定义指令。

<CodeGroup>
  ```typescript TypeScript theme={null}
  import { query } from "@anthropic-ai/claude-agent-sdk";

  const messages = [];

  for await (const message of query({
    prompt: "Help me write a Python function to calculate fibonacci numbers",
    options: {
      systemPrompt: {
        type: "preset",
        preset: "claude_code",
        append: "Always include detailed docstrings and type hints in Python code."
      }
    }
  })) {
    messages.push(message);
    if (message.type === "assistant") {
      console.log(message.message.content);
    }
  }
  ```

  ```python Python theme={null}
  from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage

  messages = []

  async for message in query(
      prompt="Help me write a Python function to calculate fibonacci numbers",
      options=ClaudeAgentOptions(
          system_prompt={
              "type": "preset",
              "preset": "claude_code",
              "append": "Always include detailed docstrings and type hints in Python code.",
          }
      ),
  ):
      messages.append(message)
      if isinstance(message, AssistantMessage):
          print(message.content)
  ```
</CodeGroup>

#### 提升跨用户和跨机器的提示缓存效果

默认情况下,使用相同 `claude_code` 预设和 `append` 文本的两个会话,如果从不同的工作目录运行,仍然无法共享提示缓存条目。这是因为预设会在你的 `append` 文本之前,将每个会话的上下文嵌入系统提示中:工作目录、是否为 git 仓库、平台、活动 shell、操作系统版本以及自动记忆路径。这些上下文中的任何差异都会产生不同的系统提示并导致缓存未命中。CLAUDE.md 内容不影响系统提示缓存,因为 SDK 会将其注入对话中,而不是系统提示中。

要使系统提示在各会话间保持完全一致,请在 TypeScript 中设置 `excludeDynamicSections: true`,或在 Python 中设置 `"exclude_dynamic_sections": True`。每个会话的上下文会被移入第一条用户消息,系统提示中只保留静态预设和你的 `append` 文本,这样相同的配置就能跨用户和跨机器共享缓存条目。

<Note>
  `excludeDynamicSections` 需要 `@anthropic-ai/claude-agent-sdk` v0.2.98 或更高版本,Python 则需要 `claude-agent-sdk` v0.1.58 或更高版本。它仅适用于预设对象形式,当 `systemPrompt` 为字符串时无效。
</Note>

下面的示例将共享的 `append` 块与 `excludeDynamicSections` 搭配使用,使一组从不同目录运行的智能体可以复用同一个缓存的系统提示:

<CodeGroup>
  ```typescript TypeScript theme={null}
  import { query } from "@anthropic-ai/claude-agent-sdk";

  for await (const message of query({
    prompt: "Triage the open issues in this repo",
    options: {
      systemPrompt: {
        type: "preset",
        preset: "claude_code",
        append: "You operate Acme's internal triage workflow. Label issues by component and severity.",
        excludeDynamicSections: true
      }
    }
  })) {
    // ...
  }
  ```

  ```python Python theme={null}
  from claude_agent_sdk import query, ClaudeAgentOptions

  async for message in query(
      prompt="Triage the open issues in this repo",
      options=ClaudeAgentOptions(
          system_prompt={
              "type": "preset",
              "preset": "claude_code",
              "append": "You operate Acme's internal triage workflow. Label issues by component and severity.",
              "exclude_dynamic_sections": True,
          },
      ),
  ):
      ...
  ```
</CodeGroup>

**权衡:** 工作目录、git 仓库标志、平台、活动 shell、操作系统版本以及自动记忆路径仍会传达给 Claude,但会作为第一条用户消息的一部分,而不是系统提示。用户消息中的指令的权重略低于系统提示中的相同文本,因此 Claude 在推理当前目录或自动记忆路径时,可能对它们的依赖程度较低。当跨会话缓存复用比最高权威性的环境上下文更重要时,请启用此选项。

关于非交互式 CLI 模式中的等效标志,请参阅 [`--exclude-dynamic-system-prompt-sections`](/docs/en/cli-reference)。

### 自定义系统提示

你可以提供一个自定义字符串作为 `systemPrompt`，用你自己的指令完全替换默认内容。

<CodeGroup>
  ```typescript TypeScript theme={null}
  import { query } from "@anthropic-ai/claude-agent-sdk";

  const customPrompt = `You are a Python coding specialist.
  Follow these guidelines:
  - Write clean, well-documented code
  - Use type hints for all functions
  - Include comprehensive docstrings
  - Prefer functional programming patterns when appropriate
  - Always explain your code choices`;

  const messages = [];

  for await (const message of query({
    prompt: "Create a data processing pipeline",
    options: {
      systemPrompt: customPrompt
    }
  })) {
    messages.push(message);
    if (message.type === "assistant") {
      console.log(message.message.content);
    }
  }
  ```

  ```python Python theme={null}
  from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage

  custom_prompt = """You are a Python coding specialist.
  Follow these guidelines:
  - Write clean, well-documented code
  - Use type hints for all functions
  - Include comprehensive docstrings
  - Prefer functional programming patterns when appropriate
  - Always explain your code choices"""

  messages = []

  async for message in query(
      prompt="Create a data processing pipeline",
      options=ClaudeAgentOptions(system_prompt=custom_prompt),
  ):
      messages.append(message)
      if isinstance(message, AssistantMessage):
          print(message.content)
  ```
</CodeGroup>

## 比较四种方法

这四种自定义方法在存放位置、共享方式以及从 `claude_code` 预设中保留的内容方面各不相同。

| 特性                    | CLAUDE.md        | 输出样式                  | `systemPrompt` 追加模式 | 自定义 `systemPrompt`  |
| ----------------------- | ---------------- | ------------------------- | -------------------------- | ---------------------- |
| **持久性**              | 项目级文件 | 保存为文件                | 仅限会话                   | 仅限会话               |
| **可复用性**            | 项目级       | 跨项目                    | 代码重复                   | 代码重复               |
| **管理方式**            | 文件系统     | CLI + 文件                | 代码中                     | 代码中                 |
| **默认工具**            | 保留         | 保留                      | 保留                       | 丢失（除非包含）       |
| **内置安全性**          | 维持         | 维持                      | 维持                       | 必须手动添加           |
| **环境上下文**          | 自动         | 自动                      | 自动                       | 必须手动提供           |
| **自定义程度**          | 仅追加       | 替换或扩展默认            | 仅追加                     | 完全控制               |
| **版本控制**            | 随项目       | 是                        | 随代码                     | 随代码                 |
| **作用范围**            | 项目特定     | 用户或项目                | 代码会话                   | 代码会话               |

"追加模式"指在 TypeScript 中使用 `systemPrompt: { type: "preset", preset: "claude_code", append: "..." }`，或在 Python 中使用 `system_prompt={"type": "preset", "preset": "claude_code", "append": "..."}`。CLAUDE.md 不会改变系统提示本身：SDK 会将其内容作为项目上下文注入到对话中。

## 使用场景与最佳实践

### 何时使用 CLAUDE.md

当某些指令应当应用于项目中的每个会话时，无论该会话使用哪个系统提示，都可以使用 CLAUDE.md：编码标准、常用命令、架构上下文以及团队约定。CLAUDE.md 会提交到你的仓库中，因此它能与所描述的代码保持同步。完整指南请参阅 [何时添加到 CLAUDE.md](/docs/en/memory#when-to-add-to-claude-md)。

当启用 `project` 设置源时会加载 CLAUDE.md 文件，而默认的 `query()` 选项会启用该设置源。如果你在 TypeScript 中显式设置了 `settingSources` 或在 Python 中显式设置了 `setting_sources`，请包含 `'project'` 以继续加载项目级 CLAUDE.md。

### 何时使用输出样式

输出样式适用于你希望跨 CLI 和 SDK 复用的角色设定，而无需更改应用程序代码。由于它们以文件形式存在于 `.claude/output-styles` 中，因此同一个角色设定既可以通过 CLI 中的 `/config` 使用，也可以通过任何加载了匹配设置源的 SDK 会话使用。

**最适用于：**

* 跨会话的持久性行为变更
* 团队共享的配置
* 专业化助手，如代码审查员、数据科学家或 DevOps 助手
* 需要版本管理的复杂提示修改

**示例：**

* 创建专用的 SQL 优化助手
* 构建以安全为重点的代码审查员
* 开发具有特定教学方法的教学助手

### 何时使用带追加的 `systemPrompt`

当 `claude_code` 预设已经适合你的产品，而你只需要叠加额外的指令时，请使用 `append`。你可以保留预设的工具指导、安全规则和编码约定，而无需重新实现它们。

**最适用于：**

* 添加特定的编码标准或偏好
* 自定义输出格式
* 添加特定领域的知识
* 修改回复的详细程度
* 在不丢失工具指令的情况下增强 Claude Code 的默认行为

### 何时使用自定义 `systemPrompt`

当你的智能体的界面、身份或权限模型与 Claude Code 的不同时，请使用自定义提示，如 [确定起点](#decide-on-a-starting-point) 中所述。你需要定义完整的指令集，包括你的智能体所需的任何工具指导和安全规则。

**最适用于：**

* 完全控制 Claude 的行为
* 专门的单会话任务
* 测试新的提示策略
* 不需要默认工具的情况
* 构建具有独特行为的专业化智能体

## 组合使用多种方法

这些方法可以组合使用。持久的输出样式或 CLAUDE.md 设定长期生效的行为，而 `append` 在其上叠加特定于会话的指令，且不会影响已保存的配置。

### 将输出样式与会话特定的附加内容结合

下面的示例假设已经激活了代码审查员(Code Reviewer)输出样式。`append` 块在角色人设之上叠加会话特定的关注领域,因此单个审查会话可以优先关注 OAuth 和令牌存储,而无需更改已保存的输出样式:

<CodeGroup>
  ```typescript TypeScript theme={null}
  import { query } from "@anthropic-ai/claude-agent-sdk";

  // Assuming "Code Reviewer" output style is active (via /config or settings)
  // Add session-specific focus areas
  const messages = [];

  for await (const message of query({
    prompt: "Review this authentication module",
    options: {
      systemPrompt: {
        type: "preset",
        preset: "claude_code",
        append: `
          For this review, prioritize:
          - OAuth 2.0 compliance
          - Token storage security
          - Session management
        `
      }
    }
  })) {
    messages.push(message);
  }
  ```

  ```python Python theme={null}
  from claude_agent_sdk import query, ClaudeAgentOptions

  # Assuming "Code Reviewer" output style is active (via /config or settings)
  # Add session-specific focus areas
  messages = []

  async for message in query(
      prompt="Review this authentication module",
      options=ClaudeAgentOptions(
          system_prompt={
              "type": "preset",
              "preset": "claude_code",
              "append": """
              For this review, prioritize:
              - OAuth 2.0 compliance
              - Token storage security
              - Session management
              """,
          }
      ),
  ):
      messages.append(message)
  ```
</CodeGroup>

## 另请参阅

* [输出样式](/docs/en/output-styles):为 CLI 创建、管理和共享输出样式,包括文件格式和存储位置
* [Claude 如何记住你的项目](/docs/en/memory):在 CLAUDE.md 中放什么、放在哪里,以及如何编写有效的项目指令
* [TypeScript SDK 参考](/docs/en/agent-sdk/typescript):完整的 `Options` 类型,包括 `systemPrompt`、`settingSources` 和 `settings`
* [Python SDK 参考](/docs/en/agent-sdk/python):完整的 `ClaudeAgentOptions` 类型,包括 `system_prompt` 和 `setting_sources`
* [设置](/docs/en/settings):`settings.json` 参考,包括输出样式和其他配置的存储位置

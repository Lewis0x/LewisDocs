---
title: Claude Code是如何工作的
source_id: claude-code/how-it-works
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/how-claude-code-works
owner: Anthropic
content_sha256: 4e80e099e79d8654eb401ae3716c034772714d56701ed5ab4577b64d197a948d
translation_of: claude-code/how-it-works
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/how-claude-code-works)

Content owner: Anthropic

> ## 文档索引
> 获取完整的文档索引，请访问：https://code.claude.com/docs/llms.txt
> 在进一步探索之前，请使用此文件来发现所有可用页面。

# Claude Code是如何工作的

> 了解智能体循环、内置工具，以及 Claude Code 如何与您的项目进行交互。

Claude Code 是一个在您终端中运行的智能体助手。虽然它擅长编程，但它可以帮助您完成任何可以从命令行执行的操作：编写文档、运行构建、搜索文件、研究主题等等。

本指南涵盖了核心架构、内置功能，以及 [高效工作的技巧](#work-effectively-with-claude-code)。有关分步演练，请参阅 [常见工作流](/docs/en/common-workflows)。有关技能、MCP 和钩子等扩展功能，请参阅 [扩展 Claude Code](/docs/en/features-overview)。

## 智能体循环

当您给 Claude 一个任务时，它会经历三个阶段：**收集上下文**、**采取行动**和**验证结果**。这些阶段相互交融。Claude 全程都在使用工具，无论是搜索文件以了解您的代码、进行编辑更改，还是运行测试来检查其工作。

<img src="https://mintcdn.com/claude-code/ikqp3_70mqIahteV/images/agentic-loop.svg?fit=max&auto=format&n=ikqp3_70mqIahteV&q=85&s=4a30fb7ce2815012a9f27c955e2c6bb0" alt="智能体循环图：您的提示词引导 Claude 收集上下文、采取行动、验证结果，并重复此过程直到任务完成。您可以随时中断。" width="720" height="280" data-path="images/agentic-loop.svg" />

该循环会根据您的请求进行自适应调整。关于代码库的问题可能只需要收集上下文。修复 Bug 会反复循环这三个阶段。重构可能涉及大量的验证工作。Claude 根据从上一步学到的内容来决定下一步需要做什么，将数十个动作串联在一起，并在此过程中不断修正方向。

您也是这个循环的一部分。您可以随时打断，将 Claude 引导向不同的方向，提供额外的上下文，或者要求它尝试不同的方法。Claude 在自主工作的同时，也会对您的输入保持响应。

智能体循环由两个组件驱动：用于推理的 [模型](#models) 和用于行动的 [工具](#tools)。Claude Code 充当了围绕 Claude 的**智能体外壳**：它提供了将语言模型转变为强大编程智能体所需的工具、上下文管理和执行环境。

### 模型

Claude Code 使用 Claude 模型来理解您的代码并推理任务。Claude 能够阅读任何语言的代码，理解各个组件如何连接，并找出实现目标所需的更改。对于复杂任务，它会将工作分解为多个步骤，执行这些步骤，并根据所学到的内容进行调整。

[提供具有不同权衡的多种模型](/docs/en/model-config)。Sonnet 能够很好地处理大多数编程任务。Opus 则为复杂的架构决策提供了更强大的推理能力。在会话中使用 `/model` 进行切换，或者从 `claude --model <name>` 开始。

当本指南提到“Claude 选择”或“Claude 决定”时，指的都是模型在进行推理。

### 工具

工具赋予了 Claude Code 智能体能力。没有工具，Claude 只能用文本回应。有了工具，Claude 就能采取行动：阅读你的代码、编辑文件、运行命令、搜索网络以及与外部服务交互。每次使用工具都会返回信息并反馈到循环中，为 Claude 的下一步决策提供依据。

内置工具通常分为五大类，每一类代表了不同的代理能力。

| 类别              | Claude 能做什么                                                                                                                                            |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **文件操作**   | 读取文件、编辑代码、创建新文件、重命名和重新组织                                                                                                |
| **搜索**            | 按模式查找文件、使用正则表达式搜索内容、探索代码库                                                                                           |
| **执行**         | 运行 shell 命令、启动服务器、运行测试、使用 git                                                                                                         |
| **Web**               | 搜索网络、获取文档、查找错误信息                                                                                                   |
| **代码智能** | 查看编辑后的类型错误和警告、跳转到定义、查找引用（需要 [code intelligence plugins](/docs/en/discover-plugins#code-intelligence)） |

这些是主要功能。Claude 还具有用于生成子代理、向你提问以及其他编排任务的工具。完整列表请参见 [Tools available to Claude](/docs/en/tools-reference)。

Claude 会根据你的提示词以及它在处理过程中学到的内容来选择使用哪些工具。当你说“修复失败的测试”时，Claude 可能会：

1. 运行测试套件以查看失败原因
2. 读取错误输出
3. 搜索相关的源代码文件
4. 读取这些文件以理解代码
5. 编辑文件以修复问题
6. 再次运行测试进行验证

每次使用工具都会为 Claude 提供新的信息，为下一步行动提供依据。这就是实际运行中的智能体循环。

**扩展基础功能：** 内置工具是基础。你可以使用 [skills](/docs/en/skills) 扩展 Claude 的知识，使用 [MCP](/docs/en/mcp) 连接外部服务，使用 [hooks](/docs/en/hooks) 自动化工作流，以及将任务卸载给 [subagents](/docs/en/sub-agents)。这些扩展在核心智能体循环之上形成了一层。关于如何选择满足你需求的扩展，请参见 [Extend Claude Code](/docs/en/features-overview)。

## Claude 可以访问的内容

本指南主要关注终端。 Claude Code 也可以在 [VS Code](/docs/en/vs-code)、[JetBrains IDEs](/docs/en/jetbrains)以及其他环境中运行。

当你在某个目录中运行 `claude` 时，Claude Code 将获得以下权限：

* **你的项目。** 你的目录和子目录中的文件，以及在获得你许可的情况下其他位置的文件。
* **你的终端。** 你可以运行的任何命令：构建工具、git、包管理器、系统实用程序、脚本。只要你能从命令行执行的操作，Claude 也能做到。
* **你的 git 状态。** 当前分支、未提交的更改以及最近的提交历史。
* **你的 [CLAUDE.md](/docs/en/memory)。** 一个 Markdown 文件，你在其中存储 Claude 在每次会话中应了解的项目特定说明、约定和上下文。
* **[自动记忆](/docs/en/memory#auto-memory)。** Claude 在你工作时自动保存的经验，例如项目模式和个人偏好。MEMORY.md 的前 200 行或 25KB（以先到者为准）会在每次会话开始时加载。
* **你配置的扩展。** 用于外部服务的 [MCP 服务器](/docs/en/mcp)，用于工作流的 [技能](/docs/en/skills)，用于委托工作的 [子代理](/docs/en/sub-agents)，以及用于浏览器交互的 [Chrome 中的 Claude](/docs/en/chrome)。

由于 Claude 可以查看你的整个项目，因此它可以跨项目工作。当你要求 Claude“修复身份验证错误”时，它会搜索相关文件，阅读多个文件以了解上下文，在它们之间进行协调一致的编辑，运行测试以验证修复，并在你要求时提交更改。这不同于只能看到当前文件的内联代码助手。

## 环境与界面

无论你在哪里使用 Claude Code，上述描述的代理循环、工具和功能都是相同的。改变的是代码执行的位置以及你与它交互的方式。

### 执行环境

Claude Code运行在三种环境中，每种环境在代码执行位置方面都有不同的权衡。

| 环境        | 代码运行位置                         | 使用场景                                                   |
| ------------------ | --------------------------------------- | ---------------------------------------------------------- |
| **本地**          | 您的机器                            | 默认。完全访问您的文件、工具和环境 |
| **云端**          | Anthropic 管理的虚拟机                   | 卸载任务，处理不在本地的代码库        |
| **远程控制** | 你的机器，通过浏览器控制 | 在执行时使用 Web UI，而你的文件保留在本地   |

### 接口

您可以访问 Claude Code，通过终端、[桌面应用](/docs/en/desktop)、[IDE扩展](/docs/en/vs-code)、[claude.ai/code](https://claude.ai/code)、[远程控制](/docs/en/remote-control)、[Slack](/docs/en/slack)，以及[CI/CD流水线](/docs/en/github-actions)。该界面 决定了您查看并与 Claude 交互的方式，但是 底层的智能体循环是相同的。参见 [使用 Claude Code 在各处](/docs/en/overview#use-claude-code-everywhere) 以获取完整列表。

## 使用会话

Claude Code 在您工作时将对话保存在本地。每条消息、工具使用情况和结果都会写入 `~/.claude/projects/` 下的纯文本 JSONL 文件中，这使得 [回退](#undo-changes-with-checkpoints)、[恢复和分支](#resume-or-fork-sessions) 会话成为可能。在 Claude 进行代码更改之前，它还会对受影响的文件进行快照，以便您可以在需要时恢复。关于路径、保留期和 如何清除此数据，请参见 [application data in `~/.claude`](/docs/en/claude-directory#application-data)。

**会话是独立的。**每个新会话都以全新的上下文窗口开始，不包含先前会话的对话历史。Claude 可以使用 [自动记忆](/docs/en/memory#auto-memory) 跨会话保留学习成果，并且您可以在 [CLAUDE.md](/docs/en/memory) 中添加您自己的持久指令。

### 跨分支工作

每个 Claude Code 对话都是与当前目录绑定的会话。`/resume` 选择器默认显示当前工作树中的会话，并提供了键盘快捷键，可将列表范围扩大到其他工作树或项目。有关选择器快捷键的完整列表以及名称解析的工作原理，请参见 [管理会话](/docs/en/sessions#use-the-session-picker)。

Claude 会读取你当前分支的文件。当你切换分支时，Claude 会读取新分支的文件，但你的对话历史记录保持不变。即使在切换分支后，Claude 也会记住你讨论过的内容。

由于会话与目录绑定，你可以通过使用 [git worktrees](/docs/en/worktrees) 来运行并行的 Claude 会话，它可为各个分支创建独立的目录。

### 恢复或分叉会话

使用 `claude --continue` 或 `claude --resume` 恢复会话会在相同的会话 ID 下重新打开它，并将新消息追加到现有对话中。使用 `--fork-session` 或 `/branch` 进行分叉会将历史记录复制到新的会话 ID 中，而原会话保持不变。

<img src="https://mintcdn.com/claude-code/ikqp3_70mqIahteV/images/session-continuity.svg?fit=max&auto=format&n=ikqp3_70mqIahteV&q=85&s=04ed0984a58e4127e05b3640265241a3" alt="会话连续性示意图：恢复将继续同一会话，分叉将创建一个带有新 ID 的新分支。" width="560" height="280" data-path="images/session-continuity.svg" />

有关恢复标志、`/resume` 选择器、命名，以及当同一会话在两个终端中打开时会发生什么，请参见 [管理会话](/docs/en/sessions)。

### 上下文窗口

Claude 的上下文窗口容纳了你的对话历史、文件内容、命令输出、[CLAUDE.md](/docs/en/memory)、[自动记忆](/docs/en/memory#auto-memory)、已加载的技能以及系统指令。随着你的工作，上下文会被逐渐填满。Claude 会自动压缩，但对话早期的指令可能会丢失。请将持久性规则放在 CLAUDE.md 中，并运行 `/context` 来查看是什么占用了空间。

有关加载内容和加载时间的交互式演练，请参见 [探索上下文窗口](/docs/en/context-window)。

#### 当上下文填满时

当你接近限制时，Claude Code 会自动管理上下文。它会首先清除较早的工具输出，然后根据需要对对话进行总结。你的请求和关键代码片段会被保留；但对话早期的详细指令可能会丢失。请将持久性规则放在 CLAUDE.md 中，而不是依赖于对话历史。

要控制在压缩期间保留的内容，可以在 CLAUDE.md 中添加一个“压缩指令”部分，或者运行带有关注点（例如 `/compact`）的 `/compact focus on the API changes`。

如果单个文件或工具输出过大，以至于每次总结后上下文都会立即被重新填满，Claude Code 会在几次尝试后停止自动压缩，并显示错误，而不是陷入死循环。有关恢复步骤，请参见 [自动压缩因系统颠簸错误而停止](/docs/en/troubleshooting#auto-compaction-stops-with-a-thrashing-error)。

运行 `/context` 来查看是什么占用了空间。MCP 工具定义默认会进行延迟处理，并通过 [工具搜索](/docs/en/mcp#scale-with-mcp-tool-search) 按需加载，因此在 Claude 使用特定工具之前，只有工具名称会消耗上下文。运行 `/mcp` 来检查每个服务器的消耗情况。

#### 使用技能和子代理管理上下文

除了压缩之外，您还可以使用其他功能来控制加载到上下文中的内容。

[技能](/docs/en/skills) 按需加载。Claude 在会话开始时会看到技能描述，但只有在技能被使用时才会加载完整内容。对于手动调用的技能，请设置 `disable-model-invocation: true` 以在需要之前将描述排除在上下文之外。对于非您编写的技能，请在设置中使用 [`skillOverrides`](/docs/en/skills#override-skill-visibility-from-settings) 执行相同的操作。

[子代理](/docs/en/sub-agents) 获得自己全新的上下文，与您的主对话完全分离。它们的工作不会使您的上下文膨胀。完成后，它们会返回一个摘要。这种隔离性正是子代理有助于处理长会话的原因。

有关各项功能的开销，请参见 [上下文开销](/docs/en/features-overview#understand-context-costs)，有关管理上下文的提示，请参见 [减少令牌使用](/docs/en/costs#reduce-token-usage)。

## 使用检查点和权限确保安全

Claude 有两种安全机制：检查点允许您撤销文件更改，而权限控制 Claude 可以在不询问的情况下执行什么操作。

### 使用检查点撤销更改

**文件编辑是可逆的。** 在 Claude 编辑文件之前，它会对当前内容进行快照。如果出现问题，请按两次 `Esc` 回溯到之前的状态，或者要求 Claude 撤销。

检查点独立于 git，并且在您恢复对话时仍然可用。它们仅涵盖文件更改，并且还原操作 [跳过符号链接和硬链接文件](/docs/en/checkpointing#symlinked-and-hard-linked-paths-not-restored)。影响远程系统（数据库、API、部署）的操作无法被检查点记录，这就是为什么 Claude 在运行具有外部副作用的命令之前会进行询问。

### 控制 Claude 能做什么

按下 `Shift+Tab` 循环切换权限模式：

* **手动**: Claude 在编辑文件和执行 shell 命令前会先询问
* **接受编辑**: Claude 无需询问即可编辑文件并运行常见的文件系统命令（如 `mkdir` 和 `mv`），但仍会询问其他命令
* **计划**: Claude 会进行探索并提出计划，而不会编辑您的源文件
* **自动**: Claude 会通过后台安全检查来评估所有操作

您也可以在 `.claude/settings.json` 中允许特定命令，这样 Claude 就不会每次都询问。这对于受信任的命令（如 `npm test` 或 `git status`）非常有用。设置的范围可以从组织级别的策略缩小到个人偏好。详情请参见 [权限](/docs/en/permissions)。

***

## 高效使用 Claude Code

这些技巧能帮您从 Claude Code 获得更好的结果。

### 向 Claude Code 寻求帮助

Claude Code 可以教您如何使用它。提出诸如“我该如何设置钩子？”或“构建我的 CLAUDE.md 的最佳方式是什么？”等问题，Claude 会进行解释。

内置命令也会引导您完成设置：

* `/init` 引导您为您的项目创建 CLAUDE.md
* `/doctor` 会运行设置检查，诊断安装和配置问题并进行修复

### 这是一次对话

Claude Code 是对话式的。您不需要完美的提示词。从您的需求开始，然后逐步细化：

```text theme={null}
Fix the login bug
```

\[Claude 进行调查，尝试某些操作]

```text theme={null}
That's not quite right. The issue is in the session handling.
```

\[Claude 调整方法]

当第一次尝试不正确时，您不必从头开始。您可以不断迭代。

#### 打断并引导

你可以随时重新引导 Claude，而无需等待当前轮次结束或重新开始：

* **按下 `Esc`** 立即停止 Claude。正在运行的工具调用将被取消，Claude 会等待你的下一条指令。
* **输入修改内容并按下 `Enter`** 发送，这不会停止正在运行的工具。Claude 会在当前操作完成后立即读取该内容，并在决定下一步操作之前进行调整。

### 开头要具体

你最初的提示词越精确，需要的修改就越少。引用具体的文件，提及限制条件，并指出示例模式。

```text theme={null}
The checkout flow is broken for users with expired cards.
Check src/payments/ for the issue, especially token refresh.
Write a failing test first, then fix it.
```

模糊的提示词也有效，但你会花更多时间来引导。像上面这样具体的提示词往往在第一次尝试时就能成功。

### 给Claude提供可供验证的内容

当Claude能够检查自己的工作时，它会表现得更好。包含测试用例，粘贴预期UI的截图，或者定义你想要的输出。

```text theme={null}
Implement validateEmail. Test cases: 'user@example.com' → true,
'invalid' → false, 'user@.com' → false. Run the tests after.
```

对于视觉相关工作，粘贴设计的截图，并让Claude将其实现与设计进行对比。

### 在实现之前先探索

对于复杂问题，将研究与编码分开。首先使用计划模式（两次 `Shift+Tab`）来分析代码库：

```text theme={null}
Read src/auth/ and understand how we handle sessions.
Then create a plan for adding OAuth support.
```

审查该计划，通过对话对其进行完善，然后让Claude去实现。这种两阶段的方法比直接跳到代码能产生更好的结果。

### 委派，而不是指挥

想象一下把任务委托给一位有能力的同事。提供背景和方向，然后相信Claude能搞定细节：

```text theme={null}
The checkout flow is broken for users with expired cards.
The relevant code is in src/payments/. Can you investigate and fix it?
```

你不需要指定要读取哪些文件或运行什么命令。Claude会自己弄清楚。

## 下一步

<CardGroup cols={2}>
  <Card title="扩展功能" icon="puzzle-piece" href="/docs/en/features-overview">
    添加技能、MCP连接和自定义命令
  </Card>

  <Card title="常见工作流" icon="graduation-cap" href="/docs/en/common-workflows">
    典型任务的分步指南
  </Card>
</CardGroup>

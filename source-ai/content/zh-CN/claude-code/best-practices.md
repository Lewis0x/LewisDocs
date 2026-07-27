---
title: Claude Code 的最佳实践
source_id: claude-code/best-practices
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/best-practices
owner: Anthropic
content_sha256: 2c42e4283aea2fb6318077c884259cbe360c3d8995fd0cb9469ebc6de0df66f2
translation_of: claude-code/best-practices
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/best-practices)

Content owner: Anthropic

> ## 文档索引
> 获取完整文档索引请访问：https://code.claude.com/docs/llms.txt
> 在深入探索之前，请使用此文件发现所有可用页面。

# Claude Code 的最佳实践

> 充分利用 Claude Code 的技巧和模式，从配置环境到跨并行会话进行扩展。

Claude Code 是一个自主的编程环境。与回答问题后就等待的聊天机器人不同，Claude Code 可以读取您的文件、运行命令、进行更改，并在您观看、重定向或完全离开时自主解决问题。

这改变了您的工作方式。您不必自己编写代码并要求 Claude 审查，而是描述您想要什么，然后由 Claude 找出如何构建它的方法。Claude 负责探索、计划和实施。

但这种自主性仍然存在学习曲线。Claude 在某些您需要理解的约束下工作。

本指南涵盖了在 Anthropic 内部团队以及在各种代码库、语言和环境中使用 Claude Code 的工程师中证明有效的模式。有关底层自主循环的工作原理，请参见 [Claude Code 的工作原理](/docs/en/how-claude-code-works)。

***

大多数最佳实践基于一个约束条件：Claude 的上下文窗口很快就会被填满，并且随着填满性能会下降。

Claude 的上下文窗口保存着您的整个对话，包括每条消息、Claude 读取的每个文件以及每个命令输出。但是，这会很快被填满。单次调试会话或代码库探索可能会生成并消耗数万个 token。

这很重要，因为随着上下文的填充，LLM 的性能会下降。当上下文窗口快满时，Claude 可能会开始“忘记”之前的指令或犯更多错误。上下文窗口是需要管理的最重要资源。要查看会话在实践中是如何填满的，请[观看互动指南](/docs/en/context-window)，了解启动时加载的内容以及每次读取文件的成本。使用 [自定义状态栏](/docs/en/statusline) 持续跟踪上下文使用情况，并参阅 [减少 token 使用量](/docs/en/costs#reduce-token-usage) 了解减少 token 使用的策略。

***

## 给 Claude 一种验证其工作的方法

<Tip>
  给 Claude 一个它可以运行的检查：测试、构建、可供比较的截图。这决定了你是一场需要全程盯着的会话，还是可以放手不管的会话。
</Tip>

Claude 会在工作看起来完成时停止。如果没有它可以运行的检查，“看起来完成了”就是唯一可用的信号，而你就成了验证闭环：每一个错误都在等你去发现。给 Claude 一些能产生通过或失败结果的东西，这个闭环就会自行闭合。Claude 完成工作，运行检查，读取结果，并不断迭代直到检查通过。

检查可以是任何能返回 Claude 可在对话中读取的信号的事物：测试套件、构建退出代码、linter、将输出与固件进行差异比对的脚本，或者与设计图进行比较的 [浏览器截图](/docs/en/chrome)。

| 策略                              | 之前                                                  | 之后                                                                                                                                                                                                   |
| ------------------------------------- | ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **提供验证标准**     | *"实现一个验证电子邮件地址的函数"* | *"编写一个 validateEmail 函数。示例测试用例： [user@example.com](mailto:user@example.com) 为真，invalid 为假，[user@.com](mailto:user@.com) 为假。实现后运行测试"* |
| **通过视觉验证 UI 变更**        | *"让仪表板看起来更好"*                      | *"\[粘贴截图] 实现这个设计。对结果进行截图并将其与原图进行比较。列出差异并修复它们"*                                                            |
| **解决根本原因，而非表面症状** | *"构建失败"*                                | *"构建失败并出现此错误：\[粘贴错误]。修复它并验证构建是否成功。解决根本原因，不要抑制该错误"*                                                             |

一旦有了检查机制，就可以决定它在多大程度上限制停止：

* **在单个提示词中**：要求 Claude 在同一条消息中运行检查并进行迭代，如上表所示。
* **在整个会话中**：将检查设置为 [`/goal` 条件](/docs/en/goal)。一个单独的评估器会在每一轮后重新检查它，并且 Claude 会一直工作直到条件满足。
* **作为确定性门禁**：一个 [Stop hook](/docs/en/hooks#stop) 将你的检查作为脚本运行，并阻止这一轮结束，直到它通过。Claude Code 会在连续拦截 8 次后覆盖该 hook 并结束这一轮。
* **通过第二意见**：一个 [验证子代理](/docs/en/sub-agents) 或一个 [动态工作流](/docs/en/workflows) 会检查其自身的发现，由一个全新的模型尝试反驳结果，这样执行工作的代理就不会是给它打分的代理。

每一个步骤都是以设置换取注意力。提示词版本适用于当今的任何任务。而 `/goal` 和 Stop hook 版本则是让无人值守的运行在没有你的情况下正确完成的关键。

让 Claude 展示证据，而不是仅仅断言成功：测试输出、它运行的命令及返回结果，或者结果截图。审查证据比你自己重新运行验证要快，而且这对你没有全程盯着的会话同样有效。

***

## 先探索，再规划，最后编码

<Tip>
  将研究和规划与实现分开，以避免解决错误的问题。
</Tip>

让 Claude 直接跳到编码可能会产生解决错误问题的代码。使用 [计划模式](/docs/en/permission-modes#analyze-before-you-edit-with-plan-mode) 将探索与执行分开。

推荐的工作流程有四个阶段：

<Steps>
  <Step title="探索">
    进入计划模式。Claude 读取文件并回答问题，不进行任何更改。

    ```txt claude (plan mode) theme={null}
    阅读 /src/auth 并理解我们如何处理会话和登录。
    也看看我们如何管理密钥的环境变量。
    ```
  </Step>

  <Step title="规划">
    要求 Claude 创建详细的实施计划。

    ```txt claude (plan mode) theme={null}
    我想添加 Google OAuth。需要更改哪些文件？
    会话流程是什么？创建一个计划。
    ```

    按 `Ctrl+G` 在文本编辑器中打开计划，在 Claude 继续之前进行直接编辑。
  </Step>

  <Step title="实施">
    退出计划模式，让 Claude 编码，并根据其计划进行验证。

    ```txt claude (default mode) theme={null}
    根据你的计划实施 OAuth 流程。为
    回调处理器编写测试，运行测试套件并修复任何故障。
    ```
  </Step>

  <Step title="提交">
    要求 Claude 使用描述性消息提交并创建一个 PR。

    ```txt claude (default mode) theme={null}
    使用描述性消息提交并打开一个 PR
    ```
  </Step>
</Steps>

<Callout>
  计划模式很有用，但也增加了开销。

  对于范围明确且修复较小的任务（如修复拼写错误、添加日志行或重命名变量），直接要求 Claude 完成。

  当你对方法不确定、当更改涉及多个文件、或者当你不熟悉要修改的代码时，规划最有用。如果你能用一句话描述差异，就跳过规划。
</Callout>

***

## 在你的提示词中提供具体的上下文

<Tip>
  你的指令越精确，需要的修正就越少。
</Tip>

Claude可以推断意图，但它无法读取你的心思。引用特定文件，提及约束条件，并指向示例模式。

| 策略                                                                                         | 之前                                               | 之后                                                                                                                                                                                                                                                                                                                                                            |
| ------------------------------------------------------------------------------------------------ | ---------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **界定任务范围。** 指定哪个文件、什么场景以及测试偏好。                  | *"为 foo.py 添加测试"*                             | *"为 foo.py 编写测试，覆盖用户登出的边缘情况。避免使用模拟对象。"*                                                                                                                                                                                                                                                                    |
| **指向来源。** 引导Claude找到能回答问题的来源。                    | *"为什么 ExecutionFactory 的 API 这么奇怪？"* | *"查看 ExecutionFactory 的 git 历史记录，总结它的 API 是怎么变成现在这样的"*                                                                                                                                                                                                                                                                             |
| **参考现有模式。** 向Claude指出你代码库中的模式。                      | *"添加一个日历小部件"*                            | *"查看首页上现有小部件的实现方式，以了解相关模式。HotDogWidget.php 是一个很好的例子。按照该模式实现一个新的日历小部件，允许用户选择月份并向前/向后翻页来选择年份。从头开始构建，不使用代码库中已用库以外的任何库。"* |
| **描述症状。** 提供症状、可能的位置以及“修复后”的样子。 | *"修复登录bug"*                                | *"用户报告称会话超时后登录失败。检查 src/auth/ 中的认证流程，特别是 token 刷新。编写一个能复现该问题的失败测试，然后修复它"*                                                                                                                                                                                 |

模糊的提示词在你进行探索且有余力进行纠偏时可能会很有用。像 `"what would you improve in this file?"` 这样的提示词能揭示出你原本想不到要问的事情。

### 提供丰富内容

<Tip>
  使用 `@` 来引用文件、粘贴截图/图片，或直接通过管道传输数据。
</Tip>

您可以通过以下几种方式向 Claude 提供丰富的数据：

* **使用 `@` 引用文件**，而不是描述代码所在的位置。Claude 会在响应前读取文件。
* **直接粘贴图片**。复制/粘贴或将图片拖放到提示词中。
* **提供 URL** 以指向文档和 API 参考。使用 `/permissions` 将常用域名加入白名单。
* **通过管道输入数据**，通过运行 `cat error.log | claude` 直接发送文件内容。
* **让 Claude 获取所需内容**。告诉 Claude 使用 Bash 命令、MCP 工具或读取文件来自行拉取上下文。

***

## 配置您的环境

几个设置步骤能让 Claude Code 在您的所有会话中显著提高效率。有关扩展功能的全面概述及各自的使用时机，请参阅 [扩展 Claude Code](/docs/en/features-overview)。

### 编写高效的 CLAUDE.md

<Tip>
  运行 `/init` 根据您当前的项目结构生成一个初始的 CLAUDE.md 文件，然后随着时间的推移进行完善。
</Tip>

CLAUDE.md 是一个特殊的文件，Claude 会在每次对话开始时读取它。请包含 Bash 命令、代码风格和工作流规则。这为 Claude 提供了仅从代码中无法推断出的持久上下文。

`/init` 命令会分析您的代码库以检测构建系统、测试框架和代码模式，为您提供一个坚实的基础来进行完善。

CLAUDE.md 文件没有强制要求的格式，但请保持简明且易于人类阅读。例如：

```markdown CLAUDE.md theme={null}
# Code style

- Use ES modules (import/export) syntax, not CommonJS (require)
- Destructure imports when possible (eg. import { foo } from 'bar')

# Workflow

- Be sure to typecheck when you're done making a series of code changes
- Prefer running single tests, and not the whole test suite, for performance
```

运行 `/context` 以确认 Claude 已加载该文件。CLAUDE.md 会在每次会话时加载，因此只需包含广泛适用的内容。对于仅偶尔相关的领域知识或工作流，请改用 [skills](/docs/en/skills)。Claude 会按需加载它们，而不会使每次对话变得臃肿。

保持简明。对于每一行，请问问自己：*“删掉这一行会导致 Claude 犯错吗？”* 如果不会，就删掉它。臃肿的 CLAUDE.md 文件会导致 Claude 忽略您的实际指令！

| ✅ 包含                                                | ❌ 排除                                              |
| ---------------------------------------------------- | -------------------------------------------------- |
| Claude 无法猜到的 Bash 命令                          | Claude 通过阅读代码就能弄清楚的事情                 |
| 与默认设置不同的代码风格规则                         | Claude 已经知道的标准语言约定                       |
| 测试说明和首选的测试运行器                            | 详细的 API 文档（改为提供文档链接）                   |
| 仓库规范（分支命名、PR 约定）                         | 频繁变更的信息                                       |
| 针对您项目的特定架构决策                              | 冗长的解释或教程                                     |
| 开发者环境特性（所需的环境变量）                      | 对代码库的逐文件描述                                 |
| 常见陷阱或不明显的行为                                | 显而易见的做法，如“编写干净的代码”                      |

如果 Claude 尽管有规则限制但依然不断做您不希望的事情，那么文件可能太长导致规则被忽略了。如果 Claude 询问您的问题已经在 CLAUDE.md 中有了答案，那么措辞可能含糊不清。请像对待代码一样对待 CLAUDE.md：在出错时进行审查，定期修剪，并通过观察 Claude 的行为是否确实发生了改变来测试修改效果。

您可以通过添加强调（例如，“重要”或“必须”）来调整指令以提高遵守度。将 CLAUDE.md 提交到 git，以便您的团队可以共同协作。该文件的价值会随着时间的推移而不断积累。

CLAUDE.md 文件可以使用 `@path/to/import` 语法导入其他文件：

```markdown CLAUDE.md theme={null}
See @README.md for project overview and @package.json for available npm commands.

# Additional Instructions

- Git workflow: @docs/git-instructions.md
- Personal overrides: @~/.claude/my-project-instructions.md
```

您可以将 CLAUDE.md 文件放置在多个位置：

* **主文件夹 (`~/.claude/CLAUDE.md`)**：应用于所有 Claude 会话
* **项目根目录 (`./CLAUDE.md`)**：提交到 git 以与您的团队共享
* **项目根目录 (`./CLAUDE.local.md`)**：个人项目特定的笔记；将此文件添加到您的 `.gitignore` 中，这样它就不会与您的团队共享
* **父目录**：适用于 monorepos，其中 `root/CLAUDE.md` 和 `root/foo/CLAUDE.md` 都会被自动引入
* **子目录**：当 Claude 读取这些目录中的文件时，会按需引入子级 CLAUDE.md 文件

### 配置权限

<Tip>
  使用 [自动模式](/docs/en/permission-modes#eliminate-prompts-with-auto-mode) 让分类器处理批准，使用 `/permissions` 将特定命令添加到白名单，或使用 `/sandbox` 进行操作系统级隔离。每种方法都减少了中断，同时让您保持控制。
</Tip>

默认情况下，Claude Code 会对可能修改您系统的操作请求权限：写入文件、Bash 命令、MCP 工具等。这很安全，但很繁琐。在第十次批准之后，您其实已经不再审查了，只是在点击通过。有三种方法可以减少这些中断：

* **自动模式**：一个单独的分类器模型审查命令，并仅阻止看起来有风险的内容：范围扩大、未知的基础设施或受敌对内容驱动的操作。最适合您信任任务的总体方向但不想点击通过每一个步骤的情况
* **权限白名单**：允许您知道是安全的特定工具，例如 `npm run lint` 或 `git commit`
* **沙盒机制**：启用操作系统级隔离，限制文件系统和网络访问，允许 Claude 在定义的边界内更自由地工作

阅读更多关于 [权限模式](/docs/en/permission-modes)、[权限规则](/docs/en/permissions) 和 [沙盒机制](/docs/en/sandboxing) 的信息。

### 使用 CLI 工具

<Tip>
  告诉 Claude Code 在与外部服务交互时使用 CLI 工具，例如 `gh`、`aws`、`gcloud` 和 `sentry-cli`。
</Tip>

CLI 工具是与外部服务交互的最上下文高效的方式。如果您使用 GitHub，请安装 `gh` CLI。Claude 知道如何使用它来创建 issue、发起 pull request 和阅读评论。如果没有 `gh`，Claude 仍然可以使用 GitHub API，但未经身份验证的请求经常会触发速率限制。

Claude 在学习它尚未掌握的 CLI 工具方面也非常出色。尝试类似 `Use 'foo-cli-tool --help' to learn about foo tool, then use it to solve A, B, C.` 的提示

### 连接 MCP 服务器

<Tip>
  运行 `claude mcp add` 以连接外部工具，如 Notion、Figma 或您的数据库。
</Tip>

借助 [MCP 服务器](/docs/en/mcp)，您可以要求 Claude 根据 issue 追踪器实现功能、查询数据库、分析监控数据、集成 Figma 设计以及自动化工作流。

### 设置钩子

<Tip>
  将钩子用于那些必须每次执行且毫无例外的操作。
</Tip>

[Hooks](/docs/en/hooks-guide) 会在 Claude 工作流的特定节点自动运行脚本。与作为建议的 CLAUDE.md 指令不同，钩子是确定性的，并保证操作会被执行。

Claude 可以为您编写钩子。尝试像 *“编写一个在每次文件编辑后运行 eslint 的钩子”* 或 *“编写一个阻止写入 migrations 文件夹的钩子”* 这样的提示。直接编辑 `.claude/settings.json` 以手动配置钩子，并运行 `/hooks` 来浏览已配置的内容。

### 创建技能

<Tip>
  在 `SKILL.md` 中创建 `.claude/skills/` 文件，为 Claude 提供领域知识和可复用的工作流。
</Tip>

[Skills](/docs/en/skills) 使用特定于你的项目、团队或领域的信息来扩展 Claude 的知识。Claude 会在相关时自动应用它们，或者你也可以使用 `/skill-name` 直接调用它们。

通过向 `SKILL.md` 添加一个包含 `.claude/skills/` 的目录来创建技能：

```markdown .claude/skills/api-conventions/SKILL.md theme={null}
---
name: api-conventions
description: REST API design conventions for our services
---
# API Conventions

- Use kebab-case for URL paths
- Use camelCase for JSON properties
- Always include pagination for list endpoints
- Version APIs in the URL path (/v1/, /v2/)
```

技能还可以定义你可直接调用的可重复工作流：

```markdown .claude/skills/fix-issue/SKILL.md theme={null}
---
name: fix-issue
description: Fix a GitHub issue
disable-model-invocation: true
---
Analyze and fix the GitHub issue: $ARGUMENTS.

1. Use `gh issue view` to get the issue details
2. Understand the problem described in the issue
3. Search the codebase for relevant files
4. Implement the necessary changes to fix the issue
5. Write and run tests to verify the fix
6. Ensure code passes linting and type checking
7. Create a descriptive commit message
8. Push and create a PR
```

运行 `/fix-issue 1234` 来调用它。对于希望手动触发且带有副作用的工作流，请使用 `disable-model-invocation: true`。

### 创建自定义子代理

<Tip>
  在 `.claude/agents/` 中定义专门的助手，让 Claude 可以委派隔离的任务。
</Tip>

[Subagents](/docs/en/sub-agents) 在它们各自的上下文中运行，并拥有各自的一组允许工具。它们对于需要读取大量文件或需要专门关注而不弄乱主对话的任务非常有用。

```markdown .claude/agents/security-reviewer.md theme={null}
---
name: security-reviewer
description: Reviews code for security vulnerabilities
tools: Read, Grep, Glob, Bash
model: opus
---
You are a senior security engineer. Review code for:
- Injection vulnerabilities (SQL, XSS, command injection)
- Authentication and authorization flaws
- Secrets or credentials in code
- Insecure data handling

Provide specific line references and suggested fixes.
```

明确告诉 Claude 使用子代理：*“使用子代理来审查此代码的安全问题。”*

### 安装插件

<Tip>
  运行 `/plugin` 浏览市场。插件无需配置即可添加技能、工具和集成。
</Tip>

[Plugins](/docs/en/plugins) 将技能、钩子、子代理和 MCP 服务器捆绑成一个来自社区和 Anthropic 的可安装单元。如果你使用强类型语言，请安装 [code intelligence plugin](/docs/en/discover-plugins#code-intelligence)，以便 Claude 进行精确的符号导航并在编辑后自动检测错误。

有关在技能、子代理、钩子和 MCP 之间进行选择的指导，请参见 [Extend Claude Code](/docs/en/features-overview#match-features-to-your-goal)。

***

## 有效沟通

你与 Claude Code 沟通的方式会极大影响结果的质量。

### 提问代码库问题

<Tip>
  问 Claude 你会问资深工程师的问题。
</Tip>

当接手一个新代码库时，使用 Claude Code 进行学习和探索。你可以问 Claude 你会问另一位工程师的同类问题：

* 日志记录是如何工作的？
* 如何创建一个新的 API 端点？
* `async move { ... }` 在 `foo.rs` 的第 134 行做什么？
* `CustomerOnboardingFlowImpl` 处理了哪些边缘情况？
* 为什么这段代码在第 333 行调用的是 `foo()` 而不是 `bar()`？

以这种方式使用 Claude Code 是一种有效的入职工作流，可提高上手速度并减轻其他工程师的负担。无需特殊提示：直接提问即可。

### 让 Claude 面试你

<Tip>
  对于较大的功能，先让 Claude 面试你。从一个最简的提示词开始，并要求 Claude 使用 `AskUserQuestion` 工具对你进行面试。
</Tip>

Claude 会询问你尚未考虑过的事情，包括技术实现、UI/UX、边缘情况和权衡。在发送提示词之前，将 `[brief description]` 替换为你的功能。

```text theme={null}
I want to build [brief description]. Interview me in detail using the AskUserQuestion tool.

Ask about technical implementation, UI/UX, edge cases, concerns, and tradeoffs. Don't ask obvious questions, dig into the hard parts I might not have considered.

Keep interviewing until we've covered everything, then write a complete spec to SPEC.md.
```

一旦规范完成，开启一个全新的会话来执行它。新会话拥有完全专注于实现的干净上下文，并且你有一份书面规范可供参考。

最有用的规范是自包含的：它们指明涉及的文件和接口，说明哪些不在范围内，并以一个证明该功能有效的端到端验证步骤结束。花在使规范精确上的时间比花在看实现上的时间回报更高。

***

## 管理你的会话

对话是持久且可逆的。好好利用这一点！

### 尽早且频繁地进行纠正

<Tip>
  一旦发现 Claude 偏离方向，请立即予以纠正。
</Tip>

最好的结果来自于紧密的反馈循环。尽管 Claude 偶尔能在第一次尝试时就完美解决问题，但快速纠正它通常能更快地产生更好的解决方案。

* **`Esc`**：使用 `Esc` 键在执行动作中途停止 Claude。上下文会被保留，因此你可以重新导向。
* **`Esc + Esc` 或 `/rewind`**：按两次 `Esc` 或运行 `/rewind` 打开回溯菜单，恢复之前的对话和代码状态，或从选定的消息开始总结。
* **`"Undo that"`**：让 Claude 撤销其更改。
* **`/clear`**：在不相关的任务之间重置上下文。带有无关上下文的长会话可能会降低性能。

如果你在一个会话中针对同一问题纠正 Claude 超过两次，上下文就会充斥着失败的方法。运行 `/clear` 并结合你所学到的内容，使用更具体的提示词重新开始。带有更好提示词的干净会话几乎总是胜过积累了多次纠正的长会话。

### 积极地管理上下文

<Tip>
  在不相关的任务之间运行 `/clear` 以重置上下文。
</Tip>

Claude Code 在你接近上下文限制时会自动压缩对话历史记录，这能保留重要的代码和决策，同时释放空间。

在长时间的会话中，Claude 的上下文窗口可能会填满无关的对话、文件内容和命令。这可能会降低性能，有时还会分散 Claude 的注意力。

* 在任务之间频繁使用 `/clear` 以完全重置上下文窗口
* 当触发自动压缩时，Claude 会总结最重要的内容，包括代码模式、文件状态和关键决策
* 要获取更多控制权，请运行 `/compact <instructions>`，例如 `/compact Focus on the API changes`
* 要仅压缩部分对话，请使用 `Esc + Esc` 或 `/rewind`，选择一个消息检查点，然后选择**从这里总结**或**总结到此处**。前者从该点开始压缩消息，同时保持先前的上下文完整无缺；后者压缩较早的消息，同时完整保留最近的消息。参见 [恢复与总结](/docs/en/checkpointing#restore-vs-summarize)。
* 在 CLAUDE.md 中使用诸如 `"When compacting, always preserve the full list of modified files and any test commands"` 之类的指令自定义压缩行为，以确保关键上下文在总结后得以保留
* 对于不需要保留在上下文中的快速提问，请使用 [`/btw`](/docs/en/interactive-mode#side-questions-with-%2Fbtw)。答案将显示在可关闭的浮层中，且永远不会进入对话历史记录，因此你可以在不增加上下文的情况下查看细节。

### 使用子智能体进行调查

<Tip>
  使用 `"use subagents to investigate X"` 委托研究。它们在独立的上下文中进行探索，从而保持你的主对话专注于实现。
</Tip>

由于上下文是你的基本限制因素，因此子智能体是最强大的可用工具之一。当 Claude 研究代码库时，它会读取大量文件，所有这些都会消耗你的上下文。子智能体在独立的上下文窗口中运行并返回总结报告：

```text theme={null}
Use subagents to investigate how our authentication system handles token
refresh, and whether we have any existing OAuth utilities I should reuse.
```

子智能体会探索代码库，读取相关文件，并报告发现的结果，所有这些都不会弄乱你的主对话。

在 Claude 实现了某些功能之后，你还可以使用子智能体进行验证：

```text theme={null}
use a subagent to review this code for edge cases
```

### 通过检查点回溯

<Tip>
  您发送的每个提示词都会创建一个检查点。您可以将对话、代码或两者同时恢复到之前的任何检查点。
</Tip>

Claude 会在每次更改之前自动对文件进行快照，以便检查点可以恢复它们。双击 `Escape` 或运行 `/rewind` 以打开回溯菜单。您可以仅恢复对话、仅恢复代码、两者均恢复，或从选定的消息生成摘要。详情请见 [Checkpointing](/docs/en/checkpointing)。

您可以告诉 Claude 尝试一些有风险的操作，而不是仔细计划每一步。如果不起作用，就回溯并尝试不同的方法。检查点会随对话一起保存，因此您可以关闭终端，稍后恢复会话，并且仍然可以进行回溯。

<Warning>
  检查点仅跟踪通过 Claude 的文件编辑工具所做的更改。不会捕获通过 Bash 命令或外部进程所做的更改。这不能替代 git。
</Warning>

### 恢复对话

<Tip>
  使用 `/rename` 命名会话，并将它们视为分支：每个工作流都有其独立的持久上下文。
</Tip>

Claude Code 在本地保存对话，因此当一项任务跨越多个时段时，您无需重新解释上下文。运行 `claude --continue` 以继续最近的会话，或者 `claude --resume` 从列表中进行选择。为会话提供描述性名称，如 `oauth-migration`，以便您日后查找。有关恢复、分支和命名的全套控制，请参见 [管理会话](/docs/en/sessions)。

***

## 自动化与扩展

一旦您能高效使用单个 Claude，就可以通过并行会话、非交互模式和扇出模式来成倍提升您的产出。

到目前为止，一切都假设只有一个人、一个 Claude 和一次对话。但是 Claude Code 可以横向扩展。本节中的技巧展示了您如何能完成更多工作。

### 运行非交互模式

<Tip>
  在 CI、pre-commit 钩子或脚本中使用 `claude -p "prompt"`。添加 `--output-format stream-json --verbose` 以获取流式 JSON 输出。
</Tip>

使用 `claude -p "your prompt"`，您可以非交互式地运行 Claude，而无需交互式提示。除非您传递 `--no-session-persistence`，否则该运行仍会创建可恢复的会话。[非交互模式](/docs/en/headless) 是您将 Claude 集成到 CI 管道、pre-commit 钩子或任何自动化工作流程的方式。这些输出格式让您能够以编程方式解析结果：纯文本、JSON 或流式 JSON。

```bash theme={null}
# One-off queries

claude -p "Explain what this project does"

# Structured output for scripts

claude -p "List all API endpoints" --output-format json

# Streaming for real-time processing

claude -p "Analyze this log file" --output-format stream-json --verbose
```

第一条命令打印纯文本。`json` 格式返回一个带有 `result` 字段的单个 JSON 对象。`stream-json` 格式每行打印一个 JSON 对象，并以初始化事件开始。

### 运行多个 Claude 会话

<Tip>
  并行运行多个 Claude 会话以加快开发速度、运行隔离的实验，或启动复杂的工作流。
</Tip>

选择适合您自己期望的协调程度的并行方法：

* [工作树](/docs/en/worktrees)：在隔离的 git 检出中运行独立的 CLI 会话，这样编辑就不会冲突
* [桌面应用程序](/docs/en/desktop#work-in-parallel-with-sessions)：以可视化方式管理多个本地会话，每个会话都在其自己的工作树中
* [Claude Code 网页版](/docs/en/claude-code-on-the-web)：在 Anthropic 管理的云基础设施上于隔离的虚拟机中运行会话
* [智能体团队](/docs/en/agent-teams)：通过共享任务、消息传递和团队主管来自动协调多个会话

除了并行化工作外，多个会话还支持以质量为中心的工作流。全新的上下文可以改善代码审查，因为 Claude 不会偏向它刚刚编写的代码。

例如，使用编写者/审查者模式：

| 会话 A (编写者)                                                      | 会话 B (审查者)                                                                                                                                                     |
| ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `Implement a rate limiter for our API endpoints`                        |                                                                                                                                                                          |
|                                                                         | `Review the rate limiter implementation in @src/middleware/rateLimiter.ts. Look for edge cases, race conditions, and consistency with our existing middleware patterns.` |
| `Here's the review feedback: [Session B output]. Address these issues.` |                                                                                                                                                                          |

您可以在测试中做类似的事情：让一个 Claude 编写测试，然后让另一个编写代码来通过这些测试。

### 跨文件展开

<Tip>
  循环遍历任务并为每个任务调用 `claude -p`。使用 `--allowedTools` 来设定批量操作的权限范围。
</Tip>

对于大型迁移或分析，您可以将工作分配到许多并行的 Claude 调用中：

<Steps>
  <Step title="生成任务列表">
    让 Claude 列出所有需要迁移的文件（例如，`list all 2,000 Python files that need migrating`）
  </Step>

  <Step title="编写脚本遍历列表">
    ```bash theme={null}
    for file in $(cat files.txt); do
      claude -p "将 $file 从 React 迁移到 Vue。返回 OK 或 FAIL。" \
        --allowedTools "Edit,Bash(git commit *)"
    done
    ```
  </Step>

  <Step title="在几个文件上进行测试，然后大规模运行">
    根据前 2-3 个文件出现的问题来优化您的提示，然后在完整的文件集上运行。`--allowedTools` 标志限制了 Claude 的操作范围，这在您进行无人值守运行时非常重要。
  </Step>
</Steps>

您还可以将 Claude 集成到现有的数据/处理流水线中：

```bash theme={null}
claude -p "<your prompt>" --output-format json | your_command
```

在开发期间使用 `--verbose` 进行调试，并在生产环境中将其关闭。

### 使用自动模式自主运行

若要执行带有后台安全检查的不间断运行，请使用 [自动模式](/docs/en/permission-modes#eliminate-prompts-with-auto-mode)。分类器模型会在命令运行前对其进行审查，阻止范围提升、未知基础设施以及由恶意内容驱动的操作，同时允许日常工作在没有提示的情况下继续进行。

```bash theme={null}
claude --permission-mode auto -p "fix all lint errors"
```

对于使用 `-p` 标志的非交互式运行，如果分类器反复阻止操作，自动模式将中止，因为没有用户可以提供帮助。有关阈值，请参见 [当自动模式回退时](/docs/en/permission-modes#when-auto-mode-falls-back)。

### 添加一个对抗性审查步骤

<Tip>
  在将任务视为完成之前，让一个子代理在全新的上下文中审查差异并报告遗漏。
</Tip>

Claude无人值守工作的时间越长，在您将工作视为完成之前，独立检查就越重要。在全新的[subagent](/docs/en/sub-agents)上下文中运行的审查者只能看到差异和您给定的标准，而看不到产生更改的推理过程，因此它会根据自己的标准来评估结果。

要进行正确性检查，请运行内置的[`/code-review` skill](/docs/en/commands)，它会在全新的子代理中审查当前的差异以查找错误，并将发现的结果返回给会话。如果要改为根据您的计划检查差异，请自行编写审查提示。指出要检查的工作、用于检查的计划，以及什么才算作一项发现：

```text theme={null}
Use a subagent to review the rate limiter diff against PLAN.md. Check that
every requirement is implemented, the listed edge cases have tests, and
nothing outside the task's scope changed. Report gaps, not style preferences.
```

由于审查者作为子代理运行，实施会话会直接收到缺陷报告，并且可以在不需要您跨窗口复制结果的情况下修复它们并重新审查。对于更长时间的自主运行，一个[agent team](/docs/en/agent-teams)可以在您抽查已记录的发现结果时，在多个任务中保持此循环继续。

<Callout>
  被提示去寻找缺陷的审查者通常会报告一些缺陷，即使工作本身毫无问题，因为这就是它被要求做的事。追逐每一项发现会导致过度设计：额外的抽象层、防御性代码以及针对不可能发生的情况的测试。告诉审查者只标记影响正确性或既定需求的缺陷，并将其余的视为可选。
</Callout>

***

## 避免常见的失败模式

这些是常见的错误。及早发现它们可以节省时间：

* **“大杂烩”式会话。** 你从一个任务开始，然后问了 Claude 一些无关的事情，接着又回到第一个任务。上下文中充满了无关信息。
  > **解决方法**：在不相关的任务之间 `/clear`。
* **反复纠正。** Claude 做错了，你纠正它，它还是错的，你再纠正。上下文被失败的尝试污染了。
  > **解决方法**：在两次纠正失败后，`/clear` 并结合你学到的经验编写一个更好的初始提示。
* **过度规定的 CLAUDE.md。** 如果你的 CLAUDE.md 太长，Claude 会忽略掉其中一半，因为重要的规则淹没在了冗杂的信息中。
  > **解决方法**：无情地精简。如果 Claude 在没有该指令的情况下已经能正确完成某事，请将其删除或转换为钩子（hook）。
* **信任与验证之间的鸿沟。** Claude 生成了一个看起来合理的实现，但它无法处理边缘情况。
  > **解决方法**：始终提供验证（测试、脚本、截图）。如果你无法验证它，就不要发布它。
* **无休止的探索。** 你让 Claude 去“调查”某事却没有界定范围。Claude 读取了数百个文件，填满了上下文。
  > **解决方法**：严格缩小调查范围或使用子代理（subagents），这样探索过程就不会消耗你的主要上下文。

***

## 培养你的直觉

本指南中的模式并非一成不变。它们是在通常情况下效果很好的起点，但未必适用于所有情况。

有时你*应该*让上下文积累，因为你正深入处理一个复杂问题，而历史记录很有价值。有时你应该跳过规划，让 Claude 自己去弄清楚，因为任务是探索性的。有时模糊的提示恰好是正确的，因为你希望在限制它之前，看看 Claude 是如何理解这个问题的。

注意观察什么方法有效。当 Claude 产出出色的结果时，留意你做了什么：提示结构、你提供的上下文以及你所处的模式。当 Claude 遇到困难时，问问为什么。是上下文太嘈杂了？提示太模糊了？还是任务太大无法一次性完成？

随着时间的推移，你将培养出任何指南都无法囊括的直觉。你将知道何时该具体、何时该开放，何时该规划、何时该探索，何时该清除上下文、何时该让它积累。

## 相关资源

* [Claude Code的工作原理](/docs/en/how-claude-code-works)：代理循环、工具和上下文管理
* [扩展 Claude Code](/docs/en/features-overview)：技能、钩子、MCP、子代理和插件
* [常见工作流](/docs/en/common-workflows)：用于调试、测试、PR 等的分步指南
* [CLAUDE.md](/docs/en/memory)：存储项目规范和持久化上下文

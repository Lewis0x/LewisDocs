---
title: Claude 如何记住你的项目
source_id: claude-code/memory
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/memory
owner: Anthropic
content_sha256: 39ff20e9f4b3c994154ccde645fee4815c625114dbdb81e10ca8c57b096872a0
translation_of: claude-code/memory
translation_model: k3
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/memory)

Content owner: Anthropic

> ## 文档索引
> 在以下位置获取完整的文档索引：https://code.claude.com/docs/llms.txt
> 在进一步探索之前，请使用此文件来发现所有可用页面。

# Claude 如何记住你的项目

> 通过 CLAUDE.md 文件为 Claude 提供持久化指令，并通过自动记忆让 Claude 自动积累学到的内容。

每个 Claude Code 会话都从一个全新的上下文窗口开始。有两种机制可以跨会话传递知识：

* **CLAUDE.md 文件**：由你编写的指令，为 Claude 提供持久化的上下文
* **自动记忆**：Claude 根据你的纠正和偏好自行记录的笔记

本页介绍如何：

* [编写和组织 CLAUDE.md 文件](#claude-md-files)
* [将规则限定到特定文件类型](#organize-rules-with-claude/rules/) 使用 `.claude/rules/`
* [配置自动记忆](#auto-memory) 让 Claude 自动记笔记
* 当指令未被遵循时进行[故障排查](#troubleshoot-memory-issues)

## CLAUDE.md 与自动记忆

Claude Code 拥有两个互补的记忆系统。两者都会在每次对话开始时加载。Claude 将它们视为上下文，而非强制配置。若要无论 Claude 做出何种决定都阻止某个操作，请改用 [PreToolUse 钩子](/docs/en/hooks-guide)。你的指令越具体、越简洁，Claude 遵循得就越一致。

|                      | CLAUDE.md 文件                                   | 自动记忆                                                      |
| :------------------- | :------------------------------------------------ | :--------------------------------------------------------------- |
| **由谁编写**    | 你                                               | Claude                                                           |
| **包含内容** | 指令与规则                            | 学到的经验与模式                                           |
| **作用范围**            | 项目、用户或组织                             | 每个仓库，跨 worktree 共享                          |
| **加载到**      | 每次会话                                     | 每次会话（前 200 行或 25KB）                          |
| **用途**          | 编码标准、工作流、项目架构 | 构建命令、调试见解、Claude 发现的偏好 |

当你想引导 Claude 的行为时，请使用 CLAUDE.md 文件。自动记忆让 Claude 无需手动操作即可从你的纠正中学习。

子代理也可以维护自己的自动记忆。详情请参阅[子代理配置](/docs/en/sub-agents#enable-persistent-memory)。

## CLAUDE.md 文件

CLAUDE.md 文件是 markdown 文件，用于为项目、你的个人工作流或整个组织向 Claude 提供持久指令。你用纯文本编写这些文件；Claude 会在每次会话开始时读取它们。

### 何时添加到 CLAUDE.md

把 CLAUDE.md 当作记录那些你本需要反复解释的内容的地方。在以下情况时添加到其中：

* Claude 第二次犯了同样的错误
* 代码审查发现了 Claude 本应了解的关于此代码库的信息
* 你在聊天中输入了与上次会话相同的纠正或澄清
* 新团队成员需要相同的上下文才能高效工作

请只保留 Claude 在每次会话中都应掌握的事实：构建命令、约定、项目布局、"始终执行 X"类规则。如果某条条目是多步骤流程或仅与代码库的某一部分相关，请将其移至[技能](/docs/en/skills)或[路径范围规则](#organize-rules-with-claude/rules/)中。[扩展机制概览](/docs/en/features-overview#build-your-setup-over-time)介绍了何时使用每种机制。

### 选择 CLAUDE.md 文件的存放位置

CLAUDE.md 文件可以存放在多个位置，每个位置对应不同的作用范围。下表按加载顺序列出它们，从最广的作用范围到最具体的作用范围，因此项目指令会在用户指令之后出现在上下文中。

| 范围                     | 位置                                                                                                                                                                     | 用途                                                         | 用例示例                                                             | 共享对象                        |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------ | -------------------------------------------------------------------- | ------------------------------- |
| **托管策略**             | • macOS：`/Library/Application Support/ClaudeCode/CLAUDE.md`<br />• Linux 和 WSL：`/etc/claude-code/CLAUDE.md`<br />• Windows：`C:\Program Files\ClaudeCode\CLAUDE.md` | 由 IT/DevOps 管理的组织级指令                                | 公司编码标准、安全策略、合规要求                                     | 组织内所有用户                  |
| **用户指令**             | `~/.claude/CLAUDE.md`                                                                                                                                                    | 适用于所有项目的个人偏好                                     | 代码风格偏好、个人工具快捷方式                                       | 仅你自己（所有项目）            |
| **项目指令**             | `./CLAUDE.md` 或 `./.claude/CLAUDE.md`                                                                                                                           | 团队共享的项目级指令                                         | 项目架构、编码标准、常用工作流                                       | 通过源代码管理共享的团队成员    |
| **本地指令**             | `./CLAUDE.local.md`                                                                                                                                                    | 个人项目专属偏好；请添加到 `.gitignore`             | 你的沙箱 URL、首选测试数据                                           | 仅你自己（当前项目）            |

CLAUDE.md 和 CLAUDE.local.md 文件如果位于工作目录以上的目录层级中，会在启动时完整加载。子目录中的文件则会在 Claude 读取这些目录中的文件时按需加载。有关完整的解析顺序，请参阅 [CLAUDE.md 文件如何加载](#how-claude-md-files-load)。

对于大型项目，你可以使用[项目规则](#organize-rules-with-claude/rules/)将指令拆分为按主题划分的文件。规则允许你将指令限定在特定的文件类型或子目录范围内。

### 设置项目的 CLAUDE.md

项目的 CLAUDE.md 可以存放在 `./CLAUDE.md` 或 `./.claude/CLAUDE.md` 中。创建此文件并添加适用于所有项目参与者的指令：构建和测试命令、编码标准、架构决策、命名约定以及常用工作流。这些指令会通过版本控制与团队共享，因此应关注项目级别的标准而非个人偏好。要确认文件已加载，请在会话中运行 `/context` 并查看 **Memory files** 下的列表。

<Tip>
  运行 `/init` 可自动生成初始的 CLAUDE.md。Claude 会分析你的代码库，并创建一个包含它发现的构建命令、测试说明和项目约定的文件。如果 CLAUDE.md 已存在，`/init` 会提出改进建议而不是覆盖它。然后在此基础上补充 Claude 自己无法发现的指令。

  设置 `CLAUDE_CODE_NEW_INIT=1` 可启用交互式多阶段流程。`/init` 会询问要设置哪些工件：CLAUDE.md 文件、技能和钩子。然后它会使用子代理探索你的代码库，通过后续提问填补空白，并在写入任何文件之前提出可供审查的方案。
</Tip>

### 编写有效的指令

CLAUDE.md 文件会在每次会话开始时加载到上下文窗口中，与你的对话一起占用 token。[上下文窗口可视化](/docs/en/context-window)展示了 CLAUDE.md 相对于其余启动上下文的加载位置。因为它们是上下文而非强制执行的配置，所以你编写指令的方式会影响 Claude 遵循它们的可靠程度。具体、简洁、结构良好的指令效果最佳。

**大小**：每个 CLAUDE.md 文件目标控制在 200 行以内。更长的文件会占用更多上下文并降低遵循度。如果你的指令变得庞大，请使用[按路径限定范围的规则](#path-specific-rules)，使指令仅在 Claude 处理匹配的文件时加载。你也可以将内容拆分为[导入](#import-additional-files)以便组织，不过导入的文件仍会在启动时加载并进入上下文窗口。

**结构**：使用 Markdown 标题和项目符号将相关指令分组。Claude 扫描结构的方式与读者相同：组织有序的章节比密集段落更容易遵循。

**具体性**：编写足够具体、可以验证的指令。例如：

* 使用“使用 2 个空格缩进”而不是“正确格式化代码”
* 使用“提交前运行 `npm test`”而不是“测试你的更改”
* 使用“API 处理程序位于 `src/api/handlers/` 中”而不是“保持文件有条理”

**一致性**：如果两条规则相互矛盾，Claude 可能会任意选择其中一条。定期检查你的 CLAUDE.md 文件、子目录中嵌套的 CLAUDE.md 文件以及 [`.claude/rules/`](#organize-rules-with-claude/rules/)，以删除过时或冲突的指令。在 monorepo 中，使用 [`claudeMdExcludes`](#exclude-specific-claude-md-files) 跳过与你工作无关的其他团队的 CLAUDE.md 文件。

### 导入其他文件

CLAUDE.md 文件可以使用 `@path/to/import` 语法导入其他文件。被导入的文件会在启动时展开并加载到上下文中，与引用它们的 CLAUDE.md 一起生效。

相对路径和绝对路径都可以使用。相对路径相对于包含导入语句的文件解析，而不是相对于工作目录。被导入的文件可以递归地导入其他文件，最大深度为四跳。

导入解析会跳过 Markdown 的行内代码和围栏代码块。如果你想在 CLAUDE.md 中提及某个路径而不导入它，请用反引号将其包裹：在反引号之外书写 `` `@README` `` keeps the text literal, while `@README` 会导入该文件。

要引入 README、package.json 和工作流指南，请在 `@` 中的任意位置使用 CLAUDE.md 语法引用它们：

```text theme={null}
See @README for project overview and @package.json for available npm commands for this project.

# Additional Instructions

- git workflow @docs/git-instructions.md
```

对于不应提交到版本控制的私有项目级偏好设置，请在项目根目录创建一个 `CLAUDE.local.md`。它会与 `CLAUDE.md` 一起加载，并以相同方式处理。将 `CLAUDE.local.md` 添加到你的 `.gitignore` 中，以免它被提交。设置 `CLAUDE_CODE_NEW_INIT=1` 后，运行 `/init` 并选择个人选项即可为你完成此操作。

如果你在同一个仓库的多个 git worktree 中工作，被 gitignore 的 `CLAUDE.local.md` 只存在于你创建它的那个 worktree 中。要在多个 worktree 之间共享个人指令，请改为从你的主目录导入一个文件：

```text theme={null}
# Individual Preferences

- @~/.claude/my-project-instructions.md
```

<Warning>
  当项目级记忆文件中的导入路径解析到工作目录之外时（例如上面的主目录导入），该导入即为外部导入。Claude Code 第一次在项目中遇到外部导入时，会显示一个列出这些文件的批准对话框。如果你拒绝，这些导入将保持禁用状态，且该对话框不会再次出现。

  该对话框保护你免受其他人提交到共享项目的文件的影响。用户作用域记忆文件（如 `~/.claude/CLAUDE.md` 和 `~/.claude/rules/`）中的导入是你自己编写的文件，因此它们无需对话框即可加载，并与你其余的个人配置具有相同的信任级别。
</Warning>

有关组织指令的更结构化的方法，请参阅 [`.claude/rules/`](#organize-rules-with-claude/rules/)。

### AGENTS.md

Claude Code 读取 `CLAUDE.md`，而不是 `AGENTS.md`。如果你的仓库已经为其他编码代理使用了 `AGENTS.md`，请创建一个导入它的 `CLAUDE.md`，这样两个工具就能读取相同的指令而无需重复。你也可以在导入语句下方添加 Claude 专属的指令。Claude 会在会话开始时加载被导入的文件，然后追加其余内容：

```markdown CLAUDE.md theme={null}
@AGENTS.md

## Claude Code

Use plan mode for changes under `src/billing/`.
```

如果你不需要添加 Claude 专属内容，符号链接也可以：

```bash theme={null}
ln -s AGENTS.md CLAUDE.md
```

该命令成功时不打印任何输出。在你的下一个会话中，运行 `/context` 并确认 `CLAUDE.md` 出现在 **Memory files** 下。

在 Windows 上，创建符号链接需要管理员权限或开发者模式，因此请改用 `@AGENTS.md` 导入。

运行 [`/init`](/docs/en/commands) 会读取位于 `.cursor/rules/` 或 `.cursorrules` 中的 Cursor 规则，以及 `.github/copilot-instructions.md` 中的 Copilot 规则，并将相关部分合并到生成的 `CLAUDE.md` 中。设置 `CLAUDE_CODE_NEW_INIT=1` 后，`/init` 还会读取 `AGENTS.md`、`.devin/rules/`、`.windsurf/rules/` 或 `.windsurfrules`，以及 `.clinerules`。

### CLAUDE.md 文件如何加载

Claude Code 通过从你当前的工作目录沿目录树向上遍历，检查沿途每个目录中的 CLAUDE.md 和 `CLAUDE.md` 文件来读取 `CLAUDE.local.md` 文件。这意味着如果你在 Claude Code 中运行 `foo/bar/`，它会加载来自 `foo/bar/CLAUDE.md`、`foo/CLAUDE.md` 以及它们旁边的任何 `CLAUDE.local.md` 文件的指令。

所有发现的文件都会被拼接到上下文中，而不是相互覆盖。在整个目录树中，内容按从文件系统根目录到你的工作目录的顺序排列。对于 `foo/bar/` 示例，`foo/CLAUDE.md` 在上下文中出现在 `foo/bar/CLAUDE.md` 之前，因此离你启动 Claude 的位置更近的指令会被最后读取。在每个目录内，`CLAUDE.local.md` 会追加在 `CLAUDE.md` 之后，因此你的个人笔记是 Claude 在该层级最后读取的内容。

Claude 还会发现当前工作目录下子目录中的 `CLAUDE.md` 和 `CLAUDE.local.md` 文件。它们不会在启动时加载，而是在 Claude 读取这些子目录中的文件时被纳入。

如果你在一个大型 monorepo 中工作，其他团队的 CLAUDE.md 文件会被拾取到，可以使用 [`claudeMdExcludes`](#exclude-specific-claude-md-files) 来跳过它们。关于根目录和按目录的 CLAUDE.md 文件及规则的完整布局，请参阅 [Monorepos 和大型仓库](/docs/en/large-codebases)。

`<!-- maintainer notes -->` 文件中的块级 HTML 注释（CLAUDE.md）会在内容注入 Claude 上下文之前被剥离。你可以用它们为人类维护者留下备注，而无需为此消耗上下文令牌。代码块内的注释会被保留。当你直接使用 Read 工具打开 CLAUDE.md 文件时，注释仍然可见。

#### 从其他目录加载

`--add-dir` 标志让 Claude 可以访问主工作目录之外的其他目录。默认情况下，这些目录中的 CLAUDE.md 文件不会被加载。

若要同时从其他目录加载内存文件，请设置 `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD` 环境变量：

```bash theme={null}
CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1 claude --add-dir ../shared-config
```

这会从附加目录加载 `CLAUDE.md`、`.claude/CLAUDE.md`、`.claude/rules/*.md` 和 `CLAUDE.local.md`。`CLAUDE.local.md` 是 如果您将 `local` 从中排除，则跳过 [`--setting-sources`](/docs/en/cli-reference).

### 使用 `.claude/rules/` 组织规则

对于较大的项目，你可以使用 `.claude/rules/` 目录将说明组织到多个文件中。这能让说明保持模块化，也便于团队维护。规则还可以[限定到特定文件路径](#path-specific-rules)，这样只有当 Claude 处理匹配文件时，它们才会加载到上下文中，从而减少干扰并节省上下文空间。

<Note>
  规则会在每次会话时加载到上下文中，或在打开匹配的文件时加载。对于不需要一直存在于上下文中的任务专属说明，请改用 [技能](/docs/en/skills)，它们仅在你调用它们时或 Claude 判断它们与你的提示相关时才会加载。
</Note>

#### 设置规则

将 Markdown 文件放置在项目的 `.claude/rules/` 目录中。每个文件应涵盖一个主题，并使用描述性文件名，例如 `testing.md` 或 `api-design.md`。所有 `.md` 文件都会被递归发现，因此你可以将规则组织到子目录中，例如 `frontend/` 或 `backend/`：

```text theme={null}
your-project/
├── .claude/
│   ├── CLAUDE.md           # Main project instructions
│   └── rules/
│       ├── code-style.md   # Code style guidelines
│       ├── testing.md      # Testing conventions
│       └── security.md     # Security requirements
```

没有 [`paths` frontmatter](#path-specific-rules) 的规则会在启动时加载，其优先级与 `.claude/CLAUDE.md` 相同。

如果你将 `project` 从 [`--setting-sources`](/docs/en/cli-reference) 中排除，项目规则将被跳过。 {/* min-version: 2.1.211 */}在 v2.1.211 之前，按需加载的规则（包括路径限定规则和嵌套 `.claude/rules/` 目录中的规则）即使 `project` 被排除也会加载。

#### 路径特定规则

可以使用带有 `paths` 字段的 YAML frontmatter 将规则限定到特定文件。这些条件规则仅在 Claude 处理与指定模式匹配的文件时才会应用。

```markdown theme={null}
---
paths:
  - "src/api/**/*.ts"
---

# API Development Rules

- All API endpoints must include input validation
- Use the standard error response format
- Include OpenAPI documentation comments
```

没有 `paths` 字段的规则会被无条件加载，并应用于所有文件。路径作用域规则在 Claude 读取与模式匹配的文件时触发，而不是在每次工具使用时触发。{/* min-version: 2.1.198 */}自 v2.1.198 起，当 Claude 通过指向项目目录的符号链接路径访问文件时（例如在符号链接的检出目录中），匹配也同样生效。

在 `paths` 字段中使用 glob 模式，按扩展名、目录或任意组合匹配文件：

| 模式                | 匹配内容                                  |
| ---------------------- | ---------------------------------------- |
| `**/*.ts`              | 任意目录中的所有 TypeScript 文件    |
| `src/**/*`             | `src/` 目录下的所有文件         |
| `*.md`                 | 项目根目录中的 Markdown 文件       |
| `src/components/*.tsx` | 特定目录中的 React 组件 |

你可以指定多个模式，并使用花括号扩展在一个模式中匹配多个扩展名：
```markdown theme={null}
---
paths:
  - "src/**/*.{ts,tsx}"
  - "lib/**/*.ts"
  - "tests/**/*.test.ts"
---
```

每个花括号组都会使展开后的模式数量相乘：`src/*.{ts,tsx}` 展开为两个模式，`{a,b}/{c,d}/*.{ts,tsx}` 展开为八个。为了保持扩展有界，规则整个 `paths` 列表共享 1,000 个展开模式和 4 MiB 的预算，而不含花括号的模式不计入该预算。

Claude Code 使用任何在展开后会超出预算的模式，且其字面量花括号不匹配任何文件。{/* min-version: 2.1.217 */}在 v2.1.217 之前，包含大量花括号组的 `paths` 值会导致 CLI 在启动时卡顿或崩溃。

Glob 语法将 `[` 视为方括号表达式的开始,例如 `[abc]`。包含无法被解析为方括号表达式的 `[` 的模式(例如 `photos [2024/**`)是无效的:它不匹配任何内容,而规则中的其他模式仍然有效。要在文件名中匹配字面的 `[`,请将其转义为 `photos \[2024/**`。{/* min-version: 2.1.207 */}在 v2.1.207 之前,一个无效模式会导致 Read 工具对规则评估的每个文件都失败,而不是不匹配任何内容。

#### 使用符号链接跨项目共享规则

`.claude/rules/` 目录支持符号链接，因此你可以维护一组共享规则，并将它们链接到多个项目中。符号链接会被正常解析和加载，循环符号链接也会被检测并妥善处理。

此示例同时链接一个共享目录和一个单独文件：

```bash theme={null}
ln -s ~/shared-claude-rules .claude/rules/shared
ln -s ~/company-standards/security.md .claude/rules/security.md
```

#### 用户级规则

`~/.claude/rules/` 中的个人规则会应用到你机器上的每个项目。可将它们用于并非特定于某个项目的偏好设置：

```text theme={null}
~/.claude/rules/
├── preferences.md    # Your personal coding preferences
└── workflows.md      # Your preferred workflows
```

用户级规则先于项目规则加载，因此项目规则具有更高优先级。

### 为大型团队管理 CLAUDE.md

对于跨团队部署 Claude Code 的组织，你可以集中管理指令，并控制加载哪些 CLAUDE.md 文件。

#### 部署组织范围的 CLAUDE.md

组织可以部署一个集中管理的 CLAUDE.md，使其应用于机器上的所有用户。此文件无法通过个人设置排除。

<Steps>
  <Step title="在托管策略位置创建文件">
    * macOS：`/Library/Application Support/ClaudeCode/CLAUDE.md`
    * Linux 和 WSL：`/etc/claude-code/CLAUDE.md`
    * Windows：`C:\Program Files\ClaudeCode\CLAUDE.md`
  </Step>

  <Step title="使用配置管理系统进行部署">
    使用 MDM、组策略、Ansible 或类似工具，将该文件分发到开发人员的机器上。有关其他组织范围的配置选项，请参阅[托管设置](/docs/en/permissions#managed-settings)。
  </Step>
</Steps>

`claudeMd` 键允许你直接将托管的 CLAUDE.md 内容放入 `managed-settings.json` 中，而无需部署单独的文件。

**范围**：机器上每个仓库中的每一次 Claude Code 会话。如需针对特定仓库的指导，请改为提交项目 CLAUDE.md。

**优先级**：与托管的 CLAUDE.md 文件相同。先于用户和项目 CLAUDE.md 加载。

**生效位置**：仅限托管设置和策略设置。在用户、项目或本地设置中设置 `claudeMd` 不会产生任何效果。

下面的示例直接在托管设置文件中添加行为指令：

```json theme={null}
{
  "claudeMd": "Always run `make lint` before committing.\nNever push directly to main."
}
```

托管的 CLAUDE.md 与[托管设置](/docs/en/settings#settings-files)服务于不同目的。使用设置进行技术强制，使用 CLAUDE.md 提供行为指导：

| 关注点                                         | 配置位置                                                  |
| :--------------------------------------------- | :-------------------------------------------------------- |
| 阻止特定工具、命令或文件路径                    | 托管设置：`permissions.deny`                            |
| 强制执行沙箱隔离                                | 托管设置：`sandbox.enabled`                            |
| 环境变量和 API 提供商路由                       | 托管设置：`env`                            |
| 身份验证方式和组织锁定                          | 托管设置：`forceLoginMethod`、`forceLoginOrgUUID`      |
| 代码风格和质量准则                              | 托管 CLAUDE.md                                 |
| 数据处理与合规提醒                              | 托管 CLAUDE.md                                 |
| 针对 Claude 的行为指令 | 托管的 CLAUDE.md |

设置规则由客户端强制执行，无论 Claude 决定如何行动。CLAUDE.md 指令会影响 Claude 的行为，但不是硬性强制执行层。

#### 排除特定的 CLAUDE.md 文件

在大型 monorepo 中, 祖先 CLAUDE.md 文件可能包含与你工作无关的指令。`claudeMdExcludes` 设置允许你通过路径或 glob 模式跳过特定文件。

此示例排除了一个顶级 CLAUDE.md 和一个父文件夹中的规则目录。将其添加到 `.claude/settings.local.json`, 以便排除仅在本地机器上生效:

```json theme={null}
{
  "claudeMdExcludes": [
    "**/monorepo/CLAUDE.md",
    "/home/user/monorepo/other-team/.claude/rules/**"
  ]
}
```

模式使用 glob 语法与绝对文件路径进行匹配。您可以在任意位置配置 `claudeMdExcludes` [设置层](/docs/en/settings#settings-files): 用户、项目、本地或托管策略。数组会跨层合并。

托管策略 CLAUDE.md 文件无法被排除。这确保了组织范围的指令无论个人设置如何都始终生效。

## 自动记忆

自动记忆让 Claude 无需你手动编写任何内容即可跨会话积累知识。Claude 在工作时会为自己保存笔记：构建命令、调试心得、架构说明、代码风格偏好以及工作流习惯。Claude 并非每次会话都会保存内容。它会根据这些信息在未来对话中是否有用来判断哪些值得记住。

### 启用或禁用自动记忆

自动记忆默认开启。要切换它，请在会话中打开 `/memory` 并使用自动记忆开关，该开关会将 `autoMemoryEnabled` 保存到位于 `~/.claude/settings.json` 的用户设置中。要为单个项目关闭它，请在该项目的设置中设置 `autoMemoryEnabled`：

```json theme={null}
{
  "autoMemoryEnabled": false
}
```

要通过环境变量禁用自动记忆，请设置 `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`。

### 存储位置

每个项目都在 `~/.claude/projects/<project>/memory/` 拥有自己的记忆目录。`<project>` 路径派生自 git 仓库，因此同一仓库内的所有工作树和子目录共享一个自动记忆目录。在 git 仓库之外，则使用项目根目录。

要将自动记忆存储在不同位置，请在 `autoMemoryDirectory` 中设置 `settings.json`。它可以从任何[设置作用域](/docs/en/settings#settings-precedence)读取：用户、项目、本地、策略或 `--settings`。

```json theme={null}
{
  "autoMemoryDirectory": "~/my-custom-memory-dir"
}
```

该值必须是绝对路径，或以 `~/` 开头。当在项目的 `.claude/settings.json` 或 `.claude/settings.local.json` 中设置时，只有在你接受该文件夹的工作区信任对话框后该值才会生效，这与管控钩子的机制相同。

该目录包含一个 `MEMORY.md` 入口文件和可选的主题文件：

```text theme={null}
~/.claude/projects/<project>/memory/
├── MEMORY.md          # Concise index, loaded into every session
├── debugging.md       # Detailed notes on debugging patterns
├── api-conventions.md # API design decisions
└── ...                # Any other topic files Claude creates
```

`MEMORY.md` 充当记忆目录的索引。Claude 会在你的会话期间读写此目录中的文件，使用 `MEMORY.md` 来跟踪哪些内容存储在哪里。

自动记忆是机器本地的。同一 git 仓库内的所有工作树和子目录共享一个自动记忆目录。文件不会跨机器或云环境共享。

### 工作原理

`MEMORY.md` 的前 200 行，或前 25KB（以先到者为准），会在每次对话开始时加载。超出该阈值的内容不会在会话启动时加载。Claude 通过将详细笔记移入单独的主题文件来保持 `MEMORY.md` 简洁。

{/* min-version: 2.1.210 */}Claude 写入 `MEMORY.md` 后，Claude Code 会针对 200 行和 25KB 的读取限制检查该文件。如果文件接近限制，Claude Code 会提醒 Claude 缩短它：每条目保留一行，将细节移入主题文件，并合并或删除过时的条目。如果文件超过限制，写入仍会成功，但 Claude Code 会返回一个[告知 Claude 重写索引的错误](/docs/en/errors#memory-index-is-over-its-read-limit)，因为超出限制的所有内容都会在下次加载时被丢弃。

{/* min-version: 2.1.211 */}该检查只衡量实际加载的内容：YAML frontmatter 和块级 HTML 注释在索引加载前会被剥离，因此它们不计入限制。在 v2.1.211 之前，Claude Code 衡量的是原始文件，即使加载的内容符合要求，frontmatter 或注释也可能触发错误。

此限制仅适用于 `MEMORY.md`。CLAUDE.md 文件无论长度如何都会完整加载，不过较短的文件能产生更好的遵循度。

像 `debugging.md` 或 `patterns.md` 这样的主题文件不会在启动时加载。Claude 会在需要这些信息时使用其标准文件工具按需读取它们。

主对话的自动记忆不会加载到[子代理](/docs/en/sub-agents#what-loads-at-startup)中；例外情况是 [fork](/docs/en/sub-agents#fork-the-current-conversation)，它会继承父对话和系统提示。通过子代理 `memory` 字段启用的子代理自身的自动记忆是一个单独的目录。

Claude 在你的会话期间读写记忆文件。当你在 Claude Code 界面中看到"Saved 2 memories"或"Recalled 2 memories"之类的消息时，Claude 正在主动更新或读取 `~/.claude/projects/<project>/memory/`。

{/* min-version: 2.1.214 */}当 Claude 写入以 YAML frontmatter 开头的记忆文件时，Claude Code 会将写入时间以 ISO 8601 时间戳的形式记录在 `modified` frontmatter 字段中。该时间戳向你以及读取记忆时的 Claude 显示事实的时效性。任何已有 frontmatter 的文件都会在 Claude 下次写入时获得该字段，包括在更早版本上创建的文件；Claude Code 绝不会为没有 frontmatter 的文件添加 frontmatter。`modified` 字段需要 Claude Code v2.1.214 或更高版本。

### 审计和编辑你的记忆

自动记忆文件是纯 markdown，你可以随时编辑或删除。运行 [`/memory`](#view-and-edit-with-%2Fmemory) 可在会话内浏览和打开记忆文件。

## 使用 `/memory` 查看和编辑

`/memory` 命令会列出用户和项目作用域下的 CLAUDE.md、CLAUDE.local.md 以及其他内存文件位置，包括尚不存在的文件对应的用户和项目 CLAUDE.md 条目。它还允许你开启或关闭自动内存，并提供打开自动内存文件夹的选项。选择任意文件即可在编辑器中打开它；如果选择尚不存在的文件，则会先创建该文件。要检查当前会话中实际加载了哪些文件，请运行 `/context`。

{/* min-version: 2.1.216 */}像 VS Code 这样的 GUI 编辑器会在单独的窗口中打开文件，并且你可以在它打开期间继续使用会话。在 v2.1.216 之前，`/memory` 会等待你关闭文件后才做出响应。像 Vim 这样的终端编辑器会占用终端，直到你退出为止。

当你要求 Claude 记住某些内容时，比如“始终使用 pnpm，而不是 npm”或“记住 API 测试需要本地 Redis 实例”，Claude 会将其保存到自动记忆中。若要改为将指令添加到 CLAUDE.md，可以直接告诉 Claude，比如“将此添加到 CLAUDE.md”，或者通过 `/memory` 自行编辑该文件。

## 排查记忆问题

以下是 CLAUDE.md 和自动记忆最常见的问题，以及相应的调试步骤。

### Claude 没有遵循我的 CLAUDE.md

CLAUDE.md 的内容是作为系统提示之后的用户消息传递的，而不是系统提示本身的一部分。Claude 会阅读它并尝试遵循它，但无法保证严格遵守，尤其是对于模糊或相互冲突的指令。

调试方法：

* 运行 `/context` 并查看 **Memory files** 下的列表，以验证你的 CLAUDE.md 和 CLAUDE.local.md 文件已加载。如果某个文件未出现在列表中，Claude 就看不到它。使用 `/memory` 打开并编辑这些文件。
* 检查相关的 CLAUDE.md 是否位于会为你的会话加载的位置（参见[选择 CLAUDE.md 文件的放置位置](#choose-where-to-put-claude-md-files)）。
* 让指令更具体。“使用 2 空格缩进”比“把代码格式写得漂亮些”效果更好。
* 检查各个 CLAUDE.md 文件中是否存在相互冲突的指令。如果两个文件对同一行为给出了不同的指导，Claude 可能会随意选择其中一个。

如果指令必须在特定时间点运行，例如在每次提交之前或每次文件编辑之后，请将其编写为 [hook](/docs/en/hooks-guide)。Hooks 会在固定的生命周期事件中以 shell 命令的形式执行，无论 Claude 决定做什么都会生效。

对于你希望放在系统提示级别的指令，请使用 [`--append-system-prompt`](/docs/en/cli-reference#system-prompt-flags)。这必须在每次调用时传递，因此更适合脚本和自动化，而不是交互式使用。

<Tip>
  使用 [`InstructionsLoaded` hook](/docs/en/hooks#instructionsloaded) 来准确记录哪些指令文件被加载、何时加载以及加载原因。这对于调试特定路径的规则或子目录中懒加载的文件非常有用。
</Tip>

### 我不知道自动记忆保存了什么

运行 `/memory` 并选择自动记忆文件夹，即可浏览 Claude 保存的内容。所有内容都是纯 Markdown，你可以阅读、编辑或删除。

### 我的 CLAUDE.md 太大了

超过 200 行的文件会消耗更多上下文，并可能降低遵循度。使用[路径范围规则](#path-specific-rules)，仅在 Claude 处理匹配文件时加载指令，或者删减并非每个会话都需要的内容。拆分为 [`@path` 导入](#import-additional-files)有助于组织，但不会减少上下文，因为导入的文件会在启动时加载。

{/* min-version: 2.1.206 */}[`/doctor`](/docs/en/commands#all-commands) 检查会为已检入的 CLAUDE.md 提出删减建议：它会删除 Claude 可以从代码库推导出的内容，例如目录结构、依赖列表和架构概述，并保留与工具默认值不同的陷阱、原理和约定。该删减检查需要 Claude Code v2.1.206 或更高版本。

### 指令在 `/compact` 之后似乎丢失了

项目根目录的 CLAUDE.md 在压缩后仍然保留：在 `/compact` 之后，Claude 会从磁盘重新读取它并将其重新注入会话。子目录中嵌套的 CLAUDE.md 文件不会自动重新注入；它们会在 Claude 下次读取该子目录中的文件时重新加载。

如果某条指令在压缩后消失了，那么它要么只在对话中给出过，要么位于尚未重新加载的嵌套 CLAUDE.md 中。将仅在对话中出现的指令添加到 CLAUDE.md，以使它们持久保存。完整说明请参见[压缩后保留的内容](/docs/en/context-window#what-survives-compaction)。

有关大小、结构和具体性方面的指导，请参见[编写有效的指令](#write-effective-instructions)。

## 相关资源

* [调试你的配置](/docs/en/debug-your-config)：诊断 CLAUDE.md 或设置未生效的原因
* [技能](/docs/en/skills)：将可重复的工作流程打包并按需加载
* [设置](/docs/en/settings)：使用设置文件配置 Claude Code 行为
* [子代理记忆](/docs/en/sub-agents#enable-persistent-memory)：让子代理维护自己的自动记忆

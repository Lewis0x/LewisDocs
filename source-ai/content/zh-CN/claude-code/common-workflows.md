---
title: 常用工作流
source_id: claude-code/common-workflows
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/common-workflows
owner: Anthropic
content_sha256: 1ebdc7f9889596a169fe4b715b6f4b0dcd2baff10e75765a193ac15b8c8f0580
translation_of: claude-code/common-workflows
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/common-workflows)

Content owner: Anthropic

> ## 文档索引
> 在此处获取完整的文档索引：https://code.claude.com/docs/llms.txt
> 在进一步探索之前，请使用此文件发现所有可用页面。

# 常用工作流

> 使用 Claude Code 探索代码库、修复错误、重构、测试以及处理其他日常任务的分步指南。

本页面收集了用于日常开发的简短秘籍。有关提示词和上下文管理的更高级指导，请参见 [最佳实践](/docs/en/best-practices)。

本页面包含：

* [提示词秘籍](#prompt-recipes) 用于探索代码、修复错误、重构、测试、PR 和文档
* [恢复之前的对话](#resume-previous-conversations) 以便任务可以跨越多次会话
* [使用工作树运行并行会话](#run-parallel-sessions-with-worktrees) 以便并发编辑不会发生冲突
* [编辑前规划](#plan-before-editing) 以便在更改写入磁盘之前进行审查
* [委派研究任务给子代理](#delegate-research-to-subagents) 以保持主上下文整洁
* [将 Claude 通过管道接入脚本](#pipe-claude-into-scripts) 用于 CI 和批处理

## 提示词秘籍

这些是用于日常任务（如探索不熟悉的代码、调试、重构、编写测试和创建 PR）的提示词模式。每个模式都适用于任何 Claude Code 界面；请根据您的项目调整措辞。

### 理解新代码库

有关在 monorepo 或大型代码库中配置 Claude Code 的信息，请参见 [Monorepo 和大型仓库](/docs/en/large-codebases)。

#### 快速获取代码库概览

假设您刚刚加入一个新项目，需要快速了解其结构。

<Steps>
  <Step title="导航到项目根目录">
    ```bash theme={null}
    cd /path/to/project
    ```

    将 `/path/to/project` 替换为您的项目路径。
  </Step>

  <Step title="启动 Claude Code">
    ```bash theme={null}
    claude
    ```
  </Step>

  <Step title="请求获取高级概览">
    ```text theme={null}
    给我这个代码库的概览
    ```
  </Step>

  <Step title="深入了解特定组件">
    ```text theme={null}
    解释这里使用的主要架构模式
    ```

    ```text theme={null}
    关键的数据模型有哪些？
    ```

    ```text theme={null}
    身份验证是如何处理的？
    ```
  </Step>
</Steps>

<Tip>
  提示：

  * 从宽泛的问题开始，然后缩小到特定区域
  * 询问项目中使用的编码约定和模式
  * 请求获取项目特定术语的词汇表
</Tip>

#### 查找相关代码

假设您需要定位与特定功能或特性相关的代码。

<Steps>
  <Step title="要求 Claude 查找相关文件">
    ```text theme={null}
    查找处理用户身份验证的文件
    ```
  </Step>

  <Step title="获取有关组件如何交互的上下文">
    ```text theme={null}
    这些身份验证文件是如何协同工作的？
    ```
  </Step>

  <Step title="理解执行流程">
    ```text theme={null}
    追踪从前端到数据库的登录过程
    ```
  </Step>
</Steps>

<Tip>
  提示：

  * 明确说明您在寻找什么
  * 使用项目中的领域语言
  * 为您的语言安装一个 [代码智能插件](/docs/en/discover-plugins#code-intelligence)，以为 Claude 提供精确的“转到定义”和“查找引用”导航
</Tip>

***

### 高效修复 Bug

假设您遇到了一条错误消息，需要找到并修复其源头。

<Steps>
  <Step title="与 Claude 分享错误">
    ```text theme={null}
    我在运行 npm test 时遇到了一个错误
    ```
  </Step>

  <Step title="询问修复建议">
    ```text theme={null}
    建议几种修复 user.ts 中的 @ts-ignore 的方法
    ```
  </Step>

  <Step title="应用修复">
    ```text theme={null}
    更新 user.ts 以添加您建议的 null 检查
    ```
  </Step>
</Steps>

<Tip>
  提示：

  * 告诉 Claude 重现问题的命令并获取堆栈跟踪
  * 提及重现该错误的任何步骤
  * 让 Claude 知道错误是间歇性的还是持续性的
</Tip>

***

### 重构代码

假设您需要更新旧代码以使用现代的模式和实践。

<Steps>
  <Step title="识别需要重构的遗留代码">
    ```text theme={null}
    在我们的代码库中查找已弃用的 API 用法
    ```
  </Step>

  <Step title="获取重构建议">
    ```text theme={null}
    建议如何重构 utils.js 以使用现代 JavaScript 特性
    ```
  </Step>

  <Step title="安全地应用更改">
    ```text theme={null}
    重构 utils.js 以使用 ES2024 特性，同时保持相同的行为
    ```
  </Step>

  <Step title="验证重构">
    ```text theme={null}
    运行重构后代码的测试
    ```
  </Step>
</Steps>

<Tip>
  提示：

  * 要求 Claude 解释现代方法的好处
  * 要求在需要时更改应保持向后兼容性
  * 以微小且可测试的增量进行重构
</Tip>

***

### 处理测试

假设您需要为未覆盖的代码添加测试。

<Steps>
  <Step title="识别未测试的代码">
    ```text theme={null}
    在 NotificationsService.swift 中查找未被测试覆盖的函数
    ```
  </Step>

  <Step title="生成测试脚手架">
    ```text theme={null}
    为通知服务添加测试
    ```
  </Step>

  <Step title="添加有意义的测试用例">
    ```text theme={null}
    为通知服务中的边缘条件添加测试用例
    ```
  </Step>

  <Step title="运行并验证测试">
    ```text theme={null}
    运行新测试并修复所有失败
    ```
  </Step>
</Steps>

Claude 可以生成遵循您项目现有模式和规范的测试。在请求测试时，请具体说明您想要验证的行为。Claude 会检查您现有的测试文件，以匹配正在使用的样式、框架和断言模式。

为了实现全面的覆盖，请让 Claude 识别您可能遗漏的边缘情况。Claude 可以分析您的代码路径，并针对容易忽略的错误条件、边界值和意外输入建议测试。

***

### 创建 Pull Request

您可以通过直接要求 Claude（“为我的更改创建一个 pr”）来创建拉取请求，或者逐步引导 Claude 完成：

<Steps>
  <Step title="总结您的更改">
    ```text theme={null}
    总结我对身份验证模块所做的更改
    ```
  </Step>

  <Step title="生成拉取请求">
    ```text theme={null}
    创建一个 pr
    ```
  </Step>

  <Step title="审查和优化">
    ```text theme={null}
    通过更多关于安全性改进的上下文来增强 PR 描述
    ```
  </Step>
</Steps>

当您使用 `gh pr create` 创建 PR 时，会话会自动链接到该 PR。稍后要找到它，请运行带有您自己的 PR 编号的 `claude --from-pr 1234`，这将打开会话选择器并筛选出链接到该 PR 的会话，或者将 PR URL 粘贴到 [`/resume` 选择器](/docs/en/sessions#use-the-session-picker) 搜索中。

<Tip>
  在提交之前审查 Claude 生成的 PR，并要求 Claude 强调潜在的风险或注意事项。
</Tip>

### 处理文档

假设你需要为代码添加或更新文档。

<Steps>
  <Step title="识别未文档化的代码">
    ```text theme={null}
    查找 auth 模块中没有正确 JSDoc 注释的函数
    ```
  </Step>

  <Step title="生成文档">
    ```text theme={null}
    为 auth.js 中未文档化的函数添加 JSDoc 注释
    ```
  </Step>

  <Step title="审查并增强">
    ```text theme={null}
    通过提供更多上下文和示例来改进生成的文档
    ```
  </Step>

  <Step title="验证文档">
    ```text theme={null}
    检查文档是否遵循我们的项目标准
    ```
  </Step>
</Steps>

<Tip>
  提示：

  * 指定你想要的文档样式（JSDoc、docstrings 等）
  * 要求在文档中提供示例
  * 要求为公共 API、接口和复杂逻辑编写文档
</Tip>

***

### 在笔记和非代码文件夹中工作

Claude Code 可以在任何目录中工作。在笔记库、文档文件夹或任何 Markdown 文件集合中运行它，以像处理代码一样搜索、编辑和重新组织内容。

`.claude/` 目录和 `CLAUDE.md` 与其他工具的配置目录并存，互不冲突。Claude 在每次调用工具时都会重新读取文件，因此下次读取该文件时，它会看到你在其他应用程序中所做的编辑。

***

### 处理图像

假设你需要处理代码库中的图像，并希望 Claude 帮助分析图像内容。

<Steps>
  <Step title="将图像添加到对话中">
    你可以使用以下任何方法：

    1. 将图像拖放到 Claude Code 窗口中
    2. 复制图像并使用 Ctrl+V 将其粘贴到 CLI 中。在 macOS 上，Cmd+V 在 iTerm2 中同样有效。
    3. 向 Claude 提供图像路径。例如，“分析这张图像：/path/to/your/image.png”
  </Step>

  <Step title="让 Claude 分析图像">
    ```text theme={null}
    这张图像展示了什么？
    ```

    ```text theme={null}
    描述此屏幕截图中的 UI 元素
    ```

    ```text theme={null}
    此图表中是否存在任何有问题的元素？
    ```
  </Step>

  <Step title="将图像用作上下文">
    ```text theme={null}
    这是该错误的屏幕截图。是什么导致了它？
    ```

    ```text theme={null}
    这是我们当前的数据库架构。我们该如何为新功能修改它？
    ```
  </Step>

  <Step title="从可视内容获取代码建议">
    ```text theme={null}
    生成 CSS 以匹配此设计模型
    ```

    ```text theme={null}
    什么样的 HTML 结构可以重新创建此组件？
    ```
  </Step>
</Steps>

<Tip>
  提示：

  * 当文本描述不清晰或繁琐时使用图像
  * 包含错误、UI 设计或图表的屏幕截图以获取更好的上下文
  * 你可以在对话中处理多张图像
  * 图像分析适用于图表、屏幕截图、模型等
  * 当 Claude 引用图像时（例如，`[Image #1]`），`Cmd+Click` (Mac) 或 `Ctrl+Click` (Windows/Linux) 用于在你的默认查看器中打开图像的链接
</Tip>

***

### 引用文件和目录

使用 @ 快速包含文件或目录，而无需等待 Claude 读取它们。

<Steps>
  <Step title="引用单个文件">
    ```text theme={null}
    解释 @src/utils/auth.js 中的逻辑
    ```

    这会将文件的完整内容包含在对话中。
  </Step>

  <Step title="引用目录">
    ```text theme={null}
    @src/components 的结构是什么？
    ```

    这会提供包含文件信息的目录列表。
  </Step>

  <Step title="引用 MCP 资源">
    ```text theme={null}
    向我展示来自 @github:repos/owner/repo/issues 的数据
    ```

    这会使用 @server:resource 格式从已连接的 MCP 服务器获取数据。详情请参见 [MCP 资源](/docs/en/mcp#use-mcp-resources)。
  </Step>
</Steps>

<Tip>
  提示：

  * 文件路径可以是相对路径或绝对路径
  * 输入 `@` 以打开路径建议菜单，然后按 Enter 或 Tab 接受高亮显示的路径，再次按 Enter 发送消息
  * @ 文件引用会将文件目录及其父目录中的 `CLAUDE.md` 添加到上下文
  * 目录引用显示的是文件列表，而不是内容
  * 您可以在单个消息中引用多个文件（例如，“file1.js 和 file2.js”）
</Tip>

***

### 按计划运行 Claude

假设您希望 Claude 自动且定期地处理任务，例如每天早上审查打开的 PR、每周审计依赖项，或者在夜间检查 CI 失败情况。

根据您希望任务运行的位置选择一个计划选项：

| 选项                                                 | 运行位置                     | 最适用场景                                                                                                                                                                                                 |
| :----------------------------------------------------- | :-------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [例程](/docs/en/routines)                               | Anthropic 托管的基础设施  | 即使在您的计算机关闭时也应该运行的任务。除了计划外，还可以在 API 调用或 GitHub 事件时触发。在 [claude.ai/code/routines](https://claude.ai/code/routines) 配置。 |
| [桌面计划任务](/docs/en/desktop-scheduled-tasks) | 您的机器，通过桌面应用 | 需要直接访问本地文件、工具或未提交更改的任务。                                                                                                                             |
| [GitHub Actions](/docs/en/github-actions)                   | 您的 CI 管道                  | 与仓库事件（如打开的 PR）绑定的任务，或应该与您的工作流配置一起存在的 cron 计划。                                                                                            |
| [`/loop`](/docs/en/scheduled-tasks)                         | 当前的 CLI 会话           | 会话打开时的快速轮询。当您开始新对话时任务停止；`--resume` 和 `--continue` 恢复未过期的任务。                                                                 |

<Tip>
  在为计划任务编写提示时，请明确说明成功的标准以及对结果的处理方式。任务自动运行，因此无法提出澄清问题。例如：“审查带有 `needs-review` 标签的打开的 PR，对任何问题留下行内评论，并在 `#eng-reviews` Slack 频道中发布摘要。”
</Tip>

***

### 询问 Claude 关于它的功能

Claude 可以内置访问其文档，并且回答有关其自身功能和局限性的问题。

#### 示例问题

```text theme={null}
can Claude Code create pull requests?
```

```text theme={null}
how does Claude Code handle permissions?
```

```text theme={null}
what skills are available?
```

```text theme={null}
how do I use MCP with Claude Code?
```

```text theme={null}
how do I configure Claude Code for Amazon Bedrock?
```

```text theme={null}
what are the limitations of Claude Code?
```

<Note>
  Claude 为这些问题提供基于文档的回答。如需实践演示，请运行 `/powerup` 获取带有动画演示的互动课程，或参阅上文的具体工作流部分。
</Note>

<Tip>
  提示：

  * 无论您使用的是什么版本，Claude 始终可以访问最新的 Claude Code 文档
  * 提出具体问题以获得详细解答
  * Claude 可以解释诸如 MCP 集成、企业配置和高级工作流等复杂功能
</Tip>

***

## 恢复之前的对话

当一个任务跨越多次会话时，请从上次中断的地方继续，而不是重新解释背景。Claude Code 会在本地保存每一次对话。

```bash theme={null}
claude --continue
```

这将恢复当前目录中最近的会话；如果还没有会话，它会打印 `No conversation found to continue` 并退出。使用 `claude --resume` 从列表中进行选择，或者在正在运行的会话内部使用 `/resume`。有关命名、分支和完整选择器参考，请参见 [管理会话](/docs/en/sessions)。

## 使用工作树运行并行会话

在一个终端中开发功能，同时在另一个终端中由 Claude 修复 bug，且两者的编辑互不冲突。每个 [git worktree](https://git-scm.com/docs/git-worktree) 都是一个位于各自分支上的独立检出，是从现有的提交创建的，因此该仓库首先需要至少一次提交。

```bash theme={null}
claude --worktree feature-auth
```

在第二个终端中使用不同的名称运行相同的命令，以启动一个隔离的并行会话。在没有提交的仓库中，该命令会失败并显示 `Failed to resolve base branch "HEAD": git rev-parse failed`。参见 [Worktrees](/docs/en/worktrees) 以了解清理、`.worktreeinclude` 和非 git VCS 支持。要从单个屏幕而不是分散的 终端，参见 [后台代理](/docs/en/agent-view)。

## 编辑前规划

对于想要在写入磁盘前进行审查的更改，请切换到规划模式。Claude 会读取文件并提出计划，但在您批准之前不会进行任何编辑。当规划模式处于激活状态时，状态栏会显示 `⏸ plan mode on`。

```bash theme={null}
claude --permission-mode plan
```

您也可以在会话中途按 `Shift+Tab` 循环切换到规划模式。循环顺序为 `default` → `acceptEdits` → `plan`。有关审批流程以及在文本编辑器中编辑计划的信息，请参阅 [规划模式](/docs/en/permission-modes#analyze-before-you-edit-with-plan-mode)。

## 将研究委托给子智能体

探索大型代码库会因文件读取而填满您的上下文。将探索任务委托出去，这样就只会返回研究结果。

```text theme={null}
use a subagent to investigate how our auth system handles token refresh
```

子智能体在其自己的上下文窗口中读取文件并报告摘要。有关定义具有自身工具和提示词的自定义智能体，请参见 [Subagents](/docs/en/sub-agents)。

## 将 Claude 接入脚本

非交互式运行 Claude，用于 CI、pre-commit 钩子或批处理。标准输入和输出像任何 Unix 工具一样工作。

```bash theme={null}
git log --oneline -20 | claude -p "summarize these recent commits"
```

请参阅 [非交互式模式](/docs/en/headless) 以了解输出格式、权限标志和扇出模式。

## 后续步骤

<CardGroup cols={2}>
  <Card title="最佳实践" icon="lightbulb" href="/docs/en/best-practices">
    充分利用 Claude Code 的模式
  </Card>

  <Card title="管理会话" icon="rotate-left" href="/docs/en/sessions">
    恢复、命名和分支对话
  </Card>

  <Card title="工作树" icon="code-branch" href="/docs/en/worktrees">
    运行隔离的并行会话
  </Card>

  <Card title="扩展 Claude Code" icon="puzzle-piece" href="/docs/en/features-overview">
    添加技能、钩子、MCP、子代理和插件
  </Card>
</CardGroup>

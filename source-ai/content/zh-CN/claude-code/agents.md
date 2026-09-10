---
title: 并行运行代理
source_id: claude-code/agents
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/agents
owner: Anthropic
content_sha256: f1e18a3c16e99e639466660864faaa0c2e9166f80cd01406661bbd23110f8b39
translation_of: claude-code/agents
translation_model: gpt-5.6
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/agents)

Content owner: Anthropic

> ## 文档索引
> 在以下地址获取完整的文档索引：https://code.claude.com/docs/llms.txt
> 使用此文件可在深入探索之前发现所有可用页面。

# 并行运行代理

> 比较 Claude Code 同时承担多个任务的方式：子代理、代理视图、代理团队和动态工作流。

[子代理](/docs/en/sub-agents)、[代理视图](/docs/en/agent-view)、[代理团队](/docs/en/agent-teams)和[动态工作流](/docs/en/workflows)各自以不同方式并行处理工作。正确的选择取决于你是想亲自留在每个对话中、把任务交出去稍后再回来检查，还是让 Claude 为你协调一组工作者。

| 方式 | 它提供什么 | 适用场景 |
| :--- | :--- | :--- |
| [子代理](/docs/en/sub-agents) | 单个会话内的受委派工作者；它们在自己的上下文中执行辅助任务并返回摘要 | 某项辅助任务会让主对话充斥你之后不会再引用的搜索结果、日志或文件内容 |
| [代理视图](/docs/en/agent-view) | 用一个屏幕分派和监控后台运行的会话，通过 `claude agents` 打开。研究预览功能 | 你有多个独立任务，希望将其交出去、一眼查看状态，并且仅在某个任务需要你时介入 |
| [代理团队](/docs/en/agent-teams) | 由负责人管理的多个协同会话，具有共享任务列表和代理间消息传递功能。实验性功能，默认禁用 | 你希望 Claude 将项目拆分成多个部分、分配这些部分，并让各工作者保持同步 |
| [动态工作流](/docs/en/workflows) | 一个运行多个子代理并交叉检查其结果的脚本，适用于规模大到无法逐轮协调或需要多轮处理的工作 | 一项工作超出了少量子代理所能处理的规模，或者你希望让各项发现相互验证：全代码库审计、500 个文件的迁移、交叉核验的研究，或从多个角度起草的计划 |

在所有方式中，工作者都是 Claude 会话。若要引入其他工具，请将其作为 [MCP 服务器](/docs/en/mcp)提供给 Claude。

还有两个工具可以支持此类工作，但它们本身并不是运行代理的方式：

* [Worktree](/docs/en/worktrees) 为每个会话提供单独的 Git 检出，因此并行会话绝不会编辑相同文件。请将它们用于你亲自运行的会话。代理视图会自动把每个已分派会话移入各自的 worktree，你生成的子代理也可以各自获得一个 worktree。
* [`/batch`](/docs/en/commands) 是一个[技能](/docs/en/skills)，它会让 Claude 将一项大型更改拆分给 5 至 30 个由 worktree 隔离的子代理，每个子代理都会打开一个拉取请求。它是子代理与 worktree 的封装用法，而不是一种独立的协调方式。

另有一些功能可以在无需你驱动每个步骤的情况下运行 Claude，但它们解决的问题与跨代理拆分工作不同：

* [后台 Bash 命令](/docs/en/interactive-mode#background-bash-commands)会在不阻塞对话的情况下运行一条 shell 命令。它不会生成代理。
* [分叉子代理](/docs/en/sub-agents#fork-the-current-conversation)通过 `/subtask` 启动，是一种继承完整对话上下文而非从全新上下文开始的子代理。它是生成子代理的一种方式，而不是独立界面。若要将整个会话复制到一个并行运行的新[后台会话](/docs/en/agent-view#from-inside-a-session)，请使用 `/fork`。当[代理视图已关闭](/docs/en/agent-view#turn-off-agent-view)时，分叉子代理命令改为 `/fork`，且 `/subtask` 不可用。
* [例行任务](/docs/en/routines)会按计划在 Anthropic 云端运行会话，而不是在你的机器上并行运行。

<Note>
  同时运行多个会话或子代理会成倍增加令牌用量。有关用量和速率限制的详情，请参阅[成本](/docs/en/costs)。
</Note>

## 选择一种方式

正确的方式取决于由谁协调工作、工作者是否需要相互通信，以及它们是否会编辑相同文件：

* **由谁协调工作？**
  * Claude 在一个对话中进行委派并收集结果：[子代理](/docs/en/sub-agents)
  * 你交出独立任务，稍后回来检查：[代理视图](/docs/en/agent-view)
  * Claude 规划、分配并监督一组工作者：[代理团队](/docs/en/agent-teams)，实验性功能，默认禁用
  * 由脚本承载计划，而不是依靠 Claude 逐轮判断：[动态工作流](/docs/en/workflows)。请参阅[工作流与子代理及技能的比较](/docs/en/workflows#when-to-use-a-workflow)
* **工作者是否需要彼此交谈？** 子代理会将结果报告给生成它们的对话，而代理视图会话仅向你报告。代理团队中的队友共享任务列表，并彼此直接发送消息。
* **任务是否会触及相同文件？** 使用 [worktree](/docs/en/worktrees) 隔离工作。你亲自运行的各个子代理和会话都可以使用单独的 worktree。代理团队不会在 worktree 中隔离队友，因此请[划分工作](/docs/en/agent-teams#avoid-file-conflicts)，让每个队友拥有不同的一组文件。

## 检查正在运行的工作

检查正在运行的工作所使用的命令取决于你采用了哪种方式：

* 对于后台会话，`claude agents` 会打开[代理视图](/docs/en/agent-view)：一个显示每个会话、其状态以及哪些会话需要你输入的屏幕。
* 对于当前会话中的子代理，具名后台子代理会连同其状态显示在 @ 提及预输入列表中。{/* min-version: 2.1.198 */}从 v2.1.198 开始，`/agents` 不再打开面板；它会输出一条通知，指向子代理文件的位置。若要[创建和编辑自定义子代理](/docs/en/sub-agents#configure-subagents)，请让 Claude 操作或直接编辑文件。尽管名称相似，`/agents` 与 `claude agents` 是彼此独立的命令。
* 对于当前会话后台运行的任何内容，`/tasks` 会列出各个项目，并允许你检查、附加或停止它。列表还包括已经完成的子代理。
* 对于动态工作流，`/workflows` 会列出正在运行和已完成的执行、每次执行所处的阶段，以及已经完成的代理数量。

若要通过桌面界面查看所有会话，请参阅[桌面应用中的并行会话](/docs/en/desktop#work-in-parallel-with-sessions)。

## 了解更多

下面每篇指南分别介绍一种方式的设置与配置：

* [创建自定义子代理](/docs/en/sub-agents)：定义可复用的专家，并控制它们可以使用哪些工具。
* [使用代理视图管理代理](/docs/en/agent-view)：分派会话、监视其状态，并在某个会话需要你时附加到其中。
* [编排代理团队](/docs/en/agent-teams)：设置负责人和队友、分配任务，并审查它们的工作。
* [编排动态工作流](/docs/en/workflows)：运行打包的工作流，或让 Claude 编写一个运行多个子代理并让它们相互验证发现的工作流。
* [使用 worktree 运行并行会话](/docs/en/worktrees)：在隔离的检出中启动 Claude、控制要复制的内容，并在之后进行清理。

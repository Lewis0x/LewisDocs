---
title: 通过动态工作流大规模编排子代理
source_id: claude-code/workflows
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/workflows
owner: Anthropic
content_sha256: 06e085b51991299f0a9eff9f55cb60bc786d9c6fd464e77915cfd58c8f1b03b7
translation_of: claude-code/workflows
translation_model: k3
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/workflows)

Content owner: Anthropic

> ## 文档索引
> 获取完整的文档索引，地址：https://code.claude.com/docs/llms.txt
> 使用此文件可在进一步探索之前发现所有可用页面。

# 通过动态工作流大规模编排子代理

> 动态工作流通过 Claude 编写、你可以重复运行的脚本编排大量子代理。适用于代码库审计、大规模迁移和交叉验证的研究。

{/* plan-availability: feature=workflows plans=pro,max,team,enterprise providers=all */}

<Note>
  动态工作流需要 Claude Code v2.1.154 或更高版本，适用于所有付费计划，并支持 Anthropic API 访问，以及 Amazon Bedrock、Google Cloud 的 Agent Platform 和 Microsoft Foundry。在 Pro 计划中，可通过 `/config` 中的“Dynamic workflows（动态工作流）”行开启。
</Note>

动态工作流是一个大规模编排 [子代理](/docs/en/sub-agents) 的 JavaScript 脚本。Claude 会根据你描述的任务编写脚本，运行时（runtime）在后台执行该脚本，同时你的会话保持响应。

当任务所需的代理数量超出单个对话的协调能力，或当你希望将编排逻辑固化为可读、可重复运行的脚本时，就应使用工作流。典型例子包括全代码库范围的缺陷排查、500 个文件的迁移、需要将来源相互交叉核对的研究问题，以及在做出承诺之前从多个独立角度起草的复杂计划。

## 何时使用工作流

[子代理](/docs/en/sub-agents)、[技能](/docs/en/skills)、[代理团队](/docs/en/agent-teams) 和工作流都可以运行多步骤任务。区别在于谁掌握计划：

|                                 | 子代理                      | 技能                       | 代理团队                            | 工作流                            |
| :------------------------------ | :----------------------------- | :--------------------------- | :------------------------------------- | :----------------------------------- |
| 它是什么                      | Claude 派生的工作者         | Claude 遵循的指令  | 监督对等会话的主导代理 | 运行时执行的脚本        |
| 谁决定接下来运行什么      | Claude，逐轮决定           | Claude，遵循提示 | 主导代理，逐轮决定           | 脚本                           |
| 中间结果存放在哪里 | Claude 的上下文窗口        | Claude 的上下文窗口      | 共享任务列表                     | 脚本变量                     |
| 什么是可重复的               | 工作者定义          | 指令             | 团队定义                    | 编排本身             |
| 规模                           | 每轮几个委派任务 | 与子代理相同            | 少数几个长时间运行的对等代理        | 每次运行数十到数百个代理 |
| 中断处理                    | 重新开始该轮              | 重新开始该轮            | 团队成员继续运行                 | 可在同一会话中恢复        |

工作流将计划移入代码。使用子代理、技能和代理团队时，Claude 是编排者：它逐轮决定接下来派生或分配什么，每个结果都会进入上下文窗口。而工作流脚本自身持有循环、分支和中间结果，因此 Claude 的上下文中只保留最终答案。

将计划移入代码还让工作流能够应用可重复的质量模式，而不仅仅是运行更多代理：它可以让独立代理在结果汇报之前对抗性地审查彼此的发现，或从多个角度起草计划并相互权衡，从而让你获得比单次执行更可信的结果。

## 运行内置工作流

查看工作流实际效果的最快方法是运行 `/deep-research`,这是 [内置工作流](#bundled-workflows),Claude Code 自带它用于跨多个来源调查问题。你会看到代理在后台完成一组阶段,而你的会话保持空闲,最后得到一份报告,而不是逐回合的记录。

<Steps>
  <Step title="运行工作流">
    使用你想调查的问题运行 `/deep-research`。它会从多个角度展开网络搜索,获取并交叉核对其找到的来源,然后综合出一份带引用的报告。

    ```text theme={null}
    /deep-research What changed in the Node.js permission model between v20 and v22?
    ```
  </Step>

  <Step title="允许工作流">
    Claude Code 会询问是否允许该工作流。选择 **Yes** 继续。具体的提示取决于你的权限模式。有关各模式的选项,请参阅[在运行前批准计划](#approve-the-plan-before-it-runs)。
  </Step>

  <Step title="查看进度">
    运行在后台开始。运行 `/workflows`,使用方向键选择该运行,然后按 Enter 打开其进度视图:

    ```text theme={null}
    /workflows
    ```

    该视图显示每个阶段及其代理数量、令牌总数和已用时间。深入查看任何阶段可以看到其代理以及每个代理的发现。有关完整的控制集,请参阅[观察运行](#watch-the-run)。

    你也可以从输入框下方的任务面板查看:运行进行时,那里会出现一行进度摘要。按下箭头聚焦它,然后按 Enter 展开。
  </Step>

  <Step title="阅读报告">
    运行完成后,报告会出现在你的会话中。它引用了每条声明的来源,未能通过交叉核对的声明已被过滤掉。

    {/* min-version: 2.1.196 */}自 v2.1.196 起,当验证代理无法检查某条声明时(例如遇到速率限制或 API 错误后),报告会将该声明列为未验证,而不是计为被驳倒。
  </Step>
</Steps>

要为你自己的任务运行工作流,可以[让 Claude 编写一个](#have-claude-write-a-workflow),一旦某次运行达到了你的预期,你就可以将其[保存](#save-the-workflow-for-reuse)为你自己的命令。

### 内置工作流

Claude Code 包含 `/deep-research` 作为内置工作流:

| 命令                     | 功能描述                                                                                                                                                                                                                                                                                                                                                                              |
| :-------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/deep-research <question>` | 围绕一个问题从多个角度展开网络搜索,获取并交叉核对其找到的来源,对每条声明进行投票,并返回一份带引用的报告,其中未通过交叉核对的声明已被过滤掉。需要 [WebSearch 工具](/docs/en/tools-reference#websearch-tool-behavior) 可用 |

{/* min-version: 2.1.218 */}`/deep-research` 仅在你调用它时运行。在 v2.1.218 之前,Claude 也可以自行启动它。

你自己[保存的工作流](#save-the-workflow-for-reuse)会以同样的方式成为命令,并与内置命令一起出现在 `/` 自动补全中。

### 观察运行

工作流在后台运行，因此当代理工作时会话保持响应。随时运行 `/workflows` 列出正在运行和已完成的工作流，然后选择一个以打开其进度视图。

```text theme={null}
/workflows
```

进度视图显示每个阶段及其代理数量、令牌总数和已用时间。页脚列出每个操作的按键：

| 按键            | 操作                                                                                                                      |
| :------------- | :-------------------------------------------------------------------------------------------------------------------------- |
| `↑` / `↓`      | 选择一个阶段或代理                                                                                                     |
| `Enter` 或 `→` | 进入所选阶段，然后进入代理以读取其提示、最近的工具调用和结果                         |
| `Esc` 或 `←`   | 返回上一级。在 v2.1.203 到 v2.1.205 中，`←` 无法从阶段或代理中退出；在这些版本上使用 `Esc` |
| `j` / `k`      | 当代理详情溢出时在其中滚动                                                                            |
| `f`            | {/* min-version: 2.1.186 */}按状态筛选所选阶段中的代理列表。再次按下以循环                     |
| `p`            | 暂停或恢复运行                                                                                                     |
| `x`            | 停止所选代理，或当焦点在运行上时停止整个工作流                                                |
| `r`            | 重启选中的正在运行的代理                                                                                          |
| `s`            | [保存](#save-the-workflow-for-reuse)本次运行的脚本为命令                                                          |

## 让 Claude 编写工作流

你可以通过两种方式让 Claude 为你的任务编写工作流：

* [在提示中请求工作流](#ask-for-a-workflow-in-your-prompt)，用你自己的话表述或包含关键字 `ultracode`，Claude 就会为该任务编写一个工作流。
* [让 Claude 通过 ultracode 自行决定](#let-claude-decide-with-ultracode)：设置 `/effort ultracode` 后，Claude 会为会话中的每个实质性任务规划一个工作流。

你也可以运行已存在的工作流命令：[内置工作流](#bundled-workflows)（如 `/deep-research`），或你[保存过的](#save-the-workflow-for-reuse)工作流。

### 在提示中请求工作流

要在不改变会话努力级别的情况下将单个任务作为工作流运行，请在提示中包含关键字 `ultracode`。用你自己的话提出请求，例如“使用工作流”或“运行工作流”，同样有效：Claude 会将直接请求视为同等的启用方式。在 v2.1.160 之前，字面触发关键字是 `workflow`；自然语言请求在两个版本中均可使用。

```text theme={null}
ultracode: audit every API endpoint under src/routes/ for missing auth checks
```

Claude Code 会在你的输入中高亮显示该关键字，Claude 会为该任务编写工作流脚本，而不是逐轮处理。该关键字只决定 Claude 如何组织工作：以这种方式启动的工作流在会话现有的[权限模式](/docs/en/permission-modes)内运行，其代理的工具调用与会话中任何其他工具调用一样，接受相同的权限检查和[沙箱隔离](/docs/en/sandboxing)。

如果运行结果符合预期，之后你可以[将其保存为命令](#save-the-workflow-for-reuse)。如果你已经用其他方式构建了一个编排器，比如一个装满子代理提示词的文件夹，或者一个分发工作的技能，你可以让 Claude 查看它，并要求它生成一个实现相同功能的工作流。

#### 取消或关闭关键词

如果你并不是想启动一个工作流，在 macOS 上按 `Option+W`，或在 Windows 和 Linux 上按 `Alt+W` 即可取消此提示的高亮，或者在光标位于高亮关键词之后时按退格键。要完全阻止该关键词触发，请在 `/config` 中关闭 Ultracode 关键词触发。

#### 关键词在哪些场景生效

该关键词仅在由你亲自输入的提示中选择生效：在交互式提示符中、在 IDE 扩展面板中、在 [Remote Control](/docs/en/remote-control) 客户端中，或在将你的键盘输入的 [`origin`](/docs/en/agent-sdk/typescript#sdkmessageorigin) 标记为 `{ kind: "human" }` 的 Agent SDK 应用程序中。当它通过其他途径进入会话时，不会启动工作流：

* 通过 `-p` 传入的提示
* Agent SDK 应用程序发送的、未标记为人类输入的提示
* 定时任务提示
* 转发到会话中的 webhook 负载或拉取请求评论

<Note>
  在 v2.1.210 之前，该关键词也会从上述任何途径启动工作流，包括转发到会话中的 webhook 负载或拉取请求评论。
</Note>

### 让 Claude 通过 ultracode 自行决定

Ultracode 是一个 Claude Code 设置，它将 `xhigh` [推理努力级别](/docs/en/model-config#adjust-effort-level) 与自动工作流编排结合在一起。开启后，Claude 会为每个实质性任务规划一个工作流，而不是等你提出要求。

```text theme={null}
/effort ultracode
```

要在会话开始时就开启 ultracode，请使用 `claude --effort ultracode` 启动。需要 Claude Code v2.1.203 或更高版本。

开启 ultracode 后，由 Claude 决定任务何时需要一个工作流。一个请求可能连续演变成多个工作流：一个用于理解代码，一个用于做出更改，还有一个用于验证。这适用于会话中的每个任务，因此与较低的努力级别相比，每个请求会消耗更多 token 并花费更长时间。

Ultracode 在当前会话中持续生效，并在你开始新会话时重置。当你回到日常工作时，使用 `/effort high` 退回。它在支持 `xhigh` [努力级别](/docs/en/model-config#adjust-effort-level) 的模型上可用；在其他模型上，`/effort` 菜单不会提供该选项。

### 在运行前批准计划

在 CLI 中，每次运行的提示会显示计划的阶段以及以下选项：

* **是，运行它**：开始运行
* **是，并且在此项目中不再询问 `<name>` 的 `<path>`**：开始运行，并从此跳过此工作流在此项目中的此提示
* **查看原始脚本**：在决定前阅读脚本
* **否**：取消

`Ctrl+G` 会在你的编辑器中打开脚本。`Tab` 让你在运行开始前调整提示。

是否看到此提示取决于你的 [权限模式](/docs/en/permission-modes)：

| 权限模式                            | 何时提示你                                                                                                                                    |
| :----------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 默认、接受编辑                      | 每次运行，除非你已为此项目中的该工作流选择 **是，并且不再询问**                                                        |
| 自动                                       | 仅首次启动。任何 **是** 都会在你的用户设置中记录同意，之后的启动将不再提示。开启 ultracode 时完全跳过 |
| 绕过权限、`claude -p`、Agent SDK | 从不。运行会立即开始                                                                                                                       |

在桌面应用中，批准卡片会显示工作流名称、阶段列表和令牌用量警告，并提供 **一次**、**始终** 和 **拒绝** 操作。进度视图会显示在“后台任务”侧栏中。

你的权限模式仅控制上述启动提示。工作流生成的子代理始终以 `acceptEdits` 模式运行，并继承你的 [工具允许列表](/docs/en/settings#permission-settings)，无论你当前会话处于何种模式。文件编辑会自动批准。

不在允许列表中的 Shell 命令、网页获取和 MCP 工具仍可能在运行中途提示你。为避免长时间运行时出现这种情况，请在开始前将代理所需的命令加入允许列表。

在 `claude -p` 和 Agent SDK 中没有可提示的人，因此工具调用会遵循你配置的权限规则，而不会进行交互式确认。

### 保存工作流以供重用

当 Claude 为你会重复执行的任务编写工作流时,你可以将该次运行的脚本保存为命令。之后,诸如在每个分支上运行的审查之类的流程每次都会运行相同的编排。

运行 `/workflows`,选择你想要保留的运行,然后按 `s`。在保存对话框中,Tab 键在两个保存位置之间切换:

* `.claude/workflows/` 位于你的项目中:与克隆该仓库的所有人共享
* `~/.claude/workflows/` 位于你的主目录中:在每个项目中都可用,仅对你可见。如果你设置了 [`CLAUDE_CONFIG_DIR`](/docs/en/env-vars),则此位置为该路径下的 `workflows/` 目录。

{/* min-version: 2.1.208 */}保存对话框会显示个人位置的解析路径。在 v2.1.208 之前，即使设置了 `CLAUDE_CONFIG_DIR`，它也显示 `~/.claude/workflows/`；文件仍然保存在配置的目录下。

按 Enter 保存。此后,该工作流在任一位置的后续会话中都以 `/<name>` 运行。

{/* min-version: 2.1.216 */}Claude Code 在写入之前会检查保存位置是否存在符号链接,并在发现时显示错误而不是通过链接写入。检查内容取决于你保存的位置:

* 项目位置：如果 `.claude`、`.claude/workflows` 或目标文件是符号链接，Claude Code 会拒绝写入。
* 个人位置:Claude Code 仅当目标文件本身是符号链接时才拒绝写入,因此由 dotfiles 工具管理的 `~/.claude` 目录仍然可以正常工作。

在 v2.1.216 之前,Claude Code 会跟随链接,这可能会将文件放到你选择的位置之外。

{/* min-version: 2.1.178 */}在具有多个 `.claude/` 目录的 monorepo 中,你可以将工作流保存在它们适用的包旁边。自 v2.1.178 起,保存到项目位置会写入你的工作目录与仓库根目录之间已存在的最近的 `.claude/workflows/` 目录,如果尚不存在,则写入仓库根目录。项目工作流也会从该路径上的每个 `.claude/workflows/` 加载,当多个目录定义了相同名称时,Claude Code 会运行最接近工作目录的那个。

如果项目工作流和个人工作流同名,则运行项目工作流。

### 在插件中分发工作流

要跨团队或仓库共享工作流,请将其包含在 [插件](/docs/en/plugins) 中。将脚本放在插件根目录下的 `workflows/` 目录中,或者通过 [`workflows` 清单字段](/docs/en/plugins-reference#component-path-fields) 指向其他位置。

插件工作流以插件名称作为命名空间。名为 `acme-tools` 的插件中包含 `meta.name` 为 `release-audit` 的脚本时,将以 `/acme-tools:release-audit` 运行。

### 向已保存的工作流传递输入

已保存的工作流可以通过 `args` 参数接受输入。脚本将其作为名为 `args` 的全局变量读取。使用它可以在调用时提供研究问题、目标路径列表或配置对象,而不必为每次运行编辑脚本。

以下提示词使用一组问题编号列表运行已保存的工作流:

```text theme={null}
> Run /triage-issues on issues 1024, 1025, and 1030
```

Claude 会将该列表作为结构化数据传递,因此脚本可以直接对 `args` 调用数组和对象方法,而无需先解析。如果省略 `args`,脚本中的该全局变量为 `undefined`。

## 工作流提示词示例

当任务大到单个智能体的上下文无法容纳,或同一步骤需要在许多条目上运行时,工作流最为合适。下面的提示词展示了常见的模式。每个提示词都要求 Claude 为该任务编写并运行一个工作流;你不需要自己编写脚本。

### 针对同一问题审计多个文件

为每个文件分派一个智能体,然后收集并验证结果。

```text theme={null}
> use a workflow to audit every route handler under src/routes/ for missing authentication checks, and adversarially verify each finding before reporting it
```

### 持续修复直到检查通过

运行检查器,修复失败之处,并重复直到通过或不再有进展。

```text theme={null}
> use a workflow to run npx tsc --noEmit and keep fixing the reported errors until the type check passes or two rounds in a row make no progress
```

### 并行迁移多个文件

发现要迁移的文件，在隔离的副本中逐一转换以避免编辑冲突，并验证每个结果。

```text theme={null}
> use a workflow to migrate every component under src/components/ from styled-components to Tailwind, working on each file in its own isolated copy
```

### 审查每个变更文件并撰写一份摘要

为每个文件运行一个审查器，然后将所有发现交给一个代理进行排序和去重。

```text theme={null}
> use a workflow to review every file changed in this PR for correctness issues, then merge the per-file findings into one ranked summary
```

### 跨多个来源研究一个主题

让读者代理分散到更新日志、问题（issues）和文档中，然后进行综合分析。内置的 `/deep-research` 工作流就是这样做的；你也可以描述一个范围更窄的版本。

```text theme={null}
> use a workflow to research how our three competitors handle rate limiting: read their public docs and recent changelog entries in parallel, then compare the approaches
```

### 持续查找问题，直到列表不再增长

按轮次持续搜索，当新一轮没有新发现时停止。

```text theme={null}
> use a workflow to find flaky tests in this repo: run the suite repeatedly, record which tests fail intermittently, and stop once two rounds in a row find nothing new
```

### 保存的脚本长什么样

当你 [保存一个工作流](#save-the-workflow-for-reuse) 时，`.claude/workflows/` 中的文件包含一个 `meta` 块，随后是编排子代理的脚本主体。你通常不需要编辑它，但这里给出一个小型脚本的结构，以便你识别 Claude 生成的内容：

```javascript theme={null}
export const meta = {
  name: 'audit-routes',
  description: 'Audit every route handler for missing auth checks',
}

const found = await agent('List every .ts file under src/routes/.', {
  schema: { type: 'object', required: ['files'], properties: { files: { type: 'array', items: { type: 'string' } } } },
})

const audits = await pipeline(found.files, file =>
  agent(`Audit ${file} for missing authentication checks.`, { label: file }),
)

return audits.filter(Boolean)
```

脚本主体是带有顶层 `await` 的普通 JavaScript。`agent()` 生成一个子代理，`pipeline()` 则对列表中的每一项各运行一个子代理。如果你想手动编辑脚本，可以让 Claude 引导你完成更改，或参阅 [Agent SDK 参考](/docs/en/agent-sdk/typescript) 中的 Workflow 工具条目，了解完整的选项集。

## 工作流如何运行

工作流运行时在隔离的环境中执行脚本，与你的对话相互独立。中间结果保存在脚本变量中，而不会进入 Claude 的上下文。

每次运行都会将其脚本写入会话目录下 `~/.claude/projects/` 中的一个文件。运行开始时 Claude 会收到该路径，因此你可以向它询问。你可以打开该文件查看 Claude 编写的编排逻辑，将其与之前运行的脚本进行对比（diff），或编辑它并让 Claude 从编辑后的版本重新启动。

运行时会随着运行进度跟踪每个代理的结果，这正是使运行能够在同一会话中[可恢复](#resume-after-a-pause)的原因。

### 行为与限制

运行时应用以下约束：

| 约束                                                               | 原因                                                                                                          |
| :------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------- |
| 运行过程中不接受用户输入                                          | 只有代理权限提示可以暂停运行。如需在阶段之间进行确认，请将每个阶段作为独立的工作流运行 |
| 工作流本身不能直接访问文件系统或 shell                            | 由代理负责读取、写入和运行命令。脚本负责协调各代理                                        |
| 最多 16 个并发代理，CPU 核心数有限的机器上会更少                  | 限制本地资源使用                                                                                      |
| 每次运行总计最多 1,000 个代理                                     | 防止失控循环                                                                                         |

## 管理运行

运行开始后，你可以从 `/workflows` 视图进行管理，或展开输入框下方任务面板中的进度行进行管理。

### 暂停后恢复

如果你停止了一次运行，可以将其恢复：已完成的 agent 会返回其缓存结果，其余的则实时运行。在你停止时仍在运行的 agent 不会被保存，恢复时会重新开始，因此将工作分散到许多小型 agent 的工作流比单个长 agent 能保留更多进度。在 `/workflows` 中恢复暂停的运行：选中它并按 `p`，或者让 Claude 用相同的脚本重新启动该工作流。

恢复仅在同一个 Claude Code 会话内有效。如果你在工作流运行时退出 Claude Code，下一个会话会从头开始该工作流。

### 成本

工作流会生成许多 agent，因此单次运行所消耗的 token 可能明显多于在对话中完成同样的任务。运行会像其他会话一样计入你套餐的用量和速率限制。

为了在投入大型任务之前估算花费，先在一小部分上运行该工作流：用一个目录代替整个仓库，或用一个狭窄的问题代替宽泛的问题。`/workflows` 视图会在运行过程中显示每个 agent 的 token 用量，你可以随时在那里停止运行而不会丢失已完成的工作。运行时的 [代理数量上限](#behavior-and-limits) 限制单次运行可以生成的 agent 数量，从而为失控脚本的成本设定上限。要让运行使用更少的 agent，请选择 `small` [规模指导原则](#set-a-size-guideline)。

Claude Code 还会标记异常增大的运行。当工作流调度超过 25 个 agent，或其预计 token 总量超过 150 万时，输入框下方任务面板中的进度行会显示 `Large workflow` 警告。该警告会指引你前往 [`/workflows`](#watch-the-run)，在那里你可以停止运行。需要 Claude Code v2.1.203 或更高版本。

该警告仅是提示性的：它不会暂停或限制运行。有两个设置会改变你看到它的时机：

* 如果你自己选择了一个 [规模指导原则](#set-a-size-guideline)，其 agent 数量会取代 25 个 agent 的阈值。内置的默认准则将阈值保持在 25。
* 开启 [ultracode](#let-claude-decide-with-ultracode) 的会话不会显示该警告，因为开启 ultracode 本身就意味着你已选择接受大规模运行。

工作流中的每个 agent 都使用你会话的模型，除非脚本将某个阶段路由到不同的模型，或设置了 [`CLAUDE_CODE_SUBAGENT_MODEL`](/docs/en/model-config#environment-variables) 环境变量（该变量会覆盖前两者）。要控制模型成本：

* 如果你通常为日常工作切换到较小的模型，请在大型运行前检查 `/model`
* 在描述任务时，让 Claude 对不需要最强模型的阶段使用较小的模型

### 设置规模指导原则

规模指导原则告诉 Claude 在编写动态工作流时应以多少个代理为目标。Claude Code 将该指导原则作为建议而非上限发送给 Claude，因此要求不同规模的提示仍然会覆盖它。需要 Claude Code v2.1.202 或更高版本。

每个值对应一个代理数量：

| 值          | Claude 目标的代理数量                         |
| :------------- | :-------------------------------------------------- |
| `unrestricted` | 无指导原则：Claude 根据任务调整工作流规模 |
| `small`        | 少于 5 个代理                                 |
| `medium`       | 少于 15 个代理                                |
| `large`        | 少于 50 个代理                                |

{/* min-version: 2.1.219 */}默认值为 `medium`。在你选择某个值之前，`/config` 行显示 `medium (default)`，工作流的 `Running in background` 行显示 `medium size (/config)`。需要 Claude Code v2.1.219 或更高版本；更早版本默认为 `unrestricted`。

要更改该准则，请在 `/config` 中为“动态工作流大小”设置选择一个值，或运行 `/config workflowSizeGuideline=small`。 {/* min-version: 2.1.219 */}在 v2.1.219 及更高版本中，你还可以在任何设置文件中设置 [`workflowSizeGuideline` 键](/docs/en/settings#available-settings)；该值优先于 `/config`，并且当设置文件提供了该值时，Claude Code 会隐藏 `/config` 行。

更改将在下一个提示时生效。无论该设置如何，[运行时代理上限](#behavior-and-limits) 仍然适用。

### 关闭工作流

工作流在 CLI、桌面应用、IDE 扩展、[非交互模式](/docs/en/headless)（通过 `claude -p`）以及 [Agent SDK](/docs/en/agent-sdk/overview) 中均可用。相同的禁用设置适用于所有界面。

要为自己关闭工作流：

* 在 `/config` 中关闭“动态工作流”开关。跨会话持久生效。
* 在 `~/.claude/settings.json` 中设置 `"disableWorkflows": true`。跨会话持久生效。
* 设置 `CLAUDE_CODE_DISABLE_WORKFLOWS=1`。在启动时读取，因此在任何位置设置都会生效。

要为整个组织关闭工作流，请在 [托管设置](/docs/en/server-managed-settings) 中设置 `"disableWorkflows": true`，或使用 [Claude Code 管理员设置](https://claude.ai/admin-settings/claude-code) 页面上的开关。

当工作流被禁用时,捆绑的工作流命令将不可用,`ultracode` 关键字不再触发运行,并且 `ultracode` 会从 `/effort` 菜单中移除。

## 相关资源

* [并行运行代理](/docs/en/agents):比较子代理、代理视图、代理团队和工作流
* [创建自定义子代理](/docs/en/sub-agents):工作流所编排的执行者原语
* [管理成本](/docs/en/costs):多代理运行如何计入使用限额

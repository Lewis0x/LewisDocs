---
title: 配置权限
source_id: claude-code/permissions
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/permissions
owner: Anthropic
content_sha256: feb61445cd4ab2418f9ccb12ab198506705a93e5cddb1a7e2c9b1072a33e4b0e
translation_of: claude-code/permissions
translation_model: k3
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/permissions)

Content owner: Anthropic

> ## 文档索引
> 在以下地址获取完整的文档索引：https://code.claude.com/docs/llms.txt
> 在进一步探索之前，使用此文件来发现所有可用的页面。

# 配置权限

> 通过细粒度的权限规则、模式和托管策略，控制 Claude Code 可以访问什么以及可以做什么。

Claude Code 支持细粒度权限，因此你可以精确指定代理被允许做什么以及不允许做什么。权限设置可以提交到版本控制并分发给组织中的所有开发人员，也可以由各个开发人员自定义。

## 权限系统

Claude Code 使用分层权限系统来平衡能力与安全性：

| 工具类型           | 示例               | 是否需要批准                                                                        | "是，不再询问"行为                     |
| :---------------- | :--------------- | :---------------------------------------------------------------------------------- | :------------------------------------- |
| 只读               | 文件读取、Grep     | 否，在 [工作目录和附加目录](#working-directories) 内                     | 不适用                                 |
| Bash 命令          | Shell 执行         | 是，除了一组内置的 [只读命令](#read-only-commands)                          | 按仓库和命令永久生效                   |
| 文件修改           | 编辑/写入文件      | 是                                                                                  | 持续到会话结束                         |

当你选择"是，不再询问"且批准被永久保存时（例如对于 Bash 命令），Claude Code 会将规则保存到 git 仓库根目录下的 `.claude/settings.local.json`，并通过 [worktrees](/docs/en/worktrees) 解析到主检出目录。该规则适用于该仓库中任何位置的未来会话，包括在子目录和 worktree 中启动的会话。文件修改批准不会保存到文件：如表所示，它持续到会话结束。在 git 仓库之外，以及当仓库根目录是你的主目录时，Claude Code 会将规则保存在你启动它的目录中。

在 v2.1.211 之前，Claude Code 总是将规则保存在启动目录中，因此在 worktree 或子目录中授予的批准不适用于仓库的其他部分。早期版本保存在子目录或 worktree 中的规则仍适用于在那里启动的会话。

在 Bash 或 PowerShell 权限提示上，按 `Ctrl+E` 可显示命令的说明：它做什么、Claude 为什么运行它，以及可能出现什么问题，并标注为**低风险**、**中风险**或**高风险**。Claude Code 仅在你按 `Ctrl+E` 时，才会将命令以及 Claude 自己对该调用的描述发送给模型以生成说明，而不是在每个提示上都这样做。显示说明不会运行该命令；再次按 `Ctrl+E` 可隐藏它。

要关闭该快捷键，请在 [ 中将 `permissionExplainerEnabled`](/docs/en/settings#global-config-settings)`false` 设置为 `~/.claude.json`。

## 管理权限

您可以使用 Claude Code 查看和管理 `/permissions` 的工具权限。此 UI 列出所有权限规则以及每条规则所在的 `settings.json` 文件。

* **Allow** 规则允许 Claude Code 在无需手动批准的情况下使用指定工具。
* **Ask** 规则会在 Claude Code 尝试使用指定工具时提示确认。
* **Deny** 规则阻止 Claude Code 使用指定工具。

规则按以下顺序评估：先 deny，然后 ask，最后 allow。按此顺序的第一个匹配项决定结果，规则的特异性不会改变该顺序。

像 `Bash(aws *)` 这样的宽泛 deny 规则会阻止所有匹配的调用，包括同时也匹配更具体的 allow 规则（如 `Bash(aws s3 ls)`）的调用，因此 deny 规则不能携带允许列表例外。同样的优先级适用于 ask 和 allow 之间：即使存在更具体的 allow 规则匹配同一调用，匹配的 ask 规则仍会提示确认。

拒绝规则的行为取决于它们是命名一个工具还是在工具内限定一个模式。像 `Bash` 这样的裸工具名会将该工具从 Claude 的上下文中完全移除，因此 Claude 永远看不到它。裸名移除适用于除 [`EndConversation`](/docs/en/tools-reference#endconversation-tool-behavior) 之外的所有工具：只要还有其他工具存在，拒绝规则就无法移除它，而询问规则也永远不会为它弹出提示。像 `Bash(rm *)` 这样的限定规则会保留该工具可用，并在 Claude 尝试发起匹配的调用时将其阻止。

<Note>
  权限规则由 Claude Code 强制执行，而不是由模型执行。你的提示或 `CLAUDE.md` 中的指令会影响 Claude 尝试做什么，但不会改变 Claude Code 所允许的内容。要授予或撤销访问权限，请使用 `/permissions`、此处描述的规则、[权限模式](/docs/en/permission-modes)，或 [PreToolUse 钩子](#extend-permissions-with-hooks)。
</Note>

## 权限模式

Claude Code 支持多种权限模式，用于控制它如何批准工具调用。请参阅 [权限模式](/docs/en/permission-modes) 了解何时使用每种模式。在你的 [设置 中设置 `defaultMode` 文件](/docs/en/settings#settings-files):

| 模式                | 描述                                                                                                                                                                                                                                                                                                 |
| :------------------ | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `default`           | 标准行为：首次使用每个工具时提示请求权限。 {/* min-version: 2.1.200 */}在 CLI、VS Code 和 JetBrains 扩展以及桌面应用中标记为 Manual，并且 Claude Code 接受 `manual` 作为别名。该标签和别名需要 Claude Code v2.1.200 或更高版本。桌面应用的标签不取决于你的 CLI 版本            |
| `acceptEdits`       | 自动接受文件编辑和常见的文件系统命令，例如针对工作目录或 `mkdir` 中路径的 `touch`、`mv`、`cp` 和 `additionalDirectories`                                                                                                                                                                                                |
| `plan`              | Claude 读取文件并运行只读 shell 命令进行探索，但不编辑你的源文件；在 [auto 模式](/docs/en/permission-modes#eliminate-prompts-with-auto-mode) 可用时，经分类器批准的命令也会运行。在 CLI 和 VS Code 扩展中标记为 Plan                                                                                       |
| `auto`              | 自动批准工具调用，并通过后台安全检查验证操作与你的请求一致                                                                                                                                                                                                                                                                             |
| `dontAsk`           | 自动拒绝工具，除非通过 `/permissions` 或 `permissions.allow` 规则预先批准。`AskUserQuestion`、[你的组织设置为 `ask`](/docs/en/mcp#organization-controls-on-connector-tools) 的连接器工具，以及标记为 [`requiresUserInteraction`](/docs/en/mcp#require-approval-for-a-specific-tool) 的 MCP 工具，即使你已经允许也会被拒绝                   |
| `bypassPermissions` | 跳过权限提示，但由明确的 `ask` 规则强制的提示、[你的组织设置为 `ask`](/docs/en/mcp#organization-controls-on-connector-tools) 的连接器工具，以及标记为 [`requiresUserInteraction`](/docs/en/mcp#require-approval-for-a-specific-tool) 的 MCP 工具除外。诸如 `rm -rf /` 之类的根目录和主目录删除操作也仍会作为熔断机制提示 |

<Warning>
  `bypassPermissions` 模式会跳过权限提示，包括对 `.git`、`.config/git`、`.claude`、`.vscode`、`.idea`、`.husky`、`.cargo`、`.devcontainer`、`.yarn` 和 `.mvn` 的写入。仅在容器或虚拟机等隔离环境中使用此模式，因为这些环境中 Claude Code 不会造成损害。

  在此模式下仍有一些提示会触发。显式 `ask` 规则、连接器工具 [你的组织设置为 `ask`](/docs/en/mcp#organization-controls-on-connector-tools)，以及标记为 [`requiresUserInteraction`](/docs/en/mcp#require-approval-for-a-specific-tool) 的 MCP 工具仍会提示。针对的移除 文件系统根目录或主目录，例如 `rm -rf /` 和 `rm -rf ~`，也会触发提示，作为防止模型出错的熔断机制，{/* min-version: 2.1.208 */}包括命令中包含使用 `$(...)` 的命令替换时 或 反引号，或通过 `<(...)` 进行进程替换。在 v2.1.208 之前，只有普通形式（例如将 `rm -rf ~` 作为独立命令输入）才会触发提示；通过替换到达删除操作的命令则不会。
</Warning>

为防止使用 `bypassPermissions` 或 `auto` 模式，请将 `permissions.disableBypassPermissionsMode` 或 `permissions.disableAutoMode` 设置为 `"disable"`（在任意 [设置文件](/docs/en/settings#settings-files) 中）。这些在 [托管设置](#managed-settings) 中最有用 在它们不可能存在的地方 被重写。

## 权限规则语法

权限规则遵循 `Tool` 或 `Tool(specifier)` 的格式。

### 匹配工具的所有使用

要匹配工具的所有使用，仅使用不带括号的工具名称：

| 规则       | 效果                         |
| :--------- | :----------------------------- |
| `Bash`     | 匹配所有 Bash 命令      |
| `WebFetch` | 匹配所有网页获取请求 |
| `Read`     | 匹配所有文件读取         |

`Bash(*)` 等同于 `Bash`，匹配所有 Bash 命令。作为拒绝规则，两种形式都会将该工具从 Claude 的上下文中移除。

### 使用说明符进行细粒度控制

在括号中添加说明符以匹配特定的工具用法：

| 规则                           | 效果                                                   |
| :----------------------------- | :------------------------------------------------------- |
| `Bash(npm run build)`          | 匹配确切命令 `npm run build`                |
| `Read(./.env)`                 | 匹配读取当前目录中的 `.env` 文件 |
| `WebFetch(domain:example.com)` | 匹配对 example.com 的获取请求                    |

### 按输入参数匹配

拒绝和询问规则可以通过 `Tool(param:value)` 匹配任何工具的顶层输入参数。当 Claude 调用该工具且该参数被设置为该确切值时，规则即匹配。针对某个参数值的允许规则无法确立整个调用是安全的，因此允许规则继续使用各工具自己的说明符语法。这适用于工具接受的任何标量参数：

| 规则                           | 匹配内容                                      |
| :----------------------------- | :------------------------------------------- |
| `Agent(model:opus)`            | 请求 Opus 模型档位的 Agent 调用 |
| `Agent(isolation:worktree)`    | 请求 git worktree 的 Agent 调用      |
| `Bash(run_in_background:true)` | 在后台运行的 Bash 调用        |

参数匹配遵循以下规则：

* 参数名必须是工具输入的直接字段，例如 Agent 工具上的 `model`。嵌套在对象或数组内部的字段不可匹配
* 每条规则只命名一个参数。要同时基于 `model` 和 `isolation` 进行门控，请编写两条规则 `Agent(model:opus)` 和 `Agent(isolation:worktree)`，而不是将它们合并在一条规则中
* 值支持 `*` 作为通配符，可匹配任意字符序列，因此 `Agent(isolation:*)` 匹配任何显式的隔离值。不带 `*` 时匹配是精确的
* 模型省略的参数永远不会被匹配，因此 `Agent(model:*)` 不匹配未设置 `model` 的调用
* 该值会与 Claude 发送的字面输入进行比较，在任何规范化之前。`Agent(model:opus)` 匹配别名 `opus`，但不匹配完整的模型 ID。使用 [`--verbose`](/docs/en/cli-reference) 运行可查看每次工具调用中确切的参数名和值
* 冒号周围的空白会被忽略

工具已经通过其自身规范化规则匹配的字段不能以这种方式匹配：Bash 和 PowerShell 的 `command`，Read、Edit 和 Write 的 `file_path`，Grep 和 Glob 的 `path`，NotebookEdit 的 `notebook_path`，以及 WebFetch 的 `url`。像 `Bash(command:rm *)` 这样的规则可能被复合命令绕过，因此 Claude Code 会忽略它并发出启动警告。请改用 `Bash(rm *)`、`Read(./path)` 或 `WebFetch(domain:host)`。

### 通配符模式

Bash 规则支持带有 `*` 的 glob 模式。通配符可以出现在命令中的任何位置。此配置允许 npm 和 git commit 命令，同时阻止 git push：

```json theme={null}
{
  "permissions": {
    "allow": [
      "Bash(npm run *)",
      "Bash(git commit *)",
      "Bash(git * main)",
      "Bash(* --version)",
      "Bash(* --help *)"
    ],
    "deny": [
      "Bash(git push *)"
    ]
  }
}
```

`*` 前的空格很重要：`Bash(ls *)` 匹配 `ls -la` 但不匹配 `lsof`，而 `Bash(ls*)` 两者都匹配。`:*` 后缀是编写尾随通配符的等效方式，因此 `Bash(ls:*)` 与 `Bash(ls *)` 匹配相同的命令。

当你对某个命令前缀选择"是，不再询问"时，权限对话框会写入空格分隔形式。`:*` 形式仅在模式末尾被识别。在像 `Bash(git:* push)` 这样的模式中，冒号被视为字面字符，不会匹配 git 命令。

### 工具名称通配符

拒绝和询问规则也接受在工具名位置使用通配模式。该模式必须匹配完整工具名：`"*"` 匹配每个工具，`"mcp__*"` 匹配所有服务器中的每个 MCP 工具。被裸名通配拒绝规则匹配到的工具会从 Claude 的上下文中移除，效果与裸工具名相同，包括 [`EndConversation`](/docs/en/tools-reference#endconversation-tool-behavior) 例外：只要还存在任何其他工具，通配拒绝就不能移除它，而通配询问也永远不会为它弹出提示。此配置会拒绝每个 MCP 工具：

```json theme={null}
{
  "permissions": {
    "deny": [
      "mcp__*"
    ]
  }
}
```

允许规则只有在字面 `mcp__<server>__` 前缀之后才接受工具名通配符。服务器段必须不含通配符，以便该规则指向你配置的特定服务器。`mcp__puppeteer__*` 匹配来自 `puppeteer` 服务器的每个工具，`mcp__github__get_*` 匹配它的 `get_` 工具。未锚定的允许通配符，例如 `"*"`、`"B*"` 或 `"mcp__*"`，会被跳过并给出警告，且不会自动批准任何内容。

工具名不匹配任何已知工具的拒绝或询问规则会产生启动警告，以捕获拼写错误。包含 `_` 或 `*` 的工具名不受此检查约束。

工具在转录和权限对话框中显示的标签可能与其规范名称不同。例如，转录中标记为 `Stop Task` 的工具，其规范名称是 `TaskStop`。权限规则和 [钩子匹配器](/docs/en/hooks) 只匹配规范名称，因此写成 `Stop Task` 的规则不会匹配。对于拒绝和询问规则，上述启动警告会捕获这种不匹配。请使用 [工具参考](/docs/en/tools-reference) 中列出的规范名称。

## 特定工具的权限规则

### Bash

Bash 权限规则支持使用 `*` 进行通配符匹配。通配符可以出现在命令中的任何位置，包括开头、中间或结尾：

* `Bash(npm run build)` 匹配精确的 Bash 命令 `npm run build`
* `Bash(npm run test *)` 匹配以 `npm run test` 开头的 Bash 命令
* `Bash(npm *)` 匹配任何以 `npm ` 开头的命令
* `Bash(* install)` 匹配任何以 ` install` 结尾的命令
* `Bash(git * main)` 匹配像 `git checkout main` 和 `git log --oneline main` 这样的命令

单个 `*` 可匹配包括空格在内的任意字符序列，因此一个通配符可以跨越多个参数。`Bash(git *)` 匹配 `git log --oneline --all`，而 `Bash(git * main)` 既匹配 `git push origin main` 也匹配 `git merge main`。

当 `*` 出现在末尾且前面有一个空格时（如 `Bash(ls *)`），它会强制单词边界，要求前缀后面必须跟空格或字符串结尾。例如，`Bash(ls *)` 匹配 `ls -la`，但不匹配 `lsof`。相比之下，不带空格的 `Bash(ls*)` 同时匹配 `ls -la` 和 `lsof`，因为没有单词边界约束。

#### 复合命令

<Tip>
  Claude Code 能够识别 shell 运算符，因此像 `Bash(safe-cmd *)` 这样的规则不会授予它运行命令 `safe-cmd && other-cmd` 的权限。可识别的命令分隔符包括 `&&`、`||`、`;`、`|`、`|&`、`&` 以及换行符。规则必须独立匹配每个子命令。
</Tip>

当你以"是，不再询问"批准一个复合命令时，Claude Code 会为每个需要批准的子命令保存一条单独的规则，而不是为整个复合字符串保存一条规则。例如，批准 `git status && npm test` 会为 `npm test` 保存一条规则，因此无论 `npm test` 之前是什么内容，未来的 `&&` 调用都能被识别。像 `cd` 这样进入子目录的子命令会为该路径生成自己的 Read 规则。单个复合命令最多可保存 5 条规则。

<h4 id="process-wrappers">
  包装器
</h4>

在匹配 Bash 规则之前，Claude Code 会剥离一组固定的包装器，因此像 `Bash(npm test *)` 这样的规则也能匹配 `timeout 30 npm test`。被剥离的包装器包括 `timeout`、`time`、`nice`、`nohup` 和 `stdbuf`，以及 shell 内建命令 `command` 和 `builtin`，还有 zsh 的 `noglob`。它们各自将其参数作为实际命令运行。有两种相关形式不会被剥离：查询形式 `command -v`（它查找命令而非运行命令），以及 zsh 的 `nocorrect`。

Claude Code 还会剥离某些已知安全的环境变量的前导赋值，因此 `Bash(npm test *)` 可以匹配 `NODE_ENV=test npm test`。允许规则不会匹配越过任何其他变量的赋值。拒绝或询问规则可以匹配越过任何前导赋值，因此处于拒绝状态的 `Bash(rm *)` 仍能匹配 `FOO=bar rm -rf tmp/`。

裸用的 `xargs` 也会被剥离，因此 `Bash(grep *)` 可以匹配 `xargs grep pattern`。剥离仅在 `xargs` 不带任何标志时适用：像 `xargs -n1 grep pattern` 这样的调用会被作为 `xargs` 命令匹配，因此为内部命令编写的规则不涵盖它。

此包装器列表是内置的，不可配置。诸如 `direnv exec`、`devbox run`、`mise exec`、`npx` 和 `docker exec` 之类的开发环境运行器不在列表中。由于这些工具会将其参数作为命令执行，像 `Bash(devbox run *)` 这样的规则会匹配 `run` 之后的任何内容，包括 `devbox run rm -rf .`。要批准环境运行器内部的工作，请编写一条同时包含运行器和内部命令的具体规则，例如 `Bash(devbox run npm test)`。为每个你想允许的内部命令添加一条规则。

诸如 `watch`、`setsid`、`ionice` 和 `flock` 之类的 exec 包装器始终会提示，并且无法通过像 `Bash(watch *)` 这样的前缀规则自动批准。同样的情况也适用于带有 `find` 或 `-exec` 的 `-delete`：`Bash(find *)` 规则不涵盖这些形式。要批准特定的调用，请为完整命令字符串编写一条精确匹配规则。

#### 只读命令

Claude Code 内置识别一组 Bash 只读命令，并在每种模式下运行它们而无需权限提示。这些命令包括 `ls`、`cat`、`echo`、`pwd`、`head`、`tail`、`grep`、`find`、`wc`、`which`、`diff`、`stat`、`du`、`cd`，以及 `git` 的只读形式。该集合不可配置；如需对其中某个命令要求提示，请为其添加 `ask` 或 `deny` 规则。

对于那些所有标志均为只读的命令，允许使用未加引号的 glob 模式，因此 `ls *.ts` 和 `wc -l src/*.py` 运行时无需提示。

在以下情况下，该集合中的命令仍会提示：

* **带有可写标志的命令使用未加引号的 glob**：具有可写或可执行标志的命令，例如 `find`、`sort`、`sed` 和 `git`，在存在未加引号的 glob 时会提示，因为该 glob 可能展开为类似 `-delete` 的标志。
* **指向其他守护进程的 `docker`**：当命令带有选择不同守护进程的标志时，例如 `docker`、`-H`，或 Podman 的 `--context` 和 `--url`，`--connection` 的只读形式会提示。
* **带有路径打开标志的 `file`**：当 `file` 传递 `-m`/`--magic-file` 或 `-f`/`--files-from` 时会提示，因为这些标志会使 `file` 打开标志值中指定的路径。
* **Windows 上的网络路径**：如果命令的参数中包含网络（UNC）路径，例如 `\\server\share\file`，则会触发提示，因为访问网络路径可能会将你的 Windows 凭据发送到该路径所指的主机。同样的检查也适用于 [PowerShell 工具](/docs/en/tools-reference#powershell-tool) 命令。
* **分析无法解析的命令**: 当 Claude Code 无法完全解析某个命令时,它会请求批准,而不是将该命令视为只读。超过 10,000 个字符的命令总是会提示确认,因为它们超出了分析所能解析的范围。

进入工作目录内路径的 `cd` 或 [additional directory](#working-directories) 也是只读的，而像 `cd packages/api && ls` 这样的复合命令在每个部分各自符合条件时无需提示即可运行。有两种组合即使每个部分都是只读的也会提示：

* **`cd` 与 `git`**：当 `cd` 切换到不同的目录时进行提示，因为在新的目录中运行 `git` 可能会执行该目录的钩子。目标解析为当前工作目录的 `cd` 属于无操作，不会触发提示。
* **`cd` 与输出重定向**：当 Claude Code 无法确定重定向目标在 `cd` 运行后将针对哪个目录进行解析时进行提示。唯一的重定向目标为 `/dev/null` 的命令（例如 `cd app; grep -r pattern . 2>/dev/null`）不会提示，因为 `/dev/null` 不依赖于工作目录。

<警告>
  试图约束命令参数的 Bash 权限模式是脆弱的。例如,`Bash(curl http://github.com/ *)` 旨在将 curl 限制为 GitHub URL,但不会匹配如下变体:

  * URL 之前的选项：`curl -X GET http://github.com/...`
  * 不同的协议：`curl https://github.com/...`
  * 重定向：`curl -L http://short.example.com/xyz`，会重定向到 GitHub
  * 变量：`URL=http://github.com && curl $URL`
  * 多余的空格：`curl  http://github.com`

  为了获得更可靠的 URL 过滤，请考虑：

  * **限制 Bash 网络工具**：使用拒绝规则阻止 `curl`、`wget` 及类似命令，然后使用 WebFetch 工具并为允许的域名配置 `WebFetch(domain:github.com)` 权限
  * **使用 PreToolUse 钩子**：实现一个钩子，验证 Bash 命令中的 URL 并阻止不允许的域名
  * **添加 CLAUDE.md 指导**：在 `CLAUDE.md` 中描述你允许的 curl 模式。这会塑造 Claude 的行为尝试，但并不能强制划定边界，因此请将其与上述选项之一结合使用

  请注意，仅使用 WebFetch 并不能阻止网络访问。如果允许 Bash，Claude 仍然可以使用 `curl`、`wget` 或其他工具访问任何 URL。
</Warning>

### PowerShell

PowerShell 权限规则使用与 Bash 规则相同的形式。带有 `*` 的通配符可在任意位置匹配，`:*` 后缀等同于结尾的 ` *`，而单独的 `PowerShell` 或 `PowerShell(*)` 可匹配每条命令。此配置允许 `Get-ChildItem` 和 `git commit` 命令，同时阻止 `Remove-Item`：

```json theme={null}
{
  "permissions": {
    "allow": [
      "PowerShell(Get-ChildItem *)",
      "PowerShell(git commit *)"
    ],
    "deny": [
      "PowerShell(Remove-Item *)"
    ]
  }
}
```

常见别名在匹配前会被规范化。为 cmdlet 名称编写的规则同样匹配其别名，因此 `PowerShell(Get-ChildItem *)` 也会匹配 `gci`、`ls` 和 `dir`。匹配不区分大小写。

Claude Code 会解析 PowerShell AST，并独立检查复合命令中的每条命令。管道运算符 `|`、语句分隔符 `;`，以及在 PowerShell 7+ 中的链运算符 `&&` 和 `||`，会将复合命令拆分为子命令。规则必须匹配每个子命令，该复合命令才会被允许。

### 读取与编辑

`Edit` 规则适用于所有编辑文件的内置工具。Claude 会尽最大努力将 `Read` 规则应用于所有读取文件的内置工具（如 Grep 和 Glob）、应用于你提示中的 `@file` 提及，以及已连接的 [IDE](/docs/en/vs-code#the-built-in-ide-mcp-server) 与 Claude 共享的选区和打开文件上下文。

{/* min-version: 2.1.208 */}`Read` 拒绝规则也会阻止同一路径上的 [编辑工具](/docs/en/errors#file-is-covered-by-a-read-deny-rule)，包括在该路径创建新文件。Write 和 NotebookEdit 不在覆盖范围内，因此对于任何工具都不得更改的路径，请添加 `Edit` 拒绝规则。需要 Claude Code v2.1.208 或更高版本。

{/* min-version: 2.1.210 */}文件权限检查仅匹配 `Edit(path)` 和 `Read(path)` 规则。`Write(path)`、`NotebookEdit(path)` 或 `Glob(path)` 规则会被接受，但这些检查永远不会匹配它们，因此 Claude Code 会在启动时针对这些无法匹配形式中的每条允许、拒绝或询问规则发出警告。请使用 `Edit(docs/**)` 替代 `Write(docs/**)` 或 `NotebookEdit(docs/**)`，使用 `Read(docs/**)` 替代 `Glob(docs/**)`。没有路径的工具名称规则（例如针对 `Write` 的拒绝规则）不受影响：它在任何地方都匹配该工具，且不会产生警告。需要 Claude Code v2.1.210 或更高版本。

项目设置中的拒绝规则 `Write(docs/**)` 会产生以下启动警告：

```text theme={null}
Permission deny rule (.claude/settings.json): Write(docs/**) is not matched by file permission checks — only Edit(path) rules are. Use Edit(docs/**) instead (Edit rules cover all file-editing tools).
```

<Warning>
  读取与编辑拒绝规则适用于 Claude 的内置文件工具，以及 Claude Code 在 Bash 中识别出的文件命令，例如 `cat`、`head`、`tail` 和 `sed`。它们不适用于间接读写文件的任意子进程，例如自行打开文件的 Python 或 Node 脚本。如需在操作系统层面强制阻止所有进程访问某路径，请[启用沙箱](/docs/en/sandboxing)。
</Warning>

读取与编辑规则都使用 [gitignore](https://git-scm.com/docs/gitignore) 模式语法，包含四种不同的模式类型；对于单段目录模式，匹配深度还取决于规则类型，本节稍后会进行说明：

| 模式            | 含义                              | 示例                          | 匹配项                                          |
| ------------------ | ------------------------------------ | -------------------------------- | ------------------------------------------------ |
| `//path`           | 从文件系统根开始的绝对路径   | `Read(//Users/alice/secrets/**)` | `/Users/alice/secrets/**`                        |
| `~/path`           | 从主目录开始的路径             | `Read(~/Documents/*.pdf)`        | `/Users/alice/Documents/*.pdf`                   |
| `/path`            | 相对于设置来源的路径 | `Edit(/src/**/*.ts)`             | `<project root>/src/**/*.ts` 在项目设置中 |
| `path` 或 `./path` | 相对于当前目录的路径   | `Read(*.env)`                    | `<cwd>/*.env`                                    |

<Warning>
  像 `/Users/alice/file` 这样的模式不是绝对路径。单个前导斜杠锚定在设置来源处,而不是文件系统根。请使用 `//Users/alice/file` 表示绝对路径。
</Warning>

`/path` 模式锚定在与定义它的设置来源相关联的目录上,因此同一条规则会根据你放置的位置匹配不同的位置:

| 规则定义于                                 | `/path` 解析为        |
| :---------------------------------------------- | :------------------------- |
| 项目设置位于 `.claude/settings.json`     | `<project root>/path`      |
| 本地设置位于 `.claude/settings.local.json` | `<original cwd>/path`      |
| 用户设置位于 `~/.claude/settings.json`      | `~/.claude/path`           |
| 通过 `--settings <file>` 传递的文件          | `<directory of file>/path` |
| CLI 标志、`/permissions` 或会话规则     | `<original cwd>/path`      |

本地设置规则锚定在你启动 Claude Code 的目录,而不是在 v2.1.211 及更高版本中 Claude Code [存储文件](#permission-system) 的仓库根目录。在仓库根目录启动的会话中,这两个目录是相同的;在 [worktree](/docs/en/worktrees) 会话中,像 `Edit(/src/**)` 这样的共享规则匹配该 worktree 自己的 `src/` 目录。

用户设置中像 `Read(/secrets/**)` 这样的拒绝规则会阻止 `~/.claude/secrets/**`,而不是你项目中的 `secrets` 目录。要在用户设置中编写一条适用于每个项目内部的规则,请改用 `//` 绝对路径或 `~/` 主目录相对路径。

在 Windows 上,路径在匹配前会被规范化为 POSIX 形式。`C:\Users\alice` 会变成 `/c/Users/alice`,因此使用 `//c/**/.env` 可匹配该驱动器上任意位置的 `.env` 文件。要跨所有驱动器匹配,请使用 `//**/.env`。

示例:

* `Edit(/docs/**)`:编辑 `<project>/docs/` 中的文件,而不是 `/docs/` 或 `<project>/.claude/docs/`
* `Read(~/.zshrc)`:读取你主目录的 `.zshrc`
* `Edit(//tmp/scratch.txt)`:编辑绝对路径 `/tmp/scratch.txt`
* `Read(src/**)`:作为允许规则,仅从 `<current-directory>/src/` 读取;作为拒绝或询问规则,匹配当前目录下任意深度的 `src` 目录

规则只匹配其锚点之下的文件;在该范围内,匹配深度取决于模式的形状,以及对于单段目录模式而言的规则类型,如下所述。裸文件名遵循 gitignore 语义并在任意深度匹配,因此 `Read(.env)` 和 `Read(**/.env)` 是等效的:

| 拒绝规则                       | 阻止                                       | 不阻止                                       |
| ------------------------------- | -------------------------------------------- | ---------------------------------------------------- |
| `Read(.env)` 或 `Read(**/.env)` | 任何 `.env` 在当前目录或当前目录之下 | `.env` 在父目录或另一个项目中      |
| `Read(//**/.env)`               | 任何 `.env` 文件系统上的任何位置        | 无；规则锚定在文件系统根目录 |

仅包含单个目录段的相对模式，例如 `src/**`，会根据规则类型在不同深度匹配：

* **允许规则**：`Edit(src/**)` 仅匹配 `<cwd>/src` 及其下的文件。若要允许任意深度的某个目录名，请写成 `Edit(**/src/**)`。
* **拒绝和询问规则**：`Read(secrets/**)` 匹配当前目录下任意深度处名为 `secrets` 的目录，因此该规则也适用于嵌套的副本。

其他所有模式形式在每种规则类型中都在相同深度匹配：`Edit(/src/**)` 和 `Edit(src/components/**)` 仅在其锚定位置匹配，而 `Edit(**/src/**)` 在任意深度匹配。

以下示例展示了在一个包含顶级 `src/` 目录以及在 `vendor/` 下嵌套副本的项目中，各种模式形态的表现：

```text theme={null}
<current-directory>/
├── src/
│   └── app.ts
└── vendor/
    └── pkg/
        └── src/
            └── lib.js
```

| 规则                                 | 匹配 `src/app.ts` | 匹配 `vendor/pkg/src/lib.js` |
| :----------------------------------- | :------------------- | :------------------------------ |
| `Edit(src/**)` 作为允许规则      | 是                  | 否                              |
| `Edit(src/**)` 作为拒绝或询问规则 | 是                  | 是                             |
| `Edit(/src/**)` 在任何规则类型中     | 是                  | 否                              |
| `Edit(**/src/**)` 在任何规则类型中   | 是                  | 是                             |

<Note>
  在 gitignore 模式中，`*` 在单个路径段内匹配，可以出现在模式中的任何位置，而 `**` 则跨目录匹配。要允许所有文件访问，请仅使用不带括号的工具名称：`Read`、`Edit` 或 `Write`。
</Note>

当你对某个文件路径选择"是，不再询问"时，Claude Code 会转义该路径中的 gitignore 模式字符，例如 `[`、`]` 和 `*`，因此生成的规则只匹配你批准的字面路径。你自己编写的规则不会被转义。在 v2.1.202 之前，Claude Code 保存的是未转义的路径，因此为名为 `[2024-06] Reports` 的目录生成的规则可能无法匹配其自身路径，或匹配到意外的同级目录。

当 Claude 访问符号链接时，权限规则会检查两个路径：符号链接本身和它解析到的文件。允许规则和拒绝规则对这对路径的处理方式不同：允许规则会回退为向你提示，而拒绝规则则直接阻止。

* **允许规则**：仅当符号链接路径及其目标都匹配时才生效。位于允许目录内但指向该目录之外的符号链接仍会提示你。
* **拒绝规则**：当符号链接路径或其目标任一匹配时生效。指向被拒绝文件的符号链接本身也会被拒绝。

例如，当 `Read(./project/**)` 被允许且 `Read(~/.ssh/**)` 被拒绝时，位于 `./project/key` 并指向 `~/.ssh/id_rsa` 的符号链接会被阻止：其目标未通过允许规则，且匹配了拒绝规则。

### WebFetch

WebFetch 规则使用 `domain:` 前缀,并匹配所请求 URL 的主机名。匹配不区分大小写,支持 `*` 通配符,并且会从规则和主机名中去除末尾的 `.`,因此 `example.com.` 和 `example.com` 被视为相同。

* `WebFetch(domain:example.com)` 匹配对 `example.com` 的请求
* `WebFetch(domain:*.example.com)` 匹配任意深度的任何子域名,例如 `api.example.com` 或 `a.b.example.com`,但不匹配 `example.com` 本身
* `WebFetch(domain:*)` 匹配每个域名,等同于裸 `WebFetch` 规则

在除前导 `*.` 或裸 `*` 之外的任何位置,通配符仅匹配两个点之间的文本。`WebFetch(domain:example.*)` 匹配 `example.org`,其中 `*` 变为 `org`,但不匹配 `example.evil.com`,因为在这种情况下 `*` 必须变为 `evil.com` 并跨越一个点。这可以防止末尾通配符匹配攻击者可能注册的域名。

### MCP

MCP 规则使用在 Claude Code 中配置的服务器名称,可选地后跟该服务器的某个工具名称。

* `mcp__puppeteer` 匹配 `puppeteer` 服务器提供的任何工具
* `mcp__puppeteer__*` 使用通配符语法,同样匹配 `puppeteer` 服务器的所有工具
* `mcp__puppeteer__puppeteer_navigate` 匹配 `puppeteer_navigate` 服务器提供的 `puppeteer` 工具

如果你的组织已将某个 [claude.ai 连接器](/docs/en/mcp#organization-controls-on-connector-tools) 工具设置为 `ask`,那么针对该工具的允许规则不会生效:Claude Code 会在每次调用时提示,即使在 `auto` 和 `bypassPermissions` 模式下也是如此。在从不提示的 `dontAsk` 模式下,Claude Code 会改为拒绝该调用。连接器工具显示为 `mcp__claude_ai_<server>__<tool>`。

### Agent(子代理)

使用 `Agent(AgentName)` 规则来控制 Claude 可以使用哪些 [子代理](/docs/en/sub-agents):

* `Agent(Explore)` 匹配 Explore 子代理
* `Agent(Plan)` 匹配 Plan 子代理
* `Agent(my-custom-agent)` 匹配名为 `my-custom-agent` 的自定义子代理

将这些规则添加到设置中的 `deny` 数组,或使用 `--disallowedTools` CLI 标志来禁用特定代理。要禁用 Explore 代理:

```json theme={null}
{
  "permissions": {
    "deny": ["Agent(Explore)"]
  }
}
```

### Cd

`Cd` 规则控制 [`/cd` 命令](/docs/en/commands) 可以将会话移动到哪些目录。`Cd` 不是模型可调用的工具:Claude 无法调用它,这些规则仅在你自己运行 `/cd` 时生效。

一个不带参数的 `Cd` 拒绝规则会完全禁用 `/cd`。一个 `Cd(<path-pattern>)` 拒绝规则会阻止匹配的目标。拒绝规则会检查目标的每一种拼写形式,包括它解析过程中经过的每个符号链接跳转,因此为某条路径编写的规则也会阻止解析到该路径的目标。

添加任何 `Cd` 允许规则会将 `/cd` 切换为白名单模式：解析后的目标目录必须匹配你的其中一条允许规则，否则 `/cd` 将拒绝执行。在未配置任何 `Cd` 规则的情况下，`/cd` 保持其默认行为，并提示你信任不熟悉的目录。

路径模式共享 `//`、`~/` 和 `/` 锚点 从 [Read and Edit rules](#read-and-edit), 但匹配锚定到整个目录 路径而非 gitignore 风格。`*` 精确匹配一个路径段，`**` 跨段匹配。末尾的 `/**` 也匹配其命名的 根。

| 规则                  | 匹配项                                   | 不匹配项               |
| --------------------- | ----------------------------------------- | ---------------------------- |
| `Cd(~/code/*)`        | `~/code/app`                              | `~/code/app/src`, `~/code`   |
| `Cd(~/code/**)`       | `~/code` 及其下的任何目录       | `~/code` 之外的目录 |
| `Cd(**/node_modules)` | 任意深度的任何 `node_modules` 目录 | `node_modules/pkg`           |

## 使用钩子扩展权限

[Claude Code钩子](/docs/en/hooks-guide)允许你注册自定义 shell 命令，在运行时评估权限。当Claude Code发起工具调用时，PreToolUse 钩子会在权限提示之前运行，适用于除[`EndConversation`](/docs/en/tools-reference#endconversation-tool-behavior)之外的每个工具。钩子输出可以拒绝该工具调用、强制提示，或跳过提示以允许调用继续。

Hook 决策不会绕过权限规则。Claude Code 无论 PreToolUse hook 返回什么，都会评估 deny 和 ask 规则：匹配的 deny 规则会阻止调用，而匹配的 ask 规则即使 hook 返回了 `"allow"` 或 `"ask"` 也仍会提示。这保留了 deny 优先 优先级，如 [Manage permissions](#manage-permissions) 中所述，包括在托管设置中设定的拒绝规则。

连接器工具 [您的组织设置为 `ask`](/docs/en/mcp#organization-controls-on-connector-tools) 和标记的 MCP 工具 [`requiresUserInteraction`](/docs/en/mcp#require-approval-for-a-specific-tool) 也仍然 当钩子返回 `"allow"` 时进行提示。

阻止型钩子也优先于允许规则。以退出码 2 结束的钩子会在评估权限规则之前停止工具调用，因此即使某个允许规则本会让调用继续，阻止仍然生效。若想在无提示的情况下运行所有 Bash 命令、只阻止少数指定命令，请将 `"Bash"` 加入允许列表，并注册一个拒绝这些特定命令的 PreToolUse 钩子。有关可改编的钩子脚本，请参见 [阻止编辑受保护文件](/docs/en/hooks-guide#block-edits-to-protected-files)。

## 工作目录

默认情况下，Claude 可以访问你启动它时所在目录中的文件。你可以扩展此访问权限：

* **在启动时**：使用 `--add-dir <path>` CLI 参数
* **在会话期间**：使用 `/add-dir` 命令
* **持久化配置**：添加到 `additionalDirectories` 中的 [设置文件](/docs/en/settings#settings-files)

附加目录中的文件遵循与原始工作目录相同的权限规则：它们无需提示即可读取，文件编辑权限遵循当前的权限模式。

在 macOS 上的后台会话中，当 Claude 需要在受保护文件夹（例如 `~/Desktop`、`~/Documents` 和 `~/Downloads`）中读取或写入文件时，会话主机会独立于你的终端请求对这些文件夹的访问权限；如果读取失败并出现 `Operation not permitted`，请参阅[如何授予后台会话文件夹访问权限](/docs/en/agent-view#background-sessions-can’t-read-desktop-documents-or-downloads-on-macos)。

若要更改会话的主工作目录而不是添加另一个目录，请使用 [`/cd`](/docs/en/commands)。`/cd` 命令需要 Claude Code v2.1.169 或更高版本。与 `/add-dir` 不同，它会迁移会话：新目录的 `CLAUDE.md` 会被加载，并且 `--resume` 会从该目录中找到会话。

### 附加目录授予文件访问权限，而非配置

添加目录会扩展 Claude 可以读取和编辑文件的范围。它不会使该目录成为完整的配置根：大多数 `.claude/` 配置不会从附加目录中发现，但有少数类型会作为例外加载。

这些例外仅适用于使用 `--add-dir` 标志或 `/add-dir` 命令添加的目录。设置文件中 `permissions.additionalDirectories` 列出的目录仅授予文件访问权限，不加载以下任何配置。

以下配置类型会从 `--add-dir` 目录中加载：

| 配置                                                                         | 从 `--add-dir` 加载                                                                                                                                            |
| :------------------------------------------------------------------------------------ | :----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Skills](/docs/en/skills)，位于 `.claude/skills/`                                             | 是，支持实时重新加载                                                                                                                                              |
| [Subagents](/docs/en/sub-agents)，位于 `.claude/agents/`                                      | 是                                                                                                                                                                |
| [Settings](/docs/en/settings)，位于 `.claude/settings.json` 和 `.claude/settings.local.json` | 仅限 `enabledPlugins` 和 `extraKnownMarketplaces` 键                                                                                                            |
| [CLAUDE.md](/docs/en/memory) 文件、`.claude/rules/` 和 `CLAUDE.local.md`                | 仅当设置了 `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1` 时。`CLAUDE.local.md` 另外还需要 `local` 设置来源，默认情况下已启用 |

Claude Code 会从当前工作目录及其父目录、位于 `~/.claude/` 的用户目录以及托管设置中发现命令和输出样式。Hooks 和其他 `.claude/settings.json` 键从当前工作目录的 `.claude/` 文件夹加载,不存在父目录回退,同时还会加载你的用户级 `~/.claude/settings.json` 和托管设置。 {/* min-version: 2.1.211 */}`.claude/settings.local.json` 改为从 git 仓库根目录加载,即使你在子目录中启动 Claude Code 也是如此;在 v2.1.211 之前,它同样只从当前工作目录加载。 [Agent SDK](/docs/en/agent-sdk/claude-code-features#control-filesystem-settings-with-settingsources) 会话在所有版本中都是从工作目录加载它。

要在项目之间共享该配置,请使用以下方法之一:

* **用户级配置**:将文件放在 `~/.claude/agents/`、`~/.claude/output-styles/` 或 `~/.claude/settings.json` 中,使其在每个项目中都可用
* **插件**:将配置打包并分发为团队可以安装的 [插件](/docs/en/plugins)
* **从配置目录启动**:从包含所需 Claude Code 配置的目录运行 `.claude/`

## 权限如何与沙箱交互

权限和[沙箱](/docs/en/sandboxing)是互补的安全层:

* **权限**控制 Claude Code 可以使用哪些工具以及可以访问哪些文件或域。它们适用于 Bash、Read、Edit、WebFetch、MCP 以及所有其他工具,但拒绝或询问规则无法阻止 [`EndConversation`](/docs/en/tools-reference#endconversation-tool-behavior)(只要还有其他工具可用)。
* **沙箱**提供操作系统级别的强制约束,限制 Bash 工具的文件系统和网络访问。它仅适用于 Bash 命令及其子进程。

两者结合使用可实现纵深防御:

* 权限拒绝规则会阻止 Claude 甚至尝试访问受限资源
* 沙箱限制可阻止 Bash 命令访问定义边界之外的资源,即使提示注入绕过了 Claude 的决策
* 沙箱中的文件系统限制将 [`sandbox.filesystem`](/docs/en/sandboxing) 设置与 Read 和 Edit 拒绝规则相结合;两者都会合并到最终的沙箱边界中
* 网络限制将 WebFetch 权限规则与沙箱的 `allowedDomains` 和 `deniedDomains` 列表相结合

当你启用沙箱并将 `autoAllowBashIfSandboxed` 保留为默认值 `true` 时,即使你的权限包含裸 `Bash` 询问规则或[等效的 `Bash(*)` 形式](#match-all-uses-of-a-tool),沙箱化的 Bash 命令也会在不提示的情况下运行:沙箱边界替代了该整体工具提示。

在[计划模式](/docs/en/permission-modes#analyze-before-you-edit-with-plan-mode)中,Claude Code 会跳过此替代。如果没有询问规则,内置的只读命令仍会在不提示的情况下运行,而在你仍在规划时,任何其他 shell 命令都会提示请求批准{/* min-version: 2.1.218 */},或者在[自动模式](/docs/en/permission-modes#eliminate-prompts-with-auto-mode)可用且 `useAutoModeDuringPlan` 开启时交给分类器处理。如果存在裸 `Bash` 询问规则,每个 Bash 命令都会提示,包括沙箱化的只读命令,这与沙箱外的行为相同。在 v2.1.212 之前,该替代同样适用于计划模式。在 v2.1.212 至 v2.1.217 中,即使自动模式可用,这些命令也会提示。

以下检查仍然适用:

* 像 `Bash(git push *)` 这样的内容范围询问规则仍会强制提示
* 显式拒绝规则仍然适用
* 针对 `rm`、你的主目录或其他关键系统路径的 `rmdir` 或 `/` 命令仍会触发提示{/* min-version: 2.1.218 */},或在[自动模式](/docs/en/permission-modes#eliminate-prompts-with-auto-mode)下进行分类器检查;分类器路由需要 Claude Code v2.1.218 或更高版本

不会在沙箱中运行的命令(例如被排除的命令)照常遵循裸 `Bash` 询问规则。请参阅[沙箱模式](/docs/en/sandboxing#sandbox-modes)以更改此行为。

## 托管设置

对于需要对 Claude Code 配置进行集中控制的组织,管理员可以部署无法被用户或项目设置覆盖的托管设置。这些策略设置遵循与常规设置文件相同的格式,可以通过 MDM/操作系统级策略、托管设置文件、[服务器托管设置](/docs/en/server-managed-settings) 或自托管的 [Claude 应用网关](/docs/en/claude-apps-gateway) 进行交付。有关交付机制和文件位置,请参阅[设置文件](/docs/en/settings#settings-files)。

### 仅限托管的设置

以下设置仅从托管设置中读取。将它们放在用户或项目设置文件中不会产生任何效果。

| 设置                                          | 描述                                                                                                                                                                                                                                                                                                                                                                                                  |
| :--------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `allowAllClaudeAiMcps`                         | 当为 `true` 时,claude.ai 连接器会与已部署的 `managed-mcp.json` 一起加载,而不是被其独占控制所抑制。请参阅[托管 MCP 配置](/docs/en/managed-mcp)                                                                                                                                                |
| `allowedChannelPlugins`                        | 允许推送消息的频道插件白名单。设置后替换默认的 Anthropic 白名单。需要 `channelsEnabled: true`。请参阅[限制可运行的频道插件](/docs/en/channels#restrict-which-channel-plugins-can-run)                                                                                          |
| `allowManagedHooksOnly`                        | 当为 `true` 时,仅加载托管钩子、SDK 钩子以及来自在托管设置中强制启用的插件的钩子 `enabledPlugins`。用户、项目和所有其他插件钩子均被阻止                                                                                                                                              |
| `allowManagedMcpServersOnly`                   | 当为 `true` 时,仅尊重来自托管设置的 `allowedMcpServers`。`deniedMcpServers` 仍会从所有来源合并。请参阅[托管 MCP 配置](/docs/en/managed-mcp)                                                                                                                                                        |
| `allowManagedPermissionRulesOnly`              | 当为 `true` 时,阻止用户和项目设置定义 `allow`、`ask` 或 `deny` 权限规则。仅应用托管设置中的规则。不影响 MCP 服务器白名单;如需该功能,请设置 `allowManagedMcpServersOnly`                                                                                                  |
| `blockedMarketplaces`                          | 市场来源黑名单。被阻止的来源在下载前就会被检查,因此它们永远不会触及文件系统。请参阅[托管市场限制](/docs/en/plugin-marketplaces#managed-marketplace-restrictions)                                                                                                              |
| `channelsEnabled`                              | 允许该组织使用 [channels](/docs/en/channels)。各计划的默认设置请参阅 [enterprise controls](/docs/en/channels#enterprise-controls)                                                                                                                                                                                       |
| `disableSideloadFlags`                         | {/* min-version: 2.1.193 */}在启动时拒绝 `--plugin-dir`、`--plugin-url`、`--agents` 和 `--mcp-config` CLI 标志。如果不这样做，用户可以通过传递这些标志为单次运行绕过 `strictKnownMarketplaces`。请参阅 [`disableSideloadFlags`](/docs/en/settings#available-settings)。需要 Claude Code v2.1.193 或更高版本 |
| `forceRemoteSettingsRefresh`                   | 当 `true` 时，阻止 CLI 启动，直到远程托管设置被最新获取，如果获取失败则退出。请参阅 [fail-closed enforcement](/docs/en/server-managed-settings#enforce-fail-closed-startup)                                                                                                                              |
| `pluginTrustMessage`                           | 附加到安装前显示的插件信任警告中的自定义消息                                                                                                                                                                                                                                                       |
| `sandbox.filesystem.allowManagedReadPathsOnly` | 当 `true` 时，仅遵循来自托管设置的 `filesystem.allowRead` 路径。`denyRead` 仍会从所有来源合并                                                                                                                                                                                                        |
| `sandbox.network.allowManagedDomainsOnly`      | 当 `true` 时，仅遵从来自托管设置的 `allowedDomains` 和 `WebFetch(domain:...)` 允许规则。未被允许的域名会被自动阻止，而不提示用户。被拒绝的域名仍会从所有来源合并                                                                                                |
| `strictKnownMarketplaces`                      | 控制用户可以添加插件并从中安装插件的插件市场来源。请参阅[托管市场限制](/docs/en/plugin-marketplaces#managed-marketplace-restrictions)                                                                                                                                                  |
| `strictPluginOnlyCustomization`                | 阻止来自用户和项目来源的技能、代理、钩子和 MCP 服务器，使它们只能来自插件或托管设置。`true` 锁定全部四个界面；数组（如 `["skills", "hooks"]`）仅锁定指定的项。请参阅 [`strictPluginOnlyCustomization`](/docs/en/settings#strictpluginonlycustomization)             |
| `wslInheritsWindowsSettings`                   | 当 Windows HKLM 注册表项中设置了 `true` 或 `C:\Program Files\ClaudeCode\managed-settings.json` 时，WSL 除 `/etc/claude-code` 外，还会从 Windows 策略链读取托管设置。请参阅 [设置文件](/docs/en/settings#settings-files)                                                                                  |

`disableBypassPermissionsMode` 通常放置在托管设置中以强制执行组织策略，但它可以在任何作用域中生效。用户可以在自己的设置中设置它，以锁定自己无法使用绕过模式。

<Note>
  在 Team 和 Enterprise 套餐中，Owner 可启用或禁用 [Remote 控制](/docs/en/remote-control) 和 [Web 会话](/docs/en/claude-code-on-the-web) 全组织范围内在 [Claude Code 管理员 设置](https://claude.ai/admin-settings/claude-code)。此外，可以使用 [`disableRemoteControl`](/docs/en/settings#available-settings) 设置按设备禁用远程控制。Web 会话没有按设备的管理设置键。
您发送的内容似乎不完整（只有「</N」），无法确定需要翻译的文本。请提供完整的待翻译内容，我会按照要求逐行翻译并输出中文 Markdown。您好，您发送的「ote」似乎不完整。请提供需要翻译的完整文本，我会按照要求逐行翻译为中文 Markdown，并保持原有结构和占位符不变。>

## 设置优先级

权限规则遵循相同的 [settings precedence](/docs/en/settings#settings-precedence)，如同所有其他 Claude Code 设置：

1. **托管设置**：无法被任何其他级别覆盖，包括命令行参数
2. **命令行参数**：临时会话覆盖项
3. **本地项目设置**（`.claude/settings.local.json`）
4. **Shared project settings** (`.claude/settings.json`)
5. **User settings** (`~/.claude/settings.json`)

如果某个工具在任一级别被拒绝，其他级别都无法允许它。例如，托管设置中的拒绝不能被 `--allowedTools` 覆盖，而 `--disallowedTools` 可以在托管设置定义的范围内增加额外限制。

同样的规则也适用于各个设置作用域：如果用户设置允许某个权限而项目设置拒绝它，拒绝规则将阻止该权限。反过来也是如此：用户级别的拒绝会阻止项目级别的允许，因为在评估允许规则之前，会先评估来自任何作用域的拒绝规则。

嵌入宿主可以通过 SDK `managedSettings` 选项提供额外的托管策略，包括权限允许规则，除非管理员设置了 `allowManaged*Only` 锁；[Deliver policy to Claude Desktop sessions](/docs/en/claude-apps-gateway#deliver-policy-to-claude-desktop-sessions) 涵盖嵌入者策略何时适用。

## 项目允许规则与工作区信任

项目 `permissions.allow` 中的 `permissions.additionalDirectories` 规则和 `.claude/settings.json` 条目会授予能力，因此 Claude Code 仅在你接受该工作区的 [工作区信任对话框](/docs/en/security#additional-safeguards) 之后才应用它们。在此之前，Claude Code 会读取这些规则但不应用它们。信任对话框会列出该文件夹将授予的允许规则和附加目录，以便你在接受之前进行审查。`deny` 和 `ask` 规则不受影响，因为它们仅用于限制。

Claude Code 按工作区保存信任，以 git 仓库根目录为键；在仓库之外，则以你启动 Claude Code 时所在的目录为键。当你在主目录中启动时，信任仅对当前会话有效，不会写入磁盘；请参阅 [附加安全措施](/docs/en/security#additional-safeguards) 说明。信任父目录不会应用嵌套项目的允许规则。

`.claude/settings.local.json` 是你自己的文件，因此工作区信任检查通常不适用于它。当仓库可能提供了该文件时——例如它被提交到 git，或 `.claude` 是符号链接——其允许规则和附加目录会像项目设置一样经过信任检查。

Claude Code 会运行 git 来检查仓库是否提供了该文件，并且仅在接受的信任对话框所覆盖的文件夹（该文件夹或其某个父目录）中运行此检查。在尚未信任的文件夹中进行交互式会话时，`.claude/settings.local.json` 中的允许规则和附加目录会像项目设置一样经过信任检查，直到你接受该对话框，除非会话运行在你自己的配置主目录中（如下所述）。在下面两个例外中，只有配置主目录例外在对话框之前生效，因为它不需要运行 git。判断某个目录不在 git 仓库内使用的是同一个 git 检查，因此“不在仓库内”例外在覆盖该文件夹的信任对话框被接受后才生效。在 v2.1.207 之前，未被跟踪的 `.claude/settings.local.json` 会在你接受对话框之前就在该文件夹中应用其允许规则。

`.claude/settings.local.json` 中的允许规则和附加目录在两种情况下也无需工作区信任即可生效：

* 你启动 Claude Code 的目录不在 git 仓库内。
* 会话运行在你自己的配置主目录中：你的主目录，或任何你已将其 `.claude` 子目录设置为 [`CLAUDE_CONFIG_DIR`](/docs/en/env-vars) 的目录。

在这两种情况下，该文件都是你自己创建的，而非仓库可能提供的文件，并且仓库提交的 `.claude/settings.local.json` 仍然需要工作区信任。版本 2.1.196 至 2.1.199 在这些工作区中将该文件视为仓库提供的文件，忽略了其允许规则，并向 stderr 打印了一条 [`this workspace has not been trusted`](/docs/en/errors#workspace-has-not-been-trusted) 警告。上述两个例外与 v2.1.195 及更早版本一致，并在 v2.1.200 中恢复。

同样从 v2.1.200 开始，对于允许规则或附加目录仍未应用、但因父目录已被信任而从未显示信任对话框的工作区，会在你下次以交互方式启动 Claude Code 时显示该对话框。对话框提供两个选项：

* **是的，我信任此文件夹**：保存对该工作区的信任，并在同一会话中应用规则。
* **否，在没有这些权限的情况下继续**：继续工作但忽略这些规则。该对话框会在下次会话中再次出现。

在 [非交互模式](/docs/en/headless)（使用 `-p`）中，不会出现对话框，规则保持被忽略状态。

## 配置示例

此 [仓库](https://github.com/anthropics/claude-code/tree/main/examples/settings) 包含针对常见部署场景的入门设置配置。可将这些配置作为起点，并根据需要进行调整。

## 另请参阅

* [设置](/docs/en/settings)：完整的配置参考，包括权限设置表
* [配置自动模式](/docs/en/auto-mode-config)：告知自动模式分类器你的组织信任哪些基础设施
* [沙箱](/docs/en/sandboxing)：针对 Bash 命令的操作系统级文件系统和网络隔离
* [身份验证](/docs/en/authentication)：设置用户对 Claude Code 的访问权限
* [安全](/docs/en/security)：安全防护措施和最佳实践
* [钩子](/docs/en/hooks-guide)：自动化工作流并扩展权限评估

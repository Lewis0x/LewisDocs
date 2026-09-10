---
title: 调试你的配置
source_id: claude-code/debug-your-config
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/debug-your-config
owner: Anthropic
content_sha256: 1c0ad5e80406b44cca2b891bcf281eb306834a3d8182fc44ff7c4dd7e4f771d8
translation_of: claude-code/debug-your-config
translation_source: official
translation_url: https://code.claude.com/docs/zh-CN/debug-your-config
localization_sha256: 2b35544c4870e8f76285b1bd3d1ff14125a8765e5ed93878aae702ae69172d6e
---
本页采用内容所有者发布的官方简体中文版本，并与本站对应英文版本进行结构校验。

[官方中文来源](https://code.claude.com/docs/zh-CN/debug-your-config)

内容所有者: Anthropic

> ## Documentation Index
> Fetch the complete documentation index at: https://code.claude.com/docs/llms.txt
> Use this file to discover all available pages before exploring further.

# 调试你的配置

> 诊断为什么 CLAUDE.md、settings、hooks、MCP 服务器或 skills 没有生效。使用 /context、/doctor、/hooks 和 /mcp 来查看实际加载了什么。

当 Claude 忽略了一条指令或你配置的功能没有出现时，通常是因为文件没有加载、从你预期之外的位置加载，或者被另一个文件覆盖了。本指南展示了如何检查 Claude Code 实际加载了什么，以便你能够缩小范围。

对于安装、身份验证和连接问题，请参阅[故障排除安装和登录](/docs/zh-CN/troubleshoot-install)。

<h2 id="see-what-loaded-into-context">
  查看加载到上下文中的内容
</h2>

`/context` 命令显示当前会话中占用上下文窗口的所有内容，按类别分解：系统提示、内存文件、skills、自定义子代理及其加载源、MCP 工具和对话消息。首先运行它来确认你的 `CLAUDE.md`、规则或 skill 描述是否存在。

对于特定类别的详细信息，请使用专用命令：

| 命令               | 显示内容                                                                  |
| :--------------- | :-------------------------------------------------------------------- |
| `/memory`        | 加载了哪些 `CLAUDE.md` 和规则文件，加上自动内存条目                                      |
| `/skills`        | 来自项目、用户和插件源的可用 skills                                                 |
| `/hooks`         | 活跃的 hook 配置                                                           |
| `/mcp`           | 连接的 MCP 服务器及其状态                                                       |
| `/permissions`   | 当前生效的已解析允许和拒绝规则                                                       |
| `/doctor`        | 配置检查：安装健康状况、无效的设置文件、未使用的扩展、同一目录中重复的[子代理](/docs/zh-CN/sub-agents)名称，以及建议的修复 |
| `/debug [issue]` | 为会话启用调试日志记录，并提示 Claude 使用日志输出和设置路径进行诊断                                |
| `/status`        | 活跃的设置源，包括是否启用了托管设置                                                    |

如果内存文件在 `/memory` 中缺失，请根据[CLAUDE.md 文件如何加载](/docs/zh-CN/memory#how-claude-md-files-load)检查其位置。子目录 `CLAUDE.md` 文件在 Claude 使用 Read 工具读取该目录中的文件时按需加载，而不是在会话开始时加载。

如果 `/memory` 确认文件已加载但 Claude 仍然没有遵循特定指令，问题可能在于指令的编写方式，而不是是否加载。CLAUDE.md 适用于你会给新队友的指导类型，例如项目约定、构建命令和文件位置。

当指令足够模糊以至于可以多种方式解释、两个文件给出相互矛盾的方向，或者文件变得足够长以至于单个规则获得较少关注时，遵守度会下降。[编写有效的指令](/docs/zh-CN/memory#write-effective-instructions)涵盖了保持高遵守度的特异性、大小和结构模式。

<Note>
  CLAUDE.md 和权限解决不同的问题。CLAUDE.md 告诉 Claude 你的项目如何工作，以便它做出好的决定。[权限](/docs/zh-CN/permissions)和[hooks](/docs/zh-CN/hooks)无论 Claude 决定什么都强制执行限制。对于"我们在这里这样做"使用 CLAUDE.md。对于安全边界和任何必须永远不会发生的事情，使用权限或 hooks，你需要一个保证而不是指导。
</Note>

<h2 id="check-resolved-settings">
  检查已解析的设置
</h2>

设置在托管、用户、项目和本地范围内合并。当存在时，托管设置总是优先。在其余的中，更接近的范围按本地、项目、用户的顺序覆盖更广泛的范围。某些设置也可以由命令行标志或[环境变量](/docs/zh-CN/env-vars)设置，它们充当另一个覆盖层。当设置似乎不适用时，你设置的值通常被另一个范围或环境变量覆盖。

运行 `/doctor` 来检查你的配置和安装。它报告它发现的内容，包括无效的设置文件、重复的安装、未使用的扩展，以及 {/* min-version: 2.1.206 */}已检入的 `CLAUDE.md` 内容 Claude 可以从代码库中推导出来，然后提议仅在你确认后应用的修复。`CLAUDE.md` 修剪检查需要 Claude Code v2.1.206 或更高版本。在 v2.1.205 之前，`/doctor` 打开一个只读诊断屏幕，按 `f` 将报告发送给 Claude 来修复。

从终端，`claude doctor` 打印只读安装和设置诊断，而不启动会话。

运行 `/status` 来查看哪些设置源是活跃的，包括是否启用了托管设置。要了解给定键哪个范围优先，请参阅[范围如何交互](/docs/zh-CN/settings#how-scopes-interact)。

<h2 id="check-mcp-servers">
  检查 MCP 服务器
</h2>

运行 `/mcp` 来查看每个配置的服务器、其连接状态以及你是否为当前项目批准了它。服务器可以定义正确但仍然不提供工具，原因有几个常见的：

* `.mcp.json` 中的项目范围服务器需要一次性批准。如果提示被关闭，服务器将保持禁用状态，直到你从 `/mcp` 批准它。
* 启动失败的服务器在 `/mcp` 中显示为失败。`command` 或 `args` 中的相对文件路径是一个常见原因，因为它们相对于你启动 Claude Code 的目录而不是 `.mcp.json` 的位置进行解析。
* 显示为已连接但列出零个工具的服务器已成功启动但没有返回工具列表。从 `/mcp` 选择**重新连接**。如果计数保持为零，运行 `claude --debug mcp` 来查看服务器的 stderr 输出。

对于配置位置和范围规则，请参阅 [MCP](/docs/zh-CN/mcp)。

<h2 id="check-hooks">
  检查 hooks
</h2>

运行 `/hooks` 来列出当前会话注册的每个 hook，按事件分组。如果你定义的 hook 没有出现，它没有被读取：hooks 在设置文件中的 `"hooks"` 键下，而不是在独立文件中。

如果 hook 出现但没有触发，匹配器通常是原因。检查它是否有这些错误：

* `matcher` 字段是一个使用 `|` 来匹配多个工具名称的单个字符串，例如 `"Edit|Write"`。{/* min-version: 2.1.191 */}`,` 分隔符是等效的，所以 `"Edit,Write"` 匹配相同的工具。在 v2.1.191 之前，逗号会进入正则表达式评估，匹配器永远不会匹配，所以如果你不在 v2.1.191 上，请使用 `|`。
* 拼写错误的工具名称会产生一个不匹配任何内容的匹配器，所以 hook 会无声地失败。
* 数组值是一个 schema 错误：Claude Code 显示设置错误通知并拒绝整个用户、项目或本地设置文件，`claude doctor` 报告验证失败，该文件中没有 hook 出现在 `/hooks` 中。在[托管设置](/docs/zh-CN/settings#settings-files)中，只有无效条目被删除，文件的其他 hooks 仍然适用。

对 `settings.json` 的编辑在短暂的文件稳定延迟后在运行的会话中生效。你不需要重新启动。如果保存后几秒钟 `/hooks` 仍然显示旧定义，再次运行 `/hooks` 来刷新视图。

如果 `/hooks` 显示 hook 但它仍然没有触发，下一步是实时观察 hook 评估。使用 `claude --debug hooks` 启动会话并触发工具调用。调试日志记录每个事件、检查了哪些匹配器以及 hook 的退出代码和输出。有关日志格式，请参阅[调试 hooks](/docs/zh-CN/hooks#debug-hooks)，有关常见失败模式，请参阅[hooks 故障排除](/docs/zh-CN/hooks-guide#limitations-and-troubleshooting)。

<h2 id="test-against-a-clean-configuration">
  针对干净配置进行测试
</h2>

{/* min-version: 2.1.169 */}使用 [`claude --safe-mode`](/docs/zh-CN/cli-reference#cli-flags) 开始，它会启动一个会话，禁用所有自定义，包括 `CLAUDE.md`、skills、plugins、hooks、MCP 服务器以及自定义命令和代理。身份验证、模型选择、内置工具和权限正常工作。如果问题在安全模式下消失，则其中一个方面是原因；使用上面的针对性检查来找出是哪一个。安全模式仍然应用来自你的组织的托管 hooks 和设置策略。托管 plugins、skills、CLAUDE.md 和 MCP 服务器被关闭。

如果问题在安全模式下仍然存在，或你的设置本身可疑，请与从你的常规设置中不加载任何内容的会话进行比较。将 [`CLAUDE_CONFIG_DIR`](/docs/zh-CN/env-vars) 指向一个空目录以绕过 `~/.claude` 下的所有内容，并从没有 `.claude` 文件夹、`.mcp.json` 或 `CLAUDE.md` 的目录启动，以便也跳过项目配置。

```bash theme={null}
cd /tmp && CLAUDE_CONFIG_DIR=/tmp/claude-clean claude
```

干净会话没有用户或项目设置、hooks、MCP 服务器、plugins 或内存。

* 如果你的组织部署了托管设置，它们仍然适用，因为它们位于 `~/.claude` 之外的系统路径中
* 在 Linux 和 Windows 上，你将被提示再次登录，因为凭证存储在配置目录下
* 在 macOS 上，凭证在 Keychain 中，会转移到干净会话

如果问题在这里消失，原因在你的真实 `~/.claude` 或项目 `.claude` 文件中的某处。一次重新引入一个，通过将文件复制到临时目录或从你的项目启动，来找到哪一个。如果它在干净会话中持续存在，原因在你的用户和项目配置之外。运行 `/status` 来检查是否启用了托管设置，查找影响 Claude Code 的[环境变量](/docs/zh-CN/env-vars)，然后参阅[故障排除](/docs/zh-CN/troubleshooting)。

<h2 id="check-common-causes">
  检查常见原因
</h2>

大多数配置意外可以追溯到一小组位置和语法规则。在假设存在错误之前检查这些：

| 症状                                                  | 原因                                                                        | 修复                                                                                                                                                              |
| :-------------------------------------------------- | :------------------------------------------------------------------------ | :-------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Hook 永远不触发                                          | `matcher` 是 JSON 数组而不是字符串                                                 | 使用单个字符串，其中 `\|` 匹配多个工具，例如 `"Edit\|Write"`。请参阅[匹配器模式](/docs/zh-CN/hooks#matcher-patterns)。                                                                            |
| Hook 永远不触发                                          | `matcher` 在 v2.1.191 之前的版本中使用 `,` 作为分隔符                                   | {/* min-version: 2.1.191 */}Claude Code v2.1.191 或更高版本将 `,` 视为列表分隔符，如 `\|`。早期版本将逗号评估为字面字符，因此 `"Edit,Write"` 不匹配任何内容。改用 `\|`，或升级 Claude Code。                    |
| Hook 永远不触发                                          | `matcher` 值是小写的，例如 `"bash"`                                               | 匹配是区分大小写的。工具名称是大写的：`Bash`、`Edit`、`Write`、`Read`。                                                                                                                |
| Hook 永远不触发                                          | Hooks 在独立文件而不是 `settings.json` 中定义                                        | 项目或用户配置没有独立的 hooks 文件。在 `settings.json` 中的 `"hooks"` 键下定义 hooks。只有[plugins](/docs/zh-CN/plugins-reference#hooks)加载单独的 `hooks/hooks.json`。请参阅[hook 配置](/docs/zh-CN/hooks)。 |
| 全局设置的权限、hooks 或 env 被忽略                             | 配置被添加到 `~/.claude.json`                                                   | `~/.claude.json` 保存应用状态和 UI 切换。`permissions`、`hooks` 和 `env` 属于 `~/.claude/settings.json`。这是两个不同的文件。                                                            |
| `settings.json` 值似乎被忽略                              | 相同的键在 `settings.local.json` 中设置                                           | `settings.local.json` 覆盖 `settings.json`，两者都覆盖 `~/.claude/settings.json`。请参阅[设置优先级](/docs/zh-CN/settings#how-scopes-interact)。                                       |
| Skill 没有出现在 `/skills` 中                             | Skill 文件在 `.claude/skills/name.md` 而不是在文件夹中                               | 使用包含 `SKILL.md` 的文件夹：`.claude/skills/name/SKILL.md`。                                                                                                            |
| Skill 出现在 `/skills` 中但 Claude 从不调用它                 | Skill 在其 frontmatter 中有 `disable-model-invocation: true`，或其描述与你表述请求的方式不匹配 | 检查 `/skills` 中的徽章：一个"user-only"标签意味着 Claude 不会自动触发它。请参阅[skill 调用](/docs/zh-CN/skills)。                                                                               |
| 子目录 `CLAUDE.md` 指令似乎被忽略                             | 子目录文件按需加载，而不是在会话开始时加载                                                     | 它们在 Claude 使用 Read 工具读取该目录中的文件时加载，而不是在启动时，也不是在写入或创建文件时。请参阅[CLAUDE.md 文件如何加载](/docs/zh-CN/memory#how-claude-md-files-load)。                                           |
| 子代理忽略 `CLAUDE.md` 指令                                | 内置的 Explore 和 Plan 代理跳过 `CLAUDE.md`。自定义子代理以与主对话相同的方式加载它                   | 对于 Explore 或 Plan，在你的委派提示中重新陈述指令。对于自定义子代理，将关键指令放在代理文件体中，它成为代理的系统提示。请参阅[启动时加载的内容](/docs/zh-CN/sub-agents#what-loads-at-startup)。                                      |
| 清理逻辑在会话结束时永远不运行                                     | 没有配置 `SessionEnd` hook                                                    | 在 `settings.json` 中添加 `SessionEnd` hook。请参阅[hook 事件列表](/docs/zh-CN/hooks#hook-events)。                                                                               |
| `.mcp.json` 中的 MCP 服务器永远不加载                         | 文件在 `.claude/` 下或使用 Claude Desktop 的配置格式                                  | 项目 MCP 配置在存储库根目录下作为 `.mcp.json`，而不是在 `.claude/` 内。请参阅[MCP 配置](/docs/zh-CN/mcp)。                                                                                      |
| 在 `settings.json` 中的 `mcpServers` 下添加的 MCP 服务器永远不出现 | `settings.json` 不读取 `mcpServers` 键                                        | 在存储库根目录的 `.mcp.json` 中定义项目服务器，或运行 `claude mcp add --scope user` 来添加用户范围的服务器。请参阅[MCP 配置](/docs/zh-CN/mcp)。                                                            |
| 添加的项目 MCP 服务器没有出现                                   | 一次性批准提示被关闭                                                                | 项目范围的服务器需要批准。运行 `/mcp` 来查看状态并批准。                                                                                                                                |
| MCP 服务器从某些目录启动失败                                    | `command` 或 `args` 使用相对文件路径                                               | 对本地脚本使用绝对路径。你的 `PATH` 上的可执行文件如 `npx` 或 `uvx` 可以按原样工作。                                                                                                           |
| MCP 服务器启动时没有预期的环境变量                                 | 变量在 `settings.json` `env` 中，不会传播到 MCP 子进程                                 | 在 `.mcp.json` 中设置每个服务器的 `env`。                                                                                                                                  |
| `Bash(rm *)` 拒绝规则不阻止 `/bin/rm` 或 `find -delete`     | 前缀规则匹配字面命令字符串，而不是底层可执行文件                                                  | 为每个变体添加显式模式，或使用[PreToolUse hook](/docs/zh-CN/hooks-guide)或[sandbox](/docs/zh-CN/sandboxing)来获得硬保证。                                                                        |

<h2 id="related-resources">
  相关资源
</h2>

有关每个配置表面的完整参考，请参阅专用页面：

* **[`.claude` 目录参考](/docs/zh-CN/claude-directory)**：每个配置文件位置及其读取方式
* **[Settings](/docs/zh-CN/settings)**：优先级顺序和完整的键列表
* **[Hooks 参考](/docs/zh-CN/hooks)**：事件名称、有效负载和 `--debug hooks` 输出格式
* **[MCP](/docs/zh-CN/mcp)**：服务器配置、批准和 `/mcp` 输出
* **[故障排除安装和登录](/docs/zh-CN/troubleshoot-install)**：`command not found`、PATH 和身份验证问题
* **[故障排除](/docs/zh-CN/troubleshooting)**：性能、挂起和搜索问题

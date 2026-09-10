---
title: 通过屏幕阅读器使用 Claude Code
source_id: claude-code/accessibility
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/accessibility
owner: Anthropic
content_sha256: 59e2a48b9bd227f5e426e25f20bbf200231d58ed248aec5c21812c9017c8a64f
translation_of: claude-code/accessibility
translation_model: k3
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/accessibility)

Content owner: Anthropic

> ## 文档索引
> 获取完整的文档索引，地址为：https://code.claude.com/docs/llms.txt
> 使用此文件可在进一步探索之前发现所有可用的页面。

# 通过屏幕阅读器使用 Claude Code

> 为 VoiceOver 和 NVDA 等屏幕阅读器设置 Claude Code，以及屏幕放大器、减弱动态效果和色盲友好主题的设置。

Claude Code 具有屏幕阅读器模式，可将其可视化终端界面替换为纯线性文本。该模式不再使用方框、进度动画和原地重绘，而是打印带标签的行，由 VoiceOver 或 NVDA 等屏幕阅读器按顺序朗读，因此你可以进行完整对话、批准工具权限，并从头到尾查看输出。

屏幕阅读器模式是可选开启的。如果你使用的是屏幕放大器、减弱动态效果或色盲友好主题，而不是屏幕阅读器，请参阅 [屏幕阅读器模式之外的无障碍设置](#accessibility-settings-beyond-screen-reader-mode)。

<Note>
  屏幕阅读器模式需要 Claude Code v2.1.181 或更高版本。更早的版本会以 `--ax-screen-reader` 拒绝 `error: unknown option '--ax-screen-reader'` 标志。
</Note>

## 开启屏幕阅读器模式

根据你使用屏幕阅读器的频率选择相应的方法：

* 仅用于单个会话：运行 `claude --ax-screen-reader`。
* 用于从某个 shell 启动的会话：将 `CLAUDE_AX_SCREEN_READER` 环境变量设置为 `1`。在 Bash 或 Zsh 中，运行 `export CLAUDE_AX_SCREEN_READER=1`；在 PowerShell 中，运行 `$env:CLAUDE_AX_SCREEN_READER = "1"`。将该行添加到你的 shell 配置文件中，以覆盖所有 shell。
* 用于机器上的每个会话：将 `"axScreenReader": true` 添加到你的用户[设置文件](/docs/en/settings)中。这覆盖任何终端，包括 VS Code 集成终端。

<Note>
  这些方法按优先级顺序列出：[`--ax-screen-reader`](/docs/en/cli-reference#cli-flags) 标志会覆盖 [`CLAUDE_AX_SCREEN_READER`](/docs/en/env-vars) 环境变量，而环境变量又会覆盖 [`axScreenReader`](/docs/en/settings#available-settings) 设置。
</Note>

如果你通过 SSH 使用 Claude Code，请在运行 Claude Code 的远程机器上设置环境变量或设置项。

当该模式开启时，Claude Code 打印的第一行内容是确认信息，标明开启该模式的方法：`[Screen Reader Mode: on via flag]`、`[Screen Reader Mode: on via env]` 或 `[Screen Reader Mode: on via settings]`。方法命名格式需要 Claude Code v2.1.206 或更高版本。当 Claude Code 重新启动自身时（例如为了完成更新安装），新进程会通过 `CLAUDE_AX_SCREEN_READER` 环境变量继承该模式，因此无论你使用了哪种方法，其确认行都会显示 `[Screen Reader Mode: on via env]`。
{/* max-version: 2.1.205 */}更早的版本会打印 `[Accessible screen reader mode: on]`。

## 关闭屏幕阅读器模式

撤销开启该模式所用的方法：启动时不带该标志、取消设置环境变量，或将 `axScreenReader` 设置为 `false`。设置 `CLAUDE_AX_SCREEN_READER=0` 后，即使该设置为 `true`，模式也会保持关闭状态。

## 
屏幕阅读器听到的内容

在屏幕阅读器模式下，Claude Code 会输出扁平文本：

* 界面镶边不使用盒线绘制字符
* 不使用仅靠颜色的提示
* 不重绘未发生变化的内容；进度旋转指示器渲染为静态文本
* Claude 回复中的表格读作 `Header: value` 句子，而不是盒线字符网格。{/* min-version: 2.1.198 */}需要 Claude Code v2.1.198 或更高版本；更早版本即使在屏幕阅读器模式下也会把表格绘制成网格。

输出会累积在终端的回滚缓冲区中,因此你可以使用屏幕阅读器的审阅命令或终端的搜索功能重新阅读之前的对话回合。

屏幕阅读器模式呈现为纯滚动文本，即使您已开启 [fullscreen rendering](/docs/en/fullscreen) 使用 [`tui` 设置](/docs/en/settings#available-settings); 该设置在模式处于激活状态时无效. 已附加 后台会话仍以全屏方式渲染；参见 [已知限制](#known-limitations)。

转录中的每条消息都以一个标签开头，屏幕阅读器会朗读该标签，说明它是什么：你的消息、Claude 的回复、工具活动、错误和提示。这些标签也是可搜索的，因此你可以通过在终端的回滚缓冲区中搜索，在转录的各个部分之间跳转：

| 标签                  | 含义                                                                                   |
| :--------------------- | :---------------------------------------------------------------------------------------- |
| `you:`                 | 你的消息                                                                             |
| `claude:`              | Claude 的回复                                                                          |
| `tool:`                | 工具活动，例如文件编辑或命令运行                                       |
| `tool error:`          | 失败的工具                                                                        |
| `error:`               | 对话中的错误，例如失败的 API 请求                                |
| `Permission Required:` | 等待你回答的权限提示                                               |
| `Cost:`                | 当 Claude Code 退出时的会话费用摘要，如果你的账户 [显示费用](/docs/en/costs) |

终端光标跟随输入插入符，因此屏幕阅读器的“读取当前行”命令会用你正在编辑的提示来回答“我在哪里”。

{/* min-version: 2.1.218 */}当你在输入中删除一个单词或一行时，Claude Code 会播报被删除的文本。需要 Claude Code v2.1.218 或更高版本。播报内容涵盖：

* 使用 `Ctrl+W`、macOS 上的 `Option+Delete` 或 Windows 上的 `Ctrl+Backspace` 删除一个单词
* 使用 `Ctrl+U` 或 `Cmd+Backspace` 删除到行首
* 使用 `Ctrl+K` 删除到行尾

查看 [text editing shortcuts](/docs/en/interactive-mode#text-editing) 了解每个按键的作用。

{/* min-version: 2.1.210 */}循环切换 [permission modes](/docs/en/permission-modes) 使用 `Shift+Tab` 会宣告你当前所处的模式，例如 `[plan mode on]` 或 `[accept edits on]`。Claude Code 只打印一次该宣告，并且 不（doesn't 是 "does not" 的缩写形式，表示否定） 在后续重绘时重复执行。需要 Claude Code v2.1.210 或更高版本。

### 在对话轮次之间跳转

Claude Code 在轮次边界处发出 OSC 133 shell 集成标记，因此终端的“跳转到上一个提示符”快捷键可以在各轮次之间移动，而无需通读整个记录：

* iTerm2：Cmd+Shift+Up
* VS Code 终端：Windows 上为 Ctrl+Up，macOS 上为 Cmd+Up
* Windows Terminal：默认没有快捷键；在其设置中绑定 `scrollToMark` 操作
* Kitty 和 Ghostty：查看终端文档以了解其跳转到提示符的快捷键

macOS Terminal 不响应这些标记，而 Claude Code 在 WezTerm 中不会发出这些标记。在这些终端中，请改为在回滚缓冲区中搜索 `you:` 标签。

## 回答菜单和提示

在屏幕阅读器模式下，通常用方向键导航的菜单（包括权限提示）会变成编号列表。每个选项都会作为编号行朗读出来，随后是一个指明有效范围的 `Enter selection` 提示。输入你想要选项的编号，然后按 Enter。

* 要取消可关闭的菜单：按 Escape。其提示以 `or Escape to cancel` 结尾。
* 如果你输入了不在列表中的编号：Claude Code 会朗读有效范围并允许你重试。

是/否提示要求输入答案，而不是双选项菜单。输入 `y` 或 `n` 并按 Enter。`yes` 和 `no` 同样有效。

## 当 Claude Code 需要你时发出提示音

在屏幕阅读器模式下，Claude Code 在需要你注意时会响起终端铃声，因此你不必一直查看记录。铃声会在以下情况响起：

* Claude 完成回复
* 出现权限提示
* 运行超过 5 秒的工具完成

铃声是终端的标准提示音。要将其静音，请在终端应用程序中更改铃声设置。铃声不需要屏幕阅读器模式：在该模式之外，将 [`preferredNotifChannel`](/docs/en/settings#available-settings) 设置为 `"terminal_bell"`，即可在 Claude 等待你时获得类似的提示。请参阅[获取终端铃声或通知](/docs/en/terminal-config#get-a-terminal-bell-or-notification)。

## 屏幕阅读器模式之外的无障碍设置

这些选项满足屏幕阅读器模式之外的无障碍需求。它们全部可以与该模式同时使用。

* The `CLAUDE_CODE_ACCESSIBILITY` [环境变量](/docs/en/env-vars)用于屏幕放大器。设置 `CLAUDE_CODE_ACCESSIBILITY=1` 可保持原生终端光标可见，以便 macOS Zoom 等放大器能够跟踪光标位置。光标跟随键盘焦点：输入时的插入符号，以及使用方向键在菜单和面板（如 `/config` 和 `/plugin`）中移动时高亮的行。{/* min-version: 2.1.218 */}菜单和面板中的行跟踪需要 Claude Code v2.1.218 或更高版本。
* The `prefersReducedMotion` [设置](/docs/en/settings#available-settings)可减少或禁用旋转动画、微光效果和其他动画，而不改变界面的其余部分。
* The `theme` [设置](/docs/en/settings#available-settings)用于选择界面颜色，包括对色盲友好的 `dark-daltonized` 和 `light-daltonized` 主题。

## 已知限制

某些行为未适配屏幕阅读器模式：

* 屏幕阅读器运行时不会自动开启屏幕阅读器模式。
* Claude Code 不会宣布通过除使用 `Shift+Tab` 循环以外的任何方式进行的权限模式更改，例如从命令进入 [计划模式](/docs/en/permission-modes#analyze-before-you-edit-with-plan-mode)。
* 附加到 [后台会话](/docs/en/agent-view) 使用 `claude attach` 或从代理视图 进入终端的备用屏幕，该屏幕没有原生回滚。这与[相同行为 其他 附加会话](/docs/en/fullscreen)。要退出，请在空提示符处按左箭头键，如果对话框获得焦点则按 Ctrl+Z。
* Claude Code 在退出时打印的摘要中公布成本，而不是逐轮公布。
* 屏幕阅读器模式不会改变 [非交互模式](/docs/en/headless) 与 `-p` 标志。非交互模式已经输出纯文本，仍然是脚本编写的替代方案。

## 报告问题

如果您的屏幕阅读器、放大镜或终端出现问题，请在 [Claude Code issue 跟踪器](https://github.com/anthropics/claude-code/issues) 上提交 issue，并在标题中注明您使用的辅助技术。报告中请包含您的操作系统、终端应用程序以及辅助技术的名称和版本。

## 相关资源

以下页面包含本页所涵盖内容的完整参考条目及相关设置：

* [设置](/docs/en/settings#available-settings)：`axScreenReader`、`prefersReducedMotion`、`theme` 和 `preferredNotifChannel` 条目
* [环境变量](/docs/en/env-vars)：`CLAUDE_AX_SCREEN_READER` 和 `CLAUDE_CODE_ACCESSIBILITY` 条目
* [CLI 参考](/docs/en/cli-reference#cli-flags)：`--ax-screen-reader` 标志
* [终端配置](/docs/en/terminal-config)：屏幕阅读器模式之外的响铃、通知和主题
* [非交互模式](/docs/en/headless)：脚本化的 `claude -p` 运行，输出纯文本而不启用屏幕阅读器模式

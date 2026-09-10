---
title: 为 Claude Code 配置您的终端
source_id: claude-code/terminal-config
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/terminal-config
owner: Anthropic
content_sha256: 73c7bf8f7f11ef90619e3615626effe8fad8d2f2abcba2648e9af9b819443369
translation_of: claude-code/terminal-config
translation_model: k3
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/terminal-config)

Content owner: Anthropic

> ## 文档索引
> 获取完整的文档索引，请访问：https://code.claude.com/docs/llms.txt
> 在进一步探索之前，使用此文件可以发现所有可用的页面。

# 为 Claude Code 配置您的终端

> 修复换行符的 Shift+Enter，在 Claude 完成时获取终端提示音，配置 tmux，匹配颜色主题，并在 Claude Code CLI 中启用 Vim 模式。

Claude Code 可以在任何终端上无需配置即可工作。此页面适用于某些特定功能未按预期工作的情况。请在下方查找您的症状。如果一切都已经感觉正常，则不需要此页面。

* [Shift+Enter 提交而不是插入换行符](#enter-multiline-prompts)
* [Option 键快捷键在 macOS 上不起作用](#enable-option-key-shortcuts-on-macos)
* [Claude 完成时没有声音或提醒](#get-a-terminal-bell-or-notification)
* [您在 tmux 内运行 Claude Code](#configure-tmux)
* [显示闪烁或滚动缓冲区跳跃](#switch-to-fullscreen-rendering)
* [您想在提示词中使用 Vim 按键](#edit-prompts-with-vim-keybindings)

此页面是关于让您的终端向 Claude Code 发送正确的信号。要更改 Claude Code 本身响应的按键，请改为参阅 [快捷键](/docs/en/keybindings)。

## 输入多行提示

按下 Enter 键会提交你的消息。要在不提交的情况下换行，请按 Ctrl+J，或者输入 `\` 然后按 Enter。两者在任何终端中都可以直接使用，无需设置。

在大多数终端中，你也可以按 Shift+Enter，但具体支持情况因终端模拟器而异：

| 终端                                                                | Shift+Enter 换行                             |
| :---------------------------------------------------------------------- | :------------------------------------------ |
| Ghostty, Kitty, iTerm2, WezTerm, Warp, Apple Terminal, Windows Terminal | 无需设置即可使用                         |
| VS Code, Cursor, Devin Desktop, Alacritty, Zed                          | 运行 `/terminal-setup` 一次                  |
| gnome-terminal、JetBrains IDE（如 PyCharm 和 Android Studio）       | 不可用；使用 Ctrl+J 或 `\` 然后 Enter |

对于 VS Code、Cursor、Devin Desktop、Alacritty 和 Zed，`/terminal-setup` 会将 Shift+Enter 和其他键位绑定写入终端的配置文件中。首次运行时，你会看到类似于 `Installed VSCode terminal Shift+Enter key binding` 的确认信息。现有的绑定会保持原样；如果你看到类似于 `VSCode terminal Shift+Enter key binding already configured` 的消息，说明没有进行任何更改。请直接在宿主终端中运行 `/terminal-setup`，而不是在 tmux 或 screen 中运行，因为它需要写入宿主终端的配置。

在 VS Code、Cursor 和 Devin Desktop 中，`/terminal-setup` 还更新了两个编辑器设置：它将 `terminal.integrated.gpuAcceleration` 设置为 `"off"` 以防止集成终端中出现乱码，并设置 `terminal.integrated.mouseWheelScrollSensitivity` 以便在 [全屏模式](/docs/en/fullscreen) 中获得更平滑的滚动。要撤销 GPU 加速更改，请将其设置回 `"auto"` 并重新加载 编辑器窗口。

如果您在 tmux 内运行，即使外部终端支持，Shift+Enter 也需要 [下方的 tmux 配置](#configure-tmux)。

要将换行符绑定到不同的键，或者交换行为使 Enter 插入换行符而 Shift+Enter 提交，请在您的 [快捷键文件](/docs/en/keybindings) 中映射 `chat:newline` 和 `chat:submit` 操作。

## 在 macOS 上启用 Option 键快捷键

一些 Claude Code 快捷键使用 Option 键，例如 Option+Enter 换行或 Option+P 切换模型。在 macOS 上，大多数终端默认情况下不发送 Option 作为修饰键，因此在启用它之前，这些快捷键不起作用。此终端设置通常标记为“将 Option 键用作 Meta 键”；Meta 是 Unix 历史上对如今标记为 Option 或 Alt 的键的称呼。

<Tabs>
  <Tab title="Apple 终端">
    打开“设置” → “配置文件” → “键盘”，然后勾选“将 Option 键用作 Meta 键”。

    如果您接受了 Claude Code 的首次运行终端设置提示，则此操作已完成。该提示会为您运行 `/terminal-setup`，从而在您的 Apple 终端配置文件中启用 Option 作为 Meta 键，并关闭声音提示。

    {/* min-version: 2.1.211 */}在 [屏幕阅读器模式](/docs/en/accessibility)下，`/terminal-setup` 会保持提示音设置不变，因此终端提示音会保持可听状态。在 v2.1.211 版本之前，即使在屏幕阅读器模式下，`/terminal-setup` 也会关闭提示音。如果之前的运行关闭了提示音，请在“设置” → “配置文件” → “高级” → “声音提示”下将其重新打开。
  </Tab>

  <Tab title="iTerm2">
    打开“设置” → “配置文件” → “按键” → “常规”，然后将左 Option 键和右 Option 键设置为“Esc+”。

    在 iTerm2 中运行 `/terminal-setup` 会启用“设置” → “常规” → “选择”下的“终端中的应用程序可以访问剪贴板”，以便 `/copy` 命令可以写入您的系统剪贴板。即使是在 tmux 中运行，该命令也能检测到 iTerm2。重启 iTerm2 以使更改生效。
  </Tab>

  <Tab title="VS Code">
    将 `"terminal.integrated.macOptionIsMeta": true` 添加到您的 VS Code 设置中。
  </Tab>
</Tabs>

对于 Ghostty、Kitty 和其他终端，请在终端的配置文件中查找“将 Option 用作 Alt”或“将 Option 用作 Meta”的设置。

## 获取终端提示音或通知

当 Claude 完成任务或暂停以等待权限提示时，它会触发一个通知事件。将其显示为终端提示音或桌面通知，可以让您在运行长任务时切换到其他工作。

默认情况下，Claude Code 仅在 Ghostty、Kitty 和 iTerm2 中发送桌面通知。在其他终端中，请将 [`preferredNotifChannel`](/docs/en/settings#available-settings) 设置为 `"terminal_bell"` 以改为响铃终端提示音，或者配置 [通知钩子](#play-a-sound-with-a-notification-hook) 以播放自定义声音或运行命令。以下设置项可开启终端提示音：

```json ~/.claude/settings.json theme={null}
{
  "preferredNotifChannel": "terminal_bell"
}
```

桌面通知会通过 SSH 到达您的本地计算机，因此远程会话仍然可以提醒您。Ghostty 和 Kitty 无需进一步设置即可将其转发到您的操作系统通知中心。iTerm2 需要您启用转发功能：

<Steps>
  <Step title="打开 iTerm2 通知设置">
    转到“设置” → “配置文件” → “终端”。
  </Step>

  <Step title="启用提醒">
    勾选“通知中心提醒”，然后点击“过滤提醒”并启用“发送转义序列生成的提醒”。
  </Step>
</Steps>

如果通知仍然没有出现，请确认您的终端应用程序在操作系统设置中具有通知权限；并且如果您是在 tmux 中运行，请[启用穿透](#configure-tmux)。

### 使用通知钩子播放声音

在任何终端中，您都可以配置 [通知钩子](/docs/en/hooks-guide#get-notified-when-claude-needs-input)，以便在 Claude 需要您注意时播放声音或运行自定义命令。钩子是伴随内置通知运行而不是取代它，因此未接收到桌面通知的终端（例如 Warp 或 VS Code 集成终端）可以使用钩子或改为将 `preferredNotifChannel` 设置为 `"terminal_bell"`。

以下示例在 macOS 上播放系统声音。链接的指南提供了适用于 macOS、Linux 和 Windows 的桌面通知命令。

```json ~/.claude/settings.json theme={null}
{
  "hooks": {
    "Notification": [
      {
        "hooks": [{ "type": "command", "command": "afplay /System/Library/Sounds/Glass.aiff" }]
      }
    ]
  }
}
```

## 配置 tmux

当 Claude Code 在 tmux 内部运行时，默认会有两个问题：Shift+Enter 会提交而不是插入换行符，并且桌面通知和 [进度条](/docs/en/settings#available-settings) 永远无法到达外层终端。将这些行添加到 `~/.tmux.conf`，然后运行 `tmux source-file ~/.tmux.conf` 以将它们应用到正在运行的服务器：

```bash ~/.tmux.conf theme={null}
set -g allow-passthrough on
set -s extended-keys on
set -as terminal-features 'xterm*:extkeys'
```

`allow-passthrough` 行让通知和进度更新到达外层终端，而不是被 tmux 吞掉。`extended-keys` 行让 tmux 区分 Shift+Enter 和普通 Enter，从而使换行快捷键生效。

## 匹配颜色主题

使用 `/theme` 命令或 `/config` 中的主题选择器，选择与您的终端匹配的 Claude Code 主题。选择 auto 选项会检测您的终端是浅色还是深色背景，因此只要您的终端跟随操作系统的外观变化，主题也会随之改变。Claude Code 无法控制终端自身的配色方案，这由终端应用程序设置。

要自定义界面底部显示的内容，请配置一个 [自定义状态行](/docs/en/statusline)，用于显示当前模型、工作目录、git 分支或其他上下文。

### 创建自定义主题

<Note>
  自定义主题需要 Claude Code v2.1.118 或更高版本。
</Note>

除了内置预设之外，`/theme` 还会列出您已定义的任何自定义主题，以及已安装的 [插件](/docs/en/plugins-reference#themes) 提供的任何主题。在列表末尾选择 **New custom theme…** 以交互方式创建一个主题：您可以为主题命名，然后选择要覆盖的各个颜色令牌。当突出显示自定义主题时，按 `Ctrl+E` 对其进行编辑。

每个自定义主题都是 `~/.claude/themes/` 中的一个 JSON 文件。不带 `.json` 扩展名的文件名是主题的别名（slug），并且选择该主题会将 `custom:<slug>` 存储为您的主题首选项。该文件包含三个可选字段：

| 字段       | 类型   | 描述                                                                                                                                     |
| :---------- | :----- | :---------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`      | string | 在 `/theme` 中显示的标签。默认为文件名别名                                                                                  |
| `base`      | string | 主题起始的内置预设：`dark`、`light`、`dark-daltonized`、`light-daltonized`、`dark-ansi` 或 `light-ansi`。默认为 `dark` |
| `overrides` | object | 颜色令牌名称到颜色值的映射。此处未列出的令牌将回退到基础预设                                                |

颜色值接受 `#rrggbb`、`#rgb`、`rgb(r,g,b)`、`ansi256(n)` 或 `ansi:<name>`，其中 `<name>` 是 16 种标准 ANSI 颜色名称之一，例如 `red` 或 `cyanBright`。未知的令牌和无效的颜色值将被忽略，因此拼写错误不会破坏渲染。

以下示例定义了一个主题，它保留了深色预设，但重新着色了提示强调、错误文本和成功文本：

```json ~/.claude/themes/dracula.json theme={null}
{
  "name": "Dracula",
  "base": "dark",
  "overrides": {
    "claude": "#bd93f9",
    "error": "#ff5555",
    "success": "#50fa7b"
  }
}
```

Claude Code 会监视 `~/.claude/themes/`，并在添加或更改文件时重新加载，因此在编辑器中所做的编辑无需重启即可应用到正在运行的会话。如果 Claude Code 启动时 `~/.claude/themes/` 文件夹本身尚不存在，请在创建第一个主题文件后重启一次。之后，更改无需重启即可应用。

下面的参考涵盖了您可以在 `overrides` 中设置的令牌。`/theme` 中的交互式编辑器显示了相同的令牌并提供实时预览，此外还有一些此处省略的单用途强调色，例如引导屏幕颜色。

<Accordion title="颜色令牌参考">
  以下示例结合了下面几个组中的令牌：品牌强调色、计划模式边框、差异背景以及全屏消息背景。

  ```json ~/.claude/themes/midnight.json theme={null}
  {
    "name": "Midnight",
    "base": "dark",
    "overrides": {
      "claude": "#a78bfa",
      "planMode": "#38bdf8",
      "diffAdded": "#14532d",
      "diffRemoved": "#7f1d1d",
      "userMessageBackground": "#1e1b4b"
    }
  }
  ```

  #### 文本与强调色

  控制整个界面中使用的主要品牌强调色和前景文本色调。

  | 令牌         | 控制                                                         |
  | :------------ | :--------------------------------------------------------------- |
  | `claude`      | 主要品牌强调色，用于加载动画和助手标签   |
  | `text`        | 默认前景文本                                          |
  | `inverseText` | 绘制在彩色背景（如状态徽章）上的文本 |
  | `inactive`    | 次要文本，如提示、时间戳和禁用项     |
  | `subtle`      | 淡边框和弱化的次要文本                   |
  | `suggestion`  | 自动补全建议和选择器中的选中高亮      |
  | `permission`  | 对话框边框，包括权限提示和选择器         |
  | `remember`    | 记忆和 `CLAUDE.md` 指示器                                |

  #### 状态颜色

  在消息和指示器中传达成功、失败和警告状态。

  | 令牌     | 控制                                             |
  | :-------- | :--------------------------------------------------- |
  | `success` | 成功消息和通过的检查                  |
  | `error`   | 错误消息和失败                          |
  | `warning` | 警告、谨慎消息和自动模式边框 |
  | `merged`  | 合并的拉取请求状态                           |

  #### 输入框和模式指示器

  设置输入框边框颜色以及在权限模式或指示器激活时显示的强调色。

  | 令牌          | 控制                                           |
  | :------------- | :------------------------------------------------- |
  | `promptBorder` | 默认权限模式下的输入框边框    |
  | `planMode`     | 计划模式强调色和边框                        |
  | `autoAccept`   | 接受编辑模式的强调色和边框                |
  | `bashBorder`   | 输入 `!` shell 命令时的输入框边框 |
  | `ide`          | IDE 连接指示器                           |
  | `fastMode`     | 快速模式指示器                                |

  #### Diff 渲染

  为文件编辑和审查中添加和删除的代码着色。

  | 令牌               | 控制                                           |
  | :------------------ | :------------------------------------------------- |
  | `diffAdded`         | 已添加行的背景                          |
  | `diffRemoved`       | 已删除行的背景                        |
  | `diffAddedDimmed`   | 已添加行附近未更改上下文的背景   |
  | `diffRemovedDimmed` | 已删除行附近未更改上下文的背景 |
  | `diffAddedWord`     | 已添加行内的单词级高亮          |
  | `diffRemovedWord`   | 已删除行内的单词级高亮         |

  #### 全屏模式

  仅在 [全屏渲染模式](/docs/en/fullscreen) 中应用，其中消息具有背景填充。

  | 令牌                        | 控制                                                      |
  | :--------------------------- | :------------------------------------------------------------ |
  | `userMessageBackground`      | 对话记录中你的消息背后的背景             |
  | `userMessageBackgroundHover` | 悬停或展开时消息背后的背景         |
  | `bashMessageBackgroundColor` | 对话记录中 `!` shell 命令条目背后的背景 |
  | `memoryBackgroundColor`      | 对话记录中 `#` 记忆条目背后的背景        |
  | `selectionBg`                | 鼠标选中的文本背景                    |

  #### 使用量进度条和说话者标签

  调整 `/usage` 视图中显示的进度条以及区分你的消息和 Claude 的消息的标签。

  | 令牌              | 控制                                          |
  | :----------------- | :------------------------------------------------ |
  | `rate_limit_fill`  | 使用量进度条的已填充部分                 |
  | `rate_limit_empty` | 使用量进度条的未填充部分               |
  | `briefLabelYou`    | 你的消息上 `You` 标签的颜色         |
  | `briefLabelClaude` | 助手消息上 `Claude` 标签的颜色 |

  #### 微光变体和子代理颜色

  几个令牌具有成对的微光变体，提供用于加载动画的动画渐变中的较浅颜色。如果动画看起来不协调，请连同其基础令牌一起覆盖微光变体。

  * `claude` 和 `claudeShimmer`
  * `warning` 和 `warningShimmer`
  * `permission` 和 `permissionShimmer`
  * `promptBorder` 和 `promptBorderShimmer`
  * `inactive` 和 `inactiveShimmer`
  * `fastMode` 和 `fastModeShimmer`

  每个 [子代理](/docs/en/sub-agents) 和并行任务都以八种命名颜色之一显示，以便你在对话记录中区分它们。令牌名称遵循 `<color>_FOR_SUBAGENTS_ONLY` 模式，其中 `<color>` 为 `red`、`blue`、`green`、`yellow`、`purple`、`orange`、`pink` 或 `cyan`。覆盖这些令牌可更改每种命名颜色的外观。例如，定义中包含 `color: blue` 的子代理将使用 `blue_FOR_SUBAGENTS_ONLY` 值进行绘制。

  提示词输入中的 [`ultrathink`](/docs/en/model-config#use-ultrathink-for-one-off-deep-reasoning) 和 [`ultraplan`](/docs/en/ultraplan) 关键字以七色彩虹渐变渲染。令牌名称遵循模式 `rainbow_<color>` 和 `rainbow_<color>_shimmer`，其中 `<color>` 为 `red`、`orange`、`yellow`、`green`、`blue`、`indigo` 或 `violet`。
</Accordion>

## 切换到全屏渲染

在 [屏幕阅读器模式](/docs/en/accessibility)下，本部分不适用。Claude Code 总是渲染为纯滚动文本，除非在附加的 [后台会话](/docs/en/agent-view)中，如果你在任何其他会话中运行 `/tui fullscreen`，Claude Code 会打印一条说明，而不是进行切换。

如果 Claude 工作时显示器闪烁或滚动位置跳动，请切换到 [全屏渲染模式](/docs/en/fullscreen)。它会绘制到终端为全屏应用保留的独立屏幕上，而不是追加到你正常的滚动缓冲区中，这能保持内存占用稳定，并增加了用于滚动和选择的鼠标支持。在此模式下，你可以在 Claude Code 内部使用鼠标或 PageUp 进行滚动，而不是使用终端原生的滚动缓冲区；有关如何搜索和复制，请参见 [全屏页面](/docs/en/fullscreen#search-and-review-the-conversation)。

如果闪烁是唯一的问题，且你的终端支持同步输出但未被自动检测到（例如 Emacs `eat`），请设置 [`CLAUDE_CODE_FORCE_SYNC_OUTPUT=1`](/docs/en/env-vars) 以在不改变渲染器的情况下停止闪烁。

运行 `/tui fullscreen` 来切换并保存偏好设置。你的对话将完整重新加载，并且未来的会话将以全屏模式启动。你也可以在启动 Claude Code 之前设置 `CLAUDE_CODE_NO_FLICKER` 环境变量：

<CodeGroup>
  ```bash Bash and Zsh theme={null}
  CLAUDE_CODE_NO_FLICKER=1 claude
  ```

  ```powershell PowerShell theme={null}
  $env:CLAUDE_CODE_NO_FLICKER = "1"; claude
  ```

  ```json ~/.claude/settings.json theme={null}
  {
    "env": {
      "CLAUDE_CODE_NO_FLICKER": "1"
    }
  }
  ```
</CodeGroup>

## 粘贴大型内容

当你向提示词中粘贴超过 800 个字符或超过两行的内容时，Claude Code 会将输入折叠为诸如 `[Pasted text #1 +120 lines]` 的占位符，以保持输入框的可用性。提交时，完整内容仍会发送给 Claude。

VS Code 集成终端可能会在超大型粘贴内容到达 Claude Code 之前丢弃部分字符，因此在此类环境中建议优先使用基于文件的工作流。对于诸如整个文件或长日志等超大型输入，请将内容写入文件并让 Claude 读取，而不是直接粘贴。这能保持对话记录的可读性，并允许 Claude 在后续轮次中通过路径引用该文件。

## 使用 Vim 快捷键编辑提示词

Claude Code 包含一种用于提示词输入的 Vim 风格编辑模式。通过 `/config` → 编辑器模式启用它，或者在 `~/.claude/settings.json` 中将 [`editorMode`](/docs/en/settings#available-settings) 设置为 `"vim"`。将编辑器模式设置回 `normal` 以将其关闭。

Vim 模式支持 NORMAL（普通）和 VISUAL（可视）模式移动和操作符的一个子集，例如 `hjkl` 导航、`v`/`V` 选择，以及 `d`/`c`/`y` 与文本对象的组合。有关完整的按键表，请参见 [Vim 编辑器模式参考](/docs/en/interactive-mode#vim-editor-mode)。

Vim 移动无法通过快捷键文件重新映射。要将诸如 `jj` 的双键 INSERT（插入）模式序列映射为 Escape，请在你的用户设置中设置 [`vimInsertModeRemaps`](/docs/en/interactive-mode#remap-insert-mode-key-sequences)。

与标准 Vim 不同，在 INSERT 模式下按 Enter 仍会提交你的提示词。若要插入换行符，请在 NORMAL 模式下使用 `o` 或 `O`，或者使用 Ctrl+J。

## 相关资源

* [交互模式](/docs/en/interactive-mode)：完整的键盘快捷键参考和 Vim 按键表
* [快捷键](/docs/en/keybindings)：重新映射任何 Claude Code 快捷键，包括 Enter 和 Shift+Enter
* [全屏渲染](/docs/en/fullscreen)：全屏模式下滚动、搜索和复制的详细信息
* [钩子指南](/docs/en/hooks-guide)：更多适用于 Linux 和 Windows 的通知钩子示例
* [故障排除](/docs/en/troubleshooting)：修复终端配置之外的问题

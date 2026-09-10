---
title: 开发者设置
source_id: codex/ide/settings
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/ide/settings
owner: OpenAI
content_sha256: 7bb53ffe75ebb87dfe5ca4bbc0ba05b6e97a12ea300cc6749b3c3544f2189308
translation_of: codex/ide/settings
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/ide/settings)

Content owner: OpenAI

# 开发者设置

> 获取完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。通过在页面 URL 后附加 `.md` 可以获取文档页面的 Markdown 版本。

Codex IDE 扩展具有两个设置层：

- **Codex 设置**控制与 Codex CLI 共享的智能体行为，包括
  模型、推理工作量、权限、沙盒、MCP 服务器以及
  个性化。Codex 从 `config.toml` 读取这些设置。
- **编辑器设置**控制扩展在 VS Code 和
  兼容编辑器中的行为方式。这些设置使用编辑器的
  设置系统中的 `chatgpt.*` 键。

## 打开 Codex 设置

在 Codex 侧边栏中选择齿轮图标，然后选择 **Codex 设置**。使用
设置面板进行常见的智能体控制，或选择 **打开 config.toml** 以
直接编辑活动配置层。

有关配置层顺序和常见键，请参阅[配置
基础](https://learn.chatgpt.com/docs/config-file/config-basic)。有关支持的每个 `config.toml` 键，请参阅
[配置参考](https://learn.chatgpt.com/docs/config-file/config-reference)。

## 更改编辑器设置

要更改设置，请按照以下步骤操作：

1. 打开您的编辑器设置。
2. 搜索 `@ext:openai.chatgpt`、`Codex` 或设置名称。
3. 更新值。

该扩展还支持 Codex 聊天界面的 VS Code 内置聊天字体设置。

## 编辑器设置参考

| 设置                                          | 默认值         | 描述                                                                                                                                                                                                                                                                                 |
| -------------------------------------------- | -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `chatgpt.commentCodeLensEnabled`             | `true`         | 在 `TODO` 注释上方显示 CodeLens，以便 Codex 能够处理它们。                                                                                                                                                                                                                                       |
| `chatgpt.openOnStartup`                      | `false`        | 在扩展完成启动时聚焦 Codex 侧边栏。                                                                                                                                                                                                                                           |
| `chatgpt.followUpQueueMode`                  | `queue`        | 选择运行期间发送的消息是等待下一次运行 (`queue`) 还是引导当前运行 (`steer`)。扩展将旧有的 `interrupt` 值视为 `steer`。按 <kbd>Cmd</kbd>/<kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>Enter</kbd> 可反转单条消息的行为。 |
| `chatgpt.composerEnterBehavior`              | `enter`        | 选择 <kbd>Enter</kbd> 是否总是发送 (`enter`)，<kbd>Cmd</kbd>/<kbd>Ctrl</kbd>+<kbd>Enter</kbd> 发送多行提示 (`cmdIfMultiline`)，或者始终需要修饰键 (`cmdAlways`)。                                                                                                                                                |
| `chatgpt.reviewDelivery`                     | `inline`       | 尽可能在当前聊天中运行 `/review` (`inline`) 或启动单独的审查聊天 (`detached`)。                                                                                                                                                                                                                               |
| `chatgpt.localeOverride`                     | 自动           | 为 Codex UI 设置首选语言。留空以自动检测。                                                                                                                                                                                                       |
| `chatgpt.runCodexInWindowsSubsystemForLinux` | `false`        | 仅限 Windows：当 WSL 可用时在 WSL 中运行 Codex。当您的代码库和工具位于 WSL2 中，或者您需要 Linux 原生工具时使用此选项。更改此设置将重新加载 VS Code。                                                                                               |
| `chatgpt.cliExecutable`                      | 未设置          | 仅限开发：设置 Codex CLI 可执行文件的路径。除非您正在开发 Codex CLI，否则不需要此设置；手动覆盖捆绑的可执行文件可能会导致扩展的某些部分无法工作。                                                                |
| `chat.fontSize`                              | 编辑器默认值 | 控制 Codex 侧边栏中的聊天文本，包括聊天内容和编写器。                                                                                                                                                                                                           |
| `chat.editor.fontSize`                       | 编辑器默认值 | 控制 Codex 聊天中代码渲染的内容，包括代码片段和差异。                                                                                                                                                                                                           |

上述 `chatgpt.*` 键属于 IDE 扩展，不放入
`config.toml`。对于共享的智能体设置，请使用 [配置
基础](https://learn.chatgpt.com/docs/config-file/config-basic)，[高级配置](https://learn.chatgpt.com/docs/config-file/config-advanced)，
以及 [配置参考](https://learn.chatgpt.com/docs/config-file/config-reference)。

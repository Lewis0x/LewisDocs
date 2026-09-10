---
title: 故障排除
source_id: codex/reference/troubleshooting
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/reference/troubleshooting
owner: OpenAI
content_sha256: f081cd8867de652c0bcd189461c1e5c60075e7203517f05670fc4c953318b24d
translation_of: codex/reference/troubleshooting
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/reference/troubleshooting)

Content owner: OpenAI

# 故障排除

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。通过在页面 URL 后附加 `.md`，可以获取文档页面的 Markdown 版本。

## 常见问题解答

### 侧边栏中出现了 Codex 未编辑的文件

如果你的项目位于 Git 仓库中，审查面板会自动
根据项目的 Git 状态显示更改，包括 Codex 未
做出的更改。

在审查面板中，你可以切换暂存的更改和尚未
暂存的更改，并将你的分支与 main 分支进行比较。

如果你只想查看上一次 Codex 对话的更改，请将差异
面板切换到 **上一轮对话** 视图。

[了解有关如何使用审查面板的更多信息](https://learn.chatgpt.com/docs/code-review?surface=app)。

### 从侧边栏中移除项目

要从侧边栏中移除项目，请将鼠标悬停在项目名称上，点击
三个点并选择“移除”。要恢复它，请使用 **聊天** 旁边的 **添加新项目** 按钮重新
添加该项目，或使用

<kbd>Cmd</kbd>+<kbd>O</kbd>。

<a id="find-archived-threads"></a>
<a id="find-archived-tasks"></a>

### 查找已归档的聊天

已归档的聊天可以在 [设置](codex://settings) 中找到。当你取消归档
聊天时，它会重新出现在其原始的侧边栏位置。

<a id="only-some-threads-appear-in-the-sidebar"></a>
<a id="only-some-tasks-appear-in-the-sidebar"></a>

### 侧边栏中只显示部分聊天

侧边栏允许你根据项目的状态过滤聊天。如果你找不到
聊天，请选择 **聊天** 旁边的过滤图标，然后选择
**按时间顺序**。如果你仍然没有看到该聊天，请打开
[设置](codex://settings) 并查看 **已归档的聊天**。

### 代码无法在工作树（worktree）上运行

工作树（Worktrees）创建在不同的目录中，默认继承
提交到 Git 的文件。根据你管理项目
依赖和工具的方式，你可能需要使用
[本地环境](https://learn.chatgpt.com/docs/environments/local-environment) 在工作树上运行安装脚本，或复制被忽略的设置文件
（使用 [`.worktreeinclude`](https://learn.chatgpt.com/docs/environments/git-worktrees#copy-ignored-local-files-into-managed-worktrees)）。
或者，你可以在常规的本地项目中检出这些更改。请参阅
[工作树文档](https://learn.chatgpt.com/docs/environments/git-worktrees) 以了解更多信息。

### 应用无法获取团队成员共享的本地环境

本地环境配置必须位于项目根目录的 `.codex` 文件夹内。如果你在一个包含多个
项目的 monorepo（单体仓库）中工作，请确保在包含该
`.codex` 文件夹的目录中打开该项目。

### Codex 请求访问 Apple Music

根据你的任务，Codex 可能需要导航文件系统。macOS 上的某些
目录（包括音乐、下载或桌面）需要
用户额外批准。如果 Codex 需要读取你的主目录，
macOS 会提示你批准访问这些文件夹。

<a id="automations-create-many-worktrees"></a>

### 计划任务创建了大量工作树

频繁的计划任务会随着时间的推移创建许多工作树。请归档你不再需要的计划
运行，除非你打算保留它们的工作树，否则请避免固定运行。

### 选择错误目标后恢复提示词

如果你不小心以错误的目标（**本地**、**工作树** 或 **云端**）开始了聊天，你可以取消当前的运行，并通过在输入框中按向上箭头键来恢复之前的提示词。

### 功能在 Codex CLI 中有效，但在 ChatGPT 桌面应用中无效

ChatGPT 桌面应用和 Codex CLI 可能包含不同的 Codex 版本，因此
某些功能可能会先出现在一个平台上，然后才出现在另一个平台上。实验性功能也可能会
最先在 Codex CLI 中推出。

要获取你系统上 Codex CLI 的版本，请运行：

```bash
codex --version
```

要获取与你的 ChatGPT 桌面应用捆绑的 Codex 版本，请使用
保留的 `Codex.app` 兼容性包路径：

```bash
/Applications/Codex.app/Contents/Resources/codex --version
```

## 反馈和日志

在消息输入框中输入 <kbd>/</kbd> 向团队提供反馈。如果
您在现有聊天中触发反馈，您可以选择共享
现有会话以及您的反馈。在提交反馈后，
您将收到一个可以分享给团队的会话 ID。

要报告问题：

1. 在 Codex GitHub 仓库中查找 [现有问题](https://github.com/openai/codex/issues)。
2. [打开一个新的 GitHub issue](https://github.com/openai/codex/issues/new?template=2-bug-report.yml&steps=Uploaded%20thread%3A%20019c0d37-d2b6-74c0-918f-0e64af9b6e14)

更多日志可在以下位置找到：

- 应用程序日志 (macOS): `~/Library/Logs/com.openai.codex/YYYY/MM/DD`
- 会话记录: `$CODEX_HOME/sessions` (默认: `~/.codex/sessions`)
- 已归档的会话: `$CODEX_HOME/archived_sessions` (默认: `~/.codex/archived_sessions`)

如果您分享日志，请先检查它们以确认不包含敏感
信息。

## 卡死状态和恢复模式

如果聊天出现卡死：

1. 检查 Codex 是否正在等待批准。
2. 打开终端并运行类似 `git status` 的基本命令。
3. 使用更小、更集中的提示词开始一个新聊天。

如果您误取消了工作树创建并丢失了提示词，请在输入框中按上
箭头键以恢复它。

## 终端问题

**终端似乎卡住了**

1. 关闭终端面板。
2. 使用 <kbd>Ctrl</kbd>+<kbd>`</kbd> 重新打开它。
3. 重新运行类似 `pwd` 或 `git status` 的基本命令。

如果命令行为与预期不同，请先在终端中验证当前目录和
分支。

如果仍然卡死，请等到活跃的聊天完成后再重启应用程序。

**字体无法正确渲染**

Codex 在审查窗格、集成终端和应用程序内显示的任何其他代码中使用相同的字体。您可以在 [设置](codex://settings) 窗格中将其配置为 **代码字体**。

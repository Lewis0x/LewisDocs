---
title: 开发者命令
source_id: codex/ide/slash-commands
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/ide/slash-commands
owner: OpenAI
content_sha256: 44f7b318f335c6a40fc767fde95b2672766f2f1f35601cb943b0e5ef7aa7a3ed
translation_of: codex/ide/slash-commands
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/ide/slash-commands)

Content owner: OpenAI

# 开发者命令

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。可以通过在页面 URL 后附加 `.md` 来获取文档页面的 Markdown 版本。

使用这些命令可以从 VS Code 命令面板控制 Codex。您还可以将它们绑定到键盘快捷键。

## 分配快捷键

要为 Codex 命令分配或更改快捷键：

1. 打开命令面板（macOS 上为 **Cmd+Shift+P** 或 Windows/Linux 上为 **Ctrl+Shift+P**）。
2. 运行 **首选项：打开键盘快捷方式**。
3. 搜索 `Codex` 或命令 ID（例如，`chatgpt.newChat`）。
4. 选择铅笔图标，然后输入您想要的快捷键。

## 扩展命令

| 命令                      | 默认快捷键                                 | 描述                                                   |
| ------------------------- | ------------------------------------------ | ------------------------------------------------------- |
| `chatgpt.addToThread`     | -                                          | 将选定的文本范围添加为当前聊天的上下文                 |
| `chatgpt.addFileToThread` | -                                          | 将整个文件添加为当前聊天的上下文                         |
| `chatgpt.newChat`         | macOS：`Cmd+N`<br />Windows/Linux：`Ctrl+N` | 创建新聊天                                             |
| `chatgpt.newCodexPanel`   | -                                          | 创建新的 Codex 面板                                      |
| `chatgpt.openCommandMenu` | -                                          | 打开 Codex 命令菜单                                     |
| `chatgpt.openSidebar`     | -                                          | 打开 Codex 侧边栏面板                                    |

斜杠命令允许您在不离开撰写框的情况下控制 Codex。使用它们来检查状态、在本地和云模式之间切换，或发送反馈。

## 使用斜杠命令

1. 在 Codex 撰写框中，输入 `/`。
2. 从列表中选择一个命令，或继续输入以进行筛选（例如，`/status`）。
3. 按 **Enter** 键。

## 可用的斜杠命令

| 斜杠命令        | 描述                                                                             |
| -------------------- | --------------------------------------------------------------------------------------- |
| `/approve`           | 当自动审查处于活动状态时，批准最近一次自动审查拒绝的重试。 |
| `/cloud`             | 当云执行可用时，在云端运行聊天。                           |
| `/cloud-environment` | 为聊天选择云环境。                                              |
| `/compact`           | 压缩当前聊天的上下文。                                                     |
| `/fast`              | 当可用时，打开或关闭由目录提供的快速服务层。                    |
| `/feedback`          | 打开反馈对话框以提交反馈，并可选地包含日志。                |
| `/fork`              | 将本地聊天复制到新的本地聊天中。                                                |
| `/goal`              | 为 Codex 设定一个持续努力的目标。                                         |
| `/ide-context`       | 打开或关闭自动 IDE 上下文。                                                   |
| `/init`              | 为当前项目生成 `AGENTS.md` 脚手架。                               |
| `/local`             | 在您的本地工作区中运行聊天。                                                   |
| `/mcp`               | 打开 MCP 状态以查看已连接的服务器。                                              |
| `/memories`          | 当“记忆”可用时，配置聊天是否可以使用或生成记忆。    |
| `/model`             | 为当前聊天选择模型。                                                  |
| `/personality`       | 当当前模型支持个性（personality）时，选择 Codex 的响应方式。               |
| `/plan`              | 切换用于多步规划的规划模式。                                               |
| `/project`           | 为新聊天选择项目。                                                         |
| `/reasoning`         | 为当前聊天选择推理工作量。                                       |
| `/review`            | 启动代码审查模式以审查未提交的更改或与基础分支进行比较。  |
| `/side`              | 在不中断主聊天的情况下启动临时侧边聊天。                         |
| `/status`            | 显示聊天 ID、上下文使用情况和速率限制。                                       |
| `/worktree`          | 在新的 Git 工作树中运行聊天。                                                     |

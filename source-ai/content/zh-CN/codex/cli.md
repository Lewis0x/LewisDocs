---
title: 检查、编辑并从终端运行代码
source_id: codex/cli
product: codex
lang: zh-CN
canonical_url: https://learn.chatgpt.com/docs/codex/cli
owner: OpenAI
content_sha256: 9895e4936d78754402c57247657cd2c46752bde97d694b9c6c95ff7c15429d58
translation_of: codex/cli
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://learn.chatgpt.com/docs/codex/cli)

Content owner: OpenAI

Codex CLI

# 检查、编辑并从终端运行代码

检查代码、进行更改、运行命令，并自动化重复性工作，而无需离开终端。

 安装 Codex

 CLI 参考

 $

 codex

```
╭──────────────────────────────────────────────────╮
│ >_ OpenAI Codex                                  │
│                                                  │
│ model:     gpt-5.6-sol medium/model to change │
│ directory: ~/code                                │
╰──────────────────────────────────────────────────╯

  To get started, describe a task or try one of these commands:

  /init - create an AGENTS.md file with instructions for Codex
  /status - show current session configuration
  /permissions - choose what Codex is allowed to do
  /model - choose what model and reasoning effort to use
  /review - review any changes and find issues

```

```
›Refactor the Dashboard component to React Hooks
```

```
  100% context left · ? for shortcuts

```

01

## 针对您的本地存储库工作

让 Codex 检查文件、进行编辑并运行您机器上已安装的工具。

02

## 保持控制权

选择适合任务的模型、推理努力程度、权限和命令。

03

## 与脚本和 CI 组合使用

以交互方式使用 Codex，或从可重复的工作流和管道中调用 codex exec。

快速入门

## 开始使用 Codex CLI

 安装 Codex、登录，并从项目目录运行您的第一个任务。

1.  1 安装 CodexmacOS/LinuxWindowsnpmHomebrew使用适用于 macOS 和 Linux 的独立安装程序安装 Codex CLI。安装 Codex`curl -fsSL https://chatgpt.com/codex/install.sh | sh`更新 Codex`curl -fsSL https://chatgpt.com/codex/install.sh | sh`
2.  2 运行 Codex 并登录
   打开一个项目目录并运行 `codex`。首次运行 Codex 时，请选择**使用 ChatGPT 登录**或其他可用的登录方法。
   [
   查看身份验证选项
   ](/codex/auth)
3.  3 开始您的第一个任务
   描述您想要实现的目标。例如，要求 Codex 解释
         项目、进行针对性的更改，或帮助调试问题。
   `
   告诉我关于这个项目的信息
   `
   在任务前后创建 Git 检查点，以便您可以还原更改。
         请参见 [最佳实践](/codex/learn/best-practices)。


后续步骤[ 探索 CLI 参考 ](/codex/developer-commands?surface=cli)[ 配置 Codex ](/codex/configuration?surface=cli)[ 使用 codex exec 实现自动化 ](/codex/non-interactive-mode)

## 查看 Codex CLI 能做什么

使用一个专注的终端循环进行交互式工作、自动化、审查和委派。

01

在您的终端中保持编码循环

在存储库中启动 Codex，以探索不熟悉的代码、规划更改、编辑文件并运行您的本地开发工具。引导当前活动回合，在命令和差异出现时进行检查，并将后续工作保留在同一会话中。


了解更多


>_OpenAI Codex(v0.143.0)模型:**gpt-5.6-solmedium**/model 更改目录:**~/code/my-app**

02

使用技能和插件

将可重复的指令打包为技能，然后添加插件，将 Codex 连接到您团队的工具和数据，而无需离开 CLI。


了解更多


zsh — plugins插件从可用的市场浏览插件。已安装 1751 个可用插件中的 17 个。[所有插件]已安装 (17)OpenAI 精选工作区与我共享openai-primary-runtime添加市场键入以搜索插件›[-][测试版] 工作区代理已安装按 Enter 键查看插件详情。[*]构建 Web 应用已安装 · OpenAI 精选通过浏览器测试构建以前端为中心的 Web 应用[-]默认模板已安装 · OpenAI 精选文档、电子表格和幻灯片的默认模板[*]文档已安装 · openai-primary-runtime创建和编辑文档工件[*]GitHub已安装 · OpenAI 精选分类 PR、问题、CI 和发布流程[*]Gmail已安装 · OpenAI 精选阅读和管理 Gmail[*]Google 日历已安装 · OpenAI 精选管理 Google 日历的活动和日程安排[-]Google 云端硬盘已安装 · OpenAI 精选跨云端硬盘、文档、表格和幻灯片工作

03

在发布前审查更改

针对未提交的更改、提交或基础分支运行专门的审查。Codex 会报告优先排序的发现，而不会修改您的工作树，因此您可以在提交或打开拉取请求之前解决风险。


了解更多


选择审查预设›1.针对基础分支进行审查(PR 风格)2.审查未提交的更改3.审查提交4.自定义审查说明

围绕 Codex 构建终端工作流



了解你可以使用的 CLI 功能，以恢复会话、添加视觉
      和网络上下文、拆分复杂工作，并将 Codex 连接到你的
      开发工具。


 01 ` codex resume ` 返回已保存的聊天  从当前仓库重新打开最近的聊天，或在需要回到之前的工作时搜索本地聊天。

 02 ` codex --image ` 为提示词引入视觉上下文  在首个提示词中附带错误截图、架构图或设计参考，或将图像粘贴到交互式编辑器中。

 03 ` subagents ` 拆分更庞大的调查任务  让 Codex 将专注的工作委派给专门的智能体，然后将它们的调查结果带回主终端会话。

 04 ` codex --search ` 搜索当前上下文  当任务依赖于当前发布版本、文档或外部行为时，将运行切换为实时网络搜索。搜索活动在记录中保持可见。

 05 ` codex cloud ` 将工作移至 Codex 云  浏览进行中和已完成的聊天，将工作提交到已配置的环境中，并从终端将结果应用到你的本地仓库。

 06 ` codex mcp ` 使用 MCP 连接外部工具  添加本地或远程 MCP 服务器，按需进行身份验证，并在 Codex 使用它们之前检查当前会话可用的工具。

 07 ` /permissions ` 为每次运行设定边界  选择 Codex 何时可以在未经询问的情况下编辑文件或运行命令，并在继续之前检查活动沙盒和可写根目录。

 08 ` codex completion ` 让 Codex 适配你的终端  为你的 shell 生成补全，选择语法主题，并在由 VISUAL 或 EDITOR 配置的编辑器中打开较长的提示词。

当你……时使用 Codex CLI


你在终端中工作

在一个专注的循环中探索、编辑和运行代码库。

你需要脚本或 CI

在可重复的工作流中运行非交互式命令。

你想要本地代码审查

在提交或打开拉取请求之前检查更改。

你想把工作交给云端

启动云端聊天，稍后再返回终端。

其他 ChatGPT 和 Codex 界面
[ 桌面版应用  在您的桌面上协调项目和长期运行的任务。 ](/codex/app)[ ChatGPT 网页版  从您的浏览器进行研究、分析和创作。 ](/codex/web)[ IDE 扩展  在您的编辑器中代码旁使用 Codex 工作。 ](/codex/ide)[ Codex 云端  在并行的云环境中运行编码任务。 ](/codex/cloud)

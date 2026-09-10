---
title: 使用 ultraplan 在云端制定计划
source_id: claude-code/ultraplan
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/ultraplan
owner: Anthropic
content_sha256: 86f52e8cf34071ba765580433b9b570011ab44375e7ce45b4006467cd42b3c33
translation_of: claude-code/ultraplan
translation_model: gpt-5.6
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/ultraplan)

Content owner: Anthropic

> ## 文档索引
> 在以下地址获取完整的文档索引：https://code.claude.com/docs/llms.txt
> 使用此文件可在深入探索之前发现所有可用页面。

# 使用 ultraplan 在云端制定计划

> 从 CLI 发起计划，在 Web 版 Claude Code 中起草，然后远程执行或返回终端执行

<Note>
  Ultraplan 目前处于研究预览阶段。其行为和功能可能会根据反馈发生变化。
</Note>

Ultraplan 会将规划任务从本地 CLI 移交给一个 [Web 版 Claude Code](/docs/en/claude-code-on-the-web) 会话，该会话以[计划模式](/docs/en/permission-modes#analyze-before-you-edit-with-plan-mode)运行。在你继续使用终端工作时，Claude 会在云端起草计划。计划准备就绪后，你可以在浏览器中打开计划，针对特定章节发表评论、要求修改，并选择在哪里执行。

当你希望获得比终端更丰富的审查界面时，这项功能会很有用：

* **定向反馈**：可以针对计划的各个章节发表评论，而不必回复整个计划
* **免干预起草**：计划在远程生成，因此终端仍可用于其他工作
* **灵活执行**：批准计划后可在 Web 上运行并创建拉取请求，也可以将计划发回终端

Ultraplan 需要 [Web 版 Claude Code](/docs/en/claude-code-on-the-web) 账户和 GitHub 仓库。由于它在 Anthropic 的云基础设施上运行，因此使用 Amazon Bedrock、Google Cloud 的 Agent Platform 或 Microsoft Foundry 时不可用。云会话在你账户的默认[云环境](/docs/en/claude-code-on-the-web#the-cloud-environment)中运行。如果你还没有云环境，ultraplan 会在首次启动时自动创建一个。

## 从 CLI 启动 ultraplan

在本地 CLI 会话中，可以通过三种方式启动 ultraplan：

* **命令**：运行 `/ultraplan`，后面接提示词
* **关键词**：在常规提示词中的任意位置包含 `ultraplan` 一词
* **从本地计划启动**：Claude 完成本地计划并显示批准对话框时，选择 **No, refine with Ultraplan on Claude Code on the web**，将草稿发送到云端继续迭代

例如，使用命令为服务迁移制定计划：

```
/ultraplan migrate the auth service from sessions to JWTs
```

通过命令和关键词启动时，会先打开确认对话框。通过本地计划启动时则会跳过此对话框，因为前面的选择已经起到确认作用。如果 [Remote Control](/docs/en/remote-control) 处于活动状态，ultraplan 启动时会将其断开，因为这两项功能都占用 claude.ai/code 界面，而同一时间只能连接一项功能。

云会话启动后，在云会话工作期间，CLI 的提示词输入区域会显示状态指示器：

| 状态                           | 含义                                                     |
| :----------------------------- | :------------------------------------------------------- |
| `◇ ultraplan`                  | Claude 正在研究你的代码库并起草计划                      |
| `◇ ultraplan needs your input` | Claude 有一个澄清问题；打开会话链接进行回答              |
| `◆ ultraplan ready`            | 计划已准备好，可在浏览器中审查                           |

运行 `/tasks` 并选择 ultraplan 条目，可打开包含会话链接、智能体活动和 **Stop ultraplan** 操作的详细视图。停止操作会归档云会话并清除指示器；不会向终端保存任何内容。

## 在浏览器中审查和修改计划

当状态变为 `◆ ultraplan ready` 时，打开会话链接，在 claude.ai 上查看计划。计划会显示在专用的审查视图中：

* **行内评论**：突出显示任意段落，并留下评论让 Claude 处理
* **表情回应**：通过对章节作出回应来表示赞同或担忧，无需撰写完整评论
* **大纲侧边栏**：在计划的各个章节之间跳转

当你要求 Claude 处理评论时，它会修改计划并提供更新后的草稿。在选择执行位置之前，你可以按需进行任意次数的迭代。

## 选择执行位置

计划符合预期后，你可以在浏览器中选择让 Claude 在同一云会话中实施计划，或将计划发回正在等待的终端。

### 在 Web 上执行

在浏览器中选择 **Approve Claude's plan and start coding**，让 Claude 在同一 Web 版 Claude Code 会话中实施计划。终端会显示确认信息，状态指示器随即清除，工作则在云端继续。实施完成后，[审查差异](/docs/en/claude-code-on-the-web#review-changes)，并从 Web 界面创建拉取请求。

### 将计划发回终端

在浏览器中选择 **Approve plan and teleport back to terminal**，即可在本地实施计划，并完整访问你的环境。当会话从 CLI 启动且终端仍在轮询时，此选项才会显示。Web 会话会被归档，以免继续并行工作。

终端会在标题为 **Ultraplan approved** 的对话框中显示计划，其中有三个选项：

* **Implement here**：将计划注入当前对话，并从先前停下的位置继续
* **Start new session**：清除当前对话，仅以计划作为上下文重新开始
* **Cancel**：将计划保存到文件而不执行；Claude 会输出文件路径，以便你稍后返回

如果启动新会话，Claude 会在顶部输出一条 `claude --resume` 命令，供你稍后返回之前的对话。

## 相关资源

* [Web 版 Claude Code](/docs/en/claude-code-on-the-web)：ultraplan 运行所依赖的云基础设施
* [计划模式](/docs/en/permission-modes#analyze-before-you-edit-with-plan-mode)：本地会话中的规划工作方式
* [使用 ultrareview 查找错误](/docs/en/ultrareview)：ultraplan 的代码审查对应功能，用于在合并前发现问题
* [Remote Control](/docs/en/remote-control)：通过 claude.ai/code 界面使用在你自己的机器上运行的会话

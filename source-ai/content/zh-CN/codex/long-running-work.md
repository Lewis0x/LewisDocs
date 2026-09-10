---
title: 长时间运行的工作
source_id: codex/long-running-work
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/long-running-work
owner: OpenAI
content_sha256: 4a598b06884cbfc2a782a32a913f3630e4b1b31078d766b8df681462f3f363b8
translation_of: codex/long-running-work
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/long-running-work)

Content owner: OpenAI

# 长时间运行的工作

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。可以通过在页面 URL 后附加 `.md` 来获取文档页面的 Markdown 版本。

对于可能需要许多步骤的工作，请给 ChatGPT 一个明确的结果、约束，
以及完成定义。将相关的工作保留在同一个对话中，以便
ChatGPT 可以使用相同的上下文来选择下一步并决定何时
完成工作。



在 ChatGPT 桌面应用中，输入 `/goal` 以启动目标模式。进度行
让你在 ChatGPT 工作时暂停、恢复、编辑或清除目标.











<CodexScreenshot
  alt="ChatGPT 桌面应用在输入框上方的目标进度控件"
  lightSrc="/images/codex/app/goal-dialog-light.webp"
  darkSrc="/images/codex/app/goal-dialog-dark.webp"
  class="my-8"
/>



<a id="start-a-goal"></a>
<a id="define-what-done-means"></a>
<a id="steer-a-running-goal"></a>
<a id="run-goals-in-parallel"></a>
<a id="related-docs"></a>



## 启动一个目标

在 ChatGPT 桌面应用、Codex CLI 或 IDE 扩展中输入 `/goal`。该
目标文本既是第一个提示，也是该任务的
完成标准。

如果结果仍然不明确，请从 `/plan` 开始。要求 ChatGPT 采访你，
识别约束，并将结果转化为具有可衡量成功
标准的目标。然后使用 `/goal` 启动精炼后的目标。





## 定义“完成”的含义

编写一个让 ChatGPT 能够验证自身进度的目标。在适用的情况下包含
以下三件事：

| 目标元素     | 包含内容                                                                      |
| ---------------- | ----------------------------------------------------------------------------- |
| **结果**      | 描述你想要的结果，而不仅仅是 ChatGPT 应该执行的活动。   |
| **约束**  | 说出所需的工具、边界、兼容性需求或要避免的方法。 |
| **验证** | 添加测试、度量或审查标准，以证明工作已完成。  |

例如：

```text
Migrate this codebase from JavaScript to TypeScript. Preserve existing behavior,
compile in strict mode without explicit `any` types, and make the full test suite pass.
```





## 引导正在运行的目标

在 ChatGPT 桌面应用中，目标进度行显示在输入框上方。使用它来
暂停或恢复工作、编辑目标或清除目标。你还可以在目标运行时发送后续
消息，以添加上下文或调整约束。

当你想要状态摘要或解释，而又不想
打断主要对话时，请使用侧边对话。在你预期会失去
连接之前暂停目标，然后在你准备好让 ChatGPT 继续时恢复它.










启动目标并不会授予 ChatGPT 更广泛的访问权限。它保持相同的
[沙盒和审批策略](https://learn.chatgpt.com/docs/sandboxing)，并在需要
做出决定时暂停。通过[自动审批
审查](https://learn.chatgpt.com/docs/sandboxing/auto-review)，单独的审查者可以
评估符合条件的请求，而无需扩展这些边界。





## 并行运行目标

每个对话都有自己的上下文、消息、结果和目标。可以并发运行对话，
但要避免让两个对话更改相同的文件。使用
[工作树](https://learn.chatgpt.com/docs/environments/git-worktrees) 为并行编码对话提供单独的
检出。





对于本地工作，请在设置中打开**运行时防止睡眠**，以便你的 Mac
保持唤醒状态。使用 [Pets](https://learn.chatgpt.com/docs/pets?surface=app) 或[系统
通知](https://learn.chatgpt.com/docs/notifications?surface=app) 来查看对话何时需要输入
或准备好接受审查.





## 相关文档

- [项目和对话](https://learn.chatgpt.com/docs/projects)
- [目标模式与提示](https://learn.chatgpt.com/docs/prompting#goal-mode)
- [Git 工作树](https://learn.chatgpt.com/docs/environments/git-worktrees)

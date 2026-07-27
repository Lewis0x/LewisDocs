---
title: 利用编辑器中已有的上下文进行构建
source_id: codex/ide
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/ide
owner: OpenAI
content_sha256: d57e2af6ef1d146b12eeb4b5c8d4750d7adb687a6ae0ad5a92406ce1c4ab38c3
translation_of: codex/ide
translation_model: k3
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/ide)

Content owner: OpenAI

Codex IDE 扩展

# 利用编辑器中已有的上下文进行构建

让 Codex 在你的代码旁协同工作。将打开的文件和选中的内容带入提示中,就地审查编辑,并在不中断工作流的情况下移交耗时较长的任务。

 安装扩展

 扩展快速入门

EXPLORER⌄ RETRY-SERVICE⌄srcretry.tsretry.test.tsbackoff.ts›testspackage.jsonretry.ts×retry.test.ts×backoff.ts×src›retry.ts›retryOperation1`import { wait } from './backoff';`2``3`export async function retryOperation<T>(`4`  fn: () => Promise<T>,`5`  retries = 3,`6`): Promise<T> {`7`  let attempt = 0;`8`  let lastError: unknown;`9``10`  while (attempt <= retries) {`11`    try {`12`      return await fn();`13`    } catch (error) {`14`      lastError = error;`15`      if (attempt >= retries) break;`16`      await wait(200 * 2 ** attempt);`17`      attempt++;`18`    }`19`  }`20`  throw lastError;`21`}`1`import { retryOperation } from './retry';`2``3`describe('retryOperation', () => {`4`  it('stops after max retries', async () => {`5`    const operation = vi.fn().mockRejectedValue('nope');`6``7`    await expect(retryOperation(operation, 2))`8`      .rejects.toBe('nope');`9``10`    expect(operation).toHaveBeenCalledTimes(3);`11`  });`12`});`1`import { setTimeout as wait } from 'timers/promises';`2``3`export function nextDelay(baseDelay: number, attempt: number) {`4`  const jitter = Math.random() * 0.2 + 0.9;`5`  return baseDelay * 2 ** attempt * jitter;`6`}`7``8`export { wait };`CODEX🧰Trace and fix a flaky retry bugTrace and fix a flaky retry bugWorked for 6m 53s**Fixed successfully.**Retry loop now stops at max retries before waiting.The retry guard now runs before the wait, so exhausted retries stop immediately while successful attempts keep the same behavior.Validation passed:Retry exhaustion stops after the configured attempt count.Backoff still runs between retryable attempts.Focused retry tests pass.Updated`retry.ts`无需更改编辑器集成。已编辑 retry.ts+2−2Undoretry.ts+2−2[审查](/codex/prompting#use-editor-context)请求后续修改5.6-Solmain 0 个问题Ln 16, Col 1TypeScript追踪并修复一个不稳定(flaky)的重试 bug。重试循环现在会在等待之前于达到最大重试次数时停止。更改已应用。

01

## 使用已打开的上下文

直接从编辑器中的输入框引用打开的文件、选中的代码和最近的聊天。Codex 从你正在查看的代码开始,让你花更少的时间重新描述问题。

02

## 在代码旁审查更改

阅读摘要、检查聚焦的差异(diff),并在同一聊天中继续跟进。只保留你想要的更改,同时让源代码和变更理由保持可见。

03

## 任务变大时进行委托

将快速迭代保留在本地,或者当任务需要更多时间和空间时连接 Codex web。在同一编辑器工作流中返回可审查的结果。

快速入门

## 在你的 IDE 中快速上手

安装或启用 Codex，登录，然后基于编辑器中已打开的上下文开始对话。

1.  1 安装或启用 Codex
   选择你的 IDE。VS Code 及兼容编辑器使用 Codex 扩展；
         Xcode 和 JetBrains IDE 提供各自的集成。
   [
   Visual Studio Code
   ](vscode:extension/openai.chatgpt)[
   Cursor
   ](cursor:extension/openai.chatgpt)[
   Windsurf
   ](windsurf:extension/openai.chatgpt)[
   Visual Studio Code Insiders
    （在新标签页中打开）](https://marketplace.visualstudio.com/items?itemName=openai.chatgpt)[
   Xcode
    （在新标签页中打开）](https://developer.apple.com/documentation/Xcode/setting-up-coding-intelligence)[
   JetBrains IDE
    （在新标签页中打开）](https://www.jetbrains.com/help/ai-assistant/codex-agent.html)
2.  2 打开 Codex
   VS Code、Cursor 或 Windsurf：

   选择 Codex 图标。如果看不到该图标，打开命令面板并
           运行 **Codex: Open Codex Sidebar**。
   Xcode：打开编码助手，
           开始新对话，并选择 Codex 作为代理。
   JetBrains IDE：
   打开 AI Chat 并选择 Codex。

3.  3 开始你的第一次对话
   打开一个项目，让 Codex 解释代码库、进行有针对性的
         修改，或帮你调试问题。在任务前后创建 Git 检查点，
         以便你可以还原更改。
   [
   阅读最佳实践
   ](/codex/learn/best-practices)

后续步骤[ 使用编辑器上下文编写提示 ](/codex/prompting#use-editor-context)[ 探索 IDE 命令 ](/codex/developer-commands?surface=ide)[ 配置扩展 ](/codex/developer-settings?surface=ide)

## 了解 Codex 在你的 IDE 中能做什么

贴近代码，Codex 随时为你解释、编辑、审查和委派任务。

01

使用已打开的上下文

将打开的文件、选中的内容或最近的对话添加到编辑器中，然后让 Codex 基于已附加的上下文解释或编辑代码。


了解更多


MERGE_REBRAND_POSITIONING.mdelement_merged_pill.png.codex/skills/add-codex-use-case/resourcesAssess 破坏性变更每周回顾Slack 消息记录仓库架构更新入门章节更新落地页插图编辑files.mdx使用来自@mergCustom⌄5.6-Sol⌄的上下文

02

在代码旁审查更改

无需额外的导航窗格，即可查看简明摘要和更改的行。检查两个受影响的文件，保留你想要的编辑，并在同一视图中提出后续请求。


了解更多


03

任务变大时进行委派

选择本地工作以进行快速、动手式的迭代，或连接 Codex Web 来委派更耗时的任务。当你返回审查结果时，对话仍然可用。


了解更多


继续于本地工作云端openai/developers-website

何时使用 Codex IDE 扩展……


你在进行有针对性的编辑

让相关文件和 Codex 保持在同一视图中。

你在学习不熟悉的代码

询问编辑器中已打开的文件和符号。

你想就地审查更改

在源代码旁检查并应用编辑。

你想委派更大的任务

从 IDE 启动云端工作，然后返回查看结果。


其他 ChatGPT 和 Codex 入口
[ 桌面应用  在桌面上协调项目和长时间运行的任务。 ](/codex/app)[ ChatGPT 网页版  在浏览器中研究、分析和创作。 ](/codex/web)[ Codex CLI  在终端中检查、编辑和自动化。 ](/codex/cli)[ Codex 云端  在并行云环境中运行编码任务。 ](/codex/cloud)

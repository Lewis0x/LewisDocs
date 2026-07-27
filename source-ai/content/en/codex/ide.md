---
title: Codex IDE Extension
source_id: codex/ide
product: codex
lang: en
canonical_url: https://developers.openai.com/codex/ide
owner: OpenAI
content_sha256: 6214f037944f6a4069f2b6f0322522ab5785810696673833f0192ba8ff84d194
---
[Official source](https://developers.openai.com/codex/ide)

Content owner: OpenAI

Codex IDE extension

# Build with the context already in your editor

Work with Codex beside your code. Bring open files and selections into the prompt, review edits in place, and hand off longer work without breaking your flow.

 Install the extension 

 Extension quickstart 

EXPLORER⌄ RETRY-SERVICE⌄srcretry.tsretry.test.tsbackoff.ts›testspackage.jsonretry.ts×retry.test.ts×backoff.ts×src›retry.ts›retryOperation1`import { wait } from './backoff';`2``3`export async function retryOperation<T>(`4`  fn: () => Promise<T>,`5`  retries = 3,`6`): Promise<T> {`7`  let attempt = 0;`8`  let lastError: unknown;`9``10`  while (attempt <= retries) {`11`    try {`12`      return await fn();`13`    } catch (error) {`14`      lastError = error;`15`      if (attempt >= retries) break;`16`      await wait(200 * 2 ** attempt);`17`      attempt++;`18`    }`19`  }`20`  throw lastError;`21`}`1`import { retryOperation } from './retry';`2``3`describe('retryOperation', () => {`4`  it('stops after max retries', async () => {`5`    const operation = vi.fn().mockRejectedValue('nope');`6``7`    await expect(retryOperation(operation, 2))`8`      .rejects.toBe('nope');`9``10`    expect(operation).toHaveBeenCalledTimes(3);`11`  });`12`});`1`import { setTimeout as wait } from 'timers/promises';`2``3`export function nextDelay(baseDelay: number, attempt: number) {`4`  const jitter = Math.random() * 0.2 + 0.9;`5`  return baseDelay * 2 ** attempt * jitter;`6`}`7``8`export { wait };`CODEX🧰Trace and fix a flaky retry bugTrace and fix a flaky retry bugWorked for 6m 53s**Fixed successfully.**Retry loop now stops at max retries before waiting.The retry guard now runs before the wait, so exhausted retries stop immediately while successful attempts keep the same behavior.Validation passed:Retry exhaustion stops after the configured attempt count.Backoff still runs between retryable attempts.Focused retry tests pass.Updated`retry.ts`without changing the editor integration.Edited retry.ts+2−2Undoretry.ts+2−2[Review](/codex/prompting#use-editor-context)Ask for follow-up changes5.6-Solmain 0 problemsLn 16, Col 1TypeScriptTrace and fix a flaky retry bug. Retry loop now stops at max retries before waiting. Changes applied.

01

## Use the context already open

Reference open files, selected code, and recent chats directly from the composer. Codex starts with the code you are already looking at, so you spend less time restating the problem.

02

## Review changes beside your code

Read the summary, inspect a focused diff, and follow up in the same chat. Keep only the changes you want while the source and rationale stay visible together.

03

## Delegate when the task grows

Keep quick iterations local, or connect Codex web when a task needs more time and room. Return to a reviewable result from the same editor workflow.

Quickstart

##  Get started in your IDE 

 Install or enable Codex, sign in, and start a chat with the context already open in your editor. 

1.  1 Install or enable Codex
   Choose your IDE. VS Code and compatible editors use the Codex extension;
         Xcode and JetBrains IDEs provide their own integrations.
   [
   Visual Studio Code
   ](vscode:extension/openai.chatgpt)[
   Cursor
   ](cursor:extension/openai.chatgpt)[
   Windsurf
   ](windsurf:extension/openai.chatgpt)[
   Visual Studio Code Insiders
    (opens in a new tab)](https://marketplace.visualstudio.com/items?itemName=openai.chatgpt)[
   Xcode
    (opens in a new tab)](https://developer.apple.com/documentation/Xcode/setting-up-coding-intelligence)[
   JetBrains IDEs
    (opens in a new tab)](https://www.jetbrains.com/help/ai-assistant/codex-agent.html)
2.  2 Open Codex
   VS Code, Cursor, or Windsurf:
    
   choose the Codex icon. If it is not visible, open the Command Palette and
           run **Codex: Open Codex Sidebar**.
   Xcode: open the coding assistant,
           start a new chat, and choose Codex as the agent.
   JetBrains IDEs: 
   open AI Chat and select Codex.
   
3.  3 Start your first chat
   Open a project and ask Codex to explain the codebase, make a focused
         change, or help you debug an issue. Create Git checkpoints before and
         after a task so you can revert changes.
   [
   Read the best practices
   ](/codex/learn/best-practices)

Next steps[ Prompt with editor context ](/codex/prompting#use-editor-context)[ Explore IDE commands ](/codex/developer-commands?surface=ide)[ Configure the extension ](/codex/developer-settings?surface=ide)

## See what Codex can do in your IDE

Stay close to the code while Codex explains, edits, reviews, and delegates.

01

Use the context already open

Add an open file, a selection, or a recent chat to the composer, then ask Codex to explain or edit the code with that context already attached.


Learn more


MERGE_REBRAND_POSITIONING.mdelement_merged_pill.png.codex/skills/add-codex-use-case/resourcesAssess breaking changesWeekly reviewSlack messagesDocument repo architectureUpdate get started sectionsUpdate landing page illustrationsEditfiles.mdxusing context from@mergCustom⌄5.6-Sol⌄

02

Review changes beside your code

Review a concise summary and the changed lines without an extra navigation pane. Inspect the two affected files, keep the edits you want, and ask for a follow-up from the same view.


Learn more


03

Delegate when the task gets bigger

Choose local work for fast, hands-on iteration, or connect Codex web to delegate a longer task. The chat stays available when you return to review the result.


Learn more


Continue inWork locallyCloudopenai/developers-website

## 

Use Codex IDE extension when…


You are making focused edits

Keep the relevant files and Codex in the same view.

You are learning unfamiliar code

Ask about the files and symbols already open in the editor.

You want to review changes in place

Inspect and apply edits alongside the source.

You want to delegate a larger task

Start cloud work from the IDE and return to the result.


Other ChatGPT and Codex surfaces
[ Desktop app  Coordinate projects and long-running tasks on your desktop. ](/codex/app)[ ChatGPT web  Research, analyze, and create from your browser. ](/codex/web)[ Codex CLI  Inspect, edit, and automate from the terminal. ](/codex/cli)[ Codex cloud  Run coding tasks in parallel cloud environments. ](/codex/cloud)

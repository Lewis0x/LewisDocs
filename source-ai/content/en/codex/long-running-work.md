---
title: Long-running work
source_id: codex/long-running-work
product: codex
lang: en
canonical_url: https://developers.openai.com/codex/long-running-work
owner: OpenAI
content_sha256: 4a598b06884cbfc2a782a32a913f3630e4b1b31078d766b8df681462f3f363b8
---
[Official source](https://developers.openai.com/codex/long-running-work)

Content owner: OpenAI

# Long-running work

> For the complete documentation index, see [llms.txt](https://learn.chatgpt.com/llms.txt). Markdown versions of documentation pages are available by appending `.md` to the page URL.

For work that may take many steps, give ChatGPT a clear outcome, constraints,
and definition of done. Keep related work in the same chat so
ChatGPT can use the same context to choose the next step and decide when the
work is complete.



In the ChatGPT desktop app, enter `/goal` to start Goal mode. The progress row
lets you pause, resume, edit, or clear the goal while ChatGPT works.











<CodexScreenshot
  alt="ChatGPT desktop app goal progress controls above the composer"
  lightSrc="/images/codex/app/goal-dialog-light.webp"
  darkSrc="/images/codex/app/goal-dialog-dark.webp"
  class="my-8"
/>



<a id="start-a-goal"></a>
<a id="define-what-done-means"></a>
<a id="steer-a-running-goal"></a>
<a id="run-goals-in-parallel"></a>
<a id="related-docs"></a>



## Start a goal

Type `/goal` in the ChatGPT desktop app, Codex CLI, or the IDE extension. The
goal text becomes both the first prompt and the completion criteria for the
task.

If the outcome is still unclear, start with `/plan`. Ask ChatGPT to interview you,
identify constraints, and turn the result into a goal with measurable success
criteria. Then start the refined goal with `/goal`.





## Define what done means

Write a goal that lets ChatGPT verify its own progress. Include three things when
they apply:

| Goal element     | What to include                                                               |
| ---------------- | ----------------------------------------------------------------------------- |
| **Outcome**      | Describe the result you want, not only the activity ChatGPT should perform.   |
| **Constraints**  | Name required tools, boundaries, compatibility needs, or approaches to avoid. |
| **Verification** | Add tests, measurements, or review criteria that prove the work is complete.  |

For example:

```text
Migrate this codebase from JavaScript to TypeScript. Preserve existing behavior,
compile in strict mode without explicit `any` types, and make the full test suite pass.
```





## Steer a running goal

In the ChatGPT desktop app, the goal progress row appears above the composer. Use it to
pause or resume work, edit the goal, or clear it. You can also send follow-up
messages while the goal runs to add context or adjust constraints.

Use a side chat when you want a status recap or an explanation without
interrupting the main chat. Pause the goal before you expect to lose
connectivity, then resume it when you're ready for ChatGPT to continue.











Starting a goal doesn't grant ChatGPT broader access. It keeps the same
[sandbox and approval policy](https://learn.chatgpt.com/docs/sandboxing) and pauses when it
needs a decision. With [automatic approval
reviews](https://learn.chatgpt.com/docs/sandboxing/auto-review), a separate reviewer can
evaluate eligible requests without expanding those boundaries.





## Run goals in parallel

Each chat keeps its own context, messages, results, and goal. Run chats
concurrently, but avoid letting two chats change the same files. Use
[worktrees](https://learn.chatgpt.com/docs/environments/git-worktrees) to give parallel coding chats separate
checkouts.





For local work, turn on **Prevent sleep while running** in settings so your Mac
stays awake. Use [Pets](https://learn.chatgpt.com/docs/pets?surface=app) or [system
notifications](https://learn.chatgpt.com/docs/notifications?surface=app) to see when a chat needs input
or is ready for review.





## Related docs

- [Projects and chats](https://learn.chatgpt.com/docs/projects)
- [Goal mode and prompting](https://learn.chatgpt.com/docs/prompting#goal-mode)
- [Git worktrees](https://learn.chatgpt.com/docs/environments/git-worktrees)

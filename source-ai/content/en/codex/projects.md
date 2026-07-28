---
title: Projects and chats
source_id: codex/projects
product: codex
lang: en
canonical_url: https://developers.openai.com/codex/projects
owner: OpenAI
content_sha256: 2dd2de3f8e4724799ea540c27cc0e6c24ca4797ee861b86625633c3b3106796d
---
[Official source](https://developers.openai.com/codex/projects)

Content owner: OpenAI

# Projects and chats

> For the complete documentation index, see [llms.txt](https://learn.chatgpt.com/llms.txt). Markdown versions of documentation pages are available by appending `.md` to the page URL.

Use a project to organize related chats and give ChatGPT the context it needs.
The **Projects** view in the ChatGPT desktop app includes ChatGPT projects and
local projects that connect to folders on your computer.

## Choose a project or start without one

Create a project when work will continue over time, produce more than one
output, or depend on the same files and sources. Start a chat without a project
when the work is self-contained and doesn't need shared project context.









<a id="work-in-a-project"></a>



## Work in a project

The **Projects** view brings ChatGPT projects and local projects into one place.
ChatGPT projects carry project files and context across related chats. A local
project gives chats access to one or more folders on your computer, such as a
collection of source files or a codebase.

Start a separate chat for each distinct outcome so its messages and results stay
focused while the project keeps related work organized.

<CodexScreenshot
  alt="ChatGPT desktop app showing multiple projects in the sidebar and chats in the main pane"
  lightSrc="/images/codex/app/multitask-light.webp"
  darkSrc="/images/codex/app/multitask-dark.webp"
  maxHeight="400px"
  class="my-8"
/>









<a id="manage-project-threads"></a>
<a id="organize-projects-and-chats"></a>



<a id="organize-projects-and-tasks"></a>

## Organize projects and chats

Keep active work visible and move finished work out of the way:

- **Pin a project** to keep it near the top of the sidebar. You can also pin it
  from the Projects view.
- **Pin a chat** when you return to it often, even if newer chats appear in the
  project.
- **Rename a chat** with a short title that describes its outcome, such as “Q3
  launch brief” or “Checkout accessibility review.”
- **Search projects** from the Projects view. Press
  <kbd>Cmd</kbd>/<kbd>Ctrl</kbd>+<kbd>G</kbd> to search past chats when you
  remember a phrase or branch name but not the title.
- **Archive a chat** when you finish the work. From a project's menu, select
  **Archive chats** to archive its chats together.

Pinning doesn't add context or change what ChatGPT can access. It only changes
where the project or chat appears in the sidebar.

Restore archived chats from **Settings > Archived chats**.







<a id="use-local-projects-for-folders-and-codebases"></a>



## Use local projects for folders and codebases

Add a local project when ChatGPT needs to read or change files on your computer.
Projects don’t need a folder, but you can attach folders as needed.

To add or change folders, open the project's menu and select **Edit project**.
Select **Add folder** to attach multiple folders. ChatGPT can read and change files
in every attached folder. To change the default working directory, point to a
folder and select **Make primary**.

New chats start in the primary folder. Codex also uses that folder for Git
operations and automatic discovery of `AGENTS.md`, skills, and `config.toml`.
Secondary folders remain available for file search, reading, and editing, but
Codex doesn't automatically discover those project files from secondary
folders.

Use multiple folders when related work lives in different places, like an app and
its documentation or a website and its backend. Create separate projects for
unrelated work or when each chat should access only one part of a repository.
This keeps the working context focused. Remote projects currently support one
folder.

Use [local environments](https://learn.chatgpt.com/docs/environments/local-environment) to define setup
actions and common commands for a project. Git review, pull request, and
[worktree](https://learn.chatgpt.com/docs/environments/git-worktrees) actions target the primary
repository. When you start a chat in a worktree, the other folders remain
attached.

Projects and worktrees organize work, but the [sandbox](https://learn.chatgpt.com/docs/sandboxing)
enforces what local commands can read, change, or access over the network.



<a id="start-without-a-project"></a>


<a id="start-a-task-without-a-project"></a>

## Start a chat without a project

Select **New chat** when the work is self-contained and doesn't need shared
project files, instructions, or folder access. Create a project first when
several chats will depend on the same context.





<a id="start-a-chat"></a>
<a id="start-a-standalone-chat"></a>


<a id="use-quick-chat-for-a-quick-conversation"></a>

## Use Quick chat for a quick question

Quick chat opens an ordinary ChatGPT chat. ChatGPT chats don't appear in the
Codex sidebar, which contains your Codex chats and projects.

Point to **New chat**, then select the **Quick chat** icon on its right. You can
also press

<kbd>Cmd+Option+N</kbd> on macOS or <kbd>Ctrl+Alt+N</kbd> on Windows. From **New
chat**, you can open an existing ChatGPT chat and add it to a Codex chat.



## Bring in other tools and context



- Attach files or [image inputs](https://learn.chatgpt.com/docs/image-inputs) directly to a chat
  when they apply only to that request.
- Install [plugins](https://learn.chatgpt.com/docs/plugins) to bring in context and actions from other
  services.
- Configure [MCP](https://learn.chatgpt.com/docs/extend/mcp) servers when your organization or developer setup
  exposes tools through Model Context Protocol.
- Use [memories](https://learn.chatgpt.com/docs/customization/memories), where available, to carry useful context from
  past work into future chats.









## Next steps

- [Learn how to write and refine prompts](https://learn.chatgpt.com/docs/prompting)
- [Learn how to use ChatGPT](https://learn.chatgpt.com/docs/use-chatgpt)
- [Continue long-running work](https://learn.chatgpt.com/docs/long-running-work)

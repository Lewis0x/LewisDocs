---
title: Codex CLI
source_id: codex/cli
product: codex
lang: en
canonical_url: https://learn.chatgpt.com/docs/codex/cli
owner: OpenAI
content_sha256: 28964d265ccf223323f515d5822420cada253435ea4555ec34f197e92e68184d
---
[Official source](https://learn.chatgpt.com/docs/codex/cli)

Content owner: OpenAI

Codex CLI

# Inspect, edit, and run code from your terminal

Inspect code, make changes, run commands, and automate repeatable work without leaving your terminal.

 Install Codex 

 CLI reference 

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

## Work against your local repository

Let Codex inspect files, make edits, and run the tools already installed on your machine.

02

## Stay in control

Choose the model, reasoning effort, permissions, and commands that fit the task.

03

## Compose with scripts and CI

Use Codex interactively or call codex exec from repeatable workflows and pipelines.

Quickstart

## Get started with Codex CLI

 Install Codex, sign in, and run your first task from a project directory. 

1.  1 Install CodexmacOS/LinuxWindowsnpmHomebrewInstall the Codex CLI with the standalone installer for macOS and Linux.Install Codex`curl -fsSL https://chatgpt.com/codex/install.sh | sh`Update Codex`curl -fsSL https://chatgpt.com/codex/install.sh | sh`
2.  2 Run Codex and sign in
   Open a project directory and run `codex`. The first time you run Codex, choose **Sign in with ChatGPT** or another available sign-in method.
   [
   Review authentication options
   ](/codex/auth)
3.  3 Start your first task
   Describe what you want to accomplish. For example, ask Codex to explain
         the project, make a focused change, or help debug an issue.
   `
   Tell me about this project
   `
   Create Git checkpoints before and after a task so you can revert changes.
         See the [best practices](/codex/learn/best-practices).
   

Next steps[ Explore the CLI reference ](/codex/developer-commands?surface=cli)[ Configure Codex ](/codex/configuration?surface=cli)[ Automate with codex exec ](/codex/non-interactive-mode)

## See what Codex CLI can do

Use one focused terminal loop for interactive work, automation, review, and delegation.

01

### Keep the coding loop in your terminal

Start Codex in a repository to explore unfamiliar code, plan a change, edit files, and run your local development tools. Steer the active turn, inspect commands and diffs as they appear, and keep follow-up work in the same session.


Learn more


>_OpenAI Codex(v0.143.0)model:**gpt-5.6-solmedium**/model to changedirectory:**~/code/my-app**

02

### Use skills and plugins

Package repeatable instructions as skills, then add plugins to connect Codex to your team's tools and data without leaving the CLI.


Learn more


zsh — pluginsPluginsBrowse plugins from available marketplaces.Installed 17 of 1751 available plugins.[All Plugins]Installed (17)OpenAI CuratedWorkspaceShared with meopenai-primary-runtimeAdd MarketplaceType to search plugins›[-][Beta] Workspace agentsInstalledPress Enter to view plugin details.[*]Build Web AppsInstalled · OpenAI CuratedBuild frontend-focused web apps with browser testing[-]Default templatesInstalled · OpenAI CuratedDefault templates for documents, spreadsheets, and slides[*]DocumentsInstalled · openai-primary-runtimeCreate and edit document artifacts[*]GitHubInstalled · OpenAI CuratedTriage PRs, issues, CI, and publish flows[*]GmailInstalled · OpenAI CuratedRead and manage Gmail[*]Google CalendarInstalled · OpenAI CuratedManage Google Calendar events and schedules[-]Google DriveInstalled · OpenAI CuratedWork across Drive, Docs, Sheets, and Slides

03

### Review changes before they ship

Run a dedicated review against uncommitted changes, a commit, or a base branch. Codex reports prioritized findings without modifying your working tree, so you can address risks before you commit or open a pull request.


Learn more


Select a review preset›1.Review against a base branch(PR Style)2.Review uncommitted changes3.Review a commit4.Custom review instructions

## Build a terminal workflow around Codex


Learn about the CLI features you can use to resume sessions, add visual
      and web context, split up complex work, and connect Codex to your
      development tools.


 01 ` codex resume ` Return to a saved chat  Reopen a recent chat from the current repository, or search across local chats when you need to return to older work. 

 02 ` codex --image ` Bring visual context into the prompt  Pass an error screenshot, architecture diagram, or design reference with the first prompt, or paste an image into the interactive composer. 

 03 ` subagents ` Split up a larger investigation  Ask Codex to delegate focused work to specialized agents, then bring their findings back into the main terminal session. 

 04 ` codex --search ` Search for current context  Switch a run to live web search when a task depends on current releases, documentation, or external behavior. Search activity stays visible in the transcript. 

 05 ` codex cloud ` Move work to Codex cloud  Browse active and completed chats, submit work to a configured environment, and apply the result to your local repository from the terminal. 

 06 ` codex mcp ` Connect external tools with MCP  Add local or remote MCP servers, authenticate when needed, and inspect the tools available to the current session before Codex uses them. 

 07 ` /permissions ` Set the boundaries for each run  Choose when Codex can edit files or run commands without asking, and inspect the active sandbox and writable roots before you continue. 

 08 ` codex completion ` Fit Codex to your terminal  Generate completions for your shell, choose a syntax theme, and open longer prompts in the editor configured by VISUAL or EDITOR. 

## Use Codex CLI when…

### You work from the terminal

Explore, edit, and run a repository in one focused loop.

### You need scripting or CI

Run a non-interactive command in a repeatable workflow.

### You want a local code review

Inspect changes before you commit or open a pull request.

### You want to hand work to the cloud

Launch a cloud chat and return to the terminal later.


Other ChatGPT and Codex surfaces
[ Desktop app  Coordinate projects and long-running tasks on your desktop. ](/codex/app)[ ChatGPT web  Research, analyze, and create from your browser. ](/codex/web)[ IDE extension  Work with Codex beside the code in your editor. ](/codex/ide)[ Codex cloud  Run coding tasks in parallel cloud environments. ](/codex/cloud)

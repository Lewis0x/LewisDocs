---
title: Plugins
source_id: codex/plugins
product: codex
lang: en
canonical_url: https://developers.openai.com/codex/plugins
owner: OpenAI
content_sha256: 0c830703fd76a00931619e4ebbc2aabe9506281da52571e64dd119147c285897
---
[Official source](https://developers.openai.com/codex/plugins)

Content owner: OpenAI

# Plugins

> For the complete documentation index, see [llms.txt](https://learn.chatgpt.com/llms.txt). Markdown versions of documentation pages are available by appending `.md` to the page URL.

## Overview

Plugins bundle capabilities into reusable workflows in ChatGPT and Codex. They
can include skills, connectors, or both. Both products use one universal plugin
directory, so the same public plugins are discoverable from their supported
surfaces.

Plugins are available with ChatGPT Work on the web and with ChatGPT Work or
Codex in the ChatGPT desktop app. Codex
CLI also has a plugin browser for Codex environments. Plugins aren't available
in Chat, the IDE extension, or mobile.



In the ChatGPT desktop app, select ChatGPT and turn on Work in the switcher, or select
Codex. Then open **Plugins** to browse, install, and use plugins. Installed
plugins can add skills, connectors, and MCP tools to new chats.









Extend what ChatGPT and Codex can do, for example:

- Install the Codex Security plugin to scan authorized code and confirm
  plausible vulnerability findings.
- Install the Gmail plugin to work with Gmail.
- Install the Google Drive plugin to work across Drive, Docs, Sheets, and
  Slides.
- Install the Slack plugin to summarize channels or draft replies.

A plugin can contain one or more of these parts:

- **Skills:** reusable instructions for specific kinds of work. ChatGPT and
  Codex can load them when needed so they follow the right steps and use the
  right references or helper scripts for a task.
- **Connectors:** connections to tools like GitHub, Slack, or Google Drive, so
  ChatGPT and Codex can read information from those tools and take actions in
  them. Connectors expose tools and can optionally include custom UI.
- **MCP servers:** services that give ChatGPT and Codex access to more tools or
  shared information, often from systems outside your local project. They're
  also the services behind connectors. They define tools, enforce auth, return
  structured data, and perform actions against external systems.
- **Browser extensions:** browser capabilities that a plugin needs for its
  workflow.
- **Hooks:** commands that run at configured lifecycle points. Review and trust
  plugin hooks before you enable them.
- **Scheduled task templates:** reusable starting points for recurring tasks
  where scheduled tasks are available.

You can share plugins by publishing them through a marketplace source, such as a
repo marketplace for a project or team. See [Build plugins](https://developers.openai.com/plugins/build/plugins)
for marketplace setup, packaging, and distribution guidance.

If you are building an integration, start with
[Build an MCP server](https://developers.openai.com/plugins/build/mcp-server).
If the plugin needs custom UI, use the
[optional UI guide](https://developers.openai.com/plugins/build/chatgpt-ui).

## Use and install plugins

<a id="plugin-directory-in-the-codex-app"></a>



### Universal plugin directory

ChatGPT and Codex use the same public plugin catalog. To browse and install
plugins from a supported graphical surface:

- On the web, turn on Work in the switcher and open **Plugins**.
- In the ChatGPT desktop app, select ChatGPT and turn on Work in the switcher, or select
  Codex. Then open **Plugins**.





<CodexScreenshot
  alt="Plugins Directory in the ChatGPT desktop app"
  lightSrc="/images/codex/plugins/directory.webp"
  darkSrc="/images/codex/plugins/directory-dark.webp"
/>





The Plugins Directory organizes plugins into tabs:

- **OpenAI:** plugins built by OpenAI.
- **Your workspace name:** plugins provided by your workspace.
- **Personal:** personal marketplace plugins, including **Created by me** and
  **Shared with me** sections when those plugins are available.

Use the separate **Installed** row to review plugins you already installed.

### Install and use a plugin

Once you open the Plugins Directory:

<WorkflowSteps>

1. Search or browse for a plugin, then open its details.
2. Select the plus button to install the plugin.
3. If the plugin needs a connector, connect it when prompted. Some plugins
   ask you to authenticate during install. Others wait until the first time you
   use them.
4. After installation, start a new chat and ask ChatGPT or Codex to use the
   plugin.

</WorkflowSteps>

After you install a plugin, you can use it directly in the prompt window:





<CodexScreenshot
  alt="Installed plugin on the Plugins page"
  lightSrc="/images/codex/plugins/plugin-github-invoke.png"
  darkSrc="/images/codex/plugins/plugin-github-invoke-dark.png"
/>







  

    
Describe the task directly

    

      Ask for the outcome you want, such as "Summarize unread Gmail threads
      from today" or "Pull the latest launch notes from Google Drive."
    

    

      Use this when you want ChatGPT to choose the right installed tools for the
      task.
    

  


  

    
Choose a specific plugin

    

      Type `@` to invoke the plugin or one of its bundled skills
      explicitly.
    

    

      Use this when you want to be specific about which plugin or skill ChatGPT
      should use. See [Skills & Plugins](https://learn.chatgpt.com/docs/skills-and-plugins).
    

  








<a id="api-key-availability"></a>



### API key availability

If you [sign in to Codex with an OpenAI API
key](https://learn.chatgpt.com/docs/auth#sign-in-with-an-api-key), you can browse, install, and manage
supported OpenAI-curated plugins in Codex CLI and Codex in the ChatGPT desktop
app. Some plugins aren't available with API key authentication because their
connection flows require unsupported OAuth capabilities. Review plugin usage
on the [Platform Usage page](https://platform.openai.com/usage).



### How permissions and data sharing work





When a plugin capability runs through a Codex host, the host's [sandbox and
approval policy](https://learn.chatgpt.com/docs/agent-approvals-security) applies.
Connections to external services use that service's own authentication and
access controls.



- Bundled skills become available when you start a new chat or CLI session
  after installation.
- If a plugin includes connectors, the active product may prompt you to install
  or sign in to those connectors during setup or the first time you use them.
- If a plugin includes MCP servers, they may require extra setup or
  authentication before you can use them.
- When ChatGPT sends data through a bundled connector, that service's terms and privacy
  policy apply.

### Remove a plugin

To remove a plugin, open it from a supported plugin browser and select
**Uninstall plugin** when that action is available. Workspace-installed or
default plugins may not offer that action; your workspace administrator controls
them instead.

Uninstalling a plugin removes the plugin bundle from that ChatGPT or Codex
environment, but bundled connectors stay connected until you manage them in
ChatGPT.

## Build your own plugin

If you want to create, test, or distribute your own plugin, see
[Build plugins](https://developers.openai.com/plugins/build/plugins). That page covers local scaffolding,
manual marketplace setup, workspace sharing, plugin manifests, and packaging
guidance.

If your plugin includes server-backed capabilities, see
[Build an MCP server](https://developers.openai.com/plugins/build/mcp-server).
MCP tools can work without custom UI or return UI when a visual surface helps
the workflow.

When your plugin is ready for review, see
[Submit plugins](https://developers.openai.com/plugins/deploy/submission) for the OpenAI Platform submission
flow, required permissions, review materials, MCP checks, and test case
requirements.

## Plugin guides

- [Record & Replay](https://learn.chatgpt.com/docs/extend/record-and-replay): Show ChatGPT a workflow
  once and turn it into a reusable skill.
- [Codex Security plugin](https://learn.chatgpt.com/docs/security/plugin): Scan authorized code,
  confirm findings, and prepare reviewed fixes.

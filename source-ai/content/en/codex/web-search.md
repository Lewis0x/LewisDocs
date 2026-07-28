---
title: Web search
source_id: codex/web-search
product: codex
lang: en
canonical_url: https://developers.openai.com/codex/web-search
owner: OpenAI
content_sha256: 334b623081441a16fe7450841962b6e27360b0f81c172a92a8f2a7af142ce2c5
---
[Official source](https://developers.openai.com/codex/web-search)

Content owner: OpenAI

# Web search

> For the complete documentation index, see [llms.txt](https://learn.chatgpt.com/llms.txt). Markdown versions of documentation pages are available by appending `.md` to the page URL.

ChatGPT includes a first-party web search tool. Treat all web results as
untrusted input.



In the ChatGPT desktop app, ask for current information in a chat. ChatGPT records
search activity with the other tool calls in the transcript.











## Configure local web search

For local Codex chats, Codex enables cached search by default. Cached mode uses
an OpenAI-maintained index instead of fetching arbitrary pages live, which
lowers—but doesn't remove—prompt injection risk.

Use live search when your task depends on the latest information. Set
`web_search = "live"` in `config.toml`. Set `web_search = "disabled"` to turn
the tool off. The `"indexed"` mode permits external web access only when the
search index gates the request. When Codex runs with full access, web search
defaults to live results. See [Config basics](https://learn.chatgpt.com/docs/config-file/config-basic)
for config file locations and precedence.





For network boundaries that apply to Codex cloud environments, see [Internet
access](https://learn.chatgpt.com/docs/cloud/internet-access).

---
title: Analytics API
source_id: codex/enterprise/analytics-api
product: codex
lang: en
canonical_url: https://developers.openai.com/codex/enterprise/analytics-api
owner: OpenAI
content_sha256: 3bfcbe67a34f78aad75e117a4ea5fdd5d14e11ec64e3c1483b239629628661f7
---
[Official source](https://developers.openai.com/codex/enterprise/analytics-api)

Content owner: OpenAI

# Analytics API

> For the complete documentation index, see [llms.txt](https://learn.chatgpt.com/llms.txt). Markdown versions of documentation pages are available by appending `.md` to the page URL.

The Codex Analytics API provides aggregated Codex usage and activity metrics for
a ChatGPT workspace.

The authenticated [Codex Analytics API reference](https://chatgpt.com/codex/cloud/settings/apireference)
is the source of truth for current access requirements, routes, request and
response schemas, metrics, time semantics, and pagination.

## When to use the Analytics API

The Analytics API is appropriate when you need to:

- Automate recurring Codex reporting.
- Join aggregated Codex metrics with internal organizational data.
- Build a controlled reporting layer for approved audiences.
- Avoid coupling an integration to an interactive dashboard.

It's not a raw audit-log interface. Use the
[Compliance API](https://learn.chatgpt.com/docs/enterprise/compliance-api) when the workflow requires
auditable activity records.

## Confirm the administration boundaries

Analytics API results are scoped to a ChatGPT workspace, but requests
authenticate with a Platform organization API key. The key's organization must
match the organization associated with the workspace.

The authenticated reference owns current key provisioning, scope requirements,
routes, schemas, fields, time semantics, and pagination behavior. This page
doesn't duplicate that contract.

## Related docs

- [Workspace analytics](https://learn.chatgpt.com/docs/enterprise/workspace-analytics)
- [Admin rollout guide](https://learn.chatgpt.com/docs/enterprise/admin-setup)
- [Governance](https://learn.chatgpt.com/docs/enterprise/governance)
- [Compliance API](https://learn.chatgpt.com/docs/enterprise/compliance-api)

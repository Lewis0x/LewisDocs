---
title: Groups and provisioning
source_id: codex/enterprise/groups-and-provisioning
product: codex
lang: en
canonical_url: https://developers.openai.com/codex/enterprise/groups-and-provisioning
owner: OpenAI
content_sha256: e21e38ef291936fc8e70a4eecd04242d7650f524a5e42e0c1a531f8914c4388f
---
[Official source](https://developers.openai.com/codex/enterprise/groups-and-provisioning)

Content owner: OpenAI

# Groups and provisioning

> For the complete documentation index, see [llms.txt](https://learn.chatgpt.com/llms.txt). Markdown versions of documentation pages are available by appending `.md` to the page URL.

Groups organize ChatGPT workspace access for a set of members and can carry
custom roles. Group membership is separate from local runtime policy and
permissions in connected systems.

For the complete control model, see
[Roles and workspace permissions](https://learn.chatgpt.com/docs/enterprise/roles-and-workspace-permissions).

## Compare membership sources

Each group has one authoritative membership source:

| Group type                | Membership source                   | When it applies                                                                  |
| ------------------------- | ----------------------------------- | -------------------------------------------------------------------------------- |
| Manually managed          | ChatGPT workspace administration    | The group is small, temporary, or not managed through directory sync             |
| Identity-provider managed | Your identity provider through SCIM | Membership should follow the organization's directory and member-removal process |

Manual and identity-provider-managed groups can coexist. For synchronized
groups, the identity provider is the membership source; later provisioning
updates can overwrite workspace-side changes. The Help Center owns current SCIM
behavior, supported attributes, and setup steps.

## Understand the access boundary

SCIM provisions workspace membership and group assignments. It doesn't grant
permissions in GitHub, Google Drive, Slack, or another connected system. It also
doesn't replace local runtime requirements or Platform API organization access.

Workspace RBAC and local runtime requirements are separate control systems. A
group can be relevant to both, but don't infer a managed-requirements matching
or precedence rule from workspace group order. Use
[Managed configuration](https://learn.chatgpt.com/docs/enterprise/managed-configuration) for the
documented delivery and local precedence rules.

## Use current setup procedures

Workspace administration details can change. Use these sources for current UI
steps, availability, and limits:

- [Manage members, seat types, roles, and access](https://help.openai.com/en/articles/8266401-managing-members-seat-types-roles-and-access-in-chatgpt-enterprise)
- [Manage groups](https://help.openai.com/en/articles/9083985-group-permissions-in-gpts)
- [SCIM integration FAQ](https://help.openai.com/en/articles/10011769-openai-platform-scim-integration-faq)
- [Manage workspace settings](https://help.openai.com/en/articles/8411955)

## Related docs

- [Authentication](https://learn.chatgpt.com/docs/auth)
- [Roles and workspace permissions](https://learn.chatgpt.com/docs/enterprise/roles-and-workspace-permissions)
- [Managed configuration](https://learn.chatgpt.com/docs/enterprise/managed-configuration)
- [Admin rollout guide](https://learn.chatgpt.com/docs/enterprise/admin-setup)

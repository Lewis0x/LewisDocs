---
title: Codex Security
source_id: codex/security
product: codex
lang: en
canonical_url: https://developers.openai.com/codex/security
owner: OpenAI
content_sha256: 984272acbae5438b9df2731aea5428797f588905035daca67bbca20d030469ae
---
[Official source](https://developers.openai.com/codex/security)

Content owner: OpenAI

# Codex Security

> For the complete documentation index, see [llms.txt](https://learn.chatgpt.com/llms.txt). Markdown versions of documentation pages are available by appending `.md` to the page URL.

<CtaPillLink
  href="https://chatgpt.com/plugins/share/676aca3811d54fa7bcdef5255236b3c4"
  label="Install plugin in ChatGPT"
  icon="external"
  class="mb-8 mt-2"
/>

For a prescriptive first local scan, start with the [Codex Security plugin
quickstart](https://learn.chatgpt.com/docs/security/plugin).

### Explore plugin use cases

- [Run a security scan](https://learn.chatgpt.com/docs/security/plugin/scans) for a repository or one scoped folder.
- [Run a deep security scan](https://learn.chatgpt.com/docs/security/plugin/deep-scans) when you need a more comprehensive scan and can wait longer for it to finish.
- [Review code changes](https://learn.chatgpt.com/docs/security/plugin/code-changes) before you merge a pull request or branch.
- [Triage a backlog](https://learn.chatgpt.com/docs/security/plugin/triage-backlog) when you have existing security findings to review.
- [Fix and verify findings](https://learn.chatgpt.com/docs/security/plugin/fix-findings) with bounded patches for approved findings.
- [Export or track findings](https://learn.chatgpt.com/docs/security/plugin/export-findings) as portable artifacts or approval-gated tracking destinations.
- [Write vulnerability reports](https://learn.chatgpt.com/docs/security/plugin/vulnerability-reports) from supplied findings, disclosure notes, source, and PoCs.
- [Propose security hardening](https://learn.chatgpt.com/docs/security/plugin/security-hardening) from scan results or other security evidence.
- [See what's new](https://learn.chatgpt.com/docs/security/plugin/changelog) in the Codex Security plugin.

The plugin runs in your Codex chat. Codex Security cloud scans connected
  GitHub repositories through Codex cloud. For Codex sandboxing, approvals,
  network controls, and admin settings, see [Agent approvals &
  security](https://learn.chatgpt.com/docs/agent-approvals-security).

## Codex Security cloud

Codex Security cloud is currently in research preview. It scans connected
GitHub repositories for likely security issues.

It helps teams:

1. **Find likely vulnerabilities** by using a repo-specific threat model and real code context.
2. **Reduce noise** by validating findings before you review them.
3. **Move findings toward fixes** with ranked results, evidence, and suggested patch options.

## How Codex Security cloud works

Codex Security scans connected repositories commit by commit.
It builds scan context from your repo, checks likely vulnerabilities against that context, and validates high-signal issues in an isolated environment before surfacing them.

You get a workflow focused on:

- repo-specific context instead of generic signatures
- validation evidence that helps reduce false positives
- suggested fixes you can review in GitHub

## Codex Security cloud access and prerequisites

Codex Security cloud works with connected GitHub repositories through Codex
cloud. If a repository isn't visible, confirm the repository is available in your
Codex cloud workspace or contact your OpenAI account team.

## Related docs

- [Codex Security plugin quickstart](https://learn.chatgpt.com/docs/security/plugin) walks through installation and a first local scan.
- [Codex Security cloud setup](https://learn.chatgpt.com/docs/security/setup) details setup, scanning, and findings review.
- [Improving the threat model](https://learn.chatgpt.com/docs/security/threat-model) explains how to tune scope, attack surface, and criticality assumptions.
- [Codex Security cloud FAQ](https://learn.chatgpt.com/docs/security/faq) covers common cloud product questions.

---
title: 安全
source_id: codex/security-administration
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/security-administration
owner: OpenAI
content_sha256: b28ea1b710853702d20860ab50baf830a902e061a78821d83578535f825f71ec
translation_of: codex/security-administration
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/security-administration)

Content owner: OpenAI

# 安全

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。通过在页面 URL 后附加 `.md`，可以获取文档页面的 Markdown 版本。

<CodexDocsOverviewLanding
  title="安全"
  description="控制 ChatGPT 和 Codex 开发者工具可以访问的内容，了解工作是如何隔离的，并为安全敏感的任务应用防护措施。"
  intro="安全控制定义了 ChatGPT 和 Codex 开发者工具可以访问的内容，以及如何审查敏感操作。权限、沙盒、批准和网络访问确立了信任边界。Codex Security 有助于查找和修复漏洞，而网络安全指南则解释了如何处理安全敏感的工作。"
  primaryCta={{
    label: "探索权限",
    href: "/codex/permissions",
  }}
  hero={{
    illustration: "security",
    backgroundImage: "/images/codex/codex-wallpaper-1.webp",
    alt: "ChatGPT 针对默认、自动、完全和自定义访问的批准选项",
  }}
  sections={[
    {
      title: "权限",
      description:
        "控制文件系统、网络、命令、批准和审查行为。",
      pages: [
        {
          title: "权限",
          description:
            "为文件系统、命令和网络访问选择配置文件。",
          href: "/codex/permissions",
          icon: "lock",
        },
        {
          title: "沙盒",
          description:
            "了解 Codex 如何隔离命令和文件更改。",
          href: "/codex/sandboxing",
          icon: "shieldCheck",
        },
        {
          title: "自动审查",
          description:
            "根据配置的策略自动审查操作。",
          href: "/codex/sandboxing/auto-review",
          icon: "dataControls",
        },
        {
          title: "代理批准和安全",
          description: "决定 Codex 在采取行动前何时必须询问。",
          href: "/codex/agent-approvals-security",
          icon: "userLock",
        },
        {
          title: "互联网访问",
          description: "控制云聊天可以访问的域。",
          href: "/codex/cloud/internet-access",
          icon: "webSearch",
        },
      ],
    },
    {
      title: "Codex Security",
      description: "查找、了解并修复漏洞。",
      pages: [
        {
          title: "Codex Security 概览",
          description:
            "评估代码并将审查后的发现转化为针对性的修复。",
          href: "/codex/security",
          icon: "shieldCheck",
        },
        {
          title: "Codex Security 云端常见问题解答",
          description:
            "获取有关云扫描、发现、隐私和访问的解答。",
          href: "/codex/security/faq",
          icon: "chat",
        },
        {
          title: "Codex Security 插件",
          description:
            "从 ChatGPT 桌面应用和 Codex CLI 运行安全工作流。",
          href: "/codex/security/plugin",
          icon: "plugin",
        },
        {
          title: "Codex Security 云端设置",
          description:
            "连接存储库并配置云安全扫描。",
          href: "/codex/security/setup",
          icon: "storage",
        },
        {
          title: "威胁模型",
          description: "审查并改进代码库的威胁模型。",
          href: "/codex/security/threat-model",
          icon: "webSearch",
        },
      ],
    },
    {
      title: "安全",
      description: "审查网络安全任务的政策和防护措施。",
      pages: [
        {
          title: "网络安全",
          description:
            "了解 Codex 如何处理安全敏感的请求。",
          href: "/codex/cyber-safety",
          icon: "userLock",
        },
      ],
    },
  ]}
/>

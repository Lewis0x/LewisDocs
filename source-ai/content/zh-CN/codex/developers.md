---
title: 开发者
source_id: codex/developers
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/developers
owner: OpenAI
content_sha256: 7d9c23f24eed093f4f47bcbbdb9cd2f60c8c2730192a489ac67d5d3c26399742
translation_of: codex/developers
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/developers)

Content owner: OpenAI

# 开发者

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。可以通过在页面 URL 后附加 `.md` 来获取文档页面的 Markdown 版本。

<CodexDocsOverviewLanding
  title="开发者"
  description="在代码库、开发环境、自动化和团队工具中使用 Codex。"
  intro="Codex 支持日常的代码工作以及跨本地和云环境的深度集成。其开发者工作流涵盖代码审查、集成终端、可重用的技能与插件、通过 SDK 和应用服务器（App Server）进行的自动化、团队工具，以及每个界面的参考资料。"
  primaryCta={{
    label: "探索工作流",
    href: "/codex/code-review?surface=app",
  }}
  hero={{
    illustration: "developers",
    backgroundImage: "/images/codex/codex-wallpaper-1.webp",
    alt: "Web 应用程序的 Codex 输出、集成终端和代码审查",
  }}
  sections={[
    {
      title: "开发工作流",
      description: "在 ChatGPT 中审查更改并使用开发工具。",
      pages: [
        {
          title: "代码审查",
          description: "在发布前审查更改并处理反馈。",
          href: "/codex/code-review",
          icon: "shieldCheck",
        },
        {
          title: "集成终端",
          description:
            "在 ChatGPT 桌面应用中运行命令并检查输出。",
          href: "/codex/integrated-terminal",
          icon: "terminal",
        },
      ],
    },
    {
      title: "扩展与自动化",
      description:
        "打包开发工作流并运行确定性自动化。",
      pages: [
        {
          title: "构建技能",
          description:
            "为 ChatGPT 和 Codex 中的可重复任务打包指令和资源。",
          href: "/codex/build-skills",
          icon: "tools",
        },
        {
          title: "构建插件",
          description: "为 ChatGPT 和 Codex 打包技能和 MCP 服务器。",
          href: "/codex/build-plugins",
          icon: "connect",
        },
        {
          title: "钩子",
          description: "在 Codex 发出生命周期事件时运行自定义命令。",
          href: "/codex/hooks",
          icon: "terminal",
        },
      ],
    },
    {
      title: "环境",
      description: "选择开发工作的运行位置及其隔离方式。",
      pages: [
        {
          title: "环境",
          description: "比较本地、云端及运行任务的其他方式。",
          href: "/codex/environments/modes",
          icon: "workspace",
        },
        {
          title: "本地环境",
          description:
            "为项目和工作树配置安装脚本和操作。",
          href: "/codex/environments/local-environment",
          icon: "terminal",
        },
        {
          title: "云环境",
          description: "将工作委托给已配置的云环境。",
          href: "/codex/environments/cloud-environment",
          icon: "storage",
        },
        {
          title: "Git 工作树",
          description: "在独立的工作树中隔离并行更改。",
          href: "/codex/environments/git-worktrees",
          icon: "folder",
        },
      ],
    },
    {
      title: "使用 Codex 构建",
      description: "将 Codex 添加到产品、系统和自动化工作流中。",
      pages: [
        {
          title: "Codex SDK",
          description: "从您的应用程序中以编程方式控制 Codex。",
          href: "/codex/codex-sdk",
          icon: "code",
        },
        {
          title: "应用服务器",
          description: "与为 Codex 客户端提供支持的协议集成。",
          href: "/codex/app-server",
          icon: "storage",
        },
        {
          title: "MCP 服务器",
          description:
            "通过模型上下文协议公开 Codex 的功能。",
          href: "/codex/mcp-server",
          icon: "connect",
        },
        {
          title: "GitHub Action",
          description: "从 GitHub Actions 工作流中运行 Codex。",
          href: "/codex/github-action",
          icon: "github",
        },
        {
          title: "非交互模式",
          description: "从脚本和其他自动化系统中运行 Codex。",
          href: "/codex/non-interactive-mode",
          icon: "terminal",
        },
      ],
    },
    {
      title: "第三方集成",
      description: "从团队已经在使用的工具中委派和跟踪工作。",
      pages: [
        {
          title: "GitHub",
          description:
            "分配工作、审查更改，并推进到拉取请求。",
          href: "/codex/third-party/github",
          icon: "github",
        },
        {
          title: "Slack",
          description:
            "从外部讨论启动 Codex 聊天并返回结果。",
          href: "/codex/third-party/slack",
          icon: "chat",
        },
        {
          title: "Linear",
          description:
            "将议题分配给 Codex，并跟进工作直至交付。",
          href: "/codex/third-party/linear",
          icon: "threads",
        },
      ],
    },
    {
      title: "参考",
      description:
        "查找开发者界面的命令、设置和插件提交错误。",
      pages: [
        {
          title: "CLI 自定义",
          description:
            "调整语法高亮、主题和 Shell 行为。",
          href: "/codex/cli-customization",
          icon: "terminal",
        },
        {
          title: "开发者命令",
          description:
            "在桌面应用、Codex CLI 和 IDE 扩展中使用命令和斜杠命令。",
          href: "/codex/developer-commands?surface=app",
          icon: "terminal",
        },
        {
          title: "开发者设置",
          description:
            "配置桌面应用、Codex CLI 和 IDE 扩展以进行开发。",
          href: "/codex/developer-settings?surface=app",
          icon: "settings",
        },
      ],
    },
  ]}
/>

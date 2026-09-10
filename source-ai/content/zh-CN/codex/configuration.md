---
title: 配置
source_id: codex/configuration
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/configuration
owner: OpenAI
content_sha256: 4bba48797099af016511fc286e8dd5fd2af213c3cc6c057a5e8f00d44002c02f
translation_of: codex/configuration
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/configuration)

Content owner: OpenAI

# 配置

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。可以通过在页面 URL 后附加 `.md` 来获取文档页面的 Markdown 版本。

<CodexDocsOverviewLanding
  title="配置"
  description="设置默认值，添加持久上下文，并自定义 ChatGPT 和 Codex 开发者工具的工作方式。"
  intro="配置决定了 ChatGPT 和 Codex 开发者工具在聊天、仓库和机器之间的行为方式。持久上下文、配置文件、仓库指南、子智能体、外部连接和 Windows 设置协同工作，以确保这些工作流对于个人和团队保持一致。"
  primaryCta={{
    label: "探索自定义",
    href: "/codex/customization/overview",
  }}
  hero={{
    illustration: "configuration",
    backgroundImage: "/images/codex/codex-wallpaper-1.webp",
    alt: "ChatGPT 设置导航、配置文件选项和个性化控制",
  }}
  sections={[
    {
      title: "自定义",
      description:
        "调整体验并在聊天之间保留有用的上下文。",
      pages: [
        {
          title: "自定义概述",
          description:
            "通过指南、技能、MCP 和子智能体来自定义 ChatGPT 和 Codex。",
          href: "/codex/customization/overview",
          icon: "customize",
        },
        {
          title: "记忆",
          description: "让 ChatGPT 在跨聊天时保留有用的上下文。",
          href: "/codex/customization/memories",
          icon: "threads",
        },
        {
          title: "纪事",
          description:
            "了解持久记忆是如何收集和管理的。",
          href: "/codex/customization/chronicle",
          icon: "stack",
        },
      ],
    },
    {
      title: "配置文件",
      description:
        "使用配置文件和变量控制模型、工具、环境和默认值。",
      pages: [
        {
          title: "配置基础",
          description:
            "了解配置层并创建配置文件。",
          href: "/codex/config-file/config-basic",
          icon: "settings",
        },
        {
          title: "高级配置",
          description:
            "使用档案、提供商、策略和高级选项。",
          href: "/codex/config-file/config-advanced",
          icon: "dataControls",
        },
        {
          title: "配置参考",
          description: "查找每个受支持的配置键。",
          href: "/codex/config-file/config-reference",
          icon: "code",
        },
        {
          title: "环境变量",
          description: "设置在不同系统和会话之间变化的值。",
          href: "/codex/config-file/environment-variables",
          icon: "terminal",
        },
        {
          title: "配置示例",
          description:
            "从一个完整且带有注释的配置示例开始。",
          href: "/codex/config-file/config-sample",
          icon: "folder",
        },
      ],
    },
    {
      title: "智能体配置",
      description: "塑造智能体如何协作并遵循项目指南。",
      pages: [
        {
          title: "AGENTS.md",
          description: "为 Codex 提供针对仓库的持久指令。",
          href: "/codex/agent-configuration/agents-md",
          icon: "folder",
        },
        {
          title: "子智能体",
          description: "将专注的任务委派给专门的智能体。",
          href: "/codex/agent-configuration/subagents",
          icon: "robot",
        },
        {
          title: "速度",
          description: "控制 Codex 工作的速度和深度。",
          href: "/codex/agent-configuration/speed",
          icon: "settings",
        },
        {
          title: "规则",
          description: "定义 Codex 可以自动运行的命令。",
          href: "/codex/agent-configuration/rules",
          icon: "dataControls",
        },
      ],
    },
    {
      title: "扩展 ChatGPT 和 Codex",
      description: "封装知识，连接服务，并添加功能。",
      pages: [
        {
          title: "录制与重放",
          description:
            "向 ChatGPT 或 Codex 展示工作流并将其转化为可重用的技能。",
          href: "/codex/extend/record-and-replay",
          icon: "tools",
        },
        {
          title: "MCP",
          description:
            "将 Codex 开发者工具连接到外部工具与上下文。",
          href: "/codex/extend/mcp",
          icon: "connect",
        },
      ],
    },
    {
      title: "Windows",
      description: "在 Windows 上原生运行 Codex 或在 WSL 内运行。",
      pages: [
        {
          title: "ChatGPT 桌面应用",
          description:
            "配合 PowerShell 或 WSL 工作流使用 ChatGPT 桌面应用。",
          href: "/codex/windows/windows-app",
          icon: "computerUse",
        },
        {
          title: "Windows 沙盒",
          description:
            "以原生文件系统和命令隔离运行 Codex。",
          href: "/codex/windows/windows-sandbox",
          icon: "lock",
        },
        {
          title: "WSL",
          description: "在由 Windows 管理的 Linux 环境中使用 Codex。",
          href: "/codex/windows/wsl",
          icon: "terminal",
        },
      ],
    },
  ]}
/>

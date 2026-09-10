---
title: 管理
source_id: codex/administration
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/administration
owner: OpenAI
content_sha256: 2edb8f5a9c815ff04561a852e5d148674402ca120a8731df7fa1559c9d550aa0
translation_of: codex/administration
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/administration)

Content owner: OpenAI

# 管理

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。可以通过在页面 URL 后附加 `.md` 来获取文档页面的 Markdown 版本。

<CodexDocsOverviewLanding
  title="管理"
  description="为 ChatGPT、Codex 开发者工具、API、插件和连接的系统设置访问权限和策略边界。"
  intro="管理涵盖六个相关的边界：ChatGPT 工作区访问；ChatGPT 桌面应用、Codex CLI 和 IDE 扩展中涵盖功能的本地运行时策略；Codex 云资格；平台 API 访问；插件可用性和连接器权限；以及连接系统中的权限。从工作区身份和访问开始，然后应用每次部署所需的运行时和源系统控制。"
  primaryCta={{
    label: "探索身份验证",
    href: "/codex/auth?surface=app",
  }}
  hero={{
    illustration: "administration",
    backgroundImage: "/images/codex/codex-wallpaper-1.webp",
    alt: "ChatGPT 工作区成员、组、访问令牌和角色控制",
  }}
  sections={[
    {
      title: "入门",
      description:
        "从发布指南开始，然后使用每个控制边界的参考页面。",
      pages: [
        {
          title: "管理员发布指南",
          description:
            "计划访问权限、分配所有者、配置控制并验证发布。",
          href: "/codex/enterprise/admin-setup",
          icon: "users",
        },
        {
          title: "ChatGPT Work 管理员常见问题解答",
          description:
            "查看 ChatGPT Work 的访问权限、数据、治理、使用和事件控制。",
          href: "/codex/enterprise/work-admin-faq",
          icon: "userLock",
        },
      ],
    },
    {
      title: "身份和身份验证",
      description:
        "选择用户的登录方式，并为编程工作流颁发凭证。",
      pages: [
        {
          title: "身份验证概述",
          description:
            "比较登录方法、凭证存储和强制控制措施。",
          href: "/codex/auth",
          icon: "key",
        },
        {
          title: "访问令牌",
          description: "创建和管理用于编程访问的令牌。",
          href: "/codex/enterprise/access-tokens",
          icon: "lock",
        },
      ],
    },
    {
      title: "工作区访问、策略和模型",
      description:
        "分配 ChatGPT 工作区访问权限，并将其与本地运行时策略、Codex 云访问和平台 API 访问分开。",
      pages: [
        {
          title: "组和预配",
          description:
            "管理手动和 SCIM 组、预配和发布队列。",
          href: "/codex/enterprise/groups-and-provisioning",
          icon: "users",
        },
        {
          title: "角色和工作区权限",
          description:
            "使用工作区、运行时、API、插件和源系统控制的规范映射。",
          href: "/codex/enterprise/roles-and-workspace-permissions",
          icon: "userLock",
        },
        {
          title: "托管配置",
          description:
            "在受支持的设备上分发托管设置，并针对 ChatGPT 桌面应用、Codex CLI 和 IDE 扩展中的涵盖功能强制执行运行时要求。",
          href: "/codex/enterprise/managed-configuration",
          icon: "dataControls",
        },
        {
          title: "HIPAA 配置",
          description:
            "为可能处理受保护健康信息的工作流配置本地运行时保护措施。",
          href: "/codex/hipaa-configuration",
          icon: "shieldCheck",
        },
        {
          title: "工作区模型可用性",
          description:
            "区分 ChatGPT、ChatGPT 桌面应用中的 Codex、Codex CLI、IDE 扩展、Codex 云和平台 API 的模型访问权限。",
          href: "/codex/enterprise/workspace-model-availability",
          icon: "settings",
        },
      ],
    },
    {
      title: "插件与连接器控制",
      description:
        "控制插件安装、内置技能、连接器支持的能力及已连接服务的访问。",
      pages: [
        {
          title: "插件控制",
          description:
            "管理插件可用性、连接器访问与操作，以及源系统权限。",
          href: "/codex/enterprise/apps-and-connectors",
          icon: "connect",
        },
        {
          title: "技能控制",
          description:
            "比较 ChatGPT 工作区、本地文件系统与插件技能控制。",
          href: "/codex/enterprise/skills",
          icon: "tools",
        },
      ],
    },
    {
      title: "使用、治理与合规",
      description:
        "衡量采用情况，并将报告或审计数据路由至其归属的系统。",
      pages: [
        {
          title: "治理",
          description:
            "针对每个问题选择合适的分析、支出与审计界面。",
          href: "/codex/enterprise/governance",
          icon: "shieldCheck",
        },
        {
          title: "工作区分析",
          description:
            "查看工作区级别的 ChatGPT 采用情况与 Codex 使用情况。",
          href: "/codex/enterprise/workspace-analytics",
          icon: "dataControls",
        },
        {
          title: "分析 API",
          description:
            "使用 Codex 分析 API 自动化开发者活动与代码审查报告。",
          href: "/codex/enterprise/analytics-api",
          icon: "code",
        },
        {
          title: "合规 API 与审计事件",
          description:
            "导出活动记录，用于审计与调查工作流。",
          href: "/codex/enterprise/compliance-api",
          icon: "userLock",
        },
      ],
    },
    {
      title: "部署与模型提供商",
      description:
        "部署 Windows 应用，连接受管主机，或配置支持的外部模型提供商。",
      pages: [
        {
          title: "Windows 应用部署",
          description:
            "为受管的 Windows 设备选择安装与更新路径。",
          href: "/codex/enterprise/windows-deployment",
          icon: "settings",
        },
        {
          title: "远程连接",
          description: "启动并控制已连接计算机上的工作。",
          href: "/codex/remote-connections",
          icon: "connect",
        },
        {
          title: "Amazon Bedrock",
          description:
            "配置支持的本地客户端，以使用通过 Bedrock 提供的模型。",
          href: "/codex/amazon-bedrock",
          icon: "storage",
        },
      ],
    },
  ]}
/>

---
title: 词汇表
source_id: codex/glossary
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/glossary
owner: OpenAI
content_sha256: 16082fb4f60b09a940ced5bd186100e6c427b4da021ed7afc8f6aabb1112d40e
translation_of: codex/glossary
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/glossary)

Content owner: OpenAI

# 词汇表

> 有关完整的文档索引，请参阅 [llms.txt](https://learn.chatgpt.com/llms.txt)。通过在页面 URL 后附加 `.md`，可获取文档页面的 Markdown 版本。

将此词汇表作为应用程序、CLI、IDE 扩展、云、SDK 和相关集成中 Codex 术语的快速参考。

<GlossaryTable
  client:load
  searchPlaceholder="按术语、定义或界面筛选"
  searchLabel="搜索词汇表术语"
  emptyStateMessage="没有符合您搜索的词汇表术语。"
  maxVisibleEntries={100}
  options={[
    {
      key: "操作",
      href: "/codex/agent-approvals-security",
      appliesTo: "桌面应用程序, 网页端, 移动端, CLI, IDE 扩展, 云",
      description:
        "由人、ChatGPT 或 Codex 执行的操作，例如编辑文件、运行命令或使用已连接的服务。",
    },
    {
      key: "代理",
      href: "/codex",
      appliesTo: "桌面应用程序, CLI, IDE 扩展, 云",
      description:
        "对上下文进行推理、使用工具并完成任务的 Codex 代理。",
    },
    {
      key: "AGENTS.md",
      href: "/codex/agent-configuration/agents-md",
      appliesTo: "桌面应用程序, CLI, IDE 扩展, 云",
      description:
        "为 Codex 提供持久指令的存储库或用户指导文件。",
    },
    {
      key: "分析仪表板",
      href: "/codex/enterprise/workspace-analytics",
      appliesTo: "企业版",
      description:
        "用于 ChatGPT 工作区采用情况和以 Codex 为重点的报告的管理中心。",
    },
    {
      key: "API 密钥登录",
      href: "/codex/auth#sign-in-with-an-api-key",
      appliesTo: "桌面应用程序, CLI, IDE 扩展",
      description: "使用 OpenAI API 密钥进行身份验证。",
    },
    {
      key: "批准策略",
      href: "/codex/agent-approvals-security#sandbox-and-approvals",
      appliesTo: "桌面应用程序, CLI, IDE 扩展",
      description: "关于 Codex 在采取行动前何时必须询问的规则。",
    },
    {
      key: "批准请求",
      href: "/codex/agent-approvals-security#automatic-approval-reviews",
      appliesTo: "桌面应用程序, CLI, IDE 扩展",
      description: "Codex 请求允许执行受限操作。",
    },
    {
      key: "应用程序（配置）",
      href: "/codex/plugins",
      appliesTo: "桌面应用程序, CLI, IDE 扩展",
      description:
        "在 `apps` 名称下存储连接器设置的 Codex 配置和应用服务器字段。",
    },
    {
      key: "应用截图",
      href: "/codex/appshots",
      appliesTo: "桌面应用程序",
      description:
        "发送到 ChatGPT 或 Codex 聊天的最前端应用窗口快照。",
    },
    {
      key: "身份验证缓存",
      href: "/codex/auth#login-caching",
      appliesTo: "桌面应用程序, CLI, IDE 扩展",
      description: "由 Codex 重复使用的本地存储登录凭据。",
    },
    {
      key: "自动批准审查",
      href: "/codex/agent-approvals-security#automatic-approval-reviews",
      appliesTo: "桌面应用程序, CLI, IDE 扩展",
      description:
        "在符合条件的批准请求继续之前，对其进行基于模型的审查。",
    },
    {
      key: "计划任务",
      href: "/codex/automations",
      appliesTo: "桌面应用程序, 网页端",
      description:
        "ChatGPT 在未来时间或按周期计划运行的提示词，具有其自身的设置和运行历史记录。",
    },
    {
      key: "计划运行",
      href: "/codex/automations#managing-tasks",
      appliesTo: "桌面应用程序, 网页端",
      description:
        "计划任务的一次执行，包括其状态以及产生的任何发现。",
    },
    {
      key: "浏览器中的 Computer Use",
      href: "/codex/browser?surface=app#app-computer-use-in-the-browser",
      appliesTo: "桌面应用程序",
      description:
        "允许 ChatGPT 直接操作内置浏览器的功能。",
    },
    {
      key: "聊天",
      href: "/codex/projects#start-a-chat",
      appliesTo: "桌面应用, Web, 移动端, CLI, IDE 扩展, 云端",
      description:
        "用于与 ChatGPT 或 Codex 交换消息的保存空间，包括共享上下文、结果和操作。快速聊天从 Codex 启动 ChatGPT 聊天。",
    },
    {
      key: "ChatGPT 登录",
      href: "/codex/auth#sign-in-with-chatgpt",
      appliesTo: "桌面应用, CLI, IDE 扩展, 云端",
      description:
        "使用 ChatGPT 账户和工作区权限进行身份验证。",
    },
    {
      key: "Chronicle",
      href: "/codex/customization/chronicle",
      appliesTo: "桌面应用",
      description:
        "根据最近的屏幕上下文构建记忆的可选功能。",
    },
    {
      key: "云端",
      href: "/codex/cloud",
      appliesTo: "桌面应用, IDE 扩展, Web",
      description:
        "Codex 在 OpenAI 管理的环境中远程工作的模式。",
    },
    {
      key: "云端环境",
      href: "/codex/environments/cloud-environment",
      appliesTo: "云端",
      description: "用于 Codex 云端聊天的已配置容器设置。",
    },
    {
      key: "云端聊天",
      href: "/codex/environments/cloud-environment#how-codex-cloud-tasks-run",
      appliesTo: "云端",
      description: "在云环境中远程运行的 Codex 聊天。",
    },
    {
      key: "Codex",
      href: "/codex",
      appliesTo: "桌面应用, CLI, IDE 扩展, Web, 云端, SDK",
      description: "OpenAI 用于软件开发任务的编码智能体。",
    },
    {
      key: "ChatGPT 桌面应用",
      href: "/codex/app",
      appliesTo: "桌面端",
      description:
        "包含 ChatGPT 和 Codex 的桌面应用，包括聊天和工作、项目、文件预览、计划任务以及开发者工具。",
    },
    {
      key: "Codex 应用服务器",
      href: "/codex/app-server",
      appliesTo: "桌面应用, IDE 扩展, SDK",
      description:
        "用于在自定义客户端中嵌入 Codex 线程、轮次、批准、历史记录和流式事件的本地 JSON-RPC 服务器。",
    },
    {
      key: "Codex CLI",
      href: "/codex/cli",
      appliesTo: "终端",
      description:
        "用于以交互方式或在脚本中运行 Codex 的终端客户端。",
    },
    {
      key: "Codex 云端",
      href: "/codex/cloud",
      appliesTo: "Web, 桌面应用, IDE 扩展",
      description:
        "由 OpenAI 管理的执行环境，Codex 可以在其中远程处理存储库任务。",
    },
    {
      key: "codex exec",
      href: "/codex/non-interactive-mode",
      appliesTo: "CLI",
      description:
        "用于从脚本或 CI 非交互式运行 Codex 的 CLI 命令。",
    },
    {
      key: "Codex IDE 扩展",
      href: "/codex/ide",
      appliesTo: "IDE",
      description:
        "用于在 VS Code、JetBrains IDE、Cursor 和 Windsurf 等 IDE 中使用 Codex 的编辑器集成。",
    },
    {
      key: "Codex SDK",
      href: "/codex/codex-sdk",
      appliesTo: "SDK",
      description:
        "用于构建 Codex 驱动的工作流或集成的编程接口。",
    },
    {
      key: "Codex 管理的工作树",
      href: "/codex/environments/git-worktrees#codex-managed-and-permanent-worktrees",
      appliesTo: "桌面应用",
      description: "Codex 为聊天创建和管理的临时工作树。",
    },
    {
      key: "压缩",
      href: "/codex/prompting#context",
      appliesTo: "桌面应用, CLI, IDE 扩展, 云端",
      description:
        "总结较旧的上下文，以便长时间运行的工作能够继续。",
    },
    {
      key: "合规性 API",
      href: "/codex/enterprise/compliance-api",
      appliesTo: "企业版",
      description:
        "用于导出受支持的 ChatGPT 工作区记录和审核元数据的 API。",
    },
    {
      key: "Computer Use",
      href: "/codex/computer-use",
      appliesTo: "桌面应用",
      description:
        "允许 ChatGPT 通过用户界面与其他应用程序交互的桌面功能。",
    },
    {
      key: "config.toml",
      href: "/codex/config-file/config-reference#configtoml",
      appliesTo: "桌面应用、CLI、IDE 扩展",
      description: "本地 Codex 配置文件。",
    },
    {
      key: "已连接的主机",
      href: "/codex/remote-connections#what-comes-from-the-connected-host",
      appliesTo: "桌面应用、移动端",
      description:
        "通过 Remote 打开的 ChatGPT 或 Codex 聊天提供文件、工具和 shell 访问权限的计算机或开发环境。",
    },
    {
      key: "连接器",
      href: "/codex/plugins",
      appliesTo: "桌面应用（ChatGPT Work、Codex）、Web（ChatGPT Work）",
      description:
        "插件的一个组件，用于将 ChatGPT 或 Codex 连接到外部服务中的数据和操作。",
    },
    {
      key: "对话",
      href: "/codex/projects#start-a-chat",
      appliesTo: "桌面应用、Web、移动端、CLI、IDE 扩展、Cloud",
      description:
        "在聊天中，人与 ChatGPT 或 Codex 之间持续进行的消息和共享上下文交换。",
    },
    {
      key: "容器缓存",
      href: "/codex/environments/cloud-environment#container-caching",
      appliesTo: "Cloud",
      description:
        "保存的云容器状态，可重复使用以加快未来的云聊天速度。",
    },
    {
      key: "上下文",
      href: "/codex/prompting#context",
      appliesTo: "桌面应用、CLI、IDE 扩展、Cloud、SDK",
      description:
        "Codex 在工作时可以使用的信息，例如文件、之前的消息、工具输出和指令。",
    },
    {
      key: "上下文窗口",
      href: "/api/docs/guides/conversation-state#managing-the-context-window",
      appliesTo: "桌面应用、CLI、IDE 扩展、Cloud、SDK",
      description:
        "模型一次可以处理的最大信息量。",
    },
    {
      key: "自定义智能体",
      href: "/codex/agent-configuration/subagents#custom-agents",
      appliesTo: "桌面应用、CLI",
      description:
        "用户定义的智能体角色，具有自己的指令和设置。",
    },
    {
      key: "拒绝读取规则",
      href: "/codex/permissions#deny-reads-with-exact-paths-or-globs",
      appliesTo: "桌面应用、CLI、IDE 扩展、Enterprise",
      description:
        "文件系统权限规则，防止 Codex 读取敏感路径或 glob 匹配项。",
    },
    {
      key: "差异",
      href: "/codex/code-review?surface=app#app-what-changes-it-shows",
      appliesTo: "桌面应用、Git、Review",
      description:
        "显示的 Git 文件变更集合，用于检查、评论、暂存或撤销。",
    },
    {
      key: "域名允许列表",
      href: "/codex/cloud/internet-access#domain-allowlist",
      appliesTo: "Cloud",
      description:
        "启用智能体互联网访问时 Codex 云端可以访问的域名集合。",
    },
    {
      key: "环境（本地）",
      href: "/codex/environments/local-environment",
      appliesTo: "桌面应用、工作树",
      description:
        "桌面应用配置，用于告诉 Codex 如何为项目设置工作树。",
    },
    {
      key: "环境变量",
      href: "/codex/environments/cloud-environment#environment-variables-and-secrets",
      appliesTo: "Cloud、CLI、IDE 扩展",
      description:
        "在任务执行期间可用的运行时配置值。",
    },
    {
      key: "临时会话",
      href: "/codex/non-interactive-mode#basic-usage",
      appliesTo: "CLI",
      description:
        "非交互式运行，在完成后跳过保存会话状态。",
    },
    {
      key: "快速模式",
      href: "/codex/agent-configuration/speed#fast-mode",
      appliesTo: "CLI、IDE 扩展",
      description:
        "速度设置，使支持的模型以更高的点数消耗换取更快的响应速度。",
    },
    {
      key: "文件系统权限",
      href: "/codex/permissions#filesystem-permissions",
      appliesTo: "桌面应用、命令行工具 (CLI)、IDE 扩展",
      description:
        "授予或拒绝对路径的读写访问权限的权限配置文件规则。",
    },
    {
      key: "发现",
      href: "/codex/automations#managing-tasks",
      appliesTo: "桌面应用",
      description: "由计划任务显现的显著结果或问题。",
    },
    {
      key: "完全访问",
      href: "/codex/sandboxing#configure-defaults",
      appliesTo: "桌面应用、命令行工具 (CLI)、IDE 扩展",
      description: "Codex 在不受正常沙盒限制的情况下运行的模式。",
    },
    {
      key: "Git 工作树",
      href: "/codex/environments/git-worktrees#whats-a-worktree",
      appliesTo: "桌面应用、Git",
      description:
        "同一存储库的第二次检出，用于并行分支工作。",
    },
    {
      key: "交接",
      href: "/codex/environments/git-worktrees#working-between-local-and-worktree",
      appliesTo: "桌面应用",
      description: "在本地和工作树之间移动聊天及其相关工作。",
    },
    {
      key: "心跳",
      href: "/codex/automations#schedule-a-task-inside-a-chat",
      appliesTo: "桌面应用",
      description:
        "将 ChatGPT 带回同一聊天的重复计划任务。",
    },
    {
      key: "钩子",
      href: "/codex/hooks",
      appliesTo: "桌面应用、命令行工具 (CLI)、IDE 扩展",
      description:
        "当 Codex 事件匹配时运行的生命周期处理程序，例如工具使用、权限请求或当一轮对话停止时。",
    },
    {
      key: "钩子事件",
      href: "/codex/hooks#config-shape",
      appliesTo: "桌面应用、命令行工具 (CLI)、IDE 扩展",
      description: "可以运行已配置的钩子处理程序的生命周期点。",
    },
    {
      key: "代码块",
      href: "/codex/code-review?surface=app#app-staging-and-reverting-files",
      appliesTo: "桌面应用、Git、审查",
      description:
        "差异中可独立暂存、取消暂存或撤销的连续部分。",
    },
    {
      key: "内联评论",
      href: "/codex/code-review?surface=app#app-inline-comments-for-feedback",
      appliesTo: "桌面应用",
      description: "附加到差异的特定行反馈。",
    },
    {
      key: "实时网络搜索",
      href: "/codex/config-file/config-basic#web-search-mode",
      appliesTo: "桌面应用、命令行工具 (CLI)、IDE 扩展",
      description: "用于获取当前信息的实时网络查找。",
    },
    {
      key: "本地",
      href: "/codex/environments/git-worktrees#working-between-local-and-worktree",
      appliesTo: "桌面应用、命令行工具 (CLI)、IDE 扩展",
      description: "Codex 在用户计算机上工作的模式。",
    },
    {
      key: "本地聊天",
      href: "/codex/environments/modes",
      appliesTo: "桌面应用、命令行工具 (CLI)、IDE 扩展",
      description: "在用户机器上运行的 ChatGPT 或 Codex 聊天。",
    },
    {
      key: "维护脚本",
      href: "/codex/environments/cloud-environment#container-caching",
      appliesTo: "云端",
      description: "缓存云容器恢复时运行的可选脚本。",
    },
    {
      key: "托管配置",
      href: "/codex/enterprise/managed-configuration",
      appliesTo: "企业版",
      description: "由组织控制的 Codex 默认设置和限制。",
    },
    {
      key: "MCP",
      href: "/codex/extend/mcp",
      appliesTo: "桌面应用、命令行工具 (CLI)、IDE 扩展",
      description:
        "模型上下文协议，一种用于将 Codex 连接到外部工具和上下文的标准。",
    },
    {
      key: "MCP 资源",
      href: "/codex/extend/mcp#supported-mcp-features",
      appliesTo: "桌面应用、命令行工具 (CLI)、IDE 扩展",
      description:
        "由 MCP 服务器公开供 Codex 检查的可读上下文。",
    },
    {
      key: "MCP 服务器",
      href: "/codex/extend/mcp#supported-mcp-features",
      appliesTo: "桌面应用、命令行工具 (CLI)、IDE 扩展",
      description: "通过 MCP 公开的外部工具或上下文提供程序。",
    },
    {
      key: "MCP 工具",
      href: "/codex/extend/mcp#supported-mcp-features",
      appliesTo: "桌面应用、CLI、IDE 扩展",
      description:
        "Codex 在任务期间可以调用的 MCP 服务器公开的操作。",
    },
    {
      key: "MDM",
      href: "/codex/enterprise/managed-configuration#macos-managed-preferences-mdm",
      appliesTo: "企业版",
      description:
        "用于分发设备配置文件和受管 Codex 设置的移动设备管理工具。",
    },
    {
      key: "Memories",
      href: "/codex/customization/memories",
      appliesTo: "桌面应用、CLI、IDE 扩展",
      description: "Codex 可在跨会话中重复使用的本地存储上下文。",
    },
    {
      key: "Model",
      href: "/codex/models",
      appliesTo: "桌面应用、CLI、IDE 扩展、云、SDK",
      description: "Codex 用于推理和工具工作的 AI 模型。",
    },
    {
      key: "Network access",
      href: "/codex/agent-approvals-security#network-access",
      appliesTo: "桌面应用、CLI、IDE 扩展、云",
      description:
        "允许命令或环境访问互联网的权限。",
    },
    {
      key: "Network policy",
      href: "/codex/agent-approvals-security#network-policy",
      appliesTo: "桌面应用、CLI、IDE 扩展",
      description:
        "用于约束沙盒出站网络流量的基于域名的允许和拒绝规则。",
    },
    {
      key: "Non-interactive mode",
      href: "/codex/non-interactive-mode",
      appliesTo: "CLI",
      description: "用于从脚本或 CI 运行 Codex 的 CLI 模式。",
    },
    {
      key: "Output schema",
      href: "/codex/non-interactive-mode#create-structured-outputs-with-a-schema",
      appliesTo: "CLI",
      description:
        "传递给 `codex exec` 以约束最终响应的 JSON Schema。",
    },
    {
      key: "Permanent worktree",
      href: "/codex/environments/git-worktrees#codex-managed-and-permanent-worktrees",
      appliesTo: "桌面应用",
      description: "作为独立项目保留的长期工作树。",
    },
    {
      key: "Permission profile",
      href: "/codex/permissions#define-and-select-a-profile",
      appliesTo: "桌面应用、CLI、IDE 扩展",
      description:
        "结合文件系统和网络规则以执行本地命令的具名最小特权策略。",
    },
    {
      key: "Plan",
      href: "/codex/learn/best-practices#plan-first-for-difficult-tasks",
      appliesTo: "桌面应用、CLI、IDE 扩展、云",
      description: "Codex 为完成任务而提出或跟踪的步骤。",
    },
    {
      key: "Plugin",
      href: "/codex/plugins",
      appliesTo: "桌面应用 (ChatGPT Work、Codex)、网页版 (ChatGPT Work)、CLI",
      description:
        "可安装的功能捆绑包，例如技能、连接器和工具，通过 ChatGPT 和 Codex 共享的通用目录分发。",
    },
    {
      key: "Plugin manifest",
      href: "https://developers.openai.com/plugins/build/plugins#plugin-structure",
      appliesTo: "插件编写",
      description:
        "标识插件并指向捆绑技能、连接器映射、MCP 服务器、挂钩和元数据的插件元数据文件。",
    },
    {
      key: "Prefix rule",
      href: "/codex/agent-configuration/rules#understand-the-rules-language",
      appliesTo: "桌面应用、CLI、IDE 扩展、企业版",
      description:
        "允许、提示或禁止匹配命令前缀的命令规则模式。",
    },
    {
      key: "Profile",
      href: "/codex/config-file/config-advanced#profiles",
      appliesTo: "CLI、IDE 扩展",
      description: "Codex 的具名配置预设。",
    },
    {
      key: "Progressive disclosure",
      href: "/codex/build-skills",
      appliesTo: "桌面应用、网页版 (ChatGPT Work)、CLI、IDE 扩展",
      description:
        "仅在需要时加载技能详情以保留上下文。",
    },
    {
      key: "Project",
      href: "/codex/projects",
      appliesTo: "桌面应用",
      description:
        "一组相关的聊天和共享资源，或用于基于文件工作的本地文件夹。",
    },
    {
      key: "Prompt",
      href: "/codex/prompting",
      appliesTo: "桌面应用、CLI、IDE 扩展、云、SDK",
      description: "发送给 ChatGPT 或 Codex 的问题、指令或目标。",
    },
    {
      key: "拉取请求审查",
      href: "/codex/code-review?surface=app#app-pull-request-reviews",
      appliesTo: "桌面应用、CLI、GitHub",
      description: "Codex 对拉取请求变更的审查或反馈。",
    },
    {
      key: "RBAC",
      href: "/codex/enterprise/roles-and-workspace-permissions",
      appliesTo: "企业版",
      description: "用于工作区权限的基于角色的访问控制。",
    },
    {
      key: "只读模式",
      href: "/codex/sandboxing",
      appliesTo: "桌面应用、CLI、IDE 扩展",
      description:
        "Codex 可以检查但未经批准不得修改的模式。",
    },
    {
      key: "推理努力",
      href: "/codex/config-file/config-basic#reasoning-effort",
      appliesTo: "桌面应用、CLI、IDE 扩展、SDK",
      description:
        "控制模型使用多少推理预算的设置。",
    },
    {
      key: "远程连接",
      href: "/codex/remote-connections",
      appliesTo: "桌面应用、移动端",
      description:
        "允许您通过连接的主机在另一台设备上访问 ChatGPT 或 Codex 聊天的连接。",
    },
    {
      key: "requirements.toml",
      href: "/codex/config-file/config-reference#requirementstoml",
      appliesTo: "企业版",
      description: "用于受管 Codex 设置的管理员强制要求文件。",
    },
    {
      key: "审查窗格",
      href: "/codex/code-review?surface=app",
      appliesTo: "桌面应用",
      description:
        "用于检查差异、评论和 Git 更改的桌面应用视图。",
    },
    {
      key: "规则",
      href: "/codex/agent-configuration/rules",
      appliesTo: "桌面应用、CLI、IDE 扩展",
      description:
        "允许、提示或拒绝命令前缀或权限异常的策略。",
    },
    {
      key: "沙盒",
      href: "/codex/sandboxing",
      appliesTo: "桌面应用、CLI、IDE 扩展",
      description:
        "强制限制 Codex 命令可以访问或修改内容的边界。",
    },
    {
      key: "沙盒模式",
      href: "/codex/config-file/config-basic#sandbox-level",
      appliesTo: "桌面应用、CLI、IDE 扩展",
      description:
        "定义 Codex 文件系统和网络限制的配置。",
    },
    {
      key: "沙盒预设",
      href: "/codex/codex-sdk#sandbox-presets",
      appliesTo: "SDK",
      description:
        "用于常见沙盒策略（例如只读、工作区写入或完全访问）的 SDK 简写。",
    },
    {
      key: "计划任务",
      href: "/codex/automations",
      appliesTo: "桌面应用",
      description: "定时任务的定时规则。",
    },
    {
      key: "密钥",
      href: "/codex/environments/cloud-environment#environment-variables-and-secrets",
      appliesTo: "云",
      description:
        "安装脚本可用的加密值，但在代理阶段之前会被移除。",
    },
    {
      key: "安装脚本",
      href: "/codex/environments/local-environment#setup-scripts",
      appliesTo: "桌面应用工作树",
      description:
        "在代理启动之前运行以安装依赖项或准备工具的脚本。",
    },
    {
      key: "技能",
      href: "/codex/build-skills",
      appliesTo: "桌面应用、Web (ChatGPT Work)、CLI、IDE 扩展",
      description:
        "包含指令和可选脚本或引用的可重用工作流包。",
    },
    {
      key: "技能调用",
      href: "/codex/build-skills#how-codex-uses-skills",
      appliesTo: "桌面应用、Web (ChatGPT Work)、CLI、IDE 扩展",
      description: "对技能的显式或隐式激活。",
    },
    {
      key: "斜杠命令",
      href: "/codex/developer-commands?surface=cli",
      appliesTo: "CLI",
      description:
        "带有前导斜杠的命令，用于控制或检查 Codex CLI 会话。",
    },
    {
      key: "独立计划任务",
      href: "/codex/automations",
      appliesTo: "Desktop app, Web",
      description:
        "计划任务，其每次运行都会启动一个新聊天，并在分类中报告结果。",
    },
    {
      key: "STDIO MCP 服务器",
      href: "/codex/extend/mcp#stdio-servers",
      appliesTo: "CLI, IDE extension",
      description:
        "由配置的命令和参数作为本地进程启动的 MCP 服务器。",
    },
    {
      key: "可流式传输的 HTTP MCP 服务器",
      href: "/codex/extend/mcp#streamable-http-servers",
      appliesTo: "CLI, IDE extension",
      description:
        "通过 HTTP 访问的 MCP 服务器，可选择使用 Bearer token 或 OAuth 身份验证。",
    },
    {
      key: "子代理",
      href: "/codex/agent-configuration/subagents",
      appliesTo: "Desktop app, CLI",
      description: "生成的专门用于处理任务某一部分的子代理。",
    },
    {
      key: "子代理工作流",
      href: "/codex/agent-configuration/subagents#core-terms",
      appliesTo: "Desktop app, CLI",
      description:
        "Codex 并行运行委派的代理并合并其结果的工作流。",
    },
    {
      key: "独立任务",
      href: "/codex/projects",
      appliesTo: "Desktop app, CLI, IDE extension, Cloud",
      description: "未归类在项目中的 Codex 任务。",
    },
    {
      key: "任务",
      href: "/codex/projects",
      appliesTo: "Desktop app, Web, Mobile, CLI, IDE extension, Cloud",
      description:
        "ChatGPT 或 Codex 致力于实现的明确结果，例如修复错误、创建文档或研究某个主题。",
    },
    {
      key: "线程",
      href: "/codex/app-server#threads",
      appliesTo: "App-server, SDK",
      description:
        "Codex 应用服务器 API 中的一个技术对象，包含轮次和存储的对话历史记录。",
    },
    {
      key: "聊天中的计划任务",
      href: "/codex/automations#schedule-a-task-inside-a-chat",
      appliesTo: "Desktop app, Web",
      description:
        "使用现有聊天上下文并将每次运行结果返回至该聊天的计划任务。",
    },
    {
      key: "线程分支"
      href: "/codex/app-server#start-or-resume-a-thread",
      appliesTo: "App-server, SDK",
      description:
        "从现有线程的存储历史记录中分支出来的新线程。",
    },
    {
      key: "轮次",
      href: "/codex/app-server#core-primitives",
      appliesTo: "Desktop app, CLI, IDE extension, Cloud, SDK",
      description:
        "聊天中的一次交流，通常包含用户提示以及代理的响应和操作。",
    },
    {
      key: "通用镜像",
      href: "/codex/environments/cloud-environment#default-universal-image",
      appliesTo: "Cloud",
      description:
        "预装了常用工具的默认 Codex 云容器镜像。",
    },
    {
      key: "网络搜索缓存",
      href: "/codex/config-file/config-basic#web-search-mode",
      appliesTo: "Desktop app, CLI, IDE extension",
      description:
        "Codex 无需实时浏览即可使用的预索引搜索结果。",
    },
    {
      key: "ChatGPT Work",
      href: "/codex/get-started-with-work",
      appliesTo: "Desktop app, Web",
      description:
        "ChatGPT 中用于研究、分析以及创建文档、演示文稿、电子表格和其他成品的代理。",
    },
    {
      key: "工作树",
      href: "/codex/environments/git-worktrees",
      appliesTo: "Desktop app",
      description:
        "Codex 在单独的 Git 工作树中隔离更改的模式。",
    },
    {
      key: "可写根目录",
      href: "/codex/agent-approvals-security#protected-paths-in-writable-roots",
      appliesTo: "Desktop app, CLI, IDE extension",
      description: "允许 Codex 修改的目录。",
    },
  ]}
/>

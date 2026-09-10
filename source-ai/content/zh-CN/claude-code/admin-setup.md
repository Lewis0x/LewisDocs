---
title: 为您的组织设置 Claude Code
source_id: claude-code/admin-setup
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/admin-setup
owner: Anthropic
content_sha256: 8a258d966111c547a29265bc71fcc518add3eea18fdfb9facbf6aafbaa569811
translation_of: claude-code/admin-setup
translation_model: k3
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/admin-setup)

Content owner: Anthropic

> ## 文档索引
> 在以下地址获取完整的文档索引：https://code.claude.com/docs/llms.txt
> 在进一步探索之前，使用此文件发现所有可用页面。

# 为您的组织设置 Claude Code

> 面向部署 Claude Code 的管理员的决策指南，涵盖 API 提供商、托管设置、策略执行、使用监控和数据处理。

Claude Code 通过托管设置执行组织策略，这些设置优先于本地开发者配置。您可以通过 Claude 管理控制台、移动设备管理（MDM）系统或磁盘上的文件来下发这些设置。这些设置控制 Claude 可以访问哪些工具、命令、服务器和网络目标。

本页面按顺序介绍各项部署决策。每一行都链接到下方对应章节以及该领域的参考页面。

<Note>
  SSO、SCIM 用户预配和席位分配在 Claude 账户级别进行配置。有关这些步骤，请参阅 [Claude Enterprise 管理员指南](https://claude.com/resources/tutorials/claude-enterprise-administrator-guide) 和 [席位分配](https://support.claude.com/en/articles/11845131-use-claude-code-with-your-team-or-enterprise-plan)。
</Note>

| 决策                                                                | 您在选择什么                                | 参考                                                                                                                                                                     |
| :---------------------------------------------------------------------- | :-------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [选择你的 API 提供商](#choose-your-api-provider)                   | Claude Code 在哪里进行身份验证以及如何计费 | [身份验证](/docs/en/authentication)，[Amazon Bedrock](/docs/en/amazon-bedrock)，[Google Cloud 的 Agent Platform](/docs/en/google-vertex-ai)，[Microsoft Foundry](/docs/en/microsoft-foundry) |
| [确定设置如何到达设备](#decide-how-settings-reach-devices) | 托管策略如何到达开发者机器       | [服务器托管设置](/docs/en/server-managed-settings)，[设置文件](/docs/en/settings#settings-files)                                                                         |
| [决定要强制执行什么](#decide-what-to-enforce)                       | 允许哪些工具、命令和集成 | [权限](/docs/en/permissions)，[沙箱](/docs/en/sandboxing)                                                                                                                  |
| [设置使用情况可见性](#set-up-usage-visibility)                     | 如何跟踪支出和采用情况                    | [分析](/docs/en/analytics)，[监控](/docs/en/monitoring-usage)，[成本](/docs/en/costs)                                                                                            |
| [审查数据处理](#review-data-handling)                           | 数据保留和合规状况               | [数据使用](/docs/en/data-usage)，[安全](/docs/en/security)                                                                                                                        |

## 选择你的 API 提供商

Claude Code 通过多个 API 提供商之一连接到 Claude。你的选择会影响计费方式、身份验证、所继承的合规性状态,以及开发人员可以使用的 Claude Code 功能。

| 提供商                      | 在以下情况下选择此项                                                                                                                      |
| :---------------------------- | :------------------------------------------------------------------------------------------------------------------------------------ |
| Claude for Teams / Enterprise | 你希望 Claude Code 和 claude.ai 在同一个按席位订阅下,且无需运行任何基础设施。这是默认推荐选项。 |
| Claude Console                | 你以 API 为先,或希望采用按用量付费的计费方式                                                                                        |
| Amazon Bedrock                | 你希望继承现有的 AWS 合规性控制和计费                                                                                              |
| Google Cloud's Agent Platform | 你希望继承现有的 GCP 合规性控制和计费                                                                                              |
| Microsoft Foundry             | 你希望继承现有的 Azure 合规性控制和计费                                                                                            |

某些 Claude Code 功能需要 claude.ai 账户。[Claude Code网页版](/docs/en/claude-code-on-the-web)、[Routines](/docs/en/routines)、[Code Review](/docs/en/code-review)、[Remote Control](/docs/en/remote-control) 以及 [Chrome 扩展](/docs/en/chrome) 无法仅通过 Console API 密钥或云提供商凭证使用。如果你通过 Amazon Bedrock、Google Cloud 的 Agent Platform 或 Microsoft Foundry 进行部署,请规划开发人员是否还需要 Claude for Teams 或 Enterprise 席位。每个功能页面都会列出其计划要求。

有关涵盖身份验证、区域和功能对等的完整提供商比较,请参阅 [企业部署概述](/docs/en/third-party-integrations)。每个提供商的身份验证设置见 [身份验证](/docs/en/authentication)。

[网络配置](/docs/en/network-config) 中的代理和防火墙要求适用于所有提供商。如果你希望在多个提供商之前使用单一端点或进行集中式请求日志记录,请参阅 [LLM 网关](/docs/en/llm-gateway)。

## 确定设置如何到达设备

托管设置定义优先于本地开发者配置的策略。Claude Code按优先级顺序检查以下四个来源，并应用第一个返回非空配置的来源。一小组[跨来源锁定键](/docs/en/settings#settings-precedence)（如沙箱允许列表锁定）在任何管理员控制的来源设置时都会生效；当配置了[`policyHelper`](/docs/en/settings#compute-managed-settings-with-a-policy-helper)时，其输出是这些检查读取的唯一来源。

| 机制                     | 交付方式                                                                                                                                                                                              | 优先级 | 平台           |
| :---------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------- | :------------- |
| 服务器托管              | claude.ai 管理控制台，或用于网关登录的自托管[Claude 应用网关](/docs/en/claude-apps-gateway)                                                                                          | 最高     | 全部           |
| plist / 注册表策略      | macOS：`com.anthropic.claudecode` plist<br />Windows：`HKLM\SOFTWARE\Policies\ClaudeCode`                                                                                                                 | 高       | macOS、Windows |
| 基于文件的托管          | macOS：`/Library/Application Support/ClaudeCode/managed-settings.json`<br />Linux 和 WSL：`/etc/claude-code/managed-settings.json`<br />Windows：`C:\Program Files\ClaudeCode\managed-settings.json`                                                                              | 中       | 全部           |
| Windows 用户注册表      | `HKCU\SOFTWARE\Policies\ClaudeCode`                                                                                                                                                                   | 最低     | 仅 Windows     |

配置好的[`policyHelper`](/docs/en/settings#compute-managed-settings-with-a-policy-helper)会抢占所有四个来源：其输出成为本次运行的唯一托管配置。请参阅[设置优先级](/docs/en/settings#settings-precedence)。

服务器托管的设置在身份验证时到达设备，并在活动会话期间每小时刷新，无需端点基础设施。通过 claude.ai 管理控制台交付需要 Claude for Teams 或 Enterprise 计划。在 Amazon Bedrock、Google Cloud 的 Agent Platform 或 Microsoft Foundry 上的部署可以通过运行[Claude 应用网关](/docs/en/claude-apps-gateway)获得相同的远程交付，或者改用基于文件或操作系统级别的机制之一。

如果您的组织混合使用多个提供商，请为 claude.ai 用户配置[服务器托管设置](/docs/en/server-managed-settings)，并加上[基于文件或 plist/注册表的回退方案](/docs/en/settings#settings-files)，以便其他用户仍能收到托管策略。

plist 和 HKLM 注册表位置可与任何提供商配合使用，并且由于需要管理员权限才能写入，因此能抵抗篡改。HKCU 处的 Windows 用户注册表无需提升权限即可写入，因此应将其视为便利的默认值，而非强制实施渠道。

默认情况下，WSL 仅读取`/etc/claude-code`处的 Linux 文件路径。要将您的 Windows 注册表和`C:\Program Files\ClaudeCode`策略扩展到同一台机器上的 WSL，请在这两个仅限管理员的 Windows 来源之一中设置[`wslInheritsWindowsSettings: true`](/docs/en/settings#available-settings)。

无论您选择哪种机制，托管值都优先于用户和项目设置。诸如`permissions.allow`和`permissions.deny`之类的数组设置会合并来自所有来源的条目，因此开发者可以扩展托管列表，但不能从中移除条目。对于[两个例外](/docs/en/settings#settings-precedence)，即`fallbackModel`和`availableModels`，托管值会替换较低层级而不是合并。

请参阅[服务器托管设置](/docs/en/server-managed-settings)和[设置文件与优先级](/docs/en/settings#settings-files)。

### WSL 会话，位于 Claude Code 桌面版

在 Windows 上，[Claude Code Desktop 可以在 WSL 2 发行版](/docs/en/desktop-wsl)内运行 Code 会话。会话的 Claude Code 进程在发行版内运行，因此它会通过上述 WSL 发现路径解析托管设置：除非部署了 `wslInheritsWindowsSettings: true`，否则仅限 Windows 的来源无法到达它。

在存在托管设置的设备上，桌面版 WSL 会话默认不可用。如果你的组织希望启用它们，请联系你的 Anthropic 客户团队。启用后：

* 通过 HKLM 注册表或 `C:\Program Files\ClaudeCode` 文件部署 `wslInheritsWindowsSettings: true`，使 WSL 会话继承与主机会话相同的策略。
* 通过在 WSL 会话中运行 `/status` 进行验证：`Setting sources` 行应显示 `Enterprise managed settings` 以及你部署的 Windows 来源、`(HKLM)` 或 `(file)`。

WSL 2 实用工具 VM 内的进程对 Windows 侧的端点检测传感器不可见。如果你使用 CrowdStrike Falcon，请按照 CrowdStrike 的 WSL 文档要求，在 WSL 2 上启用适用于 Linux 的 Falcon 传感器，并添加两项排除——一项针对 WSL 虚拟机进程，一项针对 VM 磁盘映像——以便发行版内的进程和文件活动可被观测。 Claude Code的 [OpenTelemetry 工具执行遥测](/docs/en/monitoring-usage) 在 WSL 和原生会话中以相同方式发出。

## 决定要强制执行的内容

托管设置可以锁定工具、沙箱化执行、限制 MCP 服务器和插件来源，并控制哪些钩子会运行。每一行都是一个控制面，并带有驱动它的设置键。

| 控制                                                                                | 作用                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | 关键设置                                                                                                 |
| :------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :----------------------------------------------------------------------------------------------------------- |
| [权限规则](/docs/en/permissions)                                                    | 允许、询问或拒绝特定的工具和命令                                                                                                                                                                                                         | `permissions.allow`, `permissions.deny`                                                                      |
| [权限锁定](/docs/en/permissions#managed-only-settings)                           | 仅应用托管权限规则；禁用 `--dangerously-skip-permissions`                                                                                                                                                                                                         | `allowManagedPermissionRulesOnly`, `permissions.disableBypassPermissionsMode`                                |
| [沙箱](/docs/en/sandboxing)                                                           | 操作系统级的文件系统和网络隔离，带域名允许列表                                                                                                                                                                                                         | `sandbox.enabled`, `sandbox.network.allowedDomains`                                                          |
| [托管策略 CLAUDE.md](/docs/en/memory#deploy-organization-wide-claude-md)              | 在每次会话中加载的组织级指令，无法排除                                                                                                                                                                                                         | 托管策略路径上的文件                                                                              |
| [MCP 服务器控制](/docs/en/managed-mcp)                                                  | 限制用户可以添加或连接哪些 MCP 服务器，或部署一组固定服务器                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | `allowedMcpServers`、`deniedMcpServers`、`allowManagedMcpServersOnly`，或已部署的 `managed-mcp.json` 文件 |
| [插件市场控制](/docs/en/plugin-marketplaces#managed-marketplace-restrictions) | 限制用户可以添加并从中安装的市场来源，拒绝用于在单次运行中侧载插件、代理和 MCP 服务器的 CLI 标志，并将可建议其插件的市场列入允许列表                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | `strictKnownMarketplaces`、`blockedMarketplaces`、`disableSideloadFlags`、`pluginSuggestionMarketplaces`     |
| [自定义锁定](/docs/en/settings#strictpluginonlycustomization)                   | 阻止来自用户和项目来源的技能、代理、钩子和 MCP 服务器，使其只能来自插件或托管设置                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | `strictPluginOnlyCustomization`                                                                              |
| [钩子限制](/docs/en/settings#hook-configuration)                                   | 仅加载托管钩子；限制 HTTP 钩子 URL                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | `allowManagedHooksOnly`、`allowedHttpHookUrls`                                                               |
| [登录强制](/docs/en/settings#available-settings)                                   | 将登录限制为特定方法或 Anthropic 组织。方法限制在终端、VS Code 扩展、Agent SDK、`claude setup-token` 和 `/install-github-app` 中强制执行；组织限制涵盖终端、VS Code 扩展和 Agent SDK，但不包括 [gateway](/docs/en/claude-apps-gateway) 登录，因为它不针对 Anthropic 组织进行身份验证。 {/* min-version: 2.1.212 */}在 v2.1.212 之前，只有终端登录强制执行这两个设置键中的任一个。设置后，通过 `ANTHROPIC_API_KEY`、`ANTHROPIC_AUTH_TOKEN` 或 `apiKeyHelper` 验证的会话会在启动时被阻止；云提供商会话不受影响 | `forceLoginMethod`、`forceLoginOrgUUID`                                                                      |
| [禁用代理视图](/docs/en/agent-view#how-background-sessions-are-hosted)                | 关闭 `claude agents`、`--bg`、`/background` 和按需监督器                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | `disableAgentView`                                                                                           |
| [配置企业启动器](/docs/en/corporate-launcher)                             | 为 [background-agent supervisor](/docs/en/agent-view#how-background-sessions-are-hosted)、其工作进程以及 [other covered background processes](/docs/en/corporate-launcher#what-the-launcher-covers) 添加必需的企业启动器前缀，而不是关闭代理视图                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | `processWrapper`                                                                                             |
| [模型限制](/docs/en/model-config#restrict-model-selection)                        | `availableModels` 筛选选择器中显示的模型。添加 `enforceAvailableModels` 还会约束自动选择的默认模型。有关此设置如何作用于 CLI、Web 和 IDE，请参阅 [surface coverage](/docs/en/model-config#surface-coverage)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | `availableModels`、`enforceAvailableModels`                                                                  |
| [版本下限](/docs/en/settings)                                                          | 防止自动更新安装低于组织范围最低版本的版本                                                                                                                                                                                                         | `minimumVersion`                                                                                             |
| [必需版本范围](/docs/en/settings)                                                 | 当运行的版本超出组织批准的范围时完全拒绝启动。比 `minimumVersion` 更强，后者仅阻止降级                                                                                                                                                                                                         | `requiredMinimumVersion`, `requiredMaximumVersion`                                                           |

成员通过 claude.ai 或 Anthropic API 进行身份验证的组织也可以在不部署设置的情况下治理模型：[组织模型限制](/docs/en/model-config#organization-model-restrictions) 可禁用单个模型，[组织默认模型](/docs/en/model-config#organization-default-model) 设置新会话开始时使用的模型，[组织工作量限制](/docs/en/model-config#organization-effort-limits) 按角色限制工作量级别。所有三项控制均需要 Claude Enterprise 计划。模型限制和工作量限制在服务器端强制执行；默认模型是一个起点，用户可以更改，除非组织强制执行它。强制执行功能仅向有限的一组组织开放；请咨询您的 Anthropic 客户团队了解可用性。这些控制均不适用于 Amazon Bedrock、Google Cloud 的 Agent Platform、Microsoft Foundry 或 [AWS 上的 Claude 平台](/docs/en/claude-platform-on-aws) 上的会话；在这些提供商上，请使用上面的 `availableModels` 进行限制，并使用托管设置中的 `model` 键设置默认值。

[Claude Code网页版](/docs/en/claude-code-on-the-web) 有自己的管理界面：在管理设置的云环境页面上，所有者和管理员可以创建 [组织共享环境](/docs/en/claude-code-on-the-web#organization-shared-environments)，为成员的云会话设置 [网络访问级别](/docs/en/claude-code-on-the-web#network-access)、环境变量和初始化脚本，并选择组织的默认环境。

权限规则和沙盒覆盖不同的层面。拒绝 WebFetch 会阻止 Claude 的抓取工具，但如果允许 Bash，`curl` 和 `wget` 仍可访问任何 URL。沙盒通过在操作系统层面强制执行的网络域允许列表弥补了这一缺口。

有关这些控制所防御的威胁模型，请参阅 [安全性](/docs/en/security)。

## 设置使用情况可见性

根据您需要报告的内容选择监控方式。Claude for Teams 或 Enterprise 计划与 Claude Console 组织之间，仪表板、API 和支出控制各不相同，因此在围绕某项功能规划报告之前，请先查看"可用性"列。

| 功能                 | 您获得的内容                                                                                                        | 可用性                                                                                                                                                                                                                     | 从哪里开始                                            |
| :--------------------- | :---------------------------------------------------------------------------------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :---------------------------------------------------- |
| 使用情况监控           | 通过 OpenTelemetry 导出会话、工具和令牌数据                                                                           | 所有提供商                                                                                                                                                                                                                 | [监控使用情况](/docs/en/monitoring-usage)              |
| 分析仪表板             | Teams / Enterprise 上提供采用率和贡献指标以及排行榜；Console 上提供每用户使用情况和支出指标                         | Teams / Enterprise 位于 [claude.ai/analytics](https://claude.ai/analytics/claude-code)，Console 位于 [platform.claude.com/claude-code](https://platform.claude.com/claude-code)                                                              | [分析](/docs/en/analytics)                            |
| 程序化报告             | 通过 API 获取每用户的使用情况和成本数据                                                                               | [Enterprise Analytics API](https://platform.claude.com/docs/en/api/admin/analytics) 适用于 Enterprise，[Claude Code Analytics API](https://platform.claude.com/docs/en/build-with-claude/claude-code-analytics-api) 适用于 Console             | [成本](/docs/en/costs#manage-costs-for-your-organization) |
| 支出控制               | 支出限额和速率限制                                                                                                    | Teams / Enterprise 的管理员设置、Console 的工作区限额；在第三方云上，可使用云预算控制或带有每用户[支出限额](/docs/en/claude-apps-gateway-spend-limits)的 [Claude 应用网关](/docs/en/claude-apps-gateway) | [成本](/docs/en/costs#manage-costs-for-your-organization) |

在 Teams 和 Enterprise 上，每用户的使用情况和支出数据来自您组织分析设置中的[支出报告](https://support.claude.com/en/articles/12883420-view-usage-analytics-for-team-and-enterprise-plans)，而非分析仪表板。云提供商通过 AWS Cost Explorer、GCP Billing 或 Azure Cost Management 公开支出数据。有关跨 Claude 聊天、Claude Code 和 Cowork 规划企业预算，请参阅[Claude Enterprise 消耗指南](https://support.claude.com/en/articles/14782391-claude-enterprise-consumption-guide)。

## 审查数据处理

在 Team、Enterprise、Claude API 和云提供商计划中，Anthropic 不会使用您的代码或提示词来训练模型。数据保留和合规状况由您的 API 提供商决定。

| 主题                     | 须知内容                                                                                         | 从哪里开始                                 |
| :------------------------ | :--------------------------------------------------------------------------------------------------- | :--------------------------------------------- |
| 数据使用政策         | Anthropic 收集什么、保留多长时间、哪些内容绝不用于训练                      | [数据使用](/docs/en/data-usage)                   |
| 零数据保留 (ZDR) | 请求完成后不存储任何内容。Claude for Enterprise 的合格账户可用 | [零数据保留](/docs/en/zero-data-retention) |
| 安全架构     | 网络模型、加密、身份验证、审计追踪                                               | [安全](/docs/en/security)                       |

如果您需要请求级审计日志记录，或需要按数据敏感度路由流量，请在开发人员与提供商之间放置一个网关：自托管的 [Claude 应用网关](/docs/en/claude-apps-gateway) 可记录带有 IdP 身份的逐请求审计日志，或者使用其他 [LLM 网关](/docs/en/llm-gateway)。有关监管要求和认证，请参阅 [法律与合规](/docs/en/legal-and-compliance)。

## 验证与入门

配置托管设置后，让开发人员在 Claude Code 内运行 `/status`。在 **Status（状态）** 选项卡上，`Setting sources` 行显示 `Enterprise managed settings`，后跟括号中的来源，即 `(remote)`、`(plist)`、`(HKLM)`、`(HKCU)` 或 `(file)` 之一。请参阅 [验证活动设置](/docs/en/settings#verify-active-settings)。

分享这些资源以帮助开发人员入门：

* [快速入门](/docs/en/quickstart)：从安装到使用项目的首次会话演练
* [常见工作流程](/docs/en/common-workflows)：日常任务的模式，如代码审查、重构和调试
* [Claude 101](https://anthropic.skilljar.com/claude-101) 和 [Claude Code 实战](https://anthropic.skilljar.com/claude-code-in-action)：Anthropic Academy 自定进度课程

对于登录问题，请引导开发人员参阅 [身份验证故障排除](/docs/en/troubleshoot-install#login-and-authentication)。最常见的修复方法是：

* 运行 `/logout`，然后运行 `/login` 以切换账户
* 如果缺少企业身份验证选项，请运行 `claude update`
* 更新后重启终端

如果开发人员看到"You haven't been added to your organization yet"，则表示其席位不包含 Claude Code 访问权限，需要在管理控制台中更新。

## 后续步骤

选择好提供商和交付机制后，继续进行详细配置：

* [服务器托管设置](/docs/en/server-managed-settings)：从 Claude 管理控制台交付托管策略
* [设置参考](/docs/en/settings)：每个设置键、文件位置和优先级规则
* [Monorepo 与大型仓库](/docs/en/large-codebases)：部署到 monorepo 的组织的按目录配置模式
* [Amazon Bedrock](/docs/en/amazon-bedrock)、[Google Cloud 的 Agent Platform](/docs/en/google-vertex-ai)、[Microsoft Foundry](/docs/en/microsoft-foundry)：特定于提供商的部署
* [Claude Enterprise 管理员指南](https://claude.com/resources/tutorials/claude-enterprise-administrator-guide)：SSO、SCIM、席位管理和推广手册

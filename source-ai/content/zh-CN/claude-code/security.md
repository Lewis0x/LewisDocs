---
title: 安全性
source_id: claude-code/security
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/security
owner: Anthropic
content_sha256: 15a3393a1af5d6e640beac172e0831058c4150ed29a0f2911e0137415980daaa
translation_of: claude-code/security
translation_model: gpt-5.6
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/security)

Content owner: Anthropic

> ## 文档索引
> 完整的文档索引位于：https://code.claude.com/docs/llms.txt
> 在进一步探索之前，可使用此文件发现所有可用页面。

# 安全性

> 了解 Claude Code 的安全保障措施和安全使用最佳实践。

## 我们的安全方法

### 安全基础

你的代码安全至关重要。Claude Code 以安全性为核心，并按照 Anthropic 的综合安全计划开发。有关更多信息和资源（SOC 2 Type 2 报告、ISO 27001 证书等），请访问 [Anthropic Trust Center](https://trust.anthropic.com)。

### 基于权限的架构

Claude Code 默认采用严格的只读权限。需要执行其他操作（编辑文件、运行测试、执行命令）时，Claude Code 会明确请求权限。用户可以决定只批准一次，还是允许自动执行操作。

Claude Code 在运行可能修改系统的 Bash 命令前需要批准。`ls`、`cat` 和 `git status` 等内置的[只读命令](/docs/en/permissions#read-only-commands)无需提示即可运行。通过这种方法，用户和组织可以直接配置权限。

有关详细的权限配置，请参阅[权限](/docs/en/permissions)。

### 内置保护

为降低智能体系统中的风险：

* **沙盒化 Bash 工具**：通过具有文件系统和网络隔离能力的[沙盒](/docs/en/sandboxing)运行 Bash 命令，在保障安全性的同时减少权限提示。使用 `/sandbox` 启用，并定义 Claude Code 可自主工作的边界
* **工作目录边界**：Claude Code 只能写入启动目录及其子目录，未经明确许可不能修改父目录中的文件。经批准提示后，可以使用 Read、Grep 和 Glob 工具读取此边界之外的路径。通过[附加目录](/docs/en/permissions#working-directories)扩展边界可以跳过提示；也可使用[沙盒 `denyRead` 规则](/docs/en/sandboxing#filesystem-isolation)限制只读 Bash 命令可用的更广泛读取权限，该规则仅在启用沙盒时适用
* **减少提示疲劳**：支持按用户、按代码库或按组织将常用的安全命令加入允许列表
* **Accept Edits 模式**：自动批准文件编辑，以及针对工作目录内路径的一组固定文件系统 Bash 命令，例如 `mkdir`、`touch`、`rm`、`mv`、`cp` 和 `sed`。其他 Bash 命令和超出作用域的路径仍会提示

### 用户责任

Claude Code 只拥有你授予的权限。你有责任在批准前检查建议的代码和命令是否安全。

## 防范提示注入

提示注入是一种攻击技术，攻击者通过插入恶意文本，试图覆盖或操纵 AI 助手的指令。Claude Code 包含多项防范此类攻击的保障措施：

### 核心保护

* **权限系统**：敏感操作需要明确批准
* **上下文感知分析**：通过分析完整请求检测潜在有害指令
* **输入净化**：通过处理用户输入来防止命令注入
* **网络命令批准**：`curl` 和 `wget` 等从 Web 获取内容的命令默认不会自动批准。它们与其他非只读 Bash 命令一样会触发提示，因此你仍可批准一次，或添加 `Bash(curl *)` 这样的明确允许规则。若要完全阻止它们，请将其添加到 [`permissions.deny`](/docs/en/permissions#tool-specific-permission-rules)

### 隐私保障

我们实施了多项保障措施来保护你的数据，包括：

* 敏感信息的保留期有限（请参阅[隐私中心](https://privacy.anthropic.com/en/articles/10023548-how-long-do-you-store-my-data)了解更多信息）
* 限制对用户会话数据的访问
* 用户可控制数据训练偏好。消费者用户可以随时更改其[隐私设置](https://claude.ai/settings/privacy)。

有关完整详情，请查看我们的[商业服务条款](https://www.anthropic.com/legal/commercial-terms)（适用于 Team、Enterprise 和 API 用户）或[消费者条款](https://www.anthropic.com/legal/consumer-terms)（适用于 Free、Pro 和 Max 用户），以及[隐私政策](https://www.anthropic.com/legal/privacy)。

### 其他保障措施

* **网络请求批准**：发出网络请求的工具默认需要用户批准
* **隔离的上下文窗口**：Web fetch 使用单独的上下文窗口，避免注入潜在恶意提示
* **信任验证**：首次运行代码库和使用新的 MCP 服务器时需要进行信任验证
  * 注意：使用 `-p` 标志以非交互方式运行时，信任验证会禁用
  * 注意：当你直接在主目录中启动 Claude Code 时，信任接受状态仅在当前会话中保留，不会写入磁盘，因此每次启动时都会再次出现提示。没有可将其持久保存的设置。请改为从项目子目录启动 Claude Code，此时信任接受状态会按目录保存
* **命令注入检测**：可疑的 Bash 命令即使此前已加入允许列表，也需要手动批准
* **默认拒绝式匹配**：未匹配的命令默认需要手动批准
* **自然语言说明**：复杂的 Bash 命令会附带说明，帮助用户理解
* **安全凭据存储**：如果可用，API 密钥和令牌会存储在 macOS Keychain 中；在 Windows 和 Linux 上则由文件权限保护。请参阅[凭据管理](/docs/en/authentication#credential-management)

<Warning>
  **Windows WebDAV 安全风险**：在 Windows 上运行 Claude Code 时，建议不要启用 WebDAV，也不要允许 Claude Code 访问可能包含 WebDAV 子目录的 `\\*` 等路径。由于存在安全风险，[Microsoft 已弃用 WebDAV](https://learn.microsoft.com/en-us/windows/whats-new/deprecated-features#:~:text=The%20Webclient%20\(WebDAV\)%20service%20is%20deprecated)。启用 WebDAV 可能使 Claude Code 绕过权限系统，触发向远程主机发送的网络请求。
</Warning>

**处理不受信任内容的最佳实践**：

1. 批准前检查建议的命令
2. 避免将不受信任的内容通过管道直接传给 Claude
3. 验证对关键文件提出的更改
4. 使用虚拟机（VM）运行脚本和发起工具调用，尤其是在与外部 Web 服务交互时
5. 使用 `/feedback` 报告可疑行为

<Warning>
  虽然这些保护措施显著降低了风险，但没有任何系统能够完全
  免受所有攻击。使用任何 AI 工具时，请始终保持良好的安全实践。
</Warning>

## MCP 安全

Claude Code 允许用户配置 Model Context Protocol (MCP) 服务器。允许使用的 MCP 服务器列表在源代码中配置，是由工程师签入源代码管理系统的 Claude Code 设置的一部分。

我们建议自行编写 MCP 服务器，或使用来自你信任的提供商的 MCP 服务器。你可以为 MCP 服务器配置 Claude Code 权限。Anthropic 会依据其[上架标准](https://claude.com/docs/connectors/building/review-criteria)审核连接器，然后再将其添加到 [Anthropic Directory](https://claude.ai/directory)，但不会对任何 MCP 服务器执行安全审计或管理。

## IDE 安全

有关在 IDE 中运行 Claude Code 的更多信息，请参阅 [VS Code 安全和隐私](/docs/en/vs-code#security-and-privacy)。

## 云端执行安全

使用 [Claude Code 网页版](/docs/en/claude-code-on-the-web)时，还会实施额外的安全控制：

* **隔离虚拟机**：每个云端会话都在由 Anthropic 管理的隔离 VM 中运行
* **网络访问控制**：默认限制网络访问，并可配置为禁用或仅允许特定域名
* **凭据保护**：身份验证通过安全代理处理；该代理在沙盒内使用有作用域的凭据，然后将其转换为你实际的 GitHub 身份验证令牌
* **分支限制**：Git push 操作仅限当前工作分支
* **审计日志**：云环境中的所有操作都会记录下来，用于合规和审计
* **自动清理**：云环境会在会话完成后自动终止

有关云端执行的更多详情，请参阅 [Claude Code 网页版](/docs/en/claude-code-on-the-web)。

[远程控制](/docs/en/remote-control)会话的工作方式不同：Web 界面连接到本地计算机上运行的 Claude Code 进程。所有代码执行和文件访问都留在本地，会话流量通过 TLS 经由 Anthropic API 传输；连接期间，会话记录会存储在 Anthropic 服务器上，以便跨设备同步对话，如[连接和安全](/docs/en/remote-control#connection-and-security)中所述。这里不涉及云端 VM 或沙盒。连接使用多个短期且作用域狭窄的凭据，每个凭据仅限特定用途并独立过期，以限制任何单个凭据泄露后的影响范围。

## 安全最佳实践

### 处理敏感代码

* 批准前检查所有建议的更改
* 对敏感仓库使用项目专用权限设置
* 考虑使用[开发容器](/docs/en/devcontainer)进行额外隔离
* 使用 `/permissions` 定期审计权限设置

### 团队安全

* 使用[托管设置](/docs/en/settings#settings-files)强制实施组织标准
* 通过版本控制共享已批准的权限配置
* 对团队成员开展安全最佳实践培训
* 通过 [OpenTelemetry 指标](/docs/en/monitoring-usage)监控 Claude Code 使用情况
* 使用 [`ConfigChange` hook](/docs/en/hooks#configchange)审计或阻止会话期间的设置更改

### 报告安全问题

如果你在 Claude Code 中发现安全漏洞：

1. 不要公开披露
2. 通过我们的 [HackerOne 计划](https://hackerone.com/4f1f16ba-10d3-4d09-9ecc-c721aad90f24/embedded_submissions/new)进行报告
3. 包含详细的复现步骤
4. 在公开披露前，给我们留出时间处理问题

## 相关资源

* [安全指导插件](/docs/en/security-guidance)：让 Claude 在会话期间审核并修复自身代码更改中的漏洞
* [沙盒环境](/docs/en/sandbox-environments)：比较隔离方法，并为你的威胁模型选择一种
* [沙盒](/docs/en/sandboxing)：针对 Bash 命令的文件系统和网络隔离
* [权限](/docs/en/permissions)：配置权限和访问控制
* [使用情况监控](/docs/en/monitoring-usage)：跟踪和审计 Claude Code 活动
* [开发容器](/docs/en/devcontainer)：安全的隔离环境
* [Anthropic Trust Center](https://trust.anthropic.com)：安全认证和合规性

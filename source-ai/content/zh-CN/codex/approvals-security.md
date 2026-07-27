---
title: 代理审批 & 安全
source_id: codex/approvals-security
product: codex
lang: zh-CN
canonical_url: https://learn.chatgpt.com/docs/agent-approvals-security
owner: OpenAI
content_sha256: ea4db7849c1853d49ca88ffc23ab4b066c66326b8a4a57b48c0e560aea245a79
translation_of: codex/approvals-security
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://learn.chatgpt.com/docs/agent-approvals-security)

Content owner: OpenAI

# 代理审批 & 安全

Codex 帮助保护您的代码和数据并降低被滥用的风险。

本页涵盖如何安全地操作 Codex，包括沙盒，审批，
  以及网络访问。如果您正在寻找 Codex Security，该产品用于
  扫描已连接的 GitHub 仓库，请参阅 [Codex Security](https://learn.chatgpt.com/docs/security)。

默认情况下，代理在关闭网络访问的状态下运行。在本地，Codex 使用操作系统强制执行的沙盒来限制其可触及的范围（通常仅限当前工作区），并辅以审批策略，以控制其在执行操作前何时必须暂停并征求您的许可。

有关沙盒如何在 ChatGPT 桌面应用，
Codex CLI，以及 IDE 扩展中工作的高层说明，请参阅 [sandboxing](https://learn.chatgpt.com/docs/sandboxing)。
如需更广泛的企业安全概述，请参阅 [Codex security white paper](https://trust.openai.com/?itemUid=382f924d-54f3-43a8-a9df-c39e6c959958&source=click)。

## 沙盒与审批

Codex 的安全控制来自两个协同工作的层：

- **沙盒模式**：当 Codex 执行模型生成的命令时，在技术上能做什么（例如，它可以在哪里写入以及是否可以连接网络）。
- **审批策略**：Codex 在执行操作之前（例如，离开沙盒、使用网络或运行受信任集合之外的命令）何时必须征求您的许可。

Codex 会根据您运行它的位置使用不同的沙盒模式：

- **Codex 云端**：在隔离的由 OpenAI 管理的容器中运行，防止访问您的主机系统或不相关的数据。采用两阶段运行时模型：设置阶段在代理阶段之前运行，并且可以访问网络以安装指定的依赖项，然后代理阶段默认在离线状态下运行，除非您为该环境启用互联网访问。为云环境配置的密钥仅在设置阶段可用，并会在代理阶段开始前被移除。
- **Codex CLI / IDE 扩展**：操作系统级别的机制强制执行沙盒策略。默认设置包括禁止网络访问以及将写入权限限制在当前活动的工作区内。您可以根据自身的风险承受能力配置沙盒、审批策略和网络设置。

在 `Auto` 预设中（例如，`--sandbox workspace-write --ask-for-approval on-request`），Codex 可以在工作目录中自动读取文件、进行编辑和运行命令。

Codex 请求批准编辑工作区之外的文件或运行需要网络访问的命令。如果您想要在不进行更改的情况下聊天或计划，请使用 `read-only` 命令切换到 `/permissions` 模式。

对于声明会产生副作用的 app（连接器）工具调用，即使该操作不是 shell 命令或文件更改，Codex 也会请求批准。当工具声明破坏性注释时，破坏性的 app/MCP 工具调用始终需要批准，即使它同时声明了其他提示（例如，只读提示）。

## 网络访问 <ElevatedRiskBadge class="ml-2" />

对于 Codex 云，请参阅 [agent internet access](https://learn.chatgpt.com/docs/cloud/internet-access) 来启用完整的互联网访问或域名允许列表。

对于 ChatGPT 桌面应用、Codex CLI 或 IDE 扩展，默认的 `workspace-write` 沙盒模式会保持关闭网络访问，除非您在配置中启用它：

```toml
[sandbox_workspace_write]
network_access = true
```

### 网络隔离

网络访问通过应用于脚本、
程序以及命令生成的子进程的目标规则来控制。当命令网络访问已经
启用时，开启 `network_proxy` 功能可将该流量限制
在您配置的网络策略范围内。

```toml
[features.network_proxy]
enabled = true
domains = { "api.openai.com" = "allow", "example.com" = "deny" }
```

对于一次性的 CLI 会话，当您只需要切换开关时，请使用布尔简写形式，
当您还需要设置策略选项时，请使用表格形式：

```bash
codex \
  -c 'features.network_proxy=true' \
  -c 'sandbox_workspace_write.network_access=true'

codex \
  -c 'features.network_proxy.enabled=true' \
  -c 'features.network_proxy.domains={ "api.openai.com" = "allow", "example.com" = "deny" }' \
  -c 'sandbox_workspace_write.network_access=true'
```

该功能改变了已启用网络访问的强制执行方式；它本身并不授予
网络访问权限。请将 `sandbox_workspace_write.network_access` 与
`workspace-write` 配置结合使用，以决定命令是否拥有网络访问权限：

- 网络关闭 + `network_proxy` 开启：网络保持关闭，该功能不起作用。
- 网络开启 + `network_proxy` 关闭：网络保持开启，具有不受限制的直接
  出站访问权限。
- 网络开启 + `network_proxy` 开启：网络保持开启，且出站流量
  受配置的网络策略约束。

管理员管理的 `experimental_network` 要求与用户
功能开关是分开的。它们可以在没有
`features.network_proxy` 的情况下配置并启动沙盒网络，但当处于活动状态的
沙盒将其保持关闭时，它们不会开启网络访问。请参见 [托管配置](https://learn.chatgpt.com/docs/enterprise/managed-configuration#configure-network-access-requirements)
以了解管理员侧的 `requirements.toml` 形态。

#### 网络策略

域名规则以允许列表优先：

- 精确主机仅匹配其自身。
- `*.example.com` 匹配诸如 `api.example.com` 之类的子域名，但不匹配
  `example.com`。
- `**.example.com` 同时匹配顶级域名和子域名。
- 全局 `*` 允许规则匹配任何未被拒绝的公共主机。请将 `*`
  视为广泛的网络访问，并尽可能优先使用限定范围的规则。
- `deny` 始终优先于 `allow`，且全局 `*` 仅对允许规则有效。

#### 本地和私有目标

默认情况下，`allow_local_binding = false` 会阻止环回、链路本地和
私有目标：

- 特定例外：添加精确的本地 IP 字面量或 `localhost` 允许规则
  当命令需要一个本地目标时。
- 更广泛的访问：仅当您有意
  希望获得更广泛的本地/私有访问范围时，才设置 `allow_local_binding = true`。
- 通配符：通配符规则不计作显式的本地例外。
- 已解析的地址：解析为本地/私有 IP 的主机名保持阻止状态
  即使它们与允许列表匹配。

#### DNS 重绑定保护

在允许主机名之前，Codex 会尽力执行 DNS 和 IP
分类检查：

- 失败或超时的查找将被阻止。
- 解析为非公共地址的主机名将被阻止。
- 该检查降低了 DNS 重绑定风险，但并未消除它。要完全
  防止重绑定，需要通过传输
  层固定已解析的 IP。

如果敌意 DNS 在考虑范围内，也请在较低层级执行出站控制。

#### 危险设置

有两个设置会故意扩大信任边界：

- `dangerously_allow_non_loopback_proxy = true` 可以将代理监听器暴露到
  回环地址之外。
- `dangerously_allow_all_unix_sockets = true` 会绕过 Unix 套接字白名单。

仅在严格控制的环境中使用它们。当启用 Unix 套接字代理时，
即使请求了非回环绑定，监听器也会保持仅限回环，
因此沙盒网络不会成为通往本地守护进程的远程网桥。

`network_proxy` 默认是关闭的。当你启用它时：

| 设置                                | 默认 | 行为                                                                                                                                                                              |
| -------------------------------------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `enabled`                              | `false` | 仅在命令网络访问已开启时启动沙盒网络。                                                                                                           |
| `domains`                              | 未设置   | 使用白名单行为，因此在添加 `allow` 规则之前不允许任何外部目标。支持精确主机、限定通配符和全局 `*` 允许规则；`deny` 始终优先。 |
| `unix_sockets`                         | 未设置   | 在添加明确的 `allow` 规则之前，不允许任何 Unix 套接字目标。                                                                                                         |
| `allow_local_binding`                  | `false` | 阻断本地和私有网络目标，除非添加精确的本地 IP 字面量或 `localhost` 允许规则，或者明确选择加入更广泛的本地/私有访问。                |
| `enable_socks5`                        | `true`  | 在策略允许时公开 SOCKS5 支持。                                                                                                                                         |
| `enable_socks5_udp`                    | `true`  | 在 SOCKS5 可用时允许通过 SOCKS5 进行 UDP 通信。                                                                                                                                      |
| `allow_upstream_proxy`                 | `true`  | 允许沙盒网络遵循环境中的上游代理。                                                                                                               |
| `dangerously_allow_non_loopback_proxy` | `false` | 将监听器端点保留在回环地址上，除非您故意将其公开到本地主机之外。                                                                                            |
| `dangerously_allow_all_unix_sockets`   | `false` | 除非您故意绕过该保护，否则保持基于白名单的 Unix 套接字访问。                                                                                              |

您还可以控制 [网络搜索工具](https://platform.openai.com/docs/guides/tools-web-search)，而无需授予生成的命令完全的网络访问权限。Codex 默认使用网络搜索缓存来访问结果。该缓存是由 OpenAI 维护的网络结果索引，因此缓存模式返回的是预先索引的结果，而不是获取实时页面。这减少了受到来自任意实时内容的提示注入的风险，但您仍应将网络结果视为不受信任的内容。如果您正在使用 `--yolo` 或其他 [完全访问沙盒设置](#common-sandbox-and-approval-combinations)，网络搜索将默认为实时结果。使用 `--search` 或设置 `web_search = "live"` 以允许实时浏览，或者将其设置为 `"disabled"` 以关闭该工具：

```toml
web_search = "cached"  # default
# web_search = "disabled"

# web_search = "live"  # same as --search

```

当外部网络访问应由搜索索引控制时，设置 `web_search = "indexed"`
在 Codex 中启用网络访问或网络搜索时请谨慎。
提示词注入可能会导致代理获取并遵循不受信任的指令。

## 默认值和建议

- 在启动时，Codex 会检测文件夹是否受版本控制，并建议：
  - 受版本控制的文件夹：`Auto`（工作区写入 + 按需审批）
  - 不受版本控制的文件夹：`read-only`
- 根据您的设置，Codex 也可能以 `read-only` 启动，直到您明确信任该工作目录（例如，通过新手引导提示或 `/permissions`）。
- 工作区包括当前目录和诸如 `/tmp` 之类的临时目录。使用 `/status` 命令可查看工作区中有哪些目录。
- 要接受默认值，请运行 `codex`。
- 您可以显式设置这些内容：
  - `codex --sandbox workspace-write --ask-for-approval on-request`
  - `codex --sandbox read-only --ask-for-approval on-request`

### 可写根目录中的受保护路径

在默认的 `workspace-write` 沙盒策略中，可写根目录仍然包含受保护路径：

- `<writable_root>/.git` 无论是作为目录还是文件出现，都会被保护为只读。
- 如果 `<writable_root>/.git` 是指针文件（`gitdir: ...`），解析出的 Git 目录路径也会被保护为只读。
- `<writable_root>/.agents` 作为目录存在时会被保护为只读。
- `<writable_root>/.codex` 作为目录存在时会被保护为只读。
- 保护是递归的，因此这些路径下的所有内容均为只读。

### 在没有审批提示的情况下运行

您可以使用 `--ask-for-approval never` 或 `-a never`（简写）来禁用审批提示。

此选项适用于所有 `--sandbox` 模式，因此您仍然可以控制 Codex 的自主级别。Codex 会在您设置的约束范围内尽最大努力工作。

如果您需要 Codex 在没有审批提示的情况下读取文件、进行编辑以及运行带有网络访问权限的命令，请使用 `--sandbox danger-full-access`（或 `--dangerously-bypass-approvals-and-sandbox` 标志）。在此操作之前请谨慎。

作为一种折中方案，`approval_policy = { granular = { ... } }` 允许您保持特定审批提示类别的交互性，同时自动拒绝其他提示。该细粒度策略涵盖沙盒审批、execpolicy 规则提示、MCP 提示、`request_permissions` 提示以及技能脚本审批。

### 自动批准审查

默认情况下，批准请求会路由给您：

```toml
approvals_reviewer = "user"
```

当批准为交互式时，将应用自动批准审查，例如
`approval_policy = "on-request"` 或细粒度批准策略。设置
`approvals_reviewer = "auto_review"` 以在 Codex 执行请求之前，将符合条件的批准请求
路由给审查者代理：

```toml
approval_policy = "on-request"
approvals_reviewer = "auto_review"
```

有关完整的审查者生命周期、触发条件、配置优先级，
以及失败行为，请参见
[自动审查](https://learn.chatgpt.com/docs/sandboxing/auto-review)。

审查者仅评估已经需要批准的操作，例如沙盒
提权、被阻止的网络请求、`request_permissions` 提示或
有副作用的应用程序和 MCP 工具调用。保留在沙盒内部的操作
无需额外的审查步骤即可继续。

审查者策略检查数据泄露、凭据探测、持续性的
安全削弱以及破坏性操作。当策略允许时，低风险和中风险操作
可以继续执行。该策略拒绝严重风险的操作。
高风险操作需要足够的用户授权且没有匹配的拒绝规则。
提示词构建、审查会话和解析失败会自动拒绝。超时会
单独显现，但该操作仍然不会运行。

[默认审查者策略](https://github.com/openai/codex/blob/main/codex-rs/core/src/guardian/policy.md)
位于开源 Codex 仓库中。企业可以在托管需求中将其
租户特定的部分替换为 `guardian_policy_config`。
也支持本地 `[auto_review].policy` 文本，但托管需求
优先。有关设置详细信息，请参见
[托管配置](https://learn.chatgpt.com/docs/enterprise/managed-configuration#configure-automatic-review-policy)。

在 ChatGPT 桌面应用中，这些审查显示为带有状态的自动审查项目，
例如审查中、已批准、已拒绝、已中止或已超时。它们还可以
包含针对所审查的
请求的风险级别和用户授权评估。

自动审查使用额外的模型调用，因此它可能会增加 Codex 的使用量。管理员
可以使用 `allowed_approvals_reviewers` 对其进行限制。

### 常见的沙盒与批准组合

| 意图                                                            | 标志 / 配置                                                                                                                      | 效果                                                                                                                                           |
| ----------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| 自动（预设）                                                     | _无需标志_ 或 `--sandbox workspace-write --ask-for-approval on-request`                                                      | Codex 可以读取文件、进行编辑并在工作区中运行命令。Codex 需要批准才能在工作区外进行编辑或访问网络。 |
| 安全只读浏览                                                     | `--sandbox read-only --ask-for-approval on-request`                                                                                 | Codex 可以读取文件并回答问题。Codex 需要批准才能进行编辑、运行命令或访问网络。                               |
| 只读非交互 (CI)                                                    | `--sandbox read-only --ask-for-approval never`                                                                                      | Codex 只能读取文件；从不请求批准。                                                                                              |
| 自动编辑但在运行不受信任的命令前请求批准 | `--sandbox workspace-write --ask-for-approval untrusted`                                                                            | Codex 可以读取和编辑文件，但在运行不受信任的命令前会请求批准。                                                           |
| 自动审查模式                                                  | `--sandbox workspace-write --ask-for-approval on-request -c approvals_reviewer=auto_review` 或 `approvals_reviewer = "auto_review"` | 与标准的按需模式具有相同的沙盒边界，但符合条件的审批请求将由自动审查处理，而不是呈现给用户。  |
| 危险的完全访问权限                                             | `--dangerously-bypass-approvals-and-sandbox` （别名：`--yolo`）                                                                      | <ElevatedRiskBadge /> 无沙盒；无需审批 _(不推荐)_                                                                               |

对于非交互式运行，请使用 `codex exec --sandbox workspace-write`；Codex 将较旧的 `codex exec --full-auto` 调用保留为已弃用的兼容路径，并打印警告。

使用 `--ask-for-approval untrusted` 时，Codex 仅自动运行已知安全的只读操作。可能会改变状态或触发外部执行路径的命令（例如，破坏性的 Git 操作或 Git 输出/配置覆盖标志）需要经过审批。

#### 在 `config.toml` 中配置

有关更广泛的配置工作流，请参阅 [配置基础](https://learn.chatgpt.com/docs/config-file/config-basic)、[高级配置](https://learn.chatgpt.com/docs/config-file/config-advanced#approval-policies-and-sandbox-modes) 和 [配置参考](https://learn.chatgpt.com/docs/config-file/config-reference)。

```toml
# Always ask for approval mode

approval_policy = "untrusted"
sandbox_mode    = "read-only"
allow_login_shell = false # optional hardening: disallow login shells for shell-based tools

# Optional: Allow network in workspace-write mode

[sandbox_workspace_write]
network_access = true

# Optional: granular approval policy

# approval_policy = { granular = {

#   sandbox_approval = true,

#   rules = true,

#   mcp_elicitations = true,

#   request_permissions = false,

#   skill_approval = false

# } }

```

您还可以将预设另存为 [配置文件](https://learn.chatgpt.com/docs/config-file/config-advanced#profiles)，然后使用 `codex --profile profile-name` 进行选择：

```toml
# ~/.codex/full_auto.config.toml

approval_policy = "on-request"
sandbox_mode    = "workspace-write"
```

```toml
# ~/.codex/readonly_quiet.config.toml

approval_policy = "never"
sandbox_mode    = "read-only"
```

### 在本地测试沙盒

要查看在 Codex 沙盒下运行命令时会发生什么，请使用这些 Codex CLI 命令：

```bash
# macOS

codex sandbox macos [--permissions-profile <name>] [--log-denials] [COMMAND]...
# Linux

codex sandbox linux [--permissions-profile <name>] [COMMAND]...
# Windows

codex sandbox windows [--permissions-profile <name>] [COMMAND]...
```

`sandbox` 命令也可以作为 `codex debug` 使用，并且平台辅助程序具有别名（例如 `codex sandbox seatbelt` 和 `codex sandbox landlock`）。

## 操作系统级别的沙盒

Codex 根据您的操作系统以不同的方式实施沙盒：

- **macOS** 使用 Seatbelt 策略并使用 `sandbox-exec` 运行命令，所使用的配置文件 (`-p`) 与您选择的 `--sandbox` 模式相对应。当受限的读取访问权限启用平台默认设置时，Codex 会附加一个经过精心筛选的 macOS 平台策略（而不是广泛地允许 `/System`），以保持常见工具的兼容性。
- **Linux** 默认使用 `bwrap` 加上 `seccomp`。
- **Windows** 在 [适用于 Linux 的 Windows 子系统 2 (WSL2)](https://learn.chatgpt.com/docs/windows/wsl) 中运行时，会使用 Linux 沙盒实现。Codex `0.114` 版本之前曾支持 WSL1；从 `0.115` 版本开始，Linux 沙盒迁移至 `bwrap`，因此不再支持 WSL1。在 Windows 上原生运行时，Codex 使用 [Windows 沙盒](https://learn.chatgpt.com/docs/windows/windows-sandbox#windows-sandbox) 实现。

如果您在 Windows 上使用 Codex IDE 扩展，它直接支持 WSL2。请在您的 VS Code 设置中进行以下配置，以便在 WSL2 可用时始终将代理保留在 WSL2 环境中：

```json
{
  "chatgpt.runCodexInWindowsSubsystemForLinux": true
}
```

这可以确保即使宿主操作系统是 Windows，IDE 扩展在命令、审批和文件系统访问方面也能继承 Linux 沙盒语义。在 [WSL 指南](https://learn.chatgpt.com/docs/windows/wsl) 中了解更多信息。

在 Windows 上原生运行时，请在 `config.toml` 中配置原生沙盒模式：

```toml
[windows]
sandbox = "unelevated" # or "elevated"
# sandbox_private_desktop = true  # default; set false only for compatibility

```

详情请参阅 [Windows 设置指南](https://learn.chatgpt.com/docs/windows/windows-sandbox#windows-sandbox)。

当您在诸如 Docker 之类的容器化环境中运行 Linux 时，如果宿主机或容器配置阻止了命名空间、setuid `bwrap` 或 Codex 所需的 `seccomp` 操作，沙盒可能无法正常工作。

在这种情况下，请配置您的 Docker 容器以提供所需的隔离，然后在容器内运行带有 `codex`（或 `--sandbox danger-full-access` 标志）的 `--dangerously-bypass-approvals-and-sandbox`。

### 在开发容器中运行 Codex

如果您的主机无法直接运行 Linux 沙盒，或者您的组织已经标准化了容器化开发，请使用开发容器运行 Codex，并让 Docker 提供外部隔离边界。这适用于 Visual Studio Code 开发容器及兼容工具。

使用 [Codex 安全开发容器示例](https://github.com/openai/codex/tree/main/.devcontainer) 作为参考实现。该示例安装了 Codex、常见开发工具、`bubblewrap` 以及基于防火墙的出站控制。

开发容器提供了实质性的保护，但它们并不能阻止每一次
  攻击。如果您在容器内使用 `--sandbox danger-full-access` 或
  `--dangerously-bypass-approvals-and-sandbox` 运行 Codex，恶意
  项目可以窃取开发容器内可用的任何内容，包括
  Codex 凭证。请仅对受信任的存储库使用此模式，并
  像在任何其他提权环境中一样监控 Codex 活动。

参考实现包括：

- 安装了 Codex 和常见开发工具的 Ubuntu 24.04 基础镜像；
- 用于出站访问的基于允许列表的防火墙配置文件；
- 用于在容器中重新打开工作区的 VS Code 设置和扩展推荐；
- 用于命令历史记录和 Codex 配置的持久化挂载；
- `bubblewrap`，因此当容器授予所需的权限时，Codex 仍然可以使用其 Linux 沙盒。

要尝试一下：

1. 安装 Visual Studio Code 和 [开发容器扩展](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)。
2. 将 Codex 示例 `.devcontainer` 设置复制到您的存储库中，或者直接从 Codex 存储库开始。
3. 在 VS Code 中，运行 **开发容器：在容器中打开文件夹...** 并选择 `.devcontainer/devcontainer.secure.json`。
4. 容器启动后，打开终端并运行 `codex`。

您也可以从 CLI 启动容器：

```bash
devcontainer up --workspace-folder . --config .devcontainer/devcontainer.secure.json
```

该示例包含三个主要部分：

- `.devcontainer/devcontainer.secure.json` 控制容器设置、功能、挂载、环境变量和 VS Code 扩展。
- `.devcontainer/Dockerfile.secure` 定义基于 Ubuntu 的镜像和已安装的工具。
- `.devcontainer/init-firewall.sh` 应用出站网络策略。

参考防火墙有意作为一个起点。如果您依赖域允许列表进行隔离，请实施适合您环境的 DNS 重绑定和 DNS 刷新保护，例如感知 TTL 的刷新或感知 DNS 的防火墙。

在容器内，选择以下模式之一：

- 如果开发容器配置文件授予了 `bwrap` 创建内部沙盒所需的权限，则保持 Codex 的 Linux 沙盒处于启用状态。
- 如果容器是您预期的安全边界，请在容器内使用 `--sandbox danger-full-access` 运行 Codex，这样 Codex 就不会尝试创建第二层沙盒。

## 版本控制

Codex 在版本控制工作流程下效果最佳：

- 在功能分支上工作，并在委派之前保持 `git status` 干净。这使得 Codex 补丁更容易隔离和还原。
- 首选基于补丁的工作流程（例如，`git diff`/`git apply`），而不是直接编辑跟踪的文件。频繁提交，以便您可以进行小增量回滚。
- 将 Codex 建议视为任何其他 PR：运行针对性验证、审查差异，并在提交消息中记录决策以供审计。

## 监控和遥测

Codex 支持通过 OpenTelemetry (OTel) 进行选择性加入的监控，以帮助团队审计使用情况、调查问题并满足合规性要求，同时不会削弱本地安全默认设置。遥测默认处于关闭状态；请在您的配置中显式启用它。

### 概述

- Codex 默认关闭 OTel 导出，以保持本地运行的自包含。
- 启用后，Codex 会发出结构化日志事件，涵盖聊天、API 请求、SSE/WebSocket 流活动、用户提示（默认已脱敏）、工具批准决策和工具结果。
- Codex 使用 `service.name`（发起者）、CLI 版本和环境标签标记导出的事件，以分离 dev/staging/prod 流量。

### 启用 OTel（可选）

在你的 Codex 配置中添加一个 `[otel]` 块（通常是 `~/.codex/config.toml`），选择一个导出器以及是否记录提示文本。

```toml
[otel]
environment = "staging"   # dev | staging | prod
exporter = "none"          # none | otlp-http | otlp-grpc
log_user_prompt = false     # redact prompt text unless policy allows
```

- `exporter = "none"` 保持插桩处于活动状态，但不将数据发送到任何地方。
- 要将事件发送到您自己的收集器，请选择以下之一：

```toml
[otel]
exporter = { otlp-http = {
  endpoint = "https://otel.example.com/v1/logs",
  protocol = "binary",
  headers = { "x-otlp-api-key" = "${OTLP_TOKEN}" }
}}
```

```toml
[otel]
exporter = { otlp-grpc = {
  endpoint = "https://otel.example.com:4317",
  headers = { "x-otlp-meta" = "abc123" }
}}
```

Codex 将事件批处理并在关闭时刷新它们。Codex 仅导出由其 OTel 模块生成的遥测数据。

### 事件类别

代表性事件类型包括：

- `codex.conversation_starts`（模型、推理设置、沙盒/审批策略）
- `codex.api_request`（尝试、状态/成功、持续时间以及错误详情）
- `codex.sse_event`（流事件类型、成功/失败、持续时间，以及 `response.completed` 上的 token 计数）
- `codex.websocket_request` 和 `codex.websocket_event`（请求持续时间加上每条消息的类型/success/error）
- `codex.user_prompt`（长度；除非明确启用，否则隐去内容）
- `codex.tool_decision`（已批准/已拒绝，来源：配置对比用户）
- `codex.tool_result`（持续时间、成功、输出片段）

关联的 OTel 指标（计数器加上持续时间直方图对）包括 `codex.api_request`、`codex.sse_event`、`codex.websocket.request`、`codex.websocket.event` 和 `codex.tool.call`（带有对应的 `.duration_ms` 仪表）。

有关完整的事件目录和配置参考，请参见 [GitHub 上的 Codex 配置文档](https://github.com/openai/codex/blob/main/docs/config.md#otel)。

### 安全和隐私指南

- 保持 `log_user_prompt = false`，除非策略明确允许存储提示内容。提示可能包含源代码和敏感数据。
- 仅将遥测数据路由到您控制的收集器；应用符合您合规要求的保留限制和访问控制。
- 将工具参数和输出视为敏感内容。尽可能倾向于在收集器或 SIEM 处进行隐去。
- 如果您不希望 Codex 在 `history.persistence` 下保存会话记录，请检查本地数据保留设置（例如，`history.max_bytes` / `CODEX_HOME`）。参见 [高级配置](https://learn.chatgpt.com/docs/config-file/config-advanced#history-persistence) 和 [配置参考](https://learn.chatgpt.com/docs/config-file/config-reference)。
- 如果您在关闭网络访问的情况下运行 CLI，OTel 导出将无法到达您的收集器。要进行导出，请在 `workspace-write` 模式下为 OTel 终端节点允许网络访问，或者从 Codex 云端导出并确保收集器域名在您的批准列表中。
- 定期审查事件，以检查审批/沙盒的更改以及意外的工具执行情况。

OTel 是可选的，旨在补充而非取代上述的沙盒和审批保护。

## 托管配置

企业管理员可以在 [托管配置](https://learn.chatgpt.com/docs/enterprise/managed-configuration) 中为其工作区配置 Codex 安全设置。有关设置和策略的详细信息，请参见该页面。

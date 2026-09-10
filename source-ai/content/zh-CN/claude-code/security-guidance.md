---
title: 在 Claude 编写代码时捕获安全问题
source_id: claude-code/security-guidance
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/security-guidance
owner: Anthropic
content_sha256: 6902efc58e5081202cafc7390023ebdea96b6e978c60456587d021171f9828c9
translation_of: claude-code/security-guidance
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/security-guidance)

Content owner: Anthropic

> ## 文档索引
> 在以下位置获取完整的文档索引：https://code.claude.com/docs/llms.txt
> 在进一步探索之前，使用此文件来发现所有可用页面。

# 在 Claude 编写代码时捕获安全问题

> 安装 security-guidance 插件，让 Claude 检查其自身的代码更改是否存在漏洞，并在同一会话中进行修复。

security guidance 插件使 Claude 在工作时检查其自身的代码更改是否存在常见漏洞，并在同一会话中修复所发现的问题。该插件会在代码进入拉取请求之前捕获诸如注入、不安全的反序列化和不安全的 DOM API 等问题，从而减少下游人工审查员需要承担的安全审查工作量。

安装后，该插件会自动运行。无需任何调用，也不必记住单独的命令。

该插件是 [Code Review](/docs/en/code-review) 的会话内伴侣，后者在拉取请求上运行。此插件减少了进入 PR 的内容。Code Review 则负责捕获那些仍然进入 PR 的问题。有关该插件如何与按需审查和 CI 扫描分层结合的信息，请参见 [它如何与其他安全工具配合使用](#how-this-fits-with-other-security-tools)。

## 先决条件

* Claude Code CLI 版本 2.1.144 或更高版本
* 您的 `PATH` 上需要安装 Python 3.7 或更高版本。代理式提交审查需要 Python 3.10 或更高版本，当 Claude Code 使用第三方提供商（如 Amazon Bedrock 或 Google Cloud 的 Agent Platform）时，所有模型支持的审查也是如此。该插件优先使用从 `python3.13` 到 `python3.10` 的带版本号的解释器，然后回退到 `python3`、`python` 和 `py -3`
* 您工作目录的 git 仓库。回合结束和提交审查会与 git 状态进行差异比较，并在仓库外静默跳过。每次编辑的模式检查在任何地方都有效

首次运行时，插件会在 `~/.claude/security/` 下创建一个虚拟环境，并将 Claude Agent SDK 安装到其中，这需要 `pip` 和网络访问权限。如果安装失败，或者可用的 Python 版本低于 3.10，则在第一方身份验证上的提交审查将回退为单次审查，而不是代理式审查；在第三方提供商（如 Amazon Bedrock 或 Google Cloud 的 Agent Platform）上，模型支持的审查本身需要 SDK，因此它们会被跳过。当原因是较旧的 Python 时，插件会显示一次性通知。

## 安装插件

在终端 Claude Code 会话中，从 [Anthropic 官方市场](/docs/en/discover-plugins#official-anthropic-marketplace) 安装：

```text theme={null}
/plugin install security-guidance@claude-plugins-official
```

`/plugin` 打开一个交互式面板，并且仅在终端 CLI 中可用。如果 Claude 回复 `/plugin` 在此环境中不可用，请使用另一种方式安装：

* **Claude 桌面应用程序、本地或 SSH 会话**：通过单击提示旁边的 **+** 按钮，然后选择 **Plugins** 和 **Add plugin** 来打开 [插件浏览器](/docs/en/desktop#install-plugins)
* **网络版 Claude Code 或桌面云会话**：在 `.claude/settings.json` 中声明插件，如下文 [在云会话中启用](#enable-in-cloud-sessions-and-shared-repositories) 所示

终端安装时会提示选择作用域。选择用户作用域可将插件写入您的用户设置，从而在您于此机器上启动的每个新本地会话中加载它。如果 Claude Code 报告 `Marketplace "claude-plugins-official" not found`，请使用 `/plugin marketplace add anthropics/claude-plugins-official` 添加市场。如果报告在市场中找不到该插件，说明您的本地副本已过时：请使用 `/plugin marketplace update claude-plugins-official` 刷新。然后重试安装。

然后使用 `/reload-plugins` 在当前会话中激活它，这会在不重启的情况下应用待处理的插件更改：

```text theme={null}
/reload-plugins
```

### 在云端会话和共享仓库中启用

用户范围的插件不会带入到[Claude Code网络版](/docs/en/claude-code-on-the-web), 因为那些会话运行在 Anthropic 基础设施上而不是您的机器上。要在那里启用该插件，或者为每个克隆仓库的人开启它，请在项目的签入设置中声明它:

```json .claude/settings.json theme={null}
{
  "enabledPlugins": {
    "security-guidance@claude-plugins-official": true
  }
}
```

管理员可以通过在[托管设置](/docs/en/admin-setup)中设置 [`enabledPlugins`](/docs/en/settings#plugin-settings) 来在整个组织范围内启用该插件。

## 插件检查的内容

该插件在三个节点审查 Claude 的工作，每个节点的深度不同:

* [在每次文件编辑时](#on-each-file-edit): 对有风险的调用进行快速模式匹配，不进行模型调用
* [在每轮结束时](#at-the-end-of-each-turn): 对该轮更改的所有内容进行后台模型审查
* [在 Claude 进行每次提交或推送时](#on-each-commit-or-push-claude-makes): 阅读周围代码的更深入的代理审查

您可以通过[添加您自己的规则](#add-your-own-rules).来扩展每一层。内置检查无法单独移除，但您可以独立[禁用每一层](#disable-or-uninstall).

### 在每次文件编辑时

当 Claude 写入文件时，插件会扫描新内容以查找已知的风险模式。这是无需模型调用的模式匹配，因此不会增加任何使用成本。

示例模式类别：

* 动态代码执行: `eval(`, `new Function`, `os.system`, `child_process.exec`
* 不安全的反序列化: `pickle`
* DOM注入: `dangerouslySetInnerHTML`, `.innerHTML =`, `document.write`
* 工作流文件: 在 `.github/workflows/` 下的编辑，这可以授予仓库级别的权限

该检查在编辑完成后运行，并将警告附加到 Claude 的上下文中以用于下一步。每个警告在每个会话中针对每个文件的每个模式触发一次，因此同一文件中的重复匹配不会刷屏对话。

你可以 [添加你自己的模式](#add-custom-per-edit-patterns) 到此层，使用一个 `security-patterns.yaml` 文件。

### 在每一轮结束时

一轮是指 Claude 响应的一个周期：你发送一条消息，Claude 工作并回复，然后这一轮结束。在每一轮之后，插件会计算这一轮期间工作树中所有更改的 git diff，包括来自 Claude 编辑工具、Bash 命令和子代理的更改，并将其发送到一个专注于安全的独立 Claude 审查。审查在后台运行，因此 Claude 的回复不会延迟。如果审查发现问题，Claude 会收到有关这些发现的新提示，并将它们作为后续跟进予以解决。

这可以捕获字符串匹配无法做到的问题，例如：

* 授权绕过
* 不安全的直接对象引用
* 注入
* 服务器端请求伪造
* 弱密码学

你可以直接在会话中看到发现的问题和 Claude 的解决方案。审查每轮最多覆盖 30 个更改的文件，并且在交还给你之前最多连续触发三次。

### 在 Claude 每次进行提交或推送时

当 Claude 通过其 Bash 工具运行 `git commit` 或 `git push` 时，该插件会在后台对更改运行更深度的代理审查。此审查会读取周边代码（包括调用方、清理器和相关文件），以在报告之前确定发现的问题是否真实。这些额外的上下文使得那些孤立看起来危险但在您的代码库中安全的模式保持较低的误报率。

此层仅在 Claude 通过其 Bash 工具进行提交和推送时触发。您从自己的 shell 运行的提交（包括会话内的 `!` shell 转义）不会被审查。提交和推送审查的上限为每滚动小时 20 次。如果提交审查的发现与回合结束审查已报告的内容重复，Claude 不会被重新提示，因此干净的提交不会在此层产生任何可见输出。

### 审查的独立性与局限性

该插件不会要求编写代码的同一个 Claude 实例来进行自我评分。每次编辑的检查是一个确定性的字符串匹配，不涉及任何模型。回合结束和提交审查作为单独的 Claude 调用运行，使用全新的上下文和专注于安全的提示词：审查者从差异（diff）开始，对原始方法没有偏好，且仅被指示去发现问题。

没有任何一层会阻止写入或提交。发现的问题会作为指令传达给正在编写的 Claude，Claude 会在对话中解决这些问题，而审查模型可能会遗漏某些问题。请将此插件视为深度防御的一层，而不是一个完整的安全解决方案。参见 [它如何与其他安全工具配合使用](#how-this-fits-with-other-security-tools)。

## 添加您自己的规则

该插件有两个扩展点：一个用于模型支持审查的 Markdown 指导文件，以及一个用于每次编辑字符串匹配的 YAML 或 JSON 模式文件。两者都是附加的。您可以添加检查，但不能在这些文件中禁用内置检查。

### 为模型支持的审查添加指导

在您的项目中创建 `.claude/claude-security-guidance.md` 并用通俗的语言描述您的威胁模型和审查清单。模型支持的审查会将其作为额外上下文与内置漏洞清单一起加载。

以下示例适用于具有基于角色的管理路由和客户数据日志记录策略的 Web 服务：

```markdown .claude/claude-security-guidance.md theme={null}
# Security guidance for this repo

- Do not log `customer_id` or `account_number` at INFO level or above.
- All routes under `/admin` must call `require_role("admin")` before any database read.
- Use `crypto.timingSafeEqual` for token comparison instead of `===`.
```

这些规则是审查者的指导，而不是确定性的护栏。该插件将违规行为作为发现展示出来供 Claude 修复，但它不会阻止写入，也不保证能捕捉到每一次违规。指导仅具有附加性：规定忽略某一类漏洞的规则并不会抑制这些发现。若要强制执行，请将此插件与一个 [阻止编辑的钩子](/docs/en/hooks-guide#block-edits-to-protected-files) 或 CI 检查结合使用。

### 添加自定义的每次编辑模式

创建 `.claude/security-patterns.yaml` 以将正则表达式或子字符串规则添加到 [每次编辑模式检查](#on-each-file-edit)。它们作为确定性字符串匹配与内置模式一起运行：

```yaml .claude/security-patterns.yaml theme={null}
patterns:
  - rule_name: internal_api_key
    substrings: ["sk_live_", "AKIA"]
    reminder: "Hardcoded API key prefix. Load credentials from the secret manager."
  - rule_name: tenant_unfiltered_query
    regex: "\\.objects\\.all\\(\\)"
    paths: ["**/src/tenants/**"]
    reminder: "Multi-tenant code must filter by org_id."
```

| 字段             | 类型   | 描述                                                                                                                                                     |
| :-------------- | :----- | :------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `rule_name`     | 字符串 | 警告中显示的标识符                                                                                                                         |
| `reminder`      | 字符串 | 追加到 Claude 上下文中的警告文本，上限为 1 KB                                                                                               |
| `regex`         | 字符串 | 与编辑内容进行匹配的 Python 正则表达式                                                                                                         |
| `substrings`    | 列表   | 字面子串；提供此项或 `regex`                                                                                                             |
| `paths`         | 列表   | 可选的 glob 模式；该规则仅适用于匹配的文件。Glob 匹配完整的文件路径，因此请在项目相对路径模式前加上 `**/` |
| `exclude_paths` | 列表   | 要跳过的可选 glob 模式；匹配方式与 `paths`                                                                                                |

该插件还会读取 `.claude/security-patterns.yml` 和 `.claude/security-patterns.json`，它们使用相同的模式。JSON 可在任何 Python 安装中运行。YAML 格式要求 PyYAML 可导入，而该插件不会为您安装它。该插件最多加载 50 条自定义规则，并跳过那些看起来容易发生灾难性回溯的正则表达式。

### 规则文件查找位置

该插件会在相同的位置查找 `claude-security-guidance.md` 和 `security-patterns.yaml`，这与插件的启用方式无关：

| 范围         | 路径                                        | 备注                                    |
| :------------ | :------------------------------------------ | :--------------------------------------- |
| 用户          | `~/.claude/claude-security-guidance.md`     | 适用于你机器上的每个项目 |
| 项目       | `.claude/claude-security-guidance.md`       | 随仓库签入           |
| 项目本地 | `.claude/claude-security-guidance.local.md` | 被 Git 忽略，用于个人覆盖       |

该插件会加载所有存在的位置并将它们拼接起来，对于指导文件，合并后的上限为 8 KB。管理员可以通过设备管理将用户范围的文件推送到 `~/.claude/`，从而分发组织范围内的规则。相同的路径也适用于 `security-patterns.yaml`。

## 使用成本

[per-edit pattern check](#on-each-file-edit) 不进行模型调用，也不增加任何成本。[end-of-turn](#at-the-end-of-each-turn) 和 [commit](#on-each-commit-or-push-claude-makes) 审查每次都会消耗额外的模型用量，并且像任何其他 Claude 请求一样计入你的 [usage](/docs/en/costs)。提交审查是代理式的，每次提交可能需要多个模型回合，每个滚动小时的上限为 20 次审查。预计在每次更改文件的回合中大约进行一次审查调用，而每次提交会进行一次更深入的审查，两者均受上述上限约束。

这两项基于模型的审查默认使用 Claude Opus 4.7。设置 `SECURITY_REVIEW_MODEL` 来为回合结束审查选择不同的模型，设置 `SG_AGENTIC_MODEL` 来为提交审查选择不同的模型。

该插件在所有套餐中均可用。

## 禁用或卸载

要在保留其余部分的同时关闭单个层，请设置相应的环境变量：

| 变量                        | 效果                                                                     |
| :------------------------------ | :------------------------------------------------------------------------- |
| `ENABLE_PATTERN_RULES=0`        | 禁用 [per-edit pattern check](#on-each-file-edit)                   |
| `ENABLE_STOP_REVIEW=0`          | 禁用 [end-of-turn diff review](#at-the-end-of-each-turn)            |
| `ENABLE_COMMIT_REVIEW=0`        | 禁用 [commit and push review](#on-each-commit-or-push-claude-makes) |
| `ENABLE_CODE_SECURITY_REVIEW=0` | 一次性禁用所有基于模型的审查                                   |
| `SECURITY_GUIDANCE_DISABLE=1`   | 在不卸载的情况下完全禁用插件                           |

要在你的用户范围内暂停该插件：

```text theme={null}
/plugin disable security-guidance@claude-plugins-official
```

要从你的用户范围内移除它：

```text theme={null}
/plugin uninstall security-guidance@claude-plugins-official
```

如果该插件是通过项目的 `.claude/settings.json` 启用的，从 `/plugin` 禁用它会将覆盖配置写入你的 `.claude/settings.local.json`，而不是编辑签入的文件，因此该插件对你保持关闭状态，而队友不受影响。 {/* min-version: 2.1.203 */}同一个对话框还提供了通过从共享的 `.claude/settings.json` 中移除插件来为所有人卸载它的选项；该选项需要 Claude Code v2.1.203 或更高版本。如果它是通过 [managed settings](/docs/en/admin-setup) 启用的，则只有管理员才能禁用它。

## 插件如何与 Claude Code 集成

插件完全构建在 [hooks](/docs/en/hooks) 之上，这是一种在 Claude 循环的特定节点运行您自己的代码的机制。它注册了：

| 钩子事件                                                          | 用途                                                                        |
| :--------------------------------------------------------------- | :-------------------------------------------------------------------------- |
| `SessionStart`                                                   | 引导插件的 Python 环境                                              |
| `UserPromptSubmit`                                               | 捕获工作树基线，供回合结束时审查进行差异比对 |
| `PostToolUse` 在 `Edit`、`Write` 和 `NotebookEdit` 上            | 每次编辑的模式匹配                                                       |
| `Stop`                                                           | 回合结束时的差异审查，在后台运行                               |
| `PostToolUse` 在 `Bash` 上，过滤 `git commit` 和 `git push` | 提交和推送审查，在后台运行                               |

如果您构建自己的钩子，[plugin's source](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/security-guidance) 是一个实际可用的示例，展示了如何从钩子中运行单独的模型调用并将结果反馈给会话。

## 如何将其与其他安全工具结合使用

该插件是纵深防御方法中的一层。它能在问题最早出现时（当代码仍在编辑器中时）将其捕获，但这并不是绝对的保证，也不能取代后续的检查。一个典型的技术栈包括：

| 阶段                   | 工具                                                      | 覆盖内容                                                                                          |
| :--------------------- | :-------------------------------------------------------- | :------------------------------------------------------------------------------------------------------- |
| 会话内                 | 安全指导插件                                  | Claude 编写的代码中的常见漏洞，在同一会话中修复                                  |
| 按需，单次扫描         | [`/security-review`](/docs/en/commands#all-commands)           | 对当前分支进行一次性安全扫描，在您要求时运行                                           |
| 按需，深度扫描         | [Claude Security plugin](/docs/en/claude-security)             | 对仓库或差异进行多智能体漏洞扫描，并提供独立审查的发现和补丁 |
| 拉取请求时             | [Code Review](/docs/en/code-review), Team 和 Enterprise 计划 | 具有完整代码库上下文的多智能体正确性和安全审查                                   |
| 在 CI 中                  | 您现有的静态分析和依赖扫描器     | 特定语言的规则、供应链检查以及插件不尝试进行的策略执行          |

每个后续阶段都会捕获早期阶段遗漏的内容。插件的价值在于减少到达它们的问题量，而不是消除对它们的需要。

## 故障排除

插件会将运行时诊断信息写入 `~/.claude/security/log.txt`。如果审查没有出现，请先检查那里。

审查层跳过且在对话中没有消息的常见原因：

* 该目录不是 git 仓库：回合结束和提交审查需要 git 状态，在仓库外会跳过
* 会话没有 Anthropic 身份验证且未配置第三方提供商：基于模型的审查将被跳过，仅运行每次编辑的模式检查
* 存在 `security-patterns.yaml` 文件但无法导入 PyYAML：该文件将被忽略。请改用 `security-patterns.json`

## 相关资源

为了深入了解本页涉及的内容：

* [代码审查](/docs/en/code-review): 设置 PR 阶段的多智能体审查
* [使用钩子自动执行操作](/docs/en/hooks-guide): 在相同的生命周期点构建您自己的检查
* [发现并安装插件](/docs/en/discover-plugins#official-anthropic-marketplace): 浏览其他官方插件

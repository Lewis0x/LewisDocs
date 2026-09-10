---
title: 配置自动模式
source_id: claude-code/auto-mode-config
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/auto-mode-config
owner: Anthropic
content_sha256: 6803653df6a7f24538430c747200083c25c54250774be0dad59fea066f7b38e4
translation_of: claude-code/auto-mode-config
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/auto-mode-config)

Content owner: Anthropic

> ## 文档索引
> 在以下地址获取完整的文档索引： https://code.claude.com/docs/llms.txt
> 在深入探索之前，请使用此文件来发现所有可用页面。

# 配置自动模式

> 告诉自动模式分类器您的组织信任哪些仓库、存储桶和域名。设置环境上下文，覆盖默认的阻止和允许规则，并使用自动模式 CLI 子命令检查您的有效配置。

[自动模式](/docs/en/permission-modes#eliminate-prompts-with-auto-mode) 允许 Claude Code 在没有常规权限提示的情况下运行，方法是通过分类器路由工具调用，该分类器会阻止任何不可逆的、破坏性的或旨在针对您环境之外的操作。拒绝和显式询问规则会在分类器之前进行评估，并且仍然会阻止或提示。使用 `autoMode` 设置块来告诉该分类器您的组织信任哪些仓库、存储桶和域名，这样它就会停止阻止常规的内部操作。

<Note>
  自动模式在每个提供商的所有用户中均可用，包括 Anthropic API、[AWS 上的 Claude 平台](/docs/en/claude-platform-on-aws)、Amazon Bedrock、Google Cloud 的 Agent Platform、Microsoft Foundry 以及已登录的 [Claude apps gateway](/docs/en/claude-apps-gateway) 会话。如果 Claude Code 报告您的账户无法使用自动模式，请查看 [完整要求](/docs/en/permission-modes#eliminate-prompts-with-auto-mode)，其中还涵盖了受支持的模型以及 Team 和 Enterprise 计划的所有者启用情况。 {/* min-version: 2.1.207 */}在 v2.1.158 到 v2.1.206 版本中，Amazon Bedrock、Google Cloud 的 Agent Platform、Microsoft Foundry 和 Claude apps gateway 会话上的自动模式需要设置 `CLAUDE_CODE_ENABLE_AUTO_MODE=1`；v2.1.207 版本取消了此要求。
</Note>

默认情况下，分类器仅信任工作目录和当前仓库配置的远程仓库。诸如推送到贵公司的源代码控制组织或写入团队云存储桶之类的操作会被阻止，直到您将它们添加到 `autoMode.environment` 中。

有关如何启用自动模式及其默认阻止的内容，请参见 [权限模式](/docs/en/permission-modes#eliminate-prompts-with-auto-mode)。此页面是配置参考。

本页面涵盖如何：

* [添加人工检查点](#add-a-human-checkpoint)，以通过 `permissions.ask` 处理推送和拉取请求
* [选择在何处设置规则](#where-the-classifier-reads-configuration)，跨越 CLAUDE.md、用户设置和托管设置
* [定义受信任的基础设施](#define-trusted-infrastructure)，使用 `autoMode.environment`
* [覆盖阻塞和允许规则](#override-the-block-and-allow-rules)，当默认设置不适合您的流水线时
* [通过分类器路由所有 shell 命令](#route-all-shell-commands-through-the-classifier)，使用 `autoMode.classifyAllShell`
* [检查您的有效配置](#inspect-the-defaults-and-your-effective-config)，使用 `claude auto-mode` 子命令
* [审查拒绝操作](#review-denials)，以便您知道接下来要添加什么

## 常见边界

自动模式允许推送到您正在其中工作的仓库的任何分支（包括默认分支），并默认允许创建拉取请求。名称将其标记为部署或发布目标的非默认分支（例如 `production`、`release` 或 `gh-pages`）不在该默认设置的涵盖范围内：分类器会根据自身的条件判断对其的推送，包括将其视为生产部署。推送的内容也仍会被检查，因此强制推送、将机密引入提交，或者当 CI 或部署管道运行时会导致将机密发送到仓库之外的更改仍然会被阻止。

<Info>在 v2.1.211 之前，分类器仅允许推送到您的工作分支、Claude 创建的分支以及向默认分支的常规推送。</Info>

如果您希望在每次推送或拉取请求之前都有人工检查点，请添加权限规则：[下方指南](#add-a-human-checkpoint) 会为其他所有操作保持自动模式开启。

### 添加人工检查点

最直接的机制是 [`permissions.ask`](/docs/en/permissions#permission-rule-syntax)。像下面这样具有内容作用域的询问规则会在分类器之前进行评估，并且即使在自动模式下也总是强制弹出权限提示，因为显式询问规则代表您明确表达了希望对该操作进行提示的意图。将规则添加到您的 [settings](/docs/en/settings#settings-files) 中：

```json theme={null}
{
  "permissions": {
    "ask": [
      "Bash(git push *)",
      "Bash(gh pr create *)"
    ]
  }
}
```

选择与您所需边界严格程度相匹配的机制：

| 边界                              | 机制                                                      | 自动模式下的行为                                                                                                                                                                                               |
| :-------------------------------- | :--------------------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 操作前提示                        | `permissions.ask`                                          | 对于像上述方法一样的内容作用域规则总是会进行提示。分类器无法自动批准匹配的操作。                                                                                                                                  |
| 从不运行操作                      | `permissions.deny`                                         | 在咨询分类器之前进行阻止。分类器和用户意图都无法覆盖它。                                                                                                                                                          |
| 本会话的一次性边界                | 在对话中声明，例如“在我审查之前不要推送”                | 分类器会阻止匹配的操作，但如果 [context compaction](/docs/en/costs#reduce-token-usage) 删除了声明该边界的消息，则边界可能会丢失。使用询问或拒绝规则可获得持久保证。 |

## 分类器读取配置的位置

分类器读取 Claude 自身加载的相同 [CLAUDE.md](/docs/en/memory) 内容，因此您项目的 CLAUDE.md 中的“永不强制推送”等指令会同时引导 Claude 和分类器。对于项目规范和行为规则，请从这里开始。

对于跨项目适用的规则，例如受信任的基础设施或组织范围的拒绝规则，请使用 `autoMode` 设置块。分类器从以下作用域读取 `autoMode`：

| 作用域                          | 文件                                            | 用于                                                 |
| :----------------------------- | :---------------------------------------------- | :--------------------------------------------------- |
| 单个开发者                      | `~/.claude/settings.json`                       | 个人受信任的基础设施                                 |
| 组织范围                        | [Managed settings](/docs/en/server-managed-settings) | 分发给所有开发者的受信任基础设施                       |
| `--settings` 标志或 Agent SDK | 内联 JSON                                     | 用于自动化的单次调用覆盖                             |

分类器不从 `.claude/settings.json` 或 `.claude/settings.local.json` 的项目设置中读取 `autoMode`。这两个文件都位于仓库目录中，否则签入的仓库或构建步骤可能会注入其自身的允许规则。在 v2.1.207 之前，分类器也读取 `.claude/settings.local.json`；请将该文件中的任何 `autoMode` 块移动到 `~/.claude/settings.json`。排除 `.claude/settings.local.json` 也杜绝了仓库提交该文件或本地工具或构建步骤写入该文件的情况。

每个作用域中的条目会被合并。开发者可以使用个人条目扩展 `environment`、`allow`、`soft_deny` 和 `hard_deny`，但不能删除托管设置提供的条目。由于允许规则在分类器中充当软阻止规则的例外情况，因此开发者添加的 `allow` 条目可以覆盖组织的 `soft_deny` 条目：这种合并是累加的，而不是硬性策略边界。

<Note>
  分类器是在 [权限系统](/docs/en/permissions) 之后运行的第二道门。对于无论用户意图或分类器配置如何都绝不能执行的操作，请在托管设置中使用 `permissions.deny`，它会在查询分类器之前阻止该操作，并且无法被覆盖。
</Note>

## 定义受信任的基础设施

对于大多数组织，`autoMode.environment` 是您唯一需要设置的字段。它告诉分类器哪些仓库、存储桶和域名是受信任的：分类器使用它来决定什么是“外部”，因此任何未列出的目的地都是潜在的数据外泄目标。

从 Claude Code v2.1.198 开始，`claude auto-mode defaults` 会打印三种环境条目。v2.1.195 之前的版本仅打印前五个信任槽。

* **上下文槽**：描述您的组织、技术栈和安全态势，以便分类器读取您上下文中的其他规则。与其他两种类型不同，上下文槽没有针对它们自身的规则。每个默认值为 `None configured` 或其旁边注明的保守假设：
  * **组织**
  * **Claude Code 的主要用途**：默认为软件开发
  * **云提供商**
  * **仓库可见性**：除非其远程主机和名称另有指示，否则假定仓库为私有，{/* min-version: 2.1.200 */}或者分类器读取的对话中较早进行的可见性检查显示其为公开。分类器读取的是您的消息和 Claude 运行的命令，而不是它们的输出，因此证据必须是它能读取到的内容，例如您自己的消息指明该仓库为公开；`gh repo view` 单独的输出无法到达分类器。对话记录证据检查需要 Claude Code v2.1.200 或更高版本
  * **内部共享 / 代码片段托管**：在您指定之前，公共粘贴和 gist 服务被视为在信任边界之外
  * **组织特定的 CLI**
  * **机密管理**
  * **CI/CD 部署目标**
  * **网络态势**
  * **受保护的部署命名空间 / 环境**：在您命名之前，回退到“敏感远程目标”启发式规则
  * **数据保留 / 降密**
* **信任槽**：命名分类器视为在您边界内的内容。这些槽位包括受信任的仓库、源代码控制、受信任的内部域名、受信任的云存储桶、关键内部服务和内部包注册表。仓库和源代码控制条目默认为工作仓库及其配置的远程仓库。所有其他信任槽默认为 `None configured`，因此在您添加之前，不会信任任何其他内容。 {/* min-version: 2.1.203 */}仓库的可见性仅限定于机密材料：私有仓库是机密材料的可接受目的地，但将仓库设为私有绝不会批准将机密或个人或受托数据放入其中，并且分类器将移植、重定向或首次从工作仓库外部读取的内容视为非该仓库自身的工作。此范围限定需要 Claude Code v2.1.203 或更高版本。
* **敏感度槽位**：命名保护性规则视为高风险的内容。这些槽位包括敏感数据位置与受众、敏感远程目标以及受保护的 IaC 范围。每个槽位都默认采用广泛的启发式规则，例如将名称中包含 `prod` 或 `production` 的任何主机或命名空间视为敏感远程目标，因此保护性规则在您配置任何内容之前就已生效。在敏感度槽位中命名具体目标会使这些规则应用于已命名的目标，而不是启发式规则。

<Info>在 v2.1.211 之前，上下文槽位还包括一个“默认/受保护分支”条目，该条目将 `main` 和 `master` 视为受保护，直到您命名其他分支。v2.1.211 移除了它：默认情况下允许 [推送到您正在使用的仓库的任何分支](#common-boundaries)，因此没有需要配置的受保护分支默认值。</Info>

要在默认值旁边添加您自己的条目，请在数组中包含文字字符串 `"$defaults"`。默认条目会被拼接到该位置，因此您的自定义条目可以放在它们之前或之后。

以下示例保留了默认条目，并添加了一个组织的仓库、存储桶、域名和服务。

```json theme={null}
{
  "autoMode": {
    "environment": [
      "$defaults",
      "Source control: github.example.com/acme-corp and all repos under it",
      "Trusted cloud buckets: s3://acme-build-artifacts, gs://acme-ml-datasets",
      "Trusted internal domains: *.corp.example.com, api.internal.example.com",
      "Key internal services: Jenkins at ci.example.com, Artifactory at artifacts.example.com"
    ]
  }
}
```

保存设置后，运行 `claude auto-mode config` 以 [确认生效的规则](#inspect-the-defaults-and-your-effective-config) 包含您的条目。

条目是散文形式的描述，而不是正则表达式或工具模式。分类器会将它们作为自然语言规则读取。请按照您向新工程师描述基础设施的方式来编写它们。一个详尽的环境部分涵盖：

* **组织**：您的公司名称以及 Claude Code 的主要用途，例如软件开发、基础设施自动化或数据工程
* **源代码控制**：您的开发人员推送代码的每一个 GitHub、GitLab 或 Bitbucket 组织
* **云提供商和受信任的存储桶**：Claude 应该能够读取和写入的存储桶名称或前缀
* **受信任的内部域名**：您网络内部的 API、仪表板和服务的主机名，例如 `*.internal.example.com`
* **关键的内部服务**：CI、构件注册表、内部软件包索引、事件工具
* **内部软件包注册表**：安装时应通过路由的私有 npm、PyPI 或其他注册表，以便绕过它而使用公共注册表的安装被阻止
* **敏感数据位置与受众**：包含个人数据、机密业务数据、凭证、受监管数据或类似敏感资料的存储桶、数据库或路径，以及每个位置的数据可以共享的受众群体，以便分类器保护这些位置，而不是通过内容进行猜测。 {/* min-version: 2.1.195 */}{/* max-version: 2.1.197 */}Claude Code v2.1.195 到 v2.1.197 将此条目命名为 PII / 受监管数据位置，并且仅涵盖包含个人或受监管数据的位置，而没有受众维度
* **敏感远程目标**：被视为生产环境的命名空间、主机或容器，因此对它们进行的远程 shell 和端口转发需要您的明确批准
* **受保护的 IaC 范围**：对其执行应用或销毁操作时始终要求您指明变更内容的基础设施资源
* **额外的上下文**：受监管行业的限制、多租户基础设施或合规性要求，这些会影响分类器对风险内容的判定

内部软件包注册表、敏感数据位置与受众、敏感远程目标和受保护的 IaC 范围条目需要 Claude Code v2.1.195 或更高版本。早期版本仍会将它们作为普通上下文读取，但没有针对它们的内置规则。

一个有用的起始模板：填写括号中的字段并删除不适用的行。

```json theme={null}
{
  "autoMode": {
    "environment": [
      "$defaults",
      "Organization: {COMPANY_NAME}. Primary use: {PRIMARY_USE_CASE, e.g. software development, infrastructure automation}",
      "Source control: {SOURCE_CONTROL, e.g. GitHub org github.example.com/acme-corp}",
      "Cloud provider(s): {CLOUD_PROVIDERS, e.g. AWS, GCP, Azure}",
      "Trusted cloud buckets: {TRUSTED_BUCKETS, e.g. s3://acme-builds, gs://acme-datasets}",
      "Trusted internal domains: {TRUSTED_DOMAINS, e.g. *.internal.example.com, api.example.com}",
      "Key internal services: {SERVICES, e.g. Jenkins at ci.example.com, Artifactory at artifacts.example.com}",
      "Additional context: {EXTRA, e.g. regulated industry, multi-tenant infrastructure, compliance requirements}"
    ]
  }
}
```

您提供的上下文越具体，分类器就越能区分常规内部操作和数据泄露企图。

您不需要一次性填写所有内容。一个合理的推进步骤：从默认设置开始，添加您的源代码控制组织和关键内部服务，这能解决最常见的误报，比如推送到您自己的代码库。接下来添加受信任的域名和云存储桶。随着阻塞规则的出现，再填补其余部分。

## 覆盖阻塞和允许规则

三个额外字段允许你替换分类器的内置规则列表：

* `autoMode.hard_deny`：无条件安全边界
* `autoMode.soft_deny`：用户意图可以清除的破坏性操作
* `autoMode.allow`：软阻塞规则的例外

每一个都是描述性文本数组，作为自然语言规则读取。对于在分类器之前运行的基于工具模式的硬阻塞，请使用 [`permissions.deny`](/docs/en/permissions)。

在分类器内部，优先级分为四个层级：

* `hard_deny` 规则无条件阻塞。用户意图和 `allow` 例外不适用。
* `soft_deny` 规则接下来阻塞。用户意图和 `allow` 例外可以覆盖这些规则。
* `allow` 规则随后作为例外覆盖匹配的 `soft_deny` 规则。
* 明确的用户意图会覆盖剩余的软阻塞：如果用户的消息直接且具体地描述了 Claude 即将采取的确切操作，即使匹配到了 `soft_deny` 规则，分类器也会允许它。

一般请求不计为明确意图。要求 Claude “清理仓库”并不授权强制推送，但要求 Claude “强制推送此分支”则可以。

要放宽限制，当分类器反复标记默认例外未涵盖的常规模式时，请添加到 `allow` 中。要收紧限制，对于默认设置遗漏的特定于您环境的破坏性风险，请添加到 `soft_deny` 中；或者对于绝不能跨越的安全边界，请添加到 `hard_deny` 中。

要在添加自己规则的同时保留内置规则，请在数组中包含字面字符串 `"$defaults"`。默认规则将被拼接到该位置，因此您的自定义规则可以放在它们之前或之后，并且随着内置列表在不同版本中的更改，您可以继续继承更新。

以下示例在所有四个列表中保留默认设置，并向每个列表添加特定于组织的规则。

```json theme={null}
{
  "autoMode": {
    "environment": [
      "$defaults",
      "Source control: github.example.com/acme-corp and all repos under it"
    ],
    "allow": [
      "$defaults",
      "Deploying to the staging namespace is allowed: staging is isolated from production and resets nightly",
      "Writing to s3://acme-scratch/ is allowed: ephemeral bucket with a 7-day lifecycle policy"
    ],
    "soft_deny": [
      "$defaults",
      "Never run database migrations outside the migrations CLI, even against dev databases",
      "Never modify files under infra/terraform/prod/: production infrastructure changes go through the review workflow"
    ],
    "hard_deny": [
      "$defaults",
      "Never send repository contents to third-party code-review APIs"
    ]
  }
}
```

<Danger>
  在没有 `"$defaults"` 的情况下设置 `environment`、`allow`、`soft_deny` 或 `hard_deny` 中的任何一个，都会替换该部分的整个默认列表。如果在没有 `"$defaults"` 的情况下设置数组，您将放弃该部分的内置规则：

  * `soft_deny`：每条内置软阻塞规则，包括强制推送、`curl | bash`、生产环境部署和自动模式绕过
  * `hard_deny`：内置数据泄露规则
</Danger>

每个部分都是独立评估的，因此仅设置 `environment` 会保留默认的 `allow`、`soft_deny` 和 `hard_deny` 列表不变。

仅当您打算完全接管该列表时，才省略 `"$defaults"`。为了安全地执行此操作，请运行 `claude auto-mode defaults` 以打印内置规则，将它们复制到您的设置文件中，然后根据您自己的流水线和风险承受能力审查每条规则。

## 通过分类器路由所有 shell 命令

默认情况下，诸如 `Bash(npm test)` 之类的狭窄 Bash 和 PowerShell 允许规则会延续到自动模式中，并在分类器运行之前进行解析。自动模式仅暂停授予任意代码执行权限的广泛规则，例如 `Bash(*)` 或通配符解释器。这意味着狭窄的规则仍然可能在分类器未察觉的情况下放行破坏性参数，例如规则前缀未预料到的脚本路径或标志。

将 `autoMode.classifyAllShell` 设置为 `true`，以在自动模式处于活动状态时暂停所有 Bash 和 PowerShell 允许规则，从而使分类器评估每个 shell 命令，无论您的允许列表如何。

```json theme={null}
{
  "autoMode": {
    "classifyAllShell": true
  }
}
```

这是以延迟换取覆盖率：原本会被允许规则立即批准的命令现在需要等待分类器决策，并且每个 shell 命令都计为一次分类器调用。

此设置仅在自动模式处于活动状态时适用，您的允许规则在其他权限模式下表现正常。

<Note>
  `autoMode.classifyAllShell` 需要 Claude Code v2.1.193 或更高版本。早期版本会忽略此键并继续将狭窄的 shell 允许规则延续到自动模式中。
</Note>

## 检查默认配置与您的有效配置

`claude auto-mode` 子命令可帮助您检查、验证和重置配置。

以 JSON 格式打印内置的 `environment`、`allow`、`soft_deny` 和 `hard_deny` 规则：

```bash theme={null}
claude auto-mode defaults
```

{/* min-version: 2.1.208 */}要在不通过 `jq` 进行管道传输的情况下读取单个规则的完整措辞，请传入 `--label` 并附上规则标签的开头部分，例如 `claude auto-mode defaults --label 'Git Destructive'`。匹配是对每个规则标签进行不区分大小写的前缀匹配，没有匹配项的部分将打印为空列表。需要 Claude Code v2.1.208 或更高版本。

以 JSON 格式打印分类器实际使用的内容，在已设置的地方应用您的设置，其他情况则使用默认值：

```bash theme={null}
claude auto-mode config
```

`defaults` 和 `config` 都将这四个规则列表作为单个 JSON 对象打印，其中每个规则都是一个文本字符串。这是一个截断的示例：

```json theme={null}
{
  "allow": [
    ...
    "Test Artifacts: Hardcoded test API keys, placeholder credentials in examples, or hardcoding test cases. Placeholder means authored as a placeholder — a file or value copied from a real secret or sensitive path is never a test artifact (see Sensitive-Source Provenance).",
    ...
  ],
  "soft_deny": [
    "Git Destructive [named+specifics — **must name:** the destructive operation and its target]: Force pushing (`git push --force`), deleting remote branches, tags, or releases, or rewriting remote history. Also `git commit --amend` when the commit being rewritten is not the agent's own unpushed work: either no prior `git commit` is visible (HEAD pre-dates the session), or a `git push` of the current branch is visible after the most recent commit (it has been pushed). Clears when the user asked to amend/reword/fixup, or when it is a message-only reword (`--amend -m …`, nothing newly staged) of a commit the agent visibly created this session.",
    ...
  ],
  "hard_deny": [...],
  "environment": [
    ...
    "**Trusted repo**: The git repository the agent started in (its working directory) and its configured remote(s). When the repo's public/private visibility is given — by the Repository visibility entry or the user's own message — use it to scope what is OK to commit or push there: confidential material is fine in a private repo; in a public one, only that repo's own work is — and content ported, repointed, or first read from outside this session's repo is not its own work, whoever directed the port. Visibility scopes confidential material only: secrets and sensitive data (personal & entrusted) are never cleared into any repo by its visibility (see Definitions).",
    ...
  ]
}
```

获取关于您的自定义 `allow`、`soft_deny` 和 `hard_deny` 规则的 AI 反馈：

```bash theme={null}
claude auto-mode critique
```

在保存设置后运行 `claude auto-mode config`，以确认有效规则符合您的预期，并且 `"$defaults"` 已在原处展开。如果您编写了自定义规则，`claude auto-mode critique` 会对其进行审查，并标记含糊、冗余或可能导致误报的条目。

如果您需要删除或重写内置规则而不是在其旁边添加，请将 `claude auto-mode defaults` 的输出保存到文件中，编辑列表，然后将结果粘贴到您的设置文件中以替换 `"$defaults"`。

要放弃您的自定义设置并返回内置默认值，请运行重置子命令。它需要 Claude Code v2.1.212 或更高版本，并会从您的用户设置文件中删除 `autoMode` 部分：

```bash theme={null}
claude auto-mode reset
```

该命令会总结将要移除的内容，并在写入前询问 `Reset auto mode configuration to defaults?`；传入 `--yes` 以跳过确认。重置仅更改 `~/.claude/settings.json`：来自 [托管设置](/docs/en/server-managed-settings) 或 `--settings` 标志的 `autoMode` 规则仍然适用。

## 查看拒绝项

当自动模式拒绝工具调用时，Claude Code 会在 `/permissions` 的 **最近拒绝** 选项卡下记录该拒绝。按 `r` 标记被拒绝的操作以进行重试：当你退出对话框时，Claude Code 会发送一条消息告诉模型它可以重试该工具调用并恢复对话。

### 使用允许规则、环境条目或重试来修复拒绝

Claude Code会在拒绝出现的任何地方显示被阻止的工具调用，包括记录、拒绝通知和**最近拒绝**选项卡。根据该调用试图访问的目标或执行的操作来选择修复方法：

* Claude在整个任务期间需要访问的目标，例如包注册表、内部域或代码仓库托管平台：将其添加到`autoMode.environment`中。
* 你希望从现在起无需审查即可运行的命令：添加一条`allow`规则。
* 你确实有意执行的一次性操作：在下一条消息中说明该意图，并让 Claude 重试。

在大多数会话中，随调用显示的原因是固定文本 `Blocked by classifier`，在 Claude Code v2.1.208 及更高版本中：分类器在内部严重性量表上对每个操作进行评分，而不是撰写解释。{/* min-version: 2.1.193 */}在 v2.1.193 及更高版本中，一些会话运行一种改为撰写简短解释的分类器模型；当出现此类解释时，请将其视为关于分类器遗漏了哪个目标或意图的提示。Claude Code 会选择分类器模型，因此您看到哪种原因并不由您配置。

### 修复重复拒绝

针对同一目标的重复拒绝通常意味着分类器缺少上下文。将该目标添加到 `autoMode.environment`，然后运行 `claude auto-mode config` 以确认其已生效。

若要以编程方式响应拒绝，请使用 [`PermissionDenied`钩子](/docs/en/hooks#permissiondenied)。

## 另请参阅

* [权限模式](/docs/en/permission-modes#eliminate-prompts-with-auto-mode): 什么是自动模式, 它默认拦截什么, 以及如何启用它
* [托管设置](/docs/en/server-managed-settings): 在整个组织内部署 `autoMode` 配置
* [权限](/docs/en/permissions): 在分类器运行之前应用的允许, 询问和拒绝规则
* [设置](/docs/en/settings): 完整的设置参考, 包括 `autoMode` 键

---
title: 使用 Amazon Bedrock 的 ChatGPT Work 和 Codex
source_id: codex/amazon-bedrock
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/amazon-bedrock
owner: OpenAI
content_sha256: fbfa9ceaebbc7143c43ca51488c5110e48694b07c8791e71432de97f48ce8316
translation_of: codex/amazon-bedrock
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/amazon-bedrock)

Content owner: OpenAI

# 使用 Amazon Bedrock 的 ChatGPT Work 和 Codex

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。可以通过在页面 URL 后附加 `.md` 来获取文档页面的 Markdown 版本。

配置本地 ChatGPT Work 和 Codex 界面，以使用通过 Amazon Bedrock 提供的 OpenAI
模型。在此设置中，本地客户端使用 AWS 管理的身份验证和访问控制向 Bedrock
发送模型请求。

## 工作原理

当您配置本地 ChatGPT Work 或 Codex 界面将 Amazon Bedrock 作为
模型提供商时，OpenAI 托管的 Responses API 将不在请求路径中。
本地客户端将模型请求发送到 Amazon Bedrock，并且 Bedrock 为受支持的 OpenAI
模型提供了兼容 OpenAI 的 Responses API 实现。

身份验证是 AWS 原生的。用户使用 Bedrock API 密钥或 AWS
  IAM 凭证进行身份验证。他们不使用 ChatGPT 登录或 `OPENAI_API_KEY` 来用于此
  提供商。

## 开始之前

确保您具备：

- 在 Amazon Bedrock 中访问受支持的 OpenAI 模型的权限。
- 选定模型可用的 AWS 区域。
- 为 AWS
  账户配置的 Amazon Bedrock Mantle 路径的身份验证。

## 配置提供商

将 Amazon Bedrock Mantle 路径的 `amazon-bedrock` 模型提供商添加到
`~/.codex/config.toml` 中。ChatGPT 桌面应用程序、Codex CLI、IDE 扩展和
SDK 读取相同的本地配置层。提供模型是可选的。
在需要时显式选择受支持的模型。

```toml
model_provider = "amazon-bedrock"
```

本指南涵盖了受支持的商业 AWS 区域中的 Amazon Bedrock Mantle
  路径。本地 ChatGPT Work 和 Codex 界面不支持 AWS GovCloud 区域中的 Bedrock Mantle
  端点。

## 身份验证选项

本地 ChatGPT Work 和 Codex 界面支持两条 Bedrock 身份验证路径。
它们按以下顺序进行检查：

1. Bedrock API 密钥。
2. AWS SDK 凭证链。

### 选项 1：Bedrock API 密钥

在本地客户端读取的环境中设置 Bedrock API 密钥。使用 API 密钥身份验证时您必须
指定一个区域。

```shell
export AWS_BEARER_TOKEN_BEDROCK=<your-bedrock-api-key>
export AWS_REGION=us-east-2
```

### 选项 2：AWS SDK 凭证

当您的组织通过 AWS SDK 凭证链管理 Bedrock 访问权限时，请使用此路径。
本地客户端可以使用这些标准 AWS SDK 凭证
来源：

1. 共享的 AWS `config` 和 `credentials` 文件。

```shell
   aws configure
```

2. 环境变量。

```shell
   export AWS_ACCESS_KEY_ID=<your-access-key-id>
   export AWS_SECRET_ACCESS_KEY=<your-secret-access-key>
   export AWS_SESSION_TOKEN=<your-session-token>
```

3. AWS 管理控制台凭证。

```shell
   aws login
```

4. AWS SSO 或命名配置文件。

```shell
   aws sso login --profile codex-bedrock
   export AWS_PROFILE=codex-bedrock
```

5. 使用 `credential_process` 配置的联合身份。对于企业 SSO 或
   OIDC 联合，请在本地客户端外部配置 AWS 配置文件，并让
   AWS SDK 解析凭证。将浏览器登录、令牌交换、缓存
   和刷新放入您的 AWS 配置文件的 `credential_process` 助手中。

## 桌面应用程序和 IDE 扩展

桌面应用程序和 IDE 扩展可能不会从
shell 继承环境变量。请将所需的值放入 `~/.codex/.env` 中，然后重新启动应用程序或
扩展。

```shell
export AWS_BEARER_TOKEN_BEDROCK=<your-bedrock-api-key>
export AWS_REGION=us-east-2
```

## 验证设置

- 在 Codex CLI 中，打开 `/status` 并确认 Codex 正在使用
  `amazon-bedrock` 模型提供商。
- 在 ChatGPT 桌面应用程序中，选择 Work 或 Codex，并在
  重新启动应用程序后启动一个新任务。
- 在 IDE 扩展中，在重启扩展后启动一个新会话。
- 确认选定的模型在配置的 AWS 区域中可用，并且
  AWS 身份具有访问它的权限。

## 受支持的模型

使用精确的模型 ID：

```text
openai.gpt-5.6-sol
openai.gpt-5.6-terra
openai.gpt-5.6-luna
openai.gpt-5.5
openai.gpt-5.4
```

模型可用性因 AWS 区域而异。在选择模型之前，请参见 [按 AWS
区域的模型
支持](https://docs.aws.amazon.com/bedrock/latest/userguide/models-region-compatibility.html)。

## 功能可用性

此配置支持本地 ChatGPT Work 和 Codex 工作流。托管的
Web 版 ChatGPT Work、Codex 云，以及依赖于 OpenAI 托管
云服务、托管工具或云管理的发现功能目前不可
用。

快速模式在 Amazon Bedrock 中不可用。快速模式使用优先
  处理，而 Amazon Bedrock 的初始产品仅支持按需
  推理。

<ToggleSection title="详细功能可用性">
  <CodexPlanFeatureMatrix
    client:load
    data={{
      plans: [
        {
          id: "bedrock",
          shortLabel: "Amazon Bedrock",
          label: "Amazon Bedrock",
        },
      ],
      sections: [
        {
          title: "访问权限和界面",
          features: [
            {
              name: "Web 版 ChatGPT Work",
              href: "/codex/get-started-with-work",
              availability: {
                bedrock: "unavailable",
              },
            },
            {
              name: "Codex 云",
              href: "/codex/cloud",
              availability: {
                bedrock: "unavailable",
              },
            },
            {
              name: "ChatGPT 桌面应用中的 ChatGPT Work 或 Codex",
              shortName: "ChatGPT 桌面应用",
              href: "/codex/app",
              availability: {
                bedrock: "available",
              },
            },
            {
              name: "Codex CLI",
              href: "/codex/cli",
              availability: {
                bedrock: "available",
              },
            },
            {
              name: "IDE 扩展",
              href: "/codex/ide",
              availability: {
                bedrock: "available",
              },
            },
            {
              name: "Codex SDK、`codex exec` 和可脚本化工作流",
              shortName: "Codex SDK 和脚本",
              href: "/codex/codex-sdk",
              availability: {
                bedrock: "available",
              },
            },
          ],
        },
        {
          title: "模型和多模态",
          features: [
            {
              name: "使用支持的 OpenAI 模型进行 Bedrock 支持的推理",
              shortName: "Bedrock 支持的推理",
              href: "/codex/amazon-bedrock",
              availability: {
                bedrock: "available",
              },
            },
            {
              name: "快速模式",
              href: "/codex/agent-configuration/speed",
              availability: {
                bedrock: "unavailable",
              },
            },
            {
              name: "图像生成和编辑",
              href: "/codex/image-generation?surface=app",
              availability: {
                bedrock: "unavailable",
              },
            },
            {
              name: "语音听写",
              href: "/codex/prompting#use-voice-dictation",
              availability: {
                bedrock: "unavailable",
              },
            },
            {
              name: "网络搜索",
              href: "/codex/web-search?surface=app",
              availability: {
                bedrock: "unavailable",
              },
            },
          ],
        },
        {
          title: "本地功能",
          features: [
            {
              name: "使用 `/review` 进行本地代码审查",
              shortName: "本地代码审查",
              href: "/codex/prompting#do-a-local-code-review",
              availability: {
                bedrock: "available",
              },
            },
            {
              name: "批准请求的自动审查",
              href: "/codex/sandboxing/auto-review",
              availability: {
                bedrock: "available",
              },
            },
            {
              name: "沙盒与权限控制",
              href: "/codex/permissions",
              availability: {
                bedrock: "可用",
              },
            },
            {
              name: "项目与独立计划任务",
              shortName: "计划任务",
              href: "/codex/automations",
              availability: {
                bedrock: "可用",
              },
            },
            {
              name: "计划任务",
              href: "/codex/automations",
              availability: {
                bedrock: "可用",
              },
            },
            {
              name: "工作树与内置 Git 工具",
              shortName: "内置 Git 工具",
              href: "/codex/environments/git-worktrees",
              availability: {
                bedrock: "可用",
              },
            },
            {
              name: "本地环境与可重复操作",
              shortName: "可重复操作",
              href: "/codex/environments/local-environment",
              availability: {
                bedrock: "可用",
              },
            },
            {
              name: "应用截图",
              href: "/codex/appshots",
              availability: {
                bedrock: "可用",
              },
            },
          ],
        },
        {
          title: "浏览器与远程控制",
          features: [
            {
              name: "内置浏览器预览与评论",
              shortName: "内置浏览器",
              href: "/codex/browser?surface=app",
              availability: {
                bedrock: "可用",
              },
            },
            {
              name: "浏览器中的计算机使用",
              href: "/codex/browser?surface=app#app-computer-use-in-the-browser",
              availability: {
                bedrock: "受限",
              },
            },
            {
              name: "在 Chrome 中使用 ChatGPT",
              shortName: "Chrome 浏览器控制",
              href: "/codex/chrome-extension",
              availability: {
                bedrock: "受限",
              },
            },
            {
              name: "计算机使用",
              href: "/codex/computer-use",
              availability: {
                bedrock: "受限",
              },
            },
            {
              name: "SSH 远程连接",
              shortName: "SSH 远程",
              href: "/codex/remote-connections#connect-to-an-ssh-host",
              availability: {
                bedrock: "可用",
              },
            },
            {
              name: "移动端远程控制",
              href: "/codex/remote-connections",
              availability: {
                bedrock: "不可用",
              },
            },
          ],
        },
        {
          title: "自定义与扩展",
          features: [
            {
              name: "带有 `AGENTS.md` 的自定义指令",
              shortName: "自定义指令",
              href: "/codex/agent-configuration/agents-md",
              availability: {
                bedrock: "可用",
              },
            },
            {
              name: "技能",
              href: "/codex/build-skills",
              availability: {
                bedrock: "可用",
              },
            },
            {
              name: "插件",
              href: "/codex/plugins",
              availability: {
                bedrock: "受限",
              },
              limitedFootnote: "插件",
            },
            {
              name: "插件共享",
              href: "https://developers.openai.com/plugins/build/plugins#share-a-local-plugin-with-your-workspace",
              availability: {
                bedrock: "不可用",
              },
            },
            {
              name: "连接器",
              href: "/codex/plugins",
              availability: {
                bedrock: "不可用",
              },
            },
            {
              name: "MCP",
              href: "/codex/extend/mcp",
              availability: {
                bedrock: "可用",
              },
            },
            {
              name: "子代理与自定义代理",
              shortName: "子代理",
              href: "/codex/agent-configuration/subagents",
              availability: {
                bedrock: "可用",
              },
            },
            {
              name: "记忆",
              href: "/codex/customization/memories",
              availability: {
                bedrock: "受限",
              },
            },
            {
              name: "Chronicle",
              href: "/codex/customization/chronicle",
              availability: {
                bedrock: "不可用",
              },
            },
          ],
        },
        {
          title: "云与集成",
          features: [
            {
              name: "Codex 云端聊天",
              shortName: "云端聊天",
              href: "/codex/cloud",
              availability: {
                bedrock: "不可用",
              },
            },
            {
              name: "站点",
              href: "/codex/sites",
              availability: {
                bedrock: "不可用",
              },
            },
            {
              name: "使用 `@codex` 委派 GitHub 议题与 PR",
              shortName: "GitHub 委派",
              href: "/codex/third-party/github#give-codex-other-tasks",
              availability: {
                bedrock: "不可用",
              },
            },
            {
              name: "GitHub 代码审查与自动 PR 审查",
              shortName: "GitHub PR 审查",
              href: "/codex/third-party/github",
              availability: {
                bedrock: "不可用",
              },
            },
            {
              name: "Slack 云端集成",
              shortName: "Slack 集成",
              href: "/codex/third-party/slack",
              availability: {
                bedrock: "不可用",
              },
            },
            {
              name: "Linear 云端集成",
              shortName: "Linear 集成",
              href: "/codex/third-party/linear",
              availability: {
                bedrock: "不可用",
              },
            },
          ],
        },
        {
          title: "管理、安全与分析",
          features: [
            {
              name: "SAML SSO、MFA 与工作区用户管理",
              shortName: "工作区管理",
              href: "/codex/enterprise/admin-setup",
              availability: {
                bedrock: "不可用",
              },
            },
            {
              name: "`requirements.toml` 托管配置",
              shortName: "`requirements.toml` 配置",
              href: "/codex/enterprise/managed-configuration",
              availability: {
                bedrock: "可用",
              },
            },
            {
              name: "云端托管配置策略",
              shortName: "云端托管策略",
              href: "/codex/enterprise/managed-configuration#cloud-managed-requirements",
              availability: {
                bedrock: "不可用",
              },
            },
            {
              name: "ChatGPT 工作区 RBAC 与自定义角色",
              shortName: "RBAC 与角色",
              href: "/codex/enterprise/roles-and-workspace-permissions",
              availability: {
                bedrock: "不可用",
              },
            },
            {
              name: "SCIM、EKM 与域名验证",
              shortName: "SCIM、EKM 与域名",
              href: "/codex/enterprise/admin-setup#enterprise-grade-security-and-privacy",
              availability: {
                bedrock: "不可用",
              },
            },
            {
              name: "企业级保留和数据驻留控制",
              shortName: "保留和驻留",
              href: "/codex/enterprise/admin-setup#enterprise-grade-security-and-privacy",
              availability: {
                bedrock: "不可用",
              },
            },
            {
              name: "默认不使用 API 或业务数据进行训练",
              shortName: "默认不训练",
              href: "https://openai.com/business-data/",
              availability: {
                bedrock: "可用",
              },
            },
            {
              name: "分析仪表板",
              href: "/codex/enterprise/workspace-analytics",
              availability: {
                bedrock: "不可用",
              },
            },
            {
              name: "分析 API",
              href: "/codex/enterprise/analytics-api",
              availability: {
                bedrock: "不可用",
              },
            },
            {
              name: "合规 API 和审计日志",
              shortName: "合规和审计日志",
              href: "/codex/enterprise/compliance-api",
              availability: {
                bedrock: "不可用",
              },
            },
            {
              name: "已连接 GitHub 仓库的 Codex 安全",
              shortName: "Codex 安全",
              href: "/codex/security",
              availability: {
                bedrock: "不可用",
              },
            },
          ],
        },
      ],
    }}
  />

  <div
    id="codex-plan-region-limits"
    className="not-prose mt-3 text-sm text-secondary"
  >
    <sup>*</sup> 该功能目前仅限特定区域使用。查看
    各个功能文档以了解有关地理限制的更多信息。
  

  <div
    id="codex-plan-plugin-limits"
    className="not-prose mt-1 text-sm text-secondary"
  >
    <sup>†</sup> 本地插件包在其功能不
    需要 ChatGPT 身份验证时受支持。OpenAI 精选的插件发现以及
    依赖于连接器或云托管共享的功能不
    可用。
  

</ToggleSection>

## 故障排除

如果设置失败，请检查以下几点：

- 模型 ID 与受支持的模型完全匹配。
- 您指定了模型可用的 AWS 区域。
- Bedrock API 密钥或 AWS 凭证有效且未过期。
- AWS 身份拥有访问所选 Bedrock 模型的权限。
- `AWS_BEARER_TOKEN_BEDROCK` 未设置为过期或意外的密钥。
- 对于桌面应用或 IDE 扩展的使用，所需的环境变量
  存在于 `~/.codex/.env` 中。

## 支持边界

OpenAI 支持团队可以协助处理 ChatGPT Work 和 Codex 客户端设置、
配置、本地 CLI 行为、桌面应用行为、IDE 扩展行为，
以及本地产品体验。

有关 AWS 凭证、IAM 权限、Bedrock 模型访问、配额、计费、
区域可用性、Bedrock 请求失败、AWS 服务日志或 Bedrock
服务行为，请联系客户的 AWS 管理员或 AWS 支持。

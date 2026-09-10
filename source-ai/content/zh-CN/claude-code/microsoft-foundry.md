---
title: Microsoft Foundry 上的 Claude Code
source_id: claude-code/microsoft-foundry
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/microsoft-foundry
owner: Anthropic
content_sha256: 4624c8492fbd1d0cc88300ba8f231685c38e4fd655047c10d561bc60255791b5
translation_of: claude-code/microsoft-foundry
translation_model: gpt-5.6
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/microsoft-foundry)

Content owner: Anthropic

> ## 文档索引
> 完整的文档索引位于：https://code.claude.com/docs/llms.txt
> 在进一步探索之前，可使用此文件发现所有可用页面。

# Microsoft Foundry 上的 Claude Code

> 了解如何通过 Microsoft Foundry 配置 Claude Code，包括设置、配置和故障排除。

export const ContactSalesCard = ({surface}) => {
  const utm = content => `utm_source=claude_code&utm_medium=docs&utm_content=${surface}_${content}`;
  const iconArrowRight = (size = 13) => <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <line x1="5" y1="12" x2="19" y2="12" />
      <polyline points="12 5 19 12 12 19" />
    </svg>;
  const STYLES = `
.cc-cs {
  --cs-slate: #141413;
  --cs-clay: #d97757;
  --cs-clay-deep: #c6613f;
  --cs-gray-000: #ffffff;
  --cs-gray-700: #3d3d3a;
  --cs-border-default: rgba(31, 30, 29, 0.15);
  font-family: inherit;
}
.dark .cc-cs {
  --cs-slate: #f0eee6;
  --cs-gray-000: #262624;
  --cs-gray-700: #bfbdb4;
  --cs-border-default: rgba(240, 238, 230, 0.14);
}
.cc-cs-card {
  display: flex; align-items: center; justify-content: space-between;
  gap: 16px; padding: 14px 16px; margin: 0;
  background: var(--cs-gray-000); border: 0.5px solid var(--cs-border-default);
  border-radius: 8px; flex-wrap: wrap;
}
.cc-cs-text { font-size: 13px; color: var(--cs-gray-700); line-height: 1.5; flex: 1; min-width: 240px; }
.cc-cs-text strong { font-weight: 550; color: var(--cs-slate); }
.cc-cs-actions { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.cc-cs-btn-clay {
  display: inline-flex; align-items: center; gap: 8px;
  background: var(--cs-clay-deep); color: #fff; border: none;
  border-radius: 8px; padding: 8px 14px;
  font-size: 13px; font-weight: 500;
  transition: background-color 0.15s; white-space: nowrap;
}
.cc-cs-btn-clay:hover { background: var(--cs-clay); }
.cc-cs-btn-ghost {
  display: inline-flex; align-items: center; gap: 8px;
  background: transparent; color: var(--cs-gray-700);
  border: 0.5px solid var(--cs-border-default);
  border-radius: 8px; padding: 8px 14px;
  font-size: 13px; font-weight: 500;
}
.cc-cs-btn-ghost:hover { background: rgba(0, 0, 0, 0.04); }
.dark .cc-cs-btn-ghost:hover { background: rgba(255, 255, 255, 0.04); }
@media (max-width: 720px) {
  .cc-cs-actions { width: 100%; }
}
`;
  return <div className="cc-cs not-prose">
      <style>{STYLES}</style>
      <div className="cc-cs-card">
        <div className="cc-cs-text">
          <strong>要在整个组织中部署 Claude Code？</strong> 请联系销售团队，了解企业方案、SSO 和集中计费。
        </div>
        <div className="cc-cs-actions">
          <a href={`https://claude.com/pricing?${utm('view_plans')}#plans-business`} className="cc-cs-btn-ghost">
            查看方案
          </a>
          <a href={`https://claude.com/contact-sales?${utm('contact_sales')}`} className="cc-cs-btn-clay">
            联系销售团队 {iconArrowRight()}
          </a>
        </div>
      </div>
    </div>;
};

<ContactSalesCard surface="foundry" />

## 前提条件

在为 Claude Code 配置 Microsoft Foundry 之前，请确保你拥有：

* 有权访问 Microsoft Foundry 的 Azure 订阅
* 可创建 Microsoft Foundry 资源和部署的 RBAC 权限
* 已安装并配置 Azure CLI（可选，仅当你没有其他获取凭据的机制时才需要）

<Note>
  如果要将 Claude Code 部署给多个用户，请在推出前[固定模型版本](#4-pin-model-versions)。
</Note>

## 设置

### 1. 预配 Microsoft Foundry 资源

首先，在 Azure 中创建 Claude 资源：

1. 前往 [Microsoft Foundry 门户](https://ai.azure.com/)
2. 创建新资源，并记下资源名称
3. 为 Claude 模型创建部署，并记下为每个部署指定的名称；你将在第 4 步中把这些名称设置为模型变量：

   * Claude Opus
   * Claude Sonnet
   * Claude Haiku

   配置部署时，还需要选择其[托管选项](https://platform.claude.com/docs/en/build-with-claude/claude-in-microsoft-foundry#hosting-options)，该选项决定推理是在 Azure 上运行，还是在 Anthropic 基础设施上运行。

### 2. 配置 Azure 凭据

Claude Code 支持三种 Microsoft Foundry 身份验证方法。请选择最符合你安全要求的方法。

**选项 A：API 密钥身份验证**

1. 在 Microsoft Foundry 门户中前往你的资源
2. 打开 **Endpoints and keys** 部分
3. 复制 **API Key**
4. 设置环境变量，将 `your-azure-api-key` 替换为刚复制的密钥：

```bash theme={null}
export ANTHROPIC_FOUNDRY_API_KEY=your-azure-api-key
```

**选项 B：Microsoft Entra ID 身份验证**

当 `ANTHROPIC_FOUNDRY_API_KEY` 和 `ANTHROPIC_FOUNDRY_AUTH_TOKEN` 均未设置时，Claude Code 会自动使用 Azure SDK 的[默认凭据链](https://learn.microsoft.com/en-us/azure/developer/javascript/sdk/authentication/credential-chains#defaultazurecredential-overview)。
它支持多种本地和远程工作负载身份验证方法。

在本地环境中，通常可以使用 Azure CLI：

```bash theme={null}
az login
```

**选项 C：Bearer 令牌身份验证**

{/* min-version: 2.1.203 */}Claude Code 会在每个请求中发送 `ANTHROPIC_FOUNDRY_AUTH_TOKEN` 的值，并将其用作 `Authorization: Bearer` 标头。当其他进程（例如宿主应用或登录脚本）已为你获取访问令牌时，请使用此选项。需要 Claude Code v2.1.203 或更高版本。

将该变量设置为 Microsoft Entra ID 为你的资源签发的 bearer 令牌：

```bash theme={null}
export ANTHROPIC_FOUNDRY_AUTH_TOKEN=your-entra-access-token
```

`ANTHROPIC_FOUNDRY_AUTH_TOKEN` 的优先级高于 `ANTHROPIC_FOUNDRY_API_KEY` 和默认凭据链。

<Note>
  使用 Microsoft Foundry 时，`/logout` 命令不可用，因为身份验证由 Azure 凭据处理。
</Note>

### 3. 配置 Claude Code

设置以下环境变量以启用 Microsoft Foundry：

```bash theme={null}
# Enable Microsoft Foundry integration

export CLAUDE_CODE_USE_FOUNDRY=1

# Azure resource name (replace {resource} with your resource name)

export ANTHROPIC_FOUNDRY_RESOURCE={resource}
# Or provide the full base URL:

# export ANTHROPIC_FOUNDRY_BASE_URL=https://{resource}.services.ai.azure.com/anthropic

```

### 4. 固定模型版本

<Warning>
  为每个部署固定具体的模型版本。如果不固定，`sonnet` 和 `opus` 等模型别名会解析为 Claude Code 内置的 Microsoft Foundry 默认版本；该版本可能落后于最新版本，也可能尚未在你的账户中可用。Microsoft Foundry 不会在启动时检查模型，因此默认版本不可用时，请求会失败。创建 Azure 部署时，请选择具体的模型版本，而不是“auto-update to latest”。
</Warning>

设置模型变量，使其与第 1 步中创建的部署名称匹配。

如果未设置 `ANTHROPIC_DEFAULT_OPUS_MODEL`，Microsoft Foundry 上的 `opus` 别名会解析为 Opus 4.6。请将其设置为更新的 Opus 模型 ID，例如 Opus 4.8：

```bash theme={null}
export ANTHROPIC_DEFAULT_OPUS_MODEL='claude-opus-4-8'
export ANTHROPIC_DEFAULT_SONNET_MODEL='claude-sonnet-5'
export ANTHROPIC_DEFAULT_HAIKU_MODEL='claude-haiku-4-5'
```

会话标题生成等后台任务使用小型/快速模型，通常是 Haiku 级模型。在 Microsoft Foundry 上，Claude Code 默认将其设置为主模型，因为并非每个账户都有 Haiku 部署。若要对后台任务使用 Haiku，请如上所示，将 `ANTHROPIC_DEFAULT_HAIKU_MODEL` 设置为你账户中可用的 Haiku 部署。

有关当前和旧版模型 ID，请参阅[模型概述](https://platform.claude.com/docs/en/about-claude/models/overview)。有关完整的环境变量列表，请参阅[模型配置](/docs/en/model-config#pin-models-for-third-party-deployments)。

[提示缓存](/docs/en/prompt-caching)会自动启用。若要请求 1 小时的缓存 TTL，而不是默认的 5 分钟，请设置以下变量；采用 1 小时 TTL 的缓存写入按更高费率计费：

```bash theme={null}
export ENABLE_PROMPT_CACHING_1H=1
```

### 5. 运行 Claude Code

设置环境变量后，从项目目录启动 Claude Code：

```bash theme={null}
claude
```

Claude Code 会从环境中读取 `CLAUDE_CODE_USE_FOUNDRY` 和其他 Microsoft Foundry 变量，并在收到第一个提示时连接到你的 Azure 资源。与 Amazon Bedrock 和 Google Cloud 的 Agent Platform 不同，Microsoft Foundry 没有交互式设置向导，因此第 3 步和第 4 步中的环境变量是唯一配置路径。

若要验证设置，请在 Claude Code 中运行 `/status`。API 提供商行会显示 `Microsoft Foundry`，以及你配置的资源名称或基础 URL。

## Azure RBAC 配置

`Azure AI User` 和 `Cognitive Services User` 默认角色包含调用 Claude 模型所需的全部权限。

若要使用更严格的权限，请创建具有以下内容的自定义角色：

```json theme={null}
{
  "permissions": [
    {
      "dataActions": [
        "Microsoft.CognitiveServices/accounts/providers/*"
      ]
    }
  ]
}
```

有关详细信息，请参阅 [Microsoft Foundry RBAC 文档](https://learn.microsoft.com/en-us/azure/ai-foundry/concepts/rbac-azure-ai-foundry)。

## 故障排除

如果收到错误“Failed to get token from azureADTokenProvider: ChainedTokenCredential authentication failed”：

* 在环境中配置 Entra ID，或设置 `ANTHROPIC_FOUNDRY_API_KEY`。

如果第一个提示出现重复的连接错误，导致请求失败：

* 检查 `ANTHROPIC_FOUNDRY_RESOURCE` 是否设置为实际资源名称，而不是占位符。Claude Code 会根据该值构建端点 URL，因此名称不正确会指向不存在的主机。

## 其他资源

* [Microsoft Foundry 文档](https://learn.microsoft.com/en-us/azure/ai-foundry/what-is-azure-ai-foundry)
* [Microsoft Foundry 模型](https://ai.azure.com/explore/models)
* [Microsoft Foundry 定价](https://azure.microsoft.com/en-us/pricing/details/ai-foundry/)

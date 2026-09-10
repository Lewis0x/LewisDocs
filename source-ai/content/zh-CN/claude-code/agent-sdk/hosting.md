---
title: 托管 Agent SDK
source_id: claude-code/agent-sdk/hosting
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/agent-sdk/hosting
owner: Anthropic
content_sha256: 46492f937f14492e2eb8c164dd430c6c6bb5affaaea18f19988a1657578224cc
translation_of: claude-code/agent-sdk/hosting
translation_model: k3
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/agent-sdk/hosting)

Content owner: Anthropic

> ## 文档索引
> 获取完整的文档索引:https://code.claude.com/docs/llms.txt
> 在进一步探索之前,使用此文件来发现所有可用页面。

# 托管 Agent SDK

> 在生产环境中部署 Agent SDK:面向 Docker、Kubernetes 和沙箱提供商的子进程架构、会话持久化、扩展、可观测性,以及多租户隔离。

Agent SDK 会生成并监管一个拥有 shell、工作目录以及磁盘上会话文件的 `claude` CLI 子进程。托管它并不像托管一个无状态的 API 封装。每个运行中的 agent 都是一个与本地状态绑定的长生命周期进程,这决定了你如何分配资源、持久化会话以及跨租户扩展。

本页介绍在你自己的基础设施上进行自托管:了解[子进程模型](#the-subprocess-model)、[选择会话模式](#choose-a-session-pattern)、[配置容器](#provision-the-container),以及[处理生产环境关注点](#handle-production-concerns),如持久化、可观测性、身份验证和多租户隔离。有关可部署的 Dockerfile 和 Kubernetes 清单,请参阅[托管手册](https://github.com/anthropics/claude-cookbooks/tree/main/claude_agent_sdk/hosting)。

如果你不需要基础设施控制、自定义隔离或自己的数据平面,可以考虑改用 [Managed Agents](https://platform.claude.com/docs/en/managed-agents/overview):一个托管的 REST API,其中 Anthropic 运行 agent 和沙箱,因此你的应用程序只需发送事件并流式传回结果,无需运营任何托管基础设施。

<Info>
  如需了解基本沙箱之外的安全加固,包括网络控制、凭据管理和隔离选项,请参阅[安全部署](/docs/en/agent-sdk/secure-deployment)。
</Info>

## 子进程模型

本页上的每个托管决策都源于 SDK 运行 agent 的方式。当你的代码调用 `query()` 时,SDK 会生成一个独立的 `claude` CLI 进程,并通过 stdio 与其通信。该子进程拥有 shell、工作目录以及本地磁盘上的 JSONL 会话记录。

<img src="https://mintcdn.com/claude-code/ikqp3_70mqIahteV/images/agent-sdk/hosting-subprocess.svg?fit=max&auto=format&n=ikqp3_70mqIahteV&q=85&s=9dac857ca9d3b1410c3734900c386004" alt="Request flow: client to your app, which spawns a claude CLI subprocess over stdio inside the container; the subprocess writes to local disk and calls api.anthropic.com over HTTPS" width="920" height="220" data-path="images/agent-sdk/hosting-subprocess.svg" />

一个 agent 会话对应一个子进程。运行 N 个并发会话意味着 N 个子进程,每个都有自己的进程树和记录文件。默认情况下,它们都会继承你应用程序的工作目录,因此当会话需要独立的文件系统时,请在每次 `query()` 调用时传递 `cwd`:

<CodeGroup>
  ```typescript TypeScript theme={null}
  query({ prompt, options: { cwd: "/work/session-a" } })
  ```

  ```python Python theme={null}
  query(prompt=prompt, options=ClaudeAgentOptions(cwd="/work/session-a"))
  ```
</CodeGroup>

### 存储在本地磁盘上的状态

默认情况下，有三种智能体状态存储在容器的文件系统中。它们都无法在容器重启、缩容或迁移到其他节点后存活。

| 状态                       | 默认位置                                                                                 |
| --------------------------- | ------------------------------------------------------------------------------------------------ |
| 会话转录记录         | `~/.claude/projects/`，或设置了 `CLAUDE_CONFIG_DIR` 时其下的 `projects/` 目录             |
| `CLAUDE.md` 记忆文件    | 用户层级为 `~/.claude/CLAUDE.md`，项目层级为会话的工作目录 |
| 工作目录产物 | 会话的工作目录                                                                  |

要跨主机持久化转录记录，请配置一个 [`SessionStore` 适配器](/docs/en/agent-sdk/session-storage)。记忆文件和其他工作目录产物需要各自的存储策略，例如挂载卷或对象存储同步。

关于会话、恢复和分叉在 API 层面的工作方式，请参阅 [会话](/docs/en/agent-sdk/sessions)。

## 选择一种会话模式

这四种模式涵盖了会话生命周期：容器相对于它所服务的会话存活多长时间。关于容器在哪里运行，[托管手册](https://github.com/anthropics/claude-cookbooks/blob/main/claude_agent_sdk/07_Hosting_the_agent.ipynb) 提供了适用于本地 Docker、Modal 和 Kubernetes 的 [可部署代码](https://github.com/anthropics/claude-cookbooks/tree/main/claude_agent_sdk/hosting)。在此处选择一种会话模式，并从手册中选择部署目标。

### 临时会话

为每个用户任务创建一个容器，并在任务完成时将其销毁。最适合一次性任务。在任务完成期间用户仍可与 AI 交互，但一旦完成，容器就会被销毁。

示例工作负载包括缺陷调查与修复、发票和收据提取、文档翻译以及媒体转换。

容器运行一个一次性入口点，调用 SDK 后退出。下面的示例展示了一个最小的 TypeScript 版本。将其保存为 `entrypoint.mts`，或在 `package.json` 中设置 `"type": "module"`，以便可以使用顶层 `await`。

```typescript theme={null}
import { query } from "@anthropic-ai/claude-agent-sdk";

const prompt = process.env.TASK_PROMPT!;
for await (const message of query({ prompt, options: { maxTurns: 20 } })) {
  console.log(message);
}
```

### 长时间运行的会话

运行持久的容器实例，通常每个容器托管多个 SDK 进程，以服务持续进行的工作。最适合采取自主行动、提供内容或处理高容量消息流的智能体。

示例工作负载包括：对收到的邮件进行分类和回复的电子邮件智能体、通过容器端口托管每用户可编辑站点的站点构建器，以及处理来自 Slack 等平台的持续流量的聊天机器人。

容器暴露一个 HTTP 或 WebSocket 端点，并将每个活动会话映射到一个长期存活的查询及其背后的子进程。在 TypeScript 中，使用 [`streamInput()`](/docs/en/agent-sdk/typescript#query-object) 向活动会话添加轮次，并使用 [`startup()`](/docs/en/agent-sdk/typescript#startup) 在传入流量到来之前预热子进程。在 Python 中，使用 [`ClaudeSDKClient`](/docs/en/agent-sdk/python#claudesdkclient) 跨轮次保持会话打开。容器规格的设定应使其能够在内存中容纳最大数量的并发会话。

### 混合会话

临时容器在启动时从 [`SessionStore`](/docs/en/agent-sdk/session-storage) 恢复会话状态,并将更新持久化回去。最适合跨越多次交互但在交互之间处于空闲状态的会话。容器在空闲期间关闭,并在用户返回时重新启动。

示例工作负载包括:一个进行间歇性签到的个人项目管理器、在数小时内暂停和恢复的深度研究,以及跨交互加载工单历史的客户支持代理。

根据你预计用户返回的频率来调整提供商的空闲超时。在未配置 `SessionStore` 的情况下关闭容器会连同其中的会话记录一起丢失,因此对于此模式,存储是必需的,而非可选。

该模式的关键在于通过附加共享存储按 ID 恢复会话:

<CodeGroup>
  ```typescript TypeScript theme={null}
  import { query, type SessionStore } from "@anthropic-ai/claude-agent-sdk";

  declare const userInput: string;
  declare const sessionId: string;          // looked up from your database by user
  declare const sessionStore: SessionStore; // S3, Redis, Postgres, or your own adapter

  for await (const message of query({
    prompt: userInput,
    options: { resume: sessionId, sessionStore },
  })) {
    // ...
  }
  ```

  ```python Python theme={null}
  from claude_agent_sdk import query, ClaudeAgentOptions, SessionStore
  import asyncio

  user_input: str = ...
  session_id: str = ...              # looked up from your database by user
  session_store: SessionStore = ...  # S3, Redis, Postgres, or your own adapter


  async def main():
      async for message in query(
          prompt=user_input,
          options=ClaudeAgentOptions(
              resume=session_id,
              session_store=session_store,
          ),
      ):
          ...


  asyncio.run(main())
  ```
</CodeGroup>

请参阅 [会话存储](/docs/en/agent-sdk/session-storage)，了解完整的 `SessionStore` 接口和参考适配器。

### 多智能体容器

在一个容器中运行多个 SDK 子进程。最适合需要紧密协作的智能体，例如多个智能体在共享环境中相互交互的多智能体仿真。

为每个智能体分配各自的工作目录，以免它们覆盖彼此的文件，并隔离设置加载，使每个智能体的 `CLAUDE.md` 文件不会跨智能体泄漏。有关具体选项，请参阅 [多租户隔离](#multi-tenant-isolation)。

## 配置容器

### 基于容器的沙箱

在沙箱容器中运行 SDK，以实现进程隔离、资源限制、网络控制和临时文件系统。有几家提供商专注于符合 Agent SDK 模型的沙箱容器环境。

选择提供商时需要回答的问题：

* **谁来运行沙箱**：沙箱即服务提供商会为你运营基础设施，而自托管选项则提供在你自己的环境中运行的软件。
* **冷启动延迟**：从"创建沙箱"到"准备好接受第一个请求"需要多长时间。临时模式需要亚秒级启动。长时间运行的模式可以容忍更多。
* **持久化存储**：提供商是提供持久卷还是只提供临时磁盘。混合模式需要在某处具备持久存储，无论是在沙箱内还是沙箱旁。
* **定价模式**：按秒、按请求或按小时统一计费。按秒计费适合突发性的临时工作负载。按小时计费适合长时间运行的会话。
* **网络**：支持自定义出口规则、出站代理，以及面向受监管环境的私有 VPC 对等连接。

值得评估的提供商：

* [Modal Sandbox](https://modal.com/docs/guide/sandbox)，附带一个[演示实现](https://modal.com/docs/examples/claude-slack-gif-creator)
* [Cloudflare Sandboxes](https://github.com/cloudflare/sandbox-sdk)
* [Daytona](https://www.daytona.io/)
* [E2B](https://e2b.dev/)
* [Fly Machines](https://fly.io/docs/machines/)
* [Vercel Sandbox](https://vercel.com/docs/functions/sandbox)

有关 Docker、gVisor 和 Firecracker 等自托管选项以及详细的隔离配置，请参阅[隔离技术](/docs/en/agent-sdk/secure-deployment#isolation-technologies)。

### 运行时依赖

容器只需要你的 SDK 的语言运行时：

* Python SDK 需要 Python 3.10+，TypeScript SDK 需要 Node.js 18+
* 两个 SDK 包都捆绑了适用于宿主平台的原生 Claude Code 二进制文件，因此生成的 CLI 无需单独安装 Claude Code 或 Node.js

捆绑的二进制文件与 SDK 包版本固定绑定，因此更新 SDK 就是更新 CLI 的方式。SDK 遵循语义化版本：持续接受补丁版本，在接受次版本之前请查看 [TypeScript](https://github.com/anthropics/claude-agent-sdk-typescript/blob/main/CHANGELOG.md) 或 [Python](https://github.com/anthropics/claude-agent-sdk-python/blob/main/CHANGELOG.md) 的更新日志。

### 资源

对于新启动的实例，每个智能体 1 GiB 内存、5 GiB 磁盘和 1 个 CPU 是一个合理的起点。内存使用量会随会话长度和工具活动而增长，因此请按照你实际需要的会话长度和并发度来确定规模，而不是按照空闲基线。有关如何计算每台主机的智能体数量，请参阅[扩展与并发](#scaling-and-concurrency)。

### 网络

SDK 需要到 `api.anthropic.com` 的出站 HTTPS 访问，或者在 Amazon Bedrock 或 Google Cloud 的 Agent Platform 上运行时访问你的提供商的区域端点。如果你的智能体使用[MCP 服务器](/docs/en/agent-sdk/mcp)或外部工具，它们还需要对这些端点的出站访问。对于生产环境，请通过出口代理路由出站流量，该代理强制执行域名允许列表、注入凭据并记录请求。完整模式请参阅[安全部署](/docs/en/agent-sdk/secure-deployment)。

对于入站流量，在容器上公开一个 HTTP 或 WebSocket 端口。你的应用程序在该端口上处理客户端请求，并在内部调用 SDK；子进程本身不监听网络。

## 处理生产环境问题

在发布自托管智能体之前，请先完成这些决策。

### 会话与状态持久化

默认的本地磁盘在重启、缩容或迁移到其他节点时会丢失。对于任何用户期望恢复的会话，请使用 [`SessionStore` 适配器](/docs/en/agent-sdk/session-storage) 将会话记录镜像到持久化存储。参阅 [参考实现](/docs/en/agent-sdk/session-storage#reference-implementations) 了解 S3、Redis 和 Postgres 适配器以及用于自定义实现的合规性测试套件。

关于 `SessionStore` 的行为，需要了解三点：

* **仅限会话记录**：`SessionStore` 镜像的是会话记录，而不是 `CLAUDE.md` 记忆文件或其他工作目录产物。请挂载共享卷或单独同步这些内容。
* **镜像而非替代**：子进程首先写入本地磁盘，存储端接收每个批次的副本。本地写入始终是权威来源。
* **`mirror_error` 消息**：被存储端拒绝的批次总共最多发送三次，每次重试前有短暂的退避；超时的调用不会重试。如果批次仍然失败，SDK 会丢弃该批次，发出一条 `{ type: "system", subtype: "mirror_error" }` 消息，然后继续查询。如果存储持久性很重要，请对这些消息设置告警。

### 可观测性

Agent SDK 智能体是长时间运行的进程，会在多次 API 往返中产生工具调用。没有遥测数据，你就无法看到哪些工具运行了、耗时多久，或者会话在何处停滞。

SDK 会从环境中继承 OpenTelemetry 配置。在容器或编排器层面设置 OTEL 环境变量，使每个 `query()` 调用都能将 span、指标和日志事件导出到你的收集器。下面的示例为全部三种信号启用了 OTLP 导出。`CLAUDE_CODE_ENHANCED_TELEMETRY_BETA` 仅对追踪（traces）是必需的；如果只导出指标和日志，可以省略它。

```bash title=".env" theme={null}
CLAUDE_CODE_ENABLE_TELEMETRY=1
CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1
OTEL_TRACES_EXPORTER=otlp
OTEL_METRICS_EXPORTER=otlp
OTEL_LOGS_EXPORTER=otlp
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
OTEL_EXPORTER_OTLP_ENDPOINT=http://collector.example.com:4318
```

默认情况下，导出的数据中不包含提示文本和工具输入。有关选择性启用的标志，请参阅 [控制导出中的敏感数据](/docs/en/agent-sdk/observability#control-sensitive-data-in-exports)；有关完整的信号目录，请参阅 [可观测性](/docs/en/agent-sdk/observability)。

### 身份验证与密钥

托管时需要注意三个身份验证方面的问题：

* **Anthropic API**：子进程从其环境中读取 `ANTHROPIC_API_KEY`。请从密钥管理器提供它，或者设置 `ANTHROPIC_BASE_URL` 将模型调用路由通过一个代理，由代理在容器外部注入密钥。有关代理模式，请参阅 [凭据管理](/docs/en/agent-sdk/secure-deployment#credential-management)；有关支持的身份验证方法，请参阅 [SDK 概览](/docs/en/agent-sdk/overview#get-started)。
* **入站**：在智能体容器前方的网关上实施身份验证。智能体应接收经过预先身份验证的请求，而不应成为验证用户令牌的组件。
* **出站工具**：让工具凭据远离智能体环境。通过一个代理路由出站调用，在请求离开容器后由代理注入 API 密钥。智能体发起调用；代理添加凭据。

### 扩展与并发

每个会话在其自己的子进程中运行，因此主机上的并发度受限于其内存（RAM）能容纳多少个子进程。

使用以下公式为每台主机规划容量：

```text theme={null}
agents per host = (host RAM - overhead) / (per-session RAM ceiling)
```

通过在预期的工具负载下运行一个达到目标长度的代表性会话并记录峰值 RSS，来测量每个会话的上限。[资源](#resources) 中的 1 GiB 起始值是下限，而非上限。

水平扩展的路由取决于你的模式。对于长时间运行的会话（容器持有多个会话），请在负载均衡器后运行一组容器池，并通过对 `sessionId` 进行一致性哈希将每个会话固定到一个容器上。被固定的会话会持续命中同一个容器，从而命中同一个运行中的子进程，直到它被逐出或容器重启。

来自单个会话的大量并发 [子代理](/docs/en/agent-sdk/subagents) 扇出可能会触发 API 速率限制。请将工作拆分为更小的批次，而不是一次性发起大规模分发。

### 成本

Anthropic 的 token 成本通常比容器基础设施成本高出一个数量级甚至更多。一个最小配置的容器每小时大约花费 \$0.05，而单个长时间的智能体会话可能在 token 上花费数美元。有关每个会话的 token 记账，请参阅 [成本跟踪](/docs/en/agent-sdk/cost-tracking)。

### 多租户隔离

SDK 的默认行为是从文件系统读取设置和 `CLAUDE.md` 记忆文件。在服务多个租户的共享容器中，这些文件可能会将一个租户的上下文泄露到另一个租户的会话中。

要在共享容器内隔离租户：

* 在 TypeScript 中传递 `settingSources: []`，或在 Python 中传递 `setting_sources=[]`，这样就不会加载任何文件系统设置。
* 在 `env` 中设置 `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`。[自动记忆](/docs/en/memory#auto-memory) 位于 `~/.claude/projects/<project>/memory/` 时，无论 `settingSources` 如何都会加载到系统提示中。关于其他会无条件加载的输入，请参阅 [settingSources 不控制什么](/docs/en/agent-sdk/claude-code-features#what-settingsources-does-not-control)。
* 将 `CLAUDE_CONFIG_DIR` 指向每个租户各自的目录，使租户之间不共享 `~/.claude.json` 全局配置。
* 使用每个租户各自的工作目录。在每次 `query()` 调用时都显式传递 `cwd`。
* 在您的代理服务器上应用按租户的出站规则，例如独立的出站 IP、凭据或域名允许列表，以便被入侵的租户无法通过其他租户的出站策略窃取数据。

下面的示例同时应用了四个 SDK 级别的选项。构造 `tenantDir` 和 `configDir`，使每个租户获得其他租户无法读取的路径。在 TypeScript 中，`env` 会替换子进程环境，因此要展开 `...process.env` 以保留继承的变量，如 `PATH` 和 `ANTHROPIC_API_KEY`。在 Python 中，`env` 会合并到继承的环境之上。

<CodeGroup>
  ```typescript TypeScript theme={null}
  import { query } from "@anthropic-ai/claude-agent-sdk";

  declare const prompt: string;
  declare const tenantDir: string;
  declare const configDir: string;

  for await (const message of query({
    prompt,
    options: {
      cwd: tenantDir,
      settingSources: [],
      env: {
        ...process.env,
        CLAUDE_CONFIG_DIR: configDir,
        CLAUDE_CODE_DISABLE_AUTO_MEMORY: "1",
      },
    },
  })) {
    // ...
  }
  ```

  ```python Python theme={null}
  from claude_agent_sdk import query, ClaudeAgentOptions
  import asyncio

  prompt: str = ...
  tenant_dir: str = ...
  config_dir: str = ...


  async def main():
      async for message in query(
          prompt=prompt,
          options=ClaudeAgentOptions(
              cwd=tenant_dir,
              setting_sources=[],
              env={
                  "CLAUDE_CONFIG_DIR": config_dir,
                  "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1",
              },
          ),
      ):
          ...


  asyncio.run(main())
  ```

对于按租户的网络控制，请参阅 [安全部署](/docs/en/agent-sdk/secure-deployment)。

## 已知限制

请在部署设计中围绕这些限制进行规划。

| 限制                                                | 应对方法                                                                                                                                                                                                                                                                                     |
| --------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 没有顶层会话超时                                    | 会话不会自行超时。在 `Options` 中设置 `maxTurns`，以限制智能体在停止之前进行的工具使用往返次数。                                                                                                                                                                      |
| 长时间会话中的内存增长                              | 限制会话长度或定期回收子进程。参见 [扩展与并发](#scaling-and-concurrency)。                                                                                                                                                                              |
| 大规模并行子代理扇出可能触发速率限制              | 将工作拆分为更小的批次，而不是一次性发出宽泛的分发。                                                                                                                                                                                                                             |
| 没有针对每个子代理的挂钟时间截止期限              | 在每个 [子代理](/docs/en/agent-sdk/subagents) 的 `AgentDefinition` 中使用 `maxTurns` 进行限制。仅对于后台子代理，`CLAUDE_ASYNC_AGENT_STALL_TIMEOUT_MS` 会设置一个停滞看门狗，当 `run_in_background` 子代理停止产生输出时触发；它不是总运行时间截止期限。 |

## 后续步骤

* [托管手册](https://github.com/anthropics/claude-cookbooks/blob/main/claude_agent_sdk/07_Hosting_the_agent.ipynb)：包含适用于 Docker、Modal 和 Kubernetes 的 [可部署代码](https://github.com/anthropics/claude-cookbooks/tree/main/claude_agent_sdk/hosting) 的笔记本演练。
* [会话存储](/docs/en/agent-sdk/session-storage)：使用 `SessionStore` 适配器跨主机持久化转录内容。
* [可观测性](/docs/en/agent-sdk/observability)：将 OTEL 追踪、指标和日志导出到你的收集器。
* [安全部署](/docs/en/agent-sdk/secure-deployment)：网络控制、凭据管理和隔离加固。
* [成本跟踪](/docs/en/agent-sdk/cost-tracking)：按会话的令牌和成本核算。

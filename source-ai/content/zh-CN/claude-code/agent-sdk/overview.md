---
title: Agent SDK 概述
source_id: claude-code/agent-sdk/overview
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/agent-sdk/overview
owner: Anthropic
content_sha256: 72f434e264cd03bbad3d11ede2056ef909980c790568380027fd9b65014cc4b5
translation_of: claude-code/agent-sdk/overview
translation_model: k3
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/agent-sdk/overview)

Content owner: Anthropic

> ## 文档索引
> 获取完整的文档索引：https://code.claude.com/docs/llms.txt
> 在进一步探索之前，使用此文件发现所有可用页面。

# Agent SDK 概述

> 将 Claude Code 作为库来构建生产级 AI 智能体

构建能够自主读取文件、运行命令、搜索网络、编辑代码等功能的 AI 智能体。Agent SDK 为你提供与 Claude Code 相同的工具、智能体循环和上下文管理能力，可使用 Python 和 TypeScript 编程。对于其他语言，[以编程方式运行 CLI](/docs/en/headless)，并使用 `-p` 标志和 `--output-format json`。关于智能体框架设计背后的思考，请参阅博客上的 [适用于每项任务的框架：Claude Code](https://claude.com/blog/a-harness-for-every-task-dynamic-workflows-in-claude-code) 中的动态工作流。要运行下面的示例，请先按照 [快速入门](#get-started) 中的步骤安装 SDK。

<CodeGroup>
  ```python Python theme={null}
  import asyncio
  from claude_agent_sdk import query, ClaudeAgentOptions


  async def main():
      async for message in query(
          prompt="Find and fix the bug in auth.py",
          options=ClaudeAgentOptions(allowed_tools=["Read", "Edit", "Bash"]),
      ):
          print(message)  # Claude reads the file, finds the bug, edits it


  asyncio.run(main())
  ```

  ```typescript TypeScript theme={null}
  import { query } from "@anthropic-ai/claude-agent-sdk";

  for await (const message of query({
    prompt: "Find and fix the bug in auth.ts",
    options: { allowedTools: ["Read", "Edit", "Bash"] }
  })) {
    console.log(message); // Claude reads the file, finds the bug, edits it
  }
  ```
</CodeGroup>

Agent SDK 内置了读取文件、运行命令和编辑代码的工具，因此你的 Agent 可以立即开始工作，无需自行实现工具执行。深入了解快速入门指南，或探索使用该 SDK 构建的真实 Agent：

<CardGroup cols={2}>
  <Card title="快速入门" icon="play" href="/docs/en/agent-sdk/quickstart">
    在几分钟内构建一个修复 Bug 的 Agent
  </Card>

  <Card title="示例代理" icon="star" href="https://github.com/anthropics/claude-agent-sdk-demos">
    电子邮件助手、研究代理等
  </Card>
</CardGroup>

## 开始使用

<Steps>
  <Step title="Install the SDK">
    <Tabs>
      <Tab title="TypeScript">
        ```bash theme={null}
        npm init -y
        npm pkg set type=module
        npm install @anthropic-ai/claude-agent-sdk
        npm install --save-dev tsx
        ```

        在 `"type": "module"` 中设置 `package.json` 可以让你的智能体脚本使用顶层 `await`,而 [tsx](https://tsx.is) 可直接运行 TypeScript 文件。在已有的 CommonJS 项目中,跳过前两条命令,并将脚本命名为 `agent.mts` 而不是 `agent.ts`。
      </Tab>

      <Tab title="Python (uv)">
        [uv](https://docs.astral.sh/uv/) 是一个快速的 Python 包管理器,可自动处理虚拟环境:

        ```bash theme={null}
        uv init
        uv add claude-agent-sdk
        ```
      </Tab>

      <Tab title="Python (pip)">
        创建并激活虚拟环境,然后安装该包。安装到虚拟环境中可以避免在虚拟环境之外执行 `error: externally-managed-environment` 时,最新版 Debian、Ubuntu 和 Homebrew 安装的系统 Python 所返回的 `pip install` 错误。

        在 macOS 或 Linux 上:

        ```bash theme={null}
        python3 -m venv .venv
        source .venv/bin/activate
        pip install claude-agent-sdk
        ```

        在 Windows 上:

        ```powershell theme={null}
        py -m venv .venv
        .venv\Scripts\Activate.ps1
        pip install claude-agent-sdk
        ```

        如果 PowerShell 因执行策略错误而阻止 `Activate.ps1`,请先运行 `Set-ExecutionPolicy -Scope Process RemoteSigned`。

        该 Python 包要求 Python 3.10 或更高版本。如果 pip 报告 `No matching distribution found for claude-agent-sdk`,说明你的解释器版本低于 3.10。在 macOS 或 Linux 上运行 `python3 --version`,或在 Windows 上运行 `py --version` 进行检查。
      </Tab>
    </Tabs>

    <Note>
      TypeScript 和 Python SDK 都会为你的平台捆绑原生的 Claude Code 二进制文件,因此你无需单独安装 Claude Code。
    </Note>
  </Step>

  <Step title="Set your API key">
    从 [Console](https://platform.claude.com/) 获取 API 密钥,然后将其设置为环境变量。

    在 macOS 或 Linux 上:

    ```bash theme={null}
    export ANTHROPIC_API_KEY=sk-ant-xxxxx
    ```

    在 Windows PowerShell 上:

    ```powershell theme={null}
    $env:ANTHROPIC_API_KEY = "sk-ant-xxxxx"
    ```

    SDK 还支持通过第三方 API 提供商进行身份验证:

    * **Amazon Bedrock**:设置 `CLAUDE_CODE_USE_BEDROCK=1` 环境变量并配置 AWS 凭证
    * **Claude Platform on AWS**:设置 `CLAUDE_CODE_USE_ANTHROPIC_AWS=1` 和 `ANTHROPIC_AWS_WORKSPACE_ID`,然后配置 AWS 凭证
    * **Google Cloud's Agent Platform**:设置 `CLAUDE_CODE_USE_VERTEX=1` 环境变量并配置 Google Cloud 凭证
    * **Microsoft Foundry**:设置 `CLAUDE_CODE_USE_FOUNDRY=1` 环境变量并配置 Azure 凭证

    有关详细信息,请参阅 [Amazon Bedrock](/docs/en/amazon-bedrock)、[Claude Platform on AWS](/docs/en/claude-platform-on-aws)、[Google Cloud's Agent Platform](/docs/en/google-vertex-ai) 或 [Microsoft Foundry](/docs/en/microsoft-foundry) 的设置指南。

    <Note>
      除非事先获得批准,Anthropic 不允许第三方开发者为其产品(包括基于 Claude Agent SDK 构建的智能体)提供 claude.ai 登录或速率限制。请改用本文档中描述的 API 密钥身份验证方法。
    </Note>
  </Step>

  <Step title="Run your first agent">
    此示例创建一个使用内置工具列出当前目录中文件的智能体。

    <CodeGroup>
      ```python Python theme={null}
      import asyncio
      from claude_agent_sdk import query, ClaudeAgentOptions


      async def main():
          async for message in query(
              prompt="What files are in this directory?",
              options=ClaudeAgentOptions(allowed_tools=["Bash", "Glob"]),
          ):
              if hasattr(message, "result"):
                  print(message.result)


      asyncio.run(main())
      ```

      ```typescript TypeScript theme={null}
      import { query } from "@anthropic-ai/claude-agent-sdk";

      for await (const message of query({
        prompt: "What files are in this directory?",
        options: { allowedTools: ["Bash", "Glob"] }
      })) {
        if ("result" in message) console.log(message.result);
      }
      ```
    </CodeGroup>

    将示例保存为 `agent.py` 或 `agent.ts`，然后运行它。代理会打印目录中文件的简短摘要。

    <Tabs>
      <Tab title="TypeScript">
        ```bash theme={null}
        npx tsx agent.ts
        ```

        如果你在 CommonJS 项目中把脚本命名为 `agent.mts`，请改为运行 `npx tsx agent.mts`。
      </Tab>

      <Tab title="Python (uv)">
        ```bash theme={null}
        uv run agent.py
        ```
      </Tab>

      <Tab title="Python (pip)">
        激活虚拟环境后，在 macOS 或 Linux 上：

        ```bash theme={null}
        python3 agent.py
        ```

        在 Windows 上，运行 `python agent.py`。
      </Tab>
    </Tabs>
  </Step>
</Steps>

**准备好开始构建了吗？** 按照 [快速入门](/docs/en/agent-sdk/quickstart)，在几分钟内创建一个能查找并修复错误的代理。

## 功能

让 Claude Code 强大的一切能力都可在 SDK 中使用：

<Tabs>
  <Tab title="Built-in tools">
    你的代理开箱即可读取文件、运行命令并搜索代码库。关键工具包括：

    | 工具                                                                        | 作用                                                        |
    | --------------------------------------------------------------------------- | ------------------------------------------------------------------- |
    | **Read**                                                                    | 读取工作目录中的任何文件                              |
    | **Write**                                                                   | 创建新文件                                                    |
    | **Edit**                                                                    | 对现有文件进行精确编辑                                |
    | **Bash**                                                                    | 运行终端命令、脚本和 git 操作                      |
    | **Monitor**                                                                 | 监视后台脚本，并将每一行输出作为事件做出响应 |
    | **Glob**                                                                    | 按模式查找文件（`**/*.ts`，`src/**/*.py`）                    |
    | **Grep**                                                                    | 使用正则表达式搜索文件内容                                     |
    | **WebSearch**                                                               | 搜索网络以获取当前信息                              |
    | **WebFetch**                                                                | 获取并解析网页内容                                    |
    | **[AskUserQuestion](/docs/en/agent-sdk/user-input#handle-clarifying-questions)** | 通过多选选项向用户提出澄清问题      |

    完整列表（包括调度和 worktree 工具）请参阅 [工具参考](/docs/en/tools-reference)。

    此示例创建一个在你的代码库中搜索 TODO 注释的代理：

    <CodeGroup>
      ```python Python theme={null}
      import asyncio
      from claude_agent_sdk import query, ClaudeAgentOptions


      async def main():
          async for message in query(
              prompt="Find all TODO comments and create a summary",
              options=ClaudeAgentOptions(allowed_tools=["Read", "Glob", "Grep"]),
          ):
              if hasattr(message, "result"):
                  print(message.result)


      asyncio.run(main())
      ```

      ```typescript TypeScript theme={null}
      import { query } from "@anthropic-ai/claude-agent-sdk";

      for await (const message of query({
        prompt: "Find all TODO comments and create a summary",
        options: { allowedTools: ["Read", "Glob", "Grep"] }
      })) {
        if ("result" in message) console.log(message.result);
      }
      ```
    </CodeGroup>
  </Tab>

  <Tab title="Hooks">
    在代理生命周期的关键节点运行自定义代码。SDK 钩子使用回调函数来验证、记录、阻止或转换代理行为。

    **可用的钩子：**`PreToolUse`、`PostToolUse`、`Stop`、`SessionStart`、`SessionEnd`、`UserPromptSubmit` 等等。

    此示例将所有文件更改记录到审计文件中：

    <CodeGroup>
      ```python Python theme={null}
      import asyncio
      from datetime import datetime
      from claude_agent_sdk import query, ClaudeAgentOptions, HookMatcher


      async def log_file_change(input_data, tool_use_id, context):
          file_path = input_data.get("tool_input", {}).get("file_path", "unknown")
          with open("./audit.log", "a") as f:
              f.write(f"{datetime.now()}: modified {file_path}\n")
          return {}


      async def main():
          async for message in query(
              prompt="Create a file named hello.py that prints a greeting",
              options=ClaudeAgentOptions(
                  allowed_tools=["Read", "Edit"],
                  permission_mode="acceptEdits",
                  hooks={
                      "PostToolUse": [
                          HookMatcher(matcher="Edit|Write", hooks=[log_file_change])
                      ]
                  },
              ),
          ):
              if hasattr(message, "result"):
                  print(message.result)


      asyncio.run(main())
      ```

      ```typescript TypeScript theme={null}
      import { query, HookCallback } from "@anthropic-ai/claude-agent-sdk";
      import { appendFile } from "fs/promises";

      const logFileChange: HookCallback = async (input) => {
        const filePath = (input as any).tool_input?.file_path ?? "unknown";
        await appendFile("./audit.log", `${new Date().toISOString()}: modified ${filePath}\n`);
        return {};
      };

      for await (const message of query({
        prompt: "Create a file named hello.ts that prints a greeting",
        options: {
          allowedTools: ["Read", "Edit"],
          permissionMode: "acceptEdits",
          hooks: {
            PostToolUse: [{ matcher: "Edit|Write", hooks: [logFileChange] }]
          }
        }
      })) {
        if ("result" in message) console.log(message.result);
      }
      ```
    </CodeGroup>

    代理完成后，运行 `cat audit.log` 查看记录的文件更改。

    [了解更多关于钩子的信息 →](/docs/en/agent-sdk/hooks)
  </Tab>

  <Tab title="Subagents">
    生成专门的代理来处理聚焦的子任务。主代理分派工作，子代理返回结果。

    定义具有专门指令的自定义代理。子代理通过 Agent 工具调用，因此在 `allowedTools` 中包含 `Agent` 以自动批准这些调用：

    <CodeGroup>
      ```python Python theme={null}
      import asyncio
      from claude_agent_sdk import query, ClaudeAgentOptions, AgentDefinition


      async def main():
          async for message in query(
              prompt="Use the code-reviewer agent to review this codebase",
              options=ClaudeAgentOptions(
                  allowed_tools=["Read", "Glob", "Grep", "Agent"],
                  agents={
                      "code-reviewer": AgentDefinition(
                          description="Expert code reviewer for quality and security reviews.",
                          prompt="Analyze code quality and suggest improvements.",
                          tools=["Read", "Glob", "Grep"],
                      )
                  },
              ),
          ):
              if hasattr(message, "result"):
                  print(message.result)


      asyncio.run(main())
      ```

      ```typescript TypeScript theme={null}
      import { query } from "@anthropic-ai/claude-agent-sdk";

      for await (const message of query({
        prompt: "Use the code-reviewer agent to review this codebase",
        options: {
          allowedTools: ["Read", "Glob", "Grep", "Agent"],
          agents: {
            "code-reviewer": {
              description: "Expert code reviewer for quality and security reviews.",
              prompt: "Analyze code quality and suggest improvements.",
              tools: ["Read", "Glob", "Grep"]
            }
          }
        }
      })) {
        if ("result" in message) console.log(message.result);
      }
      ```
    </CodeGroup>

    子代理上下文中产生的消息包含 `parent_tool_use_id` 字段，让你可以追踪哪些消息属于哪个子代理执行。

    [了解更多子代理相关内容 →](/docs/en/agent-sdk/subagents)
  </Tab>

  <Tab title="MCP">
    通过模型上下文协议（Model Context Protocol）连接外部系统：数据库、浏览器、API，以及[数百种更多集成](https://github.com/modelcontextprotocol/servers)。

    此示例连接 [Playwright MCP 服务器](https://github.com/microsoft/playwright-mcp)，为你的代理提供浏览器自动化能力：

    <CodeGroup>
      ```python Python theme={null}
      import asyncio
      from claude_agent_sdk import query, ClaudeAgentOptions


      async def main():
          async for message in query(
              prompt="Open example.com and describe what you see",
              options=ClaudeAgentOptions(
                  mcp_servers={
                      "playwright": {"command": "npx", "args": ["@playwright/mcp@latest"]}
                  },
                  allowed_tools=["mcp__playwright__*"],
              ),
          ):
              if hasattr(message, "result"):
                  print(message.result)


      asyncio.run(main())
      ```

      ```typescript TypeScript theme={null}
      import { query } from "@anthropic-ai/claude-agent-sdk";

      for await (const message of query({
        prompt: "Open example.com and describe what you see",
        options: {
          mcpServers: {
            playwright: { command: "npx", args: ["@playwright/mcp@latest"] }
          },
          allowedTools: ["mcp__playwright__*"]
        }
      })) {
        if ("result" in message) console.log(message.result);
      }
      ```
    </CodeGroup>

    [了解更多 MCP 相关内容 →](/docs/en/agent-sdk/mcp)
  </Tab>

  <Tab title="Permissions">
    精确控制你的代理可以使用哪些工具。允许安全操作、阻止危险操作，或对敏感操作要求批准。

    <Note>
      关于交互式批准提示和 `AskUserQuestion` 工具，请参阅 [处理批准和用户输入](/docs/en/agent-sdk/user-input)。
    </Note>

    此示例创建一个只读代理，可以分析代码但不能修改代码。`allowed_tools` 预先批准 `Read`、`Glob` 和 `Grep`，使它们无需提示即可运行。未列出的工具仍然可用，但会交由权限模式处理；要完全阻止某些工具，请使用 `disallowed_tools`。

    <CodeGroup>
      ```python Python theme={null}
      import asyncio
      from claude_agent_sdk import query, ClaudeAgentOptions


      async def main():
          async for message in query(
              prompt="Review this code for best practices",
              options=ClaudeAgentOptions(
                  allowed_tools=["Read", "Glob", "Grep"],
              ),
          ):
              if hasattr(message, "result"):
                  print(message.result)


      asyncio.run(main())
      ```

      ```typescript TypeScript theme={null}
      import { query } from "@anthropic-ai/claude-agent-sdk";

      for await (const message of query({
        prompt: "Review this code for best practices",
        options: {
          allowedTools: ["Read", "Glob", "Grep"]
        }
      })) {
        if ("result" in message) console.log(message.result);
      }
      ```
    </CodeGroup>

    [了解更多关于权限的信息 →](/docs/en/agent-sdk/permissions)
  </Tab>

  <Tab title="Sessions">
    在多次交互中保持上下文。Claude 会记住已读取的文件、已完成的分析以及对话历史。可以稍后恢复会话，或分叉会话以探索不同的方法。

    此示例从第一个查询中捕获会话 ID，然后恢复会话以带着完整上下文继续：

    <CodeGroup>
      ```python Python theme={null}
      import asyncio
      from claude_agent_sdk import query, ClaudeAgentOptions, SystemMessage, ResultMessage


      async def main():
          session_id = None

          # First query: capture the session ID
          try:
              async for message in query(
                  prompt="Read the authentication module",
                  options=ClaudeAgentOptions(allowed_tools=["Read", "Glob"]),
              ):
                  if isinstance(message, SystemMessage) and message.subtype == "init":
                      session_id = message.data["session_id"]
          except Exception as error:
              # A single-shot query() raises after yielding an error result. If
              # the failure was an error result, session_id was already captured
              # by the loop above; connection or process failures yield no
              # result message.
              print(f"Session ended with an error: {error}")

          # Resume with full context from the first query
          async for message in query(
              prompt="Now find all places that call it",  # "it" = auth module
              options=ClaudeAgentOptions(resume=session_id),
          ):
              if isinstance(message, ResultMessage):
                  print(message.result)


      asyncio.run(main())
      ```

      ```typescript TypeScript theme={null}
      import { query } from "@anthropic-ai/claude-agent-sdk";

      let sessionId: string | undefined;

      // First query: capture the session ID
      try {
        for await (const message of query({
          prompt: "Read the authentication module",
          options: { allowedTools: ["Read", "Glob"] }
        })) {
          if (message.type === "system" && message.subtype === "init") {
            sessionId = message.session_id;
          }
        }
      } catch (error) {
        // A single-shot query() throws after yielding an error result. If the
        // failure was an error result, sessionId was already captured by the
        // loop above; connection or process failures yield no result message.
        console.error(`Session ended with an error: ${error}`);
      }

      // Resume with full context from the first query
      for await (const message of query({
        prompt: "Now find all places that call it", // "it" = auth module
        options: { resume: sessionId }
      })) {
        if ("result" in message) console.log(message.result);
      }
      ```
    </CodeGroup>

    [了解更多关于会话的信息 →](/docs/en/agent-sdk/sessions)
  </Tab>
</Tabs>

### Claude Code 功能

SDK 还支持 Claude Code 的基于文件系统的配置。使用默认选项时，SDK 会从你工作目录中的 `.claude/` 以及 `~/.claude/` 加载这些配置。要限制加载哪些来源，请在选项中设置 `setting_sources`（Python）或 `settingSources`（TypeScript）。

| 功能                                          | 描述                                                                   | 位置                           |
| ------------------------------------------------ | ----------------------------------------------------------------------------- | ---------------------------------- |
| [技能（Skills）](/docs/en/agent-sdk/skills)                   | Claude 自动使用或你通过 `/name` 调用的专用能力 | `.claude/skills/*/SKILL.md`        |
| [命令（Commands）](/docs/en/agent-sdk/slash-commands)         | 旧版格式的自定义命令。新的自定义命令请使用技能      | `.claude/commands/*.md`            |
| [记忆（Memory）](/docs/en/agent-sdk/modifying-system-prompts) | 项目上下文与指令                                              | `CLAUDE.md` 或 `.claude/CLAUDE.md` |
| [插件（Plugins）](/docs/en/agent-sdk/plugins)                 | 通过技能、代理、钩子和 MCP 服务器进行扩展                            | 通过 `plugins` 选项以编程方式配置  |

## 将 Agent SDK 与其他 Claude 工具进行比较

Claude 平台提供了多种使用 Claude 构建的方式。以下是 Agent SDK 的定位：

<Tabs>
  <Tab title="Agent SDK 与 Client SDK 对比">
    [Anthropic Client SDK](https://platform.claude.com/docs/en/api/client-sdks) 为你提供直接的 API 访问：你发送提示词并自行实现工具执行。**Agent SDK** 则为你提供内置工具执行能力的 Claude。

    使用 Client SDK 时，你需要自行实现工具循环。使用 Agent SDK 时，Claude 会自动处理。以下简化的伪代码展示了两者的区别：

    <CodeGroup>
      ```python Python theme={null}
      # Client SDK: You implement the tool loop
      response = client.messages.create(...)
      while response.stop_reason == "tool_use":
          result = your_tool_executor(response.tool_use)
          response = client.messages.create(tool_result=result, **params)

      # Agent SDK: Claude handles tools autonomously
      async for message in query(prompt="Fix the bug in auth.py"):
          print(message)
      ```

      ```typescript TypeScript theme={null}
      // Client SDK: You implement the tool loop
      let response = await client.messages.create({ ...params });
      while (response.stop_reason === "tool_use") {
        const result = yourToolExecutor(response.tool_use);
        response = await client.messages.create({ tool_result: result, ...params });
      }

      // Agent SDK: Claude handles tools autonomously
      for await (const message of query({ prompt: "Fix the bug in auth.ts" })) {
        console.log(message);
      }
      ```
    </CodeGroup>
  </Tab>

  <Tab title="Agent SDK 与 Claude Code CLI 对比">
    相同的能力，不同的接口：

    | 用例                     | 最佳选择 |
    | ----------------------- | ----------- |
    | 交互式开发             | CLI         |
    | CI/CD 流水线           | SDK         |
    | 自定义应用程序         | SDK         |
    | 一次性任务             | CLI         |
    | 生产环境自动化         | SDK         |

    许多团队两者并用：CLI 用于日常开发，SDK 用于生产环境。工作流程可以在两者之间直接转换。
  </Tab>

  <Tab title="Agent SDK 与托管代理（Managed Agents）对比">
    [Managed Agents](https://platform.claude.com/docs/en/managed-agents/overview) 是一个托管的 REST API：Anthropic 运行代理和沙箱，你的应用程序发送事件并以流式方式接收结果。而 **Agent SDK** 是一个在你自己的进程中运行代理循环的库。

    |                    | Agent SDK                                                                    | 托管代理（Managed Agents）                                                                                                |
    | ------------------ | ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
    | **运行环境**        | 你的进程、你的基础设施                                            | Anthropic 托管的基础设施                                                                              |
    | **接口**      | Python 或 TypeScript 库                                                 | REST API                                                                                                      |
    | **代理操作对象** | 你基础设施上的文件                                                 | 每个会话一个托管沙箱                                                                                 |
    | **会话状态**  | 你文件系统上的 JSONL                                                     | Anthropic 托管的事件日志                                                                                    |
    | **自定义工具**   | 进程内 Python 或 TypeScript 函数                                    | Claude 触发工具；你执行并返回结果                                                      |
    | **适用场景**       | 本地原型开发、直接在你的文件系统和服务上工作的代理 | 无需运维沙箱或会话基础设施的生产代理、长时间运行和异步会话 |

    常见路径是先使用 Agent SDK 在本地进行原型开发，然后迁移到托管代理用于生产环境。
  </Tab>
</Tabs>

## 更新日志

查看 SDK 更新、错误修复和新功能的完整更新日志：

* **TypeScript SDK**：[查看 CHANGELOG.md](https://github.com/anthropics/claude-agent-sdk-typescript/blob/main/CHANGELOG.md)
* **Python SDK**：[查看 CHANGELOG.md](https://github.com/anthropics/claude-agent-sdk-python/blob/main/CHANGELOG.md)

## 报告错误

如果你在使用 Agent SDK 时遇到错误或问题：

* **TypeScript SDK**：[在 GitHub 上报告问题](https://github.com/anthropics/claude-agent-sdk-typescript/issues)
* **Python SDK**：[在 GitHub 上报告问题](https://github.com/anthropics/claude-agent-sdk-python/issues)

## 品牌指南

对于集成 Claude Agent SDK 的合作伙伴，使用 Claude 品牌是可选的。在你的产品中引用 Claude 时：

**允许的用法：**

* "Claude Agent"（下拉菜单的首选用法）
* "Claude"（当菜单已标记为 "Agents" 时）
* "{YourAgentName} Powered by Claude"（如果你已有代理名称）

**不允许的用法：**

* "Claude Code" 或 "Claude Code Agent"
* Claude Code品牌的 ASCII 艺术或模仿 Claude Code 的视觉元素

你的产品应保持自己的品牌，不应看起来像是 Claude Code 或任何 Anthropic 产品。如有关于品牌合规性的问题，请联系 Anthropic [销售团队](https://www.anthropic.com/contact-sales)。

## 许可与条款

Claude Agent SDK 的使用受 [Anthropic 商业服务条款](https://www.anthropic.com/legal/commercial-terms)约束，包括当你使用它为你自己的客户和最终用户提供产品和服务时，除非某个特定组件或依赖项按照该组件 LICENSE 文件所示受不同许可证的覆盖。

## 后续步骤

<CardGroup cols={2}>
  <Card title="快速入门" icon="play" href="/docs/en/agent-sdk/quickstart">
    在几分钟内构建一个查找并修复错误的代理
  </Card>

  <Card title="示例代理" icon="star" href="https://github.com/anthropics/claude-agent-sdk-demos">
    电子邮件助手、研究代理等
  </Card>

  <Card title="TypeScript SDK" icon="code" href="/docs/en/agent-sdk/typescript">
    完整的 TypeScript API 参考和示例
  </Card>

  <Card title="Python SDK" icon="code" href="/docs/en/agent-sdk/python">
    完整的 Python API 参考和示例
  </Card>
</CardGroup>

---
title: 快速入门
source_id: claude-code/agent-sdk/quickstart
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/agent-sdk/quickstart
owner: Anthropic
content_sha256: 548b0ae0312ae5776965cbbcae240eeb0215c33133ece3f9c65f77b3588dc81b
translation_of: claude-code/agent-sdk/quickstart
translation_model: k3
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/agent-sdk/quickstart)

Content owner: Anthropic

> ## 文档索引
> 获取完整文档索引：https://code.claude.com/docs/llms.txt
> 在进一步探索之前，使用此文件发现所有可用页面。

# 快速入门

> 使用 Python 或 TypeScript Agent SDK 构建能够自主工作的 AI 代理

使用 Agent SDK 构建一个 AI 代理，它可以读取你的代码、查找错误并修复它们，全程无需人工干预。

**你将执行的操作：**

1. 使用 Agent SDK 设置项目
2. 创建一个包含一些有 bug 的代码的文件
3. 运行一个自动查找并修复错误的代理

## 先决条件

* **Node.js 18+** 或 **Python 3.10+**
* 一个 **Anthropic 账户**（[在此注册](https://platform.claude.com/)）

## 设置

<Steps>
  <Step title="创建项目文件夹">
    为本快速入门创建一个新目录：

    ```bash theme={null}
    mkdir my-agent
    cd my-agent
    ```

    对于你自己的项目，你可以从任何文件夹运行 SDK；默认情况下，它将有权访问该目录及其子目录中的文件。
  </Step>

  <Step title="安装 SDK">
    为你的语言安装 Agent SDK 包：

    <Tabs>
      <Tab title="TypeScript（新项目）">
        ```bash theme={null}
        npm init -y
        npm pkg set type=module
        npm install @anthropic-ai/claude-agent-sdk
        npm install --save-dev tsx
        ```

        在 `package.json` 中设置 `"type": "module"` 可让你的代理脚本使用顶层 `await`，而 [tsx](https://tsx.is) 可直接运行 TypeScript 文件。安装成功时，npm 会打印 `added N packages`。
      </Tab>

      <Tab title="TypeScript（现有项目）">
        ```bash theme={null}
        npm install @anthropic-ai/claude-agent-sdk
        npm install --save-dev tsx
        ```

        [tsx](https://tsx.is) 可直接运行 TypeScript 文件。如果你的项目使用 CommonJS，请将代理脚本命名为 `agent.mts` 而不是 `agent.ts`。`.mts` 扩展名会让 tsx 将该文件视为 ES 模块，因此无需将整个项目转换为 ES 模块即可使用顶层 `await`。在本快速入门后面的创建和运行步骤中，使用 `agent.mts` 代替 `agent.ts`。
      </Tab>

      <Tab title="Python（uv）">
        [uv](https://docs.astral.sh/uv/) 是一个快速的 Python 包管理器，会自动处理虚拟环境：

        ```bash theme={null}
        uv init
        uv add claude-agent-sdk
        ```
      </Tab>

      <Tab title="Python（pip）">
        创建并激活虚拟环境，然后安装包。

        在 macOS 或 Linux 上：

        ```bash theme={null}
        python3 -m venv .venv
        source .venv/bin/activate
        pip install claude-agent-sdk
        ```

        在 Windows 上：

        ```powershell theme={null}
        py -m venv .venv
        .venv\Scripts\Activate.ps1
        pip install claude-agent-sdk
        ```

        如果 PowerShell 因执行策略错误而阻止 `Activate.ps1`，请先运行 `Set-ExecutionPolicy -Scope Process RemoteSigned`。
      </Tab>
    </Tabs>

    <Note>
      TypeScript 和 Python SDK 都会为你的平台捆绑一个原生 Claude Code 二进制文件，因此你不需要单独安装 Claude Code。
    </Note>
  </Step>

  <Step title="设置你的 API 密钥">
    从 [Claude Console](https://platform.claude.com/) 获取 API 密钥，然后在你要运行代理的 shell 中将其设置为环境变量：

    <Tabs>
      <Tab title="macOS / Linux">
        ```bash theme={null}
        export ANTHROPIC_API_KEY=your-api-key
        ```
      </Tab>

      <Tab title="Windows（PowerShell）">
        ```powershell theme={null}
        $env:ANTHROPIC_API_KEY = "your-api-key"
        ```
      </Tab>
    </Tabs>

    SDK 会从运行你的代理的进程环境中读取密钥；它不会自动加载 `.env` 文件。如果你把密钥保存在 `.env` 文件中，请在调用 SDK 之前自行加载，例如使用 `dotenv` 包。

    SDK 还支持通过第三方 API 提供商进行身份验证：

    * **Amazon Bedrock**：设置 `CLAUDE_CODE_USE_BEDROCK=1` 环境变量并配置 AWS 凭证
    * **AWS 上的 Claude 平台**：设置 `CLAUDE_CODE_USE_ANTHROPIC_AWS=1` 和 `ANTHROPIC_AWS_WORKSPACE_ID`，然后配置 AWS 凭证
    * **Google Cloud 的智能体平台**：设置 `CLAUDE_CODE_USE_VERTEX=1` 环境变量并配置 Google Cloud 凭证
    * **Microsoft Foundry**：设置 `CLAUDE_CODE_USE_FOUNDRY=1` 环境变量并配置 Azure 凭证

    有关详细信息，请参阅 [Amazon Bedrock](/docs/en/amazon-bedrock)、[AWS 上的 Claude 平台](/docs/en/claude-platform-on-aws)、[Google Cloud 的智能体平台](/docs/en/google-vertex-ai) 或 [Microsoft Foundry](/docs/en/microsoft-foundry) 的设置指南。

    <Note>
      除非事先获得批准，Anthropic 不允许第三方开发者为其产品（包括基于 Claude Agent SDK 构建的代理）提供 claude.ai 登录或速率限制。请改用本文档中描述的 API 密钥身份验证方法。
    </Note>
  </Step>
</Steps>

## 创建一个包含 bug 的文件

本快速入门将引导你构建一个能够在代码中查找并修复 bug 的代理。首先，你需要一个包含一些故意设置的 bug 的文件，供代理修复。在 `my-agent` 目录中创建 `utils.py`，并粘贴以下代码：

```python theme={null}
def calculate_average(numbers):
    total = 0
    for num in numbers:
        total += num
    return total / len(numbers)


def get_user_name(user):
    return user["name"].upper()
```

这段代码有两个 bug：

1. `calculate_average([])` 会因除以零而崩溃
2. `get_user_name(None)` 会因 TypeError 而崩溃

## 构建一个查找并修复 bug 的代理

如果你使用的是 Python SDK，请创建 `agent.py`；如果是 TypeScript，则创建 `agent.ts`。如果你现有的项目使用 CommonJS，请改用 `agent.mts`：

<CodeGroup>
  ```python Python theme={null}
  import asyncio
  from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, ResultMessage


  async def main():
      # Agentic loop: streams messages as Claude works
      async for message in query(
          prompt="Review utils.py for bugs that would cause crashes. Fix any issues you find.",
          options=ClaudeAgentOptions(
              allowed_tools=["Read", "Edit", "Glob"],  # Auto-approve these tools
              permission_mode="acceptEdits",  # Auto-approve file edits
          ),
      ):
          # Print human-readable output
          if isinstance(message, AssistantMessage):
              for block in message.content:
                  if hasattr(block, "text"):
                      print(block.text)  # Claude's reasoning
                  elif hasattr(block, "name"):
                      print(f"Tool: {block.name}")  # Tool being called
          elif isinstance(message, ResultMessage):
              print(f"Done: {message.subtype}")  # Final result


  asyncio.run(main())
  ```

  ```typescript TypeScript theme={null}
  import { query } from "@anthropic-ai/claude-agent-sdk";

  // Agentic loop: streams messages as Claude works
  for await (const message of query({
    prompt: "Review utils.py for bugs that would cause crashes. Fix any issues you find.",
    options: {
      allowedTools: ["Read", "Edit", "Glob"], // Auto-approve these tools
      permissionMode: "acceptEdits" // Auto-approve file edits
    }
  })) {
    // Print human-readable output
    if (message.type === "assistant" && message.message?.content) {
      for (const block of message.message.content) {
        if ("text" in block) {
          console.log(block.text); // Claude's reasoning
        } else if ("name" in block) {
          console.log(`Tool: ${block.name}`); // Tool being called
        }
      }
    } else if (message.type === "result") {
      console.log(`Done: ${message.subtype}`); // Final result
    }
  }
  ```
</CodeGroup>

这段代码包含三个主要部分：

1. **`query`**：创建代理循环的主入口点。它返回一个异步迭代器，因此你可以使用 `async for` 在 Claude 工作时流式接收消息。请参阅 [Python](/docs/en/agent-sdk/python#query) 或 [TypeScript](/docs/en/agent-sdk/typescript#query) SDK 参考中的完整 API。

2. **`prompt`**：你希望 Claude 完成的任务。Claude 会根据任务自行判断使用哪些工具。

3. **`options`**：代理的配置。此示例使用 `allowedTools` 预先批准 `Read`、`Edit` 和 `Glob`，并使用 `permissionMode: "acceptEdits"` 自动批准文件更改。其他选项包括 `systemPrompt`、`mcpServers` 等。请参阅 [Python](/docs/en/agent-sdk/python#claudeagentoptions) 或 [TypeScript](/docs/en/agent-sdk/typescript#options) 的所有选项。

`async for` 循环会在 Claude 思考、调用工具、观察结果并决定下一步操作时持续运行。每次迭代都会产生一条消息：Claude 的推理、一次工具调用、一个工具结果或最终结果。SDK 负责处理编排工作（工具执行、上下文管理、重试），你只需消费消息流即可。当 Claude 完成任务或遇到错误时，循环结束。

循环内部的消息处理会筛选出人类可读的输出。如果不进行筛选，你会看到原始消息对象，包括系统初始化和内部状态，这对调试很有用，但在其他情况下会显得嘈杂。

<Note>
  此示例使用流式传输来实时显示进度。如果你不需要实时输出（例如用于后台作业或 CI 流水线），可以一次性收集所有消息。详情请参阅 [Streaming vs. single-turn mode](/docs/en/agent-sdk/streaming-vs-single-mode)。
</Note>

### 运行你的代理

你的代理已准备就绪。使用以下命令运行它：

<Tabs>
  <Tab title="TypeScript">
    ```bash theme={null}
    npx tsx agent.ts
    ```

    如果你的脚本命名为 `agent.mts`，则改为运行 `npx tsx agent.mts`。
  </Tab>

  <Tab title="Python (uv)">
    ```bash theme={null}
    uv run agent.py
    ```
  </Tab>

  <Tab title="Python (pip)">
    在虚拟环境仍处于激活状态时：

    ```bash theme={null}
    python agent.py
    ```
  </Tab>
</Tabs>

在工作过程中，代理会打印其推理过程以及调用的每个工具，最后输出 `Done: success`。运行后，检查 `utils.py`。你会看到用于处理空列表和 null 用户值的防御性代码。你的代理自主完成了以下操作：

1. **读取** `utils.py` 以理解代码
2. **分析**逻辑并识别会导致崩溃的边界情况
3. **编辑**文件以添加适当的错误处理

这正是 Agent SDK 的与众不同之处：Claude 直接执行工具，而不是要求你去实现它们。

<Note>
  如果你看到“API key not found”，请确保已在运行代理的 shell 中设置了 `ANTHROPIC_API_KEY` 环境变量。SDK 不会自动加载 `.env` 文件。如需更多帮助，请参阅 [full troubleshooting guide](/docs/en/troubleshooting)。
</Note>

### 尝试其他提示词

现在您的代理已设置完成，尝试一些不同的提示词：

* `"Add docstrings to all functions in utils.py"`
* `"Add type hints to all functions in utils.py"`
* `"Create a README.md documenting the functions in utils.py"`

### 自定义您的代理

您可以通过更改选项来修改代理的行为。以下是几个示例：

**添加网络搜索功能：**

<CodeGroup>
  ```python Python theme={null}
  options = ClaudeAgentOptions(
      allowed_tools=["Read", "Edit", "Glob", "WebSearch"], permission_mode="acceptEdits"
  )
  ```

  ```typescript TypeScript hidelines={1,-1} theme={null}
  const _ = {
    options: {
      allowedTools: ["Read", "Edit", "Glob", "WebSearch"],
      permissionMode: "acceptEdits"
    }
  };
  ```
</CodeGroup>

**为 Claude 提供自定义系统提示词：**

<CodeGroup>
  ```python Python theme={null}
  options = ClaudeAgentOptions(
      allowed_tools=["Read", "Edit", "Glob"],
      permission_mode="acceptEdits",
      system_prompt="You are a senior Python developer. Always follow PEP 8 style guidelines.",
  )
  ```

  ```typescript TypeScript hidelines={1,-1} theme={null}
  const _ = {
    options: {
      allowedTools: ["Read", "Edit", "Glob"],
      permissionMode: "acceptEdits",
      systemPrompt: "You are a senior Python developer. Always follow PEP 8 style guidelines."
    }
  };
  ```
</CodeGroup>

**在终端中运行命令：**

<CodeGroup>
  ```python Python theme={null}
  options = ClaudeAgentOptions(
      allowed_tools=["Read", "Edit", "Glob", "Bash"], permission_mode="acceptEdits"
  )
  ```

  ```typescript TypeScript hidelines={1,-1} theme={null}
  const _ = {
    options: {
      allowedTools: ["Read", "Edit", "Glob", "Bash"],
      permissionMode: "acceptEdits"
    }
  };
  ```
</CodeGroup>

启用 `Bash` 后，尝试：`"Write unit tests for utils.py, run them, and fix any failures"`

## 关键概念

**工具**控制您的代理可以做什么：

| 工具                                  | 代理可以执行的操作   |
| -------------------------------------- | ----------------------- |
| `Read`, `Glob`, `Grep`                 | 只读分析      |
| `Read`, `Edit`, `Glob`                 | 分析并修改代码 |
| `Read`, `Edit`, `Bash`, `Glob`, `Grep` | 完全自动化         |

**权限模式**控制您希望有多少人工监督：

| 模式                | 行为                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | 用例                                  |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------- |
| `acceptEdits`       | 自动批准文件编辑和常见文件系统命令，其他操作会询问                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | 受信任的开发工作流             |
| `plan`              | 运行只读工具；文件编辑从不自动批准，并会到达你的 `canUseTool` 回调                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | 在批准执行前确定任务范围 |
| `dontAsk`           | 拒绝任何不在 `allowedTools` 中的内容；连接器工具 [你的组织设置为 `ask`](/docs/en/mcp#organization-controls-on-connector-tools) 以及需要用户交互的工具也会被拒绝，即使 你已经列出了它们                                                                                                                                                              | 锁定的无头代理 |
| `auto`              | 一个模型分类器负责批准或拒绝权限提示                                                                                                                                                                                                                                                                                                                             | 带有安全防护栏的自主代理  |
| `bypassPermissions` | 运行所有工具且不再提示，但以下情况除外：被显式 [`ask` 规则](/docs/en/agent-sdk/permissions#how-permissions-are-evaluated) 匹配的工具、[您的组织设置为 `ask` 的连接器工具](/docs/en/mcp#organization-controls-on-connector-tools)，以及需要用户交互的工具。在 TypeScript SDK 中，还需要在 `options` 中设置 `allowDangerouslySkipPermissions: true` | 沙盒化 CI、完全受信任的环境  |
| `default`           | 需要一个 `canUseTool` 回调来处理审批                                                                                                                                                                                                                                                                                                                                                                                                              | 自定义审批流程                     |

上面的示例使用了 `acceptEdits` 模式，它会自动批准文件操作，使代理无需交互式提示即可运行。如果你希望提示用户进行批准，请使用 `default` 模式，并提供一个用于收集用户输入的 [`canUseTool` 回调](/docs/en/agent-sdk/user-input)。如需更多控制，请参阅 [权限](/docs/en/agent-sdk/permissions)。

## 后续步骤

现在你已经创建了第一个代理，接下来学习如何扩展其功能并根据你的使用场景进行定制：

* **[权限](/docs/en/agent-sdk/permissions)**：控制你的代理可以执行的操作以及何时需要批准
* **[钩子(Hooks)](/docs/en/agent-sdk/hooks)**:在工具调用之前或之后运行自定义代码
* **[会话(Sessions)](/docs/en/agent-sdk/sessions)**：构建能够保持上下文的多轮代理
* **[MCP 服务器](/docs/en/agent-sdk/mcp)**:连接数据库、浏览器、API 及其他外部系统
* **[托管](/docs/en/agent-sdk/hosting)**：将代理部署到 Docker、云端和 CI/CD
* **[示例代理](https://github.com/anthropics/claude-agent-sdk-demos)**：查看完整示例：邮件助手、研究代理等

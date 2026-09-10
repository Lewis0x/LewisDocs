---
title: 使用检查点功能回退文件更改
source_id: claude-code/agent-sdk/file-checkpointing
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/agent-sdk/file-checkpointing
owner: Anthropic
content_sha256: edc4eb39cf9a62ed1b70aba2cbbfef7d8eedf33130a7ce21ce80792ff579f696
translation_of: claude-code/agent-sdk/file-checkpointing
translation_model: k3
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/agent-sdk/file-checkpointing)

Content owner: Anthropic

> ## 文档索引
> 获取完整文档索引，地址：https://code.claude.com/docs/llms.txt
> 在进一步探索之前，请使用此文件来发现所有可用的页面。

# 使用检查点功能回退文件更改

> 跟踪代理会话期间的文件更改，并将文件恢复到任何先前状态

文件检查点功能可跟踪代理会话期间通过 Write、Edit 和 NotebookEdit 工具进行的文件修改，允许您将文件回退到任何先前状态。想试试吗？跳转到[交互式示例](#动手试试)。

使用检查点功能，您可以：

* 通过将文件恢复到已知的良好状态来**撤销不需要的更改**
* 通过恢复到某个检查点并尝试不同的方法来**探索替代方案**
* 当代理进行了错误的修改时，**从错误中恢复**

<Warning>
  只有通过 Write、Edit 和 NotebookEdit 工具所做的更改才会被跟踪。通过 Bash 命令（如 `echo > file.txt` 或 `sed -i`）所做的更改不会被检查点系统捕获。
</Warning>

## 检查点的工作原理

当您启用文件检查点功能时，SDK 会在通过 Write、Edit 或 NotebookEdit 工具修改文件之前创建文件备份。响应流中的用户消息包含一个检查点 UUID，您可以将其用作还原点。

检查点与代理用于修改文件的以下内置工具配合使用：

| 工具         | 描述                                                        |
| ------------ | ------------------------------------------------------------------ |
| Write        | 创建新文件或用新内容覆盖现有文件 |
| Edit         | 对现有文件的特定部分进行有针对性的编辑         |
| NotebookEdit | 修改 Jupyter 笔记本中的单元格（`.ipynb` 文件）               |

<Note>
  文件回退会将磁盘上的文件恢复到先前状态。它不会回退对话本身。调用 `rewindFiles()`（TypeScript）或 `rewind_files()`（Python）后，对话历史和上下文保持不变。
</Note>

检查点系统跟踪：

* 会话期间创建的文件
* 会话期间修改的文件
* 被修改文件的原始内容

当您回退到某个检查点时，已创建的文件将被删除，已修改的文件将恢复到该时间点的内容。

## 实现检查点

要使用文件检查点，请在选项中启用它，从响应流中捕获检查点 UUID，然后在需要恢复时调用 `rewindFiles()`（TypeScript）或 `rewind_files()`（Python）。

以下示例展示了完整流程：启用检查点、从响应流中捕获检查点 UUID 和会话 ID，然后稍后恢复会话以回退文件。下面详细解释每个步骤。本节中的示例使用提示词“重构身份验证模块”。请在包含身份验证模块的项目中运行它们，或将提示词更改为命名项目中存在的文件，这样你就可以观察文件的变化，并看到回退恢复它们。

<CodeGroup>
  ```python Python theme={null}
  import asyncio
  from claude_agent_sdk import (
      ClaudeSDKClient,
      ClaudeAgentOptions,
      UserMessage,
      ResultMessage,
  )


  async def main():
      # Step 1: Enable checkpointing
      options = ClaudeAgentOptions(
          enable_file_checkpointing=True,
          permission_mode="acceptEdits",  # Auto-accept file edits without prompting
          extra_args={
              "replay-user-messages": None
          },  # Required to receive checkpoint UUIDs in the response stream
      )

      checkpoint_id = None
      session_id = None

      # Run the query and capture checkpoint UUID and session ID
      async with ClaudeSDKClient(options) as client:
          await client.query("Refactor the authentication module")

          # Step 2: Capture checkpoint UUID from the first user message
          async for message in client.receive_response():
              if isinstance(message, UserMessage) and message.uuid and not checkpoint_id:
                  checkpoint_id = message.uuid
              if isinstance(message, ResultMessage) and not session_id:
                  session_id = message.session_id

      # Step 3: Later, rewind by resuming the session with an empty prompt
      if checkpoint_id and session_id:
          async with ClaudeSDKClient(
              ClaudeAgentOptions(enable_file_checkpointing=True, resume=session_id)
          ) as client:
              await client.query("")  # Empty prompt to open the connection
              async for message in client.receive_response():
                  await client.rewind_files(checkpoint_id)
                  break
          print(f"Rewound to checkpoint: {checkpoint_id}")


  asyncio.run(main())
  ```

  ```typescript TypeScript theme={null}
  import { query } from "@anthropic-ai/claude-agent-sdk";

  async function main() {
    // Step 1: Enable checkpointing
    const opts = {
      enableFileCheckpointing: true,
      permissionMode: "acceptEdits" as const, // Auto-accept file edits without prompting
      extraArgs: { "replay-user-messages": null } // Required to receive checkpoint UUIDs in the response stream
    };

    const response = query({
      prompt: "Refactor the authentication module",
      options: opts
    });

    let checkpointId: string | undefined;
    let sessionId: string | undefined;

    // Step 2: Capture checkpoint UUID from the first user message
    try {
      for await (const message of response) {
        if (message.type === "user" && message.uuid && !checkpointId) {
          checkpointId = message.uuid;
        }
        if ("session_id" in message && !sessionId) {
          sessionId = message.session_id;
        }
      }
    } catch (error) {
      // A single-shot query() throws after yielding an error result. If the
      // failure was an error result, sessionId and checkpointId were already
      // captured by the loop above; connection or process failures yield no
      // result message.
      console.error(`Session ended with an error: ${error}`);
    }

    // Step 3: Later, rewind by resuming the session with an empty prompt
    if (checkpointId && sessionId) {
      const rewindQuery = query({
        prompt: "", // Empty prompt to open the connection
        options: { ...opts, resume: sessionId }
      });

      for await (const msg of rewindQuery) {
        await rewindQuery.rewindFiles(checkpointId);
        break;
      }
      console.log(`Rewound to checkpoint: ${checkpointId}`);
    }
  }

  main();
  ```
</CodeGroup>

<Steps>
  <Step title="启用检查点">
    配置你的 SDK 选项以启用检查点并接收检查点 UUID：

    | 选项                      | Python                                      | TypeScript                                    | 描述                                             |
    | ------------------------ | ------------------------------------------- | --------------------------------------------- | ------------------------------------------------ |
    | 启用检查点                | `enable_file_checkpointing=True`            | `enableFileCheckpointing: true`               | 跟踪文件更改以便回退                             |
    | 接收检查点 UUID           | `extra_args={"replay-user-messages": None}` | `extraArgs: { 'replay-user-messages': null }` | 在流中获取用户消息 UUID 所必需                    |

    <CodeGroup>
      ```python Python theme={null}
      options = ClaudeAgentOptions(
          enable_file_checkpointing=True,
          permission_mode="acceptEdits",
          extra_args={"replay-user-messages": None},
      )

      async with ClaudeSDKClient(options) as client:
          await client.query("Refactor the authentication module")
      ```

      ```typescript TypeScript theme={null}
      const response = query({
        prompt: "Refactor the authentication module",
        options: {
          enableFileCheckpointing: true,
          permissionMode: "acceptEdits" as const,
          extraArgs: { "replay-user-messages": null }
        }
      });
      ```
    </CodeGroup>
  </Step>

  <Step title="捕获检查点 UUID 和会话 ID">
    设置了 `replay-user-messages` 选项（如上所示）后，响应流中的每条用户消息都有一个 UUID，可充当检查点。

    对于大多数用例，捕获第一条用户消息的 UUID（`message.uuid`）即可；回退到该 UUID 会将所有文件恢复到原始状态。如需存储多个检查点并回退到中间状态，请参阅 [多个还原点](#多个还原点)。

    捕获会话 ID（`message.session_id`）是可选的；只有当你想在流完成之后稍后再回退时才需要它。如果你是在仍在处理消息时立即调用 `rewindFiles()`（如 [在高风险操作前设置检查点](#在高风险操作前设置检查点) 中的示例所示），则可以跳过捕获会话 ID。

    <CodeGroup>
      ```python Python theme={null}
      checkpoint_id = None
      session_id = None

      async for message in client.receive_response():
          # Capture the first user message UUID as the checkpoint
          if isinstance(message, UserMessage) and message.uuid and checkpoint_id is None:
              checkpoint_id = message.uuid
          # Capture session ID from the result message
          if isinstance(message, ResultMessage):
              session_id = message.session_id
      ```

      ```typescript TypeScript theme={null}
      let checkpointId: string | undefined;
      let sessionId: string | undefined;

      for await (const message of response) {
        // Capture the first user message UUID as the checkpoint
        if (message.type === "user" && message.uuid && !checkpointId) {
          checkpointId = message.uuid;
        }
        // Capture session ID from any message that has it
        if ("session_id" in message) {
          sessionId = message.session_id;
        }
      }
      ```
    </CodeGroup>
  </Step>

  <Step title="回退文件">
    要在流完成后回退，请使用空提示恢复会话，并调用 `rewind_files()`（Python）或 `rewindFiles()`（TypeScript）并传入你的检查点 UUID。你也可以在流进行期间回退；该模式请参阅 [在高风险操作前设置检查点](#在高风险操作前设置检查点)。

    <CodeGroup>
      ```python Python theme={null}
      async with ClaudeSDKClient(
          ClaudeAgentOptions(enable_file_checkpointing=True, resume=session_id)
      ) as client:
          await client.query("")  # Empty prompt to open the connection
          async for message in client.receive_response():
              if checkpoint_id:
                  await client.rewind_files(checkpoint_id)
              break
      ```

      ```typescript TypeScript theme={null}
      const rewindQuery = query({
        prompt: "", // Empty prompt to open the connection
        options: { ...opts, resume: sessionId }
      });

      for await (const msg of rewindQuery) {
        if (checkpointId) {
          await rewindQuery.rewindFiles(checkpointId);
        }
        break;
      }
      ```
    </CodeGroup>

    如果你捕获了会话 ID 和检查点 ID，也可以从 CLI 回退。此命令需要 `claude` 可执行文件，它来自[安装 Claude Code](/docs/en/setup)，不会随 SDK 包一起安装。SDK 会为你启用检查点功能，但当你直接运行 `claude -p` 时，必须设置 `CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING` 环境变量：

    ```bash theme={null}
    CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING=true claude -p --resume <session-id> --rewind-files <checkpoint-uuid>
    ```

    `--rewind-files` 标志不会出现在 `claude --help` 输出中，但 CLI 会按所示方式接受它。
  </Step>
</Steps>

## 常见模式

这些模式展示了根据你的用例捕获和使用检查点 UUID 的不同方式。

### 在高风险操作前设置检查点

此模式仅保留最新的检查点 UUID，并在每个智能体回合开始之前更新它。如果在处理过程中出现问题，你可以立即回退到最后一个安全状态并跳出循环。

在运行此示例之前，请将 `your_revert_condition`（Python）或 `yourRevertCondition`（TypeScript）替换为你自己的检查，例如错误检测或验证失败；该占位符在示例中并未定义。

<CodeGroup>
  ```python Python theme={null}
  import asyncio
  from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, UserMessage


  async def main():
      options = ClaudeAgentOptions(
          enable_file_checkpointing=True,
          permission_mode="acceptEdits",
          extra_args={"replay-user-messages": None},
      )

      safe_checkpoint = None

      async with ClaudeSDKClient(options) as client:
          await client.query("Refactor the authentication module")

          async for message in client.receive_response():
              # Update checkpoint before each agent turn starts
              # This overwrites the previous checkpoint. Only keep the latest
              if isinstance(message, UserMessage) and message.uuid:
                  safe_checkpoint = message.uuid

              # Decide when to revert based on your own logic
              # For example: error detection, validation failure, or user input
              if your_revert_condition and safe_checkpoint:
                  await client.rewind_files(safe_checkpoint)
                  # Exit the loop after rewinding, files are restored
                  break


  asyncio.run(main())
  ```

  ```typescript TypeScript theme={null}
  import { query } from "@anthropic-ai/claude-agent-sdk";

  async function main() {
    const response = query({
      prompt: "Refactor the authentication module",
      options: {
        enableFileCheckpointing: true,
        permissionMode: "acceptEdits" as const,
        extraArgs: { "replay-user-messages": null }
      }
    });

    let safeCheckpoint: string | undefined;

    for await (const message of response) {
      // Update checkpoint before each agent turn starts
      // This overwrites the previous checkpoint. Only keep the latest
      if (message.type === "user" && message.uuid) {
        safeCheckpoint = message.uuid;
      }

      // Decide when to revert based on your own logic
      // For example: error detection, validation failure, or user input
      if (yourRevertCondition && safeCheckpoint) {
        await response.rewindFiles(safeCheckpoint);
        // Exit the loop after rewinding, files are restored
        break;
      }
    }
  }

  main();
  ```
</CodeGroup>

### 多个还原点

如果 Claude 跨多个轮次进行更改，你可能希望回退到某个特定点，而不是一路回退到最开始。例如，如果 Claude 在第一轮重构了一个文件，并在第二轮添加了测试，你可能希望保留重构，但撤销测试。

此模式将所有检查点 UUID 及元数据存储在一个数组中。会话完成后，你可以回退到任何先前的检查点：

<CodeGroup>
  ```python Python theme={null}
  import asyncio
  from dataclasses import dataclass
  from datetime import datetime
  from claude_agent_sdk import (
      ClaudeSDKClient,
      ClaudeAgentOptions,
      UserMessage,
      ResultMessage,
  )


  # Store checkpoint metadata for better tracking
  @dataclass
  class Checkpoint:
      id: str
      description: str
      timestamp: datetime


  async def main():
      options = ClaudeAgentOptions(
          enable_file_checkpointing=True,
          permission_mode="acceptEdits",
          extra_args={"replay-user-messages": None},
      )

      checkpoints = []
      session_id = None

      async with ClaudeSDKClient(options) as client:
          await client.query("Refactor the authentication module")

          async for message in client.receive_response():
              if isinstance(message, UserMessage) and message.uuid:
                  checkpoints.append(
                      Checkpoint(
                          id=message.uuid,
                          description=f"After turn {len(checkpoints) + 1}",
                          timestamp=datetime.now(),
                      )
                  )
              if isinstance(message, ResultMessage) and not session_id:
                  session_id = message.session_id

      # Later: rewind to any checkpoint by resuming the session
      if checkpoints and session_id:
          target = checkpoints[0]  # Pick any checkpoint
          async with ClaudeSDKClient(
              ClaudeAgentOptions(enable_file_checkpointing=True, resume=session_id)
          ) as client:
              await client.query("")  # Empty prompt to open the connection
              async for message in client.receive_response():
                  await client.rewind_files(target.id)
                  break
          print(f"Rewound to: {target.description}")


  asyncio.run(main())
  ```

  ```typescript TypeScript theme={null}
  import { query } from "@anthropic-ai/claude-agent-sdk";

  // Store checkpoint metadata for better tracking
  interface Checkpoint {
    id: string;
    description: string;
    timestamp: Date;
  }

  async function main() {
    const opts = {
      enableFileCheckpointing: true,
      permissionMode: "acceptEdits" as const,
      extraArgs: { "replay-user-messages": null }
    };

    const response = query({
      prompt: "Refactor the authentication module",
      options: opts
    });

    const checkpoints: Checkpoint[] = [];
    let sessionId: string | undefined;

    try {
      for await (const message of response) {
        if (message.type === "user" && message.uuid) {
          checkpoints.push({
            id: message.uuid,
            description: `After turn ${checkpoints.length + 1}`,
            timestamp: new Date()
          });
        }
        if ("session_id" in message && !sessionId) {
          sessionId = message.session_id;
        }
      }
    } catch (error) {
      // A single-shot query() throws after yielding an error result. If the
      // failure was an error result, sessionId and the checkpoints array were
      // already populated by the loop above; connection or process failures
      // yield no result message.
      console.error(`Session ended with an error: ${error}`);
    }

    // Later: rewind to any checkpoint by resuming the session
    if (checkpoints.length > 0 && sessionId) {
      const target = checkpoints[0]; // Pick any checkpoint
      const rewindQuery = query({
        prompt: "", // Empty prompt to open the connection
        options: { ...opts, resume: sessionId }
      });

      for await (const msg of rewindQuery) {
        await rewindQuery.rewindFiles(target.id);
        break;
      }
      console.log(`Rewound to: ${target.description}`);
    }
  }

  main();
  ```
</CodeGroup>

## 动手试试

这个完整的示例会创建一个小的工具文件,让智能体添加文档注释,向你展示更改,然后询问你是否要回退。

在开始之前,请确保你已经[安装了 Claude Agent SDK](/docs/en/agent-sdk/quickstart)。

<Steps>
  <Step title="创建测试文件">
    创建一个名为 `utils.py`(Python)或 `utils.ts`(TypeScript)的新文件,并粘贴以下代码:

    <CodeGroup>
      ```python utils.py theme={null}
      def add(a, b):
          return a + b


      def subtract(a, b):
          return a - b


      def multiply(a, b):
          return a * b


      def divide(a, b):
          if b == 0:
              raise ValueError("Cannot divide by zero")
          return a / b
      ```

      ```typescript utils.ts theme={null}
      export function add(a: number, b: number): number {
        return a + b;
      }

      export function subtract(a: number, b: number): number {
        return a - b;
      }

      export function multiply(a: number, b: number): number {
        return a * b;
      }

      export function divide(a: number, b: number): number {
        if (b === 0) {
          throw new Error("Cannot divide by zero");
        }
        return a / b;
      }
      ```
    </CodeGroup>
  </Step>

  <Step title="运行交互式示例">
    在与你的工具文件相同的目录中,创建一个名为 `try_checkpointing.py`(Python)或 `try_checkpointing.ts`(TypeScript)的新文件,并粘贴以下代码。

    这个脚本会让 Claude 为你的工具文件添加文档注释,然后让你选择回退并恢复原始内容。

    <CodeGroup>
      ```python try_checkpointing.py theme={null}
      import asyncio
      from claude_agent_sdk import (
          ClaudeSDKClient,
          ClaudeAgentOptions,
          UserMessage,
          ResultMessage,
      )


      async def main():
          # Configure the SDK with checkpointing enabled
          # - enable_file_checkpointing: Track file changes for rewinding
          # - permission_mode: Auto-accept file edits without prompting
          # - extra_args: Required to receive user message UUIDs in the stream
          options = ClaudeAgentOptions(
              enable_file_checkpointing=True,
              permission_mode="acceptEdits",
              extra_args={"replay-user-messages": None},
          )

          checkpoint_id = None  # Store the user message UUID for rewinding
          session_id = None  # Store the session ID for resuming

          print("Running agent to add doc comments to utils.py...\n")

          # Run the agent and capture checkpoint data from the response stream
          async with ClaudeSDKClient(options) as client:
              await client.query("Add doc comments to utils.py")

              async for message in client.receive_response():
                  # Capture the first user message UUID - this is our restore point
                  if isinstance(message, UserMessage) and message.uuid and not checkpoint_id:
                      checkpoint_id = message.uuid
                  # Capture the session ID so we can resume later
                  if isinstance(message, ResultMessage):
                      session_id = message.session_id

          print("Done! Open utils.py to see the added doc comments.\n")

          # Ask the user if they want to rewind the changes
          if checkpoint_id and session_id:
              response = input("Rewind to remove the doc comments? (y/n): ")

              if response.lower() == "y":
                  # Resume the session with an empty prompt, then rewind
                  async with ClaudeSDKClient(
                      ClaudeAgentOptions(enable_file_checkpointing=True, resume=session_id)
                  ) as client:
                      await client.query("")  # Empty prompt opens the connection
                      async for message in client.receive_response():
                          await client.rewind_files(checkpoint_id)  # Restore files
                          break

                  print(
                      "\n✓ File restored! Open utils.py to verify the doc comments are gone."
                  )
              else:
                  print("\nKept the modified file.")


      asyncio.run(main())
      ```

      ```typescript try_checkpointing.ts theme={null}
      import { query } from "@anthropic-ai/claude-agent-sdk";
      import * as readline from "readline";

      async function main() {
        // Configure the SDK with checkpointing enabled
        // - enableFileCheckpointing: Track file changes for rewinding
        // - permissionMode: Auto-accept file edits without prompting
        // - extraArgs: Required to receive user message UUIDs in the stream
        const opts = {
          enableFileCheckpointing: true,
          permissionMode: "acceptEdits" as const,
          extraArgs: { "replay-user-messages": null }
        };

        let sessionId: string | undefined; // Store the session ID for resuming
        let checkpointId: string | undefined; // Store the user message UUID for rewinding

        console.log("Running agent to add doc comments to utils.ts...\n");

        // Run the agent and capture checkpoint data from the response stream
        const response = query({
          prompt: "Add doc comments to utils.ts",
          options: opts
        });

        try {
          for await (const message of response) {
            // Capture the first user message UUID - this is our restore point
            if (message.type === "user" && message.uuid && !checkpointId) {
              checkpointId = message.uuid;
            }
            // Capture the session ID so we can resume later
            if ("session_id" in message) {
              sessionId = message.session_id;
            }
          }
        } catch (error) {
          // A single-shot query() throws after yielding an error result. If the
          // failure was an error result, checkpointId and sessionId were already
          // captured by the loop above; connection or process failures yield no
          // result message.
          console.error(`Session ended with an error: ${error}`);
        }

        console.log("Done! Open utils.ts to see the added doc comments.\n");

        // Ask the user if they want to rewind the changes
        if (checkpointId && sessionId) {
          const rl = readline.createInterface({
            input: process.stdin,
            output: process.stdout
          });

          const answer = await new Promise<string>((resolve) => {
            rl.question("Rewind to remove the doc comments? (y/n): ", resolve);
          });
          rl.close();

          if (answer.toLowerCase() === "y") {
            // Resume the session with an empty prompt, then rewind
            const rewindQuery = query({
              prompt: "", // Empty prompt opens the connection
              options: { ...opts, resume: sessionId }
            });

            for await (const msg of rewindQuery) {
              await rewindQuery.rewindFiles(checkpointId); // Restore files
              break;
            }

            console.log("\n✓ File restored! Open utils.ts to verify the doc comments are gone.");
          } else {
            console.log("\nKept the modified file.");
          }
        }
      }

      main();
      ```
    </CodeGroup>

    此示例演示了完整的检查点工作流程：

    1. **启用检查点功能**：使用 `enable_file_checkpointing=True` 和 `permission_mode="acceptEdits"` 配置 SDK 以自动批准文件编辑
    2. **捕获检查点数据**：在代理运行时，存储第一条用户消息的 UUID（即你的恢复点）和会话 ID
    3. **提示是否回退**：代理完成后，检查你的工具文件查看文档注释，然后决定是否要撤销这些更改
    4. **恢复并回退**：如果选择是，则以空提示恢复会话，并调用 `rewind_files()` 恢复原始文件
  </Step>

  <Step title="运行示例">
    在与你的工具文件相同的目录中运行脚本。

    <Tip>
      在运行脚本之前，请在 IDE 或编辑器中打开你的工具文件（`utils.py` 或 `utils.ts`）。你将看到文件随着代理添加文档注释而实时更新，然后在选择回退时恢复为原始状态。
    </Tip>

    <Tabs>
      <Tab title="Python">
        ```bash theme={null}
        python try_checkpointing.py
        ```
      </Tab>

      <Tab title="TypeScript">
        ```bash theme={null}
        npx tsx try_checkpointing.ts
        ```
      </Tab>
    </Tabs>

    你将看到代理添加文档注释，然后出现提示询问是否要回退。如果选择是，文件将恢复为原始状态。
  </Step>
</Steps>

## 限制

文件检查点具有以下限制：

| 限制                         | 说明                                                          |
| ---------------------------------- | -------------------------------------------------------------------- |
| 仅限 Write/Edit/NotebookEdit 工具 | 通过 Bash 命令所做的更改不会被跟踪                   |
| 同一会话                       | 检查点与创建它们的会话绑定                |
| 仅限文件内容                  | 回退不会撤销目录的创建、移动或删除 |
| 本地文件                        | 远程或网络文件不会被跟踪                              |

## 故障排除

### 检查点选项无法识别

如果 `enableFileCheckpointing` 或 `rewindFiles()` 不可用，你可能在使用较旧的 SDK 版本。

**解决方案**：更新到最新的 SDK 版本：

* **Python**：`pip install --upgrade claude-agent-sdk`
* **TypeScript**：`npm install @anthropic-ai/claude-agent-sdk@latest`

### 用户消息没有 UUID

如果 `message.uuid` 为 `undefined` 或缺失，说明你没有收到检查点 UUID。

**原因**：未设置 `replay-user-messages` 选项。

**解决方案**：在你的选项中添加 `extra_args={"replay-user-messages": None}`（Python）或 `extraArgs: { 'replay-user-messages': null }`（TypeScript）。

### "No file checkpoint found for message" 错误

当指定的用户消息 UUID 不存在检查点数据时，会出现此错误。

**常见原因**：

* 原始会话未启用文件检查点功能（`enable_file_checkpointing` 或 `enableFileCheckpointing` 未设置为 `true`）
* 在尝试恢复和回退之前，会话未正确完成

**解决方案**：确保在原始会话上设置了 `enable_file_checkpointing=True`（Python）或 `enableFileCheckpointing: true`（TypeScript），然后使用示例中展示的模式：捕获第一条用户消息的 UUID，完整完成会话，然后使用空提示恢复并调用一次 `rewindFiles()`。

### "File rewinding is not enabled" 错误

当您在未启用检查点的情况下尝试非交互式回退时，会出现此错误：运行带有 `--rewind-files` 的裸 `claude -p`，或运行其选项未启用检查点的 SDK 会话（包括恢复的会话）。仅当在执行回退的会话上启用了 `enable_file_checkpointing`（Python）或 `enableFileCheckpointing`（TypeScript）时，SDK 才会在内部设置 `CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING` 环境变量；裸 CLI 从不设置它。

**解决方案**：对于裸 CLI，在运行命令时设置环境变量：

```bash theme={null}
CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING=true claude -p --resume <session-id> --rewind-files <checkpoint-uuid>
```

对于 SDK，在恢复的会话上设置 `enable_file_checkpointing=True`（Python）或 `enableFileCheckpointing: true`（TypeScript），如本页示例所示。

### "ProcessTransport is not ready for writing" 错误

当您在完成响应迭代后调用 `rewindFiles()` 或 `rewind_files()` 时，会出现此错误。循环完成时，与 CLI 进程的连接会关闭。

**解决方案**：使用空提示恢复会话，然后在新查询上调用回退：

<CodeGroup>
  ```python Python theme={null}
  # Resume session with empty prompt, then rewind
  async with ClaudeSDKClient(
      ClaudeAgentOptions(enable_file_checkpointing=True, resume=session_id)
  ) as client:
      await client.query("")
      async for message in client.receive_response():
          if checkpoint_id:
              await client.rewind_files(checkpoint_id)
          break
  ```

  ```typescript TypeScript theme={null}
  // Resume session with empty prompt, then rewind
  const rewindQuery = query({
    prompt: "",
    options: { ...opts, resume: sessionId }
  });

  try {
    for await (const msg of rewindQuery) {
      if (checkpointId) {
        await rewindQuery.rewindFiles(checkpointId);
      }
      break;
    }
  } catch (error) {
    // An error here means the rewind didn't complete, for example the checkpoint
    // wasn't found or the session couldn't be resumed.
    console.error(`Rewind session ended with an error: ${error}`);
  }
  ```
</CodeGroup>

## 后续步骤

* **[会话](/docs/en/agent-sdk/sessions)**：了解如何恢复会话，这是在流完成后回退所必需的。涵盖会话 ID、恢复对话和会话分叉。
* **[权限](/docs/en/agent-sdk/permissions)**：配置 Claude 可以使用哪些工具以及如何批准文件修改。如果您想更好地控制编辑何时发生，这会很有用。
* **[TypeScript SDK 参考](/docs/en/agent-sdk/typescript)**：完整的 API 参考，包括 `query()` 的所有选项和 `rewindFiles()` 方法。
* **[Python SDK 参考](/docs/en/agent-sdk/python)**：完整的 API 参考，包括 `ClaudeAgentOptions` 的所有选项和 `rewind_files()` 方法。

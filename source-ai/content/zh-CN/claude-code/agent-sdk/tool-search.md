---
title: 使用工具搜索扩展到大量工具
source_id: claude-code/agent-sdk/tool-search
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/agent-sdk/tool-search
owner: Anthropic
content_sha256: 92e7582fd652e96cee0c04ef47872309c777a72129280dbdf29374668541c35f
translation_of: claude-code/agent-sdk/tool-search
translation_model: gpt-5.6
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/agent-sdk/tool-search)

Content owner: Anthropic

> ## 文档索引
> 完整的文档索引位于：https://code.claude.com/docs/llms.txt
> 在进一步探索之前，可使用此文件发现所有可用页面。

# 使用工具搜索扩展到大量工具

> 通过按需发现并仅加载所需工具，让你的智能体扩展到数千种工具。

工具搜索使智能体能够处理数百乃至数千种工具，方法是动态发现工具并按需加载。智能体不会预先将所有工具定义加载到上下文窗口中，而是搜索你的工具目录，只加载所需工具。

随着工具库规模扩大，这种方法可以解决两个难题：

* **上下文效率：** 工具定义可能占用上下文窗口的很大一部分（50 个工具可消耗 10-20K 个令牌），留给实际工作的空间会因此减少。
* **工具选择准确率：** 一次加载超过 30-50 个工具时，工具选择准确率会下降。

工具搜索默认启用。

## 工具搜索的工作原理

工具搜索处于活动状态时，工具定义不会放入上下文窗口。智能体会收到可用工具的摘要；当任务需要尚未加载的能力时，它会搜索相关工具。默认情况下，最多会将五个最相关的工具加载到上下文中，并在后续轮次中保持可用。如果对话足够长，以至于 SDK 为释放空间而压缩较早的消息，先前发现的工具可能会被移除；智能体会在需要时再次搜索。

Claude 首次发现工具时，工具搜索会增加一次额外的往返（搜索步骤）；但对于大型工具集，每轮上下文更小所带来的收益可以抵消这项成本。工具少于 \~10 个时，预先加载全部工具通常更快。

有关底层 API 机制的详细信息，请参阅 [API 中的工具搜索](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool)。

<Note>
  Claude Sonnet 4.5、Claude Haiku 4.5、Claude Opus 4.5 及更高版本的模型支持工具搜索；当前列表请参阅 [API 文档中的模型兼容性](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool#model-compatibility)。在 Google Cloud 的 Agent Platform 上，最低支持的模型为 Claude Sonnet 4.5 和 Claude Opus 4.5。
</Note>

## 配置工具搜索

工具搜索默认开启。在 Google Cloud 的 Agent Platform 上则默认禁用；该平台从 Claude Sonnet 4.5 及更高版本和 Claude Opus 4.5 及更高版本开始支持工具搜索。当 `ANTHROPIC_BASE_URL` 指向非第一方主机时，工具搜索也会禁用，因为大多数代理不会转发 `tool_reference` 块。你可以使用 `ENABLE_TOOL_SEARCH` 环境变量覆盖任一默认行为：

| 值    | 行为                                                                                                                                                                                                                                                                 |
| :------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| （未设置）  | 工具搜索开启。工具定义会延迟加载并按需发现。在 Google Cloud 的 Agent Platform 或非第一方 `ANTHROPIC_BASE_URL` 上，回退为预先加载。                                                                                     |
| `true`   | 工具搜索始终开启。即使通过 Google Cloud 的 Agent Platform 和代理，SDK 也会发送 beta 标头。如果 Google Cloud 的 Agent Platform 模型早于 Sonnet 4.5 或 Opus 4.5，或者代理不支持 `tool_reference` 块，请求会失败。 |
| `auto`   | 检查所有工具定义的合计令牌数相对于模型上下文窗口的占比。如果超过 10%，则激活工具搜索；如果低于 10%，则照常将所有工具加载到上下文。                                                                 |
| `auto:N` | 与 `auto` 相同，但可使用自定义百分比。工具定义超过上下文窗口的 5% 时，`auto:5` 会激活。值越低，激活越早。                                                                                                                         |
| `false`  | 工具搜索关闭。每轮都会将所有工具定义加载到上下文中。                                                                                                                                                                                          |

设置 [`CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS`](/docs/en/env-vars) 会让工具搜索保持关闭，`ENABLE_TOOL_SEARCH` 无法覆盖它。该变量会移除 `defer_loading` 工具定义和 `tool_reference` 内容块所需的 beta 标头。

工具搜索适用于所有已注册工具，无论它们来自远程 MCP 服务器，还是[自定义 SDK MCP 服务器](/docs/en/agent-sdk/custom-tools)。使用 `auto` 时，阈值以所有服务器上的全部工具定义合计大小为准。

在 `env` 选项中设置该值，该选项属于 `query()`。在 TypeScript 中，`env` 会替换子进程环境，因此请展开 `...process.env` 以保留继承的变量。在 Python 中，`env` 会合并到继承的环境之上。以下示例连接到公开大量工具的远程 MCP 服务器，使用通配符预先批准所有工具，并使用 `auto:5`，使工具定义超过上下文窗口的 5% 时激活工具搜索：

<CodeGroup>
  ```typescript TypeScript theme={null}
  import { query } from "@anthropic-ai/claude-agent-sdk";

  try {
    for await (const message of query({
      prompt: "Find and run the appropriate database query",
      options: {
        mcpServers: {
          "enterprise-tools": {
            // Connect to a remote MCP server
            type: "http",
            url: "https://tools.example.com/mcp"
          }
        },
        allowedTools: ["mcp__enterprise-tools__*"], // Wildcard pre-approves all tools from this server
        env: {
          ...process.env, // env replaces the subprocess environment, so keep inherited variables
          ENABLE_TOOL_SEARCH: "auto:5" // Activate tool search when tools exceed 5% of context
        }
      }
    })) {
      if (message.type === "result" && message.subtype === "success") {
        console.log(message.result);
      }
    }
  } catch (error) {
    // A single-shot query() throws after yielding an error result
    console.log(`Session ended with an error: ${error}`);
  }
  ```

  ```python Python theme={null}
  import asyncio
  from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage


  async def main():
      options = ClaudeAgentOptions(
          mcp_servers={
              "enterprise-tools": {
                  "type": "http",
                  "url": "https://tools.example.com/mcp",
              }
          },
          allowed_tools=[
              "mcp__enterprise-tools__*"
          ],  # Wildcard pre-approves all tools from this server
          env={
              "ENABLE_TOOL_SEARCH": "auto:5"  # Activate tool search when tools exceed 5% of context
          },
      )

      try:
          async for message in query(
              prompt="Find and run the appropriate database query",
              options=options,
          ):
              if isinstance(message, ResultMessage) and message.subtype == "success":
                  print(message.result)
      except Exception as error:
          # A single-shot query() raises after yielding an error result
          print(f"Session ended with an error: {error}")


  asyncio.run(main())
  ```
</CodeGroup>

若要运行此示例，请将 `https://tools.example.com/mcp` 替换为你自己的 MCP 服务器 URL。成功后，结果文本会输出到控制台。

由于这是一次性 `query()` 调用，SDK 会在生成错误结果后抛出异常，因此示例使用 try 块封装循环。若要查看运行失败的原因，请在循环中检查结果消息的 `subtype`，例如 `error_during_execution`。有关结果消息的更多信息，请参阅[处理结果](/docs/en/agent-sdk/agent-loop#handle-the-result)。

将 `ENABLE_TOOL_SEARCH` 设置为 `"false"` 会禁用工具搜索，并在每轮中将所有工具定义加载到上下文。这会省去搜索往返；当工具集较小（少于 \~10 个工具）且定义可以轻松放入上下文窗口时，这样可能更快。

## 优化工具发现

搜索机制会将查询与工具名称和描述进行匹配。`search_slack_messages` 这类名称比 `query_slack` 更容易出现在各种请求中。包含具体关键字的描述（“Search Slack messages by keyword, channel, or date range”）比笼统描述（“Query Slack”）能匹配更多查询。

你还可以添加一个列出可用工具类别的系统提示部分。这能为智能体提供上下文，使其了解可搜索的工具类型。在 TypeScript 中通过 `systemPrompt` 选项传入文本，在 Python 中则通过 `system_prompt`；使用 `claude_code` 预设并配合 `append`，这会把你的文本添加到预设提示中，而不是替换它：

<CodeGroup>
  ```typescript TypeScript theme={null}
  options: {
    systemPrompt: {
      type: "preset",
      preset: "claude_code",
      append: "You can search for tools to interact with Slack, GitHub, and Jira."
    }
  }
  ```

  ```python Python theme={null}
  options = ClaudeAgentOptions(
      system_prompt={
          "type": "preset",
          "preset": "claude_code",
          "append": "You can search for tools to interact with Slack, GitHub, and Jira.",
      }
  )
  ```
</CodeGroup>

有关完整的系统提示选项，请参阅[修改系统提示](/docs/en/agent-sdk/modifying-system-prompts)。

## 限制

* **工具上限：** 工具目录中最多 10,000 个工具
* **搜索结果：** 默认情况下，每次搜索最多返回五个最相关的工具
* **模型支持：** Claude Sonnet 4.5、Claude Haiku 4.5、Claude Opus 4.5 及更高版本的模型；当前列表请参阅 [API 文档中的模型兼容性](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool#model-compatibility)。在 Google Cloud 的 Agent Platform 上，支持 Claude Sonnet 4.5 及更高版本和 Claude Opus 4.5 及更高版本。

## 相关文档

* [API 中的工具搜索](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool)：完整的工具搜索 API 文档，包括自定义实现
* [连接 MCP 服务器](/docs/en/agent-sdk/mcp)：通过 MCP 服务器连接外部工具
* [自定义工具](/docs/en/agent-sdk/custom-tools)：使用 SDK MCP 服务器构建自己的工具
* [TypeScript SDK 参考](/docs/en/agent-sdk/typescript)：完整 API 参考
* [Python SDK 参考](/docs/en/agent-sdk/python)：完整 API 参考

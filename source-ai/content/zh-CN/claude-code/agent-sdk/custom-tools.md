---
title: 为 Claude 提供自定义工具
source_id: claude-code/agent-sdk/custom-tools
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/agent-sdk/custom-tools
owner: Anthropic
content_sha256: 0ce3287c56927e8c76b6cff678fcc65e9f4c6f686c609a5c64d629806152023c
translation_of: claude-code/agent-sdk/custom-tools
translation_model: k3
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/agent-sdk/custom-tools)

Content owner: Anthropic

> ## 文档索引
> 在此获取完整的文档索引：https://code.claude.com/docs/llms.txt
> 在进一步探索之前，使用此文件来发现所有可用的页面。

# 为 Claude 提供自定义工具

> 使用 Claude Agent SDK 的进程内 MCP 服务器定义自定义工具，让 Claude 可以调用你的函数、访问你的 API，并执行特定领域的操作。

自定义工具通过让你定义自己的函数来扩展 Agent SDK，Claude 可以在对话期间调用这些函数。利用 SDK 的进程内 MCP 服务器，你可以让 Claude 访问数据库、外部 API、特定领域的逻辑，或你的应用所需的任何其他能力。

本指南介绍如何使用输入模式和处理程序定义工具，将它们打包到 MCP 服务器中，传递给 `query`，并控制 Claude 可以访问哪些工具。它还涵盖错误处理、工具注解，以及返回图像等非文本内容。

## 快速参考

| 如果你想要……                              | 这样做                                                                                                                                                                                                       |
| :------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 定义一个工具                                | 使用 [`@tool`](/docs/en/agent-sdk/python#tool)（Python）或 [`tool()`](/docs/en/agent-sdk/typescript#tool)（TypeScript），并指定名称、描述、模式和处理程序。参见 [创建自定义工具](#create-a-custom-tool)。 |
| 向 Claude 注册工具                          | 包装在 `create_sdk_mcp_server` / `createSdkMcpServer` 中，并在 `mcpServers` 中传递给 `query()`。参见 [调用自定义工具](#call-a-custom-tool)。                                                                  |
| 预先批准一个工具                            | 将其添加到你的允许工具列表中。参见 [配置允许的工具](#configure-allowed-tools)。                                                                                                                           |
| 从 Claude 的上下文中移除内置工具            | 传递一个 `tools` 数组，只列出你想要的内置工具。参见 [配置允许的工具](#configure-allowed-tools)。                                                                                            |
| 让 Claude 并行调用工具                      | 在无副作用的工具上设置 `readOnlyHint: true`。参见 [添加工具注解](#add-tool-annotations)。                                                                                                    |
| 控制 Claude 读取的错误消息                  | 返回 `isError: true` 来自行组织消息，而不是暴露原始异常。参见 [处理错误](#handle-errors)。                                                                                    |
| 返回图像或文件                              | 在内容数组中使用 `image` 或 `resource` 块。参见 [返回图像和资源](#return-images-and-resources)。                                                                                       |
| 返回机器可读的 JSON 结果                    | 在结果上设置 `structuredContent`。参见 [返回结构化数据](#return-structured-data)。                                                                                                                 |
| 扩展到大量工具                              | 使用 [工具搜索](/docs/en/agent-sdk/tool-search) 按需加载工具。                                                                                                                                         |

## 创建自定义工具

一个工具由四个部分定义,它们作为参数传递给 TypeScript 中的 [`tool()`](/docs/en/agent-sdk/typescript#tool) 辅助函数,或 Python 中的 [`@tool`](/docs/en/agent-sdk/python#tool) 装饰器:

* **名称:** Claude 用来调用该工具的唯一标识符。
* **描述:** 该工具的功能。Claude 会读取此描述来决定何时调用它。
* **输入模式:** Claude 必须提供的参数。在 TypeScript 中,这始终是一个 [Zod 模式](https://zod.dev/),处理程序的 `args` 会根据它自动进行类型推导。在 Python 中,这是一个将名称映射到类型的字典,例如 `{"latitude": float}`,SDK 会为你将其转换为 JSON Schema。当你需要枚举、范围、可选字段或嵌套对象时,Python 装饰器也直接接受完整的 [JSON Schema](https://json-schema.org/understanding-json-schema/about) 字典。
* **处理程序:** 当 Claude 调用该工具时运行的异步函数。它接收经过验证的参数,并且必须返回一个包含以下内容的对象:
  * `content`(必需):结果块的数组,每个块的 `type` 为 `"text"`、`"image"`、`"audio"`、`"resource"` 或 `"resource_link"`。有关非文本块,请参阅 [返回图像和资源](#return-images-and-resources)。
  * `structuredContent`(可选):一个 JSON 对象,以机器可读数据的形式保存结果,与 `content` 一起返回。请参阅 [返回结构化数据](#return-structured-data)。
  * `isError`(可选):设置为 `true` 以表示工具失败,以便 Claude 可以对其做出反应。请参阅 [处理错误](#handle-errors)。

定义工具后,使用 [`createSdkMcpServer`](/docs/en/agent-sdk/typescript#createsdkmcpserver)(TypeScript)或 [`create_sdk_mcp_server`](/docs/en/agent-sdk/python#create_sdk_mcp_server)(Python)将其包装在服务器中。该服务器在你的应用程序内部以进程内方式运行,而不是作为单独的进程。

### 天气工具示例

此示例定义了一个 `get_temperature` 工具并将其包装在 MCP 服务器中。它仅设置该工具;要将其传递给 `query` 并运行它,请参阅下方的 [调用自定义工具](#call-a-custom-tool)。

<CodeGroup>
  ```python Python theme={null}
  from typing import Any
  import httpx
  from claude_agent_sdk import tool, create_sdk_mcp_server


  # Define a tool: name, description, input schema, handler
  @tool(
      "get_temperature",
      "Get the current temperature at a location",
      {"latitude": float, "longitude": float},
  )
  async def get_temperature(args: dict[str, Any]) -> dict[str, Any]:
      async with httpx.AsyncClient() as client:
          response = await client.get(
              "https://api.open-meteo.com/v1/forecast",
              params={
                  "latitude": args["latitude"],
                  "longitude": args["longitude"],
                  "current": "temperature_2m",
                  "temperature_unit": "fahrenheit",
              },
          )
          data = response.json()

      # Return a content array - Claude sees this as the tool result
      return {
          "content": [
              {
                  "type": "text",
                  "text": f"Temperature: {data['current']['temperature_2m']}°F",
              }
          ]
      }


  # Wrap the tool in an in-process MCP server
  weather_server = create_sdk_mcp_server(
      name="weather",
      version="1.0.0",
      tools=[get_temperature],
  )
  ```

  ```typescript TypeScript theme={null}
  import { tool, createSdkMcpServer } from "@anthropic-ai/claude-agent-sdk";
  import { z } from "zod";

  // Define a tool: name, description, input schema, handler
  const getTemperature = tool(
    "get_temperature",
    "Get the current temperature at a location",
    {
      latitude: z.number().describe("Latitude coordinate"), // .describe() adds a field description Claude sees
      longitude: z.number().describe("Longitude coordinate")
    },
    async (args) => {
      // args is typed from the schema: { latitude: number; longitude: number }
      const response = await fetch(
        `https://api.open-meteo.com/v1/forecast?latitude=${args.latitude}&longitude=${args.longitude}&current=temperature_2m&temperature_unit=fahrenheit`
      );
      const data: any = await response.json();

      // Return a content array - Claude sees this as the tool result
      return {
        content: [{ type: "text", text: `Temperature: ${data.current.temperature_2m}°F` }]
      };
    }
  );

  // Wrap the tool in an in-process MCP server
  const weatherServer = createSdkMcpServer({
    name: "weather",
    version: "1.0.0",
    tools: [getTemperature]
  });
  ```
</CodeGroup>

完整的参数细节（包括 JSON Schema 输入格式和返回值结构）请参阅 [`tool()`](/docs/en/agent-sdk/typescript#tool) TypeScript 参考或 [`@tool`](/docs/en/agent-sdk/python#tool) Python 参考。

<Tip>
  要使某个参数变为可选：在 TypeScript 中，向 Zod 字段添加 `.default()`。在 Python 中，dict 模式将每个键都视为必填，因此请将该参数从模式中省略，在描述字符串中提及它，并在处理程序中用 `args.get()` 读取它。下面的 [`get_precipitation_chance` 工具](#add-more-tools) 展示了这两种模式。
</Tip>

### 调用自定义工具

通过 `mcpServers` 选项将您创建的 MCP 服务器传递给 `query`。`mcpServers` 中的键将成为 `{server_name}` 段，位于每个工具的完全限定名称中：`mcp__{server_name}__{tool_name}`。在 `allowedTools` 中列出该名称，以便工具运行时无需权限提示。

这些片段复用来自[上面的示例](#weather-tool-example)的 `weatherServer`，以询问 Claude 特定位置的天气。

<CodeGroup>
  ```python Python theme={null}
  import asyncio
  from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage


  async def main():
      options = ClaudeAgentOptions(
          mcp_servers={"weather": weather_server},
          allowed_tools=["mcp__weather__get_temperature"],
      )

      async for message in query(
          prompt="What's the temperature in San Francisco?",
          options=options,
      ):
          # ResultMessage is the final message after all tool calls complete
          if isinstance(message, ResultMessage) and message.subtype == "success":
              print(message.result)


  asyncio.run(main())
  ```

  ```typescript TypeScript theme={null}
  import { query } from "@anthropic-ai/claude-agent-sdk";

  for await (const message of query({
    prompt: "What's the temperature in San Francisco?",
    options: {
      mcpServers: { weather: weatherServer },
      allowedTools: ["mcp__weather__get_temperature"]
    }
  })) {
    // "result" is the final message after all tool calls complete
    if (message.type === "result" && message.subtype === "success") {
      console.log(message.result);
    }
  }
  ```
</CodeGroup>

将此代码片段与 [天气工具示例](#weather-tool-example) 中的工具和服务器定义合并到一个文件中,然后使用 `python weather.py`(Python)或 `npx tsx weather.ts`(TypeScript)运行它。Claude 会调用 `get_temperature`,脚本会打印一行包含旧金山当前温度的答案。

### 添加更多工具

服务器会包含你在其 `tools` 数组中列出的所有工具。当服务器上有多个工具时，你可以在 `allowedTools` 中逐个列出每个工具，或使用通配符 `mcp__weather__*` 来涵盖服务器公开的每一个工具。

下面的示例定义了第二个工具，`get_precipitation_chance`，并将 [天气工具示例](#weather-tool-example) 中原本的 `weatherServer` 定义替换为一个在数组中同时列出两个工具的定义。

<CodeGroup>
  ```python Python theme={null}
  # Define a second tool for the same server
  @tool(
      "get_precipitation_chance",
      "Get the hourly precipitation probability for a location. "
      "Optionally pass 'hours' (1-24) to control how many hours to return.",
      {"latitude": float, "longitude": float},
  )
  async def get_precipitation_chance(args: dict[str, Any]) -> dict[str, Any]:
      # 'hours' isn't in the schema - read it with .get() to make it optional
      hours = args.get("hours", 12)
      async with httpx.AsyncClient() as client:
          response = await client.get(
              "https://api.open-meteo.com/v1/forecast",
              params={
                  "latitude": args["latitude"],
                  "longitude": args["longitude"],
                  "hourly": "precipitation_probability",
                  "forecast_days": 1,
              },
          )
          data = response.json()
      chances = data["hourly"]["precipitation_probability"][:hours]

      return {
          "content": [
              {
                  "type": "text",
                  "text": f"Next {hours} hours: {'%, '.join(map(str, chances))}%",
              }
          ]
      }


  # Rebuild the server with both tools in the array
  weather_server = create_sdk_mcp_server(
      name="weather",
      version="1.0.0",
      tools=[get_temperature, get_precipitation_chance],
  )
  ```

  ```typescript TypeScript theme={null}
  // Define a second tool for the same server
  const getPrecipitationChance = tool(
    "get_precipitation_chance",
    "Get the hourly precipitation probability for a location",
    {
      latitude: z.number(),
      longitude: z.number(),
      hours: z
        .number()
        .int()
        .min(1)
        .max(24)
        .default(12) // .default() makes the parameter optional
        .describe("How many hours of forecast to return")
    },
    async (args) => {
      const response = await fetch(
        `https://api.open-meteo.com/v1/forecast?latitude=${args.latitude}&longitude=${args.longitude}&hourly=precipitation_probability&forecast_days=1`
      );
      const data: any = await response.json();
      const chances = data.hourly.precipitation_probability.slice(0, args.hours);

      return {
        content: [{ type: "text", text: `Next ${args.hours} hours: ${chances.join("%, ")}%` }]
      };
    }
  );

  // Rebuild the server with both tools in the array
  const weatherServer = createSdkMcpServer({
    name: "weather",
    version: "1.0.0",
    tools: [getTemperature, getPrecipitationChance]
  });
  ```
</CodeGroup>

[工具搜索](/docs/en/agent-sdk/tool-search) 默认启用，并会延迟加载 SDK MCP 工具：Claude 会在紧凑列表中看到每个工具的名称，并按需加载其完整模式。禁用工具搜索后，此数组中的每个工具都会在每一轮中占用上下文窗口空间。在 TypeScript 中，在 [`tool()`](/docs/en/agent-sdk/typescript#tool) 的 `extras` 参数中或在 [`createSdkMcpServer()`](/docs/en/agent-sdk/typescript#createsdkmcpserver) 的选项中传递 `alwaysLoad: true`，以在初始提示词中保留工具的完整模式。

### 添加工具注解

[工具注解](https://modelcontextprotocol.io/docs/concepts/tools#tool-annotations)是描述工具行为的可选元数据。在 TypeScript 中将它们作为第五个参数传递给 `tool()` 辅助函数，或在 Python 中通过 `annotations` 关键字参数传递给 `@tool` 装饰器。所有提示字段都是布尔值。

| 字段             | 默认值 | 含义                                                                                                               |
| :---------------- | :------ | :-------------------------------------------------------------------------------------------------------------------- |
| `readOnlyHint`    | `false` | 工具不修改其环境。控制该工具是否可以与其他只读工具并行调用。 |
| `destructiveHint` | `true`  | 工具可能执行破坏性更新。仅供参考。                                                             |
| `idempotentHint`  | `false` | 使用相同参数重复调用不会产生额外效果。仅供参考。                                 |
| `openWorldHint`   | `true`  | 工具会访问进程外部的系统。仅供参考。                                                        |

注解是元数据，而非强制执行。标记为 `readOnlyHint: true` 的工具，如果处理程序实际执行的是写操作，仍可以写入磁盘。请保持注解与处理程序的行为一致。

此示例将 `readOnlyHint` 添加到来自[天气工具示例](#weather-tool-example)的 `get_temperature` 工具。

<CodeGroup>
  ```python Python theme={null}
  from claude_agent_sdk import tool, ToolAnnotations


  @tool(
      "get_temperature",
      "Get the current temperature at a location",
      {"latitude": float, "longitude": float},
      annotations=ToolAnnotations(
          readOnlyHint=True
      ),  # Lets Claude batch this with other read-only calls
  )
  async def get_temperature(args):
      return {"content": [{"type": "text", "text": "..."}]}
  ```

  ```typescript TypeScript theme={null}
  import { tool } from "@anthropic-ai/claude-agent-sdk";
  import { z } from "zod";

  tool(
    "get_temperature",
    "Get the current temperature at a location",
    { latitude: z.number(), longitude: z.number() },
    async (args) => ({ content: [{ type: "text", text: `...` }] }),
    { annotations: { readOnlyHint: true } } // Lets Claude batch this with other read-only calls
  );
  ```
</CodeGroup>

参见 `ToolAnnotations` 的 [TypeScript](/docs/en/agent-sdk/typescript#toolannotations) 或 [Python](/docs/en/agent-sdk/python#toolannotations) 参考。

## 控制工具访问

[天气工具示例](#weather-tool-example) 注册了一个服务器，并在 `allowedTools` 中列出了工具。本节介绍工具名称是如何构造的，以及当你拥有多个工具或想要限制内置工具时如何限定访问范围。

### 工具名称格式

当 MCP 工具暴露给 Claude 时，它们的名称遵循特定的格式：

* 模式： `mcp__{server_name}__{tool_name}`
* 示例：服务器 `weather` 中名为 `get_temperature` 的工具会变成 `mcp__weather__get_temperature`

### 配置允许的工具

`tools` 选项和允许/禁止列表影响两个层面：可用性（控制某个工具是否出现在 Claude 的上下文中）和权限（控制 Claude 尝试调用时该调用是否被批准）。`tools` 和裸名称的 `disallowedTools` 条目会改变可用性。`allowedTools` 和带作用域的 `disallowedTools` 规则只改变权限。

| 选项                    | 层面        | 效果                                                                                                                                                                                                          |
| :------------------------ | :----------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `tools: ["Read", "Grep"]` | 可用性 | 只有列出的内置工具会出现在 Claude 的上下文中。未列出的内置工具会被移除。MCP 工具不受影响。                                                                                                    |
| `tools: []`               | 可用性 | 所有内置工具都会被移除。Claude 只能使用你的 MCP 工具。                                                                                                                                                  |
| 允许的工具             | 权限   | 列出的工具运行时不会弹出权限提示。未列出的工具仍然可用；调用会经过[权限流程](/docs/en/agent-sdk/permissions)。                                                               |
| 禁止的工具          | 两者         | 像 `"Bash"` 这样的裸工具名称会将该工具从 Claude 的上下文中移除，效果等同于将其从 `tools` 中省略。像 `"Bash(rm *)"` 这样的带作用域规则会将工具保留在上下文中，只拒绝匹配的调用。|

要完全移除某个内置工具，请将其从 `tools` 中省略，或在 `disallowedTools` 中列出其裸名称（Python：`disallowed_tools`）；两者都会让该工具远离上下文，使 Claude 永远不会尝试它。带作用域的 `disallowedTools` 规则会阻止匹配的调用，但工具仍然可见，因此 Claude 可能会浪费一轮来尝试它。完整的评估顺序请参阅[配置权限](/docs/en/agent-sdk/permissions)。

## 错误处理

处理程序错误不会停止智能体循环。SDK 的进程内 MCP 服务器会捕获未处理的异常并将其作为错误结果返回，因此你报告错误的方式决定了 Claude 读到的内容，而不是查询是否失败：

| 发生的情况                                                                             | 结果                                                                                                                                    |
| :--------------------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------- |
| 处理程序抛出未捕获的异常                                                     | MCP 服务器将其转换为携带原始异常消息的错误结果。Claude 会看到该消息，智能体循环继续进行。 |
| 处理程序捕获错误并返回 `isError: true`（TS）/ `"is_error": True`（Python） | Claude 会看到你编写的消息。你可以添加原始异常所缺少的上下文，例如哪个请求失败了或接下来该尝试什么。    |

在这两种情况下，Claude 都可以重试、尝试其他工具或解释失败原因。当原始异常消息不足以让 Claude 采取行动时，请自行捕获错误。

下面的示例在处理程序内部捕获了两种失败情况，并编写了 Claude 读到的错误消息。非 200 的 HTTP 状态码会从响应中被捕获并作为错误结果返回。网络错误或无效 JSON 会被外层的 `try/except`（Python）或 `try/catch`（TypeScript）捕获，同样作为错误结果返回。在这两种情况下，Claude 收到的都是描述失败情况的消息，而不是光秃秃的异常字符串。

<CodeGroup>
  ```python Python theme={null}
  import json
  import httpx
  from typing import Any
  from claude_agent_sdk import tool

  from claude_agent_sdk import tool


  @tool(
      "fetch_data",
      "Fetch data from an API",
      {"endpoint": str},  # Simple schema
  )
  async def fetch_data(args: dict[str, Any]) -> dict[str, Any]:
      try:
          async with httpx.AsyncClient() as client:
              response = await client.get(args["endpoint"])
              if response.status_code != 200:
                  # Return the failure as a tool result so Claude can react to it.
                  # is_error marks this as a failed call rather than odd-looking data.
                  return {
                      "content": [
                          {
                              "type": "text",
                              "text": f"API error: {response.status_code} {response.reason_phrase}",
                          }
                      ],
                      "is_error": True,
                  }

              data = response.json()
              return {"content": [{"type": "text", "text": json.dumps(data, indent=2)}]}
      except Exception as e:
          # Composes the message Claude reads. An uncaught exception would
          # reach Claude as the raw str(e) with no context.
          return {
              "content": [{"type": "text", "text": f"Failed to fetch data: {str(e)}"}],
              "is_error": True,
          }
  ```

  ```typescript TypeScript theme={null}
  import { tool } from "@anthropic-ai/claude-agent-sdk";
  import { z } from "zod";

  tool(
    "fetch_data",
    "Fetch data from an API",
    {
      endpoint: z.string().url().describe("API endpoint URL")
    },
    async (args) => {
      try {
        const response = await fetch(args.endpoint);

        if (!response.ok) {
          // Return the failure as a tool result so Claude can react to it.
          // isError marks this as a failed call rather than odd-looking data.
          return {
            content: [
              {
                type: "text",
                text: `API error: ${response.status} ${response.statusText}`
              }
            ],
            isError: true
          };
        }

        const data = await response.json();
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(data, null, 2)
            }
          ]
        };
      } catch (error) {
        // Composes the message Claude reads. An uncaught throw would
        // reach Claude as the raw error message with no context.
        return {
          content: [
            {
              type: "text",
              text: `Failed to fetch data: ${error instanceof Error ? error.message : String(error)}`
            }
          ],
          isError: true
        };
      }
    }
  );
  ```
</CodeGroup>

## 返回图像和资源

工具结果中的 `content` 数组接受 `text`、`image`、`audio`、`resource` 和 `resource_link` 块。你可以在同一个响应中混合使用它们。在 TypeScript 中，音频块会被保存到磁盘，Claude 会收到一个包含已保存文件路径的文本块；在 Python 中，SDK 会从工具结果中丢弃音频块并记录警告。资源链接块会被转换为包含链接名称、URI 和描述的文本块。

### 图像

图像块以内联方式携带图像字节，使用 base64 编码。没有 URL 字段。要返回位于某个 URL 的图像，请在处理程序中获取它，读取响应字节，并在返回前对其进行 base64 编码。结果会作为视觉输入进行处理。

| 字段      | 类型      | 说明                                                                      |
| :--------- | :-------- | :------------------------------------------------------------------------- |
| `type`     | `"image"` |                                                                            |
| `data`     | `string`  | Base64 编码的字节。仅原始 base64，不带 `data:image/...;base64,` 前缀  |
| `mimeType` | `string`  | 必填。例如 `image/png`、`image/jpeg`、`image/webp`、`image/gif` |

<CodeGroup>
  ```python Python theme={null}
  import base64
  import httpx
  from claude_agent_sdk import tool

  from claude_agent_sdk import tool


  # Define a tool that fetches an image from a URL and returns it to Claude
  @tool("fetch_image", "Fetch an image from a URL and return it to Claude", {"url": str})
  async def fetch_image(args):
      async with httpx.AsyncClient() as client:  # Fetch the image bytes
          response = await client.get(args["url"])

      return {
          "content": [
              {
                  "type": "image",
                  "data": base64.b64encode(response.content).decode(
                      "ascii"
                  ),  # Base64-encode the raw bytes
                  "mimeType": response.headers.get(
                      "content-type", "image/png"
                  ),  # Read MIME type from the response
              }
          ]
      }
  ```

  ```typescript TypeScript theme={null}
  import { tool } from "@anthropic-ai/claude-agent-sdk";
  import { z } from "zod";

  tool(
    "fetch_image",
    "Fetch an image from a URL and return it to Claude",
    {
      url: z.string().url()
    },
    async (args) => {
      const response = await fetch(args.url); // Fetch the image bytes
      const buffer = Buffer.from(await response.arrayBuffer()); // Read into a Buffer for base64 encoding
      const mimeType = response.headers.get("content-type") ?? "image/png";

      return {
        content: [
          {
            type: "image",
            data: buffer.toString("base64"), // Base64-encode the raw bytes
            mimeType
          }
        ]
      };
    }
  );
  ```
</CodeGroup>

### 资源

资源块嵌入一段由 URI 标识的内容。URI 是供 Claude 引用的标签；实际内容承载在该块的 `text` 或 `blob` 字段中。当你的工具产出的内容适合稍后按名称引用时（例如生成的文件或来自外部系统的记录），请使用这种方式。

| 字段               | 类型         | 说明                                                                                                                                      |
| :------------------ | :----------- | :----------------------------------------------------------------------------------------------------------------------------------------- |
| `type`              | `"resource"` |                                                                                                                                            |
| `resource.uri`      | `string`     | 内容的标识符。可为任意 URI 方案                                                                                                 |
| `resource.text`     | `string`     | 内容为文本时使用。提供此字段或 `blob`，二者不可同时提供                                                                                |
| `resource.blob`     | `string`     | 内容为二进制时使用 Base64 编码。仅限 TypeScript：Python SDK 会从工具结果中丢弃二进制资源并记录警告 |
| `resource.mimeType` | `string`     | 可选                                                                                                                                   |

此示例展示了从工具处理程序内部返回的资源块。URI `file:///tmp/report.md` 是供 Claude 稍后引用的标签；SDK 不会从该路径读取内容。

<CodeGroup>
  ```typescript TypeScript theme={null}
  return {
    content: [
      {
        type: "resource",
        resource: {
          uri: "file:///tmp/report.md", // Label for Claude to reference, not a path the SDK reads
          mimeType: "text/markdown",
          text: "# Report\n..." // The actual content, inline
        }
      }
    ]
  };
  ```

  ```python Python theme={null}
  return {
      "content": [
          {
              "type": "resource",
              "resource": {
                  "uri": "file:///tmp/report.md",  # Label for Claude to reference, not a path the SDK reads
                  "mimeType": "text/markdown",
                  "text": "# Report\n...",  # The actual content, inline
              },
          }
      ]
  }
  ```
</CodeGroup>

这些块结构来自 MCP 的 `CallToolResult` 类型。完整定义请参阅 [MCP 规范](https://modelcontextprotocol.io/specification/2025-06-18/server/tools#tool-result)。

## 返回结构化数据

`structuredContent` 是结果上一个可选的 JSON 对象，与 `content` 数组分开。使用它返回原始值，让 Claude 可以作为精确字段读取，而不是从文本字符串或图像中解析出来。

设置 `structuredContent` 后，Claude 会接收该 JSON 以及来自 `content` 的任何图像或资源块。`content` 中的文本块不会被转发，因为它们被假定为与结构化数据重复。下面的示例将图表渲染为图像块，并从同一个处理程序在 `structuredContent` 中返回其背后的数据点。在该片段中，`chartPngBuffer` 是一个持有渲染后 PNG 字节的 `Buffer`。

```typescript TypeScript theme={null}
return {
  content: [
    {
      type: "image",
      data: chartPngBuffer.toString("base64"),
      mimeType: "image/png"
    }
  ],
  structuredContent: {
    series: "temperature_2m",
    unit: "fahrenheit",
    points: [62.1, 63.4, 65.0, 64.2]
  }
};
```

<Note>
  Python `@tool` 装饰器只转发处理程序返回字典中的 `content` 和 `is_error`。要从 Python 返回 `structuredContent`，请运行 [独立 MCP 服务器](/docs/en/agent-sdk/mcp)，而不是进程内 SDK 服务器。
</Note>

## 示例：单位转换器

此工具在长度、温度和重量单位之间转换数值。用户可以问“把 100 公里换算成英里”或“72°F 是多少摄氏度”，Claude 会从请求中选择正确的单位类型和单位。

它演示了两种模式：

* **枚举模式：**`unit_type` 被约束为一组固定值。在 TypeScript 中，使用 `z.enum()`。在 Python 中，字典模式不支持枚举，因此需要完整的 JSON Schema 字典。
* **不支持的输入处理：**当找不到转换对时，处理程序返回 `isError: true`，以便 Claude 能告诉用户出了什么问题，而不是把失败当作正常结果。

<CodeGroup>
  ```python Python theme={null}
  from typing import Any
  from claude_agent_sdk import tool, create_sdk_mcp_server


  # z.enum() in TypeScript becomes an "enum" constraint in JSON Schema.
  # The dict schema has no equivalent, so full JSON Schema is required.
  @tool(
      "convert_units",
      "Convert a value from one unit to another",
      {
          "type": "object",
          "properties": {
              "unit_type": {
                  "type": "string",
                  "enum": ["length", "temperature", "weight"],
                  "description": "Category of unit",
              },
              "from_unit": {
                  "type": "string",
                  "description": "Unit to convert from, e.g. kilometers, fahrenheit, pounds",
              },
              "to_unit": {"type": "string", "description": "Unit to convert to"},
              "value": {"type": "number", "description": "Value to convert"},
          },
          "required": ["unit_type", "from_unit", "to_unit", "value"],
      },
  )
  async def convert_units(args: dict[str, Any]) -> dict[str, Any]:
      conversions = {
          "length": {
              "kilometers_to_miles": lambda v: v * 0.621371,
              "miles_to_kilometers": lambda v: v * 1.60934,
              "meters_to_feet": lambda v: v * 3.28084,
              "feet_to_meters": lambda v: v * 0.3048,
          },
          "temperature": {
              "celsius_to_fahrenheit": lambda v: (v * 9) / 5 + 32,
              "fahrenheit_to_celsius": lambda v: (v - 32) * 5 / 9,
              "celsius_to_kelvin": lambda v: v + 273.15,
              "kelvin_to_celsius": lambda v: v - 273.15,
          },
          "weight": {
              "kilograms_to_pounds": lambda v: v * 2.20462,
              "pounds_to_kilograms": lambda v: v * 0.453592,
              "grams_to_ounces": lambda v: v * 0.035274,
              "ounces_to_grams": lambda v: v * 28.3495,
          },
      }

      key = f"{args['from_unit']}_to_{args['to_unit']}"
      fn = conversions.get(args["unit_type"], {}).get(key)

      if not fn:
          return {
              "content": [
                  {
                      "type": "text",
                      "text": f"Unsupported conversion: {args['from_unit']} to {args['to_unit']}",
                  }
              ],
              "is_error": True,
          }

      result = fn(args["value"])
      return {
          "content": [
              {
                  "type": "text",
                  "text": f"{args['value']} {args['from_unit']} = {result:.4f} {args['to_unit']}",
              }
          ]
      }


  converter_server = create_sdk_mcp_server(
      name="converter",
      version="1.0.0",
      tools=[convert_units],
  )
  ```

  ```typescript TypeScript theme={null}
  import { tool, createSdkMcpServer } from "@anthropic-ai/claude-agent-sdk";
  import { z } from "zod";

  const convert = tool(
    "convert_units",
    "Convert a value from one unit to another",
    {
      unit_type: z.enum(["length", "temperature", "weight"]).describe("Category of unit"),
      from_unit: z
        .string()
        .describe("Unit to convert from, e.g. kilometers, fahrenheit, pounds"),
      to_unit: z.string().describe("Unit to convert to"),
      value: z.number().describe("Value to convert")
    },
    async (args) => {
      type Conversions = Record<string, Record<string, (v: number) => number>>;

      const conversions: Conversions = {
        length: {
          kilometers_to_miles: (v) => v * 0.621371,
          miles_to_kilometers: (v) => v * 1.60934,
          meters_to_feet: (v) => v * 3.28084,
          feet_to_meters: (v) => v * 0.3048
        },
        temperature: {
          celsius_to_fahrenheit: (v) => (v * 9) / 5 + 32,
          fahrenheit_to_celsius: (v) => ((v - 32) * 5) / 9,
          celsius_to_kelvin: (v) => v + 273.15,
          kelvin_to_celsius: (v) => v - 273.15
        },
        weight: {
          kilograms_to_pounds: (v) => v * 2.20462,
          pounds_to_kilograms: (v) => v * 0.453592,
          grams_to_ounces: (v) => v * 0.035274,
          ounces_to_grams: (v) => v * 28.3495
        }
      };

      const key = `${args.from_unit}_to_${args.to_unit}`;
      const fn = conversions[args.unit_type]?.[key];

      if (!fn) {
        return {
          content: [
            {
              type: "text",
              text: `Unsupported conversion: ${args.from_unit} to ${args.to_unit}`
            }
          ],
          isError: true
        };
      }

      const result = fn(args.value);
      return {
        content: [
          {
            type: "text",
            text: `${args.value} ${args.from_unit} = ${result.toFixed(4)} ${args.to_unit}`
          }
        ]
      };
    }
  );

  const converterServer = createSdkMcpServer({
    name: "converter",
    version: "1.0.0",
    tools: [convert]
  });
  ```
</CodeGroup>

定义好服务器后，以与天气示例相同的方式将其传递给 `query`。此示例在循环中发送三个不同的提示，以展示同一个工具处理不同的单位类型。对于每个响应，它会检查 `AssistantMessage` 对象（其中包含 Claude 在该回合中进行的工具调用），并在打印最终的 `ResultMessage` 文本之前打印每个 `ToolUseBlock`。这样你就可以看到 Claude 是在使用工具，还是在凭借自身知识作答。

由于 [工具搜索](/docs/en/agent-sdk/tool-search) 默认处于启用状态，当 Claude 加载延迟的工具模式时，输出中可能还会包含一次 `ToolSearch` 调用。

<CodeGroup>
  ```python Python theme={null}
  import asyncio
  from claude_agent_sdk import (
      query,
      ClaudeAgentOptions,
      ResultMessage,
      AssistantMessage,
      ToolUseBlock,
  )


  async def main():
      options = ClaudeAgentOptions(
          mcp_servers={"converter": converter_server},
          allowed_tools=["mcp__converter__convert_units"],
      )

      prompts = [
          "Convert 100 kilometers to miles.",
          "What is 72°F in Celsius?",
          "How many pounds is 5 kilograms?",
      ]

      for prompt in prompts:
          try:
              async for message in query(prompt=prompt, options=options):
                  if isinstance(message, AssistantMessage):
                      for block in message.content:
                          if isinstance(block, ToolUseBlock):
                              print(f"[tool call] {block.name}({block.input})")
                  elif isinstance(message, ResultMessage) and message.subtype == "success":
                      print(f"Q: {prompt}\nA: {message.result}\n")
          except Exception as error:
              # A single-shot query() raises after yielding an error result. Only success
              # results are printed above, so handle the failure here and continue with
              # the next prompt.
              print(f"Call failed: {error}")


  asyncio.run(main())
  ```

  ```typescript TypeScript theme={null}
  import { query } from "@anthropic-ai/claude-agent-sdk";

  const prompts = [
    "Convert 100 kilometers to miles.",
    "What is 72°F in Celsius?",
    "How many pounds is 5 kilograms?"
  ];

  for (const prompt of prompts) {
    try {
      for await (const message of query({
        prompt,
        options: {
          mcpServers: { converter: converterServer },
          allowedTools: ["mcp__converter__convert_units"]
        }
      })) {
        if (message.type === "assistant") {
          for (const block of message.message.content) {
            if (block.type === "tool_use") {
              console.log(`[tool call] ${block.name}`, block.input);
            }
          }
        } else if (message.type === "result" && message.subtype === "success") {
          console.log(`Q: ${prompt}\nA: ${message.result}\n`);
        }
      }
    } catch (error) {
      // A single-shot query() throws after yielding an error result. Only success
      // results are logged above, so handle the failure here and continue with
      // the next prompt.
      console.error(`Call failed: ${error}`);
    }
  }
  ```
</CodeGroup>

## 后续步骤

自定义工具将异步函数封装在标准接口中。你可以在同一服务器中混合使用本页介绍的各种模式：单个服务器可以同时承载数据库工具、API 网关工具和图像渲染器。

接下来：

* 如果你的服务器增长到包含数十个工具，请参阅[工具搜索](/docs/en/agent-sdk/tool-search)，将工具的加载推迟到 Claude 需要它们时。
* 如果你希望连接外部 MCP 服务器（文件系统、GitHub、Slack）而不是自行构建，请参阅[连接 MCP 服务器](/docs/en/agent-sdk/mcp)。
* 如需控制哪些工具自动运行、哪些需要批准，请参阅[配置权限](/docs/en/agent-sdk/permissions)。

## 相关文档

* [TypeScript SDK 参考](/docs/en/agent-sdk/typescript)
* [Python SDK 参考](/docs/en/agent-sdk/python)
* [MCP 文档](https://modelcontextprotocol.io)
* [SDK 概述](/docs/en/agent-sdk/overview)

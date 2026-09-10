---
title: SDK 中的插件
source_id: claude-code/agent-sdk/plugins
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/agent-sdk/plugins
owner: Anthropic
content_sha256: e141b7d8f77621f0e145f65b49104f6109173ffc2b5ce9f2e3e8057daf2c511a
translation_of: claude-code/agent-sdk/plugins
translation_model: gpt-5.6
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/agent-sdk/plugins)

Content owner: Anthropic

> ## 文档索引
> 在以下地址获取完整的文档索引：https://code.claude.com/docs/llms.txt
> 使用此文件可在深入探索之前发现所有可用页面。

# SDK 中的插件

> 通过 Agent SDK 加载自定义插件，使用技能、代理、钩子和 MCP 服务器扩展 Claude Code

插件允许你使用可跨项目共享的自定义功能扩展 Claude Code。通过 Agent SDK，你可以以编程方式从本地目录加载插件，为代理会话添加技能、代理、钩子和 MCP 服务器。

## 什么是插件？

插件是 Claude Code 扩展包，可以包括：

* **技能**：由模型调用、Claude 可自主使用的能力（也可以通过 `/skill-name` 调用）
* **代理**：用于特定任务的专用子代理
* **钩子**：响应工具使用及其他事件的事件处理程序
* **MCP 服务器**：通过模型上下文协议提供的外部工具集成

<Note>
  `commands/` 目录是旧格式。新插件请使用 `skills/`。为保持向后兼容，Claude Code 会继续支持两种格式。
</Note>

有关插件结构和创建插件的完整信息，请参阅[插件](/docs/en/plugins)。

## 加载插件

在选项配置中提供插件的本地文件系统路径即可加载插件。`type` 字段必须为 `"local"`，这是 SDK 接受的唯一值。若要使用通过[市场](/docs/en/plugin-marketplaces)或远程仓库分发的插件，请先下载它，再提供本地目录路径。SDK 支持从不同位置加载多个插件。

<CodeGroup>
  ```typescript TypeScript theme={null}
  import { query } from "@anthropic-ai/claude-agent-sdk";

  for await (const message of query({
    prompt: "Hello",
    options: {
      plugins: [
        { type: "local", path: "./my-plugin" },
        { type: "local", path: "/absolute/path/to/another-plugin" }
      ]
    }
  })) {
    // Plugin commands, agents, and other features are now available
  }
  ```

  ```python Python theme={null}
  import asyncio
  from claude_agent_sdk import query, ClaudeAgentOptions


  async def main():
      async for message in query(
          prompt="Hello",
          options=ClaudeAgentOptions(
              plugins=[
                  {"type": "local", "path": "./my-plugin"},
                  {"type": "local", "path": "/absolute/path/to/another-plugin"},
              ]
          ),
      ):
          # Plugin commands, agents, and other features are now available
          pass


  asyncio.run(main())
  ```
</CodeGroup>

### 路径规范

插件路径可以是：

* **相对路径**：相对于当前工作目录解析（例如 `"./plugins/my-plugin"`）
* **绝对路径**：完整文件系统路径（例如 `"/home/user/plugins/my-plugin"`）

<Note>
  路径应指向插件的根目录，即 `skills/`、`agents/`、`hooks/`、`commands/`（旧格式）或 `.claude-plugin/` 的父目录，而不是子目录。
</Note>

## 验证插件安装

插件成功加载后，会出现在系统初始化消息中。你可以验证插件是否可用：

<CodeGroup>
  ```typescript TypeScript theme={null}
  import { query } from "@anthropic-ai/claude-agent-sdk";

  for await (const message of query({
    prompt: "Hello",
    options: {
      plugins: [{ type: "local", path: "./my-plugin" }]
    }
  })) {
    if (message.type === "system" && message.subtype === "init") {
      // Check loaded plugins
      console.log("Plugins:", message.plugins);
      // Example: [{ name: "my-plugin", path: "./my-plugin" }]

      // Plugin skills appear with the plugin name as a prefix
      console.log("Skills:", message.skills);
      // Example: ["my-plugin:greet"]

      // Plugin commands use the same prefix, and skills appear here too
      console.log("Commands:", message.slash_commands);
      // Example: ["compact", "context", "my-plugin:custom-command", "my-plugin:greet"]
    }
  }
  ```

  ```python Python theme={null}
  import asyncio
  from claude_agent_sdk import query, ClaudeAgentOptions, SystemMessage


  async def main():
      async for message in query(
          prompt="Hello",
          options=ClaudeAgentOptions(
              plugins=[{"type": "local", "path": "./my-plugin"}]
          ),
      ):
          if isinstance(message, SystemMessage) and message.subtype == "init":
              # Check loaded plugins
              print("Plugins:", message.data.get("plugins"))
              # Example: [{"name": "my-plugin", "path": "./my-plugin"}]

              # Plugin skills appear with the plugin name as a prefix
              print("Skills:", message.data.get("skills"))
              # Example: ["my-plugin:greet"]

              # Plugin commands use the same prefix, and skills appear here too
              print("Commands:", message.data.get("slash_commands"))
              # Example: ["compact", "context", "my-plugin:custom-command", "my-plugin:greet"]


  asyncio.run(main())
  ```
</CodeGroup>

## 使用插件技能

插件中的技能会自动使用插件名称作为命名空间，以避免冲突。若要直接调用某项技能，请将 `/plugin-name:skill-name` 作为提示词发送。

<CodeGroup>
  ```typescript TypeScript theme={null}
  import { query } from "@anthropic-ai/claude-agent-sdk";

  // Load a plugin with a custom /greet skill
  for await (const message of query({
    prompt: "/my-plugin:greet", // Use plugin skill with namespace
    options: {
      plugins: [{ type: "local", path: "./my-plugin" }]
    }
  })) {
    // Claude executes the custom greeting skill from the plugin
    if (message.type === "assistant") {
      console.log(message.message.content);
    }
  }
  ```

  ```python Python theme={null}
  import asyncio
  from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock


  async def main():
      # Load a plugin with a custom /greet skill
      async for message in query(
          prompt="/demo-plugin:greet",  # Use plugin skill with namespace
          options=ClaudeAgentOptions(
              plugins=[{"type": "local", "path": "./plugins/demo-plugin"}]
          ),
      ):
          # Claude executes the custom greeting skill from the plugin
          if isinstance(message, AssistantMessage):
              for block in message.content:
                  if isinstance(block, TextBlock):
                      print(f"Claude: {block.text}")


  asyncio.run(main())
  ```
</CodeGroup>

<Note>
  如果你通过 CLI 安装了插件（例如 `/plugin install my-plugin@marketplace`），仍可通过提供其安装路径在 SDK 中使用它。CLI 安装的插件位于 `~/.claude/plugins/`。
</Note>

## 完整示例

下面是演示插件加载和使用的完整示例：

<CodeGroup>
  ```typescript TypeScript theme={null}
  import { query } from "@anthropic-ai/claude-agent-sdk";
  import * as path from "path";

  async function runWithPlugin() {
    const pluginPath = path.join(__dirname, "plugins", "my-plugin");

    console.log("Loading plugin from:", pluginPath);

    for await (const message of query({
      prompt: "What custom commands do you have available?",
      options: {
        plugins: [{ type: "local", path: pluginPath }],
        maxTurns: 3
      }
    })) {
      if (message.type === "system" && message.subtype === "init") {
        console.log("Loaded plugins:", message.plugins);
        console.log("Available skills:", message.skills);
        console.log("Available commands:", message.slash_commands);
      }

      if (message.type === "assistant") {
        console.log("Assistant:", message.message.content);
      }
    }
  }

  runWithPlugin().catch(console.error);
  ```

  ```python Python theme={null}
  #!/usr/bin/env python3
  """Example demonstrating how to use plugins with the Agent SDK."""

  from pathlib import Path
  import anyio
  from claude_agent_sdk import (
      AssistantMessage,
      ClaudeAgentOptions,
      SystemMessage,
      TextBlock,
      query,
  )


  async def run_with_plugin():
      """Example using a custom plugin."""
      plugin_path = Path(__file__).parent / "plugins" / "demo-plugin"

      print(f"Loading plugin from: {plugin_path}")

      options = ClaudeAgentOptions(
          plugins=[{"type": "local", "path": str(plugin_path)}],
          max_turns=3,
      )

      async for message in query(
          prompt="What custom commands do you have available?", options=options
      ):
          if isinstance(message, SystemMessage) and message.subtype == "init":
              print(f"Loaded plugins: {message.data.get('plugins')}")
              print(f"Available skills: {message.data.get('skills')}")
              print(f"Available commands: {message.data.get('slash_commands')}")

          if isinstance(message, AssistantMessage):
              for block in message.content:
                  if isinstance(block, TextBlock):
                      print(f"Assistant: {block.text}")


  if __name__ == "__main__":
      anyio.run(run_with_plugin)
  ```
</CodeGroup>

## 插件结构参考

插件目录通常包含 `.claude-plugin/plugin.json` 清单文件。清单是可选的。省略时，Claude Code 会根据目录布局自动发现组件。该目录可以包括：

```text theme={null}
my-plugin/
├── .claude-plugin/
│   └── plugin.json          # Plugin manifest (optional, components auto-discovered without it)
├── skills/                   # Agent Skills (invoked autonomously or via /skill-name)
│   └── my-skill/
│       └── SKILL.md
├── commands/                 # Legacy: use skills/ instead
│   └── custom-cmd.md
├── agents/                   # Custom agents
│   └── specialist.md
├── hooks/                    # Event handlers
│   └── hooks.json
└── .mcp.json                # MCP server definitions
```

有关创建插件的详细信息，请参阅：

* [插件](/docs/en/plugins) - 完整的插件开发指南
* [插件参考](/docs/en/plugins-reference) - 技术规范与模式定义

## 常见使用场景

### 开发与测试

在开发期间加载插件，而无需全局安装：

```typescript theme={null}
plugins: [{ type: "local", path: "./dev-plugins/my-plugin" }];
```

### 项目专用扩展

将插件纳入项目仓库，以便整个团队保持一致：

```typescript theme={null}
plugins: [{ type: "local", path: "./project-plugins/team-workflows" }];
```

### 多个插件来源

组合来自不同位置的插件：

```typescript theme={null}
plugins: [
  { type: "local", path: "./local-plugin" },
  { type: "local", path: "~/.claude/custom-plugins/shared-plugin" }
];
```

## 故障排除

### 插件未加载

如果插件没有出现在 init 消息中：

1. **检查路径**：确保路径指向插件根目录，即 `skills/`、`agents/`、`hooks/`、`commands/`（旧格式）或 `.claude-plugin/` 的父目录
2. **验证 plugin.json**：如果插件包含清单，请确保其 JSON 语法有效
3. **检查文件权限**：确保插件目录可读

### 技能未出现

如果插件技能无法工作：

1. **使用命名空间**：以 `/plugin-name:skill-name` 形式调用插件技能
2. **检查 init 消息**：验证该技能是否以正确命名空间出现在 `skills` 列表中
3. **验证技能文件**：确保每项技能都在 `skills/` 下自己的子目录中包含 `SKILL.md` 文件，例如 `skills/my-skill/SKILL.md`

### 路径解析问题

如果相对路径无法工作：

1. **检查工作目录**：相对路径从当前工作目录解析
2. **使用绝对路径**：为提高可靠性，可考虑使用绝对路径
3. **规范化路径**：使用路径实用工具正确构造路径

## 另请参阅

* [插件](/docs/en/plugins) - 完整的插件开发指南
* [插件参考](/docs/en/plugins-reference) - 技术规范
* [命令](/docs/en/agent-sdk/slash-commands) - 在 SDK 中使用命令
* [子代理](/docs/en/agent-sdk/subagents) - 使用专用代理
* [技能](/docs/en/agent-sdk/skills) - 使用 Agent Skills

---
title: 迁移到 Claude Agent SDK
source_id: claude-code/agent-sdk/migration-guide
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/agent-sdk/migration-guide
owner: Anthropic
content_sha256: b0cce4d9d3692f85b4927b3ee44806abda92ff65b5e0d4836223f0674abf37b6
translation_of: claude-code/agent-sdk/migration-guide
translation_source: official
translation_url: https://code.claude.com/docs/zh-CN/agent-sdk/migration-guide
localization_sha256: d0b651230733b8f40ba0e5500eb4e54346b3829fdc93879c5810a5557c8e3f3b
---
本页采用内容所有者发布的官方简体中文版本，并与本站对应英文版本进行结构校验。

[官方中文来源](https://code.claude.com/docs/zh-CN/agent-sdk/migration-guide)

内容所有者: Anthropic

> ## Documentation Index
> Fetch the complete documentation index at: https://code.claude.com/docs/llms.txt
> Use this file to discover all available pages before exploring further.

# 迁移到 Claude Agent SDK

> 将 Claude Code TypeScript 和 Python SDK 迁移到 Claude Agent SDK 的指南

<h2 id="overview">
  概述
</h2>

Claude Code SDK 已重命名为 **Claude Agent SDK**，其文档已重新组织。这一变化反映了该 SDK 在构建超越编码任务的 AI 代理方面的更广泛功能。

<h2 id="what’s-changed">
  变更内容
</h2>

| 方面              | 旧版本                         | 新版本                              |
| :-------------- | :-------------------------- | :------------------------------- |
| **包名称 (TS/JS)** | `@anthropic-ai/claude-code` | `@anthropic-ai/claude-agent-sdk` |
| **Python 包**    | `claude-code-sdk`           | `claude-agent-sdk`               |
| **文档位置**        | Claude Code 文档              | API 指南 → Agent SDK 部分            |

<Note>
  **文档变更：** Agent SDK 文档已从 Claude Code 文档移至 API 指南下的专门 [Agent SDK](/docs/zh-CN/agent-sdk/overview) 部分。Claude Code 文档现在专注于 CLI 工具和自动化功能。
</Note>

<h2 id="migration-steps">
  迁移步骤
</h2>

<h3 id="for-typescript/javascript-projects">
  对于 TypeScript/JavaScript 项目
</h3>

**1. 卸载旧包：**

```bash theme={null}
npm uninstall @anthropic-ai/claude-code
```

**2. 安装新包：**

```bash theme={null}
npm install @anthropic-ai/claude-agent-sdk
```

**3. 更新导入：**

将所有导入从 `@anthropic-ai/claude-code` 更改为 `@anthropic-ai/claude-agent-sdk`：

```typescript theme={null}
// 之前
import { query, tool, createSdkMcpServer } from "@anthropic-ai/claude-code";

// 之后
import { query, tool, createSdkMcpServer } from "@anthropic-ai/claude-agent-sdk";
```

**4. 更新 package.json 依赖项：**

如果您在 `package.json` 中列出了该包，请更新它：

之前：

```json theme={null}
{
  "dependencies": {
    "@anthropic-ai/claude-code": "^0.0.42"
  }
}
```

之后：

```json theme={null}
{
  "dependencies": {
    "@anthropic-ai/claude-agent-sdk": "^0.2.0"
  }
}
```

**5. 查看 [破坏性变更](#breaking-changes)**

进行完成迁移所需的任何代码更改。

<h3 id="for-python-projects">
  对于 Python 项目
</h3>

**1. 卸载旧包：**

```bash theme={null}
pip uninstall claude-code-sdk
```

**2. 安装新包：**

```bash theme={null}
pip install claude-agent-sdk
```

**3. 更新导入：**

将所有导入从 `claude_code_sdk` 更改为 `claude_agent_sdk`：

```python theme={null}
# 之前

from claude_code_sdk import query, ClaudeCodeOptions

# 之后

from claude_agent_sdk import query, ClaudeAgentOptions
```

**4. 更新类型名称：**

将 `ClaudeCodeOptions` 更改为 `ClaudeAgentOptions`：

```python theme={null}
# 之前

from claude_code_sdk import query, ClaudeCodeOptions

options = ClaudeCodeOptions(model="claude-opus-4-7")

# 之后

from claude_agent_sdk import query, ClaudeAgentOptions

options = ClaudeAgentOptions(model="claude-opus-4-7")
```

**5. 查看 [破坏性变更](#breaking-changes)**

进行完成迁移所需的任何代码更改。

<h2 id="breaking-changes">
  破坏性变更
</h2>

<Warning>
  为了改进隔离和显式配置，Claude Agent SDK v0.1.0 为从 Claude Code SDK 迁移的用户引入了破坏性变更。在迁移前请仔细查看本部分。
</Warning>

<h3 id="python-claudecodeoptions-renamed-to-claudeagentoptions">
  Python：ClaudeCodeOptions 重命名为 ClaudeAgentOptions
</h3>

**变更内容：** Python SDK 类型 `ClaudeCodeOptions` 已重命名为 `ClaudeAgentOptions`。

**迁移：**

```python theme={null}
# 之前 (claude-code-sdk)

from claude_code_sdk import query, ClaudeCodeOptions

options = ClaudeCodeOptions(model="claude-opus-4-7", permission_mode="acceptEdits")

# 之后 (claude-agent-sdk)

from claude_agent_sdk import query, ClaudeAgentOptions

options = ClaudeAgentOptions(model="claude-opus-4-7", permission_mode="acceptEdits")
```

**为什么变更：** 类型名称现在与"Claude Agent SDK"品牌相匹配，并在 SDK 的命名约定中提供一致性。

<h3 id="system-prompt-no-longer-default">
  系统提示不再是默认值
</h3>

**变更内容：** SDK 不再默认使用 Claude Code 的系统提示。

**迁移：**

<CodeGroup>
  ```typescript TypeScript theme={null}
  import { query } from "@anthropic-ai/claude-agent-sdk";

  // 之前 (v0.0.x) - 默认使用 Claude Code 的系统提示
  const before = query({ prompt: "Hello" });

  // 之后 (v0.1.0) - 默认使用最小系统提示
  // 要获得旧行为，请显式请求 Claude Code 的预设：
  const presetResult = query({
    prompt: "Hello",
    options: {
      systemPrompt: { type: "preset", preset: "claude_code" }
    }
  });

  // 或使用自定义系统提示：
  const customResult = query({
    prompt: "Hello",
    options: {
      systemPrompt: "You are a helpful coding assistant"
    }
  });
  ```

  ```python Python theme={null}
  # 之前 (v0.0.x) - 默认使用 Claude Code 的系统提示
  async for message in query(prompt="Hello"):
      print(message)

  # 之后 (v0.1.0) - 默认使用最小系统提示
  # 要获得旧行为，请显式请求 Claude Code 的预设：
  from claude_agent_sdk import query, ClaudeAgentOptions

  async for message in query(
      prompt="Hello",
      options=ClaudeAgentOptions(
          system_prompt={"type": "preset", "preset": "claude_code"}  # 使用预设
      ),
  ):
      print(message)

  # 或使用自定义系统提示：
  async for message in query(
      prompt="Hello",
      options=ClaudeAgentOptions(system_prompt="You are a helpful coding assistant"),
  ):
      print(message)
  ```
</CodeGroup>

**为什么变更：** 为 SDK 应用程序提供更好的控制和隔离。您现在可以构建具有自定义行为的代理，而无需继承 Claude Code 的 CLI 焦点指令。

<h3 id="settings-sources-default">
  设置源默认值
</h3>

此默认值在 v0.1.0 中曾短暂更改，然后被还原，因此无需迁移操作。

**当前行为：** 在 `query()` 上省略 `settingSources` 会加载用户、项目和本地文件系统设置，与 CLI 匹配。这包括 `~/.claude/settings.json`、`.claude/settings.json`、`.claude/settings.local.json`、CLAUDE.md 文件和自定义命令。

要从文件系统设置中隔离运行，请传递空数组：

<CodeGroup>
  ```typescript TypeScript theme={null}
  import { query } from "@anthropic-ai/claude-agent-sdk";

  const isolatedResult = query({
    prompt: "Hello",
    options: {
      settingSources: [] // 未加载文件系统设置
    }
  });

  // 或仅加载特定源：
  const projectOnlyResult = query({
    prompt: "Hello",
    options: {
      settingSources: ["project"] // 仅项目设置
    }
  });
  ```

  ```python Python theme={null}
  from claude_agent_sdk import query, ClaudeAgentOptions

  async for message in query(
      prompt="Hello",
      options=ClaudeAgentOptions(setting_sources=[]),  # 未加载文件系统设置
  ):
      print(message)

  # 或仅加载特定源：
  async for message in query(
      prompt="Hello",
      options=ClaudeAgentOptions(
          setting_sources=["project"]  # 仅项目设置
      ),
  ):
      print(message)
  ```
</CodeGroup>

隔离对于 CI/CD 管道、已部署的应用程序、测试环境和多租户系统特别重要，其中本地自定义不应泄露。

<Note>
  SDK v0.1.0 曾短暂默认为不加载任何设置；这在后续版本中被还原。Python SDK 0.1.59 及更早版本将空列表视为与省略选项相同，因此在依赖 `setting_sources=[]` 之前请升级。有关即使 `settingSources` 为 `[]` 时仍会读取的输入，请参阅 [settingSources 不控制的内容](/docs/zh-CN/agent-sdk/claude-code-features#what-settingsources-does-not-control)。
</Note>

<h2 id="why-the-rename">
  为什么重命名？
</h2>

Claude Code SDK 最初是为编码任务设计的，但它已发展成为构建所有类型 AI 代理的强大框架。新名称"Claude Agent SDK"更好地反映了其功能：

* 构建业务代理（法律助手、财务顾问、客户支持）
* 创建专门的编码代理（SRE 机器人、安全审查员、代码审查代理）
* 为任何领域开发自定义代理，具有工具使用、MCP 集成等功能

<h2 id="getting-help">
  获取帮助
</h2>

如果您在迁移过程中遇到任何问题：

**对于 TypeScript/JavaScript：**

1. 检查所有导入是否已更新为使用 `@anthropic-ai/claude-agent-sdk`
2. 验证您的 package.json 具有新的包名称
3. 运行 `npm install` 以确保依赖项已更新

**对于 Python：**

1. 检查所有导入是否已更新为使用 `claude_agent_sdk`
2. 验证您的 requirements.txt 或 pyproject.toml 具有新的包名称
3. 运行 `pip install claude-agent-sdk` 以确保包已安装

<h2 id="next-steps">
  后续步骤
</h2>

* 探索 [Agent SDK 概述](/docs/zh-CN/agent-sdk/overview) 以了解可用功能
* 查看 [TypeScript SDK 参考](/docs/zh-CN/agent-sdk/typescript) 以获取详细的 API 文档
* 查看 [Python SDK 参考](/docs/zh-CN/agent-sdk/python) 以获取 Python 特定文档
* 了解 [自定义工具](/docs/zh-CN/agent-sdk/custom-tools) 和 [MCP 集成](/docs/zh-CN/agent-sdk/mcp)

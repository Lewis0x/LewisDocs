---
title: 从 CLI 推荐你的插件
source_id: claude-code/plugin-hints
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/plugin-hints
owner: Anthropic
content_sha256: 7a15a21fd6fb24e30524ff5b690959f72d4ed3f7487e079fc7479299e5e5cd81
translation_of: claude-code/plugin-hints
translation_model: gpt-5.6
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/plugin-hints)

Content owner: Anthropic

> ## 文档索引
> 在以下地址获取完整的文档索引：https://code.claude.com/docs/llms.txt
> 使用此文件可在深入探索之前发现所有可用页面。

# 从 CLI 推荐你的插件

> 从 CLI 输出一行标记，让 Claude Code 提示用户安装你的官方插件。

如果你维护 CLI 或 SDK，并且在 Anthropic 官方市场中拥有插件，你的工具可以提示 Claude Code 用户安装该插件。当你的 CLI 检测到自己在 Claude Code 内运行时，会向 stderr 写入一行标记。Claude Code 读取该标记、将其从输出中移除，并向用户显示一次性安装提示。

Claude Code 会先从命令输出中移除提示行，再将输出发送给模型，因此该标记绝不会出现在对话中，也不会计入令牌用量。此协议不需要额外命令，也不会改变你的 CLI 为 Claude Code 外部用户输出的内容。

本页面向 CLI 和 SDK 维护者。如果你希望安装插件，请参阅[发现并安装插件](/docs/en/discover-plugins)。

## 工作原理

Claude Code 会将 [`CLAUDECODE`](/docs/en/env-vars) 环境变量设为 `1`，此设置适用于它通过 Bash 和 PowerShell 工具运行的每条命令以及[钩子](/docs/en/hooks)命令。{/* min-version: 2.1.172 */}从 v2.1.172 开始，它还会在这些相同的子进程中将 [`CLAUDE_CODE_CHILD_SESSION`](/docs/en/env-vars) 设为 `1`。当你的 CLI 看到其中任一变量时，就会向 stderr 写入一个自闭合 `<claude-code-hint />` 标签。在钩子命令中，提示标签会被移除并忽略。只有 Bash 和 PowerShell 工具的输出会触发安装提示。

Claude Code 收到命令输出时会：

1. 扫描提示行，并在输出到达模型之前将其移除
2. 检查提示的目标是否为 Anthropic 官方市场中的插件
3. 检查该插件是否尚未安装，并且此前是否尚未提示过
4. 向用户显示安装提示，其中会列出发出提示的命令名称

Claude Code 绝不会自动安装插件。始终由用户确认。

## 输出提示

提示安装仅对 Anthropic 官方市场中列出的插件生效。发布集成之前，请参阅[让你的插件进入官方市场](#get-your-plugin-into-the-official-marketplace)。

请以环境变量作为输出条件，使标记不太可能在用户直接运行 CLI 时出现，然后将标签单独成行写入 stderr。选择要检查的变量：

* `CLAUDECODE`：每个 Claude Code 版本都会设置，因此能够覆盖最多的会话。Claude Code 启动的 tmux 会话和 stdio MCP 服务器子进程中也会设置该变量。IDE 扩展也会在其集成终端中设置它，而用户可能正在该终端中直接运行你的 CLI。
* {/* min-version: 2.1.172 */}`CLAUDE_CODE_CHILD_SESSION`：仅在 Claude Code 自行生成的子进程中设置，例如工具调用、钩子命令和[状态行](/docs/en/statusline)命令，因此标签通常不会到达用户终端。在会话内启动的长期运行进程（例如 tmux 服务器）会捕获该变量，所以此后从该进程启动的 shell 仍会显示原始标签。要求 Claude Code v2.1.172 或更高版本，因此旧版本上的会话会错过该提示。

以下示例以 `CLAUDECODE` 作为条件以获得最大覆盖范围，并为官方市场中名为 `example-cli` 的插件输出提示：

<CodeGroup>
  ```javascript Node.js theme={null}
  if (process.env.CLAUDECODE) {
    process.stderr.write(
      '<claude-code-hint v="1" type="plugin" value="example-cli@claude-plugins-official" />\n',
    )
  }
  ```

  ```python Python theme={null}
  import os, sys

  if os.environ.get("CLAUDECODE"):
      print(
          '<claude-code-hint v="1" type="plugin" value="example-cli@claude-plugins-official" />',
          file=sys.stderr,
      )
  ```

  ```go Go theme={null}
  if os.Getenv("CLAUDECODE") != "" {
      fmt.Fprintln(os.Stderr,
          `<claude-code-hint v="1" type="plugin" value="example-cli@claude-plugins-official" />`)
  }
  ```

  ```shell Shell theme={null}
  if [ -n "$CLAUDECODE" ]; then
    printf '%s\n' '<claude-code-hint v="1" type="plugin" value="example-cli@claude-plugins-official" />' >&2
  fi
  ```
</CodeGroup>

请将 `example-cli` 替换为你的插件在官方市场中的名称。

## 选择输出位置

你可以控制哪些代码路径输出提示。Claude Code 会按插件去重，因此每次调用都输出没有任何坏处。适合的触点包括：

| 放置位置 | 有效原因 |
| :--- | :--- |
| `--help` 输出 | Claude 探索陌生 CLI 时经常运行帮助 |
| 未知子命令错误 | 恰好能在 Claude 对你的界面感到困惑时触达它 |
| 登录或身份验证成功 | 用户已经处于设置流程的思维状态 |
| 首次运行欢迎消息 | 自然的引导时机 |

## 用户看到的内容

提示通过所有检查后，Claude Code 会显示类似以下内容的提示：

```text theme={null}
─────────────────────────────────────────────────────────────
  Plugin recommendation

    The example-cli command suggests installing a plugin.

    Plugin: example-cli
    Marketplace: claude-plugins-official
    Official integration for example-cli deployments

    Would you like to install it?
    ❯ 1. Yes, install example-cli
      2. No
      3. No, and don't show plugin installation hints again

─────────────────────────────────────────────────────────────
```

提示会列出生成该提示的命令名称，因此用户可以发现工具与它所推荐插件之间的不匹配。如果用户在 30 秒内没有响应，提示会按**否**处理并关闭。

提示频率有上限，且某些会话绝不会显示提示：

* **每个插件一次**：提示显示后，Claude Code 会记录该插件，无论用户如何回答，都绝不会再为它提示。
* **每个会话一次**：在这台机器的所有 CLI 中，每个 Claude Code 会话最多显示一次提示。
* **遥测退出**：禁用了分析的会话绝不会显示提示。这包括设置了 `DISABLE_TELEMETRY` 或 `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` 的会话，以及 Amazon Bedrock 或 Google Cloud Agent Platform 等第三方提供商上适用[自动退出遥测](/docs/en/data-usage#default-behaviors-by-api-provider)的会话。

选择**是**会把插件安装到用户作用域。选择**否，并且以后不再显示插件安装提示**会为该用户禁用今后的所有提示。

## 提示格式

提示是一个具有三个必需属性的自闭合标签。

```text theme={null}
<claude-code-hint v="1" type="plugin" value="example-cli@claude-plugins-official" />
```

| 属性 | 是否必需 | 说明 |
| :--- | :--- | :--- |
| `v` | 是 | 协议版本。`1` 是唯一支持的值 |
| `type` | 是 | 提示种类。`plugin` 是唯一支持的值 |
| `value` | 是 | 采用 `name@marketplace` 格式的插件标识符 |

属性值可以使用双引号，也可以不加引号。未加引号的值不能包含空白字符。不支持转义序列。

## 要求

Claude Code 在处理提示前会强制执行两个条件。未通过任一检查的提示都会被丢弃：

* **独占一行**：标签必须单独占据一行。嵌入行中间的标签（例如位于日志语句内）会被忽略。允许该行带有前导和尾随空白。
* **官方市场**：`value` 必须引用 Anthropic 控制的市场（例如 `claude-plugins-official`）中的插件。指向其他市场的提示会被静默丢弃。

无论版本或类型是否可识别，提示行始终会在输出到达模型之前移除，因此该标记绝不会计入令牌用量。

其余指导属于建议，而非强制要求。Claude Code 无法观察你的 CLI 是否遵循这些指导：

* **写入 stderr**：stderr 可使标签不进入 `example-cli deploy | jq` 之类的 shell 管道。Claude Code 会扫描两个流，因此 stdout 也可以使用。
* **以环境变量为条件**：仅当设置了 `CLAUDECODE` 或 `CLAUDE_CODE_CHILD_SESSION` 时输出。有关两个变量的差异，请参阅[输出提示](#emit-the-hint)。

## 让你的插件进入官方市场

提示协议只对 Anthropic 官方市场 `claude-plugins-official` 中列出的插件生效。Anthropic 可自行决定如何策划该市场，而应用内提交表单会将插件添加到[社区市场](/docs/en/plugins#submit-your-plugin-to-the-community-marketplace)，提示协议不会检查该市场。如果你正在与 Anthropic 合作伙伴联系人协作，请联系对方，协调进入官方市场的事宜。

## 另请参阅

* [创建插件](/docs/en/plugins)：构建你的 CLI 所推荐的插件
* [创建和分发插件市场](/docs/en/plugin-marketplaces)：在官方市场之外托管插件
* [环境变量](/docs/en/env-vars)：`CLAUDECODE` 及相关变量的完整参考

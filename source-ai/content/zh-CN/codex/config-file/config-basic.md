---
title: 配置基础
source_id: codex/config-file/config-basic
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/config-file/config-basic
owner: OpenAI
content_sha256: eec4ad4519d829b569695a82a0e08014ea6a25a97b1e54439d6ab687e6b8aabf
translation_of: codex/config-file/config-basic
translation_model: k3
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/config-file/config-basic)

Content owner: OpenAI

# 配置基础

> 有关完整的文档索引，请参阅 [llms.txt](https://learn.chatgpt.com/llms.txt)。通过在页面 URL 后附加 `.md` 可以获取文档页面的 Markdown 版本。

Codex 从多个位置读取配置详情。您的个人默认设置位于 `~/.codex/config.toml` 中，并且您可以使用 `.codex/config.toml` 文件添加项目覆盖。出于安全考虑，Codex 仅在您信任该项目时才会加载项目 `.codex/` 层。

## Codex 配置文件

Codex 将用户级配置存储在 `~/.codex/config.toml`。要将设置限定于特定项目或子文件夹，请在您的代码库中添加一个 `.codex/config.toml` 文件。

要从 Codex IDE 扩展中打开配置文件，请选择右上角的齿轮图标，然后选择 **Codex Settings > Open config.toml**。

CLI 和 IDE 扩展共享相同的配置层。您可以使用它们来：

- 设置默认模型和提供商。
- 配置 [批准策略和沙盒设置](https://learn.chatgpt.com/docs/agent-approvals-security#sandbox-and-approvals)。
- 配置 [MCP 服务器](https://learn.chatgpt.com/docs/extend/mcp)。

## 配置优先级

Codex 按以下顺序解析值（优先级从高到低）：

1. CLI 标志和 `--config` 覆盖
2. 项目配置文件：`.codex/config.toml`，从项目根目录向下排列至当前工作目录（最近的优先；仅限受信任的项目）
3. [Profile](https://learn.chatgpt.com/docs/config-file/config-advanced#profiles) 文件，通过 `--profile profile-name` (`~/.codex/profile-name.config.toml`) 选定
4. 用户配置：`~/.codex/config.toml`
5. 系统配置（如果存在）：Unix 上的 `/etc/codex/config.toml`
6. 内置默认值

使用该优先级在 `config.toml` 中设置共享默认值，并让 [profile 文件](https://learn.chatgpt.com/docs/config-file/config-advanced#profiles) 专注于不同的值。

如果您将项目标记为不受信任，Codex 将跳过项目范围内的 `.codex/` 层，包括项目本地配置、钩子和规则。用户和系统配置仍会加载，包括用户/全局钩子和规则。

有关通过 `-c`/`--config` 进行一次性覆盖（包括 TOML 引号规则），请参阅 [高级配置](https://learn.chatgpt.com/docs/config-file/config-advanced#one-off-overrides-from-the-cli)。

在受管计算机上，您的组织也可能通过
  `requirements.toml` 强制实施约束（例如，禁止 `approval_policy = "never"` 或
  `sandbox_mode = "danger-full-access"`）。请参阅[托管
  配置](https://learn.chatgpt.com/docs/enterprise/managed-configuration) 和[管理员强制
  要求](https://learn.chatgpt.com/docs/enterprise/managed-configuration#admin-enforced-requirements-requirementstoml)。

## 常见配置选项

以下是人们最常更改的几个选项：

#### 默认模型

选择 Codex 在 CLI 和 IDE 中默认使用的模型。

```toml
model = "gpt-5.6"
```


#### 批准提示

控制 Codex 在运行生成的命令前暂停询问的时机。

```toml
approval_policy = "on-request"
```

有关 `untrusted`、`on-request` 和 `never` 之间的行为差异，请参阅 [无批准提示运行](https://learn.chatgpt.com/docs/agent-approvals-security#run-without-approval-prompts) 和 [常见沙盒和批准组合](https://learn.chatgpt.com/docs/agent-approvals-security#common-sandbox-and-approval-combinations)。

#### 沙盒级别

调整 Codex 在执行命令时拥有多少文件系统和网络访问权限。

```toml
sandbox_mode = "workspace-write"
```

有关各模式下的行为（包括受保护的 `.git`/`.codex` 路径和网络默认设置），请参阅 [沙盒和批准](https://learn.chatgpt.com/docs/agent-approvals-security#sandbox-and-approvals)、[可写根目录中的受保护路径](https://learn.chatgpt.com/docs/agent-approvals-security#protected-paths-in-writable-roots) 和 [网络访问](https://learn.chatgpt.com/docs/agent-approvals-security#network-access)。

#### 权限配置

Codex 还支持命名的权限配置，以实现可重用的文件系统和
网络策略。内置配置有 `:read-only`、`:workspace` 和
`:danger-full-access`。自定义配置使用 `[permissions.<name>]` 表和
匹配的 `default_permissions` 值。请参阅 [权限](https://learn.chatgpt.com/docs/permissions)。

#### Windows 沙盒模式

在 Windows 上原生运行 Codex 时，请在 `windows` 表中将原生沙盒模式设置为 `elevated`。仅当您没有管理员权限或提升权限的设置失败时，才使用 `unelevated`。

```toml
[windows]
sandbox = "elevated"   # Recommended
# sandbox = "unelevated" # Fallback if admin permissions/setup are unavailable

```

#### 网络搜索模式

Codex 默认为本地聊天启用网络搜索，并提供来自网络搜索缓存的结果。该缓存是 OpenAI 维护的网络结果索引，因此缓存模式返回的是预先索引的结果，而不是抓取实时页面。这减少了遭受来自任意实时内容的提示注入的风险，但您仍应将网络结果视为不受信任的内容。如果您正在使用 `--yolo` 或另一个 [完全访问沙箱设置](https://learn.chatgpt.com/docs/agent-approvals-security#common-sandbox-and-approval-combinations)，网络搜索将默认返回实时结果。使用 `web_search` 选择模式：

- `"cached"`（默认）提供来自网络搜索缓存的结果。
- `"indexed"` 仅在搜索索引控制请求时才允许外部网络访问。
- `"live"` 从网络获取最新数据（与 `--search` 相同）。
- `"disabled"` 关闭网络搜索工具。

```toml
web_search = "cached"  # default; serves results from the web search cache
# web_search = "indexed" # gate external web access through the search index

# web_search = "live"  # fetch the most recent data from the web (same as --search)

# web_search = "disabled"

```

#### 推理努力

调整在受支持的情况下模型应用多少推理努力。

```toml
model_reasoning_effort = "high"
```

#### 沟通风格

为受支持的模型设置默认沟通风格。

```toml
personality = "friendly" # or "pragmatic" or "none"
```

您稍后可以在活动会话中使用 `/personality` 覆盖此设置，或者在使用 app-server API 时按线程/轮次覆盖。

#### TUI 键盘映射

在 `tui.keymap` 下自定义终端快捷键。选定的组合器操作会回退到匹配的 `tui.keymap.global` 绑定；在受支持的情况下，上下文特定的绑定具有优先权。空列表将解除该操作的绑定。

```toml
[tui.keymap.global]
open_transcript = "ctrl-t"

[tui.keymap.composer]
submit = ["enter", "ctrl-m"]

[tui.keymap.chat]
interrupt_turn = "f12"
```

#### 命令环境

控制 Codex 将哪些环境变量转发给生成的命令。

```toml
[shell_environment_policy]
include_only = ["PATH", "HOME"]
```

#### 日志目录

覆盖 Codex 写入本地日志文件的位置。显式设置 `log_dir` 也会
在该目录中启用可选的明文 TUI 日志 `codex-tui.log`。

```toml
log_dir = "/absolute/path/to/codex-logs"
```

对于一次性运行，您也可以从 CLI 中设置它：

```bash
codex -c log_dir=./.codex-log
```

## 功能标志

使用 `config.toml` 中的 `[features]` 表来切换可选和实验性功能。

### 常见功能标志

| 键                  |        默认值        | 成熟度     | 描述                                                                              |
| -------------------- | :-------------------: | ------------ | ---------------------------------------------------------------------------------------- |
| `apps`               |         true          | 稳定       | 启用应用（连接器）集成                                                      |
| `goals`              |         true          | 稳定       | 启用持久化目标和自动延续                                        |
| `hooks`              |         true          | 稳定       | 启用来自 `hooks.json` 或内联 `[hooks]` 的生命周期钩子。参见 [Hooks](https://learn.chatgpt.com/docs/hooks)。 |
| `fast_mode`          |         true          | 稳定       | 启用 Fast 模式选择和 `service_tier = "fast"` 路径                          |
| `memories`           |         false         | 实验性 | 启用 [Memories](https://learn.chatgpt.com/docs/customization/memories)                                         |
| `multi_agent`        |         true          | 稳定       | 启用子代理协作工具                                                      |
| `personality`        |         true          | 稳定       | 启用人格选择控件                                                    |
| `remote_plugin`      |         true          | 稳定       | 启用远程插件目录                                                         |
| `shell_snapshot`     |         true          | 稳定       | 快照你的 shell 环境以加速重复命令                            |
| `shell_tool`         |         true          | 稳定       | 启用默认 `shell` 工具                                                          |
| `unified_exec`       | `true` 除 Windows 外 | 稳定       | 使用统一的 PTY 支持的执行工具                                                     |
| `web_search`         |         true          | 已弃用   | 遗留开关；建议使用顶层 `web_search` 设置                                 |
| `web_search_cached`  |         false         | 已弃用   | 遗留开关，未设置时映射到 `web_search = "cached"`                            |
| `web_search_request` |         false         | 已弃用   | 遗留开关，未设置时映射到 `web_search = "live"`                              |

此表列出了常见的面向用户的标志，而非每个内部或
  正在开发的功能。成熟度列使用诸如实验性、Beta 和稳定等标签。参见[功能
  成熟度](https://learn.chatgpt.com/docs/feature-maturity)了解如何解读这些标签。

省略功能键以保持其默认值。

有关生命周期钩子配置，参见 [Hooks](https://learn.chatgpt.com/docs/hooks)。

### 启用功能

- 在 `config.toml` 中，在 `[features]` 下添加 `feature_name = true`。
- 从 CLI 运行 `codex --enable feature_name`。
- 要启用多个功能，运行 `codex --enable feature_a --enable feature_b`。
- 要禁用某个功能，在 `config.toml` 中将该键设置为 `false`。

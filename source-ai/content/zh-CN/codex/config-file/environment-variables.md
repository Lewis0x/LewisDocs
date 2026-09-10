---
title: 环境变量
source_id: codex/config-file/environment-variables
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/config-file/environment-variables
owner: OpenAI
content_sha256: f34f1cd61da8748ffd346439b3b170127ff11094995c87a81e2af8bd98d59467
translation_of: codex/config-file/environment-variables
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/config-file/environment-variables)

Content owner: OpenAI

# 环境变量

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。可以通过在页面 URL 后附加 `.md` 来获取文档页面的 Markdown 版本。

Codex 使用 `config.toml` 进行持久设置。使用环境变量进行
shell 范围内的覆盖、自动化密钥、安装程序行为或诊断。

本页面列出了 Codex 直接读取的稳定公共环境变量。
它不列出内部开发变量、测试变量，或
特定于提供商的密钥名称，这些名称是您使用
[`env_key`](https://learn.chatgpt.com/docs/config-file/config-advanced#custom-model-providers) 自行选择的。

## 核心位置

| 变量            | 使用者                                    | 默认值      | 描述                                                                                                                                                      |
| ------------------- | ------------------------------------------ | ------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CODEX_HOME`        | CLI、IDE 扩展、应用服务器、安装程序 | `~/.codex`   | 设置 Codex 状态的根目录，包括配置、身份验证、日志、会话、技能和独立包元数据。如果设置此项，该目录必须已经存在。 |
| `CODEX_SQLITE_HOME` | CLI 和应用服务器状态                   | `CODEX_HOME` | 设置由 SQLite 支持的状态的存储位置。`sqlite_home` 配置选项优先。相对路径从当前工作目录解析。           |

有关存储在 `CODEX_HOME` 下的文件的更多信息，请参见
[配置和状态位置](https://learn.chatgpt.com/docs/config-file/config-advanced#config-and-state-locations)。

## 安装程序变量

这些变量适用于从
`https://chatgpt.com/codex/install.sh` 和
`https://chatgpt.com/codex/install.ps1` 提供的独立安装脚本。

| 变量                | 默认值                                                                              | 描述                                                                                                                                                     |
| ----------------------- | ------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CODEX_NON_INTERACTIVE` | `false`                                                                              | 设置为 `1`、`true` 或 `yes` 以跳过安装程序提示。提示将使用其默认响应，因此请将此用于脚本化安装和更新，而不是首次运行设置。 |
| `CODEX_INSTALL_DIR`     | 在 macOS/Linux 上为 `~/.local/bin`；在 Windows 上为 `%LOCALAPPDATA%\Programs\OpenAI\Codex\bin` | 更改可见 `codex` 命令的安装位置。独立包缓存仍然位于 `CODEX_HOME/packages/standalone` 下。                        |

对于无人值守安装，请在运行
下载的安装程序的 shell 上设置 `CODEX_NON_INTERACTIVE=1`：

```bash
curl -fsSL https://chatgpt.com/codex/install.sh | CODEX_NON_INTERACTIVE=1 sh
```

```powershell
$env:CODEX_NON_INTERACTIVE=1; irm https://chatgpt.com/codex/install.ps1 | iex
```

## 认证和网络

| 变量               | 使用者                             | 描述                                                                                                                                                               |
| ---------------------- | ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CODEX_API_KEY`        | `codex exec`                        | 为单次非交互式运行提供 API 密钥。这仅在 `codex exec` 中受支持；在运行仓库控制的代码时，请以内联方式设置它，而不是全局设置。 |
| `CODEX_ACCESS_TOKEN`   | CLI、应用服务器、受信任的自动化 | 为受信任的自动化提供 ChatGPT 或 Codex 访问令牌。如需持久登录，请将其通过管道传递给 `codex login --with-access-token`。                                       |
| `CODEX_CA_CERTIFICATE` | HTTPS、登录和 WebSocket 客户端 | 指向用于具有企业 TLS 拦截或私有根 CA 环境的 PEM CA 包。优先于 `SSL_CERT_FILE`。                                    |
| `SSL_CERT_FILE`        | HTTPS、登录和 WebSocket 客户端 | 当 `CODEX_CA_CERTIFICATE` 未设置时的备用 PEM CA 包路径。                                                                                                         |

对于提供商 API 密钥，设置
[`env_key`](https://learn.chatgpt.com/docs/config-file/config-advanced#custom-model-providers) 在模型提供商
配置中。Codex 会读取由该配置命名的变量，因此变量
名称本身并不是固定的 Codex 环境变量。

有关自动化密钥处理，请参见
[使用 API 密钥认证](https://learn.chatgpt.com/docs/non-interactive-mode#use-api-key-auth)。
有关访问令牌设置，请参见 [访问令牌](https://learn.chatgpt.com/docs/enterprise/access-tokens)。

## 诊断

| 变量   | 使用者            | 描述                                                                                                             |
| ---------- | ------------------ | ----------------------------------------------------------------------------------------------------------------------- |
| `RUST_LOG` | CLI 和应用服务器 | 控制 Rust 日志过滤和详细程度。`codex exec` 默认为 `error` 输出，除非您设置了更详细的值。 |

`RUST_LOG` 接受诸如 `error`、`warn`、`info`、`debug` 以及
`trace` 的值。它还接受更有针对性的 Rust 日志过滤器，例如
`codex_core=debug,codex_tui=debug`。

交互式 CLI 默认将诊断信息记录在有界的本地存储中，但
明文 `codex-tui.log` 文件是可选的。当您需要用于故障排除的明文
日志时，请显式设置 `log_dir`：

```bash
RUST_LOG=debug codex -c log_dir=./.codex-log
tail -F ./.codex-log/codex-tui.log
```

在非交互模式下，`codex exec` 会以内联方式打印消息，而不是写入
单独的 TUI 日志文件。

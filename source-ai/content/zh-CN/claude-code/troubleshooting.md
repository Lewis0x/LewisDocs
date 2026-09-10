---
title: 故障排除
source_id: claude-code/troubleshooting
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/troubleshooting
owner: Anthropic
content_sha256: e252d23b41d756e5843cc930dec11b6646d0692b5de977b55c2b0d5b1c1b2da5
translation_of: claude-code/troubleshooting
translation_model: gpt-5.6
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/troubleshooting)

Content owner: Anthropic

> ## 文档索引
> 在以下地址获取完整的文档索引：https://code.claude.com/docs/llms.txt
> 使用此文件可在深入探索之前发现所有可用页面。

# 故障排除

> 解决 Claude Code 中 CPU 或内存占用过高、挂起、自动压缩抖动和搜索问题，并为其他问题找到正确的页面。

本页面介绍 Claude Code 已经运行后出现的性能、稳定性和搜索问题。对于其他问题，请从与你遇到阻碍的位置相符的页面开始：

| 症状 | 前往 |
| :--- | :--- |
| `command not found`、安装失败、PATH 问题、`EACCES`、TLS 错误 | [排查安装与登录问题](/docs/en/troubleshoot-install) |
| 更新或安装下载失败，并显示 `The connection dropped while downloading the update` 或 `aborted` | [错误参考](/docs/en/errors#the-connection-dropped-while-downloading-the-update) |
| 登录循环、OAuth 错误、`403 Forbidden`、“organization disabled”，或 Amazon Bedrock、Google Cloud Agent Platform、Microsoft Foundry 凭据问题 | [排查安装与登录问题](/docs/en/troubleshoot-install#login-and-authentication) |
| 设置未生效、钩子未触发、MCP 服务器未加载 | [调试配置](/docs/en/debug-your-config) |
| `API Error: 5xx`、`529 Overloaded`、`429`、请求验证错误 | [错误参考](/docs/en/errors) |
| `model not found` 或 `you may not have access to it` | [错误参考](/docs/en/errors#theres-an-issue-with-the-selected-model) |
| VS Code 扩展无法连接或检测 Claude | [VS Code 集成](/docs/en/vs-code#fix-common-issues) |
| VS Code 或 SDK 应用中出现 `Claude Code process exited with code 1` | [错误参考](/docs/en/errors#claude-code-process-exited-with-code-n) |
| 未检测到 JetBrains 插件或 IDE | [JetBrains 集成](/docs/en/jetbrains#troubleshooting) |
| CPU 或内存占用过高、响应缓慢、挂起、搜索找不到文件 | 下文的[性能与稳定性](#performance-and-stability) |

如果你不确定适用哪一种情况，请在 Claude Code 内运行 `/doctor`，自动检查安装、设置、扩展和上下文用量；它会提出修复方案，并在你确认后应用。如果 `claude` 完全无法启动，请改为从 shell 运行 `claude doctor`。运行 `/mcp` 可检查 MCP 服务器状态。

## 性能与稳定性

以下各节介绍与资源使用、响应能力和搜索行为有关的问题。

### CPU 或内存占用过高

Claude Code 旨在适配大多数开发环境，但处理大型代码库时可能会消耗大量资源。如果你遇到性能问题：

1. 定期使用 `/compact` 缩减上下文大小
2. 在各项主要任务之间关闭并重新启动 Claude Code
3. 考虑将大型构建目录添加到 `.gitignore` 文件
4. 使用 [`claude --safe-mode`](/docs/en/cli-reference#cli-flags) 重新启动，以检查问题是否源自插件、MCP 服务器或钩子。它会在本次会话中禁用所有自定义项；如果资源用量下降，请参阅[调试配置](/docs/en/debug-your-config#test-against-a-clean-configuration)，找出具体来源

如果执行这些步骤后内存用量仍然很高，请运行 `/heapdump`，将 JavaScript 堆快照和内存明细写入 `~/Desktop`。在没有 Desktop 文件夹的 Linux 上，这些文件会写入你的主目录。

明细会显示常驻集大小、JS 堆、数组缓冲区和未计入的原生内存，有助于判断增长发生在 JavaScript 对象还是原生代码中。若要检查保留器，请在 Chrome DevTools 的 Memory → Load 下打开 `.heapsnapshot` 文件；明细是以 `-diagnostics.json` 结尾的文件。

<Warning>
  `.heapsnapshot` 文件包含进程中的每个字符串。不要将它附加到公开 issue 或分享出去。在 [GitHub](https://github.com/anthropics/claude-code/issues) 上报告内存问题时，只附加 `-diagnostics.json` 文件。该文件包含内存统计信息，不包含对话内容或凭据。
</Warning>

### 大型表格在终端中被截断

超过 200 行的 Markdown 表格只会渲染前 200 行，随后显示一行 `… N more rows not shown`。受限的只是显示：完整表格仍保留在对话中，而 [`/copy`](/docs/en/commands) 会复制每一行。对于大到无法在终端中阅读的表格，请让 Claude 改为将其写入文件。在 v2.1.208 之前，Claude Code 会渲染每一行，因此恢复包含非常大表格的会话时，可能会在重新渲染期间卡住。

### 自动压缩因抖动错误而停止

如果看到 `Autocompact is thrashing: the context refilled to the limit...`，说明自动压缩已成功，但某个文件或工具输出连续多次立即重新填满了上下文窗口。Claude Code 会停止重试，以免将 API 调用浪费在没有取得进展的循环上。

恢复方法：

1. 让 Claude 分成更小的块读取超大文件，例如只读取特定行范围或函数，而不是读取整个文件
2. 运行 `/compact` 并指定保留重点以舍弃大型输出，例如 `/compact keep only the plan and the diff`
3. 将大型文件工作移交给[子代理](/docs/en/sub-agents)，使其在单独的上下文窗口中运行
4. 如果不再需要先前的对话，请运行 `/clear`

### 命令挂起或冻结

如果 Claude Code 似乎没有响应：

1. 按 Ctrl+C，尝试取消当前操作
2. 如果仍无响应，可能需要关闭终端并重新启动

重新启动不会丢失对话。在相同目录中运行 `claude --resume` 即可恢复会话。

### 编辑器集成终端中的文本乱码或损坏

如果在 VS Code、Cursor 或 Devin Desktop 集成终端中运行 Claude Code 时，字符渲染成方框、拖影或错误的字形，很可能是终端的 GPU 渲染器导致的。请在 Claude Code 内运行 `/terminal-setup`，将 `terminal.integrated.gpuAcceleration` 设为 `"off"`，或者在编辑器设置中手动设置并重新加载窗口。有关 `/terminal-setup` 写入的其他设置，请参阅[终端配置](/docs/en/terminal-config)。

### 搜索与发现问题

如果 Search 工具、`@file` 提及、自定义代理或自定义技能找不到文件，可能是捆绑的 `ripgrep` 二进制文件无法在你的系统上运行。请安装适用于你平台的 `ripgrep` 软件包，并让 Claude Code 改用它：

<Tabs>
  <Tab title="macOS">
    ```bash theme={null}
    brew install ripgrep
    ```
  </Tab>

  <Tab title="Ubuntu/Debian">
    ```bash theme={null}
    sudo apt install ripgrep
    ```
  </Tab>

  <Tab title="Alpine">
    ```bash theme={null}
    apk add ripgrep
    ```

    `ripgrep` 位于 Alpine 的 community 软件源中。如果 `apk` 报告缺少该软件包，请参阅 [Alpine Linux 设置](/docs/en/setup#alpine-linux-and-musl-based-distributions)。
  </Tab>

  <Tab title="Arch">
    ```bash theme={null}
    pacman -S ripgrep
    ```
  </Tab>

  <Tab title="Windows">
    ```powershell theme={null}
    winget install BurntSushi.ripgrep.MSVC
    ```
  </Tab>
</Tabs>

然后在你的[环境](/docs/en/env-vars)中设置 `USE_BUILTIN_RIPGREP=0`。若要确认切换已生效，请在终端中运行 `claude doctor`，并检查 Search 行是否显示系统 ripgrep 的路径，而不是 `OK (bundled)`。

### WSL 上搜索结果缓慢或不完整

[跨 WSL 文件系统工作](https://learn.microsoft.com/en-us/windows/wsl/filesystems)时的磁盘读取性能损失，可能导致在 WSL 上使用 Claude Code 时得到的匹配项少于预期。搜索仍然有效，但返回的结果少于原生文件系统。

<Note>
  在这种情况下，`claude doctor` 会将 Search 显示为 OK。
</Note>

**解决方案：**

1. **提交更具体的搜索**：通过指定目录或文件类型，减少搜索的文件数量：“在 auth-service 软件包中搜索 JWT 验证逻辑”或“查找 JS 文件中对 md5 哈希的使用”。

2. **将项目移到 Linux 文件系统**：如果可以，请确保项目位于 Linux 文件系统（`/home/`），而不是 Windows 文件系统（`/mnt/c/`）。

3. **改用原生 Windows**：考虑在 Windows 上原生运行 Claude Code，而不是通过 WSL 运行，以获得更好的文件系统性能。

## 获取更多帮助

如果你遇到本页面未介绍的问题：

1. 运行 `/doctor` 进行设置检查，并运行 `/mcp` 检查 MCP 服务器状态
2. 在 Claude Code 内使用 `/feedback` 命令，直接向 Anthropic 报告问题
3. 查看 [GitHub 仓库](https://github.com/anthropics/claude-code)中的已知问题
4. 直接询问 Claude 的能力和功能。Claude 内置了对其文档的访问能力。

对于账户、账单或订阅问题，请改为联系 Anthropic 支持：登录 [claude.ai](https://claude.ai)（Console 用户登录 [platform.claude.com](https://platform.claude.com)），点击左下角姓名首字母，然后选择 **Get help**。有关完整流程（包括每个计划中的哪些用户可以联系人工客服），请参阅[如何获取支持](https://support.claude.com/en/articles/9015913-how-to-get-support)。

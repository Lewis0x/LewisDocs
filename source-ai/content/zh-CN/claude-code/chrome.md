---
title: 将 Claude Code 与 Chrome 配合使用
source_id: claude-code/chrome
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/chrome
owner: Anthropic
content_sha256: 5a950a736c9b5b79672a8f447173e0dffccbf0a08427ec34a3633200b31586d9
translation_of: claude-code/chrome
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/chrome)

Content owner: Anthropic

> ## 文档索引
> 在以下地址获取完整的文档索引：https://code.claude.com/docs/llms.txt
> 在深入探索之前，请使用此文件发现所有可用页面。

# 将 Claude Code 与 Chrome 配合使用

> 将 Claude Code 连接到你的 Chrome 浏览器，以测试 Web 应用、使用控制台日志进行调试、自动填充表单，以及从网页中提取数据。

Claude Code 与 [Claude in Chrome 浏览器扩展](https://chromewebstore.google.com/detail/claude/fcoeoabgfenejglbffodgkkbkcdhcgfn) 集成，让你能够从 CLI 或 [VS Code 扩展](/docs/en/vs-code#automate-browser-tasks-with-chrome) 获得浏览器自动化能力。编写代码，然后在浏览器中测试和调试，无需切换上下文。

Claude 会为浏览器任务打开新标签页，并共享你浏览器的登录状态，因此它可以访问你已登录的任何网站。浏览器操作在可见的 Chrome 窗口中实时运行。当 Claude 遇到登录页面或验证码时，它会暂停并要求你手动处理。

<Note>
  Chrome 集成支持 Google Chrome 和 Microsoft Edge。Claude Code 还会检测扩展程序并在其他基于 Chromium 的浏览器中建立连接，包括 Brave、Arc、Vivaldi 和 Opera。Chrome 集成在 Windows Subsystem for Linux (WSL) 中不受支持。
</Note>

## 功能

连接 Chrome 后，你可以在单个工作流中将浏览器操作与编码任务串联起来：

* **实时调试**：直接读取控制台错误和 DOM 状态，然后修复导致这些问题的代码
* **设计验证**：根据 Figma 设计稿构建 UI，然后在浏览器中打开以验证其是否匹配
* **Web 应用测试**：测试表单验证、检查视觉回归，或验证用户流程
* **已认证的 Web 应用**：与 Google Docs、Gmail、Notion 或你已登录的任何应用交互，无需 API 连接器
* **数据提取**：从网页中提取结构化信息并保存到本地
* **任务自动化**：自动化重复的浏览器任务，如数据录入、表单填充或多站点工作流
* **文件上传**：将本地文件附加到网页上的上传字段
* **会话录制**：将浏览器交互录制为 GIF，用于记录或分享操作过程

## 先决条件

在将 Claude Code 与 Chrome 配合使用之前，你需要：

* [Google Chrome](https://www.google.com/chrome/)、[Microsoft Edge](https://www.microsoft.com/edge)，或其他基于 Chromium 的浏览器，如 Brave、Arc、Vivaldi 或 Opera
* [Claude in Chrome 扩展程序](https://chromewebstore.google.com/detail/claude/fcoeoabgfenejglbffodgkkbkcdhcgfn) 版本 1.0.36 或更高，可在 Chrome 网上应用店获取
* [Claude Code](/docs/en/quickstart#step-1-install-claude-code)
* 直接的 Anthropic 套餐（Pro、Max、Team 或 Enterprise）

Chrome 集成还需要使用 `/login` 登录。如果你使用 API 密钥或来自 [`claude setup-token`](/docs/en/authentication#generate-a-long-lived-token) 的长期有效令牌进行身份验证，Claude Code 会保持 Chrome 集成关闭，即使你传递了 `--chrome`，因为浏览器扩展程序无法使用这些凭据进行身份验证。在 v2.1.216 版本之前，这些会话可以启用 Chrome 集成，但每次尝试连接浏览器扩展程序时都会因 403 错误而失败。

<Note>
  Chrome 集成不可通过 Amazon Bedrock、Google Cloud's Agent Platform 或 Microsoft Foundry 等第三方提供商使用。如果你仅通过第三方提供商访问 Claude，则需要一个单独的 claude.ai 账户才能使用此功能。
</Note>

## 在 CLI 中入门

<Steps>
  <Step title="使用 Chrome 启动 Claude Code">
    使用 `--chrome` 标志启动 Claude Code：

    ```bash theme={null}
    claude --chrome
    ```

    首次使用 Chrome 启动时，Claude Code 会显示一个一次性对话框，介绍该集成并说明网站权限的工作原理。按 Enter 键继续。

    要在不使用该标志的情况下为未来的会话启用 Chrome，请参阅 [默认启用 Chrome](#enable-chrome-by-default)。
  </Step>

  <Step title="让 Claude 使用浏览器">
    此示例从您的终端或编辑器中导航到页面，与其进行交互，并报告其发现的内容：

    ```text theme={null}
    Go to code.claude.com/docs, click on the search box,
    type "hooks", and tell me what results appear
    ```

    首次浏览器操作会请求使用 `claude-in-chrome` 技能的权限。批准后，Claude 将打开一个新标签页并开始任务。
  </Step>
</Steps>

随时运行 `/chrome` 以检查连接状态、管理权限、重新连接扩展程序，或选择要使用的已连接浏览器。当状态面板显示“Status: Enabled”和“Extension: Installed”时，表示集成正在运行。如果在浏览器操作开始时连接了多个浏览器，Claude 会提示您选择一个。

对于 VS Code，请参阅 [VS Code 中的浏览器自动化](/docs/en/vs-code#automate-browser-tasks-with-chrome)。

### 在 Claude 提示时安装扩展

当 Claude 在交互式会话中需要使用您的浏览器来执行任务，并且 Claude Code 未检测到该扩展时，Claude Code 会显示标题为“Claude 想使用您的浏览器”的安装提示，每个会话最多显示一次。该提示要求 Claude Code v2.1.206 或更高版本。在 Windows 上，**安装扩展**选项需要 v2.1.211 或更高版本；在 v2.1.211 之前，选择该选项无法打开安装页面。

该提示提供三个选项：

* **安装扩展**：在您的浏览器中打开扩展安装页面并开始引导式设置。 Claude Code 等待安装完成，连接扩展，并在同一会话中启用浏览器工具。连接准备就绪后，选择“继续使用浏览器工具”，Claude 将在您的浏览器中恢复任务。您可以随时选择“在没有浏览器工具的情况下继续”以退出设置，并在稍后使用 `/chrome` 完成。
* **暂不**：在没有浏览器工具的情况下继续任务。提示可能会在以后的会话中再次出现。
* **不再询问**：在所有未来的会话中停止该提示。您仍然可以随时使用 `/chrome` 设置集成。

如果您的组织阻止了 `claude-in-chrome` MCP 服务器，并使用了 [`deniedMcpServers` 托管设置](/docs/en/managed-mcp#policy-based-control-with-allowlists-and-denylists), Claude Code 将不显示安装提示。

### 默认启用 Chrome

为了避免在每次会话中传递 `--chrome`，请运行 `/chrome` 并选择“默认启用”。

当 Chrome 未运行时，Claude Code 会正常启动。在 v2.1.211 版本之前，如果启用了 Chrome 集成但 Chrome 未运行，启动过程可能会卡住。

在 [VS Code 扩展](/docs/en/vs-code#automate-browser-tasks-with-chrome) 中，只要安装了 Chrome 扩展，就可以使用 Chrome。不需要额外的标志。

<Note>
  在 CLI 中默认启用 Chrome 会增加上下文的使用量，因为浏览器工具会一直被加载。如果您发现上下文消耗增加，请禁用此设置并仅在需要时使用 `--chrome`。
</Note>

### 管理网站权限

网站级别的权限继承自 Chrome 扩展。在 Chrome 扩展设置中管理权限，以控制 Claude 可以浏览、点击和输入哪些网站。

### 计划模式下的浏览器工具

在 [计划模式](/docs/en/permission-modes#analyze-before-you-edit-with-plan-mode) 下，仅读取页面或浏览器状态的浏览器工具调用在运行时不会弹出权限提示，而更改状态的调用则会提示请求批准。

* **只读调用**：`read_page`、`get_page_text`、`find`、读取控制台消息或网络请求，以及截取屏幕截图
* **状态更改调用**：点击、输入、导航、标签页和窗口管理，以及录制 GIF

从 v2.1.199 版本开始，原本为只读的调用如果设置了更改状态的输入标志（例如 `tabs_context_mcp` 上的 `createIfEmpty`、控制台和网络读取器上的 `clear`，或屏幕截图上的 `save_to_disk`），也会提示请求批准。只有当 `browser_batch` 调用内部的每个操作都是只读时，该调用才会在不提示的情况下运行。

## 示例工作流

这些示例展示了将浏览器操作与编码任务相结合的常见方式。运行 `/mcp`，选择 `claude-in-chrome`，然后选择 **查看工具** 以查看可用浏览器工具的完整列表。

### 测试本地 Web 应用程序

在开发 Web 应用程序时，让 Claude 验证您的更改是否正常工作：

```text theme={null}
I just updated the login form validation. Can you open localhost:3000,
try submitting the form with invalid data, and check if the error
messages appear correctly?
```

Claude 导航到您的本地服务器，与表单进行交互，并报告其观察到的结果。

### 使用控制台日志进行调试

Claude 可以读取控制台输出以帮助诊断问题。告诉 Claude 要查找哪些模式，而不是索要所有控制台输出，因为日志可能非常冗长：

```text theme={null}
Open the dashboard page and check the console for any errors when
the page loads.
```

Claude 读取控制台消息，并可以筛选特定的模式或错误类型。

### 自动填写表单

加快重复性的数据录入任务：

```text theme={null}
I have a spreadsheet of customer contacts in contacts.csv. For each row,
go to the CRM at crm.example.com, click "Add Contact", and fill in the
name, email, and phone fields.
```

Claude 读取您的本地文件，导航 Web 界面，并为每条记录输入数据。

### 上传文件到网页

Claude 可以将您机器上的文件附加到页面的上传字段中。 Claude Code 读取文件并将其内容发送给浏览器，因此上传在本地和远程会话中均可进行。需要 Claude Code v2.1.211 或更高版本。

此示例将一个日志文件附加到表单中：

```text theme={null}
Open the bug tracker at bugs.example.com, create a new issue,
and attach logs/session.log to it
```

上传有以下三个限制：

* **权限**：Claude 只有在会话被允许读取文件时才能上传文件，因此 [权限规则](/docs/en/settings#permission-settings) 拒绝 `Read` 访问文件也会阻止上传该文件。
* **大小**：单次上传最多可包含总计 10 MB 的文件。
* **硬链接**：Claude 会拒绝具有多个硬链接的文件，这在像 `node_modules` 这样的包管理器存储区中很常见。请复制该文件并上传副本。

### 在 Google Docs 中起草内容

使用 Claude 直接在您的文档中编写，无需设置 API：

```text theme={null}
Draft a project update based on the recent commits and add it to my
Google Doc at docs.google.com/document/d/abc123
```

Claude 会打开文档，点击进入编辑器，并输入内容。这适用于您已登录的任何网络应用程序：Gmail、Notion、Sheets 等。

### 从网页中提取数据

从网站提取结构化信息：

```text theme={null}
Go to the product listings page and extract the name, price, and
availability for each item. Save the results as a CSV file.
```

Claude 会导航至页面，读取内容，并将数据汇总为结构化格式。

### 运行多站点工作流

跨多个网站协调任务：

```text theme={null}
Check my calendar for meetings tomorrow, then for each meeting with
an external attendee, look up their company website and add a note
about what they do.
```

Claude 会跨标签页工作以收集信息并完成工作流。

### 录制演示 GIF

创建可共享的浏览器交互记录：

```text theme={null}
Record a GIF showing how to complete the checkout flow, from adding
an item to the cart through to the confirmation page.
```

Claude 会记录交互序列并将其保存为 GIF 文件。该记录会捕获浏览器中所有可见的内容，包括已登录页面上的账户详细信息，因此在将其分享给团队外部之前，请先进行审查。

### 将屏幕截图保存到磁盘

要求 Claude 将屏幕截图保留为文件：

```text theme={null}
Take a screenshot of the checkout page and save it to disk
```

Claude 会将图像保存到磁盘并报告文件路径。在 v2.1.211 之前，屏幕截图工具的 `save_to_disk` 选项不会写入文件。

## 疑难解答

### 未检测到扩展

如果 Claude Code 无法检测到 Chrome 扩展：

1. 验证 Chrome 扩展是否已安装并在 `chrome://extensions` 中启用
2. 通过运行 `claude --version` 验证 Claude Code 是否为最新版本
3. 检查 Chrome 是否正在运行
4. 运行 `/chrome` 并选择“重新连接扩展”以重新建立连接
5. 如果问题仍然存在，请重启 Claude Code 和 Chrome

首次启用 Chrome 集成时，Claude Code 会安装一个原生消息主机配置文件。Chrome 在启动时读取此文件，因此如果首次尝试时未检测到扩展，请重启 Chrome 以获取新配置。

从 v2.1.199 版本开始，Claude Code 仅在首次安装时会打开一个浏览器标签页，提示您连接扩展。之后重写配置文件的会话（例如，在切换 Claude Code 构建版本或配置目录后）不会重新打开它。

如果连接仍然失败，请验证主机配置文件是否存在于以下位置：

对于 Chrome：

* **macOS**: `~/Library/Application Support/Google/Chrome/NativeMessagingHosts/com.anthropic.claude_code_browser_extension.json`
* **Linux**: `~/.config/google-chrome/NativeMessagingHosts/com.anthropic.claude_code_browser_extension.json`
* **Windows**: 在 Windows 注册表中检查 `HKCU\Software\Google\Chrome\NativeMessagingHosts\`

对于 Edge：

* **macOS**: `~/Library/Application Support/Microsoft Edge/NativeMessagingHosts/com.anthropic.claude_code_browser_extension.json`
* **Linux**: `~/.config/microsoft-edge/NativeMessagingHosts/com.anthropic.claude_code_browser_extension.json`
* **Windows**: 在 Windows 注册表中检查 `HKCU\Software\Microsoft\Edge\NativeMessagingHosts\`

其他基于 Chromium 的浏览器会从各自以浏览器名称命名的配置目录中读取相同的文件。例如，macOS 上的 Brave 使用 `~/Library/Application Support/BraveSoftware/Brave-Browser/NativeMessagingHosts/`，而在 Windows 上，每个浏览器都有自己的注册表项，例如 `HKCU\Software\BraveSoftware\Brave-Browser\NativeMessagingHosts\`。

### 浏览器无响应

如果 Claude 的浏览器命令停止工作：

1. 检查是否有模态对话框（alert、confirm、prompt）阻塞了页面。JavaScript 对话框会阻塞浏览器事件，并阻止 Claude 接收命令。手动关闭对话框，然后告诉 Claude 继续。
2. 要求 Claude 创建一个新标签页并重试
3. 通过在 `chrome://extensions` 中禁用并重新启用 Chrome 扩展来重启它

### 长会话期间连接断开

Chrome 扩展的 service worker 在长时间会话期间可能会进入空闲状态，从而中断连接。如果浏览器工具在一段时间的非活动状态后停止工作，请运行 `/chrome` 并选择“重新连接扩展”。

### Windows 特有问题

在 Windows 上，您可能会遇到：

* **命名管道冲突 (EADDRINUSE)**: 如果另一个进程正在使用相同的命名管道，请重启 Claude Code。关闭可能正在使用 Chrome 的任何其他 Claude Code 会话。
* **原生消息主机错误**: 如果原生消息主机在启动时崩溃，请尝试重新安装 Claude Code 以重新生成主机配置。
* **设置页面无法打开**: {/* min-version: 2.1.211 */}更新 Claude Code。在 v2.1.211 版本之前，提示您连接扩展的浏览器标签页可能在 Windows 上无法打开。

### 常见错误消息

这些是最常遇到的错误及其解决方法：

| 错误                                         | 原因                                            | 修复                                                             |
| ------------------------------------------- | ------------------------------------------------ | --------------------------------------------------------------- |
| "Browser extension is not connected"                           | 原生消息主机无法连接到扩展                        | 重启 Chrome 和 Claude Code，然后运行 `/chrome` 重新连接 |
| 扩展在 `/chrome` 中显示"Not detected" | Chrome 扩展未安装或已被禁用                       | 在 `chrome://extensions` 中安装或启用该扩展                  |
| "No tab available"                           | Claude 在标签页就绪前尝试操作                     | 要求 Claude 创建一个新标签页并重试                         |
| "Receiving end does not exist"                               | 扩展 service worker 已进入空闲状态               | 运行 `/chrome` 并选择“重新连接扩展”                   |

## 另请参阅

* [计算机使用](/docs/en/computer-use): 当任务无法在浏览器中完成时，控制原生 macOS 应用
* [在 VS Code 中使用 Claude Code](/docs/en/vs-code#automate-browser-tasks-with-chrome)：VS Code 扩展中的浏览器自动化
* [CLI参考](/docs/en/cli-reference): 命令行标志包括 `--chrome`
* [常见工作流](/docs/en/common-workflows)：更多使用 Claude Code 的方式
* [数据与隐私](/docs/en/data-usage)：Claude Code如何处理您的数据
* [在 Chrome 中开始使用 Claude](https://support.claude.com/en/articles/12012173-getting-started-with-claude-in-chrome): Chrome 扩展程序的完整文档，包括快捷键、日程安排和权限

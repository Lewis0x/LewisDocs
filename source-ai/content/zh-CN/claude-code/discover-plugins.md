---
title: 通过市场发现并安装预构建的插件
source_id: claude-code/discover-plugins
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/discover-plugins
owner: Anthropic
content_sha256: 26886c4d4253e15510a59ef269d0bb102e6290851789b628f8e7dde926367c49
translation_of: claude-code/discover-plugins
translation_model: k3
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/discover-plugins)

Content owner: Anthropic

> ## 文档索引
> 在此获取完整的文档索引： https://code.claude.com/docs/llms.txt
> 在深入探索之前，请使用此文件来发现所有可用的页面。

# 通过市场发现并安装预构建的插件

> 从市场查找并安装插件，以通过新的技能、代理和功能来扩展 Claude Code。

插件通过技能、代理、挂钩和 MCP 服务器来扩展 Claude Code。插件市场是帮助您发现并安装这些扩展的目录，而无需您亲自构建。

想要创建并分发您自己的市场？请参阅 [创建并分发插件市场](/docs/en/plugin-marketplaces)。

## 市场的工作原理

市场是其他人创建并共享的插件目录。使用市场分为两步：

<Steps>
  <Step title="添加市场">
    这将在 Claude Code 中注册目录，以便您浏览可用内容。目前尚未安装任何插件。
  </Step>

  <Step title="安装单个插件">
    浏览目录并安装您想要的插件。
  </Step>
</Steps>

可以把它想象成添加应用商店：添加商店让您可以浏览其集合，但您仍需单独选择要下载的应用。

## Anthropic 官方市场

当您启动 Claude Code 时，Anthropic 官方市场（`claude-plugins-official`）会自动可用。运行 `/plugin` 并转到 **发现** 选项卡以浏览可用内容，或在 [claude.com/plugins](https://claude.com/plugins) 查看目录。

要从官方市场安装插件，请使用 `/plugin install <name>@claude-plugins-official`。例如，要安装 GitHub 集成：

```shell theme={null}
/plugin install github@claude-plugins-official
```

`/plugin` 会在终端 CLI 中打开一个交互式面板。如果 Claude 回复说 `/plugin` 在此环境中不可用，请在 Claude 桌面应用程序中使用 [插件浏览器](/docs/en/desktop#install-plugins)，或者对于云会话，在 `.claude/settings.json` 中的 [`enabledPlugins`](/docs/en/settings#enabledplugins) 下声明插件。

如果 Claude Code 报告 `Marketplace "claude-plugins-official" not found`，请使用 `/plugin marketplace add anthropics/claude-plugins-official` 添加市场。如果报告在市场中找不到该插件，说明您的本地副本已过时：请使用 `/plugin marketplace update claude-plugins-official` 刷新。然后重试安装。

<Note>
  官方市场由 Anthropic 精心挑选，收录内容由 Anthropic 自行决定。应用内的提交表单会将插件添加到 [社区市场](#community-marketplace)，而不是官方市场。要独立分发插件，请 [创建您自己的市场](/docs/en/plugin-marketplaces) 并与用户分享。
</Note>

官方市场包含几个类别的插件：

### 代码智能

代码智能插件启用了 Claude Code 的内置 LSP 工具，使 Claude 能够在编辑后立即跳转到定义、查找引用并查看类型错误。这些插件配置 [语言服务器协议](https://microsoft.github.io/language-server-protocol/) 连接，这与为 VS Code 的代码智能提供支持的技术相同。

这些插件要求您的系统上安装语言服务器二进制文件。如果您已经安装了语言服务器，当您打开项目时，Claude 可能会提示您安装相应的插件。

| 语言       | 插件                | 所需二进制文件                |
| :--------- | :------------------ | :--------------------------- |
| C/C++      | `clangd-lsp`        | `clangd`                     |
| C#         | `csharp-lsp`        | `csharp-ls`                  |
| Go         | `gopls-lsp`         | `gopls`                      |
| Java       | `jdtls-lsp`         | `jdtls`                      |
| Kotlin     | `kotlin-lsp`        | `kotlin-language-server`     |
| Lua        | `lua-lsp`           | `lua-language-server`        |
| PHP        | `php-lsp`           | `intelephense`               |
| Python     | `pyright-lsp`       | `pyright-langserver`         |
| Rust       | `rust-analyzer-lsp` | `rust-analyzer`              |
| Swift      | `swift-lsp`         | `sourcekit-lsp`              |
| TypeScript | `typescript-lsp`    | `typescript-language-server` |

您也可以为其他语言 [创建您自己的 LSP 插件](/docs/en/plugins-reference#lsp-servers)。

<Note>
  如果在安装插件后，您在 `/plugin` 的“错误”选项卡中看到 `Executable not found in $PATH`，请从上表中安装所需的二进制文件。
</Note>

#### Claude 从代码智能插件中获得的功能

一旦安装了代码智能插件并且其语言服务器二进制文件可用，Claude 将获得两项能力：

* **自动诊断**：在 Claude 每次编辑文件后，语言服务器会分析更改并自动回报错误和警告。Claude 能够看到类型错误、缺失的导入和语法问题，而无需运行编译器或 linter。如果 Claude 引入了错误，它会在同一轮次中注意到并修复该问题。除了安装插件外，这不需要任何配置。当出现“找到诊断信息”指示器时，您可以按 **Ctrl+O** 内联查看诊断信息。
* **代码导航**：Claude 可以使用语言服务器跳转到定义、查找引用、获取悬停时的类型信息、列出符号、查找实现并跟踪调用层次结构。与基于 grep 的搜索相比，这些操作为 Claude 提供了更精确的导航能力，尽管其可用性可能因语言和环境而异。

如果遇到问题，请参阅 [代码智能故障排除](#code-intelligence-issues)。

### 外部集成

这些插件捆绑了预配置的 [MCP 服务器](/docs/en/mcp)，因此您无需手动设置即可将 Claude 连接到外部服务：

* **源代码控制**：`github`, `gitlab`
* **项目管理**：`atlassian` (Jira/Confluence), `asana`, `linear`, `notion`
* **设计**：`figma`
* **基础设施**：`vercel`, `firebase`, `supabase`
* **沟通**：`slack`
* **监控**：`sentry`

### 自动安全审查

`security-guidance` 插件会审查 Claude 所做的每项更改是否存在常见漏洞，并指示 Claude 在同一会话中修复发现的问题。有关它检查的内容以及如何添加项目特定规则，请参阅 [在 Claude 编写代码时捕获安全问题](/docs/en/security-guidance)。

### 开发工作流

用于为常见开发任务添加技能和代理的插件：

* **commit-commands**：Git 提交工作流，包括提交、推送和创建 PR
* **pr-review-toolkit**：用于审查拉取请求的专用代理
* **agent-sdk-dev**：使用 Claude Agent SDK 进行构建的工具
* **plugin-dev**：用于创建您自己的插件的工具包

### 输出样式

自定义 Claude 的响应方式：

* **explanatory-output-style**：关于实现选择的教育性见解
* **learning-output-style**：用于技能培养的交互式学习模式

## 社区市场

位于 [`anthropics/claude-plugins-community`](https://github.com/anthropics/claude-plugins-community) 的社区市场托管了已通过 Anthropic 自动验证和安全筛查的第三方插件。目录中的每个插件都固定到特定的提交 SHA。与官方市场不同，您需要手动添加它：

```shell theme={null}
/plugin marketplace add anthropics/claude-plugins-community
```

然后使用 `claude-community` 市场名称从中安装插件：

```shell theme={null}
/plugin install <plugin-name>@claude-community
```

要将自己的插件提交到社区市场，请参阅 插件创建指南中的 [将您的插件提交到社区市场](/docs/en/plugins#submit-your-plugin-to-the-community-marketplace)。

## 试一试：添加演示市场

Anthropic 还维护着一个 [演示插件市场](https://github.com/anthropics/claude-code/tree/main/plugins) (`claude-code-plugins`)，其中包含展示了插件系统功能的示例插件。与官方市场不同，您需要手动添加此市场。

<Steps>
  <Step title="添加市场">
    在 Claude Code 内，为 `anthropics/claude-code` 市场运行 `plugin marketplace add` 命令：

    ```shell theme={null}
    /plugin marketplace add anthropics/claude-code
    ```

    这将下载市场目录并使其插件可供您使用。
  </Step>

  <Step title="浏览可用插件">
    运行 `/plugin` 以打开插件管理器。这将打开一个带有四个选项卡的标签式界面，您可以使用 **Tab** 键在它们之间循环切换，或使用 **Shift+Tab** 键后退：

    * **发现**：浏览来自您所有市场的可用插件
    * **已安装**：查看和管理您已安装的插件
    * **市场**：添加、删除或更新您已添加的市场
    * **错误**：查看任何插件加载错误

    转到 **发现** 选项卡以查看您刚刚添加的市场中的插件。{/* min-version: 2.1.154 */}当您的管理员通过 [`pluginSuggestionMarketplaces`](/docs/en/settings#available-settings) 托管设置将市场列入白名单时，标记为与您当前工作目录相关的插件将被置顶，并带有 **推荐用于此目录** 标签。
  </Step>

  <Step title="安装插件">
    选择一个插件以查看其详细信息。详细信息窗格显示了该插件包含的内容及其成本：

    * {/* min-version: 2.1.143 */}一个 **上下文成本** 估算，让您可以看到该插件每轮将向您的 [上下文窗口](/docs/en/features-overview#understand-context-costs) 添加多少令牌（Claude Code v2.1.143 及更高版本）
    * {/* min-version: 2.1.144 */}插件的 **最后更新** 日期 (v2.1.144 及更高版本)
    * {/* min-version: 2.1.145 */}一个 **将安装** 部分，列出了插件的命令、代理、技能、挂钩以及 MCP 和 LSP 服务器，以便您在安装前准确审查它添加了什么 (v2.1.145 及更高版本)

    选择安装范围：

    * **用户范围**：为您自己在所有项目中安装
    * **项目范围**：为此存储库的所有协作者安装
    * **本地范围**：仅为您自己在此存储库中安装

    例如，选择 **commit-commands**（一个添加了 git 工作流技能的插件），并将其安装到您的用户范围。

    您也可以从命令行开始安装：

    ```shell theme={null}
    /plugin install commit-commands@claude-code-plugins
    ```

    请参阅 [配置范围](/docs/en/settings#configuration-scopes) 以了解更多关于范围的信息。
  </Step>

  <Step title="使用你的新插件">
    安装后，运行 `/reload-plugins` 以激活插件。插件技能以插件名为命名空间，因此 **commit-commands** 提供了类似 `/commit-commands:commit` 的技能。

    尝试修改一个文件并运行：

    ```shell theme={null}
    /commit-commands:commit
    ```

    这将暂存你的更改，生成提交信息，并创建提交。

    每个插件的运作方式都不同。在 **发现** 选项卡中查看插件详情，了解其提供的命令和技能，或访问其主页获取使用指南。
  </Step>
</Steps>

本指南的其余部分介绍了添加市场、安装插件以及管理配置的所有方法。

## 添加市场

使用 `/plugin marketplace add` 命令从不同来源添加市场。

<Tip>
  **快捷方式**：你可以使用 `/plugin market` 代替 `/plugin marketplace`，以及使用 `rm` 代替 `remove`。
</Tip>

* **GitHub 仓库**：`owner/repo` 格式，例如 `anthropics/claude-code`
* **Git URL**：任何 git 仓库 URL，包括 GitLab、Bitbucket 和自托管服务器
* **本地路径**：目录或指向 `marketplace.json` 文件的直接路径
* **远程 URL**：指向托管的 `marketplace.json` 文件的直接 URL

### 从 GitHub 添加

使用 `owner/repo` 格式添加包含 `.claude-plugin/marketplace.json` 文件的 GitHub 仓库，其中 `owner` 是 GitHub 用户名或组织，而 `repo` 是仓库名称。

例如，`anthropics/claude-code` 指向由 `anthropics` 拥有的 `claude-code` 仓库：

```shell theme={null}
/plugin marketplace add anthropics/claude-code
```

### 从其他 Git 托管平台添加

通过提供完整的 URL 来添加任何 git 仓库。这适用于任何 Git 托管平台，包括 GitLab、Bitbucket 和自托管服务器。请包含 `.git` 后缀，以便 Claude Code 克隆该仓库，而不是将 URL 视为指向托管的 `marketplace.json` 文件的直接链接。

请同时包含 `https://` 前缀。Claude Code v2.1.196 及更高版本会将没有添加前缀的域名（例如 `gitlab.com/company/plugins.git`）视为无效的 GitHub `owner/repo` 简写而拒绝，并且错误提示会要求你添加前缀。早期版本会将其误读为 GitHub 仓库路径，并在克隆时失败。

使用 HTTPS：

```shell theme={null}
/plugin marketplace add https://gitlab.com/company/plugins.git
```

使用 SSH：

```shell theme={null}
/plugin marketplace add git@gitlab.com:company/plugins.git
```

要添加特定的分支或标签，请在后面追加 `#` 并接上该引用：

```shell theme={null}
/plugin marketplace add https://gitlab.com/company/plugins.git#v1.0.0
```

### 从本地路径添加

添加一个包含 `.claude-plugin/marketplace.json` 文件的本地目录：

```shell theme={null}
/plugin marketplace add ./my-marketplace
```

你也可以添加指向 `marketplace.json` 文件的直接路径：

```shell theme={null}
/plugin marketplace add ./path/to/marketplace.json
```

### 从远程 URL 添加

通过 URL 添加远程 `marketplace.json` 文件：

```shell theme={null}
/plugin marketplace add https://example.com/marketplace.json
```

<Note>
  与基于 Git 的市场相比，基于 URL 的市场有一些限制。如果你在安装插件时遇到“path not found”错误，请参阅 [故障排除](/docs/en/plugin-marketplaces#plugins-with-relative-paths-fail-in-url-based-marketplaces)。
</Note>

## 安装插件

添加市场后，你可以直接安装插件：

```shell theme={null}
/plugin install plugin-name@marketplace-name
```

该命令会打开该插件的详细信息，你可以在其中选择[安装范围](/docs/en/settings#configuration-scopes)。当你运行`/plugin`，转到**发现**选项卡，并在插件上按下**回车键**时，你会看到相同的选项：

* **用户范围**：为你在所有项目中安装
* **项目范围**：为此存储库的所有协作者安装，这会将插件添加到`.claude/settings.json`
* **本地范围**：仅在此存储库中为你自己安装，不与协作者共享

要在没有交互步骤的情况下进行安装，请使用[`claude plugin install`](/docs/en/plugins-reference#plugin-install) 命令行命令，除非你传递`--scope`，否则它将安装到用户范围。

你可能还会看到具有**受管**范围的插件。这些插件由管理员通过[受管设置](/docs/en/settings#settings-files)进行安装，并且无法修改。

安装后，运行`/reload-plugins`以在当前会话中激活插件。

<Warning>
  在安装插件之前，请确保你信任它。Anthropic 不控制插件中包含哪些 MCP 服务器、文件或其他软件，也无法验证它们是否能按预期工作。查看每个插件的主页以获取更多信息。
</Warning>

## 管理已安装的插件

运行`/plugin`并转到**已安装**选项卡以查看、启用、禁用或卸载你的插件。列表按范围分组并排序，以便你首先看到问题：有加载错误或未解析依赖项的插件显示在顶部，其次是你的收藏夹，禁用的插件折叠在底部的折叠标题后面。

从列表中你可以：

* 按下`f`以收藏或取消收藏选中的插件
* 输入以按插件名称或描述进行筛选
* 按回车键打开插件的详细视图并启用、禁用或卸载它

卸载由项目的`.claude/settings.json`启用的插件时，系统会询问你所指的范围：是仅为你自己禁用它（这会将覆盖配置写入你的`.claude/settings.local.json`并保留该插件为项目的安装状态），还是为所有人卸载它（这会将其从共享的`.claude/settings.json`中移除）。需要Claude Code v2.1.203 或更高版本。在 v2.1.203 之前，对话框仅提供本地禁用选项。

详细视图显示了插件提供的组件：命令、技能、代理、挂钩、MCP 服务器和 LSP 服务器。使用`claude plugin details`可以在命令行中获取相同的清单。

**已安装**选项卡还会将你自己安装但至少两周未使用（跨越至少 10 个会话）的市场插件，收集到**最近未使用**标题下。详细视图为每个插件显示一行**最后使用**时间。利用这些信息可以找出那些你不再使用但仍会增加启动和上下文成本的插件，然后将它们禁用或卸载。需要Claude Code v2.1.187 或更高版本。

有两种插件永远不会被列为未使用：

* 由你的组织管理或你使用`--plugin-dir`加载的插件
* 提供主题、输出样式、监视器或工作流的插件，因为它们在没有可跟踪调用的情况下也能提供价值

当你的组织使用[`strictKnownMarketplaces`](/docs/en/settings#strictknownmarketplaces)限制市场时，**最近未使用**标题和**最后使用**行都会被隐藏。

当插件的[语言服务器](/docs/en/plugins#add-lsp-servers-to-your-plugin)提供诊断或响应代码导航请求时，即算作已使用，因此服务器在你的会话中处于活动状态的 LSP 插件不会被列为未使用。在 v2.1.203 之前，语言服务器活动无法被计入使用量，因此提供 LSP 服务器的插件完全不受此分组限制，就像目前主题和输出样式插件一样。

在统计语言服务器活动的版本上的首次会话，也会重置每个尚未记录任何使用的 LSP 插件的使用记录，这样 Claude Code 就不会根据在其服务器活动被追踪之前记录的数据，将您早先安装的插件判定为未使用。在 v2.1.206 之前，该首次会话可能会在 **最近未使用** 下列出正在积极使用的 LSP 插件，并建议您审查它。

当您安装声明了依赖项的插件时，安装输出会列出随其一起自动安装的依赖项。

您也可以使用直接命令来管理插件。

列出已安装的插件而无需打开菜单：

```shell theme={null}
/plugin list
```

传递 `--enabled` 或 `--disabled` 以仅显示处于该状态的插件。

在不卸载的情况下禁用插件：

```shell theme={null}
/plugin disable plugin-name@marketplace-name
```

重新启用已禁用的插件：

```shell theme={null}
/plugin enable plugin-name@marketplace-name
```

在这些标识符中，`plugin-name` 是插件的 `name`（在 [市场条目](/docs/en/plugin-marketplaces#plugin-entries) 中），这可能不同于 `name`（在插件自身的 `plugin.json` 中）。

从 Claude Code v2.1.195 开始，`/plugin` 界面中的**启用**和**禁用**功能适用于两个名称不同的插件，并且 `/plugin enable` 和 `/plugin disable` 接受其中任何一个名称。当您在早期版本中禁用此类插件时，Claude Code 会报告 `already disabled` 并保持其启用状态。

完全移除插件：

```shell theme={null}
/plugin uninstall plugin-name@marketplace-name
```

`--scope` 选项允许您使用 CLI 命令来定位特定的作用域：

```shell theme={null}
claude plugin install formatter@your-org --scope project
claude plugin uninstall formatter@your-org --scope project
```

### 无需重启即可应用插件更改

当您在会话期间安装、启用或禁用插件时，运行 `/reload-plugins` 即可在不重启的情况下获取所有更改：

```shell theme={null}
/reload-plugins
```

Claude Code 会重新加载所有活动的插件，并显示插件、技能、代理、挂钩、插件 MCP 服务器和插件 LSP 服务器的数量。

重新加载会在下一次请求时产生令牌开销：新加载的组件会在追加到对话的内容中进行自我宣告，而现有的历史记录仍从提示缓存中读取。提供 MCP 服务器的插件如果其工具未被 [工具搜索](/docs/en/mcp#scale-with-mcp-tool-search) 延迟，则会消耗更多成本：此更改会使缓存失效，并且下一次请求会重新读取整个对话。 {/* min-version: 2.1.163 */}在这种情况下，`/reload-plugins` 会显示警告且不应用重新加载；请传入 `--force` 以强制应用。详情请参阅 [启用或禁用插件](/docs/en/prompt-caching#enabling-or-disabling-a-plugin)。

## 管理市场

您可以通过交互式 `/plugin` 界面或使用 CLI 命令来管理市场。

### 使用交互式界面

运行 `/plugin` 并转到 **市场** 选项卡以：

* 查看所有已添加的市场及其来源和状态
* 添加新市场
* 更新市场列表以获取最新插件
* 移除您不再需要的市场

### 使用 CLI 命令

您也可以使用直接命令来管理市场。

列出所有已配置的市场：

```shell theme={null}
/plugin marketplace list
```

从市场刷新插件列表：

```shell theme={null}
/plugin marketplace update marketplace-name
```

移除市场：

```shell theme={null}
/plugin marketplace remove marketplace-name
```

<Warning>
  移除市场将卸载您从该市场安装的任何插件。
</Warning>

### 配置自动更新

Claude Code 可以在启动后于后台自动更新市场及其已安装的插件。当为某个市场启用自动更新时，Claude Code 会刷新市场数据，并将已安装的插件更新为磁盘上的最新版本。

Claude Code 会在您的会话开始后检查市场及插件更新，并带有最多十分钟的随机延迟，因此正在运行的会话会继续使用其在启动时加载的版本。如果有插件被更新，您将看到一条提示您运行 `/reload-plugins` 的通知，或者新版本将在您下次启动时加载。

通过 UI 为各个市场切换自动更新：

1. 运行 `/plugin` 以打开插件管理器
2. 选择 **市场**
3. 从列表中选择一个市场
4. 选择 **启用自动更新** 或 **禁用自动更新**

官方 Anthropic 市场默认启用自动更新。第三方和本地开发市场默认禁用自动更新。

管理员还可以在托管设置中为每个 [`extraKnownMarketplaces`](/docs/en/settings#extraknownmarketplaces) 条目设置 `"autoUpdate": true`，从而为组织市场启用自动更新，而无需每个用户手动切换。

要完全禁用 Claude Code 和所有插件的全部自动更新，请设置 `DISABLE_AUTOUPDATER` 环境变量。详情请参阅 [自动更新](/docs/en/setup#auto-updates)。

要在禁用 Claude Code 自动更新的同时保持插件自动更新处于启用状态，请设置 `FORCE_AUTOUPDATE_PLUGINS=1` 以及 `DISABLE_AUTOUPDATER`：

```bash theme={null}
export DISABLE_AUTOUPDATER=1
export FORCE_AUTOUPDATE_PLUGINS=1
```

当您希望手动管理 Claude Code 更新但仍接收自动插件更新时，这非常有用。

## 配置团队市场

团队管理员可以通过将市场配置添加到 `.claude/settings.json` 来为项目设置自动市场安装。当团队成员信任该仓库文件夹时，Claude Code 会提示他们安装这些市场和插件。

从 Claude Code v2.1.195 版本开始，此安装步骤适用于加载插件的每个路径。如果只有项目的 `.claude/settings.json` 启用了某个插件，并且该插件来自外部源（如 GitHub 仓库或 npm 包），则在团队成员安装它之前，该插件不会加载。在此之前，Claude Code 会报告该插件未安装，并显示要运行的 `claude plugin install` 命令。

将 `extraKnownMarketplaces` 添加到项目的 `.claude/settings.json` 中：

```json theme={null}
{
  "extraKnownMarketplaces": {
    "my-team-tools": {
      "source": {
        "source": "github",
        "repo": "your-org/claude-plugins"
      }
    }
  }
}
```

有关完整的配置选项（包括 `extraKnownMarketplaces` 和 `enabledPlugins`），请参见 [插件设置](/docs/en/settings#plugin-settings)。

## 安全

插件和市场是受高度信任的组件，可以使用您的用户权限在您的计算机上执行任意代码。仅从您信任的来源安装插件和添加市场。组织可以使用 [受管市场限制](/docs/en/plugin-marketplaces#managed-marketplace-restrictions) 来限制允许用户添加的市场。

## 故障排除

### /plugin 命令无法识别

如果您看到“unknown command”或 `/plugin` 命令未出现：

1. **检查您的版本**：运行 `claude --version` 查看已安装的内容。
2. **更新 Claude Code**：
   * **Homebrew**：`brew upgrade claude-code`，或者如果您安装了该 cask，请使用 `brew upgrade claude-code@latest`
   * **npm**：`npm install -g @anthropic-ai/claude-code@latest`
   * **原生安装程序**：从 [安装设置](/docs/en/setup) 重新运行安装命令
3. **重启 Claude Code**：更新后，重启您的终端并再次运行 `claude`。

### 常见问题

* **市场无法加载**：验证 URL 是否可访问，以及该路径下是否存在 `.claude-plugin/marketplace.json`
* **插件安装失败**：检查插件源 URL 是否可访问，以及仓库是否公开，或者您是否有权访问它们
* **安装后找不到文件**：插件会被复制到缓存中，因此引用插件目录外部文件的路径将不起作用
* **插件技能未显示**：使用 `rm -rf ~/.claude/plugins/cache` 清除缓存，重启 Claude Code，然后重新安装插件。

有关包含解决方案的详细故障排除，请参阅市场指南中的 [故障排除](/docs/en/plugin-marketplaces#troubleshooting)。有关调试工具，请参阅 [调试和开发工具](/docs/en/plugins-reference#debugging-and-development-tools)。

### 代码智能问题

* **语言服务器未启动**：验证二进制文件是否已安装并在您的 `$PATH` 中可用。查看 `/plugin` 错误选项卡以获取详细信息。
* **高内存占用**：像 `rust-analyzer` 和 `pyright` 这样的语言服务器在大型项目中可能会消耗大量内存。如果您遇到内存问题，请使用 `/plugin disable <plugin-name>` 禁用插件，并改用 Claude 内置的搜索工具。
* **单体仓库中的误报诊断**：如果工作区未正确配置，语言服务器可能会报告内部包的未解析导入错误。这些不会影响 Claude 编辑代码的能力。

## 后续步骤

* **构建您自己的插件**：请参阅 [插件](/docs/en/plugins) 来创建技能、代理和挂钩
* **创建市场**：请参阅 [创建插件市场](/docs/en/plugin-marketplaces) 向您的团队或社区分发插件
* **技术参考**：请参阅 [插件参考](/docs/en/plugins-reference) 获取完整规范

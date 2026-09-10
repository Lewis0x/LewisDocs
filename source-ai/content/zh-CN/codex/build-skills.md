---
title: 构建技能
source_id: codex/build-skills
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/build-skills
owner: OpenAI
content_sha256: 19a9f659488c9e4fd20315bfde0561d74445aacb372352d807c72ad710535d05
translation_of: codex/build-skills
translation_model: k3
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/build-skills)

Content owner: OpenAI

# 构建技能

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。通过在页面 URL 后附加 `.md`，可获取文档页面的 Markdown 版本。

使用智能体技能来扩展 ChatGPT 和 Codex 的特定任务能力。一个
技能封装了指令、资源和可选脚本，以便任一产品
能够可靠地遵循工作流。技能建立在
[开放智能体技能标准](https://agentskills.io)之上。

技能是可重用工作流的创作格式。插件通过 ChatGPT 和 Codex 共享的通用插件目录分发
可重用技能和连接器。插件可在网页版 ChatGPT Work 中使用，可在
ChatGPT 桌面应用中与 ChatGPT Work 和 Codex 一起使用，也可通过 Codex CLI 使用。使用
技能来设计工作流本身，然后将其打包为
[插件](https://developers.openai.com/plugins/build/plugins)，当你希望
其他人安装它时。

独立技能可在 ChatGPT 桌面应用、Codex CLI 和 IDE
扩展中使用。捆绑在插件中的技能也可通过受支持的
插件界面使用，包括网页版 ChatGPT Work。

在 ChatGPT 桌面应用中，打开侧边栏中的 **Skills**，以查看和探索
跨项目创建的技能。

<CodexScreenshot
  alt="显示 ChatGPT 桌面应用中可用技能的技能选择器"
  lightSrc="/images/codex/app/skill-selector-light.webp"
  darkSrc="/images/codex/app/skill-selector-dark.webp"
  maxHeight="400px"
  class="my-8"
/>

技能使用 **渐进式披露** 来高效管理上下文。ChatGPT 和
Codex 从每个技能的名称和描述开始，然后当它们决定使用该技能时加载完整的
`SKILL.md` 指令。

在 Codex 中，初始列表还包括每个技能的文件路径。为了避免
挤占提示词的其余部分，此列表最多使用模型上下文窗口的 2%，
或者在上下文窗口大小未知时使用 8,000 个字符。如果安装了许多
技能，Codex 会首先缩短技能描述。对于大型技能
集合，Codex 可能会从初始列表中省略某些技能并显示警告。

此预算仅适用于初始技能列表。当 Codex 选择某个技能时，它仍会读取该技能的完整 SKILL.md 指令。

技能是一个包含 `SKILL.md` 文件以及可选脚本和引用的目录。`SKILL.md` 文件必须包含 `name` 和 `description`。

<FileTree
  class="mt-4"
  tree={[
    {
      name: "my-skill/",
      open: true,
      children: [
        {
          name: "SKILL.md",
          comment: "必需：指令 + 元数据",
        },
        {
          name: "scripts/",
          comment: "可选：可执行代码",
        },
        {
          name: "references/",
          comment: "可选：文档",
        },
        {
          name: "assets/",
          comment: "可选：模板，资源",
        },
        {
          name: "agents/",
          open: true,
          children: [
            {
              name: "openai.yaml",
              comment: "可选：外观和依赖项",
            },
          ],
        },
      ],
    },

]}
/>

<a id="how-codex-uses-skills"></a>

## ChatGPT 和 Codex 如何使用技能

ChatGPT 和 Codex 可以通过两种方式激活技能：

1. **显式调用：** 直接在你的提示词中包含该技能。在
   ChatGPT 中，输入 `@` 来选择一个技能。在 Codex CLI 或 IDE 扩展中，运行
   `/skills` 或输入 `$` 来提及一个技能。
2. **隐式调用：** 当你的任务
   匹配该技能的 `description` 时，ChatGPT 或 Codex 可以选择一个技能。

因为隐式匹配取决于 `description`，所以要编写简洁的描述，
明确范围和边界。将关键用例和触发词放在最前面，
这样即使在描述被缩短的情况下，宿主仍然可以匹配该技能。

## 创建一个技能

如果您已经知道工作流，并且演示比描述更容易，请使用
[Record & Replay](https://learn.chatgpt.com/docs/extend/record-and-replay)。记录器会捕获
工作流，检查各个步骤，并从演示中
起草一个可重用的技能。

如果您想改为描述该技能，请使用内置的创建器。在 ChatGPT
Work 中，将其调用为 `@skill-creator`。在 Codex 中，将其调用为：

```text
$skill-creator
```

创建器会询问该技能的作用、应在什么情况下触发，以及它是应保持仅指令状态还是包含脚本。默认为仅指令。

您还可以通过创建一个包含 `SKILL.md` 文件的文件夹来手动创建技能：

```md
---
name: skill-name
description: Explain exactly when this skill should and should not trigger.
---

Skill instructions for ChatGPT or Codex to follow.
```

Codex 会自动检测技能的更改。如果未显示更新，请重启 Codex。

<a id="where-to-save-skills"></a>

## Codex 在哪里加载本地技能

Codex 从仓库、用户、管理员和系统位置读取技能。对于仓库，Codex 会扫描从当前工作目录到仓库根目录的每个目录中的 `.agents/skills`。如果两个技能共享相同的 `name`，Codex 不会合并它们；两者都可以出现在技能选择器中。

| 技能范围 | 位置                                                                                                  | 建议用途                                                                                                                                                                                        |
| :---------- | :-------------------------------------------------------------------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `REPO`      | `$CWD/.agents/skills` <br /> 当前工作目录：您启动 Codex 的地方。                           | 如果您处于仓库或代码环境中，团队可以签入与工作文件夹相关的技能。例如，仅与微服务或模块相关的技能。                              |
| `REPO`      | `$CWD/../.agents/skills` <br /> 当您在 Git 仓库内启动 Codex 时位于 CWD 上方的一个文件夹。         | 如果您处于带有嵌套文件夹的仓库中，组织可以签入与父文件夹中共享区域相关的技能。                                                                       |
| `REPO`      | `$REPO_ROOT/.agents/skills` <br /> 当您在 Git 仓库内启动 Codex 时的最顶层根文件夹。 | 如果您处于带有嵌套文件夹的仓库中，组织可以签入与使用该仓库的每个人都相关的技能。这些技能作为根技能可供仓库中的任何子文件夹使用。 |
| `USER`      | `$HOME/.agents/skills` <br /> 签入到用户个人文件夹中的任何技能。                         | 用于管理适用于用户可能工作的任何仓库的、与该用户相关的技能。                                                                                                           |
| `ADMIN`     | `/etc/codex/skills` <br /> 在共享的系统位置签入到机器或容器的任何技能。 | 用于 SDK 脚本、自动化，以及签入机器上每个用户都可用的默认管理员技能。                                                                                     |
| `SYSTEM`    | 由 OpenAI 与 Codex 捆绑。                                                                             | 与广泛受众相关的有用技能，例如 skill-creator 和 plan 技能。每个人在启动 Codex 时都可以使用。                                                                   |

Codex 支持符号链接的技能文件夹，并在扫描这些位置时跟随符号链接目标。

这些位置用于编写和本地发现。当你想要
将可重用的技能分发到单个仓库之外，或者选择将它们与
连接器捆绑在一起时，请使用 [插件](https://developers.openai.com/plugins/build/plugins)。

## 使用插件分发技能

直接技能文件夹最适合用于本地编写和仓库范围的工作流。如果
你想分发可重用的技能、将两个或多个技能捆绑在一起，或者
将技能与连接器一起发布，请将它们打包为
[插件](https://developers.openai.com/plugins/build/plugins)。

插件可以包含一个或多个技能。它们还可以选择性地将
已注册的 MCP 服务器连接、捆绑的 MCP 服务器配置，以及
呈现资源捆绑到单个包中。

## 安装精选技能供本地使用

要在内置技能之外为你自己的本地 Codex 设置添加精选技能，请使用 `$skill-installer`。例如，要安装 `$linear` 技能：

```bash
$skill-installer linear
```

你也可以提示安装程序从其他仓库下载技能。
Codex 会自动检测新安装的技能；如果没有显示，
请重启 Codex。

将此用于本地设置和实验。对于你
自己技能的可重用分发，推荐使用插件。

## 启用或禁用本地 Codex 技能

在 `~/.codex/config.toml` 中使用 `[[skills.config]]` 条目，可以在不删除技能的情况下禁用它：

```toml
[[skills.config]]
path = "/path/to/skill/SKILL.md"
enabled = false
```

更改 `~/.codex/config.toml` 后重启 Codex。

## 可选元数据

添加 `agents/openai.yaml` 以在 [ChatGPT 桌面应用](https://learn.chatgpt.com/docs/app) 中配置 UI 元数据、设置调用策略，并声明工具依赖项，从而在使用该技能时获得更无缝的体验。

```yaml
interface:
  display_name: "Optional user-facing name"
  short_description: "Optional user-facing description"
  icon_small: "./assets/small-logo.svg"
  icon_large: "./assets/large-logo.png"
  brand_color: "#3B82F6"
  default_prompt: "Optional surrounding prompt to use the skill with"

policy:
  allow_implicit_invocation: false

dependencies:
  tools:
    - type: "mcp"
      value: "openaiDeveloperDocs"
      description: "OpenAI Docs MCP server"
      transport: "streamable_http"
      url: "https://developers.openai.com/mcp"
```

`allow_implicit_invocation`（默认值：`true`）：当 `false` 时，Codex 将不会根据用户提示隐式调用技能；显式的 `$skill` 调用仍然有效。

## 最佳实践

- 保持每个技能专注于一项任务。
- 除非需要确定性行为或外部工具，否则优先选择指令而不是脚本。
- 编写具有明确输入和输出的命令式步骤。
- 根据技能描述测试提示，以确认正确的触发行为。

有关更多示例，请参阅
[GitHub CI 修复](https://github.com/openai/skills/tree/main/skills/.curated/gh-fix-ci)、
[PDF](https://github.com/openai/skills/tree/main/skills/.curated/pdf)、
[Linear](https://github.com/openai/skills/tree/main/skills/.curated/linear)、
[openai/skills](https://github.com/openai/skills) 以及
[智能体技能规范](https://agentskills.io/specification)。对于
可安装的分发，推荐使用 [插件](https://developers.openai.com/plugins/build/plugins)。

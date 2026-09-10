---
title: 本地环境
source_id: codex/environments/local-environment
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/environments/local-environment
owner: OpenAI
content_sha256: 54cd50e2188ca596e38358984892056c5162f610597408656628d1dbec11ee3a
translation_of: codex/environments/local-environment
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/environments/local-environment)

Content owner: OpenAI

# 本地环境

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。可以通过在页面 URL 后附加 `.md` 来获取文档页面的 Markdown 版本。

本地环境允许您为工作树配置设置步骤，以及项目的常见操作。

本地环境仅在 ChatGPT 桌面应用的 Codex 中可用。
  在配置或使用本地环境之前，请选择 **Codex**。

您可以通过 [ChatGPT desktop app settings](codex://settings) 面板来配置本地环境。您可以将生成的文件检入到项目的 Git 仓库中以便与他人共享。

Codex 将此配置存储在 `.codex` 文件夹中，该文件夹位于您
项目的根目录。如果您的仓库包含多个项目，请打开包含共享的
`.codex` 文件夹的项目目录。

## 设置脚本

由于工作树在与本地聊天不同的目录中运行，您的项目可能未完全设置，并且可能缺少未检入到您仓库的依赖项或文件。当 Codex 在开始新聊天时创建新工作树，设置脚本会自动运行。

使用此脚本运行配置环境所需的任何命令，例如安装依赖项或运行构建过程。

例如，对于 TypeScript 项目，您可能希望使用设置脚本安装依赖项并进行初始构建：

```bash
npm install
npm run build
```

如果您的设置是特定于平台的，请为 macOS、Windows 或 Linux 定义设置脚本以覆盖默认设置。

## 操作

<section class="feature-grid">



使用操作来定义常见任务，例如启动应用程序的开发服务器或运行测试套件。这些操作显示在 ChatGPT 桌面应用的顶部栏中，以便快速访问。这些操作在应用的 [integrated terminal](https://learn.chatgpt.com/docs/integrated-terminal) 中运行。

操作有助于避免您输入常见动作，例如为项目触发构建或启动开发服务器。对于一次性的快速调试，您可以直接使用集成终端。



<CodexScreenshot
  alt="ChatGPT 桌面应用设置中显示的项目操作列表"
  lightSrc="/images/codex/app/actions-light.webp"
  darkSrc="/images/codex/app/actions-dark.webp"
  maxHeight="400px"
  class="mb-4 lg:mb-0"
/>

</section>

例如，对于 Node.js 项目，您可以创建一个包含以下脚本的“运行”操作：

```bash
npm start
```

如果您的操作命令是特定于平台的，请为 macOS、Windows 和 Linux 定义特定于平台的脚本。

为了标识您的操作，请选择与每个操作关联的图标。

## 使用内置 Git 工具







在 Codex 中，ChatGPT 桌面应用在每个
本地项目和工作树旁边提供了常见的 Git 控件。差异面板显示了当前检出中的更改，
并允许您添加内联注释以供 Codex 处理。您可以暂存或还原单个
代码块、暂存或还原整个文件、提交更改、推送分支，以及创建
拉取请求，而无需离开应用程序。

使用 [integrated terminal](https://learn.chatgpt.com/docs/integrated-terminal) 进行未在应用中公开的 Git
操作。为了将并发更改与
您的本地检出隔离开来，请在 [worktree](https://learn.chatgpt.com/docs/environments/git-worktrees) 中启动任务。



<Illustration description="Codex 环境摘要面板">
  <EnvironmentPanelIllustration ariaLabel="Codex 环境摘要面板" />
</Illustration>

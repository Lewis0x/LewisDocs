---
title: 云环境
source_id: codex/environments/cloud-environment
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/environments/cloud-environment
owner: OpenAI
content_sha256: f33c31a5da1f64f85570d4e61052a1ce8c43b1ca2171f2186ca23f67444ae300
translation_of: codex/environments/cloud-environment
translation_model: k3
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/environments/cloud-environment)

Content owner: OpenAI

# 云环境

> 完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。可以通过在页面 URL 后附加 `.md` 来获取文档页面的 Markdown 版本。

使用环境来控制 Codex 在云端对话期间安装和运行的内容。例如，您可以添加依赖项、安装代码检查和格式化等工具，并设置环境变量。

在 [Codex 设置](https://chatgpt.com/codex/settings/environments) 中配置环境。

<a id="how-codex-cloud-tasks-run"></a>

## Codex 云端对话的运行方式

当您提交提示词时，会发生以下情况：

1. Codex 创建一个容器，并在选定的分支或提交 SHA 处检出您的仓库。
2. Codex 运行您的设置脚本，并在恢复缓存的容器时运行可选的维护脚本。
3. Codex 应用您的互联网访问设置。设置脚本在具有互联网访问权限的情况下运行。默认情况下，代理的互联网访问是关闭的，但您可以根据需要启用受限或不受限制的访问。请参见 [代理互联网访问](https://learn.chatgpt.com/docs/cloud/internet-access)。
4. 代理循环运行终端命令。它会编辑代码、运行检查，并尝试验证其工作成果。如果您的仓库包含 `AGENTS.md`，代理将使用它来查找特定于项目的代码检查和测试命令。
5. 当代理完成时，它会显示其答案以及它更改的任何文件的差异。您可以创建一个 PR 或提出后续问题。

## 默认通用镜像

Codex 代理在一个名为 `universal` 的默认容器镜像中运行，该镜像预装了常见的语言、包和工具。

在环境设置中，选择 **设置包版本** 以固定 Python、Node.js 和其他运行时的版本。

有关已安装内容的详细信息，请参见
  [openai/codex-universal](https://github.com/openai/codex-universal) 获取
  参考 Dockerfile 以及可在本地拉取和测试的镜像。

虽然 `codex-universal` 为了速度和便利预装了多种语言，但您也可以使用 [设置脚本](#manual-setup) 在容器中安装额外的包。

## 环境变量与机密

**环境变量** 在整个对话期间（包括设置脚本和代理阶段）均被设置。

**机密** 与环境变量类似，不同之处在于：

- 它们在存储时会增加一层加密，仅在任务执行时才会解密。
- 它们仅对设置脚本可用。出于安全原因，机密会在代理阶段开始前被移除。

## 自动设置

对于使用常见包管理器（`npm`、`yarn`、`pnpm`、`pip`、`pipenv` 和 `poetry`）的项目，Codex 可以自动安装依赖项和工具。

## 手动设置

如果您的开发设置更为复杂，您也可以提供一个自定义设置脚本。例如：

```bash
# Install type checker

pip install pyright

# Install dependencies

poetry install --with test
pnpm install
```

设置脚本在独立于代理的 Bash 会话中运行，因此像
  `export` 这样的命令不会保留到代理阶段。要保留环境
  变量，请将它们添加到 `~/.bashrc` 或在环境设置中进行配置。

## 容器缓存

Codex 会将容器状态缓存最多 12 小时，以加快新聊天和后续操作的速度。

当环境被缓存时：

- Codex 会克隆仓库并检出默认分支。
- Codex 会运行设置脚本并缓存生成的容器状态。

当恢复缓存的容器时：

- Codex 会检出为该聊天指定的分支。
- Codex 会运行维护脚本（可选）。当设置脚本在较早的提交上运行且需要更新依赖项时，这非常有用。

如果您更改了设置脚本、维护脚本、环境变量或机密，Codex 会自动使缓存失效。如果您的代码仓库发生更改导致缓存状态不兼容，请在环境页面上选择 **重置缓存**。

对于 Business 和 Enterprise 用户，缓存由所有拥有
  该环境访问权限的用户共享。使缓存失效将影响
  您工作空间中该环境的所有用户。

## 互联网访问和网络代理

在设置脚本阶段可以访问互联网以安装依赖项。在代理阶段，默认关闭互联网访问，但您可以配置受限或不受限的访问权限。参见 [代理互联网访问](https://learn.chatgpt.com/docs/cloud/internet-access).

出于安全和防止滥用的目的，环境运行在 HTTP/HTTPS 网络代理之后。所有出站互联网流量都通过此代理。

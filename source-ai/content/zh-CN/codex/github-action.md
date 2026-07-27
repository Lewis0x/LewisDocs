---
title: Codex GitHub Action
source_id: codex/github-action
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/github-action
owner: OpenAI
content_sha256: c7e4ac20c7ea626ddeabb3d43d7e30ce9e53cc2ba810dcc2816c996b9d1edfeb
translation_of: codex/github-action
translation_model: k3
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/github-action)

Content owner: OpenAI

# Codex GitHub Action

使用 Codex GitHub Action（`openai/codex-action@v1`）在 CI/CD 任务中运行 Codex、应用补丁，或在 GitHub Actions 工作流中发布评审。
该 Action 会安装 Codex CLI，在你提供 API 密钥时启动 Responses API 代理，并按照你指定的权限运行 `codex exec`。

在以下场景中使用该 Action：

- 在拉取请求或发布时自动获取 Codex 反馈，而无需自行管理 CLI。
- 在 CI 流水线中将变更与 Codex 驱动的质量检查挂钩。
- 从工作流文件运行可重复的 Codex 任务（代码评审、发布准备、迁移）。

有关 CI 示例，请参阅[非交互模式](https://learn.chatgpt.com/docs/non-interactive-mode)，并在 [openai/codex-action 仓库](https://github.com/openai/codex-action)中浏览源代码。

## 前提条件

- 将你的 OpenAI 密钥存储为 GitHub secret（例如 `OPENAI_API_KEY`），并在工作流中引用它。
- 在 Linux 或 macOS 运行器上运行任务。对于 Windows，请设置 `safety-strategy: unsafe`。
- 在调用该 Action 之前先检出你的代码，以便 Codex 可以读取仓库内容。
- 确定要运行的提示词。你可以通过 `prompt` 提供内联文本，或使用 `prompt-file` 指向仓库中已提交的文件。

## 示例工作流

下面的示例工作流会评审新的拉取请求，捕获 Codex 的响应，并将其发布回 PR。

```yaml
name: Codex pull request review
on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  codex:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    outputs:
      final_message: ${{ steps.run_codex.outputs.final-message }}
    steps:
      - uses: actions/checkout@v5
        with:
          ref: refs/pull/${{ github.event.pull_request.number }}/merge
          fetch-depth: 0
          persist-credentials: false

      - name: Run Codex
        id: run_codex
        uses: openai/codex-action@v1
        with:
          openai-api-key: ${{ secrets.OPENAI_API_KEY }}
          prompt-file: .github/codex/prompts/review.md
          output-file: codex-output.md

  post_feedback:
    runs-on: ubuntu-latest
    needs: codex
    if: needs.codex.outputs.final_message != ''
    permissions:
      issues: write
      pull-requests: write
    steps:
      - name: Post Codex feedback
        uses: actions/github-script@v7
        with:
          github-token: ${{ github.token }}
          script: |
            await github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.payload.pull_request.number,
              body: process.env.CODEX_FINAL_MESSAGE,
            });
        env:
          CODEX_FINAL_MESSAGE: ${{ needs.codex.outputs.final_message }}
```

将 `.github/codex/prompts/review.md` 替换为你自己的提示词文件，或使用 `prompt` 输入提供内联文本。该示例还会将 Codex 的最终消息写入 `codex-output.md`，以便后续检查或上传为构件。

## 配置 `codex exec`

通过设置映射到 `codex exec` 选项的 Action 输入来微调 Codex 的运行方式：

- `prompt` 或 `prompt-file`（二选一）：内联指令，或指向仓库中包含任务的 Markdown 或文本文件的路径。建议将提示词存储在 `.github/codex/prompts/` 中。
- `codex-args`：额外的 CLI 标志。提供 JSON 数组（例如 `["--ephemeral"]`）或 shell 字符串（`--profile ci`）以配置会话、配置文件或 MCP 设置。
- `model` 和 `effort`：选择你想要的 Codex 代理配置；留空则使用默认值。
- `sandbox`：将沙箱模式（`workspace-write`、`read-only`、`danger-full-access`）与 Codex 运行期间所需的权限相匹配。
- `output-file`：将 Codex 的最终消息保存到磁盘，以便后续步骤上传或进行差异比较。
- `codex-version`：固定特定的 CLI 版本。留空则使用最新发布的版本。
- `codex-home`：指向共享的 Codex 主目录，以便在各步骤之间复用配置文件或 MCP 设置。

## 管理权限

除非你加以限制，否则 Codex 在 GitHub 托管的运行器上拥有广泛的访问权限。使用以下输入来控制暴露范围：

- `safety-strategy`（默认 `drop-sudo`）在运行 Codex 之前移除 `sudo`。这对任务而言是不可逆的，可保护内存中的机密。在 Windows 上，你必须设置 `safety-strategy: unsafe`。
- `unprivileged-user` 将 `safety-strategy: unprivileged-user` 与 `codex-user` 配对，以特定账户身份运行 Codex。确保该用户可以读写仓库的检出内容（所有权修复请参见 [`unprivileged-user` 示例](https://github.com/openai/codex-action/blob/main/examples/unprivileged-user.yml)）。
- `read-only` 阻止 Codex 更改文件或使用网络，但它仍以提升的权限运行。不要仅依赖 `read-only` 来保护机密。
- `sandbox` 在 Codex 内部限制文件系统和网络访问。请选择仍能让任务完成的最窄选项。
- `allow-users` 和 `allow-bots` 限制谁可以触发工作流。默认情况下，只有具有写权限的用户才能运行该 Action；可以明确列出额外的可信账户，或将该字段留空以使用默认行为。

## 捕获输出

该操作通过 `final-message` 输出发出最后一条 Codex 消息。将其映射到作业输出（如上所示），或在后续步骤中直接处理。如果你希望从运行器收集完整的对话记录，可将 `output-file` 与上传工件功能结合使用。当你需要结构化数据时，通过 `--output-schema` 传递 `codex-args` 以强制 JSON 格式。

## 安全检查清单

- 限制谁可以启动工作流。优先使用受信任的事件或显式批准，而不是允许所有人针对你的仓库运行 Codex。
- 清理来自拉取请求、提交消息或议题正文的提示输入，以避免提示注入。在将 HTML 注释或隐藏文本提供给 Codex 之前先进行审查。
- 通过在 `OPENAI_API_KEY` 上保留 `safety-strategy` 或将 Codex 移至非特权用户来保护你的 `drop-sudo`。切勿在多租户运行器上让该操作处于 `unsafe` 模式。
- 将 Codex 作为作业中的最后一步运行，以便后续步骤不会继承任何意外的状态更改。
- 如果你怀疑代理日志或操作输出泄露了机密材料，请立即轮换密钥。

## 故障排除

- **你同时设置了 prompt 和 prompt-file**：删除重复的输入，以便你只提供一个来源。
- **responses-api-proxy 未写入服务器信息**：确认 API 密钥存在且有效；代理仅在你提供 `openai-api-key` 时启动。
- **预期 `sudo` 被移除，但 `sudo` 成功了**：确保之前的步骤没有恢复 `sudo`，并且运行器操作系统是 Linux 或 macOS。使用全新的作业重新运行。
- **`drop-sudo` 之后出现权限错误**：在操作运行之前授予写入权限（例如使用 `chmod -R g+rwX "$GITHUB_WORKSPACE"` 或采用非特权用户模式）。
- **未经授权的触发被阻止**：如果你需要允许默认写入协作者之外的服务账户，请调整 `allow-users` 或 `allow-bots` 输入。

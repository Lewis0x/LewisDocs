---
title: 工作树
source_id: codex/environments/git-worktrees
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/environments/git-worktrees
owner: OpenAI
content_sha256: 23639350d256217fddece01fb9cc83871dc346ca12597880fda74334b1d31e3b
translation_of: codex/environments/git-worktrees
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/environments/git-worktrees)

Content owner: OpenAI

# 工作树

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。可以通过在页面 URL 后附加 `.md` 来获取文档页面的 Markdown 版本。

在 ChatGPT 桌面应用程序中，工作树允许 Codex 在同一项目中运行多个独立的聊天，而不会相互干扰。对于 Git 存储库，[计划任务](https://learn.chatgpt.com/docs/automations) 可以在专用的后台工作树上运行，从而不会与您正在进行的工作发生冲突。在非版本控制的项目中，计划任务直接在项目目录中运行。您也可以手动在工作树中启动聊天，并使用交接（Handoff）功能在本地（Local）和工作树（Worktree）之间移动聊天。

工作树仅在 ChatGPT 桌面应用程序的 Codex 中可用。选择
  **Codex**，然后再在工作树中启动聊天。

## 什么是工作树

工作树仅在属于 Git 存储库的项目中有效，因为它们在底层使用了 [Git worktrees](https://git-scm.com/docs/git-worktree)。工作树允许您创建存储库的第二个副本（“检出”）。每个工作树都拥有您存储库中每个文件各自的副本，但它们都共享有关提交、分支等的相同元数据（`.git` 文件夹）。这使您可以并行检出和处理多个分支。

## 术语

- **本地检出**：您创建的存储库。在 ChatGPT 桌面应用程序中有时简称为**本地**。
- **工作树**：在 ChatGPT 桌面应用程序中从您的本地检出创建的 [Git worktree](https://git-scm.com/docs/git-worktree)。
- **交接（Handoff）**：在本地和工作树之间移动聊天的流程。Codex 负责处理在两者之间安全移动您的工作所需的 Git 操作。

## 为什么使用工作树

1. 与 Codex 并行工作，而不会干扰您当前的本地设置。
2. 在您专注于前台工作的同时排队后台任务。
3. 当您准备好进行更直接地检查、测试或协作时，稍后可以将聊天移动到本地。

## 入门

工作树需要 Git 存储库。请确保您选择的项目位于 Git 存储库中。

<WorkflowSteps variant="headings">

1.  选择“工作树”

    在新聊天视图中，选择输入框下方的**工作树**。
    （可选）选择一个 [本地环境](https://learn.chatgpt.com/docs/environments/local-environment) 来为工作树运行设置脚本。

2.  选择起始分支

    在输入框下方，选择作为工作树基础的 Git 分支。可以是您的 `main` / `master` 分支、功能分支，或者是包含未暂存本地更改的当前分支。

3.  提交您的提示

    提交您的提示后，Codex 会根据您选择的分支创建一个 Git 工作树。默认情况下，Codex 在 ["detached HEAD"](https://git-scm.com/docs/git-checkout#_detached_head) 下工作。

4.  选择继续工作的位置

    当您准备好后，您可以直接在工作树上继续工作，也可以将聊天交接给您的本地检出。向本地交接或从本地交接会移动您的聊天_和_代码，以便您可以在另一个检出中继续。

</WorkflowSteps>

## 在本地与工作树之间工作

工作树的外观和感觉与你的本地检出非常相似。不同之处在于它们在你工作流中的位置。你可以将本地视为前台，将工作树视为后台。交接（Handoff）功能允许你在它们之间移动聊天。

在底层，交接功能负责处理在两个检出之间安全移动工作所需的 Git 操作。这很重要，因为 **Git 只允许一个分支同时在一个地方被检出**。如果你在工作树上检出了一个分支，你就**无法**同时在本地检出中检出它，反之亦然。

在实践中，有两条常见路径：

1. [专门在工作树上工作](#option-1-working-on-the-worktree)。当你可以直接在工作树上验证更改时，这条路径效果最好，例如因为你已经使用[本地环境设置脚本](https://learn.chatgpt.com/docs/environments/local-environment)安装了依赖项和工具。
2. [将聊天移交给本地](#option-2-handing-a-chat-off-to-local)。当你想要将聊天带到前台时使用此选项，例如因为你想在常用的 IDE 中检查更改，或者只能运行一个应用程序实例。

### 选项 1：在工作树上工作







如果你想带着更改完全留在工作树上，请使用聊天头部的**在此处创建分支**按钮，将你的工作树转换为一个分支。

从这里你可以提交更改，将分支推送到你的远程仓库，并在 GitHub 上发起拉取请求。

你可以使用头部的“打开”按钮在工作树中打开 IDE，使用集成终端，或者任何你需要从工作树目录执行的其他操作。




<CodexScreenshot
  alt="工作树聊天视图，包含分支控制和工作树详细信息"
  lightSrc="/images/codex/app/worktree-light.webp"
  darkSrc="/images/codex/app/worktree-dark.webp"
  maxHeight="400px"
  class="mb-4 lg:mb-0"
/>




请记住，如果你在工作树上创建了一个分支，你就无法在任何其他工作树（包括你的本地检出）中检出它。

<a id="option-2-handing-a-thread-off-to-local"></a>
<a id="option-2-handing-a-chat-off-to-local"></a>
<a id="option-2-handing-a-task-off-to-local"></a>

### 选项 2：将聊天移交给本地







如果你想将聊天带到前台，请在聊天头部选择**移交**并将其移动到**本地**。

当你想在常用的 IDE 窗口中阅读更改、运行现有的开发服务器，或者在你日常使用的相同环境中验证工作时，此路径非常有效。

Codex 负责处理在工作树和你的本地检出之间安全移动聊天所需的 Git 步骤。

每个聊天随着时间的推移会保持同一个关联的工作树。如果你稍后将聊天移回工作树，Codex 会将其返回到该相同的后台环境，以便你可以从上次中断的地方继续。




<CodexScreenshot
  alt="移交对话框，将聊天从工作树移动到本地"
  lightSrc="/images/codex/app/handoff-light.webp"
  darkSrc="/images/codex/app/handoff-dark.webp"
  maxHeight="400px"
  class="mb-4 lg:mb-0"
/>




你也可以反方向操作。如果你已经在本地工作并想要释放前台，请使用**移交**将聊天移动到工作树。当你想让 Codex 在后台继续工作，同时你将注意力转回到本地的其他事情上时，这非常有用。

由于交接使用 Git 操作，任何作为你的 `.gitignore` 文件一部分的文件都不会随聊天一起移动，除非 Codex 使用 `.worktreeinclude` 将它们复制到本地受管工作树中。

## 高级细节

### Codex 管理的和永久工作树

默认情况下，聊天使用 Codex 管理的工作树。这些工作树旨在让人感觉轻量级且用完即弃。Codex 管理的工作树通常专用于一个聊天，如果您稍后将其交回，Codex 会将该聊天返回到同一个工作树。

如果您想要一个长期存在的环境，请从侧边栏中项目的三点菜单创建一个永久工作树。这会创建一个新的永久工作树作为其自身的项目。永久工作树不会被自动删除，您可以从同一个工作树启动多个聊天。

### Codex 如何为您管理工作树

Codex 在 `$CODEX_HOME/worktrees` 中创建工作树。起始提交是您开始聊天时所选分支的 `HEAD` 提交。如果您选择了一个带有本地更改的分支，Codex 也会将未提交的更改应用到工作树。该工作树不会作为分支被检出。它处于 [detached HEAD](https://git-scm.com/docs/git-checkout#_detached_head) 状态。这使得 Codex 可以创建多个工作树，而不会污染您的分支。

### 将忽略的本地文件复制到受管工作树中

本地 Codex 管理的工作树从 Git 检出开始，因此被跟踪的文件已经存在。如果您的存储库忽略了新工作树所需的本地设置文件，请在存储库根目录添加一个 `.worktreeinclude` 文件，并列出在 Codex 创建受管工作树时要复制的忽略路径或 `.gitignore` 样式的模式。

将此用于 Git 有意忽略的文件，例如 `.env`、`.env.local` 或 `config/secrets.json`。Codex 仅复制与 `.worktreeinclude` 匹配的忽略文件；它不会复制 Git 未跟踪的其他本地文件。不要列出被跟踪的文件。

Codex 会自动将忽略的 `AGENTS.override.md` 复制到本地受管工作树中，因此您不需要在 `.worktreeinclude` 中列出它。

```text
# .worktreeinclude

.env
.env.local
config/secrets.json
```

Codex 会跳过源符号链接，并且不会覆盖新检出中已存在的文件。此行为适用于本地 ChatGPT 桌面应用受管工作树，而不适用于远程工作树或您自己从命令行创建的 Git 工作树。

### 分支限制

假设 Codex 在工作树上完成了一些工作，而您选择使用**在此处创建分支**在其上创建一个 `feature/a` 分支。现在，您想在本地检出上尝试它。如果您尝试检出该分支，您会收到以下错误：

```
fatal: 'feature/a' is already used by worktree at '<WORKTREE_PATH>'
```

要解决此问题，您需要在工作树上检出另一个分支而不是 `feature/a`。

如果您计划在本地检出该分支，请使用交接将聊天移动到本地，而不是试图同时在两个地方保持检出同一个分支。

<ToggleSection title="为什么存在此限制">
Git 阻止同一个分支同时在多个工作树中被检出，因为分支代表一个单一的可变引用 (`refs/heads/<name>`)，其含义是工作树的“当前检出状态”。

当检出分支时，Git 将其 HEAD 视为该工作树所拥有，并期望提交、重置、变基和合并等操作以定义良好且串行化的方式推进该引用。允许多个工作树同时检出同一分支会在哪个工作树的操作更新分支引用方面产生歧义和竞争条件，从而可能导致丢失提交、不一致的索引或不明确的冲突解决。

通过强制执行每个工作树一个分支的规则，Git 保证每个分支都有一个单一权威的工作副本，同时仍允许其他工作树通过 detached HEAD 或单独的分支安全地引用相同的提交。

</ToggleSection>

### 工作树清理

工作树会占用大量磁盘空间。每个工作树都有自己的一套仓库文件、依赖项、构建缓存等。因此，ChatGPT 桌面应用会尝试将工作树的数量保持在合理的限制内。

默认情况下，Codex 会保留您最近的 15 个由 Codex 管理的工作树。如果您希望自己管理磁盘使用情况，可以在设置中更改此限制或关闭自动删除功能。

Codex 会尽量避免删除仍然重要的工作树。在以下情况下，由 Codex 管理的工作树不会被自动删除：

- 有固定的聊天与其绑定
- 聊天仍在进行中
- 该工作树是永久工作树

在以下情况下，由 Codex 管理的工作树会被自动删除：

- 您归档了关联的聊天
- Codex 需要删除旧的工作树以保持在您配置的限制内

在删除由 Codex 管理的工作树之前，Codex 会保存其上工作的快照。如果您在工作树被删除后打开聊天，您将看到恢复它的选项。

## 常见问题解答

<ToggleSection title="我可以控制工作树的创建位置吗？">
  可以。Codex 默认在 `$CODEX_HOME/worktrees` 下
  创建受管工作树。要选择其他位置，请打开 **设置 > 工作树** 并更改
  **工作树根目录**。
</ToggleSection>

<a id="can-i-move-a-chat-between-local-and-worktree"></a>

<ToggleSection title="我可以在本地和工作树之间移动聊天吗？">
  可以。使用聊天头部中的 **移交** 在您的本地
  检出和工作树之间移动聊天。Codex 会处理在不同环境间安全移动
  聊天所需的 Git 操作。如果您稍后将聊天移交回工作树，
  Codex 会将其返回到同一个关联的工作树。
</ToggleSection>

<a id="what-happens-to-chats-if-a-worktree-is-deleted"></a>

<ToggleSection title="如果工作树被删除，聊天会怎样？">
  即使底层工作树目录被删除，聊天也可以保留在您的历史记录中。对于由 Codex 管理的工作树，Codex 会在删除
  工作树之前保存快照，并在您重新打开相关联的聊天时
  提供恢复它的选项。
  当您归档永久工作树的
  聊天时，永久工作树不会被自动删除。
</ToggleSection>

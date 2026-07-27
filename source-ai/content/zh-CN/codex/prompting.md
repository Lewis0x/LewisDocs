---
title: 提示
source_id: codex/prompting
product: codex
lang: zh-CN
canonical_url: https://learn.chatgpt.com/docs/prompting
owner: OpenAI
content_sha256: 7dbe05fc5c5f1740e8cabb68d99c966fff79d24167e1ab5d4276c626b93cc557
translation_of: codex/prompting
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://learn.chatgpt.com/docs/prompting)

Content owner: OpenAI

# 提示

<a id="prompts"></a>

## 提示概述

提示是你告诉 ChatGPT 你想知道、制作或更改什么的方式。一个提示
可以是一个问题、一条指令或一个目标。你不需要技术语法或
死板的公式。用你自己的话开始，审查回复，并使用后续
消息来塑造结果。

简短的提示通常就足够了。对于更大或更重要的任务，请包含
重要的部分：

- **目标：** ChatGPT 应该做什么？
- **上下文：** 哪些信息或来源会有帮助？
- **输出：** 你需要什么格式、长度或详细程度？
- **边界：** 什么必须保持不变？ChatGPT 应该避免什么，或在采取行动前与
  你确认什么？

仅使用有帮助的部分。你不需要填写每一项或遵循
规定的格式。

## 描述你需要的结果

从结果开始，而不是详细的步骤列表。包含受众或
格式，当这些细节会改变 ChatGPT 应该生成的内容时。

```text
Turn these meeting notes into a short update for the project team.
Put the decisions and next steps first.
```

此提示解释了要创建什么以及谁会阅读它。当流程本身
很重要时，描述该流程。否则，留出空间让 ChatGPT 搜索、比较
信息，并调整其方法。

<a id="context"></a>

## 添加有用的上下文

分享可能会改变结果的信息。仅添加
重要的来源，并解释 ChatGPT 应该从每个来源中获取什么。

- 附上文档、电子表格、演示文稿或 PDF 文件，当你希望
  ChatGPT 总结、比较、转换或 [create files for review](https://learn.chatgpt.com/docs/artifacts-viewer) 时。
- 添加截图、图表或其他 [image input](https://learn.chatgpt.com/docs/image-inputs)，当
  任务依赖于视觉上下文时。指出重要的区域，而不是
  仅依赖图像本身。
- 要求 ChatGPT 使用 [web search](https://learn.chatgpt.com/docs/web-search)，当答案依赖于
  当前信息时，当你需要检查结果时，请要求提供来源。
- 使用 [project](https://learn.chatgpt.com/docs/projects)，当相关对话需要共享文件、
  来源或本地文件夹时。

### 使用连接的来源

当 ChatGPT 有权访问连接的来源时，指出它应该去哪里查找以及什么
它应该找到什么。你不需要描述它应该执行的每一次搜索。

```text
Use the latest project plan in Drive and relevant decisions and updates from
the project's Slack channel to prepare a status update.
```

连接的来源需要匹配的插件，并且可用性可能取决于
你的套餐和工作区设置。

### 使用插件

插件为 ChatGPT 和 Codex 提供了可重用的指令以及与工具的连接
例如 Google Drive、Gmail、Slack 和 GitHub。这两个产品都从同一个通用目录中提取公共
插件。索取你需要的结果，让
当前的活动界面从可用的工具中进行选择。在 ChatGPT 中，输入 `@`
在输入框中以选择特定的插件。

[<IconItem title="了解插件" className="mt-4">
    <span slot="icon">
      <Plugin />
    </span>
    在 ChatGPT 和 Codex 中查找、安装和使用插件。
  </IconItem>](https://learn.chatgpt.com/docs/plugins)

### 个性化 ChatGPT

将应适用于所有对话的偏好设置放在 **设置 > 个性化** 中
作为自定义指令。仅与当前对话有关的详细信息保留在
提示中。

[<IconItem title="审查个性化设置" className="mt-4">
    <span slot="icon">
      <Settings />
    </span>
    设置默认个性化、自定义指令和其他应用偏好。
  </IconItem>](https://learn.chatgpt.com/docs/reference/settings#personalization)

## 设定防止实际问题的边界

边界是 ChatGPT 避免创建额外工作所需的几条指令
或采取你不希望的行动。当更改错误的细节
会导致结果无法使用时，或者当你想在某些内容影响
其他人之前对其进行审查时，请添加一个边界。

- 保持已批准的日期和预算数字不变。
- 仅使用提供的来源。标记缺失的信息而不是猜测。
- 将建议保持在规定的预算范围内。
- 将消息准备为草稿。不要发送。

专注于最重要的一两个边界。你不需要控制
ChatGPT 采取的每一个步骤。

## 让结果随时可用

告诉 ChatGPT 你打算如何使用结果。这有助于它选择正确的
长度、详细程度和组织结构。

- 将其制作成一份一页纸的摘要，供主管在会前快速浏览。把
  决定和后续步骤放在最前面。
- 将这些笔记转化为包含决定、负责人和截止
  日期的跟进邮件。
- 创建一个清晰的计划支出与实际支出对比表，并突出显示任何
  超过 10% 的差异。

对于重要的工作，请要求 ChatGPT 进行最终检查，例如确认每个
行动项都有负责人和截止日期，或者标记它无法
验证的信息。然后在你使用或分享结果之前，自己进行审查。

## 通过后续消息改进结果

你的第一个提示词不需要完美。审查结果，然后提出
你想要的具体修改。

```text
Make the opening more direct, keep the evidence, and move the recommendation
above the background section.
```

你可以添加缺失的来源、纠正方向、要求另一个选项，或者
更改详细程度，而无需从头开始。

### 引导和排队

当 Codex 已经在工作时，你可以发送另一条消息，而无需等待
当前运行完成：

- **引导** 会将消息添加到当前运行中。使用它来改变方向、添加
  缺失的细节或分享新信息。
- **排队** 会将消息保存到下一次运行。将其用于应该
  等待当前工作完成的后续操作。

在 ChatGPT 桌面应用程序中，在以下位置选择默认设置：
[**设置 > 通用 > 后续行为**](https://learn.chatgpt.com/docs/reference/settings#general)。
排队的消息会显示在输入框上方，你可以在此编辑、重新排序、发送或
删除它们。该设置还显示了针对单条消息使用其他行为的快捷方式，
而无需更改你的默认设置。

在 Codex CLI 中，在 Codex 工作时按 <kbd>Enter</kbd> 键以引导当前
轮次，或者按 <kbd>Tab</kbd> 键将消息排队等待下一轮。请参阅
[交互式快捷键](https://learn.chatgpt.com/docs/developer-commands?surface=cli#cli-interactive-shortcuts)
了解详情。

## 将各部分组合起来

对于使用已连接来源的项目更新，一个完整的提示词可能看起来
像这样：

```text
Prepare a one-page project status update for Monday's leadership meeting. Use
the latest project plan in Drive and relevant decisions and updates from the
project's Slack channel.

Lead with the decisions leadership needs to make and the next steps. Summarize
progress, risks, owners, and due dates. Keep approved dates and budget figures
unchanged. Flag any conflicting or missing information, and don't send or
publish anything.

Before you finish, check that every next step has an owner and due date.
```

这个提示词涵盖了**目标**、**背景**、**输出**和**边界**，然后
要求进行最终检查，而无需详细说明每一个步骤。

## 使用语音听写

在 ChatGPT 桌面应用程序中，在输入框
可见时按住 <kbd>Ctrl</kbd>+<kbd>M</kbd>，然后开始说话。ChatGPT 会将你的语音转录到输入框中，以便
你在发送提示词之前进行审查和编辑。

<CodexScreenshot
  alt="输入框中带有转录提示词的语音听写指示器"
  lightSrc="/images/codex/app/voice-dictation-light.webp"
  darkSrc="/images/codex/app/voice-dictation-dark.webp"
  maxHeight="400px"
  class="my-8"
/>

<a id="threads"></a>
<a id="chats"></a>

## 聊天提示词示例

将聊天用于提问、创意、草稿和日常决定。从
你想要的结果开始，然后仅在它会改变答案时添加细节。

### 理解一个主题

```text
Explain how compound interest works for someone who has never invested.
Use one concrete example and define any financial terms you introduce.
```

### 起草和完善写作

```text
Draft a friendly email declining this invitation because I will be traveling.
Keep it under 120 words and leave the door open for a future event.
```

### 比较各种选项

```text
Compare these two phone plans for one person who travels internationally twice
a year. Show the important differences in a table, then recommend one and explain
the tradeoff.
```

### 制定实用计划

```text
Plan five weekday dinners that take less than 30 minutes. Avoid peanuts, reuse
ingredients across meals, and finish with one consolidated shopping list.
```

<a id="prompting-for-work"></a>
<a id="prompting-in-work-mode"></a>

## ChatGPT Work 提示词

将聊天用于快速提问、简短重写、头脑风暴和轻量级
草稿。将 ChatGPT Work 用于利用不同来源或工具、涉及
一系列步骤、进行更改或生成更大的交付物的任务。

在 ChatGPT Work 中，描述你需要的结果，提供源材料，指明
受众，并解释你将如何审查工作。要求 ChatGPT 计划、
收集所需信息、创建文件，并在完成前进行检查。

<a id="use-work-efficiently"></a>
<a id="use-work-mode-efficiently"></a>

### 高效使用 ChatGPT Work

ChatGPT Work 对于耗时或重复性任务，或您可以
重复使用的成品文件非常有用。如果某个任务能节省
时间、提高质量或帮助您做出重要决定，那么即使它消耗更多额度也依然值得。

从您可以审查的一个结果开始：

- 仅包含相关来源，并在适当时限制日期范围。
- 定义受众、输出格式和所需长度。
- 将必需的工作与可选的改进或润色分开。
- 当方法很重要时，要求提供一个计划。在 ChatGPT
  发送、发布或更改他人依赖的信息之前，要求必须获得您的批准。
- 如果任务开始执行您不再需要的工作，请缩小范围或停止任务。

审查第一个结果，完善指令，并在其
正常运作后重复使用该工作流。

### 将源材料转换为成品文件

```text
Use the attached quarterly reports to create a leadership brief and a six-slide
presentation.

The audience is the executive team. Lead with the three decisions they need to
make, distinguish reported facts from your analysis, cite each number to its
source file, and check that the brief and slides agree before you finish.
```

### 研究一项决策

```text
Research three customer-support platforms for a 50-person company. Compare
pricing, security, integrations, and migration effort using current sources.
Deliver a recommendation memo with links, assumptions, and the questions we
should answer before signing a contract.
```

### 协调一次发布

```text
Create a launch plan for the attached product brief. Include the timeline,
owners, dependencies, risks, announcement draft, customer FAQ, and a checklist
for launch day. Flag any missing decisions before producing the final files.
```

对于重复性工作，请先在普通聊天中完善提示。在输出可靠后，
[在该聊天中安排任务](https://learn.chatgpt.com/docs/automations#schedule-a-task-inside-a-chat)。
当每次计划运行都应开始
一个新聊天时，请改为创建独立的计划任务。

<a id="use-editor-context"></a>

## 为 Codex 编写提示

当您希望 ChatGPT 处理代码、代码库或开发者工具时，请使用 Codex。
一个有用的 Codex 提示会说明您想要的行为，指向相关的代码或
重现步骤，保留重要的约束条件，并说明如何验证
更改。

<a id="goal-mode"></a>

对于多步骤任务，当您希望 Codex 在编辑前
调查并提出一种方法时，请在应用组合器中输入 `/plan`。当 [目标模式](https://learn.chatgpt.com/docs/long-running-work)
可用时，请在计划后使用 `/goal` 来设定持久目标。有关当前的命令列表，请参阅[应用斜杠
命令](https://learn.chatgpt.com/docs/reference/slash-commands)
。

### 如何阅读这些示例

每个工作流包含：

- **何时使用**以及最适合的 Codex 环境（IDE、CLI 或云端）。
- 带有用户提示示例的**步骤**。
- **上下文说明**：Codex 自动看到的内容与您应该附加的内容的区别。
- **验证**：如何检查输出。

> **注意：** IDE 扩展会自动将您打开的文件作为上下文包含在内。在 CLI 中，请明确提及路径，或使用 `/mention` 和 `@` 路径自动补全来附加文件。

Codex 在 [沙盒](https://learn.chatgpt.com/docs/sandboxing) 内运行本地命令，
该沙盒限制了文件和网络访问。如果任务需要跨越该边界，
Codex 将在继续之前遵循您的批准策略。

### 解释代码库

当您处于入职阶段、接手某个服务，或试图推导某个协议、数据模型或请求流时，请使用此方法。

#### IDE 扩展工作流（本地探索最快）

<WorkflowSteps>

1. 打开最相关的文件。
2. 选择您关心的代码（可选但推荐）。
3. 提示 Codex：

   ```text
   解释请求如何流经所选代码。

   包括：
   - 涉及的每个模块职责的简短摘要
   - 验证了哪些数据以及在哪里验证
   - 更改此代码时需要注意的一两个“陷阱”
   ```

</WorkflowSteps>

验证：

- 要求提供一个您可以验证的图表或清单：

```text
Summarize the request flow as a numbered list of steps. Then list the files involved.
```

#### CLI 工作流（当您需要记录 + shell 命令时很有用）

<WorkflowSteps>

1. 启动交互式会话：

   ```bash
   codex
   ```

2. 附加文件（可选）并提示：

   ```text
   我需要了解此服务使用的协议。阅读 @foo.ts @schema.ts 并解释架构和请求/响应流程。重点关注必填字段与可选字段以及向后兼容性规则。
   ```

</WorkflowSteps>

上下文说明：

- 您可以在组合器中使用 `@` 从工作区插入文件路径，或使用 `/mention` 附加特定文件。

### 修复 Bug

当您遇到可以在本地重现的失败行为时，请使用此方法。

#### CLI 工作流（包含复现和验证的紧密循环）

<WorkflowSteps>

1. 在仓库根目录启动 Codex：

   ```bash
   codex
   ```

2. 给 Codex 提供一个复现方案，以及你怀疑的文件：

   ```text
   Bug：在设置屏幕上点击“Save”有时会显示“Saved”，但不会保留更改。

   复现：
   1) 启动应用：npm run dev
   2) 前往 /settings
   3) 切换“Enable alerts”
   4) 点击 Save
   5) 刷新页面：开关会重置

   约束：
   - 不要更改 API 形状。
   - 保持修复最小化，并在可行的情况下添加回归测试。

   首先在本地复现 bug，然后提出补丁并运行检查。
   ```

</WorkflowSteps>

上下文说明：

- 由你提供：复现步骤和约束（这些比高层面的描述更重要）。
- 由 Codex 提供：命令输出、发现的调用点以及它触发的任何堆栈跟踪。

验证：

- Codex 应在修复后重新运行复现步骤。
- 如果你有标准的检查流水线，要求它运行：

```text
After the fix, run lint + the smallest relevant test suite. Report the commands and results.
```

#### IDE 扩展工作流

<WorkflowSteps>

1. 打开你认为存在 bug 的文件，以及它最近的调用者。
2. 提示 Codex：

   ```text
   找到导致显示“Saved”但未保留更改的 bug。提出修复方案后，告诉我在 UI 中如何验证它。
   ```

</WorkflowSteps>

### 编写测试

当你想要定义测试的确切范围时使用此方法。

#### IDE 扩展工作流（基于选择）

<WorkflowSteps>

1. 打开包含该函数的文件。
2. 选择定义该函数的行。从命令面板中选择“Add to Codex Thread”将这些行添加到上下文中。
3. 提示 Codex：

   ```text
   为此函数编写单元测试。遵循其他测试中使用的约定。
   ```

</WorkflowSteps>

上下文说明：

- 由“Add to Codex Thread”命令提供：选定的行（这是“line number”范围），以及打开的文件。

#### CLI 工作流（提示中描述的路径 + 行范围）

<WorkflowSteps>

1. 启动 Codex：

   ```bash
   codex
   ```

2. 使用函数名提示：

   ```text
   为 @invert_list 中的 transform.ts 函数添加测试。覆盖正常路径和边缘情况。
   ```

</WorkflowSteps>

### 从截图制作原型

当你想要将设计模型、截图或 UI 参考转换为可运行的原型时使用此方法。

#### CLI 工作流（图像 + 提示）

<WorkflowSteps>

1. 将你的截图保存在本地（例如 `./specs/ui.png`）。
2. 运行 Codex：

   ```bash
   codex
   ```

3. 将图像文件拖入终端以将其附加到提示中。

4. 跟进约束和结构：

   ```text
   基于此图像创建一个新的仪表板。

   约束：
   - 使用 react、vite 和 tailwind。用 typescript 编写代码。
   - 尽可能匹配间距、排版和布局。

   输出：
   - 渲染 UI 的新路由/页面
   - 所需的任何小组件
   - README.md 以及在本地运行它的说明
   ```

</WorkflowSteps>

上下文说明：

- 图像提供了视觉要求，但你仍需指定实现约束（框架、路由、组件样式）。
- 将图像未显示的行为包含在文本中，例如悬停状态、验证规则或键盘交互。

验证：

- 要求 Codex 运行开发服务器（如果允许）并确切告诉你在哪里查看：

```text
Start the dev server and tell me the local URL/route to view the prototype.
```

#### IDE 扩展工作流（图像 + 现有文件）

<WorkflowSteps>

1. 在 Codex 聊天中附加图像（拖放或粘贴）。
2. 提示 Codex：

   ```text
   创建一个新的设置页面。使用附加的截图作为目标 UI。
   遵循此项目中其他文件的设计和视觉模式。
   ```

</WorkflowSteps>

### 通过实时更新迭代 UI

当你在 Codex 编辑代码时，想要一个紧密的“设计 → 调整 → 刷新 → 调整”循环时使用此方法。

#### CLI 工作流（运行 Vite，然后通过小提示进行迭代）

<WorkflowSteps>

1. 启动 Codex：

   ```bash
   codex
   ```

2. 在单独的终端窗口中启动开发服务器：

   ```bash
   npm run dev
   ```

3. 提示 Codex 进行更改：

   ```text
   为落地页提出 2-3 项样式改进。
   ```

4. 选择一个方向，并使用具体的小提示进行迭代：

   ```text
   选择选项 2。

   仅更改页眉：
   - 使排版更具编辑风格
   - 增加空白
   - 确保其在移动端依然美观
   ```

5. 通过有针对性的请求重复操作：

   ```text
   下次迭代：减少视觉噪音。
   保持布局，但简化颜色并移除任何多余的边框。
   ```

</WorkflowSteps>

验证：

- 在 Codex 更新代码时在浏览器中审查更改。
- 提交您喜欢的更改，并还原您不喜欢的更改。
- 如果您还原或更改了某项编辑，请告知 Codex，这样它在处理下一个提示时就不会覆盖您的编辑。

### 将重构委托给云端

当您希望利用本地上下文设计方法，然后将漫长的实现过程委托给可以并行运行的云端聊天时，请使用此功能。

#### 本地规划（IDE）

<WorkflowSteps>

1. 确保您当前的工作已提交或至少已储藏，以便您能够干净地比较更改。
2. 要求 Codex 生成重构计划。如果您有 `$plan` 技能可用，请显式调用它：

   ```text
   $plan

   我们需要重构认证子系统以实现：
   - 划分职责（令牌解析 vs 会话加载 vs 权限）
   - 减少循环导入
   - 提升可测试性

   约束条件：
   - 无用户可见的行为变化
   - 保持公共 API 稳定
   - 包含循序渐进的迁移计划
   ```

3. 审查计划并协商修改：

   ```text
   修改计划以：
   - 明确指定每个里程碑中移动哪些文件
   - 包含回滚策略
   ```

</WorkflowSteps>

上下文说明：

- 当 Codex 能够在本地扫描当前代码（入口点、模块边界、依赖图提示）时，规划效果最佳。

#### 云端委托（IDE → 云端）

<WorkflowSteps>

1. 如果您尚未这样做，请设置一个 [Codex 云端环境](https://learn.chatgpt.com/docs/environments/cloud-environment)。
2. 点击提示词输入框下方的云图标，并选择您的云端环境。
3. 当您输入下一个提示时，Codex 会在云端创建一个新的聊天，该聊天会保留现有的聊天上下文（包括计划和任何本地源代码更改）。

   ```text
   实现计划中的里程碑 1。
   ```

4. 审查云端差异，如有需要则进行迭代。

5. 直接从云端创建 PR，或将更改拉取到本地以进行测试和完成。

6. 针对计划中的其他里程碑进行迭代。

</WorkflowSteps>

委托给云端的任务在隔离环境中运行。除非您为环境启用互联网访问，否则在代理阶段期间互联网访问是关闭的。了解更多关于 [云端互联网访问](https://learn.chatgpt.com/docs/cloud/internet-access) 的信息。

### 进行本地代码审查

当您希望在提交或创建 PR 之前获得第二双眼睛时，请使用此功能。

#### CLI 工作流（审查您的工作树）

<WorkflowSteps>

1. 启动 Codex：

   ```bash
   codex
   ```

2. 运行审查命令：

   ```text
   /review
   ```

3. 可选：提供自定义的重点关注指令：

   ```text
   /review 关注边界情况和安全问题
   ```

</WorkflowSteps>

验证：

- 根据审查反馈应用修复，然后重新运行 `/review` 以确认您已解决这些问题。

### 审查 GitHub 拉取请求

当您希望获得审查反馈而无需在本地拉取分支时，请使用此功能。

在使用此功能之前，请在您的仓库中启用 Codex **代码审查**。请参阅 [代码审查](https://learn.chatgpt.com/docs/third-party/github)。

#### GitHub 工作流（评论驱动）

<WorkflowSteps>

1. 在 GitHub 上打开拉取请求。
2. 发表一条标记 Codex 的评论，明确指出关注领域：

   ```text
   @codex review
   ```

3. 可选：提供更明确的指令。

   ```text
   @codex review for security vulnerabilities and security concerns
   ```

</WorkflowSteps>

### 更新文档

当您需要准确、清晰的文档更改时使用此项。

#### IDE 或 CLI 工作流（本地编辑 + 本地验证）

<WorkflowSteps>

1. 确定要更改的文档文件并打开它们（IDE），或者 `@` 提及它们（IDE 或 CLI）。
2. 向 Codex 提示范围和验证要求：

   ```text
   更新“高级功能”文档，提供身份验证故障排除指南。验证所有链接是否有效。
   ```

3. 在 Codex 起草更改后，审阅文档并根据需要进行迭代。

</WorkflowSteps>

验证：

- 阅读渲染后的页面。

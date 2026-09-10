---
title: Codex Security 云常见问题解答
source_id: codex/security/faq
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/security/faq
owner: OpenAI
content_sha256: 36ecfa5f99341e58dc9fb95c58ad364d700c628ddfffd2d368c7803c0aa44c0f
translation_of: codex/security/faq
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/security/faq)

Content owner: OpenAI

# Codex Security 云常见问题解答

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。通过在页面 URL 后附加 `.md`，可以获取文档页面的 Markdown 版本。

本常见问题解答涵盖了 Codex Security 云。有关在
Codex 任务中运行的本地扫描和工作流，请参见 [Codex Security 插件快速入门](https://learn.chatgpt.com/docs/security/plugin)。

{/* vale Microsoft.Auto = NO */}
{/* vale Vale.Spelling = NO */}

## 入门

### 什么是 Codex Security？

软件安全仍然是工程领域中最困难且最重要的问题之一。Codex Security 是一个由大语言模型 (LLM) 驱动的安全分析工具包，它能够检查源代码，并返回带有建议补丁的结构化、分级的漏洞发现结果。它帮助开发人员和安全团队大规模发现和修复安全问题。

### 为什么它很重要？

软件是现代工业和社会的基础，而漏洞会带来系统性风险。Codex Security 支持防御者优先的工作流，通过持续识别可能的问题、在可能的情况下对其进行验证并提出修复建议，来帮助团队在不拖慢开发进度的情况下提升安全性。

### Codex Security 解决了什么业务问题？

Codex Security 缩短了从疑似问题到带有证据和建议补丁的已确认、可重现发现结果的路径。与仅使用传统扫描工具相比，这减少了分类审查的负担并降低了误报率。

### Codex Security 是如何工作的？

Codex Security 在一个临时的、隔离的容器中运行分析，并临时克隆目标存储库。它执行代码级分析，并返回结构化的发现结果，其中包含描述、文件和位置、严重程度、根本原因以及建议的补救措施。

对于包含验证步骤的发现结果，系统会在同一个沙盒中执行建议的命令或测试，记录成功或失败、退出代码、标准输出、标准错误、测试结果以及任何生成的差异或工件，并将该输出作为证据附加以供审查。

### 它会取代 SAST 吗？

不会。Codex Security 是对 SAST 的补充。它增加了基于 LLM 的语义推理和自动验证，而现有的 SAST 工具仍然提供广泛的确定性覆盖。

## 功能

### 什么是分析流水线？

Codex Security 遵循分阶段的流水线：

1. **分析** 为存储库构建威胁模型。
2. **提交扫描** 审查合并的提交和存储库历史记录，以查找可能的问题。
3. **验证** 尝试在沙盒中重现可能的漏洞，以减少误报。
4. **修补** 与 Codex 集成，提出补丁，供审查者在发起 PR 之前进行检查。

它在 GitHub、Codex 和标准审查工作流中与工程师协同工作。

### 支持哪些语言？

Codex Security 与语言无关。在实践中，性能取决于模型对存储库所使用语言和框架的推理能力。

### 扫描完成后我会得到什么输出？

您将获得带有严重程度、验证状态以及可用时提供补丁建议的分级发现结果。发现结果还可以包括崩溃输出、重现证据、调用路径上下文和相关注释。

### 客户代码是如何隔离的？

每个分析和验证作业都在具有会话范围工具的临时 Codex 容器中运行。工件被提取以供审查，容器在作业完成后被销毁。

### Codex Security 会自动应用补丁吗？

不会。建议的补丁是推荐的补救措施。用户可以进行审查，并从发现结果 UI 将其作为 PR 推送到 GitHub，但 Codex Security 不会自动将更改应用到存储库。

### 项目需要进行构建才能扫描吗？

不需要。Codex Security 可以在没有编译步骤的情况下，根据代码库和提交的上下文生成发现结果。在自动验证期间，如果有助于重现问题，它可能会尝试在容器内构建项目。有关环境设置的详细信息，请参阅 [Codex 云环境](https://learn.chatgpt.com/docs/environments/cloud-environment)。

### Codex Security 如何减少误报并避免损坏的补丁？

Codex Security 使用两个阶段。首先，模型对可能的问题进行排序。然后，自动验证尝试在干净的容器中重现每个问题。成功重现的发现结果将被标记为已验证，这有助于在人工审查之前减少误报。

### 初始扫描需要多长时间，之后会发生什么？

初始扫描时间取决于代码库大小、构建时间以及有多少发现结果进入验证阶段。对于某些代码库，扫描可能需要几个小时。对于较大的代码库，可能需要几天时间。后续的扫描通常更快，因为它们侧重于新的提交和增量更改。

### 什么是威胁模型？

威胁模型是代码库在扫描时的安全上下文。它将简洁的项目概述与攻击面详细信息（如入口点、信任边界、身份验证假设和风险组件）结合在一起。有关更多详细信息，请参阅 [改进威胁模型](https://learn.chatgpt.com/docs/security/threat-model)。

### 威胁模型是如何生成的？

Codex Security 会提示模型总结代码库架构和安全入口点，对代码库类型进行分类，运行专门的提取器，并将结果合并为整个扫描过程中使用的项目概述或威胁模型产出物。

### 它会取代人工安全审查吗？

不会。Codex Security 可以加速审查并帮助对发现结果进行排序，但它不能取代代码级别的验证、可利用性检查或人工威胁评估。

### 我可以编辑威胁模型吗？

可以。Codex Security 会创建初始威胁模型，您可以随着架构、风险和业务背景的变化对其进行更新。有关编辑工作流，请参阅 [改进威胁模型](https://learn.chatgpt.com/docs/security/threat-model)。

### 在使用威胁建模之前，我需要配置扫描吗？

是的。威胁模型指导与您扫描的方式和内容密切相关，因此您需要先配置代码库。请参阅 [Codex Security 设置](https://learn.chatgpt.com/docs/security/setup)。

### 建议的补丁包含什么？

当可以为发现结果生成补救措施时，建议的补丁包含一个最小可操作的差异（diff），并带有文件名和行上下文。

### 补丁会直接修改我的 PR 分支吗？

不会。该工作流会生成差异、补丁文件或建议的更改，供维护者和审查者在应用之前进行检查。

## 验证

### 什么是自动验证？

自动验证是在隔离容器中尝试重现可疑问题的阶段。它会记录重现是成功还是失败，并捕获日志、命令和相关产出物作为证据。

### 如果验证失败会怎样？

该发现结果将保持未验证状态。日志和报告仍会记录已尝试的操作，以便工程师可以重试、进一步调查或调整重现步骤。

{/* vale Microsoft.Auto = YES */}
{/* vale Vale.Spelling = YES */}

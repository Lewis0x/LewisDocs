---
title: Codex Security 云端设置
source_id: codex/security/setup
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/security/setup
owner: OpenAI
content_sha256: ea3a6c31bd2ace6ac4addce40ec07df47a321b85add0b03a511535c5709d86e0
translation_of: codex/security/setup
translation_model: k3
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/security/setup)

Content owner: OpenAI

# Codex Security 云端设置

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。可以通过在页面 URL 后附加 `.md` 来获取文档页面的 Markdown 版本。

本页面将引导您从初始访问到在 Codex Security 云端审查发现的问题和补救
拉取请求。

首先确认您已设置好 Codex 云端。如果没有，请参见 [Codex
  云端](https://learn.chatgpt.com/docs/cloud) 以开始使用。

## 1. 访问与环境

Codex Security 云端会扫描通过以下方式连接的 GitHub 仓库：
[Codex 云端](https://learn.chatgpt.com/docs/cloud)。

- 确认您的工作区有权访问 Codex Security 云端。
- 确认您要扫描的仓库在 Codex 云端可用。

前往 [Codex 环境](https://chatgpt.com/codex/settings/environments) 并检查该仓库是否已有环境。如果没有，请在继续之前在此处创建一个。

<CtaPillLink
  href="https://chatgpt.com/codex/settings/environments"
  label="打开环境"
  icon="external"
  class="my-8"
/>



  <img
    src={createEnvironment.src}
    alt="Codex 环境"
    class="block h-auto w-full"
  />



## 2. 新建安全扫描

环境创建完成后，前往 [创建安全扫描](https://chatgpt.com/codex/security/scans/new) 并选择您刚刚连接的仓库。

<CtaPillLink
  href="https://chatgpt.com/codex/security/scans/new"
  label="创建安全扫描"
  icon="external"
  class="my-8"
/>

Codex Security 会优先从最新的提交开始向后扫描仓库。它利用这一点来构建和刷新随着新提交的到来而产生的扫描上下文。

要配置仓库：

1. 选择 GitHub 组织。
2. 选择仓库。
3. 选择您要扫描的分支。
4. 选择环境。
5. 选择一个 **历史窗口**。较长的窗口提供更多的上下文，但回填所需的时间更长。
6. 点击 **创建**。



  <img
    src={createScan.src}
    alt="创建安全扫描"
    class="block h-auto w-full"
  />



## 3. 初始扫描可能需要一些时间

当您创建扫描时，Codex Security 首先会跨选定的历史窗口运行提交级别的安全检查。
初始回填可能需要几个小时，特别是对于较大的仓库或较长的窗口。
如果发现的问题没有立即显示，这是正常的。请等待初始扫描完成，然后再提交工单或进行故障排除。

初始扫描设置是自动且彻底的。这可能需要几个小时。请不要
  因为第一组发现的问题出现延迟而惊慌。

## 4. 审查扫描并改进威胁模型

<CtaPillLink
  href="https://chatgpt.com/codex/security/scans"
  label="审查扫描"
  icon="external"
  class="my-8"
/>



  <img
    src={reviewThreatModel.src}
    alt="Codex Security 中的威胁模型编辑器"
    class="block h-auto w-full"
  />



初始扫描完成后，打开扫描并审查生成的威胁模型。
初始发现的问题出现后，更新威胁模型以使其与您的架构、信任边界和业务上下文相匹配。
这有助于 Codex Security 为您的团队对问题进行排序。

如果您希望更改扫描结果，您可以编辑威胁模型，以包含您更新后的
  范围、优先级和假设。

初始发现的问题出现后，重新审视模型，以便扫描指导与当前的优先级保持一致。
保持其最新状态有助于 Codex Security 提出更好的建议。

有关威胁模型及其如何影响严重性和分诊的更深入说明，请参见 [改进威胁模型](https://learn.chatgpt.com/docs/security/threat-model)。

## 5. 查看发现结果并修补

初始回填完成后，从**发现结果**视图查看发现的问题。

<CtaPillLink
  href="https://chatgpt.com/codex/security/findings"
  label="打开发现结果"
  icon="external"
  class="my-8"
/>

您可以使用两种视图：

- **推荐发现结果**：仓库中最关键问题的动态前 10 名列表
- **所有发现结果**：整个仓库中可排序、可筛选的发现结果表格

![推荐发现结果视图](https://learn.chatgpt.com/docs/security/images/aardvark_recommended_findings.png)

点击某个发现结果以打开其详情页，其中包含：

- 问题的简明描述
- 关键元数据，例如提交详情和文件路径
- 关于影响的上下文推理
- 相关代码摘录
- 可用时的调用路径或数据流上下文
- 验证步骤和验证输出

您可以直接在发现详情页面审查每个发现并创建 PR。

<CtaPillLink
  href="https://chatgpt.com/codex/security/findings"
  label="审查发现并创建 PR"
  icon="external"
  class="my-8"
/>

## 相关文档

- [Codex Security](https://learn.chatgpt.com/docs/security) 提供产品概述。
- [Codex Security cloud FAQ](https://learn.chatgpt.com/docs/security/faq) 涵盖常见的云问题。
- [Improving the threat model](https://learn.chatgpt.com/docs/security/threat-model) 解释如何改进扫描上下文和发现优先级。

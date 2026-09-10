---
title: Codex Security 插件快速入门
source_id: codex/security/plugin
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/security/plugin
owner: OpenAI
content_sha256: 5500e82828035c29a1c7c4064b6b2961169a2d20e33e71dbcf13fc2f10b8bf0a
translation_of: codex/security/plugin
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/security/plugin)

Content owner: OpenAI

# Codex Security 插件快速入门

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。可以通过在页面 URL 后附加 `.md` 来获取文档页面的 Markdown 版本。

Codex Security 会扫描你的代码以查找漏洞，并验证合理可信的
发现结果。对于每个可报告的问题，它会为你提供审查结果所需的证据和修复
指导。仅扫描你拥有或已获得
评估许可的代码。

按照此快速入门指南安装插件，并在 Codex 中对本地
代码库运行只读扫描。

本页面涵盖了在本地 Codex 聊天中运行的插件。要在 Codex 云端扫描
  已连接的 GitHub 代码库，请参见 [Codex Security 云端
  设置](https://learn.chatgpt.com/docs/security/setup)。

## 安装插件



1. 在 [ChatGPT 桌面
   应用程序](https://chatgpt.com/download/) 中打开你要在 Codex 中评估的代码库。
2. 打开 **插件**，搜索 **Codex Security**，或使用以下按钮：

   

     <ButtonLink
       href="codex://plugins/install/codex-security?marketplace=openai-curated"
       color="primary"
       variant="solid"
       size="lg"
       pill
     >
       安装 Codex Security 插件
     </ButtonLink>
   


3. 为该代码库启动一个新的 Codex 聊天。不要继续现有的聊天。





托管的桌面应用目录和公开的 Codex CLI 市场可能会提供
  不同版本的插件。在依赖某项功能或
  开始长时间扫描之前，请查看[插件
  更新日志](https://learn.chatgpt.com/docs/security/plugin/changelog)。

## 运行你的首次扫描

为获得最佳扫描质量，请使用 `gpt-5.6-sol`
配合 `xhigh` 推理强度。



<VideoPlayer
  src="/videos/codex/security/scan-setup-to-findings.mp4"
  poster="/videos/codex/security/scan-setup-to-findings-poster.webp"
/>

<WorkflowSteps variant="headings">

1. 请求普通扫描

   在新聊天中发送此提示词：

```text
   Run a Codex Security scan on this repository.
```

2. 确认设置

   Codex 在开始之前会打开一个设置工作区。对于首次运行，请使用以下
   设置：
   - **扫描类型：** `Codebase`
   - **深度扫描：** 关闭
   - **扫描区域：** `Entire codebase`
   - **威胁模型范围指导：** 除非你已经知道一个
     值得优先处理的特定攻击媒介或应用区域，否则留空。

   确认 **代码库**、**当前分支** 和 **最后提交** 标识的是
   你打算扫描的代码库。然后选择 **开始扫描**。

   <figure className="not-prose my-6">
     

       <img
         src={scanSetup.src}
         alt="Codex Security 设置工作区配置为扫描整个代码库"
         className="block h-auto w-full"
       />
     

     <figcaption className="mt-3 text-sm text-secondary">
       在开始扫描之前，配置扫描目标、扫描区域、分支以及可选的威胁模型
       指导。
     </figcaption>
   </figure>

3. 让扫描完成

   保持扫描运行，直到工作区报告已完成。如果
   Codex 识别出配置限制，请在批准配置更新之前审查该限制和
   确切的建议更改。

4. 审查结果

   使用 UI 浏览发现结果，或打开 `report.md` 作为
   完整扫描目录的入口点。

   <figure className="not-prose my-6">
     

       <img
         src={findingsWorkspace.src}
         alt="已完成 OWASP Juice Shop 的 Codex Security 发现结果工作区"
         className="block h-auto w-full"
       />
     

     <figcaption className="mt-3 text-sm text-secondary">
       按严重程度、类别、目录、补丁状态和
       审查状态浏览发现结果。
     </figcaption>
   </figure>

</WorkflowSteps>







## 扫描创建的内容



每次完成的扫描都会打开一个发现工作区。使用它来审查发现和
覆盖率，而无需检查原始产物。扫描还会创建以下
文件。



- `report.md`，扫描结果的主要可读入口点。
- `findings/<slug>/`，包含针对每个可报告发现的一份详细漏洞报告，以及可用的支持性
  概念验证文件。
- `hardening/`，包含结构强化组合以及支持性提案
  或图表（当扫描具有可报告的发现时）。
- 结构化扫描数据位于 `scan-manifest.json`、`findings.json` 和
  `coverage.json` 中，用于自动化和集成。您通常不需要
  自己打开这些文件。

在共享或存档结果时，请将完整的扫描目录放在一起，以便
来自 `report.md` 的链接能够继续工作。

## 选择您的下一个工作流

- [运行标准或限定范围的扫描](https://learn.chatgpt.com/docs/security/plugin/scans) 以审查
  使用默认工作流的存储库或单个文件夹。
- [运行深度扫描](https://learn.chatgpt.com/docs/security/plugin/deep-scans) 以进行更彻底的扫描，
  当您可以允许更长的运行时间时。
- [审查代码变更](https://learn.chatgpt.com/docs/security/plugin/code-changes) 以评估拉取
  请求、提交、分支范围或工作树补丁。
- [对积压工作进行分类](https://learn.chatgpt.com/docs/security/plugin/triage-backlog) 以审查现有的
  安全发现。
- [修复并验证发现](https://learn.chatgpt.com/docs/security/plugin/fix-findings) 在您
  接受一个发现进行修复之后。
- [导出或跟踪发现](https://learn.chatgpt.com/docs/security/plugin/export-findings) 以创建
  JSON、CSV、SARIF、需审批的 Linear、GitHub 或 Jira 工单，或私有
  草稿版 GitHub 安全公告。
- [编写漏洞报告](https://learn.chatgpt.com/docs/security/plugin/vulnerability-reports)
  将提供的发现、披露说明、源代码和 PoC 转换为
  独立报告。
- [提出安全强化建议](https://learn.chatgpt.com/docs/security/plugin/security-hardening) 以
  根据扫描结果或其他
  安全证据来考虑结构或架构选项。

---
title: 运行深度安全扫描
source_id: codex/security/plugin/deep-scans
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/security/plugin/deep-scans
owner: OpenAI
content_sha256: c60c848222715e76672b96cf92c6059d39c85378077091a010aa33ea21d90e71
translation_of: codex/security/plugin/deep-scans
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/security/plugin/deep-scans)

Content owner: OpenAI

# 运行深度安全扫描

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。通过在页面 URL 后附加 `.md`，可以获取文档页面的 Markdown 版本。

当您需要更彻底的审查并且可以接受更长的
运行时间时，请运行深度扫描。深度扫描会更广泛地搜索存储库，并且可以减少
不同运行之间的变异性。

首先进行一次 [标准扫描](https://learn.chatgpt.com/docs/security/plugin/scans)，以检查您的范围
和结果。然后，当您需要更彻底的评估时，使用深度扫描。

## 在标准扫描和深度扫描之间进行选择

|                         | 标准扫描                                      | 深度扫描                                             |
| ----------------------- | -------------------------------------------------- | ----------------------------------------------------- |
| 最适用于                | 首次运行以及常规的存储库或文件夹审查 | 标准扫描后的更彻底审查           |
| 变异性             | 标准                                           | 降低                                               |
| 范围                   | 存储库或显式文件夹                      | 存储库或显式文件夹                         |
| 运行时间和资源   | 较低                                              | 较高                                                |
| 拉取请求和差异 | 使用变更审查工作流                     | 不支持；请改用变更审查工作流 |

## 启动深度扫描

对于整个存储库的审查，发送：

```text
Use $codex-security:deep-security-scan to run a deep security scan of this repository.
```

对于单仓库（monorepo）中的单个组件，请显式指定文件夹：

```text
Use $codex-security:deep-security-scan to run a deep security scan of /absolute/path/to/repository/services/payments.
```

对于 ChatGPT 桌面应用程序中的范围限定深度扫描，所选文件夹将成为
**代码库**。扫描区域涵盖整个所选文件夹。

## 确认设置和预检

<WorkflowSteps>

1. 确认**扫描类型**为 `Codebase` 并且**深度扫描**已开启。
2. 确认**代码库**是您打算
   扫描的存储库或确切文件夹。
3. 仅为具体的攻击向量、敏感的
   应用程序区域或代码无法揭示的存储库上下文添加威胁模型指导。
4. 选择**开始扫描**。
5. 审查能力预检。如果它提出了配置更改，
   请审查确切的更改，并仅当其符合您的环境时才让 Codex 应用它。如果 Codex 告诉您需要重启，请开始一个新的聊天。

</WorkflowSteps>

深度扫描需要委托工作器以及至少六个可用的工作器插槽。如果
当前运行时不满足这些要求，请使用标准扫描或
将任务移动到通过能力预检的运行时。

在受支持的桌面应用程序版本上，发现工作器会继承您选择的
模型和推理设置。保持扫描处于活动状态，直到 Codex 报告其
完成。重新打开或重新运行已保存的扫描不会固定插件版本，
也不能保证因更新而中断的工作将恢复。在更新插件或
启动另一次深度扫描之前，请检查[插件
更新日志](https://learn.chatgpt.com/docs/security/plugin/changelog)。

<VideoPlayer
  src="/videos/codex/security/deep-scan-progress.mp4"
  poster="/videos/codex/security/deep-scan-progress-poster.webp"
/>

## 审查结果

深度扫描使用与标准扫描相同的发现工作区和完整扫描目录。
从 `report.md` 开始，它链接到每个可报告发现的详细报告，以及当发现仍然存在时的结构强化组合。在共享或归档结果时，请将链接的 `findings/` 和 `hardening/` 目录与报告一起保留。

在查看发现之前审查覆盖范围摘要。即使是深度扫描也有局限性，
因此在得出结论之前，请检查延迟的表面和剩余的证明空白。
对于您接受的发现，请继续进行[修复并验证
发现](https://learn.chatgpt.com/docs/security/plugin/fix-findings)。

要审查拉取请求、提交、分支范围或本地补丁，请使用[审查代码
更改](https://learn.chatgpt.com/docs/security/plugin/code-changes)。深度扫描永远无法替代
专注于差异（diff）的工作流。

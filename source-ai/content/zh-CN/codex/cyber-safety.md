---
title: 网络安全
source_id: codex/cyber-safety
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/cyber-safety
owner: OpenAI
content_sha256: 1e8e479eb48c513a3e31b1c37a6c5b49e0557adbd8ca107e3799d1078edd9256
translation_of: codex/cyber-safety
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/cyber-safety)

Content owner: OpenAI

# 网络安全

> 有关完整的文档索引，请参阅 [llms.txt](https://learn.chatgpt.com/llms.txt)。可以通过在页面 URL 后附加 `.md` 来获取文档页面的 Markdown 版本。

[GPT-5.3-Codex](https://openai.com/index/introducing-gpt-5-3-codex/) 是我们在 [预备框架](https://cdn.openai.com/pdf/18a02b5d-6b67-4cec-ab64-68cdfbddebcd/preparedness-framework-v2.pdf) 下视为具有高网络安全能力的第一个模型，这需要额外的保障措施。这些保障措施包括训练模型拒绝明显恶意的请求，例如窃取凭据。

除了安全训练外，基于分类器的自动监控器会检测可疑网络活动的信号，并将高风险流量路由到网络能力较弱的模型（GPT-5.2）。我们预计只有极小部分的流量会受到这些缓解措施的影响，并且我们正在努力完善我们的政策、分类器和产品内通知。

## 我们为什么要这样做

近几个月来，我们看到模型在网络安全任务上的性能有了显著提升，使开发人员和安全专业人员都受益。随着我们的模型在漏洞发现等网络安全相关任务上的能力不断提升，我们正采取预防措施：扩大保护和执行力度，以支持合法研究，同时减缓滥用行为。

网络能力本质上具有双重用途。支撑重要防御工作（如渗透测试、漏洞研究、大规模扫描、恶意软件分析和威胁情报）的相同知识和技术，也可能在现实世界中造成危害。

在可以利用它们来改善安全性的环境中，这些功能和技术需要保持可用且更易于使用。我们的 [网络安全可信访问](https://openai.com/index/trusted-access-for-cyber/) 试点项目使个人和组织能够继续使用模型进行潜在的高风险网络安全活动，而不会受到干扰。

## 工作原理

进行网络安全相关工作或可能被自动检测系统[误判](#false-positives)的类似活动的开发人员和安全专业人员，其请求可能会作为后备被重新路由到 GPT-5.2。我们预计缓解措施只会影响极小部分的流量，并且我们正在积极努力校准我们的政策和分类器。

Codex CLI 的最新 alpha 版本包含针对
  请求被重新路由时的产品内消息。此消息将在未来几天内
  得到所有客户端的支持。

受缓解措施影响的账户可以通过加入下方的 [可信访问](#trusted-access-for-cyber) 计划来恢复对 GPT-5.3-Codex 的访问。

我们认识到加入可信访问可能并不适合所有人，因此随着我们扩大这些缓解措施并[加强](https://openai.com/index/strengthening-cyber-resilience/)网络韧性，我们计划在大多数情况下从账户级别的安全检查转向请求级别的检查。

## 网络安全可信访问

我们正在试点“可信访问”，这使得开发人员能够保留高级功能，同时我们继续为正式发布校准政策和分类器。我们的目标是让极少数用户需要加入 [网络安全可信访问](https://openai.com/index/trusted-access-for-cyber/)。

要使用模型进行潜在的高风险网络安全工作：

- 用户可以在 [chatgpt.com/cyber](https://chatgpt.com/cyber) 验证其身份
- 企业可以通过其 OpenAI 代表默认为其整个团队请求 [可信访问](https://openai.com/form/enterprise-trusted-access-for-cyber/)

可能需要访问具有更强网络能力或更宽松的模型以加速合法防御工作的安全研究人员和团队，可以对我们的 [仅限邀请的计划⁠](https://docs.google.com/forms/d/e/1FAIpQLSea_ptovrS3xZeZ9FoZFkKtEJFWGxNrZb1c52GW4BVjB2KVNA/viewform?usp=header) 表示意向。拥有可信访问权限的用户仍必须遵守我们的 [使用政策⁠](https://openai.com/policies/usage-policies/) 和 [使用条款⁠](https://openai.com/policies/row-terms-of-use/)。

## 误报

合法或非网络安全的活动偶尔可能会被标记。当发生重新路由时，响应模型将在 API 请求日志和 CLI 中的产品内通知中可见，很快将在所有界面中可见。如果您遇到认为不正确的重新路由，请通过 `/feedback` 报告误报。

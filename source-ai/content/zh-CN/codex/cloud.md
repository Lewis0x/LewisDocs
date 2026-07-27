---
title: 在并行云环境中运行编码任务
source_id: codex/cloud
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/cloud
owner: OpenAI
content_sha256: ab3267843a1c7b0565eeaa04ed4dac05a01d9212fbfc5a6964388f5b65d89288
translation_of: codex/cloud
translation_model: k3
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/cloud)

Content owner: OpenAI

Codex 云端

# 在并行云环境中运行编码任务

在隔离的云环境中运行任务、并行工作，并从网页、GitHub、Linear 或 Slack 开始工作。

 打开 Codex 云端（在新标签页中打开）

 设置 Codex 云端

我们应该构建什么？让 Codex 在云端做任何事选择环境聊天代码审查归档为分析仪表板添加 CSV 导出今天 · acme/analytics-dashboard · codex/csv-export归档修复结账重试的边缘情况昨天 · harbor/payments-api · codex/retry-guard+31−1归档记录新的身份验证流程6月11日 · northstar/developer-portal · codex/auth-docs已合并+24−8归档为设置添加键盘导航6月10日 · evergreen/design-system · codex/keyboard-nav已关闭+7−4归档

01

## 并行运行工作

为较长的任务分配专用环境，让它们在你处理其他事情时继续运行。

02

## 重现环境

配置每个仓库所需的依赖项、工具、变量和设置步骤。

03

## 合并前审查

检查摘要和差异，请求后续修改，或在结果就绪时打开拉取请求。

快速入门

## 设置 Codex 云端

 连接 GitHub，创建环境，并开始你的第一个云端聊天。

1.  1 打开 Codex 并登录
   前往 [Codex](https://chatgpt.com/codex) 并使用你的 ChatGPT 账户登录。

2.  2 连接 GitHub
   按提示连接你的 GitHub 账户，然后选择 Codex 可以访问的仓库。

3.  3 创建环境
   打开 [环境设置](https://chatgpt.com/codex/settings/environments) 并为你的仓库创建一个环境。配置任务所需的任何依赖项、工具、环境变量或密钥。

   有关配置详情，请参阅 [云环境](/codex/environments/cloud-environment)。

4.  4 开始你的第一个任务
   返回 [Codex](https://chatgpt.com/codex)，选择你的环境，并描述你想要的结果。你可以观看任务日志，或让任务在后台运行。

5.  5 审查结果
   审查摘要和差异。要求 Codex 进行后续修改，或在工作就绪时打开拉取请求。

后续步骤[ 自定义云环境 ](/codex/environments/cloud-environment)[ 配置代理互联网访问 ](/codex/cloud/internet-access)[ 在 GitHub 中使用 Codex ](/codex/third-party/github)[ 在 Linear 中使用 Codex ](/codex/third-party/linear)[ 在 Slack 中使用 Codex ](/codex/third-party/slack)

## 了解 Codex 云端能做什么

为每个任务提供所需的环境，然后按你的时间安排审查结果。

01

委派多个任务

并行启动工作，并在每个任务达到可审查结果时返回查看。

了解更多

聊天代码审查安全审查归档最近7天修复文档中的失效链接7月7日 · acme/developer-portal已合并+1−1为输入和输出模态添加工具提示7月7日 · northstar/design-system已合并+31−16更早分析调查数据以发现产品痛点5月18日 · evergreen/product-research已取消

02

构建可重现的环境

配置仓库所需的依赖项、工具、变量和设置步骤。

了解更多

环境搜索环境创建环境名称仓库聊天数量共享创建者创建时间developer-docsacme/developer-portal128工作区mia@acme.example2026年6月24日ui-componentsnorthstar/design-system64工作区leo@northstar.example2026年6月10日product-insightsevergreen/product-research27工作区sam@evergreen.example2026年5月18日payments-stagingharbor/payments-api312工作区ava@harbor.example2026年4月30日

03

从你的集成中委派任务

从 GitHub 拉取请求、Linear 问题或 Slack 频道和讨论串中在 Codex 云端启动工作。

了解更多

GitHub拉取请求和问题Linear问题和评论Slack频道和讨论串

在以下情况下使用 Codex 云端…


工作需要在后台运行

委派一个较长的任务，并在其完成时再回来查看。

你想比较多次尝试的结果

并行运行任务，而不占用你的本地机器。

工作始于 GitHub、Linear 或 Slack

使用集成来移交工作，而无需离开拉取请求、问题、频道或讨论串。

你不在开发机器旁

通过网页或 Codex CLI 启动和审查工作。


其他 ChatGPT 和 Codex 界面
[ 桌面应用  在桌面上协调项目和长时间运行的任务。](/codex/app)[ ChatGPT 网页版  在浏览器中进行研究、分析和创作。](/codex/web)[ Codex CLI  在终端中检查、编辑和自动化。](/codex/cli)[ IDE 扩展  在编辑器中与 Codex 并肩处理代码。](/codex/ide)

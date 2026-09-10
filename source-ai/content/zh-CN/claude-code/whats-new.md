---
title: 新增功能
source_id: claude-code/whats-new
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/whats-new/index
owner: Anthropic
content_sha256: 9f66cbe31eb348a6d14df057a1b0bfa8dc0ee89e9e40db163a1be1723d518d34
translation_of: claude-code/whats-new
translation_model: gpt-5.6
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/whats-new/index)

Content owner: Anthropic

> ## 文档索引
> 在以下地址获取完整的文档索引：https://code.claude.com/docs/llms.txt
> 使用此文件可在深入探索之前发现所有可用页面。

# 新增功能

> 每周汇总值得关注的 Claude Code 功能，并提供代码片段、演示及其重要性背景。

每周开发摘要重点介绍最可能改变你工作方式的功能。每个条目都包含可运行的代码、简短演示以及完整文档链接。有关所有错误修复和细微改进，请参阅[变更日志](/docs/en/changelog)。

<Update label="第 29 周" description="2026 年 7 月 13 日至 17 日" tags={["v2.1.207–v2.1.212"]}>
  **Artifacts 调用你的 MCP 连接器**：已发布的 artifact 可以在每位查看者打开页面时，通过他们自己的 MCP 连接器提取实时数据并执行操作；本周还新增了公开分享链接、Team 和 Enterprise 中的编辑者角色，以及从 Claude Tag 会话创建 artifact 的功能。

  本周还有：**屏幕阅读器模式**用适合 VoiceOver 和 NVDA 等屏幕阅读器的纯线性文本取代可视化终端界面；**`/fork`** 将对话复制到新的后台会话，而你可以继续工作；**自动模式**在 Amazon Bedrock、Google Cloud Agent Platform 和 Microsoft Foundry 上不再需要选择启用变量。

  [阅读第 29 周摘要 →](/docs/en/whats-new/2026-w29)
</Update>

<Update label="第 28 周" description="2026 年 7 月 6 日至 10 日" tags={["v2.1.202–v2.1.206"]}>
  **Desktop 中的应用内浏览器**：桌面版 Claude Code 现在拥有内置浏览器，因此 Claude 可以打开文档、设计或任何其他网站，并像与你的本地开发服务器预览交互一样与页面交互。

  本周还有：**`/doctor`** 是一项完整设置检查，可诊断并修复问题，`/checkup` 是其别名；**自动模式**会阻止篡改对话记录，并在对未解析变量执行 `rm -rf` 前询问；**代理视图行**会显示带颜色的状态词和分类器撰写的标题。

  [阅读第 28 周摘要 →](/docs/en/whats-new/2026-w28)
</Update>

<Update label="第 27 周" description="2026 年 6 月 29 日至 7 月 3 日" tags={["v2.1.195–v2.1.201"]}>
  **Claude Sonnet 5**：Pro、Team Standard 和 Enterprise 订阅席位的新默认模型，以 Sonnet 的定价提供顶级编码和工具使用能力，拥有原生 1M 令牌上下文窗口，并默认开启自适应思考。

  本周还有：**Claude in Chrome** 面向所有 Anthropic 直连计划正式发布；**子代理默认在后台运行**，因此它们运行时 Claude 会继续工作；**Linux 上的 Claude Desktop** 以测试版形式登陆 Ubuntu 和 Debian；**`/radio`** 可调入 Claude FM lo-fi 广播。

  [阅读第 27 周摘要 →](/docs/en/whats-new/2026-w27)
</Update>

<Update label="第 26 周" description="2026 年 6 月 22 日至 26 日" tags={["v2.1.185–v2.1.193"]}>
  **`claude mcp login`**：直接从 shell 对已配置的 MCP 服务器进行身份验证，而无需使用交互式 `/mcp` 菜单；之后可使用 `claude mcp logout` 清除其存储的凭据。

  本周还有：**shell 模式会响应命令输出**（`! npm test` 无需第二条提示词即可获得说明）；**`/rewind`** 可以恢复运行 `/clear` 之前的对话；**后台子代理**现在会在主会话中显示权限提示，而不是自动拒绝。

  [阅读第 26 周摘要 →](/docs/en/whats-new/2026-w26)
</Update>

<Update label="第 25 周" description="2026 年 6 月 15 日至 19 日" tags={["v2.1.178–v2.1.183"]}>
  **Artifacts**：将会话输出转化为 claude.ai 上实时、可分享的页面，并随会话工作原地更新；此功能现已在 Team 和 Enterprise 计划中进入测试版。

  本周还有：**拒绝与询问规则可匹配工具参数**，使用 `Tool(param:value)`，例如 `Agent(model:opus)`；**`/config key=value`** 可从提示词、`-p` 模式和 Remote Control 设置任何配置；当你没有要求舍弃本地工作时，**自动模式会阻止破坏性 Git 命令**。

  [阅读第 25 周摘要 →](/docs/en/whats-new/2026-w25)
</Update>

<Update label="第 24 周" description="2026 年 6 月 8 日至 12 日" tags={["v2.1.166–v2.1.176"]}>
  **`/cd`**：在对话中途将当前会话移到新的工作目录，无需重建提示词缓存。

  本周还有：**子代理可以生成自己的子代理**（后台链最多可深入五层）；**`--safe-mode`** 会以禁用所有自定义项的状态启动 Claude Code，以便排查问题；**`fallbackModel`** 可按顺序配置最多三个后备模型。

  [阅读第 24 周摘要 →](/docs/en/whats-new/2026-w24)
</Update>

<Update label="第 23 周" description="2026 年 6 月 1 日至 5 日" tags={["v2.1.158–v2.1.165"]}>
  **Amazon Bedrock、Google Cloud Agent Platform 和 Microsoft Foundry 上的自动模式**：自动模式现在可通过第三方提供商用于 Opus 4.7 和 Opus 4.8，以后台安全检查取代权限提示。

  本周还有：**更安全的自动编辑**会在 `acceptEdits` 模式下写入可运行代码的文件前提示；**`/plugin list`** 会直接列出已安装的插件；**版本要求**让托管部署能够要求使用获准的 Claude Code 版本范围。

  [阅读第 23 周摘要 →](/docs/en/whats-new/2026-w23)
</Update>

<Update label="第 22 周" description="2026 年 5 月 25 日至 29 日" tags={["v2.1.150–v2.1.157"]}>
  **Claude Opus 4.8**：Max、Team Premium、Enterprise 按用量付费和 Anthropic API 账户的新默认模型，默认使用高努力程度，并为最困难的任务提供 `/effort xhigh`。

  本周还有：**动态工作流**通过 Claude 编写的脚本编排数十至数百个子代理；**security-guidance 插件**会在 Claude 工作时审查其更改中的漏洞；**快速模式**以每 MTok \$10/\$50 的价格运行 Opus 4.8。

  [阅读第 22 周摘要 →](/docs/en/whats-new/2026-w22)
</Update>

<Update label="第 21 周" description="2026 年 5 月 18 日至 22 日" tags={["v2.1.143–v2.1.149"]}>
  **Pro 计划上的自动模式**：自动模式现在可在 Pro 账户上运行，除 Opus 外还支持 Sonnet 4.6，以后台安全检查取代权限提示。

  本周还有：**`/usage`** 会按技能、子代理、插件和 MCP 服务器细分计划限制的消耗来源；新的 **`/code-review`** 命令会报告正确性错误；**后台会话**会出现在 `/resume` 中，并在固定后保持活动。

  [阅读第 21 周摘要 →](/docs/en/whats-new/2026-w21)
</Update>

<Update label="第 20 周" description="2026 年 5 月 11 日至 15 日" tags={["v2.1.139–v2.1.142"]}>
  **代理视图**：`claude agents` 会打开一个显示所有 Claude Code 会话的屏幕，其中会列出正在运行、等待你处理而受阻的内容以及已经完成的内容。

  本周还有：**`/goal`** 会让 Claude 跨轮次持续工作，直到满足完成条件；**快速模式**现在默认运行 Opus 4.7；**回退菜单**可以通过“总结到此处”压缩较早的上下文。

  [阅读第 20 周摘要 →](/docs/en/whats-new/2026-w20)
</Update>

<Update label="第 19 周" description="2026 年 5 月 4 日至 8 日" tags={["v2.1.128–v2.1.136"]}>
  **插件可从 `.zip` 压缩包和 URL 加载**：`--plugin-dir` 现在接受 `.zip` 文件，而 `--plugin-url` 会为当前会话获取插件压缩包。

  本周还有：**`worktree.baseRef`** 可选择新 worktree 从远程默认分支还是本地 `HEAD` 创建分支；**自动模式硬拒绝规则**不受允许例外影响，会无条件阻止操作；**钩子可通过 `effort.level` 和 `$CLAUDE_EFFORT` 查看当前努力程度**。

  [阅读第 19 周摘要 →](/docs/en/whats-new/2026-w19)
</Update>

<Update label="第 18 周" description="2026 年 4 月 27 日至 5 月 1 日" tags={["v2.1.120–v2.1.126"]}>
  **无需 Git Bash 的 Windows**：不再要求安装 Git for Windows，并且 Bash 不存在时，Claude Code 会使用 PowerShell 作为 shell 工具。

  本周还有：**`claude ultrareview`** 将云端代码审查带入 CI 和脚本；**`claude project purge`** 会清理项目的本地状态；将 **PR URL 粘贴到 `/resume`** 中可找到创建该 PR 的会话。

  [阅读第 18 周摘要 →](/docs/en/whats-new/2026-w18)
</Update>

<Update label="第 17 周" description="2026 年 4 月 20 日至 24 日" tags={["v2.1.114–v2.1.119"]}>
  **`/ultrareview`** 以公开研究预览形式推出：一组查找错误的代理会在云端运行，并将发现自动送回 CLI 或 Desktop。

  本周还有：**会话回顾**会显示终端失去焦点期间发生的内容；**自定义主题**允许通过 `/theme` 或插件构建和发布调色板；**Claude Code Web** 经过重新设计，新增会话侧边栏和拖放布局。

  [阅读第 17 周摘要 →](/docs/en/whats-new/2026-w17)
</Update>

<Update label="第 16 周" description="2026 年 4 月 13 日至 17 日" tags={["v2.1.105–v2.1.113"]}>
  **Claude Opus 4.7** 成为 Max 和 Team Premium 的新默认模型，并带来新的 `xhigh` 努力程度；它是大多数编码工作的推荐设置，还提供交互式 `/effort` 滑块以精细调整。

  本周还有：Claude Code Web 上的 **Routines** 可按照计划、GitHub 事件或 API 调用触发模板化云端代理；**移动推送通知**会在长任务完成或 Claude 需要你时提醒手机；`/usage` 会显示限制的消耗来源；CLI 则迁移到原生二进制文件。

  [阅读第 16 周摘要 →](/docs/en/whats-new/2026-w16)
</Update>

<Update label="第 15 周" description="2026 年 4 月 6 日至 10 日" tags={["v2.1.92–v2.1.101"]}>
  **Ultraplan** 进入早期预览：从 CLI 在云端起草计划、在 Web 编辑器中审阅和评论，然后远程运行，或将其拉回本地。首次运行现在会自动为你创建云端环境。

  本周还有：**Monitor** 工具会将后台事件流式传入对话，让 Claude 可以跟踪日志并实时响应；省略间隔时，`/loop` 会自行控制节奏；`/team-onboarding` 会将设置打包为可重放指南；`/autofix-pr` 可从终端启用 PR 自动修复。

  [阅读第 15 周摘要 →](/docs/en/whats-new/2026-w15)
</Update>

<Update label="第 14 周" description="2026 年 3 月 30 日至 4 月 3 日" tags={["v2.1.86–v2.1.91"]}>
  **计算机使用**以研究预览形式登陆 CLI：Claude 可以从终端打开原生应用、点击操作 UI 并验证更改。它最适合为只能通过 GUI 验证的内容闭合验证循环。

  本周还有：`/powerup` 交互式课程、无闪烁的备用屏幕渲染、每个工具最高 500K 的 MCP 结果大小覆盖值，以及 Bash 工具 `PATH` 中的插件可执行文件。

  [阅读第 14 周摘要 →](/docs/en/whats-new/2026-w14)
</Update>

<Update label="第 13 周" description="2026 年 3 月 23 日至 27 日" tags={["v2.1.83–v2.1.85"]}>
  **自动模式**以研究预览形式推出：分类器会处理权限提示，让安全操作不受打断地运行，并阻止有风险的操作。它是在批准一切与使用 `--dangerously-skip-permissions` 之间的折中方案。

  本周还有：Desktop 应用中的计算机使用、Web 上的 PR 自动修复、使用 `/` 搜索对话记录、适用于 Windows 的原生 PowerShell 工具，以及条件 `if` 钩子。

  [阅读第 13 周摘要 →](/docs/en/whats-new/2026-w13)
</Update>

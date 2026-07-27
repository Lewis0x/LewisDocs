# Codex 学习路径

这条路径从命令行使用开始，依次理解提示方式、项目级指令、安全审批和定制能力，再扩展到 IDE、云端任务、MCP 与 CI 自动化。建议按顺序阅读，并结合当前仓库完成一次小范围实现和验证。

## 1. 熟悉命令行入口

- [Codex CLI](/ai/zh-CN/codex/cli)

先掌握启动、选择工作目录和运行任务的基本流程，理解 Codex 如何与本地仓库协作。

## 2. 清晰描述任务

- [提示与任务说明](/ai/zh-CN/codex/prompting)

学习提供目标、约束、验收标准和相关上下文，让任务既明确又保留合理的工程判断空间。

## 3. 配置仓库规则

- [AGENTS.md 配置](/ai/zh-CN/codex/agents-md)

把团队长期有效的操作规则放在合适层级，让不同目录中的工作遵循对应约束。

## 4. 理解审批与安全

- [审批和安全机制](/ai/zh-CN/codex/approvals-security)

区分本地可回退操作与外部写入、发布、凭据处理等高风险动作，建立清晰授权边界。

## 5. 组合定制能力

- [定制能力概览](/ai/zh-CN/codex/customization)

在基础流程可靠后，再根据团队需要配置技能、工具和自动化，并持续验证它们的行为。

## 6. 校准日常使用方法

- [Codex 最佳实践](/ai/zh-CN/codex/best-practices)

把计划、上下文、验证和迭代习惯组合起来，针对不同 Codex 界面选择合适的工作方式。

## 7. 在编辑器中协作

- [Codex IDE 扩展](/ai/zh-CN/codex/ide)

利用当前文件、选区和编辑器上下文发起任务，在本地修改与云端委派之间选择合适的执行位置。

## 8. 委派云端任务

- [Codex 云端任务](/ai/zh-CN/codex/cloud)

配置隔离环境、仓库访问和任务上下文，让长时间工作在云端执行并返回可审查的结果。

## 9. 通过 MCP 扩展工具

- [Codex MCP 配置](/ai/zh-CN/codex/mcp)

为本地 Codex 客户端连接外部工具和上下文，理解配置位置、认证方式与可用能力边界。

## 10. 接入 GitHub Actions

- [Codex GitHub Action](/ai/zh-CN/codex/github-action)

在 CI/CD 中运行可重复的 Codex 任务，并为凭据、沙箱权限、输出和失败处理设置明确边界。

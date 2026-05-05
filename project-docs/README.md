# 项目文档索引

本目录是 `LewisDocs` 这个**站点工程本身**的元文档。
区别于 `docs/`（对外发布的 11 份研究内容）和 `source/`（原始 V4 源文件），本目录解释「为什么这样建站、如何开发它、如何使用它」。

> **金规则**：所有改动都走「本地编辑 → `git push` → CI 自动部署到 Cloudflare Pages」。详见 [03-开发文档 §0](./03-development.md) 与 [/CLAUDE.md](../CLAUDE.md)。

| 文档 | 受众 | 何时读 |
|---|---|---|
| [01-需求文档](./01-requirements.md) | PM / 决策者 / 新接手维护者 | 想搞清楚为什么要这个站点 |
| [02-方案文档](./02-design.md) | 架构师 / 维护者 / 评审人 | 想理解技术选型、ADR、反爬五层防御决策 |
| [03-开发文档](./03-development.md) | 开发 / 内容维护者 / 运维 | **§0 金规则：本地优先**；修改源文档、调整站点、Cloudflare 面板配置、水印取证 |
| [04-使用文档](./04-usage.md) | 阅读者 / 团队成员 | 第一次访问站点 |
| [05-注释方法学](./05-annotation-methodology.md) | 写新内容的作者 / 审 PR 的维护者 | 何时给术语加注释、用哪种通道（T1-T4 决策树） |
| [dmca-template.md](./dmca-template.md) | 维护者（出事时用） | 命中水印泄漏后的 DMCA 提交模板 + 各平台联络方 |
| [../CLAUDE.md](../CLAUDE.md) | AI 助手（自动读取） | 工作流硬规则、源文件 vs 派生文件、常见坑 |

## 与外部文档的关系

```
LewisDocs/                     本地路径推荐：D:\Work\LewisDocs\
├── source/                    源材料：V4 原始 11 份 Markdown（人工编辑）
├── docs/                      VitePress 内容
│   ├── *.md                   派生：由 source/ 自动生成（不可手改）
│   ├── public/                源材料：robots.txt / ai.txt / _headers / 蜜罐
│   └── .vitepress/            源材料：config / theme
├── scripts/                   源材料：import / rewrite-links / watermark
├── project-docs/              ← 本目录：工程的元文档
│   ├── 01-requirements.md
│   ├── 02-design.md
│   ├── 03-development.md
│   ├── 04-usage.md
│   └── dmca-template.md
├── .github/workflows/         源材料：CI 配置
├── README.md                  快速上手（部署、工作流）
├── CLAUDE.md                  AI 助手自动读取的项目硬规则
└── LICENSE                    CC BY-NC-ND 4.0 + AI Use Restriction
```

## 修订纪律

- **需求**变化 → 改 `01-requirements.md` 并在变更日志中留痕
- **方案**变化（技术栈、目录结构、构建流程） → 改 `02-design.md`，必要时新增 ADR 段落
- **开发流程**变化（脚本、命令、CI） → 改 `03-development.md`
- **使用方式**变化（导航、搜索、URL 规则） → 改 `04-usage.md`

不要把这四份文档变成"全是历史"的流水账。**它们只反映当前状态**；历史保留在 git log 里。

# 项目文档索引

本目录是 `cad-api-docs` 这个**站点工程本身**的元文档。
区别于 `docs/`（对外发布的 11 份研究内容）和 `source/`（原始 V4 源文件），本目录解释「为什么这样建站、如何开发它、如何使用它」。

| 文档 | 受众 | 何时读 |
|---|---|---|
| [01-需求文档](./01-requirements.md) | PM / 决策者 / 新接手维护者 | 想搞清楚为什么要这个站点 |
| [02-方案文档](./02-design.md) | 架构师 / 维护者 / 评审人 | 想理解技术选型、ADR、反爬五层防御决策 |
| [03-开发文档](./03-development.md) | 开发 / 内容维护者 / 运维 | 修改源文档、调整站点、Cloudflare 面板配置、水印取证 |
| [04-使用文档](./04-usage.md) | 阅读者 / 团队成员 | 第一次访问站点 |
| [dmca-template.md](./dmca-template.md) | 维护者（出事时用） | 命中水印泄漏后的 DMCA 提交模板 + 各平台联络方 |

## 与外部文档的关系

```
cad-api-docs/
├── source/                    源材料：V4 原始 11 份 Markdown（不可改）
├── docs/                      VitePress 内容（由 source 自动生成）
├── project-docs/              ← 本目录：工程的元文档
│   ├── 01-requirements.md
│   ├── 02-design.md
│   ├── 03-development.md
│   └── 04-usage.md
├── README.md                  快速上手（部署、开发循环）
└── (V4 上游) IMPLEMENTATION_PLAN.md   原始施工方案（已实施）
```

## 修订纪律

- **需求**变化 → 改 `01-requirements.md` 并在变更日志中留痕
- **方案**变化（技术栈、目录结构、构建流程） → 改 `02-design.md`，必要时新增 ADR 段落
- **开发流程**变化（脚本、命令、CI） → 改 `03-development.md`
- **使用方式**变化（导航、搜索、URL 规则） → 改 `04-usage.md`

不要把这四份文档变成"全是历史"的流水账。**它们只反映当前状态**；历史保留在 git log 里。

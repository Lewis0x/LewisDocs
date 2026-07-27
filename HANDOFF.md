# AI Agent 双语手册 MVP Handoff

- 更新时间：2026-07-27
- 目标仓库：`Lewis0x/LewisDocs`
- 工作分支：`codex/ai-agent-handbook`
- 实现基线：`4bb62e7` (`feat(ai): add manually synced bilingual agent handbook`)

## Recovery card

Goal:

- 为团队提供 Claude Code 与 Codex 官方文档的内部双语镜像。
- 通过人工触发同步抓取固定来源，并用 `kimi-k3` 只翻译发生变化的页面。

Completed:

- 固定 10 项官方来源：Claude Code 5 项、Codex 5 项。
- 唯一人工同步入口：`npm run ai:sync`。
- 私有内容根、英文规范化、SHA-256 比较、按变化翻译和失败回滚。
- 10 对双语页面、2 页中文学习路径的格式与配对校验。
- 内部 `/ai/` 路由、语言切换、本地搜索和默认公开构建隔离。
- 自动化、浏览器、视觉、规格和安全验收已完成。

Current state:

- 实现已推送到 `origin/codex/ai-agent-handbook`。
- 默认公开构建不会包含 `/ai/`。
- 公开仓库只包含代码、测试和来源元数据，不包含第三方正文、中文译文或学习路径全文。
- 尚未创建 PR，也未合并或部署。

Next step:

1. 选择一个私有、绝对路径作为 `AI_CONTENT_ROOT`。
2. 在私有内容根中人工编写两份中文学习路径。
3. 通过进程环境注入 `MOONSHOT_API_KEY`，执行首次真实同步。
4. 在 Windows 上补跑验证，并对真实内部构建执行浏览器检查。

Not verified:

- Windows 环境未运行。
- 未执行真实 Kimi 请求，因为开发验收时没有 `MOONSHOT_API_KEY`。
- 未选择最终内网托管位置。

Do not:

- 不要把 `MOONSHOT_API_KEY` 写入文件、命令参数、日志或报告。
- 不要把 `AI_CONTENT_ROOT` 指向公开仓库中的受跟踪目录。
- 不要提交 `.ai-local/`、`.ai-content/`、`docs/ai/` 或任何第三方正文/译文。
- 不要直接编辑 `docs/ai/`；它是内部构建的派生目录。
- 不要增加定时同步、PR Bot、全量抓取或第二套 `ai:*` 用户命令。

Key files:

- `project-docs/07-ai-agent-handbook-spec.md`
- `project-docs/08-ai-agent-handbook-acceptance.md`
- `source-ai/sources.yaml`
- `scripts/ai/sync.py`
- `scripts/ai/materialize.py`
- `scripts/ai/page_validation.py`
- `scripts/ai_content_gate.mjs`
- `docs/.vitepress/config.ts`

## 1. 冻结的 MVP 边界

MVP 只处理 `source-ai/sources.yaml` 中的 10 项来源，不自动发现新页面：

- Claude Code：quickstart、memory、permissions、extensions、best-practices。
- Codex：cli、prompting、agents-md、approvals-security、customization。

同步由维护者人工运行。Kimi 只负责翻译变化页，不是内容来源。以下均不在
MVP 范围：定时任务、自动 PR/合并、Academy、课程进度、离线包、签名发布、
动态 inventory 和全量站点镜像。

## 2. 环境要求

- Node.js 18 以上，推荐 Node.js 20 LTS 或 24。
- npm 9 以上。
- AI 同步启动器要求 Python 3.11 以上。
- 首次安装 JavaScript 依赖使用 `npm ci`。
- Python AI 依赖由 `scripts/run_ai_python.mjs` 和锁文件自动准备在
  `.ai-local/`，不要手工提交该目录。

确认 CLI 可用且不触发网络同步：

```sh
npm run ai:sync -- --help
```

## 3. 私有内容根

`AI_CONTENT_ROOT` 必须是已存在的绝对路径，指向私有 Git checkout、内网目录，
或开发机上已被 Git 忽略的 `.ai-content/`。不得使用符号链接，也不得位于公开
受跟踪内容中。

首次真实同步前至少准备：

```text
$AI_CONTENT_ROOT/
└── learn/
    └── zh-CN/
        ├── claude-code.md
        └── codex.md
```

每份学习路径必须按 `source-ai/sources.yaml` 顺序，恰好包含对应产品的 5 个
Markdown 路由链接；不得混入额外 Markdown 链接：

```text
/ai/zh-CN/<product>/<slug>
```

首次成功同步会接受 10 对正文；完整布局为：

```text
$AI_CONTENT_ROOT/
├── en/
│   ├── claude-code/*.md
│   └── codex/*.md
├── zh-CN/
│   ├── claude-code/*.md
│   └── codex/*.md
└── learn/
    └── zh-CN/
        ├── claude-code.md
        └── codex.md
```

学习路径是团队自有内容，不由 Kimi 生成，也不会在同步时被覆盖。

## 4. 人工同步运行手册

1. 让 `AI_CONTENT_ROOT` 在当前进程中指向私有绝对路径。
2. 首次同步或上游有变化时，通过团队批准的秘密管理方式，把
   `MOONSHOT_API_KEY` 注入当前进程环境。不要把真实值写进 shell 脚本。
3. 运行：

   ```sh
   npm run ai:sync
   ```

4. 检查终端结果及 `.ai-local/report.json`。
5. 同步结束后从当前进程环境移除 `MOONSHOT_API_KEY`。

行为约定：

- 全部哈希未变化时输出 `no changes`，不需要读取 key，也不调用 Kimi。
- 有变化但无 key 时返回 `KEY_REQUIRED`，接受内容保持不变。
- 抓取、解析、翻译、校验或写入失败时返回稳定错误码，旧接受内容继续可用。
- `.ai-local/` 只保存当前候选和无秘密报告，不是正式内容根。

## 5. 构建模式

### 默认公开模式

确保没有设置 `INCLUDE_AI_HANDBOOK=1`，然后运行：

```sh
npm run prepare-content
npm run build
```

预期结果：构建成功，`docs/ai/` 和产物 `/ai/` 路由均不存在。

### 内部模式

在同一进程环境中设置：

```text
INCLUDE_AI_HANDBOOK=1
AI_CONTENT_ROOT=<私有绝对路径>
```

然后运行：

```sh
npm run prepare-content
npm run build
```

预期结果：生成 20 个双语正文路由和 2 个中文学习路径路由，共 22 个 `/ai/`
页面。内部构建不需要 `MOONSHOT_API_KEY`。

## 6. 提交前验证

```sh
node scripts/run_ai_python.mjs --ai -- -m pytest tests/ai -q
node scripts/run_ai_python.mjs --ai -- -m basedpyright
node scripts/run_ai_python.mjs --ai -- -m ruff check scripts/ai tests/ai
node scripts/run_ai_python.mjs --ai -- -m ruff format --check scripts/ai tests/ai
node --test tests/ai/node/*.test.mjs
npm run typecheck
npm run lint:ts
npm run build
git diff --check
```

最近一次本地验收结果：

- Python：189 passed。
- Node：27 passed。
- basedpyright：0 errors、0 warnings、0 notes。
- Ruff、格式、TypeScript、Biome 和默认构建：通过。
- 内部合成构建：22 个路由并通过构建校验。
- 浏览器：375×812、768×900、1280×800 三档通过，无横向溢出或控制台错误。
- 最终规格/实现门禁与代码质量/安全评审：CLEAR。

完整验收摘要见 `project-docs/08-ai-agent-handbook-acceptance.md`。本地原始证据
目录不属于公开提交内容。

## 7. 接手后的完成条件

在宣称真实内部内容可用前，至少补齐：

1. 两份团队自有中文学习路径。
2. 一次使用真实官方来源和 `kimi-k3` 的成功同步。
3. 紧接着再运行一次 no-op，同步应显示 `no changes` 且不需要 key。
4. Windows 上的测试、双模式构建和内部站浏览器检查。
5. 确认私有内容根与最终内网托管方案不会公开第三方全文或译文。

PR、合并、部署、仓库可见性和内网发布均需要维护者单独决定。

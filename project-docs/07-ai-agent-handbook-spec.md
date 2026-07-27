# AI Agent 双语手册 MVP 规格

状态：MVP 实施基线 · 日期：2026-07-26 · 载体：LewisDocs

## 1. 规格目的

本规格定义 LewisDocs `/ai/` 文档区的首个可交付版本。
它只解决一件事：把少量、固定的 Claude Code 与 Codex 官方页面，
通过人工触发的同步流程生成可搜索、可切换语言的英文镜像与中文翻译。

本规格是 `/ai/` MVP 的范围与验收依据。现有 CAD 内容、路由、搜索和构建
行为继续遵循原有规则，不因本功能改变。

规范用语：

- “必须”表示验收所需条件。
- “应该”表示默认选择；偏离时必须说明原因。
- “可以”表示不影响 MVP 验收的实现选择。
- “公开仓库”指当前公开的 `Lewis0x/LewisDocs` GitHub 仓库。
- “接受内容”指一次成功同步后位于 `AI_CONTENT_ROOT` 的完整正文快照。
- `.ai-local/` 只存放未接受的本轮 staging 候选。

## 2. 用户结果

完成后，团队成员可以：

1. 在内部 LewisDocs 构建中阅读 10 个固定官方页面的英文镜像。
2. 阅读与每个英文页面一一对应的中文 AI 翻译。
3. 在英文与中文页面间显式切换。
4. 使用既有 VitePress 搜索查找当前语言的 AI 文档。
5. 从每个产品的一页中文学习路径开始阅读。
6. 由维护者运行一个命令，人工检查并同步上游变化。

主要读者是具备 Git、终端和 AI 编码助手基础的内部开发者。

## 3. 固定决策

- 只接入 Claude Code 与 Codex。
- 每个产品固定 5 个官方页面，共 10 个来源、10 对双语页面。
- 来源清单由维护者人工维护，不从站点地图或全量索引自动扩张。
- 唯一用户入口是 `npm run ai:sync`。
- 同步只由人工触发，不设后台任务。
- 中文翻译模型固定为 Kimi Code API 的 `kimi-for-coding`。
- Kimi 只承担翻译，不作为文档来源或站点产品分类。
- 英文页面是内容判断的基准；中文页必须声明 AI 翻译且英文为准。
- 公开仓库只跟踪 10 项来源元数据、代码和测试，不跟踪第三方正文或学习路径全文。
- 接受内容位于 `AI_CONTENT_ROOT` 指定的私有 Git checkout 或内网目录。
- 只有显式设置 `INCLUDE_AI_HANDBOOK=1` 的内部构建才生成 `/ai/`。
- 默认构建和公开 GitHub Actions / Cloudflare 构建不得生成 `/ai/`。
- GPT-SOL 负责规划、规格设计、测试设计与验收评估。

## 4. 范围

### 4.1 MVP 包含

- 人工维护的 10 项来源清单。
- 官方页面抓取与 Markdown 规范化。
- 规范化英文正文的 SHA-256 变更比较。
- 只翻译发生变化的页面。
- 英文与中文正式内容的成对更新。
- 页面来源、归属、哈希和翻译提示。
- 每个产品一页轻量中文学习路径。
- 双语路由、语言切换和站内搜索。
- 与现有 LewisDocs 构建的集成。
- 从私有内容根向内部站点派生 AI 页面。
- 有限、可重复、用户可观察的验收检查。

### 4.2 MVP 不包含

以下属于旧稿的废弃设计，不是 MVP，也不得作为完成条件：

- Academy 内容接入、Gemini CLI 或 Kimi 文档接入；
- 动态全量 inventory、课程模型、课程覆盖率；
- 定时同步、PR Bot、自动合并；
- 离线 ZIP、自带服务器；
- release、seal、signature 或 artifact 生命周期；
- 观察账本、15 门禁或复杂发布状态机；
- Cloudflare rights guard、451/410、自动撤稿；
- 多翻译服务商抽象和未来扩展框架。

当前 `package.json` 中已有九个 `ai:*` 命令的框架：
`ai:validate`、`ai:check`、`ai:inventory`、`ai:sync`、`ai:generate`、
`ai:gate`、`ai:offline`、`ai:academy-export`、`ai:rights-enforce`。
这套九命令框架属于废弃设计。MVP 实施必须从 `package.json` 删除除 `ai:sync`
外的上述八个 `ai:*` scripts，使它们不再存在；内部 Python 模块可以保留，但不是 npm 用户入口。

MVP 不改写 CAD 研究内容，不改变既有 CAD 路由，也不为 CAD 区增加多语言。
`project-docs/01-requirements.md` 当前“课程和离线包”的旧措辞由本规格取代；实施阶段必须同步改为“固定双语来源与两页轻量学习路径”。

## 5. 固定官方来源

清单必须恰好包含下列 10 项。`canonical_url` 用于页面署名与用户跳转，
`fetch_url` 用于同步获取。

### 5.1 Claude Code

| slug | canonical URL | preferred fetch URL |
|---|---|---|
| `quickstart` | `https://code.claude.com/docs/en/quickstart` | `https://code.claude.com/docs/en/quickstart.md` |
| `memory` | `https://code.claude.com/docs/en/memory` | `https://code.claude.com/docs/en/memory.md` |
| `permissions` | `https://code.claude.com/docs/en/permissions` | `https://code.claude.com/docs/en/permissions.md` |
| `extensions` | `https://code.claude.com/docs/en/features-overview` | `https://code.claude.com/docs/en/features-overview.md` |
| `best-practices` | `https://code.claude.com/docs/en/best-practices` | `https://code.claude.com/docs/en/best-practices.md` |

这 5 项的 `fetch_format` 均为 `markdown`，内容所有者为 Anthropic。

### 5.2 Codex

| slug | canonical URL | preferred fetch URL |
|---|---|---|
| `cli` | `https://learn.chatgpt.com/docs/codex/cli` | `https://learn.chatgpt.com/docs/codex/cli` |
| `prompting` | `https://learn.chatgpt.com/docs/prompting` | `https://learn.chatgpt.com/docs/prompting.md` |
| `agents-md` | `https://learn.chatgpt.com/docs/agent-configuration/agents-md` | `https://learn.chatgpt.com/docs/agent-configuration/agents-md.md` |
| `approvals-security` | `https://learn.chatgpt.com/docs/agent-approvals-security` | `https://learn.chatgpt.com/docs/agent-approvals-security.md` |
| `customization` | `https://learn.chatgpt.com/docs/customization/overview` | `https://learn.chatgpt.com/docs/customization/overview.md` |

`cli` 的 `.md` 端点只有组件外壳，因此必须抓取 canonical HTML，
其 `fetch_format` 为 `html`。其余 4 项使用 `markdown`。
这 5 项的内容所有者为 OpenAI。

不得在一次普通同步中增加、删除或替换来源。来源变更必须先由维护者修改本规格
和清单，再进入实现与验收。

## 6. 最小目录

| 路径 | 用途 |
|---|---|
| `source-ai/sources.yaml` | 公开仓库跟踪的固定来源清单 |
| `$AI_CONTENT_ROOT/en/<product>/<slug>.md` | 英文接受内容 |
| `$AI_CONTENT_ROOT/zh-CN/<product>/<slug>.md` | 中文接受内容 |
| `$AI_CONTENT_ROOT/learn/zh-CN/{claude-code,codex}.md` | 两页中文学习路径 |
| `.ai-local/fetched/` | 本轮原始抓取 |
| `.ai-local/normalized/` | 本轮规范化英文候选 |
| `.ai-local/translated/` | 本轮中文候选 |
| `.ai-local/report.json` | 本轮同步报告 |
| `docs/ai/` | 仅内部构建临时派生，不跟踪 |

约束：

- `AI_CONTENT_ROOT` 是同步和内部构建的本地接口，必须指向私有 Git checkout 或内网目录；开发时可显式指向仓库内 Git ignored 的 `.ai-content/`。
- `.ai-content/`、`.ai-local/` 和 `docs/ai/` 必须被 Git 忽略。
- `source-ai/sources.yaml` 可以公开跟踪；英文、中文和学习路径全文不得写入公开仓库中的 `source-ai/en/`、`source-ai/zh-CN/` 或 `source-ai/learn/`。
- `docs/ai/` 只从接受内容派生，不是编辑或持久保存入口。
- 实现代码可以位于现有 `scripts/ai/`，但不得形成第二套用户命令。

## 7. 来源清单

`source-ai/sources.yaml` 是人工维护的有序列表。每项只允许以下字段：

| 字段 | 含义 |
|---|---|
| `id` | 稳定标识，格式为 `<product>/<slug>` |
| `product` | `claude-code` 或 `codex` |
| `slug` | 第 5 节冻结的页面名 |
| `title` | 站点显示的英文标题 |
| `canonical_url` | 用户可访问的官方页面 |
| `fetch_url` | 同步实际请求的官方地址 |
| `fetch_format` | `markdown` 或 `html` |
| `owner` | `Anthropic` 或 `OpenAI` |

清单校验必须拒绝：

- 重复 `id`、重复产品与 slug 组合；
- 未知字段、缺失字段或空字符串；
- 非 HTTPS URL；
- 第 5 节以外的产品、页面或 URL；
- `cli` 使用非 `html` 抓取，或其他页面使用错误格式；
- 条目总数不是 10，或任一产品不是 5 项。

条目顺序只影响导航显示，不参与正文变更判断。

## 8. 页面格式与配对

### 8.1 Frontmatter

英文页和中文页必须包含下列 frontmatter 字段：

| 字段 | 英文页 | 中文页 |
|---|---|---|
| `title` | 英文标题 | 中文标题 |
| `source_id` | `<product>/<slug>` | 与英文相同 |
| `product` | `claude-code` 或 `codex` | 与英文相同 |
| `lang` | `en` | `zh-CN` |
| `canonical_url` | 清单中的官方 URL | 与英文相同 |
| `owner` | `Anthropic` 或 `OpenAI` | 与英文相同 |
| `content_sha256` | 64 位小写十六进制 | 与英文相同 |
| `translation_of` | 不使用 | 等于 `source_id` |
| `translation_model` | 不使用 | `kimi-for-coding` |
| `ai_translated` | 不使用 | `true` |

哈希是规范化英文正文的 SHA-256，不包含生成的 frontmatter。
中文页的 `content_sha256` 指向它所翻译的英文版本，不是中文正文哈希。

### 8.2 配对规则

每个清单条目必须恰好对应一份英文页和一份中文页：

- 两页的 `source_id`、`product`、`canonical_url`、`owner` 和
  `content_sha256` 必须一致。
- 文件路径中的产品与 slug 必须匹配清单。
- 中文 `translation_of` 必须等于英文 `source_id`。
- 不允许孤立英文页、孤立中文页或同一来源的多个译本。
- 正文顶部必须保留官方来源链接和内容归属。
- 中文正文顶部必须显示：
  “本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。”
- 页面不得声称 LewisDocs、维护团队或译文得到来源方官方认可。

## 9. 学习路径

MVP 只提供两份团队自有的轻量中文页：

- `$AI_CONTENT_ROOT/learn/zh-CN/claude-code.md`
- `$AI_CONTENT_ROOT/learn/zh-CN/codex.md`

每页只需包含：

1. 适合谁阅读；
2. 推荐的 5 页阅读顺序；
3. 每页一句学习目标；
4. 指向对应中文页的链接；
5. 必要时提供“遇到歧义请切换英文”的说明。

学习路径不是课程，不定义单元、课时、进度或测验。
它们是团队自有内容，不伪装成官方教程，不要求英文配对。

## 10. 路由与导航

内部构建的正式路由固定为：

```text
/ai/en/claude-code/<slug>
/ai/en/codex/<slug>
/ai/zh-CN/claude-code/<slug>
/ai/zh-CN/codex/<slug>
/ai/zh-CN/learn/claude-code
/ai/zh-CN/learn/codex
```

规则：

- 英文和中文来源页通过同一 `source_id` 配对。
- 语言切换目标必须由配对数据确定，不能只替换 URL 字符串。
- 英文页显示“中文”入口，中文页显示“English”入口。
- 两个学习路径页不显示不存在的英文切换目标。
- 内部构建的 AI 文档纳入既有 VitePress 本地搜索。
- 搜索结果必须标明语言，且能从结果进入正确语言路由。
- CAD 的现有路由、导航和搜索结果保持不变。

## 11. 人工同步

### 11.1 唯一入口

维护者只运行：

```sh
npm run ai:sync
```

该命令完成抓取、规范化、比较、必要翻译、校验和正式内容更新。
内部模块可以分工，但不得要求用户串联其他 `ai:*` 命令。

### 11.2 最小数据流

一次同步按以下顺序执行：

1. 读取并校验人工维护的 10 项清单。
2. 校验 `AI_CONTENT_ROOT` 是明确指定且不位于公开跟踪内容中的接受内容根。
3. 抓取全部 10 个固定页面到 `.ai-local/fetched/`。
4. 将响应转换为可读、稳定的规范化 Markdown，写入
   `.ai-local/normalized/`。
5. 计算每页规范化英文正文的 SHA-256，与接受内容中英文页的
   `content_sha256` 比较。
6. 对哈希未变化的页面复用现有英文与中文接受内容。
7. 只把新增或变化页面交给 `kimi-for-coding` 翻译，候选写入
   `.ai-local/translated/`。
8. 对完整 10 对候选执行清单、配对、哈希、翻译保护和页面格式校验。
9. 只有全部抓取、必要翻译和全部校验成功后，才更新
   `$AI_CONTENT_ROOT/en/` 与 `$AI_CONTENT_ROOT/zh-CN/`。
10. 写出不含秘密的 `.ai-local/report.json`，供维护者查看变化和结果。

若清单、抓取、解析、翻译、校验或可控写入任一步失败，本次命令必须以失败退出，
并且不得修改接受内容。上一次接受的双语页面继续保留。

在进入正式更新步骤之前，候选必须全部位于 `.ai-local/`。
正式更新应先准备完整文件集合，再进行短暂的接受内容根内替换。
MVP 不承诺进程崩溃、断电等情况下的跨目录事务原子性；这不降低正常失败路径
“不触碰接受内容”的要求。

### 11.3 Markdown 规范化

规范化必须满足：

- 输出 UTF-8 Markdown。
- 删除抓取时间、请求头和其他每次运行会变化的传输信息。
- 保留标题层级、段落、列表、表格、代码块、链接和图片引用。
- HTML 来源只提取官方正文，不把导航、页脚或脚本作为正文。
- 统一换行和文件结尾，避免仅由格式噪声触发翻译。
- 空正文、明显组件外壳或无法得到可读正文必须视为抓取失败。
- 不因页面标题或网络元数据变化而跳过真实正文比较。

规范化规则必须是确定的：相同有效响应产生相同 Markdown 和 SHA-256。

9 个 Markdown 来源必须返回 2xx，且 Content-Type 与正文均可识别为
Markdown；否则为 `FETCH_FAILED`。不得自动改抓 HTML 或以 HTML 外壳降级成功。

唯一 HTML 来源 `codex/cli` 必须由固定测试 fixture 锁定一个 DOM selector/path；
它必须恰好命中一个非空主正文节点，否则为 `FETCH_FAILED`。测试必须固定该 fixture
的期望 normalized Markdown 和 SHA-256。线上页面使用同一选择契约，不猜测备用 CSS 类，也不回退到整个 `body`。

### 11.4 内容准备顺序

内容准备的固定顺序是：

1. CAD import；
2. CAD rewrite，显式排除 `docs/ai/**`；
3. CAD link-citations，显式排除 `docs/ai/**`；
4. 仅当 `INCLUDE_AI_HANDBOOK=1` 时，从 `AI_CONTENT_ROOT` 将 AI 内容 materialize 到 `docs/ai/`，且必须最后运行。

CAD import 也不得生成或覆盖 `docs/ai/`。未设置开关的默认/公开准备必须确保
不存在残留 `docs/ai/` 输入；公开构建产物不得含 `/ai/` 路由。设置开关但
`AI_CONTENT_ROOT` 缺失、不可读或校验失败时必须停止构建。

## 12. Kimi 翻译

### 12.1 凭据与调用

- OpenAI 兼容端点固定为 `https://api.kimi.com/coding/v1/chat/completions`。
- 模型名固定为 `kimi-for-coding`。
- API 凭据只从环境变量 `MOONSHOT_API_KEY` 读取。
- 凭据不得写入仓库文件、`.ai-local/`、命令行参数、报告或日志。
- 所有页面哈希均未变化时，不需要 `MOONSHOT_API_KEY`，也不得调用 Kimi。
- 有变化且缺少凭据时，同步必须在修改接受内容前失败，并给出可操作提示。
- 只发送变化页面所需的规范化正文与翻译指令。

### 12.2 不得翻译的内容

翻译时必须原样保留：

- 围栏代码块及其语言标记；
- 行内代码；
- URL；
- Markdown 链接目标；
- 命令、选项、环境变量；
- 文件名与路径；
- 产品名、API 标识符和配置键。

链接可见文字可以翻译，但链接目标不得改变。
Markdown 结构必须保持可渲染；不得凭空增删事实、步骤、警告或代码。

### 12.3 翻译校验

变化页的中文候选至少校验：

- 输出非空且为 UTF-8；
- frontmatter 完整并与英文配对；
- 代码块数量与内容逐字节一致；
- 行内代码集合一致；
- URL 与链接目标集合一致；
- 命令、文件名和路径保护检查通过；
- 含固定 AI 翻译提示；
- 未混入模型解释、道歉或对话前后缀。

任一变化页失败会使整次同步失败，不允许用旧译文配新英文。

## 13. 错误与退出

MVP 只需要以下小型错误分类，报告和终端输出可使用同一代码：

| 代码 | 含义 |
|---|---|
| `MANIFEST_INVALID` | 固定来源清单不完整或不一致 |
| `FETCH_FAILED` | 官方页面无法取得或正文不可读 |
| `KEY_REQUIRED` | 有变化但未提供 Kimi 凭据 |
| `TRANSLATION_FAILED` | Kimi 调用或译文保护检查失败 |
| `VALIDATION_FAILED` | 哈希、配对、格式或路由校验失败 |
| `WRITE_FAILED` | 正式更新阶段发生本地写入错误 |

成功且无变化时退出码为 0，并明确输出 `no changes`。
失败时退出码非 0，输出受影响的 `source_id` 和错误代码，但不得输出秘密、
完整请求凭据或不必要的上游全文。

## 14. 公开与权利边界

当前 `Lewis0x/LewisDocs` GitHub 仓库与 Cloudflare 部署路径均为公开路径。本功能的公开仓库内容只能包括代码、测试和 10 项 allowlist/manifest 元数据；不得保存英文全文、中文全文或两页学习路径全文。

- 每个页面必须保留 canonical 官方来源 URL、内容所有者和“官方来源”说明。
- 英文镜像与中文译文不改变第三方内容的所有权。
- LewisDocs 自有许可证不得被描述为覆盖第三方原文或译文。
- 不得虚构 Anthropic、OpenAI 或 Moonshot 对本站的认可、合作或背书。
- 公开 GitHub Actions / Cloudflare 构建不得设置 `INCLUDE_AI_HANDBOOK=1` 或读取 `AI_CONTENT_ROOT`，并必须验证产物不含 `/ai/`。
- 两项用户结果——10 对双语页面与两页学习路径——只由私有内容根和内部站完成。
- 未经用户另行明确批准，不得改变仓库 visibility，不得创建远程私有内容库，
  也不得向任何公开托管位置发布第三方全文。
- 本规格只定义本地内容根接口，不创建远程资源；内部构建成功不等于公开授权。

本规格不设计自动权利判断。若权利边界发生变化，维护者应停止公开发布并另行
决定处理方式。

## 15. 安全与日志

- `MOONSHOT_API_KEY` 只存在于运行进程环境。
- `.ai-local/`、`.ai-content/` 与内部生成的 `docs/ai/` 必须被 Git 忽略。
- 报告只记录 `source_id`、旧/新哈希、是否变化、是否翻译和结果代码。
- 日志不得打印环境变量、认证头或完整 API 请求。
- 测试必须使用假凭据或 mock，不向真实翻译服务发送测试数据。
- 同步不得改写清单以外的接受内容。
- 网络重定向后的最终主机必须仍属于相应官方站点；否则抓取失败。

## 16. 验收

验收由 GPT-SOL 根据本节设计、评估并记录结果。实现者提供可运行证据，
但不能用实现说明代替用户可观察结果。

| ID | 场景 | 用户可观察的通过条件 |
|---|---|---|
| AC1 | 固定来源与数量 | 公开仓库清单恰为第 5 节的 10 项；接受内容包含 10 份英文和 10 份中文，共 10 对；每对 frontmatter、哈希、来源链接和归属一致。 |
| AC2 | 双语浏览与搜索 | 内部站任意来源页可双向切换语言；两页学习路径各连到 5 个中文页；搜索命中两种语言并进入正确路由；CAD 搜索与既有页面仍可用。 |
| AC3 | 幂等 no-op | 对相同上游内容连续运行两次 `npm run ai:sync`，第二次以 0 退出并显示 `no changes`，不要求 key，Kimi 调用为 0，接受内容快照和公开仓库 Git 状态不变。 |
| AC4 | 单页变化 | 受控测试只改变一个来源时，只翻译并更新接受内容中对应的一份英文和一份中文；其余 9 对字节与哈希不变；报告只标记该 `source_id`。 |
| AC5 | 五类失败保护 | 基于成功基线，分别注入 manifest、fetch、translation、validation 和可控 write 故障；每次均非 0 退出并分别显示 `MANIFEST_INVALID`、`FETCH_FAILED`、`TRANSLATION_FAILED`、`VALIDATION_FAILED`、`WRITE_FAILED`，接受内容快照不变且旧内容可构建。断电与 kill 不在此验收内。 |
| AC6 | 秘密不泄漏 | 以可识别假 key 运行成功、失败和 no-op 后，Git diff、`.ai-local/`、捕获日志和构建产物均找不到该 key；no-op 未读取或要求 key。 |
| AC7 | CAD 回归不变 | CAD 来源、路由、导航、中文搜索和回链检查继续通过；rewrite 与 link-citations 排除 `docs/ai/**`；AI 派生正文没有被 CAD 规则二次改写。 |
| AC8 | 双模式构建 | 内部验收以 `INCLUDE_AI_HANDBOOK=1` 和私有 fixture/content root 执行内容准备及 `npm run build`，产物含 10 对页面与 2 个学习路径；不设开关的公开默认构建同样通过且产物不含 `/ai/`。 |

## 17. 完成定义

只有同时满足以下条件，MVP 才算完成：

1. `npm run ai:sync` 是唯一受支持入口。
2. 清单严格包含固定 10 项官方来源。
3. `AI_CONTENT_ROOT` 内的 10 对双语页面和 2 个中文学习路径页符合本规格。
4. 无变化不需要 key、不调用 Kimi、不改文件。
5. 变化页只由 `kimi-for-coding` 翻译，并通过内容保护校验。
6. 五类可控失败路径都不改变接受内容快照。
7. 页面保留来源、归属和 AI 翻译提示，不声称官方背书。
8. 公开仓库不含全文，公开默认构建不含 `/ai/`。
9. AC1 至 AC8 均有通过证据。
10. 两种模式的 `npm run build` 均通过，CAD 回归不变。

不要求证明进程崩溃或断电时的跨目录事务原子性。

## 18. 待用户提供但不阻塞写代码的运行输入

以下输入不影响本地实现、mock 测试和规格验收准备：

- `MOONSHOT_API_KEY`：只在首次真实翻译或上游页面实际变化时，通过环境变量提供。
- 内网托管位置：在进入发布阶段时由用户决定；开发可先将
  `AI_CONTENT_ROOT` 指向本地 Git ignored 的 `.ai-content/`。

在这些输入尚未提供时，团队仍可完成代码、fixture、失败保护、no-op、
构建集成和全部不调用真实 Kimi 的测试。

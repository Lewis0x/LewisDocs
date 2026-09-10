# LewisDocs 单一双语学习路径、搜索与导航改造方案

> 状态：Implemented locally（待提交与部署）  
> 日期：2026-07-29  
> 目标读者：LewisDocs 维护者与后续实现代理

## 1. 摘要

本方案把 LewisDocs 的学习体验从“中文学习路径 + 双语参考文档”改为：

- 每个产品只有一条学习路径；
- 中文和英文只是同一学习路径的显示状态；
- 切换语言不改变 URL 或当前学习阶段；
- 未完成中文翻译的官方文档明确回退到英文；
- 搜索能够召回常用缩写、全称、中英文术语和文件名；
- 移动端目录只展示当前产品，避免 Claude Code 与 Codex 的完整目录同时展开。

本方案在学习体验、路由、导航与搜索方面取代
`2026-07-26-ai-agent-handbook.md` 中的对应设计。旧方案关于来源同步、
内容校验、敏感数据、原子物化、默认构建隔离和 CAD 回归保护的规则继续有效。

## 2. 已锁定的产品决策

1. Claude Code 和 Codex 各有且仅有一条学习路径。
2. 学习路径内部不区分中文路径和英文路径。
3. 学习路径使用原地语言切换，不因语言变化而导航到另一个 URL。
4. 学习路径只提供阶段、阅读、实践与验收说明，不记录任务完成状态或学习进度。
5. 当前翻译缺口采用分阶段收敛：英文页面继续可访问，中文缺失时明确回退英文。
6. 本轮不翻译剩余全部页面，也不立即启用严格的全量双语发布门禁。
7. 搜索和导航不得为中英文分别创建重复实体。

## 3. 目标路由与兼容性

正式学习路径固定为：

```text
/ai/learn/claude-code
/ai/learn/codex
```

官方来源页面继续使用现有路由：

```text
/ai/en/<product>/<slug>
/ai/zh-CN/<product>/<slug>
```

旧学习路径执行永久重定向：

```text
/ai/zh-CN/learn/claude-code  -> /ai/learn/claude-code
/ai/zh-CN/learn/codex       -> /ai/learn/codex
```

旧路由不得继续生成 HTML、搜索文档或独立进度。Cloudflare Pages 使用仓库内
`_redirects` 文件完成 301，不在 Cloudflare 控制台中手工配置。

## 4. 学习路径数据模型

### 4.1 文件布局

团队自有课程内容存放在：

```text
source-ai/learning/
  claude-code.path.json
  claude-code.en.json
  claude-code.zh-CN.json
  codex.path.json
  codex.en.json
  codex.zh-CN.json
```

`*.path.json` 是语言无关的规范来源；语言文件只保存显示文案。

### 4.2 结构文件

```json
{
  "version": 1,
  "product": "codex",
  "stages": [
    {
      "id": "project-instructions",
      "source_ids": ["codex/agents-md"],
      "tasks": [
        {
          "id": "create-project-guidance",
          "kind": "practice"
        },
        {
          "id": "verify-guidance-discovery",
          "kind": "verify"
        }
      ]
    }
  ]
}
```

约束：

- `version` 本轮固定为 `1`。
- `product` 只能是 `claude-code` 或 `codex`，并与文件名一致。
- 阶段和任务 ID 使用稳定的小写 kebab-case。
- 每个阶段至少包含一项阅读材料和一项实践或验证任务。
- 每个 `source_id` 必须存在于 `source-ai/sources.yaml`。
- 阶段 ID 在产品内唯一，任务 ID 在产品内全局唯一。
- 语言切换、翻译状态和页面路由不得写入结构文件。

### 4.3 语言文件

```json
{
  "version": 1,
  "product": "codex",
  "title": "Codex 学习路径",
  "summary": "通过真实、可回退的小任务掌握 Codex。",
  "stages": {
    "project-instructions": {
      "title": "建立项目级指令",
      "objective": "让 Codex 在后续任务中稳定读取项目约束。"
    }
  },
  "tasks": {
    "create-project-guidance": {
      "title": "编写项目指令",
      "instruction": "在练习仓库中添加一条可验证的项目规则。",
      "done_when": "Codex 能说明规则来源，并在任务中遵守该规则。"
    },
    "verify-guidance-discovery": {
      "title": "验证发现顺序",
      "instruction": "要求 Codex 列出当前生效的项目指令。",
      "done_when": "输出与仓库中的指令层级一致。"
    }
  }
}
```

中文和英文文件必须具有完全相同的：

- `version`；
- `product`；
- stage key 集合；
- task key 集合。

语言文件不得改变阶段顺序、任务顺序、来源链接或完成逻辑。

### 4.4 验证边界

使用现有 Python/Pydantic 边界执行严格验证：

- 模型冻结并设置 `extra="forbid"`；
- 缺少、多出或重复的 key 均导致物化失败；
- 文案必须为非空字符串；
- 结构文件引用但语言文件缺失的阶段或任务导致失败；
- 语言文件存在但结构文件未引用的孤立文案导致失败；
- 所有错误继续使用固定的 `AIAgentError` 和错误码边界。

## 5. 固定学习阶段

### 5.1 Claude Code

| 顺序 | 阶段 ID | 主要文档 | 实践目标 |
|---|---|---|---|
| 1 | `first-controlled-task` | `claude-code/quickstart` | 在练习仓库完成一次只读探索和一项小修改 |
| 2 | `project-context` | `claude-code/memory`, `claude-code/best-practices` | 建立可验证的项目记忆或项目指令 |
| 3 | `permissions-and-sandbox` | `claude-code/permissions`, `claude-code/sandboxing` | 识别读取、写入、命令和外部操作的审批边界 |
| 4 | `implementation-loop` | `claude-code/common-workflows`, `claude-code/code-review` | 完成修改、测试、diff 检查和复审闭环 |
| 5 | `subagents` | `claude-code/subagents` | 委派一次边界清晰的只读分析任务 |
| 6 | `hooks` | `claude-code/hooks-guide` | 配置一个可回退的格式化或校验 Hook |
| 7 | `mcp` | `claude-code/mcp` | 连接一个只读 MCP 并检查数据与权限边界 |
| 8 | `delivery-automation` | `claude-code/github-actions` | 阅读并本地检查自动化配置，不执行远程发布 |

### 5.2 Codex

| 顺序 | 阶段 ID | 主要文档 | 实践目标 |
|---|---|---|---|
| 1 | `first-controlled-task` | `codex/quickstart`, `codex/prompting` | 在练习仓库完成只读探索并改进一次提示 |
| 2 | `project-instructions` | `codex/agents-md` | 创建并验证一条 `AGENTS.md` 项目规则 |
| 3 | `approvals-and-sandbox` | `codex/approvals-security`, `codex/sandboxing` | 识别审批、沙箱和外部操作边界 |
| 4 | `implementation-loop` | `codex/best-practices`, `codex/code-review` | 完成修改、测试、diff 检查和代码审查 |
| 5 | `mcp` | `codex/mcp` | 连接一个只读 MCP 并确认工具调用范围 |
| 6 | `skills-and-plugins` | `codex/build-skills`, `codex/skills-and-plugins` | 把一个重复流程整理为可复用能力 |
| 7 | `cloud-and-ci` | `codex/cloud`, `codex/github-action` | 理解云任务与 CI 接口，不执行未经授权的远程写操作 |

每个阶段的语言文件都应包含：

1. 阶段目标；
2. 推荐阅读；
3. 一项可回退实践；
4. 一项可观察的完成标准；
5. 必要的权限或风险说明。

## 6. 页面组件与状态

### 6.1 组件职责

新增 `AiLearningPath` 组件：

- 读取经过验证的结构和双语文案；
- 根据当前语言渲染同一阶段与任务；
- 生成稳定锚点 `stage-<stage_id>`；
- 解析官方文档目标路由；
- 静态显示实践任务、完成标准和风险说明；
- 不提供勾选、完成状态、进度条或重置功能。

扩展现有语言切换能力：

- 来源页继续通过配对路由切换页面；
- 学习路径页使用同一控件原地切换文案；
- 两种模式共享语言状态；
- 切换学习路径语言时不得调用路由导航。

### 6.2 语言状态

本地存储键：

```text
lewisdocs:ai-language:v1
```

合法值：

```text
en
zh-CN
```

初始值优先级：

1. 合法的已保存偏好；
2. 当前官方来源页的 `frontmatter.lang`；
3. 浏览器语言以 `zh` 开头时使用 `zh-CN`；
4. 其余情况使用 `en`。

来源页点击语言切换时，在导航前写入新偏好。学习路径切换时只更新偏好和当前组件。

### 6.3 无进度状态

学习路径不写入任务完成状态，也不创建产品级进度存储键。浏览器本地只保留
全站共享的语言偏好。任务及其完成标准用于指导用户自行实践，不作为可勾选的
应用状态。

## 7. 翻译缺口与链接解析

当前英文来源数量远高于中文译文数量，本轮采用明确回退：

1. 用户选择英文时始终链接 `/ai/en/...`。
2. 用户选择中文且译文存在时链接 `/ai/zh-CN/...`。
3. 用户选择中文但译文不存在时链接英文，并在链接旁显示本地化的 `EN`/“英文回退”说明。
4. 缺少中文译文不得隐藏学习阶段、任务或英文来源。
5. 翻译覆盖率达到 100% 后，再单独移除回退政策并启用严格的成对发布门禁。

同步流程不得再按已翻译路由裁剪学习路径。学习路径结构由团队自有数据决定，
翻译状态只影响文档链接解析。

## 8. 搜索同义词与缩写

### 8.1 概念表

新增独立搜索概念模块，初始词表固定为：

| 概念 ID | 别名 | 首选来源 |
|---|---|---|
| `mcp` | `mcp`, `model context protocol`, `模型上下文协议` | `claude-code/mcp`, `codex/mcp` |
| `agents-md` | `agents.md`, `agents md`, `project instructions`, `repository instructions`, `项目指令`, `仓库指令` | `codex/agents-md` |
| `claude-md` | `claude.md`, `claude md`, `project memory`, `项目记忆` | `claude-code/memory` |
| `subagents` | `subagent`, `subagents`, `sub-agent`, `子代理`, `子智能体` | 两个产品的 subagents 页面 |
| `hooks` | `hook`, `hooks`, `钩子`, `生命周期钩子` | 两个产品的 Hooks 页面 |
| `permissions` | `permission`, `permissions`, `approval`, `approvals`, `权限`, `审批` | 权限与审批页面 |
| `sandbox` | `sandbox`, `sandboxing`, `沙箱`, `隔离执行` | 两个产品的 sandboxing 页面 |
| `skills` | `skill`, `skills`, `技能` | 两个产品的 Skills 页面 |
| `plugins` | `plugin`, `plugins`, `插件` | 插件与扩展页面 |
| `ci` | `ci`, `github actions`, `持续集成` | 两个产品的 GitHub Actions 页面 |

不得将 `model`、`context`、`agent`、`代理` 等高歧义单词独立映射到概念。

### 8.2 分词与排名

- 文本先做 Unicode NFKC、小写化、空白和标点归一化。
- 使用最长短语匹配，为命中内容附加内部 token，例如 `__ai_mcp`。
- 索引分词器保留普通词并附加概念 token。
- 查询完全等于某个别名时，只使用对应概念 token。
- 多词查询保留非别名部分，并以概念 token 代替完整别名跨度。
- 概念 token 和长度不超过 3 的缩写禁用 fuzzy 与 prefix。
- 其他词继续使用 `fuzzy: 0.2` 和 prefix。
- 字段权重为 `title: 8`, `titles: 3`, `text: 2`。
- 概念 token 的 term boost 为 6。
- 首选来源页面的 document boost 为 6。
- 与当前语言偏好一致的页面额外 boost 为 1.5。

MiniSearch `7.2.0` 应声明为直接开发依赖，避免测试依赖 VitePress 的传递依赖。

### 8.3 学习路径索引

- 每个产品的学习路径只生成一个搜索文档。
- 搜索渲染器把两种语言文案写入同一索引记录。
- 阶段使用稳定搜索锚点 `#stage-<stage_id>`，与组件实际 DOM 一致。
- 结果标题使用双语名称，例如 `Codex 学习路径 / Codex Learning Path`。
- 搜索结果不得出现中文路径和英文路径两条重复记录。

## 9. 导航与移动端

### 9.1 顶部导航与首页

- 删除“中文学习路径”“英文学习路径”等标签。
- 每个产品菜单只保留一个“学习路径”入口。
- 首页学习路径区域不再设置语言列。
- 产品卡片直接进入该产品唯一的学习路径。

### 9.2 文档侧栏

按产品和来源页语言生成四套文档侧栏：

```text
Claude Code + en
Claude Code + zh-CN
Codex + en
Codex + zh-CN
```

规则：

- 当前侧栏只展示当前产品；
- 顶部使用 `Claude Code | Codex` 分段控件切换产品；
- 分类标签按来源页语言显示；
- 分类默认折叠，当前页面所属分类自动展开；
- 中文侧栏中缺少译文的条目链接英文并标记 `EN`；
- 不在移动端同时渲染两个产品的完整文档树。

### 9.3 学习路径导航

- 学习路径页不创建语言侧栏分支；
- 页面自身提供阶段导航；
- 桌面显示紧凑的阶段索引；
- 移动端使用折叠菜单或原生选择菜单跳转阶段；
- 阶段导航使用稳定 ID，不因语言切换改变锚点。

### 9.4 上一篇与下一篇

- 来源页上一篇/下一篇限制在当前产品和当前来源语言；
- 英文回退页面按其实际英文上下文计算；
- 学习路径不参与来源文档的自动分页序列；
- 不允许 Codex 页面跳转到 Claude Code 页面。

## 10. 实施顺序

### 阶段 A：规范与数据边界

1. 更新 AI handbook 规范和需求文档。
2. 增加学习路径 JSON 模型及 Pydantic 验证。
3. 迁移现有两份中文 Markdown 内容为结构文件和双语文案。
4. 测试语言 key、来源 ID、稳定 ID 和错误边界。

### 阶段 B：单一路由与组件

1. 修改物化器，生成两个 canonical 学习页面。
2. 移除按翻译状态裁剪学习阶段的逻辑。
3. 实现语言状态和静态 `AiLearningPath`。
4. 增加旧路由 301 和构建路由验证。

### 阶段 C：搜索

1. 增加概念词表和双模式 tokenizer。
2. 接入 MiniSearch 排名配置。
3. 把学习路径双语文案合并为单一索引记录。
4. 增加真实 MiniSearch 排名回归测试。

### 阶段 D：导航与响应式

1. 将侧栏拆为产品与来源语言上下文。
2. 增加产品分段控件和学习阶段导航。
3. 修正首页、顶部菜单和文档分页。
4. 完成桌面、平板、移动端与旧 localStorage 浏览器验证。

## 11. 测试与验收

### 11.1 Python

- 接受完整、同构的中英文学习数据；
- 拒绝缺失、多余、重复或非法 ID；
- 拒绝不存在的 `source_id`；
- 生成恰好两个 canonical 学习路由；
- 不再生成旧中文学习路由；
- 翻译缺失不删除阶段；
- 物化失败继续保持原子回滚；
- 动态路由清单、搜索清单和 HTML 清单一致。

### 11.2 Node

- 语言偏好优先级和非法值回退；
- 语言偏好保存、刷新恢复和非法值回退；
- 所有搜索别名唯一且目标来源存在；
- `MCP`、完整英文名和中文名映射到同一概念；
- `AGENTS.md`、`agents md`、`项目指令`映射一致；
- 高歧义单词不触发概念映射；
- MiniSearch 实际排名满足验收阈值。

### 11.3 搜索验收

- `MCP`、`Model Context Protocol`、`模型上下文协议`：MCP 总览进入前 3。
- `AGENTS.md`、`项目指令`：Codex AGENTS.md 进入前 3。
- `hooks`、`钩子`：Hooks 指南进入前 5。
- `model`、`context`：不得被强制导向 MCP。
- 每个词表别名至少返回一项结果。
- 每个学习路径只能出现一个 canonical 搜索结果。

### 11.4 浏览器验收

在 390×844、768×1024、1280×800 三个视口验证：

- 学习路径语言切换后 URL 和锚点不变；
- 标题、任务、完成标准和链接目标同步切换；
- 中文缺失时英文回退标记清楚；
- 页面不显示任务勾选、完成百分比、进度条或重置控件；
- 移动目录只展示当前产品；
- 当前分类和当前阶段可在两次操作内到达；
- 无横向溢出、内容遮挡或控制台错误；
- 带旧 localStorage 状态时无 hydration 问题。

### 11.5 回归

- CAD 来源、路由、搜索、导航和水印流程保持不变；
- 默认构建的 AI 开关行为保持不变；
- 官方来源页双语配对和语言切换保持可用；
- 当前工作区已有的翻译、锚点本地化、taxonomy 和同步改动不得回退。

## 12. 非目标

- 不实现账号登录、云端进度或跨设备同步；
- 不实现本地学习进度、任务勾选或完成状态；
- 不把学习路径拆成中文和英文两个页面；
- 不在本轮完成全部文档翻译；
- 不改变第三方官方文档的所有权或来源声明；
- 不在 Cloudflare、GitHub Web UI 或其他远程控制台中手工配置；
- 不在未经明确授权时推送、创建 PR 或部署。

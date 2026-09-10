---
title: 提示词库
source_id: claude-code/prompt-library
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/prompt-library
owner: Anthropic
content_sha256: 922e064e2fb8742b8af2ed8b48cff81d9839e0ce998245dfb97417b93dd27ac9
translation_of: claude-code/prompt-library
translation_model: k3
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/prompt-library)

Content owner: Anthropic

> ## 文档索引
> 在以下地址获取完整的文档索引：https://code.claude.com/docs/llms.txt
> 在进一步探索之前，使用此文件发现所有可用页面。

# 提示词库

> 适用于 Claude Code 的复制粘贴提示词，按任务和角色标记。

export const PromptLibrary = ({text = {}, labels = {}, tagLabels = {}, phaseLabels = {}, sourceLabels = {}, catLabels = {}}) => {
  const RAW = useMemo(() => [{
    id: 'get-oriented-in-a',
    sdlc: 'discover',
    cat: 'Onboard',
    startN: 1,
    roles: [],
    prompt: 'give me an overview of this codebase: architecture, key directories, and how the pieces connect',
    nextHref: '/en/memory',
    src: 'workflows'
  }, {
    id: 'explain-unfamiliar-code',
    sdlc: 'discover',
    cat: 'Understand',
    roles: [],
    prompt: 'explain what {path} does and how data flows through it. write it up as {format}',
    slots: {
      path: 'src/scheduler/queue.ts',
      format: 'an HTML page with a diagram, then open it in my browser'
    },
    nextHref: '/en/output-styles',
    src: 'workflows'
  }, {
    id: 'find-where-something-happens',
    sdlc: 'discover',
    cat: 'Understand',
    startN: 2,
    roles: [],
    prompt: 'where do we {behavior}?',
    slots: {
      behavior: 'validate uploaded file types'
    },
    src: 'workflows'
  }, {
    id: 'see-what-depends-on',
    sdlc: 'discover',
    cat: 'Understand',
    roles: [],
    prompt: 'what would break if I deleted {target}?',
    slots: {
      target: 'the retryWithBackoff helper'
    },
    src: 'workflows'
  }, {
    id: 'trace-how-code-evolved',
    sdlc: 'discover',
    cat: 'Understand',
    roles: [],
    prompt: 'look through the commit history of {path} and summarize how it evolved and why',
    slots: {
      path: 'internal/auth/session.go'
    },
    src: 'best-practices'
  }, {
    id: 'scope-a-change-before',
    sdlc: 'discover',
    cat: 'Understand',
    roles: ['pm', 'design'],
    prompt: 'which files would I need to touch to {change}?',
    slots: {
      change: 'add a dark mode toggle to settings'
    },
    src: 'teams'
  }, {
    id: 'ask-the-codebase-a',
    sdlc: 'discover',
    cat: 'Understand',
    roles: ['pm'],
    prompt: 'I am a {role}. walk me through what happens when a user {action}, from the UI down to the result',
    slots: {
      role: 'PM',
      action: 'clicks Export to PDF'
    },
    nextHref: '/en/output-styles',
    src: 'teams'
  }, {
    id: 'plan-a-multi-file',
    sdlc: 'design',
    cat: 'Plan',
    roles: ['pm', 'design'],
    prompt: 'plan how to refactor the {target} to {goal}. list the files you would change, but don\'t edit anything yet',
    slots: {
      target: 'payment module',
      goal: 'support multiple currencies'
    },
    src: 'workflows'
  }, {
    id: 'draft-a-spec-by',
    sdlc: 'design',
    cat: 'Plan',
    roles: ['pm'],
    prompt: 'I want to build {feature}. interview me about implementation, UX, edge cases, and tradeoffs until we have covered everything, then write the spec to SPEC.md',
    slots: {
      feature: 'per-workspace rate limits'
    },
    nextHref: '/en/skills',
    src: 'best-practices'
  }, {
    id: 'turn-a-meeting-into',
    sdlc: 'design',
    cat: 'Plan',
    roles: ['pm'],
    prompt: 'read {input} and write up the action items, then create a {tracker} ticket for each with acceptance criteria',
    slots: {
      input: '@meeting-notes.md',
      tracker: 'Linear'
    },
    needs: 'tracker',
    nextHref: '/en/skills',
    src: 'teams'
  }, {
    id: 'map-edge-cases-before',
    sdlc: 'design',
    cat: 'Plan',
    roles: ['design', 'pm'],
    prompt: 'list the error states, empty states, and edge cases for {feature} that the design needs to cover',
    slots: {
      feature: 'the file upload flow'
    },
    src: 'teams'
  }, {
    id: 'turn-a-mockup-into',
    sdlc: 'design',
    cat: 'Prototype',
    roles: ['design', 'pm', 'marketing'],
    paste: 'mockup',
    prompt: '这是一个模型图。构建一个我可以点击操作的工作原型，与所示的布局和状态保持一致',
    src: 'teams'
  }, {
    id: 'implement-from-a-screenshot',
    sdlc: 'design',
    cat: 'Prototype',
    roles: ['design'],
    paste: 'design',
    needs: 'browser',
    prompt: '实现这个设计，然后对结果截图，与原图对比，并修复所有差异',
    nextHref: '/en/goal',
    src: 'best-practices'
  }, {
    id: 'follow-an-existing-pattern',
    sdlc: 'build',
    cat: 'Implement',
    roles: [],
    prompt: '查看 {example} 是如何实现的，以理解其模式，然后用同样的方式构建 {new}',
    slots: {
      example: 'GitHub webhook 处理器',
      new: '一个 Stripe webhook 处理器'
    },
    nextHref: '/en/memory',
    src: 'best-practices'
  }, {
    id: 'generate-docs-for-code',
    sdlc: 'build',
    cat: 'Implement',
    roles: ['docs'],
    prompt: '找出 {scope} 中缺少 {format} 注释的部分并添加注释，风格与文件中已有的保持一致',
    slots: {
      scope: 'src/auth/ 中的公共函数',
      format: 'JSDoc'
    },
    src: 'workflows'
  }, {
    id: 'add-a-small-well',
    sdlc: 'build',
    cat: 'Implement',
    roles: [],
    prompt: '添加一个 {endpoint} 端点，返回 {payload}',
    slots: {
      endpoint: '/health',
      payload: '应用版本和运行时间'
    },
    src: 'workflows'
  }, {
    id: 'build-a-small-internal',
    sdlc: 'build',
    cat: 'Implement',
    roles: ['pm', 'design', 'marketing', 'docs'],
    prompt: '使用 HTML、CSS 和原生 JavaScript 创建一个 {tool}，然后在我的浏览器中打开它',
    slots: {
      tool: '三列的拖放式看板'
    },
    src: 'teams'
  }, {
    id: 'work-an-issue-end',
    sdlc: 'build',
    cat: 'Implement',
    roles: [],
    prompt: '阅读 issue #{issue}，实现修复，并运行测试',
    slots: {
      issue: '312'
    },
    needs: 'gh',
    src: 'workflows'
  }, {
    id: 'find-and-update-copy',
    sdlc: 'build',
    cat: 'Implement',
    roles: ['design', 'docs', 'marketing'],
    prompt: '找出所有写着 "{copy}" 或类似表述的地方，逐一展示其上下文，然后将它们全部更新为 "{new}"。不要改动测试和更新日志',
    slots: {
      copy: '免费注册',
      new: '开始免费试用'
    },
    src: 'teams'
  }, {
    id: 'draft-from-past-examples',
    sdlc: 'build',
    cat: 'Implement',
    roles: ['docs', 'marketing', 'pm'],
    prompt: '阅读 {folder} 中的 {examples}，学习其结构和语气，然后为 {topic} 起草一份新的',
    slots: {
      examples: '隐私影响评估',
      folder: 'legal/pia/',
      topic: '新的分析集成'
    },
    nextHref: '/en/skills',
    src: 'legal'
  }, {
    id: 'write-tests-run-them',
    sdlc: 'build',
    cat: 'Test',
    startN: 4,
    roles: [],
    prompt: '为 {path} 编写测试，运行它们，并修复所有失败',
    slots: {
      path: 'app/parsers/feed.py'
    },
    nextHref: '/en/memory',
    src: 'workflows'
  }, {
    id: 'drive-implementation-from-tests',
    sdlc: 'build',
    cat: 'Test',
    roles: [],
    prompt: '先为 {feature} 编写测试，然后实现它直到测试通过',
    slots: {
      feature: '密码重置流程'
    },
    src: 'ebook'
  }, {
    id: 'fill-gaps-from-a',
    sdlc: 'build',
    cat: 'Test',
    roles: [],
    prompt: '阅读 {report}，为覆盖率最低的文件添加测试，直到每个文件都高于 {target}%',
    slots: {
      report: 'coverage/coverage-summary.json',
      target: '80'
    },
    nextHref: '/en/goal',
    src: 'workflows'
  }, {
    id: 'migrate-a-pattern-across',
    sdlc: 'build',
    cat: 'Refactor',
    roles: [],
    prompt: '将所有内容从 {from} 迁移到 {to}：找出每个需要修改的地方，然后完成修改',
    slots: {
      from: '旧的日志 API',
      to: '结构化日志记录器'
    },
    src: '工作流'
  }, {
    id: 'port-code-between-languages',
    sdlc: 'build',
    cat: '重构',
    roles: [],
    prompt: '将 {source} 移植到 {target}，保持相同的 {keep}',
    slots: {
      source: '这个 Python 模块',
      target: 'Rust',
      keep: '公共 API 和测试行为'
    },
    src: '团队'
  }, {
    id: 'optimize-against-a-measurable',
    sdlc: 'build',
    cat: '重构',
    roles: ['data'],
    prompt: '优化 {target}，将 {metric} 从 {current} 降到 {goal} 以下',
    slots: {
      target: '搜索查询',
      metric: 'p95 延迟',
      current: '2 秒',
      goal: '500 毫秒'
    },
    nextHref: '/en/goal',
    src: '电子书'
  }, {
    id: 'fix-a-precise-visual',
    sdlc: 'build',
    cat: '重构',
    roles: ['design'],
    prompt: '{element} 在 {viewport} 上超出了 {container} {amount}。修复它。',
    slots: {
      element: '登录按钮',
      amount: '20px',
      container: '卡片边框',
      viewport: '移动端'
    },
    nextHref: '/en/desktop#preview-your-app',
    src: '电子书'
  }, {
    id: 'review-your-changes-before',
    sdlc: 'build',
    cat: '审查',
    startN: 5,
    roles: [],
    prompt: '审查我未提交的更改，并在我提交之前标记出任何看起来有风险的地方',
    nextHref: '/en/commands',
    src: '工作流'
  }, {
    id: 'review-a-pull-request',
    sdlc: 'build',
    cat: '审查',
    roles: [],
    prompt: '审查 PR #{pr}，总结更改内容，然后列出任何疑虑',
    slots: {
      pr: '247'
    },
    needs: 'gh',
    nextHref: '/en/code-review',
    src: '工作流'
  }, {
    id: 'review-infrastructure-changes-before',
    sdlc: 'build',
    cat: '审查',
    roles: ['security', 'ops'],
    paste: 'plan',
    prompt: '这是我的 Terraform plan 输出。它将会做什么，其中有没有会引发问题的内容？',
    src: '团队'
  }, {
    id: 'run-a-security-review',
    sdlc: 'build',
    cat: '审查',
    roles: ['security'],
    prompt: '使用子代理审查 {path} 中的安全问题，并报告其发现',
    slots: {
      path: 'src/api/'
    },
    nextHref: '/en/sub-agents',
    src: '最佳实践'
  }, {
    id: 'review-content-before-sending',
    sdlc: 'build',
    cat: '审查',
    roles: ['marketing', 'docs'],
    prompt: '审查 {file} 是否存在 {concerns}，并列出在发送给 {reviewer} 之前我应该修复的任何问题',
    slots: {
      file: 'launch-post.md',
      concerns: '无依据的声明、缺失的署名以及品牌规范问题',
      reviewer: '法务'
    },
    nextHref: '/en/skills',
    src: '法务'
  }, {
    id: 'course-correct-a-wrong',
    sdlc: 'build',
    cat: '引导',
    roles: [],
    prompt: '这不对：{feedback}。换一种方法试试',
    slots: {
      feedback: '函数签名需要保持向后兼容'
    },
    nextHref: '/en/checkpointing',
    src: '最佳实践'
  }, {
    id: 'narrow-the-scope-of',
    sdlc: 'build',
    cat: '引导',
    roles: [],
    prompt: '改得太多了。只保留对 {scope} 的更改，撤销你的其他编辑',
    slots: {
      scope: 'src/forms/ 中的校验逻辑'
    },
    src: '最佳实践'
  }, {
    id: 'turn-a-correction-into',
    sdlc: 'build',
    cat: '引导',
    roles: [],
    prompt: '你一直在{mistake}。在 CLAUDE.md 中添加一条规则，让这种情况不再发生',
    slots: {
      mistake: '在这个使用命名导出的项目中使用默认导出'
    },
    nextHref: '/en/memory',
    src: '最佳实践'
  }, {
    id: 'resolve-merge-conflicts',
    sdlc: 'ship',
    cat: 'Git',
    roles: [],
    prompt: '解决此分支中的合并冲突，并解释你从每一侧保留了什么',
    src: '工作流'
  }, {
    id: 'commit-with-a-generated',
    sdlc: 'ship',
    cat: 'Git',
    roles: [],
    prompt: '提交这些更改，并附上一条总结我所做工作的消息',
    src: 'workflows'
  }, {
    id: 'open-a-pull-request',
    sdlc: 'ship',
    cat: 'Git',
    roles: [],
    prompt: '在 {tracker} 中找到关于 {topic} 的工单，并打开一个实现它的 PR',
    slots: {
      tracker: 'Linear',
      topic: '登录超时'
    },
    needs: 'tracker',
    src: 'workflows'
  }, {
    id: 'draft-release-notes-from',
    sdlc: 'ship',
    cat: 'Release',
    roles: ['pm', 'docs', 'marketing'],
    prompt: '对比 {from} 与 {to}，并按功能、修复和破坏性变更分组起草发布说明',
    slots: {
      from: 'v2.3.0',
      to: 'v2.4.0'
    },
    nextHref: '/en/skills',
    src: 'workflows'
  }, {
    id: 'write-a-ci-workflow',
    sdlc: 'ship',
    cat: 'Release',
    roles: ['ops'],
    prompt: '编写一个 GitHub Actions 工作流，在每次推送到 {branch} 时 {steps}',
    slots: {
      steps: '运行测试并部署到预发布环境',
      branch: 'main'
    },
    src: 'workflows'
  }, {
    id: 'find-and-fix-a',
    sdlc: 'operate',
    cat: 'Debug',
    startN: 3,
    roles: [],
    prompt: '{test} 测试失败了，找出原因并修复它',
    slots: {
      test: 'UserAuth'
    },
    src: 'workflows'
  }, {
    id: 'investigate-a-reported-error',
    sdlc: 'operate',
    cat: 'Debug',
    roles: ['ops'],
    prompt: '用户在 {where} 上看到了 {symptom}。调查一下，告诉我发生了什么',
    slots: {
      symptom: '500 错误',
      where: '/api/settings'
    },
    nextHref: '/en/web-quickstart#pre-fill-sessions',
    src: 'workflows'
  }, {
    id: 'fix-a-build-error',
    sdlc: 'operate',
    cat: 'Debug',
    roles: ['ops'],
    paste: 'error',
    prompt: '这是一个构建错误。修复根本原因并验证构建成功',
    src: 'best-practices'
  }, {
    id: 'investigate-a-production-incident',
    sdlc: 'operate',
    cat: 'Incident',
    roles: ['ops', 'security'],
    prompt: '{symptom}。检查日志、最近的部署和配置变更，然后告诉我最可能的原因',
    slots: {
      symptom: '结账接口一小时前开始返回 500 错误'
    },
    nextHref: '/en/mcp',
    src: 'workflows'
  }, {
    id: 'diagnose-from-a-console',
    sdlc: 'operate',
    cat: 'Incident',
    roles: ['ops', 'data'],
    paste: 'screenshot',
    prompt: '这是 {console} 的截图。带我分析为什么 {resource} 出现故障，并给出修复它的确切命令',
    slots: {
      console: 'GCP Kubernetes 仪表板',
      resource: '这个 pod'
    },
    src: 'teams'
  }, {
    id: 'query-logs-in-plain',
    sdlc: 'operate',
    cat: 'Incident',
    roles: ['security', 'ops', 'data'],
    prompt: '显示 {timeframe} 内 {scope} 的所有 {events}。编写查询、运行它，并告诉我有什么值得注意的地方',
    slots: {
      events: '失败的登录',
      scope: '认证服务',
      timeframe: '过去 24 小时'
    },
    needs: 'db',
    src: 'cybersecurity'
  }, {
    id: 'analyze-a-data-file',
    sdlc: 'operate',
    cat: 'Data',
    roles: ['data', 'pm', 'marketing'],
    paste: 'csv',
    prompt: '读取 {file}，总结关键模式，并将结果写入 {output}',
    slots: {
      file: '@reports/q1-signups.csv',
      output: '一个带图表的 HTML 页面，然后在我的浏览器中打开它'
    },
    nextHref: '/en/mcp',
    src: 'teams'
  }, {
    id: 'generate-variations-from-performance',
    sdlc: 'operate',
    cat: 'Data',
    roles: ['marketing', 'data'],
    paste: 'csv',
    prompt: '读取 {file}，找出表现不佳的 {items}，并生成 {n} 个不超过 {limit} 个字符的新变体',
    slots: {
      file: '@ads-performance.csv',
      items: '标题',
      n: '20',
      limit: '90'
    },
    nextHref: '/en/mcp',
    src: 'teams'
  }, {
    id: 'turn-a-recurring-task',
    sdlc: 'operate',
    cat: 'Automate',
    roles: [],
    prompt: '为此项目创建一个 /{name} 技能，使其 {steps}',
    slots: {
      name: 'ship',
      steps: '运行 linter 和测试，然后起草提交信息'
    },
    src: 'workflows'
  }, {
    id: 'add-a-hook-for',
    sdlc: 'operate',
    cat: 'Automate',
    roles: [],
    prompt: '编写一个在每次 {event} 之后 {action} 的钩子',
    slots: {
      action: '运行 Prettier',
      event: '编辑 .ts 或 .tsx 文件'
    },
    src: 'best-practices'
  }, {
    id: 'connect-a-tool-with',
    sdlc: 'operate',
    cat: 'Automate',
    roles: [],
    prompt: '设置 {server} MCP 服务器，以便你能直接读取我的 {data}',
    slots: {
      server: 'Sentry',
      data: '错误报告'
    },
    src: 'workflows'
  }, {
    id: 'capture-what-to-remember',
    sdlc: 'operate',
    cat: 'Automate',
    roles: ['pm', 'docs'],
    prompt: '总结本次会话所做的工作，并建议要添加到 CLAUDE.md 的内容',
    src: 'teams'
  }], []);
  const PROMPTS = useMemo(() => {
    if (typeof window !== 'undefined') {
      const rawIds = new Set(RAW.map(p => p.id));
      RAW.forEach(p => {
        if (!text[p.id]) console.warn('[prompt-library] 没有此 id 的 text[] 条目：', p.id);
      });
      Object.keys(text).forEach(k => {
        if (!rawIds.has(k)) console.warn('[prompt-library] 孤立的 text[] 键：', k);
      });
    }
    return RAW.map(p => ({
      ...p,
      title: p.id,
      teaches: '',
      ...text[p.id] || ({})
    }));
  }, [RAW, text]);
  const L = labels;
  const TL = k => tagLabels[k] || k;
  const CAT_TAG = useMemo(() => ({
    Onboard: 'understand',
    Understand: 'understand',
    Plan: 'plan',
    Prototype: 'prototype',
    Implement: 'build',
    Test: 'test',
    Refactor: 'refactor',
    Review: 'review',
    Steer: 'steer',
    Git: 'git',
    Release: 'release',
    Debug: 'debug',
    Incident: 'debug',
    Data: 'data',
    Automate: 'automate'
  }), []);
  const TAGS = useMemo(() => ['understand', 'plan', 'prototype', 'build', 'test', 'refactor', 'review', 'steer', 'debug', 'git', 'release', 'data', 'automate', 'pm', 'design', 'docs', 'marketing', 'security', 'ops'], []);
  const tagsOf = p => [CAT_TAG[p.cat], ...p.roles || []];
  const doc = useMemo(() => {
    const p = typeof window !== 'undefined' ? window.location.pathname : '';
    const base = p.startsWith('/docs/') ? '/docs' : '';
    const m = p.slice(base.length).match(/^\/([a-z]{2}(?:-[A-Z]{2})?)\//);
    const locale = m ? m[1] : 'en';
    return href => {
      if (!href || href[0] !== '/' || href[1] === '/') return href;
      return base + (href.startsWith('/en/') ? '/' + locale + href.slice(3) : href);
    };
  }, []);
  const linkify = s => {
    const out = [];
    let last = 0;
    const re = /\[([^\]]+)\]\(([^)]+)\)/g;
    for (let m; m = re.exec(s); ) {
      if (m.index > last) out.push(s.slice(last, m.index));
      out.push(<a key={m.index} href={doc(m[2])}>{m[1]}</a>);
      last = re.lastIndex;
    }
    if (last < s.length) out.push(s.slice(last));
    return out;
  };
  const codeify = s => s.split(/(`[^`]+`)/g).map((part, i) => part[0] === '`' ? <code key={i}>{part.slice(1, -1)}</code> : part);
  const SOURCES = useMemo(() => ({
    'workflows': '/en/common-workflows',
    'teams': 'https://claude.com/blog/how-anthropic-teams-use-claude-code',
    'legal': 'https://claude.com/blog/how-anthropic-uses-claude-legal',
    'cybersecurity': 'https://claude.com/blog/how-anthropic-uses-claude-cybersecurity',
    'best-practices': '/en/best-practices',
    'ebook': 'https://resources.anthropic.com/hubfs/Scaling%20agentic%20coding%20across%20your%20organization.pdf'
  }), []);
  const [mounted, setMounted] = useState(false);
  const [q, setQ] = useState('');
  const [start, setStart] = useState(true);
  const [sel, setSel] = useState(null);
  const [openId, setOpenId] = useState(null);
  const [copied, setCopied] = useState(null);
  const [fills, setFills] = useState({});
  const copyTimer = useRef(null);
  useEffect(() => {
    setMounted(true);
    return () => clearTimeout(copyTimer.current);
  }, []);
  const setFill = (id, key, val) => setFills(f => ({
    ...f,
    [id + '.' + key]: val
  }));
  const fillOf = (p, key) => {
    const v = fills[p.id + '.' + key];
    return v !== undefined ? v : p.slots && p.slots[key] !== undefined ? p.slots[key] : '';
  };
  const assemble = p => p.prompt.replace(/\{(\w+)\}/g, (_, k) => fillOf(p, k) || p.slots && p.slots[k] || k);
  const preview = p => p.prompt.replace(/\{(\w+)\}/g, (_, k) => p.slots && p.slots[k] || k);
  const bodyText = p => preview(p) + ' ' + p.teaches.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') + ' ' + (p.next || '');
  const widthFor = s => (s || '').length + 3 + 'ch';
  const ql = q.trim().toLowerCase();
  const toggleTag = k => {
    setStart(false);
    setSel(s => !ql && s === k ? null : k);
  };
  const clear = () => {
    setStart(false);
    setSel(null);
    setQ('');
  };
  const results = useMemo(() => {
    const list = PROMPTS.filter(p => {
      if (ql) return p.title.toLowerCase().includes(ql) || bodyText(p).toLowerCase().includes(ql);
      if (start) return !!p.startN;
      if (sel) return tagsOf(p).includes(sel);
      return true;
    });
    if (ql) return list;
    if (start) return list.sort((a, b) => a.startN - b.startN);
    if (sel) return list.sort((a, b) => (a.roles || []).length - (b.roles || []).length || (b.sdlc === 'operate') - (a.sdlc === 'operate'));
    return list;
  }, [PROMPTS, ql, start, sel]);
  const matchSnippet = p => {
    if (!ql || p.title.toLowerCase().includes(ql)) return null;
    const txt = bodyText(p);
    const at = txt.toLowerCase().indexOf(ql);
    if (at < 0) return null;
    const lo = Math.max(0, at - 30), hi = Math.min(txt.length, at + ql.length + 50);
    return [lo > 0 ? '…' : '', txt.slice(lo, at), <mark key="m">{txt.slice(at, at + ql.length)}</mark>, txt.slice(at + ql.length, hi), hi < txt.length ? '…' : ''];
  };
  const grouped = useMemo(() => {
    if (start && !q.trim()) return [];
    const g = {};
    for (const p of results) {
      const key = p.sdlc + '|' + p.cat;
      (g[key] = g[key] || ({
        sdlc: p.sdlc,
        cat: p.cat,
        items: []
      })).items.push(p);
    }
    return Object.values(g);
  }, [results, start, q]);
  const copy = async (str, id) => {
    try {
      await navigator.clipboard.writeText(str);
    } catch {
      const ta = document.createElement('textarea');
      ta.value = str;
      ta.setAttribute('readonly', '');
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
    }
    clearTimeout(copyTimer.current);
    setCopied(id);
    copyTimer.current = setTimeout(() => setCopied(null), 1600);
  };
  const promptBody = p => {
    if (!p.slots) return <code>{p.prompt}</code>;
    const parts = p.prompt.split(/(\{\w+\})/g);
    return <code>
        {parts.map((part, idx) => {
      const m = part.match(/^\{(\w+)\}$/);
      if (!m) return <span key={idx}>{part}</span>;
      const k = m[1];
      const val = fillOf(p, k);
      return <input key={idx} type="text" className="pl-slot" value={val} placeholder={p.slots[k] || k} aria-label={k} style={{
        width: widthFor(val || p.slots[k])
      }} onChange={e => setFill(p.id, k, e.target.value)} onFocus={e => e.target.select()} onClick={e => e.stopPropagation()} />;
    })}
      </code>;
  };
  const card = p => {
    const open = openId === p.id;
    const srcHref = SOURCES[p.src];
    const srcLabel = sourceLabels[p.src];
    const snip = matchSnippet(p);
    return <div key={p.id} className={'pl-card' + (open ? ' pl-open' : '')}>
        <button type="button" className="pl-head" onClick={() => setOpenId(open ? null : p.id)} aria-expanded={open}>
          <span className="pl-title">{p.title}</span>
          {!!p.startN && <span className="pl-chip">{L.startHere} · {p.startN}</span>}
        </button>
        {snip ? <div className="pl-match">{snip}</div> : <code className="pl-prompt-preview">{preview(p)}</code>}
        {open && <div className="pl-body">
            <div className="pl-label">{p.slots ? L.fillAndCopy : L.copyThis}</div>
            {p.needs && L.needs && L.needs[p.needs] && <div className="pl-hint pl-needs">
                <span className="pl-needs-label">{L.needsLabel}</span> {linkify(L.needs[p.needs])}
              </div>}
            {p.paste && L.paste && L.paste[p.paste] && <div className="pl-hint pl-paste">{L.paste[p.paste]}</div>}
            {p.slots && <div className="pl-hint">
                {L.hintBefore} <span className="pl-hint-chip">{L.hintChip}</span> {L.hintAfter}
              </div>}
            <div className="pl-prompt-box">
              <span className="pl-caret">{'❯'}</span>
              {promptBody(p)}
              <button type="button" className="pl-copy" onClick={() => copy(assemble(p), p.id)}>
                {copied === p.id ? L.copied : L.copy}
              </button>
            </div>
            <div className="pl-label">{L.whyWorks}</div>
            <div className="pl-teaches">{linkify(p.teaches)}</div>
            {p.nextHref && p.next && <div className="pl-next">
                <span className="pl-next-label">{L.makeItStick}</span>
                <a href={doc(p.nextHref)}>{codeify(p.next)} →</a>
              </div>}
            {srcLabel && <div className="pl-src">{L.from} {srcHref ? <a href={doc(srcHref)}>{srcLabel}</a> : srcLabel}</div>}
          </div>}
      </div>;
  };
  const STYLES = useMemo(() => `
.pl {
  --pl-accent: #D97757;
  --pl-accent-bg: rgba(217,119,87,0.07);
  --pl-bg: #fff;
  --pl-surface: #FAFAF7;
  --pl-border: #E8E6DC;
  --pl-border-subtle: rgba(31,30,29,0.08);
  --pl-text: #141413;
  --pl-text-2: #5E5D59;
  --pl-text-3: #73726C;
  --pl-text-4: #9C9A92;
  --pl-mono: var(--font-mono, ui-monospace, SFMono-Regular, Menlo, monospace);
  font-family: 'Anthropic Sans', -apple-system, BlinkMacSystemFont, sans-serif;
  font-size: 16px; color: var(--pl-text); margin: 8px 0 32px;
}
.dark .pl {
  --pl-bg: #1f1e1d;
  --pl-surface: #262624;
  --pl-border: #3d3d3a;
  --pl-border-subtle: rgba(240,238,230,0.08);
  --pl-text: #f0eee6;
  --pl-text-2: #bfbdb4;
  --pl-text-3: #91908a;
  --pl-text-4: #73726c;
}
.pl *, .pl *::before, .pl *::after { box-sizing: border-box; }
.pl button { font-family: inherit; cursor: pointer; }
.pl a { color: var(--pl-accent); text-decoration: none; }
.pl a:hover { text-decoration: underline; }

.pl-search {
  display: flex; align-items: center; gap: 10px;
  padding: 14px 18px; background: var(--pl-surface);
  border: 1px solid var(--pl-border); border-radius: 12px;
  margin-bottom: 14px;
}
.pl-search input {
  flex: 1; border: none; outline: none; background: transparent;
  font-size: 16px; color: var(--pl-text);
}
.pl-search input::placeholder { color: var(--pl-text-4); }

.pl-tags { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; margin-bottom: 18px; }
.pl-tag {
  padding: 7px 14px; border: 1px solid var(--pl-border); background: var(--pl-bg);
  font-size: 14px; color: var(--pl-text-2); border-radius: 999px;
}
.pl-tag:hover { background: var(--pl-surface); }
.pl-tag.pl-on { background: var(--pl-text); border-color: var(--pl-text); color: var(--pl-bg); }
.pl-tag.pl-start { color: var(--pl-accent); font-weight: 500; }
.pl-tag.pl-start.pl-on { background: var(--pl-accent); border-color: var(--pl-accent); color: #fff; }
.pl-tags.pl-dim .pl-tag { opacity: 0.5; }
.pl-tags.pl-dim .pl-tag:hover { opacity: 1; }
.pl-sep { width: 1px; height: 22px; background: var(--pl-border); margin: 0 4px; }
.pl-clear { border: none; background: none; font-size: 13px; color: var(--pl-text-4); padding: 4px 6px; }
.pl-clear:hover { color: var(--pl-text-2); }
.pl-count { margin-left: auto; font-size: 14px; color: var(--pl-text-4); }

.pl-group-h {
  font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--pl-text-4); margin: 24px 0 12px;
}
.pl-group-h .pl-phase { color: var(--pl-text-3); }
.pl-card {
  border: 1px solid var(--pl-border-subtle); border-radius: 10px;
  margin-bottom: 12px; background: var(--pl-bg); overflow: hidden;
  padding: 14px 18px;
}
.pl-card.pl-open { border-color: var(--pl-border); background: var(--pl-surface); }
.pl-head {
  width: 100%; display: flex; align-items: baseline; gap: 12px;
  border: none; background: transparent; text-align: left; padding: 0;
}
.pl-head:focus-visible { outline: 2px solid var(--pl-accent); outline-offset: 2px; border-radius: 6px; }
.pl-title {
  flex: 1; font-size: 17px; font-weight: 500; color: var(--pl-text);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.pl-prompt-preview {
  display: block; font-family: var(--pl-mono); font-size: 13.5px; color: var(--pl-text-3);
  margin-top: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.pl-chip {
  font-size: 11px; letter-spacing: 0.05em; text-transform: uppercase;
  padding: 3px 9px; border-radius: 999px; flex-shrink: 0;
  background: var(--pl-accent-bg); color: var(--pl-accent);
}

.pl-body { margin-top: 14px; padding-top: 14px; border-top: 1px solid var(--pl-border-subtle); }
.pl-label {
  font-size: 11.5px; letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--pl-text-4); margin: 12px 0 8px;
}
.pl-prompt-box {
  display: flex; align-items: center; gap: 10px;
  padding: 14px 16px; background: #141413; color: #f0eee6;
  border-radius: 8px; font-family: var(--pl-mono); font-size: 15px;
}
.pl-caret { color: var(--pl-accent); flex-shrink: 0; }
.pl-prompt-box code { flex: 1; background: none; padding: 0; color: inherit; white-space: pre-wrap; line-height: 1.9; }
.pl-slot {
  font-family: var(--pl-mono); font-size: inherit;
  background: rgba(217,119,87,0.15); color: #f0eee6;
  border: none; border-bottom: 1.5px dashed var(--pl-accent);
  border-radius: 4px 4px 0 0; padding: 2px 6px; margin: 0 1px;
  outline: none; min-width: 6ch; max-width: 100%;
  box-sizing: content-box; cursor: text;
}
.pl-slot:hover { background: rgba(217,119,87,0.22); }
.pl-slot:focus { background: rgba(217,119,87,0.28); border-bottom-style: solid; }
.pl-slot::placeholder { color: rgba(240,238,230,0.4); font-style: italic; }
.pl-hint { font-size: 14px; color: var(--pl-text-3); margin: 0 0 10px; }
.pl-paste { color: var(--pl-text-2); }
.pl-needs { color: var(--pl-text-2); }
.pl-needs-label {
  display: inline-block; font-size: 10.5px; letter-spacing: 0.06em;
  text-transform: uppercase; padding: 2px 7px; margin-right: 6px;
  border-radius: 4px; background: var(--pl-accent-bg); color: var(--pl-accent);
}
.pl-hint-chip {
  font-family: var(--pl-mono); font-size: 0.92em;
  background: var(--pl-accent-bg); color: var(--pl-accent);
  border-bottom: 1.5px dashed var(--pl-accent);
  border-radius: 3px 3px 0 0; padding: 1px 5px;
}
.pl-copy {
  font-size: 12.5px; padding: 6px 12px; border-radius: 6px;
  background: var(--pl-accent); color: #fff; border: none; flex-shrink: 0;
}
.pl-teaches { display: block; font-size: 15.5px; color: var(--pl-text-2); margin: 4px 0 0; line-height: 1.6; }
.pl-match {
  display: block; font-size: 13.5px; color: var(--pl-text-3);
  margin-top: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.pl-match mark { background: var(--pl-accent-bg); color: var(--pl-text); padding: 1px 2px; border-radius: 3px; }
.pl-next {
  display: flex; align-items: baseline; gap: 10px;
  margin: 14px 0 0; padding: 10px 12px;
  background: var(--pl-accent-bg); border-radius: 8px; font-size: 14.5px;
}
.pl-next-label {
  font-size: 11px; letter-spacing: 0.06em; text-transform: uppercase;
  color: var(--pl-accent); font-weight: 600; flex-shrink: 0;
}
.pl-src { display: block; font-size: 14px; color: var(--pl-text-4); margin: 14px 0 0; }

.pl-show-all {
  display: block; width: 100%; padding: 14px; margin-top: 4px;
  border: 1px dashed var(--pl-border); border-radius: 10px;
  background: transparent; font-size: 15px; color: var(--pl-accent);
  text-align: center;
}
.pl-show-all:hover { background: var(--pl-accent-bg); border-style: solid; }

.pl-empty {
  padding: 32px; text-align: center; color: var(--pl-text-4);
  border: 1px dashed var(--pl-border); border-radius: 10px;
}
`, []);
  if (!mounted) return <div className="pl" style={{
    minHeight: 480
  }} />;
  return <div className="pl">
      <style>{STYLES}</style>

      <div className="pl-search">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{
    color: 'var(--pl-text-4)'
  }}>
          <circle cx="11" cy="11" r="7" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
        <input type="text" placeholder={L.search} value={q} onChange={e => {
    setQ(e.target.value);
    if (e.target.value) setStart(false);
  }} aria-label={L.search} />
      </div>

      <div className={'pl-tags' + (ql ? ' pl-dim' : '')}>
        <button type="button" className={'pl-tag pl-start' + (!ql && start ? ' pl-on' : '')} onClick={() => {
    setQ('');
    setStart(!start);
    if (!start) setSel(null);
  }}>
          ★ {L.startHere}
        </button>
        <span className="pl-sep" />
        {TAGS.map(k => <button key={k} type="button" aria-pressed={!ql && sel === k} className={'pl-tag' + (!ql && sel === k ? ' pl-on' : '')} onClick={() => {
    setQ('');
    toggleTag(k);
  }}>
            {TL(k)}
          </button>)}
        {(start || sel || q) && <button type="button" className="pl-clear" onClick={clear}>{L.clear}</button>}
        <span className="pl-count">{results.length} {results.length === 1 ? L.prompt : L.prompts}</span>
      </div>

      {results.length === 0 ? <div className="pl-empty">
          {L.noMatch} {ql ? <code>{q}</code> : null} <button type="button" className="pl-clear" onClick={clear}>{L.clear}</button>
        </div> : !ql && start ? <div>
          <div className="pl-group-h">{L.startHereHeader}</div>
          {results.map(card)}
          <button type="button" className="pl-show-all" onClick={clear}>
            {L.showAll && L.showAll.replace('{n}', PROMPTS.length)} →
          </button>
        </div> : grouped.map(g => <div key={g.sdlc + '|' + g.cat}>
            <div className="pl-group-h"><span className="pl-phase">{phaseLabels[g.sdlc] || g.sdlc}</span> · {catLabels[g.cat] || g.cat}</div>
            {g.items.map(card)}
          </div>)}
    </div>;
};

这是一个可复制到 Claude Code 的提示词库。用它来探索你尚未尝试过的工作方式，或在你不确定从哪里开始时使用。

这些提示词收集自多份 Anthropic 指南，包括 [常见工作流](/docs/en/common-workflows)、[最佳实践](/docs/en/best-practices)，以及 [Anthropic 团队如何使用 Claude Code](https://claude.com/blog/how-anthropic-teams-use-claude-code)。它们是起点，而不是脚本。打开任意提示词下的**为什么这有效**，查看其背后的模式，从而写出你自己的提示词。

export const labels = {
  startHere: "从这里开始",
  startHereHeader: "五个可优先尝试的提示词",
  showAll: "显示全部 {n} 个提示词",
  search: "搜索提示词…",
  clear: "清除",
  prompt: "提示词",
  prompts: "提示词",
  noMatch: "没有匹配的提示词",
  fillAndCopy: "填写并复制",
  copyThis: "复制此提示词",
  hintBefore: "在",
  hintChip: "高亮",
  hintAfter: "字段中输入内容以自定义，然后复制。",
  copy: "复制",
  copied: "已复制",
  whyWorks: "为什么这有效",
  makeItStick: "让它真正固化下来",
  from: "来自",
  paste: {
    mockup: "粘贴、拖入或 @-提及你的模型图，然后发送：",
    design: "粘贴、拖入或 @-提及你的设计图，然后发送：",
    screenshot: "粘贴、拖入或 @-提及你的屏幕截图，然后发送：",
    plan: "先将你的计划输出粘贴到提示词中，然后发送：",
    error: "先将错误输出粘贴到提示词中，然后发送：",
    csv: "将你的文件拖入提示词中，或用你自己的 @-提及替换下方路径："
  },
  needsLabel: "需要",
  needs: {
    tracker: "将你的问题跟踪器添加为 [claude.ai 连接器](/docs/en/mcp#use-mcp-servers-from-claude-ai) 或 [MCP 服务器](/docs/en/mcp)。",
    gh: "已完成 [gh CLI](https://cli.github.com) 认证，或将 GitHub 添加为 [claude.ai 连接器](/docs/en/mcp#use-mcp-servers-from-claude-ai)。",
    browser: "一种让 Claude 渲染结果并截图的方式。[桌面应用](/docs/en/desktop#preview-your-app) 已内置此功能。在终端中，安装 [Chrome 扩展](/docs/en/chrome) 或 Playwright [MCP](/docs/en/mcp) 服务器。",
    db: "将你的数据仓库或日志存储添加为 [claude.ai 连接器](/docs/en/mcp#use-mcp-servers-from-claude-ai) 或 [MCP 服务器](/docs/en/mcp)。"
  }
};

export const tagLabels = {
  understand: "理解",
  plan: "规划",
  prototype: "原型",
  build: "构建",
  test: "测试",
  refactor: "重构",
  review: "审查",
  steer: "引导",
  debug: "调试",
  git: "Git",
  release: "发布",
  data: "数据",
  automate: "自动化",
  pm: "产品",
  design: "设计",
  docs: "文档",
  marketing: "市场营销",
  security: "安全",
  ops: "值班"
};

export const phaseLabels = {
  discover: "探索",
  design: "设计",
  build: "构建",
  ship: "交付",
  operate: "运营"
};

export const sourceLabels = {
  workflows: "常见工作流",
  teams: "Anthropic 团队如何使用 Claude Code",
  legal: "Anthropic 如何在法务中使用 Claude",
  cybersecurity: "Anthropic 如何在网络安全中使用 Claude",
  "best-practices": "最佳实践",
  ebook: "扩展智能体编码指南"
};

export const catLabels = {
  Onboard: "上手",
  Understand: "理解",
  Plan: "规划",
  Prototype: "原型",
  Implement: "实现",
  Test: "测试",
  Refactor: "重构",
  Review: "审查",
  Steer: "引导",
  Git: "Git",
  Release: "发布",
  Debug: "调试",
  Incident: "事故",
  Data: "数据",
  Automate: "自动化"
};

export const text = {
  "get-oriented-in-a": {
    title: "在新仓库中快速熟悉情况",
    teaches: "描述你想知道什么,而不是要读哪些文件。Claude 会自行探索项目并返回一份关于它如何组合在一起的摘要。",
    next: "运行 `/init` 来设置 `CLAUDE.md`,让 Claude 在每次会话中都记住这些"
  },
  "explain-unfamiliar-code": {
    title: "解释不熟悉的代码",
    teaches: "指明文件名,并说明你希望答案以什么格式呈现。可以把 HTML 页面换成图表、要点列表,或任何适合你学习方式的格式。",
    next: "设置输出风格,让 Claude 始终以你喜欢的格式进行解释"
  },
  "find-where-something-happens": {
    title: "找到某事发生的位置",
    teaches: "按行为而不是按文件名搜索。即使你不知道文件叫什么或在哪个目录中,搜索也能奏效。"
  },
  "see-what-depends-on": {
    title: "在删除之前检查会破坏什么",
    teaches: "在移除任何内容之前先询问。调用者和下游影响的列表会告诉你,你面对的是一行清理,还是需要协调的变更。"
  },
  "trace-how-code-evolved": {
    title: "追溯代码的演变过程",
    teaches: "当问题是"为什么"而不是"是什么"时,指向提交历史。Claude 会读取你使用的任何版本控制的日志和 blame,并解释当前实现背后的决策。"
  },
  "scope-a-change-before": {
    title: "在开始前界定变更范围",
    teaches: "在把工作提交到路线图之前先估算规模。文件列表会告诉你,你面对的是单个组件还是跨领域的变更。"
  },
  "ask-the-codebase-a": {
    title: "向代码库提出产品问题",
    teaches: "说明你的角色,以便答案以合适的层次呈现。Claude 会从源代码解释产品实际做什么,而你无需阅读代码。",
    next: "设置输出风格,让 Claude 始终以这个层次给出答案"
  },
  "plan-a-multi-file": {
    title: "在动代码之前规划多文件变更",
    teaches: "加上"先不要编辑"可以将探索与变更分开,这样你就能在任何代码变动之前看到方案。要让"先规划"成为每次提示的默认行为,按 Shift+Tab 进入 [计划模式](/docs/en/permission-modes#analyze-before-you-edit-with-plan-mode)。"
  },
  "draft-a-spec-by": {
    title: "通过访谈起草规范",
    teaches: "让 Claude 采访你,而不是自己写规范。Claude 会向你提出结构化的问题,直到需求完整,然后将结果写入文件。",
    next: "将你的访谈问题保存为 `/spec` 技能,让每份规范都以同样的方式开始"
  },
  "turn-a-meeting-into": {
    title: "把会议变成工单",
    teaches: "跳过转录步骤。Claude 从非结构化输入中提取行动项，并通过 [MCP](/docs/en/mcp) 直接写入你的跟踪工具，因此你审查的是工单，而不是转录稿。",
    next: "将其保存为 `/tickets` 技能"
  },
  "map-edge-cases-before": {
    title: "在构建之前梳理边界情况",
    teaches: "询问缺少什么，而不是已有什么。Claude 会列出顺利路径设计往往容易遗漏的错误状态、空状态和边界情况。"
  },
  "turn-a-mockup-into": {
    title: "将模型图变成可运行的原型",
    teaches: "可点击的原型能回答静态模型图无法回答的问题。把可运行的代码交给工程团队，而不是在文档中解释交互方式。"
  },
  "implement-from-a-screenshot": {
    title: "根据截图实现并自我检查",
    teaches: "这为 Claude 提供了一个验证循环：它渲染界面、与源图像对比，并自行迭代，无需你指出每一处差距。",
    next: "使用 `/goal` 让 Claude 持续迭代，直到截图匹配为止"
  },
  "follow-an-existing-pattern": {
    title: "遵循现有的模式",
    teaches: "指向你已经认可的代码。没有参考时，Claude 默认采用通用的最佳实践；有了参考，它会匹配你代码库实际使用的约定。",
    next: "让 Claude 把它遵循的模式写入 `CLAUDE.md`，这样以后的会话无需参考也能保持一致"
  },
  "add-a-small-well": {
    title: "添加一个小而定义明确的功能",
    teaches: "说明输入和输出，而不是如何构建。Claude 会找到类似代码所在的位置，并将你的代码添加在旁边。"
  },
  "build-a-small-internal": {
    title: "从零开始构建一个小型内部工具",
    teaches: "你不需要项目、框架或构建步骤。描述这个工具，并让 Claude 打开它，这样你能立即看到它运行起来。"
  },
  "work-an-issue-end": {
    title: "端到端处理一个工单",
    teaches: "提供工单编号，而不是摘要。Claude 会自己阅读完整的工单，因此你可能会忘记提到的需求也能传达，并且它会在汇报之前验证更改。"
  },
  "find-and-update-copy": {
    title: "在整个代码库中查找并更新文案",
    teaches: "要求给出各种变体并说明要跳过的内容。Claude 能找到字面搜索会遗漏的措辞，同时不改动测试夹具和历史记录，因此你只需审查用户实际看到的文案。"
  },
  "draft-from-past-examples": {
    title: "参考过去的示例起草文档",
    teaches: "指向一个已完成作品的文件夹，而不是描述你的风格。Claude 会从你已经交付的内容中学习结构和语气，因此初稿读起来就像出自你手。",
    next: "将这种语气保存为技能，让每份草稿都从这里开始"
  },
  "write-tests-run-them": {
    title: "编写测试、运行测试、修复失败",
    teaches: "把编写、运行和修复一起提出，这样 Claude 无需停下来等待指示就能持续迭代。",
    next: "运行 `/init`，让 Claude 自动学习你的测试命令"
  },
  "drive-implementation-from-tests": {
    title: "用测试驱动实现",
    teaches: "测试驱动开发：测试定义了工作何时完成，Claude 会不断迭代实现，直到测试通过。"
  },
  "fill-gaps-from-a": {
    title: "根据覆盖率报告补齐缺口",
    teaches: "指向覆盖率报告，而不是猜测哪些未测试。Claude 会读取实际数据，并为最需要测试的文件编写测试。",
    next: "将其设置为 `/goal`，让 Claude 持续编写测试，直到覆盖率达到目标"
  },
  "port-code-between-languages": {
    title: "将代码移植到另一种语言",
    teaches: "说明要保留什么，而不只是目标语言。指出必须保持不变的 API 或行为，为 Claude 提供了一个可以对照检查移植结果的契约。"
  },
  "generate-docs-for-code": {
    title: "为缺少文档的代码生成文档",
    teaches: "说明范围和格式。Claude 会找出缺失的部分，并匹配文件中已有的注释风格，让新文档读起来与其余部分一致。"
  },
  "migrate-a-pattern-across": {
    title: "在整个代码库中迁移某个模式",
    teaches: "描述旧模式和新模式。先让 Claude 找出每一处位置，意味着调用点会列在回复中，这样你可以检查是否有遗漏。"
  },
  "optimize-against-a-measurable": {
    title: "针对可衡量的目标进行优化",
    teaches: "说明指标和目标值，就为 Claude 给出了明确的完成定义。",
    next: "将其设置为 `/goal`，让 Claude 持续测量和迭代，直到达到该数值"
  },
  "fix-a-precise-visual": {
    title: "修复一个精确的视觉问题",
    teaches: "精确的视觉反馈能带来精确的修复。说明确切的元素、尺寸和视口。",
    next: "添加一个预览工具，让 Claude 自行截图并验证修复效果"
  },
  "review-your-changes-before": {
    title: "在提交前审查你的更改",
    teaches: "在修复成本还低的时候发现问题。Claude 会完整阅读被修改的文件，而不仅仅是 diff 行，因此能发现快速自查容易遗漏的问题。",
    next: "运行 `/code-review`，用一条命令完成同样的检查"
  },
  "review-a-pull-request": {
    title: "审查一个拉取请求",
    teaches: "Claude 在整个代码库的上下文中进行审查，而不仅仅是看 diff。它会阅读被修改的代码及其调用对象，因此能发现仅看 diff 的审查会遗漏的问题。",
    next: "通过 Code Review 为每个 PR 开启此功能"
  },
  "review-infrastructure-changes-before": {
    title: "在应用前审查基础设施变更",
    teaches: "计划输出内容密集且难以浏览。把它粘贴过来，就能在应用之前得到一份通俗易懂的实际变更摘要。"
  },
  "run-a-security-review": {
    title: "使用子代理运行安全审查",
    teaches: "[子代理](/docs/en/sub-agents) 在自己的上下文窗口中运行审计并汇报摘要，因此漫长的安全审查不会占满你的主会话。内置的通用子代理无需额外配置即可处理此任务。",
    next: "设置一个整个团队都能使用的专用安全审查子代理"
  },
  "review-content-before-sending": {
    title: "在正式审查前发现问题",
    teaches: "在人工投入时间之前先做一轮检查。说明你希望检查的重点，让审查更有针对性，然后修复发现的问题，发出一份更干净的草稿。",
    next: "将你的审查清单保存为整个团队都能运行的技能"
  },
  "course-correct-a-wrong": {
    title: "纠正错误的方向",
    teaches: "指出 Claude 遗漏的约束，而不只是说它错了。具体的理由能给 Claude 一个在重试时需要满足的具体约束，而不是再次猜测。",
    next: "按两次 `Esc` 打开回退菜单，恢复代码和对话，让重试从干净的状态开始"
  },
  "narrow-the-scope-of": {
    title: "缩小更改的范围",
    teaches: "当方向正确但更改范围过大时，让 Claude 保留其中一部分，而不是全部回退。明确的边界能防止一个小修复演变成一次重构。"
  },
  "turn-a-correction-into": {
    title: "把一次纠正变成一条规则",
    teaches: "聊天中的纠正不会与团队共享。写入项目 [CLAUDE.md](/docs/en/memory) 的规则在提交后即被共享，Claude 会在每次会话开始时读取它。",
    next: "打开 `/memory` 查看 Claude 所写的内容"
  },
  "resolve-merge-conflicts": {
    title: "解决合并冲突",
    teaches: "说明你想要的状态，而不是保留哪些标记。要求给出推理过程能让合并结果可审查，而不是一个黑盒。"
  },
  "commit-with-a-generated": {
    title: "使用生成的消息提交",
    teaches: "让 Claude 从 diff 推导提交消息。它会匹配你仓库现有的提交风格。"
  },
  "open-a-pull-request": {
    title: "从工单创建拉取请求",
    teaches: "跳过在追踪器、编辑器和 GitHub 之间的上下文切换。一个提示即可读取规范、完成修改并创建 PR。"
  },
  "draft-release-notes-from": {
    title: "根据 git 历史起草发布说明",
    teaches: "给出两个参考点和你想要的结构。Claude 会读取两者之间的提交日志并起草一份可编辑的更新日志。",
    next: "将其保存为 `/changelog` 技能"
  },
  "write-a-ci-workflow": {
    title: "编写 CI 工作流",
    teaches: "描述它应在何时运行、应做什么;YAML 会为你生成,并匹配你项目的构建和测试命令。"
  },
  "find-and-fix-a": {
    title: "找到并修复失败的测试",
    teaches: "描述症状即可;你不需要知道哪个文件出了问题。Claude 会运行测试以查看失败,追溯到源代码,并修复它。"
  },
  "investigate-a-reported-error": {
    title: "调查报告的错误",
    teaches: "描述症状和位置;Claude 会读取相关代码路径并追踪可能的原因。如果有堆栈跟踪或日志,请一并粘贴。",
    next: "在你的运维手册中放置一个深度链接,用预填的提示打开 Claude"
  },
  "fix-a-build-error": {
    title: "从根源修复构建错误",
    teaches: "要求找到根本原因并进行验证,可以防止那种只抑制错误而不解决问题的表面补丁。"
  },
  "investigate-a-production-incident": {
    title: "调查生产事故",
    teaches: "列出要关联的证据来源,而不是要采取的步骤。Claude 会综合读取日志、git 历史和配置来缩小原因范围。",
    next: "通过 MCP 连接 Sentry 或你的日志存储"
  },
  "query-logs-in-plain": {
    title: "用自然语言查询日志",
    teaches: "直接提问,而不是编写 SQL。Claude 会构建查询、针对你连接的日志运行它,并同时显示查询和结果,以便你检查实际执行的内容。"
  },
  "diagnose-from-a-console": {
    title: "根据控制台截图进行诊断",
    teaches: "云控制台能告诉你问题所在,但不会告诉你修复命令。Claude 会读取截图,并将仪表盘内容翻译成需要运行的 kubectl、gcloud 或 aws 命令。"
  },
  "analyze-a-data-file": {
    title: "分析数据文件",
    teaches: "一次性问题不需要一次性脚本。指向项目文件夹中的文件,Claude 会直接读取它、找出规律,并将输出写到你指定的位置。",
    next: "通过 MCP 连接数据源,而不是导出文件"
  },
  "generate-variations-from-performance": {
    title: "根据效果数据生成变体",
    teaches: "在一开始就说明约束条件,让生成保持在限制范围内。Claude 会读取指标、选择要替换的内容,并生成符合要求的替代方案。",
    next: "通过 MCP 连接广告平台,而不是导出文件"
  },
  "turn-a-recurring-task": {
    title: "将重复性任务变成技能",
    teaches: "把步骤命名一次;即可作为命令重复使用。Claude 会编写一个 [技能](/docs/en/skills),团队中的任何人都可以运行。"
  },
  "add-a-hook-for": {
    title: "为重复行为添加钩子",
    teaches: "钩子可以让行为自动发生,而不需要你记得去要求。描述触发条件和动作,Claude 会编写 [钩子](/docs/en/hooks) 配置。"
  },
  "connect-a-tool-with": {
    title: "通过 MCP 连接工具",
    teaches: "连接一次数据源,而不是每次会话都粘贴数据。完成 [MCP](/docs/en/mcp) 设置后,当你询问时,Claude 会直接从工具中读取。"
  },
  "capture-what-to-remember": {
    title: "记录下次要记住的内容",
    teaches: "在你忘记之前先问。Claude 知道本次会话中它必须弄清楚的内容，并提出 [CLAUDE.md](/docs/en/memory) 条目，以便下次会话能从这些上下文开始。"
  }
};

<PromptLibrary text={text} labels={labels} tagLabels={tagLabels} phaseLabels={phaseLabels} sourceLabels={sourceLabels} catLabels={catLabels} />

## 是什么让这些提示词奏效

上面的提示词有几个共同的模式。识别这些模式有助于你将这里的任何提示词适配到自己的任务中。

**描述结果，而不是步骤。** 说出你想要什么，让 Claude 自己去查找文件。下面的提示词无需指明任何文件路径即可生效。

```text theme={null}
add rate limiting to the public API and make sure existing tests still pass
```

**给它一种检查自己工作的方式。** 在同一个提示词中要求运行、测试、比较或验证，这样 Claude 会迭代而不是在一次尝试后就停止。

```text theme={null}
write the migration, run it against the dev database, and confirm the schema matches
```

**指向一个参考。** 指定一个现有的文件、测试或模式作为匹配目标，这样新代码就能与你已有的内容保持一致。

```text theme={null}
add a settings page that follows the same layout as the profile page
```

**说明可衡量的目标。** 当目标是性能或覆盖率时，给出指标和阈值，使完成标准明确无误。

```text theme={null}
get the bundle size under 200KB and show me what you removed
```

**给它实际产物。** 将错误、日志、截图和计划输出直接粘贴到提示词中，或输入 `@` 来引用文件。Claude 会读取原始内容，而不是你的转述。

```text theme={null}
why is the build failing? @build.log
```

**说明你想要的回答方式。** 指明格式、长度或受众，使解释符合你的使用方式。要让某种格式成为每次回复的默认格式，请设置 [output style](/docs/en/output-styles)。

```text theme={null}
explain how the payment retry logic works as an HTML page with a diagram, then open it in my browser
```

有关每种模式的更多信息，请参阅 [best practices](/docs/en/best-practices)。

## 这些提示词来自哪里

这些提示词基于 Anthropic 已发布资源中的模式。每张卡片都链接到其来源：

* [Common workflows](/docs/en/common-workflows)：核心任务的分步指南
* [Best practices](/docs/en/best-practices)：提示词模式与项目设置
* [How Anthropic teams use Claude Code](https://claude.com/blog/how-anthropic-teams-use-claude-code)：来自工程、产品、设计和数据团队的真实工作流程，并深入探讨了 [legal](https://claude.com/blog/how-anthropic-uses-claude-legal)、[marketing](https://claude.com/blog/how-anthropic-uses-claude-marketing) 和 [cybersecurity](https://claude.com/blog/how-anthropic-uses-claude-cybersecurity)
* [Scaling agentic coding guide](https://resources.anthropic.com/hubfs/Scaling%20agentic%20coding%20across%20your%20organization.pdf)：企业采用指南

有关这些模式的视频演示，请参阅 Anthropic Academy 上的免费 [Claude Code in Action](https://anthropic.skilljar.com/claude-code-in-action) 课程。

## 相关资源

本页上的提示词是起点。一旦某个提示词在你的项目中奏效，下一步就是让它可重复：将其保存为 [skill](/docs/en/skills)，这样团队中的任何人都可以将其作为 `/command` 运行，并将 Claude 学到的约定记录在 [CLAUDE.md](/docs/en/memory) 中，让每次会话都能带着这些上下文开始，而不是让 Claude 重新学习。对于更大或风险更高的更改，[plan mode](/docs/en/permission-modes#analyze-before-you-edit-with-plan-mode) 会在任何编辑发生之前向你展示文件列表。

如果你要在整个团队中推广 Claude Code，请参阅 [administration](/docs/en/admin-setup) 了解托管设置和策略，并参阅 [costs and usage](/docs/en/costs) 了解这些工作在你的套餐中如何计费。

export const AI_CATEGORIES = Object.freeze([
  {
    id: 'start',
    label: '入门与概览',
    labels: { en: 'Getting started', 'zh-CN': '入门与概览' },
  },
  {
    id: 'workflows',
    label: '工作流与实践',
    labels: { en: 'Workflows and practices', 'zh-CN': '工作流与实践' },
  },
  {
    id: 'clients',
    label: '客户端与使用界面',
    labels: { en: 'Clients and interfaces', 'zh-CN': '客户端与使用界面' },
  },
  {
    id: 'configuration',
    label: '配置与上下文',
    labels: { en: 'Configuration and context', 'zh-CN': '配置与上下文' },
  },
  {
    id: 'agents',
    label: 'Agent 与协作',
    labels: { en: 'Agents and collaboration', 'zh-CN': 'Agent 与协作' },
  },
  {
    id: 'extensions',
    label: '工具、扩展与集成',
    labels: { en: 'Tools, extensions, and integrations', 'zh-CN': '工具、扩展与集成' },
  },
  {
    id: 'sdk',
    label: 'SDK、API 与开发',
    labels: { en: 'SDK, API, and development', 'zh-CN': 'SDK、API 与开发' },
  },
  {
    id: 'automation',
    label: '自动化与交付',
    labels: { en: 'Automation and delivery', 'zh-CN': '自动化与交付' },
  },
  {
    id: 'security',
    label: '安全、权限与治理',
    labels: { en: 'Security, permissions, and governance', 'zh-CN': '安全、权限与治理' },
  },
  {
    id: 'enterprise',
    label: '企业部署与平台',
    labels: { en: 'Enterprise deployment and platforms', 'zh-CN': '企业部署与平台' },
  },
  {
    id: 'models',
    label: '模型、成本与用量',
    labels: { en: 'Models, cost, and usage', 'zh-CN': '模型、成本与用量' },
  },
  {
    id: 'reference',
    label: '参考、排障与更新',
    labels: { en: 'Reference, troubleshooting, and updates', 'zh-CN': '参考、排障与更新' },
  },
])

const CLAUDE_CODE_RULES = [
  ['sdk', [/^agent-sdk\//]],
  [
    'security',
    [
      /^(authentication|data-usage|legal-and-compliance|network-config)$/,
      /^(permission-modes|permissions|sandbox-environments|sandboxing)$/,
      /^(security|security-guidance|zero-data-retention)$/,
    ],
  ],
  [
    'enterprise',
    [
      /^(admin-setup|amazon-bedrock|claude-platform-on-aws)$/,
      /^claude-apps-gateway(?:-.+)?$/,
      /^(communications-kit|corporate-launcher|gateways)$/,
      /^(google-vertex-ai|llm-gateway(?:-.+)?|managed-mcp)$/,
      /^(microsoft-foundry|server-managed-settings|third-party-integrations)$/,
    ],
  ],
  [
    'models',
    [
      /^(analytics|costs|fast-mode|model-config|monitoring-usage)$/,
      /^(prompt-caching)$/,
    ],
  ],
  [
    'automation',
    [
      /^(desktop-scheduled-tasks|github-actions|gitlab-ci-cd)$/,
      /^(headless|hooks|hooks-guide|routines|scheduled-tasks|workflows)$/,
    ],
  ],
  [
    'agents',
    [
      /^(advisor|agent-teams|agent-view|agents|goal)$/,
      /^(subagents|ultraplan|ultrareview)$/,
    ],
  ],
  [
    'extensions',
    [
      /^(channels|channels-reference|discover-plugins|mcp|mcp-quickstart)$/,
      /^(plugin-.+|plugins|plugins-reference|skills|slack)$/,
      /^(tools-reference)$/,
    ],
  ],
  [
    'clients',
    [
      /^(accessibility|chrome|claude-code-on-the-web|computer-use)$/,
      /^desktop(?:-.+)?$/,
      /^(fullscreen|interactive-mode|jetbrains|keybindings|mobile)$/,
      /^(platforms|remote-control|terminal-config|voice-dictation)$/,
      /^(vs-code|web-quickstart)$/,
    ],
  ],
  [
    'configuration',
    [
      /^(claude-directory|context-window|debug-your-config|env-vars)$/,
      /^(memory|output-styles|prompt-library|settings|statusline)$/,
    ],
  ],
  [
    'workflows',
    [
      /^(artifacts|best-practices|checkpointing|code-review)$/,
      /^(common-workflows|large-codebases|sessions|worktrees)$/,
    ],
  ],
  [
    'start',
    [
      /^(extensions|feature-availability|how-it-works|overview)$/,
      /^(quickstart|setup)$/,
    ],
  ],
]

const CODEX_RULES = [
  [
    'security',
    [
      /^(approvals-security|cyber-safety|permission-modes|permissions)$/,
      /^sandboxing(?:\/.+)?$/,
      /^security(?:\/.+)?$/,
      /^(security-administration)$/,
    ],
  ],
  [
    'enterprise',
    [
      /^(administration|amazon-bedrock|auth)$/,
      /^enterprise(?:\/.+)?$/,
      /^environments(?:\/.+)?$/,
    ],
  ],
  [
    'sdk',
    [
      /^(app-server|codex-sdk|developers|mcp-server|open-source)$/,
      /^extend(?:\/.+)?$/,
    ],
  ],
  [
    'automation',
    [
      /^(automations|github-action|hooks|non-interactive-mode|notifications)$/,
    ],
  ],
  [
    'agents',
    [
      /^agent-configuration(?:\/.+)?$/,
      /^(agents-md|pets)$/,
    ],
  ],
  [
    'extensions',
    [
      /^(build-plugins|build-skills|mcp|plugins|skills-and-plugins)$/,
      /^third-party(?:\/.+)?$/,
    ],
  ],
  [
    'clients',
    [
      /^app(?:\/.+)?$/,
      /^(appshots|browser|chrome-extension|cli|cli-customization)$/,
      /^cli(?:\/.+)?$/,
      /^cloud(?:\/.+)?$/,
      /^(computer-use|ide|integrated-terminal|remote-connections|use-chatgpt|web)$/,
      /^ide(?:\/.+)?$/,
      /^windows(?:\/.+)?$/,
    ],
  ],
  [
    'configuration',
    [
      /^config-file(?:\/.+)?$/,
      /^(configuration|custom-prompts|customization|personalize)$/,
      /^customization(?:\/.+)?$/,
    ],
  ],
  [
    'models',
    [
      /^(feature-maturity|models|pricing)$/,
      /^features(?:\/.+)$/,
    ],
  ],
  [
    'workflows',
    [
      /^(artifacts-viewer|best-practices|code-review|image-generation)$/,
      /^(image-inputs|import|long-running-work|projects|prompting|sites)$/,
      /^(visualizations)$/,
      /^guides(?:\/.+)?$/,
    ],
  ],
  [
    'start',
    [
      /^(community\/codex-for-oss|features|get-started-with-work|overview)$/,
      /^(quickstart|resources|videos)$/,
    ],
  ],
]

const PRODUCT_RULES = {
  'claude-code': CLAUDE_CODE_RULES,
  codex: CODEX_RULES,
}

export const classifyAiSource = (source) => {
  const rules = PRODUCT_RULES[source.product] ?? []
  for (const [category, patterns] of rules) {
    if (patterns.some((pattern) => pattern.test(source.slug))) return category
  }
  return 'reference'
}

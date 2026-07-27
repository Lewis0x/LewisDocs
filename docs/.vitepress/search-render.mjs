export function createSearchRenderer(includeAiHandbook) {
  return (src, env, md) => {
    const html = md.render(src, env)
    if (
      env.frontmatter?.search === false ||
      env.relativePath.startsWith('superpowers/plans/')
    ) {
      return ''
    }
    if (!includeAiHandbook || !env.relativePath.startsWith('ai/')) return html

    const frontmatterTitle = env.frontmatter?.title
    const learningTitle = env.relativePath.endsWith('/learn/claude-code.md')
      ? '中文 · Claude Code 学习路径'
      : env.relativePath.endsWith('/learn/codex.md')
        ? '中文 · Codex 学习路径'
        : undefined
    const title = typeof frontmatterTitle === 'string' ? frontmatterTitle : learningTitle
    if (title === undefined) return html

    const titledSource = src.replace(/^#\s+.+$/m, `# ${title}`)
    return md.render(titledSource === src ? `# ${title}\n\n${src}` : titledSource, env)
  }
}

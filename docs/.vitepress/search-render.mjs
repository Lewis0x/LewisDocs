export function buildLearningSearchMarkdown(path, en, zh) {
  const lines = [
    `# ${zh.title} / ${en.title}`,
    '',
    zh.summary,
    '',
    en.summary,
  ]
  for (const stage of path.stages) {
    const zhStage = zh.stages[stage.id]
    const enStage = en.stages[stage.id]
    lines.push(
      '',
      `## ${zhStage.title} / ${enStage.title} {#stage-${stage.id}}`,
      '',
      zhStage.objective,
      '',
      enStage.objective,
      '',
      stage.source_ids.join(' '),
    )
    for (const task of stage.tasks) {
      const zhTask = zh.tasks[task.id]
      const enTask = en.tasks[task.id]
      lines.push(
        '',
        `### ${zhTask.title} / ${enTask.title}`,
        '',
        zhTask.instruction,
        '',
        enTask.instruction,
        '',
        zhTask.done_when,
        '',
        enTask.done_when,
      )
    }
  }
  return `${lines.join('\n')}\n`
}

export function createSearchRenderer(includeAiHandbook, learningPages = {}) {
  return (src, env, md) => {
    const html = md.render(src, env)
    if (
      env.frontmatter?.search === false ||
      env.relativePath.startsWith('superpowers/plans/')
    ) {
      return ''
    }
    if (!includeAiHandbook || !env.relativePath.startsWith('ai/')) return html

    const learningPage = learningPages[env.relativePath]
    if (typeof learningPage === 'string') {
      return md.render(learningPage, env)
    }

    const frontmatterTitle = env.frontmatter?.title
    const title =
      typeof frontmatterTitle === 'string' ? frontmatterTitle : undefined
    if (title === undefined) return html

    const titledSource = src.replace(/^#\s+.+$/m, `# ${title}`)
    return md.render(titledSource === src ? `# ${title}\n\n${src}` : titledSource, env)
  }
}

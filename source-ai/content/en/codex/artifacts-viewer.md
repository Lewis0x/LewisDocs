---
title: Work with files
source_id: codex/artifacts-viewer
product: codex
lang: en
canonical_url: https://developers.openai.com/codex/artifacts-viewer
owner: OpenAI
content_sha256: db0ff3a369f56c899a2d8f6dee916501dd9220a49245b2647ef002671895dcc2
---
[Official source](https://developers.openai.com/codex/artifacts-viewer)

Content owner: OpenAI

# Work with files

> For the complete documentation index, see [llms.txt](https://learn.chatgpt.com/llms.txt). Markdown versions of documentation pages are available by appending `.md` to the page URL.

When a task produces a file, give ChatGPT the source data, expected file type,
structure, and review criteria that matter for the task. The preview and review
tools depend on the surface you use.



The ChatGPT desktop app previews generated documents, presentations,
spreadsheets, and PDF files alongside the chat. Use annotations to point at a
specific part of a preview and request a focused revision.











<CodexScreenshot
  alt="ChatGPT desktop app showing a generated presentation preview"
  lightSrc="/images/codex/app/artifact-viewer-light.webp"
  darkSrc="/images/codex/app/artifact-viewer-dark.webp"
  maxHeight="420px"
  variant="no-wallpaper"
  class="my-8"
/>



## Create files for review

For spreadsheets and presentations, describe the sheets, columns, charts,
slide sections, and checks you expect. Ask ChatGPT to explain where it saved the
output and how it checked the result.

<a id="refine-files-with-annotations"></a>



<a id="review-and-refine-files"></a>



## Refine files with annotations

Annotations let you point to a specific part of a file and tell ChatGPT
what to change. The same annotation workflow available for code, Markdown
files, and websites also works with documents, spreadsheets, and
presentations.

For example, you can:

- Select a navigation bar on a website and ask ChatGPT to change its font.
- Highlight a claim in an investment thesis and ask for its source.
- Mark a chart on a slide and request a clearer label.

ChatGPT uses the selected area as context for your request, so you can refine
the file without starting over or changing the parts you already like.
Annotations are particularly useful after the first draft, when the work needs
review and iteration.







## Review and refine files

Use the chat sidebar while a task runs. It can surface the agent's plan,
sources, generated files, and chat summary so you can steer the work,
inspect generated files, and request another pass.

Ask ChatGPT to explain where it saved each file and how it verified the
result. Use the preview to inspect the output, then give focused feedback about
the structure, data, layout, or validation that needs another pass.



## Related docs

- [Image generation](https://learn.chatgpt.com/docs/image-generation)

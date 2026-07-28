---
title: Browser
source_id: codex/browser
product: codex
lang: en
canonical_url: https://developers.openai.com/codex/browser
owner: OpenAI
content_sha256: 273face911b208fb6d8e3c06e72ed8203a5dbfec7e4170393f4a52dc5ebb6386
---
[Official source](https://developers.openai.com/codex/browser)

Content owner: OpenAI

# Browser

> For the complete documentation index, see [llms.txt](https://learn.chatgpt.com/llms.txt). Markdown versions of documentation pages are available by appending `.md` to the page URL.

Browser lets ChatGPT open websites, gather current information, and take action
while you stay in control. Use it to compare options, complete a multi-step task
on a website, or review a page you're building.

Browser is available in ChatGPT on the web and in the ChatGPT desktop app.

Treat page content as untrusted context. Review the site and proposed action
before sharing sensitive information or allowing ChatGPT to act.



The built-in browser in the ChatGPT desktop app gives you and ChatGPT a shared
view of websites and local web apps inside a chat. Use it to preview a page,
leave visual feedback, or let ChatGPT interact with a site on your behalf.

The built-in browser uses a browser profile that is separate from your regular
browser. It doesn't automatically share your existing tabs or browser session.
You can sign in directly when a task requires an account. Open **Settings >
Browser** to manage browser data and any profile-import features available on
your device.

Browser downloads go to your system Downloads folder by default. In **Settings >
Browser**, you can choose another download location, reset it to the system
default, or turn on **Ask where to save downloads**.

Use the [Chrome extension](https://learn.chatgpt.com/docs/chrome-extension) instead when ChatGPT needs
to work in an existing Chrome tab or use your regular Chrome profile.

Open the built-in browser from the toolbar, by clicking a URL, by navigating
manually, or by pressing <kbd>Cmd</kbd>+<kbd>Shift</kbd>+<kbd>B</kbd>
(<kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>B</kbd> on Windows).

<CodexScreenshot
  alt="ChatGPT desktop app showing a browser comment on a local web app preview"
  lightSrc="/images/codex/app/in-app-browser-light.webp"
  darkSrc="/images/codex/app/in-app-browser-dark.webp"
  maxHeight="420px"
  variant="no-wallpaper"
/>

<a id="browser-use"></a>

## Computer Use in the browser

In the desktop app, Computer Use lets ChatGPT Work or Codex operate the
built-in browser directly. The selected experience can open pages, click, type,
inspect rendered state, take screenshots, and verify the result of its work in
the page.

Select ChatGPT and turn on Work in the switcher, or select Codex. Open the Plugins
Directory and install **Browser**. Then ask ChatGPT or Codex to use the browser
in your task, or reference it directly with `@Browser`.

For example:

```text
Use the browser to open http://localhost:3000/settings, reproduce the layout
bug, and fix only the overflowing controls.
```

ChatGPT asks before it uses a website unless you have already allowed that
site. Manage allowed and blocked sites in **Settings > Browser**. ChatGPT also
asks for confirmation before sensitive actions such as submitting information,
making a purchase, changing permissions, or deleting data. ChatGPT can't
automate file uploads in the built-in browser.

Instructions on a page can be misleading or malicious. A website permission
  lets ChatGPT interact with that site; it doesn't make the site's content
  trustworthy or approve every action.

## Preview a page

1. Start your app's development server in the [integrated terminal](https://learn.chatgpt.com/docs/integrated-terminal) or with a [local environment action](https://learn.chatgpt.com/docs/environments/local-environment#actions).
2. Open the local route, file-backed page, or public page by clicking a URL or
   navigating manually in the browser.
3. Review the rendered state alongside the code diff.
4. Leave browser comments on the elements or areas that need changes.
5. Ask ChatGPT to address the comments and keep the scope narrow.

For example:

```text
I left comments on the pricing page in the built-in browser. Address the mobile
layout issues and keep the card structure unchanged.
```

## Comment on the page

When a bug is visible only in the rendered page, use browser comments to give
ChatGPT precise feedback.

1. Turn on **Annotation mode**.
2. Click an element, or drag to select an area.
3. Write and save your comment.
4. Send a message in the chat asking ChatGPT to address the comments.

Comments work best when you name the problem and the result you want:

```text
This button overflows on mobile. Keep the label on one line if it fits,
otherwise wrap it without changing the card height.
```

```text
This tooltip covers the data point under the cursor. Reposition the tooltip so
it stays inside the chart bounds.
```

<section class="feature-grid">




### Styling feedback

When you add an annotation to a section on the page, select **Adjust** next to
the text input to give ChatGPT more granular style feedback. You can change
values such as font, text, spacing, and color, preview the result on the page,
and then send the annotation with a clearer target.




<CodexScreenshot
  alt="ChatGPT desktop app showing built-in browser annotation style controls"
  lightSrc="/images/codex/app/iab-annotations-light.webp"
  darkSrc="/images/codex/app/iab-annotations-dark.webp"
  maxHeight="420px"
/>

</section>

## Keep browser tasks scoped

Keep each browser task small enough to review in one pass.

- Name the page, route, or URL.
- Name the state you care about, such as loading, empty, error, or success.
- Leave comments on the exact elements or areas that need changes.
- Review the page again after ChatGPT finishes.
- Ask ChatGPT to start or check the development server before it opens a local
  page.

For repository changes, use the [review pane](https://learn.chatgpt.com/docs/code-review?surface=app) to
inspect the changes and leave comments.

<section class="feature-grid">




## Developer mode

Developer mode works with Computer Use in Chrome and the built-in browser. It
gives ChatGPT controlled access to the Chrome DevTools Protocol (CDP). Use it to
profile JavaScript, inspect console output and network traffic, examine the DOM
and applied styles, or diagnose an issue in the live browser.

To enable it, open [**Settings > Browser**](codex://settings/browser-use) and,
under **Developer mode**, turn on **Enable full CDP access**. If your
organization has disabled this setting, you can't enable it locally. Admins can
set `browser_use_full_cdp_access = false` under `[features]` in
[`requirements.toml`](https://learn.chatgpt.com/docs/enterprise/managed-configuration#pin-feature-flags)
to disable full CDP access and prevent users from enabling the corresponding
setting in the ChatGPT desktop app.

Full CDP access can expose sensitive browser internals. ChatGPT asks for
explicit approval before it uses full CDP to inspect a website. Review the
site, task, and requested access before approving it.

Use `@Browser` for the built-in browser. To use Developer mode in Chrome,
[set up the Chrome extension](https://learn.chatgpt.com/docs/chrome-extension) and invoke `@Chrome`.

For example:

```text
This app is slow. Use @Browser to capture a performance trace and inspect
network traffic, then identify the bottleneck.
```




<CodexScreenshot
  alt="ChatGPT desktop app Browser settings showing Developer mode with full CDP access enabled"
  lightSrc="/images/codex/app/browser-developer-mode-light.webp"
  darkSrc="/images/codex/app/browser-developer-mode-dark.webp"
  maxHeight="420px"
/>

</section>

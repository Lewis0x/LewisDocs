---
title: 浏览器
source_id: codex/browser
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/browser
owner: OpenAI
content_sha256: 273face911b208fb6d8e3c06e72ed8203a5dbfec7e4170393f4a52dc5ebb6386
translation_of: codex/browser
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/browser)

Content owner: OpenAI

# 浏览器

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。通过在页面 URL 后附加 `.md`，可以获得文档页面的 Markdown 版本。

浏览器让 ChatGPT 能够打开网站、收集当前信息并采取行动，
同时由您保持控制权。您可以使用它来比较选项、在网站上完成多步骤任务，
或审查您正在构建的页面。

浏览器在 ChatGPT 网页版和 ChatGPT 桌面应用程序中均可用。

将页面内容视为不受信任的上下文。在共享敏感信息或允许 ChatGPT 采取行动之前，请审查网站和建议的操作。



ChatGPT 桌面应用程序中的内置浏览器为您和 ChatGPT 提供了在聊天中查看网站和
本地 Web 应用程序的共享视图。使用它来预览页面、
留下视觉反馈，或让 ChatGPT 代表您与网站进行交互。

内置浏览器使用的浏览器配置文件与您的常规
浏览器是分开的。它不会自动共享您现有的标签页或浏览器会话。
当任务需要账户时，您可以直接登录。打开 **设置 >
浏览器** 来管理浏览器数据以及您的设备上
可用的任何配置文件导入功能。

浏览器下载的内容默认进入您的系统“下载”文件夹。在 **设置 >
浏览器** 中，您可以选择其他下载位置，将其重置为系统
默认位置，或开启 **下载前询问保存位置**。

当 ChatGPT 需要
在现有的 Chrome 标签页中工作或使用您的常规 Chrome 配置文件时，请改用 [Chrome 扩展程序](https://learn.chatgpt.com/docs/chrome-extension)。

您可以通过工具栏、点击 URL、手动
导航，或按 <kbd>Cmd</kbd>+<kbd>Shift</kbd>+<kbd>B</kbd>（在 Windows 上为 <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>B</kbd>）来打开内置浏览器。

<CodexScreenshot
  alt="ChatGPT 桌面应用在本地 Web 应用程序预览中显示浏览器评论"
  lightSrc="/images/codex/app/in-app-browser-light.webp"
  darkSrc="/images/codex/app/in-app-browser-dark.webp"
  maxHeight="420px"
  variant="no-wallpaper"
/>

<a id="browser-use"></a>

## 浏览器中的计算机使用

在桌面应用程序中，计算机使用功能允许 ChatGPT Work 或 Codex 直接操作
内置浏览器。所选的体验可以打开页面、点击、输入、
检查渲染状态、截取屏幕截图，并验证其在页面中
工作的结果。

在切换器中选择 ChatGPT 并开启 Work，或者选择 Codex。打开插件
目录并安装 **浏览器**。然后让 ChatGPT 或 Codex 在您的任务中
使用浏览器，或直接使用 `@Browser` 引用它。

例如：

```text
Use the browser to open http://localhost:3000/settings, reproduce the layout
bug, and fix only the overflowing controls.
```

除非您已经允许了该网站，否则 ChatGPT 在使用
网站之前会询问您。在 **设置 > 浏览器** 中管理允许和阻止的网站。ChatGPT 还会
在敏感操作（例如提交信息、
购买、更改权限或删除数据）之前要求确认。ChatGPT 无法
在内置浏览器中自动执行文件上传操作。

页面上的说明可能具有误导性或恶意。网站权限
  允许 ChatGPT 与该网站交互；这并不意味着该网站的内容
  是值得信任的，也不代表批准了其每一项操作。

## 预览页面

1. 在 [集成终端](https://learn.chatgpt.com/docs/integrated-terminal) 中或通过 [本地环境操作](https://learn.chatgpt.com/docs/environments/local-environment#actions) 启动您的应用程序的开发服务器。
2. 通过点击 URL 或在浏览器中
   手动导航，打开本地路由、基于文件的页面或公共页面。
3. 在代码差异旁边查看渲染状态。
4. 在需要更改的元素或区域留下浏览器评论。
5. 要求 ChatGPT 处理评论，并保持范围尽可能小。

例如：

```text
I left comments on the pricing page in the built-in browser. Address the mobile
layout issues and keep the card structure unchanged.
```

## 在页面上发表评论

当 Bug 仅在渲染后的页面中可见时，使用浏览器评论来提供
给 ChatGPT 精确的反馈。

1. 开启 **标注模式**。
2. 点击一个元素，或拖动以选择一个区域。
3. 写下并保存您的评论。
4. 在聊天中发送消息，要求 ChatGPT 处理这些评论。

当您说明问题和期望的结果时，评论的效果最佳：

```text
This button overflows on mobile. Keep the label on one line if it fits,
otherwise wrap it without changing the card height.
```

```text
This tooltip covers the data point under the cursor. Reposition the tooltip so
it stays inside the chart bounds.
```

<section class="feature-grid">




### 样式反馈

当您在页面上的某个部分添加注释时，选择文本输入框旁边的 **调整**
以向 ChatGPT 提供更精细的样式反馈。您可以更改
字体、文本、间距和颜色等值，在页面上预览结果，
然后以更明确的目标发送该注释。




<CodexScreenshot
  alt="显示内置浏览器注释样式控件的 ChatGPT 桌面应用程序"
  lightSrc="/images/codex/app/iab-annotations-light.webp"
  darkSrc="/images/codex/app/iab-annotations-dark.webp"
  maxHeight="420px"
/>

</section>

## 保持浏览器任务的范围明确

将每个浏览器任务保持在足够小、以便一次性审查的范围内。

- 指出页面、路由或 URL 的名称。
- 指出您关心的状态，例如加载中、空、错误或成功。
- 在需要更改的确切元素或区域留下评论。
- ChatGPT 完成后再次审查页面。
- 要求 ChatGPT 启动或检查开发服务器，然后再打开本地
  页面。

对于代码库更改，使用 [审查面板](https://learn.chatgpt.com/docs/code-review?surface=app) 来
检查更改并留下评论。

<section class="feature-grid">




## 开发者模式

开发者模式适用于 Chrome 中的计算机使用功能和内置浏览器。它
赋予 ChatGPT 受控访问 Chrome 开发者工具协议（CDP）的权限。使用它来
分析 JavaScript、检查控制台输出和网络流量、检查 DOM
和应用样式，或在实时浏览器中诊断问题。

要启用它，请打开 [**设置 > 浏览器**](codex://settings/browser-use)，并
在**开发者模式**下，开启**启用完整 CDP 访问权限**。如果你的
组织已禁用此设置，您将无法在本地启用它。管理员可以
在 [`requirements.toml`](https://learn.chatgpt.com/docs/enterprise/managed-configuration#pin-feature-flags) 中的 `[features]` 之下设置 `browser_use_full_cdp_access = false`
以禁用完整的 CDP 访问权限，并防止用户启用相应的
ChatGPT 桌面应用程序中的设置。

完整的 CDP 访问权限可能会暴露敏感的浏览器内部信息。ChatGPT 会要求
在使用完整 CDP 检查网站之前获得明确的批准。在批准之前，请审查
网站、任务和请求的访问权限。

在内置浏览器中使用 `@Browser`。要在 Chrome 中使用开发者模式，
[设置 Chrome 扩展程序](https://learn.chatgpt.com/docs/chrome-extension) 并调用 `@Chrome`。

例如：

```text
This app is slow. Use @Browser to capture a performance trace and inspect
network traffic, then identify the bottleneck.
```




<CodexScreenshot
  alt="显示启用了完整 CDP 访问权限的开发者模式的 ChatGPT 桌面应用程序浏览器设置"
  lightSrc="/images/codex/app/browser-developer-mode-light.webp"
  darkSrc="/images/codex/app/browser-developer-mode-dark.webp"
  maxHeight="420px"
/>

</section>

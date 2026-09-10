---
title: 构建插件
source_id: codex/build-plugins
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/build-plugins
owner: OpenAI
content_sha256: e71a8ecdc251be1cdf1b815149b88707777dc59ec6eb7e2081037f36d7ff3e46
translation_of: codex/build-plugins
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/build-plugins)

Content owner: OpenAI

# 构建插件

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。可以通过在页面 URL 后附加 `.md` 来获取文档页面的 Markdown 版本。

要构建或提交插件，请使用完整的
[developers.openai.com 上的构建器文档](https://developers.openai.com/plugins)。



  <ButtonLink href="/plugins" color="primary" variant="solid" size="lg">
    构建并提交插件
  </ButtonLink>



本页面提供了简要介绍。插件是一个可安装的包，
可以包含技能、MCP 服务器或两者兼有。MCP 服务器还可以返回
可选的 UI。

ChatGPT 和 Codex 共享一个通用插件目录。只需发布一次公共插件，
即可让同一条目在两个产品的受支持界面中被发现。
在开发期间，使用本地市场测试该包，
然后再提交到通用目录。

当您仍在迭代单个个人工作流时，请从技能开始。
当您想要共享该工作流、打包相关技能、
连接到外部服务，或向团队分发稳定的功能时，请构建插件。

## 使用 `@plugin-creator` 创建插件

为了实现最快的设置，请在 ChatGPT 工作模式中使用内置的 `@plugin-creator` 技能，
或在 Codex 中使用 `$plugin-creator`。

<CodexScreenshot
  alt="ChatGPT 中的插件创建者技能"
  lightSrc="/images/codex/plugins/plugin-creator.png"
  darkSrc="/images/codex/plugins/plugin-creator-dark.png"
/>

描述预期结果、要包含的技能或 MCP 服务器，以及您是否想要
一个用于测试的本地市场条目。例如：

```text
@plugin-creator Create a plugin named meeting-follow-up.
Include a skill that turns meeting notes into decisions, owners, and next steps.
Add it to a personal marketplace so I can test it locally.
```

该技能会创建所需的 `.codex-plugin/plugin.json` 清单，组织
插件文件夹，并可将插件添加到本地市场。

<CodexScreenshot
  alt="调用插件创建者技能"
  lightSrc="/images/codex/plugins/plugin-creator-invoke.png"
  darkSrc="/images/codex/plugins/plugin-creator-invoke-dark.png"
/>

完成后：

1. 查看 `.codex-plugin/plugin.json`。
2. 在 `skills/` 下检查每个捆绑的技能。
3. 刷新 ChatGPT 或 Codex，并从其本地市场
   源安装该插件。
4. 在新对话中使用代表性请求来测试插件。

如果插件包含 MCP 服务器，请先构建并测试该服务器，然后
向 `@plugin-creator` 提供已注册的连接详细信息。请遵循完整的
[MCP 服务器工作流](https://developers.openai.com/plugins/build/mcp-server)
以了解工具、身份验证、部署和测试。

## 手动创建仅包含技能的插件

一个最小的插件包含一个清单和至少一个技能：

```text
meeting-follow-up/
├── .codex-plugin/
│   └── plugin.json
└── skills/
    └── meeting-follow-up/
        └── SKILL.md
```

创建 `.codex-plugin/plugin.json`：

```json
{
  "name": "meeting-follow-up",
  "version": "1.0.0",
  "description": "Turn meeting notes into decisions and next steps",
  "skills": "./skills/"
}
```

然后添加 `skills/meeting-follow-up/SKILL.md`：

```md
---
name: meeting-follow-up
description: Extract decisions, owners, and next steps from meeting notes.
---

Review the meeting notes. Return:

1. Decisions
2. Action items with owners
3. Open questions
```

使用 kebab case（短横线命名法）格式的稳定插件名称。保持技能描述足够具体，
以便 ChatGPT 和 Codex 能够识别何时应用该工作流。

使用 `@plugin-creator` 将文件夹添加到本地市场，然后安装并在
共享前进行测试。

## 继续查看构建器文档

获取完整的构建器文档，请使用
[插件文档](https://developers.openai.com/plugins/)。它涵盖了：

- [插件架构](https://developers.openai.com/plugins/concepts/plugins)
- [构建技能](https://developers.openai.com/plugins/build/skills)
- [构建 MCP 服务器](https://developers.openai.com/plugins/build/mcp-server)
- [添加可选 UI](https://developers.openai.com/plugins/build/chatgpt-ui)
- [打包插件](https://developers.openai.com/plugins/build/plugins)
- [测试插件](https://developers.openai.com/plugins/deploy/connect-chatgpt)
- [提交和发布](https://developers.openai.com/plugins/deploy/submission)

要浏览、安装、启用或移除插件，请参阅[使用
插件](https://learn.chatgpt.com/docs/plugins)。

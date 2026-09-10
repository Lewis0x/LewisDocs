---
title: 录制与回放
source_id: codex/extend/record-and-replay
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/extend/record-and-replay
owner: OpenAI
content_sha256: 7d9a11d234f29b4363d075fd7093509041c29db0e0a80d3249437e19ddcb47fc
translation_of: codex/extend/record-and-replay
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/extend/record-and-replay)

Content owner: OpenAI

# 录制与回放

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。可以通过在页面 URL 后附加 `.md` 来获取文档页面的 Markdown 版本。

录制与回放在 macOS 上可用。初始可用地区不包括
  欧洲经济区、英国和瑞士。计算机使用功能也
  必须可用并已启用。

录制与回放允许你在你的
Mac 上演示工作流，并将其转变为可重复使用的技能。当工作流具有重复性、
依赖于你的偏好，或者比在提示词中描述更容易展示时，请使用它。

例如，你可以记录如何提交费用报告、预订停车位、
创建配置正确的问题、发布视频或下载定期
报告。ChatGPT 或 Codex 可以将此模式打包成一项技能，你可以
再次使用“计算机使用”、浏览器操作、已连接的插件或它们的
组合来使用它。

## 开始之前

挑选一个你已经知道如何完成的工作流。当步骤稳定且
成功标准明确时，录制与回放的效果最佳。

## 开始录制

<WorkflowSteps>

1. 在 ChatGPT 桌面应用中，选择 ChatGPT 并在切换器中开启 Work，或者选择 Codex。然后打开**插件**。
2. 打开 **+** 菜单。
3. 选择 **录制技能**。
4. 查看建议的提示词，添加任何有用的上下文，然后提交它。
5. 当聊天请求权限以录制你的操作时，一旦你准备好
   演示该工作流，请批准请求。
6. 在你的 Mac 上执行该工作流。
7. 完成后，从菜单栏或覆盖层停止录制，或者告诉
   聊天你已完成。

</WorkflowSteps>

在录制期间，ChatGPT 或 Codex 会观察所需的操作和窗口内容
来学习该工作流。录制将持续到你停止它为止。请保持录制
专注于你希望该技能教授的任务。

在你停止录制后，ChatGPT 或 Codex 会检查捕获的工作流并
起草一项技能。该技能会解释何时使用该工作流，需要哪些输入，
遵循什么步骤，以及如何验证结果。你也可以要求
进一步改进。

## 回放工作流

启动一个新的 ChatGPT 或 Codex 聊天，并要求它使用生成的技能。提供
这次不同的值，例如要上传的文件、
要创建的问题或报告的日期范围。

产品将该技能用作任务的可重用上下文。然后它可以
使用当前环境中可用的工具完成该工作流，
包括“计算机使用”、浏览器操作和已安装的插件。

## 获得更好录制效果的建议

- 保持演示简短且完整。
- 在开始录制之前，说明你的目标以及任何在技能使用时可能
  发生变化的特定输入。
- 使用逼真的输入，但避免使用机密和敏感数据。
- 录制后完善技能，以指出重要的隐藏偏好，
  例如命名约定、字段默认值或决策点。
- 当工作流完成时停止录制，而不是继续录制
  无关的清理工作。

## 何时构建另一个插件

录制与回放是一种从演示的工作流中快速创建技能的方法。
如果你想在整个团队中分发一个单独的稳定包，捆绑
多项技能，包含连接器，添加 MCP 服务器，或管理安装
元数据，请将该工作流打包成它自己的插件。请参见
[构建插件](https://developers.openai.com/plugins/build/plugins)。

## 故障排除

### 我看不到“录制与回放”

如果你的组织使用 `requirements.toml` 管理 Codex，
`[features].computer_use` 要求也会控制“录制与回放”。设置
`computer_use = false` 会使这两项功能均不可用。

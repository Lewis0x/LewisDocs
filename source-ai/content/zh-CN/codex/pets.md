---
title: 宠物
source_id: codex/pets
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/pets
owner: OpenAI
content_sha256: 4c2df8bda41c065c931c0f2285887627ed8b26f3d20d5bc6e581e980cfdb4761
translation_of: codex/pets
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/pets)

Content owner: OpenAI

# 宠物

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。可以通过在页面 URL 后附加 `.md` 来获取文档页面的 Markdown 版本。

宠物是用于跟进工作的可选动画伴侣。宠物出现的位置
以及它显示的内容取决于您使用的界面。选择宠物会改变其
外观，而不会改变 ChatGPT 完成任务的方式。



  

    <CodexPetsDemo client:load mobileAlignment="left" />
  




## 使用悬浮宠物

在 ChatGPT 桌面应用中，宠物可以悬浮在其他应用窗口上方，并帮助
您跟进各个聊天中的活动。

### 选择并唤醒宠物

1. 打开应用底部的个人资料菜单并选择**宠物**。您也
   可以打开 [**设置**](codex://settings) 并前往**宠物**。
2. 选择内置或自定义宠物。
3. 输入 `/pet`，或打开命令菜单并选择**唤醒宠物**。

在**设置 > 宠物**或命令菜单中选择**隐藏宠物**，或输入
`/pet`，以隐藏宠物。当您重新打开应用时，您的选择和宠物的位置会保持
不变。

当您选择自定义宠物时，它也会显示在您的**个人资料**视图中。

### 了解宠物状态

| 状态          | 含义                                                  |
| --------------- | -------------------------------------------------------- |
| **运行中**     | 聊天正在积极工作中。                              |
| **需要输入** | 聊天需要您的批准、回答或其他决定。 |
| **已就绪**       | 聊天已完成并有未读活动。            |
| **已阻塞**     | 聊天失败或遇到系统错误。             |

当多个聊天有活动时，宠物会优先处理需要
输入的聊天，其次是已阻塞、已就绪和运行中的聊天。打开活动托盘来
选择一个聊天。

选择宠物以返回 ChatGPT，或选择一个活动以打开其聊天。
活动托盘独立于[系统
通知](https://learn.chatgpt.com/docs/notifications?surface=app)。

### 跟随计算机使用

在 macOS 上，[计算机使用](https://learn.chatgpt.com/docs/computer-use) 画中画窗口可以
附加到已唤醒的宠物上。移动宠物，窗口也会随之移动。

### 创建自定义宠物

1. 打开**设置 > 宠物**并选择**创建您自己的宠物**。
2. 应用会安装捆绑的 `hatch-pet` 技能，重新加载技能，并打开
   一个新聊天。
3. 描述您想要的宠物并发送提示词。
4. 当任务完成后，返回**设置 > 宠物**，选择**刷新**，
   并选择您的新宠物。

在桌面应用中创建的自定义宠物本地存储在您的计算机上。
它们不会自动同步到 ChatGPT 网页版。

### 减少动画

宠物会遵循您操作系统的减少动态效果设置。当减少
动态效果启用时，宠物会使用静止帧而不是精灵动画。










## 相关文档

- [通知](https://learn.chatgpt.com/docs/notifications)
- [长时间运行的工作](https://learn.chatgpt.com/docs/long-running-work)
- [ChatGPT 桌面应用设置](https://learn.chatgpt.com/docs/reference/settings#pets)

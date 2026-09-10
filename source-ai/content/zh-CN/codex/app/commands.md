---
title: 命令
source_id: codex/app/commands
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/app/commands
owner: OpenAI
content_sha256: 12808b430c321343a77293cd7706eef031318e56e59e45fef72c00c9c7dcd53f
translation_of: codex/app/commands
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/app/commands)

Content owner: OpenAI

# 命令

> 完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。可以通过在页面 URL 后附加 `.md` 来获取文档页面的 Markdown 版本。

使用这些命令和键盘快捷键来导航应用程序。

## 键盘快捷键

|             | 操作              | 快捷键                                                                                                               |
| ----------- | ------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| **通用** |                     |                                                                                                                        |
|             | 命令菜单        | <kbd>Cmd</kbd>/<kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>P</kbd> 或 <kbd>Cmd</kbd>/<kbd>Ctrl</kbd> + <kbd>K</kbd>      |
|             | 设置            | <kbd>Cmd</kbd>/<kbd>Ctrl</kbd> + <kbd>,</kbd>                                                                          |
|             | 键盘快捷键  | <kbd>Cmd</kbd>/<kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>/</kbd>                                                       |
|             | 打开文件夹         | <kbd>Cmd</kbd>/<kbd>Ctrl</kbd> + <kbd>O</kbd>                                                                          |
|             | 后退       | <kbd>Cmd</kbd>/<kbd>Ctrl</kbd> + <kbd>[</kbd>                                                                          |
|             | 前进    | <kbd>Cmd</kbd>/<kbd>Ctrl</kbd> + <kbd>]</kbd>                                                                          |
|             | 增大字体  | <kbd>Cmd</kbd>/<kbd>Ctrl</kbd> + <kbd>+</kbd>                                                                          |
|             | 减小字体  | <kbd>Cmd</kbd>/<kbd>Ctrl</kbd> + <kbd>-</kbd>                                                                          |
|             | 切换侧边栏      | <kbd>Cmd</kbd>/<kbd>Ctrl</kbd> + <kbd>B</kbd>                                                                          |
|             | 打开审阅标签页     | <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>G</kbd>                                                                      |
|             | 切换审阅面板 | <kbd>Cmd</kbd>/<kbd>Ctrl</kbd> + <kbd>Alt</kbd> + <kbd>B</kbd>                                                         |
|             | 切换底部面板 | <kbd>Cmd</kbd>/<kbd>Ctrl</kbd> + <kbd>J</kbd>                                                                          |
|             | 切换终端     | <kbd>Ctrl</kbd> + <kbd>`</kbd>                                                                                         |
|             | 清除终端  | <kbd>Ctrl</kbd> + <kbd>L</kbd>                                                                                         |
| **聊天**    | 快速聊天          | <kbd>Cmd</kbd> + <kbd>Option</kbd> + <kbd>N</kbd> (macOS) 或 <kbd>Ctrl</kbd> + <kbd>Alt</kbd> + <kbd>N</kbd> (Windows) |
|             | 新建聊天            | <kbd>Cmd</kbd>/<kbd>Ctrl</kbd> + <kbd>N</kbd> 或 <kbd>Cmd</kbd>/<kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>O</kbd>      |
|             | 搜索聊天        | <kbd>Cmd</kbd>/<kbd>Ctrl</kbd> + <kbd>G</kbd>                                                                          |
|             | 在聊天中查找        | <kbd>Cmd</kbd>/<kbd>Ctrl</kbd> + <kbd>F</kbd>                                                                          |
|             | 上一个聊天       | <kbd>Cmd</kbd>/<kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>[</kbd>                                                       |
|             | 下一个聊天           | <kbd>Cmd</kbd>/<kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>]</kbd>                                                       |
| **输入**   | 听写           | <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>D</kbd>                                                                      |

要查找、自定义或重置快捷键，请打开 **设置 > 键盘快捷键**。
你可以按命令名称搜索，或者将搜索字段切换为按键模式
并按下你想查找的快捷键。

<a id="search-past-tasks-and-find-in-a-task"></a>

## 搜索过去的聊天并在聊天中查找

使用聊天搜索 (<kbd>Cmd</kbd>/<kbd>Ctrl</kbd> + <kbd>G</kbd>) 重新打开过去的
聊天。当扩展匹配可用时，它还可以匹配聊天内容和
Git 分支名称，因此你可以搜索聊天中的短语或
诸如 `fix/login-redirect` 之类的分支。

在打开某个聊天后，使用 **在聊天中查找** (<kbd>Cmd</kbd>/<kbd>Ctrl</kbd> + <kbd>F</kbd>) 以在其中查找文本。它不会跨其他聊天进行搜索。

有关以 `/` 开头的操作，请参见 [斜杠命令](https://learn.chatgpt.com/docs/reference/slash-commands)。

## 深层链接

ChatGPT 桌面应用保留了 `codex://` URL 方案以实现兼容性，因此
链接可以直接打开应用程序的特定部分。在将查询字符串值添加到
URL 之前，请对其进行编码。

### 支持的链接

创建链接时请使用这些规范格式。以下各节按链接类型列出了完整的参考信息。

| 深层链接                                                                   | 打开                                                   |
| --------------------------------------------------------------------------- | ------------------------------------------------------- |
| `codex://threads/new`                                                       | 一个新的本地聊天。                                       |
| `codex://new?<query>`                                                       | 带有至少一个查询参数的新本地聊天。     |
| `codex://threads/<thread-id>`                                               | 一个本地聊天。`<thread-id>` 是其技术线程 ID。 |
| `codex://settings`                                                          | 设置。                                               |
| `codex://settings/connections/<connection-type>`                            | 计算机、设备或 SSH 连接设置。           |
| `codex://settings/connections/ssh/add?name=<ssh-config-host>`               | 将你的 SSH 配置中的主机添加到 Codex。              |
| `codex://skills`                                                            | 技能。                                                 |
| `codex://automations`                                                       | 计划任务，并打开创建流程。                    |
| `codex://plugins/install/<plugin-name>?marketplace=<marketplace-name>`      | 来自已知市场的插件的安装流程。 |
| `codex://plugins/<plugin-id>`                                               | 插件详情页。                                   |
| `codex://plugins/<plugin-name>?marketplacePath=<absolute-marketplace-path>` | 来自本地市场的本地插件详情页。    |
| `codex://pets/install?name=<pet-name>&imageUrl=<https-image-url>`           | 宠物安装流程。                                   |

<a id="tasks"></a>

### 聊天

当你需要打开现有的本地聊天或开始一个新的聊天时，请使用这些链接。

| 深度链接                     | 打开                                                                                                        |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------ |
| `codex://threads/<thread-id>` | 一个本地聊天。`<thread-id>` 是其技术线程 ID。                                                      |
| `codex://threads/new`         | 一个新的本地聊天。                                                                                            |
| `codex://threads/new?<query>` | 一个带有可选查询参数的新的本地聊天。                                                             |
| `codex://new?<query>`         | 一个新的本地聊天。至少包含 `prompt`、`path` 或 `originUrl` 中的一个；否则链接不起作用。 |

对于 `codex://threads/new` 或 `codex://new`，根据需要添加这些查询参数中的任意一个；你可以将它们组合在同一个 URL 中。

| 查询参数              | 必需 | 作用                                                                                                                                                  |
| ---------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `prompt=<text>`              | 否       | 设置初始撰写文本。                                                                                                                               |
| `path=<absolute-path>`       | 否       | 在本地工作区中打开新聊天。`path` 必须是本地目录的绝对路径。有效时，Codex 会将该目录用作活动工作区。 |
| `originUrl=<git-remote-url>` | 否       | 根据 Git 远程 URL 匹配你当前的工作区根目录之一。如果同时存在 `path`，Codex 会优先解析 `path`。                                        |

示例：[给我看看关于我如何使用 Codex 的一些趣味统计数据](codex://threads/new?prompt=Show%20me%20some%20fun%20stats%20about%20how%20I%27ve%20been%20using%20Codex)

<a id="start-a-task-with-a-plugin"></a>

#### 使用插件开始聊天

为了帮助用户开始由插件支持的聊天，请在编码前的
提示词中包含插件提及：

```text
[@Example](plugin://example@openai-curated) Summarize this document: https://example.com/document/123
```

将完整的提示词编码为 URI 组件——例如，使用
`encodeURIComponent` 在 JavaScript 中——并将其传递给 `prompt` 参数：

```text
codex://new?prompt=%5B%40Example%5D(plugin%3A%2F%2Fexample%40openai-curated)%20Summarize%20this%20document%3A%20https%3A%2F%2Fexample.com%2Fdocument%2F123
```

该链接会打开一个新聊天，并将解码后的提示词显示在撰写框中。它不会
自动发送提示词。当用户发送提示词后，Codex 可以在
该聊天中使用已安装的插件。如果插件未安装但用户可以
使用，Codex 会要求用户安装它并连接任何必需的连接器。
设置完成后，用户可以选择 **继续** 以恢复同一个聊天。工作区
设置可以限制用户能够安装的插件。有关插件安装
和权限详情，请参见 [插件](https://learn.chatgpt.com/docs/plugins)。

### 设置

当你需要打开设置或特定设置页面时，请使用这些链接。

| 深度链接                                                     | 打开                                                                                        |
| ------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| `codex://settings`                                            | 设置。                                                                                    |
| `codex://settings/browser-use`                                | 浏览器设置。                                                                            |
| `codex://settings/computer-use/google-chrome`                 | 用于计算机的 Google Chrome 设置。                                                     |
| `codex://settings/connections`                                | 远程连接设置。                                                                 |
| `codex://settings/connections/computer`                       | 从其他设备控制此 Mac 或 PC 的设置。                                 |
| `codex://settings/connections/devices`                        | 控制其他设备的设置。                                                      |
| `codex://settings/connections/ssh`                            | SSH 连接设置。                                                                     |
| `codex://settings/connections/ssh/add?name=<ssh-config-host>` | 将指定的主机别名添加为 Codex 管理的连接，然后打开 SSH 连接设置。 |

`name` 值必须与 `~/.ssh/config` 中的主机别名匹配。该链接会禁用
所添加主机的自动连接。如果 Codex 找不到指定的主机，它将
打开 SSH 连接设置并显示错误。

不支持的 `codex://settings/...` 路径将打开主设置页面。

### 技能

当你需要打开技能时，请使用这些链接。

| 深度链接        | 打开   |
| ---------------- | ------- |
| `codex://skills` | 技能。 |

### 计划任务

当你需要打开**计划任务**时，请使用这些链接。

| 深度链接             | 打开                                |
| --------------------- | ------------------------------------ |
| `codex://automations` | 带有已开启创建流程的计划任务。 |

### 插件

插件链接使用不同的形式，具体取决于你是从市场安装、打开插件，还是从本地 `marketplace.json` 进行操作。有关插件基础知识，请参阅 [插件](https://learn.chatgpt.com/docs/plugins)。有关本地或代码库市场设置，请参阅 [构建插件](https://developers.openai.com/plugins/build/plugins#build-your-own-curated-plugin-list)。

#### 插件安装

使用此表单可从 Codex 已知的市场打开插件的安装流程。

| 深度链接                                                              | 打开                                           |
| ---------------------------------------------------------------------- | ----------------------------------------------- |
| `codex://plugins/install/<plugin-name>?marketplace=<marketplace-name>` | 插件的插件详情或安装流程。 |

| 查询参数                  | 必需 | 作用                                                                    |
| -------------------------------- | -------- | ------------------------------------------------------------------------------- |
| `marketplace=<marketplace-name>` | 是      | 标识市场。对于 OpenAI 精选的插件，请使用 `openai-curated`。 |

安装链接仅接受 `marketplace` 查询参数。如果 Codex 找不到请求的市场或插件，它将改为打开插件页面。

#### 插件详情

| 深层链接                     | 打开                 |
| ----------------------------- | --------------------- |
| `codex://plugins/<plugin-id>` | 插件详情页面。 |

`<plugin-id>` 必须标识该插件。对于 OpenAI 精选的插件，请使用 `<plugin-name>@openai-curated` 格式。

Codex 生成的插件链接也可以包含这些查询参数。手动编写链接时请省略这两者。

| 查询参数    | 必填 | 作用                                                                                                                                    |
| ------------------ | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `hostId=<host-id>` | 否       | 标识拥有插件上下文的 Codex 主机，例如 `local` 或您配置的其中一个远程连接。Codex 提供这些 ID。 |
| `source=manage`    | 否       | 保留应用程序的插件管理入口点。它并非仅限管理员使用。                                                                         |

示例：[打开 OpenAI Developers 插件](codex://plugins/openai-developers@openai-curated)

#### 本地插件

有关本地或仓库市场设置，请参见 [构建插件](https://developers.openai.com/plugins/build/plugins#build-your-own-curated-plugin-list)。

| 深层链接                                                                   | 打开                                                |
| --------------------------------------------------------------------------- | ---------------------------------------------------- |
| `codex://plugins/<plugin-name>?marketplacePath=<absolute-marketplace-path>` | 来自本地市场的本地插件详情页面。 |

| 查询参数                               | 必填 | 作用                                                                                               |
| --------------------------------------------- | -------- | ---------------------------------------------------------------------------------------------------------- |
| `marketplacePath=<absolute-marketplace-path>` | 是      | 本地 `marketplace.json` 的绝对路径，例如 `/Users/alex/.agents/plugins/marketplace.json`。 |
| `mode=share`                                  | 否       | 打开该本地插件的分享流程。                                                                |

### 宠物

当启用该功能时，可使用这些链接打开宠物安装流程。

| 深层链接                                                         | 打开                 |
| ----------------------------------------------------------------- | --------------------- |
| `codex://pets/install?name=<pet-name>&imageUrl=<https-image-url>` | 宠物安装流程。 |

| 查询参数                | 必填 | 作用                                                                                |
| ------------------------------ | -------- | ------------------------------------------------------------------------------------------- |
| `name=<pet-name>`              | 是      | 设置宠物名称。该值必须至少包含一个非空白字符。            |
| `imageUrl=<https-image-url>`   | 是      | 为宠物图像或精灵图提供一个绝对的 HTTPS URL。                           |
| `description=<text>`           | 否       | 为安装流程添加描述。                                                     |
| `spriteVersionNumber=<1-or-2>` | 否       | 选择精灵图格式。默认为 `1`；唯一另一个支持的值为 `2`。 |

安装链接仅接受这些查询参数。无效的名称、非 HTTPS
图像 URL、不支持的精灵图版本或额外的路径片段都会导致链接
不起作用。

## 另请参阅

- [功能](https://learn.chatgpt.com/docs/features)
- [设置](https://learn.chatgpt.com/docs/reference/settings)
- [斜杠命令](https://learn.chatgpt.com/docs/reference/slash-commands)

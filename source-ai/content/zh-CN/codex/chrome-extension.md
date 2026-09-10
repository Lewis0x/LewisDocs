---
title: Chrome 扩展程序
source_id: codex/chrome-extension
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/chrome-extension
owner: OpenAI
content_sha256: bbdcfcf9ce52809c09de19f196fad64d78c1b10751d7f773ea91090b381fcc04
translation_of: codex/chrome-extension
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/chrome-extension)

Content owner: OpenAI

# Chrome 扩展程序

> 完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。可以通过在页面 URL 后附加 `.md` 来获取文档页面的 Markdown 版本。

使用 Chrome 扩展程序让 ChatGPT 控制你的 Chrome 浏览器。ChatGPT 可以
读取或操作你已经登录的网站，例如 LinkedIn、
Salesforce、Gmail 或内部工具。

如果要让 ChatGPT 控制其内置浏览器，请使用 `@Browser`。
[内置浏览器](https://help.openai.com/en/articles/20001277-using-the-built-in-browser-in-the-chatgpt-desktop-app)
支持登录并将浏览工作保留在 ChatGPT 内部，而无需使用你的
Chrome 配置文件。

ChatGPT 还可以根据任务需要在不同工具之间切换，在有专用集成时使用插件，
在需要已登录浏览器
上下文时使用 Chrome，在访问本地主机时使用内置浏览器。



  <Alert
    client:load
    color="warning"
    variant="soft"
    description="将页面内容视为不受信任的上下文，并在允许 ChatGPT 继续之前审查网站。"
  />



## 在 Chrome 中使用 ChatGPT

在正在查看的页面旁打开 ChatGPT，询问有关该页面的问题，或者继续
执行可以使用其上下文以及本地文件和已连接应用的任务。
当任务需要时，ChatGPT 可以使用你打开的标签页中的上下文。

1. 打开你要处理的页面。
2. 从 Chrome 工具栏或**扩展程序**菜单中选择 ChatGPT。在 macOS 上，你
   还可以按 <kbd>Cmd</kbd>+<kbd>Shift</kbd>+<kbd>.</kbd>。
3. 询问有关页面的问题或给 ChatGPT 分配任务。

该面板会与你打开它的标签页保持在一起。你在 Chrome 中发起的聊天
可以在 ChatGPT 应用程序中使用，并且你可以在
Chrome 中打开最近的 ChatGPT 聊天，因此你可以在任何一处继续工作。

<Illustration description="ChatGPT 在当前 Chrome 标签页旁打开。">
  <ChromeSidePanelIllustration
    ariaLabel="ChatGPT 在当前 Chrome 标签页旁打开。"
    backgroundImage="/images/codex/codex-wallpaper-1.webp"
  />
</Illustration>

## 设置 Chrome 扩展程序

在 ChatGPT 桌面应用程序中，打开插件目录并安装 **Chrome**。
目前不支持其他基于 Chromium 的浏览器。请按照设置流程
操作以：

1. 安装 [Chrome
   扩展程序](https://chromewebstore.google.com/detail/chatgpt/hehggadaopoacecdllhhajmbjkdcmajg)。
2. 批准 Chrome 的权限提示。
3. 打开 Chrome 并确认已加载 ChatGPT 侧边聊天。

<Illustration description="Computer Use 设置显示通过 Chrome 扩展程序连接的 Google Chrome。">
  <ComputerUseSettingsIllustration
    ariaLabel="Computer Use 设置显示通过 Chrome 扩展程序连接的 Google Chrome。"
    aspectRatio="3 / 1"
    controlRows={[
      {
        id: "chrome",
        title: "Google Chrome",
        description: "已连接到浏览器扩展程序以进行额外控制",
        icon: "chrome",
        enabled: true,
        connected: true,
        manageLabel: "管理",
      },
    ]}
    showAlwaysAllowedApps={false}
  />
</Illustration>

## 从 ChatGPT 启动 Chrome 任务

插件设置完成后，启动一个新的 ChatGPT Work 或 Codex 聊天。ChatGPT
在任务需要网站并且你已经
登录到 Chrome 时，可以自动使用 Chrome。你也可以直接在提示词中调用它：

```text
@Chrome open Salesforce and update the account from these call notes.
```

如果 Chrome 尚未打开，ChatGPT 可以打开它。Chrome 浏览器任务在
Chrome 标签页组中运行，以便将任务的工作保持在一起。

## 控制网站访问权限

默认情况下，ChatGPT 在与每个新网站交互之前都会询问。ChatGPT 基于
网站主机给出提示，例如 `example.com`。

当 ChatGPT 要求使用某个网站时，你可以选择符合
任务和你的风险承受能力的选项：

- **允许一次**以让 ChatGPT 使用该网站一次。
- **允许此站点**以便 ChatGPT 无需询问即可再次使用该网站。
- **允许所有站点**以便 ChatGPT 无需询问即可使用网站。
- **拒绝**以阻止 ChatGPT 使用该网站。

### 管理允许和阻止的网站

在 ChatGPT 桌面应用中，前往 **设置** > **计算机使用**，然后选择
**Google Chrome** 旁边的 **管理**，以管理域名的
允许列表和阻止列表。允许列表包含 ChatGPT 无需再次询问即可使用的域名。
阻止列表包含 ChatGPT 不应使用的域名。

从允许列表中删除域名意味着 ChatGPT 在使用前会再次询问。
从阻止列表中删除域名意味着 ChatGPT 可以再次询问，而不是
将该域名视为已阻止。

#### 允许所有网站 <ElevatedRiskBadge class="ml-2" />

如果您选择 **允许所有网站**，ChatGPT 将不再要求确认
即可使用网站。只有在您信任 ChatGPT 可以使用 Chrome 中打开的任何
网站时，才选择此选项。

#### 浏览器历史记录 <ElevatedRiskBadge class="ml-2" />

浏览器历史记录可能包含敏感遥测数据、内部 URL、搜索词、
以及已登录设备上 Chrome 会话中的活动。如果您允许 ChatGPT
访问浏览器历史记录，相关的历史记录条目可能会成为
ChatGPT 用于任务的上下文的一部分。恶意或误导性的页面内容可能会增加
ChatGPT 将此数据复制到非预期位置的风险。

ChatGPT 在需要使用浏览器历史记录时会进行询问。ChatGPT 会将历史记录访问范围限定于
该请求，并且历史记录没有“始终允许”的选项。

## 数据与安全

### Chrome 扩展程序权限

当您安装扩展程序时，Chrome 会要求您接受扩展程序权限。
权限提示可能包括：

- 访问页面调试器
- 读取和更改您在所有网站上的所有数据
- 读取和更改您所有已登录设备上的浏览历史记录
- 显示通知
- 读取和更改您的书签
- 管理您的下载内容
- 与合作的本地应用程序通信
- 查看和管理您的标签页组

这些 Chrome 权限使扩展程序能够操作浏览器
工作流。在任务期间使用网站或浏览器历史记录之前，ChatGPT 仍会使用其自身的确认、设置、允许列表和
阻止列表。

### 记忆

计算机使用功能遵循您的“记忆”设置。如果开启“记忆”，ChatGPT 可以
在 Chrome 中工作时使用相关的已保存记忆。如果关闭“记忆”，浏览器
控制功能将不会使用记忆。

### OpenAI 从浏览中存储的内容

OpenAI 不会单独存储来自
扩展程序的 Chrome 操作完整记录。OpenAI 仅在浏览器活动成为 ChatGPT
上下文的一部分时才会存储浏览器活动，例如 ChatGPT 从页面读取的文本、屏幕截图、工具调用、
摘要、消息或聊天中包含的其他内容。

您的 ChatGPT 数据控制措施适用于在上下文中处理的内容。
避免通过浏览器任务发送机密或高度敏感的数据，除非
确有必要且您在场审查每个提示词。

## 故障排除

如果 ChatGPT 无法连接到 Chrome，请首先确认 ChatGPT 尝试
访问的网站不在“设置”的屏蔽列表中。如果该网站未被屏蔽，请
依次完成以下检查：

1. 更新 ChatGPT 桌面应用程序。如果您安装了多个 ChatGPT 或 Codex
   桌面应用程序，请逐一更新，或者卸载不再使用的副本。
2. 关闭 ChatGPT 侧边栏，重启 Chrome，然后从
   Chrome 工具栏或**扩展程序**菜单重新打开该扩展。确认侧边栏聊天是否加载。如果
   无法加载或提示缺少原生主机，请移除并重新添加
   ChatGPT 桌面应用程序**插件**中的 Chrome 插件，然后再次
   按照设置流程操作。
3. 在应用程序中，选择 ChatGPT 并在切换器中开启 Work，或者选择 Codex。打开
   **插件**并确认 Chrome 插件已开启。如果插件已关闭，
   请将其开启并重试任务。
4. 确保您使用的是安装了该扩展的
   同一个 Chrome 配置文件。如果您使用多个 Chrome 配置文件，请在当前活动的配置文件中安装并启用
   该扩展。
5. 开启新的 ChatGPT Work 或 Codex 聊天，然后再次尝试 Chrome 任务。这可以
   清除特定于聊天的连接状态。
6. 重启 ChatGPT 桌面应用程序，然后再试一次。如果扩展仍然
   无法连接，请卸载 Chrome 扩展，移除并重新添加
   **插件**中的 Chrome 插件，并再次按照设置流程操作。
7. 如果侧边栏聊天能加载，但 ChatGPT 仍然无法使用 Chrome，请在应用程序中运行 `/feedback`
   并在联系支持团队时提供聊天 ID。

### 上传文件

如果 Chrome 任务需要从您的计算机上传文件，请允许 Chrome
扩展在 Chrome 中访问文件 URL：

1. 在 Chrome 中，打开工具栏中的扩展程序图标，然后点击**管理
   扩展程序**。
2. 在扩展卡片上，点击**详细信息**。
3. 开启**允许访问文件网址**。

更改设置后，再次启动 Chrome 任务。

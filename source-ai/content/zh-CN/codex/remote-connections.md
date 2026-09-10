---
title: 远程连接
source_id: codex/remote-connections
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/remote-connections
owner: OpenAI
content_sha256: 14b290d550d35d9330534dd1f88ee1681f929c4414b64c35b2181ed52340f475
translation_of: codex/remote-connections
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/remote-connections)

Content owner: OpenAI

# 远程连接

> 完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。通过在页面 URL 后附加 `.md`，可以获得文档页面的 Markdown 版本。

远程连接允许您访问在另一台设备或机器上运行的工作。
在 ChatGPT 移动应用中，打开 **远程** 以处理位于
已连接的 Mac 或 Windows 设备上的 ChatGPT 或 Codex 聊天。您还可以从另一台
运行 ChatGPT 桌面应用的受支持设备继续工作，或者将应用连接到
SSH 主机上的项目。

远程访问会使用已连接主机的项目、聊天、文件、凭据、
权限、插件、计算机使用、浏览器设置以及本地工具。

## 您可以远程执行的操作

- 在主机的项目中发起新聊天，或继续现有的聊天。
- 发送后续指令、回答问题并引导正在进行的工作。
- 批准命令和其他操作。
- 审查输出、差异、测试结果、终端输出和屏幕截图。
- 当 ChatGPT 完成任务或需要您的关注时收到通知。
- 在已连接的主机和聊天之间切换。

接下来的部分将介绍如何在 ChatGPT 移动应用中打开 **远程** 以访问
桌面主机。要将 Codex 连接到 SSH 主机上的项目，请参见
[连接到 SSH 主机](#connect-to-an-ssh-host)。



  <CodexScreenshot
    alt="ChatGPT 移动应用中的远程设置界面"
    lightSrc="/images/codex/app/mobile-setup-light.webp"
    darkSrc="/images/codex/app/mobile-setup-dark.webp"
    variant="no-wallpaper"
    maxHeight="none"
    maxWidth="420px"
  />



<a id="before-you-set-up-mobile-access"></a>

## 在设置远程之前

远程支持在 macOS 和 Windows 上运行 ChatGPT 桌面应用的主机。
  您可以从 iOS 或 Android 上的 ChatGPT 控制主机，也可以从另一台 Mac 或
  Windows 设备进行控制（当 **控制其他设备** 可用时）。可用性可能
  因推出情况而异。

请确保您具备：

- 您想使用的 ChatGPT 账户和工作空间中的 Codex 访问权限。
- iOS 或 Android 设备上的最新 ChatGPT 移动应用。如果 **远程**
  未出现在应用中，请先更新 ChatGPT。
- 在已唤醒的主机上运行的最新版 macOS 或 Windows ChatGPT 桌面应用，该主机需
  在线，并且已登录到相同的账户和工作空间。移动端设置从应用开始；
  您无法从 Codex CLI 或 IDE 扩展中进行设置。
- 该账户或工作空间所需的任何多因素身份验证、SSO 或通行密钥配置，适用于
  该账户或工作空间。

如果您通过 ChatGPT 工作空间使用 Codex，您的管理员可能需要启用
远程控制访问权限，然后您才能从手机进行连接。

<a id="set-up-mobile-access"></a>

## 设置远程

从您要连接的主机上的 ChatGPT 桌面应用开始。设置流程
为该主机启用远程访问，然后显示一个二维码，您可以用
手机扫描它。
该二维码会将该手机与该主机配对。将每部手机或受支持的
桌面应用设备与您希望其控制的每个主机进行配对。

自 2026 年 6 月 8 日起使用过的现有连接仍保持配对。如果您自
  2026 年 6 月 8 日起未曾使用过现有连接，请更新这两个应用并重新
  配对设备。

<WorkflowSteps variant="headings">

1. 开始远程设置。

   在主机上打开应用，并在侧边栏中选择**设置远程**。

2. 扫描二维码。

   使用您的手机扫描应用显示的二维码。该二维码会打开 ChatGPT，
   以便您可以完成将移动应用连接到主机的操作。

3. 在 ChatGPT 中完成设置。

   ChatGPT 将打开远程设置流程。确认相同的 ChatGPT 账户
   和工作区，然后完成任何所需的多因素身份验证、SSO
   或通行密钥步骤。设置成功后，该主机将出现在您手机的
   远程中。

4. 检查主机设置。

   在主机的应用中，使用**设置 > 连接**来管理已连接的
   设备。您还可以选择是否让计算机保持唤醒状态、启用
   Computer Use，或安装 Chrome 扩展程序。

</WorkflowSteps>

<Illustration description="用于允许设备控制此 Mac 并使其保持唤醒的连接控件。">
  <RemoteConnectionsIllustration
    view="control-this-mac"
    ariaLabel="用于允许设备控制此 Mac 并使其保持唤醒的连接控件。"
  />
</Illustration>

## 选择要连接的内容

从您已经使用 ChatGPT 的笔记本电脑或台式机开始。当您需要持续访问或
不同的环境时，添加一台常开计算机或 SSH 主机。

### 

<Desktop width={17} height={17} />

您的笔记本电脑或台式机



连接已安装桌面应用的 Mac 或 Windows PC。这
提供了对您已在使用的相同项目、聊天、凭据、插件和本地
设置的远程访问。

如果该计算机休眠、失去网络访问权限或关闭应用，远程访问
将停止，直到它再次可用。如果您将此计算机用作主机设备，
请保持其接通电源，并使用主机的连接设置使其在
可用时保持唤醒状态。

在 Mac 笔记本电脑上，在打开盖子并接通
电源的情况下，远程访问可以保持可用。如果合上盖子，还需要连接外部显示器。选择
**睡眠**仍然会停止远程访问。

在 Windows 主机上，保持会话解锁，并供使用
[Computer Use](https://learn.chatgpt.com/docs/computer-use)的任务可用。Windows 上的 Computer Use 在
前台运行，因此远程控制最适合在您
将主机桌面专用于该任务时启动或检查工作。

### 

<Storage width={17} height={17} />

专用的常开计算机



当您希望 ChatGPT 保持
可访问以进行长时间运行的工作时，请使用专用的常开 Mac 或 Windows PC。

安装 ChatGPT 或
Codex 应在该机器上使用的项目、凭据、MCP 服务器、技能和工具。

### 

<Terminal width={17} height={17} />

远程开发环境



当项目
已经存在于远程环境中时，请使用 SSH 主机或受管理的远程开发环境。首先将桌面应用主机连接到该
环境；您的手机仍连接到同一台主机，并且 ChatGPT 在
远程环境中连同其依赖项、安全策略和计算
资源一起工作。

有关 SSH 设置的详细信息，请参阅 [connect to an SSH host](#connect-to-an-ssh-host)。

对于常开计算机或远程主机上的浏览器或桌面任务，启用
  Computer Use 并在该主机上安装 Chrome 扩展程序。

## 来自所连接主机的内容

你的手机向 ChatGPT 发送提示词、批准和后续消息。所连接的
主机提供了 ChatGPT 使用的环境。

这意味着：

- 仓库文件和本地文档来自所连接的主机。
- Shell 命令在该主机或远程环境上运行。
- MCP 服务器、技能、浏览器访问和 Computer Use 来自该主机的
  配置。
- 已登录的网站和桌面应用仅在该主机可以
  访问它们时才可用。
- 沙盒设置、安全控制和操作批准仍然适用
  于所连接的会话。

安全中继层使受信任的机器能够跨越你授权的
ChatGPT 设备保持可访问，而不会将它们直接暴露给公共互联网。

## 从另一台设备继续工作

你可以从另一台运行 ChatGPT 桌面
应用并支持远程控制的已登录设备继续工作。例如，如果你的笔记本电脑不可用，你可以
在始终在线的主机上从手机开始聊天，然后稍后在
你的笔记本电脑上打开应用并在那里继续同一个聊天。

在提供此功能的 Mac 或 Windows 设备上，使用**设置 >
连接 > 控制其他设备**来添加另一台主机。一台设备可以
同时允许远程访问并控制另一台设备。

<Illustration description="用于从这台 Mac 控制另一台设备的连接设置卡片。">
  <RemoteConnectionsIllustration
    view="control-other-devices"
    ariaLabel="用于从这台 Mac 控制另一台设备的连接设置卡片。"
  />
</Illustration>

## 连接到 SSH 主机

在 ChatGPT 桌面应用中，从 SSH 主机添加远程项目并针对远程
文件系统和 shell 运行聊天。远程项目聊天会运行命令、
读取文件并在远程主机上写入更改。

保持远程主机的配置与你在正常 SSH 访问中使用的
安全期望相同：受信任的密钥、最小权限账户，并且没有
未经身份验证的公共监听器。

<WorkflowSteps variant="headings">

1. 将主机添加到你的 SSH 配置中，以便 Codex 可以自动发现它。

```text
   Host devbox
     HostName devbox.example.com
     User you
     IdentityFile ~/.ssh/id_ed25519
```

   Codex 从 `~/.ssh/config` 读取具体的主机别名，使用
   OpenSSH 解析它们，并忽略仅有模式的主机。

2. 确认你可以从运行该应用的机器通过 SSH 连接到该主机。

```bash
   ssh devbox
```

3. 在远程主机上安装并对 Codex 进行身份验证。

   该应用通过 SSH 启动远程 Codex 应用服务器，并使用远程
   用户的登录 shell。确保 `codex` 命令在
   该 shell 中的远程主机的 `PATH` 上可用。

4. 在应用中，打开**设置 > 连接**，添加或启用 SSH 主机，然后
   选择一个远程项目文件夹。

</WorkflowSteps>

<Illustration description="包含三个远程主机的连接 SSH 列表。">
  <RemoteConnectionsIllustration
    view="ssh"
    ariaLabel="包含三个远程主机的连接 SSH 列表。"
  />
</Illustration>

<a id="hand-off-a-thread-between-hosts"></a>
<a id="hand-off-a-chat-between-hosts"></a>
<a id="hand-off-a-task-between-hosts"></a>

## 在主机之间移交对话

移交功能可在您的本地计算机
和已连接的远程主机之间移动现有对话及其 Git 状态。使用它在本地开始工作，在
远程计算机的工作树中继续，稍后再带回对话。

在移交对话之前，请连接目标主机并保存项目
到该主机上的同一 Git 仓库。如果项目是
仓库的子目录，请在两台主机上保存相同的子目录。Codex 仅显示
具有匹配的已保存项目的目标位置。

要移交对话，请：

1. 在桌面应用中打开对话。
2. 在对话页脚，选择当前运行位置，然后选择
   目标主机。当把远程对话移回
   到本地计算机时，选择**此计算机**。
3. 检查目标和分支，然后选择**移交**。

Codex 在目标主机上创建或重用工作树，传输
对话及 Git 状态，并将对话切换到该主机。如果对话
正在运行，移交会在传输前中断当前响应。

您也可以在另一个对话中要求 Codex 将指定对话移交到
已连接的主机。Codex 无法移交发出请求的对话，且不支持移交
到 Codex 云环境。

## 身份验证和网络暴露

远程连接使用 SSH 启动和管理远程 Codex 应用服务器。
请勿在共享或公共网络上直接暴露应用服务器传输层。

如果您需要访问当前网络之外的远程计算机，请使用 VPN
或网格网络工具，而不要将应用服务器直接暴露到
互联网。

## 故障排除

### 您在手机上没有看到主机

请确认主机上的桌面应用正在运行，且您已启用**允许
其他设备连接**，并且两台设备使用同一个 ChatGPT 账户和
工作区。如果您自 2026 年 6 月 8 日起未使用过该连接，请更新
这两个应用并重新配对设备。

### 重新登录后“远程控制”已关闭

退出 ChatGPT 会关闭**远程控制**，但这不会移除您
现有的设备配对。重新登录后，请打开**远程控制**以
恢复先前的连接状态。

如果您在开启**远程控制**并选择**添加**后看到错误，
请重启主机上的 ChatGPT 桌面应用，然后再试一次。

### 批准请求未出现

在 ChatGPT 移动应用中，打开**远程**。确认手机和主机使用
相同的 ChatGPT 账户和工作区，然后重新扫描二维码，或从主机重启
设置。如果您使用的是 ChatGPT 工作区，请要求管理员确认
他们已启用远程控制访问。

### 远程会话断开连接

检查主机是否进入睡眠状态、网络连接是否中断或应用是否关闭。
在 ChatGPT 运行期间，请保持主机处于唤醒和连接状态。

### 身份验证阻止了设置

完成设置期间显示的账户或工作区身份验证提示。如果
您的组织要求使用 SSO、多因素身份验证或通行密钥，
请在重试前完成该流程。如果设置仍然失败，请让您的工作区
管理员确认他们已启用远程控制访问。

## 另请参阅

- [ChatGPT 桌面应用](https://learn.chatgpt.com/docs/app)
- [功能](https://learn.chatgpt.com/docs/features)
- [ChatGPT 桌面应用设置](https://learn.chatgpt.com/docs/reference/settings)
- [计算机使用](https://learn.chatgpt.com/docs/computer-use)
- [Chrome 扩展程序](https://learn.chatgpt.com/docs/chrome-extension)
- [命令行选项](https://learn.chatgpt.com/docs/developer-commands?surface=cli)
- [身份验证](https://learn.chatgpt.com/docs/auth)

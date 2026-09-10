---
title: 在模拟器中测试 iOS 应用
source_id: claude-code/desktop-ios-simulator
product: claude-code
lang: zh-CN
canonical_url: https://code.claude.com/docs/en/desktop-ios-simulator
owner: Anthropic
content_sha256: fe24f1eaff4f64378d48390e70415ba2ee1d9607330c77d65ba49b8aea8db79f
translation_of: claude-code/desktop-ios-simulator
translation_model: gpt-5.6
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://code.claude.com/docs/en/desktop-ios-simulator)

Content owner: Anthropic

> ## 文档索引
> 在以下地址获取完整的文档索引：https://code.claude.com/docs/llms.txt
> 使用此文件可在深入探索之前发现所有可用页面。

# 在模拟器中测试 iOS 应用

> 当 Claude 构建、运行或检查你的应用时，Claude Code Desktop 会在 iOS Simulator 窗格中打开应用，并为每个会话提供单独的模拟器。

<Note>
  iOS Simulator 窗格目前在 macOS 版 Claude Code Desktop 中提供公开测试版。它适用于 Pro、Max 和 Team 计划，但不适用于 Enterprise 计划。
</Note>

iOS Simulator 窗格会在 Claude Code Desktop 的对话旁显示运行于 Apple iOS Simulator 中的应用。当 Claude 在模拟器中构建、安装、启动或检查你的应用时，该窗格会自动打开，并实时传输设备屏幕。你可以用它观察 Claude 运行和测试应用，也可以在 Claude 继续工作时自行点击操作应用。

模拟器窗格会直接驱动模拟器，因此无需[计算机使用](/docs/en/desktop#let-claude-use-your-computer)，也绝不会接管屏幕或隐藏其他窗口。而在 CLI 中，Claude 会改为通过[计算机使用](/docs/en/computer-use#test-a-simulator-flow)访问 iOS Simulator；它会像你使用鼠标一样控制屏幕上的模拟器。

## 要求

模拟器窗格使用 Apple 的模拟器工具，桌面应用本身不包含这些工具。开始会话前，请确保具备：

* Claude Desktop v1.24012.0 或更高版本
* Mac，因为 Apple iOS Simulator 只能在 macOS 上运行
* 已安装 iOS 平台的 [Xcode](https://developer.apple.com/xcode/)，它会提供模拟器设备。如果 Xcode 尚未列出任何模拟器，请参阅[模拟器窗格显示未找到模拟器](#the-simulator-pane-says-no-simulators-were-found)

<Note>
  在本页面中，“设备”是指模拟的 iPhone 或 iPad，即你在 Xcode 的 **Window → Devices and Simulators** 下管理的同类模拟器设备，而不是物理硬件。
</Note>

模拟器窗格仅在本地会话中可用。在[云端](/docs/en/desktop#run-long-running-tasks-remotely)和 [SSH](/docs/en/desktop#ssh-sessions) 会话中，Claude 在无法访问你 Mac 上模拟器的机器上运行。

## 在模拟器中运行应用

无需使用命令或设置即可打开模拟器窗格。Claude 在模拟器中运行你的应用时会自动打开它。

<Steps>
  <Step title="打开你的 iOS 项目">
    在 Claude Code Desktop 中打开 **Code** 选项卡，并以应用项目作为[项目文件夹](/docs/en/desktop#start-a-session)启动会话。任何能为 iOS Simulator 构建应用的项目都可以使用。
  </Step>

  <Step title="让 Claude 运行或测试应用">
    围绕运行或验证应用来表述任务。例如：

    ```text theme={null}
    Build the app and run it in the simulator to check the onboarding flow.
    ```
  </Step>

  <Step title="在模拟器窗格中观察应用">
    应用在模拟器中启动时，iOS Simulator 窗格会在对话旁打开。Claude 首次使用某个设备时，桌面应用会要求你授权；请参阅[授予 Claude 设备访问权限](#grant-claude-access-to-a-device)。Claude 会安装应用、点击操作，并读取屏幕以验证自己的更改，而你可以全程观察。
  </Step>
</Steps>

无论在会话的哪个阶段，只要 Claude 在模拟器中启动应用，模拟器窗格都会打开。当你的请求与查看应用有关时，例如“新屏幕看起来正确吗？”，Claude 会在开始工作前启动模拟器。Claude 修复错误或更改屏幕后，请让它验证更改：如果窗格尚未打开，重新启动应用会再次打开它。

模拟器窗格会显示应用实际启动到的设备。若要在特定设备上测试，请在请求中指定其名称，例如“在 iPhone SE 模拟器上运行”，Claude 构建和启动时就会以该设备为目标。

Claude 启动的设备也会出现在 Apple Simulator 应用中，而 Claude 也可以将应用安装到你已经启动的设备上。

你也可以自行打开模拟器窗格。会话附加过模拟器或编辑过 Swift 文件后，会话工具栏的 **Views** 菜单会显示 **iOS Simulator** 条目。如果窗格尚未显示设备，请点击 **Attach simulator**，或从旁边的设备菜单中选择特定设备；选择已关机的设备会将其启动。如果缺少 Xcode 或其模拟器，窗格会改为显示设置步骤，并在你完成时逐项勾选。

## 自行控制模拟器

模拟器窗格具有交互能力，而不只是查看器。在 Claude 工作期间或任务之间，你可以：

* 在设备屏幕上点击和拖动，以执行轻点与滑动
* 使用与 Apple Simulator 应用相同的快捷键按硬件按钮：**Cmd+Shift+H** 返回主屏幕、**Cmd+L** 锁定、**Cmd+Up Arrow** 和 **Cmd+Down Arrow** 调节音量
* 使用旋转按钮或 **Cmd+Right Arrow** 将设备顺时针旋转四分之一圈
* 从设备菜单中切换窗格所显示的设备；该菜单会列出每个模拟器的操作系统版本以及是否已启动
* 使用窗格的捕获按钮或快捷键，通过 **Cmd+S** 保存屏幕截图，或通过 **Cmd+R** 保存屏幕录制；文件会保存到 Desktop
* 点击 **Detach simulator** 停止传输设备画面但不将其关机，这会让窗格返回 **Attach simulator** 状态

设备名称下方的一行控件用于调整来自模拟器的视频流。如果窗格给 Mac 带来压力，请降低 **Frame rate** 或 **Resolution**；还可在 H.264 和 JPEG 之间切换 **Encoding**，或者勾选 **FPS** 以显示窗格接收到的帧率。这些设置只会改变窗格显示设备的方式，不会改变应用的运行方式。

你和 Claude 驱动的是同一台设备，因此你的点击会改变 Claude 所看到的应用状态。若要让 Claude 检查特定屏幕，请先通过点击导航到该屏幕，然后提出请求。Claude 驱动设备时，窗格会在屏幕上方显示 **Claude is using this device** 徽标；请等到徽标消失后再点击，以确保结果反映的是应用行为，而不是你的输入。

## 会话如何管理设备

每台设备都属于启动它的会话，因此[并行会话](/docs/en/desktop#work-in-parallel-with-sessions)不会共享设备：你在一个会话窗格中看到的是该会话的工作，而不是另一个会话的工作。在侧边栏中切换会话时，模拟器视图会随对话一起切换；切换回来时，会从同一设备上次停下的位置继续。如果 Claude 使用多个设备，每台设备都会打开自己的窗格，每个会话最多 4 个。

Claude Code Desktop 会在自己启动的模拟器不再使用后将其关闭：当你退出应用、归档会话，或从窗格分离设备 10 分钟后。由你自行启动的设备，无论是从窗格还是 Apple Simulator 应用启动，都绝不会自动关闭。若要立即关闭已附加设备，请使用窗格中的关机按钮。

## 授予 Claude 设备访问权限

Claude 控制设备前会请求你的同意，而构建应用或在设备上打开 URL 则遵循会话的权限模式。你或你的组织也可以完全关闭 Claude 的访问权限。

### 首次使用时允许设备

Claude 首次使用模拟器时，桌面应用会要求你允许。此同意涵盖控制该设备以及截取设备屏幕截图，并且是每台设备同意一次，而不是每个会话一次。Claude 截取的设备屏幕截图会发送给 Anthropic，并按照你正常的对话保留设置进行保留，因此不要在 Claude 使用的设备上登录真实账户。

允许设备后，Claude 在该设备上的操作（例如轻点、输入、启动应用和截取屏幕截图）无需进一步提示即可运行。它们与你在窗格中点击具有相同的信任级别，而且只会触及模拟设备，因此该窗格不需要计算机使用所要求的 macOS Accessibility 和 Screen Recording 权限。

如果拒绝，设备仍会启动，窗格也仍可供你自行点击；只有 Claude 的访问权限会保持关闭。若之后改变主意，请在窗格中点击 **Let Claude use it**。

### 遵循权限模式的操作

有两项操作遵循会话的[权限模式](/docs/en/permissions#permission-modes)，而不是一次性同意：

* 在设备上打开 URL，例如测试深层链接或在设备的 Safari 中加载页面，因为 URL 可以将数据带出设备。
* 构建应用，因为 `xcodebuild` 会在你的 Mac 上运行项目的构建脚本。检查已经在进行的构建不会触发提示。

### 关闭模拟器访问权限

你可以在桌面应用的设置中关闭 Claude 的模拟器访问权限。组织有两种方式可以为所有人关闭它：

* `disableMobileSimulatorTools` [托管设置](/docs/en/desktop#managed-settings)会阻止 Claude 的模拟器工具。模拟器窗格仍可供你自行点击，并且无法从应用内覆盖该设置。
* `requireCoworkFullVmSandbox` 策略键会让 Claude 的工具在隔离虚拟机中运行，而不是在你的 Mac 上运行；它会完全禁用模拟器窗格和 Claude 的模拟器工具，因此设置该键时，窗格无法附加设备。

任一设置适用时，Claude 都会告知你。

## 限制

Claude 只能驱动模拟设备，无法控制物理 iPhone 或 iPad。若要在物理设备上测试，请自行从 Xcode 在该设备上运行应用，然后描述你看到的内容，或将屏幕截图附加到对话中供 Claude 处理。

## 故障排除

### Claude 运行应用时模拟器窗格没有打开

Claude 可能没有识别出你想运行或测试应用，或者缺少模拟器工具。请检查以下事项：

* 明确说明目标，例如“在 iOS Simulator 中运行应用，并点击完成注册流程”。
* 单独启动 Simulator 应用，确认 Xcode 和 iOS Simulator 已安装。
* 如果你的组织管理 Claude Code，[模拟器工具可能已被策略禁用](#turn-off-simulator-access)。
* 模拟器窗格要求 Claude Desktop v1.24012.0 或更高版本。打开 **Claude → Check for Updates**，然后重新启动应用。

### 模拟器窗格显示未找到模拟器

Xcode 已安装，但没有可列出的 iOS 模拟器。模拟器窗格会显示要执行的设置步骤，并在每项完成时逐项勾选。若要手动安装缺失组件，请从 Xcode 设置中下载 iOS 模拟器运行时，或运行 `xcodebuild -downloadPlatform iOS`。

## 另请参阅

* [Desktop 中的计算机使用](/docs/en/desktop#let-claude-use-your-computer)：控制没有专用窗格的应用屏幕
* [CLI 中的计算机使用](/docs/en/computer-use)：CLI 如何访问 iOS Simulator
* [使用会话并行工作](/docs/en/desktop#work-in-parallel-with-sessions)：会话如何隔离更改
* [Claude Code Desktop 入门](/docs/en/desktop-quickstart)

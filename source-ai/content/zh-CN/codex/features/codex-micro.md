---
title: Codex Micro
source_id: codex/features/codex-micro
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/features/codex-micro
owner: OpenAI
content_sha256: 085c4654dd68e0a353e17ab38bb06be836143fa234b01cb3854a242563397014
translation_of: codex/features/codex-micro
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/features/codex-micro)

Content owner: OpenAI

# Codex Micro

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。可以通过在页面 URL 后附加 `.md` 来获取文档页面的 Markdown 版本。

Codex Micro 是 Codex 和 Work Louder 之间限量推出的合作产品。它
可与 ChatGPT 桌面应用程序配合使用，为您提供一种快捷的方式来查看对话、
在对话间切换、使用按键说话，以及触发常用操作或技能，
而无需离开键盘。

  

  

    <Illustration description="带有发光的 Agent Keys、可自定义的 Command Keys、一个拨盘和一个摇杆的交互式 Codex Micro 键盘">
      <CodexMicroKeyboardIllustration
        ariaLabel="带有发光的 Agent Keys、可自定义的 Command Keys、一个拨盘和一个摇杆的交互式 Codex Micro 键盘"
      />
    </Illustration>
  




## 设置 Codex Micro

1. 打开 ChatGPT 桌面应用程序。
2. 使用 USB-C 数据线或蓝牙将 Codex Micro 连接到您的计算机，然后
   按照 ChatGPT 检测到它时出现的设置提示进行操作。
3. 在 macOS 上，出现提示时允许 **输入监控**，以便 ChatGPT 能够响应
   按键操作。
4. 打开 **设置 > Codex Micro**，以选择 Agent Keys 跟踪的对话，
   为命令键和模拟方向分配操作，并调整
   灯光。

要再次打开这些设置，请按住拨盘 500 毫秒，或者
选择 ChatGPT 底部您的账户名旁边的 Codex Micro 图标。

在 ChatGPT 首次检测到该设备后，您将在“设置”中看到 **Codex Micro**。如果您想在 ChatGPT 之外使用该设备，请自定义这些
控件，请使用 [Work Louder Input](https://worklouder.cc/micro-setup)。

<a id="read-and-switch-tasks-with-agent-keys"></a>

## 使用 Agent Keys 阅读并切换对话

六个磨砂 Agent Keys 中的每一个都可以跟踪一个对话，并亮起以显示其
当前状态。按一次 Agent Key 可切换到该对话，而无需将
ChatGPT 置于前台。在 350 毫秒内按两次可切换对话，并
将 ChatGPT 窗口置于前台。

| 颜色 | 状态           | 含义                                   |
| ----- | ---------------- | ----------------------------------------- |
| 白色 | 空闲             | 对话处于空闲状态。                         |
| 蓝色  | 思考中           | ChatGPT 正在工作。                        |
| 绿色 | 已完成           | 对话已完成，并带有未读更新。             |
| 琥珀 | 需要输入         | ChatGPT 需要您的批准或回复。             |
| 红色   | 错误            | 出现了错误。                              |
| 关闭   | 无分配对话       | 此按键未跟踪对话。                        |

所选对话的按键会以其状态灯颜色脉动。

默认情况下，这些按键会跟踪您最近更新的六个对话，无论
它们是否被固定。您可以在 **设置 > Codex
Micro** 中更改 **Agent source** 以使用不同的排列方式：

- **最近的对话**：跟踪最近更新的六个对话，无论固定还是
  未固定。
- **已固定的对话**：跟踪 **已固定** 中的前六个对话。
- **优先对话**：将等待输入的对话、未读对话和活跃
  对话排在前面。
- **自定义分配**：选择分配给每个 Agent Key 的对话。按下一个未
  分配的 Agent Key 可打开一个新对话。当您开始对话时，ChatGPT
  会将其分配给该按键。

状态颜色保持不变。您可以决定 Agent Keys 跟踪哪些对话，
但您无法将它们变成额外的命令键。

## 使用和自定义命令键

Codex Micro 的默认布局包含六个操作：



  


|                            按键                            | 默认操作                           |
| :-------------------------------------------------------: | ---------------------------------------- |
|  <CodexMicroTableKeycap keycapId="FAST" label="Fast" />   | 打开或关闭快速模式。                |
| <CodexMicroTableKeycap keycapId="APPR" label="Approve" /> | 批准当前请求。             |
| <CodexMicroTableKeycap keycapId="REJ" label="Decline" />  | 拒绝当前请求。             |
|  <CodexMicroTableKeycap keycapId="SPLIT" label="Fork" />  | 在新对话中继续当前对话。 |
|   <CodexMicroTableKeycap keycapId="MIC" label="Mic" />    | 开始按键说话。                      |
| <CodexMicroTableKeycap keycapId="CODEX" label="Codex" />  | 发送输入框中的消息。        |

  

  


Mic 键使用您电脑的麦克风。Codex Micro 本身没有
麦克风。说话时按住该键，说完后松开。
要进行免提录音，请在 350 毫秒内连续按两次以保持
录音。再次按下即可停止。

录音时，海绿色的光会在键盘上流转。当
ChatGPT 处理您的语音时，它会变成移动的白光，然后变成
常亮的白光，表示提示词已就绪。按下 Codex 键将其发送。

在 **设置 > Codex Micro** 中，选择一个命令键，然后选择其键帽和
操作。您可以打开浏览器或终端，审查更改，使用 Git 提交，
创建拉取请求，附加文件或照片，管理计划任务，更改
推理强度，或打开 **技能**。如果您选择的键帽已在
其他地方使用过，ChatGPT 会交换这两个键帽，而不是重复使用同一个键帽。

重新映射按键后，请更换物理键帽以匹配其新操作。

  




## 使用摇杆和拨盘



  


摇杆可以自由地向任何方向移动。当您将其推离
中心足够远时，ChatGPT 会将此移动转换为四个方向
操作之一。Codex Micro 的初始映射如下所示。

在 **设置 > Codex Micro** 中，为每个
方向选择任何可用的 ChatGPT 桌面命令或已启用的技能。

  

  


| 方向 | 默认操作             |
| --------- | -------------------------- |
| 上        | 打开或关闭计划模式。  |
| 右     | 在应用历史记录中前进。 |
| 下      | 显示或隐藏侧边栏。  |
| 左      | 在应用历史记录中后退。    |

  




拨盘可在输入框控件和选项之间移动，默认选中 **推理**。
转动拨盘可更改选择，然后按下它以
打开或选择聚焦的控件。当输入框控件或菜单打开时，
拨盘右侧紧邻的 Agent Key 会亮起红灯。按下该键
以取消。

在 **设置 > Codex Micro** 中，选择拨盘是使用 **输入框
导航** 还是 **仅推理**。在 **仅推理** 模式下，转动拨盘
会打开并调整推理强度。按下拨盘可打开滑块或其
高级选项。

## 调整灯光

在 **设置 > Codex Micro** 中，调整亮度并选择当您
不使用 Codex Micro 时灯光保持亮起的时间。当您
使用键盘或 Agent Key 状态改变时，灯光会重新亮起。默认情况下，灯光在
三分钟后熄灭。

当键盘报告其电池状态时，您可以在 **设置 >
Codex Micro** 以及 Codex Micro 图标的侧边栏提示中看到它。

## 添加更多层

Codex 使用第 1 层。使用 [Work Louder
Input](https://worklouder.cc/micro-setup) 配置最多五个额外的层，
为其他应用提供快捷方式和操作。

## 排查 Codex Micro 故障

### 重新配对键盘

使用左下角触摸控制重新开始配对。背面按钮
控制电源，不会启动配对。

1. 按住左下角触摸控制三秒以进入通信
   模式。
2. 轻触控制选择蓝牙通道 1、2 或 3。
3. 在该通道上按住控制三秒。通道灯闪烁
   表示正在配对，配对成功后常亮。

### 修复 macOS 上的输入监控

如果 **设置 > Codex Micro** 显示输入监控未设置，请选择
**打开系统设置**，然后按照以下步骤操作：

1. 打开 **系统设置 > 隐私与安全性 > 输入监控**。
2. 如果 ChatGPT 已在列表中，请开启其访问权限。如果缺少，将
   **ChatGPT** 从应用程序拖入列表，或选择 **添加 (+)** 并选择
   **ChatGPT**。
3. 退出并重新打开 ChatGPT，然后确认 ChatGPT 在第 1 层检测到 Codex Micro。

有关此 macOS 权限的更多信息，请参阅 [Apple 的输入监控
指南](https://support.apple.com/guide/mac-help/mchl4cedafb6/mac)。

### 获取更多 Work Louder 帮助

如需有关蓝牙、线缆、电源或重置键盘的帮助，请参阅
[Work Louder 的 Creator Micro 2 设置指南](https://worklouder.cc/micro-setup)。
如需直接支持，请发送邮件至 [hello@worklouder.cc](mailto:hello@worklouder.cc)。

## 获取 Codex Micro

您可以通过 [OpenAI Supply
Co](https://openai.com/supply/co-lab/work-louder/) 购买 Codex Micro，售完即止。

{/* vale Microsoft.We = NO */}
{/* vale write-good.TooWordy = NO */}

我们预计订单将在购买后不久开始发货。

{/* vale Microsoft.We = YES */}
{/* vale write-good.TooWordy = YES */}

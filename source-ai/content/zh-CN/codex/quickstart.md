---
title: 快速入门
source_id: codex/quickstart
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/quickstart
owner: OpenAI
content_sha256: a90df8853e663dc3b473e6c5fea576426914f49689540c5bd10432d90425acfc
translation_of: codex/quickstart
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/quickstart)

Content owner: OpenAI

# 快速入门

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。可以通过在页面 URL 后附加 `.md` 来获取文档页面的 Markdown 版本。

## 在哪里使用 ChatGPT

在不同的平台上使用 ChatGPT，包括
[ChatGPT 桌面应用程序](https://learn.chatgpt.com/docs/app) 和 [网络版 ChatGPT](https://learn.chatgpt.com/docs/web)。选择
适合您工作的选项。

<Illustration description="卡片比较了 ChatGPT 桌面应用程序和网络版 ChatGPT">
  <QuickstartSetupSelector />
</Illustration>

如果您是开发者，并希望在终端或代码编辑器中使用 Codex，
  请尝试 [Codex CLI](https://learn.chatgpt.com/docs/codex/cli) 或 [Codex IDE 扩展](https://learn.chatgpt.com/docs/codex/ide)。

## 设置

{/* prettier-ignore */}
<Tabs
  id="codex-quickstart-setup"
  param="setup"
  defaultTab="web"
  size="md"
  tabs={[
    { id: "app", label: "桌面版" },
    { id: "web", label: "网页版" },
  ]}
>
  

ChatGPT 桌面应用程序适用于 Windows 和 macOS。将其用于项目、
本地文件、更长的任务和快速聊天。

<WorkflowSteps variant="headings">
1. <h3 id="setup-app-install">安装 ChatGPT 桌面应用程序</h3>

    选择适合您操作系统的版本：

    <CodexAppDownloadCta client:load className="mb-4" />

2.  <h3 id="setup-app-sign-in">打开 ChatGPT 桌面应用程序并登录</h3>

    打开应用程序，然后使用您的 ChatGPT 帐户登录。

    您也可以通过 API 密钥使用 Codex。[某些功能可能不可用](https://learn.chatgpt.com/docs/pricing#feature-availability)。

3.  <h3 id="setup-app-select-workspace">选择 ChatGPT 的工作位置</h3>

    开始聊天、创建项目或打开文件夹。ChatGPT 可以读取和修改
    您所选文件夹中的文件。[了解有关聊天和项目的更多信息](https://learn.chatgpt.com/docs/projects)。

4.  <h3 id="setup-app-start-task">开始聊天</h3>

            


          


                - 对于研究、分析或文档、演示文稿、
                  电子表格和站点等交付物，请选择 **ChatGPT**，然后切换到 **工作**，位于
                  新聊天页面的顶部、撰写框上方。
                - 对于需要代码库上下文和开发者工具的软件开发，请选择
                  ChatGPT 下拉菜单中的 **Codex**。
                - 对于快速提问或聊天，请选择 **ChatGPT**，然后选择 **聊天**，
                  位于新聊天页面顶部的切换器中、撰写框上方。在
                  Codex 中，指向 **新聊天**，然后选择其右侧的 **快速聊天** 图标。

                了解有关 [使用 ChatGPT](https://learn.chatgpt.com/docs/use-chatgpt) 的更多信息。

              


          <ChatGPTModeDropdown client:load />

    


5.  <h3 id="setup-app-send-message">发送您的第一条消息</h3>

    描述您的目标并添加 ChatGPT 所需的任何文件或上下文。尝试一个示例：

    <CodexPromptComposer
      client:load
      id="first-message-example"
      promptOptions={[
        {
          label: "准备决策",
          prompt:
            "审阅此项目中的报告和笔记，比较各个选项，并创建一份一页纸的决策备忘录，包含建议、风险、待解决问题和来源链接。",
        },
        {
          label: "分析电子表格",
          prompt:
            "合并此文件夹中的电子表格，清理不一致的记录，确定最重要的趋势，并创建一份包含图表和简明易懂摘要的简要报告。",
        },
        {
          label: "改进此应用",
          prompt:
            "检查此应用，确定一项高影响力的可用性改进，实施该改进，更新相关测试，并在移动端和桌面端验证结果。",
        },
      ]}
      className="!mt-3 !mb-10 w-full max-w-3xl min-w-0"
    />

    探索更多 [使用案例](https://learn.chatgpt.com/use-cases)。

</WorkflowSteps>

  


  

ChatGPT 可在网络上使用，并包括聊天和 ChatGPT Work。

<WorkflowSteps variant="headings">
1. <h3 id="setup-web-sign-in">打开 ChatGPT 并登录</h3>

前往 [chatgpt.com](https://chatgpt.com) 并使用您的 ChatGPT 账号登录。

2.  <h3 id="setup-web-start-task">开始聊天</h3>

            


          


                - 选择 **聊天** 来提问、探索想法，并处理某个主题
                  以对话的方式。
                - 选择 **工作** 来研究、分析信息，并创建文档、
                  演示文稿、电子表格、Sites 或其他已完成的工作。

                了解更多关于 [使用 ChatGPT](https://learn.chatgpt.com/docs/use-chatgpt) 的信息。

              


          <ChatWorkSegmentPicker client:load />

    


3.  <h3 id="setup-web-select-workspace">选择 ChatGPT 的工作位置</h3>

    开始聊天或选择一个项目。项目可以包含聊天、文件和指令。

4.  <h3 id="setup-web-send-message">发送您的第一条消息</h3>

    描述您的目标并添加 ChatGPT 需要的任何文件或上下文。尝试以下示例：

    <CodexPromptComposer
      client:load
      id="web-first-message-example"
      destination="web"
      placeholder="给 ChatGPT 发消息"
      promptOptions={[
        {
          label: "做出决定",
          prompt:
            "研究我是否应该[决定]，比较最佳选项，解释我目前情况的利弊权衡，并附上引用推荐其中一个。",
        },
        {
          label: "每日简报",
          prompt:
            "每个工作日早上 8:00，查看我关联的日历和最近的消息，然后给我发送一份简报，包含今天的优先事项、会议准备、我需要回复的消息以及阻碍事项。",
        },
        {
          label: "策划活动",
          prompt:
            "帮我策划我的活动。问我关于场合、客人、日期、地点、预算以及你需要的任何其他信息。然后创建一个时间表、预算、邀请函文案和清单，并发布一个 Site 供我邀请客人和收集回复。",
        },
      ]}
      className="!mt-3 !mb-10 w-full max-w-3xl min-w-0"
    />

</WorkflowSteps>

  


</Tabs>



## 后续步骤

[了解更多关于 ChatGPT 桌面应用的信息



      <OpenBook />
    

    使用 ChatGPT 桌面应用来处理您的本地项目。](https://learn.chatgpt.com/docs/app)
[导入您的设置



      <CompareArrows />
    

    将支持的设置、项目和最近的工作导入到 ChatGPT 中。](https://learn.chatgpt.com/docs/import)

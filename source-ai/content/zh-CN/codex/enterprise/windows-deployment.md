---
title: 部署 Windows 应用
source_id: codex/enterprise/windows-deployment
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/enterprise/windows-deployment
owner: OpenAI
content_sha256: f847326f784e47a8fde40a70b6fbcb6103b814a594eca815eb6b9d36db6776fa
translation_of: codex/enterprise/windows-deployment
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/enterprise/windows-deployment)

Content owner: OpenAI

# 部署 Windows 应用

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。可以通过在页面 URL 后附加 `.md` 来获取文档页面的 Markdown 版本。

用户可以自行安装 ChatGPT 桌面应用，或者您的 IT 团队可以
使用企业管理工具进行部署。该应用已由 Store 签名，但
用户无需打开 Microsoft Store 即可安装或更新它。

## 让用户自行安装和更新应用

如果用户可以管理自己的应用程序，请引导他们访问
[Web 安装程序](https://get.microsoft.com/installer/download/9PLM9XGG6VKS?cid=website_cta_psi)。
该安装程序提供标准的安装和自动更新
体验。在安装或更新过程中可能会出现 Microsoft Store 组件，但
用户无需自行浏览 Store。

您也可以从命令行安装该应用：

```powershell
winget install --id 9PLM9XGG6VKS -s msstore
```

## 使用企业管理工具部署应用

如果您的组织集中管理软件，请使用 Microsoft Intune 或
其他兼容的移动设备管理 (MDM) 或软件部署
平台。如果您的平台支持 Microsoft Store 应用部署，请在 Store 应用流程中搜索
来自 OpenAI 的 ChatGPT，或者使用此 Store 产品 ID：

```text
9PLM9XGG6VKS
```

有关设置的详细信息，请参阅以下 Microsoft 文档：

- [企业部署指南](https://1drv.ms/b/c/123ec1ed6c72a14a/IQDVdo5pE5P3QKg5r0eieSvfAeE7cW0yy58ncBFW7OYajwU?e=dGH94F)
- [Intune 部署指南](https://1drv.ms/b/c/123ec1ed6c72a14a/IQDh_5o31T6XT7bUn5RPldEJAZX58gEuRr8YnJD7d2IMpec?e=nByKw6)
- [MECM 部署指南](https://1drv.ms/b/c/123ec1ed6c72a14a/IQB829f_TSbkR7-H9qA4Q9ntAa9D2He3qMjXksWi2ozdeg8?e=GTKgAl)
- [将 Microsoft Store 应用添加到 Microsoft Intune](https://learn.microsoft.com/en-us/intune/app-management/deployment/add-microsoft-store)

## 在没有 Microsoft 分发服务的情况下安装

如果您的环境无法使用 Microsoft 应用分发服务来进行
初始安装，请为每种设备下载已进行 Store 签名的 MSIX 包
架构：

| 设备架构 | 包                                                                                  |
| ------------------- | ---------------------------------------------------------------------------------------- |
| x64                 | [ChatGPT-x64.msix](https://persistent.oaistatic.com/codex-app-prod/ChatGPT-x64.msix)     |
| Arm64               | [ChatGPT-arm64.msix](https://persistent.oaistatic.com/codex-app-prod/ChatGPT-arm64.msix) |

这些稳定链接指向每种
架构最新发布的已进行 Store 签名的包。对于需要许可证文件的离线部署工作流，
还请下载
[离线许可证 (`ChatGPT-License.xml`)](https://persistent.oaistatic.com/codex-app-prod/ChatGPT-License.xml)。
将相应的 MSIX 以及许可证文件（如需要）导入到您的 MDM
或软件部署平台中。

初始安装后，可以访问
`persistent.oaistatic.com` 的设备可以自动安装更新，因此您无需
通过管理工具重新部署较新的包。

此部署路径：

- 支持在受限环境中进行初始安装。
- 支持 x64 和 Arm64 设备。
- 不提供独立的 MSI 或非 Store 的 EXE。

## 相关资源

- [Windows 版 ChatGPT 桌面应用](https://learn.chatgpt.com/docs/windows/windows-app)

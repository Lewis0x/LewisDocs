---
title: 权限
source_id: codex/permissions
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/permissions
owner: OpenAI
content_sha256: 856086daf88f45bda93f36d77adac76de3505911d2bdc9293ce8abbe0f92b713
translation_of: codex/permissions
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/permissions)

Content owner: OpenAI

# 权限

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。可以通过在页面 URL 后附加 `.md` 来获取文档页面的 Markdown 版本。

测试版。权限配置文件正处于积极开发中，可能会发生更改。

权限配置文件无法与较旧的沙盒设置组合使用。请配置
  `default_permissions` 和 `[permissions]`，或者 `sandbox_mode` /
  `sandbox_workspace_write`，但不能同时配置两者。如果 `sandbox_mode` 出现在任何
  已加载的配置文件中，你传递了 `--sandbox`，或者所选的配置文件设置了
  `sandbox_mode`，Codex 将使用那些较旧的沙盒设置，而不是
  `default_permissions`。

托管的 `allowed_permission_profiles` 是个例外：它会使 Codex 使用
权限配置文件。在部署托管
配置文件允许列表之前，请移除诸如
`sandbox_mode` 和 `[sandbox_workspace_write]` 等较旧的设置。对于混合版本的企业推广，你可以将
托管的 `allowed_sandbox_modes` 要求作为临时的兼容性
约束保留，直到每个客户端都运行 Codex 0.138.0 或更高版本。

权限配置文件允许你为 Codex 代表你运行的
本地命令应用最小权限边界。配置文件是一个命名策略，它结合了文件系统
规则（定义命令可以读取或写入哪些内容）与网络规则（定义
命令可以访问哪些目标地址）。

使用配置文件可以在不授予对你的机器或网络的
广泛访问权限的情况下，为 Codex 提供当前聊天所需的足够访问权限。例如，只读配置文件可以
让 Codex 检查项目而不对其进行编辑，而具备写入权限的配置文件
可以将编辑操作限制在选定的工作区根目录中。

本地权限配置文件在 macOS、Linux、WSL 和原生
Windows 上受支持。请参见 [范围与强制执行](#scope-and-enforcement) 了解特定平台的
详细信息和注意事项。

有关 Codex 云网络设置，请参见 [互联网访问](https://learn.chatgpt.com/docs/cloud/internet-access)。

## 定义和选择配置文件

Codex 包含三个内置权限配置文件：

- `:read-only` 保持本地命令执行为只读。
- `:workspace` 允许在活动工作区根目录和系统临时目录内进行写入。
- `:danger-full-access` 移除本地沙盒限制，应仅在
  有意进行这种广泛访问时使用。

在 `[permissions.<name>]` 下创建一个命名配置文件，然后设置顶级
`default_permissions` 键为该配置文件名称或上述内置名称之一。
在此示例中，`project-edit` 是一个用户定义的配置文件名称，而不是内置
值。

企业管理员可以定义配置文件，并限制用户可以通过托管的
`requirements.toml` 选择哪些配置文件。一旦
`allowed_permission_profiles` 存在，被省略的配置文件将被拒绝，
包括被省略的内置配置文件和未来 Codex 版本中添加的配置文件。请参见
[控制可用的权限配置文件](https://learn.chatgpt.com/docs/enterprise/managed-configuration#control-available-permission-profiles)
了解推荐的托管配置。

自定义配置文件使用两个相关概念：

- `[permissions.<name>.workspace_roots]` 添加应作为该配置文件
  工作区根目录的具体目录。
- `[permissions.<name>.filesystem.":workspace_roots"]` 定义 Codex 在每个有效工作区根目录（即当前
  会话的运行时工作区根目录加上上述配置文件定义的根目录）内应用的文件系统
  规则。

配置文件也使用正常的配置层模型。更高优先级的层可以
在相同的配置文件名称下添加或替换条目，而无需重述整个
配置文件。

例如，组织级别的配置和用户级别的配置可以
独立地扩展相同的配置文件：

```toml
# /etc/codex/config.toml

[permissions.server.workspace_roots]
"~/code/server" = true
```

```toml
# ~/.codex/config.toml

[permissions.server.workspace_roots]
"~/code/mobile-app" = true
```

当 `server` 处于活动状态时，两个工作区根目录都将参与有效的
配置文件。

```toml
default_permissions = "project-edit"

[permissions.project-edit.workspace_roots]
"~/code/app" = true
"~/code/shared-lib" = true

[permissions.project-edit.filesystem]
":minimal" = "read"

[permissions.project-edit.filesystem.":workspace_roots"]
"." = "write"
".devcontainer" = "read"
"**/*.env" = "deny"

[permissions.project-edit.network]
enabled = true

[permissions.project-edit.network.domains]
"api.openai.com" = "allow"
"objects.githubusercontent.com" = "allow"
"*.github.com" = "allow"
"tracking.example.com" = "deny"
```

此配置文件：

- 读取常用开发者工具所需的最小运行时路径。
- 将相同的工作区根目录规则应用于当前会话和
  配置文件定义的根目录。
- 在每个根目录下保持如 `.devcontainer/` 等 IDE 相邻设置为
  只读。
- 使用通配符规则拒绝匹配的环境文件。
- 仅允许通过配置的域策略进行网络访问。

在活动的配置文件中，即使更广泛的
路径可读或可写，更严格的拒绝规则仍然有效。例如，配置文件可以使工作区根目录
可写，同时仍将匹配的 `.env` 路径设置为 `deny`。

## 扩展配置文件

当一个配置文件与内置或另一个命名
配置文件大部分相同时，请使用 `extends`。优先扩展内置配置文件，而不是从头开始，以便
延续基准保护。例如，扩展 `:workspace` 会将
工作区根目录的 `.codex` 目录保持为只读，除非你明确
覆盖它。设置父级一次，然后仅添加或覆盖不同的
规则。

```toml
default_permissions = "project-edit"

[permissions.project-edit]
description = "Project editing with OpenAI API access."
extends = ":workspace"

[permissions.project-edit.filesystem.":workspace_roots"]
"**/*.env" = "deny"

[permissions.project-edit.network]
enabled = true

[permissions.project-edit.network.domains]
"api.openai.com" = "allow"
```

此配置文件以 `:workspace` 开始，保持拒绝匹配的 `.env` 文件，并
允许对 `api.openai.com` 的请求。配置文件可以扩展 `:read-only`、
`:workspace` 或另一个命名配置文件。它不能扩展
`:danger-full-access`；Codex 还会拒绝未知的父级和继承
循环。

## 配置规范

| 条目                                                             | 类型 / 值              | 默认                 | 详细信息                                                                                                                                                                                                                                                                                                                                                                                                                       |
| ----------------------------------------------------------------- | -------------------------- | ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `default_permissions`                                             | 字符串配置文件名        | 无                    | 命名 Codex 默认应用的权限配置文件。它必须匹配 `[permissions]` 下的配置文件或诸如 `:workspace` 的内置配置文件。显式设置以获得可预测的行为；仅在 `:workspace` 和 `:read-only` 均被明确允许时，受管理的要求才可省略它。除非受管理的 `allowed_permission_profiles` 告诉它在本次设置中使用权限配置文件，否则 Codex 将使用较旧的沙盒设置。 |
| `[permissions.<name>]`                                            | 表                      | 无                    | 定义一个命名配置文件。 `default_permissions` 选择一个配置文件作为默认；其他权限配置文件设置也使用该配置文件名。                                                                                                                                                                                                                                                                               |
| `permissions.<name>.description`                                  | 字符串                     | 无                    | 为该配置文件提供人类可读的描述。配置文件不会通过 `extends` 继承其父级的描述。                                                                                                                                                                                                                                                                                                 |
| `permissions.<name>.extends`                                      | 字符串配置文件名        | 无                    | 从另一个命名的配置文件或内置的 `:read-only` 或 `:workspace` 配置文件启动此配置文件。Codex 会拒绝 `:danger-full-access`、未知的父级以及继承循环。                                                                                                                                                                                                                                            |
| `[permissions.<name>.workspace_roots]`                            | 表                      | 无                    | 添加由配置文件定义的工作区根目录，这些根目录与当前会话的运行时工作区根目录一起接受 `:workspace_roots` 文件系统规则。                                                                                                                                                                                                                                                                                |
| `permissions.<name>.workspace_roots."<path>"`                     | 布尔值                    | `false`                 | 当 `true` 时，将该路径添加到配置文件的工作区根目录集合中。设置为 `false` 的条目保持不活动状态。                                                                                                                                                                                                                                                                                                                        |
| `[permissions.<name>.filesystem]`                                 | 表                      | 无                    | 将文件系统路径映射到访问值或限定的子路径映射。缺失或空的文件系统表会保持文件系统访问受限，并发出启动警告。                                                                                                                                                                                                                                                               |
| `permissions.<name>.filesystem.glob_scan_max_depth`               | 数字                     | 无                    | 在 Codex 于沙箱启动前对匹配项进行快照时，限制 Linux、WSL 和原生 Windows 上的拒绝读取通配符展开。较大的值会增加启动扫描的工作量。当无界的 `**` 模式需要有界的预展开时，请使用至少为 `1` 的值。                                                                                                                                                              |
| `[permissions.<name>.filesystem]."<path>"`                        | `read`、`write` 或 `deny` | 无                    | 为受支持的路径授予直接访问权限。`deny` 拒绝访问，并且优先于同等具体程度的 `write` 或 `read` 条目。Codex 会拒绝活动运行时无法强制执行的直接写入规则。                                                                                                                                                                                                                            |
| `[permissions.<name>.filesystem."<path>"]."<subpath>"`            | `read`、`write` 或 `deny` | 无                    | 授予对 `<path>` 的子代的访问权限。基础路径请使用 `.`。其他子路径必须是相对子代，并且不能包含 `.` 或 `..` 组件。                                                                                                                                                                                                                                                                  |
| `[permissions.<name>.network]`                                    | 表                      | 无                    | 为配置文件配置网络沙盒代理和沙盒网络策略。                                                                                                                                                                                                                                                                                                                                          |
| `permissions.<name>.network.enabled`                              | 布尔值                    | `false`                 | 为配置文件中的沙盒化命令启用网络访问。这会更改沙盒网络策略；它本身不会启动网络代理。                                                                                                                                                                                                                                                                         |
| `[permissions.<name>.network.domains]`                            | 表                      | 无                    | 将主机模式映射到 `allow` 或 `deny`。如果没有 `allow` 条目，域名请求将被阻止。拒绝条目优先于允许条目。                                                                                                                                                                                                                                                                                   |
| `permissions.<name>.network.domains."<pattern>"`                  | `allow` 或 `deny`          | 无                    | 支持精确主机，`*.example.com` 用于子域，`**.example.com` 用于顶级域及子域，以及 `*` 作为仅允许的全局通配符。主机模式会通过修剪、转换为小写、去除末尾点以及去除简单端口或方括号来进行标准化。                                                                                                                                                           |
| `[permissions.<name>.network.unix_sockets]`                       | 表                      | 无                    | 映射 Unix 套接字允许列表覆盖。仅用于本地集成，例如 Docker。                                                                                                                                                                                                                                                                                                                                         |
| `permissions.<name>.network.unix_sockets."<path>"`                | `allow` 或 `deny`          | 无                    | 使用 `allow` 将绝对 Unix 套接字路径添加到有效的允许列表中，或者使用 `deny` 拒绝它。被拒绝的条目将从有效的允许列表中省略。                                                                                                                                                                                                                                                                |
| `permissions.<name>.network.proxy_url`                            | URL 字符串                 | `http://127.0.0.1:3128` | 用于 `HTTP_PROXY`、`HTTPS_PROXY`、websocket 代理变量及相关工具代理环境变量的 HTTP 代理监听器。                                                                                                                                                                                                                                                                                            |
| `permissions.<name>.network.enable_socks5`                        | 布尔值                    | `true`                  | 启用用于 `ALL_PROXY` 和 FTP 代理变量的 SOCKS5 监听器。                                                                                                                                                                                                                                                                                                                                                     |
| `permissions.<name>.network.socks_url`                            | URL 字符串                 | `http://127.0.0.1:8081` | SOCKS5 监听器地址。                                                                                                                                                                                                                                                                                                                                                                                                      |
| `permissions.<name>.network.enable_socks5_udp`                    | 布尔值                    | `true`                  | 在启用 SOCKS5 监听器时启用 SOCKS5 UDP 支持。                                                                                                                                                                                                                                                                                                                                                               |
| `permissions.<name>.network.allow_upstream_proxy`                 | 布尔值                    | `true`                  | 允许网络沙盒代理在处理出站请求时遵守上游 `HTTP(S)_PROXY` 和 `ALL_PROXY` 设置。                                                                                                                                                                                                                                                                                                          |
| `permissions.<name>.network.allow_local_binding`                  | 布尔值                    | `false`                 | 在 `true` 时禁用本地/私有网络防护。当 `false` 时，必须将确切的本地字面量（例如 `localhost` 或 `127.0.0.1`）显式加入允许列表，并且解析为本地或私有 IP 的主机名仍将保持被阻止状态。                                                                                                                                                                                                |
| `permissions.<name>.network.dangerously_allow_non_loopback_proxy` | 布尔值                    | `false`                 | 允许代理监听器绑定非环回地址。对于普通的本地开发，请保持未设置状态。                                                                                                                                                                                                                                                                                                                            |
| `permissions.<name>.network.dangerously_allow_all_unix_sockets`   | 布尔型                    | `false`                 | 在支持 Unix 套接字代理的情况下绕过 Unix 套接字白名单。这是一个宽泛的本地逃生舱。                                                                                                                                                                                                                                               |

## 文件系统权限

文件系统条目使用 `read`、`write` 或 `deny`：

| 访问权限  | 含义                                                                                                                           |
| ------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `read`  | 允许命令读取文件并列出该路径下的目录。命令不能在此处创建、修改、重命名或删除文件。 |
| `write` | 允许命令读取和修改该路径下的文件，包括在操作系统允许的情况下创建、重命名和删除文件。  |
| `deny`  | 拒绝该路径下的读取和写入操作。使用它从更宽泛的 `read` 或 `write` 授权中划分出被拒绝的子路径。         |

更具体的条目会覆盖更宽泛的条目。当两个条目指向
同一路径时，`deny` 优先于 `write`，并且 `write` 优先于
`read`。

这种优先级允许配置文件首先描述一个宽泛的工作区域，然后划分出
应该保持不可读的文件或目录：

```toml
[permissions.project-edit.filesystem]
":minimal" = "read"

[permissions.project-edit.filesystem.":workspace_roots"]
"." = "write"
".devcontainer" = "read"
"**/*.env" = "deny"
```

在此示例中，工作区根目录保持可写，`.devcontainer/` 保持
可读而不可写，并且匹配的环境变量文件对沙盒化的
命令保持不可用。

更具体的路径也可以在更宽泛的拒绝范围内重新打开一个更窄的子树：

```toml
[permissions.project-edit.filesystem]
"~/Documents" = "deny"
"~/Documents/codex" = "write"
```

支持的路径形式：

| 路径               | 含义                                                                                     | 作用域子路径 |
| ------------------ | ------------------------------------------------------------------------------------------- | --------------- |
| `:root`            | 文件系统根目录                                                                         | `.` 仅限        |
| `:minimal`         | 常用工具所需的平台和运行时路径                                           | `.` 仅限        |
| `:workspace_roots` | 当前会话的工作区根目录加上任何已启用的配置文件定义的工作区根目录      | 是             |
| `:tmpdir`          | `$TMPDIR` 的位置（如果可用）                                               | `.` 仅限        |
| `:slash_tmp`       | `/tmp` 文件夹（如果存在）                                                             | `.` 仅限        |
| `/absolute/path`   | 平台绝对路径，例如 macOS 上的 `/path`/Linux/WSL 或原生 Windows 上的 `C:\path` | 是             |
| `~/path`           | 当前用户主目录下的路径                                              | 是             |

在原生 Windows 上，相对于主目录的路径也可以使用反斜杠，例如
`~\work`。

仅在配置文件确实需要宽泛的读取覆盖范围时才使用 `:root`：

```toml
[permissions.audit.filesystem]
":root" = "read"
```

使用 `:workspace_roots` 下的嵌套条目来限制对工作区根目录的访问
相对子路径：

```toml
[permissions.project-edit.filesystem.":workspace_roots"]
"." = "write"          # each workspace root
"docs" = "read"        # each workspace-root docs directory
"generated" = "deny"   # each workspace-root generated directory
```

嵌套的子路径必须保留在其工作区根目录内。诸如以下的父级遍历
`../other-repo` 会被拒绝。

### 拒绝具有确切路径或通配符的读取

将 `deny` 用于 Codex 不应读取的文件或子树，即使更广泛的
配置文件规则授予了附近的访问权限。确切路径适用于稳定位置
（例如 `~/.ssh`）。当配置文件需要覆盖
一系列确切位置在不同代码库中有所不同的敏感文件时，通配符模式效果更好。

当通配符位于 `:workspace_roots` 下时，Codex 会将其解释为相对于每个
有效工作区根目录。例如：

```toml
[permissions.project-edit.filesystem.":workspace_roots"]
"**/*.env" = "deny"
```

此规则拒绝读取在每个运行时或
配置文件定义的工作区根目录下找到的匹配 `.env` 文件。当您希望保留正常的
工作区写入，同时保持环境文件、生成的密钥或类似的
携带凭据的文件不可读时使用它。

`deny` 通配符模式作为拒绝读取规则受到支持。`read` 或 `write` 通配符
在 Linux、WSL 和原生 Windows 沙盒上的可移植性较差，因此尽可能首选确切
路径或子树规则（例如 `"docs/**" = "read"`）。

在 Linux、WSL 和原生 Windows 上，无界的 `**` 拒绝读取模式可能需要
在沙盒启动之前进行有界的预扩展。当您
使用诸如 `"**/*.env" = "deny"` 之类的无界模式时，请设置 `glob_scan_max_depth`：

```toml
[permissions.project-edit.filesystem]
glob_scan_max_depth = 3

[permissions.project-edit.filesystem.":workspace_roots"]
"**/*.env" = "deny"
```

`glob_scan_max_depth` 必须至少为 `1`。更高的值会在
沙盒启动之前扫描得更深，这会增加 Linux、WSL 和原生 Windows 上的启动工作。
如果您不想使用有界扩展，请枚举明确的深度，例如
`*.env`、`*/*.env` 和 `*/*/*.env`。

当相同的规则应应用于
多个当前会话根目录时，将可重用的工作区根目录添加到配置文件中：

```toml
[permissions.project-edit.workspace_roots]
"~/code/app" = true
"~/code/shared-lib" = true
```

当此配置文件处于活动状态时，Codex 会将 `:workspace_roots` 规则应用于
当前会话的运行时工作区根目录以及每个启用的配置文件定义的
工作区根目录。

在原生 Windows 上，支持将驱动器号路径（例如 `D:\work`）和 UNC 路径（例如
`\\server\share`）作为绝对路径。

## 网络权限

设置 `enabled = true` 以允许所选配置文件的网络访问：

```toml
[permissions.project-edit.network]
enabled = true
```

当启用网络访问时，Codex 默认使用完整的网络行为。
大多数配置文件还应定义域规则：

```toml
[permissions.project-edit.network.domains]
"example.com" = "allow"      # exact host
"*.example.com" = "allow"    # subdomains only
"**.example.com" = "allow"   # apex and subdomains
"ads.example.com" = "deny"   # deny wins over allow
```

网络沙盒代理默认绑定到本地侦听器：

```toml
[permissions.project-edit.network]
enabled = true
proxy_url = "http://127.0.0.1:3128"
enable_socks5 = true
socks_url = "http://127.0.0.1:8081"
enable_socks5_udp = true
```

除非您正在与
特定的运行时集成，否则将这些侦听器设置保留为默认值。`dangerously_*` 网络键是
针对特殊环境的应急手段，不应用于普通的本地开发。

### 本地和私有网络

Codex 默认应用本地/私有网络防护，作为针对 DNS
重绑定和意外访问本地服务的防御。要有意允许
字面本地目标，请将确切的主机或 IP 字面值加入白名单：

```toml
[permissions.project-edit.network.domains]
"localhost" = "allow"
"127.0.0.1" = "allow"
```

仅当配置文件必须访问已加入白名单的
解析为本地或私有地址的主机名时，才设置 `allow_local_binding = true`：

```toml
[permissions.project-edit.network]
enabled = true
allow_local_binding = true

[permissions.project-edit.network.domains]
"localhost" = "allow"
```

### Unix 套接字

Unix 套接字代理是 Docker 等工具的本地应急手段。请谨慎
使用它：

```toml
[permissions.project-edit.network.unix_sockets]
"/var/run/docker.sock" = "allow"
"/tmp/old.sock" = "deny"
```

使用 `deny` 拒绝套接字路径，包括继承的允许条目。被拒绝的
套接字路径将从有效白名单中省略。

当启用 Unix 套接字时，请将代理侦听器绑定到环回地址。

## 从较旧的沙盒设置迁移

权限配置文件取代了较旧的 `sandbox_mode` 和
`sandbox_workspace_write` 的组合，当您希望使用一个可重用的配置文件来同时描述
文件系统和网络行为时。请在会话中使用其中一种系统，而不是
同时使用两者。

建议的起点：

- 对于只读工作流，使用内置的 `:read-only` 配置文件，或者定义一个
  仅在需要的地方具有读取访问权限的自定义配置文件。
- 对于工作区编辑，使用内置的 `:workspace` 配置文件，或者定义一个
  通过 `:workspace_roots` 进行写入并且仅添加工作流所需的额外
  临时或缓存路径的自定义配置文件。
- 对于不受限制的本地执行，仅当您
  有意需要最广泛的本地访问模型时才使用 `:danger-full-access`。

配置文件描述了会话的本地默认姿态。组织管理的
要求仍然可以添加用户配置不应
放宽的限制。请参阅 [托管配置](https://learn.chatgpt.com/docs/enterprise/managed-configuration)
以了解管理员强制执行的文件系统和网络约束。

## 范围与强制执行

权限配置文件定义了本地沙盒命令
执行的边界。请将它们与批准策略以及
连接器、MCP 服务器、内置浏览器、Computer Use 和 Codex 云的单独控件结合使用。

### 配置文件控制的内容

- **本地命令执行：** 权限配置文件管理在您的
  机器上运行的沙盒命令。连接器、MCP 服务器、浏览器或
  计算机使用界面、Codex 云环境设置以及批准的
  权限提升使用它们各自的控件。
- **文件系统写入：** 具有写入权限的配置文件可以创建持久性更改。
  请将写入脚本、构建步骤、包管理器钩子、shell 启动
  文件和共享目录的操作视为敏感操作，因为后续的工具或用户可以
  在原始沙盒上下文之外执行这些文件。
- **出站目的地：** 网络域名规则限制了沙盒
  命令流量可以通过网络代理到达的位置。它们不能确定
  允许的目的地是否可信，并且通配符允许规则保持
  宽泛。
- **本地服务：** 默认情况下，本地和私有网络目标会被阻止。
  将 `localhost`、私有 IP、Unix 套接字加入白名单，或设置
  `allow_local_binding = true` 将明确开启对本地服务的访问。

### 强制执行的工作原理

- 在 macOS 上，Codex 使用 Seatbelt 沙盒配置文件。如果所选策略无法
  通过平台沙盒强制执行，Codex 将拒绝运行该命令，而不是
  在无沙盒的情况下静默运行它。
- 在 Linux 和 WSL 上，Codex 使用 [bubblewrap](https://github.com/containers/bubblewrap)
  和 [seccomp](https://www.kernel.org/doc/html/latest/userspace-api/seccomp_filter.html)，
  并提供 Landlock 用于兼容性回退路径。最强的
  执行路径取决于用户命名空间和内核支持；受限的
  容器宿主机可能会强制使用兼容性路径，而未支持的拆分策略
  将被拒绝。
- 在原生 Windows 上，[`elevated` 沙盒](https://learn.chatgpt.com/docs/windows/windows-sandbox#windows-sandbox)
  是最强的，因为它可以使用专用的较低权限沙盒用户、
  文件系统权限边界和防火墙规则。`unelevated`
  沙盒是一种回退方案，其网络隔离较弱，并且无法强制执行
  每一个拆分的读/写分配，因此未支持的策略会被拒绝。当您需要
  Linux 沙盒模型时，请使用 WSL。

### 操作指南

选择仍然能够完成任务的最严格配置文件，特别是在您
授予写入或出站网络访问权限时。保持批准策略、机密
处理和允许规则与该访问级别保持一致。

## 常见配置文件

### 具有网络白名单的只读模式

```toml
default_permissions = "readonly-net"

[permissions.readonly-net.filesystem]
":minimal" = "read"

[permissions.readonly-net.filesystem.":workspace_roots"]
"." = "read"

[permissions.readonly-net.network]
enabled = true

[permissions.readonly-net.network.domains]
"api.openai.com" = "allow"
```

### 限制于工作区的文件访问

这是一个权限配置文件的示例，它将使您的 Codex 工作区文件夹可写，同时拒绝读取文件系统的其余部分（具有有限的例外情况，由 `:minimal` 决定）。

```toml
default_permissions = "workspace-only"

[permissions.workspace-only]
# By extending the :workspace profile, you get Codex's safeguards to ensure

# subfolders such as .codex/ and .git/ within a workspace root are read-only

# while the rest of the folder is writable.

extends = ":workspace"

[permissions.workspace-only.filesystem]
# By default, deny read access to all files on disk.

":root" = "deny"

# Though in practice, a software agent needs to be able to read folders that

# contain common tools, such as `/usr/bin`, to get work done, so grant access

# to a "minimal" set of files and folders, as determined by Codex.

":minimal" = "read"

# By extending the :workspace profile, :tmpdir and :slash_tmp are "write" by

# default, though you can deny access to them altogether, if desired.

":tmpdir" = "deny"
":slash_tmp" = "deny"
```

### 无网络的工作区写入

```toml
default_permissions = "project-edit"

[permissions.project-edit.filesystem]
":minimal" = "read"

[permissions.project-edit.filesystem.":workspace_roots"]
"." = "write"

[permissions.project-edit.network]
enabled = false
```

### 具有公共 Web 访问权限的工作区写入

```toml
default_permissions = "workspace-net"

[permissions.workspace-net.filesystem]
":minimal" = "read"

[permissions.workspace-net.filesystem.":workspace_roots"]
"." = "write"

[permissions.workspace-net.network]
enabled = true

[permissions.workspace-net.network.domains]
"*" = "allow"
```

仅当您打算允许公共网络
访问时，才使用全局 `"*"` 允许规则。拒绝规则可以收紧宽泛的允许列表。

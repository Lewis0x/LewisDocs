---
title: 对代码更改进行安全审查
source_id: codex/security/plugin/code-changes
product: codex
lang: zh-CN
canonical_url: https://developers.openai.com/codex/security/plugin/code-changes
owner: OpenAI
content_sha256: 9628c60f026588ff8e69bf3c20370103cb3d5d7f71aa3ad09c1947ccaf1d0208
translation_of: codex/security/plugin/code-changes
translation_model: glm-5.2
ai_translated: true
---
本页由 AI 翻译，可能存在误差；如有歧义，以英文原文为准。

[Official source](https://developers.openai.com/codex/security/plugin/code-changes)

Content owner: OpenAI

# 对代码更改进行安全审查

> 有关完整的文档索引，请参见 [llms.txt](https://learn.chatgpt.com/llms.txt)。通过在页面 URL 后附加 `.md` 可获取文档页面的 Markdown 版本。

运行安全更改审查，以在一个基于 Git 的变更集中查找回归。
Codex 会审查每个已更改的源码类文件及其直接为其提供支持的代码。
它不会将审查扩展为完整的仓库审计。

要扫描整个仓库而不是特定的更改，请参见[运行安全
扫描](https://learn.chatgpt.com/docs/security/plugin/scans)。

## 运行手动审查

对于未提交的更改，询问 Codex：

```text
Use $codex-security:security-diff-scan to review my current uncommitted changes for security regressions.
```

对于提交或分支范围，在需要时指定两个修订版本：

```text
Use $codex-security:security-diff-scan to review the changes from origin/main to HEAD for security regressions. Focus on authentication, authorization, input handling, filesystem access, network requests, and secrets.
```

当拉取请求的基准和头部修订版本在本地检出中可用时，您也可以直接指定拉取请求。

## 在设置中确认更改

<WorkflowSteps>

1. 确认 **Scan type** 为 `Changes`。
2. 确认检出的 **Codebase**、**Current branch** 和 **Last commit**。
3. 在 **Changes to review** 下，选择：
   - `Uncommitted changes` 用于当前工作树。
   - 最新提交用于单次提交审查。
   - 基准和头部修订版本用于分支或拉取请求范围。
4. 确认摘要描述了您打算审查的更改。
5. 选择 **Start scan**。

</WorkflowSteps>

Codex 不会检出另一个分支或切换所选的工作树。如果
请求的修订版本在本地不可用，请在审查前获取它，或者
提供本地可用的基准和头部。

## 处理发现结果

在您审查结果之后，[修复并验证已接受的
发现](https://learn.chatgpt.com/docs/security/plugin/fix-findings) 或 [导出和跟踪
发现](https://learn.chatgpt.com/docs/security/plugin/export-findings)。

## 在 CI/CD 中自动化审查

当运行器可以在无需交互的情况下调用 Codex CLI 时，在 CI 中运行 `$codex-security:security-diff-scan`。首先，安装 CLI 和插件，但不
暴露扫描凭据：

```bash
npm install --global @openai/codex
codex plugin add codex-security@openai-curated
```

安装命令使用公共 Codex CLI 插件市场，它可能
提供与托管桌面应用程序目录不同的版本。检查
[插件变更日志](https://learn.chatgpt.com/docs/security/plugin/changelog)，然后再依赖于
CI 中的特定插件版本或功能。

接下来，从您的 CI 密钥存储中提供一个 OpenAI API 密钥作为
`CODEX_SECURITY_API_KEY`。仅为扫描暴露凭据：

```bash
CODEX_API_KEY="$CODEX_SECURITY_API_KEY" codex exec \
  --sandbox workspace-write \
  "Use \$codex-security:security-diff-scan to review changes from $BASE_REVISION to $HEAD_REVISION for security regressions. Do not modify the checkout."
```

可写的沙盒允许扫描创建临时构件。提示词
仍然要求 Codex 保持源码检出不变。

扫描将其输出写入到
`$TMPDIR/codex-security-scans/<repository>/<scan-id>/`：

| 文件                 | 内容                                                                                                                                                    |
| -------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `report.md`          | 指向完整扫描目录的主要可读入口点。                                                                                                |
| `findings/<slug>/`   | 每个可报告发现的一份详细漏洞报告，并在可用时附有支持性的概念验证文件。                                            |
| `hardening/`         | 结构加固组合和支撑建议或图表（当扫描具有可报告的发现时）。                                                  |
| `findings.json`      | 具有稳定标识符、严重性、置信度、源位置和补救措施的发现结果。使用它来创建拉取请求评论或供下游工具使用。 |
| `scan-manifest.json` | 包含已审查目标、修订版本和构件哈希的密封扫描收据。                                                                               |
| `coverage.json`      | 已审查和推迟的表面、排除项以及覆盖完整性。                                                                                      |

[`findings.json` 模式](https://github.com/openai/plugins/blob/main/plugins/codex-security/schemas/findings.schema.json)
定义了完整的结构。该模式包含以下字段：

| 字段                     | 类型   | 描述                                                            |
| ------------------------- | ------ | ---------------------------------------------------------------------- |
| `documentType`            | 字符串 | 将文档标识为 `codex-security.findings`。                  |
| `schemaVersion`           | 字符串 | 标识发现结果的架构版本。                                |
| `scanId`                  | 字符串 | 标识生成发现结果的扫描。                        |
| `findings`                | 数组  | 包含零个或多个发现结果对象。                                 |
| `findings[].findingId`    | 字符串 | 派生自发现结果指纹的稳定发现标识符。        |
| `findings[].occurrenceId` | 字符串 | 标识在特定扫描中此发现结果的出现。          |
| `findings[].ruleId`       | 字符串 | 标识漏洞家族。                                   |
| `findings[].identity`     | 对象 | 包含语义锚点和可选的同级实例标识符。 |
| `findings[].fingerprints` | 对象 | 包含指纹算法和主要指纹。            |
| `findings[].title`        | 字符串 | 提供简短的发现结果标题。                                      |
| `findings[].summary`      | 字符串 | 总结漏洞及其影响。                           |
| `findings[].severity`     | 对象 | 包含严重性级别和可选的评分详情。              |
| `findings[].confidence`   | 对象 | 包含置信度级别和依据。                           |
| `findings[].taxonomy`     | 对象 | 包含漏洞类别和 CWE 标识符。               |
| `findings[].locations`    | 数组  | 列出受影响的文件、行号和位置角色。                |
| `findings[].remediation`  | 字符串 | 描述建议的修复方案。                                         |
| `findings[].provenance`   | 对象 | 标识发现结果的来源。                                  |

例如，此命令为每个发现结果打印一行制表符分隔的数据：

```bash
jq -r '
  .findings[] |
  [.findingId, .severity.level, .confidence.level, .locations[0].path, .locations[0].startLine, .title] |
  @tsv
' findings.json
```

这些示例假定使用受信任的 Linux 运行器，并配置了 Node.js 和 `npm`、Git、Python
3、`jq` 以及提供商的命令行工具。`npm` 全局包前缀
必须是可写的。

选择适用于您的 CI 提供商的示例：

<Tabs
  id="codex-security-ci-examples"
  param="ci"
  defaultTab="github"
  tabs={[
    { id: "github", label: "GitHub Actions" },
    { id: "gitlab", label: "GitLab CI/CD" },
    { id: "azure", label: "Azure Pipelines" },
    { id: "jenkins", label: "Jenkins" },
  ]}
>
  


```yaml
name: Codex Security review

on:
  pull_request:

jobs:
  security-review:
    if: github.event.pull_request.head.repo.full_name == github.repository
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: actions/checkout@v5
        with:
          ref: ${{ github.event.pull_request.head.sha }}
          fetch-depth: 0
          persist-credentials: false

      - name: Install Codex Security
        env:
          CODEX_HOME: ${{ runner.temp }}/codex-home
        run: |
          npm install --global @openai/codex
          codex plugin add codex-security@openai-curated

      - name: Review code changes
        env:
          CODEX_SECURITY_API_KEY: ${{ secrets.CODEX_SECURITY_API_KEY }}
          CODEX_HOME: ${{ runner.temp }}/codex-home
          TMPDIR: ${{ runner.temp }}/codex-security
          BASE_SHA: ${{ github.event.pull_request.base.sha }}
          HEAD_REVISION: ${{ github.event.pull_request.head.sha }}
        run: |
          BASE_REVISION="$(git merge-base "$BASE_SHA" "$HEAD_REVISION")"
          CODEX_API_KEY="$CODEX_SECURITY_API_KEY" codex exec \
            --sandbox workspace-write \
            "Use \$codex-security:security-diff-scan to review changes from $BASE_REVISION to $HEAD_REVISION for security regressions. Do not modify the checkout."

      - name: Comment with findings
        if: always()
        env:
          GH_TOKEN: ${{ github.token }}
          PR_NUMBER: ${{ github.event.pull_request.number }}
        run: |
          findings="$(find "${{ runner.temp }}/codex-security/codex-security-scans" -name findings.json -print -quit 2>/dev/null || true)"
          test -n "$findings" || exit 0
          jq -r '
            "## Codex Security findings",
            "",
            if (.findings | length) == 0 then "No findings reported."
            else .findings[] | "- **\(.severity.level | ascii_upcase)**: \(.title) (`\(.locations[0].path):\(.locations[0].startLine)`)\n  \(.summary)"
            end
          ' "$findings" | gh pr comment "$PR_NUMBER" --body-file -

      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: codex-security-review
          path: ${{ runner.temp }}/codex-security/codex-security-scans
```

  


  


创建已掩码的 `CODEX_SECURITY_API_KEY` 和 `GITLAB_TOKEN` CI/CD 变量。
GitLab 令牌需要 API 访问权限才能创建合并请求注释。

```yaml
codex-security-review:
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event" && $CI_MERGE_REQUEST_SOURCE_PROJECT_ID == $CI_PROJECT_ID'
  variables:
    GIT_DEPTH: "0"
  script:
    - |
      codex_security_api_key="$CODEX_SECURITY_API_KEY"
      unset CODEX_SECURITY_API_KEY GITLAB_TOKEN
      export CODEX_HOME="/tmp/codex-home-$CI_JOB_ID"
      export TMPDIR="/tmp/codex-security-$CI_JOB_ID"
      export BASE_REVISION="$CI_MERGE_REQUEST_DIFF_BASE_SHA"
      export HEAD_REVISION="${CI_MERGE_REQUEST_SOURCE_BRANCH_SHA:-$CI_COMMIT_SHA}"
      npm install --global @openai/codex
      codex plugin add codex-security@openai-curated
      CODEX_API_KEY="$codex_security_api_key" codex exec \
        --sandbox workspace-write \
        "Use \$codex-security:security-diff-scan to review changes from $BASE_REVISION to $HEAD_REVISION for security regressions. Do not modify the checkout."
  after_script:
    - |
      gitlab_token="$GITLAB_TOKEN"
      unset CODEX_SECURITY_API_KEY GITLAB_TOKEN
      scan_root="/tmp/codex-security-$CI_JOB_ID/codex-security-scans"
      findings="$(find "$scan_root" -name findings.json -print -quit 2>/dev/null || true)"
      if [ -n "$findings" ]; then
        jq -r '
          "## Codex Security findings",
          "",
          if (.findings | length) == 0 then "No findings reported."
          else .findings[] | "- **\(.severity.level | ascii_upcase)**: \(.title) (`\(.locations[0].path):\(.locations[0].startLine)`)\n  \(.summary)"
          end
        ' "$findings" > codex-security-comment.md
        curl --fail --request POST \
          --header "PRIVATE-TOKEN: $gitlab_token" \
          --form "body=<codex-security-comment.md" \
          "$CI_API_V4_URL/projects/$CI_PROJECT_ID/merge_requests/$CI_MERGE_REQUEST_IID/notes"
      fi
      if [ -d "$scan_root" ]; then
        tar -czf codex-security-artifacts.tar.gz -C "$scan_root" .
      fi
  artifacts:
    when: always
    paths:
      - codex-security-artifacts.tar.gz
```

  


  


```yaml
trigger: none

pool:
  vmImage: ubuntu-latest

steps:
  - checkout: self
    fetchDepth: 0

  - bash: |
      set -euo pipefail
      export CODEX_HOME="$AGENT_TEMPDIRECTORY/codex-home"
      npm install --global @openai/codex
      codex plugin add codex-security@openai-curated
    displayName: Install Codex Security

  - bash: |
      set -euo pipefail
      export CODEX_HOME="$AGENT_TEMPDIRECTORY/codex-home"
      export TMPDIR="$AGENT_TEMPDIRECTORY/codex-security"
      export HEAD_REVISION="$SYSTEM_PULLREQUEST_SOURCECOMMITID"
      export BASE_REVISION="$(git merge-base HEAD^1 "$HEAD_REVISION")"
      CODEX_API_KEY="$CODEX_SECURITY_API_KEY" codex exec \
        --sandbox workspace-write \
        "Use \$codex-security:security-diff-scan to review changes from $BASE_REVISION to $HEAD_REVISION for security regressions. Do not modify the checkout."
    displayName: Review code changes
    condition: and(succeeded(), ne(variables['System.PullRequest.IsFork'], 'True'))
    env:
      CODEX_SECURITY_API_KEY: $(CODEX_SECURITY_API_KEY)

  - publish: $(Agent.TempDirectory)/codex-security/codex-security-scans
    artifact: codex-security-review
    condition: always()
```

对于 Azure Repos，请配置 **Build validation** 分支策略，以便在
拉取请求上运行流水线。

  


  


```groovy
pipeline {
  agent { label 'linux' }
  stages {
    stage('Codex Security review') {
      when {
        allOf {
          changeRequest()
          expression { !env.CHANGE_FORK?.trim() }
        }
      }
      steps {
        sh '''#!/usr/bin/env bash
          set -euo pipefail
          export CODEX_HOME="/tmp/codex-home-$BUILD_TAG"
          export TMPDIR="/tmp/codex-security-$BUILD_TAG"
          mkdir -p "$TMPDIR"
          git fetch --no-tags origin "$CHANGE_TARGET"
          target="$(git rev-parse FETCH_HEAD)"
          git fetch --no-tags origin "$CHANGE_BRANCH"
          git rev-parse FETCH_HEAD > "$TMPDIR/head"
          git merge-base "$target" "$(cat "$TMPDIR/head")" > "$TMPDIR/base"
          npm install --global @openai/codex
          codex plugin add codex-security@openai-curated
        '''
        withCredentials([string(credentialsId: 'codex-security-api-key', variable: 'CODEX_SECURITY_API_KEY')]) {
          sh '''#!/usr/bin/env bash
            set +x
            set -euo pipefail
            export CODEX_HOME="/tmp/codex-home-$BUILD_TAG"
            export TMPDIR="/tmp/codex-security-$BUILD_TAG"
            export HEAD_REVISION="$(cat "$TMPDIR/head")"
            export BASE_REVISION="$(cat "$TMPDIR/base")"
            CODEX_API_KEY="$CODEX_SECURITY_API_KEY" codex exec \
              --sandbox workspace-write \
              "Use \$codex-security:security-diff-scan to review changes from $BASE_REVISION to $HEAD_REVISION for security regressions. Do not modify the checkout."
          '''
        }
      }
      post {
        always {
          sh '''#!/usr/bin/env bash
            set -euo pipefail
            scan_root="/tmp/codex-security-$BUILD_TAG/codex-security-scans"
            if [ -d "$scan_root" ]; then
              tar -czf codex-security-artifacts.tar.gz -C "$scan_root" .
            fi
          '''
          archiveArtifacts artifacts: 'codex-security-artifacts.tar.gz', allowEmptyArchive: true
        }
      }
    }
  }
}
```

  

</Tabs>

这些示例跳过来自复刻仓库的拉取请求。仅从受保护的流水线定义中运行凭据作业，且仅针对受信任使用扫描
凭据的贡献者。归档 `codex-security-scans` 以将结构化的发现结果、
清单、覆盖率构件、`report.md` 及其链接的 `findings/` 和
`hardening/` 输出保留在一起。从建议性结果开始，在将作业设为必选检查之前审查
覆盖率
和运行时间。

有关 API 密钥处理和沙盒控制，请参阅[非交互
模式](https://learn.chatgpt.com/docs/non-interactive-mode)。如果您的组织允许使用 [Codex
GitHub Action](https://learn.chatgpt.com/docs/github-action)，它可以在运行时安装 CLI，但是
您仍必须先安装该插件，并将该操作的 `codex-home`
输入指向同一个 `CODEX_HOME`。

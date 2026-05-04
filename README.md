# 通用 CAD 平台 API 设计哲学 · 文档站点

11 份研究文档（约 17.4 万字）的 VitePress 静态站点。

## 项目元文档

| 想了解 | 看这里 |
|---|---|
| 为什么要这个站点、要做什么、不做什么 | [project-docs/01-需求文档](./project-docs/01-requirements.md) |
| 技术选型、架构决策、ADR 记录 | [project-docs/02-方案文档](./project-docs/02-design.md) |
| 如何开发、调试、升级 VitePress、反爬运维 SOP | [project-docs/03-开发文档](./project-docs/03-development.md) |
| 站点访问者如何用搜索、跳转、深色模式等 | [project-docs/04-使用文档](./project-docs/04-usage.md) |
| 内容版权与 AI 训练限制条款 | [LICENSE](./LICENSE) |
| 命中泄漏后的 DMCA 流程 | [project-docs/dmca-template.md](./project-docs/dmca-template.md) |


## 在本地查看

```bash
# 一次性准备：把源文件转换为站点内容
npm install
npm run prepare-content

# 启动开发服务器
npm run dev
# 浏览器打开 http://localhost:5173
```

## 内容更新流程

修改 `source/` 下任何 V4 文档后：

```bash
npm run prepare-content   # 重新导入并改写回链
npm run dev               # 本地预览
git add . && git commit -m "update content" && git push
# CI 自动重新构建并发布
```

## 部署

### 选项 A（主推）：Cloudflare Pages

1. 在 Cloudflare 拿到 API Token（`Cloudflare Pages › Edit` 权限）+ Account ID
2. 仓库 Settings → Secrets and variables → Actions 加：
   - `CLOUDFLARE_API_TOKEN`
   - `CLOUDFLARE_ACCOUNT_ID`
3. 推到 `main`，CI（`.github/workflows/cloudflare-pages.yml`）自动构建并部署
4. 默认 URL：`https://lewisdocs.pages.dev/`（Cloudflare 自动小写项目名）
5. 首次部署成功后，到 Cloudflare 面板按 [03-development.md §12](./project-docs/03-development.md) 启用 WAF 规则、Bot Fight Mode、Rate Limiting

### 选项 B（已停用，可回退）：GitHub Pages

`.github/workflows/pages.yml` 加了 `if: false`。回退步骤：

1. 把 `if: false` 改成 `if: true`
2. 把 `docs/.vitepress/config.ts` 的 `base` 改回 `'/LewisDocs/'`
3. 在 `cloudflare-pages.yml` 加 `if: false` 关掉
4. URL 变回 `https://<user>.github.io/<repo>/`

### 选项 C：GitLab Pages

1. 推到 GitLab 默认分支
2. CI 见 `.gitlab-ci.yml`
3. 访问 `https://<group>.gitlab.io/<project>/`

### 选项 C：内网 Nginx

```bash
npm run prepare-content
npm run build
rsync -avz docs/.vitepress/dist/ user@server:/var/www/cad-api/

# Nginx
server {
    listen 80;
    server_name docs.your-company.cn;
    root /var/www/cad-api;
    index index.html;
    location / {
        try_files $uri $uri.html $uri/ =404;
    }
}
```

### 选项 D：对象存储（OSS / COS / MinIO）

```bash
npm run prepare-content && npm run build
# 上传 docs/.vitepress/dist/ 到对象存储 → 启用静态网站托管
```

## 子路径部署

如果部署到子路径如 `/cad-api/`，把 `.vitepress/config.ts` 中的 `base` 改为 `'/cad-api/'`。

## 项目结构

```
cad-api-docs/
├── docs/
│   ├── .vitepress/         # VitePress 配置与主题
│   ├── index.md            # 站点内容（由 source/ 自动生成，不要直接改）
│   ├── theory.md
│   ├── comparison.md
│   └── platforms/*.md
├── source/                 # V4 原始文档
├── scripts/
│   ├── import_docs.py      # source/ → docs/ + 加 frontmatter
│   └── rewrite_links.py    # [回链：...] → 真链接
├── project-docs/           # 工程的元文档（需求 / 方案 / 开发 / 使用）
├── .github/workflows/      # GitHub Pages 配置（主推）
└── .gitlab-ci.yml          # GitLab Pages 配置（备选）
```

## 团队成员使用建议

- **首次访问**：从首页（导读）开始，按"阅读路径"选择适合自己的入口
- **搜索**：右上角搜索框支持中文全文搜索（`Ctrl+K` / `⌘+K` 快速调出）
- **跨文档跳转**：所有 `[回链：...]` 都是可点击链接
- **深色模式**：右上角主题切换按钮
- **书签**：每个章节都有独立 URL，可直接发给同事

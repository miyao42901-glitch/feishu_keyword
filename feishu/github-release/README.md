# GitHub 飞书插件发布仓说明

GitHub 空仓目录结构（与常见飞书插件仓一致）：

```text
<repo>/
  dist/           # npm run build 产物（勿手改）
    assets/
    index.html
    favicon.svg
    jzl_icon.png
  package.json    # 版本号，prepare-github-release 会同步
  README.md
```

## 首次

```powershell
cd <仓库根>
git clone <GitHub空仓URL> public/feishu
```

## 每次发测试包

构建前确保仓根 `.env` 含 `VITE_YDDM_API_BASE`、`VITE_SYNC_API_BASE`（见 `.env.test` / `.env.master`）。  
插件页面在飞书 CDN（`ext.baseopendev.com`）加载时，**不能**用相对路径 `/yddm-api`，否则会打到对象存储并返回 412。

```powershell
# 仓库根
cp .env.test .env
.\release.bat

# 或
cd feishu
npm run build:github:test
cd ..\public\feishu
git add dist package.json
git commit -m "2.0.x"
git push
```

Docker / 测试域 Nginx 仍使用扁平目录时，请用 `npm run build:public:test`（同步到 `public/feishu` 根目录，非 `dist/`）。

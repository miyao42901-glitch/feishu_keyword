# 飞书关键词监控管理后台 (`admin/`)

独立 **Vite + Vue 3 + TypeScript + Element Plus**。生产部署在站点路径 **`/admin`**（Traefik `StripPrefix` 后由 nginx 提供静态资源）；API 前缀为 **`/api`**。

- API 基址由仓根 `.env` 的 `VITE_ADMIN_API_ORIGIN` 注入（`vite.config.ts` 的 `envDir` 指向仓库根）；测试/正式见 `.env.test` / `.env.master`，打包用仓根 `build-public-*.bat`。
- 开发时 Vite 将 `/api` 代理到本机 `http://127.0.0.1:8000`，避免浏览器跨域。

## 本地运行

```bash
cd admin
npm ci
npm run dev:local    # 本机 127.0.0.1:8000
npm run dev:lan      # 局域网：仓根 cp .env.test .env 与 cp .env.local.example .env.local
```

浏览器打开 `http://localhost:5101/admin/`（注意末尾斜杠与 `base: '/admin/'` 一致）。

若需指向线上 API 调试（不经本地代理），可用：

```bash
npm run dev
```

## 构建

```bash
npm run build
```

产物在 `admin/dist/`。

发布到仓库内 Docker 挂载目录（测试环境，API 域名为 `test-fskw.tbpf.com`）：

```bash
npm run build:public:test
```

会将 `dist/` 同步到仓根 **`public/admin/`**（与 CI rsync 目标一致）。正式环境用 `build:public:prod`。

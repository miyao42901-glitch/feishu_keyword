# 飞书关键词监控管理后台 (`admin/`)

独立 **Vite + Vue 3 + TypeScript + Element Plus**。生产部署在站点路径 **`/admin`**（Traefik `StripPrefix` 后由 nginx 提供静态资源）；API 前缀为 **`/api`**。

- 默认生产 API 基址：`https://feishukeyword.tbpf.com`（见 `src/config/adminApiOrigin.ts`，可用 `VITE_ADMIN_API_ORIGIN` 覆盖）。
- 开发时 Vite 将 `/api` 代理到本机 `http://127.0.0.1:8000`，避免浏览器跨域。

## 本地运行

```bash
cd admin
npm ci
npm run dev:local
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

发布到仓库内 Docker 挂载目录：

```bash
npm run build:public
```

会将 `dist/` 同步到仓根 **`public/admin/`**（与 CI rsync 目标一致）。

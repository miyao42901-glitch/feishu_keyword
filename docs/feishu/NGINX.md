# Nginx 反向代理（消除跨域）

## 目标

浏览器只访问 **一个入口**（如 `http://192.168.1.24`），由 Nginx 转发：

| 路径 | 上游 | 说明 |
|------|------|------|
| `/api/v1/` | `192.168.1.11:8765` | 采集 / 异步任务 |
| `/api/` | `127.0.0.1:8000` | 飞书任务配置（`server/`） |
| `/yddm-api/` | YDDM 上游（示例 `192.168.1.11:8001`） | YDDM 登录、计费 |
| `/` | `5173`（开发）或 `feishu/dist`（生产） | 前端 |

## 配置示例

仓库内示例：`deploy/nginx/feishu-keyword.conf.example`。

```powershell
# 复制并修改 upstream / server_name 后 reload nginx
nginx -t
nginx -s reload
```

## 前端环境变量（`feishu/.env`）

**不要**再写 `VITE_SYNC_API_BASE=http://192.168.1.11:8765`（会跨域）。

```env
# 与 Nginx 对外地址一致（不含 /api）
VITE_API_BASE_URL=http://192.168.1.24

# 采集 API：不配置，请求走同源 /api/v1/...
# （留空即可，见 sync-api-common.ts）

# YDDM 登录/计费：走同源 /yddm-api
# VITE_YDDM_API_BASE=/yddm-api
```

修改 `.env` 后需 **`npm run dev` 重启**；生产需重新 **`npm run build`**。

## 开发两种用法

1. **仅 Vite**（默认）：访问 `http://IP:5173`，Vite 内置代理，无需 Nginx。
2. **Nginx + Vite**：访问 `http://IP`（80），Nginx 把 `/` 转到 `5173`，`/api/v1` 转到 `8765`。

## 生产静态部署（`feishu-web` / `fskw-feishu.tbpf.com`）

Docker 使用 `deploy/feishu-static/default.conf`：除静态资源外，**同源反代** `/api/v1/`、`/api/`、`/yddm-api/`，浏览器无需跨域。

```powershell
cd feishu
npm run build:public:prod   # VITE_API_BASE_URL=https://fskw-feishu.tbpf.com
```

打包脚本请使用 **飞书前端域名**（`fskw-feishu.tbpf.com` / `test-fskw-feishu.tbpf.com`），**不要**写 `fskw.tbpf.com`（API 域），否则 `GET /api/v1/async/tasks` 会跨域。

栈内需同时启动 **`api`** 与 **`worker`（含 sync-api）** profile，否则 `/api/v1` 反代会 502。

自建 Nginx 可参考 `deploy/feishu-static/default.conf`；勿再单独写 `VITE_SYNC_API_BASE` 指向 `8765`。

## 常见问题

- **仍跨域 / CORS on `fskw.tbpf.com/api/v1`**：多为前端打包把 `VITE_API_BASE_URL` 设成 API 域、页面却在 `fskw-feishu.*` 打开。应改为飞书域打包，或去掉 `VITE_SYNC_API_BASE` 让采集走同源 `/api/v1`。
- **仍跨域**：检查是否仍配置了 `VITE_SYNC_API_BASE` 指向 `8765`；应去掉后重建前端。
- **404 on /api/v1**（无 `Access-Control-Allow-Origin`）：Traefik 未挂上 sync-api（正式域需 `docker compose --profile worker up`），或 `location /api/v1/` 未在 `location /api/` **之前**。
- **OPTIONS 失败**：走飞书静态 Nginx 同源后一般无 CORS；若直连 `fskw.tbpf.com` 且返回 404，浏览器也会报 CORS。

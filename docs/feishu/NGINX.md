# Nginx 反向代理（消除跨域）

## 目标

浏览器只访问 **一个入口**（开发可为 `http://IP:5173` 或 `http://IP`），由 Vite 或 Nginx 转发：

| 路径 | 上游 | 说明 |
|------|------|------|
| `/api/v1/` | `127.0.0.1:8765`（开发）或 `api:8765`（Docker） | 采集 / 异步任务（`server/`） |
| `/yddm-api/` | `https://api.yddm.com` | YDDM 登录、计费 |
| `/` | `5173`（开发）或 `public/feishu`（生产） | 前端 |

生产 **`feishu-web`** 不再反代 `/api/` 到其它端口；业务 API 仅 **`/api/v1/`**。

## 配置示例

仓库内示例：`deploy/nginx/feishu-keyword.conf.example`（自建 Nginx 可参考）。

生产 Docker 使用 [`deploy/feishu-static/default.conf`](../../deploy/feishu-static/default.conf)：`/api/v1/` → `http://api:8765`。

```powershell
# 复制并修改 upstream / server_name 后 reload nginx
nginx -t
nginx -s reload
```

## 前端环境变量（仓根 `.env` / `.env.local`）

Vite `envDir` 指向**仓库根**。本地示例：`cp .env.test .env`，局域网联调可 `cp .env.local.example .env.local` 并改 IP。

**不要**再写 `VITE_SYNC_API_BASE=http://host:8765`（会跨域）；采集走同源 `/api/v1/` 或仓根 `SYNC_PROXY_TARGET`（仅 Vite 开发代理）。

```env
# 开发：Vite 将 /api/v1 代理到本机 API
SYNC_PROXY_TARGET=http://127.0.0.1:8765

# YDDM：生产走同源 /yddm-api；见 .env.test / .env.master 的 YDDM_PROXY_TARGET
```

修改 env 后需 **`npm run dev` 重启**；线上静态由 **CI Runner** 编译打包部署。

## 开发两种用法

1. **仅 Vite**（默认）：访问 `http://IP:5173`，Vite 内置代理 `/api/v1` → `8765`，无需 Nginx。
2. **Nginx + Vite**：访问 `http://IP`（80），Nginx 把 `/` 转到 `5173`，`/api/v1` 转到 `8765`。

后端须已启动：`cd server && python run.py`。

## 生产静态部署（`feishu-web` / `fskw-feishu.tbpf.com`）

Docker 使用 `deploy/feishu-static/default.conf`：静态资源 + 同源反代 **`/api/v1/`**、`/yddm-api/`。

```bash
# 仓根（可选本地预检；CI Runner 会自动 build:public:prod）
cp .env.master .env && cd feishu && npm run build:public:prod
```

打包脚本请使用 **飞书前端域名**（`fskw-feishu.tbpf.com` / `test-fskw-feishu.tbpf.com`），页面在飞书域打开时 API 走同源 `/api/v1`，无需指向 `fskw.tbpf.com`。

栈内需同时启动 **`--profile feishu --profile worker`**（`feishu-web` + `api` + `celery-worker`），否则 `/api/v1` 反代会 502。

Traefik 另将 **`API_PUBLIC_HOST`**（如 `test-fskw.tbpf.com`）的 `/api/v1` 直接路由到 `api` 服务，供外部系统或 curl 探活。

## 常见问题

- **仍跨域**：检查是否仍配置了 `VITE_SYNC_API_BASE` 指向独立 `:8765`；应去掉后重建前端，或确保页面与 API 同源（飞书静态域 + `/api/v1`）。
- **404 on /api/v1**：未启动 `worker` profile（缺少 `api` 容器），或 nginx `location /api/v1/` 配置错误。
- **502**：`api` 未就绪或 Celery/DB/Redis 配置错误；在栈内执行 `docker compose exec feishu-web wget -qO- http://api:8765/api/v1/health` 排查。

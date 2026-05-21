# fskw 部署说明

## 域名

| 环境 | API | Admin | Feishu 静态 |
|------|-----|-------|-------------|
| 测试 | https://fskw-test.tbpf.com | https://fskw-admin-test.tbpf.com | https://fskw-feishu-test.tbpf.com |
| 正式 | https://fskw.tbpf.com | https://fskw-admin.tbpf.com | https://fskw-feishu.tbpf.com |

探活：`GET https://fskw-test.tbpf.com/ci-test`

**测试管理后台**：https://fskw-admin-test.tbpf.com/login — 账号 **`admin`** / 密码 **`Admin123a`**（种子数据，上线前请改密）

## 架构（双后端 + 单 Compose）

| 组件 | 说明 |
|------|------|
| `api` | `server/` FastAPI :8000 — `/ci-test`、`/api/*`、`/api/admin/v1/*` |
| `sync-api` | `python/` FastAPI :8765 — `/api/v1/*`（Traefik 高优先级路由） |
| `celery-worker` | 异步采集 **必须** 常驻 |
| `admin-web` / `feishu-web` | 静态 nginx |

与稿轻松一致：**仓库仅一份** [`docker-compose.yml`](../docker-compose.yml)；测试/正式靠主机目录与 **栈根 `.env`** 区分（`cp -f server/.env .env`）。

```bash
# 测试
cd /docker/fskw-test
cp -f server/.env.test server/.env && chmod 600 server/.env
cp -f server/.env .env && chmod 600 .env
cp -f python/.env.test python/.env 2>/dev/null || true
docker compose --profile admin --profile feishu --profile worker up -d --build

# 正式
cd /docker/fskw
cp -f server/.env.master server/.env && chmod 600 server/.env
cp -f server/.env .env && chmod 600 .env
cp -f python/.env.master python/.env 2>/dev/null || true
docker compose --profile admin --profile feishu --profile worker up -d --build
```

## 环境变量（对齐稿轻松）

| 机制 | 文件 | 用途 |
|------|------|------|
| Compose 插值 | 栈根 `/docker/fskw-test/.env` | `API_PUBLIC_HOST`、`TRAEFIK_*`、`PYTHON_IMAGE` |
| 容器业务 | `server/.env`、`python/.env` | `DATABASE_URL`、`REDIS_*` |

模板：`server/.env.test` / `server/.env.master`、`python/.env.test` / `python/.env.master`（仓内占位符；真实口令仅写远端）。

一键写入远端（从稿轻松测试栈读取 MySQL 口令）：

```bash
bash scripts/remote-setup-env.sh
```

## 数据库与种子

```bash
# 在可连 gqs-mysql 的环境（如 api 容器内）
cd /app && python scripts/init_schema.py
python scripts/seed_demo.py
# python 表：sync-api 启动时 DATABASE_RUN_MIGRATIONS=1 会跑迁移；或执行 python/social_platform/database/schema.sql
```

## GitLab CI

- `test` 分支：自动 `deploy-test`（rsync `server/`、`python/`、`public/*`、`docker-compose.yml`）
- `master`：`deploy-prod` 手动/变更触发
- 本地先 `build-public-test.bat` 并提交 `public/admin`、`public/feishu`

## 验收 curl

```bash
curl -sS https://fskw-test.tbpf.com/ci-test
curl -sS https://fskw-test.tbpf.com/api/v1/health
curl -sS -X POST https://fskw-test.tbpf.com/api/admin/v1/system/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"Admin123a"}'
```

## 本地开发

```bash
cd server && cp .env.example .env && uvicorn app.main:app --reload --port 8000
cd python && cp .env.example .env && python run.py   # :8765
# celery -A social_platform.tasks.celery_app worker -l info -P gevent -c 4
cd admin && npm run dev:local
cd feishu && npm run dev:local
```

推送 test 前：`.\build-public-test.bat` → `git push origin test`

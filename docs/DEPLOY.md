# feishu_keyword 部署说明

## 主机目录

| 环境 | 路径 |
|------|------|
| 测试 | `/docker/feishu_keyword-test` |
| 正式 | `/docker/feishu_keyword` |

从旧名迁移（一次性，在 `121.43.231.225` 上）：

```bash
# 先停旧栈，再改名，避免 compose 项目名冲突
cd /docker/feishu_keyword-test && docker compose --profile admin --profile feishu --profile worker down
cd /docker/feishu_keyword && docker compose --profile admin --profile feishu --profile worker down 2>/dev/null || true
mv /docker/fskw-test /docker/feishu_keyword-test
mv /docker/fskw /docker/feishu_keyword
# 确认 server/.env、python/.env、栈根 .env 仍在；或推送 test 分支让 CI rsync 后再 up
cd /docker/feishu_keyword-test && cp -f server/.env .env && docker compose --profile admin --profile feishu --profile worker up -d --build
```

### Traefik 路由重复（fskw-test 与 test-fskw 并存）

若 Traefik 面板同时出现 `Host(\`fskw-test.tbpf.com\`)` / `fkw-api-test` 与 `test-fskw.tbpf.com` / `test-fkw-api`，说明**旧 compose 项目 `fskw-test-*` 容器仍在 `proxy` 网络**。以 `server/.env.test` 为准（`test-fskw.*`、`test-fkw-*`）。

```bash
bash scripts/cleanup-old-fskw-test-stack.sh
# 确认仅 feishu_keyword-test-* 在运行：docker ps --filter network=proxy | grep feishu_keyword
```

## 域名

命名约定：**测试环境**使用 `test-` 前缀（如 `test-fskw.tbpf.com`）；**正式**为 `fskw*.tbpf.com`。

| 环境 | API | Admin | Feishu 静态 |
|------|-----|-------|-------------|
| 测试 | https://test-fskw.tbpf.com | https://test-fskw-admin.tbpf.com | https://test-fskw-feishu.tbpf.com |
| 正式 | https://fskw.tbpf.com | https://fskw-admin.tbpf.com | https://fskw-feishu.tbpf.com |

对应 `server/.env.test` 中 `API_PUBLIC_HOST`、`ADMIN_PUBLIC_HOST`、`FEISHU_PUBLIC_HOST` 及 `TRAEFIK_*_ROUTER_NAME`。

**DNS**：改域名后须：

1. 远端更新 `/docker/feishu_keyword-test/server/.env.test` 并 `cp` 为 `server/.env`、栈根 `.env`（CI **不** rsync `.env.test`）
2. 本地 `build-public-test.bat` 后提交 `public/admin`、`public/feishu`
3. 推送 `test` 触发流水线

探活：`GET https://test-fskw.tbpf.com/ci-test`

**测试管理后台**：https://test-fskw-admin.tbpf.com/login — 账号 **`admin`** / 密码 **`Admin123a`**（种子数据，上线前请改密）

## 架构（双后端 + 单 Compose）

| 组件 | 说明 |
|------|------|
| `api` | `server/` FastAPI :8000 — `/ci-test`、`/api/*`、`/api/admin/v1/*` |
| `sync-api` | `python/` FastAPI :8765 — `/api/v1/*`（Traefik 高优先级路由） |
| `celery-worker` | 异步采集 **必须** 常驻 |
| `admin-web` / `feishu-web` | 静态 nginx |

**仓库仅一份** [`docker-compose.yml`](../docker-compose.yml)；测试/正式靠主机目录与 **栈根 `.env`** 区分（`cp -f server/.env .env`）。

MySQL/Redis 由 **traefik 栈**（`/docker/traefik`）提供：`tbpf-mysql`、`tbpf-redis`，业务容器加入 `proxy` 网络即可访问。

```bash
# 测试
cd /docker/feishu_keyword-test
cp -f server/.env.test server/.env && chmod 600 server/.env
cp -f server/.env .env && chmod 600 .env
cp -f python/.env.test python/.env 2>/dev/null || true
docker compose --profile admin --profile feishu --profile worker up -d --build

# 正式
cd /docker/feishu_keyword
cp -f server/.env.master server/.env && chmod 600 server/.env
cp -f server/.env .env && chmod 600 .env
cp -f python/.env.master python/.env 2>/dev/null || true
docker compose --profile admin --profile feishu --profile worker up -d --build
```

## 环境变量

| 机制 | 文件 | 用途 |
|------|------|------|
| Compose 插值 | 栈根 `/docker/feishu_keyword-test/.env` | `API_PUBLIC_HOST`、`TRAEFIK_*`、`PYTHON_IMAGE`、`DATABASE_URL` 等 |
| 容器业务 | `server/.env`、`python/.env` | 与栈根一致或复制自 `server/.env` |

模板：`server/.env.test` / `server/.env.master`、`python/.env.*`（仓内 `PASSWORD` 占位）；栈根字段见 [`.env.stack.example`](../.env.stack.example)。

**真实口令**写在服务器栈根 `.env` 或 `server/.env`（与 `/docker/traefik/.env` 中 `MYSQL_ROOT_PASSWORD` 一致），勿提交 Git。

一键写入远端（在部署机执行）：

```bash
# 需已配置 /docker/traefik/.env 或栈根 .env 中的 MYSQL_ROOT_PASSWORD
bash scripts/remote-setup-env.sh
```

## MySQL

共享实例：**`tbpf-mysql`**（`121.43.231.225:3306`），phpMyAdmin：https://pma.tbpf.com

| 用途 | 用户 | 说明 |
|------|------|------|
| 应用 `DATABASE_URL`、`python` | **root** | 默认库 **`feishu_keyword`**；root 可跨库，**勿在 `jzl_editor` 建本项目表或改稿轻松数据** |

连接串（远端 `server/.env`）：

`mysql+pymysql://root:<MYSQL_ROOT_PASSWORD>@tbpf-mysql:3306/feishu_keyword?charset=utf8mb4`

**勿**对运行中 `tbpf-mysql` 使用 `skip-grant-tables` 热改配置。历史稿轻松 `gqs-mysql` 脚本见 [`scripts/legacy/`](../scripts/legacy/)。

## 数据库与种子

**独立库 `feishu_keyword`**：与 traefik 默认库 `jzl_editor`（稿轻松）分离。

### 首次：创建库

```bash
bash scripts/init-feishu-keyword-db.sh
# 或在 phpMyAdmin 执行 scripts/create_feishu_db.sql
```

### 建表与演示账号

```bash
bash scripts/bootstrap-feishu-keyword-db.sh
# 或
docker exec feishu_keyword-test-api-1 python scripts/init_schema.py
docker exec feishu_keyword-test-api-1 python scripts/seed_demo.py
```

管理端登录：`admin` / `Admin123a`

python 业务表：sync-api 启动时 `DATABASE_RUN_MIGRATIONS=1` 会迁移；或执行 `python/social_platform/database/schema.sql`

## GitLab CI

- `test` 分支：自动 `deploy-test`（rsync 后先 `docker compose down --remove-orphans` 再 `up`）
- 部署前会检查 `tbpf-mysql` 是否运行；未运行则 WARN，需 `cd /docker/traefik && docker compose up -d mysql redis`
- `master`：`deploy-prod` 手动/变更触发
- 本地先 `build-public-test.bat` 并提交 `public/admin`、`public/feishu`

## 验收 curl

```bash
curl -sS https://test-fskw.tbpf.com/ci-test
curl -sS https://test-fskw.tbpf.com/api/v1/health
curl -sS -X POST https://test-fskw.tbpf.com/api/admin/v1/system/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"Admin123a"}'
```

## 本地开发

```bash
cd server && cp .env.example .env && uvicorn app.main:app --reload --port 8000
cd python && cp .env.example .env && python run.py   # :8765
cd admin && npm run dev:local
cd feishu && npm run dev:local
```

推送 test 前：`.\build-public-test.bat` → `git push origin test`

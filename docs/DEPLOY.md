# feishu_keyword 部署说明

## 主机目录

| 环境 | 路径 |
|------|------|
| 测试 | `/docker/feishu_keyword-test` |
| 正式 | `/docker/feishu_keyword` |

## 域名

命名约定：**测试环境**使用 `test-` 前缀（如 `test-fskw.tbpf.com`）；**正式**为 `fskw*.tbpf.com`。

| 环境 | API | Admin | Feishu 静态 |
|------|-----|-------|-------------|
| 测试 | https://test-fskw.tbpf.com | https://test-fskw-admin.tbpf.com | https://test-fskw-feishu.tbpf.com |
| 正式 | https://fskw.tbpf.com | https://fskw-admin.tbpf.com | https://fskw-feishu.tbpf.com |

对应仓根 [`.env.test`](../.env.test) / [`.env.master`](../.env.master) 中 `API_PUBLIC_HOST`、`ADMIN_PUBLIC_HOST`、`FEISHU_PUBLIC_HOST` 及 `TRAEFIK_*_ROUTER_NAME`。

**DNS**：改域名后须：

1. 远端更新栈根 `.env.test` 或 `.env.master`（CI **不** rsync 含真实口令的 `.env`；可维护服务器上的 `.env.test`）
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

**仓库仅一份** [`docker-compose.yml`](../docker-compose.yml)；测试/正式靠主机目录与 **栈根 `.env`** 区分（`cp -f .env.test .env` 或 `cp -f .env.master .env`）。

MySQL/Redis 由 **traefik 栈**（`/docker/traefik`）提供：`tbpf-mysql`、`tbpf-redis`，业务容器加入 `proxy` 网络即可访问。

```bash
# 测试
cd /docker/feishu_keyword-test
cp -f .env.test .env && chmod 600 .env
docker compose --profile admin --profile feishu --profile worker up -d --build

# 正式
cd /docker/feishu_keyword
cp -f .env.master .env && chmod 600 .env
docker compose --profile admin --profile feishu --profile worker up -d --build
```

## 环境变量

| 文件 | 用途 |
|------|------|
| [`.env.example`](../.env.example) | 全量变量说明（可提交） |
| `.env.test` / `.env.master` | 测试/正式模板（仓内 `PASSWORD` 占位；服务器可覆盖真实口令） |
| `.env` | 生效文件（gitignore）；`cp .env.test .env` 或 `cp .env.master .env` |

Compose 插值与 `api` / `sync-api` / `celery-worker` **均只读栈根 `./.env`**。前端 Vite 构建同样读仓根（`build-public-*.bat` 会先复制对应模板为 `.env`）。

**真实口令**写在服务器栈根 `.env`（与 `/docker/traefik/.env` 中 `MYSQL_ROOT_PASSWORD` 一致），勿提交 Git。

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

连接串（远端栈根 `.env`）：

`mysql+pymysql://root:<MYSQL_ROOT_PASSWORD>@tbpf-mysql:3306/feishu_keyword?charset=utf8mb4`

**勿**对运行中 `tbpf-mysql` 使用 `skip-grant-tables` 热改配置。

### 从旧版多文件 env 迁移（一次性）

若服务器仍有 `server/.env*`、`python/.env*`，请合并到栈根 `.env.test` / `.env.master` 后删除子目录 env 文件，再 `cp -f .env.test .env`（或 `.env.master`）。

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

- `test` 分支：自动 `deploy-test`（测试栈 `/docker/feishu_keyword-test`）；**同一流水线**中手动运行 `deploy-prod` 发布正式栈 `/docker/feishu_keyword`
- `deploy-prod` / `deploy-test` 均使用 `--profile admin --profile feishu --profile worker`，部署后校验 `feishu-web` → `sync-api:8765/api/v1/health`（避免 `/api/v1` 502）
- 远端须有栈根 `.env.test`（测试）或 `.env.master`（正式），CI 会 `cp` 为 `.env`
- 部署前会检查 `tbpf-mysql` 是否运行；未运行则 WARN，需 `cd /docker/traefik && docker compose up -d mysql redis`
- 测试：`build-public-test.bat`；**正式**：`build-public-prod.bat` 后再提交 `public/admin`、`public/feishu`
- `master` 分支亦可手动/变更触发 `deploy-prod`（与从 `test` 触发二选一）

## 验收 curl

```bash
curl -sS https://test-fskw.tbpf.com/ci-test
curl -sS https://test-fskw.tbpf.com/api/v1/health
curl -sS -X POST https://test-fskw.tbpf.com/api/admin/v1/system/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"Admin123a"}'
```

## 本地开发

### 局域网联调（不用 Docker）

```bash
cp .env.test .env
cp .env.local.example .env.local   # 可选，覆盖为 127.0.0.1
cd server && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
cd python && python run.py
cd admin && npm run dev:lan
cd feishu && npm run dev:lan
```

加载顺序（server/python/Vite）：**仓根 `.env` → `.env.local`**。

推送 test 前：`.\build-public-test.bat` → `git push origin test`

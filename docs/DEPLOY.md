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

1. 在栈根维护 `.env.test` 或 `.env.master`（含真实口令）；**每次部署**执行 `cp -f .env.test .env`（正式用 `.env.master`）。勿长期手改 `.env`，它会被覆盖。
2. 测试：`build-public-test.bat` → 提交 `public/*` → 推送 `test`（自动 `deploy-test`）
3. 正式：`build-public-prod.bat` → 提交 `public/*` → **MR 合并 `master`** → 流水线中手动 `deploy-prod`

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
| `.env.test` / `.env.master` | 测试/正式**源文件**（改配置只改这里） |
| `.env` | 生效文件（gitignore）；由上一行 **覆盖** 得到，CI 与 `docker compose` 只读此文件 |

```bash
# 测试栈每次部署前/CI 内均会执行：
cp -f .env.test .env && chmod 600 .env
# 正式：
cp -f .env.master .env && chmod 600 .env
```

Compose 插值与 `api` / `sync-api` / `celery-worker` **均只读栈根 `./.env`**。本地/打包构建：`build-public-*.bat` 会先把对应 `.env.test` 或 `.env.master` 复制为 `.env`。

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

python 业务表：`sync-api` 启动且 `DATABASE_RUN_MIGRATIONS=1` 时，若库中无 `feishu_async_tasks` 会先执行 `schema.sql` 基线建表，再跑列/索引迁移；`server` 侧表仍用 `api` 容器 `init_schema.py`

## GitLab CI

| 分支 | 触发方式 | 部署任务 |
|------|----------|----------|
| `test` | 推送后**自动**执行 | `deploy-test` → 测试栈 `/docker/feishu_keyword-test` |
| `master` | **MR 合并进 master** 后产生流水线 | 在流水线中**手动**运行 `deploy-prod` → 正式栈 `/docker/feishu_keyword` |

推荐发布流程：开发分支 → 合并/推 `test` → 验收测试环境 → `build-public-prod.bat` 并提交 `public/*` → MR 合并 `master` → 手动 `deploy-prod`。

- `deploy-prod` / `deploy-test` 均使用 `--profile admin --profile feishu --profile worker`，部署后校验 `feishu-web` → `sync-api:8765/api/v1/health`（避免 `/api/v1` 502）
- 远端须有栈根 `.env.test`（测试）或 `.env.master`（正式）；CI 每次部署 **`cp -f` 覆盖 `.env`**
- 部署前会检查 `tbpf-mysql` 是否运行；未运行则 WARN，需 `cd /docker/traefik && docker compose up -d mysql redis`
- 测试：`build-public-test.bat`；**正式**：`build-public-prod.bat` 后再提交 `public/admin`、`public/feishu`

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

| 阶段 | 命令 |
|------|------|
| 测栈 | `.\build-public-test.bat` → `git push origin test`（自动 `deploy-test`） |
| 正式 | `.\build-public-prod.bat` → 提交 `public/*` → MR 合并 `master` → 流水线手动 `deploy-prod` |

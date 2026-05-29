# feishu_keyword 部署说明

## 主机目录

| 环境 | 路径 |
|------|------|
| 测试 | `/docker/feishu_keyword-test` |
| 正式 | `/docker/feishu_keyword` |

## 域名

命名约定：**测试环境**使用 `test-` 前缀（如 `test-fskw.tbpf.com`）；**正式**为 `fskw*.tbpf.com`。

| 环境 | API（Traefik → `api:8765`，路径 `/api/v1`） | Admin 静态 | Feishu 静态 |
|------|---------------------------------------------|------------|-------------|
| 测试 | https://test-fskw.tbpf.com | https://test-fskw-admin.tbpf.com | https://test-fskw-feishu.tbpf.com |
| 正式 | https://fskw.tbpf.com | https://fskw-admin.tbpf.com | https://fskw-feishu.tbpf.com |

对应仓根 [`.env.test`](../.env.test) / [`.env.master`](../.env.master) 中 `API_PUBLIC_HOST`、`ADMIN_PUBLIC_HOST`、`FEISHU_PUBLIC_HOST` 及 `TRAEFIK_*_ROUTER_NAME`。

**DNS**：改域名后须：

1. 在栈根维护 `.env.test` 或 `.env.master`（含真实口令）；**每次部署**执行 `cp -f .env.test .env`（正式用 `.env.master`）。勿长期手改 `.env`，它会被覆盖。
2. 测试：本地 merge 到 `test` → `git push origin test`（CI 在 Runner 编译 `public/admin` 与 `public/feishu` 并 tar+scp 部署）
3. 正式：GitLab **MR** 合并 `master` → 流水线中手动 `deploy-prod`（CI 使用 `.env.master` 编译正式静态）

探活：`GET https://test-fskw.tbpf.com/api/v1/health`；管理端：`GET https://test-fskw.tbpf.com/api/admin/v1/health`

## Docker 服务

| 服务 | profile | 说明 |
|------|---------|------|
| `api` | `worker` | `server/` 镜像，FastAPI **:8765**，对外 `/api/v1/*` 与 `/api/admin/v1/*`（Traefik） |
| `celery-worker` | `worker` | 同一镜像，执行异步采集任务 |
| `admin-web` | `admin` | nginx 静态 `public/admin`，Traefik 域名 `ADMIN_PUBLIC_HOST` |
| `feishu-web` | `feishu` | nginx 静态 `public/feishu`，同源反代 `/api/v1/` → `api:8765` |

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

Compose 插值与 `api` / `celery-worker` **均只读栈根 `./.env`**。本地预检：先 `cp .env.test|.env.master .env`，再在 `admin/`、`feishu/` 内 `npm run build:public:test|prod`（admin 构建依赖 `VITE_ADMIN_API_ORIGIN`）。

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
| 应用 `DATABASE_URL` | **root** | 默认库 **`feishu_keyword`** |

连接串（远端栈根 `.env`）：

`mysql+pymysql://root:<MYSQL_ROOT_PASSWORD>@tbpf-mysql:3306/feishu_keyword?charset=utf8mb4`

**勿**对运行中 `tbpf-mysql` 使用 `skip-grant-tables` 热改配置。

### 首次：创建库

```bash
bash scripts/init-feishu-keyword-db.sh
# 或在 phpMyAdmin 执行 scripts/create_feishu_db.sql
```

### 建表

`api` 启动且 `DATABASE_RUN_MIGRATIONS=1` 时：

1. 若库中无 `feishu_async_tasks`，执行 [`server/migrations/schema.sql`](../server/migrations/schema.sql) 基线建表；
2. 再由 [`server/social_platform/database/db_migrate.py`](../server/social_platform/database/db_migrate.py) 做列对齐与索引补丁。

详见 [server/migrations/README.md](../server/migrations/README.md)。

## GitLab CI

| 分支 | 触发方式 | 部署任务 |
|------|----------|----------|
| `test` | 推送后**自动**执行 | `deploy-test` → 测试栈 `/docker/feishu_keyword-test` |
| `master` | **MR 合并进 master** 后产生流水线 | 在流水线中**手动**运行 `deploy-prod` → 正式栈 `/docker/feishu_keyword` |

推荐发布流程：个人分支 → **本地 merge `test`** → push `test` → 验收测试环境 → GitLab **MR** 合并 `master` → 手动 `deploy-prod`。分支规范见 [GIT_WORKFLOW.md](./GIT_WORKFLOW.md)。

**CI 流程**（Shell Runner）：`scripts/ci-build-frontend.sh` 编译 **admin + feishu** → `ci-pack-deploy.sh` 打 `deploy.pkg.tar.gz` → **scp** 到栈根 → `ci-deploy-remote.sh` 解压并 `docker compose up -d --build`。

- `deploy-prod` / `deploy-test` 均使用 `--profile admin --profile feishu --profile worker`
- 部署后校验：`feishu-web` 容器内访问 `http://api:8765/api/v1/health`
- 远端须有栈根 `.env.test`（测试）或 `.env.master`（正式）；部署时 **`cp -f` 覆盖 `.env`**
- 部署前会检查 `tbpf-mysql` 是否运行；未运行则 WARN
- **Runner 前置**：Node.js 18+、`npm`、`bash`、`tar`、`scp`、`ssh`；可选 CI 变量 `NPM_CONFIG_REGISTRY`

## 验收 curl

```bash
curl -sS https://test-fskw.tbpf.com/api/v1/health
```

## 本地开发

### 局域网联调（不用 Docker）

```bash
cp .env.test .env
cp .env.local.example .env.local   # 可选，覆盖为 127.0.0.1

cd server && python run.py
cd feishu && npm run dev:lan
```

另开终端启动 Celery Worker（命令见 [server/README.md](./server/README.md)）。

加载顺序：**仓根 `.env` → `.env.local`**。

| 阶段 | 命令 |
|------|------|
| 测栈 | 本地 `git merge` 个人分支到 `test` → `git push origin test`（CI 自动编译并 `deploy-test`） |
| 正式 | GitLab MR 合并 `master` → 流水线手动 `deploy-prod`（CI 使用 `.env.master` 编译） |

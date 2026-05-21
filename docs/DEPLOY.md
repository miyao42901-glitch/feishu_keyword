# fskw 部署说明

## 域名

| 环境 | API | Admin | Feishu 静态 |
|------|-----|-------|-------------|
| 测试 | https://fskw-test.tbpf.com | https://fskw-admin-test.tbpf.com | https://fskw-feishu-test.tbpf.com |
| 正式 | https://fskw.tbpf.com | https://fskw-admin.tbpf.com | https://fskw-feishu.tbpf.com |

探活：`GET https://fskw-test.tbpf.com/ci-test`（正式为 `fskw.tbpf.com`）。

## 主机与 Compose

- 与稿轻松同机，复用 **`gqs-mysql`**、**`gqs-redis`**（`/docker/gaoqingsong` 已 `--profile db up`）。
- 测试栈：`/docker/fskw-test`
- 正式栈：`/docker/fskw`
- 编排真源：仓库根 `docker-compose.yml` + `docker-compose.test.yml` 或 `docker-compose.prod.yml`
- Traefik：`*.tbpf.com` 泛解析 + `certresolver=dnspod`（标签内域名写死，不用 Compose 变量）

```bash
# 测试
cd /docker/fskw-test
docker compose -f docker-compose.yml -f docker-compose.test.yml --profile admin --profile feishu up -d --build

# 正式
cd /docker/fskw
docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile admin --profile feishu up -d --build
```

## 首次 SSH 配置（121.43.231.225）

1. `mkdir -p /docker/fskw-test/server /docker/fskw/server` 及 `public/admin`、`public/feishu`、`deploy/*-static`。
2. 参考 `/docker/gaoqingsong-test/server/.env.test` 中的 `MYSQL_USER` / `MYSQL_PASSWORD`，写入 fskw 的 `.env.test` / `.env.master`：
   - `DATABASE_URL=mysql+pymysql://用户:口令@gqs-mysql:3306/feishu_keyword?charset=utf8mb4`
   - `REDIS_HOST=gqs-redis`，测试 `REDIS_DB=2`，正式 `REDIS_DB=3`
3. 在 `gqs-mysql` 创建库 `feishu_keyword` 并授权（`lanlang_v1` 通常无 `CREATE DATABASE` 权限，请用 **phpMyAdmin**（`pma.tbpf.com`）或具备 root 权限的方式执行 `scripts/create_feishu_db.sql`）。
4. `chmod 600` 各 `server/.env`。

远端已可通过 `scripts/remote-setup-env.sh` 写入 `/docker/fskw-test/server/.env.test` 与 `/docker/fskw/server/.env.master`（含真实 `DATABASE_URL`）。

CI rsync **不会覆盖** 远端 `.env`、`.env.test`、`.env.master`（仅同步代码与 compose）。

## GitLab CI

- 变量：`SSH_PRIVATE_KEY`、`HOST_IP`（默认 `121.43.231.225`）
- **`test` 分支**：自动 `deploy-test`（构建 admin/feishu → rsync → compose up）
- **`master` 分支**：`deploy-prod` 变更时自动或手动触发

## `public/feishu` 与 GitHub

- **Docker 线上域**（上表 Feishu 列）：由 CI 构建并 rsync 到服务器；目录 **`public/feishu` 不进主 GitLab 仓**。
- **飞书/GitHub 发布**：在本机 `public/feishu` 内维护 GitHub 空仓，执行 `npm run build:public:prod` 后 **手动** `git push`；可用 `release.bat` 辅助构建（参数 `prod` 为正式 API 地址构建）。

## 本地开发

```bash
# 后端
cd server && cp .env.example .env  # 编辑 DATABASE_URL
uvicorn app.main:app --reload --port 8000

# admin
cd admin && npm run dev:local

# feishu
cd feishu && npm run dev:local
```

# 飞书关键词监控插件

## 当前项目

本项目是面向**飞书（Lark）**的**关键词监控插件**，用于在飞书生态内配置关键词采集任务、对接 YDDM 账户，并将各平台搜索结果写入 MySQL。

- **全称**：飞书关键词监控插件
- **GitLab 仓库**：[http://192.168.1.200:8080/jzl/feishu_keyword/](http://192.168.1.200:8080/jzl/feishu_keyword/)

## 线上部署

主机目录：`/docker/feishu_keyword-test`（测试）、`/docker/feishu_keyword`（正式）。测试域名前缀为 `test-`（如 `test-fskw.tbpf.com`）。

| 环境 | API（`/api/v1`） | Admin 静态 | Feishu 静态 |
|------|------------------|------------|-------------|
| 测试 | https://test-fskw.tbpf.com | https://test-fskw-admin.tbpf.com | https://test-fskw-feishu.tbpf.com |
| 正式 | https://fskw.tbpf.com | https://fskw-admin.tbpf.com | https://fskw-feishu.tbpf.com |

探活：`GET https://test-fskw.tbpf.com/api/v1/health`

详细步骤见 [docs/DEPLOY.md](docs/DEPLOY.md)；文档索引见 [docs/README.md](docs/README.md)。

## MySQL / Redis（traefik 共享栈）

基础设施在 `/docker/traefik`：`tbpf-mysql`、`tbpf-redis`（`proxy` 网络）。phpMyAdmin：https://pma.tbpf.com

**本项目独立库 `feishu_keyword`**；应用与运维均用 **root**（与 traefik `MYSQL_ROOT_PASSWORD` 一致，便于跨库）。真实口令写在各环境**栈根** `.env`（由 [.env.test](.env.test) / [.env.master](.env.master) 复制，见 [.env.example](.env.example)），勿提交 Git。

| 用途 | 主机 | 账号 | 库名 |
|------|------|------|------|
| 应用 `DATABASE_URL` / 运维 | `tbpf-mysql:3306` | `root` | **`feishu_keyword`**（默认；可跨库查询） |
| Redis | `tbpf-redis:6379` | 无密码 | 测试 DB `2`、正式 DB `3` |

连接串示例（远端栈根 `.env`）：

`mysql+pymysql://root:***@tbpf-mysql:3306/feishu_keyword?charset=utf8mb4`

一键写入远端 env：`bash scripts/remote-setup-env.sh`（读栈根或 `/docker/traefik/.env` 中的口令）。

## 后端与前端

| 服务 | 路径前缀 | 目录 |
|------|----------|------|
| HTTP API + Celery 异步采集 | `/api/v1` | `server/`（FastAPI :8765，需 `celery-worker`） |
| 管理后台前端 | `/admin` | `admin/` → 静态产物 `public/admin/` |
| 飞书插件前端 | — | `feishu/` → 静态产物 `public/feishu/` |

## `public` 目录

| 路径 | 说明 |
|------|------|
| `public/admin/` | 管理后台静态资源（**CI Runner 编译**后随 tar 部署；勿提交 Git） |
| `public/feishu/` | 飞书插件静态资源（**CI Runner 编译**后随 tar 部署；勿提交 Git） |

## 本地开发

**局域网联调（不用 Docker）**：在仓根 `cp .env.test .env`，再 `cp .env.local.example .env.local`，按本机 IP 改 `DATABASE_URL`、`SYNC_PROXY_TARGET` 等。

```bash
cp .env.test .env
cp .env.local.example .env.local   # 可选覆盖

cd server && python run.py
# 另开终端：Celery Worker（见 docs/server/README.md）

cd feishu && npm run dev:lan
```

仅本机回环可用 `npm run dev:local`（`127.0.0.1`）。Docker/远端部署见 [docs/DEPLOY.md](docs/DEPLOY.md)（`.env.test` / `.env.master`）。

**CI / 分支**：本地 merge 到 `test` 后 `git push origin test`（Runner 编译 `admin` + `feishu` 并 tar+scp 自动部署）；正式环境 GitLab MR 合并 `master` 后手动 `deploy-prod`。详见 [docs/GIT_WORKFLOW.md](docs/GIT_WORKFLOW.md)、[docs/DEPLOY.md](docs/DEPLOY.md)。

本地预检构建：在 `feishu/`（或 `admin/`）内 `npm run build:public:test|prod`（先 `cp .env.test .env` 或 `cp .env.master .env`）；**不必**为部署提交 `public/*`。

## 目录结构

```
feishu_keyword/
├── docker-compose.yml      # 唯一编排真源（api、celery-worker、admin-web、feishu-web）
├── .env.example            # 统一环境变量模板
├── .env.test / .env.master # 测试/正式占位（可提交 PASSWORD 版）
├── admin/                  # 管理后台前端
├── feishu/                 # 飞书插件前端
├── server/                 # FastAPI + Celery + 平台采集
├── deploy/
├── public/
└── docs/
```

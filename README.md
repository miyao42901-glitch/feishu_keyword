# 飞书关键词监控插件

## 当前项目

本项目是面向**飞书（Lark）**的**关键词监控插件**，用于在飞书生态内对关键词进行监控与相关能力扩展。

- **全称**：飞书关键词监控插件  
- **GitLab 仓库**：[http://192.168.1.200:8080/jzl/feishu_keyword/](http://192.168.1.200:8080/jzl/feishu_keyword/)

## 线上部署

主机目录：`/docker/feishu_keyword-test`（测试）、`/docker/feishu_keyword`（正式）。测试域名前缀为 `test-`（如 `test-fskw.tbpf.com`）。

| 环境 | API | Admin | Feishu 静态 |
|------|-----|-------|-------------|
| 测试 | https://test-fskw.tbpf.com | https://test-fskw-admin.tbpf.com | https://test-fskw-feishu.tbpf.com |
| 正式 | https://fskw.tbpf.com | https://fskw-admin.tbpf.com | https://fskw-feishu.tbpf.com |

探活：`GET https://test-fskw.tbpf.com/ci-test`

**测试管理后台登录**：https://test-fskw-admin.tbpf.com/login — 账号 `admin` / 密码 `Admin123a`（首次登录后请修改）

详细步骤见 [docs/DEPLOY.md](docs/DEPLOY.md)。

## MySQL / Redis（traefik 共享栈）

基础设施在 `/docker/traefik`：`tbpf-mysql`、`tbpf-redis`（`proxy` 网络）。phpMyAdmin：https://pma.tbpf.com

**本项目独立库 `feishu_keyword`**；应用与运维均用 **root**（与 traefik `MYSQL_ROOT_PASSWORD` 一致，便于跨库）。真实口令写在各环境**栈根** `.env`（见 [.env.stack.example](.env.stack.example)），勿提交 Git。

| 用途 | 主机 | 账号 | 库名 |
|------|------|------|------|
| 应用 `DATABASE_URL` / 运维 | `tbpf-mysql:3306` | `root` | **`feishu_keyword`**（默认；可跨库查询） |
| Redis | `tbpf-redis:6379` | 无密码 | 测试 DB `2`、正式 DB `3` |

连接串示例（远端 `server/.env`）：

`mysql+pymysql://root:***@tbpf-mysql:3306/feishu_keyword?charset=utf8mb4`

一键写入远端 env：`bash scripts/remote-setup-env.sh`（读栈根或 `/docker/traefik/.env` 中的口令）。

## 双后端

| 服务 | 路径前缀 | 目录 |
|------|----------|------|
| 业务 API（管理端、飞书任务配置） | `/api`、`/api/admin/v1`、`/ci-test` | `server/` |
| 采集/异步 API | `/api/v1` | `python/`（需 Celery Worker） |

## `public` 目录

| 路径 | 说明 |
|------|------|
| `public/admin/` | 管理端静态，本地 `build:public:*` 后提交主仓 |
| `public/feishu/` | 飞书静态，本地 `build:public:*` 后提交主仓 |

## 本地开发

**局域网联调（不用 Docker）**：各子目录复制 `*.env.local.example` → `.env.local`，按本机 IP 改 `192.168.1.11` 等。

```bash
cd server && cp .env.local.example .env.local   # 填 DATABASE_URL、Redis
cd python && cp .env.local.example .env.local
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000   # 在 server 目录
python run.py                                             # 在 python 目录

cd admin && cp .env.local.example .env.local && npm run dev:lan
cd feishu && cp .env.local.example .env.local && npm run dev:lan
```

仅本机回环可用 `npm run dev:local`（`127.0.0.1`）。Docker/远端部署见 [docs/DEPLOY.md](docs/DEPLOY.md)（`.env.test` / `.env.master`）。

部署前预编译（测试）：仓根 `build-public-test.bat`，提交 `public/admin`、`public/feishu` 后推送 `test` 分支。

## 目录结构

```
feishu_keyword/
├── docker-compose.yml      # 唯一编排真源（测试/正式靠栈目录 .env 区分）
├── .env.stack.example      # 栈根 .env 字段说明
├── build-public-test.bat
├── admin/
├── feishu/
├── python/                 # 采集与异步任务（lyc 分支合并）
├── server/
├── deploy/
├── public/
└── docs/
```

# server/ 技术文档索引

## 适用范围

| 项 | 说明 |
|----|------|
| **对应代码目录** | 仓库根目录下的 **`server/`** |
| **职责** | FastAPI `/api/v1`、MySQL 任务与结果、Celery 异步采集、各平台 Worker |

---

## 技术栈

以 `server/requirements.txt` 为准；当前约定如下。

| 类别 | 技术 | 说明 |
|------|------|------|
| 语言 | Python 3 | 建议 3.9+（Docker 镜像 `python:3.9-slim`） |
| Web 框架 | FastAPI | 路由、OpenAPI |
| ASGI 服务器 | Uvicorn | 生产容器：`uvicorn http_service:app`；开发：`python run.py` |
| ORM | SQLAlchemy 2.x | 模型见 `social_platform/models/` |
| 任务队列 | Celery + Redis | Worker：`social_platform.tasks.celery_app` |
| 数据库驱动 | PyMySQL | 连接串 `mysql+pymysql://...` |
| 配置 | 仓根 `.env` | 经 `config/settings.py`、`social_platform/env_bootstrap.py` 加载 |

---

## 与本目录相关的规范文档

| 文档 | 说明 |
|------|------|
| [HTTP_API.md](./HTTP_API.md) | `/api/v1` 路径、鉴权 Header、同步/异步任务、限流 |
| [DATABASE.md](../DATABASE.md) | 库名、五张业务表、`DATABASE_URL` |
| [DEVELOPMENT.md](../DEVELOPMENT.md) | 分层目录、Git 与注释 |
| [DEPLOY.md](../DEPLOY.md) | Docker `api` / `celery-worker`、CI 与健康检查 |

---

## 目录结构（摘要）

```
server/
├── run.py                 # 本地开发启动（HTTP + 可选调度）
├── http_service.py        # FastAPI 应用入口（Docker CMD）
├── http_api/v1/           # /api/v1 路由（sync、async、health）
├── social_platform/       # 业务：models、services、tasks、database
├── workers/               # douyin / xhs / wxvideo / mp 采集
├── config/                # 配置读取
├── migrations/            # schema.sql 与增量 SQL
└── requirements.txt
```

---

## 本地运行

环境：仓根 `cp .env.test .env`（可选 `cp .env.local.example .env.local`）。需本机或局域网可访问的 **MySQL**（`feishu_keyword`）与 **Redis**（Celery）。

```powershell
cd server
pip install -r requirements.txt

# 终端 1：HTTP API（默认 :8765）
python run.py

# 终端 2：Celery Worker
celery -A social_platform.tasks.celery_app:celery_app worker -l info -P gevent -c 4 --prefetch-multiplier=1
```

- OpenAPI：`http://127.0.0.1:8765/docs`
- 健康检查：`GET http://127.0.0.1:8765/api/v1/health`

`DATABASE_RUN_MIGRATIONS=1` 时，启动会自动执行 `schema.sql`（新库）与 `db_migrate.py` 补丁。

---

## Docker

与 `docker-compose.yml` 中 **`api`**、**`celery-worker`** 服务共用同一镜像（`server/Dockerfile`）：

- `api`：暴露 8765，Traefik 将公网 `API_PUBLIC_HOST` 的 `/api/v1` 转发到此服务
- `celery-worker`：执行异步采集；须与 `api` 同栈、同 `.env` 中的 `DATABASE_URL` 与 Redis

`feishu-web` 容器内 nginx 将浏览器请求的 `/api/v1/` 反代到 `http://api:8765`（见 `deploy/feishu-static/default.conf`）。

---

## 接口实现与注释

- **`http_api/v1/*.py`** 路由处理函数须写**中文 docstring**（路径、Header、Body、响应结构），与 **[HTTP_API.md](./HTTP_API.md)** 一致。
- 前端封装见 **`feishu/src/lib/async-task-api.ts`**、**`feishu/src/lib/*-sync-api.ts`** 等（JSDoc 与路径对应）。

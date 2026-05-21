# Python 采集与 HTTP 服务

本目录提供 **统一 HTTP API**（FastAPI）、**异步任务**（Celery + MySQL + Redis）及四平台 **Worker** 实现。与仓库根目录 `server/`、`feishu/` **无 Python 业务耦合**。

- **Python 版本**：3.9.x（见 `pyproject.toml`）
- **接口说明**：[`HTTP_API.md`](HTTP_API.md)
- **部署与启动**：[`DEPLOYMENT.md`](DEPLOYMENT.md)（含 FastAPI / Celery 并发与生产流程）

## 快速启动

```bash
cd python
pip install -r requirements.txt
cp .env.example .env   # 填写 DATABASE_URL、REDIS_URL

# 终端 1（内部unicorn启动）
python run.py

# 终端 2（异步任务必须；gevent 4 并发，见 .env CELERY_WORKER_*） 先info一段时间看看
celery -A social_platform.tasks.celery_app worker -l info -P gevent -c 4 --prefetch-multiplier=1
```

仅写 `celery ... worker -l info` 亦可（池类型与并发从 `.env` 的 `CELERY_WORKER_POOL` / `CELERY_WORKER_CONCURRENCY` 读取）。

生产提高 HTTP 并发示例：

```bash
HTTP_WORKERS=4 python run.py
celery -A social_platform.tasks.celery_app worker -l info -P gevent -c 8 --prefetch-multiplier=1
```

## 目录一览

| 路径 | 作用 |
|------|------|
| `run.py` + `http_service.py` | 统一 FastAPI，默认 `:8765` |
| `http_api/` | `/api/v1` 路由（同步、异步、验收） |
| `social_platform/` | 任务服务、ORM、Celery 应用、调度 |
| `social_platform/tasks/celery_app.py` | **Celery 应用入口** |
| `workers/` | 各平台采集实现（douyin / xhs / mp / wxvideo） |
| `DEPLOYMENT.md` | 部署、并发、systemd、排障 |
| `HTTP_API.md` | 请求/响应契约 |
| `requirements-http.txt` | HTTP + Celery + DB 依赖 |
| `.env.example` | 环境变量模板 |

## 设计原则

1. **隔离**：不与 `server` / `feishu` 互相 import 业务包。
2. **Worker 自治**：各平台 Worker 可独立演进。
3. **契约**：JSON 形状见 `HTTP_API.md` 与 `contracts/`（文档用，非运行时库）。

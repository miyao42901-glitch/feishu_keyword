# Python 层架构说明

本目录承载**爬虫 Worker** 及其配套工具。业务流程代码在仓库根目录的 **`server/`** 与 **`feishu/`**；与 **`python/workers/`**、**`python/social_platform/`** 在代码上**禁止互相 import** 到业务包、无与 `server` 共享的 Python 包。

**解释器版本**：本目录下代码与依赖按 **Python 3.9.x** 编写与测试（见 `pyproject.toml` 的 `requires-python`）；请勿使用 3.10 及以上运行，以免类型与三方库行为不一致。

## 统一 HTTP（推荐）

- 在 `python/` 下安装依赖：`pip install -r requirements-http.txt`
- 启动：**`python run.py`**（默认 `0.0.0.0:8765`，可用环境变量 `HTTP_HOST`、`HTTP_PORT`、`HTTP_RELOAD`）
- 路由：统一前缀 **`/api/v1`** — `GET /api/v1/health`；抖音/小红书 **`POST /api/v1/sync/...`**（**Query：`key`** + **扁平 JSON Body**）；聚合 **`POST /api/v1/run`**；异步 **`POST /api/v1/async/tasks`**、`GET .../async/tasks/{id}`、`GET .../async/tasks/{id}/results`（需 `DATABASE_URL` + Celery worker，见 `HTTP_API.md`）
- **接口说明（路径、参数、响应格式）**：见 **`HTTP_API.md`**

## Celery（异步任务 Worker / Beat）

应用入口与 **`celery -A`** 目标一致，任选其一：

- **`celery_jobs.celery_app:celery_app`**（兼容包名，推荐命令行使用）
- **`social_platform.tasks.celery_app:celery_app`**（定义所在模块）

**前置**：已安装 `requirements-http.txt`；本机 **Redis** 可连（默认 `REDIS_URL=redis://127.0.0.1:6379/0`）；异步 HTTP 消费任务还需在 **`python/.env`** 中配置 **`DATABASE_URL`**（与 `run.py` 使用同一 `.env`）。工作目录须在仓库的 **`python/`** 下执行（保证 `celery_jobs`、`workers` 在 `PYTHONPATH` 中）。

**Windows 说明**：默认 **prefork + billiard** 在部分 Win10/Win11 上会触发 `fast_trace_task` 里 `_loc` 解包失败（`ValueError: not enough values to unpack`）。本项目在 `social_platform/tasks/celery_app.py` 中已对 **Windows** 自动设置 `FORKED_BY_MULTIPROCESSING=1` 且 **`worker_pool = solo`**（单进程串行消费任务）。生产高并发请在 **Linux / WSL / Docker** 上跑 Worker（默认 `prefork`，可用 **`-c N`**）。

### Worker（处理 `POST /api/v1/async/tasks` 入队任务）

```bash
cd python
celery -A celery_jobs.celery_app worker -l info
```

常用可选参数（**Linux / macOS** 等以 prefork 为池时）：

- **`-c 4`**：并发子进程数。
- **`-Q celery`**：若配置了自定义队列名，在此指定。
- **`-P threads`** 或 **`-P eventlet`**：若在 Windows 上仍需自行改池（需 `pip install eventlet`），可显式指定；一般无需再传，已默认 `solo`。

### Beat（定时调度，默认关闭）

Beat 仅在环境变量 **`CELERY_BEAT_ENABLED=1`** 时加载 `social_platform/tasks/beat_schedule.py` 中的示例计划（见 `config/settings.py`）。开启后另开进程：

```bash
cd python
set CELERY_BEAT_ENABLED=1
celery -A celery_jobs.celery_app beat -l info
```

Linux / macOS：

```bash
cd python
CELERY_BEAT_ENABLED=1 celery -A celery_jobs.celery_app beat -l info
```

生产环境请 **Worker 与 Beat 分进程部署**；示例 Beat 中的 `key`、关键词等需在 `beat_schedule.py` 中改为真实值或改为从配置读取。

### 开发调试（不落 Redis）

在 `.env` 中设置 **`CELERY_TASK_ALWAYS_EAGER=1`** 时，任务在当前进程同步执行（便于断点），**不要**用于生产。

### 已注册任务名（供排查 / `inspect`）

| Celery 任务名 | 作用 |
|----------------|------|
| `social_platform.tasks.worker_tasks.run_social_async_task` | 执行异步社交采集（HTTP 提交后由 broker 投递） |
| `celery_jobs.tasks.social_task.run_jzl_social` | 兼容名：聚合 `run_task`（Beat 示例与旧调用） |

## 目录一览

| 路径 | 作用 |
|------|------|
| `run.py` + `http_service.py` | **统一 FastAPI**，单端口对外 |
| `http_api/` | 对外 API 版本：`v1/` 等；常量见 `http_api/versions.py` |
| `http_api/v1/sync_api.py` | 同步路由（原 v1 行为） |
| `http_api/v1/async_api.py` | 异步任务提交 / 状态 / 结果分页 |
| `social_platform/tasks/` | Celery 应用、Beat 示例、异步执行入口 |
| `social_platform/services/` | `task_service` / `result_service`（HTTP 与 Worker 共用） |
| `social_platform/models/` | MySQL ORM：`feishu_async_tasks`、分平台 `feishu_*_results` |
| `social_platform/database/` | 连接、可选 `schema.sql` 建表脚本 |
| `celery_jobs/celery_app.py` | **兼容入口**：转发至 `social_platform.tasks.celery_app` |
| `HTTP_API.md` | **HTTP 数据接口**说明（`X-API-KEY`、`POST /api/v1/run`） |
| `requirements-http.txt` | 运行 `run.py` 所需依赖 |
| `workers/` | 仅 **`douyin_worker/`**、**`xhs_worker/`** |
| `social_platform/` | 共享 HTTP / 聚合任务 / 响应与 Schema（供上述 Worker 引用） |
| `extra/` | 非运行时占位或历史残留（如原 `multi_social` 的依赖清单） |
| `contracts/` | 请求/响应 JSON 的文档与 Schema，**非运行时共享库** |
| `.env` | 本地密钥与 URL；勿提交。可复制 **`python/.env.example`** |

## 设计原则

1. **隔离**：`server` / `feishu` 与 `python/workers/*` 无 Python 依赖关系。
2. **Worker 自治**：各 Worker 自带依赖文件与 Python 版本策略。
3. **契约**：路径与 JSON 形状见各 Worker `README.md` 与 `contracts/`。

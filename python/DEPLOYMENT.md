# 部署与启动指南

本文说明 **FastAPI HTTP** 与 **Celery Worker** 的安装、本地开发、生产部署与并发调优。接口字段见 **`HTTP_API.md`**，架构概览见 **`README.md`**。

---

## 1. 架构与进程分工

```
                    ┌─────────────────────────────────────┐
                    │  客户端 / 飞书插件 / 业务后端        │
                    └──────────────────┬──────────────────┘
                                       │ HTTP
                    ┌──────────────────▼──────────────────┐
                    │  FastAPI（run.py / uvicorn）         │
                    │  - 同步 search-page / search-all    │
                    │  - 异步任务提交 / 状态 / 结果 / 验收  │
                    │  - 内置调度轮询（默认每 15s）        │
                    └───────┬──────────────────┬──────────┘
                            │                  │
                     MySQL  │                  │ Redis
                            │                  │
              ┌─────────────▼────────┐   ┌─────▼──────────────────┐
              │ feishu_async_tasks   │   │ Broker + 调度 ZSET      │
              │ feishu_*_results     │   └─────┬────────────────────┘
              └──────────────────────┘         │
                    ┌──────────────────────────▼──────────────────┐
                    │  Celery Worker（必须单独进程）                   │
                    │  - run_social_async_task：实际采集与落库         │
                    │  - worker_ready：从 MySQL 恢复 Redis 调度        │
                    └─────────────────────────────────────────────────┘
```

| 组件 | 是否必须 | 作用 |
|------|----------|------|
| **FastAPI**（`run.py`） | 是 | 对外 API；默认在进程内轮询到期异步任务 |
| **Celery Worker** | 异步/定时采集 **必须** | 消费队列中的采集任务 |
| **Celery Beat** | 一般 **否** | 仅在没有 HTTP、且 `ASYNC_SCHEDULE_BEAT_ENABLED=1` 时替代内置轮询 |
| **Redis** | 是（异步） | Celery Broker；异步任务调度 ZSET |
| **MySQL** | 异步 **必须** | 任务元数据与分平台结果表 |

> **说明**：原 `celery_jobs/` 目录仅为 `celery -A` 的兼容转发，已删除。统一使用  
> **`social_platform.tasks.celery_app:celery_app`**。

---

## 2. 环境准备

### 2.1 系统要求

- **Python 3.9.x**（见 `pyproject.toml`，勿用 3.10+）
- **Celery 默认推荐 `gevent`**（I/O 采集）；Linux 可选用 `prefork` 多进程
- **Redis**、**MySQL 5.7+ / 8.x**

### 2.2 安装依赖

```bash
cd python
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux:   source .venv/bin/activate
pip install -r requirements-http.txt
```

### 2.3 配置文件

环境变量与 `server/`、Vite 前端**共用仓库根**（`social_platform/env_bootstrap.py`、`config/settings.py` 加载 `.env` → `.env.local`）：

```bash
# 在仓库根目录
cp .env.test .env
# 可选：cp .env.local.example .env.local
# 编辑 .env，至少配置：
#   DATABASE_URL=mysql+pymysql://user:pass@127.0.0.1:3306/feishu_keyword?charset=utf8mb4
#   REDIS_URL=redis://127.0.0.1:6379/0
#   CELERY_BROKER_URL=   # 留空则与 REDIS_URL 相同（推荐）
```

完整字段见仓根 **`.env.example`**；Docker / GitLab 部署见 **`docs/DEPLOY.md`**。

**常见错误**：`CELERY_BROKER_URL` 指向未启动的 RabbitMQ（`amqp://...`）会导致 `WinError 10061`。本地请留空或显式设为 Redis URL。

### 2.4 数据库

- 生产：用迁移脚本 / DBA 流程建表（`social_platform/database/schema.sql` 作参考）
- 开发：可设 `ASYNC_TASK_DB_AUTO_CREATE=1`；`DATABASE_RUN_MIGRATIONS=1` 在 HTTP 启动时补列

---

## 3. 本地开发启动（最小可用）

在 **`python/`** 目录开 **两个终端**（共用仓根 **`.env`**）：

**终端 1 — HTTP**

```bash
cd python
python run.py
```

**终端 2 — Celery Worker（gevent × 4，适合 I/O 采集）**

```bash
cd python
pip install -r requirements-http.txt   # 含 gevent
celery -A social_platform.tasks.celery_app worker -l info -P gevent -c 4 --prefetch-multiplier=1
```

或在 `.env` 中设置 `CELERY_WORKER_POOL=gevent`、`CELERY_WORKER_CONCURRENCY=4` 后简写：

```bash
celery -A social_platform.tasks.celery_app worker -l info
```

验证：

- `GET http://127.0.0.1:8765/api/v1/health`
- 文档：`http://127.0.0.1:8765/docs`
- ApiFox文档 `https://s.apifox.cn/ef07b14c-bbfd-4ed9-b26b-5bf796bfa15e`

开发热重载（仅 HTTP，单进程）：

```bash
set HTTP_RELOAD=1
python run.py
```

调试同步执行 Celery（**勿用于生产**）：

```bash
# .env
CELERY_TASK_ALWAYS_EAGER=1
```

此时可不启 Worker，但无法模拟队列积压与多 Worker 行为。

---

## 4. 提高并发

### 4.1 FastAPI / Uvicorn

| 方式 | 命令 / 配置 | 说明 |
|------|-------------|------|
| 多 worker 进程 | `HTTP_WORKERS=4 python run.py` | `run.py` 在非 reload 时传给 uvicorn |
| 命令行 | `uvicorn http_service:app --host 0.0.0.0 --port 8765 --workers 4` | 与 `run.py` 等价，适合 systemd |
| Gunicorn + Uvicorn | 见 §5.3 | 生产常用 |

建议：

- CPU 核数附近起步，例如 `workers = 2 * CPU + 1` 再压测调整
- **不要** 与 `HTTP_RELOAD=1` 同时使用多 worker
- 内置异步调度轮询跑在 **每个** HTTP worker 内；多 worker 时依赖 Redis 锁防重复 dispatch（见 `async_dispatch_loop`）。生产若 worker 数很多，可改为 **单实例 HTTP + 多 Celery Worker**，或关闭 HTTP 轮询改 Beat（§4.3）

### 4.2 Celery Worker

**推荐（Windows / Linux 通用，I/O 采集）**

```bash
cd python
celery -A social_platform.tasks.celery_app worker -l info -P gevent -c 4 --prefetch-multiplier=1
```

| 参数 | 含义 |
|------|------|
| `-P gevent` | 协程池，适合 HTTP 等待型任务；Windows 上可避免 prefork 的 `_loc` 问题 |
| `-c 4` | 4 个并发 greenlet（可通过 `.env` 的 `CELERY_WORKER_CONCURRENCY` 默认） |
| `--prefetch-multiplier=1` | 长任务时避免单 worker 囤积过多消息 |

`.env` 默认（与上表等价，可省略命令行参数）：

```env
CELERY_WORKER_POOL=gevent
CELERY_WORKER_CONCURRENCY=4
CELERY_WORKER_PREFETCH_MULTIPLIER=1
```

**Linux 多进程（CPU 密集或需进程隔离时）**

```bash
celery -A social_platform.tasks.celery_app worker -l info -P prefork -c 8 --prefetch-multiplier=1
```

| 参数 | 含义 |
|------|------|
| `-P prefork` | 多子进程（默认池） |
| `--autoscale=10,3` | 可选：负载高时扩到 10、空闲缩到 3 |

采集任务多为 **I/O 等待**，优先 **gevent**；`-c` 可略高于 CPU 核数，以队列长度与第三方限流为准。

**Windows 注意**

- 未配置 `CELERY_WORKER_POOL` 时仍回退 `solo`（单进程）
- 已配置 `gevent` 时请安装依赖：`pip install -r requirements-http.txt`

### 4.3 调度：避免重复扫描

默认：

```env
ASYNC_DISPATCH_HTTP_ENABLED=1
ASYNC_SCHEDULE_BEAT_ENABLED=0
```

仅当 **不部署 HTTP**、只有 Celery 时：

```env
ASYNC_DISPATCH_HTTP_ENABLED=0
ASYNC_SCHEDULE_BEAT_ENABLED=1
```

```bash
celery -A social_platform.tasks.celery_app beat -l info
```

**切勿** 同时开启 HTTP 轮询与 Beat 的 `tick_async_schedule_dispatch`（会重复投递）。

---

## 5. 生产部署流程

### 5.1 推荐拓扑

```
[Nginx] → [Uvicorn/Gunicorn × N] → MySQL
                ↓
         [Celery Worker × M] → Redis (broker + 调度)
```

最小生产：**1～2 个 HTTP 实例 + 2～4 个 Celery Worker 进程（或 1 台机多 `-c`）**，共用 `.env`。

### 5.2 部署检查清单

1. [ ] `pip install -r requirements-http.txt`（固定版本可锁 `pip freeze`）
2. [ ] `.env`：`DATABASE_URL`、`REDIS_URL`、业务 `YDDM_*` 等
3. [ ] `CELERY_BROKER_URL` 留空或 Redis；**不要**误配 RabbitMQ
4. [ ] `CELERY_TASK_ALWAYS_EAGER=0`
5. [ ] `ASYNC_DISPATCH_HTTP_ENABLED=1` 且 `ASYNC_SCHEDULE_BEAT_ENABLED=0`（有 HTTP 时）
6. [ ] MySQL 表与迁移已执行
7. [ ] 防火墙：仅暴露 Nginx 端口；Redis/MySQL 内网
8. [ ] 启动顺序：**Redis → MySQL → Celery Worker → HTTP**（Worker 先启可恢复调度）
9. [ ] 健康检查：`GET /api/v1/health`
10. [ ] 日志采集与磁盘（结果表增长）

### 5.3 systemd 示例（Linux）

**`/etc/systemd/system/feishu-http.service`**

```ini
[Unit]
Description=Feishu Keyword HTTP API
After=network.target mysql.service redis.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/feishu_keyword/python
EnvironmentFile=/opt/feishu_keyword/.env
Environment=HTTP_WORKERS=4
ExecStart=/opt/feishu_keyword/python/.venv/bin/gunicorn http_service:app \
  -k uvicorn.workers.UvicornWorker \
  -b 0.0.0.0:8765 \
  -w 4 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

安装 Gunicorn：`pip install 'gunicorn>=21,<23'`

**`/etc/systemd/system/feishu-celery.service`**

```ini
[Unit]
Description=Feishu Keyword Celery Worker
After=network.target redis.service mysql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/feishu_keyword/python
EnvironmentFile=/opt/feishu_keyword/.env
ExecStart=/opt/feishu_keyword/python/.venv/bin/celery \
  -A social_platform.tasks.celery_app worker \
  -l info -P gevent -c 4 --prefetch-multiplier=1
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable feishu-http feishu-celery
sudo systemctl start feishu-celery
sudo systemctl start feishu-http
```

### 5.4 Nginx 反向代理（片段）

```nginx
upstream feishu_http {
    server 127.0.0.1:8765;
    keepalive 32;
}

server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://feishu_http;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 300s;
        client_max_body_size 10m;
    }
}
```

### 5.5 Docker（思路）

可多阶段镜像：基础镜像 Python 3.9，复制 `python/`，`pip install -r requirements-http.txt`，分别用 `CMD` 跑 HTTP 与 Celery（两个 service 共用 image、不同 command）。挂载 `.env` 或 K8s Secret。Broker/DB 用 compose 网络内 Redis、MySQL 服务名。

### 5.6 发布与回滚

1. `git pull` / 发布制品到 `/opt/feishu_keyword`
2. `pip install -r requirements-http.txt`（依赖变更时）
3. 执行 DB 迁移（若有）
4. `systemctl restart feishu-celery`（先 Worker，恢复 Redis 调度）
5. `systemctl restart feishu-http`
6. 抽查 health、提交一条测试异步任务、查 `GET .../async/tasks/{id}`

回滚：恢复上一版本代码与镜像，重启两个服务；数据库回滚需单独脚本。

---

## 6. 环境变量速查

| 变量 | 默认 | 说明 |
|------|------|------|
| `HTTP_HOST` / `HTTP_PORT` | `0.0.0.0` / `8765` | HTTP 监听 |
| `HTTP_WORKERS` | `1` | Uvicorn 进程数（与 `HTTP_RELOAD` 互斥） |
| `HTTP_RELOAD` | 关 | 开发热重载 |
| `DATABASE_URL` | 空 | 未配置则异步接口 503 |
| `REDIS_URL` | `redis://127.0.0.1:6379/0` | Redis |
| `CELERY_BROKER_URL` | 空→同 REDIS | Broker |
| `CELERY_TASK_ALWAYS_EAGER` | `0` | `1`=同步调试 |
| `ASYNC_DISPATCH_HTTP_ENABLED` | `1` | HTTP 内调度轮询 |
| `ASYNC_DISPATCH_POLL_SECONDS` | `15` | 轮询间隔（秒） |
| `ASYNC_SCHEDULE_BEAT_ENABLED` | `0` | 无 HTTP 时用 Beat |
| `ASYNC_TASK_MAX_ACTIVE_PER_USER` | `10` | 单用户活跃任务上限 |

完整列表见仓根 **`.env.example`**。

---

## 7. 运维与排障

| 现象 | 可能原因 | 处理 |
|------|----------|------|
| `WinError 10061` / `OperationalError` | Broker 连不上 | 检查 Redis；`CELERY_BROKER_URL` 勿指向未启 RabbitMQ |
| 异步任务一直 `pending` | 未启 Worker | 启动 `celery worker` |
| 定时任务密集触发 | HTTP 与 Beat 双开 | 只保留一种调度（§4.3） |
| 调度时间差 8 小时 | 旧数据或客户端时区 | 新任务用墙钟字符串；见 `schedule_time.py` |
| Windows 上 Celery 报错 `_loc` | 误用 prefork | 改用 `-P gevent`（见 `CELERY_WORKER_POOL=gevent`） |
| `MISCONF ... stop-writes-on-bgsave-error` | Windows Redis BGSAVE fork/OOM 失败 | 见 **§7.1**；修复后重启 Worker |

### 7.1 Windows Redis：`MISCONF` 与 Celery 崩溃

**现象**：Celery Worker 报 `Unrecoverable error: ResponseError('MISCONF Redis is configured to save RDB snapshots...')`，随后退出。

**原因**（常见于 [tporadowski/redis](https://github.com/tporadowski/redis) on Windows）：

1. Redis 按 `save` 规则触发后台 RDB（`BGSAVE`），通过 **fork** 子进程写 `dump.rdb`。
2. fork 子进程在加载配置或分配内存时 **OOM**（`zmalloc_default_oom`），日志见 `D:\Redis\server_log.txt`：`fork operation failed`、`Background saving terminated by signal 1`。
3. 默认 `stop-writes-on-bgsave-error yes` 时，一次 bgsave 失败会 **禁止所有写命令**，Broker 入队、调度 ZSET、任务缓存均失败。

这与 **磁盘满** 无关（可先 `redis-cli INFO persistence` 看 `rdb_last_bgsave_status`）。

**处理步骤**：

1. 确认 Redis 可写：`redis-cli SET __test__ 1`（或指定库 `redis-cli -n 3 SET __test__ 1`）。
2. 开发机一键缓解（允许 bgsave 失败时仍可写入，调度可从 MySQL 恢复）：

   ```powershell
   cd python
   powershell -ExecutionPolicy Bypass -File scripts/redis_windows_fix.ps1
   ```

   或手动：

   ```bash
   redis-cli CONFIG SET stop-writes-on-bgsave-error no
   redis-cli CONFIG REWRITE
   ```

3. **重启 Celery Worker**（及仍在跑的 `run.py` 若已报错）。
4. 若日志仍频繁 fork 失败：关闭占用内存的程序、重启 Redis 服务；或换 WSL/Linux Redis；生产环境勿长期关闭 `stop-writes-on-bgsave-error`。

查看 Celery 注册任务：

```bash
celery -A social_platform.tasks.celery_app inspect registered
```

---

## 8. 已注册 Celery 任务

| 任务名 | 作用 |
|--------|------|
| `social_platform.tasks.worker_tasks.run_social_async_task` | 执行异步采集 |
| `social_platform.tasks.worker_tasks.tick_async_schedule_dispatch` | Beat 调度扫描（可选） |
| `social_platform.tasks.worker_tasks.run_jzl_social` | Beat 示例聚合（`CELERY_BEAT_ENABLED=1` 时） |

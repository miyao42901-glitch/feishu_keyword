# Workers（爬虫脚本）

本目录**仅保留**在统一 HTTP 中挂载的两个平台 Worker：

- **`douyin_worker/`** — 抖音（`parser.py`、`spider.py`、`_job.py`）
- **`xhs_worker/`** — 小红书（同上）

共享逻辑（HTTP 客户端、爬虫基类、`aggregated_job`、`TaskEnvelope` 等）在 **`../social_platform/`**，不在本目录下。

## 约束

- **禁止**被 `server` 或 `feishu` 以 Python `import` 引用。
- **禁止** `import` 仓库内 `server.app` 等业务包；数据经 **`python/run.py`** 暴露的 HTTP 传入。
- 启动前需将 **`python/`** 与 **`python/workers/`** 加入 `PYTHONPATH`（`run.py` / `http_service.py` 已处理）。

## 新建 Worker

若新增第三平台，仍在 `workers/<name>/` 下建目录，并在 `http_service.py` / `http_api/` 与 `social_platform/aggregated_job.py` 中接线；契约见 **`../contracts/`**。

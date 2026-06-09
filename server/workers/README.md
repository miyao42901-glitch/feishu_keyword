# server/workers

四平台 Celery Worker（抖音 / 小红书 / 公众号 / 微信视频号）。

- 共享 HTTP 与时间工具在 **`server/social_platform/`**（`run.py` / `http_service.py` 已将 `server/` 与 `server/workers` 加入 `sys.path`）。
- 数据经 **`server/run.py`** 暴露的 HTTP API 传入，Worker 不直接依赖前端代码。

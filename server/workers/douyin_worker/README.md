# douyin_worker

抖音单平台 Worker。解析逻辑在 **`parser.py`**（`DouyinParser.parse`），编排与业务重试在 **`spider.py`**。

共享 HTTP 与时间工具在 **`server/social_platform/`**（`run.py` / `http_service.py` 已将 `server/` 与 `server/workers` 加入 `sys.path`）。

## action

- `douyin_search_page`：`key`, `keyword`, `cursor`, `logid`
- `douyin_search_all`：`key`, `keyword`, `max_pages`

默认接口见 `social_platform/urls.py` 中的 `DOUYIN_GENERAL_URL`，可用环境变量 `DOUYIN_GENERAL_URL` 覆盖。

# xhs_worker

小红书单平台 Worker。解析在 **`parser.py`**，请求与业务重试在 **`spider.py`**。

共享 HTTP 与时间工具在 **`server/social_platform/`**（见 `douyin_worker/README.md`）。

## action

- `xhs_search_page`：`key`, `keyword`, `page`
- `xhs_search_all`：`key`, `keyword`, `max_pages`

默认 URL：`social_platform.urls.XHS_GENERAL_URL`；环境变量 `XHS_GENERAL_URL` 可覆盖。

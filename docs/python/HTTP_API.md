# 统一 HTTP 数据接口说明

服务由 `run.py` 启动，默认监听 **`http://<主机>:8765`**（可用环境变量 `HTTP_HOST`、`HTTP_PORT` 覆盖）。

交互式文档：服务启动后访问 **`http://<主机>:<端口>/docs`**（Swagger UI）、**`/redoc`**。

---

## 0. 接口一览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/health` | 健康检查 |
| POST | `/api/v1/run` | 聚合入口（snake_case `action`） |
| POST | `/api/v1/sync/douyin/search-page` | 抖音单页搜索（同步） |
| POST | `/api/v1/sync/douyin/search-all` | 抖音多页搜索（同步） |
| POST | `/api/v1/sync/xhs/search-page` | 小红书单页搜索（同步） |
| POST | `/api/v1/sync/xhs/search-all` | 小红书多页搜索（同步） |
| POST | `/api/v1/async/tasks` | 提交异步任务（kebab-case `action`） |
| POST | `/api/v1/async/tasks/edit` | 编辑任务（部分更新） |
| GET | `/api/v1/async/tasks` | 任务列表与汇总（`X-API-Key` + `X-User-Id`） |
| GET | `/api/v1/async/tasks/{task_id}` | 查询任务状态 |
| GET | `/api/v1/async/tasks/{task_id}/results` | 分页查询落库结果 |
| POST | `/api/v1/async/tasks/{task_id}/cancel` | 取消任务 |
| POST | `/api/v1/async/tasks/{task_id}/delete` | 删除任务（停止 Celery 并删库） |
| POST | `/api/v1/async/tasks/{task_id}/restart` | 重启任务 |
| GET | `/api/v1/results/acceptance` | 待验收 id（平台 → id 列表） |
| POST | `/api/v1/results/acceptance` | 批量验收（`is_upload=1`） |

下文以 **`BASE = http://127.0.0.1:8765`** 为例，业务路径均为 **`BASE + /api/v1` + 资源路径**。

**Content-Type：** 除 `GET` 外均为 **`application/json`**。

---

## 1. 路径版本

当前对外 API 统一挂在 **`/api/v1`** 下（见 `http_api/versions.py` 中 `API_V1_PREFIX`）。

---

## 2. 鉴权与请求体约定

### 2.1 同步接口 `POST /api/v1/sync/...`

| 位置 | 说明 |
|------|------|
| **Header `X-API-Key`** | 必填，下游 YDDM / 大加拉等使用的 **`key`** |
| **Header `X-User-Id`** | 必填，用户标识，用于结果落库 |
| **JSON Body** | 仅业务字段（如 `keyword`），**不要**包一层 `body` / `params` |

```bash
curl -s -X POST "http://127.0.0.1:8765/api/v1/sync/douyin/search-page" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY" \
  -H "X-User-Id: user_001" \
  -d "{\"keyword\": \"人民日报\"}"
```

### 2.2 聚合 `POST /api/v1/run`

JSON：`action` + `params`。`params` 内凭证可用 **`key`** 或 **`X-API-KEY`**（映射为下游 `key`；二者都有时非空 **`key`** 优先）。见第 8 节。

### 2.3 异步 `POST /api/v1/async/tasks`

| 位置 | 说明 |
|------|------|
| **Header `X-API-Key`** | 必填 |
| **Header `X-User-Id`** | 必填，须与 yddm `users/me` 返回的用户 id 一致 |
| **JSON Body** | `{ "action": "<kebab-case>", "body": { ... } }`，`body` 字段与同平台同步 search 接口一致 |
| **Query `priority`** | 可选，**0～9**，默认 `0`，数值越大 Celery 优先级越高 |

异步 **GET** 接口可选带 **`X-User-Id`**：若提供且与任务所属用户不一致，返回 **403**。

**校验失败：** 可能返回 **422**（FastAPI 标准校验结构）或 **400**（`code` + `msg`）。

### 2.4 限流（按接口独立 scope）

同一用户（`X-User-Id`，无则按 IP）在 **60 秒** 滑动窗口内计数；**每个 HTTP 路由单独一个 Redis 桶**，互不占额度（勿再用统一的 `async_list` 等合并 scope）。

| 方法 | 路径 | scope | 默认上限 / 60s |
|------|------|-------|----------------|
| POST | `/api/v1/async/tasks` | `async_submit` | 30 |
| POST | `/api/v1/async/tasks/edit` | `async_task_edit` | 60 |
| GET | `/api/v1/async/tasks` | `async_task_list` | 60 |
| GET | `/api/v1/async/tasks/{task_id}` | `async_task_status` | 120 |
| GET | `/api/v1/async/tasks/{task_id}/results` | `async_task_results` | 120 |
| POST | `/api/v1/async/tasks/{task_id}/cancel` | `async_task_cancel` | 30 |
| POST | `/api/v1/async/tasks/{task_id}/delete` | `async_task_delete` | 30 |
| POST | `/api/v1/async/tasks/{task_id}/restart` | `async_task_restart` | 30 |
| GET | `/api/v1/results/acceptance` | `result_acceptance_pending` | 120 |
| POST | `/api/v1/results/acceptance` | `result_acceptance_accept` | 60 |

超限返回 **429**，`code` 为限流业务码，响应头含 **`Retry-After`**（秒）。常量定义见 `http_api/rate_limit_scopes.py`。

---

## 3. 统一响应格式

成功或业务层错误时，HTTP 状态码多为 **200**（异步未配置库为 **503**，任务不存在为 **404**），通过 **`code`** 区分：

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | int | **`0` 表示成功**；非 0 见 `social_platform/api_status_codes.py`（如 **`1001`** 余额不足、**`1021`** 异步任务数超限） |
| `msg` | string | 人类可读说明 |
| `data` | object \| null | 负载，结构因接口而异（见下表） |

### 3.1 响应 `data` 结构对照

| 接口类型 | 成功时 `data` 结构 |
|----------|-------------------|
| `GET /health` | `{ "status": "ok" }`（**无** `result` / `meta` 包装） |
| 同步 search / `POST /run` | `{ "result": <Worker 返回>, "meta": { "worker", "version", ... } }` |
| 异步三个接口 | `{ "result": <业务数据>, "meta": { "worker": "async_api", "platform", "source", "action", "result_table", ... } }` |

**同步 / 异步成功示例：**

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "result": { },
    "meta": {
      "worker": "douyin_worker",
      "version": "1.0.0",
      "platform": "douyin",
      "source": "douyin",
      "action": "douyin-search-all",
      "result_table": "feishu_douyin_results"
    }
  }
}
```

> 同步接口的 `meta` 主要来自 Worker（如 `douyin_worker`），并可能合并多页采集字段（`pages_fetched`、`records_returned` 等，见第 12.7 节）。异步接口的 `meta` 由 HTTP 层注入，用于标识平台与结果表，**不含**第三方采集过程字段。

**业务失败示例：**

```json
{
  "code": 400,
  "msg": "参数错误",
  "data": null
}
```

---

## 4. 健康检查

### `GET /api/v1/health`

无需鉴权。

```bash
curl -s "http://127.0.0.1:8765/api/v1/health"
```

**成功响应：**

```json
{
  "code": 0,
  "msg": "ok",
  "data": { "status": "ok" }
}
```

---

## 5. 聚合任务 `POST /api/v1/run`

单入口按 **`action`**（**snake_case**）分发到抖音或小红书 Worker（`social_platform/aggregated_job.py`）。

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `action` | string | 是 | 见下表 |
| `params` | object | 否 | 默认 `{}`；业务字段见第 8 节 |

**支持的 `action`：**

| `action` | 说明 |
|----------|------|
| `douyin_search_page` | 抖音单页搜索 |
| `douyin_search_all` | 抖音多页聚合 |
| `xhs_search_page` | 小红书单页搜索 |
| `xhs_search_all` | 小红书多页聚合 |

**请求示例：**

```bash
curl -s -X POST "http://127.0.0.1:8765/api/v1/run" \
  -H "Content-Type: application/json" \
  -d "{\"action\":\"douyin_search_page\",\"params\":{\"X-API-KEY\":\"YOUR_SECRET\",\"keyword\":\"关键词\"}}"
```

**成功响应：** 与第 3 节一致，`data.result` 为 Worker 原始 `data`，`data.meta` 含 `jzl_social` 与具体 Worker 信息。

不支持的 `action` 时，`code` 非 0，`msg` 中含 `unsupported action`。

---

## 6. 抖音同步接口

路径前缀：**`/api/v1/sync/douyin`**。均需 **Header `X-API-Key` + `X-User-Id`** + **扁平 JSON Body**。

### 6.1 单页搜索 `POST .../search-page`

**Body 参数（`DouyinSearchPageBody`）：**

| 字段 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `keyword` | string | 是 | — | 搜索关键词，**1～100** 字 |
| `cursor` | string | 否 | `""` | 翻页游标；首页留空 |
| `log_id` / `logid` | string | 否 | `""` | 翻页参数；首页留空 |
| `sort_type` | string | 否 | `"0"` | `0` 综合，`1` 最多点赞，`2` 最新发布 |
| `publish_time` | string | 否 | `"0"` | `0` 不限，`1` 1 天内，`7` 7 天内，`180` 180 天内 |
| `filter_duration` | string | 否 | `"0"` | `0` 不限，`0-1` 1 分钟内，`1-5` 1～5 分钟，`1-10000` 5 分钟以上 |
| `content_type` | string | 否 | `"0"` | `0` 不限，`1` 视频，`2` 图文 |
| `exclude_words` | string | 否 | `""` | 排除词，空格分隔 |

```bash
curl -s -X POST "http://127.0.0.1:8765/api/v1/sync/douyin/search-page" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY" \
  -H "X-User-Id: user_001" \
  -d "{\"keyword\":\"人民日报\",\"sort_type\":\"2\",\"publish_time\":\"7\"}"
```

**成功时 `data.result`：** 第三方单页原始结构（含 `data` 列表、`cursor`、`log_id` 等，以实际返回为准）。配置 `DATABASE_URL` 时整页结果会落库 `feishu_douyin_results`。

---

### 6.2 多页搜索 `POST .../search-all`

**Body 参数（`DouyinSearchAllBody` = 公共多页字段 + 抖音扩展）：**

#### 公共多页字段（`PublicSearchAllBody`，小红书 search-all 共用）

| 字段 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `keyword` | string | 是 | — | 搜索关键词 |
| `fetch_count` | int | 否 | `100` | 最多采集**不重复**条数（按 `aweme_id`），**1～500**，达到即停 |
| `sort_type` | int | 否 | `1` | `0`/`1`：不按客户端发布时间截窗；**`2`**：启用时间窗（见第 12 节） |
| `time_range` | int | 否 | `7` | 天数，**≥1**；**仅 `sort_type=2` 时**参与客户端时间窗 |
| `exclude_words` | string | 否 | `""` | 排除词，空格分隔，过滤标题/描述 |

#### 抖音扩展字段（可选，传给第三方筛选 / 翻页）

| 字段 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `cursor` | string | 否 | `""` | 可选起始翻页游标 |
| `log_id` / `logid` | string | 否 | `""` | 可选起始翻页参数 |
| `publish_time` | string | 否 | `""` | 第三方发布时间筛选（空则下游默认） |
| `filter_duration` | string | 否 | `""` | 视频时长筛选 |
| `content_type` | string | 否 | `""` | 内容形式筛选 |

**落库：** 每向第三方成功拉取一页并过滤后写入 `feishu_douyin_results`（需 `DATABASE_URL`）。

**最简请求：**

```json
{ "keyword": "穿搭" }
```

等价于 `fetch_count=100`、`sort_type=1`、`time_range=7`（`time_range` 在 `sort_type≠2` 时不截断）。

**按近 7 天时间窗：**

```json
{
  "keyword": "穿搭",
  "fetch_count": 100,
  "sort_type": 2,
  "time_range": 7
}
```

```bash
curl -s -X POST "http://127.0.0.1:8765/api/v1/sync/douyin/search-all" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY" \
  -H "X-User-Id: user_001" \
  -d "{\"keyword\":\"穿搭\",\"fetch_count\":100,\"sort_type\":2,\"time_range\":7}"
```

**成功时 `data.result` 常见字段：** `records`（结果列表）、`balance`、`insufficient_balance`、`last_error`；`data.meta` 含 `pages_fetched`、`records_returned`、`fetch_count_cap`、时间窗字段等（见第 12.7 节）。

**采集行为详解：** 第 12 节。

---

## 7. 小红书同步接口

路径前缀：**`/api/v1/sync/xhs`**。均需 **Header `X-API-Key` + `X-User-Id`** + **扁平 JSON Body**。

### 7.1 单页搜索 `POST .../search-page`

**Body 参数（`XhsSearchPageBody`）：**

| 字段 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `keyword` | string | 是 | — | 搜索关键词 |
| `page` | int | 否 | `1` | 页码，≥1 |
| `sort_type` | string | 否 | `"0"` | `0` 综合，`1` 最多点赞，`2` 最新发布 |
| `content_type` | string | 否 | `""` | `video` 视频笔记，`note` 普通笔记，空=不限 |
| `note_time` | string | 否 | `"0"` | `0` 不限，`1` 1 天内，`7` 7 天内，`180` 180 天内 |
| `exclude_words` | string | 否 | `""` | 排除词 |

请求体会映射为 YDDM 字段：`sort`（如 `time_descending`）、`note_type`、`note_time`（如 `week`）等。

```bash
curl -s -X POST "http://127.0.0.1:8765/api/v1/sync/xhs/search-page" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY" \
  -H "X-User-Id: user_001" \
  -d "{\"keyword\":\"穿搭博主\",\"page\":1,\"sort_type\":\"2\",\"content_type\":\"video\",\"note_time\":\"7\"}"
```

---

### 7.2 多页搜索 `POST .../search-all`

**Body 参数（`XhsSearchAllBody`）：**

#### 必填 / 常用（与抖音公共字段相同）

| 字段 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `keyword` | string | 是 | — | 搜索关键词 |
| `fetch_count` | int | 否 | `100` | **1～500**，按 `note_id` 去重累计 |
| `sort_type` | int | 否 | `1` | 同抖音；**`2`** 时启用客户端时间窗 |
| `time_range` | int | 否 | `7` | 仅 `sort_type=2` 生效 |
| `exclude_words` | string | 否 | `""` | 排除词 |

> 模型中还声明了 `cursor`、`log_id`、`publish_time`、`filter_duration`、`content_type`（与抖音模型对齐），**小红书多页 Worker 不使用**，请求中可省略。

**落库：** 每页写入 `feishu_xhs_results`。

```bash
curl -s -X POST "http://127.0.0.1:8765/api/v1/sync/xhs/search-all" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY" \
  -H "X-User-Id: user_001" \
  -d "{\"keyword\":\"穿搭博主\",\"fetch_count\":50,\"sort_type\":2,\"time_range\":7}"
```

**单页筛选**（`content_type`、`note_time` 等）请使用 **search-page**；search-all 主要通过 `sort_type` / `time_range` 控制客户端时间窗与条数上限。

**采集行为详解：** 第 12 节。

---

## 8. `POST /api/v1/run` 的 `params` 与异步 `body` 对照

| 同步路径 | `POST /run` 的 `action` | 异步 `action` | `body` / `params` 业务字段 |
|----------|-------------------------|---------------|---------------------------|
| `.../douyin/search-page` | `douyin_search_page` | `douyin-search-page` | `keyword`；可选 `cursor`、`log_id`/`logid`、`sort_type`、`publish_time`、`filter_duration`、`content_type`、`exclude_words` |
| `.../douyin/search-all` | `douyin_search_all` | `douyin-search-all` | `keyword`；可选 `fetch_count`、`sort_type`、`time_range`、`exclude_words`；抖音可选 `cursor`、`log_id`、`publish_time`、`filter_duration`、`content_type` |
| `.../xhs/search-page` | `xhs_search_page` | `xhs-search-page` | `keyword`；可选 `page`、`sort_type`、`content_type`、`note_time`、`exclude_words` |
| `.../xhs/search-all` | `xhs_search_all` | `xhs-search-all` | `keyword`；可选 `fetch_count`、`sort_type`、`time_range`、`exclude_words` |
| — | — | `douyin-search-detail` | `post_id`（作品 ID / aweme_id），**未实现**，任务会失败 |
| — | — | `xhs-search-detail` | `post_id`（笔记 note_id），**未实现**，任务会失败 |

另加 **`key`** 或 **`X-API-KEY`**（仅 `POST /run` 的 `params` 需要；同步/异步用 Header `X-API-Key`）。

---

## 9. 环境与配置

见 **`python/.env.example`**，常用项：

| 变量 | 说明 |
|------|------|
| `HTTP_HOST` / `HTTP_PORT` | HTTP 监听地址与端口 |
| `DOUYIN_GENERAL_URL` / `XHS_GENERAL_URL` | 第三方 API 地址覆盖 |
| `DATABASE_URL` | MySQL 连接串；为空则异步接口 **503** |
| `ASYNC_TASK_DB_AUTO_CREATE` | 开发环境启动时自动建表 |
| `REDIS_URL` / `CELERY_BROKER_URL` | Celery Broker |
| `ASYNC_DISPATCH_HTTP_ENABLED` | `run.py` 是否在后台扫描 Redis 调度（默认 **1**，与 Worker 配合即可） |
| `ASYNC_DISPATCH_POLL_SECONDS` | 上述扫描间隔（秒，默认 **15**） |
| `ASYNC_SCHEDULE_BEAT_ENABLED` | 无 HTTP 时用 Celery Beat 做同样扫描（默认 **0**） |
| `ASYNC_TASK_RUNNING_STALE_SECONDS` | `running` 超时重置为 `pending`（默认 **1800**） |
| `ASYNC_RESULTS_DEFAULT_LIMIT` | `GET .../results` 默认 `limit`（最大 **200**） |
| `ASYNC_TASK_MAX_ACTIVE_PER_USER` | 单用户 `pending`+`running` 任务上限，超限 **429**、`code=1021` |
| `YDDM_USERS_ME_URL` | 提交异步任务前校验用户 |

**推荐部署**（`python/` 目录，共用 `.env` 中的 `DATABASE_URL` 与 `REDIS_URL`）：

```bash
python run.py
celery -A social_platform.tasks.celery_app worker -l info -P gevent -c 4 --prefetch-multiplier=1
```

并发与 systemd / Nginx 配置见 **`DEPLOYMENT.md`**。

任务记录写入 MySQL 表 `feishu_async_tasks`；`search-all` / `search-page` 采集结果写入对应 `feishu_*_results` 表（同步单次执行 `task_id` 可为空，验收走 `/api/v1/results/acceptance`）。

---

## 10. 异步任务（Celery + MySQL）

### 10.1 已注册 `action`（`social_platform/actions/registry.py`）

| `action` | 平台 | 落库 | 说明 |
|----------|------|------|------|
| `douyin-search-all` | douyin | 是 | 多页搜索，body 同 §6.2 |
| `douyin-search-page` | douyin | 是 | 单页搜索，body 同 §6.1 |
| `douyin-search-detail` | douyin | 否 | 占位，`body.post_id` 必填，执行未实现 |
| `xhs-search-all` | xhs | 是 | 多页搜索，body 同 §7.2 |
| `xhs-search-page` | xhs | 是 | 单页搜索，body 同 §7.1 |
| `xhs-search-detail` | xhs | 否 | 占位，`body.post_id` 必填，执行未实现 |

---

### 10.2 提交任务 `POST /api/v1/async/tasks`

**Header：** `X-API-Key`、`X-User-Id`（必填）

**Query：**

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `priority` | int | `0` | **0～9**，Celery 优先级 |

**Body：**

| 字段 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `task_name` | string | 是 | — | 任务名称，**1～100** 字符，不能为空字符串 |
| `action` | string | 是 | — | 上表 kebab-case 之一 |
| `body` | object | 否 | `{}` | 业务参数（**不含** `fetch_count`）；按 `action` 做 Pydantic 校验 |
| `task_start_time` | string | 是 | — | 定时窗口开始（ISO8601 或毫秒时间戳）；**无时区时按东八区（Asia/Shanghai）** |
| `task_end_time` | string | 是 | — | 定时窗口结束，须晚于开始时间与当前时间；无时区同上 |
| `interval_minutes` | int | 否 | `60` | 窗口内采集间隔（分钟），最小 **5** |
| `fetch_count` | int | 否 | `100` | 单次采集条数上限，**1～500**（与 `interval_minutes` 同级，不入 `body`） |

窗口内由 Celery 按 `interval_minutes` 周期执行；`fetch_count` 在每次执行时注入 `search-all` 类 action。

**请求示例（抖音 search-all）：**

```json
{
  "task_name": "完成项目报告",
  "action": "douyin-search-all",
  "body": {
    "keyword": "人民日报",
    "sort_type": 2,
    "time_range": 7
  },
  "task_start_time": "2026-05-18T00:00:00Z",
  "task_end_time": "2026-05-25T00:00:00Z",
  "interval_minutes": 60,
  "fetch_count": 100
}
```

**请求示例（小红书 search-all）：**

```json
{
  "task_name": "小红书穿搭采集",
  "action": "xhs-search-all",
  "body": {
    "keyword": "穿搭博主"
  },
  "task_start_time": "2026-05-18T00:00:00Z",
  "task_end_time": "2026-05-20T00:00:00Z",
  "interval_minutes": 30,
  "fetch_count": 50
}
```

**成功响应：**

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "result": {
      "task_id": 42,
      "status": "pending"
    },
    "meta": {
      "worker": "async_api",
      "version": "1.0.0",
      "platform": "douyin",
      "source": "douyin",
      "action": "douyin-search-all",
      "result_table": "feishu_douyin_results"
    }
  }
}
```

**常见错误：**

| HTTP | `code` / 体 | 说明 |
|------|-------------|------|
| 400 | `400` 或 `{"code":400,"message":"unsupported action"}` | 未知 `action`、缺少 `task_name` 或 body 校验失败 |
| 401 | `1005` 等 | 无效的 `X-API-Key`（yddm 校验失败） |
| 429 | `1021` | 该用户进行中任务数超限 |
| 503 | 非 0 | 未配置 `DATABASE_URL` |

---

### 10.3 查询状态 `GET /api/v1/async/tasks/{task_id}`

**Path：** `task_id` 为任务数字主键（字符串形式亦可）。

**Header：** `X-User-Id` 可选；若提供须与任务 `user_id` 一致。

**成功时 `data.result` 字段：**

| 字段 | 说明 |
|------|------|
| `task_id` | 任务 ID |
| `task_name` | 任务名称 |
| `user_id` | 所属用户 |
| `platform` | 由 `action` 推导（`douyin` / `xhs`），不入库 |
| `status` | `pending` / `running` / `success` / `failed` / `cancelled` 等 |
| `action` | 提交时的 kebab-case action |
| `error_message` | 失败摘要（最长 64 字符） |
| `celery_task_id` | Celery 任务 ID |
| `priority` | 0～9 |
| `cancel_requested` | 是否已请求取消 |
| `success_count` / `failed_count` | 落库成功 / 失败累计 |
| `task_start_time` / `task_end_time` | 定时窗口起止（ISO8601 UTC，`Z`） |
| `interval_minutes` | 采集间隔（分钟） |
| `fetch_count` | 单次采集条数上限 |
| `create_time` / `update_time` | ISO8601 UTC（带 `Z`） |

**`data.meta`：** 同 §10.2（含 `platform`、`source`、`result_table`）。

**404：** 任务不存在。

列表 `GET /api/v1/async/tasks` 的 `data.result.items[]` 中同样包含 `task_name` 字段。

---

### 10.3.1 编辑任务 `POST /api/v1/async/tasks/edit`

**Header：** `X-API-Key`、`X-User-Id`（必填，与提交/取消任务一致，经 yddm `users/me` 校验）

**Body（JSON）：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `task_id` | int | 是 | 任务 ID |
| `task_name` | string | 否 | 1～100 字符 |
| `interval_minutes` | int | 否 | ≥ 5；仅 **pending** 可改 |
| `fetch_count` | int | 否 | 1～500；仅 **pending** 可改 |
| `task_start_time` | string | 否 | 定时窗口开始；仅 **pending** 可改 |
| `task_end_time` | string | 否 | 定时窗口结束；仅 **pending** 可改 |
| `priority` | int | 否 | 0～9；仅 **pending** 可改 |

除 `task_name` 外，调度类字段仅在任务状态为 `pending` 时允许修改。**至少提供一个**要修改的字段（除 `task_id` 外）。

**成功响应：** `data.result` 为更新后的完整任务对象（字段同 §10.3，含 `task_name`）。

**示例：**

```bash
curl -s -X POST "http://127.0.0.1:8765/api/v1/async/tasks/edit" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY" \
  -H "X-User-Id: 12345" \
  -d '{"task_id": 42, "task_name": "完成项目报告（修订）"}'
```

**常见错误：**

| HTTP | `code` | 说明 |
|------|--------|------|
| 401 | `1005` 等 | `X-API-Key` 无效或未授权 |
| 503 | `1022` | 用户校验服务暂时不可用，请稍后重试 |
| 400 | `400` | 缺少 `task_id`、未提供可修改字段、`task_name` 长度不合法等 |
| 403 | `1020` | `X-User-Id` 与任务归属不一致 |
| 404 | `1023` | 任务不存在 |

服务端会记录编辑日志（用户、时间、任务 ID、变更字段及新值）。

---

### 10.3.2 删除任务 `POST /api/v1/async/tasks/{task_id}/delete`

**Header：** `X-User-Id`（必填，须与任务在库中的 `user_id` 一致）

**说明：** 删除接口**不调用** yddm 用户校验，避免「用户校验服务暂时不可用」时无法清理任务。`pending` / `running` / `success` / `failed` / **`cancelled`** 等任意状态均可删除。

**行为：**

1. 从 Redis 调度 ZSET 移除，并删除任务快照、`api_key` 缓存、投递锁
2. 若任务为 `pending` / `running`，对当前 `celery_task_id` 执行 `revoke`（`running` 时 `terminate=true` 以尝试终止正在执行的 Worker）
3. 删除 MySQL `feishu_async_tasks` 对应行；各平台结果表 `feishu_*_results` 中 `task_id` 关联行因 **ON DELETE CASCADE** 一并删除

**成功响应：**

```json
{
  "code": 0,
  "data": {
    "result": {
      "task_id": "42",
      "deleted": true
    }
  }
}
```

**常见错误：**

| HTTP | `code` | 说明 |
|------|--------|------|
| 404 | `1023` | 任务不存在 |
| 403 | `1020` | `X-User-Id` 与任务归属不一致 |

与「取消」不同：取消依赖 yddm 校验且已 `cancelled` 时返回 409；**删除**不依赖 yddm，且**已取消任务也可直接删除**。删除为不可恢复，请谨慎调用。

**示例：**

```bash
curl -s -X POST "http://127.0.0.1:8765/api/v1/async/tasks/42/delete" \
  -H "X-User-Id: 12345"
```

---

### 10.4 取消任务 `POST /api/v1/async/tasks/{task_id}/cancel`

**Header：** `X-API-Key`、`X-User-Id`（必填，与提交任务一致）

**行为：**

- MySQL 任务置为 `cancelled`，`cancel_requested=true`
- 若存在进行中的 Celery 消息则 `revoke`（不强制杀进程）
- **不删除** Redis 任务快照与 `api_key`，保留 **1 天**（`86400` 秒），便于后续重启读取 `success_count` 等
- 从调度 ZSET 移除，不再周期触发

**成功响应：**

```json
{
  "code": 0,
  "data": {
    "result": {
      "task_id": "7",
      "status": "cancelled"
    }
  }
}
```

**常见错误：**

| HTTP | `code` | 说明 |
|------|--------|------|
| 404 | `1023` | 任务不存在 |
| 403 | `1020` | 用户与任务归属不一致 |
| 409 | `1027` | 任务已取消，重复取消 |

---

### 10.5 重启任务 `POST /api/v1/async/tasks/{task_id}/restart`

**Header：** `X-API-Key`、`X-User-Id`（必填）

**适用状态：** `cancelled`、`success`、`failed` 等已结束状态；**不可**重启 `pending` / `running`。

**行为：**

1. 从 Redis 读取任务快照（含 `success_count`、`failed_count`、`body_json` 等）；若无缓存或缺少 `action`，回退 MySQL 任务表
2. 将计数写回 MySQL，`status` 置为 `pending`，清除 `cancel_requested` / `celery_task_id` / `error_message`
3. 按原 `task_start_time`～`task_end_time` 窗口与 `interval_minutes` 重新入队采集

**成功响应：**

```json
{
  "code": 0,
  "data": {
    "result": {
      "task_id": 7,
      "status": "pending",
      "success_count": 40,
      "failed_count": 2,
      "snapshot_source": "redis"
    }
  }
}
```

`snapshot_source`：`redis` 表示计数来自取消后保留的快照；`mysql` 表示 Redis 无数据时从库表读取。

**常见错误：**

| HTTP | `code` | 说明 |
|------|--------|------|
| 404 | `1023` | 任务不存在 |
| 403 | `1020` | 用户不一致 |
| 409 | `1028` | 任务进行中，无法重启 |
| 409 | `1029` | `task_end_time` 已过，窗口结束 |
| 429 | `1021` | 用户进行中任务数超限 |
| 503 | `1024` | Redis / 数据库未就绪 |

---

### 10.6 分页结果 `GET /api/v1/async/tasks/{task_id}/results`

从对应平台表 **`feishu_{platform}_results`** 读取；**不做跨平台字段统一**，列名与数据库一致。

**Query：**

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `page` | int | `1` | 页码，从 **1** 开始 |
| `limit` | int | `ASYNC_RESULTS_DEFAULT_LIMIT`（默认 20） | 每页条数，**1～200** |
| `is_upload` | int | 不传=不过滤 | `0` 或 `1`，按是否已上传筛选 |

**成功时 `data.result`：**

```json
{
  "page": 1,
  "limit": 20,
  "total": 135,
  "items": [ { } ]
}
```

**`items[]` 不返回的基层字段：** `id`、`task_id`、`user_id`、`create_time`、`update_time`。通过 **`data.meta.platform`** / **`data.meta.source`** 区分平台。

#### 抖音 `items[]` 字段（`feishu_douyin_results`）

`post_id`、`keyword`、`nickname`、`sec_uid`、`content_type`、`is_upload`、`title`、`summary`、`page_url`、`avatar_url`、`author_signature`、`verify_name`、`cover_url`、`duration_seconds`、`has_music`、`publish_time_ms`、`like_count`、`comment_count`、`share_count`、`collect_count`、`primary_image_url`、`primary_video_url`

#### 小红书 `items[]` 字段（`feishu_xhs_results`）

与抖音相同列集，**另含** `xsec_token`；`page_url` 长度限制与抖音不同（以表结构为准）。

**示例：**

```bash
curl -s "http://127.0.0.1:8765/api/v1/async/tasks/42/results?page=1&limit=20&is_upload=0" \
  -H "X-User-Id: user_001"
```

---

## 11. 实现位置（维护用）

| 内容 | 路径 |
|------|------|
| 路由注册与版本前缀 | `http_api/v1/routes.py`、`http_api/versions.py` |
| 同步路由 | `http_api/v1/sync_api.py` |
| 异步路由 | `http_api/v1/async_api.py` |
| `X-API-KEY` → `key` 映射 | `http_api/dajiala_params.py` |
| 对外业务状态码 | `social_platform/api_status_codes.py` |
| 响应封装 | `social_platform/api_response.py` |
| POST Body 模型 | `http_sync_bodies.py` |
| Action 注册表 | `social_platform/actions/registry.py` |
| 异步任务 / 结果服务 | `social_platform/services/task_service.py`、`result_service.py` |
| 结果表 DDL | `social_platform/database/schema.sql` |
| 多页拉取逻辑 | `social_platform/utils/search_fetch_all.py` |
| Celery | `social_platform/tasks/celery_app.py` |

版本变更时请同步更新本文档与 `python/README.md`。

---

## 12. `*-search-all` 多页采集行为说明

适用于：

- 同步：`POST /api/v1/sync/douyin/search-all`、`POST /api/v1/sync/xhs/search-all`
- 异步：`douyin-search-all`、`xhs-search-all`（`body` 字段相同）
- 聚合：`POST /api/v1/run` 且 `action` 为 `douyin_search_all` / `xhs_search_all`

### 12.1 公共参数速查

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `keyword` | string | **必填** | 搜索关键词 |
| `fetch_count` | int | `100` | 最多 **不重复** 条数，**1～500** |
| `sort_type` | int | `1` | **仅 `2` 时** `time_range` 参与客户端时间窗 |
| `time_range` | int | `7` | 近 N 天（与 `sort_type=2` 联用） |
| `exclude_words` | string | `""` | 排除词 |

**统一停止条件（满足任一即停）：**

1. 已达 **`fetch_count`**
2. **`sort_type=2`** 且时间窗内无更多符合条件数据
3. 第三方无下一页 / 空列表
4. 余额不足或接口报错

### 12.2 `sort_type` 与时间窗

| `sort_type` | `time_range` | 客户端时间窗 | 典型行为 |
|-------------|--------------|--------------|----------|
| 未传（仅旧版 `POST /run` 的 `params` 无此键） | — | 昨天 00:00～当前 | 兼容历史 |
| `0` 或 `1`（含仅写 `keyword` 时的默认 `1`） | 不生效 | 不按发布时间截窗 | 连续翻页至 `fetch_count` |
| `2` | 生效 | `[当前 − N 天, 当前]` | 近 N 天且 ≤ `fetch_count` |

> 经同步/异步 Pydantic 校验时，缺省会补 `sort_type=1`、`time_range=7`；**`time_range` 在 `sort_type≠2` 时不截断**。

### 12.3 典型场景

| 请求 | 行为摘要 |
|------|----------|
| `{ "keyword": "穿搭" }` | 最多 **100** 条，不按客户端时间过滤 |
| `{ "keyword": "穿搭", "fetch_count": 50 }` | 最多 **50** 条 |
| `{ "keyword": "穿搭", "sort_type": 2, "time_range": 7 }` | 近 7 天内，最多 **100** 条（先到先停） |
| `{ "keyword": "穿搭", "sort_type": 2, "time_range": 30, "fetch_count": 500 }` | 近 30 天，最多 **500** 条 |

### 12.4 平台差异

| 项目 | 抖音 | 小红书 |
|------|------|--------|
| 翻页 | `cursor` + `log_id` | `page` 递增 |
| 第三方筛选（search-all） | 可传 `publish_time`、`filter_duration`、`content_type` | 多页主要用 `sort_type`/`time_range`；单页筛选用 search-page |
| 落库表 | `feishu_douyin_results` | `feishu_xhs_results` |
| 去重键 | `aweme_id` → `post_id` | `note_id` → `post_id` |

### 12.5 高级参数（一般不经同步 Body 传递）

通过 **`POST /api/v1/run`** 的 `params` 或历史 `body_json` 仍可传入（Worker 支持，Pydantic 未声明）：

| 字段 | 作用 |
|------|------|
| `max_pages` | 仅限制最大页数，不做发布时间窗 |
| `start_date` / `end_date` | ISO 时间，显式客户端过滤窗口（优先于 `time_range`） |

### 12.6 同步 search-all 成功时 `data.result` / `meta` 摘要

| 字段 | 说明 |
|------|------|
| `records` | 汇总列表（条数 ≤ `fetch_count`） |
| `balance` | 账户余额（若有） |
| `meta.worker` / `meta.version` | 如 `douyin_worker` / `1.0.0` |
| `meta.use_date_window` | 是否启用客户端发布时间窗 |
| `meta.start_date_effective` / `end_date_effective` | 实际时间窗（ISO） |
| `meta.records_returned` | 实际返回条数 |
| `meta.fetch_count_cap` | 本次条数上限 |
| `meta.pages_fetched` | 向第三方请求的页数 |
| `meta.stopped_before_start_date` | 是否因遇到早于窗口下界的条目而停止翻页 |

异步任务完成后，业务数据在 **`GET .../results`** 的 `data.result.items` 中按平台表字段返回；任务级元信息在 **`data.meta`**（§10.2～10.4）。

---

## 13. 视频号搜索接口（wxvideo / wx/sousou）

路径：
- `POST /api/v1/sync/wxvideo/search-page`
- `POST /api/v1/sync/wxvideo/search-all`
- 异步 action: `wxvideo-search-page` / `wxvideo-search-all`

### 参数说明（search-page / search-all 通用）

| 字段 | 类型 | 必需 | 说明 | 示例 |
|------|------|------|------|------|
| `keyword` | string | 是 | 搜索关键词 | "人民日报" |
| `sort_type` | int | 否 | 0=综合, 1=最新, 2=最热（内部映射） | 1 |
| `note_time` | int | 否 | 0=不限, 1=最近1天, 2=最近7天, 3=最近半年（原 publish_time_type） | 1 |
| `page` / `currentPage` | int | 否 | 页码，第一页=1 | 1 |
| `offset` | int | 否 | 翻页偏移，第一页=0，后续填上次返回 | 0 |
| `cookies_buffer` | string | 否 | 第二页起必填，填上次返回的 cookies_buffer | "" |

**注意**：`mode=1`、`search_type=2` 内部写死。`sort_type` 会映射为第三方 sort_type。

### 示例 Body（search-page 第一页）

```json
{
  "keyword": "人民日报",
  "sort_type": 1,
  "note_time": 1,
  "page": 1,
  "offset": 0,
  "cookies_buffer": ""
}
```

翻页时带上返回的 `offset` 和 `cookies_buffer`。

返回字段包含：title、publish_time（毫秒）、duration（秒）、nickname、avatar_url、like_count 等 + next_offset / cookies_buffer。

落库表：`feishu_wxvideo_results`

---

## 14. 公众号搜索接口（mp）

路径：
- `POST /api/v1/sync/mp/search-page`
- `POST /api/v1/sync/mp/search-all`
- 异步 action: `mp-search-page` / `mp-search-all`

### 参数说明

| 字段 | 类型 | 必需 | 说明 | 映射说明 |
|------|------|------|------|----------|
| `keyword` | string | 是 | 搜索关键词 | - |
| `sort_type` | int | 否 | 0/1/2 | 映射为 Sub_search_type: 0→0, 1→4, 2→2 |
| `note_time` | int | 否 | 时间范围 | 直接透传 |
| `page` / `currentPage` | int | 否 | 页码 | 内部统一使用 currentPage 传第三方 |
| `offset` | int | 否 | 翻页偏移 | 同视频号 |
| `cookies_buffer` | string | 否 | 翻页凭证 | 同视频号 |

**注意**：`mode=2`、`BusinessType=2` 写死。

### 示例 Body

```json
{
  "keyword": "大模型",
  "sort_type": 0,
  "note_time": 0,
  "page": 1
}
```

返回字段映射：
- `date` → `publish_time`（秒→毫秒）
- `desc` → `content`
- `doc_url` → `url`
- `reportId` → `article_id` / `post_id`
- `source.title` → `author`
- `thumbUrl` → `avatar_url`
- `title` → 经 HTML 清洗后的标题

落库表：`feishu_mp_results`

---

## 15. 异步任务 Action 汇总（kebab-case）

| 平台 | 单页 Action | 多页 Action |
|------|-------------|-------------|
| 抖音 | douyin-search-page | douyin-search-all |
| 小红书 | xhs-search-page | xhs-search-all |
| 视频号 | wxvideo-search-page | wxvideo-search-all |
| 公众号 | mp-search-page | mp-search-all |

所有异步任务提交 Body 格式统一为：

```json
{
  "action": "wxvideo-search-page",
  "body": { ...业务参数... }
}
```

Contracts 示例文件见 `contracts/v1/` 目录下的 `*.example.json`。

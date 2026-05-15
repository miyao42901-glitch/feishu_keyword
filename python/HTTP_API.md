# 统一 HTTP 数据接口说明

服务由 `run.py` 启动，默认监听 **`http://<主机>:8765`**（可用环境变量 `HTTP_HOST`、`HTTP_PORT` 覆盖）。除 **`GET /api/v1/health`** 外，业务接口均为 **`POST`**，**`Content-Type: application/json`**。

交互式文档：服务启动后访问 **`http://<主机>:<端口>/docs`**（Swagger UI）、**`/redoc`**。

---

## 1. 路径版本

当前对外 API 统一挂在 **`/api/v1`** 下（见 `http_api/versions.py` 中 `API_V1_PREFIX`）。后续新增 **`/api/v2`** 时单独注册路由即可。

下文以 **`BASE = http://127.0.0.1:8765`** 为例，业务路径均为 **`BASE + /api/v1` + 资源路径**（如 **`/api/v1/health`**）。

---

## 2. 请求体约定（同步接口）

**`POST /api/v1/sync/...`**：

| 位置 | 说明 |
|------|------|
| **Header** | **`X-API-Key`**（必填）：下游 YDDM / 大加拉等使用的 **`key`** |
| **Header** | **`X-User-Id`**（必填）：用户标识，用于结果落库 |
| **JSON Body** | 仅业务字段（如 `keyword`、`cursor` 等），**不要**再包一层 `body` / `params` |

示例：

```bash
curl -s -X POST "http://127.0.0.1:8765/api/v1/sync/douyin/search-page" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY" \
  -H "X-User-Id: user_001" \
  -d "{\"keyword\": \"人民日报\"}"
```

**`POST /api/v1/run`**：仍为 **`action` + `params`** 单 JSON；`params` 内凭证可用 **`X-API-KEY`**（映射为下游 `key`）或直接传 **`key`**。见第 8 节。

**异步 `POST /api/v1/async/tasks`**：`action` 为 **kebab-case**（如 `douyin-search-all`），`body` 字段与同步 search 接口一致。见第 10 节。

**校验失败（FastAPI）：** 可能返回 **422** 及标准校验错误结构。

### Python `requests` 示例

```python
import requests

url = "http://127.0.0.1:8765/api/v1/sync/douyin/search-page"
headers = {"X-API-Key": "YOUR_KEY", "X-User-Id": "user_001"}
payload = {"keyword": "人民日报"}

response = requests.post(url, headers=headers, json=payload)
print(response.text)
```

---

## 3. 统一响应格式

成功或业务层错误时，HTTP 状态码多为 **200**，通过 **`code`** 区分：

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | int | **`0` 表示成功**；非 0 为业务/逻辑错误（见 `social_platform/api_status_codes.py` 中 `API_STATUS_MESSAGES`，如 **`1001`** 余额不足、**`400`** 参数错误） |
| `msg` | string | 人类可读说明 |
| `data` | object \| null | 负载；成功时通常含 `result`，部分接口含 `meta` |

**成功示例：**

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "result": { }
  }
}
```

含 Worker 元信息时，`data` 可能为 `{ "result": { }, "meta": { } }`。

**失败示例（业务错误，`code` ≠ 0）：**

```json
{
  "code": 400,
  "msg": "参数错误",
  "data": null
}
```

余额不足等场景可能出现 **`code: 1001`**（见 `social_platform/api_response.py` 中 `from_worker_run`）。

---

## 4. 健康检查

### `GET /api/v1/health`

**响应：** 与第 3 节一致，`data` 内为 `{ "status": "ok" }`（以实际返回为准）。

```bash
curl -s "http://127.0.0.1:8765/api/v1/health"
```

---

## 5. 聚合任务 `POST /api/v1/run`

单入口按 **`action`** 分发到抖音或小红书 Worker（逻辑见 `social_platform/aggregated_job.py`）。

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `action` | string | 是 | 见下表 |
| `params` | object | 否 | 默认 `{}`；凭证请用 **`X-API-KEY`**，业务字段与同步接口一致（见第 8 节） |

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
  -d "{\"action\":\"douyin_search_page\",\"params\":{\"X-API-KEY\":\"YOUR_SECRET\",\"keyword\":\"关键词\",\"cursor\":\"\",\"logid\":\"\"}}"
```

不支持的 `action` 时，响应为业务失败（`code` 非 0），`msg` 中含 `unsupported action`。

---

## 6. 抖音同步接口（仅 POST + JSON）

路径前缀：**`/api/v1/sync/douyin`**

所有接口：**Header `X-API-Key` + `X-User-Id`** + **扁平 JSON Body**。

### 6.1 单页搜索 `POST .../search-page`

| Body 字段 | 类型 | 必填 | 默认 | 说明 |
|-----------|------|------|------|------|
| `keyword` | string | 是 | — | 1～100 字 |
| `cursor` | string | 否 | `""` | 首页留空；翻页用上一页返回的 `cursor` |
| `log_id` / `logid` | string | 否 | `""` | 首页留空；翻页用上一页返回的 `log_id` |
| `sort_type` | string | 否 | `"0"` | `0` 综合，`1` 最多点赞，`2` 最新发布 |
| `publish_time` | string | 否 | `"0"` | `0` 不限，`1` 1天内，`7` 7天内，`180` 180天内 |
| `filter_duration` | string | 否 | `"0"` | `0` 不限，`0-1` / `1-5` / `1-10000` 见模型说明 |
| `content_type` | string | 否 | `"0"` | `0` 不限，`1` 视频，`2` 图文 |
| `exclude_words` | string | 否 | `""` | 排除词，空格分隔 |

```bash
curl -s -X POST "http://127.0.0.1:8765/api/v1/sync/douyin/search-page" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY" \
  -H "X-User-Id: user_001" \
  -d "{\"keyword\":\"人民日报\",\"sort_type\":\"2\",\"publish_time\":\"7\"}"
```

### 6.2 多页搜索 `POST .../search-all`

| Body 字段 | 类型 | 必填 | 默认 | 说明 |
|-----------|------|------|------|------|
| `keyword` | string | 是 | — | 搜索词 |
| `fetch_count` | int | 否 | `100` | 采集条数上限，**1～500** |
| `sort_type` | int | 否 | `1` | `0`/`1` 不按客户端时间窗截断；`2` 按时间（见下节） |
| `time_range` | int | 否 | `7` | 天数；**仅 `sort_type=2` 时生效** |
| `exclude_words` | string | 否 | `""` | 排除词 |
| `cursor` | string | 否 | `""` | 可选起始翻页游标 |
| `log_id` / `logid` | string | 否 | `""` | 可选起始翻页参数 |
| `publish_time` | string | 否 | `""` | 传给第三方的发布时间筛选（空则下游默认） |
| `filter_duration` | string | 否 | `""` | 视频时长筛选 |
| `content_type` | string | 否 | `""` | 内容形式筛选 |

**落库：** 每向第三方成功拉取一页并过滤后，即将当页结果写入 `feishu_douyin_results`（需配置 `DATABASE_URL`）。

```bash
curl -s -X POST "http://127.0.0.1:8765/api/v1/sync/douyin/search-all" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY" \
  -H "X-User-Id: user_001" \
  -d "{\"keyword\":\"穿搭\",\"fetch_count\":100,\"sort_type\":2,\"time_range\":7}"
```

**采集行为详解见第 12 节（`douyin-search-all` / `xhs-search-all`）。**

---

## 7. 小红书同步接口（仅 POST + JSON）

路径前缀：**`/api/v1/sync/xhs`**

**Header `X-API-Key` + `X-User-Id`** + **扁平 Body**。

### 7.1 单页搜索 `POST .../search-page`

| Body 字段 | 类型 | 必填 | 默认 | 说明 |
|-----------|------|------|------|------|
| `keyword` | string | 是 | — | 搜索词 |
| `page` | int | 否 | `1` | 页码，≥1 |
| `sort_type` | string | 否 | `"0"` | `0` 综合，`1` 最多点赞，`2` 最新发布 |
| `content_type` | string | 否 | `""` | `video` / `note` / 空=不限 |
| `note_time` | string | 否 | `"0"` | `0` 不限，`1` 1天内，`7` 7天内，`180` 180天内 |
| `exclude_words` | string | 否 | `""` | 排除词 |

请求体会映射为 YDDM 字段：`sort`（如 `time_descending`）、`note_type`、`note_time`（如 `week`）等。

```bash
curl -s -X POST "http://127.0.0.1:8765/api/v1/sync/xhs/search-page" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY" \
  -H "X-User-Id: user_001" \
  -d "{\"keyword\":\"穿搭博主\",\"page\":1,\"sort_type\":\"2\",\"content_type\":\"video\",\"note_time\":\"7\"}"
```

### 7.2 多页搜索 `POST .../search-all`

| Body 字段 | 类型 | 必填 | 默认 | 说明 |
|-----------|------|------|------|------|
| `keyword` | string | 是 | — | 搜索词 |
| `fetch_count` | int | 否 | `100` | 采集条数上限，**1～500** |
| `sort_type` | int | 否 | `1` | 同抖音 search-all |
| `time_range` | int | 否 | `7` | 仅 `sort_type=2` 时参与客户端时间窗 |
| `exclude_words` | string | 否 | `""` | 排除词 |

**落库：** 每页写入 `feishu_xhs_results`。

```bash
curl -s -X POST "http://127.0.0.1:8765/api/v1/sync/xhs/search-all" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY" \
  -H "X-User-Id: user_001" \
  -d "{\"keyword\":\"穿搭博主\",\"fetch_count\":50,\"sort_type\":2,\"time_range\":7}"
```

**采集行为详解见第 12 节。**

## 8. 与 `POST /api/v1/run` 的 `params` 对应关系

调用 **`POST /api/v1/run`** 时，`params` 为**单对象**（与同步接口合并后传给 Worker 的字段一致）：可传 **`key`**，或使用 **`X-API-KEY`**（会映射为 `key`；若二者都有，非空 **`key`** 优先）。

| `action` | `params` 中业务字段（另加 **`key`** 或 **`X-API-KEY`**） |
|----------|----------------|
| `douyin_search_page` | `keyword`；可选 `cursor`、`log_id`/`logid`、`sort_type`、`publish_time`、`filter_duration`、`content_type`、`exclude_words` |
| `douyin_search_all` | `keyword`；可选 `fetch_count`、`sort_type`、`time_range`、`exclude_words` 及抖音筛选字段；见第 12 节 |
| `xhs_search_page` | `keyword`；可选 `page`、`sort_type`、`content_type`、`note_time`、`exclude_words` |
| `xhs_search_all` | `keyword`；可选 `fetch_count`、`sort_type`、`time_range`、`exclude_words`；见第 12 节 |

异步任务 **`action`** 使用 kebab-case：`douyin-search-all`、`xhs-search-all` 等，`body` 字段与上表相同（无需包 `params`）。

---

## 9. 环境与配置

- 本地密钥、上游 URL 等见 **`python/.env`**（可复制 `python/.env.example`）。
- 抖音 / 小红书默认请求地址可由环境变量 **`DOUYIN_GENERAL_URL`**、**`XHS_GENERAL_URL`** 覆盖（与 Worker 内逻辑一致）。

---

## 10. 异步任务（Celery + MySQL）

前置：**`DATABASE_URL`**（如 `mysql+pymysql://user:pass@host:3306/db?charset=utf8mb4`）、**Redis**（`REDIS_URL` / `CELERY_BROKER_URL`），并单独启动 Worker：`celery -A celery_jobs.celery_app worker -l info`（在 `python/` 目录、与 `run.py` 共用 `.env`）。可选 **`ASYNC_TASK_DB_AUTO_CREATE=1`** 在 HTTP 启动时自动建表（生产请用 `social_platform/database/schema.sql` 或迁移工具）。

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/async/tasks` | JSON：`action`（**kebab-case**，须在 `social_platform/actions/registry.py` 注册）+ `body`（对象，按 action 做 Pydantic 校验）；**Header `X-API-Key`**、**`X-User-Id`** 必填；Query **`priority`** 可选 0～9。未知 `action` 返回 HTTP 400，体为 `{"code":400,"message":"unsupported action"}`。响应统一 `{code,msg,data}` 内 `data.task_id`、`data.status`。 |
| GET | `/api/v1/async/tasks/{task_id}` | 状态：`pending` / `running` / `success` / `failed` / `cancelled` 等；`data.platform` 由 `action` **推导**（不落库）。 |
| GET | `/api/v1/async/tasks/{task_id}/results` | Query **`page`**（从 1 起）、**`limit`**、**`is_upload`**（0/1）；结果来自 `feishu_*_results` 分表。 |

未配置 **`DATABASE_URL`** 时上述接口返回 **503**。示例 JSON 见 **`contracts/v1/async_task_submit.example.json`**。Action 注册表见 **`social_platform/actions/registry.py`**。

---

## 11. 实现位置（维护用）

| 内容 | 路径 |
|------|------|
| 路由注册与版本前缀 | `http_api/v1/routes.py`、`http_api/versions.py` |
| 同步路由 | `http_api/v1/sync_api.py` |
| 异步路由 | `http_api/v1/async_api.py` |
| `X-API-KEY` → `key` 映射 | `http_api/dajiala_params.py`（`to_worker_params`） |
| 对外业务状态码与文案 | `social_platform/api_status_codes.py` |
| POST Body 模型 | `http_sync_bodies.py` |
| Action 注册表 | `social_platform/actions/registry.py` |
| 异步任务服务 / ORM | `social_platform/services/`、`social_platform/models/`、`social_platform/database/` |
| Celery 应用 | `social_platform/tasks/celery_app.py`（兼容入口 `celery_jobs/celery_app.py`） |
| 响应封装 | `social_platform/api_response.py` |
| 多页拉取与停止逻辑 | `social_platform/utils/search_fetch_all.py` |

版本变更时请同步更新本文档与 `python/README.md` 中的路由摘要。

---

## 12. `*-search-all` 多页采集行为说明

适用于：

- 同步：`POST /api/v1/sync/douyin/search-all`、`POST /api/v1/sync/xhs/search-all`
- 异步：`action` 为 `douyin-search-all`、`xhs-search-all`（`body` 字段相同）
- 聚合：`POST /api/v1/run` 且 `action` 为 `douyin_search_all` / `xhs_search_all`

### 12.1 公共参数（`http_sync_bodies.PublicSearchAllBody`）

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `keyword` | string | **必填** | 搜索关键词 |
| `fetch_count` | int | `100` | 最多采集 **不重复** 条数（按 `note_id` / `aweme_id`），**1～500**；达到即停 |
| `sort_type` | int | `1` | 见下表；**仅值为 `2` 时 `time_range` 才参与客户端时间窗** |
| `time_range` | int | `7` | 天数；与 `sort_type=2` 联用，表示「近 N 天」 |
| `exclude_words` | string | `""` | 排除词（解析后过滤标题/描述） |

**统一停止条件（满足任一即停）：**

1. 已采集条数达到 **`fetch_count`**
2. **`sort_type=2`** 且按发布时间判断，时间窗内已无更多符合条件的数据
3. 第三方返回无下一页 / 空列表
4. 余额不足或接口报错

响应 `data.result`（或 Worker `data`）中的 **`meta`** 字段会回显有效时间窗、`pages_fetched`、`records_returned`、`fetch_count_cap` 等，便于核对实际采到哪一段。

### 12.2 `sort_type` 与时间窗（客户端二次过滤）

列表默认按 **发布时间从新到旧** 排序。启用时间窗时，仅保留 `publish_time`（毫秒）落在 **`[start, end]`** 内的记录；遇到早于 `start` 的条目即不再翻页。

| `sort_type` | `time_range` 是否生效 | 客户端时间窗 | 典型采集范围 |
|-------------|----------------------|--------------|--------------|
| **未传**（仅旧版 `POST /run` 的 `params` 中完全没有该字段） | — | **昨天本地 00:00:00 ～ 当前时刻** | 兼容历史行为；再受 `fetch_count` 限制 |
| **`0` 或 `1`**（含只填 `keyword` 时 Pydantic 默认 `sort_type=1`） | **否** | 不按发布时间截窗 | 按第三方排序连续翻页，最多 **`fetch_count`** 条 |
| **`2`** | **是** | **`[当前时刻 − time_range 天, 当前时刻]`** | 近 N 天内、且不超过 **`fetch_count`** 条 |

> **说明：** 走同步接口或异步任务且 body 经 Pydantic 校验时，即使请求 JSON 里只写 `{"keyword":"xxx"}`，服务端也会补上默认 `fetch_count=100`、`sort_type=1`、`time_range=7`；其中 **`time_range` 在 `sort_type≠2` 时不参与截断**。只有旧版聚合接口在 `params` 里**完全不包含** `sort_type` 键时，才会走「昨天～当前」时间窗。

### 12.3 典型请求与「采到哪一段数据」

以下默认经 **同步 / 异步** 校验（带默认 `sort_type=1`），除非注明为旧版 `POST /run`。

#### 只填 `keyword`

```json
{ "keyword": "穿搭" }
```

| 项目 | 行为 |
|------|------|
| 等价参数 | `fetch_count=100`，`sort_type=1`，`time_range=7`（`time_range` 不生效） |
| 采集范围 | 不按客户端发布时间过滤；按第三方列表顺序翻页 |
| 最多条数 | **100**（或第三方提前无数据） |
| 示例 | 关键词下共有 200 条可翻页 → 采 **100** 条后停止 |

#### 只改条数上限

```json
{ "keyword": "穿搭", "fetch_count": 50 }
```

最多采集 **50** 条；其余同「只填 keyword」。

#### 按时间范围采集（`sort_type=2`）

```json
{ "keyword": "穿搭", "fetch_count": 100, "sort_type": 2, "time_range": 7 }
```

| 场景 | 近 7 天内符合条件的数据量 | 实际采集 |
|------|---------------------------|----------|
| 示例 1 | 80 条 | **80** 条后停止（时间窗内已穷尽） |
| 示例 2 | 200 条 | **100** 条后停止（达到 `fetch_count`） |

时间窗下界：当前时刻往前 **7×24 小时**（本地时间）；上界：当前时刻。仅统计 **`publish_time` 落在该区间内** 的记录。

#### `sort_type=2` 且加大天数

```json
{ "keyword": "穿搭", "sort_type": 2, "time_range": 30, "fetch_count": 500 }
```

客户端时间窗为 **近 30 天**，最多 **500** 条（二者先到先停）。

#### `sort_type=0`

```json
{ "keyword": "穿搭", "sort_type": 0 }
```

与 `sort_type=1` 相同：**不做客户端时间窗过滤**，最多默认 **100** 条。

### 12.4 平台差异

| 项目 | 抖音 `douyin-search-all` | 小红书 `xhs-search-all` |
|------|--------------------------|-------------------------|
| 翻页 | `cursor` + `log_id` | `page` 递增（映射 YDDM） |
| 可选筛选 | `publish_time`、`filter_duration`、`content_type` 等传给第三方 | 多页场景主要用 `sort_type` / `time_range` 控制客户端截断；单页筛选项见 search-page |
| 落库表 | `feishu_douyin_results` | `feishu_xhs_results` |
| 落库时机 | 每成功拉取一页并过滤后写库 | 同左 |

### 12.5 异步任务示例

```json
{
  "action": "douyin-search-all",
  "body": {
    "keyword": "人民日报",
    "fetch_count": 100,
    "sort_type": 2,
    "time_range": 7
  }
}
```

```json
{
  "action": "xhs-search-all",
  "body": {
    "keyword": "穿搭博主",
    "fetch_count": 50
  }
}
```

第二个示例等价于 `sort_type=1`、最多 **50** 条、**不按客户端时间窗过滤**。

### 12.6 高级 / 兼容参数（一般无需在同步 Body 中传递）

通过 **`POST /api/v1/run`** 的 `params` 或历史任务 `body_json` 仍可传入（未在 Pydantic 模型中声明，但 Worker 支持）：

| 字段 | 作用 |
|------|------|
| `max_pages` | 仅设置页数上限、**不做**发布时间窗过滤 |
| `start_date` / `end_date` | ISO 时间字符串，显式指定客户端过滤窗口（优先于 `time_range`） |

### 12.7 返回结构摘要（search-all 成功时）

`data.result` 内常见字段：

| 字段 | 说明 |
|------|------|
| `records` | 汇总后的结果列表（条数 ≤ `fetch_count`） |
| `balance` | 第三方账户余额（若有） |
| `meta.use_date_window` | 是否启用了客户端发布时间窗 |
| `meta.start_date_effective` / `end_date_effective` | 实际使用的时间窗（ISO） |
| `meta.records_returned` | 实际返回条数 |
| `meta.fetch_count_cap` | 本次请求的条数上限 |
| `meta.pages_fetched` | 向第三方请求的页数 |
| `meta.stopped_before_start_date` | 是否因遇到早于窗口下界的条目而停止翻页 |

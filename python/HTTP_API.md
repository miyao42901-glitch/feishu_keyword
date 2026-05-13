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
| **Query** | **`key`**（必填）：与大加拉等下游请求中的 **`key`** 一致 |
| **JSON Body** | 仅业务字段（如 `keyword`、`cursor` 等），**不要**再包一层 `body` / `params` |

示例 URL + 请求体（与 Apifox / `requests` 常见写法一致）：

- URL：`POST /api/v1/sync/douyin/search-page?key=YOUR_KEY`
- Body：`{"keyword": "人民日报"}`（可带 `cursor`、`logid`，见下节）

**`POST /api/v1/run`**：仍为 **`action` + `params`** 单 JSON；`params` 内凭证可用 **`X-API-KEY`**（映射为下游 `key`）或直接传 **`key`**。见第 8 节。

**校验失败（FastAPI）：** 可能返回 **422** 及标准校验错误结构。

### Python `requests` 示例

```python
import requests

url = "http://127.0.0.1:8765/api/v1/sync/douyin/search-page"
params = {"key": "YOUR_KEY"}
payload = {"keyword": "人民日报"}

response = requests.post(url, params=params, json=payload)
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

所有接口：**Query 参数 `key`** + **扁平 JSON Body**（仅业务字段）。

### 6.1 单页搜索 `POST .../search-page`

| Query 参数 | 必填 | 说明 |
|------------|------|------|
| `key` | 是 | 下游大加拉等使用的 **`key`** |

| Body 字段 | 类型 | 必填 | 默认 | 说明 |
|-----------|------|------|------|------|
| `keyword` | string | 是 | — | `min_length=1` |
| `cursor` | string | 否 | `""` | |
| `logid` | string | 否 | `""` | |

```bash
curl -s -X POST "http://127.0.0.1:8765/api/v1/sync/douyin/search-page?key=YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"keyword\":\"人民日报\",\"cursor\":\"\",\"logid\":\"\"}"
```

### 6.2 多页搜索 `POST .../search-all`

| Query 参数 | 必填 | 说明 |
|------------|------|------|
| `key` | 是 | 同上 |

| Body 字段 | 类型 | 必填 | 默认 | 说明 |
|-----------|------|------|------|------|
| `keyword` | string | 是 | — | |
| `max_pages` | int | 否 | `10` | **1～50** |

```bash
curl -s -X POST "http://127.0.0.1:8765/api/v1/sync/douyin/search-all?key=YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"keyword\":\"test\",\"max_pages\":5}"
```

---

## 7. 小红书同步接口（仅 POST + JSON）

路径前缀：**`/api/v1/sync/xhs`**

**Query `key`** + **扁平 Body**。

### 7.1 单页搜索 `POST .../search-page`

| Query 参数 | 必填 | 说明 |
|------------|------|------|
| `key` | 是 | 下游大加拉等使用的 **`key`** |

| Body 字段 | 类型 | 必填 | 默认 | 说明 |
|-----------|------|------|------|------|
| `keyword` | string | 是 | — | |
| `page` | string | 否 | `"1"` | |

### 7.2 多页搜索 `POST .../search-all`

| Query 参数 | 必填 | 说明 |
|------------|------|------|
| `key` | 是 | 同上 |

| Body 字段 | 类型 | 必填 | 默认 | 说明 |
|-----------|------|------|------|------|
| `keyword` | string | 是 | — | |
| `max_pages` | int | 否 | `10` | **1～50** |

---

## 8. 与 `POST /api/v1/run` 的 `params` 对应关系

调用 **`POST /api/v1/run`** 时，`params` 为**单对象**（与同步接口合并后传给 Worker 的字段一致）：可传 **`key`**，或使用 **`X-API-KEY`**（会映射为 `key`；若二者都有，非空 **`key`** 优先）。

| `action` | `params` 中业务字段（另加 **`key`** 或 **`X-API-KEY`**） |
|----------|----------------|
| `douyin_search_page` | `keyword`, `cursor`, `logid`（后两者可省略，默认空串） |
| `douyin_search_all` | `keyword`, `max_pages`（可选，默认 10，1～50） |
| `xhs_search_page` | `keyword`, `page`（可选，默认 `"1"`） |
| `xhs_search_all` | `keyword`, `max_pages`（可选，默认 10，1～50） |

---

## 9. 环境与配置

- 本地密钥、上游 URL 等见 **`python/.env`**（可复制 `python/.env.example`）。
- 抖音 / 小红书默认请求地址可由环境变量 **`DOUYIN_GENERAL_URL`**、**`XHS_GENERAL_URL`** 覆盖（与 Worker 内逻辑一致）。

---

## 10. 实现位置（维护用）

| 内容 | 路径 |
|------|------|
| 路由注册与版本前缀 | `http_api/v1/routes.py`、`http_api/versions.py` |
| `X-API-KEY` → `key` 映射 | `http_api/dajiala_params.py`（`to_worker_params`） |
| 对外业务状态码与文案 | `social_platform/api_status_codes.py` |
| POST Body 模型 | `http_sync_bodies.py` |
| 聚合信封 | `social_platform/schemas.py`（`TaskEnvelope`） |
| 响应封装 | `social_platform/api_response.py` |

版本变更时请同步更新本文档与 `python/README.md` 中的路由摘要。

# HTTP 接口规范

## 适用范围

| 项 | 说明 |
|----|------|
| **对应代码目录** | 仓库根目录下的 **`server/`**（FastAPI 应用） |
| **相关文档** | [server 技术栈与文档索引](./server/README.md) · [数据库约定](./DATABASE.md)（接口读写库表时） · [工程约定](./DEVELOPMENT.md) |

---

## 1. 基础约定

| 项 | 约定 |
|----|------|
| 基础路径 | 所有业务接口挂在 **`/api`** 下（由 `app.main` 统一 `prefix`） |
| 格式 | **`application/json`**（`POST`/`PUT`/`PATCH` 请求体为 JSON，除非将来明确支持表单上传） |
| 文档 | 内置 OpenAPI：`/docs`（Swagger）、`/redoc` |

## 2. URL 与命名

- 资源集合使用 **复数名词 + kebab-case** 路径段，例如：`/api/monitoring-plans`。
- 单条资源如需详情接口，使用 **`/{id}`**，例如：`/api/monitoring-plans/1`（待实现时遵守）。
- **不使用**动词作路径主体（避免 `/api/getPlans`）；动作用 HTTP 方法表达。

## 3. HTTP 方法语义

| 方法 | 用途 |
|------|------|
| `GET` | 查询，**不应**产生副作用；可缓存语义 |
| `POST` | 创建资源或非幂等操作 |
| `PUT` / `PATCH` | 全量 / 部分更新（按需选用） |
| `DELETE` | 删除或逻辑删除（与产品约定一致） |

## 4. 列表与分页

查询列表时推荐统一查询参数（与现有实现一致时可扩展）：

| 参数 | 类型 | 说明 |
|------|------|------|
| `skip` | `int` | 偏移量，默认 `0` |
| `limit` | `int` | 每页条数，默认见 `server/app/core/config.py` 的 `DEFAULT_LIST_LIMIT`，且不得超过 `MAX_LIST_LIMIT` |

服务端必须在服务层对 `limit` 做上限裁剪，防止单次过大查询。

## 5. 统一响应体（`code` / `message` / `data`）

所有 **`/api`** 接口均采用同一外层结构：

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | `int` | **`0` 表示业务成功**；非 `0` 表示失败（业务错误码，见 `server/app/schemas/api_response.py` 中 `BizCode`） |
| `message` | `string` | 给人看的说明；成功时如「查询成功」「保存成功」，失败时说明原因 |
| `data` | `object \| array \| null` | 成功时为具体载荷；失败时一般为 `null`。参数校验失败时 `data` 内可能含 `errors` 明细 |

HTTP 状态码仍遵循语义（如 404、422、503），**客户端应以响应体内的 `code` 为准做分支**。

典型错误码：`40001` 参数类、`40401` 资源不存在、`50301` 数据库不可用、`50001` 服务器内部错误。

## 6. 版本控制

- 当前无 `/v1` 前缀；若未来破坏性变更，可引入 **`/api/v2`** 或请求头版本协商，并在本文档追加说明。

## 7. 与前端协作

- 前端（`feishu/`）请求后端时使用环境变量或配置中的 **API Base URL**，禁止硬编码生产地址。
- 跨域（CORS）若需浏览器直连后端，在 FastAPI 中集中配置，不在各路由重复处理。

## 8. 飞书任务配置（`feishu_task_configs`）

以下接口均需在请求头携带 **`X-Api-Key`**（与前端持久化的 YDDM API Key /「授权码」一致）；未携带或为空时返回 **HTTP 401**，业务码 `40101`。服务端仅返回或修改 **`owner_api_key` 与该 Key 一致** 的任务行。

外层仍为 **`{ code, message, data }`**；下列为 **`data` 在成功时的形状**。

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/feishu-task-configs` | `data` 为列表项数组（见下表） |
| `GET` | `/api/feishu-task-configs/{id}` | `data` 含 `config` 对象 |
| `POST` | `/api/feishu-task-configs` | 请求体 `{"config": { ... }}`；成功时 `data` 为 `{ "id": number }` |
| `PUT` | `/api/feishu-task-configs/{id}` | 全量更新；请求体同上 |
| `DELETE` | `/api/feishu-task-configs/{id}` | 删除；成功时 `data` 为 `{ "id": number }` |

列表项字段（除 `id`、`plan_name`、`updated_at` 外，其余由 `config_json` 解析，可能为 `null`）：`task_type`、`platform_keys`、`effective_at`、`expire_at`、`task_paused`、`task_abnormal`（任务异常如接口失败）、`run_status`（可与 `task_abnormal` 一并表示失败）。

库表与字段见 [DATABASE.md](./DATABASE.md) 中 `feishu_task_configs`。

---

## 9. 代码位置与接口注释约定

| 类别 | 路径 | 注释要求 |
|------|------|----------|
| 路由聚合 | `server/app/api/router.py` | 模块 docstring 维护子路由一览表；新增路由时同步更新 |
| 业务路由 | `server/app/api/routers/*.py` | 每个 **HTTP 处理函数** 使用中文 docstring：**路径**、**Args**、**Returns**（成功时 `data` 形态）、必要时 **Raises** |
| 依赖注入 | `server/app/api/deps.py` | `get_db` 等说明生命周期与使用方式 |
| 全局异常 | `server/app/api/exception_handlers.py` | 各 handler 说明何时触发、HTTP 状态与 `data` 形态 |
| 请求/响应模型 | `server/app/schemas/*.py` | 与对外 JSON 相关的 Model 注明对应路由与字段含义 |
| 前端封装 | `feishu/src/lib/api.ts` | 文件头说明统一响应与 `apiFetch` 行为；每个 **导出函数** 使用 JSDoc（路径语义、`@param`、`@returns`、`@throws`） |

**文档与代码同步**：新增或变更路径、`data` 形状时，须同时更新本节或上文相关表格及路由 docstring，避免 OpenAPI、`docs/API.md` 与实现不一致。

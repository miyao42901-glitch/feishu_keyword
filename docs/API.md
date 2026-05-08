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

## 5. 响应体

- **成功**：返回约定 Schema（Pydantic `response_model`），结构稳定、字段含义明确。
- **健康检查** `GET /api/health`：保留 `status`、`service`、`database`（`configured` / `reachable` / `error`）结构，前端与运维可依赖该形状。

错误响应（后续如引入统一异常处理器）建议包含：

- `detail`：人类可读说明（中文或中英文由产品定）
- 必要时 `code`：稳定业务/错误码字符串

（当前项目若尚未实现全局异常处理，新增接口时与现有风格保持一致。）

## 6. 版本控制

- 当前无 `/v1` 前缀；若未来破坏性变更，可引入 **`/api/v2`** 或请求头版本协商，并在本文档追加说明。

## 7. 与前端协作

- 前端（`feishu/`）请求后端时使用环境变量或配置中的 **API Base URL**，禁止硬编码生产地址。
- 跨域（CORS）若需浏览器直连后端，在 FastAPI 中集中配置，不在各路由重复处理。

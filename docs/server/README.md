# server/ 技术文档索引

## 适用范围

| 项 | 说明 |
|----|------|
| **对应代码目录** | 仓库根目录下的 **`server/`** |
| **职责** | HTTP API、MySQL 访问、业务服务；与飞书开放平台交互时可在本目录扩展客户端封装 |

---

## 技术栈

以 `server/requirements.txt` 为准；当前约定如下。

| 类别 | 技术 | 说明 |
|------|------|------|
| 语言 | Python 3 | 建议使用 3.10+（与本地虚拟环境一致） |
| Web 框架 | FastAPI | 路由、依赖注入、OpenAPI |
| ASGI 服务器 | Uvicorn | 开发：`uvicorn app.main:app` |
| ORM | SQLAlchemy 2.x | 模型见 `app/models/` |
| 数据库驱动 | PyMySQL | 经连接串 `mysql+pymysql://...` |
| 配置 | python-dotenv | 仓根 `.env` → `.env.local`（见 `app/env_loader.py`） |
| HTTP 客户端 | httpx | 调用外部 API（飞书、采集服务等） |

---

## 与本目录相关的规范文档

| 文档 | 说明 |
|------|------|
| [HTTP 接口规范](../API.md) | `/api` 前缀、REST 命名、分页、**统一响应 `code` / `message` / `data`**（详见该文档 §5）、响应约定 |
| [数据库与 ORM](../DATABASE.md) | 库名、表字段、`DATABASE_URL`、变更清单 |
| [工程约定](../DEVELOPMENT.md) | 分层目录、`get_db`、Git 与注释 |

---

## 统一 API 响应（`code` / `message` / `data`）

业务接口均返回同一外层 JSON：

| 字段 | 说明 |
|------|------|
| `code` | `0` 成功；非 `0` 为业务错误码（见 `app/schemas/api_response.py` 中 `BizCode`） |
| `message` | 给人阅读的说明（成功 / 失败文案） |
| `data` | 成功时为载荷；失败时多为 `null`（校验失败时可能含 `errors`） |

HTTP 状态码（404、422、503 等）仍保留语义；**客户端建议以响应体内的 `code` 分支**。全局异常由 `app/api/exception_handlers.py` 转为上述格式。

**权威说明与错误码表**：见 **[HTTP 接口规范](../API.md)** 文档第五节「统一响应体」。

---

## 本地运行

```powershell
cd server
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- OpenAPI：`http://127.0.0.1:8000/docs`
- 环境：仓根 `cp .env.test .env`（可选 `cp .env.local.example .env.local`），勿使用 `server/.env*`

---

## 代码分层（摘要）

详见 [DEVELOPMENT.md](../DEVELOPMENT.md) 第二节：

- **C 端 / 业务 API**：`app/main.py` → `app/api/router.py` → `app/api/routers/` → `services/` → `models/` / `schemas/`
- **管理端 API**：`server/admin/`（`admin/router.py` 聚合 `admin/routers/*`，挂载前缀 `/api/admin/v1`；与仓库根 `admin/` Vue 静态站对应）

## 接口实现与注释

- 各 **`app/api/routers/*.py`** 内处理函数须写**中文 docstring**（路径、参数、成功 `data`、常见错误），与 **[HTTP 接口规范 §9](../API.md#9-代码位置与接口注释约定)** 一致。
- 前端直连封装见 **`feishu/src/lib/api.ts`**（JSDoc 与后端路径对应）。

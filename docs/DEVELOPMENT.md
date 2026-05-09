# 开发规则与工程约定

## 适用范围

| 项 | 说明 |
|----|------|
| **对应范围** | **全仓库**（根目录、`server/`、`feishu/`、`docs/` 等） |
| **按目录查阅** | 后端专项：[docs/server/README.md](./server/README.md) · 前端专项：[docs/feishu/README.md](./feishu/README.md) |

---

## 1. 仓库与子项目

| 目录 | 技术栈 | 说明 |
|------|--------|------|
| `server/` | Python 3 + FastAPI + SQLAlchemy | HTTP API、库表访问、业务服务 |
| `feishu/` | Vue 3 + Vite + TypeScript | 飞书插件 / 前端页面 |

库名、表与字段以 **[DATABASE.md](./DATABASE.md)** 为准。

## 2. 前端复杂页面与私有组件（`feishu/src/views`）

配置区块较多的页面拆为**目录 + `index.vue` + 私有子组件**：

| 约定 | 说明 |
|------|------|
| 入口 | **`SomeFeature/index.vue`**：表单/状态、校验、`api` 提交、编排子组件 |
| 私有组件 | **`SomeFeature/components/*.vue`**：仅该功能使用，不放全局 `src/components/` |
| 同目录模块 | 可选 **`types.ts`、`constants.ts`**：本页与子组件共享类型与常量 |

示例：**新建任务** → `views/TaskCreateForm/index.vue`，各配置块在 **`views/TaskCreateForm/components/`**。组件名与注释细则见 **[component-style.md](./feishu/component-style.md)**。

## 3. 后端分层（`server/app`）

| 层级 | 路径 | 职责 |
|------|------|------|
| 入口 | `main.py` | 创建 `FastAPI` 应用，仅挂载路由 |
| 路由聚合 | `api/router.py` | `include_router` 汇总子路由 |
| 子路由 | `api/routers/*.py` | HTTP 路径、参数、调用服务 |
| 依赖 | `api/deps.py` | `get_db` 等 |
| 业务 | `services/*.py` | 查询与事务 |
| 模型 | `models/` | ORM 与表映射（与 DATABASE.md 一致） |
| 校验/DTO | `schemas/` | Pydantic |
| 配置常量 | `core/config.py` | 非敏感常量 |
| 数据库引擎 | `db.py` | `DATABASE_URL`、引擎、会话工厂 |

**接口响应格式**：`server/` 对外 JSON 统一为 **`{ code, message, data }`**（成功 `code=0`），详见 **[API.md](./API.md)** 第五节；实现涉及 `schemas/api_response.py`、`api/exception_handlers.py`。

**接口注释**：`app/api/routers/` 下每个路由处理函数须中文说明路径、参数与 `data`；`schemas/` 与 **`feishu/src/lib/api.ts`** 的 JSDoc 与 **[API.md](./API.md) 第九节** 对齐。

## 4. 注释

模块 / 类 / 公开函数使用中文说明职责；避免无意义注释。

## 5. 环境与密钥

- `server/.env` 配置 `DATABASE_URL`，详见 [DATABASE.md](./DATABASE.md)。
- 勿提交 `.env`；模板见 `server/.env.example`。

## 6. 运行（后端）

```powershell
cd server
.\.venv\Scripts\uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## 7. Git

提交聚焦需求；说明「改了什么、为何」。不擅自扩大范围。

## 8. 构建与验证

- **不要求**在每次完成开发任务后固定执行前端生产构建（如 `feishu/` 下 `npm run build`）或等价的全量打包校验；以任务说明、提测、CI 或协作方明确要求为准。
- 需要确认产物、排查构建错误、或用户/流程明确要求验证时，再执行对应构建或测试命令。

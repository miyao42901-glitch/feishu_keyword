# 开发规则与工程约定

## 适用范围

| 项 | 说明 |
|----|------|
| **对应范围** | **全仓库**（根目录、`server/`、`admin/`、`feishu/`、`docs/` 等） |
| **按目录查阅** | 后端专项：[docs/server/README.md](./server/README.md) · 管理端：[admin/README.md](../admin/README.md) · 飞书插件：[docs/feishu/README.md](./feishu/README.md) |

---

## 1. 仓库与子项目

| 目录 | 技术栈 | 说明 |
|------|--------|------|
| `server/` | Python 3 + FastAPI + SQLAlchemy | HTTP API、库表访问、业务服务 |
| `admin/` | Vue 3 + Vite + TypeScript | 管理后台；产物输出到 `public/admin/` |
| `feishu/` | Vue 3 + Vite + TypeScript | 飞书插件；产物输出到 `public/feishu/` |

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

- **不要求**在每次完成开发任务后固定执行前端生产构建；以任务说明、提测、CI 或协作方明确要求为准。
- **GitLab 部署（`test` / `master`）**：Runner **不安装 Node**；须在本地把 **admin** 与 **feishu** 都编译进 `public/admin`、`public/feishu` 后 **提交主仓**（CI 只 rsync）。

```powershell
# 测试环境（推荐：仓根一键脚本）
.\build-public-test.bat

# 或分别执行
cd admin  && npm run build:public:test   # -> public/admin/
cd feishu && npm run build:public:test   # -> public/feishu/
```

正式环境将 `test` 换为 `prod`，或使用 `.\build-public-prod.bat`。详见 [DEPLOY.md](./DEPLOY.md)。

- 需要确认产物、排查构建错误时，再执行上述构建或测试命令。

## 9. 跨模块复用（避免重复造轮子）

**原则**：同一套业务规则、校验、日期/数字处理、API 封装等，**只应在一处维护**；其它页面或路由通过**导入公共模块**复用，禁止在多个组件里复制粘贴后各自改一半。

| 范围 | 建议落点 | 说明 |
|------|----------|------|
| 前端（`feishu/`） | **`feishu/src/lib/*.ts`** | 与具体 `.vue` 无强绑定的纯函数、常量、Element Plus 规则工厂等；已有示例：**`lib/datetime-task-window.ts`**（任务生效/过期时间与 `el-date-picker` 禁用、表单校验）。 |
| 前端仅某功能域内 | 同目录 **`types.ts` / `constants.ts`** 或 `components/` 内再抽一层 | 若逻辑仅被同一 `views/SomeFeature/` 下多个子组件使用，可先放在该目录，**重复出现在第二个功能域时再上提到 `lib/`**。 |
| 后端（`server/`） | **`app/services/`**、**`app/core/`** 或既有工具模块 | 数据库访问仍在 `services`；可复用的纯逻辑抽到独立函数模块，由多个 `routers` 或 `services` 引用。 |

**开发流程（每次改代码都应执行）**：

1. **先搜**：在 `feishu/src`、`server/app` 内 `grep`/搜索是否已有同名或相近实现。  
2. **再决定**：能复用则扩展原模块；不能则新建公共模块并把旧调用迁过去。  
3. **禁止**：为赶工在第二个文件里复制大段相同逻辑且不加注释指向「单一数据源」。

违反本节约定的 PR 应在评审中要求合并重复实现后再合入。

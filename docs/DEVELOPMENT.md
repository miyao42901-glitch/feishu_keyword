# 开发规则与工程约定

## 适用范围

| 项 | 说明 |
|----|------|
| **对应范围** | **全仓库**（根目录、`server/`、`admin/`、`feishu/`、`docs/` 等） |
| **按目录查阅** | 后端：[docs/server/README.md](./server/README.md) · 飞书插件：[docs/feishu/README.md](./feishu/README.md) · 管理后台：[admin/README.md](../admin/README.md) |

---

## 1. 仓库与子项目

| 目录 | 技术栈 | 说明 |
|------|--------|------|
| `server/` | Python 3 + FastAPI + SQLAlchemy + Celery | HTTP `/api/v1`、异步任务、平台采集 Worker |
| `admin/` | Vue 3 + Vite + TypeScript + Element Plus | 管理后台；产物输出到 `public/admin/` |
| `feishu/` | Vue 3 + Vite + TypeScript | 飞书插件；产物输出到 `public/feishu/` |

库名、表与字段以 **[DATABASE.md](./DATABASE.md)** 为准；HTTP 路径与请求体以 **[server/HTTP_API.md](./server/HTTP_API.md)** 为准。

## 2. 前端复杂页面与私有组件（`feishu/src/views`）

配置区块较多的页面拆为**目录 + `index.vue` + 私有子组件**：

| 约定 | 说明 |
|------|------|
| 入口 | **`SomeFeature/index.vue`**：表单/状态、校验、`api` 提交、编排子组件 |
| 私有组件 | **`SomeFeature/components/*.vue`**：仅该功能使用，不放全局 `src/components/` |
| 同目录模块 | 可选 **`types.ts`、`constants.ts`**：本页与子组件共享类型与常量 |

示例：**新建任务** → `views/TaskCreateForm/index.vue`，各配置块在 **`views/TaskCreateForm/components/`**。组件名与注释细则见 **[component-style.md](./feishu/component-style.md)**。

## 3. 后端分层（`server/`）

| 层级 | 路径 | 职责 |
|------|------|------|
| HTTP 入口 | `http_service.py` | 挂载 FastAPI 应用 |
| 本地启动 | `run.py` | 开发态启动 API 与可选调度循环 |
| 路由 | `http_api/v1/*.py` | `/api/v1` 路径、参数校验 |
| 业务 | `social_platform/services/*.py` | 任务、结果、调度 |
| 模型 | `social_platform/models/` | ORM 与表映射（与 DATABASE.md 一致） |
| 校验/DTO | `social_platform/schemas/` | Pydantic |
| 配置 | `config/settings.py` | 读取仓根 `.env` |
| 迁移 | `social_platform/database/db_migrate.py` | 启动时 schema 与列补丁 |
| 采集 | `workers/*_worker/` | 各平台 spider / parser |

**接口注释**：`http_api/v1/` 下路由须中文说明路径、Header、Body；`feishu/src/lib/*.ts` 的 JSDoc 与 **[HTTP_API.md](./server/HTTP_API.md)** 对齐。

## 4. 注释

模块 / 类 / 公开函数使用中文说明职责；避免无意义注释。

## 5. 环境与密钥

- 环境变量**真源在仓库根**：`.env.example`、`.env.test`、`.env.master`、`.env.local.example`；本地 `cp .env.test .env`，可选 `cp .env.local.example .env.local` 覆盖。
- `server/`、`admin/`、`feishu/` 均加载仓根 `.env` → `.env.local`（Vite `envDir` 指向仓根）。
- 勿提交 `.env` / `.env.local`；详见 [DATABASE.md](./DATABASE.md)。

## 6. 运行（后端）

```powershell
cd server
python run.py
```

默认监听 **`http://127.0.0.1:8765`**（`HTTP_HOST` / `HTTP_PORT` 可覆盖）。OpenAPI：`http://127.0.0.1:8765/docs`。

异步任务需另开终端启动 Celery Worker，命令见 [server/README.md](./server/README.md)。

## 7. Git

提交聚焦需求；说明「改了什么、为何」。不擅自扩大范围。

**分支与部署**（个人拼音缩写分支、`test` 仅 merge、`master` 仅 GitLab MR）须遵守 **[GIT_WORKFLOW.md](./GIT_WORKFLOW.md)**，禁止在 `test`/`master` 上直接开发，禁止 `git push origin hxp:test` 跳过本地 `test` 合并。

## 8. 构建与验证

- **不要求**在每次完成开发任务后固定执行前端生产构建；以任务说明、提测、CI 或协作方明确要求为准。
- **GitLab CI**：本地 merge 到 **`test`** 并 `git push origin test` 后，Runner 编译 `public/admin` 与 `public/feishu` 并 **tar+scp** 部署（`deploy-test`）；**GitLab MR 合并 `master`** 后手动 `deploy-prod`。分支流程见 [GIT_WORKFLOW.md](./GIT_WORKFLOW.md)。详见 [DEPLOY.md](./DEPLOY.md)。

```bash
# 本地预检（可选；CI 会在 Linux Runner 上自动 build:public:*）
cp .env.test .env && cd admin && npm run build:public:test
cp .env.test .env && cd feishu && npm run build:public:test
cp .env.master .env && cd admin && npm run build:public:prod
cp .env.master .env && cd feishu && npm run build:public:prod
```

- 需要确认产物、排查构建错误时，再执行上述构建或测试命令。

## 9. 跨模块复用（避免重复造轮子）

**原则**：同一套业务规则、校验、日期/数字处理、API 封装等，**只应在一处维护**；其它页面或路由通过**导入公共模块**复用，禁止在多个组件里复制粘贴后各自改一半。

| 范围 | 建议落点 | 说明 |
|------|----------|------|
| 前端（`feishu/`） | **`feishu/src/lib/*.ts`** | 与具体 `.vue` 无强绑定的纯函数、常量、Element Plus 规则工厂等；已有示例：**`lib/datetime-task-window.ts`**。 |
| 前端仅某功能域内 | 同目录 **`types.ts` / `constants.ts`** 或 `components/` 内再抽一层 | 若逻辑仅被同一 `views/SomeFeature/` 下多个子组件使用，可先放在该目录，**重复出现在第二个功能域时再上提到 `lib/`**。 |
| 后端（`server/`） | **`social_platform/services/`**、**`social_platform/utils/`** | 数据库访问仍在 `services`；可复用的纯逻辑抽到独立模块，由多个路由或 `services` 引用。 |

**开发流程（每次改代码都应执行）**：

1. **先搜**：在 `feishu/src`、`server/` 内 `grep`/搜索是否已有同名或相近实现。
2. **再决定**：能复用则扩展原模块；不能则新建公共模块并把旧调用迁过去。
3. **禁止**：为赶工在第二个文件里复制大段相同逻辑且不加注释指向「单一数据源」。

违反本节约定的 PR 应在评审中要求合并重复实现后再合入。

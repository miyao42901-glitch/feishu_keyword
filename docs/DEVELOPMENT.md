# 开发规则与工程约定

## 1. 仓库与子项目

| 目录 | 技术栈 | 说明 |
|------|--------|------|
| `server/` | Python 3 + FastAPI + SQLAlchemy | HTTP API、库表访问、业务服务 |
| `feishu/` | Vue 3 + Vite + TypeScript | 飞书插件 / 前端页面 |

库名、表与字段以 **[DATABASE.md](./DATABASE.md)** 为准。

## 2. 后端分层（`server/app`）

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
| 数据库引擎 | `db.py` | `DATABASE_URL`、引擎、健康检查 |

## 3. 注释

模块 / 类 / 公开函数使用中文说明职责；避免无意义注释。

## 4. 环境与密钥

- `server/.env` 配置 `DATABASE_URL`，详见 [DATABASE.md](./DATABASE.md)。
- 勿提交 `.env`；模板见 `server/.env.example`。

## 5. 运行（后端）

```powershell
cd server
.\.venv\Scripts\uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## 6. Git

提交聚焦需求；说明「改了什么、为何」。不擅自扩大范围。

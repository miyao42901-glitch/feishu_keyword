"""
按业务域拆分的 HTTP 路由子模块。

每个子模块导出各自的 `APIRouter`，由 `app.api.router` 统一挂载到 `/api` 前缀下。
"""

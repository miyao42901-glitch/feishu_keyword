"""
HTTP API 包。

目录约定：
- `deps.py`：依赖注入（如 `get_db`）；
- `router.py`：聚合子路由；
- `routers/`：按业务拆分的 `APIRouter`；
- `routes.py`：兼容旧导入路径，转发至 `router.api_router`。
"""

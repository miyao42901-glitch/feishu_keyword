"""
聚合所有子路由，供 `main` 挂载到统一前缀 `/api`。

新增业务域时：在 `app.api.routers` 下增加模块，并在此处 `include_router`。

当前子模块与路径前缀（具体路径见各模块内 `@router` 装饰器）：

| 模块 | 文件 | 说明 |
|------|------|------|
| 监控方案 | `routers/monitoring_plans.py` | `GET /api/monitoring-plans` 等 |
| 飞书任务配置 | `routers/feishu_task_configs.py` | `GET|POST|PUT /api/feishu-task-configs` |

各路由处理函数须用中文文档字符串说明用途、主要参数与成功时 `data` 形态（与 `docs/API.md` 一致）。
"""

from fastapi import APIRouter

from app.api.routers import feishu_task_configs, monitoring_plans

api_router = APIRouter()
api_router.include_router(monitoring_plans.router, tags=["监控方案"])
api_router.include_router(feishu_task_configs.router, tags=["飞书任务配置"])

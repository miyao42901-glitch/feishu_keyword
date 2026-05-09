"""
聚合所有子路由，供 `main` 挂载到统一前缀 `/api`。

新增业务域时：在 `app.api.routers` 下增加模块，并在此处 `include_router`。
"""

from fastapi import APIRouter

from app.api.routers import feishu_task_configs, health, monitoring_plans

api_router = APIRouter()
api_router.include_router(health.router, tags=["健康检查"])
api_router.include_router(monitoring_plans.router, tags=["监控方案"])
api_router.include_router(feishu_task_configs.router, tags=["飞书任务配置"])

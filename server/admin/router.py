"""管理端 API 总路由，挂载到 `/api/admin/v1`。"""

from fastapi import APIRouter

from admin.routers import system
from admin.schemas.response import admin_ok

admin_router = APIRouter()
admin_router.include_router(system.router)


@admin_router.get("/health", tags=["管理端-探活"])
def admin_health():
    """运维探活，免登录。"""
    return admin_ok(data={"ok": True, "module": "admin"})

"""管理端 API 总路由，挂载于 `/api/admin/v1`。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, FastAPI

from admin.deps import AdminContext, require_admin
from admin.routers import system
from admin.schemas.response import admin_ok

admin_router = APIRouter()
admin_router.include_router(system.router)


@admin_router.get("/health", tags=["管理端-探活"])
def admin_health():
    """运维探活，免登录。"""
    return admin_ok(data={"ok": True, "module": "admin"})


@admin_router.get("/system/me", tags=["管理端-系统"])
def admin_me(ctx: AdminContext = Depends(require_admin)):
    """当前登录管理员信息（需 Header `token`）。"""
    return admin_ok(data={"admin": ctx.profile, "admin_id": ctx.admin_id})


def register_admin_routes(app: FastAPI) -> None:
    app.include_router(admin_router, prefix="/api/admin/v1")

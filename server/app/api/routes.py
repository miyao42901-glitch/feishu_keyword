"""
兼容入口：历史代码可能从本模块导入 `router`。

实际聚合逻辑见 `app.api.router.api_router`。
"""

from app.api.router import api_router as router

__all__ = ["router"]

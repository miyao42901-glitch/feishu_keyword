"""注册 v1 路由：同步 + 异步。"""

from __future__ import annotations

from fastapi import FastAPI

from http_api.constants import API_V1_PREFIX
from http_api.v1.async_api import build_async_router
from http_api.v1.results_api import build_results_router
from http_api.v1.sync_api import build_sync_routers


def register_v1_routes(app: FastAPI) -> None:
    """仅注册版本化路径：`/api/v1/...`。"""
    health_r, run_r, sync_r = build_sync_routers()
    async_r = build_async_router()
    results_r = build_results_router()

    app.include_router(health_r, prefix=API_V1_PREFIX)
    app.include_router(run_r, prefix=API_V1_PREFIX)
    app.include_router(sync_r, prefix=API_V1_PREFIX)
    app.include_router(async_r, prefix=API_V1_PREFIX)
    app.include_router(results_r, prefix=API_V1_PREFIX)

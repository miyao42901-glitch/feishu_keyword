"""API v1：抖音 / 小红书同步接口 + 聚合 POST /api/v1/run。"""
from __future__ import annotations

from typing import Annotated, Any

from douyin_worker._job import run_task as run_douyin
from fastapi import APIRouter, FastAPI, Header
from fastapi.responses import JSONResponse
from http_api.dajiala_params import to_worker_params
from http_sync_bodies import (
    DouyinSearchAllBody,
    DouyinSearchPageBody,
    XhsSearchAllBody,
    XhsSearchPageBody,
)
from social_platform.aggregated_job import run_task as run_multi
from social_platform.api_response import from_worker_run, ok
from social_platform.schemas import TaskEnvelope
from xhs_worker._job import run_task as run_xhs

from http_api.versions import API_V1_PREFIX


def _resp(run_task_fn: Any, action: str, params: dict[str, Any]) -> JSONResponse:
    raw = run_task_fn({"action": action, "params": params})
    return JSONResponse(from_worker_run(raw))


def _sync_worker_params(x_api_key: str, body: Any) -> dict[str, Any]:
    """Worker 仍用 `key` 字段承载凭证；对外同步接口凭证来自 Header `X-API-Key`。"""
    return {"key": x_api_key.strip(), **body.model_dump()}


def _build_routers() -> tuple[APIRouter, APIRouter, APIRouter]:
    health = APIRouter(tags=["v1-health"])
    run_ = APIRouter(tags=["v1-aggregate"])
    sync = APIRouter(prefix="/sync", tags=["v1-sync"])

    @health.get("/health")
    def health_v1() -> dict[str, Any]:
        return ok(data={"status": "ok"})

    @run_.post("/run")
    def run_aggregate(body: TaskEnvelope) -> JSONResponse:
        """按 action 前缀走抖音或小红书（与 aggregated_job 相同逻辑）。"""
        payload = body.model_dump()
        payload["params"] = to_worker_params(payload.get("params") or {})
        raw = run_multi(payload)
        return JSONResponse(from_worker_run(raw))

    @sync.post("/douyin/search-page")
    def douyin_search_page_post(
        body: DouyinSearchPageBody,
        x_api_key: Annotated[str, Header(alias="X-API-Key", min_length=1)],
    ) -> JSONResponse:
        return _resp(run_douyin, "douyin_search_page", _sync_worker_params(x_api_key, body))

    @sync.post("/douyin/search-all")
    def douyin_search_all_post(
        body: DouyinSearchAllBody,
        x_api_key: Annotated[str, Header(alias="X-API-Key", min_length=1)],
    ) -> JSONResponse:
        return _resp(run_douyin, "douyin_search_all", _sync_worker_params(x_api_key, body))

    @sync.post("/xhs/search-page")
    def xhs_search_page_post(
        body: XhsSearchPageBody,
        x_api_key: Annotated[str, Header(alias="X-API-Key", min_length=1)],
    ) -> JSONResponse:
        return _resp(run_xhs, "xhs_search_page", _sync_worker_params(x_api_key, body))

    @sync.post("/xhs/search-all")
    def xhs_search_all_post(
        body: XhsSearchAllBody,
        x_api_key: Annotated[str, Header(alias="X-API-Key", min_length=1)],
    ) -> JSONResponse:
        return _resp(run_xhs, "xhs_search_all", _sync_worker_params(x_api_key, body))

    return health, run_, sync


def register_v1_routes(app: FastAPI) -> None:
    """仅注册版本化路径：`/api/v1/...`。"""
    health_r, run_r, sync_r = _build_routers()

    app.include_router(health_r, prefix=API_V1_PREFIX)
    app.include_router(run_r, prefix=API_V1_PREFIX)
    app.include_router(sync_r, prefix=API_V1_PREFIX)

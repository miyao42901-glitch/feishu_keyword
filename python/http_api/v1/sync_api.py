"""API v1：抖音 / 小红书同步接口 + 聚合 POST /api/v1/run。"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated, Any

_repo_py = Path(__file__).resolve().parent.parent.parent
for _d in (_repo_py, _repo_py / "workers"):
    _s = str(_d.resolve())
    if _s not in {str(Path(p).resolve()) for p in sys.path if isinstance(p, str) and p}:
        sys.path.insert(0, _s)

from douyin_worker._job import execute_douyin_search_all, run_task as run_douyin
from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse
from social_platform.utils.param_dict import to_worker_params
from http_sync_bodies import (
    DouyinSearchAllBody,
    DouyinSearchPageBody,
    XhsSearchAllBody,
    XhsSearchPageBody,
)
from social_platform.aggregated_job import run_task as run_multi
from social_platform.api_response import from_worker_run, ok
from social_platform.schemas import TaskEnvelope
from social_platform.services.search_persist import (
    try_save_search_after_crawl,
    try_save_search_result_chunk,
)
from xhs_worker._job import execute_xhs_search_all, run_task as run_xhs


def _resp(
    run_task_fn: Any,
    action: str,
    params: dict[str, Any],
    *,
    user_id: str,
) -> JSONResponse:
    raw = run_task_fn({"action": action, "params": params})
    try_save_search_after_crawl(action, params, raw, user_id=user_id, task_id=None)
    return JSONResponse(from_worker_run(raw))


def _sync_worker_params(x_api_key: str, body: Any) -> dict[str, Any]:
    """Worker 仍用 `key` 字段承载凭证；对外同步接口凭证来自 Header `X-API-Key`。"""
    return {"key": x_api_key.strip(), **body.model_dump()}


def build_sync_routers() -> tuple[APIRouter, APIRouter, APIRouter]:
    health = APIRouter(tags=["v1-health"])
    run_ = APIRouter(tags=["v1-aggregate"])
    sync = APIRouter(prefix="/sync", tags=["v1-sync"])

    @health.get("/health")
    def health_v1() -> dict[str, Any]:
        return ok(data={"status": "ok"})

    @run_.post("/run")
    def run_aggregate(
        body: TaskEnvelope,
        x_user_id: Annotated[str, Header(alias="X-User-Id", min_length=1)],
    ) -> JSONResponse:
        """按 action 前缀走抖音或小红书（与 aggregated_job 相同逻辑）。"""
        payload = body.model_dump()
        payload["params"] = to_worker_params(payload.get("params") or {})
        raw = run_multi(payload)
        try_save_search_after_crawl(
            str(payload.get("action") or ""),
            dict(payload.get("params") or {}),
            raw,
            user_id=x_user_id.strip(),
            task_id=None,
        )
        return JSONResponse(from_worker_run(raw))

    @sync.post("/douyin/search-page")
    def douyin_search_page_post(
        body: DouyinSearchPageBody,
        x_api_key: Annotated[str, Header(alias="X-API-Key", min_length=1)],
        x_user_id: Annotated[str, Header(alias="X-User-Id", min_length=1)],
    ) -> JSONResponse:
        return _resp(
            run_douyin,
            "douyin_search_page",
            _sync_worker_params(x_api_key, body),
            user_id=x_user_id.strip(),
        )

    @sync.post("/douyin/search-all")
    def douyin_search_all_post(
        body: DouyinSearchAllBody,
        x_api_key: Annotated[str, Header(alias="X-API-Key", min_length=1)],
        x_user_id: Annotated[str, Header(alias="X-User-Id", min_length=1)],
    ) -> JSONResponse:
        params = _sync_worker_params(x_api_key, body)
        uid = x_user_id.strip()

        def _sync_page(chunk: list) -> None:
            try_save_search_result_chunk(
                "douyin_search_all", params, chunk, user_id=uid, task_id=None
            )

        raw = execute_douyin_search_all(params, sync_page_save=_sync_page)
        try_save_search_after_crawl("douyin_search_all", params, raw, user_id=uid, task_id=None)
        return JSONResponse(from_worker_run(raw))

    @sync.post("/xhs/search-page")
    def xhs_search_page_post(
        body: XhsSearchPageBody,
        x_api_key: Annotated[str, Header(alias="X-API-Key", min_length=1)],
        x_user_id: Annotated[str, Header(alias="X-User-Id", min_length=1)],
    ) -> JSONResponse:
        return _resp(
            run_xhs,
            "xhs_search_page",
            _sync_worker_params(x_api_key, body),
            user_id=x_user_id.strip(),
        )

    @sync.post("/xhs/search-all")
    def xhs_search_all_post(
        body: XhsSearchAllBody,
        x_api_key: Annotated[str, Header(alias="X-API-Key", min_length=1)],
        x_user_id: Annotated[str, Header(alias="X-User-Id", min_length=1)],
    ) -> JSONResponse:
        params = _sync_worker_params(x_api_key, body)
        uid = x_user_id.strip()

        def _sync_page(chunk: list) -> None:
            try_save_search_result_chunk(
                "xhs_search_all", params, chunk, user_id=uid, task_id=None
            )

        raw = execute_xhs_search_all(params, sync_page_save=_sync_page)
        try_save_search_after_crawl("xhs_search_all", params, raw, user_id=uid, task_id=None)
        return JSONResponse(from_worker_run(raw))

    return health, run_, sync

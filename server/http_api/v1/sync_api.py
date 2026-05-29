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

from douyin_worker._job import execute_douyin_search_all
from douyin_worker._job import run_task as run_douyin
from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse
from mp_worker._job import run_task as run_mp
from wxvideo_worker._job import run_task as run_wx
from xhs_worker._job import execute_xhs_search_all
from xhs_worker._job import run_task as run_xhs

from http_api.rate_limit import ip_rate_limit
from http_sync_bodies import (
    DouyinSearchAllBody,
    DouyinSearchPageBody,
    MpSearchAllBody,
    MpSearchPageBody,
    WxSosoSearchAllBody,
    WxSosoSearchPageBody,
    XhsSearchAllBody,
    XhsSearchPageBody,
)
from social_platform.aggregated_job import run_task as run_multi
from social_platform.api_response import from_worker_run, ok, respond
from social_platform.schemas import TaskEnvelope
from social_platform.services.search_persist import (
    try_save_search_after_crawl,
    try_save_search_result_chunk,
)
from social_platform.utils.param_dict import to_worker_params


def _resp(run_task_fn: Any, action: str, params: dict[str, Any]) -> JSONResponse:
    raw = run_task_fn({"action": action, "params": params})
    try_save_search_after_crawl(action, params, raw, user_id="", task_id=None)
    return respond(from_worker_run(raw))


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

    @run_.post(
        "/run",
        dependencies=[ip_rate_limit(max_requests=30, window_seconds=60, scope="sync_run")],
    )
    def run_aggregate(body: TaskEnvelope) -> JSONResponse:
        """按 action 前缀走抖音或小红书（与 aggregated_job 相同逻辑）。"""
        payload = body.model_dump()
        payload["params"] = to_worker_params(payload.get("params") or {})
        raw = run_multi(payload)
        try_save_search_after_crawl(
            str(payload.get("action") or ""),
            dict(payload.get("params") or {}),
            raw,
            user_id="",
            task_id=None,
        )

        return respond(from_worker_run(raw))

    @sync.post(
        "/douyin/search-page",
        dependencies=[
            ip_rate_limit(max_requests=60, window_seconds=60, scope="sync_search_page")
        ],
    )
    def douyin_search_page_post(
        body: DouyinSearchPageBody,
        x_api_key: Annotated[str, Header(alias="X-API-Key", min_length=1)],
    ) -> JSONResponse:
        return _resp(
            run_douyin,
            "douyin_search_page",
            _sync_worker_params(x_api_key, body),
        )

    @sync.post(
        "/douyin/search-all",
        dependencies=[
            ip_rate_limit(max_requests=10, window_seconds=60, scope="sync_search_all")
        ],
    )
    def douyin_search_all_post(
        body: DouyinSearchAllBody,
        x_api_key: Annotated[str, Header(alias="X-API-Key", min_length=1)],
    ) -> JSONResponse:
        params = _sync_worker_params(x_api_key, body)

        def _sync_page(chunk: list) -> None:
            try_save_search_result_chunk(
                "douyin_search_all", params, chunk, user_id="", task_id=None
            )

        raw = execute_douyin_search_all(params, sync_page_save=_sync_page)

        try_save_search_after_crawl(
            "douyin_search_all", params, raw, user_id="", task_id=None
        )

        return respond(from_worker_run(raw))

    @sync.post(
        "/xhs/search-page",
        dependencies=[
            ip_rate_limit(max_requests=60, window_seconds=60, scope="sync_search_page")
        ],
    )
    def xhs_search_page_post(
        body: XhsSearchPageBody,
        x_api_key: Annotated[str, Header(alias="X-API-Key", min_length=1)],
    ) -> JSONResponse:
        return _resp(
            run_xhs,
            "xhs_search_page",
            _sync_worker_params(x_api_key, body),
        )

    @sync.post(
        "/xhs/search-all",
        dependencies=[
            ip_rate_limit(max_requests=10, window_seconds=60, scope="sync_search_all")
        ],
    )
    def xhs_search_all_post(
        body: XhsSearchAllBody,
        x_api_key: Annotated[str, Header(alias="X-API-Key", min_length=1)],
    ) -> JSONResponse:
        params = _sync_worker_params(x_api_key, body)

        def _sync_page(chunk: list) -> None:
            try_save_search_result_chunk(
                "xhs_search_all", params, chunk, user_id="", task_id=None
            )

        raw = execute_xhs_search_all(params, sync_page_save=_sync_page)

        try_save_search_after_crawl(
            "xhs_search_all", params, raw, user_id="", task_id=None
        )

        return respond(from_worker_run(raw))

    @sync.post(
        "/wxvideo/search-page",
        dependencies=[
            ip_rate_limit(max_requests=60, window_seconds=60, scope="sync_search_page")
        ],
    )
    def wx_sousou_search_page_post(
        body: WxSosoSearchPageBody,
        x_api_key: Annotated[str, Header(alias="X-API-Key", min_length=1)],
    ) -> JSONResponse:
        return _resp(
            run_wx,
            "wx_sousou_search_page",
            _sync_worker_params(x_api_key, body),
        )

    @sync.post(
        "/wxvideo/search-all",
        dependencies=[
            ip_rate_limit(max_requests=10, window_seconds=60, scope="sync_search_all")
        ],
    )
    def wx_sousou_search_all_post(
        body: WxSosoSearchAllBody,
        x_api_key: Annotated[str, Header(alias="X-API-Key", min_length=1)],
    ) -> JSONResponse:
        params = _sync_worker_params(x_api_key, body)

        raw = run_wx({"action": "wx_sousou_search_all", "params": params})

        try_save_search_after_crawl(
            "wx_sousou_search_all", params, raw, user_id="", task_id=None
        )

        return respond(from_worker_run(raw))

    @sync.post(
        "/mp/search-page",
        dependencies=[
            ip_rate_limit(max_requests=60, window_seconds=60, scope="sync_search_page")
        ],
    )
    def mp_search_page_post(
        body: MpSearchPageBody,
        x_api_key: Annotated[str, Header(alias="X-API-Key", min_length=1)],
    ) -> JSONResponse:
        return _resp(
            run_mp,
            "mp-search-page",
            _sync_worker_params(x_api_key, body),
        )

    @sync.post(
        "/mp/search-all",
        dependencies=[
            ip_rate_limit(max_requests=10, window_seconds=60, scope="sync_search_all")
        ],
    )
    def mp_search_all_post(
        body: MpSearchAllBody,
        x_api_key: Annotated[str, Header(alias="X-API-Key", min_length=1)],
    ) -> JSONResponse:
        params = _sync_worker_params(x_api_key, body)

        raw = run_mp({"action": "mp-search-all", "params": params})

        try_save_search_after_crawl(
            "mp-search-all", params, raw, user_id="", task_id=None
        )

        return respond(from_worker_run(raw))

    return health, run_, sync

"""结果验收：四平台批量接口（含同步单次、无 task_id 的数据）。"""

from __future__ import annotations

from typing import Annotated, Any, Generator, Optional

from fastapi import APIRouter, Body, Depends, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from http_api.rate_limit import ip_rate_limit
from http_api.rate_limit_scopes import (
    RESULT_ACCEPTANCE_ACCEPT,
    RESULT_ACCEPTANCE_PENDING,
)
from social_platform.api_response import ok_with_meta, respond, respond_err, respond_yddm_error
from social_platform.api_status_codes import CODE_BAD_REQUEST, CODE_SERVICE_UNAVAILABLE, get_message
from social_platform.services import result_service, task_service
from social_platform.services.yddm_user_client import YddmCallError

_DB_UNAVAILABLE_MSG = "异步任务未配置：请设置环境变量 DATABASE_URL"


def get_db() -> Generator[Optional[Session], None, None]:
    if not task_service.database_configured():
        yield None
        return

    from social_platform.database.session import get_session_factory

    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()


def _require_db(db: Optional[Session]) -> None:
    if db is None:
        raise respond_err(CODE_SERVICE_UNAVAILABLE, _DB_UNAVAILABLE_MSG, http_status=503)


def build_results_router() -> APIRouter:
    r = APIRouter(prefix="/results", tags=["v1-results"])

    @r.get(
        "/acceptance",
        dependencies=[
            ip_rate_limit(
                max_requests=120, window_seconds=60, scope=RESULT_ACCEPTANCE_PENDING
            )
        ],
    )
    def list_pending_acceptance(
        x_api_key: Annotated[str, Header(alias="X-API-Key", min_length=1)],
        x_user_id: Annotated[str, Header(alias="X-User-Id", min_length=1)],
        db: Annotated[Optional[Session], Depends(get_db)],
    ) -> JSONResponse:
        """
        待验收 id 列表（``is_upload=0``）。
        返回 ``{ "douyin": [1,2], "xhs": [3], ... }``，含无 task_id 的同步单次数据。
        """
        if db is None:
            return respond_err(CODE_SERVICE_UNAVAILABLE, _DB_UNAVAILABLE_MSG, http_status=503)

        try:
            uid = task_service.assert_async_task_user(
                api_key=x_api_key.strip(),
                x_user_id=x_user_id.strip(),
            )
        except YddmCallError as e:
            return respond_yddm_error(e.api_code, e.message, http_status=e.http_status)

        data, meta = result_service.list_batch_acceptance_pending(db, user_id=uid)  # type: ignore[arg-type]
        return respond(ok_with_meta(data, meta))

    @r.post(
        "/acceptance",
        dependencies=[
            ip_rate_limit(
                max_requests=60, window_seconds=60, scope=RESULT_ACCEPTANCE_ACCEPT
            )
        ],
    )
    def accept_batch(
        body: Annotated[dict[str, Any], Body(...)],
        x_api_key: Annotated[str, Header(alias="X-API-Key", min_length=1)],
        x_user_id: Annotated[str, Header(alias="X-User-Id", min_length=1)],
        db: Annotated[Optional[Session], Depends(get_db)],
    ) -> JSONResponse:
        """
        验收通过：请求体为平台 → id 列表，例如
        ``{ "douyin": [1, 2], "xhs": [3] }``。
        """
        if db is None:
            return respond_err(CODE_SERVICE_UNAVAILABLE, _DB_UNAVAILABLE_MSG, http_status=503)

        by_platform: dict[str, list[int]] = {}
        for key, val in (body or {}).items():
            if key in ("accepted", "total"):
                continue
            if not isinstance(val, list):
                return respond_err(
                    CODE_BAD_REQUEST,
                    f"invalid ids for platform {key!r}: expected list",
                    http_status=400,
                )
            by_platform[str(key)] = [int(i) for i in val]
        if not by_platform:
            return respond_err(
                CODE_BAD_REQUEST,
                get_message(CODE_BAD_REQUEST),
                http_status=400,
            )

        try:
            uid = task_service.assert_async_task_user(
                api_key=x_api_key.strip(),
                x_user_id=x_user_id.strip(),
            )
        except YddmCallError as e:
            return respond_yddm_error(e.api_code, e.message, http_status=e.http_status)

        try:
            data, meta = result_service.accept_batch_results(
                db,  # type: ignore[arg-type]
                user_id=uid,
                by_platform=by_platform,
            )
        except ValueError as e:
            return respond_err(
                CODE_BAD_REQUEST,
                str(e) or get_message(CODE_BAD_REQUEST),
                http_status=400,
            )

        return respond(ok_with_meta(data, meta))

    return r

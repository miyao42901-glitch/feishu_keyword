"""API v1：异步任务提交 / 状态 / 结果分页。"""

from __future__ import annotations

from typing import Annotated, Generator, Optional

from fastapi import APIRouter, Depends, Header, Query
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from config.settings import get_settings
from http_api.rate_limit import ip_rate_limit
from http_api.rate_limit_scopes import (
    ASYNC_SUBMIT,
    ASYNC_TASK_CANCEL,
    ASYNC_TASK_DELETE,
    ASYNC_TASK_EDIT,
    ASYNC_TASK_LIST,
    ASYNC_TASK_RESTART,
    ASYNC_TASK_RESULTS,
    ASYNC_TASK_STATUS,
)
from social_platform.actions.registry import get_action_spec
from social_platform.api_response import (
    ApiHttpError,
    async_task_meta,
    ok_with_meta,
    respond,
    respond_err,
    respond_yddm_error,
)
from social_platform.api_status_codes import (
    CODE_ASYNC_SUBMIT_DUPLICATE,
    CODE_ASYNC_SUBMIT_USER_MISMATCH,
    CODE_ASYNC_TASK_ALREADY_ACTIVE,
    CODE_ASYNC_TASK_ALREADY_CANCELLED,
    CODE_ASYNC_TASK_WINDOW_ENDED,
    CODE_BAD_REQUEST,
    CODE_NOT_FOUND,
    CODE_SERVICE_UNAVAILABLE,
    CODE_UNSUPPORTED_ACTION,
    get_message,
)
from social_platform.schemas.async_edit import AsyncTaskEditRequest
from social_platform.schemas.async_submit import AsyncTaskSubmitRequest
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


def _require_matching_user(*, task_user_id: str, x_user_id: Optional[str]) -> None:
    if x_user_id is None or not str(x_user_id).strip():
        return

    if str(task_user_id).strip() != str(x_user_id).strip():
        raise ApiHttpError(
            CODE_ASYNC_SUBMIT_USER_MISMATCH,
            http_status=403,
        )


def _require_db(db: Optional[Session]) -> None:
    if db is None:
        raise ApiHttpError(
            CODE_SERVICE_UNAVAILABLE,
            _DB_UNAVAILABLE_MSG,
            http_status=503,
        )


def _edit_async_task_handler(
    *,
    body: AsyncTaskEditRequest,
    x_api_key: str,
    x_user_id: str,
    db: Session,
) -> JSONResponse:
    try:
        uid = task_service.assert_async_task_user(
            api_key=x_api_key.strip(),
            x_user_id=x_user_id.strip(),
        )
    except YddmCallError as e:
        return respond_yddm_error(e.api_code, e.message, http_status=e.http_status)

    try:
        updated = task_service.update_async_task(
            db,
            str(body.task_id),
            user_id=uid,
            updates=body.updates_dict(),
        )
    except ValidationError as ve:
        return respond_err(
            CODE_BAD_REQUEST,
            get_message(CODE_BAD_REQUEST),
            data={"errors": ve.errors()},
            http_status=400,
        )
    except ApiHttpError as e:
        return respond_err(
            e.code,
            e.msg,
            e.data,
            http_status=e.http_status,
            headers=e.headers,
        )
    except ValueError as e:
        return respond_err(
            CODE_BAD_REQUEST,
            str(e) or get_message(CODE_BAD_REQUEST),
            http_status=400,
        )

    if updated is None:
        return respond_err(CODE_NOT_FOUND, http_status=404)

    return respond(
        ok_with_meta(
            updated.model_dump(),
            async_task_meta(platform=updated.platform, action=updated.action),
        )
    )


def build_async_router() -> APIRouter:
    r = APIRouter(prefix="/async", tags=["v1-async"])

    @r.post(
        "/tasks",
        dependencies=[ip_rate_limit(max_requests=30, window_seconds=60, scope=ASYNC_SUBMIT)],
    )
    def submit_async_task(
        body: AsyncTaskSubmitRequest,
        x_api_key: Annotated[str, Header(alias="X-API-Key", min_length=1)],
        x_user_id: Annotated[str, Header(alias="X-User-Id", min_length=1)],
        db: Annotated[Optional[Session], Depends(get_db)],
        priority: Annotated[int, Query(ge=0, le=9)] = 0,
    ) -> JSONResponse:

        _require_db(db)

        if not task_service.redis_ready():
            return respond_err(
                CODE_SERVICE_UNAVAILABLE,
                "Redis 未就绪：异步任务需 Redis 缓存与调度，请检查 REDIS_URL",
                http_status=503,
            )

        action = (body.action or "").strip()

        if get_action_spec(action) is None:
            return respond_err(CODE_UNSUPPORTED_ACTION, http_status=400)

        try:
            schedule_start, schedule_end = task_service.parse_task_schedule_times(
                body.task_start_time,
                body.task_end_time,
            )

            tid = task_service.submit_async_task(
                db,  # type: ignore[arg-type]
                action=action,
                body=body.body if isinstance(body.body, dict) else {},
                user_id=x_user_id.strip(),
                api_key=x_api_key.strip(),
                task_name=body.task_name,
                task_start_time=schedule_start,
                task_end_time=schedule_end,
                interval_minutes=task_service.normalize_interval_minutes(
                    body.interval_minutes
                ),
                fetch_count=task_service.normalize_fetch_count(body.fetch_count),
                priority=priority,
            )

        except ValidationError as ve:

            return respond_err(
                CODE_BAD_REQUEST,
                get_message(CODE_BAD_REQUEST),
                data={"errors": ve.errors()},
                http_status=400,
            )

        except LookupError:

            return respond_err(CODE_UNSUPPORTED_ACTION, http_status=400)

        except ValueError as e:

            return respond_err(
                CODE_BAD_REQUEST,
                str(e) or get_message(CODE_BAD_REQUEST),
                http_status=400,
            )

        except RuntimeError as e:

            return respond_err(
                CODE_SERVICE_UNAVAILABLE,
                str(e) or get_message(CODE_SERVICE_UNAVAILABLE),
                http_status=503,
            )

        except task_service.AsyncTaskDuplicateError as dup:

            return respond_err(
                CODE_ASYNC_SUBMIT_DUPLICATE,
                get_message(CODE_ASYNC_SUBMIT_DUPLICATE),
                data={"task_id": dup.existing_task_id},
                http_status=409,
            )

        except YddmCallError as e:

            return respond_yddm_error(e.api_code, e.message, http_status=e.http_status)

        spec = get_action_spec(action)

        plat = spec.platform if spec is not None else ""

        st = task_service.get_task_status(db, str(tid))  # type: ignore[arg-type]
        result: dict = {"task_id": tid, "status": "pending"}
        if st is not None:
            result = st.model_dump()

        return respond(
            ok_with_meta(
                result,
                async_task_meta(platform=plat, action=action),
            )
        )

    @r.post(
        "/tasks/edit",
        dependencies=[
            ip_rate_limit(max_requests=60, window_seconds=60, scope=ASYNC_TASK_EDIT)
        ],
    )
    def edit_async_task(
        body: AsyncTaskEditRequest,
        x_api_key: Annotated[str, Header(alias="X-API-Key", min_length=1)],
        x_user_id: Annotated[str, Header(alias="X-User-Id", min_length=1)],
        db: Annotated[Optional[Session], Depends(get_db)],
    ) -> JSONResponse:
        _require_db(db)
        return _edit_async_task_handler(
            body=body,
            x_api_key=x_api_key,
            x_user_id=x_user_id,
            db=db,  # type: ignore[arg-type]
        )

    @r.get(
        "/tasks",
        dependencies=[
            ip_rate_limit(max_requests=60, window_seconds=60, scope=ASYNC_TASK_LIST)
        ],
    )
    def list_async_tasks(
        x_api_key: Annotated[str, Header(alias="X-API-Key", min_length=1)],
        x_user_id: Annotated[str, Header(alias="X-User-Id", min_length=1)],
        db: Annotated[Optional[Session], Depends(get_db)],
        page: Annotated[int, Query(ge=1)] = 1,
        limit: Annotated[int, Query(ge=1, le=100)] = 20,
        task_status: Annotated[
            Optional[str],
            Query(description="按状态筛选：pending/running/success/failed/cancelled"),
        ] = None,
    ) -> JSONResponse:
        _require_db(db)

        try:
            uid = task_service.assert_async_task_user(
                api_key=x_api_key.strip(),
                x_user_id=x_user_id.strip(),
            )
        except YddmCallError as e:
            return respond_yddm_error(e.api_code, e.message, http_status=e.http_status)

        data = task_service.list_async_tasks_for_user(
            db,  # type: ignore[arg-type]
            uid,
            page=page,
            limit=limit,
            status=task_status,
        )
        return respond(
            ok_with_meta(
                data.model_dump(),
                async_task_meta(platform="", action=""),
            )
        )

    @r.get(
        "/tasks/{task_id}",
        dependencies=[
            ip_rate_limit(max_requests=120, window_seconds=60, scope=ASYNC_TASK_STATUS)
        ],
    )
    def get_task_status(
        task_id: str,
        db: Annotated[Optional[Session], Depends(get_db)],
        x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    ) -> JSONResponse:

        _require_db(db)

        st = task_service.get_task_status(db, task_id)  # type: ignore[arg-type]

        if st is None:
            return respond_err(CODE_NOT_FOUND, http_status=404)

        _require_matching_user(task_user_id=st.user_id, x_user_id=x_user_id)

        return respond(
            ok_with_meta(
                st.model_dump(),
                async_task_meta(platform=st.platform, action=st.action),
            )
        )

    @r.post(
        "/tasks/{task_id}/cancel",
        dependencies=[
            ip_rate_limit(max_requests=30, window_seconds=60, scope=ASYNC_TASK_CANCEL)
        ],
    )
    def cancel_async_task(
        task_id: str,
        x_api_key: Annotated[str, Header(alias="X-API-Key", min_length=1)],
        x_user_id: Annotated[str, Header(alias="X-User-Id", min_length=1)],
        db: Annotated[Optional[Session], Depends(get_db)],
    ) -> JSONResponse:
        _require_db(db)

        try:
            uid = task_service.assert_async_task_user(
                api_key=x_api_key.strip(),
                x_user_id=x_user_id.strip(),
            )
        except YddmCallError as e:
            return respond_yddm_error(e.api_code, e.message, http_status=e.http_status)

        try:
            outcome = task_service.cancel_async_task(
                db,  # type: ignore[arg-type]
                task_id,
                user_id=uid,
            )
        except ApiHttpError as e:
            return respond_err(
                e.code,
                e.msg,
                e.data,
                http_status=e.http_status,
                headers=e.headers,
            )

        if outcome is None:
            return respond_err(CODE_NOT_FOUND, http_status=404)

        if outcome == "already_cancelled":
            return respond_err(
                CODE_ASYNC_TASK_ALREADY_CANCELLED,
                get_message(CODE_ASYNC_TASK_ALREADY_CANCELLED),
                data={"task_id": task_id, "status": "cancelled"},
                http_status=409,
            )

        st = task_service.get_task_status(db, task_id)  # type: ignore[arg-type]
        if st is None:
            return respond_err(CODE_NOT_FOUND, http_status=404)

        return respond(
            ok_with_meta(
                {"task_id": st.task_id, "status": st.status},
                async_task_meta(platform=st.platform, action=st.action),
            )
        )

    @r.post(
        "/tasks/{task_id}/delete",
        dependencies=[
            ip_rate_limit(max_requests=30, window_seconds=60, scope=ASYNC_TASK_DELETE)
        ],
    )
    def delete_async_task(
        task_id: str,
        x_user_id: Annotated[str, Header(alias="X-User-Id", min_length=1)],
        db: Annotated[Optional[Session], Depends(get_db)],
    ) -> JSONResponse:
        """删除任务：仅校验 X-User-Id 与库中 user_id 一致（不调用 yddm）；任意状态含 cancelled 均可删。"""
        _require_db(db)

        try:
            deleted = task_service.delete_async_task(
                db,  # type: ignore[arg-type]
                task_id,
                user_id=x_user_id.strip(),
            )
        except ApiHttpError as e:
            return respond_err(
                e.code,
                e.msg,
                e.data,
                http_status=e.http_status,
                headers=e.headers,
            )

        if not deleted:
            return respond_err(CODE_NOT_FOUND, http_status=404)

        return respond(
            ok_with_meta(
                {"task_id": task_id, "deleted": True},
                async_task_meta(platform="", action=""),
            )
        )

    @r.post(
        "/tasks/{task_id}/restart",
        dependencies=[
            ip_rate_limit(max_requests=30, window_seconds=60, scope=ASYNC_TASK_RESTART)
        ],
    )
    def restart_async_task(
        task_id: str,
        x_api_key: Annotated[str, Header(alias="X-API-Key", min_length=1)],
        x_user_id: Annotated[str, Header(alias="X-User-Id", min_length=1)],
        db: Annotated[Optional[Session], Depends(get_db)],
    ) -> JSONResponse:
        _require_db(db)

        if not task_service.redis_ready():
            return respond_err(
                CODE_SERVICE_UNAVAILABLE,
                "Redis 未就绪：异步任务需 Redis 缓存与调度，请检查 REDIS_URL",
                http_status=503,
            )

        try:
            uid = task_service.assert_async_task_user(
                api_key=x_api_key.strip(),
                x_user_id=x_user_id.strip(),
            )
        except YddmCallError as e:
            return respond_yddm_error(e.api_code, e.message, http_status=e.http_status)

        try:
            outcome = task_service.restart_async_task(
                db,  # type: ignore[arg-type]
                task_id,
                user_id=uid,
                api_key=x_api_key.strip(),
            )
        except ApiHttpError as e:
            return respond_err(
                e.code,
                e.msg,
                e.data,
                http_status=e.http_status,
                headers=e.headers,
            )
        except RuntimeError as e:
            return respond_err(
                CODE_SERVICE_UNAVAILABLE,
                str(e) or get_message(CODE_SERVICE_UNAVAILABLE),
                http_status=503,
            )
        except YddmCallError as e:
            return respond_yddm_error(e.api_code, e.message, http_status=e.http_status)

        if outcome is None:
            return respond_err(CODE_NOT_FOUND, http_status=404)

        if outcome == "already_active":
            return respond_err(
                CODE_ASYNC_TASK_ALREADY_ACTIVE,
                get_message(CODE_ASYNC_TASK_ALREADY_ACTIVE),
                data={"task_id": task_id, "status": "pending"},
                http_status=409,
            )

        if outcome == "window_ended":
            return respond_err(
                CODE_ASYNC_TASK_WINDOW_ENDED,
                get_message(CODE_ASYNC_TASK_WINDOW_ENDED),
                data={"task_id": task_id},
                http_status=409,
            )

        if not isinstance(outcome, task_service.AsyncTaskRestartResult):
            return respond_err(CODE_NOT_FOUND, http_status=404)

        st = task_service.get_task_status(db, task_id)  # type: ignore[arg-type]
        if st is None:
            return respond_err(CODE_NOT_FOUND, http_status=404)

        return respond(
            ok_with_meta(
                {
                    "task_id": st.task_id,
                    "status": st.status,
                    "success_count": st.success_count,
                    "failed_count": st.failed_count,
                    "snapshot_source": outcome.snapshot_source,
                },
                async_task_meta(platform=st.platform, action=st.action),
            )
        )

    @r.get(
        "/tasks/{task_id}/results",
        dependencies=[
            ip_rate_limit(max_requests=60, window_seconds=60, scope=ASYNC_TASK_RESULTS)
        ],
    )
    def get_task_results(
        task_id: str,
        db: Annotated[Optional[Session], Depends(get_db)],
        page: Annotated[int, Query(ge=1)] = 1,
        limit: Annotated[Optional[int], Query(ge=1, le=200)] = None,
        is_upload: Annotated[int, Query(ge=0, le=1)] = 0,
        x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    ) -> JSONResponse:

        _require_db(db)

        st = task_service.get_task_status(db, task_id)  # type: ignore[arg-type]

        if st is None:
            return respond_err(CODE_NOT_FOUND, http_status=404)

        _require_matching_user(task_user_id=st.user_id, x_user_id=x_user_id)

        lim = limit if limit is not None else get_settings().async_results_default_limit

        lim = max(1, min(200, int(lim)))

        data, meta = result_service.paginate_result(
            db,  # type: ignore[arg-type]
            task_id,
            page=page,
            limit=lim,
            is_upload=is_upload,
        )

        return respond(ok_with_meta(data.model_dump(), meta))

    return r

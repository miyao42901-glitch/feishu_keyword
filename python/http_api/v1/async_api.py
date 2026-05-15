"""API v1：异步任务提交 / 状态 / 结果分页。"""
from __future__ import annotations

from typing import Annotated, Generator, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from config.settings import get_settings
from social_platform.actions.registry import get_action_spec
from social_platform.api_response import err, ok
from social_platform.api_status_codes import CODE_BAD_REQUEST, CODE_FAILED, get_message
from social_platform.schemas.async_submit import AsyncTaskSubmitRequest
from social_platform.services import result_service, task_service
from social_platform.services.yddm_user_client import YddmCallError


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
        raise HTTPException(status_code=403, detail="X-User-Id does not match task owner")


def build_async_router() -> APIRouter:
    r = APIRouter(prefix="/async", tags=["v1-async"])

    @r.post("/tasks")
    def submit_async_task(
        body: AsyncTaskSubmitRequest,
        x_api_key: Annotated[str, Header(alias="X-API-Key", min_length=1)],
        x_user_id: Annotated[str, Header(alias="X-User-Id", min_length=1)],
        db: Annotated[Optional[Session], Depends(get_db)],
        priority: Annotated[int, Query(ge=0, le=9)] = 0,
    ) -> JSONResponse:
        if db is None:
            return JSONResponse(
                err(CODE_FAILED, "异步任务未配置：请设置环境变量 DATABASE_URL"),
                status_code=503,
            )
        action = (body.action or "").strip()
        if get_action_spec(action) is None:
            return JSONResponse(
                {"code": 400, "message": "unsupported action"},
                status_code=400,
            )
        try:
            tid = task_service.submit_async_task(
                db,
                action=action,
                body=body.body if isinstance(body.body, dict) else {},
                user_id=x_user_id.strip(),
                api_key=x_api_key.strip(),
                priority=priority,
            )
        except ValidationError as ve:
            return JSONResponse(
                err(CODE_BAD_REQUEST, "validation failed", data={"errors": ve.errors()}),
                status_code=400,
            )
        except LookupError:
            return JSONResponse(
                {"code": 400, "message": "unsupported action"},
                status_code=400,
            )
        except ValueError as e:
            return JSONResponse(err(CODE_BAD_REQUEST, str(e) or get_message(CODE_BAD_REQUEST)))
        except RuntimeError as e:
            return JSONResponse(
                err(CODE_FAILED, str(e)),
                status_code=503,
            )
        except YddmCallError as e:
            return JSONResponse(
                err(e.api_code, e.message),
                status_code=e.http_status,
            )
        return JSONResponse(ok(data={"task_id": tid, "status": "pending"}))

    @r.get("/tasks/{task_id}")
    def get_task_status(
        task_id: str,
        db: Annotated[Optional[Session], Depends(get_db)],
        x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    ) -> JSONResponse:
        if db is None:
            return JSONResponse(
                err(CODE_FAILED, "异步任务未配置：请设置环境变量 DATABASE_URL"),
                status_code=503,
            )
        st = task_service.get_task_status(db, task_id)
        if st is None:
            raise HTTPException(status_code=404, detail="task not found")
        _require_matching_user(task_user_id=st.user_id, x_user_id=x_user_id)
        return JSONResponse(ok(data=st.model_dump()))

    @r.get("/tasks/{task_id}/results")
    def get_task_results(
        task_id: str,
        db: Annotated[Optional[Session], Depends(get_db)],
        page: Annotated[int, Query(ge=1)] = 1,
        limit: Annotated[Optional[int], Query(ge=1, le=200)] = None,
        is_upload: Annotated[Optional[int], Query(ge=0, le=1)] = None,
        x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    ) -> JSONResponse:
        if db is None:
            return JSONResponse(
                err(CODE_FAILED, "异步任务未配置：请设置环境变量 DATABASE_URL"),
                status_code=503,
            )
        st = task_service.get_task_status(db, task_id)
        if st is None:
            raise HTTPException(status_code=404, detail="task not found")
        _require_matching_user(task_user_id=st.user_id, x_user_id=x_user_id)
        lim = limit if limit is not None else get_settings().async_results_default_limit
        lim = max(1, min(200, int(lim)))
        data = result_service.paginate_result(
            db,
            task_id,
            page=page,
            limit=lim,
            is_upload=is_upload,
        )
        return JSONResponse(ok(data=data.model_dump()))

    return r

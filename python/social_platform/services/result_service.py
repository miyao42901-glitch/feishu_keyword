from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from social_platform.actions.registry import platform_for_result_listing
from social_platform.api_response import async_task_meta
from social_platform.models.async_task import AsyncTask
from social_platform.models.results.registry import get_result_model
from social_platform.schemas.async_task import AsyncTaskResultsResponse
from social_platform.services.result_store_service import paginate_task_results
from social_platform.utils.async_task_ids import parse_async_task_pk


def paginate_result(
    db: Session,
    task_id: str,
    page: int,
    limit: int,
    *,
    is_upload: Optional[int] = None,
) -> tuple[AsyncTaskResultsResponse, dict[str, Any]]:
    """
    从按平台拆分的结果表分页；无法解析平台时返回空列表。
    查询按任务所属 user_id 过滤。
    page 从 1 开始。
    """
    pk = parse_async_task_pk(task_id)
    if pk is None:
        return (
            AsyncTaskResultsResponse(page=page, limit=limit, total=0, items=[]),
            async_task_meta(platform="", action=""),
        )

    task = db.get(AsyncTask, pk)
    if task is None:
        return (
            AsyncTaskResultsResponse(page=page, limit=limit, total=0, items=[]),
            async_task_meta(platform="", action=""),
        )

    action = task.action or ""
    plat = (platform_for_result_listing(action) or "").strip().lower()
    meta = async_task_meta(platform=plat, action=action)
    if plat:
        try:
            get_result_model(plat)
        except ValueError:
            plat = ""

    if not plat:
        return AsyncTaskResultsResponse(page=page, limit=limit, total=0, items=[]), meta

    total, items = paginate_task_results(
        db,
        platform=plat,
        task_id=pk,
        page=page,
        limit=limit,
        user_id=task.user_id,
        is_upload=is_upload,
    )
    return (
        AsyncTaskResultsResponse(page=page, limit=limit, total=total, items=items),
        meta,
    )

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from config.settings import get_settings
from social_platform.actions.registry import (
    body_dict_for_db,
    platform_for_result_listing,
    validate_body_for_action,
)
from social_platform.api_status_codes import CODE_ASYNC_SUBMIT_QUOTA_EXCEEDED, get_message
from social_platform.models.async_task import AsyncTask
from social_platform.schemas.async_task import AsyncTaskStatusResponse
from social_platform.utils.async_task_ids import parse_async_task_pk
from social_platform.services.yddm_user_client import YddmCallError, assert_x_user_id_matches_yddm


def _iso(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    return dt.replace(microsecond=0).isoformat() + "Z"


def count_active_async_tasks(db: Session, user_id: str) -> int:
    uid = (user_id or "").strip()
    if not uid:
        return 0
    stmt = (
        select(func.count())
        .select_from(AsyncTask)
        .where(
            AsyncTask.user_id == uid,
            AsyncTask.status.in_(("pending", "running")),
        )
    )
    return int(db.scalar(stmt) or 0)


def submit_async_task(
    db: Session,
    *,
    action: str,
    body: dict[str, Any],
    user_id: str,
    api_key: str,
    priority: int = 0,
) -> int:
    """写入任务并入队 Celery；先校验 action/body，再校验 yddm 用户与单用户任务上限。"""
    settings = get_settings()
    validated = validate_body_for_action(action, body)
    body_for_db = body_dict_for_db(validated)

    uid = assert_x_user_id_matches_yddm(settings, api_key=api_key, x_user_id=user_id)

    max_active = max(1, int(settings.async_task_max_active_per_user))
    if count_active_async_tasks(db, uid) >= max_active:
        raise YddmCallError(
            api_code=CODE_ASYNC_SUBMIT_QUOTA_EXCEEDED,
            http_status=429,
            message=get_message(CODE_ASYNC_SUBMIT_QUOTA_EXCEEDED),
        )

    row = AsyncTask(
        user_id=uid[:64],
        status="pending",
        action=action.strip()[:128],
        body_json=body_for_db,
        priority=max(0, min(9, int(priority))),
    )
    db.add(row)
    db.flush()
    task_id = int(row.id)
    db.commit()

    from social_platform.tasks.worker_tasks import run_social_async_task

    celery_priority = row.priority
    async_result = run_social_async_task.apply_async(
        args=[task_id, (api_key or "").strip()],
        priority=celery_priority,
    )
    row2 = db.get(AsyncTask, task_id)
    if row2 is not None:
        row2.celery_task_id = async_result.id[:128] if async_result.id else None
        db.add(row2)
        db.commit()
    return task_id


def get_task_status(db: Session, task_id: str) -> Optional[AsyncTaskStatusResponse]:
    pk = parse_async_task_pk(task_id)
    if pk is None:
        return None
    row = db.get(AsyncTask, pk)
    if row is None:
        return None
    plat = platform_for_result_listing(row.action) or ""
    return AsyncTaskStatusResponse(
        task_id=int(row.id),
        user_id=row.user_id,
        platform=plat,
        status=row.status,
        action=row.action,
        error_message=row.error_message,
        celery_task_id=row.celery_task_id,
        priority=row.priority,
        cancel_requested=row.cancel_requested,
        success_count=int(row.success_count or 0),
        failed_count=int(row.failed_count or 0),
        create_time=_iso(row.create_time),
        update_time=_iso(row.update_time),
    )


def request_cancel(db: Session, task_id: str) -> bool:
    """标记取消并尝试 revoke（尽力而为）。"""
    pk = parse_async_task_pk(task_id)
    if pk is None:
        return False
    row = db.get(AsyncTask, pk)
    if row is None:
        return False
    row.cancel_requested = True
    row.update_time = datetime.utcnow()
    db.add(row)
    db.commit()
    if row.celery_task_id and row.status in ("pending", "running"):
        from social_platform.tasks.celery_app import celery_app

        celery_app.control.revoke(row.celery_task_id, terminate=False)
    return True


def database_configured() -> bool:
    return bool(get_settings().database_url.strip())

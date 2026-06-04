"""管理端：运营看板聚合（埋点数据）。"""

from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from admin.deps import get_db
from admin.schemas.response import admin_ok
from social_platform.services import analytics_service, task_service

router = APIRouter(prefix="/analytics", tags=["管理端-埋点看板"])


def _db_or_none(db: Session) -> Optional[Session]:
    if not task_service.database_configured():
        return None
    return db


@router.get("/overview")
def analytics_overview(
    range: Literal["day", "week", "month"] = Query(default="month"),
    db: Session = Depends(get_db),
):
    """数据概览 KPI + 图表 + 漏斗（Phase 1 基于已入库埋点聚合）。"""
    session = _db_or_none(db)
    if session is None:
        return admin_ok(data={"range": range, "kpis": {}, "charts": {}, "funnel": {}, "empty": True})
    data = analytics_service.get_overview(session, range)
    return admin_ok(data=data)


@router.get("/exec-runs")
def analytics_exec_runs(
    range: Literal["day", "week", "month"] = Query(default="day"),
    db: Session = Depends(get_db),
):
    """执行监控（Phase 2）。"""
    session = _db_or_none(db)
    if session is None:
        return admin_ok(data={"range": range, "total": 0, "success": 0, "successRate": "-", "avgDurationMs": 0, "records": []})
    data = analytics_service.get_exec_runs(session, range)
    return admin_ok(data=data)


@router.get("/api-calls")
def analytics_api_calls(
    range: Literal["day", "week", "month"] = Query(default="day"),
    db: Session = Depends(get_db),
):
    """API 监控（Phase 2）。"""
    session = _db_or_none(db)
    if session is None:
        return admin_ok(data={"range": range, "total": 0, "success": 0, "successRate": "-", "avgLatencyMs": 0, "platformStats": [], "records": []})
    data = analytics_service.get_api_calls(session, range)
    return admin_ok(data=data)


@router.get("/push-logs")
def analytics_push_logs(
    range: Literal["day", "week", "month"] = Query(default="day"),
    db: Session = Depends(get_db),
):
    """推送监控（Phase 3）。"""
    session = _db_or_none(db)
    if session is None:
        return admin_ok(data={"range": range, "total": 0, "sendSuccess": 0, "callbackSuccess": 0, "deliveryRate": "-", "notifyOnCount": 0, "notifyOffCount": 0, "records": []})
    data = analytics_service.get_push_logs(session, range)
    return admin_ok(data=data)


@router.get("/users")
def analytics_users(
    range: Literal["day", "week", "month"] = Query(default="month"),
    db: Session = Depends(get_db),
):
    """用户管理（Phase 3）。"""
    session = _db_or_none(db)
    if session is None:
        return admin_ok(data={"range": range, "totalUsers": 0, "activeUsers": 0, "newUsers": 0, "retention": "-", "records": []})
    data = analytics_service.get_users(session, range)
    return admin_ok(data=data)


@router.put("/users/{user_id}/remark")
def update_user_remark(
    user_id: str,
    body: dict,
    db: Session = Depends(get_db),
):
    """更新用户运营备注（Phase 3）。"""
    session = _db_or_none(db)
    if session is None:
        return admin_ok(data={"updated": False})
    remark = str(body.get("remark") or "")[:255]
    analytics_service.update_user_remark(session, user_id=user_id, remark=remark)
    return admin_ok(data={"updated": True})


@router.get("/users/{user_id}/detail")
def analytics_user_detail(
    user_id: str,
    db: Session = Depends(get_db),
):
    """用户详情（Phase 3）。"""
    session = _db_or_none(db)
    if session is None:
        return admin_ok(data=None)
    data = analytics_service.get_user_detail(session, user_id=user_id)
    return admin_ok(data=data)


@router.get("/tasks")
def analytics_tasks(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    keyword: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    created_start: Optional[str] = Query(default=None),
    created_end: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """任务管理（Phase 4）。"""
    session = _db_or_none(db)
    if session is None:
        return admin_ok(data={"total": 0, "page": page, "limit": limit, "records": [], "stats": {}})
    data = analytics_service.get_tasks(
        session,
        page=page,
        limit=limit,
        keyword=keyword,
        status=status,
        created_start=created_start,
        created_end=created_end,
    )
    return admin_ok(data=data)

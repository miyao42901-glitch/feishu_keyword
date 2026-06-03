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

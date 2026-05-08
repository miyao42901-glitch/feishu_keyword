"""
监控方案 CRUD 相关接口（当前仅列表）。
"""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import DEFAULT_LIST_LIMIT
from app.schemas import MonitoringPlanOut
from app.services.monitoring_plan_service import list_monitoring_plans as fetch_plans

router = APIRouter()


@router.get("/monitoring-plans", response_model=List[MonitoringPlanOut])
def list_monitoring_plans(
    skip: int = 0,
    limit: int = DEFAULT_LIST_LIMIT,
    db: Session = Depends(get_db),
) -> List[MonitoringPlanOut]:
    """
    分页返回监控方案列表。

    Args:
        skip: 偏移量，默认 0。
        limit: 每页条数，默认取配置 `DEFAULT_LIST_LIMIT`，且受全局上限约束。

    Returns:
        `MonitoringPlanOut` 数组，无数据时为空数组。
    """
    rows = fetch_plans(db, skip=skip, limit=limit)
    return rows

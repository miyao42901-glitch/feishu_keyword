"""
监控方案（monitoring_plans）相关的业务逻辑。
"""

from __future__ import annotations

from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import MAX_LIST_LIMIT
from app.models import MonitoringPlan


def list_monitoring_plans(db: Session, *, skip: int = 0, limit: int = 100) -> List[MonitoringPlan]:
    """
    分页查询监控方案列表。

    Args:
        db: 数据库会话。
        skip: 跳过的记录数（偏移量）。
        limit: 本页最大条数，超过上限时会被截断为 `MAX_LIST_LIMIT`。

    Returns:
        `MonitoringPlan` 实体列表（可能为空列表）。
    """
    safe_limit = min(limit, MAX_LIST_LIMIT)
    stmt = select(MonitoringPlan).offset(skip).limit(safe_limit)
    return list(db.scalars(stmt).all())

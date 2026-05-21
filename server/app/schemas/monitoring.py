"""
监控方案相关的 API 出参/入参模型（Pydantic）。

与 `MonitoringPlan` ORM 字段对齐，用于 OpenAPI 文档与响应校验。
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class MonitoringPlanOut(BaseModel):
    """返回给前端的单条监控方案结构（列表项或详情）。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    plan_name: Optional[str] = None
    status: Optional[str] = None
    effective_time: Optional[datetime] = None
    expire_time: Optional[datetime] = None
    keyword_logic: Optional[str] = None
    sync_word_expand: Optional[int] = None
    version: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

"""
监控方案 CRUD 相关接口（当前仅列表）。

响应统一为 `{ code, message, data }`。
"""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import DEFAULT_LIST_LIMIT
from app.schemas import MonitoringPlanOut
from app.schemas.api_response import ApiResponse
from app.services.monitoring_plan_service import list_monitoring_plans as fetch_plans

router = APIRouter()


@router.get("/monitoring-plans")
def list_monitoring_plans(
    skip: int = 0,
    limit: int = DEFAULT_LIST_LIMIT,
    db: Session = Depends(get_db),
) -> ApiResponse[List[MonitoringPlanOut]]:
    """
    分页查询监控方案列表（表 `monitoring_plans`）。

    路径：`GET /api/monitoring-plans`。

    Args:
        skip: 偏移量，默认 0。
        limit: 每页条数，默认 `DEFAULT_LIST_LIMIT`，服务端裁剪不超过 `MAX_LIST_LIMIT`。

    Returns:
        统一信封：`code=0` 时 `data` 为 `MonitoringPlanOut` 数组（可能为空数组）。

    Note:
        与 OpenAPI `/docs` 中本接口说明一致；响应外层见 `docs/API.md` 第五节。
    """
    rows = fetch_plans(db, skip=skip, limit=limit)
    items = [MonitoringPlanOut.model_validate(r) for r in rows]
    return ApiResponse.success(data=items, message="查询成功")

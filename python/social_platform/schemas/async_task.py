from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class AsyncTaskSubmitResponse(BaseModel):
    task_id: int
    status: str = "pending"


class AsyncTaskStatusResponse(BaseModel):
    task_id: int
    user_id: str = ""
    platform: str = Field(
        default="",
        description="由已注册 action 推导，仅用于查询响应；不入库、不由客户端提交",
    )
    status: str
    action: str
    error_message: Optional[str] = None
    celery_task_id: Optional[str] = None
    priority: int = 0
    cancel_requested: bool = False
    success_count: int = 0
    failed_count: int = 0
    task_start_time: Optional[str] = None
    task_end_time: Optional[str] = None
    interval_minutes: int = 60
    fetch_count: int = 100
    create_time: Optional[str] = None
    update_time: Optional[str] = None


class AsyncTaskResultsResponse(BaseModel):
    page: int
    limit: int
    total: int
    items: list[Any] = Field(default_factory=list)

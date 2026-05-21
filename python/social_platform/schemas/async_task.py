from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class AsyncTaskSubmitResponse(BaseModel):
    task_id: int
    status: str = "pending"


class AsyncTaskStatusResponse(BaseModel):
    task_id: int
    task_name: str = ""
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
    next_run_at: Optional[str] = None
    current_run_id: Optional[str] = None
    running_lease_until: Optional[str] = None
    interval_minutes: int = 60
    fetch_count: int = 100
    create_time: Optional[str] = None
    update_time: Optional[str] = None


class AsyncTaskResultsResponse(BaseModel):
    page: int
    limit: int
    total: int
    items: list[Any] = Field(default_factory=list)


class AsyncTaskListSummary(BaseModel):
    """当前用户任务汇总（按任务条数 + 采集计数累加）。"""

    total: int = 0
    pending: int = 0
    running: int = 0
    success: int = 0
    failed: int = 0
    cancelled: int = 0
    active: int = Field(
        default=0, description="pending + running 任务数"
    )
    total_success_count: int = Field(
        default=0, description="各任务 success_count 之和"
    )
    total_failed_count: int = Field(
        default=0, description="各任务 failed_count 之和"
    )


class AsyncTaskListResponse(BaseModel):
    page: int
    limit: int
    summary: AsyncTaskListSummary
    items: list[AsyncTaskStatusResponse] = Field(default_factory=list)


# 验收接口请求/响应为顶层键值对：douyin/xhs/mp/wxvideo → id 列表或更新行数，另含 total/accepted。

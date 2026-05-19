"""异步任务提交请求体（POST /api/v1/async/tasks）。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class AsyncTaskSubmitRequest(BaseModel):
    action: str = Field(
        ..., min_length=1, max_length=128, description="已注册的 kebab-case action"
    )
    body: dict[str, Any] = Field(
        default_factory=dict, description="业务参数，按 action 做 Pydantic 校验"
    )
    task_start_time: str = Field(
        ...,
        min_length=1,
        description="定时任务开始时间（ISO8601 或毫秒时间戳，必填）",
    )
    task_end_time: str = Field(
        ...,
        min_length=1,
        description="定时任务结束时间（ISO8601 或毫秒时间戳，必填）",
    )
    interval_minutes: int = Field(
        default=60,
        ge=5,
        description="定时采集频率（分钟），不传默认 60，最小 5",
    )
    fetch_count: int = Field(
        default=100,
        ge=1,
        le=500,
        description="单次采集条数上限，不传默认 100",
    )

    @field_validator("task_start_time", "task_end_time", mode="before")
    @classmethod
    def _require_non_blank_time(cls, value: Any) -> Any:
        if value is None:
            raise ValueError("task_start_time 与 task_end_time 为必填")
        if isinstance(value, str) and not value.strip():
            raise ValueError("task_start_time 与 task_end_time 为必填")
        return value

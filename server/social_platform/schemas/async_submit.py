"""异步任务提交请求体（POST /api/v1/async/tasks）。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class AsyncTaskSubmitRequest(BaseModel):
    task_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="任务名称（必填，1～100 字符）",
    )
    action: str = Field(
        ..., min_length=1, max_length=128, description="已注册的 kebab-case action"
    )
    body: dict[str, Any] = Field(
        default_factory=dict, description="业务参数，按 action 做 Pydantic 校验"
    )
    task_start_time: str = Field(
        ...,
        min_length=1,
        description=(
            "定时任务开始时间（必填）：\"YYYY-MM-DD HH:MM:SS\"，按 naive datetime 原样入库，"
            "亦支持 ISO8601 / 毫秒时间戳"
        ),
    )
    task_end_time: str = Field(
        ...,
        min_length=1,
        description=(
            "定时任务结束时间（必填）：\"YYYY-MM-DD HH:MM:SS\"，按 naive datetime 原样入库，"
            "亦支持 ISO8601 / 毫秒时间戳"
        ),
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

    @field_validator("task_name", mode="before")
    @classmethod
    def _normalize_task_name(cls, value: Any) -> Any:
        if value is None:
            raise ValueError("task_name 为必填")
        if not isinstance(value, str):
            return value
        stripped = value.strip()
        if not stripped or len(stripped) > 100:
            raise ValueError("task_name 长度须为 1～100 字符")
        return stripped

    @field_validator("task_start_time", "task_end_time", mode="before")
    @classmethod
    def _require_non_blank_time(cls, value: Any) -> Any:
        if value is None:
            raise ValueError("task_start_time 与 task_end_time 为必填")
        if isinstance(value, str) and not value.strip():
            raise ValueError("task_start_time 与 task_end_time 为必填")
        return value

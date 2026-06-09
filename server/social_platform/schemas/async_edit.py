"""异步任务编辑请求体。"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class AsyncTaskEditRequest(BaseModel):
    """部分更新异步任务；POST /api/v1/async/tasks/edit。"""

    task_id: int = Field(..., description="任务 ID（必填）")
    task_name: Optional[str] = Field(None, description="任务名称，1～100 字符")
    interval_minutes: Optional[int] = Field(None, ge=5, description="采集间隔（分钟）")
    fetch_count: Optional[int] = Field(None, ge=1, le=500, description="单次采集条数上限")
    task_start_time: Optional[str] = Field(
        None, min_length=1, description="定时窗口开始"
    )
    task_end_time: Optional[str] = Field(None, min_length=1, description="定时窗口结束")
    priority: Optional[int] = Field(None, ge=0, le=9, description="Celery 优先级 0～9")

    @field_validator("task_name", mode="before")
    @classmethod
    def _validate_task_name(cls, value: Any) -> Any:
        if value is None:
            return None
        if not isinstance(value, str):
            return value
        stripped = value.strip()
        if not stripped or len(stripped) > 100:
            raise ValueError("task_name 长度须为 1～100 字符")
        return stripped

    @model_validator(mode="after")
    def _at_least_one_update_field(self) -> AsyncTaskEditRequest:
        if any(
            getattr(self, name) is not None
            for name in (
                "task_name",
                "interval_minutes",
                "fetch_count",
                "task_start_time",
                "task_end_time",
                "priority",
            )
        ):
            return self
        raise ValueError("至少提供一个要修改的字段")

    def updates_dict(self) -> dict[str, Any]:
        """仅包含显式传入的更新字段。"""
        out: dict[str, Any] = {}
        for name in (
            "task_name",
            "interval_minutes",
            "fetch_count",
            "task_start_time",
            "task_end_time",
            "priority",
        ):
            val = getattr(self, name)
            if val is not None:
                out[name] = val
        return out

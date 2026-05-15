"""异步任务提交请求体（POST /api/v1/async/tasks）。"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AsyncTaskSubmitRequest(BaseModel):
    action: str = Field(..., min_length=1, max_length=128, description="已注册的 kebab-case action")
    body: dict[str, Any] = Field(default_factory=dict, description="业务参数，按 action 做 Pydantic 校验")

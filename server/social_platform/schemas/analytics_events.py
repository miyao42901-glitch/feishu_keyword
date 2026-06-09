"""埋点事件上报请求体。"""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

AnalyticsEventName = Literal[
    "page_view",
    "task_create",
    "notify_toggle",
    "user_profile",
]

ALLOWED_ANALYTICS_EVENTS: frozenset[str] = frozenset(
    {"page_view", "task_create", "notify_toggle", "user_profile"}
)


class AnalyticsEventItem(BaseModel):
    event: str = Field(..., min_length=1, max_length=64)
    user_id: Optional[str] = Field(default=None, max_length=64)
    ts: Optional[str] = Field(default=None, max_length=32)
    properties: dict[str, Any] = Field(default_factory=dict)


class AnalyticsEventsRequest(BaseModel):
    events: list[AnalyticsEventItem] = Field(..., min_length=1, max_length=50)

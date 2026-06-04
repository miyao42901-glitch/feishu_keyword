"""API 调用上下文：用于在 HTTP 请求层记录埋点（Phase 2）。"""

from __future__ import annotations

import contextvars
from typing import Any, Optional

from sqlalchemy.orm import Session

api_call_context: contextvars.ContextVar[Optional[dict[str, Any]]] = contextvars.ContextVar(
    "api_call_context", default=None
)


def set_api_call_context(
    *,
    db: Session,
    task_id: Optional[str] = None,
    exec_id: Optional[str] = None,
    platform: Optional[str] = None,
) -> Any:
    """设置 API 调用上下文，返回 token 用于清理。"""
    ctx = {
        "db": db,
        "task_id": task_id,
        "exec_id": exec_id,
        "platform": platform,
    }
    return api_call_context.set(ctx)


def clear_api_call_context(token: Any) -> None:
    """清理上下文。"""
    api_call_context.reset(token)


def get_api_call_context() -> Optional[dict[str, Any]]:
    """获取当前上下文。"""
    return api_call_context.get()

"""管理端 API 响应：code=200 表示成功（与 admin 前端 axios 拦截器一致）。"""

from __future__ import annotations

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")

ADMIN_CODE_SUCCESS = 200


class AdminApiResponse(BaseModel, Generic[T]):
    code: int = ADMIN_CODE_SUCCESS
    msg: str = "success"
    data: Optional[T] = None


def admin_ok(data: Any = None, msg: str = "success") -> dict[str, Any]:
    return {"code": ADMIN_CODE_SUCCESS, "msg": msg, "data": data}


def admin_fail(code: int, msg: str) -> dict[str, Any]:
    return {"code": code, "msg": msg, "data": None}

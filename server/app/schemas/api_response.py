"""
统一 API 响应：`code` + `message` + `data`。

- `code == 0` 表示业务成功，`data` 为载荷。
- `code != 0` 表示失败，`data` 一般为 `null`（校验错误时可将详情放入 `data`）。
"""

from __future__ import annotations

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class BizCode:
    """业务错误码（与 HTTP 状态分工：HTTP 表传输层，code 表业务语义）。"""

    SUCCESS = 0
    BAD_REQUEST = 40001
    UNAUTHORIZED = 40101
    FORBIDDEN = 40301
    NOT_FOUND = 40401
    CONFLICT = 40901
    DB_ERROR = 50301
    INTERNAL_ERROR = 50001


def http_status_to_biz_code(status_code: int) -> int:
    """将常见 HTTP 状态映射为业务码（用于异常处理统一输出）。"""
    mapping = {
        400: BizCode.BAD_REQUEST,
        401: BizCode.UNAUTHORIZED,
        403: BizCode.FORBIDDEN,
        404: BizCode.NOT_FOUND,
        409: BizCode.CONFLICT,
        422: BizCode.BAD_REQUEST,
        503: BizCode.DB_ERROR,
        500: BizCode.INTERNAL_ERROR,
    }
    return mapping.get(status_code, BizCode.INTERNAL_ERROR)


def default_message_for_code(code: int) -> str:
    """按业务码返回规范中文说明。"""
    table = {
        BizCode.SUCCESS: "成功",
        BizCode.BAD_REQUEST: "请求参数不正确",
        BizCode.UNAUTHORIZED: "未授权",
        BizCode.FORBIDDEN: "禁止访问",
        BizCode.NOT_FOUND: "资源不存在",
        BizCode.CONFLICT: "资源冲突",
        BizCode.DB_ERROR: "数据库不可用或服务异常",
        BizCode.INTERNAL_ERROR: "服务器内部错误",
    }
    return table.get(code, "请求处理失败")


class ApiResponse(BaseModel, Generic[T]):
    """统一响应体。"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    code: int = BizCode.SUCCESS
    message: str = "操作成功"
    data: Optional[T] = None

    @classmethod
    def success(cls, data: Optional[T] = None, message: str = "操作成功") -> ApiResponse[T]:
        return cls(code=BizCode.SUCCESS, message=message, data=data)

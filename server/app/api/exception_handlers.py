"""
将 Starlette/FastAPI 异常转换为统一 `{ code, message, data }` 响应。
"""

from __future__ import annotations

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.schemas.api_response import ApiResponse, BizCode, default_message_for_code, http_status_to_biz_code


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    biz = http_status_to_biz_code(exc.status_code)
    detail = exc.detail
    if isinstance(detail, str) and detail.strip():
        msg = detail
    elif isinstance(detail, list):
        msg = default_message_for_code(biz)
    else:
        msg = default_message_for_code(biz) if detail is None else str(detail)
    body = ApiResponse(code=biz, message=msg, data=None).model_dump(mode="json")
    return JSONResponse(status_code=exc.status_code, content=body)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    body = ApiResponse(
        code=BizCode.BAD_REQUEST,
        message="请求参数校验失败",
        data={"errors": exc.errors()},
    ).model_dump(mode="json")
    return JSONResponse(status_code=422, content=body)


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """未捕获异常：HTTP 500 + 统一错误体（不向客户端暴露堆栈）。"""
    import logging

    logging.getLogger(__name__).exception("未处理异常: %s", exc)
    body = ApiResponse(
        code=BizCode.INTERNAL_ERROR,
        message=default_message_for_code(BizCode.INTERNAL_ERROR),
        data=None,
    ).model_dump(mode="json")
    return JSONResponse(status_code=500, content=body)

"""管理端 HTTP 异常（与 `/api/v1` 的 ApiHttpError 分离）。"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AdminHttpError(Exception):
    def __init__(
        self,
        code: int,
        msg: str,
        *,
        data: Any = None,
        http_status: int = 200,
    ) -> None:
        self.code = int(code)
        self.msg = msg.strip() or "请求失败"
        self.data = data
        self.http_status = http_status


def register_admin_exception_handlers(app: FastAPI) -> None:
    from social_platform.debug_errors import enrich_error_payload

    @app.exception_handler(AdminHttpError)
    async def _admin_http_error(_request: Request, exc: AdminHttpError) -> JSONResponse:
        data = enrich_error_payload(
            exc.data,
            exc=exc,
            api_code=exc.code,
            namespace="admin",
        )
        return JSONResponse(
            status_code=exc.http_status,
            content={"code": exc.code, "msg": exc.msg, "data": data},
        )

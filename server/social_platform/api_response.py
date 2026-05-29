"""统一 HTTP 响应：{code, msg, data}。code=0 表示成功。"""

from __future__ import annotations

from typing import Any, Mapping

from fastapi.responses import JSONResponse

from social_platform.api_status_codes import (
    API_STATUS_MESSAGES,
    CODE_ASYNC_SUBMIT_DUPLICATE,
    CODE_ASYNC_SUBMIT_QUOTA_EXCEEDED,
    CODE_ASYNC_SUBMIT_USER_MISMATCH,
    CODE_ASYNC_TASK_ALREADY_CANCELLED,
    CODE_BAD_REQUEST,
    CODE_FAILED,
    CODE_INSUFFICIENT_BALANCE,
    CODE_INVALID_API_KEY,
    CODE_NOT_FOUND,
    CODE_RATE_LIMIT_EXCEEDED,
    CODE_REQUEST_LIMIT_EXCEEDED,
    CODE_SERVICE_UNAVAILABLE,
    CODE_SUCCESS,
    CODE_UNSUPPORTED_ACTION,
    CODE_YDDM_USERS_ME_FAILED,
    get_message,
    normalize_upstream_error_code,
)

CODE_OK = CODE_SUCCESS


class ApiHttpError(Exception):
    """在路由或依赖中抛出，由 ``http_service`` 注册的全局处理器转为统一 JSON。"""

    def __init__(
        self,
        code: int,
        msg: str | None = None,
        *,
        data: Any = None,
        http_status: int | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        self.code = int(code)
        self.msg = (
            msg if msg is not None else get_message(self.code)
        ).strip() or get_message(CODE_FAILED)
        self.data = data
        self.http_status = http_status
        self.headers = dict(headers or {})


def http_status_for_api_code(code: int) -> int:
    """业务码 → 建议 HTTP 状态码（成功体带非 0 code 时仍可用 200）。"""
    c = int(code)
    if c == CODE_SUCCESS:
        return 200
    if c == CODE_BAD_REQUEST:
        return 400
    if c in (CODE_INVALID_API_KEY, 1008, 1002):
        return 401
    if c in (CODE_ASYNC_SUBMIT_USER_MISMATCH, 1010):
        return 403
    if c == CODE_NOT_FOUND:
        return 404
    if c in (CODE_ASYNC_SUBMIT_DUPLICATE, CODE_ASYNC_TASK_ALREADY_CANCELLED):
        return 409
    if c in (
        CODE_REQUEST_LIMIT_EXCEEDED,
        CODE_ASYNC_SUBMIT_QUOTA_EXCEEDED,
        CODE_RATE_LIMIT_EXCEEDED,
    ):
        return 429
    if c in (CODE_SERVICE_UNAVAILABLE, CODE_YDDM_USERS_ME_FAILED, 5000, 5003):
        return 503
    if c == CODE_INSUFFICIENT_BALANCE:
        return 200
    if c == CODE_UNSUPPORTED_ACTION:
        return 400
    if 1000 <= c < 2000:
        return 400
    return 500


def ok(data: Any = None, msg: str = "ok") -> dict[str, Any]:
    return {"code": CODE_OK, "msg": msg, "data": data}


def ok_with_meta(result: Any, meta: dict[str, Any], msg: str = "ok") -> dict[str, Any]:
    """与同步 Worker 成功响应一致：`data.result` + `data.meta`。"""
    return ok(data={"result": result, "meta": meta}, msg=msg)


def err(code: int, msg: str, data: Any = None) -> dict[str, Any]:
    return {"code": int(code), "msg": msg, "data": data}


def respond(
    body: dict[str, Any],
    *,
    http_status: int | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    """将 ``ok`` / ``err`` 字典包装为 ``JSONResponse``。"""
    code = int(body.get("code", CODE_FAILED))
    status = http_status if http_status is not None else http_status_for_api_code(code)
    hdrs = dict(headers) if headers else None
    return JSONResponse(body, status_code=status, headers=hdrs)


def respond_ok(
    data: Any = None,
    msg: str = "ok",
    *,
    http_status: int | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    return respond(ok(data=data, msg=msg), http_status=http_status, headers=headers)


def respond_err(
    code: int,
    msg: str | None = None,
    data: Any = None,
    *,
    http_status: int | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    text = (msg if msg is not None else get_message(code)).strip() or get_message(
        CODE_FAILED
    )
    return respond(err(code, text, data=data), http_status=http_status, headers=headers)


def respond_yddm_error(
    api_code: int,
    message: str,
    *,
    http_status: int | None = None,
    data: Any = None,
) -> JSONResponse:
    return respond_err(api_code, message, data=data, http_status=http_status)


def async_task_meta(*, platform: str, action: str = "") -> dict[str, Any]:
    """异步 HTTP 接口 meta：标识数据来源平台与结果表。"""
    from social_platform.utils.worker_runtime import worker_meta

    plat = (platform or "").strip().lower()
    out: dict[str, Any] = {
        **worker_meta("async_api", "1.0.0"),
        "platform": plat,
        "source": plat,
    }
    act = (action or "").strip()
    if act:
        out["action"] = act
    if plat:
        out["result_table"] = f"feishu_{plat}_results"
    return out


def worker_run_insufficient_balance(result: Any) -> bool:
    """Worker 返回 {ok, data, ...} 且 data.insufficient_balance 或上游业务码 1001。"""
    if not isinstance(result, dict):
        return False
    data = result.get("data")
    if isinstance(data, dict) and data.get("insufficient_balance"):
        return True
    err = result.get("error")
    if isinstance(err, dict):
        try:
            if int(err.get("code", -1)) == CODE_INSUFFICIENT_BALANCE:
                return True
        except (TypeError, ValueError):
            pass
    return False


def from_worker_run(result: dict[str, Any]) -> dict[str, Any]:
    """
    将各 Worker run_task 内部结构 {ok, data, error, meta} 转为统一响应。
    余额不足：ok 为 false 且 data 内含 insufficient_balance 时 code=1001。
    """
    meta = result.get("meta")
    if result.get("ok"):
        inner = result.get("data")
        if meta is not None:
            return ok(data={"result": inner, "meta": meta})
        return ok(data={"result": inner})

    raw = result.get("data")
    if isinstance(raw, dict) and raw.get("insufficient_balance"):
        return err(
            CODE_INSUFFICIENT_BALANCE,
            get_message(CODE_INSUFFICIENT_BALANCE),
            data={"result": raw, "meta": meta},
        )

    e = result.get("error")
    if isinstance(e, dict):
        raw_code = int(e.get("code", CODE_FAILED))
        out_code = normalize_upstream_error_code(raw_code)
        upstream_msg = e.get("msg")
        um = str(upstream_msg).strip() if upstream_msg is not None else ""

        if out_code not in API_STATUS_MESSAGES:
            return err(
                CODE_FAILED,
                um or get_message(CODE_FAILED),
                data={"meta": meta} if meta is not None else None,
            )

        return err(
            out_code,
            get_message(out_code),
            data={"meta": meta} if meta is not None else None,
        )

    if isinstance(e, str):
        err_text = e.strip()
        if "unsupported action" in err_text or "不支持" in err_text:
            return err(
                CODE_UNSUPPORTED_ACTION,
                get_message(CODE_UNSUPPORTED_ACTION),
                data={"meta": meta} if meta is not None else None,
            )
        return err(
            CODE_BAD_REQUEST,
            (
                f"{get_message(CODE_BAD_REQUEST)}: {err_text}"
                if err_text
                else get_message(CODE_BAD_REQUEST)
            ),
            data={"meta": meta} if meta is not None else None,
        )

    return err(
        CODE_FAILED,
        get_message(CODE_FAILED),
        data={"meta": meta} if meta is not None else None,
    )


def normalize_body(body: Any) -> dict[str, Any]:
    """若上游已是统一格式则原样返回；若是旧版 {ok:...} 则转换。"""
    if isinstance(body, dict) and "code" in body and "msg" in body and "data" in body:
        return body
    if isinstance(body, dict) and "ok" in body:
        return from_worker_run(body)
    return err(CODE_BAD_REQUEST, get_message(CODE_BAD_REQUEST), data=body)


def _json_safe_value(value: Any) -> Any:
    """将校验错误详情转为可 ``json.dumps`` 的值（如 ``bytes`` → ``str``）。"""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, (list, tuple)):
        return [_json_safe_value(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _json_safe_value(v) for k, v in value.items()}
    return str(value)


def register_api_exception_handlers(app: Any) -> None:
    """在 FastAPI 应用上注册统一异常响应（``http_service`` 启动时调用）。"""
    from fastapi.exceptions import RequestValidationError

    @app.exception_handler(ApiHttpError)
    async def _api_http_error_handler(_request: Any, exc: ApiHttpError) -> JSONResponse:
        return respond_err(
            exc.code,
            exc.msg,
            exc.data,
            http_status=exc.http_status,
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error_handler(
        _request: Any, exc: RequestValidationError
    ) -> JSONResponse:
        return respond_err(
            CODE_BAD_REQUEST,
            get_message(CODE_BAD_REQUEST),
            data={"errors": _json_safe_value(exc.errors())},
            http_status=400,
        )

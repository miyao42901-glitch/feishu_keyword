"""统一 HTTP 响应：{code, msg, data}。code=0 表示成功。"""
from __future__ import annotations

from typing import Any

from social_platform.api_status_codes import (
    API_STATUS_MESSAGES,
    CODE_BAD_REQUEST,
    CODE_FAILED,
    CODE_INSUFFICIENT_BALANCE,
    CODE_SUCCESS,
    get_message,
    normalize_upstream_error_code,
)

CODE_OK = CODE_SUCCESS


def ok(data: Any = None, msg: str = "ok") -> dict[str, Any]:
    return {"code": CODE_OK, "msg": msg, "data": data}


def err(code: int, msg: str, data: Any = None) -> dict[str, Any]:
    return {"code": int(code), "msg": msg, "data": data}


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
            return err(CODE_FAILED, um or get_message(CODE_FAILED), data={"meta": meta} if meta is not None else None)

        return err(out_code, get_message(out_code), data={"meta": meta} if meta is not None else None)

    if isinstance(e, str):
        err_text = e.strip()
        if "unsupported action" in err_text or "不支持" in err_text:
            return err(1019, get_message(1019), data={"meta": meta} if meta is not None else None)
        return err(
            CODE_BAD_REQUEST,
            f"{get_message(CODE_BAD_REQUEST)}: {err_text}" if err_text else get_message(CODE_BAD_REQUEST),
            data={"meta": meta} if meta is not None else None,
        )

    return err(CODE_FAILED, get_message(CODE_FAILED), data={"meta": meta} if meta is not None else None)


def normalize_body(body: Any) -> dict[str, Any]:
    """若上游已是统一格式则原样返回；若是旧版 {ok:...} 则转换。"""
    if isinstance(body, dict) and "code" in body and "msg" in body and "data" in body:
        return body
    if isinstance(body, dict) and "ok" in body:
        return from_worker_run(body)
    return err(CODE_BAD_REQUEST, get_message(CODE_BAD_REQUEST), data=body)

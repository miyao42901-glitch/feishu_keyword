"""测试环境（ENVIRONMENT=test）下向 API 响应附加可观测的调试信息。"""

from __future__ import annotations

import traceback
from typing import Any

from config.settings import get_settings


def expose_debug_details() -> bool:
    return get_settings().is_test_environment()


def format_exception_debug(exc: BaseException, *, traceback_limit: int = 12) -> dict[str, Any]:
    tb_lines = traceback.format_exception(type(exc), exc, exc.__traceback__)
    tail = tb_lines[-traceback_limit:] if traceback_limit > 0 else tb_lines
    return {
        "type": type(exc).__name__,
        "detail": str(exc),
        "traceback": [line.rstrip("\n") for line in tail if line.strip()],
    }


def merge_debug_data(data: Any, debug: dict[str, Any]) -> Any:
    if not debug:
        return data
    if data is None:
        return {"debug": debug}
    if isinstance(data, dict):
        merged = dict(data)
        merged["debug"] = {**merged.get("debug", {}), **debug}
        return merged
    return {"value": data, "debug": debug}


def enrich_error_payload(
    data: Any,
    exc: BaseException | None = None,
    **extra: Any,
) -> Any:
    if not expose_debug_details():
        return data
    debug: dict[str, Any] = {"environment": get_settings().environment or "test"}
    if exc is not None:
        debug.update(format_exception_debug(exc))
    debug.update(extra)
    return merge_debug_data(data, debug)


def public_error_message(exc: BaseException, *, generic: str) -> str:
    if expose_debug_details():
        detail = str(exc).strip()
        return detail or generic
    return generic

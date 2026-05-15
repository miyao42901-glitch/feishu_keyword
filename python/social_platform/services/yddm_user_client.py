"""提交异步任务前：用 yddm「当前用户」接口校验 X-API-Key，并核对 X-User-Id。"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from config.settings import Settings
from social_platform.api_status_codes import (
    CODE_ASYNC_SUBMIT_USER_MISMATCH,
    CODE_YDDM_USERS_ME_FAILED,
    get_message,
)


class YddmCallError(Exception):
    """校验失败：使用 `api_code` / `http_status` 构造统一 HTTP 响应。"""

    def __init__(self, *, api_code: int, http_status: int, message: str) -> None:
        super().__init__(message)
        self.api_code = int(api_code)
        self.http_status = int(http_status)
        self.message = str(message)


def _parse_me_json(raw: str) -> dict[str, Any]:
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError as e:
        raise YddmCallError(
            api_code=CODE_YDDM_USERS_ME_FAILED,
            http_status=502,
            message=get_message(CODE_YDDM_USERS_ME_FAILED),
        ) from e
    if not isinstance(obj, dict):
        raise YddmCallError(
            api_code=CODE_YDDM_USERS_ME_FAILED,
            http_status=502,
            message=get_message(CODE_YDDM_USERS_ME_FAILED),
        )
    return obj


def fetch_yddm_me_user_id(settings: Settings, api_key: str) -> int:
    """
    GET users/me，请求头携带 `X-API-KEY`（与 yddm 文档一致）。
    成功时返回 `data.id`（整数）。
    """
    url = (settings.yddm_users_me_url or "").strip()
    if not url:
        raise RuntimeError("yddm_users_me_url (YDDM_USERS_ME_URL) is not configured")
    key = (api_key or "").strip()
    if not key:
        raise YddmCallError(api_code=1005, http_status=401, message=get_message(1005))

    req = urllib.request.Request(url, method="GET", headers={"X-API-KEY": key})
    timeout = float(settings.yddm_users_me_timeout_sec or 10.0)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        try:
            raw = e.read().decode("utf-8", errors="replace")
        except Exception:
            raw = ""
        msg = get_message(1005)
        if raw.strip().startswith("{"):
            try:
                obj = json.loads(raw)
                if isinstance(obj, dict) and str(obj.get("msg", "")).strip():
                    msg = str(obj.get("msg")).strip()
            except json.JSONDecodeError:
                pass
        raise YddmCallError(api_code=1005, http_status=401, message=msg) from e
    except TimeoutError as e:
        raise YddmCallError(
            api_code=CODE_YDDM_USERS_ME_FAILED,
            http_status=503,
            message=get_message(CODE_YDDM_USERS_ME_FAILED),
        ) from e
    except OSError as e:
        raise YddmCallError(
            api_code=CODE_YDDM_USERS_ME_FAILED,
            http_status=503,
            message=get_message(CODE_YDDM_USERS_ME_FAILED),
        ) from e

    body = _parse_me_json(raw)
    if int(body.get("code", -1)) != 0:
        msg = str(body.get("msg") or "").strip() or get_message(1005)
        raise YddmCallError(api_code=1005, http_status=401, message=msg)

    data = body.get("data")
    if not isinstance(data, dict):
        raise YddmCallError(
            api_code=CODE_YDDM_USERS_ME_FAILED,
            http_status=502,
            message=get_message(CODE_YDDM_USERS_ME_FAILED),
        )
    uid = data.get("id")
    if uid is None:
        raise YddmCallError(
            api_code=CODE_YDDM_USERS_ME_FAILED,
            http_status=502,
            message=get_message(CODE_YDDM_USERS_ME_FAILED),
        )
    try:
        return int(uid)
    except (TypeError, ValueError) as e:
        raise YddmCallError(
            api_code=CODE_YDDM_USERS_ME_FAILED,
            http_status=502,
            message=get_message(CODE_YDDM_USERS_ME_FAILED),
        ) from e


def assert_x_user_id_matches_yddm(settings: Settings, *, api_key: str, x_user_id: str) -> str:
    """
    校验 `X-User-Id` 与 `X-API-Key` 在 yddm 侧解析出的用户 id 一致。
    返回规范化的 `user_id` 字符串（与库中 `feishu_async_tasks.user_id` 一致）。
    """
    remote_id = fetch_yddm_me_user_id(settings, api_key)
    claimed = str((x_user_id or "").strip())
    if not claimed.isdigit():
        raise YddmCallError(
            api_code=CODE_ASYNC_SUBMIT_USER_MISMATCH,
            http_status=403,
            message=get_message(CODE_ASYNC_SUBMIT_USER_MISMATCH),
        )
    if int(claimed) != int(remote_id):
        raise YddmCallError(
            api_code=CODE_ASYNC_SUBMIT_USER_MISMATCH,
            http_status=403,
            message=get_message(CODE_ASYNC_SUBMIT_USER_MISMATCH),
        )
    return str(int(remote_id))

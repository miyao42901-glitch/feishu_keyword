"""
任务卡片展示状态：仅由服务端根据 `config` 与当前时间计算，与历史前端推导规则一致。

前端只展示 `display_status` / `stopped_kind`，不在浏览器侧重复业务判断。
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Optional, Tuple

from app.services.feishu_task_config_service import task_paused_from_config

_DISPLAY = frozenset({"running", "stopped", "completed", "failed", "pending_run"})
_STOPPED_KIND = frozenset({"before_effective", "paused_in_window", "neutral"})


def _parse_datetime_ms(raw: Any) -> Optional[int]:
    """将表单/接口中的日期时间字符串解析为毫秒时间戳（与前端 dayjs 可比）；失败返回 None。"""
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    normalized = s.replace("T", " ", 1)
    patterns = (
        ("%Y-%m-%d %H:%M:%S", 19),
        ("%Y-%m-%d %H:%M", 16),
        ("%Y-%m-%d", 10),
    )
    for fmt, take in patterns:
        if len(normalized) < take:
            continue
        chunk = normalized[:take]
        try:
            dt = datetime.strptime(chunk, fmt)
            return int(dt.timestamp() * 1000)
        except ValueError:
            continue
    return None


def _task_abnormal_from_config(cfg: dict[str, Any]) -> bool:
    for key in ("taskAbnormal", "task_abnormal"):
        if key not in cfg:
            continue
        v = cfg[key]
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            s = v.strip().lower()
            if s in ("true", "1", "yes", "on"):
                return True
        if isinstance(v, (int, float)) and v == 1:
            return True
    return False


def _is_failed(cfg: dict[str, Any]) -> bool:
    rs = cfg.get("runStatus")
    if isinstance(rs, str) and rs.strip().lower() == "failed":
        return True
    return _task_abnormal_from_config(cfg)


def _derive_list_status(
    eff_ms: Optional[int],
    exp_ms: Optional[int],
    task_paused: bool,
    is_failed: bool,
    now_ms: int,
) -> str:
    eff_ok = eff_ms is not None
    exp_ok = exp_ms is not None

    if eff_ok and exp_ok and eff_ms is not None and exp_ms is not None:
        if now_ms > exp_ms:
            return "completed"
        if is_failed:
            return "failed"
        if now_ms < eff_ms:
            return "pending_run"
        if task_paused:
            return "stopped"
        return "running"

    if eff_ok and eff_ms is not None and not exp_ok:
        if is_failed:
            return "failed"
        if now_ms < eff_ms:
            return "pending_run"
        if task_paused:
            return "stopped"
        return "running"

    if is_failed:
        return "failed"
    return "stopped"


def _derive_stopped_kind(display: str, eff_ms: Optional[int], now_ms: int) -> Optional[str]:
    if display != "stopped":
        return None
    if eff_ms is None:
        return "neutral"
    if now_ms < eff_ms:
        return "before_effective"
    return "paused_in_window"


def compute_card_status(
    cfg: dict[str, Any],
    *,
    now_ms: Optional[int] = None,
) -> Tuple[str, Optional[str]]:
    """
    返回 (`display_status`, `stopped_kind`)。
    `stopped_kind` 仅在 `display_status == stopped` 时有值，否则为 None。
    `pending_run` 表示未到 `effectiveAt`、尚未进入运行窗口（与窗口内暂停的 `stopped` 区分）。
    """
    if now_ms is None:
        now_ms = int(time.time() * 1000)

    task_type = cfg.get("taskType")
    is_realtime = task_type == "realtime"

    eff_ms = _parse_datetime_ms(cfg.get("effectiveAt"))
    exp_ms = _parse_datetime_ms(cfg.get("expireAt"))
    has_valid_window = eff_ms is not None and exp_ms is not None

    task_paused = task_paused_from_config(cfg)
    failed = _is_failed(cfg)

    if is_realtime and not has_valid_window:
        if failed:
            status = "failed"
        elif task_paused:
            status = "stopped"
        else:
            status = "running"
    else:
        status = _derive_list_status(eff_ms, exp_ms, task_paused, failed, now_ms)

    if status not in _DISPLAY:
        status = "stopped"

    sk = _derive_stopped_kind(status, eff_ms, now_ms)
    if sk is not None and sk not in _STOPPED_KIND:
        sk = "neutral"

    return status, sk

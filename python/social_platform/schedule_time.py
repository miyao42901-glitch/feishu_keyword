"""异步任务定时窗口：与 Celery ``timezone=Asia/Shanghai`` 对齐。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo

# 与 social_platform.tasks.celery_app 中 enable_utc + timezone 一致
SCHEDULE_TZ = ZoneInfo("Asia/Shanghai")


def schedule_now_utc_naive() -> datetime:
    """当前时刻（UTC naive），用于与库中统一后的窗口时间比较。"""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def normalize_schedule_datetime(dt: datetime) -> datetime:
    """
    将 API / DB 中的时刻规范为 UTC naive。
    无时区的 naive 按东八区（Asia/Shanghai）理解，避免与 ``utcnow`` 混比导致永不执行。
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=SCHEDULE_TZ)
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def normalize_schedule_optional(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    return normalize_schedule_datetime(dt)


def schedule_utc_iso(dt: datetime) -> str:
    """Redis 缓存：写入已为 UTC naive 的时刻（带 Z，读回不再按东八区偏移）。"""
    if dt.tzinfo is not None:
        u = dt.astimezone(timezone.utc).replace(tzinfo=None)
    else:
        u = dt.replace(tzinfo=None)
    return u.isoformat() + "Z"


def parse_schedule_utc_iso(value: str) -> Optional[datetime]:
    raw = (value or "").strip()
    if not raw:
        return None
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        return parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed

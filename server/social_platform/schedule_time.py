"""异步任务定时窗口：与 Celery ``timezone=Asia/Shanghai`` 对齐。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo

# 与 social_platform.tasks.celery_app 中 enable_utc + timezone 一致
SCHEDULE_TZ = ZoneInfo("Asia/Shanghai")


def schedule_now_utc_naive() -> datetime:
    """当前时刻（UTC naive）；仅用于与第三方 UTC 字段对齐，任务调度请用 ``schedule_now_wall_naive``。"""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def schedule_now_wall_naive() -> datetime:
    """当前时刻（naive datetime，与 MySQL DATETIME 一致，不做 UTC 偏移）。"""
    return datetime.now(SCHEDULE_TZ).replace(tzinfo=None)


def naive_dt(dt: datetime) -> datetime:
    """
    入库 / 比较用 naive datetime：
    - 无时区：原样写入（如 ``2026-05-19 10:00:00``）；
    - 有时区：先换成东八区墙钟再去掉 tzinfo（仅用于带 ``Z`` / ``+08:00`` 的 ISO 入参）。
    """
    if dt.tzinfo is None:
        return dt.replace(microsecond=0)
    return dt.astimezone(SCHEDULE_TZ).replace(tzinfo=None).replace(microsecond=0)


def normalize_schedule_datetime(dt: datetime) -> datetime:
    """兼容旧调用：与 ``naive_dt`` 相同，不再转 UTC。"""
    return naive_dt(dt)


def normalize_api_schedule_to_wall(dt: datetime) -> datetime:
    """兼容旧调用：与 ``naive_dt`` 相同。"""
    return naive_dt(dt)


def utc_naive_from_storage(dt: datetime) -> datetime:
    """读取 MySQL DATETIME：与 ``naive_dt`` 相同。"""
    return naive_dt(dt)


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


def schedule_wall_clock_str(dt: Optional[datetime]) -> Optional[str]:
    """HTTP / Redis：与 MySQL 相同的 ``YYYY-MM-DD HH:MM:SS`` 字符串。"""
    if dt is None:
        return None
    return naive_dt(dt).strftime("%Y-%m-%d %H:%M:%S")


def schedule_api_iso(dt: Optional[datetime]) -> Optional[str]:
    """HTTP API：与 ``schedule_wall_clock_str`` 相同格式（兼容旧调用名）。"""
    return schedule_wall_clock_str(dt)


def wall_clock_to_timestamp(dt: datetime) -> float:
    """Redis ZSET score：naive 墙钟按东八区解释后的 Unix 时间戳。"""
    return naive_dt(dt).replace(tzinfo=SCHEDULE_TZ).timestamp()


def parse_schedule_wall_clock(value: str) -> Optional[datetime]:
    """解析 Redis/API 时刻：``YYYY-MM-DD HH:MM:SS`` 或 ISO/Z。"""
    raw = (value or "").strip()
    if not raw:
        return None
    if raw.endswith("Z") or "T" in raw:
        return parse_schedule_utc_iso(raw)
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def parse_schedule_utc_iso(value: str) -> Optional[datetime]:
    """解析带 ``Z`` / 偏移的 ISO；结果经 ``naive_dt`` 落为墙钟 naive。"""
    raw = (value or "").strip()
    if not raw:
        return None
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    return naive_dt(parsed)

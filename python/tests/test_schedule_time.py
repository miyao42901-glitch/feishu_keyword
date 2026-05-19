"""定时窗口时区：naive 按 Asia/Shanghai 转 UTC。"""

from __future__ import annotations

import unittest
import unittest.mock
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from social_platform.schedule_time import (
    normalize_schedule_datetime,
    schedule_now_utc_naive,
    utc_naive_from_storage,
)
from social_platform.services import async_task_redis
from social_platform.services.async_task_redis import is_run_at_due


class TestScheduleTimezone(unittest.TestCase):
    def test_naive_start_interpreted_as_shanghai(self) -> None:
        """用户填 10:00（东八区）在 UTC 05:19 时应视为已到点。"""
        start_local = datetime(2026, 5, 19, 10, 0, 0)
        start_utc = normalize_schedule_datetime(start_local)
        self.assertEqual(start_utc.hour, 2)
        now_utc = datetime(2026, 5, 19, 5, 19, 0)
        self.assertTrue(is_run_at_due(start_utc, now=now_utc))

    def test_schedule_now_is_utc_naive(self) -> None:
        now = schedule_now_utc_naive()
        self.assertIsNone(now.tzinfo)
        utc = datetime.now(timezone.utc).replace(tzinfo=None)
        self.assertLess(abs((now - utc).total_seconds()), 5.0)

    def test_db_next_run_not_shifted_when_scheduling_zset(self) -> None:
        """schedule_next 写入的 UTC naive next_run_at 进 ZSET 时不应再按东八区偏移。"""
        next_run = datetime(2026, 5, 19, 12, 30, 0)
        with unittest.mock.patch(
            "social_platform.services.async_task_redis.get_redis"
        ) as mock_redis, unittest.mock.patch(
            "social_platform.services.async_task_redis.redis_configured",
            return_value=True,
        ):
            async_task_redis.schedule_async_task_run(99, next_run)
        score = mock_redis.return_value.zadd.call_args[0][1]["99"]
        self.assertEqual(score, utc_naive_from_storage(next_run).timestamp())
        shifted = normalize_schedule_datetime(next_run).timestamp()
        self.assertNotEqual(score, shifted)


if __name__ == "__main__":
    unittest.main()

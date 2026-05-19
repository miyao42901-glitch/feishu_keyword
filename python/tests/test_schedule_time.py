"""定时窗口时区：naive 按 Asia/Shanghai 转 UTC。"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from social_platform.schedule_time import (
    normalize_schedule_datetime,
    schedule_now_utc_naive,
)
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


if __name__ == "__main__":
    unittest.main()

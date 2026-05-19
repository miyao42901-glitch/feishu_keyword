"""异步任务 Redis 调度：next_run_at / interval_seconds 单元测试。"""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from social_platform.services import async_task_redis
from social_platform.services.task_service import (
    interval_minutes_to_seconds,
    next_run_after_completion,
    normalize_interval_minutes,
)


def _fake_row(
    *,
    task_id: int = 1,
    interval_minutes: int = 10,
    status: str = "pending",
    start: datetime | None = None,
    end: datetime | None = None,
    update_time: datetime | None = None,
) -> SimpleNamespace:
    now = datetime(2026, 5, 19, 10, 0, 0)
    return SimpleNamespace(
        id=task_id,
        user_id="u1",
        status=status,
        action="mp-search-all",
        body_json={},
        error_message=None,
        celery_task_id=None,
        priority=0,
        cancel_requested=False,
        success_count=0,
        failed_count=0,
        task_start_time=start or now,
        task_end_time=end or (now + timedelta(hours=24)),
        interval_minutes=interval_minutes,
        fetch_count=100,
        update_time=update_time or now,
    )


class TestIntervalSeconds(unittest.TestCase):
    def test_minutes_to_seconds(self) -> None:
        self.assertEqual(interval_minutes_to_seconds(5), 300)
        self.assertEqual(interval_minutes_to_seconds(60), 3600)
        self.assertEqual(interval_minutes_to_seconds(3), 300)  # min 5 min


class TestRowToCache(unittest.TestCase):
    def test_cache_includes_next_run_and_interval_seconds(self) -> None:
        from social_platform.schedule_time import schedule_utc_iso

        row = _fake_row(interval_minutes=15)
        nxt = datetime(2026, 5, 19, 10, 15, 0)
        payload = async_task_redis._row_to_cache(row, next_run_at=nxt)
        self.assertEqual(payload["interval_minutes"], 15)
        self.assertEqual(payload["interval_seconds"], 900)
        self.assertEqual(payload["next_run_at"], schedule_utc_iso(nxt))

    def test_running_clears_next_run(self) -> None:
        row = _fake_row(status="running")
        payload = async_task_redis._row_to_cache(
            row,
            next_run_at=datetime(2026, 5, 19, 11, 0, 0),
            previous={"next_run_at": "2026-05-19T11:00:00"},
        )
        self.assertNotIn("next_run_at", payload)


class TestResolveNextRunAt(unittest.TestCase):
    def test_uses_cached_next_run_when_future(self) -> None:
        from social_platform.schedule_time import schedule_utc_iso

        row = _fake_row()
        now = datetime(2026, 5, 19, 2, 5, 0)
        nxt = datetime(2026, 5, 19, 2, 20, 0)
        cached = {"next_run_at": schedule_utc_iso(nxt)}
        resolved = async_task_redis.resolve_next_run_at(row, cached=cached, now=now)
        self.assertEqual(resolved, nxt)

    def test_is_run_at_due(self) -> None:
        now = datetime(2026, 5, 19, 2, 0, 0)
        self.assertTrue(
            async_task_redis.is_run_at_due(datetime(2026, 5, 19, 1, 59, 0), now=now)
        )
        self.assertFalse(
            async_task_redis.is_run_at_due(datetime(2026, 5, 19, 2, 1, 0), now=now)
        )


class TestNextRunAfterCompletion(unittest.TestCase):
    def test_next_run_uses_minute_interval(self) -> None:
        row = _fake_row(interval_minutes=10)
        done = datetime(2026, 5, 19, 10, 0, 0)
        nxt = next_run_after_completion(row, done)
        self.assertEqual(nxt, done + timedelta(minutes=10))

    def test_interval_seconds_matches_minutes(self) -> None:
        minutes = normalize_interval_minutes(10)
        self.assertEqual(minutes * 60, interval_minutes_to_seconds(minutes))


class TestAsyncDispatchTick(unittest.TestCase):
    @patch(
        "social_platform.services.async_task_redis.recover_stale_pending_tasks",
        return_value=1,
    )
    @patch(
        "social_platform.services.async_task_redis.recover_stale_running_tasks",
        return_value=0,
    )
    @patch(
        "social_platform.services.async_task_redis.dispatch_due_async_tasks",
        return_value=2,
    )
    def test_run_tick(
        self,
        _dispatch: MagicMock,
        _running: MagicMock,
        _pending: MagicMock,
    ) -> None:
        from social_platform.services.async_dispatch_tick import run_async_dispatch_tick

        r = run_async_dispatch_tick()
        self.assertEqual(r.dispatched, 2)
        self.assertEqual(r.recovered_pending, 1)


class TestRecoverStaleRunning(unittest.TestCase):
    @patch("social_platform.services.async_task_redis.dispatch_task_by_id")
    @patch("social_platform.services.async_task_redis.update_async_task_cache")
    @patch("social_platform.services.async_task_redis.schedule_async_task_run")
    @patch("social_platform.services.async_task_redis.get_cached_async_task")
    @patch("social_platform.services.async_task_redis.get_cached_api_key")
    @patch("social_platform.services.async_task_redis.redis_configured", return_value=True)
    @patch("social_platform.services.async_task_redis.get_redis")
    @patch("social_platform.database.session.session_scope")
    @patch("config.settings.get_settings")
    def test_resets_stale_running(
        self,
        mock_settings: MagicMock,
        mock_scope: MagicMock,
        mock_get_redis: MagicMock,
        _redis_ok: MagicMock,
        mock_api_key: MagicMock,
        mock_cached: MagicMock,
        mock_schedule: MagicMock,
        mock_update: MagicMock,
        mock_dispatch: MagicMock,
    ) -> None:
        mock_settings.return_value = SimpleNamespace(async_task_running_stale_seconds=600)
        now = datetime.utcnow()
        row = _fake_row(
            status="running",
            start=now - timedelta(hours=2),
            update_time=now - timedelta(hours=2),
        )

        db = MagicMock()
        db.scalars.return_value = [row]
        mock_scope.return_value.__enter__.return_value = db
        mock_api_key.return_value = "key-1"
        mock_cached.return_value = {}
        mock_get_redis.return_value.delete = MagicMock()
        mock_dispatch.return_value = "celery-id"

        n = async_task_redis.recover_stale_running_tasks()

        self.assertEqual(n, 1)
        self.assertEqual(row.status, "pending")
        mock_schedule.assert_called_once()


class TestRecoverStalePending(unittest.TestCase):
    @patch("social_platform.services.async_task_redis.dispatch_task_by_id")
    @patch("social_platform.services.async_task_redis.update_async_task_cache")
    @patch("social_platform.services.async_task_redis.schedule_async_task_run")
    @patch("social_platform.services.async_task_redis.get_cached_async_task")
    @patch("social_platform.services.async_task_redis.get_cached_api_key")
    @patch("social_platform.services.async_task_redis.redis_configured", return_value=True)
    @patch("social_platform.database.session.session_scope")
    def test_skips_dispatch_when_next_run_in_future(
        self,
        mock_scope: MagicMock,
        _redis_ok: MagicMock,
        mock_api_key: MagicMock,
        mock_cached: MagicMock,
        mock_schedule: MagicMock,
        mock_update: MagicMock,
        mock_dispatch: MagicMock,
    ) -> None:
        now = datetime(2026, 5, 19, 5, 0, 0)
        row = _fake_row(
            start=datetime(2026, 5, 19, 4, 0, 0),
            end=datetime(2026, 5, 20, 5, 0, 0),
        )
        future = now + timedelta(minutes=30)

        db = MagicMock()
        db.scalars.return_value = [row]
        mock_scope.return_value.__enter__.return_value = db

        mock_api_key.return_value = "key-1"
        from social_platform.schedule_time import schedule_utc_iso

        mock_cached.return_value = {
            "next_run_at": schedule_utc_iso(future),
            "interval_seconds": 600,
        }

        with patch(
            "social_platform.services.async_task_redis.schedule_now_utc_naive",
            return_value=now,
        ):
            n = async_task_redis.recover_stale_pending_tasks()

        self.assertEqual(n, 0)
        mock_schedule.assert_called_once()
        mock_dispatch.assert_not_called()

    @patch("social_platform.services.async_task_redis.dispatch_task_by_id")
    @patch("social_platform.services.async_task_redis.update_async_task_cache")
    @patch("social_platform.services.async_task_redis.schedule_async_task_run")
    @patch("social_platform.services.async_task_redis.get_cached_async_task")
    @patch("social_platform.services.async_task_redis.get_cached_api_key")
    @patch("social_platform.services.async_task_redis.redis_configured", return_value=True)
    @patch("social_platform.database.session.session_scope")
    def test_skips_dispatch_when_celery_task_id_recent(
        self,
        mock_scope: MagicMock,
        _redis_ok: MagicMock,
        mock_api_key: MagicMock,
        mock_cached: MagicMock,
        mock_schedule: MagicMock,
        mock_update: MagicMock,
        mock_dispatch: MagicMock,
    ) -> None:
        now = datetime(2026, 5, 19, 5, 0, 0)
        row = _fake_row(
            status="pending",
            start=datetime(2026, 5, 19, 4, 0, 0),
            end=datetime(2026, 5, 20, 5, 0, 0),
            update_time=now,
        )
        row.celery_task_id = "already-queued"

        db = MagicMock()
        db.scalars.return_value = [row]
        mock_scope.return_value.__enter__.return_value = db
        mock_api_key.return_value = "key-1"
        mock_cached.return_value = {}

        with patch(
            "social_platform.services.async_task_redis.schedule_now_utc_naive",
            return_value=now,
        ), patch(
            "social_platform.services.async_task_redis._pending_already_queued",
            return_value=True,
        ):
            n = async_task_redis.recover_stale_pending_tasks()

        self.assertEqual(n, 0)
        mock_dispatch.assert_not_called()


class TestEnqueueAsyncTaskExecution(unittest.TestCase):
    @patch("social_platform.services.async_task_redis.dispatch_task_by_id")
    @patch("social_platform.services.async_task_redis.unschedule_async_task")
    @patch("social_platform.services.async_task_redis.apply_celery_run_at")
    @patch("social_platform.services.async_task_redis.schedule_async_task_run")
    @patch("social_platform.services.async_task_redis.cache_async_task")
    @patch("social_platform.services.async_task_redis.schedule_now_utc_naive")
    def test_due_now_only_celery_no_zset(
        self,
        mock_now: MagicMock,
        _cache: MagicMock,
        mock_schedule: MagicMock,
        mock_apply: MagicMock,
        mock_unschedule: MagicMock,
        mock_dispatch: MagicMock,
    ) -> None:
        now = datetime(2026, 5, 19, 10, 0, 0)
        mock_now.return_value = now
        row = _fake_row(start=now, end=now + timedelta(hours=1))
        mock_apply.return_value = "celery-1"

        cid = async_task_redis.enqueue_async_task_execution(
            row, api_key="key-1", run_at=now
        )

        self.assertEqual(cid, "celery-1")
        mock_schedule.assert_not_called()
        mock_unschedule.assert_called_once_with(int(row.id))
        mock_dispatch.assert_not_called()

    @patch("social_platform.services.async_task_redis.apply_celery_run_at")
    @patch("social_platform.services.async_task_redis.schedule_async_task_run")
    @patch("social_platform.services.async_task_redis.cache_async_task")
    def test_future_run_only_zset(
        self,
        _cache: MagicMock,
        mock_schedule: MagicMock,
        mock_apply: MagicMock,
    ) -> None:
        # schedule_now 为 UTC naive；normalize_schedule_datetime 将 naive 按东八区理解
        now = datetime(2026, 5, 19, 10, 0, 0)
        row = _fake_row(start=now, end=now + timedelta(hours=24))
        future = now + timedelta(hours=10)

        with patch(
            "social_platform.services.async_task_redis.schedule_now_utc_naive",
            return_value=now,
        ):
            async_task_redis.enqueue_async_task_execution(
                row, api_key="key-1", run_at=future
            )

        mock_schedule.assert_called_once()
        mock_apply.assert_not_called()


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from social_platform.services import async_task_redis


def _row(
    *,
    task_id: int = 1,
    status: str = "pending",
    cancel_requested: bool = False,
    start: datetime | None = None,
    end: datetime | None = None,
    next_run_at: datetime | None = None,
) -> SimpleNamespace:
    now = datetime(2026, 5, 19, 8, 0, 0)
    return SimpleNamespace(
        id=task_id,
        status=status,
        cancel_requested=cancel_requested,
        task_start_time=start or (now - timedelta(hours=12)),
        task_end_time=end or (now + timedelta(hours=24)),
        next_run_at=next_run_at,
        priority=0,
        celery_task_id=None,
        update_time=now,
    )


class TestRestoreSchedule(unittest.TestCase):
    @patch("social_platform.services.async_task_redis.update_async_task_cache")
    @patch("social_platform.services.async_task_redis.resolve_next_run_at")
    @patch("social_platform.services.async_task_redis.get_cached_async_task")
    @patch("social_platform.services.async_task_redis.resolve_api_key_for_task")
    @patch("social_platform.database.session.session_scope")
    @patch("social_platform.services.async_task_redis.get_redis")
    @patch("social_platform.services.async_task_redis.redis_configured", return_value=True)
    @patch("config.settings.get_settings")
    def test_restore_pending_task(
        self,
        mock_settings: MagicMock,
        _redis_ok: MagicMock,
        mock_get_redis: MagicMock,
        mock_scope: MagicMock,
        mock_api_key: MagicMock,
        mock_cached: MagicMock,
        mock_next: MagicMock,
        mock_update_cache: MagicMock,
    ) -> None:
        now = datetime(2026, 5, 19, 8, 0, 0)
        nxt = now + timedelta(minutes=5)
        row = _row(status="pending", next_run_at=nxt)
        db = MagicMock()
        db.scalars.return_value = [row]
        mock_scope.return_value.__enter__.return_value = db
        mock_api_key.return_value = "k"
        mock_cached.return_value = {}
        mock_next.return_value = nxt
        mock_settings.return_value = SimpleNamespace(async_restore_dispatch_due_on_startup=False)
        r = MagicMock()
        r.set.return_value = True
        r.zscore.return_value = None
        mock_get_redis.return_value = r

        with patch(
            "social_platform.services.async_task_redis.schedule_now_utc_naive",
            return_value=now,
        ):
            stats = async_task_redis.restore_schedule_tasks_from_mysql()

        self.assertEqual(stats["restored"], 1)
        self.assertEqual(stats["dispatch_due_count"], 0)
        r.zadd.assert_called_once()
        mock_update_cache.assert_called_once()

    @patch("social_platform.services.async_task_redis._log_cleanup_schedule_member")
    @patch("social_platform.services.async_task_redis.resolve_next_run_at")
    @patch("social_platform.services.async_task_redis.get_cached_async_task")
    @patch("social_platform.services.async_task_redis.resolve_api_key_for_task")
    @patch("social_platform.database.session.session_scope")
    @patch("social_platform.services.async_task_redis.get_redis")
    @patch("social_platform.services.async_task_redis.redis_configured", return_value=True)
    @patch("config.settings.get_settings")
    def test_restore_skips_cancelled(
        self,
        mock_settings: MagicMock,
        _redis_ok: MagicMock,
        mock_get_redis: MagicMock,
        mock_scope: MagicMock,
        mock_api_key: MagicMock,
        _cached: MagicMock,
        _next: MagicMock,
        mock_cleanup: MagicMock,
    ) -> None:
        now = datetime(2026, 5, 19, 8, 0, 0)
        row = _row(status="cancelled", cancel_requested=True)
        db = MagicMock()
        db.scalars.return_value = [row]
        mock_scope.return_value.__enter__.return_value = db
        mock_settings.return_value = SimpleNamespace(async_restore_dispatch_due_on_startup=False)
        r = MagicMock()
        r.set.return_value = True
        mock_get_redis.return_value = r

        with patch(
            "social_platform.services.async_task_redis.schedule_now_utc_naive",
            return_value=now,
        ):
            stats = async_task_redis.restore_schedule_tasks_from_mysql()

        self.assertEqual(stats["restored"], 0)
        mock_api_key.assert_not_called()
        mock_cleanup.assert_called_once()

    @patch("social_platform.services.async_task_redis.dispatch_task_by_id", return_value="cid")
    @patch("social_platform.services.async_task_redis.update_async_task_cache")
    @patch("social_platform.services.async_task_redis.resolve_next_run_at")
    @patch("social_platform.services.async_task_redis.get_cached_async_task")
    @patch("social_platform.services.async_task_redis.resolve_api_key_for_task")
    @patch("social_platform.database.session.session_scope")
    @patch("social_platform.services.async_task_redis.get_redis")
    @patch("social_platform.services.async_task_redis.redis_configured", return_value=True)
    @patch("config.settings.get_settings")
    def test_restore_due_task_dispatch_immediately(
        self,
        mock_settings: MagicMock,
        _redis_ok: MagicMock,
        mock_get_redis: MagicMock,
        mock_scope: MagicMock,
        mock_api_key: MagicMock,
        _cached: MagicMock,
        mock_next: MagicMock,
        _update_cache: MagicMock,
        _dispatch: MagicMock,
    ) -> None:
        now = datetime(2026, 5, 19, 8, 0, 0)
        due = now - timedelta(seconds=1)
        row = _row(status="pending", next_run_at=due)
        db = MagicMock()
        db.scalars.return_value = [row]
        mock_scope.return_value.__enter__.return_value = db
        mock_api_key.return_value = "k"
        mock_next.return_value = due
        mock_settings.return_value = SimpleNamespace(async_restore_dispatch_due_on_startup=True)
        r = MagicMock()
        r.set.return_value = True
        r.zscore.return_value = None
        mock_get_redis.return_value = r

        with patch(
            "social_platform.services.async_task_redis.schedule_now_utc_naive",
            return_value=now,
        ):
            stats = async_task_redis.restore_schedule_tasks_from_mysql()

        self.assertEqual(stats["dispatch_due_count"], 1)


class TestDispatchLockAndCleanup(unittest.TestCase):
    @patch("social_platform.services.async_task_redis.apply_celery_run_at", return_value="cid")
    @patch("social_platform.services.async_task_redis.resolve_next_run_at")
    @patch("social_platform.services.async_task_redis.get_cached_async_task", return_value={})
    @patch("social_platform.services.async_task_redis.resolve_api_key_for_task", return_value="k")
    @patch("social_platform.database.session.session_scope")
    @patch("social_platform.services.async_task_redis.get_redis")
    @patch("social_platform.services.async_task_redis.redis_configured", return_value=True)
    @patch("config.settings.get_settings")
    def test_stale_dispatch_lock_cleanup(
        self,
        mock_settings: MagicMock,
        _redis_ok: MagicMock,
        mock_get_redis: MagicMock,
        mock_scope: MagicMock,
        _api_key: MagicMock,
        _cached: MagicMock,
        mock_next: MagicMock,
        _apply: MagicMock,
    ) -> None:
        now = datetime(2026, 5, 19, 8, 0, 0)
        row = _row(status="pending", next_run_at=now)
        db = MagicMock()
        db.get.return_value = row
        mock_scope.return_value.__enter__.return_value = db
        mock_next.return_value = now
        mock_settings.return_value = SimpleNamespace(async_dispatch_lock_ttl_seconds=600)
        r = MagicMock()
        r.set.side_effect = [False, True]
        r.ttl.return_value = 0
        mock_get_redis.return_value = r

        with patch(
            "social_platform.services.async_task_redis.schedule_now_utc_naive",
            return_value=now,
        ):
            cid = async_task_redis.dispatch_task_by_id(1)

        self.assertEqual(cid, "cid")
        self.assertGreaterEqual(r.delete.call_count, 2)

    @patch("social_platform.services.async_task_redis._log_cleanup_schedule_member")
    @patch("social_platform.services.async_task_redis.dispatch_task_by_id", return_value=None)
    @patch("social_platform.database.session.session_scope")
    @patch("social_platform.services.async_task_redis.get_redis")
    @patch("social_platform.services.async_task_redis.redis_configured", return_value=True)
    def test_dispatch_due_cleans_expired_member(
        self,
        _redis_ok: MagicMock,
        mock_get_redis: MagicMock,
        mock_scope: MagicMock,
        _dispatch: MagicMock,
        mock_cleanup: MagicMock,
    ) -> None:
        now = datetime(2026, 5, 19, 8, 0, 0)
        row = _row(status="success")
        db = MagicMock()
        db.get.return_value = row
        mock_scope.return_value.__enter__.return_value = db
        r = MagicMock()
        r.zrangebyscore.return_value = [b"1"]
        r.zrem.return_value = 1
        mock_get_redis.return_value = r

        with patch(
            "social_platform.services.async_task_redis.schedule_now_utc_naive",
            return_value=now,
        ):
            n = async_task_redis.dispatch_due_async_tasks()

        self.assertEqual(n, 0)
        mock_cleanup.assert_called_once()

    @patch("config.settings.get_settings")
    def test_ttl_cap(self, mock_settings: MagicMock) -> None:
        now = datetime(2026, 5, 19, 8, 0, 0)
        end = now + timedelta(days=365)
        mock_settings.return_value = SimpleNamespace(async_task_redis_max_ttl_seconds=100)
        with patch(
            "social_platform.services.async_task_redis.schedule_now_utc_naive",
            return_value=now,
        ):
            ttl = async_task_redis._ttl_seconds(end)
        self.assertEqual(ttl, 100)


class TestDualDispatchWarning(unittest.TestCase):
    @patch("social_platform.services.async_dispatch_loop.logger")
    @patch("social_platform.services.async_dispatch_loop.get_settings")
    def test_dual_dispatch_warning(self, mock_settings: MagicMock, mock_logger: MagicMock) -> None:
        from social_platform.services.async_dispatch_loop import start_async_dispatch_loop

        mock_settings.return_value = SimpleNamespace(
            async_dispatch_http_enabled=True,
            async_schedule_beat_enabled=True,
            database_url="",
            async_dispatch_poll_seconds=15.0,
        )
        start_async_dispatch_loop()
        mock_logger.warning.assert_called()


if __name__ == "__main__":
    unittest.main()

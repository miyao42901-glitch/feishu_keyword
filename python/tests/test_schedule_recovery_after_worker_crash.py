from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from social_platform.services import async_task_redis
from social_platform.tasks import task_executor


def _row(
    *,
    status: str = "pending",
    now: datetime | None = None,
    next_run_at: datetime | None = None,
    running_lease_until: datetime | None = None,
    celery_task_id: str | None = None,
) -> SimpleNamespace:
    t = now or datetime.now(timezone.utc)
    return SimpleNamespace(
        id=1,
        user_id="u1",
        action="mp-search-all",
        body_json={"keyword": "k"},
        api_key="k",
        status=status,
        cancel_requested=False,
        error_message=None,
        celery_task_id=celery_task_id,
        priority=0,
        success_count=0,
        failed_count=0,
        task_start_time=t - timedelta(minutes=10),
        task_end_time=t + timedelta(hours=2),
        next_run_at=next_run_at,
        current_run_id=None,
        running_lease_until=running_lease_until,
        interval_minutes=10,
        fetch_count=10,
        update_time=t,
        create_time=t,
    )


class TestScheduleRecoveryAfterCrash(unittest.TestCase):
    @patch("social_platform.tasks.task_executor.task_service.schedule_next_async_run")
    @patch("social_platform.tasks.task_executor.execute_public_action")
    @patch("social_platform.tasks.task_executor.async_task_redis.update_async_task_cache")
    @patch("social_platform.tasks.task_executor.task_service.utc_now_naive")
    def test_worker_start_clears_next_run_at_while_running(
        self,
        mock_now: MagicMock,
        mock_cache: MagicMock,
        mock_execute: MagicMock,
        mock_schedule_next: MagicMock,
    ) -> None:
        now = datetime(2026, 5, 19, 7, 0, 0)
        row = _row(
            now=now.replace(tzinfo=timezone.utc),
            status="pending",
            next_run_at=now,
        )
        db = MagicMock()
        db.get.side_effect = lambda _m, _i: row
        mock_now.return_value = now
        mock_execute.side_effect = RuntimeError("boom")
        mock_schedule_next.return_value = True

        task_executor.execute_async_social_task(db, 1, "k")

        self.assertIsNone(row.next_run_at)
        self.assertEqual(row.status, "running")
        self.assertIsNotNone(row.current_run_id)
        self.assertIsNotNone(row.running_lease_until)
        mock_cache.assert_called()
        self.assertTrue(mock_cache.call_args.kwargs.get("clear_next_run"))

    @patch("social_platform.services.async_task_redis.dispatch_task_by_id", return_value=None)
    @patch("social_platform.services.async_task_redis.resolve_api_key_for_task", return_value="k")
    @patch("social_platform.database.session.session_scope")
    @patch("social_platform.services.async_task_redis.get_redis")
    @patch("social_platform.services.async_task_redis.redis_configured", return_value=True)
    @patch("config.settings.get_settings")
    def test_restore_rebuilds_schedule_from_mysql_next_run_at(
        self,
        mock_settings: MagicMock,
        _redis_ok: MagicMock,
        mock_get_redis: MagicMock,
        mock_scope: MagicMock,
        _api: MagicMock,
        _dispatch: MagicMock,
    ) -> None:
        now = datetime(2026, 5, 19, 8, 0, 0)
        row = _row(
            now=now.replace(tzinfo=timezone.utc),
            status="pending",
            next_run_at=datetime(2026, 5, 19, 8, 30, 0),
        )
        db = MagicMock()
        db.scalars.return_value = [row]
        mock_scope.return_value.__enter__.return_value = db
        mock_settings.return_value = SimpleNamespace(
            async_restore_dispatch_due_on_startup=False,
            async_task_redis_max_ttl_seconds=604800,
        )
        r = MagicMock()
        r.set.return_value = True
        r.zscore.return_value = 0.0
        r.get.return_value = None
        mock_get_redis.return_value = r

        with patch(
            "social_platform.services.async_task_redis.schedule_now_utc_naive",
            return_value=now,
        ):
            async_task_redis.restore_schedule_tasks_from_mysql()

        member = str(int(row.id))
        expected = row.next_run_at.timestamp()
        r.zadd.assert_any_call(async_task_redis.SCHEDULE_ZSET, {member: expected})

    @patch("social_platform.services.async_task_redis.apply_celery_run_at")
    @patch("social_platform.database.session.session_scope")
    @patch("social_platform.services.async_task_redis.get_redis")
    @patch("social_platform.services.async_task_redis.redis_configured", return_value=True)
    def test_dispatch_overlap_skips_when_running_lease_active(
        self,
        _redis_ok: MagicMock,
        mock_get_redis: MagicMock,
        mock_scope: MagicMock,
        mock_apply: MagicMock,
    ) -> None:
        now = datetime(2026, 5, 19, 8, 0, 0)
        row = _row(
            status="running",
            now=now.replace(tzinfo=timezone.utc),
            next_run_at=now,
            running_lease_until=now + timedelta(minutes=30),
            celery_task_id="cid-existing",
        )
        db = MagicMock()
        db.get.return_value = row
        mock_scope.return_value.__enter__.return_value = db
        r = MagicMock()
        r.set.return_value = True
        mock_get_redis.return_value = r

        with patch(
            "social_platform.services.async_task_redis.schedule_now_utc_naive",
            return_value=now,
        ):
            cid = async_task_redis.dispatch_task_by_id(1)

        self.assertIsNone(cid)
        mock_apply.assert_not_called()

    @patch("social_platform.services.async_task_redis.update_async_task_cache")
    @patch("social_platform.services.async_task_redis.cache_async_task")
    @patch("social_platform.services.async_task_redis.schedule_async_task_run")
    @patch("social_platform.services.async_task_redis.dispatch_task_by_id")
    @patch("social_platform.services.async_task_redis.resolve_api_key_for_task", return_value="k")
    @patch("social_platform.database.session.session_scope")
    @patch("social_platform.services.async_task_redis.get_redis")
    @patch("social_platform.services.async_task_redis.redis_configured", return_value=True)
    def test_running_lease_timeout_recover_reschedules(
        self,
        _redis_ok: MagicMock,
        mock_get_redis: MagicMock,
        mock_scope: MagicMock,
        _api: MagicMock,
        _dispatch: MagicMock,
        _schedule: MagicMock,
        _cache: MagicMock,
        _update: MagicMock,
    ) -> None:
        now = datetime(2026, 5, 19, 8, 0, 0)
        row = _row(
            status="running",
            now=now.replace(tzinfo=timezone.utc),
            next_run_at=None,
            running_lease_until=now - timedelta(seconds=1),
            celery_task_id="cid-old",
        )
        db = MagicMock()
        db.scalars.return_value = [row]
        mock_scope.return_value.__enter__.return_value = db
        r = MagicMock()
        mock_get_redis.return_value = r

        with patch(
            "social_platform.services.async_task_redis.schedule_now_utc_naive",
            return_value=now,
        ):
            reset = async_task_redis.recover_stale_running_tasks()

        self.assertEqual(reset, 1)
        self.assertEqual(row.status, "pending")
        self.assertIsNotNone(row.next_run_at)
        self.assertIsNone(row.running_lease_until)
        self.assertIsNone(row.current_run_id)


if __name__ == "__main__":
    unittest.main()

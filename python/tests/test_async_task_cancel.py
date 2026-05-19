"""异步任务取消 / 重启：Redis 保留与 MySQL 状态。"""

from __future__ import annotations

import json
import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from social_platform.services import async_task_redis


class TestDeleteAsyncTaskRedis(unittest.TestCase):
    @patch("social_platform.services.async_task_redis.get_redis")
    @patch("social_platform.services.async_task_redis.redis_configured", return_value=True)
    def test_deletes_keys_and_zset(self, _cfg: MagicMock, mock_redis: MagicMock) -> None:
        r = MagicMock()
        mock_redis.return_value = r
        async_task_redis.delete_async_task_redis(42)
        r.zrem.assert_called_once_with(
            async_task_redis.SCHEDULE_ZSET,
            "42",
        )
        r.delete.assert_called_once()
        keys = r.delete.call_args[0]
        self.assertEqual(len(keys), 3)


class TestRetainAsyncTaskRedisOnCancel(unittest.TestCase):
    @patch("social_platform.services.async_task_redis.get_cached_api_key", return_value="key-1")
    @patch("social_platform.services.async_task_redis.get_cached_async_task", return_value={})
    @patch("social_platform.services.async_task_redis.get_redis")
    @patch("social_platform.services.async_task_redis.redis_configured", return_value=True)
    def test_retains_snapshot_with_one_day_ttl(
        self,
        _cfg: MagicMock,
        mock_redis: MagicMock,
        _cached: MagicMock,
        _api: MagicMock,
    ) -> None:
        r = MagicMock()
        mock_redis.return_value = r
        now = datetime.utcnow()
        row = SimpleNamespace(
            id=7,
            user_id="100",
            status="cancelled",
            action="wxvideo-search-all",
            body_json={"keyword": "k"},
            error_message=None,
            celery_task_id=None,
            priority=0,
            cancel_requested=True,
            success_count=12,
            failed_count=3,
            task_start_time=now,
            task_end_time=now + timedelta(days=1),
            interval_minutes=60,
            fetch_count=100,
        )
        async_task_redis.retain_async_task_redis_on_cancel(row)
        r.zrem.assert_called_once()
        r.delete.assert_called_once()
        self.assertEqual(r.delete.call_args[0][0], async_task_redis._dispatch_lock_key(7))
        task_set = r.setex.call_args_list[0]
        self.assertEqual(task_set[0][0], async_task_redis._task_key(7))
        self.assertEqual(task_set[0][1], async_task_redis.CANCELLED_TASK_CACHE_TTL_SECONDS)
        payload = json.loads(task_set[0][2])
        self.assertEqual(payload["success_count"], 12)
        api_set = r.setex.call_args_list[1]
        self.assertEqual(api_set[0][0], async_task_redis._api_key_key(7))
        self.assertEqual(api_set[0][1], async_task_redis.CANCELLED_TASK_CACHE_TTL_SECONDS)


class TestCancelAsyncTask(unittest.TestCase):
    @patch("social_platform.services.async_task_redis.retain_async_task_redis_on_cancel")
    @patch("social_platform.tasks.celery_app.celery_app")
    def test_sets_cancelled_and_retains_redis(
        self,
        mock_celery: MagicMock,
        mock_retain: MagicMock,
    ) -> None:
        from social_platform.services import task_service

        now = datetime.utcnow()
        row = SimpleNamespace(
            id=7,
            user_id="100",
            status="pending",
            celery_task_id="celery-1",
            cancel_requested=False,
        )
        db = MagicMock()
        db.get.return_value = row

        outcome = task_service.cancel_async_task(db, "7", user_id="100")

        self.assertEqual(outcome, "cancelled")
        self.assertTrue(row.cancel_requested)
        self.assertEqual(row.status, "cancelled")
        db.add.assert_called_once_with(row)
        db.commit.assert_called_once()
        mock_retain.assert_called_once_with(row)
        mock_celery.control.revoke.assert_called_once_with("celery-1", terminate=False)

    @patch("social_platform.services.async_task_redis.retain_async_task_redis_on_cancel")
    def test_already_cancelled_returns_without_side_effects(
        self, mock_retain: MagicMock
    ) -> None:
        from social_platform.services import task_service

        row = SimpleNamespace(
            id=8,
            user_id="100",
            status="cancelled",
            celery_task_id=None,
            cancel_requested=True,
        )
        db = MagicMock()
        db.get.return_value = row

        outcome = task_service.cancel_async_task(db, "8", user_id="100")

        self.assertEqual(outcome, "already_cancelled")
        mock_retain.assert_not_called()
        db.commit.assert_not_called()


class TestLoadRestartSnapshot(unittest.TestCase):
    def test_prefers_redis_cache(self) -> None:
        now = datetime.utcnow()
        row = SimpleNamespace(
            id=1,
            success_count=1,
            failed_count=2,
            action="mp-search-all",
            body_json={"keyword": "db"},
            interval_minutes=60,
            fetch_count=50,
            priority=0,
            task_start_time=now,
            task_end_time=now + timedelta(hours=1),
        )
        cached = {
            "success_count": 99,
            "failed_count": 8,
            "action": "wxvideo-search-all",
            "body_json": {"keyword": "redis"},
            "interval_minutes": 30,
            "fetch_count": 100,
        }
        with patch.object(
            async_task_redis, "get_cached_async_task", return_value=cached
        ):
            snap = async_task_redis.load_async_task_restart_snapshot(1, row)
        self.assertEqual(snap["source"], "redis")
        self.assertEqual(snap["success_count"], 99)
        self.assertEqual(snap["body_json"]["keyword"], "redis")

    def test_falls_back_to_mysql(self) -> None:
        now = datetime.utcnow()
        row = SimpleNamespace(
            id=2,
            success_count=5,
            failed_count=1,
            action="xhs-search-all",
            body_json={"keyword": "mysql"},
            interval_minutes=60,
            fetch_count=80,
            priority=1,
            task_start_time=now,
            task_end_time=now + timedelta(hours=1),
        )
        with patch.object(async_task_redis, "get_cached_async_task", return_value=None):
            snap = async_task_redis.load_async_task_restart_snapshot(2, row)
        self.assertEqual(snap["source"], "mysql")
        self.assertEqual(snap["success_count"], 5)


class TestRestartAsyncTask(unittest.TestCase):
    @patch("social_platform.services.task_service.enqueue_async_task_run")
    @patch("social_platform.services.task_service.count_active_async_tasks", return_value=0)
    @patch("social_platform.services.task_service.redis_ready", return_value=True)
    @patch("social_platform.services.async_task_redis.load_async_task_restart_snapshot")
    def test_restarts_cancelled_task(
        self,
        mock_snap: MagicMock,
        _redis: MagicMock,
        _count: MagicMock,
        mock_enqueue: MagicMock,
    ) -> None:
        from social_platform.services import task_service

        now = datetime.utcnow()
        row = SimpleNamespace(
            id=9,
            user_id="100",
            status="cancelled",
            cancel_requested=True,
            celery_task_id=None,
            error_message="err",
            success_count=0,
            failed_count=0,
            task_start_time=now - timedelta(hours=1),
            task_end_time=now + timedelta(hours=24),
            interval_minutes=60,
            fetch_count=100,
            priority=0,
            action="wxvideo-search-all",
            body_json={},
            update_time=now,
        )
        db = MagicMock()
        db.get.side_effect = [row, row]
        mock_snap.return_value = {
            "success_count": 40,
            "failed_count": 2,
            "source": "redis",
        }

        outcome = task_service.restart_async_task(
            db, "9", user_id="100", api_key="key-1"
        )

        self.assertIsInstance(outcome, task_service.AsyncTaskRestartResult)
        self.assertEqual(outcome.snapshot_source, "redis")
        self.assertEqual(row.success_count, 40)
        self.assertEqual(row.failed_count, 2)
        self.assertFalse(row.cancel_requested)
        self.assertEqual(row.status, "pending")
        self.assertIsNone(row.celery_task_id)
        self.assertIsNone(row.error_message)
        mock_enqueue.assert_called_once()

    @patch("social_platform.services.task_service.redis_ready", return_value=True)
    def test_already_active(self, _redis: MagicMock) -> None:
        from social_platform.services import task_service

        row = SimpleNamespace(
            id=10,
            user_id="100",
            status="running",
            task_end_time=datetime.utcnow() + timedelta(hours=1),
        )
        db = MagicMock()
        db.get.return_value = row

        outcome = task_service.restart_async_task(
            db, "10", user_id="100", api_key="key-1"
        )
        self.assertEqual(outcome, "already_active")


if __name__ == "__main__":
    unittest.main()

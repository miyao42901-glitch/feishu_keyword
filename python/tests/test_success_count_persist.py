from __future__ import annotations

import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from social_platform.services import task_service
from social_platform.services.result_store_service import save_search_results
from social_platform.services.search_persist import (
    apply_search_persist_stats_to_async_task,
)


def _task_row(
    *,
    action: str = "xhs-search-all",
    success_count: int = 0,
    failed_count: int = 0,
    fetch_count: int = 10,
) -> SimpleNamespace:
    now = datetime.utcnow()
    return SimpleNamespace(
        id=1,
        user_id="u1",
        action=action,
        body_json={},
        success_count=success_count,
        failed_count=failed_count,
        fetch_count=fetch_count,
        cancel_requested=False,
        status="running",
        update_time=now,
        create_time=now,
        task_end_time=now + timedelta(hours=1),
        interval_minutes=10,
        api_key="k",
    )


class _FakeDb:
    def __init__(self, task: SimpleNamespace) -> None:
        self.task = task
        self.added = 0
        self.commits = 0

    def get(self, _model_or_id: object, _task_id: int) -> SimpleNamespace:
        return self.task

    def add(self, _obj: object) -> None:
        self.added += 1

    def commit(self) -> None:
        self.commits += 1


class TestPersistCountRules(unittest.TestCase):
    def test_inserted_accumulates_success_count(self) -> None:
        task = _task_row(success_count=1, failed_count=0)
        db = _FakeDb(task)
        apply_search_persist_stats_to_async_task(
            db,
            1,
            {
                "inserted_count": 3,
                "duplicated_count": 1,
                "failed_count": 2,
                "skipped_count": 0,
            },
        )
        self.assertEqual(task.success_count, 4)
        self.assertEqual(task.failed_count, 3)

    def test_duplicate_does_not_accumulate_success_count(self) -> None:
        task = _task_row(success_count=5, failed_count=0)
        db = _FakeDb(task)
        apply_search_persist_stats_to_async_task(
            db,
            1,
            {
                "inserted_count": 0,
                "duplicated_count": 7,
                "failed_count": 0,
                "skipped_count": 0,
            },
        )
        self.assertEqual(task.success_count, 5)
        self.assertEqual(task.failed_count, 7)

    def test_inserted_zero_keeps_success_count_unchanged(self) -> None:
        task = _task_row(success_count=2, failed_count=1)
        db = _FakeDb(task)
        apply_search_persist_stats_to_async_task(
            db,
            1,
            {
                "inserted_count": 0,
                "duplicated_count": 0,
                "failed_count": 1,
                "skipped_count": 1,
            },
        )
        self.assertEqual(task.success_count, 2)
        self.assertEqual(task.failed_count, 3)

    @patch("social_platform.services.result_store_service._normalize_rows")
    @patch("social_platform.services.result_store_service.get_settings")
    def test_bulk_insert_returns_unified_structure(
        self,
        mock_settings: MagicMock,
        mock_normalize: MagicMock,
    ) -> None:
        mock_settings.return_value = SimpleNamespace(database_url="mysql://x")
        mock_model = SimpleNamespace(post_id="post_id")
        mock_normalize.return_value = (mock_model, [], 0)
        out = save_search_results("xhs", "kw", [], user_id="u1", task_id=1)
        self.assertIn("inserted_count", out)
        self.assertIn("duplicated_count", out)
        self.assertIn("failed_count", out)
        self.assertIn("row_results", out)

    def test_xhs_success_count_increases_by_inserted(self) -> None:
        task = _task_row(action="xhs-search-all", success_count=0, failed_count=0)
        db = _FakeDb(task)
        apply_search_persist_stats_to_async_task(
            db,
            1,
            {
                "inserted_count": 4,
                "duplicated_count": 2,
                "failed_count": 0,
                "skipped_count": 0,
            },
        )
        self.assertEqual(task.success_count, 4)


class TestScheduleNextWithUnifiedSuccessCount(unittest.TestCase):
    def test_body_for_worker_uses_per_run_fetch_count(self) -> None:
        task = _task_row(success_count=35, fetch_count=10)
        body = task_service.body_for_worker_execution(task)
        self.assertEqual(body["fetch_count"], 10)

    @patch("social_platform.services.task_service.async_task_redis.enqueue_async_task_execution")
    @patch("social_platform.services.task_service.async_task_redis.get_cached_api_key", return_value="k")
    @patch(
        "social_platform.services.task_service.next_run_after_completion",
        return_value=datetime.utcnow() + timedelta(minutes=10),
    )
    def test_fetch_count_reached_still_schedules_next_run(
        self,
        _next: MagicMock,
        _cached: MagicMock,
        mock_enqueue: MagicMock,
    ) -> None:
        task = _task_row(success_count=10, fetch_count=10)
        db = _FakeDb(task)
        ok = task_service.schedule_next_async_run(
            db,
            1,
            "k",
            completed_at=datetime.utcnow(),
            last_ok=True,
        )
        self.assertTrue(ok)
        self.assertEqual(task.status, "pending")
        mock_enqueue.assert_called_once()

    @patch("social_platform.services.task_service.async_task_redis.enqueue_async_task_execution")
    @patch("social_platform.services.task_service.async_task_redis.get_cached_api_key", return_value="k")
    @patch(
        "social_platform.services.task_service.next_run_after_completion",
        return_value=datetime.utcnow() + timedelta(minutes=10),
    )
    def test_success_count_accumulates_but_schedule_continues(
        self,
        _next: MagicMock,
        _cached: MagicMock,
        mock_enqueue: MagicMock,
    ) -> None:
        task = _task_row(success_count=35, fetch_count=10)
        db = _FakeDb(task)
        ok = task_service.schedule_next_async_run(
            db,
            1,
            "k",
            completed_at=datetime.utcnow(),
            last_ok=True,
        )
        self.assertTrue(ok)
        self.assertEqual(task.status, "pending")
        mock_enqueue.assert_called_once()

    def test_window_end_marks_success(self) -> None:
        task = _task_row(success_count=10, fetch_count=10)
        db = _FakeDb(task)
        done = datetime.utcnow() + timedelta(hours=2)
        ok = task_service.schedule_next_async_run(
            db,
            1,
            "k",
            completed_at=done,
            last_ok=True,
        )
        self.assertFalse(ok)
        self.assertEqual(task.status, "success")

    def test_cancel_requested_marks_cancelled(self) -> None:
        task = _task_row(success_count=10, fetch_count=10)
        task.cancel_requested = True
        db = _FakeDb(task)
        ok = task_service.schedule_next_async_run(db, 1, "k")
        self.assertFalse(ok)
        self.assertEqual(task.status, "cancelled")


if __name__ == "__main__":
    unittest.main()

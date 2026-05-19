from __future__ import annotations

import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from social_platform.services import async_task_redis, task_service
from social_platform.utils import search_fetch_all as sfa


def _settings() -> SimpleNamespace:
    return SimpleNamespace(
        async_search_all_max_pages=500,
        async_search_all_max_run_seconds=3600.0,
        async_search_duplicate_page_threshold=5,
        async_search_guards_async_only=False,
    )


def _offset_body(_params: dict[str, object]) -> dict[str, object]:
    return {"offset": "0", "cookies_buffer": "", "currentPage": 1}


def _task_row(
    *,
    now: datetime,
    success_count: int = 0,
    fetch_count: int = 10,
    status: str = "running",
    task_end_time: datetime | None = None,
) -> SimpleNamespace:
    end = task_end_time or (now + timedelta(hours=1))
    return SimpleNamespace(
        id=1,
        user_id="u1",
        status=status,
        action="mp-search-all",
        body_json={"keyword": "k"},
        api_key="k",
        error_message=None,
        celery_task_id=None,
        priority=0,
        cancel_requested=False,
        success_count=success_count,
        failed_count=0,
        task_start_time=now - timedelta(minutes=10),
        task_end_time=end,
        next_run_at=None,
        interval_minutes=10,
        fetch_count=fetch_count,
        update_time=now,
        create_time=now,
    )


class _FakeDb:
    def __init__(self, task: SimpleNamespace) -> None:
        self.task = task
        self.commits = 0

    def get(self, _model: object, _task_id: int) -> SimpleNamespace:
        return self.task

    def add(self, _obj: object) -> None:
        return None

    def commit(self) -> None:
        self.commits += 1


class TestFetchCountPerSchedule(unittest.TestCase):
    @patch.object(sfa, "_guards_apply", return_value=True)
    @patch("config.settings.get_settings")
    def test_single_run_stops_at_fetch_count_even_if_has_more(
        self, mock_settings: MagicMock, _guards: MagicMock
    ) -> None:
        mock_settings.return_value = _settings()
        calls = {"n": 0}

        def api_call(_url: str, _key: str, _body: dict[str, object]) -> dict[str, object]:
            calls["n"] += 1
            n = calls["n"]
            data = [{"post_id": f"p{n}-{i}"} for i in range(5)]
            return {
                "data": data,
                "next_offset": str(n),
                "cookies_buffer": f"ck-{n}",
                "has_more": True,
            }

        out = sfa.fetch_offset_cookies_search_all(
            "http://test",
            "k",
            {"keyword": "k"},
            body_builder=_offset_body,
            api_call=api_call,
            fetch_count_cap=10,
            after_each_page=lambda chunk: len(chunk),
            log_platform="mp",
        )
        self.assertEqual(calls["n"], 2)
        self.assertEqual(out["meta"]["records_returned"], 10)
        self.assertEqual(out["meta"]["stop_reason"], sfa.STOP_FETCH_COUNT_REACHED)

    @patch("social_platform.services.task_service.async_task_redis.enqueue_async_task_execution")
    @patch("social_platform.services.task_service.async_task_redis.get_cached_api_key", return_value="k")
    @patch("social_platform.services.task_service.next_run_after_completion")
    def test_success_count_100_still_schedules_next_round(
        self,
        mock_next: MagicMock,
        _cached: MagicMock,
        mock_enqueue: MagicMock,
    ) -> None:
        now = datetime.utcnow()
        task = _task_row(now=now, success_count=100, fetch_count=10)
        db = _FakeDb(task)
        nxt = now + timedelta(minutes=10)
        mock_next.return_value = nxt

        ok = task_service.schedule_next_async_run(
            db, 1, "k", completed_at=now, last_ok=True
        )

        self.assertTrue(ok)
        self.assertEqual(task.status, "pending")
        self.assertEqual(task.next_run_at, nxt)
        mock_enqueue.assert_called_once()

    @patch("social_platform.services.task_service.async_task_redis.enqueue_async_task_execution")
    @patch("social_platform.services.task_service.async_task_redis.get_cached_api_key", return_value="k")
    @patch("social_platform.services.task_service.next_run_after_completion")
    def test_next_run_at_written_to_mysql_on_schedule(
        self,
        mock_next: MagicMock,
        _cached: MagicMock,
        _enqueue: MagicMock,
    ) -> None:
        now = datetime.utcnow()
        task = _task_row(now=now, success_count=0, fetch_count=10)
        db = _FakeDb(task)
        nxt = now + timedelta(minutes=15)
        mock_next.return_value = nxt

        task_service.schedule_next_async_run(db, 1, "k", completed_at=now, last_ok=True)

        self.assertEqual(task.next_run_at, nxt)
        self.assertEqual(task.status, "pending")

    def test_running_cache_keeps_next_run_at(self) -> None:
        now = datetime.utcnow()
        row = _task_row(now=now, status="running")
        nxt = now + timedelta(minutes=10)
        payload = async_task_redis._row_to_cache(row, next_run_at=nxt)
        self.assertIn("next_run_at", payload)

    @patch("social_platform.services.task_service.async_task_redis.enqueue_async_task_execution")
    @patch("social_platform.services.task_service.async_task_redis.get_cached_api_key", return_value="k")
    def test_mark_success_only_when_task_end_reached(
        self,
        _cached: MagicMock,
        mock_enqueue: MagicMock,
    ) -> None:
        now = datetime.utcnow()
        task = _task_row(now=now, task_end_time=now + timedelta(minutes=20))
        db = _FakeDb(task)

        with patch(
            "social_platform.services.task_service.next_run_after_completion",
            return_value=now + timedelta(minutes=10),
        ):
            keep_running = task_service.schedule_next_async_run(
                db, 1, "k", completed_at=now, last_ok=True
            )
        self.assertTrue(keep_running)
        self.assertEqual(task.status, "pending")

        with patch(
            "social_platform.services.task_service.next_run_after_completion",
            return_value=None,
        ):
            reached_end = task_service.schedule_next_async_run(
                db, 1, "k", completed_at=now + timedelta(hours=1), last_ok=True
            )
        self.assertFalse(reached_end)
        self.assertEqual(task.status, "success")
        self.assertIsNone(task.next_run_at)
        self.assertEqual(mock_enqueue.call_count, 1)

    @patch.object(sfa, "_guards_apply", return_value=True)
    @patch("config.settings.get_settings")
    def test_mp_offset_growth_no_infinite_paging(
        self, mock_settings: MagicMock, _guards: MagicMock
    ) -> None:
        mock_settings.return_value = _settings()
        calls = {"n": 0}

        def api_call(_url: str, _key: str, body: dict[str, object]) -> dict[str, object]:
            calls["n"] += 1
            n = calls["n"]
            self.assertEqual(str(body.get("offset", "")), str(n - 1))
            return {
                "data": [{"post_id": f"p{n}-{i}"} for i in range(3)],
                "next_offset": str(n),
                "cookies_buffer": f"ck-{n}",
                "has_more": True,
            }

        out = sfa.fetch_offset_cookies_search_all(
            "http://test",
            "k",
            {"keyword": "k"},
            body_builder=_offset_body,
            api_call=api_call,
            fetch_count_cap=10,
            after_each_page=lambda chunk: len(chunk),
            log_platform="mp",
        )
        self.assertEqual(calls["n"], 4)
        self.assertEqual(out["meta"]["stop_reason"], sfa.STOP_FETCH_COUNT_REACHED)

    @patch.object(sfa, "_guards_apply", return_value=True)
    @patch("config.settings.get_settings")
    def test_repeated_page_token_stops_offset_search(
        self, mock_settings: MagicMock, _guards: MagicMock
    ) -> None:
        mock_settings.return_value = _settings()

        def api_call(_url: str, _key: str, _body: dict[str, object]) -> dict[str, object]:
            return {
                "data": [{"post_id": "same"}],
                "next_offset": "fixed",
                "cookies_buffer": "fixed-cookie",
                "has_more": True,
            }

        out = sfa.fetch_offset_cookies_search_all(
            "http://test",
            "k",
            {"keyword": "k"},
            body_builder=_offset_body,
            api_call=api_call,
            fetch_count_cap=100,
            after_each_page=lambda chunk: len(chunk),
            log_platform="mp",
        )
        self.assertEqual(out["meta"]["pages_fetched"], 2)
        self.assertEqual(out["meta"]["stop_reason"], sfa.STOP_REPEATED_PAGE_TOKEN)


if __name__ == "__main__":
    unittest.main()

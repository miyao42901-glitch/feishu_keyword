from __future__ import annotations

import sys
from pathlib import Path
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

# 与运行时一致：确保 workers/ 与 python/ 在 import 路径中
_ROOT = Path(__file__).resolve().parents[1]
for _p in (_ROOT, _ROOT / "workers"):
    _s = str(_p)
    if _s not in sys.path:
        sys.path.insert(0, _s)

from workers.douyin_worker._job import execute_douyin_search_all
from workers.mp_worker._job import execute_mp_search_all
from workers.wxvideo_worker._job import execute_wxvideo_search_all
from workers.xhs_worker._job import execute_xhs_search_all


def _base_params() -> dict:
    return {"key": "k", "keyword": "kw"}


class TestSearchAllTimeParams(unittest.TestCase):
    @patch("workers.douyin_worker._job.fetch_douyin_all")
    @patch("workers.douyin_worker._job.resolved_service_url", return_value="http://x")
    def test_douyin_accepts_start_end_time(
        self, _url: MagicMock, mock_fetch: MagicMock
    ) -> None:
        mock_fetch.return_value = {
            "records": [],
            "balance": 0,
            "insufficient_balance": False,
            "last_error": None,
            "meta": {},
        }
        params = _base_params() | {
            "start_time": "2026-05-19 10:00:00",
            "end_time": "2026-05-19 12:00:00",
        }
        execute_douyin_search_all(params)
        self.assertIsInstance(mock_fetch.call_args.kwargs["start_date"], datetime)
        self.assertIsInstance(mock_fetch.call_args.kwargs["end_date"], datetime)

    @patch("workers.xhs_worker._job.fetch_xhs_all")
    @patch("workers.xhs_worker._job.resolved_service_url", return_value="http://x")
    def test_xhs_accepts_start_end_time(
        self, _url: MagicMock, mock_fetch: MagicMock
    ) -> None:
        mock_fetch.return_value = {
            "records": [],
            "balance": 0,
            "insufficient_balance": False,
            "last_error": None,
            "meta": {},
        }
        params = _base_params() | {
            "start_time": "2026-05-19 10:00:00",
            "end_time": "2026-05-19 12:00:00",
        }
        execute_xhs_search_all(params)
        self.assertIsInstance(mock_fetch.call_args.kwargs["start_date"], datetime)
        self.assertIsInstance(mock_fetch.call_args.kwargs["end_date"], datetime)

    @patch("workers.mp_worker._job.fetch_mp_all")
    @patch("workers.mp_worker._job.service_url", return_value="http://x")
    def test_mp_accepts_start_end_time(
        self, _url: MagicMock, mock_fetch: MagicMock
    ) -> None:
        mock_fetch.return_value = {
            "records": [],
            "balance": 0,
            "insufficient_balance": False,
            "last_error": None,
            "meta": {},
        }
        params = _base_params() | {
            "start_time": "2026-05-19 10:00:00",
            "end_time": "2026-05-19 12:00:00",
        }
        execute_mp_search_all(params)
        self.assertIsInstance(mock_fetch.call_args.kwargs["start_date"], datetime)
        self.assertIsInstance(mock_fetch.call_args.kwargs["end_date"], datetime)

    @patch("workers.wxvideo_worker._job.fetch_wxvideo_all")
    @patch("workers.wxvideo_worker._job.service_url", return_value="http://x")
    def test_wxvideo_accepts_start_end_time(
        self, _url: MagicMock, mock_fetch: MagicMock
    ) -> None:
        mock_fetch.return_value = {
            "records": [],
            "balance": 0,
            "insufficient_balance": False,
            "last_error": None,
            "meta": {},
        }
        params = _base_params() | {
            "start_time": "2026-05-19 10:00:00",
            "end_time": "2026-05-19 12:00:00",
        }
        execute_wxvideo_search_all(params)
        self.assertIsInstance(mock_fetch.call_args.kwargs["start_date"], datetime)
        self.assertIsInstance(mock_fetch.call_args.kwargs["end_date"], datetime)


if __name__ == "__main__":
    unittest.main()

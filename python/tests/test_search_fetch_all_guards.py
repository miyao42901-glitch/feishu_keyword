"""search_fetch_all 翻页止损单元测试（无真实网络）。"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from config.settings import get_settings
from social_platform.utils import search_fetch_all as sfa


def _body(_params: dict) -> dict:
    return {"keyword": "k", "cursor": "", "log_id": ""}


class SearchFetchAllGuardsTests(unittest.TestCase):
    def setUp(self) -> None:
        get_settings.cache_clear()

    def tearDown(self) -> None:
        get_settings.cache_clear()

    def _settings(self, **overrides: object):
        base = MagicMock()
        base.async_search_all_max_pages = 50
        base.async_search_all_max_run_seconds = 900.0
        base.async_search_duplicate_page_threshold = 5
        base.async_search_guards_async_only = False
        for k, v in overrides.items():
            setattr(base, k, v)
        return base

    @patch.object(sfa, "_guards_apply", return_value=True)
    @patch("config.settings.get_settings")
    def test_stops_at_max_pages(self, mock_settings: MagicMock, _guards: MagicMock) -> None:
        mock_settings.return_value = self._settings(async_search_all_max_pages=2)
        calls: list[int] = []

        def api_call(_url: str, _key: str, body: dict) -> dict:
            calls.append(1)
            n = len(calls)
            return {
                "data": [{"aweme_id": f"a{n}"}],
                "next_cursor": f"c{n}",
                "next_logid": f"l{n}",
                "has_more": True,
            }

        out = sfa.fetch_douyin_search_all(
            "http://test",
            "key",
            {"keyword": "k"},
            body_builder=_body,
            api_call=api_call,
            list_sort_type=0,
            fetch_count_cap=500,
        )
        self.assertEqual(len(calls), 2)
        self.assertEqual(out["meta"]["stop_reason"], sfa.STOP_MAX_PAGES_REACHED)
        self.assertEqual(out["meta"]["pages_fetched"], 2)

    @patch.object(sfa, "_guards_apply", return_value=True)
    @patch("config.settings.get_settings")
    def test_stops_at_max_run_seconds(self, mock_settings: MagicMock, _guards: MagicMock) -> None:
        mock_settings.return_value = self._settings(
            async_search_all_max_pages=50,
            async_search_all_max_run_seconds=1.0,
        )
        clock = iter([0.0, 0.0, 0.2, 2.0, 2.0, 2.0])

        def monotonic() -> float:
            return next(clock, 2.0)

        def api_call(_url: str, _key: str, _body: dict) -> dict:
            return {
                "data": [{"aweme_id": "a1"}],
                "next_cursor": "c",
                "next_logid": "l",
                "has_more": True,
            }

        with patch.object(sfa.time, "monotonic", side_effect=monotonic):
            out = sfa.fetch_douyin_search_all(
                "http://test",
                "key",
                {"keyword": "k"},
                body_builder=_body,
                api_call=api_call,
                list_sort_type=0,
                fetch_count_cap=500,
            )
        self.assertEqual(out["meta"]["stop_reason"], sfa.STOP_MAX_RUN_SECONDS_REACHED)

    @patch.object(sfa, "_guards_apply", return_value=True)
    @patch("config.settings.get_settings")
    def test_stops_on_repeated_page_token(self, mock_settings: MagicMock, _guards: MagicMock) -> None:
        mock_settings.return_value = self._settings(async_search_all_max_pages=10)

        def api_call(_url: str, _key: str, _body: dict) -> dict:
            return {
                "data": [{"aweme_id": "same"}],
                "next_cursor": "fixed",
                "next_logid": "fixed",
                "has_more": True,
            }

        out = sfa.fetch_douyin_search_all(
            "http://test",
            "key",
            {"keyword": "k"},
            body_builder=_body,
            api_call=api_call,
            list_sort_type=0,
            fetch_count_cap=500,
        )
        self.assertEqual(out["meta"]["stop_reason"], sfa.STOP_REPEATED_PAGE_TOKEN)
        self.assertEqual(out["meta"]["pages_fetched"], 2)

    @patch.object(sfa, "_guards_apply", return_value=True)
    @patch("config.settings.get_settings")
    def test_stops_on_empty_page(self, mock_settings: MagicMock, _guards: MagicMock) -> None:
        mock_settings.return_value = self._settings(async_search_all_max_pages=10)

        def api_call(_url: str, _key: str, _body: dict) -> dict:
            return {"data": [], "has_more": True}

        out = sfa.fetch_douyin_search_all(
            "http://test",
            "key",
            {"keyword": "k"},
            body_builder=_body,
            api_call=api_call,
            list_sort_type=0,
            fetch_count_cap=500,
        )
        self.assertEqual(out["meta"]["stop_reason"], sfa.STOP_EMPTY_PAGE)
        self.assertEqual(out["meta"]["pages_fetched"], 1)

    @patch.object(sfa, "_guards_apply", return_value=True)
    @patch("config.settings.get_settings")
    def test_continues_then_stops_no_more_data(self, mock_settings: MagicMock, _guards: MagicMock) -> None:
        mock_settings.return_value = self._settings(async_search_all_max_pages=10)
        n = [0]

        def api_call(_url: str, _key: str, _body: dict) -> dict:
            n[0] += 1
            if n[0] == 1:
                return {
                    "data": [{"aweme_id": "a1"}],
                    "next_cursor": "c2",
                    "next_logid": "l2",
                    "has_more": True,
                }
            return {
                "data": [{"aweme_id": "a2"}],
                "next_cursor": "",
                "next_logid": "",
                "has_more": False,
            }

        out = sfa.fetch_douyin_search_all(
            "http://test",
            "key",
            {"keyword": "k"},
            body_builder=_body,
            api_call=api_call,
            list_sort_type=0,
            fetch_count_cap=500,
        )
        self.assertEqual(out["meta"]["stop_reason"], sfa.STOP_NO_MORE_DATA)
        self.assertEqual(out["meta"]["pages_fetched"], 2)
        self.assertEqual(len(out["records"]), 2)

    @patch.object(sfa, "_guards_apply", return_value=False)
    def test_legacy_safety_max_pages_when_guards_off(self, _guards: MagicMock) -> None:
        self.assertEqual(sfa._configured_safety_max_pages(), sfa.LEGACY_SAFETY_MAX_PAGES)

    @patch.object(sfa, "_guards_apply", return_value=True)
    @patch("config.settings.get_settings")
    def test_stops_at_fetch_count(self, mock_settings: MagicMock, _guards: MagicMock) -> None:
        mock_settings.return_value = self._settings(async_search_all_max_pages=10)

        def api_call(_url: str, _key: str, _body: dict) -> dict:
            return {
                "data": [{"aweme_id": "a1"}, {"aweme_id": "a2"}],
                "next_cursor": "c",
                "next_logid": "l",
                "has_more": True,
            }

        out = sfa.fetch_douyin_search_all(
            "http://test",
            "key",
            {"keyword": "k"},
            body_builder=_body,
            api_call=api_call,
            list_sort_type=0,
            fetch_count_cap=2,
        )
        self.assertEqual(out["meta"]["stop_reason"], sfa.STOP_FETCH_COUNT_REACHED)
        self.assertEqual(len(out["records"]), 2)


if __name__ == "__main__":
    unittest.main()

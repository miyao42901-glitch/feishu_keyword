"""IP 限流：短 scope Redis key + 毫秒 ZSET。"""

from __future__ import annotations

import re
import unittest
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from http_api.rate_limit import (
    _check_ip_rate_limit_memory,
    _check_ip_rate_limit_redis,
    _redis_rate_limit_key,
    ip_rate_limit,
    normalize_rate_limit_scope,
)
from social_platform.api_response import ApiHttpError, register_api_exception_handlers
from social_platform.api_status_codes import CODE_RATE_LIMIT_EXCEEDED


class TestScopeAndKey(unittest.TestCase):
    def test_scope_rejects_path_like_strings(self) -> None:
        with self.assertRaises(ValueError):
            normalize_rate_limit_scope("/api/v1/async/tasks")
        with self.assertRaises(ValueError):
            normalize_rate_limit_scope("GET:/foo")

    def test_redis_key_has_no_url(self) -> None:
        key = _redis_rate_limit_key("1.2.3.4", "async_submit")
        self.assertEqual(key, "feishu:ratelimit:async_submit:1.2.3.4")
        self.assertNotIn("/", key)


class TestRedisRateLimitMember(unittest.TestCase):
    @patch("http_api.rate_limit.get_redis")
    def test_zadd_uses_ms_member_not_float_timestamp(self, mock_get: MagicMock) -> None:
        r = MagicMock()
        mock_get.return_value = r
        pipe = MagicMock()
        r.pipeline.return_value = pipe
        pipe.execute.return_value = [0, 0]

        _check_ip_rate_limit_redis(
            "9.9.9.9",
            "async_submit",
            max_requests=10,
            window_seconds=60,
        )

        member, score = next(iter(r.zadd.call_args[0][1].items()))
        self.assertRegex(member, r"^\d+-[1-9]\d{0,2}$")
        self.assertIsInstance(score, int)
        self.assertGreater(score, 1_000_000_000_000)


class TestMemoryRateLimit(unittest.TestCase):
    def test_blocks_after_max_requests(self) -> None:
        for _ in range(3):
            _check_ip_rate_limit_memory(
                "1.2.3.4",
                "async_submit",
                max_requests=3,
                window_seconds=60,
            )
        with self.assertRaises(ApiHttpError) as ctx:
            _check_ip_rate_limit_memory(
                "1.2.3.4",
                "async_submit",
                max_requests=3,
                window_seconds=60,
            )
        self.assertEqual(ctx.exception.code, CODE_RATE_LIMIT_EXCEEDED)


class TestFastApiRateLimitDep(unittest.TestCase):
    def test_returns_429_json(self) -> None:
        app = FastAPI()
        register_api_exception_handlers(app)

        @app.get("/x", dependencies=[ip_rate_limit(max_requests=2, scope="test_scope")])
        def _x() -> dict[str, str]:
            return {"ok": "1"}

        client = TestClient(app)
        self.assertEqual(client.get("/x").status_code, 200)
        self.assertEqual(client.get("/x").status_code, 200)
        r = client.get("/x")
        self.assertEqual(r.status_code, 429)
        self.assertEqual(r.json().get("code"), CODE_RATE_LIMIT_EXCEEDED)


if __name__ == "__main__":
    unittest.main()

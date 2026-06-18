#!/usr/bin/env python3
"""四平台高并发假数据压测：不调 YDDM；MySQL 数据不删除。"""

from __future__ import annotations

import argparse
import importlib
import random
import string
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterator
from unittest.mock import patch

_SERVER_ROOT = Path(__file__).resolve().parents[1]
_WORKERS_ROOT = _SERVER_ROOT / "workers"
for _p in (_SERVER_ROOT, _WORKERS_ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from social_platform.models.results.registry import list_supported_platforms
from social_platform.services.result_store_service import save_search_results

ALL_PLATFORMS = tuple(list_supported_platforms())


@dataclass
class RunStats:
    lock: threading.Lock = field(default_factory=threading.Lock)
    inserted: int = 0
    duplicated: int = 0
    persist_errors: int = 0
    skipped: int = 0
    deadlock_1205: int = 0
    other_errors: int = 0
    error_samples: list[str] = field(default_factory=list)
    chunks_ok: int = 0
    chunks_failed: int = 0

    def merge_save_result(self, result: dict[str, Any]) -> None:
        with self.lock:
            self.inserted += int(result.get("inserted_count") or result.get("inserted") or 0)
            self.duplicated += int(result.get("duplicated_count") or result.get("duplicated") or 0)
            self.persist_errors += int(result.get("failed_count") or result.get("persist_errors") or 0)
            self.skipped += int(result.get("skipped_count") or result.get("skipped") or 0)
            self.chunks_ok += 1

    def record_exception(self, exc: BaseException) -> None:
        msg = f"{type(exc).__name__}: {exc}"
        is_1205 = "1205" in msg or any("1205" in str(a) for a in getattr(exc, "args", ()))
        with self.lock:
            self.chunks_failed += 1
            if is_1205:
                self.deadlock_1205 += 1
            else:
                self.other_errors += 1
                if len(self.error_samples) < 30:
                    self.error_samples.append(msg)

    def lines(self, label: str) -> list[str]:
        with self.lock:
            return [
                f"=== {label} ===",
                f"chunks ok / failed:     {self.chunks_ok} / {self.chunks_failed}",
                f"inserted:                {self.inserted}",
                f"duplicated:              {self.duplicated}",
                f"persist_errors:          {self.persist_errors}",
                f"skipped:                 {self.skipped}",
                f"deadlock (1205):         {self.deadlock_1205}",
                f"other exceptions:        {self.other_errors}",
            ] + (["--- samples ---", *self.error_samples] if self.error_samples else [])


def _rand(n: int = 10) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


def _parse_platforms(raw: str) -> tuple[str, ...]:
    if raw.strip().lower() in ("all", "*"):
        return ALL_PLATFORMS
    chosen = tuple(p.strip().lower() for p in raw.split(",") if p.strip())
    bad = [p for p in chosen if p not in ALL_PLATFORMS]
    if bad:
        raise SystemExit(f"unsupported platform(s): {bad}; supported: {ALL_PLATFORMS}")
    return chosen


def make_mock_row(platform: str, post_id: str, seq: int) -> dict[str, Any]:
    if platform == "xhs":
        xsec = f"mock_xsec_{seq}"
        return {
            "note_id": post_id,
            "title": f"mock xhs title {seq}",
            "desc": f"mock xhs desc {uuid.uuid4().hex[:8]}",
            "xsec_token": xsec,
            "url": f"https://www.xiaohongshu.com/explore/{post_id}?xsec_token={xsec}&xsec_source=pc_search",
            "publish_time": int(time.time() * 1000) - random.randint(0, 86400_000 * 30),
            "like_count": random.randint(0, 9999),
            "comment_count": random.randint(0, 500),
            "collect_count": random.randint(0, 999),
            "duration": random.randint(0, 120),
            "has_music": bool(random.getrandbits(1)),
            "images_list": [f"https://example.com/xhs/{post_id}.jpg"],
            "video_list": [],
            "nickname": f"xhs_nick_{seq % 7}",
            "userid": f"xhs_uid_{seq % 7}",
            "avatar": f"https://example.com/xhs/avatar/{seq % 7}.jpg",
            "content_type": random.choice(["normal", "video"]),
        }
    if platform == "douyin":
        return {
            "aweme_id": post_id,
            "nickname": f"dy_nick_{seq % 7}",
            "user_id": f"dy_sec_{seq % 7}",
            "title": f"mock douyin title {seq}",
            "desc": f"mock douyin desc {uuid.uuid4().hex[:8]}",
            "url": f"https://www.douyin.com/video/{post_id}",
            "avatar": f"https://example.com/dy/avatar/{seq % 7}.jpg",
            "signature": f"sig_{seq}",
            "verify_name": "",
            "cover": f"https://example.com/dy/cover/{post_id}.jpg",
            "duration": float(random.randint(5, 180)),
            "publish_time": int(time.time() * 1000) - random.randint(0, 86400_000 * 30),
            "like_count": random.randint(0, 99999),
            "comment_count": random.randint(0, 5000),
            "share_count": random.randint(0, 2000),
            "collect_count": random.randint(0, 3000),
            "video_list": [f"https://example.com/dy/video/{post_id}.mp4"],
        }
    if platform == "wxvideo":
        return {
            "post_id": post_id,
            "nickname": f"wxv_nick_{seq % 7}",
            "avatar_url": f"https://example.com/wxv/avatar/{seq % 7}.jpg",
            "title": f"mock wxvideo title {seq}",
            "publish_time": int(time.time()) - random.randint(0, 86400 * 30),
            "duration": random.randint(5, 300),
            "cover_url": f"https://example.com/wxv/cover/{post_id}.jpg",
            "video_url": f"https://example.com/wxv/video/{post_id}.mp4",
            "like_count": random.randint(0, 9999),
            "comment_count": random.randint(0, 500),
            "forward_count": random.randint(0, 200),
            "thumb_count": random.randint(0, 1000),
        }
    if platform == "mp":
        return {
            "post_id": post_id,
            "article_id": post_id,
            "company_name": f"mock_mp_company_{seq % 5}",
            "biz": f"biz_{seq % 5}",
            "title": f"mock mp title {seq}",
            "summary": f"mock mp summary {uuid.uuid4().hex[:8]}",
            "url": f"https://mp.weixin.qq.com/s/{post_id}",
            "avatar_url": f"https://example.com/mp/avatar/{seq % 7}.jpg",
            "publish_time": int(time.time()) - random.randint(0, 86400 * 30),
        }
    raise ValueError(f"unsupported platform: {platform!r}")


def make_chunk_rows(
    platform: str,
    chunk_index: int,
    rows_per_chunk: int,
    overlap_pool: list[str],
    overlap_ratio: float,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    prefix = platform[:3]
    for i in range(rows_per_chunk):
        if overlap_pool and random.random() < overlap_ratio:
            post_id = random.choice(overlap_pool)
        else:
            post_id = f"mock_{prefix}_{chunk_index}_{i}_{_rand()}"
        rows.append(make_mock_row(platform, post_id, chunk_index * 1000 + i))
    return rows


def run_persist_mode(
    platform: str,
    workers: int,
    tasks: int,
    rows_per_chunk: int,
    overlap_ratio: float,
    task_id_base: int,
    user_id: str,
    keyword: str,
) -> RunStats:
    stats = RunStats()
    overlap_pool = [f"overlap_{platform}_{i}_{_rand(8)}" for i in range(max(2, rows_per_chunk))]
    jobs = [(task_id_base + t, c) for t in range(tasks) for c in range(workers)]

    def work(task_id: int, chunk_index: int) -> None:
        rows = make_chunk_rows(platform, chunk_index, rows_per_chunk, overlap_pool, overlap_ratio)
        try:
            stats.merge_save_result(
                save_search_results(platform, keyword, rows, user_id=user_id, task_id=task_id)
            )
        except Exception as exc:
            stats.record_exception(exc)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        for f in as_completed(pool.submit(work, tid, ci) for tid, ci in jobs):
            f.result()
    return stats


@contextmanager
def async_persist_ctx(platform: str, task_id: int, user_id: str, keyword: str) -> Iterator[None]:
    from social_platform.services.search_persist import search_all_async_ctx

    token = search_all_async_ctx.set({
        "task_id": task_id,
        "user_id": user_id,
        "platform": platform,
        "keyword": keyword,
        "run_id": f"mock-{platform}-{task_id}-{uuid.uuid4().hex[:8]}",
    })
    try:
        yield
    finally:
        search_all_async_ctx.reset(token)


_WORKER_SPECS: dict[str, dict[str, str]] = {
    "xhs": {"module": "xhs_worker._job", "execute": "execute_xhs_search_all", "api_fn": "call_xhs_api"},
    "douyin": {"module": "douyin_worker._job", "execute": "execute_douyin_search_all", "api_fn": "call_douyin_api"},
    "wxvideo": {"module": "wxvideo_worker._job", "execute": "execute_wxvideo_search_all", "api_fn": "call_wxvideo_api"},
    "mp": {"module": "mp_worker._job", "execute": "execute_mp_search_all", "api_fn": "call_mp_api"},
}


def _worker_params(keyword: str, rows_per_chunk: int, max_pages: int) -> dict[str, Any]:
    return {
        "key": "mock-key",
        "keyword": keyword,
        "fetch_count": rows_per_chunk * max_pages,
        "max_pages": max_pages,
    }


def _make_worker_api_mock(
    platform: str,
    rows_per_chunk: int,
    overlap_pool: list[str],
    overlap_ratio: float,
    max_pages: int,
    page_state: dict[int, int],
    lock: threading.Lock,
) -> Callable[..., dict[str, Any]]:
    if platform == "xhs":
        from xhs_worker.parser import XhsParser

        def mock_call_xhs_api(api_url: str, key: str, body: dict[str, Any]) -> dict[str, Any]:
            del api_url, key
            page = int(body.get("page") or 1)
            with lock:
                ci = page_state.get(page, page)
                page_state[page] = ci + 1
            rows = make_chunk_rows("xhs", ci, rows_per_chunk, overlap_pool, overlap_ratio)
            items = [{
                "note": {
                    "id": r["note_id"],
                    "xsec_token": r["xsec_token"],
                    "title": r["title"],
                    "desc": r["desc"],
                    "timestamp": int(r["publish_time"] // 1000),
                    "liked_count": r["like_count"],
                    "comments_count": r["comment_count"],
                    "collected_count": r["collect_count"],
                    "type": r["content_type"],
                    "has_music": r["has_music"],
                    "video_duration": "0:36",
                    "images_list": [{"url": u} for u in r["images_list"]],
                    "user": {"nickname": r["nickname"], "userid": r["userid"], "images": r["avatar"]},
                }
            } for r in rows]
            parsed = XhsParser().parse({"data": {"items": items}, "balance": 99999, "cost": 1})
            parsed["has_more"] = page < max_pages
            return parsed

        return mock_call_xhs_api

    def mock_api(api_url: str, key: str, body: dict[str, Any]) -> dict[str, Any]:
        del api_url, key
        page = int(body.get("page") or body.get("cursor") or 1)
        with lock:
            ci = page_state.get(page, page)
            page_state[page] = ci + 1
        rows = make_chunk_rows(platform, ci, rows_per_chunk, overlap_pool, overlap_ratio)
        return {
            "data": rows,
            "balance": 99999,
            "cost": 1,
            "error": None,
            "insufficient_balance": False,
            "has_more": page < max_pages,
        }

    return mock_api


def run_worker_mode(
    platform: str,
    workers: int,
    tasks: int,
    rows_per_chunk: int,
    overlap_ratio: float,
    task_id_base: int,
    user_id: str,
    keyword: str,
    max_pages: int,
) -> RunStats:
    spec = _WORKER_SPECS[platform]
    mod = importlib.import_module(spec["module"])
    execute_fn = getattr(mod, spec["execute"])
    stats = RunStats()
    overlap_pool = [f"overlap_w_{platform}_{i}_{_rand(8)}" for i in range(max(2, rows_per_chunk))]
    page_state: dict[int, int] = {}
    lock = threading.Lock()
    mock_api = _make_worker_api_mock(
        platform, rows_per_chunk, overlap_pool, overlap_ratio, max_pages, page_state, lock
    )
    patch_target = f"{spec['module']}.{spec['api_fn']}"

    def run_one(task_id: int) -> None:
        try:
            with async_persist_ctx(platform, task_id, user_id, keyword):
                with patch(patch_target, side_effect=mock_api):
                    out = execute_fn(_worker_params(keyword, rows_per_chunk, max_pages))
            if not out.get("ok"):
                stats.record_exception(RuntimeError(str(out.get("error") or out)))
            else:
                stats.chunks_ok += 1
        except Exception as exc:
            stats.record_exception(exc)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(run_one, [task_id_base + t for t in range(tasks)]))
    return stats


def _task_id_base_for(platform: str, base: int) -> int:
    offsets = {"xhs": 0, "douyin": 100_000, "wxvideo": 200_000, "mp": 300_000}
    return base + offsets.get(platform, 0)


def main() -> None:
    p = argparse.ArgumentParser(description="四平台假数据并发压测（不调 YDDM）")
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--tasks", type=int, default=2)
    p.add_argument("--rows-per-chunk", type=int, default=5)
    p.add_argument("--overlap-ratio", type=float, default=0.2)
    p.add_argument("--mode", choices=("persist", "worker", "both"), default="both")
    p.add_argument("--platforms", default="all", help=f"逗号分隔或 all；支持: {','.join(ALL_PLATFORMS)}")
    p.add_argument("--task-id-base", type=int, default=9_000_000)
    p.add_argument("--user-id", default="mock_concurrent_user")
    p.add_argument("--keyword", default="mock_keyword_concurrent")
    p.add_argument("--max-pages", type=int, default=2)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()
    random.seed(args.seed)
    platforms = _parse_platforms(args.platforms)

    print(f"platforms={platforms} mode={args.mode} workers={args.workers} tasks={args.tasks}")
    print("不调 YDDM；MySQL 数据不删除")

    for platform in platforms:
        tid_base = _task_id_base_for(platform, args.task_id_base)
        kw = f"{args.keyword}_{platform}"

        if args.mode in ("persist", "both"):
            t0 = time.perf_counter()
            st = run_persist_mode(
                platform, args.workers, args.tasks, args.rows_per_chunk,
                args.overlap_ratio, tid_base, args.user_id, kw,
            )
            print("\n" + "\n".join(st.lines(f"{platform}/persist")))
            print(f"elapsed: {time.perf_counter() - t0:.2f}s")

        if args.mode in ("worker", "both"):
            t0 = time.perf_counter()
            try:
                st = run_worker_mode(
                    platform, args.workers, args.tasks, args.rows_per_chunk,
                    args.overlap_ratio, tid_base + 10_000, args.user_id, kw, args.max_pages,
                )
                print("\n" + "\n".join(st.lines(f"{platform}/worker")))
                print(f"elapsed: {time.perf_counter() - t0:.2f}s")
            except (SystemExit, AttributeError, ImportError) as exc:
                print(f"\n[{platform}/worker] SKIP: {exc}")


if __name__ == "__main__":
    main()
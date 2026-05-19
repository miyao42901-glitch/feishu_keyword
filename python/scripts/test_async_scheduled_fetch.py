#!/usr/bin/env python3
"""
四平台定时异步任务集成测试脚本。

检查项：
  1. 单次执行内 success_count 增量不超过 fetch_count（单轮停止）
  2. 周期任务允许累计 success_count 超过 fetch_count
  3. 定时窗口内按 interval_minutes 触发执行（success_count 阶梯增长或 status=running）
  4. 结果表 post_id 无重复（单次入库去重）

用法（HTTP，需 run.py + celery worker + Redis + MySQL）::

    cd python
    set FEISHU_API_KEY=你的key
    set FEISHU_USER_ID=14
    python scripts/test_async_scheduled_fetch.py

用法（直连 DB，跳过 yddm HTTP 校验，可配合 --execute-once 立即跑一轮）::

    python scripts/test_async_scheduled_fetch.py --mode direct --execute-once
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

_PY_ROOT = Path(__file__).resolve().parent.parent
if str(_PY_ROOT) not in sys.path:
    sys.path.insert(0, str(_PY_ROOT))

API_PREFIX = "/api/v1"

PLATFORMS: list[tuple[str, str]] = [
    ("douyin", "douyin-search-all"),
    ("xhs", "xhs-search-all"),
    ("wxvideo", "wxvideo-search-all"),
    ("mp", "mp-search-all"),
]


@dataclass
class TaskProbe:
    platform: str
    action: str
    task_id: int
    fetch_count: int
    interval_minutes: int
    success_history: list[tuple[float, int, str]] = field(default_factory=list)
    run_deltas: list[int] = field(default_factory=list)
    post_ids: set[str] = field(default_factory=set)
    issues: list[str] = field(default_factory=list)
    last_run_meta: dict[str, Any] = field(default_factory=dict)
    last_pages_fetched: Optional[int] = None

    def record(self, *, success_count: int, status: str) -> None:
        prev = self.success_history[-1][1] if self.success_history else None
        self.success_history.append((time.time(), success_count, status))
        if prev is not None and success_count > prev:
            self.run_deltas.append(success_count - prev)

    def analyze(self) -> dict[str, Any]:
        for i, delta in enumerate(self.run_deltas, 1):
            if delta > self.fetch_count:
                self.issues.append(
                    f"第{i}次执行增量={delta} 超过 fetch_count={self.fetch_count}"
                )
        runs = len(self.run_deltas)
        if self.last_pages_fetched is not None and self.last_pages_fetched > 50:
            self.issues.append(
                f"单次抓取页数过多 pages_fetched={self.last_pages_fetched}（疑似未停止翻页）"
            )
        if self.last_run_meta:
            cap = int(self.last_run_meta.get("fetch_count_cap") or self.fetch_count)
            ret = int(self.last_run_meta.get("records_returned") or 0)
            if ret > cap:
                self.issues.append(
                    f"单次 records_returned={ret} 超过 fetch_count_cap={cap}"
                )
            stop = self.last_run_meta.get("stop_reason")
            if stop in (None, "") and ret > 0:
                self.issues.append("有数据返回但缺少 stop_reason")
        if runs == 0 and max_sc == 0 and not self.last_run_meta:
            self.issues.append("窗口内未观察到 success_count 增长（可能未执行或 API 无数据）")
        return {
            "platform": self.platform,
            "action": self.action,
            "task_id": self.task_id,
            "fetch_count": self.fetch_count,
            "max_success_count": max_sc,
            "run_count_observed": runs,
            "run_deltas": self.run_deltas,
            "unique_post_ids": len(self.post_ids),
            "last_run_meta": self.last_run_meta,
            "issues": self.issues,
            "ok": not self.issues,
        }


def _fmt_dt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _http_json(
    method: str,
    url: str,
    *,
    headers: dict[str, str],
    body: Optional[dict[str, Any]] = None,
    timeout: float = 60.0,
) -> dict[str, Any]:
    data = None
    hdrs = dict(headers)
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        hdrs.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"code": e.code, "msg": raw, "data": None}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"code": -1, "msg": raw, "data": None}


class HttpClient:
    def __init__(self, base: str, api_key: str, user_id: str) -> None:
        self.base = base.rstrip("/")
        self.api_key = api_key.strip()
        self.user_id = user_id.strip()

    def _headers(self) -> dict[str, str]:
        return {
            "X-API-Key": self.api_key,
            "X-User-Id": self.user_id,
        }

    def submit(self, payload: dict[str, Any]) -> int:
        url = f"{self.base}{API_PREFIX}/async/tasks"
        out = _http_json("POST", url, headers=self._headers(), body=payload)
        if int(out.get("code", -1)) != 0:
            raise RuntimeError(f"submit failed: {out}")
        tid = (out.get("data") or {}).get("task_id")
        if tid is None:
            raise RuntimeError(f"submit missing task_id: {out}")
        return int(tid)

    def status(self, task_id: int) -> dict[str, Any]:
        url = f"{self.base}{API_PREFIX}/async/tasks/{task_id}"
        out = _http_json("GET", url, headers=self._headers())
        if int(out.get("code", -1)) != 0:
            raise RuntimeError(f"status failed: {out}")
        return out.get("data") or {}

    def results(self, task_id: int, *, page: int = 1, limit: int = 200) -> dict[str, Any]:
        url = f"{self.base}{API_PREFIX}/async/tasks/{task_id}/results?page={page}&limit={limit}"
        out = _http_json("GET", url, headers=self._headers())
        if int(out.get("code", -1)) != 0:
            raise RuntimeError(f"results failed: {out}")
        return out.get("data") or {}

    def cancel(self, task_id: int) -> None:
        url = f"{self.base}{API_PREFIX}/async/tasks/{task_id}/cancel"
        _http_json("POST", url, headers=self._headers(), body={})


def _collect_post_ids(client: HttpClient, probe: TaskProbe) -> None:
    page = 1
    while True:
        data = client.results(probe.task_id, page=page, limit=200)
        items = data.get("items") or []
        for item in items:
            if not isinstance(item, dict):
                continue
            pid = item.get("post_id") or item.get("aweme_id") or item.get("note_id")
            if pid is not None and str(pid).strip():
                pid_s = str(pid).strip()
                if pid_s in probe.post_ids:
                    probe.issues.append(f"结果列表出现重复 post_id={pid_s}")
                probe.post_ids.add(pid_s)
        total = int(data.get("total") or 0)
        if page * 200 >= total or not items:
            break
        page += 1


def submit_direct(
    *,
    user_id: str,
    api_key: str,
    action: str,
    body: dict[str, Any],
    task_start: datetime,
    task_end: datetime,
    interval_minutes: int,
    fetch_count: int,
) -> int:
    from unittest.mock import patch

    from social_platform.database.session import session_scope
    from social_platform.services import task_service

    with patch(
        "social_platform.services.task_service.assert_x_user_id_matches_yddm",
        return_value=str(user_id),
    ):
        with session_scope() as db:
            return task_service.submit_async_task(
                db,
                action=action,
                body=body,
                user_id=str(user_id),
                api_key=api_key,
                task_start_time=task_start,
                task_end_time=task_end,
                interval_minutes=interval_minutes,
                fetch_count=fetch_count,
            )


def status_direct(task_id: int) -> dict[str, Any]:
    from social_platform.database.session import session_scope
    from social_platform.services import task_service

    with session_scope() as db:
        st = task_service.get_task_status(db, str(task_id))
    if st is None:
        raise RuntimeError(f"task {task_id} not found")
    return st.model_dump()


def cleanup_pending_direct(*, user_id: str) -> int:
    from sqlalchemy import select

    from social_platform.database.session import session_scope
    from social_platform.models.async_task import AsyncTask
    from social_platform.services import async_task_redis

    n = 0
    with session_scope() as db:
        rows = db.scalars(
            select(AsyncTask).where(
                AsyncTask.user_id == str(user_id),
                AsyncTask.status.in_(("pending", "running")),
            )
        ).all()
        for row in rows:
            row.cancel_requested = True
            row.status = "cancelled"
            row.update_time = datetime.utcnow()
            db.add(row)
            async_task_redis.retain_async_task_redis_on_cancel(row)
            n += 1
        db.commit()
    return n


def cancel_direct(task_id: int, *, user_id: str, api_key: str) -> None:
    from unittest.mock import patch

    from social_platform.database.session import session_scope
    from social_platform.services import task_service

    with patch(
        "social_platform.services.task_service.assert_async_task_user",
        return_value=str(user_id),
    ):
        with session_scope() as db:
            task_service.cancel_async_task(db, str(task_id), user_id=str(user_id))


def execute_once_direct(task_id: int, api_key: str) -> dict[str, Any]:
    """执行一轮（与 Celery 相同路径）并返回 worker data.meta。"""
    from social_platform.api_response import from_worker_run
    from social_platform.api_status_codes import CODE_SUCCESS
    from social_platform.database.session import session_scope
    from social_platform.actions.runner import execute_public_action
    from social_platform.models.async_task import AsyncTask
    from social_platform.services import async_task_redis, task_service
    from social_platform.services.search_persist import (
        SearchAllAsyncPersistState,
        apply_search_persist_stats_to_async_task,
        bind_search_all_async_persist,
        try_save_search_after_crawl,
        unbind_search_all_async_persist,
    )

    meta: dict[str, Any] = {}
    with session_scope() as db:
        row = db.get(AsyncTask, int(task_id))
        if row is None:
            return meta
        body = task_service.body_for_worker_execution(row)
        token = bind_search_all_async_persist(
            SearchAllAsyncPersistState(
                db=db,
                task_id=int(task_id),
                run_id=str(getattr(row, "current_run_id", "") or "manual-run"),
                user_id=str(row.user_id or ""),
                public_action=str(row.action or ""),
                body=body,
            )
        )
        try:
            raw = execute_public_action(str(row.action or ""), body, api_key)
            data = raw.get("data") if isinstance(raw.get("data"), dict) else {}
            meta = dict(data.get("meta") or {})
            stats = try_save_search_after_crawl(
                str(row.action or ""),
                body,
                raw,
                user_id=str(row.user_id or ""),
                task_id=int(task_id),
            )
            if stats:
                apply_search_persist_stats_to_async_task(db, int(task_id), stats)
            api_body = from_worker_run(raw)
            ok = int(api_body.get("code", -1)) == CODE_SUCCESS
            row = db.get(AsyncTask, int(task_id))
            if row is not None:
                row.update_time = datetime.utcnow()
                if not ok:
                    msg = api_body.get("msg")
                    row.error_message = (str(msg) if msg is not None else "")[:64] or None
                else:
                    row.error_message = None
                db.add(row)
                db.commit()
                async_task_redis.update_async_task_cache(row, clear_next_run=True)
            task_service.schedule_next_async_run(
                db,
                int(task_id),
                api_key,
                completed_at=task_service.utc_now_naive(),
                last_ok=ok,
            )
        finally:
            unbind_search_all_async_persist(token)
    return meta


def dispatch_tick() -> None:
    from social_platform.services.async_dispatch_tick import run_async_dispatch_tick

    run_async_dispatch_tick()


def build_submit_payload(
    action: str,
    keyword: str,
    *,
    task_start: datetime,
    task_end: datetime,
    interval_minutes: int,
    fetch_count: int,
) -> dict[str, Any]:
    return {
        "action": action,
        "body": {
            "keyword": keyword,
            "sort_type": 2,
        },
        "task_start_time": _fmt_dt(task_start),
        "task_end_time": _fmt_dt(task_end),
        "interval_minutes": interval_minutes,
        "fetch_count": fetch_count,
    }


def monitor(
    probes: list[TaskProbe],
    *,
    client: Optional[HttpClient],
    poll_seconds: float,
    duration_seconds: float,
    status_fn,
    collect_results: bool,
) -> None:
    deadline = time.time() + duration_seconds
    tick = 0
    while time.time() < deadline:
        tick += 1
        print(f"\n--- poll #{tick} @ {datetime.now().strftime('%H:%M:%S')} ---")
        dispatch_tick()
        for probe in probes:
            st = status_fn(probe.task_id)
            sc = int(st.get("success_count") or 0)
            status = str(st.get("status") or "")
            probe.record(success_count=sc, status=status)
            print(
                f"  [{probe.platform}] task={probe.task_id} status={status} "
                f"success_count={sc}/{probe.fetch_count} failed={st.get('failed_count', 0)}"
            )
            if collect_results and client is not None:
                try:
                    _collect_post_ids(client, probe)
                except Exception as e:
                    probe.issues.append(f"拉取结果失败: {e}")
        time.sleep(poll_seconds)


def _configure_stdio() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass


def main() -> int:
    _configure_stdio()
    parser = argparse.ArgumentParser(description="四平台定时异步任务集成测试")
    parser.add_argument(
        "--mode",
        choices=("http", "direct"),
        default=os.environ.get("FEISHU_TEST_MODE", "http"),
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("FEISHU_API_BASE", "http://127.0.0.1:8765"),
    )
    parser.add_argument("--api-key", default=os.environ.get("FEISHU_API_KEY", ""))
    parser.add_argument("--user-id", default=os.environ.get("FEISHU_USER_ID", ""))
    parser.add_argument("--keyword", default="西湖")
    parser.add_argument(
        "--no-platform-suffix",
        action="store_true",
        help="不在 keyword 后追加 -{platform}（四平台用同一关键词）",
    )
    parser.add_argument(
        "--cleanup-pending",
        action="store_true",
        help="提交前取消当前用户所有 pending/running 任务（避免配额占满）",
    )
    parser.add_argument(
        "--only",
        default="",
        help="仅测试指定平台，逗号分隔：douyin,xhs,wxvideo,mp",
    )
    parser.add_argument("--fetch-count", type=int, default=10)
    parser.add_argument("--interval-minutes", type=int, default=10)
    parser.add_argument(
        "--window-minutes",
        type=int,
        default=25,
        help="任务窗口长度（从当前时刻起），用于观察至少 2 次定时",
    )
    parser.add_argument("--poll-seconds", type=float, default=20.0)
    parser.add_argument(
        "--duration-seconds",
        type=float,
        default=None,
        help="监控时长，默认 window_minutes + interval",
    )
    parser.add_argument(
        "--execute-once",
        action="store_true",
        help="direct 模式：提交后立即执行一轮（不依赖 celery）",
    )
    parser.add_argument("--no-cancel", action="store_true", help="结束后不取消任务")
    args = parser.parse_args()

    if args.interval_minutes < 5:
        print("interval_minutes 最小为 5，已调整为 5")
        args.interval_minutes = 5

    now = datetime.now().replace(microsecond=0)
    task_start = now
    task_end = now + timedelta(minutes=args.window_minutes)
    duration = args.duration_seconds
    if duration is None:
        duration = float(args.window_minutes * 60 + args.interval_minutes * 60)

    api_key = (args.api_key or "").strip()
    user_id = (args.user_id or "").strip()
    if args.mode == "http" and (not api_key or not user_id):
        print("HTTP 模式需要 FEISHU_API_KEY 与 FEISHU_USER_ID（或 --api-key / --user-id）")
        return 2

    if args.mode == "direct" and not user_id:
        user_id = "9999"
    if args.mode == "direct" and not api_key:
        api_key = "test-key-direct"

    client: Optional[HttpClient] = None
    if args.mode == "http":
        client = HttpClient(args.base_url, api_key, user_id)
        submit_fn = lambda action, kw: client.submit(  # noqa: E731
            build_submit_payload(
                action,
                kw,
                task_start=task_start,
                task_end=task_end,
                interval_minutes=args.interval_minutes,
                fetch_count=args.fetch_count,
            )
        )
        status_fn = lambda tid: client.status(tid)  # noqa: E731
        cancel_fn = lambda tid: client.cancel(tid)  # noqa: E731
    else:
        submit_fn = lambda action, kw: submit_direct(  # noqa: E731
            user_id=user_id,
            api_key=api_key,
            action=action,
            body={"keyword": kw, "sort_type": 2},
            task_start=task_start,
            task_end=task_end,
            interval_minutes=args.interval_minutes,
            fetch_count=args.fetch_count,
        )
        status_fn = status_direct
        cancel_fn = lambda tid: cancel_direct(tid, user_id=user_id, api_key=api_key)  # noqa: E731

    print("=== 四平台定时任务测试 ===")
    print(f"mode={args.mode} window=[{_fmt_dt(task_start)} ~ {_fmt_dt(task_end)}]")
    print(f"interval_minutes={args.interval_minutes} fetch_count={args.fetch_count}")
    print(f"monitor {duration:.0f}s, poll every {args.poll_seconds}s")

    if args.cleanup_pending:
        if args.mode == "direct":
            n = cleanup_pending_direct(user_id=user_id)
            print(f"已取消 pending/running 任务数: {n}")
        else:
            print("cleanup-pending 当前仅支持 --mode direct")

    only = {x.strip().lower() for x in (args.only or "").split(",") if x.strip()}
    platform_list = PLATFORMS
    if only:
        platform_list = [(p, a) for p, a in PLATFORMS if p in only]

    probes: list[TaskProbe] = []
    for platform, action in platform_list:
        kw = args.keyword if args.no_platform_suffix else f"{args.keyword}-{platform}"
        try:
            tid = submit_fn(action, kw)
        except Exception as e:
            print(f"[{platform}] 提交失败: {e}")
            continue
        probes.append(
            TaskProbe(
                platform=platform,
                action=action,
                task_id=tid,
                fetch_count=args.fetch_count,
                interval_minutes=args.interval_minutes,
            )
        )
        print(f"[{platform}] 已提交 task_id={tid} keyword={kw!r}")

    if not probes:
        print("无任务提交成功，退出")
        return 1

    if args.mode == "direct" and args.execute_once:
        print("\n>>> direct: 立即执行一轮 <<<")
        for probe in probes:
            try:
                meta = execute_once_direct(probe.task_id, api_key)
                probe.last_run_meta = meta
                probe.last_pages_fetched = int(meta.get("pages_fetched") or 0)
                print(
                    f"  [{probe.platform}] task={probe.task_id} "
                    f"pages={probe.last_pages_fetched} "
                    f"records={meta.get('records_returned')} "
                    f"stop_reason={meta.get('stop_reason')}"
                )
            except Exception as e:
                probe.issues.append(f"执行失败: {e}")
                print(f"  [{probe.platform}] 执行失败: {e}")

    monitor(
        probes,
        client=client,
        poll_seconds=args.poll_seconds,
        duration_seconds=duration,
        status_fn=status_fn,
        collect_results=client is not None,
    )

    print("\n=== 汇总 ===")
    all_ok = True
    for probe in probes:
        report = probe.analyze()
        all_ok = all_ok and report["ok"]
        print(json.dumps(report, ensure_ascii=False, indent=2))

    if not args.no_cancel:
        print("\n>>> 取消测试任务 <<<")
        for probe in probes:
            try:
                cancel_fn(probe.task_id)
                print(f"  [{probe.platform}] task={probe.task_id} cancelled")
            except Exception as e:
                print(f"  [{probe.platform}] 取消失败: {e}")

    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

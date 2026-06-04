"""埋点写入与看板聚合（Phase 1：页面浏览 / 任务创建 / 通知开关 / 用户维度）。"""

from __future__ import annotations

import datetime as dt
import json
import logging
import uuid
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from social_platform.schemas.analytics_events import ALLOWED_ANALYTICS_EVENTS
from social_platform.schedule_time import schedule_now_wall_naive

logger = logging.getLogger(__name__)

RangeKey = str  # day | week | month


def _parse_event_ts(raw: Optional[str]) -> dt.datetime:
    if raw:
        s = raw.strip()
        if s.endswith("Z"):
            s = s[:-1]
        for fmt in (
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
        ):
            try:
                return dt.datetime.strptime(s[:26], fmt)
            except ValueError:
                continue
    return schedule_now_wall_naive()


def _range_bounds(range_key: str, now: Optional[dt.datetime] = None) -> tuple[dt.datetime, dt.datetime]:
    now = now or schedule_now_wall_naive()
    end = now
    if range_key == "day":
        start = dt.datetime(now.year, now.month, now.day)
    elif range_key == "week":
        start = now - dt.timedelta(days=now.weekday())
        start = dt.datetime(start.year, start.month, start.day)
    else:
        start = dt.datetime(now.year, now.month, 1)
    return start, end


def _prev_range_bounds(range_key: str, now: Optional[dt.datetime] = None) -> tuple[dt.datetime, dt.datetime]:
    now = now or schedule_now_wall_naive()
    cur_start, _ = _range_bounds(range_key, now)
    if range_key == "day":
        prev_end = cur_start - dt.timedelta(seconds=1)
        prev_start = dt.datetime(prev_end.year, prev_end.month, prev_end.day)
    elif range_key == "week":
        prev_end = cur_start - dt.timedelta(seconds=1)
        prev_start = prev_end - dt.timedelta(days=prev_end.weekday())
        prev_start = dt.datetime(prev_start.year, prev_start.month, prev_start.day)
    else:
        if cur_start.month == 1:
            prev_start = dt.datetime(cur_start.year - 1, 12, 1)
        else:
            prev_start = dt.datetime(cur_start.year, cur_start.month - 1, 1)
        prev_end = cur_start - dt.timedelta(seconds=1)
    return prev_start, prev_end


def _compare_label(range_key: str) -> str:
    if range_key == "day":
        return "较昨日"
    if range_key == "week":
        return "较上周"
    return "较上月"


def _pct(num: float, den: float) -> str:
    if den <= 0:
        return "-"
    return f"{num / den * 100:.1f}%"


def _fmt_int(n: int | float) -> str | int:
    val = int(n)
    if val >= 1000:
        return f"{val:,}"
    return val


def ingest_events(db: Session, events: list[dict[str, Any]]) -> int:
    accepted = 0
    for item in events:
        name = str(item.get("event") or "").strip()
        if name not in ALLOWED_ANALYTICS_EVENTS:
            continue
        props = item.get("properties") if isinstance(item.get("properties"), dict) else {}
        user_id = str(item.get("user_id") or props.get("user_id") or "").strip() or None
        ts = _parse_event_ts(item.get("ts") or props.get("ts"))

        if name == "page_view":
            _insert_page_view(db, user_id, props, ts)
            if user_id:
                _touch_user(db, user_id, props, ts)
            accepted += 1
        elif name == "task_create":
            if not user_id:
                continue
            _upsert_task(db, user_id, props, ts)
            _touch_user(db, user_id, props, ts)
            accepted += 1
        elif name == "notify_toggle":
            if not user_id:
                continue
            _insert_notify_toggle(db, user_id, props, ts)
            _touch_user(db, user_id, props, ts)
            accepted += 1
        elif name == "user_profile":
            if not user_id:
                continue
            _upsert_user_profile(db, user_id, props, ts)
            accepted += 1
    if accepted:
        db.commit()
    return accepted


def _insert_page_view(
    db: Session,
    user_id: Optional[str],
    props: dict[str, Any],
    ts: dt.datetime,
) -> None:
    db.execute(
        text(
            """
            INSERT INTO analytics_page_view
              (user_id, page_name, source, device_type, plugin_version, visited_at)
            VALUES
              (:user_id, :page_name, :source, :device_type, :plugin_version, :visited_at)
            """
        ),
        {
            "user_id": user_id,
            "page_name": str(props.get("page_name") or props.get("page") or "unknown")[:64],
            "source": _opt_str(props.get("source"), 128),
            "device_type": _opt_str(props.get("device_type"), 16),
            "plugin_version": _opt_str(props.get("plugin_version"), 32),
            "visited_at": ts,
        },
    )


def _insert_notify_toggle(
    db: Session,
    user_id: str,
    props: dict[str, Any],
    ts: dt.datetime,
) -> None:
    enabled_raw = props.get("enabled")
    if enabled_raw is None:
        enabled_raw = props.get("notify_enabled")
    enabled = 1 if enabled_raw in (True, 1, "1", "true", "开", "on") else 0
    db.execute(
        text(
            """
            INSERT INTO analytics_notify_toggle (user_id, task_id, enabled, toggled_at)
            VALUES (:user_id, :task_id, :enabled, :toggled_at)
            """
        ),
        {
            "user_id": user_id[:64],
            "task_id": _opt_str(props.get("task_id"), 64),
            "enabled": enabled,
            "toggled_at": ts,
        },
    )


def _upsert_task(
    db: Session,
    user_id: str,
    props: dict[str, Any],
    ts: dt.datetime,
) -> None:
    task_id = str(props.get("task_id") or "").strip()
    if not task_id:
        task_id = f"local-{uuid.uuid4().hex[:12]}"
    task_type = str(props.get("task_type") or "定时任务")[:32]
    keyword_count = int(props.get("keyword_count") or 0)
    platforms = props.get("platforms")
    if isinstance(platforms, str):
        try:
            platforms = json.loads(platforms)
        except json.JSONDecodeError:
            platforms = [platforms]
    if not isinstance(platforms, list):
        platforms = []
    notify_enabled = 1 if props.get("notify_enabled") in (True, 1, "1", "true", "开", "on") else 0
    status = str(props.get("status") or "运行中")[:32]
    db.execute(
        text(
            """
            INSERT INTO analytics_task
              (task_id, user_id, task_type, keyword_count, platforms_json, status, notify_enabled, created_at)
            VALUES
              (:task_id, :user_id, :task_type, :keyword_count, :platforms_json, :status, :notify_enabled, :created_at)
            ON DUPLICATE KEY UPDATE
              task_type = VALUES(task_type),
              keyword_count = VALUES(keyword_count),
              platforms_json = VALUES(platforms_json),
              status = VALUES(status),
              notify_enabled = VALUES(notify_enabled),
              updated_at = CURRENT_TIMESTAMP
            """
        ),
        {
            "task_id": task_id[:64],
            "user_id": user_id[:64],
            "task_type": task_type,
            "keyword_count": keyword_count,
            "platforms_json": json.dumps(platforms, ensure_ascii=False),
            "status": status,
            "notify_enabled": notify_enabled,
            "created_at": ts,
        },
    )


def _upsert_user_profile(
    db: Session,
    user_id: str,
    props: dict[str, Any],
    ts: dt.datetime,
) -> None:
    db.execute(
        text(
            """
            INSERT INTO analytics_user
              (user_id, feishu_id, phone, plugin_version, device_type, active_hours, first_use_at, last_active_at)
            VALUES
              (:user_id, :feishu_id, :phone, :plugin_version, :device_type, :active_hours, :first_use_at, :last_active_at)
            ON DUPLICATE KEY UPDATE
              feishu_id = COALESCE(VALUES(feishu_id), feishu_id),
              phone = COALESCE(VALUES(phone), phone),
              plugin_version = COALESCE(VALUES(plugin_version), plugin_version),
              device_type = COALESCE(VALUES(device_type), device_type),
              active_hours = COALESCE(VALUES(active_hours), active_hours),
              first_use_at = COALESCE(first_use_at, VALUES(first_use_at)),
              last_active_at = VALUES(last_active_at),
              updated_at = CURRENT_TIMESTAMP
            """
        ),
        {
            "user_id": user_id[:64],
            "feishu_id": _opt_str(props.get("feishu_id"), 128),
            "phone": _opt_str(props.get("phone"), 32),
            "plugin_version": _opt_str(props.get("plugin_version"), 32),
            "device_type": _opt_str(props.get("device_type"), 16),
            "active_hours": _opt_str(props.get("active_hours"), 64),
            "first_use_at": ts,
            "last_active_at": ts,
        },
    )


def _touch_user(
    db: Session,
    user_id: str,
    props: dict[str, Any],
    ts: dt.datetime,
) -> None:
    db.execute(
        text(
            """
            INSERT INTO analytics_user (user_id, plugin_version, device_type, first_use_at, last_active_at)
            VALUES (:user_id, :plugin_version, :device_type, :ts, :ts)
            ON DUPLICATE KEY UPDATE
              plugin_version = COALESCE(VALUES(plugin_version), plugin_version),
              device_type = COALESCE(VALUES(device_type), device_type),
              last_active_at = VALUES(last_active_at),
              updated_at = CURRENT_TIMESTAMP
            """
        ),
        {
            "user_id": user_id[:64],
            "plugin_version": _opt_str(props.get("plugin_version"), 32),
            "device_type": _opt_str(props.get("device_type"), 16),
            "ts": ts,
        },
    )


def _opt_str(val: Any, max_len: int) -> Optional[str]:
    if val is None:
        return None
    s = str(val).strip()
    if not s:
        return None
    return s[:max_len]


def get_overview(db: Session, range_key: str = "month") -> dict[str, Any]:
    start, end = _range_bounds(range_key)
    prev_start, prev_end = _prev_range_bounds(range_key)
    compare = _compare_label(range_key)

    active_tasks = _scalar(
        db,
        """
        SELECT COUNT(DISTINCT task_id) FROM analytics_exec_run
        WHERE started_at >= :start AND started_at <= :end
        """,
        start,
        end,
    )
    if active_tasks == 0:
        active_tasks = _scalar(
            db,
            """
            SELECT COUNT(*) FROM analytics_task
            WHERE created_at >= :start AND created_at <= :end
            """,
            start,
            end,
        )

    exec_total = _scalar(
        db,
        "SELECT COUNT(*) FROM analytics_exec_run WHERE started_at >= :start AND started_at <= :end",
        start,
        end,
    )
    exec_ok = _scalar(
        db,
        """
        SELECT COUNT(*) FROM analytics_exec_run
        WHERE started_at >= :start AND started_at <= :end AND result = '成功'
        """,
        start,
        end,
    )

    api_total = _scalar(
        db,
        "SELECT COUNT(*) FROM analytics_api_call WHERE called_at >= :start AND called_at <= :end",
        start,
        end,
    )
    api_ok = _scalar(
        db,
        """
        SELECT COUNT(*) FROM analytics_api_call
        WHERE called_at >= :start AND called_at <= :end AND result = '成功'
        """,
        start,
        end,
    )

    points = _scalar(
        db,
        """
        SELECT COALESCE(SUM(amount), 0) FROM analytics_point_consume
        WHERE consumed_at >= :start AND consumed_at <= :end
        """,
        start,
        end,
    )

    active_users = _scalar(
        db,
        """
        SELECT COUNT(DISTINCT user_id) FROM (
          SELECT user_id FROM analytics_exec_run
          WHERE user_id IS NOT NULL AND started_at >= :start AND started_at <= :end
          UNION
          SELECT user_id FROM analytics_task
          WHERE created_at >= :start AND created_at <= :end
          UNION
          SELECT user_id FROM analytics_page_view
          WHERE user_id IS NOT NULL AND visited_at >= :start AND visited_at <= :end
        ) t
        """,
        start,
        end,
    )

    task_total = _scalar_simple(db, "SELECT COUNT(*) FROM analytics_task")
    avg_tasks = round(task_total / active_users, 1) if active_users else 0

    push_send_ok = _scalar(
        db,
        """
        SELECT COUNT(*) FROM analytics_push_log
        WHERE send_at >= :start AND send_at <= :end AND send_result = '成功'
        """,
        start,
        end,
    )
    push_cb_ok = _scalar(
        db,
        """
        SELECT COUNT(*) FROM analytics_push_log
        WHERE send_at >= :start AND send_at <= :end
          AND send_result = '成功' AND callback_result = '成功'
        """,
        start,
        end,
    )

    prev_active_users = _scalar(
        db,
        """
        SELECT COUNT(DISTINCT user_id) FROM (
          SELECT user_id FROM analytics_page_view
          WHERE user_id IS NOT NULL AND visited_at >= :start AND visited_at <= :end
          UNION
          SELECT user_id FROM analytics_task
          WHERE created_at >= :start AND created_at <= :end
        ) t
        """,
        prev_start,
        prev_end,
    )
    retention = "-"
    if prev_active_users > 0:
        retained = _scalar(
            db,
            """
            SELECT COUNT(*) FROM (
              SELECT DISTINCT p.user_id FROM analytics_page_view p
              WHERE p.user_id IS NOT NULL AND p.visited_at >= :cur_start AND p.visited_at <= :cur_end
                AND p.user_id IN (
                  SELECT DISTINCT user_id FROM analytics_page_view
                  WHERE user_id IS NOT NULL AND visited_at >= :prev_start AND visited_at <= :prev_end
                  UNION
                  SELECT DISTINCT user_id FROM analytics_task
                  WHERE created_at >= :prev_start AND created_at <= :prev_end
                )
            ) x
            """,
            start,
            end,
            prev_start,
            prev_end,
        )
        retention = _pct(retained, prev_active_users)

    new_users = _scalar(
        db,
        """
        SELECT COUNT(*) FROM analytics_user
        WHERE first_use_at >= :start AND first_use_at <= :end
        """,
        start,
        end,
    )
    new_users_label = (
        f"今日新增: {new_users}"
        if range_key == "day"
        else (f"本周新增: {new_users}" if range_key == "week" else f"本月新增: {new_users}")
    )

    kpis = {
        "activeTasks": _fmt_int(active_tasks),
        "execRate": _pct(exec_ok, exec_total) if exec_total else "-",
        "apiRate": _pct(api_ok, api_total) if api_total else "-",
        "points": _fmt_int(points) if points else (0 if range_key == "day" else "0"),
        "retention": retention,
        "avgTasks": str(avg_tasks) if avg_tasks else "-",
        "pushRate": _pct(push_cb_ok, push_send_ok) if push_send_ok else "-",
        "activeUsers": _fmt_int(active_users),
        "compare": compare,
        "newUsers": new_users_label,
    }

    charts = {
        "trend": _build_trend_chart(db, end),
        "taskStatus": _build_task_status_chart(db, start, end),
        "platformApi": _build_platform_api_chart(db, start, end),
        "topUsers": _build_top_users_chart(db, start, end),
    }
    funnel = _build_funnel(db, end)

    has_data = (
        active_users > 0
        or task_total > 0
        or _scalar(
            db,
            "SELECT COUNT(*) FROM analytics_page_view WHERE visited_at >= :start AND visited_at <= :end",
            start,
            end,
        )
        > 0
    )

    return {
        "range": range_key,
        "kpis": kpis,
        "charts": charts,
        "funnel": funnel,
        "empty": not has_data,
    }


def _scalar_simple(db: Session, sql: str) -> int:
    val = db.execute(text(sql)).scalar()
    return int(val or 0)


def _scalar(
    db: Session,
    sql: str,
    start: dt.datetime,
    end: dt.datetime,
    prev_start: Optional[dt.datetime] = None,
    prev_end: Optional[dt.datetime] = None,
) -> int:
    params: dict[str, Any] = {"start": start, "end": end}
    if prev_start is not None:
        params["prev_start"] = prev_start
    if prev_end is not None:
        params["prev_end"] = prev_end
    if ":cur_start" in sql:
        params["cur_start"] = start
        params["cur_end"] = end
    val = db.execute(text(sql), params).scalar()
    return int(val or 0)


def _build_trend_chart(db: Session, end: dt.datetime) -> dict[str, Any]:
    labels: list[str] = []
    active_users: list[int] = []
    exec_counts: list[int] = []
    for i in range(29, -1, -1):
        day = end - dt.timedelta(days=i)
        day_start = dt.datetime(day.year, day.month, day.day)
        day_end = day_start + dt.timedelta(days=1) - dt.timedelta(seconds=1)
        labels.append(f"{day.month}/{day.day}")
        active_users.append(
            _scalar(
                db,
                """
                SELECT COUNT(DISTINCT user_id) FROM analytics_page_view
                WHERE user_id IS NOT NULL AND visited_at >= :start AND visited_at <= :end
                """,
                day_start,
                day_end,
            )
        )
        exec_counts.append(
            _scalar(
                db,
                """
                SELECT COUNT(*) FROM analytics_task
                WHERE created_at >= :start AND created_at <= :end
                """,
                day_start,
                day_end,
            )
        )
    return {"labels": labels, "activeUsers": active_users, "execCounts": exec_counts}


def _build_task_status_chart(db: Session, start: dt.datetime, end: dt.datetime) -> list[dict[str, Any]]:
    rows = db.execute(
        text(
            """
            SELECT status, COUNT(*) AS cnt FROM analytics_task
            WHERE created_at >= :start AND created_at <= :end
            GROUP BY status
            """
        ),
        {"start": start, "end": end},
    ).mappings().all()
    if not rows:
        return [
            {"name": "运行中", "value": 0},
            {"name": "已停止", "value": 0},
            {"name": "已完成", "value": 0},
        ]
    return [{"name": str(r["status"]), "value": int(r["cnt"])} for r in rows]


def _build_platform_api_chart(db: Session, start: dt.datetime, end: dt.datetime) -> dict[str, Any]:
    rows = db.execute(
        text(
            """
            SELECT platform, COUNT(*) AS cnt FROM analytics_api_call
            WHERE called_at >= :start AND called_at <= :end AND platform IS NOT NULL
            GROUP BY platform ORDER BY cnt DESC LIMIT 7
            """
        ),
        {"start": start, "end": end},
    ).mappings().all()
    return {
        "labels": [str(r["platform"]) for r in rows],
        "values": [int(r["cnt"]) for r in rows],
    }


def _build_top_users_chart(db: Session, start: dt.datetime, end: dt.datetime) -> dict[str, Any]:
    rows = db.execute(
        text(
            """
            SELECT u.user_id, COALESCE(NULLIF(u.phone, ''), u.user_id) AS label,
                   COUNT(t.task_id) AS cnt
            FROM analytics_user u
            LEFT JOIN analytics_task t ON t.user_id = u.user_id
              AND t.created_at >= :start AND t.created_at <= :end
            GROUP BY u.user_id, u.phone
            ORDER BY cnt DESC, u.last_active_at DESC
            LIMIT 5
            """
        ),
        {"start": start, "end": end},
    ).mappings().all()
    return {
        "labels": [str(r["label"])[:16] for r in rows],
        "values": [int(r["cnt"]) for r in rows],
    }


def _build_funnel(db: Session, end: dt.datetime) -> dict[str, Any]:
    start = end - dt.timedelta(days=6)
    home = _scalar(
        db,
        """
        SELECT COUNT(*) FROM analytics_page_view
        WHERE page_name IN ('首页', '任务列表', 'home', 'tasks')
          AND visited_at >= :start AND visited_at <= :end
        """,
        start,
        end,
    )
    login = _scalar(
        db,
        """
        SELECT COUNT(*) FROM analytics_page_view
        WHERE page_name IN ('登录', '登录注册页', 'login')
          AND visited_at >= :start AND visited_at <= :end
        """,
        start,
        end,
    )
    create = _scalar(
        db,
        """
        SELECT COUNT(*) FROM analytics_page_view
        WHERE page_name IN ('新建任务', '任务创建', 'task_create')
          AND visited_at >= :start AND visited_at <= :end
        """,
        start,
        end,
    )
    success = _scalar(
        db,
        """
        SELECT COUNT(*) FROM analytics_task
        WHERE created_at >= :start AND created_at <= :end
        """,
        start,
        end,
    )
    steps = [
        {"label": "首页访问", "value": home, "note": "近7天页面浏览", "loss": ""},
        {"label": "登录注册页", "value": login, "note": "进入登录流程", "loss": ""},
        {"label": "新建任务页", "value": create, "note": "打开创建页", "loss": ""},
        {"label": "创建成功", "value": success, "note": "任务创建埋点", "loss": ""},
    ]
    conversion = _pct(success, home) if home else "0%"
    return {
        "steps": steps,
        "losses": [],
        "conversionRate": conversion,
        "rangeLabel": "近7天",
    }


def write_exec_run_start(
    db: Session,
    *,
    exec_id: str,
    task_id: str,
    user_id: Optional[str],
    task_type: Optional[str],
    run_no: Optional[int],
) -> None:
    """记录执行开始（Phase 2）。"""
    db.execute(
        text(
            """
            INSERT INTO analytics_exec_run
              (exec_id, task_id, user_id, task_type, run_no, started_at, points, collect_count)
            VALUES
              (:exec_id, :task_id, :user_id, :task_type, :run_no, :started_at, 0, 0)
            """
        ),
        {
            "exec_id": str(exec_id)[:64],
            "task_id": str(task_id)[:64],
            "user_id": _opt_str(user_id, 64),
            "task_type": _opt_str(task_type, 32),
            "run_no": run_no,
            "started_at": schedule_now_wall_naive(),
        },
    )
    db.commit()


def write_exec_run_end(
    db: Session,
    *,
    exec_id: str,
    result: str,
    fail_reason: Optional[str] = None,
    points: int = 0,
    collect_count: int = 0,
) -> None:
    """更新执行结束（Phase 2）。"""
    now = schedule_now_wall_naive()
    db.execute(
        text(
            """
            UPDATE analytics_exec_run
            SET ended_at = :ended_at,
                duration_ms = TIMESTAMPDIFF(MICROSECOND, started_at, :ended_at) DIV 1000,
                result = :result,
                fail_reason = :fail_reason,
                points = :points,
                collect_count = :collect_count
            WHERE exec_id = :exec_id
            """
        ),
        {
            "exec_id": str(exec_id)[:64],
            "ended_at": now,
            "result": str(result)[:16],
            "fail_reason": _opt_str(fail_reason, 255),
            "points": int(points),
            "collect_count": int(collect_count),
        },
    )
    db.commit()


def write_api_call(
    db: Session,
    *,
    request_id: str,
    task_id: Optional[str],
    exec_id: Optional[str],
    platform: Optional[str],
    result: str,
    error_code: Optional[str] = None,
    latency_ms: Optional[int] = None,
) -> None:
    """记录 API 调用（Phase 2）。"""
    db.execute(
        text(
            """
            INSERT INTO analytics_api_call
              (request_id, task_id, exec_id, platform, called_at, result, error_code, latency_ms)
            VALUES
              (:request_id, :task_id, :exec_id, :platform, :called_at, :result, :error_code, :latency_ms)
            """
        ),
        {
            "request_id": str(request_id)[:64],
            "task_id": _opt_str(task_id, 64),
            "exec_id": _opt_str(exec_id, 64),
            "platform": _opt_str(platform, 64),
            "called_at": schedule_now_wall_naive(),
            "result": str(result)[:16],
            "error_code": _opt_str(error_code, 32),
            "latency_ms": latency_ms,
        },
    )
    db.commit()


def write_point_consume(
    db: Session,
    *,
    consume_id: str,
    user_id: str,
    task_id: Optional[str],
    exec_id: Optional[str],
    platform: Optional[str],
    amount: int,
    balance: Optional[int],
) -> None:
    """记录点数消耗（Phase 2）。"""
    db.execute(
        text(
            """
            INSERT INTO analytics_point_consume
              (consume_id, user_id, task_id, exec_id, platform, amount, balance, consumed_at)
            VALUES
              (:consume_id, :user_id, :task_id, :exec_id, :platform, :amount, :balance, :consumed_at)
            """
        ),
        {
            "consume_id": str(consume_id)[:64],
            "user_id": str(user_id)[:64],
            "task_id": _opt_str(task_id, 64),
            "exec_id": _opt_str(exec_id, 64),
            "platform": _opt_str(platform, 64),
            "amount": int(amount),
            "balance": balance,
            "consumed_at": schedule_now_wall_naive(),
        },
    )
    db.commit()


def get_exec_runs(db: Session, range_key: str = "day") -> dict[str, Any]:
    """执行监控页数据（Phase 2）。"""
    start, end = _range_bounds(range_key)
    
    total = _scalar(
        db,
        "SELECT COUNT(*) FROM analytics_exec_run WHERE started_at >= :start AND started_at <= :end",
        start,
        end,
    )
    success = _scalar(
        db,
        """
        SELECT COUNT(*) FROM analytics_exec_run
        WHERE started_at >= :start AND started_at <= :end AND result = '成功'
        """,
        start,
        end,
    )
    
    avg_duration = db.execute(
        text(
            """
            SELECT COALESCE(AVG(duration_ms), 0) FROM analytics_exec_run
            WHERE started_at >= :start AND started_at <= :end AND duration_ms IS NOT NULL
            """
        ),
        {"start": start, "end": end},
    ).scalar()
    
    rows = db.execute(
        text(
            """
            SELECT exec_id, task_id, user_id, task_type, started_at, ended_at,
                   duration_ms, result, fail_reason, points, collect_count
            FROM analytics_exec_run
            WHERE started_at >= :start AND started_at <= :end
            ORDER BY started_at DESC
            LIMIT 100
            """
        ),
        {"start": start, "end": end},
    ).mappings().all()
    
    records = []
    for r in rows:
        records.append({
            "execId": str(r["exec_id"]),
            "taskId": str(r["task_id"]),
            "userId": str(r["user_id"] or ""),
            "taskType": str(r["task_type"] or ""),
            "startedAt": r["started_at"].isoformat() if r["started_at"] else "",
            "endedAt": r["ended_at"].isoformat() if r["ended_at"] else "",
            "durationMs": int(r["duration_ms"] or 0),
            "result": str(r["result"] or ""),
            "failReason": str(r["fail_reason"] or ""),
            "points": int(r["points"] or 0),
            "collectCount": int(r["collect_count"] or 0),
        })
    
    return {
        "range": range_key,
        "total": total,
        "success": success,
        "successRate": _pct(success, total) if total else "-",
        "avgDurationMs": int(avg_duration or 0),
        "records": records,
    }


def get_api_calls(db: Session, range_key: str = "day") -> dict[str, Any]:
    """API 监控页数据（Phase 2）。"""
    start, end = _range_bounds(range_key)
    
    total = _scalar(
        db,
        "SELECT COUNT(*) FROM analytics_api_call WHERE called_at >= :start AND called_at <= :end",
        start,
        end,
    )
    success = _scalar(
        db,
        """
        SELECT COUNT(*) FROM analytics_api_call
        WHERE called_at >= :start AND called_at <= :end AND result = '成功'
        """,
        start,
        end,
    )
    
    avg_latency = db.execute(
        text(
            """
            SELECT COALESCE(AVG(latency_ms), 0) FROM analytics_api_call
            WHERE called_at >= :start AND called_at <= :end AND latency_ms IS NOT NULL
            """
        ),
        {"start": start, "end": end},
    ).scalar()
    
    platform_rows = db.execute(
        text(
            """
            SELECT platform, COUNT(*) AS cnt,
                   SUM(CASE WHEN result = '成功' THEN 1 ELSE 0 END) AS success_cnt
            FROM analytics_api_call
            WHERE called_at >= :start AND called_at <= :end AND platform IS NOT NULL
            GROUP BY platform
            ORDER BY cnt DESC
            LIMIT 10
            """
        ),
        {"start": start, "end": end},
    ).mappings().all()
    
    platform_stats = []
    for p in platform_rows:
        cnt = int(p["cnt"] or 0)
        success_cnt = int(p["success_cnt"] or 0)
        platform_stats.append({
            "platform": str(p["platform"]),
            "total": cnt,
            "success": success_cnt,
            "successRate": _pct(success_cnt, cnt) if cnt else "-",
        })
    
    rows = db.execute(
        text(
            """
            SELECT request_id, task_id, exec_id, platform, called_at,
                   result, error_code, latency_ms
            FROM analytics_api_call
            WHERE called_at >= :start AND called_at <= :end
            ORDER BY called_at DESC
            LIMIT 100
            """
        ),
        {"start": start, "end": end},
    ).mappings().all()
    
    records = []
    for r in rows:
        records.append({
            "requestId": str(r["request_id"]),
            "taskId": str(r["task_id"] or ""),
            "execId": str(r["exec_id"] or ""),
            "platform": str(r["platform"] or ""),
            "calledAt": r["called_at"].isoformat() if r["called_at"] else "",
            "result": str(r["result"] or ""),
            "errorCode": str(r["error_code"] or ""),
            "latencyMs": int(r["latency_ms"] or 0),
        })
    
    return {
        "range": range_key,
        "total": total,
        "success": success,
        "successRate": _pct(success, total) if total else "-",
        "avgLatencyMs": int(avg_latency or 0),
        "platformStats": platform_stats,
        "records": records,
    }


def write_push_log(
    db: Session,
    *,
    push_id: str,
    task_id: Optional[str],
    user_id: Optional[str],
    webhook: Optional[str],
    send_result: str,
    new_data_count: int = 0,
    error_code: Optional[str] = None,
) -> None:
    """记录推送发送（Phase 3）。"""
    db.execute(
        text(
            """
            INSERT INTO analytics_push_log
              (push_id, task_id, user_id, webhook, send_at, send_result, new_data_count, error_code, retry_count)
            VALUES
              (:push_id, :task_id, :user_id, :webhook, :send_at, :send_result, :new_data_count, :error_code, 0)
            """
        ),
        {
            "push_id": str(push_id)[:64],
            "task_id": _opt_str(task_id, 64),
            "user_id": _opt_str(user_id, 64),
            "webhook": _opt_str(webhook, 512),
            "send_at": schedule_now_wall_naive(),
            "send_result": str(send_result)[:16],
            "new_data_count": int(new_data_count),
            "error_code": _opt_str(error_code, 32),
        },
    )
    db.commit()


def update_push_callback(
    db: Session,
    *,
    push_id: str,
    callback_result: str,
) -> None:
    """更新推送回调结果（Phase 3）。"""
    db.execute(
        text(
            """
            UPDATE analytics_push_log
            SET callback_at = :callback_at,
                callback_result = :callback_result
            WHERE push_id = :push_id
            """
        ),
        {
            "push_id": str(push_id)[:64],
            "callback_at": schedule_now_wall_naive(),
            "callback_result": str(callback_result)[:16],
        },
    )
    db.commit()


def get_push_logs(db: Session, range_key: str = "day") -> dict[str, Any]:
    """推送监控页数据（Phase 3）。"""
    start, end = _range_bounds(range_key)
    
    total = _scalar(
        db,
        "SELECT COUNT(*) FROM analytics_push_log WHERE send_at >= :start AND send_at <= :end",
        start,
        end,
    )
    send_success = _scalar(
        db,
        """
        SELECT COUNT(*) FROM analytics_push_log
        WHERE send_at >= :start AND send_at <= :end AND send_result = '成功'
        """,
        start,
        end,
    )
    callback_success = _scalar(
        db,
        """
        SELECT COUNT(*) FROM analytics_push_log
        WHERE send_at >= :start AND send_at <= :end
          AND send_result = '成功' AND callback_result = '成功'
        """,
        start,
        end,
    )
    
    notify_on = _scalar(
        db,
        """
        SELECT COUNT(*) FROM analytics_notify_toggle
        WHERE toggled_at >= :start AND toggled_at <= :end AND enabled = 1
        """,
        start,
        end,
    )
    notify_off = _scalar(
        db,
        """
        SELECT COUNT(*) FROM analytics_notify_toggle
        WHERE toggled_at >= :start AND toggled_at <= :end AND enabled = 0
        """,
        start,
        end,
    )
    
    rows = db.execute(
        text(
            """
            SELECT push_id, task_id, user_id, webhook, send_at, send_result,
                   callback_at, callback_result, new_data_count, error_code, retry_count
            FROM analytics_push_log
            WHERE send_at >= :start AND send_at <= :end
            ORDER BY send_at DESC
            LIMIT 100
            """
        ),
        {"start": start, "end": end},
    ).mappings().all()
    
    records = []
    for r in rows:
        records.append({
            "pushId": str(r["push_id"]),
            "taskId": str(r["task_id"] or ""),
            "userId": str(r["user_id"] or ""),
            "webhook": str(r["webhook"] or ""),
            "sendAt": r["send_at"].isoformat() if r["send_at"] else "",
            "sendResult": str(r["send_result"] or ""),
            "callbackAt": r["callback_at"].isoformat() if r["callback_at"] else "",
            "callbackResult": str(r["callback_result"] or ""),
            "newDataCount": int(r["new_data_count"] or 0),
            "errorCode": str(r["error_code"] or ""),
            "retryCount": int(r["retry_count"] or 0),
        })
    
    return {
        "range": range_key,
        "total": total,
        "sendSuccess": send_success,
        "callbackSuccess": callback_success,
        "deliveryRate": _pct(callback_success, send_success) if send_success else "-",
        "notifyOnCount": notify_on,
        "notifyOffCount": notify_off,
        "records": records,
    }


def get_users(db: Session, range_key: str = "month") -> dict[str, Any]:
    """用户管理页数据（Phase 3）。"""
    start, end = _range_bounds(range_key)
    
    total_users = _scalar_simple(db, "SELECT COUNT(*) FROM analytics_user")
    active_users = _scalar(
        db,
        """
        SELECT COUNT(DISTINCT user_id) FROM analytics_user
        WHERE last_active_at >= :start AND last_active_at <= :end
        """,
        start,
        end,
    )
    new_users = _scalar(
        db,
        """
        SELECT COUNT(*) FROM analytics_user
        WHERE first_use_at >= :start AND first_use_at <= :end
        """,
        start,
        end,
    )
    
    prev_start, prev_end = _prev_range_bounds(range_key)
    prev_active = _scalar(
        db,
        """
        SELECT COUNT(DISTINCT user_id) FROM analytics_user
        WHERE last_active_at >= :start AND last_active_at <= :end
        """,
        prev_start,
        prev_end,
    )
    
    retention = "-"
    if prev_active > 0:
        retained = _scalar(
            db,
            """
            SELECT COUNT(DISTINCT u.user_id) FROM analytics_user u
            WHERE u.last_active_at >= :cur_start AND u.last_active_at <= :cur_end
              AND u.user_id IN (
                SELECT user_id FROM analytics_user
                WHERE last_active_at >= :prev_start AND last_active_at <= :prev_end
              )
            """,
            start,
            end,
            prev_start,
            prev_end,
        )
        retention = _pct(retained, prev_active)
    
    rows = db.execute(
        text(
            """
            SELECT u.user_id, u.feishu_id, u.phone, u.device_type, u.plugin_version,
                   u.remark, u.first_use_at, u.last_active_at, u.active_hours,
                   COUNT(DISTINCT t.task_id) AS task_count,
                   COALESCE(SUM(p.amount), 0) AS points_consumed
            FROM analytics_user u
            LEFT JOIN analytics_task t ON t.user_id = u.user_id
            LEFT JOIN analytics_point_consume p ON p.user_id = u.user_id
              AND p.consumed_at >= :start AND p.consumed_at <= :end
            GROUP BY u.user_id, u.feishu_id, u.phone, u.device_type, u.plugin_version,
                     u.remark, u.first_use_at, u.last_active_at, u.active_hours
            ORDER BY u.last_active_at DESC
            LIMIT 100
            """
        ),
        {"start": start, "end": end},
    ).mappings().all()
    
    records = []
    for r in rows:
        records.append({
            "userId": str(r["user_id"]),
            "feishuId": str(r["feishu_id"] or ""),
            "phone": str(r["phone"] or ""),
            "deviceType": str(r["device_type"] or ""),
            "pluginVersion": str(r["plugin_version"] or ""),
            "remark": str(r["remark"] or ""),
            "firstUseAt": r["first_use_at"].isoformat() if r["first_use_at"] else "",
            "lastActiveAt": r["last_active_at"].isoformat() if r["last_active_at"] else "",
            "activeHours": str(r["active_hours"] or ""),
            "taskCount": int(r["task_count"] or 0),
            "pointsConsumed": int(r["points_consumed"] or 0),
        })
    
    return {
        "range": range_key,
        "totalUsers": total_users,
        "activeUsers": active_users,
        "newUsers": new_users,
        "retention": retention,
        "records": records,
    }


def update_user_remark(db: Session, *, user_id: str, remark: str) -> None:
    """更新用户运营备注（Phase 3）。"""
    db.execute(
        text(
            """
            UPDATE analytics_user
            SET remark = :remark,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = :user_id
            """
        ),
        {
            "user_id": str(user_id)[:64],
            "remark": str(remark)[:255] if remark else None,
        },
    )
    db.commit()


def get_tasks(
    db: Session,
    *,
    page: int = 1,
    limit: int = 20,
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    created_start: Optional[str] = None,
    created_end: Optional[str] = None,
) -> dict[str, Any]:
    """任务管理页数据：直接读 feishu_async_tasks 表。"""
    from social_platform.models.async_task import AsyncTask
    from sqlalchemy import select, func, case

    conditions = []
    if status:
        conditions.append(f"status = :status")
    if keyword:
        conditions.append("(task_name LIKE :kw OR CAST(id AS CHAR) LIKE :kw OR user_id LIKE :kw)")
    if created_start:
        conditions.append("create_time >= :created_start")
    if created_end:
        conditions.append("create_time <= :created_end")

    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    params: dict[str, Any] = {}
    if status:
        params["status"] = status
    if keyword:
        params["kw"] = f"%{keyword}%"
    if created_start:
        params["created_start"] = created_start
    if created_end:
        params["created_end"] = created_end

    total = int(
        db.execute(
            text(f"SELECT COUNT(*) FROM feishu_async_tasks {where_clause}"),
            params,
        ).scalar() or 0
    )

    offset = (page - 1) * limit
    rows = db.execute(
        text(
            f"""
            SELECT id, user_id, task_name, status, action, body_json,
                   api_key, error_message, success_count, failed_count,
                   task_start_time, task_end_time, next_run_at,
                   interval_minutes, fetch_count, create_time, update_time
            FROM feishu_async_tasks
            {where_clause}
            ORDER BY id DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        {**params, "limit": limit, "offset": offset},
    ).mappings().all()

    _PLATFORM_MAP = {
        "douyin": "抖音",
        "xhs": "小红书",
        "wx": "视频号",
        "mp": "公众号",
    }

    def _platform_from_action(action: str) -> str:
        a = (action or "").lower()
        for key, label in _PLATFORM_MAP.items():
            if a.startswith(key) or f"-{key}-" in a or a.endswith(f"-{key}"):
                return label
        return action.split("-")[0] if action else ""

    def _status_label(s: str) -> str:
        return {
            "pending": "待执行",
            "running": "运行中",
            "success": "已完成",
            "failed": "已失败",
            "cancelled": "已取消",
        }.get(s, s)

    records = []
    for r in rows:
        body = r["body_json"] if isinstance(r["body_json"], dict) else {}
        keyword_val = body.get("keyword") or body.get("keywords") or body.get("q") or ""
        keywords = [keyword_val] if isinstance(keyword_val, str) and keyword_val else (keyword_val if isinstance(keyword_val, list) else [])
        platform = _platform_from_action(str(r["action"] or ""))
        records.append({
            "id": str(r["id"]),
            "taskName": str(r["task_name"] or ""),
            "status": _status_label(str(r["status"] or "")),
            "statusRaw": str(r["status"] or ""),
            "action": str(r["action"] or ""),
            "platform": platform,
            "keywords": keywords,
            "userId": str(r["user_id"] or ""),
            "intervalMinutes": int(r["interval_minutes"] or 60),
            "fetchCount": int(r["fetch_count"] or 100),
            "successCount": int(r["success_count"] or 0),
            "failedCount": int(r["failed_count"] or 0),
            "errorMessage": str(r["error_message"] or ""),
            "taskStartTime": r["task_start_time"].isoformat() if r["task_start_time"] else "",
            "taskEndTime": r["task_end_time"].isoformat() if r["task_end_time"] else "",
            "nextRunAt": r["next_run_at"].isoformat() if r["next_run_at"] else "",
            "createdAt": r["create_time"].isoformat() if r["create_time"] else "",
            "updatedAt": r["update_time"].isoformat() if r["update_time"] else "",
        })

    status_counts_rows = db.execute(
        text("SELECT status, COUNT(*) AS cnt FROM feishu_async_tasks GROUP BY status")
    ).mappings().all()
    status_counts: dict[str, int] = {r["status"]: int(r["cnt"]) for r in status_counts_rows}

    total_all = sum(status_counts.values())
    running = status_counts.get("running", 0) + status_counts.get("pending", 0)
    stopped = status_counts.get("cancelled", 0) + status_counts.get("failed", 0)
    completed = status_counts.get("success", 0)

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "records": records,
        "stats": {
            "total": total_all,
            "running": running,
            "stopped": stopped,
            "completed": completed,
        },
    }


def get_user_detail(db: Session, *, user_id: str) -> Optional[dict[str, Any]]:
    """用户详情（Phase 3）。"""
    user_row = db.execute(
        text(
            """
            SELECT user_id, feishu_id, phone, device_type, plugin_version,
                   remark, first_use_at, last_active_at, active_hours
            FROM analytics_user
            WHERE user_id = :user_id
            """
        ),
        {"user_id": str(user_id)[:64]},
    ).mappings().first()
    
    if not user_row:
        return None
    
    tasks = db.execute(
        text(
            """
            SELECT task_id, task_type, keyword_count, platforms_json, status, created_at
            FROM analytics_task
            WHERE user_id = :user_id
            ORDER BY created_at DESC
            LIMIT 20
            """
        ),
        {"user_id": str(user_id)[:64]},
    ).mappings().all()
    
    points = db.execute(
        text(
            """
            SELECT consume_id, task_id, platform, amount, balance, consumed_at
            FROM analytics_point_consume
            WHERE user_id = :user_id
            ORDER BY consumed_at DESC
            LIMIT 50
            """
        ),
        {"user_id": str(user_id)[:64]},
    ).mappings().all()
    
    uid = str(user_id)[:64]
    exec_count = int(
        db.execute(
            text("SELECT COUNT(*) FROM analytics_exec_run WHERE user_id = :user_id"),
            {"user_id": uid},
        ).scalar() or 0
    )
    
    exec_success = int(
        db.execute(
            text("SELECT COUNT(*) FROM analytics_exec_run WHERE user_id = :user_id AND result = '成功'"),
            {"user_id": uid},
        ).scalar() or 0
    )
    
    total_points = int(
        db.execute(
            text("SELECT COALESCE(SUM(amount), 0) FROM analytics_point_consume WHERE user_id = :user_id"),
            {"user_id": uid},
        ).scalar() or 0
    )
    
    return {
        "userId": str(user_row["user_id"]),
        "feishuId": str(user_row["feishu_id"] or ""),
        "phone": str(user_row["phone"] or ""),
        "deviceType": str(user_row["device_type"] or ""),
        "pluginVersion": str(user_row["plugin_version"] or ""),
        "remark": str(user_row["remark"] or ""),
        "firstUseAt": user_row["first_use_at"].isoformat() if user_row["first_use_at"] else "",
        "lastActiveAt": user_row["last_active_at"].isoformat() if user_row["last_active_at"] else "",
        "activeHours": str(user_row["active_hours"] or ""),
        "taskCount": len(tasks),
        "execCount": exec_count,
        "execSuccessRate": _pct(exec_success, exec_count) if exec_count else "-",
        "totalPoints": total_points,
        "tasks": [
            {
                "taskId": str(t["task_id"]),
                "taskType": str(t["task_type"] or ""),
                "keywordCount": int(t["keyword_count"] or 0),
                "platforms": t["platforms_json"] if isinstance(t["platforms_json"], list) else [],
                "status": str(t["status"] or ""),
                "createdAt": t["created_at"].isoformat() if t["created_at"] else "",
            }
            for t in tasks
        ],
        "points": [
            {
                "consumeId": str(p["consume_id"]),
                "taskId": str(p["task_id"] or ""),
                "platform": str(p["platform"] or ""),
                "amount": int(p["amount"] or 0),
                "balance": int(p["balance"] or 0),
                "consumedAt": p["consumed_at"].isoformat() if p["consumed_at"] else "",
            }
            for p in points
        ],
    }

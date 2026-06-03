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

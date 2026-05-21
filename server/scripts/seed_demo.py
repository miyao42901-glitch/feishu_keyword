#!/usr/bin/env python3
"""测试环境演示数据（可重复执行，先删演示 ID）。"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

_SERVER = Path(__file__).resolve().parents[1]
if str(_SERVER) not in sys.path:
    sys.path.insert(0, str(_SERVER))

from sqlalchemy import text

from app.db import engine

DEMO_PLAN_ID = 90001
DEMO_CONFIG_ID = 90001


def main() -> None:
    if engine is None:
        print("ERROR: DATABASE_URL 未配置", file=sys.stderr)
        sys.exit(1)

    config_json = {
        "taskName": "演示任务",
        "selectedSources": ["douyin"],
        "keywords": ["演示关键词"],
    }

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM feishu_task_configs WHERE id = :id"), {"id": DEMO_CONFIG_ID})
        conn.execute(text("DELETE FROM monitoring_plans WHERE id = :id"), {"id": DEMO_PLAN_ID})

        conn.execute(
            text(
                """
                INSERT INTO monitoring_plans (
                    id, plan_name, status, effective_time, created_at, updated_at
                ) VALUES (
                    :id, :name, 'active', :now, :now, :now
                )
                """
            ),
            {
                "id": DEMO_PLAN_ID,
                "name": "演示监控方案",
                "now": datetime.now(),
            },
        )

        conn.execute(
            text(
                """
                INSERT INTO feishu_task_configs (
                    id, plan_name, config_json, created_at, updated_at
                ) VALUES (
                    :id, :name, :cfg, :now, :now
                )
                """
            ),
            {
                "id": DEMO_CONFIG_ID,
                "name": "演示飞书任务",
                "cfg": json.dumps(config_json, ensure_ascii=False),
                "now": datetime.now(),
            },
        )

    print("seed_demo: monitoring_plans + feishu_task_configs inserted")
    print("admin login: admin / Admin123a (from migrations seed)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""创建 server ORM 表 + 执行 server/migrations/*.sql（sys_* RBAC）。"""

from __future__ import annotations

import sys
from pathlib import Path

_SERVER = Path(__file__).resolve().parents[1]
if str(_SERVER) not in sys.path:
    sys.path.insert(0, str(_SERVER))

from sqlalchemy import text

from app.db import engine
from app.models.base import Base
from app.models import tables  # noqa: F401


def _run_sql_files() -> None:
    mig_dir = _SERVER / "migrations"
    if not mig_dir.is_dir():
        return
    files = sorted(mig_dir.glob("*.sql"))
    with engine.begin() as conn:
        for path in files:
            sql = path.read_text(encoding="utf-8")
            for stmt in sql.split(";"):
                chunk = stmt.strip()
                if not chunk or chunk.startswith("--"):
                    continue
                if chunk.upper().startswith("DROP TABLE"):
                    continue
                conn.execute(text(chunk))
            print(f"applied: {path.name}")


def main() -> None:
    if engine is None:
        print("ERROR: DATABASE_URL 未配置", file=sys.stderr)
        sys.exit(1)
    Base.metadata.create_all(bind=engine, checkfirst=True)
    print("ORM tables: create_all done")
    _run_sql_files()
    print("init_schema: ok")


if __name__ == "__main__":
    main()

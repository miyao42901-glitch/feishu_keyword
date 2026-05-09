"""
确保存在 `feishu_task_configs` 表（CREATE TABLE IF NOT EXISTS）。

在 `server/` 目录执行：
    .\\.venv\\Scripts\\python scripts\\ensure_feishu_task_configs_table.py

依赖 `server/.env` 中的 `DATABASE_URL`。
"""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

_SERVER_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_SERVER_ROOT / ".env")

DDL = """
CREATE TABLE IF NOT EXISTS feishu_task_configs (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  plan_name VARCHAR(200) NULL COMMENT '方案名称（列表展示，可与 config_json 内冗余）',
  config_json LONGTEXT NOT NULL COMMENT '前端表单完整 JSON',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""


def main() -> None:
    import os

    url = os.getenv("DATABASE_URL")
    if not url or not url.strip():
        print("错误：未设置 DATABASE_URL，请配置 server/.env", file=sys.stderr)
        sys.exit(1)

    engine = create_engine(url, pool_pre_ping=True)
    try:
        with engine.begin() as conn:
            conn.execute(text(DDL))
    except Exception as exc:  # noqa: BLE001
        print(f"执行失败：{exc}", file=sys.stderr)
        sys.exit(1)

    print("feishu_task_configs 表已就绪（若已存在则跳过创建）。")


if __name__ == "__main__":
    main()

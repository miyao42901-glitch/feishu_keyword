"""
确保存在 `feishu_task_configs` 表（CREATE TABLE IF NOT EXISTS）。

在 `server/` 目录执行：
    .\\.venv\\Scripts\\python scripts\\ensure_feishu_task_configs_table.py

依赖仓根 `.env` / `.env.local` 中的 `DATABASE_URL`。
"""

from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect, text

_SERVER_ROOT = Path(__file__).resolve().parent.parent
if str(_SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(_SERVER_ROOT))

from app.env_loader import load_server_dotenv

load_server_dotenv()

DDL = """
CREATE TABLE IF NOT EXISTS feishu_task_configs (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  plan_name VARCHAR(200) NULL COMMENT '方案名称（列表展示，可与 config_json 内冗余）',
  owner_api_key VARCHAR(256) NULL COMMENT 'YDDM API Key，与请求头 X-Api-Key 一致，按账户隔离',
  config_json LONGTEXT NOT NULL COMMENT '前端表单完整 JSON',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_feishu_task_configs_owner (owner_api_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

ALTER_ADD_OWNER = """
ALTER TABLE feishu_task_configs
  ADD COLUMN owner_api_key VARCHAR(256) NULL
  COMMENT 'YDDM API Key，与请求头 X-Api-Key 一致，按账户隔离'
  AFTER plan_name
"""

ALTER_ADD_INDEX = """
ALTER TABLE feishu_task_configs
  ADD KEY idx_feishu_task_configs_owner (owner_api_key)
"""


def main() -> None:
    import os

    url = os.getenv("DATABASE_URL")
    if not url or not url.strip():
        print("错误：未设置 DATABASE_URL，请配置仓根 .env 或 .env.local", file=sys.stderr)
        sys.exit(1)

    engine = create_engine(url, pool_pre_ping=True)
    try:
        with engine.begin() as conn:
            conn.execute(text(DDL))
        insp = inspect(engine)
        if insp.has_table("feishu_task_configs"):
            col_names = {c["name"] for c in insp.get_columns("feishu_task_configs")}
            if "owner_api_key" not in col_names:
                with engine.begin() as conn:
                    conn.execute(text(ALTER_ADD_OWNER))
            insp_after = inspect(engine)
            idx_names = {i["name"] for i in insp_after.get_indexes("feishu_task_configs")}
            if "idx_feishu_task_configs_owner" not in idx_names:
                with engine.begin() as conn:
                    conn.execute(text(ALTER_ADD_INDEX))
    except Exception as exc:  # noqa: BLE001
        print(f"执行失败：{exc}", file=sys.stderr)
        sys.exit(1)

    print("feishu_task_configs 表已就绪（若已存在则跳过创建）。")


if __name__ == "__main__":
    main()

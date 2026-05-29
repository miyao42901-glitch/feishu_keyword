# server/migrations

异步任务与平台结果表相关的 MySQL 脚本。

| 文件 | 用途 | 执行方 |
|------|------|--------|
| [`schema.sql`](schema.sql) | 新库全量 `CREATE TABLE IF NOT EXISTS`（`feishu_async_tasks` + 各 `feishu_*_results`） | `api` 启动时（`DATABASE_RUN_MIGRATIONS=1` 且库中无 `feishu_async_tasks`），见 [`social_platform/database/db_migrate.py`](../social_platform/database/db_migrate.py) |
| [`012_create_sys_backoffice_rbac.sql`](012_create_sys_backoffice_rbac.sql) | 管理端 RBAC 表（`sys_admin` 等） | `api` 启动时（`DATABASE_RUN_MIGRATIONS=1` 且库中无 `sys_admin`） |
| [`013_seed_sys_backoffice_dev.sql`](013_seed_sys_backoffice_dev.sql) | 开发种子（`admin` / `Admin123a`） | 同上，仅在首次建 RBAC 表后执行 |
| `001`–`011` | 存量库增量或说明性 SQL | **人工**按文件名与注释在低峰执行；**新库一般只需 `schema.sql`** |
| `db_migrate.py` | 列对齐、索引等幂等补丁 | 每次 `api` 启动（`DATABASE_RUN_MIGRATIONS=1`） |

## 增量脚本说明

- 带编号的 `*.sql`：可对已有库执行 `ALTER`（执行前备份、在从库验证）。
- 说明性文件（如 `003_schema_align_notes.sql`）：阅读注释后按需手工执行，非一律自动跑。
- 破坏性变更脚本：执行前确认数据可丢弃或已备份；可清空数据的库可 DROP 相关表后重新执行 `schema.sql`。

表结构权威定义以 **`schema.sql`** 为准；ORM 见 `social_platform/models/`。

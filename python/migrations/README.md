# python/migrations

采集/异步任务（`sync-api`）相关 MySQL 脚本与基线 schema。

| 文件 | 用途 | 执行方 |
|------|------|--------|
| [`schema.sql`](schema.sql) | 新库全量 `CREATE TABLE IF NOT EXISTS` | `sync-api` 启动时（`DATABASE_RUN_MIGRATIONS=1` 且库中无 `feishu_async_tasks`），见 [`social_platform/database/db_migrate.py`](../social_platform/database/db_migrate.py) |
| `001`–`011` | 存量库增量或说明性脚本 | **人工**按编号与文件内注释在低峰执行；**新库一般只需 `schema.sql`** |
| `db_migrate.py` | 列对齐、`fetch_count`/`api_key` 等 + P0 索引幂等补丁 | 每次 HTTP 启动（`DATABASE_RUN_MIGRATIONS=1`） |

## 增量脚本说明

- **001–002、004、006–011**：可对已有库执行 `ALTER`（执行前备份、在从库验证）。
- **003**：迁移步骤说明，非可直接执行的 DDL。
- **005**：破坏性变更（UUID → BIGINT），占位说明；可清空数据的库请 DROP 后执行 `schema.sql`，勿盲目执行本文件。

管理端业务表（`server/`）不在此目录，使用 `server/scripts/init_schema.py`。

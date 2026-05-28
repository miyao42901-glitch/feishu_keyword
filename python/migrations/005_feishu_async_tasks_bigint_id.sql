-- 破坏性变更：将 `feishu_async_tasks.id` 由 UUID(VARCHAR) 改为 BIGINT 自增，并同步结果表 `task_id` 类型。
-- 仅适用于可清空数据的开发/测试库；生产需自行制定迁移（导出、映射、回填）。
--
-- 执行前：SET FOREIGN_KEY_CHECKS=0; 按序 DROP 子表再 DROP 父表；再执行 schema.sql 全量建表。
-- 或在新环境直接使用当前 `python/migrations/schema.sql`，勿执行本文件。

-- 占位：避免空迁移文件；实际操作见 schema.sql 与运维文档。

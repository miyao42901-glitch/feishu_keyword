-- 存量库：feishu_async_tasks 去掉 platform / params_json，改为 body_json(JSON)，action 单独存。
-- 新库请直接使用 python/migrations/schema.sql 全量建表，无需执行本脚本。
--
-- 执行前备份；在从库或副本上验证后再上生产。
-- 需要 MySQL 8.0.29+（使用 DROP COLUMN IF EXISTS）；更低版本请手工删列。
--
-- 若旧表 params_json 存的就是「与 Worker 一致的参数字典」（与现 body_json 语义一致），
-- 取消注释下面一行做回填；若历史结构不同，请自行 ETL 后再 DROP 旧列。

ALTER TABLE feishu_async_tasks
    ADD COLUMN body_json JSON NULL COMMENT '仅存储请求 body 对象（不含 API Key）' AFTER action;

-- UPDATE feishu_async_tasks SET body_json = CAST(params_json AS JSON) WHERE body_json IS NULL AND params_json IS NOT NULL;

UPDATE feishu_async_tasks SET body_json = JSON_OBJECT() WHERE body_json IS NULL;

ALTER TABLE feishu_async_tasks
    MODIFY COLUMN body_json JSON NOT NULL COMMENT '仅存储请求 body 对象（不含 API Key）；平台由 action 在应用层解析';

ALTER TABLE feishu_async_tasks DROP COLUMN IF EXISTS params_json;
-- platform 上的索引会随列删除；若单独建过索引且报错，可先 DROP INDEX ix_feishu_async_tasks_platform
ALTER TABLE feishu_async_tasks DROP COLUMN IF EXISTS platform;

-- action 索引若已存在会报错，可忽略或先 DROP 再 ADD
-- ALTER TABLE feishu_async_tasks ADD INDEX ix_feishu_async_tasks_action (action);

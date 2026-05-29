-- 存量库：为异步任务表增加 user_id / platform（按维护窗口执行；数据需自行核对）
-- 若自旧版单表搜索结果迁移，请自行 ETL 至 feishu_douyin_results / feishu_xhs_results

ALTER TABLE feishu_async_tasks
    ADD COLUMN user_id VARCHAR(128) NOT NULL DEFAULT 'anonymous' AFTER id,
    ADD COLUMN platform VARCHAR(32) NOT NULL DEFAULT '' AFTER user_id,
    ADD INDEX ix_feishu_async_tasks_user_id (user_id),
    ADD INDEX ix_feishu_async_tasks_platform (platform);

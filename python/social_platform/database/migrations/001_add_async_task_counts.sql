-- 已有库升级：为异步任务表增加落库统计列（执行一次即可）
ALTER TABLE feishu_async_tasks
    ADD COLUMN success_count INT NOT NULL DEFAULT 0 AFTER cancel_requested,
    ADD COLUMN failed_count INT NOT NULL DEFAULT 0 AFTER success_count;

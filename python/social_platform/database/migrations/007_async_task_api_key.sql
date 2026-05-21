-- feishu_async_tasks：新增 api_key 字段，支持 Celery 重启后从 MySQL 恢复调度与鉴权
-- 在已有库执行一次（MySQL 8+）

ALTER TABLE feishu_async_tasks
    ADD COLUMN api_key VARCHAR(128) NOT NULL DEFAULT ''
        COMMENT '提交任务的API_KEY'
        AFTER body_json;

-- feishu_async_tasks：任务展示名称
ALTER TABLE feishu_async_tasks
    ADD COLUMN task_name VARCHAR(100) NOT NULL DEFAULT '' COMMENT '任务名称（1～100 字符）' AFTER user_id;

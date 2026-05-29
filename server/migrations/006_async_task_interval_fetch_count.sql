-- feishu_async_tasks：collect_interval_minutes -> interval_minutes；新增 fetch_count
-- 在已有库执行一次（MySQL 8+）

ALTER TABLE feishu_async_tasks
    CHANGE COLUMN collect_interval_minutes interval_minutes INT NOT NULL DEFAULT 60
        COMMENT '定时采集频率（分钟），最小 5，默认 60';

ALTER TABLE feishu_async_tasks
    ADD COLUMN fetch_count INT NOT NULL DEFAULT 100
        COMMENT '单次采集条数上限，1～500，默认 100'
        AFTER interval_minutes;

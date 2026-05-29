-- P0 索引优化：用户任务列表、结果分页、待验收查询
-- 存量库低峰执行；新库见 schema.sql

-- feishu_async_tasks：list / count_active / 按状态筛选 + ORDER BY id DESC
ALTER TABLE feishu_async_tasks
    ADD INDEX ix_async_tasks_user_status_id (user_id, status, id DESC);

ALTER TABLE feishu_douyin_results
    ADD INDEX ix_feishu_douyin_results_task_upload_ct (task_id, is_upload, create_time DESC),
    ADD INDEX ix_feishu_douyin_results_user_upload_id (user_id, is_upload, id);

ALTER TABLE feishu_xhs_results
    ADD INDEX ix_feishu_xhs_results_task_upload_ct (task_id, is_upload, create_time DESC),
    ADD INDEX ix_feishu_xhs_results_user_upload_id (user_id, is_upload, id);

ALTER TABLE feishu_wxvideo_results
    ADD INDEX ix_feishu_wxvideo_results_task_upload_ct (task_id, is_upload, create_time DESC),
    ADD INDEX ix_feishu_wxvideo_results_user_upload_id (user_id, is_upload, id);

ALTER TABLE feishu_mp_results
    ADD INDEX ix_feishu_mp_results_task_upload_ct (task_id, is_upload, create_time DESC),
    ADD INDEX ix_feishu_mp_results_user_upload_id (user_id, is_upload, id);

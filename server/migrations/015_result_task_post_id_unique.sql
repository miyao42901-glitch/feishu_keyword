-- 结果表去重范围：post_id 全局唯一 → (task_id, post_id) 任务内唯一
-- 不同异步任务可写入相同 post_id；同一任务内仍不可重复。

ALTER TABLE feishu_douyin_results
    DROP INDEX uq_feishu_douyin_results_post_id,
    ADD UNIQUE KEY uq_feishu_douyin_results_task_post (task_id, post_id);

ALTER TABLE feishu_xhs_results
    DROP INDEX uq_feishu_xhs_results_post_id,
    ADD UNIQUE KEY uq_feishu_xhs_results_task_post (task_id, post_id);

ALTER TABLE feishu_wxvideo_results
    DROP INDEX uq_feishu_wxvideo_results_post_id,
    ADD UNIQUE KEY uq_feishu_wxvideo_results_task_post (task_id, post_id);

ALTER TABLE feishu_mp_results
    DROP INDEX uq_feishu_mp_results_post_id,
    ADD UNIQUE KEY uq_feishu_mp_results_task_post (task_id, post_id);

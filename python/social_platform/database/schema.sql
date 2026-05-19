-- MySQL 8+ utf8mb4：异步任务 + 按平台结果表（与 SQLAlchemy models 对齐）
-- 不含 LONGTEXT；`summary` 为 TEXT（无默认值，由应用写入）

CREATE TABLE IF NOT EXISTS feishu_async_tasks (
    id BIGINT NOT NULL AUTO_INCREMENT COMMENT '任务主键自增数字' PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL COMMENT '调用方系统用户 ID（与 yddm users/me 的 data.id 一致），用于权限与统计',
    status VARCHAR(32) NOT NULL DEFAULT 'pending' COMMENT '任务状态：pending/running/success/failed/cancelled',
    action VARCHAR(128) NOT NULL DEFAULT '' COMMENT '对外已注册 action（kebab-case），如 douyin-search-all',
    body_json JSON NOT NULL COMMENT '仅存储请求 body 对象（不含 API Key）；平台由 action 在应用层解析',
    api_key VARCHAR(128) NOT NULL DEFAULT '' COMMENT '提交任务的API_KEY',
    error_message VARCHAR(64) NULL COMMENT '失败时的错误摘要，最长 64 字符',
    celery_task_id VARCHAR(128) NULL COMMENT 'Celery AsyncResult.id，用于撤销与排查',
    priority INT NOT NULL DEFAULT 0 COMMENT '任务优先级 0-9，数值越大优先级越高',
    cancel_requested TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否已请求取消：0 否 1 是',
    success_count INT NOT NULL DEFAULT 0 COMMENT '落库成功条数累计（含去重后视为成功）',
    failed_count INT NOT NULL DEFAULT 0 COMMENT '落库失败/跳过条数累计',
    task_start_time DATETIME NOT NULL COMMENT '定时任务开始时间（前端传入，UTC 存储）',
    task_end_time DATETIME NOT NULL COMMENT '定时任务结束时间（前端传入，UTC 存储）',
    interval_minutes INT NOT NULL DEFAULT 60 COMMENT '定时采集频率（分钟），最小 5，默认 60',
    fetch_count INT NOT NULL DEFAULT 100 COMMENT '单次采集条数上限，1～500，默认 100',
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后更新时间',
    INDEX ix_feishu_async_tasks_status (status),
    INDEX ix_feishu_async_tasks_user_id (user_id),
    INDEX ix_feishu_async_tasks_action (action),
    INDEX ix_feishu_async_tasks_celery_task_id (celery_task_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='异步采集任务';

-- 抖音 / 小红书结果表列集合一致（小红书多 xsec_token），未使用列填默认值

CREATE TABLE IF NOT EXISTS feishu_douyin_results (
    id BIGINT NOT NULL AUTO_INCREMENT COMMENT '自增主键' PRIMARY KEY,
    task_id BIGINT NULL COMMENT '关联异步任务 ID，同步接口可为空',
    user_id VARCHAR(64) NOT NULL COMMENT '调用方系统用户 ID',
    post_id VARCHAR(64) NOT NULL COMMENT '平台内容主键，对应抖音 aweme_id',
    keyword VARCHAR(64) NOT NULL DEFAULT '' COMMENT '搜索关键词',
    nickname VARCHAR(64) NOT NULL DEFAULT '' COMMENT '作者昵称',
    sec_uid VARCHAR(128) NOT NULL DEFAULT '' COMMENT '作者抖音 sec_uid',
    content_type VARCHAR(16) NOT NULL DEFAULT '' COMMENT '内容类型，如 video',
    is_upload TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否已上传：0 否 1 是（由其他系统更新）',
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '入库时间',
    update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后更新时间',
    title VARCHAR(500) NOT NULL DEFAULT '' COMMENT '作品标题',
    summary TEXT NOT NULL COMMENT '作品正文/描述摘要',
    page_url VARCHAR(512) NOT NULL DEFAULT '' COMMENT '作品详情页链接',
    avatar_url VARCHAR(256) NOT NULL DEFAULT '' COMMENT '作者头像 URL',
    author_signature VARCHAR(256) NOT NULL DEFAULT '' COMMENT '作者签名',
    verify_name VARCHAR(128) NOT NULL DEFAULT '' COMMENT '企业/个人认证文案',
    cover_url VARCHAR(256) NOT NULL DEFAULT '' COMMENT '封面图 URL',
    duration_seconds INT NOT NULL DEFAULT 0 COMMENT '视频时长（秒）',
    has_music TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否含音乐：0 否 1 是（抖音侧占位）',
    publish_time_ms BIGINT NOT NULL DEFAULT 0 COMMENT '发布时间毫秒时间戳',
    like_count INT NOT NULL DEFAULT 0 COMMENT '点赞数',
    comment_count INT NOT NULL DEFAULT 0 COMMENT '评论数',
    share_count INT NOT NULL DEFAULT 0 COMMENT '分享数',
    collect_count INT NOT NULL DEFAULT 0 COMMENT '收藏数',
    primary_image_url VARCHAR(256) NOT NULL DEFAULT '' COMMENT '主图 URL（可与封面一致）',
    primary_video_url VARCHAR(256) NOT NULL DEFAULT '' COMMENT '主视频播放地址（取解析列表首条）',
    UNIQUE KEY uq_feishu_douyin_results_post_id (post_id),
    INDEX ix_feishu_douyin_results_task_id (task_id),
    INDEX ix_feishu_douyin_results_user_id (user_id),
    INDEX ix_feishu_douyin_results_is_upload (is_upload),
    INDEX ix_feishu_douyin_results_create_time (create_time),
    INDEX ix_feishu_douyin_results_keyword (keyword),
    CONSTRAINT fk_feishu_douyin_results_task
        FOREIGN KEY (task_id) REFERENCES feishu_async_tasks (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='抖音搜索结果';

CREATE TABLE IF NOT EXISTS feishu_xhs_results (
    id BIGINT NOT NULL AUTO_INCREMENT COMMENT '自增主键' PRIMARY KEY,
    task_id BIGINT NULL COMMENT '关联异步任务 ID，同步接口可为空',
    user_id VARCHAR(64) NOT NULL COMMENT '调用方系统用户 ID',
    post_id VARCHAR(64) NOT NULL COMMENT '平台内容主键，对应小红书 note_id',
    keyword VARCHAR(64) NOT NULL DEFAULT '' COMMENT '搜索关键词',
    nickname VARCHAR(64) NOT NULL DEFAULT '' COMMENT '作者昵称',
    sec_uid VARCHAR(128) NOT NULL DEFAULT '' COMMENT '作者站内用户 ID（userid）',
    content_type VARCHAR(16) NOT NULL DEFAULT '' COMMENT '内容类型：normal/video 等',
    is_upload TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否已上传：0 否 1 是（由其他系统更新）',
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '入库时间',
    update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后更新时间',
    title VARCHAR(500) NOT NULL DEFAULT '' COMMENT '笔记标题',
    summary TEXT NOT NULL COMMENT '笔记正文摘要',
    page_url VARCHAR(256) NOT NULL DEFAULT '' COMMENT '笔记详情页链接',
    xsec_token VARCHAR(64) NOT NULL DEFAULT '' COMMENT '笔记 xsec_token，用于链接有效性',
    avatar_url VARCHAR(256) NOT NULL DEFAULT '' COMMENT '作者头像 URL',
    author_signature VARCHAR(256) NOT NULL DEFAULT '' COMMENT '作者签名（小红书侧占位）',
    verify_name VARCHAR(64) NOT NULL DEFAULT '' COMMENT '认证文案（小红书侧占位）',
    cover_url VARCHAR(256) NOT NULL DEFAULT '' COMMENT '封面/首图 URL',
    duration_seconds INT NOT NULL DEFAULT 0 COMMENT '视频时长（秒）',
    has_music TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否含音乐：0 否 1 是',
    publish_time_ms BIGINT NOT NULL DEFAULT 0 COMMENT '发布时间毫秒时间戳',
    like_count INT NOT NULL DEFAULT 0 COMMENT '点赞数',
    comment_count INT NOT NULL DEFAULT 0 COMMENT '评论数',
    share_count INT NOT NULL DEFAULT 0 COMMENT '分享数（小红书侧占位）',
    collect_count INT NOT NULL DEFAULT 0 COMMENT '收藏数',
    primary_image_url VARCHAR(256) NOT NULL DEFAULT '' COMMENT '主图 URL',
    primary_video_url VARCHAR(256) NOT NULL DEFAULT '' COMMENT '主视频地址（取解析列表首条）',
    UNIQUE KEY uq_feishu_xhs_results_post_id (post_id),
    INDEX ix_feishu_xhs_results_task_id (task_id),
    INDEX ix_feishu_xhs_results_user_id (user_id),
    INDEX ix_feishu_xhs_results_is_upload (is_upload),
    INDEX ix_feishu_xhs_results_create_time (create_time),
    INDEX ix_feishu_xhs_results_keyword (keyword),
    CONSTRAINT fk_feishu_xhs_results_task
        FOREIGN KEY (task_id) REFERENCES feishu_async_tasks (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='小红书搜索结果';

CREATE TABLE IF NOT EXISTS feishu_wxvideo_results (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '自增ID',
    task_id BIGINT NULL COMMENT '关联异步任务ID',
    user_id VARCHAR(64) NOT NULL COMMENT '用户ID',
    post_id VARCHAR(64) NOT NULL COMMENT '视频 exportId',
    keyword VARCHAR(64) NOT NULL DEFAULT '' COMMENT '搜索关键词',
    nickname VARCHAR(64) NOT NULL DEFAULT '' COMMENT 'UP主名字',
    avatar_url VARCHAR(256) NOT NULL DEFAULT '' COMMENT 'UP主头像',
    title VARCHAR(500) NOT NULL DEFAULT '' COMMENT '视频标题',
    publish_time BIGINT NOT NULL DEFAULT 0 COMMENT '发布时间（毫秒时间戳）',
    duration INT NOT NULL DEFAULT 0 COMMENT '视频时长（秒）',
    cover_url VARCHAR(512) NOT NULL DEFAULT '' COMMENT '封面图',
    video_url VARCHAR(512) NOT NULL DEFAULT '' COMMENT '视频下载链接',
    like_count INT NOT NULL DEFAULT 0 COMMENT '点赞数',
    comment_count INT NOT NULL DEFAULT 0 COMMENT '评论数',
    forward_count INT NOT NULL DEFAULT 0 COMMENT '转发数',
    thumb_count INT NOT NULL DEFAULT 0 COMMENT '小心心数',
    is_upload TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否已上传',
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uq_feishu_wxvideo_results_post_id (post_id),
    INDEX ix_feishu_wxvideo_results_task_id (task_id),
    INDEX ix_feishu_wxvideo_results_user_id (user_id),
    INDEX ix_feishu_wxvideo_results_is_upload (is_upload),
    INDEX ix_feishu_wxvideo_results_create_time (create_time),
    INDEX ix_feishu_wxvideo_results_keyword (keyword),
    CONSTRAINT fk_feishu_wxvideo_results_task
        FOREIGN KEY (task_id) REFERENCES feishu_async_tasks (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='视频号搜索结果';

CREATE TABLE IF NOT EXISTS feishu_mp_results (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '自增ID',
    task_id BIGINT NULL COMMENT '关联异步任务ID',
    user_id VARCHAR(64) NOT NULL COMMENT '用户ID',
    post_id VARCHAR(64) NOT NULL COMMENT '文章ID',
    keyword VARCHAR(64) NOT NULL DEFAULT '' COMMENT '搜索关键词',
    company_name VARCHAR(128) NOT NULL DEFAULT '' COMMENT '公众号名称',
    biz VARCHAR(64) NOT NULL DEFAULT '' COMMENT '微信公众号 biz',
    title VARCHAR(500) NOT NULL DEFAULT '' COMMENT '文章标题',
    summary TEXT NOT NULL COMMENT '正文摘要',
    url VARCHAR(512) NOT NULL DEFAULT '' COMMENT '文章链接',
    avatar_url VARCHAR(256) NOT NULL DEFAULT '' COMMENT '作者头像',
    publish_time BIGINT NOT NULL DEFAULT 0 COMMENT '发布时间（毫秒时间戳）',
    is_upload TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否已上传',
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uq_feishu_mp_results_post_id (post_id),
    INDEX ix_feishu_mp_results_task_id (task_id),
    INDEX ix_feishu_mp_results_user_id (user_id),
    INDEX ix_feishu_mp_results_is_upload (is_upload),
    INDEX ix_feishu_mp_results_create_time (create_time),
    INDEX ix_feishu_mp_results_keyword (keyword),
    CONSTRAINT fk_feishu_mp_results_task
        FOREIGN KEY (task_id) REFERENCES feishu_async_tasks (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='公众号文章搜索结果';

-- 已有库升级（在 feishu_async_tasks 已存在时执行一次）：
-- ALTER TABLE feishu_async_tasks
--     ADD COLUMN task_start_time DATETIME NOT NULL COMMENT '定时任务开始时间（前端传入，UTC 存储）' AFTER failed_count,
--     ADD COLUMN task_end_time DATETIME NOT NULL COMMENT '定时任务结束时间（前端传入，UTC 存储）' AFTER task_start_time,
--     ADD COLUMN interval_minutes INT NOT NULL DEFAULT 60 COMMENT '定时采集频率（分钟），最小 5，默认 60' AFTER task_end_time,
--     ADD COLUMN fetch_count INT NOT NULL DEFAULT 100 COMMENT '单次采集条数上限，1～500，默认 100' AFTER interval_minutes;
--
-- ALTER TABLE feishu_async_tasks
--     ADD COLUMN api_key VARCHAR(128) NOT NULL DEFAULT '' COMMENT '提交任务的API_KEY' AFTER body_json;

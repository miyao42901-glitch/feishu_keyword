-- 埋点 / 运营看板事实表（Phase 1 起用；api 启动时若不存在 analytics_user 则自动执行）

CREATE TABLE IF NOT EXISTS `analytics_user` (
  `user_id` varchar(64) NOT NULL COMMENT 'YDDM 用户 ID',
  `feishu_id` varchar(128) DEFAULT NULL COMMENT '飞书 open_id / 标识',
  `phone` varchar(32) DEFAULT NULL COMMENT '手机号（脱敏存储）',
  `remark` varchar(255) DEFAULT NULL COMMENT '运营备注（admin 维护）',
  `plugin_version` varchar(32) DEFAULT NULL COMMENT '插件版本',
  `device_type` varchar(16) DEFAULT NULL COMMENT '手机/桌面/Web',
  `active_hours` varchar(64) DEFAULT NULL COMMENT '活跃时段描述',
  `first_use_at` datetime DEFAULT NULL COMMENT '首次使用插件',
  `last_active_at` datetime DEFAULT NULL COMMENT '最近活跃',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`),
  KEY `idx_analytics_user_last_active` (`last_active_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='埋点用户维度';

CREATE TABLE IF NOT EXISTS `analytics_task` (
  `task_id` varchar(64) NOT NULL COMMENT '任务 ID（异步为 server id，单次可为本地 id）',
  `user_id` varchar(64) NOT NULL COMMENT '创建用户',
  `task_type` varchar(32) NOT NULL COMMENT '定时任务/单次任务',
  `keyword_count` int NOT NULL DEFAULT 0 COMMENT '关键词数量',
  `platforms_json` json DEFAULT NULL COMMENT '信源平台列表',
  `status` varchar(32) NOT NULL DEFAULT '运行中' COMMENT '运行中/已停止/已完成',
  `notify_enabled` tinyint(1) NOT NULL DEFAULT 0 COMMENT '通知开关',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`task_id`),
  KEY `idx_analytics_task_user` (`user_id`),
  KEY `idx_analytics_task_status` (`status`),
  KEY `idx_analytics_task_created` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='埋点任务快照';

CREATE TABLE IF NOT EXISTS `analytics_page_view` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` varchar(64) DEFAULT NULL COMMENT '未登录可为空',
  `page_name` varchar(64) NOT NULL COMMENT '页面名称',
  `source` varchar(128) DEFAULT NULL COMMENT '来源',
  `device_type` varchar(16) DEFAULT NULL,
  `plugin_version` varchar(32) DEFAULT NULL,
  `visited_at` datetime NOT NULL COMMENT '访问时间',
  PRIMARY KEY (`id`),
  KEY `idx_apv_visited` (`visited_at`),
  KEY `idx_apv_user_visited` (`user_id`, `visited_at`),
  KEY `idx_apv_page_visited` (`page_name`, `visited_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='页面浏览';

CREATE TABLE IF NOT EXISTS `analytics_notify_toggle` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` varchar(64) NOT NULL,
  `task_id` varchar(64) DEFAULT NULL,
  `enabled` tinyint(1) NOT NULL COMMENT '1=开 0=关',
  `toggled_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_ant_toggled` (`toggled_at`),
  KEY `idx_ant_user_toggled` (`user_id`, `toggled_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='通知开关切换';

CREATE TABLE IF NOT EXISTS `analytics_exec_run` (
  `exec_id` varchar(64) NOT NULL COMMENT '执行 ID',
  `task_id` varchar(64) NOT NULL,
  `user_id` varchar(64) DEFAULT NULL,
  `task_type` varchar(32) DEFAULT NULL,
  `run_no` int DEFAULT NULL COMMENT '第几次执行（定时任务）',
  `started_at` datetime NOT NULL,
  `ended_at` datetime DEFAULT NULL,
  `duration_ms` int DEFAULT NULL,
  `result` varchar(16) DEFAULT NULL COMMENT '成功/失败',
  `fail_reason` varchar(255) DEFAULT NULL,
  `points` int NOT NULL DEFAULT 0,
  `collect_count` int NOT NULL DEFAULT 0,
  PRIMARY KEY (`exec_id`),
  KEY `idx_aer_task` (`task_id`),
  KEY `idx_aer_started` (`started_at`),
  KEY `idx_aer_user_started` (`user_id`, `started_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='任务执行（Phase 2 写入）';

CREATE TABLE IF NOT EXISTS `analytics_api_call` (
  `request_id` varchar(64) NOT NULL,
  `task_id` varchar(64) DEFAULT NULL,
  `exec_id` varchar(64) DEFAULT NULL,
  `platform` varchar(64) DEFAULT NULL,
  `called_at` datetime NOT NULL,
  `result` varchar(16) NOT NULL COMMENT '成功/失败',
  `error_code` varchar(32) DEFAULT NULL,
  `latency_ms` int DEFAULT NULL,
  PRIMARY KEY (`request_id`),
  KEY `idx_aac_called` (`called_at`),
  KEY `idx_aac_platform` (`platform`, `called_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='API 调用（Phase 2 写入）';

CREATE TABLE IF NOT EXISTS `analytics_point_consume` (
  `consume_id` varchar(64) NOT NULL,
  `user_id` varchar(64) NOT NULL,
  `task_id` varchar(64) DEFAULT NULL,
  `exec_id` varchar(64) DEFAULT NULL,
  `platform` varchar(64) DEFAULT NULL,
  `amount` int NOT NULL DEFAULT 0,
  `balance` int DEFAULT NULL,
  `consumed_at` datetime NOT NULL,
  PRIMARY KEY (`consume_id`),
  KEY `idx_apc_user` (`user_id`, `consumed_at`),
  KEY `idx_apc_consumed` (`consumed_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='点数消耗（Phase 2 写入）';

CREATE TABLE IF NOT EXISTS `analytics_push_log` (
  `push_id` varchar(64) NOT NULL,
  `task_id` varchar(64) DEFAULT NULL,
  `user_id` varchar(64) DEFAULT NULL,
  `webhook` varchar(512) DEFAULT NULL,
  `send_at` datetime DEFAULT NULL,
  `send_result` varchar(16) DEFAULT NULL,
  `callback_at` datetime DEFAULT NULL,
  `callback_result` varchar(16) DEFAULT NULL,
  `new_data_count` int NOT NULL DEFAULT 0,
  `error_code` varchar(32) DEFAULT NULL,
  `retry_count` int NOT NULL DEFAULT 0,
  PRIMARY KEY (`push_id`),
  KEY `idx_apl_send` (`send_at`),
  KEY `idx_apl_task` (`task_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='推送记录（Phase 3 写入）';

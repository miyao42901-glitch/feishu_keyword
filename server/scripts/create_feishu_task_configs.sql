-- 飞书插件「任务配置」持久化表。在库 feishu_keyword 中执行（与 DATABASE.md 一致）。
-- 执行顺序：先建库/选库，再运行本脚本。

CREATE TABLE IF NOT EXISTS feishu_task_configs (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  plan_name VARCHAR(200) NULL COMMENT '方案名称（列表展示，可与 config_json 内冗余）',
  owner_api_key VARCHAR(256) NULL COMMENT 'YDDM API Key，与请求头 X-Api-Key 一致，按账户隔离',
  config_json LONGTEXT NOT NULL COMMENT '前端表单完整 JSON',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_feishu_task_configs_owner (owner_api_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 目的: 创建管理后台 RBAC 相关表 (sys_*), 与 docs/admin/导读 一页纸一致
-- 状态: 脚本已入库; 未在共用 RDS 执行前请勿登记「已执行」
-- 兼容性: 新表, 老业务代码无引用; 执行后需配合 server 管理端路由与种子数据
-- 执行方式: MySQL 5.7+ / 8.x, utf8mb4_general_ci (与现库 employee 等表一致)
-- 回滚: 见文件末尾 DROP TABLE 顺序 (仅空库/可接受丢数据时使用)

CREATE TABLE IF NOT EXISTS `sys_admin` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '管理员主键',
  `username` varchar(64) NOT NULL COMMENT '登录名',
  `password_hash` varchar(255) NOT NULL COMMENT 'bcrypt 密码哈希',
  `nickname` varchar(64) NOT NULL DEFAULT '' COMMENT '显示名',
  `avatar` varchar(255) DEFAULT NULL COMMENT '头像 URL',
  `mobile` varchar(32) DEFAULT NULL COMMENT '手机',
  `email` varchar(128) DEFAULT NULL COMMENT '邮箱',
  `remark` varchar(255) DEFAULT NULL COMMENT '备注',
  `is_disable` tinyint NOT NULL DEFAULT 0 COMMENT '1=禁用 0=正常',
  `is_delete` tinyint NOT NULL DEFAULT 0 COMMENT '1=已删 0=未删',
  `last_login_at` datetime DEFAULT NULL COMMENT '最近成功登录',
  `create_by` int DEFAULT NULL COMMENT '创建人 sys_admin.id',
  `create_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_sys_admin_username` (`username`),
  KEY `idx_sys_admin_disable_delete` (`is_disable`, `is_delete`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='系统管理员';

CREATE TABLE IF NOT EXISTS `sys_role` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(64) NOT NULL COMMENT '角色名',
  `code` varchar(64) DEFAULT NULL COMMENT '角色编码',
  `sort` int NOT NULL DEFAULT 0,
  `is_disable` tinyint NOT NULL DEFAULT 0,
  `is_delete` tinyint NOT NULL DEFAULT 0,
  `create_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_sys_role_code` (`code`),
  KEY `idx_sys_role_disable_delete` (`is_disable`, `is_delete`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='系统角色';

CREATE TABLE IF NOT EXISTS `sys_menu` (
  `id` int NOT NULL AUTO_INCREMENT,
  `parent_id` int NOT NULL DEFAULT 0 COMMENT '0=顶级',
  `type` tinyint NOT NULL DEFAULT 1 COMMENT '1=目录 2=菜单 3=按钮',
  `name` varchar(64) NOT NULL DEFAULT '' COMMENT '菜单名',
  `icon` varchar(64) DEFAULT NULL,
  `path` varchar(255) DEFAULT NULL COMMENT '前端路由 path',
  `component` varchar(255) DEFAULT NULL COMMENT '前端组件路径',
  `auth` varchar(128) NOT NULL DEFAULT '' COMMENT '权限串, 与 API path 映射一致',
  `sort` int NOT NULL DEFAULT 0,
  `is_show` tinyint NOT NULL DEFAULT 1,
  `is_disable` tinyint NOT NULL DEFAULT 0,
  `create_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_sys_menu_auth` (`auth`),
  KEY `idx_sys_menu_parent` (`parent_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='菜单与权限点';

CREATE TABLE IF NOT EXISTS `sys_admin_role` (
  `admin_id` int NOT NULL,
  `role_id` int NOT NULL,
  PRIMARY KEY (`admin_id`, `role_id`),
  KEY `idx_sys_admin_role_role` (`role_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='管理员-角色';

CREATE TABLE IF NOT EXISTS `sys_role_menu` (
  `role_id` int NOT NULL,
  `menu_id` int NOT NULL,
  PRIMARY KEY (`role_id`, `menu_id`),
  KEY `idx_sys_role_menu_menu` (`menu_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='角色-菜单';

CREATE TABLE IF NOT EXISTS `sys_oper_log` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `admin_id` int NOT NULL,
  `title` varchar(128) DEFAULT NULL,
  `module` varchar(128) DEFAULT NULL,
  `method` varchar(16) DEFAULT NULL,
  `request_url` varchar(512) DEFAULT NULL,
  `ip` varchar(64) DEFAULT NULL,
  `user_agent` varchar(512) DEFAULT NULL,
  `oper_param` text COMMENT '入参摘要, 须脱敏',
  `status` tinyint NOT NULL DEFAULT 1 COMMENT '1=成功 2=失败',
  `error_msg` text,
  `create_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_sys_oper_log_admin_time` (`admin_id`, `create_at`),
  KEY `idx_sys_oper_log_create` (`create_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='管理端操作审计';

-- 回滚 (慎用):
-- SET FOREIGN_KEY_CHECKS=0;
-- DROP TABLE IF EXISTS sys_oper_log;
-- DROP TABLE IF EXISTS sys_role_menu;
-- DROP TABLE IF EXISTS sys_admin_role;
-- DROP TABLE IF EXISTS sys_menu;
-- DROP TABLE IF EXISTS sys_role;
-- DROP TABLE IF EXISTS sys_admin;
-- SET FOREIGN_KEY_CHECKS=1;

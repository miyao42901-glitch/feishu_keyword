-- 开发/联调种子：超级管理员 + 角色 + 菜单绑定
-- 默认口令: Admin123a（bcrypt 见 password_hash）
-- 生产执行前必须改密

SET NAMES utf8mb4;

INSERT INTO `sys_role` (`id`, `name`, `code`, `sort`, `is_disable`, `is_delete`)
VALUES (1, '超级管理员', 'super', 0, 0, 0)
ON DUPLICATE KEY UPDATE `name` = VALUES(`name`), `code` = VALUES(`code`);

INSERT INTO `sys_admin` (
  `id`, `username`, `password_hash`, `nickname`, `is_disable`, `is_delete`
) VALUES (
  1,
  'admin',
  '$2b$12$RP5c2ForgS97N/3UeeiTleOX1iemnFIqammpXhLsKHxMilgcH6P9m',
  '超级管理员',
  0,
  0
)
ON DUPLICATE KEY UPDATE
  `nickname` = VALUES(`nickname`),
  `password_hash` = VALUES(`password_hash`);

INSERT INTO `sys_admin_role` (`admin_id`, `role_id`) VALUES (1, 1)
ON DUPLICATE KEY UPDATE `admin_id` = VALUES(`admin_id`);

INSERT INTO `sys_menu` (`id`, `parent_id`, `type`, `name`, `icon`, `path`, `component`, `auth`, `sort`, `is_show`, `is_disable`)
VALUES
  (1, 0, 1, '系统', 'setting', '/system', 'Layout', 'system', 10, 1, 0),
  (2, 1, 2, '管理员信息', 'user', 'self', 'system/self', 'system:admin:self', 1, 1, 0),
  (3, 1, 2, '修改密码', 'lock', 'password', 'system/password', 'system:admin:password', 2, 1, 0),
  (4, 0, 1, '用户管理', 'user-filled', '/cuser', 'Layout', 'cuser', 20, 1, 0),
  (5, 4, 2, '终端用户', 'avatar', 'list', 'cuser/list', 'cuser:list', 1, 1, 0)
ON DUPLICATE KEY UPDATE
  `name` = VALUES(`name`),
  `path` = VALUES(`path`),
  `component` = VALUES(`component`),
  `auth` = VALUES(`auth`);

INSERT INTO `sys_role_menu` (`role_id`, `menu_id`)
SELECT 1, m.id FROM `sys_menu` m
WHERE m.id IN (1, 2, 3, 4, 5)
ON DUPLICATE KEY UPDATE `role_id` = VALUES(`role_id`);

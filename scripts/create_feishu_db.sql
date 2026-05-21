-- 在 phpMyAdmin（https://pma.tbpf.com）用 root 登录后执行。
-- 仅创建 feishu_keyword 库，勿对 jzl_editor 执行 DROP/DELETE/改表。

CREATE DATABASE IF NOT EXISTS feishu_keyword
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

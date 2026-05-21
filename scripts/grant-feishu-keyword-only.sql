-- 在 phpMyAdmin（https://pma.tbpf.com）用 MySQL **root** 登录后执行。
-- 仅创建/授权 feishu_keyword 库，不要对 jzl_editor 执行 DROP/DELETE/改表。
-- 应用连接串：mysql+pymysql://lanlang_v1:***@gqs-mysql:3306/feishu_keyword

CREATE DATABASE IF NOT EXISTS feishu_keyword
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

GRANT ALL PRIVILEGES ON feishu_keyword.* TO 'lanlang_v1'@'%';
FLUSH PRIVILEGES;

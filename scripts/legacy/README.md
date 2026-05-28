# 已废弃脚本（稿轻松 gqs-mysql / lanlang_v1 时代）

MySQL 已迁移至 traefik 栈 `tbpf-mysql`，应用使用 **root** 连接。请勿再对运行中的 `tbpf-mysql` 使用 `skip-grant-tables` 热改配置（曾导致 phpMyAdmin 不可用）。

当前运维请使用：

- `scripts/remote-setup-env.sh` — 写入远端 env 并建 `feishu_keyword` 库
- `scripts/init-feishu-keyword-db.sh` — 仅建库
- `scripts/create_feishu_db.sql` — phpMyAdmin 手工建库

本目录内脚本仅作历史参考，针对已下线的 `gqs-mysql`。

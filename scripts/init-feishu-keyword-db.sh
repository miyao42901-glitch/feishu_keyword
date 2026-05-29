#!/bin/bash
# 仅在共享 MySQL（tbpf-mysql）上创建 feishu_keyword 库，不修改 jzl_editor 等库的数据与表。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=env-mysql-from-traefik.sh
source "$SCRIPT_DIR/env-mysql-from-traefik.sh"

if ! ROOT_PW="$(load_mysql_root_password)"; then
  echo "ERROR: MYSQL_ROOT_PASSWORD empty（请配置 ${TRAEFIK_ENV}）"
  exit 1
fi

mysql_root() {
  docker exec tbpf-mysql mysql -uroot -p"${ROOT_PW}" -h127.0.0.1 "$@"
}

echo "==> CREATE DATABASE feishu_keyword (if not exists)"
mysql_root -e \
  "CREATE DATABASE IF NOT EXISTS feishu_keyword CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

mysql_root -e "SHOW DATABASES LIKE 'feishu_keyword';"
echo "done: feishu_keyword 库已就绪（tbpf-mysql），稿轻松库未改动"

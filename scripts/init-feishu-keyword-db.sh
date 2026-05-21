#!/bin/bash
# 仅在共享 MySQL 上创建/授权 feishu_keyword 库，不修改稿轻松 jzl_editor 等库的数据与表。
set -euo pipefail

GQS_ENV="${GQS_ENV:-/docker/gaoqingsong-test/server/.env}"
if [ ! -f "$GQS_ENV" ]; then
  echo "ERROR: missing $GQS_ENV"
  exit 1
fi
# shellcheck disable=SC1090
source "$GQS_ENV"

ROOT_PW="${MYSQL_ROOT_PASSWORD:-}"
MYSQL_USER="${MYSQL_USER:-lanlang_v1}"
if [ -z "$ROOT_PW" ]; then
  echo "ERROR: MYSQL_ROOT_PASSWORD empty in $GQS_ENV"
  exit 1
fi

mysql_root() {
  docker exec gqs-mysql mysql -uroot -p"${ROOT_PW}" -h127.0.0.1 "$@"
}

echo "==> CREATE DATABASE feishu_keyword (if not exists)"
mysql_root -e \
  "CREATE DATABASE IF NOT EXISTS feishu_keyword CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

echo "==> GRANT ${MYSQL_USER} on feishu_keyword.* only (不碰 jzl_editor)"
mysql_root -e \
  "GRANT ALL PRIVILEGES ON feishu_keyword.* TO '${MYSQL_USER}'@'%'; FLUSH PRIVILEGES;"

mysql_root -e "SHOW DATABASES LIKE 'feishu_keyword';"
echo "done: feishu_keyword 库已就绪，稿轻松库未改动"

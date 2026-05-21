#!/bin/bash
# 仅在共享 MySQL（tbpf-mysql）上创建 feishu_keyword 库，不修改 jzl_editor 等库的数据与表。
set -euo pipefail

TEST_ROOT="${TEST_ROOT:-/docker/feishu_keyword-test}"
PROD_ROOT="${PROD_ROOT:-/docker/feishu_keyword}"
TRAEFIK_ENV="${TRAEFIK_ENV:-/docker/traefik/.env}"

ROOT_PW=""
for f in "$TEST_ROOT/.env" "$PROD_ROOT/.env" "$TRAEFIK_ENV"; do
  if [ -f "$f" ]; then
    # shellcheck disable=SC1090
    set +u
    source "$f" 2>/dev/null || true
    set -u
    if [ -n "${MYSQL_ROOT_PASSWORD:-}" ]; then
      ROOT_PW="${MYSQL_ROOT_PASSWORD}"
      break
    fi
  fi
done

if [ -z "$ROOT_PW" ]; then
  echo "ERROR: MYSQL_ROOT_PASSWORD empty（配置栈根 .env 或 $TRAEFIK_ENV）"
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

#!/bin/bash
# 在部署主机执行：根据 traefik 栈 MYSQL_ROOT_PASSWORD 写入测试/正式栈根 .env.test / .env.master，并创建 feishu_keyword 库。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=env-mysql-from-traefik.sh
source "$SCRIPT_DIR/env-mysql-from-traefik.sh"

TEST_ROOT="${TEST_ROOT:-/docker/feishu_keyword-test}"
PROD_ROOT="${PROD_ROOT:-/docker/feishu_keyword}"

if ! MYSQL_ROOT_PASSWORD="$(load_mysql_root_password)"; then
  echo "ERROR: 未找到 MYSQL_ROOT_PASSWORD（请配置 ${TRAEFIK_ENV}）"
  exit 1
fi

MYSQL_USER=root
DB_URL="$(build_feishu_database_url "$MYSQL_ROOT_PASSWORD")"

mkdir -p "$TEST_ROOT/public/admin" "$TEST_ROOT/public/feishu" \
  "$TEST_ROOT/deploy/admin-static" "$TEST_ROOT/deploy/feishu-static" \
  "$PROD_ROOT/public/admin" "$PROD_ROOT/public/feishu" \
  "$PROD_ROOT/deploy/admin-static" "$PROD_ROOT/deploy/feishu-static"

write_env_test() {
  cat > "$TEST_ROOT/.env.test" <<EOF
MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}

APT_DEBIAN_MIRROR=mirrors.aliyun.com
PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
PYTHON_IMAGE=

ENVIRONMENT=test

DATABASE_URL=${DB_URL}

REDIS_HOST=tbpf-redis
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=2

REDIS_URL=redis://tbpf-redis:6379/2
CELERY_BROKER_URL=redis://tbpf-redis:6379/2
CELERY_RESULT_BACKEND=redis://tbpf-redis:6379/2
CELERY_TASK_ALWAYS_EAGER=0
CELERY_WORKER_POOL=gevent
CELERY_WORKER_CONCURRENCY=4
CELERY_WORKER_PREFETCH_MULTIPLIER=1
CELERY_BEAT_ENABLED=0

API_PUBLIC_HOST=test-fskw.tbpf.com
ADMIN_PUBLIC_HOST=test-fskw-admin.tbpf.com
FEISHU_PUBLIC_HOST=test-fskw-feishu.tbpf.com
TRAEFIK_SYNC_ROUTER_NAME=test-fkw-sync
TRAEFIK_ADMIN_ROUTER_NAME=test-fkw-admin
TRAEFIK_FEISHU_ROUTER_NAME=test-fkw-feishu

HTTP_HOST=0.0.0.0
HTTP_PORT=8765

ASYNC_SCHEDULE_BEAT_ENABLED=0
ASYNC_DISPATCH_HTTP_ENABLED=1
ASYNC_RESTORE_DISPATCH_DUE_ON_STARTUP=0
ASYNC_DISPATCH_LOCK_TTL_SECONDS=600
ASYNC_TASK_REDIS_MAX_TTL_SECONDS=604800
ASYNC_DISPATCH_POLL_SECONDS=15
DATABASE_RUN_MIGRATIONS=1
ASYNC_TASK_DB_AUTO_CREATE=0
ASYNC_RESULTS_DEFAULT_LIMIT=20
ASYNC_TASK_MAX_ACTIVE_PER_USER=10
ASYNC_SEARCH_ALL_MAX_PAGES=50
ASYNC_SEARCH_ALL_MAX_RUN_SECONDS=900
ASYNC_SEARCH_DUPLICATE_PAGE_THRESHOLD=5
ASYNC_SEARCH_GUARDS_ASYNC_ONLY=1

YDDM_PROXY_TARGET=https://api.yddm.com
SYNC_PROXY_TARGET=https://test-fskw-feishu.tbpf.com
VITE_ADMIN_API_ORIGIN=https://test-fskw.tbpf.com
EOF
  chmod 600 "$TEST_ROOT/.env.test"
}

write_env_prod() {
  cat > "$PROD_ROOT/.env.master" <<EOF
MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}

APT_DEBIAN_MIRROR=mirrors.aliyun.com
PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
PYTHON_IMAGE=

ENVIRONMENT=prod

DATABASE_URL=${DB_URL}

REDIS_HOST=tbpf-redis
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=3

REDIS_URL=redis://tbpf-redis:6379/3
CELERY_BROKER_URL=redis://tbpf-redis:6379/3
CELERY_RESULT_BACKEND=redis://tbpf-redis:6379/3
CELERY_TASK_ALWAYS_EAGER=0
CELERY_WORKER_POOL=gevent
CELERY_WORKER_CONCURRENCY=4
CELERY_WORKER_PREFETCH_MULTIPLIER=1
CELERY_BEAT_ENABLED=0

API_PUBLIC_HOST=fskw.tbpf.com
ADMIN_PUBLIC_HOST=fskw-admin.tbpf.com
FEISHU_PUBLIC_HOST=fskw-feishu.tbpf.com
TRAEFIK_SYNC_ROUTER_NAME=fkw-sync-prod
TRAEFIK_ADMIN_ROUTER_NAME=fkw-admin-prod
TRAEFIK_FEISHU_ROUTER_NAME=fkw-feishu-prod

HTTP_HOST=0.0.0.0
HTTP_PORT=8765

ASYNC_SCHEDULE_BEAT_ENABLED=0
ASYNC_DISPATCH_HTTP_ENABLED=1
ASYNC_RESTORE_DISPATCH_DUE_ON_STARTUP=0
ASYNC_DISPATCH_LOCK_TTL_SECONDS=600
ASYNC_TASK_REDIS_MAX_TTL_SECONDS=604800
ASYNC_DISPATCH_POLL_SECONDS=15
DATABASE_RUN_MIGRATIONS=1
ASYNC_TASK_DB_AUTO_CREATE=0
ASYNC_RESULTS_DEFAULT_LIMIT=20
ASYNC_TASK_MAX_ACTIVE_PER_USER=10
ASYNC_SEARCH_ALL_MAX_PAGES=50
ASYNC_SEARCH_ALL_MAX_RUN_SECONDS=900
ASYNC_SEARCH_DUPLICATE_PAGE_THRESHOLD=5
ASYNC_SEARCH_GUARDS_ASYNC_ONLY=1

YDDM_PROXY_TARGET=https://api.yddm.com
SYNC_PROXY_TARGET=https://fskw-feishu.tbpf.com
VITE_ADMIN_API_ORIGIN=https://fskw.tbpf.com
EOF
  chmod 600 "$PROD_ROOT/.env.master"
}

write_env_test
write_env_prod

cp -f "$TEST_ROOT/.env.test" "$TEST_ROOT/.env"
chmod 600 "$TEST_ROOT/.env"
echo "remote-setup-env: $TEST_ROOT 已 cp .env.test -> .env"

if docker exec tbpf-mysql mysql -uroot -p"${MYSQL_ROOT_PASSWORD}" -h127.0.0.1 -e \
  "CREATE DATABASE IF NOT EXISTS feishu_keyword CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null; then
  echo "remote-setup-env: feishu_keyword 库已就绪（tbpf-mysql）"
else
  echo "WARN: 无法连接 tbpf-mysql 建库（请确认 traefik 栈已 up：cd /docker/traefik && docker compose up -d mysql redis）"
  echo "      可在 phpMyAdmin 执行: scripts/create_feishu_db.sql"
fi

echo "remote-setup-env: done（口令来源 ${TRAEFIK_ENV}；$TEST_ROOT/.env.test、$PROD_ROOT/.env.master）"

#!/bin/bash
set -euo pipefail

GQS_ENV="${GQS_ENV:-/docker/gaoqingsong-test/server/.env}"
if [ ! -f "$GQS_ENV" ]; then
  echo "ERROR: missing $GQS_ENV"
  exit 1
fi
# shellcheck disable=SC1090
source "$GQS_ENV"

MYSQL_USER="${MYSQL_USER:-lanlang_v1}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-}"
REDIS_PASSWORD="${REDIS_PASSWORD:-}"

mkdir -p /docker/fskw-test/server /docker/fskw-test/python \
  /docker/fskw/server /docker/fskw/python \
  /docker/fskw-test/public/admin /docker/fskw-test/public/feishu \
  /docker/fskw-test/deploy/admin-static /docker/fskw-test/deploy/feishu-static \
  /docker/fskw/public/admin /docker/fskw/public/feishu \
  /docker/fskw/deploy/admin-static /docker/fskw/deploy/feishu-static

DB_URL="mysql+pymysql://${MYSQL_USER}:${MYSQL_PASSWORD}@gqs-mysql:3306/feishu_keyword?charset=utf8mb4"

write_server_test() {
  cat > /docker/fskw-test/server/.env.test <<EOF
APT_DEBIAN_MIRROR=mirrors.aliyun.com
PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
PYTHON_IMAGE=

ENVIRONMENT=test

DATABASE_URL=${DB_URL}

REDIS_HOST=gqs-redis
REDIS_PORT=6379
REDIS_PASSWORD=${REDIS_PASSWORD}
REDIS_DB=2

API_PUBLIC_HOST=fskw-test.tbpf.com
ADMIN_PUBLIC_HOST=fskw-admin-test.tbpf.com
FEISHU_PUBLIC_HOST=fskw-feishu-test.tbpf.com
TRAEFIK_API_ROUTER_NAME=fkw-api-test
TRAEFIK_SYNC_ROUTER_NAME=fkw-sync-test
TRAEFIK_ADMIN_ROUTER_NAME=fkw-admin-test
TRAEFIK_FEISHU_ROUTER_NAME=fkw-feishu-test
EOF
  cp -f /docker/fskw-test/server/.env.test /docker/fskw-test/server/.env
  chmod 600 /docker/fskw-test/server/.env.test /docker/fskw-test/server/.env
  cp -f /docker/fskw-test/server/.env /docker/fskw-test/.env
  chmod 600 /docker/fskw-test/.env
}

write_server_prod() {
  cat > /docker/fskw/server/.env.master <<EOF
APT_DEBIAN_MIRROR=mirrors.aliyun.com
PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
PYTHON_IMAGE=

ENVIRONMENT=prod

DATABASE_URL=${DB_URL}

REDIS_HOST=gqs-redis
REDIS_PORT=6379
REDIS_PASSWORD=${REDIS_PASSWORD}
REDIS_DB=3

API_PUBLIC_HOST=fskw.tbpf.com
ADMIN_PUBLIC_HOST=fskw-admin.tbpf.com
FEISHU_PUBLIC_HOST=fskw-feishu.tbpf.com
TRAEFIK_API_ROUTER_NAME=fkw-api-prod
TRAEFIK_SYNC_ROUTER_NAME=fkw-sync-prod
TRAEFIK_ADMIN_ROUTER_NAME=fkw-admin-prod
TRAEFIK_FEISHU_ROUTER_NAME=fkw-feishu-prod
EOF
  chmod 600 /docker/fskw/server/.env.master
}

write_python_test() {
  cat > /docker/fskw-test/python/.env.test <<EOF
DATABASE_URL=${DB_URL}
REDIS_URL=redis://gqs-redis:6379/2
CELERY_BROKER_URL=
CELERY_RESULT_BACKEND=
DATABASE_RUN_MIGRATIONS=1
ASYNC_TASK_DB_AUTO_CREATE=0
HTTP_HOST=0.0.0.0
HTTP_PORT=8765
ASYNC_DISPATCH_HTTP_ENABLED=1
ASYNC_SCHEDULE_BEAT_ENABLED=0
EOF
  cp -f /docker/fskw-test/python/.env.test /docker/fskw-test/python/.env
  chmod 600 /docker/fskw-test/python/.env.test /docker/fskw-test/python/.env
}

write_python_prod() {
  cat > /docker/fskw/python/.env.master <<EOF
DATABASE_URL=${DB_URL}
REDIS_URL=redis://gqs-redis:6379/3
CELERY_BROKER_URL=
CELERY_RESULT_BACKEND=
DATABASE_RUN_MIGRATIONS=1
ASYNC_TASK_DB_AUTO_CREATE=0
HTTP_HOST=0.0.0.0
HTTP_PORT=8765
ASYNC_DISPATCH_HTTP_ENABLED=1
ASYNC_SCHEDULE_BEAT_ENABLED=0
EOF
  chmod 600 /docker/fskw/python/.env.master
}

write_server_test
write_server_prod
write_python_test
write_python_prod

docker exec gqs-mysql mysql -u"${MYSQL_USER}" -p"${MYSQL_PASSWORD}" -e \
  "CREATE DATABASE IF NOT EXISTS feishu_keyword CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" \
  2>/dev/null || true

echo "remote-setup-env: done"

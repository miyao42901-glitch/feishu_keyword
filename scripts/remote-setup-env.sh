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
MYSQL_ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD:-}"
REDIS_PASSWORD="${REDIS_PASSWORD:-}"

mkdir -p /docker/feishu_keyword-test/server /docker/feishu_keyword-test/python \
  /docker/feishu_keyword/server /docker/feishu_keyword/python \
  /docker/feishu_keyword-test/public/admin /docker/feishu_keyword-test/public/feishu \
  /docker/feishu_keyword-test/deploy/admin-static /docker/feishu_keyword-test/deploy/feishu-static \
  /docker/feishu_keyword/public/admin /docker/feishu_keyword/public/feishu \
  /docker/feishu_keyword/deploy/admin-static /docker/feishu_keyword/deploy/feishu-static

DB_URL="mysql+pymysql://${MYSQL_USER}:${MYSQL_PASSWORD}@gqs-mysql:3306/feishu_keyword?charset=utf8mb4"

write_server_test() {
  cat > /docker/feishu_keyword-test/server/.env.test <<EOF
APT_DEBIAN_MIRROR=mirrors.aliyun.com
PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
PYTHON_IMAGE=

ENVIRONMENT=test

DATABASE_URL=${DB_URL}

REDIS_HOST=gqs-redis
REDIS_PORT=6379
REDIS_PASSWORD=${REDIS_PASSWORD}
REDIS_DB=2

API_PUBLIC_HOST=test-fskw.tbpf.com
ADMIN_PUBLIC_HOST=test-fskw-admin.tbpf.com
FEISHU_PUBLIC_HOST=test-fskw-feishu.tbpf.com
TRAEFIK_API_ROUTER_NAME=test-fkw-api
TRAEFIK_SYNC_ROUTER_NAME=test-fkw-sync
TRAEFIK_ADMIN_ROUTER_NAME=test-fkw-admin
TRAEFIK_FEISHU_ROUTER_NAME=test-fkw-feishu
EOF
  cp -f /docker/feishu_keyword-test/server/.env.test /docker/feishu_keyword-test/server/.env
  chmod 600 /docker/feishu_keyword-test/server/.env.test /docker/feishu_keyword-test/server/.env
  cp -f /docker/feishu_keyword-test/server/.env /docker/feishu_keyword-test/.env
  chmod 600 /docker/feishu_keyword-test/.env
}

write_server_prod() {
  cat > /docker/feishu_keyword/server/.env.master <<EOF
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
  chmod 600 /docker/feishu_keyword/server/.env.master
}

write_python_test() {
  cat > /docker/feishu_keyword-test/python/.env.test <<EOF
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
  cp -f /docker/feishu_keyword-test/python/.env.test /docker/feishu_keyword-test/python/.env
  chmod 600 /docker/feishu_keyword-test/python/.env.test /docker/feishu_keyword-test/python/.env
}

write_python_prod() {
  cat > /docker/feishu_keyword/python/.env.master <<EOF
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
  chmod 600 /docker/feishu_keyword/python/.env.master
}

write_server_test
write_server_prod
write_python_test
write_python_prod

# 仅创建 feishu_keyword 库（不写入 jzl_editor）。lanlang_v1 通常无权 CREATE/GRANT，需 root 授权。
if docker exec gqs-mysql mysql -uroot -p"${MYSQL_ROOT_PASSWORD}" -h127.0.0.1 -e \
  "CREATE DATABASE IF NOT EXISTS feishu_keyword CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   GRANT ALL PRIVILEGES ON feishu_keyword.* TO '${MYSQL_USER}'@'%';
   FLUSH PRIVILEGES;" 2>/dev/null; then
  echo "remote-setup-env: feishu_keyword 库已创建并授权给 ${MYSQL_USER}"
else
  echo "WARN: 无法用 root 授权 feishu_keyword（稿轻松 .env 中 MYSQL_ROOT_PASSWORD 可能与实际 root 不一致）"
  echo "      请在 phpMyAdmin 用 root 执行: scripts/grant-feishu-keyword-only.sql"
  echo "      仅授权 feishu_keyword.*，勿修改 jzl_editor 库内数据"
fi

echo "remote-setup-env: done"

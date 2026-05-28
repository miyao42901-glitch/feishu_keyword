#!/bin/bash
# 在部署主机执行：根据栈根/traefik .env 写入 feishu_keyword 测试/正式 env，并创建 feishu_keyword 库。
set -euo pipefail

TEST_ROOT="${TEST_ROOT:-/docker/feishu_keyword-test}"
PROD_ROOT="${PROD_ROOT:-/docker/feishu_keyword}"
TRAEFIK_ENV="${TRAEFIK_ENV:-/docker/traefik/.env}"

load_mysql_root_password() {
  local pw=""
  for f in "$TEST_ROOT/.env" "$PROD_ROOT/.env" "$TRAEFIK_ENV"; do
    if [ -f "$f" ]; then
      # shellcheck disable=SC1090
      set +u
      source "$f" 2>/dev/null || true
      set -u
      if [ -n "${MYSQL_ROOT_PASSWORD:-}" ]; then
        pw="${MYSQL_ROOT_PASSWORD}"
        break
      fi
    fi
  done
  if [ -z "$pw" ]; then
    echo "ERROR: 未找到 MYSQL_ROOT_PASSWORD（请配置 $TEST_ROOT/.env 或 $TRAEFIK_ENV）"
    exit 1
  fi
  MYSQL_ROOT_PASSWORD="$pw"
}

load_mysql_root_password

MYSQL_USER=root
DB_URL="mysql+pymysql://${MYSQL_USER}:${MYSQL_ROOT_PASSWORD}@tbpf-mysql:3306/feishu_keyword?charset=utf8mb4"

mkdir -p "$TEST_ROOT/server" "$TEST_ROOT/python" \
  "$PROD_ROOT/server" "$PROD_ROOT/python" \
  "$TEST_ROOT/public/admin" "$TEST_ROOT/public/feishu" \
  "$TEST_ROOT/deploy/admin-static" "$TEST_ROOT/deploy/feishu-static" \
  "$PROD_ROOT/public/admin" "$PROD_ROOT/public/feishu" \
  "$PROD_ROOT/deploy/admin-static" "$PROD_ROOT/deploy/feishu-static"

write_server_test() {
  cat > "$TEST_ROOT/server/.env.test" <<EOF
APT_DEBIAN_MIRROR=mirrors.aliyun.com
PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
PYTHON_IMAGE=

ENVIRONMENT=test

DATABASE_URL=${DB_URL}

REDIS_HOST=tbpf-redis
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=2

API_PUBLIC_HOST=test-fskw.tbpf.com
ADMIN_PUBLIC_HOST=test-fskw-admin.tbpf.com
FEISHU_PUBLIC_HOST=test-fskw-feishu.tbpf.com
TRAEFIK_API_ROUTER_NAME=test-fkw-api
TRAEFIK_SYNC_ROUTER_NAME=test-fkw-sync
TRAEFIK_ADMIN_ROUTER_NAME=test-fkw-admin
TRAEFIK_FEISHU_ROUTER_NAME=test-fkw-feishu
EOF
  cp -f "$TEST_ROOT/server/.env.test" "$TEST_ROOT/server/.env"
  chmod 600 "$TEST_ROOT/server/.env.test" "$TEST_ROOT/server/.env"
  cp -f "$TEST_ROOT/server/.env" "$TEST_ROOT/.env"
  chmod 600 "$TEST_ROOT/.env"
}

write_server_prod() {
  cat > "$PROD_ROOT/server/.env.master" <<EOF
APT_DEBIAN_MIRROR=mirrors.aliyun.com
PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
PYTHON_IMAGE=

ENVIRONMENT=prod

DATABASE_URL=${DB_URL}

REDIS_HOST=tbpf-redis
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=3

API_PUBLIC_HOST=fskw.tbpf.com
ADMIN_PUBLIC_HOST=fskw-admin.tbpf.com
FEISHU_PUBLIC_HOST=fskw-feishu.tbpf.com
TRAEFIK_API_ROUTER_NAME=fkw-api-prod
TRAEFIK_SYNC_ROUTER_NAME=fkw-sync-prod
TRAEFIK_ADMIN_ROUTER_NAME=fkw-admin-prod
TRAEFIK_FEISHU_ROUTER_NAME=fkw-feishu-prod
EOF
  chmod 600 "$PROD_ROOT/server/.env.master"
}

write_python_test() {
  cat > "$TEST_ROOT/python/.env.test" <<EOF
DATABASE_URL=${DB_URL}
REDIS_URL=redis://tbpf-redis:6379/2
CELERY_BROKER_URL=
CELERY_RESULT_BACKEND=
DATABASE_RUN_MIGRATIONS=1
ASYNC_TASK_DB_AUTO_CREATE=0
HTTP_HOST=0.0.0.0
HTTP_PORT=8765
ASYNC_DISPATCH_HTTP_ENABLED=1
ASYNC_SCHEDULE_BEAT_ENABLED=0
EOF
  cp -f "$TEST_ROOT/python/.env.test" "$TEST_ROOT/python/.env"
  chmod 600 "$TEST_ROOT/python/.env.test" "$TEST_ROOT/python/.env"
}

write_python_prod() {
  cat > "$PROD_ROOT/python/.env.master" <<EOF
DATABASE_URL=${DB_URL}
REDIS_URL=redis://tbpf-redis:6379/3
CELERY_BROKER_URL=
CELERY_RESULT_BACKEND=
DATABASE_RUN_MIGRATIONS=1
ASYNC_TASK_DB_AUTO_CREATE=0
HTTP_HOST=0.0.0.0
HTTP_PORT=8765
ASYNC_DISPATCH_HTTP_ENABLED=1
ASYNC_SCHEDULE_BEAT_ENABLED=0
EOF
  chmod 600 "$PROD_ROOT/python/.env.master"
}

write_server_test
write_server_prod
write_python_test
write_python_prod

if docker exec tbpf-mysql mysql -uroot -p"${MYSQL_ROOT_PASSWORD}" -h127.0.0.1 -e \
  "CREATE DATABASE IF NOT EXISTS feishu_keyword CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null; then
  echo "remote-setup-env: feishu_keyword 库已就绪（tbpf-mysql）"
else
  echo "WARN: 无法连接 tbpf-mysql 建库（请确认 traefik 栈已 up：cd /docker/traefik && docker compose up -d mysql redis）"
  echo "      可在 phpMyAdmin 执行: scripts/create_feishu_db.sql"
fi

echo "remote-setup-env: done"

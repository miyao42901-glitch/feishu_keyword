#!/bin/bash
set -euo pipefail

MYSQL_USER="${MYSQL_USER:-lanlang_v1}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-lUgKNXSuJrtIcoO}"

mkdir -p /docker/fskw-test/server /docker/fskw/server \
  /docker/fskw-test/public/admin /docker/fskw-test/public/feishu \
  /docker/fskw-test/deploy/admin-static /docker/fskw-test/deploy/feishu-static \
  /docker/fskw/public/admin /docker/fskw/public/feishu \
  /docker/fskw/deploy/admin-static /docker/fskw/deploy/feishu-static

DB_URL="mysql+pymysql://${MYSQL_USER}:${MYSQL_PASSWORD}@gqs-mysql:3306/feishu_keyword?charset=utf8mb4"

write_test() {
  cat > /docker/fskw-test/server/.env.test <<EOF
APT_DEBIAN_MIRROR=mirrors.aliyun.com
PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
PYTHON_IMAGE=

ENVIRONMENT=test

DATABASE_URL=${DB_URL}

REDIS_HOST=gqs-redis
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=2

API_PUBLIC_HOST=fskw-test.tbpf.com
ADMIN_PUBLIC_HOST=fskw-admin-test.tbpf.com
FEISHU_PUBLIC_HOST=fskw-feishu-test.tbpf.com
EOF
  cp -f /docker/fskw-test/server/.env.test /docker/fskw-test/server/.env
  chmod 600 /docker/fskw-test/server/.env.test /docker/fskw-test/server/.env
}

write_master() {
  cat > /docker/fskw/server/.env.master <<EOF
APT_DEBIAN_MIRROR=mirrors.aliyun.com
PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
PYTHON_IMAGE=

ENVIRONMENT=prod

DATABASE_URL=${DB_URL}

REDIS_HOST=gqs-redis
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=3

API_PUBLIC_HOST=fskw.tbpf.com
ADMIN_PUBLIC_HOST=fskw-admin.tbpf.com
FEISHU_PUBLIC_HOST=fskw-feishu.tbpf.com
EOF
  chmod 600 /docker/fskw/server/.env.master
}

write_test
write_master

docker exec gqs-mysql mysql -u"${MYSQL_USER}" -p"${MYSQL_PASSWORD}" -e \
  "CREATE DATABASE IF NOT EXISTS feishu_keyword CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" \
  || docker exec gqs-mysql mysql -uroot -p"${MYSQL_PASSWORD}" -e \
  "CREATE DATABASE IF NOT EXISTS feishu_keyword CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

echo "remote-setup-env: done"

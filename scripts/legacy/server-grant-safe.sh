#!/bin/bash
set -euo pipefail
SOCK=/var/run/mysqld/mysqld.sock
ROOT_PW='lUgKNXSuJrtIcoO'

m() {
  docker exec gqs-mysql mysql --no-defaults --socket="$SOCK" -uroot "$@"
}

cleanup() {
  docker exec gqs-mysql rm -f /etc/mysql/conf.d/zz-feishu-grant.cnf 2>/dev/null || true
  docker restart gqs-mysql >/dev/null
}
trap cleanup EXIT

docker exec gqs-mysql rm -f /etc/mysql/conf.d/zz-feishu-grant.cnf 2>/dev/null || true
docker exec gqs-mysql sh -c 'printf "%s\n" "[mysqld]" "skip-grant-tables=1" > /etc/mysql/conf.d/zz-feishu-grant.cnf'
docker restart gqs-mysql
sleep 12
for i in $(seq 1 25); do m -e "SELECT 1" &>/dev/null && break; sleep 2; done

m -e "FLUSH PRIVILEGES;"
m -e "CREATE DATABASE IF NOT EXISTS feishu_keyword CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
m -e "GRANT ALL PRIVILEGES ON feishu_keyword.* TO 'lanlang_v1'@'%';"
m -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '${ROOT_PW}';" 2>/dev/null || true
m -e "ALTER USER 'root'@'%' IDENTIFIED WITH mysql_native_password BY '${ROOT_PW}';" 2>/dev/null || true
m -e "FLUSH PRIVILEGES;"

docker exec gqs-mysql rm -f /etc/mysql/conf.d/zz-feishu-grant.cnf
trap - EXIT
docker restart gqs-mysql
sleep 15

docker exec gqs-mysql mysql -uroot -p"${ROOT_PW}" -h127.0.0.1 -e "SELECT 'root' AS ok;" 
docker exec gqs-mysql mysql -ulanlang_v1 -p"${ROOT_PW}" -D feishu_keyword -e "SELECT 'fk' AS ok;"

docker exec feishu_keyword-test-api-1 python scripts/init_schema.py
docker exec feishu_keyword-test-api-1 python scripts/seed_demo.py
echo OK

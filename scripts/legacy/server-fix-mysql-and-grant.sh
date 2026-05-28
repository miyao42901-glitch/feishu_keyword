#!/bin/bash
# 恢复 MySQL 3306 + 授权 feishu_keyword + 同步 root 密码（不碰 jzl_editor 数据）
set -euo pipefail

ROOT_PW='lUgKNXSuJrtIcoO'
LANLANG_PW='lUgKNXSuJrtIcoO'
SOCK=/var/run/mysqld/mysqld.sock

mysql_sock() {
  docker exec gqs-mysql mysql -uroot --socket="$SOCK" "$@"
}

echo "==> remove stale skip-grant if any"
docker exec gqs-mysql rm -f /etc/mysql/conf.d/zz-feishu-grant.cnf 2>/dev/null || true

echo "==> enable skip-grant-tables (socket only)"
docker exec gqs-mysql sh -c 'printf "%s\n" "[mysqld]" "skip-grant-tables=1" > /etc/mysql/conf.d/zz-feishu-grant.cnf'
docker restart gqs-mysql
sleep 10
for i in $(seq 1 30); do
  if mysql_sock -e "SELECT 1" &>/dev/null; then break; fi
  sleep 2
done

echo "==> grant feishu_keyword + fix root password"
mysql_sock -e "FLUSH PRIVILEGES;"
mysql_sock -e "CREATE DATABASE IF NOT EXISTS feishu_keyword CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql_sock -e "GRANT ALL PRIVILEGES ON feishu_keyword.* TO 'lanlang_v1'@'%';"
mysql_sock -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '${ROOT_PW}';" 2>/dev/null || \
  mysql_sock -e "CREATE USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '${ROOT_PW}'; GRANT ALL ON *.* TO 'root'@'localhost' WITH GRANT OPTION;"
mysql_sock -e "ALTER USER 'root'@'%' IDENTIFIED WITH mysql_native_password BY '${ROOT_PW}';" 2>/dev/null || \
  mysql_sock -e "CREATE USER 'root'@'%' IDENTIFIED WITH mysql_native_password BY '${ROOT_PW}'; GRANT ALL ON *.* TO 'root'@'%' WITH GRANT OPTION;"
mysql_sock -e "FLUSH PRIVILEGES;"

echo "==> restore normal mysqld (port 3306)"
docker exec gqs-mysql rm -f /etc/mysql/conf.d/zz-feishu-grant.cnf
docker restart gqs-mysql
sleep 15
docker logs gqs-mysql --tail 1 2>&1 | grep -q 'port: 3306' && echo "port 3306 OK" || docker logs gqs-mysql --tail 1

echo "==> verify"
docker exec gqs-mysql mysql -uroot -p"${ROOT_PW}" -h127.0.0.1 -e "SELECT 'root_ok' AS s;"
docker exec gqs-mysql mysql -ulanlang_v1 -p"${LANLANG_PW}" -D feishu_keyword -e "SELECT 'feishu_keyword_ok' AS s;"

API=feishu_keyword-test-api-1
if docker ps --format '{{.Names}}' | grep -qx "$API"; then
  docker exec "$API" python scripts/init_schema.py
  docker exec "$API" python scripts/seed_demo.py
fi

echo "done"

#!/bin/bash
# 重置 gqs-mysql 的 root 密码为 lUgKNXSuJrtIcoO（独立 recovery 容器，避免搞乱运行中 mysqld）
set -euo pipefail

PW='lUgKNXSuJrtIcoO'
DATA=/docker/gaoqingsong/data/mysql
SQL=/tmp/reset-root.sql

cat > "$SQL" <<EOF
USE mysql;
FLUSH PRIVILEGES;
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '${PW}';
ALTER USER 'root'@'%' IDENTIFIED WITH mysql_native_password BY '${PW}';
FLUSH PRIVILEGES;
EOF

echo "==> stop gqs-mysql"
docker stop gqs-mysql

echo "==> recovery container with skip-grant-tables"
docker rm -f gqs-mysql-recovery 2>/dev/null || true
docker run -d --name gqs-mysql-recovery \
  -v "${DATA}:/var/lib/mysql" \
  mysql:8.0 \
  mysqld --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci \
  --default-authentication-plugin=mysql_native_password \
  --skip-grant-tables

for i in $(seq 1 40); do
  if docker exec gqs-mysql-recovery mysqladmin --no-defaults --socket=/var/run/mysqld/mysqld.sock ping &>/dev/null; then
    break
  fi
  sleep 2
done

echo "==> apply password"
docker cp "$SQL" gqs-mysql-recovery:/tmp/reset-root.sql
docker exec gqs-mysql-recovery sh -c 'mysql --no-defaults --socket=/var/run/mysqld/mysqld.sock -uroot < /tmp/reset-root.sql'

echo "==> stop recovery, start gqs-mysql"
docker stop gqs-mysql-recovery
docker rm gqs-mysql-recovery
docker start gqs-mysql
sleep 8
docker exec gqs-mysql rm -f /etc/mysql/conf.d/zz-reset-root.cnf 2>/dev/null || true
docker restart gqs-mysql
sleep 18

echo "==> verify port 3306 + root login"
docker logs gqs-mysql 2>&1 | grep 'port:' | tail -1
docker exec gqs-mysql mysql -uroot -p"${PW}" -h127.0.0.1 -e "SELECT USER() AS u;"
echo "root reset OK"

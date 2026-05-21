#!/bin/bash
set -euo pipefail

MYSQL_SOCK=/var/run/mysqld/mysqld.sock
LANLANG_PW=lUgKNXSuJrtIcoO

mysql_root() {
  docker exec gqs-mysql mysql -uroot --socket="$MYSQL_SOCK" "$@"
}

wait_mysql_sock() {
  for i in $(seq 1 40); do
    if mysql_root -e "SELECT 1" &>/dev/null; then
      return 0
    fi
    sleep 2
  done
  echo "ERROR: mysql socket not ready"
  return 1
}

echo "==> 1) 临时 skip-grant-tables"
docker exec gqs-mysql sh -c 'printf "%s\n" "[mysqld]" "skip-grant-tables=1" > /etc/mysql/conf.d/zz-feishu-grant.cnf'
docker restart gqs-mysql
sleep 8
wait_mysql_sock

echo "==> 2) GRANT feishu_keyword only"
mysql_root -e "FLUSH PRIVILEGES;"
mysql_root -e "CREATE DATABASE IF NOT EXISTS feishu_keyword CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql_root -e "GRANT ALL PRIVILEGES ON feishu_keyword.* TO 'lanlang_v1'@'%';"
mysql_root -e "FLUSH PRIVILEGES;"

echo "==> 3) 恢复正常 mysqld"
docker exec gqs-mysql rm -f /etc/mysql/conf.d/zz-feishu-grant.cnf
docker restart gqs-mysql
sleep 12
for i in $(seq 1 30); do
  if docker exec gqs-mysql mysql -ulanlang_v1 -p"${LANLANG_PW}" -D feishu_keyword -e "SELECT 1" &>/dev/null; then
    echo "lanlang_v1 -> feishu_keyword OK"
    break
  fi
  sleep 2
done

API_CTN=feishu_keyword-test-api-1
if ! docker ps --format '{{.Names}}' | grep -qx "$API_CTN"; then
  echo "ERROR: $API_CTN not running"
  exit 1
fi

echo "==> 4) init_schema + seed_demo"
docker exec "$API_CTN" python scripts/init_schema.py
docker exec "$API_CTN" python scripts/seed_demo.py

echo "==> 5) login test"
curl -sS -X POST https://test-fskw.tbpf.com/api/admin/v1/system/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"Admin123a"}'
echo ""
echo "done"

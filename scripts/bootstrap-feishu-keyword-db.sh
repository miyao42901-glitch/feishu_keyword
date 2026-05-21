#!/bin/bash
# 在 feishu_keyword 已 GRANT 后，于测试栈 api 容器内建表+种子（只连 feishu_keyword）。
set -euo pipefail

STACK="${STACK:-/docker/feishu_keyword-test}"
API_CTN="${API_CTN:-feishu_keyword-test-api-1}"

if ! docker ps --format '{{.Names}}' | grep -qx "$API_CTN"; then
  echo "ERROR: container $API_CTN not running"
  exit 1
fi

echo "==> init_schema (feishu_keyword only)"
docker exec "$API_CTN" python scripts/init_schema.py
echo "==> seed_demo"
docker exec "$API_CTN" python scripts/seed_demo.py
echo "done"

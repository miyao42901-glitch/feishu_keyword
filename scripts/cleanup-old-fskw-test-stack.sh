#!/bin/bash
# 下线旧测试栈容器（fskw-test.tbpf.com / fkw-api-test 等），避免与 feishu_keyword-test（test-fskw.*）Traefik 路由重复。
# 在部署主机执行：bash scripts/cleanup-old-fskw-test-stack.sh
set -euo pipefail

OLD_PROJECT="${OLD_PROJECT:-fskw-test}"
NAMES=$(docker ps -a --filter "name=${OLD_PROJECT}-" --format '{{.Names}}' || true)

if [ -z "$NAMES" ]; then
  echo "cleanup: 未发现 ${OLD_PROJECT}-* 容器，无需处理"
  exit 0
fi

echo "cleanup: 将停止并删除以下容器："
echo "$NAMES"
docker stop $NAMES 2>/dev/null || true
docker rm $NAMES 2>/dev/null || true

if [ -d /docker/fskw-test ]; then
  echo "cleanup: 旧目录 /docker/fskw-test 仍存在（仅静态残留，可手工 rm -rf 确认无数据后删除）"
fi

echo "cleanup: done。Traefik 中 fskw-test.tbpf.com / fkw-api-test 路由应已消失。"

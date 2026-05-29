#!/usr/bin/env bash
# 打包部署产物为 deploy.pkg.tar.gz（不含栈根生效 .env；含占位 .env.test|.env.master）
# 用法：bash scripts/ci-pack-deploy.sh test|prod
set -euo pipefail

ENV_MODE="${1:-}"
if [[ "$ENV_MODE" != "test" && "$ENV_MODE" != "prod" ]]; then
  echo "usage: ci-pack-deploy.sh test|prod"
  exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PKG_NAME="${PKG_NAME:-deploy.pkg.tar.gz}"
rm -f "$PKG_NAME"

if [[ "$ENV_MODE" == "test" ]]; then
  ENV_TEMPLATE=".env.test"
else
  ENV_TEMPLATE=".env.master"
fi

for path in docker-compose.yml server public/admin public/feishu \
  deploy/admin-static deploy/feishu-static deploy/BUILD_INFO "$ENV_TEMPLATE"; do
  if [[ ! -e "$path" ]]; then
    echo "ERROR: 打包缺少 $path"
    exit 1
  fi
done

echo "==> 打包 $PKG_NAME"
tar czf "$PKG_NAME" \
  --exclude='.venv' \
  --exclude='venv' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='server/.env' \
  docker-compose.yml \
  server \
  public/admin \
  public/feishu \
  deploy/admin-static \
  deploy/feishu-static \
  deploy/BUILD_INFO \
  "$ENV_TEMPLATE"

ls -lh "$PKG_NAME"
echo "ci-pack-deploy: ok ($ENV_MODE)"

#!/usr/bin/env bash
# Shell Runner：编译 admin + feishu 到 public/（Vite envDir=仓根）
# 用法：bash scripts/ci-build-frontend.sh test|prod
set -euo pipefail

ENV_MODE="${1:-}"
if [[ "$ENV_MODE" != "test" && "$ENV_MODE" != "prod" ]]; then
  echo "usage: ci-build-frontend.sh test|prod"
  exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

ensure_node() {
  if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
    node -v
    npm -v
    return 0
  fi
  if command -v apt-get >/dev/null 2>&1; then
    apt-get update -qq
    apt-get install -y -qq nodejs npm >/dev/null 2>&1 || true
  elif command -v apk >/dev/null 2>&1; then
    apk add --no-cache nodejs npm >/dev/null 2>&1 || true
  fi
  if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
    echo "ERROR: Runner 需要 Node.js 18+ 与 npm（请安装或配置 Shell Runner）"
    exit 1
  fi
}

ensure_node

if [[ "$ENV_MODE" == "test" ]]; then
  ENV_SRC=".env.test"
  BUILD_SCRIPT="build:public:test"
else
  ENV_SRC=".env.master"
  BUILD_SCRIPT="build:public:prod"
fi

if [[ ! -f "$ENV_SRC" ]]; then
  echo "ERROR: 缺少仓根 $ENV_SRC"
  exit 1
fi

echo "==> 使用 $ENV_SRC 覆盖 .env（Vite envDir=仓根）"
cp -f "$ENV_SRC" .env

echo "==> admin npm ci + $BUILD_SCRIPT"
(
  cd admin
  npm ci
  npm run "$BUILD_SCRIPT"
)

echo "==> feishu npm ci + $BUILD_SCRIPT"
(
  cd feishu
  npm ci
  npm run "$BUILD_SCRIPT"
)

if [[ ! -f public/admin/index.html ]]; then
  echo "ERROR: 缺少 public/admin/index.html"
  exit 1
fi
if [[ ! -f public/feishu/index.html ]]; then
  echo "ERROR: 缺少 public/feishu/index.html"
  exit 1
fi

if [[ "$ENV_MODE" == "prod" ]]; then
  if grep -rq 'test-fskw' public/feishu/assets public/admin/assets 2>/dev/null; then
    echo "WARN: 静态资源含 test-fskw，正式域可能异常"
  fi
fi

echo "ci-build-frontend: ok ($ENV_MODE)"

#!/usr/bin/env bash
# 在部署主机执行：解压 deploy.pkg.tar.gz → docker compose up（由 CI 经 ssh 传入）
# 环境变量：DEPLOY_ROOT、ENV_FILE（.env.test|.env.master）、COMPOSE_PROFILES、PKG_NAME
set -euo pipefail

DEPLOY_ROOT="${DEPLOY_ROOT:?DEPLOY_ROOT required}"
ENV_FILE="${ENV_FILE:?ENV_FILE required}"
COMPOSE_PROFILES="${COMPOSE_PROFILES:---profile admin --profile feishu --profile worker}"
PKG_NAME="${PKG_NAME:-deploy.pkg.tar.gz}"

mkdir -p "$DEPLOY_ROOT"
cd "$DEPLOY_ROOT"

if [[ ! -f "$PKG_NAME" ]]; then
  echo "ERROR: 缺少 $DEPLOY_ROOT/$PKG_NAME"
  exit 1
fi

ENV_BAK=""
if [[ -f "$ENV_FILE" ]]; then
  ENV_BAK="$(mktemp)"
  cp -a "$ENV_FILE" "$ENV_BAK"
fi

echo "==> 解压 $PKG_NAME → $DEPLOY_ROOT"
tar -xzf "$PKG_NAME"
rm -f "$PKG_NAME"

if [[ -n "$ENV_BAK" ]]; then
  cp -a "$ENV_BAK" "$ENV_FILE"
  rm -f "$ENV_BAK"
  echo "==> 保留远端已有 $ENV_FILE（未用包内占位覆盖）"
elif [[ -f "$ENV_FILE" ]]; then
  chmod 600 "$ENV_FILE"
  echo "WARN: 首次落盘 $ENV_FILE（包内占位模板），请 SSH 修改真实口令"
else
  echo "ERROR: 解压后仍缺少 $ENV_FILE"
  exit 1
fi

if [[ -f "server/$ENV_FILE" ]] && [[ ! -f "$ENV_FILE" ]]; then
  echo "迁移: server/$ENV_FILE -> 栈根 $ENV_FILE"
  cp -f "server/$ENV_FILE" "$ENV_FILE"
  chmod 600 "$ENV_FILE"
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: 远端缺少栈根 $ENV_FILE，请执行: bash scripts/remote-setup-env.sh"
  exit 1
fi

echo "==> 使用 $ENV_FILE 覆盖 .env（Compose 与容器均读 .env）"
cp -f "$ENV_FILE" .env
chmod 600 .env

if ! docker ps --format '{{.Names}}' | grep -q '^tbpf-mysql$'; then
  echo "WARN: tbpf-mysql 未运行，请先: cd /docker/traefik && docker compose up -d mysql redis"
fi

# shellcheck disable=SC2086
docker compose $COMPOSE_PROFILES down --remove-orphans 2>/dev/null || true
# shellcheck disable=SC2086
docker compose $COMPOSE_PROFILES up -d --build
# shellcheck disable=SC2086
docker compose $COMPOSE_PROFILES ps

echo "==> 等待 sync-api HTTP 就绪（feishu-web -> /api/v1/health）..."
health_ok=0
for i in $(seq 1 40); do
  # shellcheck disable=SC2086
  if docker compose $COMPOSE_PROFILES exec -T feishu-web wget -qO- --timeout=5 http://sync-api:8765/api/v1/health >/dev/null 2>&1; then
    health_ok=1
    echo "sync-api health ok (attempt $i)"
    break
  fi
  echo "等待 sync-api... ($i/40)"
  sleep 3
done

if [[ "$health_ok" -ne 1 ]]; then
  echo "ERROR: feishu-web 无法访问 sync-api:8765/api/v1/health"
  # shellcheck disable=SC2086
  docker compose $COMPOSE_PROFILES logs feishu-web --tail 30 || true
  # shellcheck disable=SC2086
  docker compose $COMPOSE_PROFILES logs sync-api --tail 80 || true
  exit 1
fi

# shellcheck disable=SC2086
docker compose $COMPOSE_PROFILES exec -T feishu-web wget -qO- http://sync-api:8765/api/v1/health | head -c 400
echo ""
echo "ci-deploy-remote: done ($DEPLOY_ROOT)"

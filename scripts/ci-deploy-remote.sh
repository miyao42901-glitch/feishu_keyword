#!/usr/bin/env bash
# 在部署主机执行：解压 deploy.pkg.tar.gz → docker compose up（由 CI 经 ssh 传入）
# 环境变量：DEPLOY_ROOT、ENV_FILE（.env.test|.env.master）、COMPOSE_PROFILES、PKG_NAME
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=env-mysql-from-traefik.sh
source "$SCRIPT_DIR/env-mysql-from-traefik.sh"

DEPLOY_ROOT="${DEPLOY_ROOT:?DEPLOY_ROOT required}"
ENV_FILE="${ENV_FILE:?ENV_FILE required}"
COMPOSE_PROFILES="${COMPOSE_PROFILES:---profile admin --profile feishu --profile worker}"
PKG_NAME="${PKG_NAME:-deploy.pkg.tar.gz}"

# 远端保留口令等敏感项；若下列键在远端为空，则用本次 CI 包内模板补全（避免 api 因 CELERY 未配置崩溃）
# MySQL 口令见 merge_db_credentials_from_traefik（/docker/traefik/.env）
ENV_PATCH_KEYS=(
  CELERY_BROKER_URL
  CELERY_RESULT_BACKEND
  ADMIN_PUBLIC_HOST
  TRAEFIK_ADMIN_ROUTER_NAME
  VITE_ADMIN_API_ORIGIN
)

env_get() {
  local file="$1" key="$2"
  grep -E "^${key}=" "$file" 2>/dev/null | head -1 | cut -d= -f2- || true
}

env_set() {
  local file="$1" key="$2" val="$3"
  if grep -q "^${key}=" "$file"; then
    sed -i "s|^${key}=.*|${key}=${val}|" "$file"
  else
    echo "${key}=${val}" >> "$file"
  fi
}

is_env_placeholder() {
  local val="${1//[[:space:]]/}"
  [[ -z "$val" || "$val" == "PASSWORD" || "$val" == "your_root_password" ]]
}

is_database_url_placeholder() {
  local val="$1"
  if is_env_placeholder "$val"; then
    return 0
  fi
  if [[ "$val" == *":PASSWORD@"* || "$val" == *":your_root_password@"* || "$val" == *"root:@"* ]]; then
    return 0
  fi
  return 1
}

should_patch_env_key() {
  local key="$1" remote_val="$2" pkg_val="$3"
  if [[ -z "${pkg_val//[[:space:]]/}" ]]; then
    return 1
  fi
  [[ -z "${remote_val//[[:space:]]/}" ]]
}

merge_empty_env_from_package() {
  local target="$1" pkg="$2"
  local key remote_val pkg_val
  for key in "${ENV_PATCH_KEYS[@]}"; do
    remote_val="$(env_get "$target" "$key")"
    pkg_val="$(env_get "$pkg" "$key")"
    if should_patch_env_key "$key" "$remote_val" "$pkg_val"; then
      env_set "$target" "$key" "$pkg_val"
      echo "==> 补全 ${ENV_FILE}: ${key}（远端为空，采用包内模板）"
    fi
  done
  # Celery 仍空时，回退为 REDIS_URL（与仓根 .env.test 约定一致）
  remote_val="$(env_get "$target" CELERY_BROKER_URL)"
  if [[ -z "${remote_val//[[:space:]]/}" ]]; then
    local redis_url
    redis_url="$(env_get "$target" REDIS_URL)"
    if [[ -n "${redis_url//[[:space:]]/}" ]]; then
      env_set "$target" CELERY_BROKER_URL "$redis_url"
      env_set "$target" CELERY_RESULT_BACKEND "$redis_url"
      echo "==> 补全 ${ENV_FILE}: CELERY_* ← REDIS_URL"
    fi
  fi
}

merge_db_credentials_from_traefik() {
  local target="$1"
  local pw db_url
  if ! pw="$(load_mysql_root_password)"; then
    echo "WARN: 未从 ${TRAEFIK_ENV} 读取 MYSQL_ROOT_PASSWORD"
    return 0
  fi
  if is_env_placeholder "$(env_get "$target" MYSQL_ROOT_PASSWORD)"; then
    env_set "$target" MYSQL_ROOT_PASSWORD "$pw"
    echo "==> 补全 ${ENV_FILE}: MYSQL_ROOT_PASSWORD ← ${TRAEFIK_ENV}"
  fi
  if is_database_url_placeholder "$(env_get "$target" DATABASE_URL)"; then
    db_url="$(build_feishu_database_url "$pw")"
    env_set "$target" DATABASE_URL "$db_url"
    echo "==> 补全 ${ENV_FILE}: DATABASE_URL ← ${TRAEFIK_ENV}"
  fi
}

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

ENV_FROM_PKG="$(mktemp)"
cp -a "$ENV_FILE" "$ENV_FROM_PKG"

if [[ -n "$ENV_BAK" ]]; then
  cp -a "$ENV_BAK" "$ENV_FILE"
  rm -f "$ENV_BAK"
  echo "==> 保留远端已有 $ENV_FILE（未用包内占位覆盖口令）"
  merge_empty_env_from_package "$ENV_FILE" "$ENV_FROM_PKG"
  merge_db_credentials_from_traefik "$ENV_FILE"
elif [[ -f "$ENV_FILE" ]]; then
  chmod 600 "$ENV_FILE"
  merge_db_credentials_from_traefik "$ENV_FILE"
  echo "WARN: 首次落盘 ${ENV_FILE}（包内占位模板）；MySQL 已从 ${TRAEFIK_ENV} 补全（若可读）"
else
  rm -f "$ENV_FROM_PKG"
  echo "ERROR: 解压后仍缺少 $ENV_FILE"
  exit 1
fi
rm -f "$ENV_FROM_PKG"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: 远端缺少栈根 $ENV_FILE，请执行: bash scripts/remote-setup-env.sh"
  exit 1
fi

if is_database_url_placeholder "$(env_get "$ENV_FILE" DATABASE_URL)"; then
  echo "ERROR: DATABASE_URL 仍为占位，请配置 ${TRAEFIK_ENV} 后执行: bash scripts/remote-setup-env.sh"
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

echo "==> 等待 api HTTP 就绪（feishu-web -> /api/v1/health）..."
health_ok=0
for i in $(seq 1 40); do
  # shellcheck disable=SC2086
  if docker compose $COMPOSE_PROFILES exec -T feishu-web wget -qO- --timeout=5 http://api:8765/api/v1/health >/dev/null 2>&1; then
    health_ok=1
    echo "api health ok (attempt $i)"
    break
  fi
  echo "等待 api... ($i/40)"
  sleep 3
done

if [[ "$health_ok" -ne 1 ]]; then
  echo "ERROR: feishu-web 无法访问 api:8765/api/v1/health"
  # shellcheck disable=SC2086
  docker compose $COMPOSE_PROFILES logs feishu-web --tail 30 || true
  # shellcheck disable=SC2086
  docker compose $COMPOSE_PROFILES logs api --tail 80 || true
  exit 1
fi

# shellcheck disable=SC2086
docker compose $COMPOSE_PROFILES exec -T feishu-web wget -qO- http://api:8765/api/v1/health | head -c 400
echo ""
echo "ci-deploy-remote: done ($DEPLOY_ROOT)"

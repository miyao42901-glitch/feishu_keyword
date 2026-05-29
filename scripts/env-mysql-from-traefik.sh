#!/usr/bin/env bash
# 从 traefik 栈 .env 读取 MYSQL_ROOT_PASSWORD，供 remote-setup-env / ci-deploy-remote 共用。
# 优先级：/docker/traefik/.env → 当前部署栈根 .env → 测试/正式栈根 .env

TRAEFIK_ENV="${TRAEFIK_ENV:-/docker/traefik/.env}"
TEST_ROOT="${TEST_ROOT:-/docker/feishu_keyword-test}"
PROD_ROOT="${PROD_ROOT:-/docker/feishu_keyword}"

_is_mysql_password_usable() {
  local val="${1//[[:space:]]/}"
  [[ -n "$val" && "$val" != "PASSWORD" && "$val" != "your_root_password" ]]
}

read_mysql_root_password_from_file() {
  local f="$1" line pw
  [[ -f "$f" ]] || return 1
  line="$(grep -E '^MYSQL_ROOT_PASSWORD=' "$f" 2>/dev/null | head -1 || true)"
  pw="${line#MYSQL_ROOT_PASSWORD=}"
  if _is_mysql_password_usable "$pw"; then
    printf '%s' "$pw"
    return 0
  fi
  return 1
}

load_mysql_root_password() {
  local pw="" f
  local candidates=(
    "$TRAEFIK_ENV"
    "${DEPLOY_ROOT:-}/.env"
    "$TEST_ROOT/.env"
    "$PROD_ROOT/.env"
  )
  for f in "${candidates[@]}"; do
    [[ -n "$f" && -f "$f" ]] || continue
    if pw="$(read_mysql_root_password_from_file "$f")"; then
      printf '%s' "$pw"
      return 0
    fi
  done
  return 1
}

build_feishu_database_url() {
  local pw="$1"
  printf 'mysql+pymysql://root:%s@tbpf-mysql:3306/feishu_keyword?charset=utf8mb4' "$pw"
}

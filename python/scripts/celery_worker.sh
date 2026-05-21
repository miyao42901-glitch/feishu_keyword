#!/usr/bin/env bash
# Celery Worker：gevent 池，4 并发
set -euo pipefail
cd "$(dirname "$0")/.."
POOL="${CELERY_WORKER_POOL:-gevent}"
CONCURRENCY="${CELERY_WORKER_CONCURRENCY:-4}"
PREFETCH="${CELERY_WORKER_PREFETCH_MULTIPLIER:-1}"
exec celery -A social_platform.tasks.celery_app worker -l info \
  -P "$POOL" -c "$CONCURRENCY" --prefetch-multiplier="$PREFETCH"

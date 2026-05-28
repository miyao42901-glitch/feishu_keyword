# Celery Worker：gevent 池，4 并发（与 .env 中 CELERY_WORKER_* 一致）
Set-Location $PSScriptRoot\..
$env:CELERY_WORKER_POOL = if ($env:CELERY_WORKER_POOL) { $env:CELERY_WORKER_POOL } else { "gevent" }
$concurrency = if ($env:CELERY_WORKER_CONCURRENCY) { $env:CELERY_WORKER_CONCURRENCY } else { "4" }
$prefetch = if ($env:CELERY_WORKER_PREFETCH_MULTIPLIER) { $env:CELERY_WORKER_PREFETCH_MULTIPLIER } else { "1" }
celery -A social_platform.tasks.celery_app worker -l info -P $env:CELERY_WORKER_POOL -c $concurrency --prefetch-multiplier=$prefetch

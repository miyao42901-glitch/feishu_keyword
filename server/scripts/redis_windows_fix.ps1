# Windows 本地 Redis：缓解 BGSAVE fork 失败导致 MISCONF、Celery 无法写入
# 用法（在 python 目录或任意路径）:
#   powershell -ExecutionPolicy Bypass -File scripts/redis_windows_fix.ps1
#
# 说明：Broker/调度数据可从 MySQL 恢复；开发环境允许 bgsave 失败时继续写入。
# 生产请在 Linux Redis 上保持 stop-writes-on-bgsave-error yes，并保证持久化正常。

$ErrorActionPreference = "Stop"

function Invoke-RedisCli {
    param([string[]]$Args)
    $out = & redis-cli @Args 2>&1
    if ($LASTEXITCODE -ne 0) { throw "redis-cli failed: $out" }
    return $out
}

Write-Host "PING..."
Invoke-RedisCli @("PING") | Out-Host

Write-Host "Setting stop-writes-on-bgsave-error=no (dev-friendly)..."
Invoke-RedisCli @("CONFIG", "SET", "stop-writes-on-bgsave-error", "no") | Out-Host

Write-Host "Persisting to redis.conf (CONFIG REWRITE)..."
try {
    Invoke-RedisCli @("CONFIG", "REWRITE") | Out-Host
} catch {
    Write-Warning "CONFIG REWRITE failed; runtime setting still applies until Redis restart. Edit redis.conf manually."
}

Write-Host "Testing write on db 3 (typical REDIS_URL suffix)..."
Invoke-RedisCli @("-n", "3", "SET", "__feishu_health__", "ok") | Out-Host
Invoke-RedisCli @("-n", "3", "DEL", "__feishu_health__") | Out-Host

Write-Host "Done. If BGSAVE still fails, check D:\Redis\server_log.txt for 'fork operation failed' or OOM."

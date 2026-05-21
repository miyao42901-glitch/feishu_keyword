/**
 * 抖音 / 小红书 search-page 共用：HTTP、任务配置解析、去重收集。
 */

import {
  assertSyncEnvelopeOk,
  buildSyncApiHeaders,
  extractSyncResultDiagnostics,
  extractSyncResultPageMeta,
  getSyncApiBase,
  isSyncHttpError,
  SyncHttpError,
  type SyncFetchContext,
} from '@/lib/sync-api-common'
import { refreshYddmUserBalance } from '@/lib/refresh-yddm-balance'
import { primeSyncEndpointDiscountAfterSuccess } from '@/lib/sync-set-discount'

/** 第三方 search-page 不稳定时，HTTP 5xx 最多重试次数 */
export const SYNC_SEARCH_PAGE_MAX_ATTEMPTS = 3

const SYNC_SEARCH_RETRY_DELAY_MS = 400

function isRetryableSyncHttpStatus(status: number): boolean {
  return status === 500 || status === 502 || status === 503 || status === 504
}

function sleepMs(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export type SyncSortType = '0' | '1' | '2'

export function readConfigArray(config: Record<string, unknown>, camel: string, snake?: string): string[] {
  const raw = snake != null ? (config[camel] ?? config[snake]) : config[camel]
  if (!Array.isArray(raw)) return []
  return raw
    .filter((x): x is string => typeof x === 'string')
    .map((s) => s.trim())
    .filter(Boolean)
}

function readKeywordsFromAsyncRefs(config: Record<string, unknown>): string[] {
  const raw = config.asyncTaskRefs ?? config.async_task_refs
  if (!Array.isArray(raw)) return []
  const out: string[] = []
  for (const x of raw) {
    if (!x || typeof x !== 'object') continue
    const kw = String((x as Record<string, unknown>).keyword ?? '').trim()
    if (kw) out.push(kw)
  }
  return [...new Set(out)]
}

/**
 * search-page / async 采集用关键词列表。
 * 兼容 `keywords[]`、`keyword` 字符串、`asyncTaskRefs[].keyword`、YDDM `body.keyword`。
 * 均未配置时仍发起一次请求（`keyword` 为空，由采集服务处理）。
 */
export function readSearchKeywords(config: Record<string, unknown>): string[] {
  let keywords = readConfigArray(config, 'keywords')
  if (!keywords.length) {
    const single = String(config.keyword ?? '').trim()
    if (single) keywords = [single]
  }
  if (!keywords.length) {
    keywords = readKeywordsFromAsyncRefs(config)
  }
  if (!keywords.length) {
    const bodyRaw = config.body
    if (bodyRaw && typeof bodyRaw === 'object' && !Array.isArray(bodyRaw)) {
      const bk = String((bodyRaw as Record<string, unknown>).keyword ?? '').trim()
      if (bk) keywords = [bk]
    }
  }
  return keywords.length ? keywords : ['']
}

export function readDataRange(config: Record<string, unknown>): number {
  const v = config.dataRange ?? config.data_range
  const n = typeof v === 'number' ? v : Number(v)
  if (!Number.isFinite(n) || n < 1) return 20
  return Math.min(100, Math.floor(n))
}

export function buildExcludeWords(config: Record<string, unknown>): string {
  return readConfigArray(config, 'excludeKeywords', 'exclude_keywords').join(' ')
}

/** 表单 `sortOrder` → API `sort_type` */
export function mapSortType(sortOrder: string): SyncSortType {
  switch (sortOrder.trim()) {
    case 'hottest':
      return '1'
    case 'latest':
      return '2'
    default:
      return '0'
  }
}

/**
 * 表单 `publishTime` → 时间范围（抖音 `publish_time` / 小红书 `note_time`）。
 * `0` 不限，`1` 1 天内，`7` 7 天内，`180` 180 天内。
 */
export function mapNoteTime(publishTime: string): string {
  switch (publishTime.trim()) {
    case '1d':
      return '1'
    case '1w':
      return '7'
    case '6m':
      return '180'
    default:
      return '0'
  }
}

export function assertKeywordLength(keyword: string): string {
  const kw = keyword.trim()
  if (kw.length > 100) {
    throw new Error('搜索关键词不能超过 100 个字')
  }
  return kw
}

export async function getSyncApiJson(input: {
  path: string
  platformLabel: string
  ctx: SyncFetchContext
  /** 可选 Query，如 Apifox `X-API-KEY`（与 Header `x-api-key` 二选一或并存） */
  query?: Record<string, string>
}): Promise<unknown> {
  let url = `${getSyncApiBase()}${input.path}`
  if (input.query && Object.keys(input.query).length > 0) {
    const qs = new URLSearchParams(input.query).toString()
    url += url.includes('?') ? `&${qs}` : `?${qs}`
  }
  const headers = buildSyncApiHeaders(input.ctx)
  const res = await fetch(url, {
    method: 'GET',
    headers: headers as Record<string, string>,
  })
  const text = await res.text()
  let parsed: unknown = null
  if (text) {
    try {
      parsed = JSON.parse(text) as unknown
    } catch {
      if (!res.ok) throw new SyncHttpError(`${input.platformLabel} HTTP ${res.status}`, res.status)
      throw new Error(`${input.platformLabel}响应不是合法 JSON`)
    }
  }
  if (!res.ok) {
    const detail = formatSyncHttpErrorDetail(parsed, text, res.status)
    if (import.meta.env.DEV) {
      console.warn(`[sync-api] GET ${url}`, { status: res.status, detail, headers: headers['X-User-Id'] })
    }
    const msg = detail.trim() ? detail.trim() : `${input.platformLabel} HTTP ${res.status}`
    throw new SyncHttpError(msg, res.status)
  }
  assertSyncEnvelopeOk(parsed)
  return parsed
}

function formatSyncHttpErrorDetail(parsed: unknown, text: string, status: number): string {
  if (parsed && typeof parsed === 'object' && parsed !== null) {
    const o = parsed as Record<string, unknown>
    const msg = String(o.msg ?? o.message ?? '').trim()
    const code = o.code != null ? String(o.code) : ''
    if (msg && code) return `${msg}（code=${code}）`
    if (msg) return msg
    if (code) return `HTTP ${status}（code=${code}）`
  }
  const t = text.trim()
  if (t) return t.length > 200 ? `${t.slice(0, 200)}…` : t
  if (status === 401) return '未授权：请重新登录，并确认顶部授权码与当前账户一致'
  if (status === 400) return '请求参数错误：请检查任务配置（关键词、开始/结束时间、条数等）'
  return ''
}

function logSyncApiRequest(
  method: string,
  url: string,
  meta: { status: number; platformLabel: string; body?: Record<string, unknown>; detail?: string },
): void {
  if (!import.meta.env.DEV) return
  const itemCount =
    meta.body == null
      ? undefined
      : (() => {
          try {
            const preview = JSON.stringify(meta.body)
            return preview.length > 800 ? `${preview.slice(0, 800)}…` : preview
          } catch {
            return undefined
          }
        })()
  console.log(`[sync-api] ${method} ${url}`, {
    platform: meta.platformLabel,
    status: meta.status,
    ...(itemCount != null ? { body: itemCount } : {}),
    ...(meta.detail ? { detail: meta.detail } : {}),
  })
}

export async function postSyncApiJson(input: {
  path: string
  platformLabel: string
  body: Record<string, unknown>
  ctx: SyncFetchContext
}): Promise<unknown> {
  const url = `${getSyncApiBase()}${input.path}`
  const headers = buildSyncApiHeaders(input.ctx)
  const res = await fetch(url, {
    method: 'POST',
    headers: headers as Record<string, string>,
    body: JSON.stringify(input.body),
  })
  const text = await res.text()
  let parsed: unknown = null
  if (text) {
    try {
      parsed = JSON.parse(text) as unknown
    } catch {
      if (!res.ok) {
        logSyncApiRequest('POST', url, {
          status: res.status,
          platformLabel: input.platformLabel,
          body: input.body,
          detail: text.slice(0, 300),
        })
        throw new SyncHttpError(`${input.platformLabel} HTTP ${res.status}`, res.status)
      }
      throw new Error(`${input.platformLabel}响应不是合法 JSON`)
    }
  }
  if (!res.ok) {
    const detail = formatSyncHttpErrorDetail(parsed, text, res.status)
    logSyncApiRequest('POST', url, {
      status: res.status,
      platformLabel: input.platformLabel,
      body: input.body,
      detail: detail.trim() ? detail.trim().slice(0, 300) : text.slice(0, 300),
    })
    const msg = detail.trim() ? detail.trim() : `${input.platformLabel} HTTP ${res.status}`
    throw new SyncHttpError(msg, res.status)
  }
  assertSyncEnvelopeOk(parsed)
  const diag = extractSyncResultDiagnostics(parsed)
  logSyncApiRequest('POST', url, {
    status: res.status,
    platformLabel: input.platformLabel,
    body: input.body,
    detail: `items=${diag.itemCount}`,
  })
  if (import.meta.env.DEV && diag.itemCount === 0) {
    console.warn(`[sync-api] ${input.platformLabel} 返回 0 条`, {
      path: input.path,
      balance: diag.balance,
      insufficientBalance: diag.insufficientBalance,
      error: diag.error,
      rawDataLength: diag.rawDataLength,
      resultKeys: diag.resultKeys,
      nextCursor: diag.nextCursor,
      nextLogid: diag.nextLogid,
      payloadPreview: (() => {
        try {
          const s = JSON.stringify(parsed)
          return s.length > 1200 ? `${s.slice(0, 1200)}…` : s
        } catch {
          return parsed
        }
      })(),
    })
  }
  return parsed
}

export async function postSyncSearchPage(input: {
  path: string
  platformLabel: string
  body: Record<string, unknown>
  ctx: SyncFetchContext
}): Promise<unknown> {
  let lastErr: unknown
  for (let attempt = 1; attempt <= SYNC_SEARCH_PAGE_MAX_ATTEMPTS; attempt++) {
    try {
      const parsed = await postSyncApiJson(input)
      await primeSyncEndpointDiscountAfterSuccess(input.path, input.ctx)
      const pageMeta = extractSyncResultPageMeta(parsed)
      if (pageMeta.insufficientBalance) {
        throw new Error('账户积分不足，无法继续采集')
      }
      void refreshYddmUserBalance()
      if (attempt > 1 && import.meta.env.DEV) {
        console.log('[sync-api] search-page 重试成功', {
          platform: input.platformLabel,
          attempt,
          path: input.path,
        })
      }
      return parsed
    } catch (err) {
      lastErr = err
      const status = isSyncHttpError(err) ? err.status : 0
      const canRetry = isRetryableSyncHttpStatus(status) && attempt < SYNC_SEARCH_PAGE_MAX_ATTEMPTS
      if (!canRetry) break
      if (import.meta.env.DEV) {
        console.warn('[sync-api] search-page 将重试', {
          platform: input.platformLabel,
          attempt,
          status,
          path: input.path,
        })
      }
      await sleepMs(SYNC_SEARCH_RETRY_DELAY_MS * attempt)
    }
  }
  throw lastErr instanceof Error ? lastErr : new Error(String(lastErr))
}

function pickItemId(item: Record<string, unknown>, idKeys: string[]): string {
  for (const key of idKeys) {
    const v = item[key]
    if (v != null && String(v).trim()) return String(v).trim()
  }
  return ''
}

export function mergeResultItems(input: {
  batch: Record<string, unknown>[]
  collected: Record<string, unknown>[]
  seenIds: Set<string>
  itemIdKeys: string[]
  limit: number
  /** 与 `buildPlatformItemDedupKey` 一致，如 `douyin` */
  platformKey?: string
}): boolean {
  for (const item of input.batch) {
    const id = pickItemId(item, input.itemIdKeys)
    if (id) {
      const dedupKey = input.platformKey ? `${input.platformKey}:${id}` : id
      if (input.seenIds.has(dedupKey)) continue
      input.seenIds.add(dedupKey)
    }
    input.collected.push(item)
    if (input.collected.length >= input.limit) return true
  }
  return input.collected.length >= input.limit
}

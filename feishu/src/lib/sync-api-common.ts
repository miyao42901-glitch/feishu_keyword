/**
 * 采集同步服务（如 192.168.1.11:8765）通用：基址、请求头、响应解析。
 */

/** 采集服务请求头（YDDM 要求 `X-User-Id` 必填） */
export type SyncApiHeaders = {
  'Content-Type': string
  'x-api-key': string
  'X-User-Id': string
  [property: string]: unknown
}

export type SyncFetchContext = {
  apiKey: string
  userId?: string | number | null
  /** YDDM 登录用户手机号，用于 YDDM `POST /admin/set_discount` */
  phoneNum?: string | null
  /** 单次任务 search-page：不调用 `POST /admin/set_discount` */
  skipSetDiscount?: boolean
  /**
   * 当前平台采集会话内是否已成功触发过 `set_discount`（仅在 search-page 成功响应后置 true）。
   * 同一平台翻页复用；切换平台时由 `resetPlatformSyncBillingSession` 重置。
   */
  platformDiscountPrimed?: boolean
}

/** search-page / 同步 HTTP 失败（含 status，供 500 重试判断） */
export class SyncHttpError extends Error {
  readonly status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'SyncHttpError'
    this.status = status
  }
}

export function isSyncHttpError(err: unknown): err is SyncHttpError {
  return err instanceof SyncHttpError
}

/**
 * 同步采集 API 根地址（无末尾 `/`）。
 * - 未配置 `VITE_SYNC_API_BASE`：空字符串，请求走同源 `/api/v1/...`（Vite 或 Nginx 反代到 8765）
 * - 已配置：直连，如 `http://192.168.1.11:8765`（需上游开 CORS）
 */
export function getSyncApiBase(): string {
  const raw = (import.meta.env.VITE_SYNC_API_BASE as string | undefined)?.trim()
  if (raw) return raw.replace(/\/$/, '')
  return ''
}

export function buildSyncApiHeaders(ctx: SyncFetchContext): SyncApiHeaders {
  const key = ctx.apiKey?.trim()
  if (!key) throw new Error('缺少 x-api-key：请先登录并配置 API Key')
  const uid = ctx.userId
  const userId = uid != null ? String(uid).trim() : ''
  if (!userId) {
    throw new Error('缺少 X-User-Id：请先登录 YDDM 账户')
  }
  return {
    'Content-Type': 'application/json',
    'x-api-key': key,
    'X-User-Id': userId,
  }
}

export function assertSyncEnvelopeOk(payload: unknown): void {
  if (!payload || typeof payload !== 'object') return
  const root = payload as Record<string, unknown>
  const code = root.code
  if (code === 0 || code === '0') return
  if (code == null) return
  const msg =
    (typeof root.msg === 'string' && root.msg.trim()) ||
    (typeof root.message === 'string' && root.message.trim()) ||
    `采集接口错误（code=${String(code)}）`
  throw new Error(msg)
}

/** 部分接口把 `data` / `result` 以 JSON 字符串返回 */
function unwrapMaybeJson(value: unknown): unknown {
  if (typeof value !== 'string') return value
  const s = value.trim()
  if (!s.startsWith('{') && !s.startsWith('[')) return value
  try {
    return JSON.parse(s) as unknown
  } catch {
    return value
  }
}

function trySyncResultObjectArray(v: unknown): Record<string, unknown>[] {
  if (!Array.isArray(v)) return []
  return v
    .filter((x): x is Record<string, unknown> => x != null && typeof x === 'object')
    .map(normalizeSyncResultItem)
}

/** 部分接口条目包在 aweme_info / note 等子对象里 */
function normalizeSyncResultItem(item: Record<string, unknown>): Record<string, unknown> {
  const nested =
    item.aweme_info ??
    item.awemeInfo ??
    item.note ??
    item.note_info ??
    item.noteInfo ??
    item.feed ??
    item.video
  if (nested && typeof nested === 'object' && !Array.isArray(nested)) {
    return { ...(nested as Record<string, unknown>), ...item }
  }
  return item
}

function pickSyncResultArrayFromRecord(obj: Record<string, unknown>): Record<string, unknown>[] {
  for (const key of [
    'data',
    'list',
    'items',
    'results',
    'records',
    'rows',
    'aweme_list',
    'awemeList',
    'notes',
    'note_list',
    'noteList',
    'feeds',
    'videos',
  ]) {
    const hit = trySyncResultObjectArray(obj[key])
    if (hit.length) return hit
  }
  return []
}

/**
 * 解析 search-page / async results 列表。
 * 优先 `data.result.data[]`（视频号/公众号），并兼容抖音/小红书 `list`、`items`、`aweme_list` 等。
 */
function readDataEnvelope(payload: Record<string, unknown>): Record<string, unknown> | null {
  const data = unwrapMaybeJson(payload.data)
  if (!data || typeof data !== 'object' || Array.isArray(data)) return null
  return data as Record<string, unknown>
}

function readResultEnvelope(data: Record<string, unknown>): Record<string, unknown> | null {
  const result = unwrapMaybeJson(data.result)
  if (!result || typeof result !== 'object' || Array.isArray(result)) return null
  return result as Record<string, unknown>
}

export type SyncResultDiagnostics = {
  itemCount: number
  balance?: number | null
  error?: unknown
  insufficientBalance?: boolean
  nextCursor?: unknown
  nextLogid?: unknown
  resultKeys?: string[]
  rawDataLength?: number | null
}

export function extractSyncResultDiagnostics(payload: unknown): SyncResultDiagnostics {
  const itemCount = extractSyncResultItems(payload).length
  if (!payload || typeof payload !== 'object') return { itemCount }
  const data = readDataEnvelope(payload as Record<string, unknown>)
  if (!data) return { itemCount }
  const result = readResultEnvelope(data)
  if (!result) return { itemCount, resultKeys: Object.keys(data) }
  const raw = result.data
  return {
    itemCount,
    balance: typeof result.balance === 'number' ? result.balance : null,
    error: result.error ?? data.error,
    insufficientBalance:
      result.insufficient_balance === true || result.insufficientBalance === true,
    nextCursor: result.next_cursor ?? result.nextCursor,
    nextLogid: result.next_logid ?? result.next_log_id ?? result.nextLogid,
    resultKeys: Object.keys(result),
    rawDataLength: Array.isArray(raw) ? raw.length : null,
  }
}

/** `GET .../async/tasks/{id}/results` 响应中的 `data.meta` */
export type AsyncTaskResultsMeta = {
  platform?: string
  source?: string
  action?: string
  resultTable?: string
}

export function extractAsyncTaskResultsMeta(payload: unknown): AsyncTaskResultsMeta {
  if (!payload || typeof payload !== 'object') return {}
  const data = (payload as Record<string, unknown>).data
  if (!data || typeof data !== 'object') return {}
  const meta = (data as Record<string, unknown>).meta
  if (!meta || typeof meta !== 'object') return {}
  const m = meta as Record<string, unknown>
  const platform = String(m.platform ?? m.source ?? '').trim().toLowerCase()
  const source = String(m.source ?? '').trim().toLowerCase()
  const action = String(m.action ?? '').trim()
  const resultTable = String(m.result_table ?? m.resultTable ?? '').trim()
  return {
    platform: platform || undefined,
    source: source || undefined,
    action: action || undefined,
    resultTable: resultTable || undefined,
  }
}

export function extractSyncResultItems(payload: unknown): Record<string, unknown>[] {
  if (!payload || typeof payload !== 'object') return []
  const root = payload as Record<string, unknown>
  const data = unwrapMaybeJson(root.data)

  if (Array.isArray(data)) return trySyncResultObjectArray(data)

  if (data && typeof data === 'object') {
    const d = data as Record<string, unknown>
    const fromData = pickSyncResultArrayFromRecord(d)
    if (fromData.length) return fromData

    const result = unwrapMaybeJson(d.result)
    if (result && typeof result === 'object' && !Array.isArray(result)) {
      const fromResult = pickSyncResultArrayFromRecord(result as Record<string, unknown>)
      if (fromResult.length) return fromResult
    }
  }

  return trySyncResultObjectArray(root.items ?? root.results ?? root.list)
}

/** 解析 `data.result` 上的账户余额（若接口返回） */
export function extractSyncResultBalance(payload: unknown): number | null {
  if (!payload || typeof payload !== 'object') return null
  const data = (payload as Record<string, unknown>).data
  if (!data || typeof data !== 'object') return null
  const result = (data as Record<string, unknown>).result
  if (!result || typeof result !== 'object') return null
  const bal = (result as Record<string, unknown>).balance
  return typeof bal === 'number' && Number.isFinite(bal) ? bal : null
}

export type SyncResultPageMeta = {
  nextCursor?: number | string
  nextLogid?: string
  insufficientBalance?: boolean
  hasMore: boolean
}

export function extractSyncResultPageMeta(payload: unknown): SyncResultPageMeta {
  if (!payload || typeof payload !== 'object') {
    return { hasMore: false }
  }
  const data = (payload as Record<string, unknown>).data
  if (!data || typeof data !== 'object') return { hasMore: false }
  const result = (data as Record<string, unknown>).result
  if (!result || typeof result !== 'object') return { hasMore: false }
  const r = result as Record<string, unknown>
  const nextCursor = r.next_cursor ?? r.nextCursor
  const nextLogid =
    typeof r.next_logid === 'string'
      ? r.next_logid
      : typeof r.next_log_id === 'string'
        ? r.next_log_id
        : typeof r.nextLogid === 'string'
          ? r.nextLogid
          : undefined
  const insufficient =
    r.insufficient_balance === true || r.insufficientBalance === true
  const hasMoreFlag = r.has_more ?? r.hasMore
  const hasCursor =
    nextCursor != null &&
    nextCursor !== '' &&
    !(typeof nextCursor === 'number' && !Number.isFinite(nextCursor))
  const hasLogId = Boolean(nextLogid?.trim())
  const hasMore =
    hasMoreFlag === true ||
    hasMoreFlag === 1 ||
    hasMoreFlag === '1' ||
    hasCursor ||
    hasLogId
  return {
    nextCursor: nextCursor as number | string | undefined,
    nextLogid,
    insufficientBalance: insufficient,
    hasMore,
  }
}

/** 微信 search-page（视频号/公众号）翻页：`data.result.next_offset` / `cookies_buffer` */
export type WxSearchPageMeta = {
  offset: string
  cookies_buffer: string
  insufficientBalance?: boolean
  hasMore: boolean
}

/** @deprecated 使用 `WxSearchPageMeta` */
export type GzhResultPageMeta = WxSearchPageMeta

export function extractWxSearchPageMeta(payload: unknown): WxSearchPageMeta {
  const empty: WxSearchPageMeta = { offset: '', cookies_buffer: '', hasMore: false }
  if (!payload || typeof payload !== 'object') return empty

  const data = (payload as Record<string, unknown>).data
  if (!data || typeof data !== 'object') return empty
  const result = (data as Record<string, unknown>).result
  if (!result || typeof result !== 'object') return empty

  const r = result as Record<string, unknown>
  const offsetRaw = r.next_offset ?? r.nextOffset ?? r.offset
  const cookiesRaw = r.cookies_buffer ?? r.cookiesBuffer ?? r.next_cookies_buffer
  const offset = offsetRaw != null && String(offsetRaw).trim() ? String(offsetRaw).trim() : ''
  const cookies_buffer = cookiesRaw != null ? String(cookiesRaw).trim() : ''
  const insufficient =
    r.insufficient_balance === true || r.insufficientBalance === true
  const hasMoreFlag = r.has_more ?? r.hasMore
  const hasMore =
    hasMoreFlag === true ||
    hasMoreFlag === 1 ||
    hasMoreFlag === '1' ||
    (hasMoreFlag !== false && Boolean(offset || cookies_buffer))

  return {
    offset,
    cookies_buffer,
    insufficientBalance: insufficient,
    hasMore,
  }
}

/** @deprecated 使用 `extractWxSearchPageMeta` */
export const extractGzhResultPageMeta = extractWxSearchPageMeta

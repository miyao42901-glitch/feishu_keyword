/**
 * 采集同步服务（如 192.168.1.11:8765）通用：基址、请求头、响应解析。
 */

/** 与 Apifox `ApifoxModel` 一致的 Header 形态 */
export type SyncApiHeaders = {
  'Content-Type': string
  'x-api-key': string
  'x-user-id'?: string
  [property: string]: unknown
}

export type SyncFetchContext = {
  apiKey: string
  userId?: string | number | null
  /** YDDM 登录用户手机号，用于 YDDM `POST /admin/set_discount` */
  phoneNum?: string | null
}

/** 采集服务根地址：`8765/api/v1/...`（无 `/sync` 路径前缀） */
const DEFAULT_SYNC_API_BASE = 'http://192.168.1.11:8765'

/**
 * 同步采集 API 根地址（无末尾 `/`）。
 * - 开发未配置时：空字符串，请求走同源 `/api/v1/...` → Vite 代理到 8765
 * - 已配置 `VITE_SYNC_API_BASE`：直连，如 `http://192.168.1.11:8765`
 */
export function getSyncApiBase(): string {
  const raw = (import.meta.env.VITE_SYNC_API_BASE as string | undefined)?.trim()
  if (raw) return raw.replace(/\/$/, '')
  if (import.meta.env.DEV) return ''
  return DEFAULT_SYNC_API_BASE
}

export function buildSyncApiHeaders(ctx: SyncFetchContext): SyncApiHeaders {
  const key = ctx.apiKey?.trim()
  if (!key) throw new Error('缺少 x-api-key：请先登录并配置 API Key')
  const headers: SyncApiHeaders = {
    'Content-Type': 'application/json',
    'x-api-key': key,
  }
  const uid = ctx.userId
  if (uid != null && String(uid).trim()) {
    headers['x-user-id'] = String(uid).trim()
  }
  return headers
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

/**
 * 解析 search-page / async results 列表：`data.result.data[]`。
 * 抖音项含 `aweme_id`、`publish_time`(ms)、`video_list` 等；小红书项含 `note_id`、`userid`、`images_list` 等。
 */
export function extractSyncResultItems(payload: unknown): Record<string, unknown>[] {
  if (!payload || typeof payload !== 'object') return []
  const root = payload as Record<string, unknown>
  const data = root.data
  if (!data || typeof data !== 'object') return []
  const result = (data as Record<string, unknown>).result
  if (!result || typeof result !== 'object') return []
  const inner = (result as Record<string, unknown>).data
  if (!Array.isArray(inner)) return []
  return inner.filter((x): x is Record<string, unknown> => x != null && typeof x === 'object')
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
  const hasMore =
    nextCursor != null &&
    nextCursor !== '' &&
    !(typeof nextCursor === 'number' && !Number.isFinite(nextCursor))
  return {
    nextCursor: nextCursor as number | string | undefined,
    nextLogid,
    insufficientBalance: insufficient,
    hasMore,
  }
}

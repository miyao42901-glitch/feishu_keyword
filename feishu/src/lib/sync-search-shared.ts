/**
 * 抖音 / 小红书 search-page 共用：HTTP、任务配置解析、去重收集。
 */

import {
  assertSyncEnvelopeOk,
  buildSyncApiHeaders,
  extractSyncResultPageMeta,
  getSyncApiBase,
  type SyncFetchContext,
} from '@/lib/sync-api-common'
import { ensureSyncEndpointDiscountForPath } from '@/lib/sync-set-discount'

export type SyncSortType = '0' | '1' | '2'

export function readConfigArray(config: Record<string, unknown>, camel: string, snake?: string): string[] {
  const raw = snake != null ? (config[camel] ?? config[snake]) : config[camel]
  if (!Array.isArray(raw)) return []
  return raw
    .filter((x): x is string => typeof x === 'string')
    .map((s) => s.trim())
    .filter(Boolean)
}

/**
 * search-page / async 采集用关键词列表。
 * 未配置关键词时仍发起一次请求（`keyword` 为空字符串，由采集服务按「不限关键词」处理）。
 */
export function readSearchKeywords(config: Record<string, unknown>): string[] {
  const keywords = readConfigArray(config, 'keywords')
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
}): Promise<unknown> {
  const url = `${getSyncApiBase()}${input.path}`
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
      if (!res.ok) throw new Error(`${input.platformLabel} HTTP ${res.status}`)
      throw new Error(`${input.platformLabel}响应不是合法 JSON`)
    }
  }
  if (!res.ok) {
    const detail =
      parsed && typeof parsed === 'object' && parsed !== null
        ? String((parsed as Record<string, unknown>).msg ?? (parsed as Record<string, unknown>).message ?? '')
        : text
    throw new Error(detail.trim() ? detail.trim() : `${input.platformLabel} HTTP ${res.status}`)
  }
  assertSyncEnvelopeOk(parsed)
  return parsed
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
      if (!res.ok) throw new Error(`${input.platformLabel} HTTP ${res.status}`)
      throw new Error(`${input.platformLabel}响应不是合法 JSON`)
    }
  }
  if (!res.ok) {
    const detail =
      parsed && typeof parsed === 'object' && parsed !== null
        ? String((parsed as Record<string, unknown>).msg ?? (parsed as Record<string, unknown>).message ?? '')
        : text
    throw new Error(detail.trim() ? detail.trim() : `${input.platformLabel} HTTP ${res.status}`)
  }
  assertSyncEnvelopeOk(parsed)
  return parsed
}

export async function postSyncSearchPage(input: {
  path: string
  platformLabel: string
  body: Record<string, unknown>
  ctx: SyncFetchContext
}): Promise<unknown> {
  await ensureSyncEndpointDiscountForPath(input.path, input.ctx)
  const parsed = await postSyncApiJson(input)
  const pageMeta = extractSyncResultPageMeta(parsed)
  if (pageMeta.insufficientBalance) {
    throw new Error('账户积分不足，无法继续采集')
  }
  return parsed
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
}): boolean {
  for (const item of input.batch) {
    const id = pickItemId(item, input.itemIdKeys)
    if (id) {
      if (input.seenIds.has(id)) continue
      input.seenIds.add(id)
    }
    input.collected.push(item)
    if (input.collected.length >= input.limit) return true
  }
  return input.collected.length >= input.limit
}

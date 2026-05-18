/**
 * 本地 `feishu/test_data/` 下与「抖音 / 小红书」同步接口同构的演示 JSON。
 * 当任务为运行中且仅勾选上述平台时，按任务配置过滤后用于写入飞书多维表格（及条数统计等）。
 */

import { platformDisplayNames } from '@/views/TaskCreateForm/constants'
import type { PlatformKey } from '@/components/PlatformIcon.vue'
import { mapItemToColumnValues } from '@/lib/test-data-field-map'

/** 当前 fixtures 与 `sourcePlatforms` 中已开放的平台 id 一致 */
export const TEST_DATA_PLATFORM_IDS = new Set<PlatformKey>(['douyin', 'xiaohongshu'])

export type TestFeedRow = {
  taskId: number
  taskName: string
  platform: PlatformKey
  platformLabel: string
  title: string
  author: string
  publishedAt: string
  url: string
  /** 排序用（不展示） */
  publishMs: number
  /** 按任务 sourceFieldSelection 映射的列名 → 值（飞书列名与表单字段标签一致） */
  fieldColumns: Record<string, string>
}

const DOUYIN_DATA_URL = new URL('../../test_data/抖音搜索（同步）.json', import.meta.url).href
const XHS_DATA_URL = new URL('../../test_data/小红书搜索（同步）.json', import.meta.url).href

let douyinPayload: unknown | undefined
let xhsPayload: unknown | undefined

async function loadDouyinPayload(): Promise<unknown> {
  if (douyinPayload !== undefined) return douyinPayload
  const res = await fetch(DOUYIN_DATA_URL)
  if (!res.ok) throw new Error(`加载抖音演示数据失败 HTTP ${res.status}`)
  douyinPayload = (await res.json()) as unknown
  return douyinPayload
}

async function loadXhsPayload(): Promise<unknown> {
  if (xhsPayload !== undefined) return xhsPayload
  const res = await fetch(XHS_DATA_URL)
  if (!res.ok) throw new Error(`加载小红书演示数据失败 HTTP ${res.status}`)
  xhsPayload = (await res.json()) as unknown
  return xhsPayload
}

function extractResultItems(payload: unknown): Record<string, unknown>[] {
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

function readConfigArray(config: Record<string, unknown>, camel: string, snake?: string): string[] {
  const raw = snake != null ? (config[camel] ?? config[snake]) : config[camel]
  if (!Array.isArray(raw)) return []
  return raw
    .filter((x): x is string => typeof x === 'string')
    .map((s) => s.trim())
    .filter(Boolean)
}

function readSelectedSources(config: Record<string, unknown>): PlatformKey[] {
  const raw = config.selectedSources ?? config.selected_sources
  if (!Array.isArray(raw)) return []
  const out: PlatformKey[] = []
  for (const x of raw) {
    if (typeof x !== 'string') continue
    const s = x.trim()
    if (s === 'douyin' || s === 'xiaohongshu') out.push(s)
  }
  return out
}

function readDataRange(config: Record<string, unknown>): number {
  const v = config.dataRange ?? config.data_range
  const n = typeof v === 'number' ? v : Number(v)
  if (!Number.isFinite(n) || n < 1) return 20
  return Math.min(100, Math.floor(n))
}

function combineText(parts: (unknown)[]): string {
  return parts
    .filter((x) => typeof x === 'string')
    .map((s) => (s as string).trim())
    .filter(Boolean)
    .join(' ')
}

function matchesKeywords(text: string, keywords: string[]): boolean {
  if (!keywords.length) return true
  const t = text.toLowerCase()
  return keywords.some((kw) => t.includes(kw.toLowerCase()))
}

function hasExclude(text: string, excludes: string[]): boolean {
  if (!excludes.length) return false
  const t = text.toLowerCase()
  return excludes.some((ex) => ex && t.includes(ex.toLowerCase()))
}

function formatPublish(ms: number): string {
  if (!Number.isFinite(ms)) return '—'
  const d = new Date(ms)
  return Number.isNaN(d.getTime()) ? '—' : d.toLocaleString('zh-CN', { hour12: false })
}

function mapDouyinItem(
  item: Record<string, unknown>,
  taskId: number,
  taskName: string,
  config: Record<string, unknown>,
): TestFeedRow | null {
  const title = typeof item.title === 'string' ? item.title : ''
  const desc = typeof item.desc === 'string' ? item.desc : ''
  const url = typeof item.url === 'string' ? item.url : ''
  const author = typeof item.nickname === 'string' ? item.nickname : '—'
  const pt = item.publish_time
  const publishMs = typeof pt === 'number' ? pt : Number(pt)
  const ms = Number.isFinite(publishMs) ? publishMs : 0
  return {
    taskId,
    taskName,
    platform: 'douyin',
    platformLabel: platformDisplayNames.douyin,
    title: title || desc || '—',
    author,
    publishedAt: formatPublish(ms),
    url: url || '—',
    publishMs: ms,
    fieldColumns: mapItemToColumnValues(item, 'douyin', config),
  }
}

function mapXhsItem(
  item: Record<string, unknown>,
  taskId: number,
  taskName: string,
  config: Record<string, unknown>,
): TestFeedRow | null {
  const title = typeof item.title === 'string' ? item.title : ''
  const desc = typeof item.desc === 'string' ? item.desc : ''
  const url = typeof item.url === 'string' ? item.url : ''
  const author = typeof item.nickname === 'string' ? item.nickname : '—'
  const pt = item.publish_time
  const publishMs = typeof pt === 'number' ? pt : Number(pt)
  const ms = Number.isFinite(publishMs) ? publishMs : 0
  return {
    taskId,
    taskName,
    platform: 'xiaohongshu',
    platformLabel: platformDisplayNames.xiaohongshu,
    title: title || desc || '—',
    author,
    publishedAt: formatPublish(ms),
    url: url || '—',
    publishMs: ms,
    fieldColumns: mapItemToColumnValues(item, 'xiaohongshu', config),
  }
}

export function taskUsesOnlyTestDataPlatforms(platformKeys: string[] | undefined): boolean {
  if (!platformKeys?.length) return false
  return platformKeys.every((k) => TEST_DATA_PLATFORM_IDS.has(k as PlatformKey))
}

/**
 * 从任务配置与本地 JSON 生成演示采集行（已按关键词 / 排除词 / dataRange 裁剪）。
 */
export async function buildTestDataFeedFromConfig(params: {
  taskId: number
  taskName: string
  config: Record<string, unknown>
}): Promise<TestFeedRow[]> {
  const { taskId, taskName, config } = params
  const sources = readSelectedSources(config)
  if (!sources.length || !taskUsesOnlyTestDataPlatforms(sources)) return []

  const keywords = readConfigArray(config, 'keywords')
  const excludes = readConfigArray(config, 'excludeKeywords', 'exclude_keywords')
  const limit = readDataRange(config)

  const douyinRows: TestFeedRow[] = []
  const xhsRows: TestFeedRow[] = []

  if (sources.includes('douyin')) {
    const payload = await loadDouyinPayload()
    for (const item of extractResultItems(payload)) {
      const row = mapDouyinItem(item, taskId, taskName, config)
      if (!row) continue
      const blob = combineText([row.title, row.author])
      if (!matchesKeywords(blob, keywords)) continue
      if (hasExclude(blob, excludes)) continue
      douyinRows.push(row)
    }
  }

  if (sources.includes('xiaohongshu')) {
    const payload = await loadXhsPayload()
    for (const item of extractResultItems(payload)) {
      const row = mapXhsItem(item, taskId, taskName, config)
      if (!row) continue
      const blob = combineText([row.title, row.author])
      if (!matchesKeywords(blob, keywords)) continue
      if (hasExclude(blob, excludes)) continue
      xhsRows.push(row)
    }
  }

  douyinRows.sort((a, b) => b.publishMs - a.publishMs)
  xhsRows.sort((a, b) => b.publishMs - a.publishMs)
  return [...douyinRows.slice(0, limit), ...xhsRows.slice(0, limit)]
}
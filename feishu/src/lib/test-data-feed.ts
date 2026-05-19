/**
 * 运行中任务采集数据：优先 `GET /api/v1/async/tasks/{id}/results`；
 * 无 `asyncTaskRefs` 时回退同步 search-page。
 */

import {
  getAsyncTaskResults,
  getAsyncTaskStatus,
  isRealtimeTaskConfig,
  readAsyncTaskIds,
  readAsyncTaskRefs,
} from '@/lib/async-task-api'
import { refreshYddmUserBalance } from '@/lib/refresh-yddm-balance'
import { fetchDouyinSearchItems } from '@/lib/douyin-sync-api'
import type { SyncFetchContext } from '@/lib/sync-api-common'
import { fetchXhsSearchItems } from '@/lib/xhs-sync-api'
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
  const ms = readPublishMs(item)
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
  const ms = readPublishMs(item)
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

function inferPlatformFromItem(item: Record<string, unknown>): PlatformKey | null {
  if (item.aweme_id != null || item.awemeId != null) return 'douyin'
  if (item.note_id != null || item.noteId != null) return 'xiaohongshu'
  return null
}

function readPublishMs(item: Record<string, unknown>): number {
  const pt = item.publish_time
  const n = typeof pt === 'number' ? pt : Number(pt)
  return Number.isFinite(n) ? n : 0
}

async function buildTestDataFeedFromAsyncResults(params: {
  taskId: number
  taskName: string
  config: Record<string, unknown>
  sync: SyncFetchContext
}): Promise<TestFeedRow[]> {
  const { taskId, taskName, config, sync } = params
  let refs = readAsyncTaskRefs(config)
  if (!refs.length) {
    refs = readAsyncTaskIds(config).map((taskId) => ({
      taskId,
      platform: 'douyin' as PlatformKey,
      keyword: '',
    }))
  }
  if (!refs.length) return []

  const limit = readDataRange(config)
  const douyinRows: TestFeedRow[] = []
  const xhsRows: TestFeedRow[] = []

  for (const ref of refs) {
    try {
      const status = await getAsyncTaskStatus(sync, ref.taskId)
      if (status.lifecycle === 'failed') continue
    } catch {
      /* 状态查询失败时仍尝试拉结果 */
    }

    let items: Record<string, unknown>[] = []
    try {
      const payload = await getAsyncTaskResults(sync, ref.taskId)
      items = payload.items
    } catch {
      continue
    }

    for (const item of items) {
      const platform = ref.platform ?? inferPlatformFromItem(item)
      if (platform === 'douyin') {
        const row = mapDouyinItem(item, taskId, taskName, config)
        if (row) douyinRows.push(row)
      } else if (platform === 'xiaohongshu') {
        const row = mapXhsItem(item, taskId, taskName, config)
        if (row) xhsRows.push(row)
      }
    }
  }

  douyinRows.sort((a, b) => b.publishMs - a.publishMs)
  xhsRows.sort((a, b) => b.publishMs - a.publishMs)
  const rows = [...douyinRows.slice(0, limit), ...xhsRows.slice(0, limit)]
  void refreshYddmUserBalance()
  return rows
}

/**
 * 从任务配置拉取采集数据（已按 dataRange 裁剪）。
 */
export async function buildTestDataFeedFromConfig(params: {
  taskId: number
  taskName: string
  config: Record<string, unknown>
  /** 同步采集接口鉴权（抖音 / 小红书）；未传时无法拉取 */
  sync?: SyncFetchContext
}): Promise<TestFeedRow[]> {
  const { taskId, taskName, config, sync } = params
  const sources = readSelectedSources(config)
  if (!sources.length || !taskUsesOnlyTestDataPlatforms(sources)) return []

  if (
    !isRealtimeTaskConfig(config) &&
    readAsyncTaskIds(config).length &&
    sync?.apiKey?.trim()
  ) {
    return buildTestDataFeedFromAsyncResults({ taskId, taskName, config, sync })
  }

  const limit = readDataRange(config)

  const douyinRows: TestFeedRow[] = []
  const xhsRows: TestFeedRow[] = []

  if (sources.includes('douyin')) {
    if (!sync?.apiKey?.trim()) {
      throw new Error('抖音采集需要 API Key，请先登录')
    }
    const items = await fetchDouyinSearchItems(config, sync)
    for (const item of items) {
      const row = mapDouyinItem(item, taskId, taskName, config)
      if (row) douyinRows.push(row)
    }
  }

  if (sources.includes('xiaohongshu')) {
    if (!sync?.apiKey?.trim()) {
      throw new Error('小红书采集需要 API Key，请先登录')
    }
    const items = await fetchXhsSearchItems(config, sync)
    for (const item of items) {
      const row = mapXhsItem(item, taskId, taskName, config)
      if (row) xhsRows.push(row)
    }
  }

  douyinRows.sort((a, b) => b.publishMs - a.publishMs)
  xhsRows.sort((a, b) => b.publishMs - a.publishMs)
  const rows = [...douyinRows.slice(0, limit), ...xhsRows.slice(0, limit)]
  void refreshYddmUserBalance()
  return rows
}
/**
 * 运行中任务采集数据：先 `GET /api/v1/async/tasks/{id}`，仅 `running` 时再 `GET .../results`，写入多维表格；
 * 无 `asyncTaskRefs` 时回退同步 search-page。
 */

import {
  fetchAsyncTaskStatusAndResultsMaps,
  isRealtimeTaskConfig,
  postResultsAcceptanceAfterAsyncFetch,
  readAsyncTaskIds,
  readAsyncTaskRefs,
  type AsyncTaskRef,
  type AsyncTaskStatusResult,
} from '@/lib/async-task-api'
import { refreshYddmUserBalance } from '@/lib/refresh-yddm-balance'
import { fetchDouyinSearchItems } from '@/lib/douyin-sync-api'
import type { SyncFetchContext } from '@/lib/sync-api-common'
import {
  isSyncCollectionPlatform,
  readSyncCollectionPlatforms,
  taskUsesOnlySyncCollectionPlatforms,
} from '@/lib/sync-collection-platforms'
import { fetchGzhSearchItems } from '@/lib/gzh-sync-api'
import { fetchWxvideoSearchItems } from '@/lib/wxvideo-sync-api'
import type { SyncItemsByPlatform } from '@/lib/sync-collection-cache'
import { peekSyncCollectionCache } from '@/lib/sync-collection-cache'
import { fetchXhsSearchItems } from '@/lib/xhs-sync-api'
import { platformDisplayNames } from '@/views/TaskCreateForm/constants'
import type { PlatformKey } from '@/components/PlatformIcon.vue'
import { mapItemToColumnValues, readXhsPublishTimeMs } from '@/lib/test-data-field-map'

/** @deprecated 使用 `SYNC_COLLECTION_PLATFORM_IDS` */
export const TEST_DATA_PLATFORM_IDS = new Set<PlatformKey>([
  'douyin',
  'xiaohongshu',
  'shipinhao',
  'gzh',
])

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
  /** 本条数据采集时刻（毫秒时间戳） */
  collectedAtMs: number
  /** 平台内容主键（写入去重用，不依赖是否勾选「笔记ID」等列） */
  itemStableId: string
}

function readSelectedSources(config: Record<string, unknown>): PlatformKey[] {
  return readSyncCollectionPlatforms(config)
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
  collectedAtMs: number,
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
    fieldColumns: mapItemToColumnValues(item, 'douyin', config, { collectedAtMs }),
    collectedAtMs,
    itemStableId: readItemStableId(item, 'douyin'),
  }
}

function mapXhsItem(
  item: Record<string, unknown>,
  taskId: number,
  taskName: string,
  config: Record<string, unknown>,
  collectedAtMs: number,
): TestFeedRow | null {
  const title = typeof item.title === 'string' ? item.title : ''
  const desc =
    typeof item.desc === 'string'
      ? item.desc
      : typeof item.summary === 'string'
        ? item.summary
        : ''
  const url =
    typeof item.page_url === 'string'
      ? item.page_url
      : typeof item.url === 'string'
        ? item.url
        : ''
  const author = typeof item.nickname === 'string' ? item.nickname : '—'
  const ms = readXhsPublishTimeMs(item) || readPublishMs(item)
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
    fieldColumns: mapItemToColumnValues(item, 'xiaohongshu', config, { collectedAtMs }),
    collectedAtMs,
    itemStableId: readItemStableId(item, 'xiaohongshu'),
  }
}

export function taskUsesOnlyTestDataPlatforms(platformKeys: string[] | undefined): boolean {
  return taskUsesOnlySyncCollectionPlatforms(platformKeys)
}

function mapGzhItem(
  item: Record<string, unknown>,
  taskId: number,
  taskName: string,
  config: Record<string, unknown>,
  collectedAtMs: number,
): TestFeedRow | null {
  const title =
    typeof item.title === 'string'
      ? item.title
      : typeof item.article_title === 'string'
        ? item.article_title
        : ''
  const desc =
    typeof item.content === 'string'
      ? item.content
      : typeof item.desc === 'string'
        ? item.desc
        : ''
  const url =
    (typeof item.url === 'string' && item.url) ||
    (typeof item.link === 'string' && item.link) ||
    (typeof item.video_url === 'string' && item.video_url) ||
    (typeof item.videoUrl === 'string' && item.videoUrl) ||
    (typeof item.source_url === 'string' && item.source_url) ||
    ''
  const author =
    typeof item.biz_name === 'string'
      ? item.biz_name
      : typeof item.nickname === 'string'
        ? item.nickname
        : typeof item.author === 'string'
          ? item.author
          : '—'
  const ms = readPublishMs(item)
  return {
    taskId,
    taskName,
    platform: 'gzh',
    platformLabel: platformDisplayNames.gzh,
    title: title || desc || '—',
    author,
    publishedAt: formatPublish(ms),
    url: url || '—',
    publishMs: ms,
    fieldColumns: mapItemToColumnValues(item, 'gzh', config, { collectedAtMs }),
    collectedAtMs,
    itemStableId: readItemStableId(item, 'gzh'),
  }
}

function mapShipinhaoItem(
  item: Record<string, unknown>,
  taskId: number,
  taskName: string,
  config: Record<string, unknown>,
  collectedAtMs: number,
): TestFeedRow | null {
  const title = typeof item.title === 'string' ? item.title : ''
  const desc = typeof item.desc === 'string' ? item.desc : ''
  const url =
    (typeof item.video_url === 'string' && item.video_url) ||
    (typeof item.videoUrl === 'string' && item.videoUrl) ||
    (typeof item.url === 'string' && item.url) ||
    ''
  const author = typeof item.nickname === 'string' ? item.nickname : '—'
  const ms = readPublishMs(item)
  return {
    taskId,
    taskName,
    platform: 'shipinhao',
    platformLabel: platformDisplayNames.shipinhao,
    title: title || desc || '—',
    author,
    publishedAt: formatPublish(ms),
    url: url || '—',
    publishMs: ms,
    fieldColumns: mapItemToColumnValues(item, 'shipinhao', config, { collectedAtMs }),
    collectedAtMs,
    itemStableId: readItemStableId(item, 'shipinhao'),
  }
}

/** 异步子任务已绑定平台时以 ref 为准（避免小红书条目含 object_id 等被误判为公众号/视频号） */
function resolvePlatformForAsyncItem(
  item: Record<string, unknown>,
  ref: AsyncTaskRef,
): PlatformKey {
  if (isSyncCollectionPlatform(ref.platform)) return ref.platform
  return inferPlatformFromItem(item) ?? 'douyin'
}

function inferPlatformFromItem(item: Record<string, unknown>): PlatformKey | null {
  if (item.aweme_id != null || item.awemeId != null) return 'douyin'
  if (item.note_id != null || item.noteId != null) return 'xiaohongshu'
  if (
    item.post_id != null ||
    item.postId != null ||
    item.feed_id != null ||
    item.feedId != null ||
    item.object_id != null ||
    item.objectId != null
  ) {
    if (item.duration != null || item.video_url != null || item.videoUrl != null) {
      return 'shipinhao'
    }
    return 'gzh'
  }
  if (
    item.article_id != null ||
    item.articleId != null ||
    item.msg_id != null ||
    item.msgId != null ||
    item.appmsgid != null
  ) {
    return 'gzh'
  }
  return null
}

function readPublishMs(item: Record<string, unknown>): number {
  const ms = readXhsPublishTimeMs(item)
  if (ms > 0) return ms
  const pt = item.publish_time
  const n = typeof pt === 'number' ? pt : Number(pt)
  return Number.isFinite(n) ? n : 0
}

function pickFirstStringField(item: Record<string, unknown>, keys: string[]): string {
  for (const key of keys) {
    const v = item[key]
    if (v != null && String(v).trim()) return String(v).trim()
  }
  return ''
}

/** 从原始条目读取平台唯一 id（用于飞书写入去重） */
export function readItemStableId(item: Record<string, unknown>, platform: PlatformKey): string {
  switch (platform) {
    case 'douyin':
      return pickFirstStringField(item, ['aweme_id', 'awemeId'])
    case 'xiaohongshu': {
      const id = pickFirstStringField(item, [
        'post_id',
        'postId',
        'note_id',
        'noteId',
        'noteid',
        'id',
        'note_card_id',
        'noteCardId',
        'red_id',
        'redId',
      ])
      if (id) return id
      const url = pickFirstStringField(item, [
        'page_url',
        'pageUrl',
        'url',
        'share_url',
        'shareUrl',
        'link',
        'note_url',
      ])
      if (url) return url
      const title = pickFirstStringField(item, ['title', 'desc'])
      const uid = pickFirstStringField(item, ['userid', 'user_id', 'userId'])
      const pt = readPublishMs(item)
      if (title || uid || pt > 0) return `${pt}:${uid}:${title.slice(0, 120)}`
      return ''
    }
    case 'shipinhao':
      return pickFirstStringField(item, [
        'feed_id',
        'feedId',
        'object_id',
        'objectId',
        'post_id',
        'postId',
      ])
    case 'gzh':
      return pickFirstStringField(item, ['article_id', 'articleId', 'msg_id', 'msgId', 'appmsgid'])
    default:
      return ''
  }
}

function inferPlatformFromResultItems(items: Record<string, unknown>[]): PlatformKey {
  const counts = new Map<PlatformKey, number>()
  for (const item of items) {
    const p = inferPlatformFromItem(item)
    if (p) counts.set(p, (counts.get(p) ?? 0) + 1)
  }
  let best: PlatformKey = 'douyin'
  let max = 0
  for (const [p, n] of counts) {
    if (n > max) {
      max = n
      best = p
    }
  }
  return best
}

/** 采集时刻：优先接口字段，否则用发布时间（避免轮询时 Date.now() 变化） */
function readCollectedAtMs(item: Record<string, unknown>): number {
  for (const key of ['collected_at', 'collectedAt', 'gather_time', 'gatherTime', 'create_time', 'createTime']) {
    const raw = item[key]
    const n = typeof raw === 'number' ? raw : Number(raw)
    if (Number.isFinite(n) && n > 0) return n
  }
  const publish = readPublishMs(item)
  return publish > 0 ? publish : 0
}

type AsyncFeedBuildResult = {
  rows: TestFeedRow[]
  statusMap: Map<string, AsyncTaskStatusResult>
}

async function buildTestDataFeedFromAsyncResults(params: {
  taskId: number
  taskName: string
  config: Record<string, unknown>
  sync: SyncFetchContext
}): Promise<AsyncFeedBuildResult> {
  const { taskId, taskName, config, sync } = params
  let refs = readAsyncTaskRefs(config)
  const fallbackTaskIds = refs.length ? [] : readAsyncTaskIds(config)
  const taskIds = refs.length ? refs.map((r) => r.taskId) : fallbackTaskIds
  if (!taskIds.length) return { rows: [], statusMap: new Map() }

  const limit = readDataRange(config)
  const douyinRows: TestFeedRow[] = []
  const xhsRows: TestFeedRow[] = []
  const shipinhaoRows: TestFeedRow[] = []
  const gzhRows: TestFeedRow[] = []

  const { statusMap, resultsMap } = await fetchAsyncTaskStatusAndResultsMaps(sync, taskIds, {
    refs,
    skipAcceptance: true,
  })

  if (!refs.length) {
    refs = fallbackTaskIds.map((asyncId) => ({
      taskId: asyncId,
      platform: inferPlatformFromResultItems(resultsMap.get(asyncId) ?? []),
      keyword: '',
    }))
  }

  await postResultsAcceptanceAfterAsyncFetch(sync, refs, resultsMap)

  for (const ref of refs) {
    const status = statusMap.get(ref.taskId)
    if (status?.lifecycle === 'failed') continue

    const items = resultsMap.get(ref.taskId) ?? []
    if (!items.length) continue

    for (const item of items) {
      const platform = resolvePlatformForAsyncItem(item, ref)
      const collectedAtMs = readCollectedAtMs(item)
      if (platform === 'douyin') {
        const row = mapDouyinItem(item, taskId, taskName, config, collectedAtMs)
        if (row) douyinRows.push(row)
      } else if (platform === 'xiaohongshu') {
        const row = mapXhsItem(item, taskId, taskName, config, collectedAtMs)
        if (row) xhsRows.push(row)
      } else if (platform === 'shipinhao') {
        const row = mapShipinhaoItem(item, taskId, taskName, config, collectedAtMs)
        if (row) shipinhaoRows.push(row)
      } else if (platform === 'gzh') {
        const row = mapGzhItem(item, taskId, taskName, config, collectedAtMs)
        if (row) gzhRows.push(row)
      }
    }
  }

  douyinRows.sort((a, b) => b.publishMs - a.publishMs)
  xhsRows.sort((a, b) => b.publishMs - a.publishMs)
  shipinhaoRows.sort((a, b) => b.publishMs - a.publishMs)
  gzhRows.sort((a, b) => b.publishMs - a.publishMs)
  const rows = [
    ...douyinRows.slice(0, limit),
    ...xhsRows.slice(0, limit),
    ...shipinhaoRows.slice(0, limit),
    ...gzhRows.slice(0, limit),
  ]
  void refreshYddmUserBalance()

  if (import.meta.env.DEV) {
    console.log('[feed-build-async]', {
      taskId,
      limit,
      refs: refs.map((r) => ({ platform: r.platform, taskId: r.taskId, keyword: r.keyword })),
      rowCounts: {
        douyin: douyinRows.length,
        xiaohongshu: xhsRows.length,
        shipinhao: shipinhaoRows.length,
        gzh: gzhRows.length,
      },
      xhsMissingStableId: xhsRows.filter((r) => !r.itemStableId).length,
    })
  }

  return { rows, statusMap }
}

export type BuildTestDataFeedResult = {
  rows: TestFeedRow[]
  /** 定时任务异步子任务状态（供 Webhook 失败检测复用，避免重复请求） */
  asyncStatusMap?: Map<string, AsyncTaskStatusResult>
}

/**
 * 从任务配置拉取采集数据。
 * `dataRange` 为各平台独立上限：选 20 条时抖音、小红书、视频号、公众号各最多 20 条。
 */
export async function buildTestDataFeedFromConfig(params: {
  taskId: number
  taskName: string
  config: Record<string, unknown>
  /** 同步采集接口鉴权（抖音 / 小红书）；未传时无法拉取 */
  sync?: SyncFetchContext
  /** 单次任务刚采集完的结果，避免重复请求 search-page */
  preloadedItems?: SyncItemsByPlatform
}): Promise<BuildTestDataFeedResult> {
  const { taskId, taskName, config, sync } = params
  const preloaded = params.preloadedItems ?? peekSyncCollectionCache(taskId)
  const sources = readSelectedSources(config)
  if (!sources.length || !taskUsesOnlyTestDataPlatforms(sources)) {
    return { rows: [] }
  }

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
  const shipinhaoRows: TestFeedRow[] = []
  const gzhRows: TestFeedRow[] = []

  const needSyncKey =
    (sources.includes('douyin') && !preloaded?.douyin) ||
    (sources.includes('xiaohongshu') && !preloaded?.xiaohongshu) ||
    (sources.includes('shipinhao') && !preloaded?.shipinhao) ||
    (sources.includes('gzh') && !preloaded?.gzh)
  if (needSyncKey && !sync?.apiKey?.trim()) {
    throw new Error('采集需要 API Key，请先登录')
  }

  if (sources.includes('douyin')) {
    const items =
      preloaded?.douyin ?? (await fetchDouyinSearchItems(config, sync!))
    for (const item of items) {
      const row = mapDouyinItem(item, taskId, taskName, config, Date.now())
      if (row) douyinRows.push(row)
    }
  }

  if (sources.includes('xiaohongshu')) {
    const items =
      preloaded?.xiaohongshu ?? (await fetchXhsSearchItems(config, sync!))
    for (const item of items) {
      const row = mapXhsItem(item, taskId, taskName, config, Date.now())
      if (row) xhsRows.push(row)
    }
  }

  if (sources.includes('shipinhao')) {
    const items =
      preloaded?.shipinhao ?? (await fetchWxvideoSearchItems(config, sync!))
    for (const item of items) {
      const row = mapShipinhaoItem(item, taskId, taskName, config, Date.now())
      if (row) shipinhaoRows.push(row)
    }
  }

  if (sources.includes('gzh')) {
    const items = preloaded?.gzh ?? (await fetchGzhSearchItems(config, sync!))
    for (const item of items) {
      const row = mapGzhItem(item, taskId, taskName, config, Date.now())
      if (row) gzhRows.push(row)
    }
  }

  douyinRows.sort((a, b) => b.publishMs - a.publishMs)
  xhsRows.sort((a, b) => b.publishMs - a.publishMs)
  shipinhaoRows.sort((a, b) => b.publishMs - a.publishMs)
  gzhRows.sort((a, b) => b.publishMs - a.publishMs)
  const rows = [
    ...douyinRows.slice(0, limit),
    ...xhsRows.slice(0, limit),
    ...shipinhaoRows.slice(0, limit),
    ...gzhRows.slice(0, limit),
  ]

  if (import.meta.env.DEV) {
    console.log('[feed-build]', {
      taskId,
      limit,
      preloadedCounts: {
        douyin: preloaded?.douyin?.length ?? null,
        xiaohongshu: preloaded?.xiaohongshu?.length ?? null,
        shipinhao: preloaded?.shipinhao?.length ?? null,
        gzh: preloaded?.gzh?.length ?? null,
      },
      rowCounts: {
        douyin: douyinRows.length,
        xiaohongshu: xhsRows.length,
        shipinhao: shipinhaoRows.length,
        gzh: gzhRows.length,
      },
      sampleIds: {
        douyin: douyinRows[0]?.fieldColumns['视频唯一ID'],
        xiaohongshu: xhsRows[0]?.fieldColumns['笔记ID'],
        shipinhao: shipinhaoRows[0]?.fieldColumns['视频唯一ID'],
        gzh: gzhRows[0]?.fieldColumns['文章ID'],
      },
    })
    if (sources.includes('douyin') && !douyinRows.length) {
      console.warn('[feed-build] 抖音 items 未解析为行，首条原始:', preloaded?.douyin?.[0])
    }
    if (sources.includes('xiaohongshu') && !xhsRows.length) {
      console.warn('[feed-build] 小红书 items 未解析为行，首条原始:', preloaded?.xiaohongshu?.[0])
    }
  }

  void refreshYddmUserBalance()
  return { rows }
}
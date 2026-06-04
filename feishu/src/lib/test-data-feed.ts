/**
 * 定时任务：`GET .../async/tasks/{子任务id}/results`（`running`/`completed`，或 `pending` 且 next_run_at+3min；首屏空结果最多重试 3 次，仍无数据不验收）。
 * 单次任务：各平台 `POST /api/v1/sync/{platform}/search-page`（不走 results）。
 */

import {
  clearRealtimeAsyncBindings,
  fetchAsyncTaskStatusAndResultsMaps,
  isRealtimeTaskConfig,
  postResultsAcceptanceAfterAsyncFetch,
  readAsyncSubTaskIdsForResults,
  readAsyncTaskRefs,
  shouldUseAsyncTaskResultsFeed,
  type AsyncTaskRef,
  type AsyncTaskResultsBatch,
  type AsyncTaskStatusResult,
} from '@/lib/async-task-api'
import { applyTaskTypeFromListCard } from '@/lib/feishu-async-task-config'
import { resetPlatformSyncBillingSession } from '@/lib/sync-set-discount'
import { fetchDouyinSearchItems } from '@/lib/douyin-sync-api'
import type { SyncFetchContext } from '@/lib/sync-api-common'
import {
  defaultNewTableNameForPlatform,
  isSyncCollectionPlatform,
  mapYddmPlatformToSyncId,
  readSyncCollectionPlatforms,
  taskUsesOnlySyncCollectionPlatforms,
  type SyncCollectionPlatformId,
} from '@/lib/sync-collection-platforms'
import { fetchGzhSearchItems } from '@/lib/gzh-sync-api'
import { fetchWxvideoSearchItems } from '@/lib/wxvideo-sync-api'
import type { SyncItemsByPlatform } from '@/lib/sync-collection-cache'
import { peekSyncCollectionCache } from '@/lib/sync-collection-cache'
import { fetchXhsSearchItems } from '@/lib/xhs-sync-api'
import { platformDisplayNames } from '@/views/TaskCreateForm/constants'
import type { PlatformKey } from '@/components/PlatformIcon.vue'
import type { TaskCardModel } from '@/views/tasks/types'
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

/** 同一平台 + 内容 ID 去重键（与飞书写入指纹一致） */
export function buildPlatformItemDedupKey(platform: PlatformKey, itemStableId: string): string {
  return `${platform}:${itemStableId.trim()}`
}

/** 按「平台 + itemStableId」去重，保留首次出现的条目 */
export function dedupeTestFeedRows(rows: TestFeedRow[]): TestFeedRow[] {
  const seen = new Set<string>()
  const out: TestFeedRow[] = []
  for (const row of rows) {
    const id = row.itemStableId?.trim()
    if (id) {
      const key = buildPlatformItemDedupKey(row.platform, id)
      if (seen.has(key)) continue
      seen.add(key)
    }
    out.push(row)
  }
  return out
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

/** 异步子任务已绑定平台时以 ref / results.meta 为准（避免条目字段误判平台） */
function resolvePlatformForAsyncItem(
  item: Record<string, unknown>,
  ref: AsyncTaskRef,
  resultsPlatform?: SyncCollectionPlatformId | null,
): PlatformKey {
  if (isSyncCollectionPlatform(ref.platform)) return ref.platform
  if (resultsPlatform) return resultsPlatform
  return inferPlatformFromItem(item) ?? 'douyin'
}

function refPlatformFromResultsBatch(batch: AsyncTaskResultsBatch | undefined): PlatformKey {
  if (batch?.platform) return batch.platform
  const fromMeta = mapYddmPlatformToSyncId(batch?.meta.platform ?? batch?.meta.source)
  if (fromMeta) return fromMeta
  return inferPlatformFromResultItems(batch?.items ?? [])
}

/** 将 results `meta.platform` / `result_table` 写入任务配置，供按平台建表 */
export function applyAsyncResultsMetaToConfig(
  config: Record<string, unknown>,
  resultsMap: Map<string, AsyncTaskResultsBatch>,
): SyncCollectionPlatformId[] {
  const platforms = new Set<SyncCollectionPlatformId>()
  const nameMap: Record<string, string> = {}
  const rawNames = config.platformNewTableNames ?? config.platform_new_table_names
  if (rawNames && typeof rawNames === 'object' && !Array.isArray(rawNames)) {
    for (const [k, v] of Object.entries(rawNames as Record<string, unknown>)) {
      if (typeof v === 'string' && v.trim() && isSyncCollectionPlatform(k)) {
        nameMap[k] = v.trim()
      }
    }
  }

  for (const p of readSyncCollectionPlatforms(config)) {
    platforms.add(p)
    if (!nameMap[p]?.trim()) {
      nameMap[p] = defaultNewTableNameForPlatform(p)
    }
  }

  for (const batch of resultsMap.values()) {
    const platform = batch.platform ?? mapYddmPlatformToSyncId(batch.meta.platform ?? batch.meta.source)
    if (!platform) continue
    platforms.add(platform)
    if (!nameMap[platform]?.trim()) {
      nameMap[platform] = defaultNewTableNameForPlatform(platform)
    }
  }

  if (platforms.size) {
    const existing = readSyncCollectionPlatforms(config)
    const merged = [...new Set([...existing, ...platforms])]
    config.selectedSources = merged
  }
  if (Object.keys(nameMap).length) {
    config.platformNewTableNames = nameMap
  }
  return [...platforms]
}

function inferPlatformFromItem(item: Record<string, unknown>): PlatformKey | null {
  const resultRef = pickFirstStringField(item, ['result_ref', 'resultRef'])
  if (resultRef.startsWith('douyin:')) return 'douyin'
  if (resultRef.startsWith('xhs:')) return 'xiaohongshu'
  const pageUrl = readDouyinPageUrl(item)
  if (pageUrl.includes('douyin.com')) return 'douyin'
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

function readDouyinPageUrl(item: Record<string, unknown>): string {
  return pickFirstStringField(item, ['page_url', 'pageUrl', 'url'])
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
      return pickFirstStringField(item, ['aweme_id', 'awemeId', 'post_id', 'postId', 'id'])
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
  /** 来自 `GET .../results` 的 `data.meta.platform`（即使 items 为空） */
  resultPlatforms: SyncCollectionPlatformId[]
}

async function buildTestDataFeedFromAsyncResults(params: {
  taskId: number
  taskName: string
  config: Record<string, unknown>
  sync: SyncFetchContext
  /** 列表卡片已是 running 时跳过 `GET .../tasks/{id}` */
  skipStatusFetchForTaskIds?: string[]
  /** `pending` 且 next_run_at+3min：各平台子任务拉 `GET .../results` */
  pendingResultsDue?: boolean
}): Promise<AsyncFeedBuildResult> {
  const { taskId, taskName, config, sync } = params
  if (isRealtimeTaskConfig(config)) {
    return { rows: [], statusMap: new Map(), resultPlatforms: [] }
  }
  let refs = readAsyncTaskRefs(config)
  const subTaskIds = readAsyncSubTaskIdsForResults(config, taskId)
  const taskIds = refs.length ? refs.map((r) => r.taskId) : subTaskIds
  if (!taskIds.length) return { rows: [], statusMap: new Map(), resultPlatforms: [] }

  const limit = readDataRange(config)
  const douyinRows: TestFeedRow[] = []
  const xhsRows: TestFeedRow[] = []
  const shipinhaoRows: TestFeedRow[] = []
  const gzhRows: TestFeedRow[] = []

  const { statusMap, resultsMap } = await fetchAsyncTaskStatusAndResultsMaps(sync, taskIds, {
    refs,
    skipAcceptance: true,
    skipStatusFetchForIds: params.skipStatusFetchForTaskIds,
    maxItemsPerTask: limit,
    pendingResultsDue: params.pendingResultsDue,
  })

  if (!refs.length) {
    refs = taskIds.map((asyncId) => ({
      taskId: asyncId,
      platform: refPlatformFromResultsBatch(resultsMap.get(asyncId)),
      keyword: '',
    }))
  } else {
    refs = refs.map((ref) => {
      const batch = resultsMap.get(ref.taskId)
      const fromMeta = batch?.platform ?? mapYddmPlatformToSyncId(batch?.meta.platform)
      if (fromMeta && !isSyncCollectionPlatform(ref.platform)) {
        return { ...ref, platform: fromMeta }
      }
      return ref
    })
  }

  const resultPlatforms = applyAsyncResultsMetaToConfig(config, resultsMap)

  await postResultsAcceptanceAfterAsyncFetch(sync, refs, resultsMap)

  for (const ref of refs) {
    const status = statusMap.get(ref.taskId)
    if (status?.lifecycle === 'failed') continue

    const batch = resultsMap.get(ref.taskId)
    const items = batch?.items ?? []
    const resultsPlatform = batch?.platform ?? null
    if (!items.length) continue

    for (const item of items) {
      const platform = resolvePlatformForAsyncItem(item, ref, resultsPlatform)
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
    ...dedupeTestFeedRows(douyinRows),
    ...dedupeTestFeedRows(xhsRows),
    ...dedupeTestFeedRows(shipinhaoRows),
    ...dedupeTestFeedRows(gzhRows),
  ]

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

  return { rows, statusMap, resultPlatforms }
}

export type BuildTestDataFeedResult = {
  rows: TestFeedRow[]
  /** 定时任务异步子任务状态（供 Webhook 失败检测复用，避免重复请求） */
  asyncStatusMap?: Map<string, AsyncTaskStatusResult>
  /** `GET .../results` 的 `meta.platform` 解析出的平台（用于建表，可无采集行） */
  resultPlatforms?: SyncCollectionPlatformId[]
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
  /** 仅构建指定平台行（各表管各表；避免写抖音时顺带请求视频号等） */
  onlyPlatforms?: SyncCollectionPlatformId[]
  /** 列表已 running 的子任务，拉 results 时不重复 `GET .../tasks/{id}` */
  skipStatusFetchForTaskIds?: string[]
  /** `pending` 且 next_run_at+3min：各平台子任务拉 `GET .../results` */
  pendingResultsDue?: boolean
  /** 列表卡片：单次任务强制走 search-page */
  card?: TaskCardModel
}): Promise<BuildTestDataFeedResult> {
  const { taskId, taskName, sync } = params
  let config = params.card
    ? applyTaskTypeFromListCard({ ...params.config }, params.card)
    : { ...params.config }
  if (isRealtimeTaskConfig(config)) {
    config = clearRealtimeAsyncBindings(config)
  }

  const preloaded = params.preloadedItems ?? peekSyncCollectionCache(taskId)
  const hasPreloaded =
    Boolean(preloaded?.douyin?.length) ||
    Boolean(preloaded?.xiaohongshu?.length) ||
    Boolean(preloaded?.shipinhao?.length) ||
    Boolean(preloaded?.gzh?.length)

  let sources = readSelectedSources(config)
  if (params.onlyPlatforms?.length) {
    const allow = new Set(params.onlyPlatforms)
    sources = sources.filter((p) => allow.has(p as SyncCollectionPlatformId))
  }
  if (!sources.length || !taskUsesOnlyTestDataPlatforms(sources)) {
    return { rows: [] }
  }

  const useAsyncResults = shouldUseAsyncTaskResultsFeed(config, {
    parentTaskId: taskId,
    hasPreloadedSyncItems: hasPreloaded,
  })
  if (import.meta.env.DEV) {
    console.log('[feed-route]', {
      taskId,
      useAsyncResults,
      realtime: isRealtimeTaskConfig(config),
      hasPreloaded,
      cardType: params.card?.taskTypeLabel,
    })
  }
  if (useAsyncResults && sync?.apiKey?.trim()) {
    const asyncFeed = await buildTestDataFeedFromAsyncResults({
      taskId,
      taskName,
      config,
      sync,
      skipStatusFetchForTaskIds: params.skipStatusFetchForTaskIds,
      pendingResultsDue: params.pendingResultsDue,
    })
    return {
      rows: asyncFeed.rows,
      asyncStatusMap: asyncFeed.statusMap,
      resultPlatforms: asyncFeed.resultPlatforms,
    }
  }

  const syncForSearchPage: SyncFetchContext | undefined = sync
    ? { ...sync, skipSetDiscount: isRealtimeTaskConfig(config) || sync.skipSetDiscount === true }
    : undefined

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
  if (needSyncKey && !syncForSearchPage?.apiKey?.trim()) {
    throw new Error('采集需要 API Key，请先登录')
  }

  if (sources.includes('douyin')) {
    const douyinCtx = resetPlatformSyncBillingSession(syncForSearchPage!)
    const items = preloaded?.douyin ?? (await fetchDouyinSearchItems(config, douyinCtx))
    for (const item of items) {
      const row = mapDouyinItem(item, taskId, taskName, config, Date.now())
      if (row) douyinRows.push(row)
    }
  }

  if (sources.includes('xiaohongshu')) {
    const xhsCtx = resetPlatformSyncBillingSession(syncForSearchPage!)
    const items = preloaded?.xiaohongshu ?? (await fetchXhsSearchItems(config, xhsCtx))
    for (const item of items) {
      const row = mapXhsItem(item, taskId, taskName, config, Date.now())
      if (row) xhsRows.push(row)
    }
  }

  if (sources.includes('shipinhao')) {
    const wxCtx = resetPlatformSyncBillingSession(syncForSearchPage!)
    const items = preloaded?.shipinhao ?? (await fetchWxvideoSearchItems(config, wxCtx))
    for (const item of items) {
      const row = mapShipinhaoItem(item, taskId, taskName, config, Date.now())
      if (row) shipinhaoRows.push(row)
    }
  }

  if (sources.includes('gzh')) {
    const gzhCtx = resetPlatformSyncBillingSession(syncForSearchPage!)
    const items = preloaded?.gzh ?? (await fetchGzhSearchItems(config, gzhCtx))
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
    ...dedupeTestFeedRows(douyinRows),
    ...dedupeTestFeedRows(xhsRows),
    ...dedupeTestFeedRows(shipinhaoRows),
    ...dedupeTestFeedRows(gzhRows),
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

  return { rows }
}
/**
 * 已接入 search-page 同步采集的平台（表单 `selectedSources` id）。
 * API 路径段可能与 id 不同，例如 shipinhao → `/api/v1/sync/wxvideo/search-page`。
 */
export const SYNC_COLLECTION_PLATFORM_IDS = ['douyin', 'xiaohongshu', 'shipinhao', 'gzh'] as const

export type SyncCollectionPlatformId = (typeof SYNC_COLLECTION_PLATFORM_IDS)[number]

export function isSyncCollectionPlatform(id: string): id is SyncCollectionPlatformId {
  return (SYNC_COLLECTION_PLATFORM_IDS as readonly string[]).includes(id)
}

/** YDDM `meta.platform` / 列表 `platform`（如 `mp`、`xhs`、`wxvideo`）→ 表单平台 id */
const YDDM_PLATFORM_TO_SYNC_ID: Record<string, SyncCollectionPlatformId> = {
  douyin: 'douyin',
  xhs: 'xiaohongshu',
  xiaohongshu: 'xiaohongshu',
  mp: 'gzh',
  gzh: 'gzh',
  wxvideo: 'shipinhao',
  shipinhao: 'shipinhao',
}

export function mapYddmPlatformToSyncId(
  raw: string | undefined | null,
): SyncCollectionPlatformId | null {
  const s = String(raw ?? '').trim().toLowerCase()
  if (!s) return null
  const hit = YDDM_PLATFORM_TO_SYNC_ID[s]
  if (hit) return hit
  return isSyncCollectionPlatform(s) ? s : null
}

export function readSyncCollectionPlatforms(config: Record<string, unknown>): SyncCollectionPlatformId[] {
  const raw = config.selectedSources ?? config.selected_sources
  if (!Array.isArray(raw)) return []
  const picked = new Set<SyncCollectionPlatformId>()
  for (const x of raw) {
    if (typeof x !== 'string') continue
    const s = x.trim()
    if (isSyncCollectionPlatform(s)) picked.add(s)
  }
  return SYNC_COLLECTION_PLATFORM_IDS.filter((id) => picked.has(id))
}

/** 各平台 search-page 路径（仅对已勾选平台发起请求） */
export const SYNC_SEARCH_PAGE_BY_PLATFORM: Record<
  SyncCollectionPlatformId,
  { path: string; label: string }
> = {
  douyin: { path: '/api/v1/sync/douyin/search-page', label: '抖音' },
  xiaohongshu: { path: '/api/v1/sync/xhs/search-page', label: '小红书' },
  shipinhao: { path: '/api/v1/sync/wxvideo/search-page', label: '视频号' },
  gzh: { path: '/api/v1/sync/wxvideo/search-page', label: '公众号' },
}

export const syncCollectionPlatformLabels: Record<SyncCollectionPlatformId, string> = {
  douyin: '抖音',
  xiaohongshu: '小红书',
  shipinhao: '视频号',
  gzh: '公众号',
}

export function defaultNewTableNameForPlatform(platform: SyncCollectionPlatformId): string {
  return `${syncCollectionPlatformLabels[platform]}数据表`
}

/** 运行中任务演示/飞书写入：仅当所选平台全部属于已接入列表 */
export function taskUsesOnlySyncCollectionPlatforms(platformKeys: string[] | undefined): boolean {
  if (!platformKeys?.length) return false
  return platformKeys.every((k) => isSyncCollectionPlatform(k))
}

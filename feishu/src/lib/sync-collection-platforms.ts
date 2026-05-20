/**
 * 已接入 search-page 同步采集的平台（表单 `selectedSources` id）。
 * API 路径段可能与 id 不同，例如 shipinhao → `/api/v1/sync/wxvideo/search-page`。
 */
export const SYNC_COLLECTION_PLATFORM_IDS = ['douyin', 'xiaohongshu', 'shipinhao', 'gzh'] as const

export type SyncCollectionPlatformId = (typeof SYNC_COLLECTION_PLATFORM_IDS)[number]

export function isSyncCollectionPlatform(id: string): id is SyncCollectionPlatformId {
  return (SYNC_COLLECTION_PLATFORM_IDS as readonly string[]).includes(id)
}

export function readSyncCollectionPlatforms(config: Record<string, unknown>): SyncCollectionPlatformId[] {
  const raw = config.selectedSources ?? config.selected_sources
  if (!Array.isArray(raw)) return []
  const out: SyncCollectionPlatformId[] = []
  for (const x of raw) {
    if (typeof x !== 'string') continue
    const s = x.trim()
    if (isSyncCollectionPlatform(s)) out.push(s)
  }
  return out
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

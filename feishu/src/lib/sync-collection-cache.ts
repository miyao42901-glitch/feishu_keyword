/**
 * 单次同步采集结果缓存：避免「提交采集」与「写入多维表格」重复请求 search-page。
 */

import type { PlatformKey } from '@/components/PlatformIcon.vue'

export type SyncItemsByPlatform = Partial<Record<PlatformKey, Record<string, unknown>[]>>

const cacheByTaskId = new Map<number, SyncItemsByPlatform>()

export function setSyncCollectionCache(taskId: number, items: SyncItemsByPlatform): void {
  if (!Object.keys(items).length) return
  cacheByTaskId.set(taskId, items)
}

/** 读取并清除缓存（写入飞书后调用，避免脏数据） */
export function takeSyncCollectionCache(taskId: number): SyncItemsByPlatform | undefined {
  const hit = cacheByTaskId.get(taskId)
  if (hit) cacheByTaskId.delete(taskId)
  return hit
}

export function peekSyncCollectionCache(taskId: number): SyncItemsByPlatform | undefined {
  return cacheByTaskId.get(taskId)
}

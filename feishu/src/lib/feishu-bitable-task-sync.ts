/**
 * 任务采集结果 → 飞书多维表格：自动建表（高级配置表名）并写入行数据。
 */

import type { PlatformKey } from '@/components/PlatformIcon.vue'
import { getFeishuTaskConfig, updateFeishuTaskConfig } from '@/lib/api'
import type { SyncFetchContext } from '@/lib/sync-api-common'
import {
  appendTestFeedRowsToBitable,
  ensureBitableTablesForTask,
  type TestFeedBitableDeps,
} from '@/lib/feishu-bitable-append-feed'
import { readSyncCollectionPlatforms } from '@/lib/sync-collection-platforms'
import { buildTestDataFeedFromConfig, taskUsesOnlyTestDataPlatforms } from '@/lib/test-data-feed'
import type { SyncItemsByPlatform } from '@/lib/sync-collection-cache'
import { takeSyncCollectionCache } from '@/lib/sync-collection-cache'

export function createTestFeedBitableDeps(): TestFeedBitableDeps {
  return {
    persistPlatformTableReference: async (input) => {
      const detail = await getFeishuTaskConfig(input.taskId)
      const raw = detail.config
      const cfg =
        raw != null && typeof raw === 'object' && !Array.isArray(raw)
          ? ({ ...raw } as Record<string, unknown>)
          : {}
      const rawIds = cfg.platformExistingTableIds ?? cfg.platform_existing_table_ids
      const ids: Record<string, unknown> =
        rawIds && typeof rawIds === 'object' && !Array.isArray(rawIds)
          ? { ...(rawIds as Record<string, unknown>) }
          : {}
      if (input.tableId.trim()) {
        ids[input.platform] = input.tableId
      } else {
        delete ids[input.platform]
      }
      cfg.platformExistingTableIds = ids
      await updateFeishuTaskConfig(input.taskId, cfg)
    },
  }
}

function readPlatformKeys(config: Record<string, unknown>): PlatformKey[] {
  return readSyncCollectionPlatforms(config)
}

/**
 * 按任务配置创建平台表（`tableMode === 'new'` 时用高级配置中的表名）并写入采集行。
 * 单次任务在「已完成」态也会执行（不依赖列表「运行中」轮询）。
 */
export async function syncTaskCollectionToBitable(input: {
  taskId: number
  taskName: string
  config: Record<string, unknown>
  syncCtx: SyncFetchContext
  /** 与本次提交采集同批数据，避免二次 search-page */
  preloadedItems?: SyncItemsByPlatform
}): Promise<{ tableReady: boolean; rowCount: number; written: number }> {
  const platforms = readPlatformKeys(input.config)
  if (!platforms.length || !taskUsesOnlyTestDataPlatforms(platforms)) {
    return { tableReady: false, rowCount: 0, written: 0 }
  }

  const deps = createTestFeedBitableDeps()
  await ensureBitableTablesForTask(input.taskId, input.config, deps)

  let cfg = input.config
  try {
    const detail = await getFeishuTaskConfig(input.taskId)
    if (detail.config != null && typeof detail.config === 'object' && !Array.isArray(detail.config)) {
      cfg = detail.config as Record<string, unknown>
    }
  } catch {
    /* 使用入参配置 */
  }

  const preloadedItems =
    input.preloadedItems ?? takeSyncCollectionCache(input.taskId)

  const { rows } = await buildTestDataFeedFromConfig({
    taskId: input.taskId,
    taskName: input.taskName,
    config: cfg,
    sync: input.syncCtx,
    preloadedItems,
  })

  const configByTaskId = new Map<number, Record<string, unknown>>([[input.taskId, cfg]])
  const writtenByTask = await appendTestFeedRowsToBitable(rows, configByTaskId, deps)
  const written = writtenByTask.get(input.taskId) ?? 0

  takeSyncCollectionCache(input.taskId)

  if (import.meta.env.DEV) {
    const byPlatform = (p: PlatformKey) => rows.filter((r) => r.platform === p)
    console.log('[bitable-sync]', {
      taskId: input.taskId,
      rowCount: rows.length,
      written,
      usedPreload: Boolean(preloadedItems),
      rowsByPlatform: {
        douyin: byPlatform('douyin').length,
        xiaohongshu: byPlatform('xiaohongshu').length,
        shipinhao: byPlatform('shipinhao').length,
        gzh: byPlatform('gzh').length,
      },
      sampleFieldColumns: {
        douyin: byPlatform('douyin')[0]?.fieldColumns,
        xiaohongshu: byPlatform('xiaohongshu')[0]?.fieldColumns,
      },
    })
  }

  return { tableReady: true, rowCount: rows.length, written }
}

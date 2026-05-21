/**
 * 任务采集结果 → 飞书多维表格：自动建表（高级配置表名）并写入行数据。
 */

import type { PlatformKey } from '@/components/PlatformIcon.vue'
import { loadLocalTaskConfig, mergeLocalTaskConfig } from '@/lib/feishu-task-config-local'
import type { SyncFetchContext } from '@/lib/sync-api-common'
import {
  appendTestFeedRowsToBitable,
  clearGlobalBitableAppendDedup,
  ensureBitableTablesForTask,
  readPlatformNewTableName,
  type TestFeedBitableDeps,
} from '@/lib/feishu-bitable-append-feed'
import { switchBitableUiToTable } from '@/lib/feishu-bitable-tables'
import {
  defaultNewTableNameForPlatform,
  isSyncCollectionPlatform,
  readSyncCollectionPlatforms,
  type SyncCollectionPlatformId,
} from '@/lib/sync-collection-platforms'

function mergePlatformsForBitableTables(
  ...groups: (SyncCollectionPlatformId[] | undefined)[]
): SyncCollectionPlatformId[] {
  const out = new Set<SyncCollectionPlatformId>()
  for (const g of groups) {
    for (const p of g ?? []) {
      if (isSyncCollectionPlatform(p)) out.add(p)
    }
  }
  return [...out]
}
import { buildTestDataFeedFromConfig, taskUsesOnlyTestDataPlatforms } from '@/lib/test-data-feed'
import {
  applyFullSourceFieldSelectionForBitableWrite,
  ensureSourceFieldSelectionInConfig,
} from '@/views/TaskCreateForm/source-field-catalog'
import type { SyncItemsByPlatform } from '@/lib/sync-collection-cache'
import { takeSyncCollectionCache } from '@/lib/sync-collection-cache'
import { applyTaskTypeFromListCard } from '@/lib/feishu-async-task-config'
import { clearRealtimeAsyncBindings, isRealtimeTaskConfig } from '@/lib/async-task-api'
import type { TaskCardModel } from '@/views/tasks/types'

export function createTestFeedBitableDeps(): TestFeedBitableDeps {
  return {
    persistPlatformTableReference: async (input) => {
      const raw = loadLocalTaskConfig(input.taskId)
      const cfg =
        raw != null ? ({ ...raw } as Record<string, unknown>) : ({} as Record<string, unknown>)
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
      mergeLocalTaskConfig(input.taskId, cfg)
    },
  }
}

function readPlatformKeys(config: Record<string, unknown>): SyncCollectionPlatformId[] {
  return readSyncCollectionPlatforms(config)
}

function readTableMode(cfg: Record<string, unknown>): 'new' | 'existing' {
  const m = cfg.tableMode ?? cfg.table_mode
  return m === 'existing' ? 'existing' : 'new'
}

function hasBoundExistingTables(cfg: Record<string, unknown>): boolean {
  const raw = cfg.platformExistingTableIds ?? cfg.platform_existing_table_ids
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return false
  return Object.values(raw as Record<string, unknown>).some(
    (v) => typeof v === 'string' && v.trim().length > 0,
  )
}

function platformsFromPreloaded(preloaded?: SyncItemsByPlatform): SyncCollectionPlatformId[] {
  if (!preloaded) return []
  const out: SyncCollectionPlatformId[] = []
  for (const id of ['douyin', 'xiaohongshu', 'shipinhao', 'gzh'] as const) {
    const items = preloaded[id]
    if (items?.length) out.push(id)
  }
  return out
}

/** 预加载结果里出现过的平台（含 0 条），用于先建表 */
function platformsTouchedInPreload(preloaded?: SyncItemsByPlatform): SyncCollectionPlatformId[] {
  if (!preloaded) return []
  return (['douyin', 'xiaohongshu', 'shipinhao', 'gzh'] as const).filter(
    (id) => preloaded[id] != null,
  )
}

/**
 * 列表执行写表：合并本次采集 config、卡片平台、预加载结果，保证能建表/写行。
 */
export function normalizeConfigForBitableSync(
  config: Record<string, unknown>,
  options?: {
    card?: TaskCardModel
    preloadedItems?: SyncItemsByPlatform
  },
): Record<string, unknown> {
  let cfg: Record<string, unknown> = { ...config }
  if (options?.card) {
    cfg = applyTaskTypeFromListCard(cfg, options.card)
  }
  if (isRealtimeTaskConfig(cfg)) {
    cfg = clearRealtimeAsyncBindings(cfg)
  }

  const fromCard = options?.card?.platformKeys?.filter((k): k is SyncCollectionPlatformId =>
    isSyncCollectionPlatform(k),
  )
  let platforms = readPlatformKeys(cfg)
  if (!platforms.length && fromCard?.length) {
    platforms = fromCard
    cfg.selectedSources = platforms
  }
  if (!platforms.length) {
    platforms = platformsFromPreloaded(options?.preloadedItems)
    if (platforms.length) cfg.selectedSources = platforms
  }

  const mode = readTableMode(cfg)
  if (mode !== 'existing' || !hasBoundExistingTables(cfg)) {
    cfg.tableMode = 'new'
  }

  const names = (cfg.platformNewTableNames ?? cfg.platform_new_table_names) as
    | Record<string, unknown>
    | undefined
  const nameMap: Record<string, string> =
    names && typeof names === 'object' && !Array.isArray(names)
      ? Object.fromEntries(
          Object.entries(names)
            .filter((entry): entry is [string, string] => {
              const v = entry[1]
              return typeof v === 'string' && v.trim().length > 0
            })
            .map(([k, v]) => [k, v.trim()]),
        )
      : {}
  const nameMapForSelected: Record<string, string> = {}
  for (const p of platforms) {
    nameMapForSelected[p] = nameMap[p]?.trim() || defaultNewTableNameForPlatform(p)
  }
  if (platforms.length) cfg.platformNewTableNames = nameMapForSelected

  ensureSourceFieldSelectionInConfig(cfg)
  applyFullSourceFieldSelectionForBitableWrite(cfg)
  return cfg
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
  card?: TaskCardModel
  /** 与本次提交采集同批数据，避免二次 search-page */
  preloadedItems?: SyncItemsByPlatform
}): Promise<{
  tableReady: boolean
  rowCount: number
  written: number
  createdTables: string[]
  /** 写入完成后建议切换到的数据表 id */
  focusTableId?: string
}> {
  clearGlobalBitableAppendDedup()

  const cfgBase = normalizeConfigForBitableSync(input.config, {
    card: input.card,
    preloadedItems: input.preloadedItems,
  })

  let platforms = readPlatformKeys(cfgBase)
  const touchedPreload = platformsTouchedInPreload(input.preloadedItems)
  const withDataPreload = platformsFromPreloaded(input.preloadedItems)
  if (touchedPreload.length) {
    platforms = [...new Set([...platforms, ...touchedPreload])]
  } else if (!platforms.length && withDataPreload.length) {
    platforms = withDataPreload
  }

  if (!platforms.length) {
    throw new Error('未识别到采集平台，无法新建数据表（请保存任务并勾选平台）')
  }
  if (!taskUsesOnlyTestDataPlatforms(platforms)) {
    throw new Error('当前平台暂不支持自动写入多维表格')
  }

  mergeLocalTaskConfig(input.taskId, cfgBase)

  const deps = createTestFeedBitableDeps()
  let createdTables: string[] = []

  let cfg = loadLocalTaskConfig(input.taskId) ?? cfgBase

  const preloadedItems =
    input.preloadedItems ?? takeSyncCollectionCache(input.taskId)

  const feed = await buildTestDataFeedFromConfig({
    taskId: input.taskId,
    taskName: input.taskName,
    config: cfg,
    sync: input.syncCtx,
    preloadedItems,
    card: input.card,
  })
  const rows = feed.rows

  const platformsForTables = mergePlatformsForBitableTables(
    platforms,
    feed.resultPlatforms,
    readPlatformKeys(cfg),
  )

  if (readTableMode(cfg) === 'new' && platformsForTables.length) {
    createdTables = await ensureBitableTablesForTask(input.taskId, cfg, deps, {
      platforms: platformsForTables,
    })
    cfg = loadLocalTaskConfig(input.taskId) ?? cfg
  }

  if (!rows.length) {
    const firstId = platforms.map((p) => readPlatformExistingTableIdFromCfg(cfg, p)).find(Boolean)
    if (firstId) await switchBitableUiToTable(firstId)
    if (createdTables.length) {
      return {
        tableReady: readTableMode(cfg) === 'new',
        rowCount: 0,
        written: 0,
        createdTables,
        focusTableId: firstId,
      }
    }
    throw new Error('采集结果为空，未写入多维表格（请检查平台返回或任务配置）')
  }

  const configByTaskId = new Map<number, Record<string, unknown>>([[input.taskId, cfg]])
  const writtenByTask = await appendTestFeedRowsToBitable(rows, configByTaskId, deps)
  const written = writtenByTask.get(input.taskId) ?? 0

  let focusTableId: string | undefined
  for (const p of platforms) {
    const tid = readPlatformExistingTableIdFromCfg(cfg, p)
    if (tid) {
      focusTableId = tid
      const hasRows = rows.some((r) => r.platform === p)
      if (hasRows) break
    }
  }
  if (focusTableId) {
    await switchBitableUiToTable(focusTableId)
  }

  takeSyncCollectionCache(input.taskId)

  if (import.meta.env.DEV) {
    const byPlatform = (p: PlatformKey) => rows.filter((r) => r.platform === p)
    console.log('[bitable-sync]', {
      taskId: input.taskId,
      tableMode: readTableMode(cfg),
      rowCount: rows.length,
      written,
      createdTables,
      usedPreload: Boolean(preloadedItems),
      douyin: byPlatform('douyin').length,
      xhs: byPlatform('xiaohongshu').length,
    })
  }

  return {
    tableReady: readTableMode(cfg) === 'new',
    rowCount: rows.length,
    written,
    createdTables,
    focusTableId,
  }
}

/**
 * 单次任务：某一平台 search-page 完成后立即建表并写入（对齐 FeishuPlugin「先 addTable 再 addRecords」）。
 * 不调用 `clearGlobalBitableAppendDedup`，由调用方在整次「立即执行」开始时清一次即可。
 */
export async function syncSinglePlatformCollectionToBitable(input: {
  taskId: number
  taskName: string
  config: Record<string, unknown>
  syncCtx: SyncFetchContext
  platform: SyncCollectionPlatformId
  items: Record<string, unknown>[]
}): Promise<{
  rowCount: number
  written: number
  createdTables: string[]
  focusTableId?: string
}> {
  const preloaded: SyncItemsByPlatform = { [input.platform]: input.items }
  const cfgBase = normalizeConfigForBitableSync(input.config, { preloadedItems: preloaded })
  if (!taskUsesOnlyTestDataPlatforms([input.platform])) {
    throw new Error('当前平台暂不支持自动写入多维表格')
  }

  mergeLocalTaskConfig(input.taskId, cfgBase)
  const deps = createTestFeedBitableDeps()
  let createdTables: string[] = []

  let cfg = loadLocalTaskConfig(input.taskId) ?? cfgBase
  if (readTableMode(cfg) === 'new') {
    createdTables = await ensureBitableTablesForTask(input.taskId, cfg, deps, {
      platforms: [input.platform],
    })
    cfg = loadLocalTaskConfig(input.taskId) ?? cfg
  }

  const feed = await buildTestDataFeedFromConfig({
    taskId: input.taskId,
    taskName: input.taskName,
    config: cfg,
    sync: input.syncCtx,
    preloadedItems: preloaded,
    onlyPlatforms: [input.platform],
  })
  const rows = feed.rows.filter((r) => r.platform === input.platform)
  const tableName = readPlatformNewTableName(cfg, input.platform)

  if (!rows.length) {
    const tableId = readPlatformExistingTableIdFromCfg(cfg, input.platform)
    if (tableId) await switchBitableUiToTable(tableId)
    return { rowCount: 0, written: 0, createdTables: createdTables.length ? createdTables : [tableName], focusTableId: tableId || undefined }
  }

  const configByTaskId = new Map<number, Record<string, unknown>>([[input.taskId, cfg]])
  const writtenByTask = await appendTestFeedRowsToBitable(rows, configByTaskId, deps)
  const written = writtenByTask.get(input.taskId) ?? 0
  if (rows.length > 0 && written === 0) {
    throw new Error(
      `已解析 ${rows.length} 条，但写入飞书为 0 条（字段映射或 addRecords 失败，请查看控制台 [bitable-append]）`,
    )
  }
  const focusTableId = readPlatformExistingTableIdFromCfg(cfg, input.platform) || undefined
  if (focusTableId) await switchBitableUiToTable(focusTableId)

  if (import.meta.env.DEV) {
    console.log('[bitable-sync-platform]', {
      platform: input.platform,
      items: input.items.length,
      rowCount: rows.length,
      written,
      tableName,
      focusTableId,
    })
  }

  return {
    rowCount: rows.length,
    written,
    createdTables: createdTables.length ? createdTables : [tableName],
    focusTableId,
  }
}

function readPlatformExistingTableIdFromCfg(
  cfg: Record<string, unknown>,
  platform: SyncCollectionPlatformId,
): string {
  const raw = cfg.platformExistingTableIds ?? cfg.platform_existing_table_ids
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return ''
  const v = (raw as Record<string, unknown>)[platform]
  return typeof v === 'string' ? v.trim() : ''
}

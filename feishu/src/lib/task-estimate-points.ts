import type { PlatformKey } from '@/components/PlatformIcon.vue'
import { countScheduledExecutionRounds } from '@/lib/datetime-task-window'
import { estimatedApiPagesNeeded } from '@/lib/sync-platform-page-size'
import { syncPointsPackageForPlatform, TARGET_POINTS_PER_ROW } from '@/lib/sync-set-discount'
import type { SyncItemsByPlatform } from '@/lib/sync-collection-cache'
import { readSyncCollectionPlatforms } from '@/lib/sync-collection-platforms'
import { readSearchKeywords } from '@/lib/sync-search-shared'
import type { TaskCreateFormModel } from '@/views/TaskCreateForm/types'

export type TaskPointsEstimateBreakdown = {
  /** 折扣生效后按实采条数折算（约 {@link TARGET_POINTS_PER_ROW}/条），仅供参考 */
  rowPoints: number
  /** 按预估 search-page 次数 × 平台积分档位（上限，与 YDDM 按次扣费口径一致） */
  apiCallPoints: number
  total: number
  /** 定时任务：监控窗口内预计采集轮次；单次任务为 1 */
  scheduledExecutionRounds: number
  /** 每轮、每关键词、各平台按选择条数折算的「按条」积分（未乘轮次/关键词） */
  rowPointsPerRound: number
  /** 每轮、每关键词、各平台按预估请求次数 × 档位（未乘轮次/关键词） */
  apiCallPointsPerRound: number
}

/** 各平台统一：每条 {@link TARGET_POINTS_PER_ROW} 积分（折扣生效后） */
export function pointsPerRowForPlatform(_platform: PlatformKey): number {
  return TARGET_POINTS_PER_ROW
}

/** 按平台实际采集条数估算积分（翻页凑满或不足上限时按实条数计；折扣生效后口径） */
export function estimatePointsForPlatformRows(platform: PlatformKey, rowCount: number): number {
  const n = Math.max(0, Math.floor(rowCount))
  return n * pointsPerRowForPlatform(platform)
}

/**
 * 按平台选择条数估算 search-page 请求积分上限：预估翻页次数 × 该平台积分档位。
 */
export function estimateApiCallPointsForPlatform(platform: PlatformKey, rowCount: number): number {
  const pages = estimatedApiPagesNeeded(rowCount, platform)
  const pkg = syncPointsPackageForPlatform(platform)
  return pages * pkg
}

/** 各平台实采条数汇总积分（折扣后按条，任务完成展示用） */
export function estimatePointsFromItemsByPlatform(itemsByPlatform: SyncItemsByPlatform): number {
  let sum = 0
  for (const [platform, items] of Object.entries(itemsByPlatform) as [
    PlatformKey,
    Record<string, unknown>[] | undefined,
  ][]) {
    if (!items?.length) continue
    sum += estimatePointsForPlatformRows(platform, items.length)
  }
  return Math.ceil(sum)
}

function readKeywordMultiplier(keywords: string[]): number {
  const n = keywords.map((k) => k.trim()).filter(Boolean).length
  return n > 0 ? n : 1
}

function buildPointsEstimate(input: {
  rowCount: number
  sources: PlatformKey[]
  scheduledExecutionRounds: number
  keywordMultiplier: number
}): TaskPointsEstimateBreakdown {
  const { rowCount, sources, scheduledExecutionRounds, keywordMultiplier } = input
  const rowPointsPerRound = sources.reduce(
    (sum, platform) => sum + estimatePointsForPlatformRows(platform, rowCount),
    0,
  )
  const apiCallPointsPerRound = sources.reduce(
    (sum, platform) => sum + estimateApiCallPointsForPlatform(platform, rowCount),
    0,
  )
  const roundKeywordFactor = scheduledExecutionRounds * keywordMultiplier
  const rowPoints = rowPointsPerRound * roundKeywordFactor
  const apiCallPoints = apiCallPointsPerRound * roundKeywordFactor
  return {
    rowPoints,
    apiCallPoints,
    total: Math.ceil(apiCallPoints),
    scheduledExecutionRounds,
    rowPointsPerRound,
    apiCallPointsPerRound,
  }
}

/**
 * 预估消耗上限：各勾选平台按「凑满选择条数所需的 search-page 次数 × 积分档位」累加，
 * 再 × 关键词数 × 定时轮次。与 YDDM 按接口扣费（档位约 1000/1500/2000/次）对齐；
 * 折扣生效后实扣可能低于本值（约按实采条数 × 100）。
 */
export function estimateTaskPointsBreakdown(form: TaskCreateFormModel): TaskPointsEstimateBreakdown {
  const rowCount = Math.max(0, Math.floor(Number(form.dataRange)) || 0)
  const sources = form.selectedSources?.length ? form.selectedSources : []
  const scheduledExecutionRounds =
    form.taskType === 'scheduled'
      ? countScheduledExecutionRounds(form.effectiveAt, form.expireAt, form.crawlFrequency)
      : 1
  const keywordMultiplier = readKeywordMultiplier(
    form.keywords?.map((k) => String(k)) ?? [],
  )
  return buildPointsEstimate({
    rowCount,
    sources,
    scheduledExecutionRounds,
    keywordMultiplier,
  })
}

/** 从任务配置 JSON 估算（列表/详情展示用） */
export function estimateTaskPointsBreakdownFromConfig(
  config: Record<string, unknown>,
): TaskPointsEstimateBreakdown {
  const rowCount = Math.max(0, Math.floor(Number(config.dataRange ?? config.data_range)) || 0)
  const sources = readSyncCollectionPlatforms(config)
  const tt = config.taskType ?? config.task_type
  const scheduledExecutionRounds =
    tt === 'scheduled'
      ? countScheduledExecutionRounds(
          config.effectiveAt ?? config.effective_at,
          config.expireAt ?? config.expire_at,
          config.crawlFrequency ?? config.crawl_frequency,
        )
      : 1
  const keywordMultiplier = readKeywordMultiplier(readSearchKeywords(config))
  return buildPointsEstimate({
    rowCount,
    sources,
    scheduledExecutionRounds,
    keywordMultiplier,
  })
}

/** @deprecated 请使用 `estimateTaskPointsBreakdown` */
export function estimateTaskSavePoints(form: TaskCreateFormModel): number {
  return estimateTaskPointsBreakdown(form).total
}

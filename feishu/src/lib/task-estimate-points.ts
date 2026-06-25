import type { PlatformKey } from '@/components/PlatformIcon.vue'
import { countScheduledExecutionRounds } from '@/lib/datetime-task-window'
import {
  estimatedRowsFromPages,
  normalizeDataPageCount,
} from '@/lib/sync-platform-page-size'
import { syncPointsPackageForPlatform, TARGET_POINTS_PER_ROW } from '@/lib/sync-set-discount'
import type { SyncItemsByPlatform } from '@/lib/sync-collection-cache'
import { readSyncCollectionPlatforms } from '@/lib/sync-collection-platforms'
import { readSearchKeywords } from '@/lib/sync-search-shared'
import type { TaskCreateFormModel } from '@/views/TaskCreateForm/types'

/** 预估消耗（上限）：每条按 0.05 元计（1000 积分 = 1 元 → 50 积分/条） */
export const ESTIMATE_YUAN_PER_ROW = 0.05
export const POINTS_PER_YUAN = 1000

export type CollectionSuccessSummary = {
  articleCount: number
  consumptionPoints: number
  balancePoints: number
}

export function buildCollectionSuccessSummary(
  articleCount: number,
  balancePoints: number,
): CollectionSuccessSummary {
  const count = Math.max(0, Math.floor(articleCount))
  return {
    articleCount: count,
    consumptionPoints: estimateConsumptionCapPointsForRows(count),
    balancePoints: Math.max(0, Math.floor(balancePoints)),
  }
}

export type TaskPointsEstimateBreakdown = {
  /** 折扣生效后按实采条数折算（约 {@link TARGET_POINTS_PER_ROW}/条），仅供参考 */
  rowPoints: number
  /** 按预估 search-page 次数 × 平台积分档位（仅供参考，不再用于上限展示） */
  apiCallPoints: number
  total: number
  /** 定时任务：监控窗口内预计采集轮次；单次任务为 1 */
  scheduledExecutionRounds: number
  /** 每轮、每关键词、各平台按作品数据范围（页数）折算的「按条」积分（未乘轮次/关键词） */
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
 * 按平台作品数据范围（页数）估算 search-page 请求积分：页数 × 该平台积分档位。
 */
export function estimateApiCallPointsForPlatform(platform: PlatformKey, pageCount: number): number {
  const pages = normalizeDataPageCount(pageCount)
  return pages * syncPointsPackageForPlatform(platform)
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

/** 预估条数上限 × 0.05 元/条，折算为积分（单平台单关键词单轮） */
export function estimateConsumptionCapPointsForRows(rowCount: number): number {
  const rows = Math.max(0, Math.floor(rowCount))
  return rows * ESTIMATE_YUAN_PER_ROW * POINTS_PER_YUAN
}

function buildPointsEstimate(input: {
  pageCount: number
  sources: PlatformKey[]
  scheduledExecutionRounds: number
  keywordMultiplier: number
}): TaskPointsEstimateBreakdown {
  const { pageCount, sources, scheduledExecutionRounds, keywordMultiplier } = input
  const pages = normalizeDataPageCount(pageCount)
  const rowPointsPerRound = sources.reduce(
    (sum, platform) => sum + estimatePointsForPlatformRows(platform, estimatedRowsFromPages(pages, platform)),
    0,
  )
  const apiCallPointsPerRound = sources.reduce(
    (sum, platform) => sum + estimateApiCallPointsForPlatform(platform, pages),
    0,
  )
  const roundKeywordFactor = scheduledExecutionRounds * keywordMultiplier
  const rowPoints = rowPointsPerRound * roundKeywordFactor
  const apiCallPoints = apiCallPointsPerRound * roundKeywordFactor
  const capPointsPerRound = sources.reduce(
    (sum, platform) =>
      sum + estimateConsumptionCapPointsForRows(estimatedRowsFromPages(pages, platform)),
    0,
  )
  const consumptionCap = capPointsPerRound * roundKeywordFactor
  return {
    rowPoints,
    apiCallPoints,
    total: Math.ceil(consumptionCap),
    scheduledExecutionRounds,
    rowPointsPerRound,
    apiCallPointsPerRound,
  }
}

/**
 * 预估消耗上限：作品数据范围（页数）× 每页典型条数 × 0.05 元/条，
 * 再 × 勾选平台数 × 关键词数 × 定时轮次。
 */
export function estimateTaskPointsBreakdown(form: TaskCreateFormModel): TaskPointsEstimateBreakdown {
  const pageCount = normalizeDataPageCount(form.dataRange)
  const sources = form.selectedSources?.length ? form.selectedSources : []
  const scheduledExecutionRounds =
    form.taskType === 'scheduled'
      ? countScheduledExecutionRounds(form.effectiveAt, form.expireAt, form.crawlFrequency)
      : 1
  const keywordMultiplier = readKeywordMultiplier(
    form.keywords?.map((k) => String(k)) ?? [],
  )
  return buildPointsEstimate({
    pageCount,
    sources,
    scheduledExecutionRounds,
    keywordMultiplier,
  })
}

/** 从任务配置 JSON 估算（列表/详情展示用） */
export function estimateTaskPointsBreakdownFromConfig(
  config: Record<string, unknown>,
): TaskPointsEstimateBreakdown {
  const pageCount = normalizeDataPageCount(config.dataRange ?? config.data_range)
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
    pageCount,
    sources,
    scheduledExecutionRounds,
    keywordMultiplier,
  })
}

/** @deprecated 请使用 `estimateTaskPointsBreakdown` */
export function estimateTaskSavePoints(form: TaskCreateFormModel): number {
  return estimateTaskPointsBreakdown(form).total
}

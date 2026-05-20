import type { PlatformKey } from '@/components/PlatformIcon.vue'
import { countScheduledExecutionRounds } from '@/lib/datetime-task-window'
import { TARGET_POINTS_PER_ROW } from '@/lib/sync-set-discount'
import type { SyncItemsByPlatform } from '@/lib/sync-collection-cache'
import { readSyncCollectionPlatforms } from '@/lib/sync-collection-platforms'
import { readSearchKeywords } from '@/lib/sync-search-shared'
import type { TaskCreateFormModel } from '@/views/TaskCreateForm/types'

export type TaskPointsEstimateBreakdown = {
  /** 各平台：选择条数 × 每条预估积分（已含轮次、关键词乘数） */
  rowPoints: number
  /** 保留字段，当前计费口径不计入预估 */
  apiCallPoints: number
  total: number
  /** 定时任务：监控窗口内预计采集轮次；单次任务为 1 */
  scheduledExecutionRounds: number
  /** 每轮、每平台按选择条数折算的积分（未乘轮次/关键词） */
  rowPointsPerRound: number
}

/** 各平台统一：每条 {@link TARGET_POINTS_PER_ROW} 积分（由折扣档位 ÷ rate 保证） */
export function pointsPerRowForPlatform(_platform: PlatformKey): number {
  return TARGET_POINTS_PER_ROW
}

/** 按平台实际采集条数估算积分（翻页凑满或不足上限时按实条数计） */
export function estimatePointsForPlatformRows(platform: PlatformKey, rowCount: number): number {
  const n = Math.max(0, Math.floor(rowCount))
  return n * pointsPerRowForPlatform(platform)
}

/** 各平台实采条数汇总积分 */
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

function readKeywordMultiplier(form: TaskCreateFormModel): number {
  const keywords = form.keywords?.map((k) => k.trim()).filter(Boolean) ?? []
  return keywords.length > 0 ? keywords.length : 1
}

/**
 * 预估消耗上限：各勾选平台 × 选择条数 × 每条积分。
 * 定时任务再 × 监控窗口内预计采集轮次 × 关键词数（与异步提交 platform×keyword 条数一致）。
 * 实际扣费按每轮、每平台实采条数累计。
 */
export function estimateTaskPointsBreakdown(form: TaskCreateFormModel): TaskPointsEstimateBreakdown {
  const rowCount = Math.max(0, Math.floor(Number(form.dataRange)) || 0)
  const sources = form.selectedSources?.length ? form.selectedSources : []
  const rowPointsPerRound = sources.reduce(
    (sum, platform) => sum + estimatePointsForPlatformRows(platform, rowCount),
    0,
  )
  const scheduledExecutionRounds =
    form.taskType === 'scheduled'
      ? countScheduledExecutionRounds(form.effectiveAt, form.expireAt, form.crawlFrequency)
      : 1
  const keywordMultiplier = form.taskType === 'scheduled' ? readKeywordMultiplier(form) : 1
  const rowPoints = rowPointsPerRound * scheduledExecutionRounds * keywordMultiplier
  return {
    rowPoints,
    apiCallPoints: 0,
    total: Math.ceil(rowPoints),
    scheduledExecutionRounds,
    rowPointsPerRound,
  }
}

/** 从任务配置 JSON 估算（列表/详情展示用） */
export function estimateTaskPointsBreakdownFromConfig(
  config: Record<string, unknown>,
): TaskPointsEstimateBreakdown {
  const rowCount = Math.max(0, Math.floor(Number(config.dataRange ?? config.data_range)) || 0)
  const sources = readSyncCollectionPlatforms(config)
  const rowPointsPerRound = sources.reduce(
    (sum, platform) => sum + estimatePointsForPlatformRows(platform, rowCount),
    0,
  )
  const tt = config.taskType ?? config.task_type
  const scheduledExecutionRounds =
    tt === 'scheduled'
      ? countScheduledExecutionRounds(
          config.effectiveAt ?? config.effective_at,
          config.expireAt ?? config.expire_at,
          config.crawlFrequency ?? config.crawl_frequency,
        )
      : 1
  const keywords = readSearchKeywords(config)
  const keywordMultiplier = tt === 'scheduled' ? (keywords.length > 0 ? keywords.length : 1) : 1
  const rowPoints = rowPointsPerRound * scheduledExecutionRounds * keywordMultiplier
  return {
    rowPoints,
    apiCallPoints: 0,
    total: Math.ceil(rowPoints),
    scheduledExecutionRounds,
    rowPointsPerRound,
  }
}

/** @deprecated 请使用 `estimateTaskPointsBreakdown` */
export function estimateTaskSavePoints(form: TaskCreateFormModel): number {
  return estimateTaskPointsBreakdown(form).total
}

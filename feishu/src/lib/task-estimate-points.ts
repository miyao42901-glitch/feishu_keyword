import { POINTS_PER_DATA_ROW } from '@/lib/account-balance'
import type { TaskCreateFormModel } from '@/views/TaskCreateForm/types'

export type TaskPointsEstimateBreakdown = {
  /** 采集条数 × 每条积分 */
  rowPoints: number
  /** 保留字段，当前计费口径不计入预估 */
  apiCallPoints: number
  total: number
}

/**
 * 预估消耗积分：按「选择条数 × {@link POINTS_PER_DATA_ROW}」计算。
 * 前端展示用，非正式扣费依据。
 */
export function estimateTaskPointsBreakdown(form: TaskCreateFormModel): TaskPointsEstimateBreakdown {
  const rowCount = Math.max(0, Math.floor(Number(form.dataRange)) || 0)
  const rowPoints = rowCount * POINTS_PER_DATA_ROW
  return {
    rowPoints,
    apiCallPoints: 0,
    total: rowPoints,
  }
}

/** @deprecated 请使用 `estimateTaskPointsBreakdown` */
export function estimateTaskSavePoints(form: TaskCreateFormModel): number {
  return estimateTaskPointsBreakdown(form).total
}

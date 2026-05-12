import type { TaskCreateFormModel } from '@/views/TaskCreateForm/types'
import { countOptionalSelectedSourceFields } from '@/views/TaskCreateForm/source-field-catalog'

export type TaskPointsEstimateBreakdown = {
  /** 选择条数：与「列表条数」一致，按 1 点/条计入 */
  rowPoints: number
  /**
   * 平台调用接口数估算：每个已选信源至少 1 次列表类调用；
   * 每多勾一项非必选采集字段记为额外 1 次接口（必选字段不计入；前端展示口径）。
   */
  apiCallPoints: number
  total: number
}

/**
 * 预估消耗拆解：选择条数（一条一积分点）+ 平台调用接口数（见返回值说明）。
 * 前端展示用，非扣费依据；后端若提供正式预估可替换。
 */
export function estimateTaskPointsBreakdown(form: TaskCreateFormModel): TaskPointsEstimateBreakdown {
  const rowPoints = Math.max(0, Math.floor(Number(form.dataRange)) || 0)
  let apiCallPoints = 0
  for (const pl of form.selectedSources) {
    const extra = countOptionalSelectedSourceFields(form, pl)
    apiCallPoints += 1 + extra
  }
  return {
    rowPoints,
    apiCallPoints,
    total: rowPoints + apiCallPoints,
  }
}

/** @deprecated 请使用 `estimateTaskPointsBreakdown`；保留别名供简短展示 */
export function estimateTaskSavePoints(form: TaskCreateFormModel): number {
  return estimateTaskPointsBreakdown(form).total
}

import type { TaskCreateFormModel } from '@/views/TaskCreateForm/types'

/**
 * 根据当前表单字段估算「保存/运行」大致点数（前端展示用，非扣费依据）。
 * 后续若后端提供正式预估接口，可改为请求结果。
 */
export function estimateTaskSavePoints(form: TaskCreateFormModel): number {
  const platforms = Math.max(1, form.selectedSources.length)
  const range = Math.max(1, form.dataRange)
  const keywords = form.keywords.length
  const exclude = form.excludeKeywords.length
  let pts = 2
  pts += platforms
  pts += Math.min(8, Math.ceil(range / 150))
  pts += Math.min(5, Math.ceil((keywords + exclude) / 5))
  if (form.taskType === 'realtime') {
    pts += 2
  } else {
    const freq = Number(form.crawlFrequency) || 5
    pts += Math.min(4, Math.max(0, Math.ceil(60 / freq) - 1))
  }
  return Math.max(1, Math.min(99, Math.round(pts)))
}

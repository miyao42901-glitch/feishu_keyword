/**
 * 任务列表展示模型（列表接口未返回运行态与信源时，由前端补充占位或本地推导）。
 */
export type TaskListStatus = 'running' | 'completed' | 'stopped' | 'failed'

export type TaskListTaskType = 'scheduled'

export interface TaskListItem {
  id: number
  title: string
  status: TaskListStatus
  /** 已用顿号拼接好的平台文案，如「小红书、微博」 */
  platformsLabel: string
  taskType: TaskListTaskType
  /** 展示用日期，如 2024-01-15 */
  dateLabel: string
  updatedAt: string
}

/**
 * 任务列表卡片运行态（与表单 `runStatus` / 列表 `run_status` 一致）。
 */
import type { TaskRunStatus } from '@/views/TaskCreateForm/types'

export type { TaskRunStatus } from '@/views/TaskCreateForm/types'

/** 列表单行视图模型（由接口列表项映射而来） */
export interface TaskCardModel {
  id: number
  name: string
  platformsLabel: string
  taskTypeLabel: string
  dateLabel: string
  status: TaskRunStatus
  /** 角标未读数；0 表示不展示 */
  notificationCount: number
}

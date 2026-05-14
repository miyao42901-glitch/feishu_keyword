/**
 * 任务列表卡片：状态由接口 `display_status` / `stopped_kind` 展示，不在前端计算业务态。
 */
import type { TaskRunStatus, TaskStoppedKind } from '@/views/TaskCreateForm/types'

export type { TaskRunStatus, TaskStoppedKind } from '@/views/TaskCreateForm/types'

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
  /** 用于主操作：重选时间 / 区分启动场景 */
  effectiveAtRaw: string | null
  expireAtRaw: string | null
  /** 仅在 `status === 'stopped'` 时用于区分「未到生效」与「窗口内暂停」；`pending_run` 时恒为 `neutral` */
  stoppedKind: TaskStoppedKind
}

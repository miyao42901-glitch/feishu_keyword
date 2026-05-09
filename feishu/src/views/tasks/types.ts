/**
 * 任务列表卡片：运行态为演示用（真实调度接入后可由接口字段驱动）。
 */
export type TaskRunStatus = 'running' | 'completed' | 'stopped' | 'failed'

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

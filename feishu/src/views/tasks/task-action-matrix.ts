import type { TaskRunStatus } from '@/views/TaskCreateForm/types'

export type TaskActionKey = 'view' | 'edit' | 'stop' | 'delete' | 'retry'

/**
 * 任务卡片/详情底部操作可见性。
 *
 * | 操作 | 运行中 | 已完成 | 已停止 | 失败 | 待运行 |
 * |------|--------|--------|--------|------|--------|
 * | 查看 | ✓      | ✓      | ✓      | ✓    | ✓      |
 * | 编辑 | ✓      | —      | ✓      | ✓    | ✓      |
 * | 停止 | ✓      | —      | —      | —    | —      |
 * | 删除 | ✓      | ✓      | ✓      | ✓    | ✓      |
 * | 重试 | —      | —      | —      | ✓    | —      |
 */
const ACTION_MATRIX: Record<TaskActionKey, Record<TaskRunStatus, boolean>> = {
  view: {
    running: true,
    completed: true,
    stopped: true,
    failed: true,
    pending_run: true,
  },
  edit: {
    running: true,
    completed: false,
    stopped: true,
    failed: true,
    pending_run: true,
  },
  stop: {
    running: true,
    completed: false,
    stopped: false,
    failed: false,
    pending_run: false,
  },
  delete: {
    running: true,
    completed: true,
    stopped: true,
    failed: true,
    pending_run: true,
  },
  retry: {
    running: false,
    completed: false,
    stopped: false,
    failed: true,
    pending_run: false,
  },
}

export function canTaskAction(status: TaskRunStatus, action: TaskActionKey): boolean {
  return ACTION_MATRIX[action][status] ?? false
}

/** 主操作按钮类型（停止 / 重试）；无则不应展示主操作按钮 */
export type TaskPrimaryActionKind = 'stop' | 'retry' | 'execute'

export function taskPrimaryActionKind(
  status: TaskRunStatus,
  options?: { taskTypeLabel?: string },
): TaskPrimaryActionKind | null {
  if (canTaskAction(status, 'stop')) return 'stop'
  if (canTaskAction(status, 'retry')) return 'retry'
  if (
    options?.taskTypeLabel === '单次任务' &&
    (status === 'stopped' || status === 'completed' || status === 'pending_run')
  ) {
    return 'execute'
  }
  // 定时任务在 pending_run 状态也可以立即执行
  if (status === 'pending_run' && options?.taskTypeLabel === '定时任务') {
    return 'execute'
  }
  return null
}

export function taskPrimaryActionLabel(kind: TaskPrimaryActionKind): string {
  if (kind === 'stop') return '停止'
  if (kind === 'execute') return '执行'
  return '重试'
}

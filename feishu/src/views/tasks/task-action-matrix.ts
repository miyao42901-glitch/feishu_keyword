import type { TaskRunStatus } from '@/views/TaskCreateForm/types'

export type TaskActionKey = 'view' | 'edit' | 'stop' | 'delete' | 'retry'

/**
 * 任务卡片/详情底部操作可见性。
 *
 * | 操作 | 运行中 | 已完成 | 已停止 | 失败 | 待运行 |
 * |------|--------|--------|--------|------|--------|
 * | 查看 | ✓      | ✓      | ✓      | ✓    | ✓      |
 * | 编辑 | ✓      | ✓      | ✓      | ✓    | ✓      |
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
    completed: true,
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
export type TaskPrimaryActionKind = 'stop' | 'retry'

export function taskPrimaryActionKind(status: TaskRunStatus): TaskPrimaryActionKind | null {
  if (canTaskAction(status, 'stop')) return 'stop'
  if (canTaskAction(status, 'retry')) return 'retry'
  return null
}

export function taskPrimaryActionLabel(kind: TaskPrimaryActionKind): string {
  return kind === 'stop' ? '停止' : '重试'
}

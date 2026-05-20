import { describe, expect, it } from 'vitest'

import {
  isAsyncCardRunningStatus,
  shouldHideAsyncListTaskRecord,
  taskStatsFromAsyncSummary,
} from '@/lib/feishu-task-list-api'
import type { TaskCardModel } from '@/views/tasks/types'

describe('taskStatsFromAsyncSummary', () => {
  it('运行中仅用 summary.running，不含 pending', () => {
    const stats = taskStatsFromAsyncSummary(
      {
        total: 4,
        pending: 4,
        running: 0,
        success: 0,
        failed: 0,
        cancelled: 0,
        active: 4,
        total_success_count: 80,
        total_failed_count: 0,
      },
      [],
    )
    expect(stats.running).toBe(0)
    expect(stats.total).toBe(4)
  })
})

describe('shouldHideAsyncListTaskRecord', () => {
  it('任务名以「测试」开头则隐藏', () => {
    expect(shouldHideAsyncListTaskRecord({ task_name: '测试定时任务' })).toBe(true)
    expect(shouldHideAsyncListTaskRecord({ task_name: '测试任务' })).toBe(true)
    expect(shouldHideAsyncListTaskRecord({ task_name: '正式任务' })).toBe(false)
  })
})

describe('isAsyncCardRunningStatus', () => {
  it('pending_run 不算运行中', () => {
    expect(isAsyncCardRunningStatus('pending_run')).toBe(false)
    expect(isAsyncCardRunningStatus('running')).toBe(true)
  })
})

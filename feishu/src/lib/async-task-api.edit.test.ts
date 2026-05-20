import { describe, expect, it } from 'vitest'

import {
  buildAsyncTaskEditRequest,
  canEditAsyncScheduleFields,
  configPatchFromAsyncTaskRecord,
} from '@/lib/async-task-api'

describe('canEditAsyncScheduleFields', () => {
  it('仅 pending / pending_run 可改调度', () => {
    expect(canEditAsyncScheduleFields('pending_run')).toBe(true)
    expect(canEditAsyncScheduleFields('pending')).toBe(true)
    expect(canEditAsyncScheduleFields('running')).toBe(false)
    expect(canEditAsyncScheduleFields('completed')).toBe(false)
  })
})

describe('buildAsyncTaskEditRequest', () => {
  const base = {
    planName: '监控任务A',
    crawlFrequency: '5',
    effectiveAt: '2026-05-20 14:00:00',
    expireAt: '2026-05-20 14:13:00',
    dataRange: 20,
  }

  it('pending：包含调度字段', () => {
    const body = buildAsyncTaskEditRequest(4, base, { allowScheduleFields: true })
    expect(body).toEqual({
      task_id: 4,
      task_name: '监控任务A',
      interval_minutes: 5,
      fetch_count: 20,
      task_start_time: '2026-05-20 14:00:00',
      task_end_time: '2026-05-20 14:13:00',
    })
  })

  it('非 pending：仅 task_name', () => {
    const body = buildAsyncTaskEditRequest(4, base, { allowScheduleFields: false })
    expect(body).toEqual({
      task_id: 4,
      task_name: '监控任务A',
    })
  })

  it('采集频率小于 5 分钟时报错', () => {
    expect(() =>
      buildAsyncTaskEditRequest(1, { ...base, crawlFrequency: '3' }, { allowScheduleFields: true }),
    ).toThrow(/5/)
  })
})

describe('configPatchFromAsyncTaskRecord', () => {
  it('从列表条目构造表单补丁', () => {
    const patch = configPatchFromAsyncTaskRecord({
      task_name: '抖音任务',
      task_start_time: '2026-05-20 14:00:00',
      task_end_time: '2026-05-20 14:13:00',
      interval_minutes: 5,
      fetch_count: 20,
      platform: 'douyin',
      keyword: '美妆',
    })
    expect(patch.planName).toBe('抖音任务')
    expect(patch.taskType).toBe('scheduled')
    expect(patch.crawlFrequency).toBe('5')
    expect(patch.dataRange).toBe(20)
    expect(patch.selectedSources).toEqual(['douyin'])
    expect(patch.keywords).toEqual(['美妆'])
  })
})

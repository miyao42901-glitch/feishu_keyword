import { describe, expect, it } from 'vitest'

import {
  buildAsyncTaskSubmitRequest,
  readAsyncTaskName,
  readAsyncTaskSchedule,
} from '@/lib/async-task-api'

describe('readAsyncTaskSchedule', () => {
  it('从表单配置读取 YDDM 调度参数', () => {
    const schedule = readAsyncTaskSchedule({
      effectiveAt: '2026-05-20 14:00:00',
      expireAt: '2026-05-20 14:13:00',
      crawlFrequency: '5',
      dataRange: 20,
    })
    expect(schedule).toEqual({
      task_start_time: '2026-05-20 14:00:00',
      task_end_time: '2026-05-20 14:13:00',
      interval_minutes: 5,
      fetch_count: 20,
    })
  })

  it('缺少开始时间时抛出', () => {
    expect(() =>
      readAsyncTaskSchedule({ expireAt: '2026-05-20 14:13:00', crawlFrequency: '5' }),
    ).toThrow(/开始/)
  })
})

describe('readAsyncTaskName / buildAsyncTaskSubmitRequest', () => {
  const config = {
    planName: '四平台监控',
    effectiveAt: '2026-05-20 14:00:00',
    expireAt: '2026-05-20 14:13:00',
    crawlFrequency: '5',
    dataRange: 20,
  }

  it('读取任务名称', () => {
    expect(readAsyncTaskName(config)).toBe('四平台监控')
  })

  it('提交体包含 task_name', () => {
    const req = buildAsyncTaskSubmitRequest('douyin', config, '美妆')
    expect(req.task_name).toBe('四平台监控')
    expect(req.interval_minutes).toBe(5)
    expect(req.body.keyword).toBe('美妆')
  })
})

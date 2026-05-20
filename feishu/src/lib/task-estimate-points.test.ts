import { describe, expect, it } from 'vitest'

import { estimateTaskPointsBreakdownFromConfig } from '@/lib/task-estimate-points'

/** 四平台 × 20 条 × 100 积分/条 × 3 轮 × 1 关键词 */
const SCENARIO_CONFIG: Record<string, unknown> = {
  taskType: 'scheduled',
  effectiveAt: '2026-05-20 14:00:00',
  expireAt: '2026-05-20 14:13:00',
  crawlFrequency: '5',
  dataRange: 20,
  selectedSources: ['douyin', 'xiaohongshu', 'gzh', 'shipinhao'],
  keywords: ['美妆'],
}

describe('estimateTaskPointsBreakdownFromConfig', () => {
  it('用户场景：4 平台、20 条、4 轮（含开始时刻首轮）、1 关键词 → 32000 积分上限', () => {
    const est = estimateTaskPointsBreakdownFromConfig(SCENARIO_CONFIG)
    expect(est.scheduledExecutionRounds).toBe(4)
    expect(est.rowPointsPerRound).toBe(4 * 20 * 100)
    expect(est.total).toBe(32_000)
  })

  it('关键词数乘入预估', () => {
    const est = estimateTaskPointsBreakdownFromConfig({
      ...SCENARIO_CONFIG,
      keywords: ['a', 'b'],
    })
    expect(est.total).toBe(64_000)
  })

  it('单次任务不计多轮', () => {
    const est = estimateTaskPointsBreakdownFromConfig({
      ...SCENARIO_CONFIG,
      taskType: 'realtime',
    })
    expect(est.scheduledExecutionRounds).toBe(1)
    expect(est.total).toBe(8_000)
  })
})

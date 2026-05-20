import dayjs from 'dayjs'
import { describe, expect, it } from 'vitest'

import {
  countScheduledExecutionRounds,
  isScheduledFeedPollDue,
  listScheduledExecutionRunAtMs,
  msUntilNextScheduledRunPoll,
  parseTaskDateTimeString,
  scheduledRunPolledMarkThrough,
} from '@/lib/datetime-task-window'

function formatRunTimes(runAtMs: number[]): string[] {
  return runAtMs.map((ms) => dayjs(ms).format('HH:mm'))
}

describe('parseTaskDateTimeString', () => {
  it('解析合法日期时间', () => {
    const d = parseTaskDateTimeString('2026-05-20 14:00:00')
    expect(d?.isValid()).toBe(true)
    expect(d?.format('HH:mm')).toBe('14:00')
  })

  it('空值返回 null', () => {
    expect(parseTaskDateTimeString('')).toBeNull()
    expect(parseTaskDateTimeString(null)).toBeNull()
  })
})

describe('countScheduledExecutionRounds', () => {
  it('14:29~14:41、5 分钟 → 首轮 14:29，共 4 轮', () => {
    const runs = listScheduledExecutionRunAtMs(
      '2026-05-20 14:29:00',
      '2026-05-20 14:41:00',
      5,
    )
    expect(formatRunTimes(runs)).toEqual(['14:29', '14:34', '14:39', '14:41'])
    expect(countScheduledExecutionRounds('2026-05-20 14:29:00', '2026-05-20 14:41:00', 5)).toBe(
      4,
    )
  })

  it('14:00~14:13、5 分钟 → 首轮 14:00，共 4 轮', () => {
    expect(
      countScheduledExecutionRounds('2026-05-20 14:00:00', '2026-05-20 14:13:00', 5),
    ).toBe(4)
    expect(
      formatRunTimes(
        listScheduledExecutionRunAtMs('2026-05-20 14:00:00', '2026-05-20 14:13:00', 5),
      ),
    ).toEqual(['14:00', '14:05', '14:10', '14:13'])
  })

  it('14:00~14:10、5 分钟 → 14:00 / 14:05 / 14:10 共 3 轮', () => {
    expect(
      countScheduledExecutionRounds('2026-05-20 14:00:00', '2026-05-20 14:10:00', 5),
    ).toBe(3)
  })

  it('结束时间不晚于开始 → 0 轮', () => {
    expect(
      countScheduledExecutionRounds('2026-05-20 14:00:00', '2026-05-20 14:00:00', 5),
    ).toBe(0)
  })

  it('非法时间回退为 1 轮', () => {
    expect(countScheduledExecutionRounds('', '2026-05-20 14:13:00', 5)).toBe(1)
  })
})

describe('msUntilNextScheduledRunPoll', () => {
  const eff = '2026-05-20 14:29:00'
  const exp = '2026-05-20 14:41:00'
  const freq = 5

  it('开始前等到 14:29', () => {
    const now = dayjs('2026-05-20 14:28:00').valueOf()
    expect(msUntilNextScheduledRunPoll(eff, exp, freq, undefined, now)).toBe(60_000)
  })

  it('14:29 到点应立即拉取', () => {
    const now = dayjs('2026-05-20 14:29:10').valueOf()
    expect(isScheduledFeedPollDue(eff, exp, freq, undefined, now)).toBe(true)
    expect(msUntilNextScheduledRunPoll(eff, exp, freq, undefined, now)).toBe(0)
  })

  it('14:29 拉取后等到 14:34', () => {
    const now = dayjs('2026-05-20 14:30:00').valueOf()
    const mark = scheduledRunPolledMarkThrough(eff, exp, freq, now)
    expect(msUntilNextScheduledRunPoll(eff, exp, freq, mark, now)).toBe(4 * 60_000)
  })
})

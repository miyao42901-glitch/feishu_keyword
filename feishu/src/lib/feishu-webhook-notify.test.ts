import dayjs from 'dayjs'
import { afterEach, describe, expect, it, vi } from 'vitest'

import {
  computeScheduledRoundKey,
  readCrawlPollIntervalMs,
  resetTaskWebhookRoundDedupe,
} from '@/lib/feishu-webhook-notify'

const SCENARIO_CONFIG: Record<string, unknown> = {
  taskType: 'scheduled',
  effectiveAt: '2026-05-20 14:00:00',
  expireAt: '2026-05-20 14:13:00',
  crawlFrequency: '5',
  feishuNotifyEnabled: true,
  feishuWebhookUrl: 'https://example.com/hook',
}

function msAt(time: string): number {
  return dayjs(`2026-05-20 ${time}:00`).valueOf()
}

describe('computeScheduledRoundKey', () => {
  it('窗口开始前返回 null', () => {
    expect(computeScheduledRoundKey(SCENARIO_CONFIG, msAt('13:59'))).toBeNull()
  })

  it('14:00~14:04 为 r0', () => {
    expect(computeScheduledRoundKey(SCENARIO_CONFIG, msAt('14:00'))).toBe('r0')
    expect(computeScheduledRoundKey(SCENARIO_CONFIG, msAt('14:04'))).toBe('r0')
  })

  it('14:05~14:09 为 r1', () => {
    expect(computeScheduledRoundKey(SCENARIO_CONFIG, msAt('14:05'))).toBe('r1')
    expect(computeScheduledRoundKey(SCENARIO_CONFIG, msAt('14:09'))).toBe('r1')
  })

  it('14:10~14:13 为 r2（含 14:10 与 14:13 两轮 YDDM 采集）', () => {
    expect(computeScheduledRoundKey(SCENARIO_CONFIG, msAt('14:10'))).toBe('r2')
    expect(computeScheduledRoundKey(SCENARIO_CONFIG, msAt('14:13'))).toBe('r2')
  })

  it('窗口结束后返回 null', () => {
    expect(computeScheduledRoundKey(SCENARIO_CONFIG, msAt('14:14'))).toBeNull()
  })
})

describe('readCrawlPollIntervalMs', () => {
  it('定时任务轮询间隔等于采集频率（毫秒）', () => {
    expect(readCrawlPollIntervalMs(SCENARIO_CONFIG)).toBe(5 * 60_000)
  })

  it('单次任务使用较短回退间隔', () => {
    expect(
      readCrawlPollIntervalMs({ taskType: 'realtime', crawlFrequency: '5' }, {
        realtimeFallbackMs: 30_000,
      }),
    ).toBe(30_000)
  })
})

describe('resetTaskWebhookRoundDedupe', () => {
  const storage = new Map<string, string>()

  afterEach(() => {
    storage.clear()
    vi.unstubAllGlobals()
  })

  it('清除 localStorage 中的轮次去重键', () => {
    vi.stubGlobal('localStorage', {
      getItem: (k: string) => storage.get(k) ?? null,
      setItem: (k: string, v: string) => {
        storage.set(k, v)
      },
      removeItem: (k: string) => {
        storage.delete(k)
      },
    })
    storage.set(
      'feishu_keyword_webhook_task_42',
      JSON.stringify({ lastRoundNotifyKey: 'r1', lastFailedNotifyKey: 'x' }),
    )
    resetTaskWebhookRoundDedupe(42)
    const next = JSON.parse(storage.get('feishu_keyword_webhook_task_42') ?? '{}') as Record<
      string,
      unknown
    >
    expect(next.lastRoundNotifyKey).toBeUndefined()
    expect(next.lastFailedNotifyKey).toBeUndefined()
  })
})

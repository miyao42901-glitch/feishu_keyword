import { describe, expect, it } from 'vitest'

import { buildFeedConfigFromListCard, narrowFeedConfigToListCard } from '@/lib/feishu-task-feed-config'
import type { TaskCardModel } from '@/views/tasks/types'

const card: TaskCardModel = {
  id: 126,
  name: '测试定时任务',
  platformKeys: ['douyin'],
  platformsLabel: '抖音',
  taskTypeLabel: '定时任务',
  dateLabel: '2026-05-20',
  status: 'running',
  notificationCount: 0,
  effectiveAtRaw: '2026-05-20 16:13:00',
  expireAtRaw: '2026-05-20 16:26:00',
  stoppedKind: 'neutral',
}

describe('buildFeedConfigFromListCard', () => {
  it('生成单条 asyncTaskRefs 供拉 results', () => {
    const cfg = buildFeedConfigFromListCard(card)
    const refs = cfg.asyncTaskRefs as { taskId: string; platform: string }[]
    expect(refs).toHaveLength(1)
    expect(refs[0]?.taskId).toBe('126')
    expect(refs[0]?.platform).toBe('douyin')
  })
})

describe('narrowFeedConfigToListCard', () => {
  it('多平台配置只保留当前卡片子任务', () => {
    const cfg = narrowFeedConfigToListCard(
      {
        asyncTaskRefs: [
          { taskId: '126', platform: 'douyin', keyword: 'a' },
          { taskId: '127', platform: 'shipinhao', keyword: 'a' },
        ],
      },
      card,
    )
    const refs = cfg.asyncTaskRefs as { taskId: string }[]
    expect(refs).toHaveLength(1)
    expect(refs[0]?.taskId).toBe('126')
  })
})

/**
 * 列表页拉数：YDDM 子任务与表单 config 的拼接（无 `server/` 请求）。
 */

import { configPatchFromAsyncTaskRecord, isRealtimeTaskConfig, readAsyncTaskRefs } from '@/lib/async-task-api'
import { loadLocalTaskConfig } from '@/lib/feishu-task-config-local'
import { readSearchKeywords } from '@/lib/sync-search-shared'
import type { TaskCardModel } from '@/views/tasks/types'

export { resolveFeedConfigForListCard } from '@/lib/feishu-async-task-config'

const YDDM_PLATFORM_FROM_CARD: Record<string, string> = {
  douyin: 'douyin',
  xiaohongshu: 'xhs',
  shipinhao: 'wxvideo',
  gzh: 'mp',
}

/** 无本地/远程配置时：用列表卡片字段拼最小 config（含当前子任务 `asyncTaskRefs`） */
export function buildFeedConfigFromListCard(card: TaskCardModel): Record<string, unknown> {
  const platformKey = card.platformKeys[0]
  if (!platformKey) throw new Error('列表卡片缺少平台信息')

  const isRealtime = card.taskTypeLabel === '单次任务'
  const patch = configPatchFromAsyncTaskRecord(
    isRealtime
      ? {
          task_name: card.name,
          platform: YDDM_PLATFORM_FROM_CARD[platformKey] ?? platformKey,
          fetch_count: 20,
          task_type: 'realtime',
        }
      : {
          task_name: card.name,
          task_start_time: card.effectiveAtRaw,
          task_end_time: card.expireAtRaw,
          platform: YDDM_PLATFORM_FROM_CARD[platformKey] ?? platformKey,
          interval_minutes: 5,
          fetch_count: 20,
          task_type: 'scheduled',
        },
  )
  patch.taskType = isRealtime ? 'realtime' : 'scheduled'
  patch.selectedSources = [platformKey]

  if (!isRealtime) {
    patch.asyncTaskRefs = [
      {
        taskId: String(card.id),
        platform: platformKey,
        keyword: Array.isArray(patch.keywords) ? String((patch.keywords as string[])[0] ?? '') : '',
      },
    ]
    patch.asyncTaskIds = [String(card.id)]
  } else {
    delete patch.asyncTaskRefs
    delete patch.asyncTaskIds
  }

  const local = loadLocalTaskConfig(card.id)
  if (local) {
    const merged = { ...patch, ...local, taskType: patch.taskType, task_type: patch.taskType }
    const kw = readSearchKeywords(merged)
    if (kw.length && kw[0]) (merged as Record<string, unknown>).keywords = kw
    return narrowFeedConfigToListCard(merged, card)
  }
  return patch
}

/** 多平台共一条配置时，列表按 YDDM 子任务拉数只保留当前卡片对应 ref */
export function narrowFeedConfigToListCard(
  config: Record<string, unknown>,
  card: TaskCardModel,
): Record<string, unknown> {
  if (card.taskTypeLabel === '单次任务' || isRealtimeTaskConfig(config)) {
    const next = { ...config }
    delete next.asyncTaskRefs
    delete next.asyncTaskIds
    return next
  }
  const want = String(card.id)
  const refs = readAsyncTaskRefs(config).filter((r) => r.taskId === want)
  if (!refs.length) return buildFeedConfigFromListCard(card)
  const narrowed: Record<string, unknown> = { ...config, asyncTaskRefs: refs, asyncTaskIds: [want] }
  const refKeywords = refs.map((r) => r.keyword.trim()).filter(Boolean)
  const existing = readSearchKeywords(narrowed)
  if (refKeywords.length && (!existing.length || !existing[0])) {
    narrowed.keywords = [...new Set(refKeywords)]
  }
  return narrowed
}

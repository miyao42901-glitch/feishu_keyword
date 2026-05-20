/**
 * 列表页拉数：YDDM 列表 `task_id` 与 `feishu_task_configs.id` 常不一致，需解析/回退配置。
 */

import { getFeishuTaskConfig, listFeishuTaskConfigs, type FeishuTaskConfigDetail } from '@/lib/api'
import {
  configPatchFromAsyncTaskRecord,
  readAsyncTaskIds,
  readAsyncTaskRefs,
} from '@/lib/async-task-api'
import type { TaskCardModel } from '@/views/tasks/types'

const YDDM_PLATFORM_FROM_CARD: Record<string, string> = {
  douyin: 'douyin',
  xiaohongshu: 'xhs',
  shipinhao: 'wxvideo',
  gzh: 'mp',
}

/** 无本地配置时：用列表卡片字段拼最小 config（含当前子任务 `asyncTaskRefs`） */
export function buildFeedConfigFromListCard(card: TaskCardModel): Record<string, unknown> {
  const platformKey = card.platformKeys[0]
  if (!platformKey) throw new Error('列表卡片缺少平台信息')

  const patch = configPatchFromAsyncTaskRecord({
    task_name: card.name,
    task_start_time: card.effectiveAtRaw,
    task_end_time: card.expireAtRaw,
    platform: YDDM_PLATFORM_FROM_CARD[platformKey] ?? platformKey,
    interval_minutes: 5,
    fetch_count: 20,
  })

  patch.asyncTaskRefs = [
    {
      taskId: String(card.id),
      platform: platformKey,
      keyword: Array.isArray(patch.keywords) ? String((patch.keywords as string[])[0] ?? '') : '',
    },
  ]
  patch.asyncTaskIds = [String(card.id)]
  return patch
}

/** 在本地任务配置中查找包含指定 YDDM `task_id` 的配置 */
export async function findFeishuConfigContainingAsyncTaskId(
  yddmTaskId: number,
): Promise<FeishuTaskConfigDetail | null> {
  const want = String(yddmTaskId)
  let skip = 0
  const pageSize = 100
  for (let page = 0; page < 10; page++) {
    const list = await listFeishuTaskConfigs(skip, pageSize)
    if (!list.length) break
    for (const item of list) {
      try {
        const detail = await getFeishuTaskConfig(item.id)
        const cfg = detail.config
        if (!cfg || typeof cfg !== 'object' || Array.isArray(cfg)) continue
        const rec = cfg as Record<string, unknown>
        const refs = readAsyncTaskRefs(rec)
        if (refs.some((r) => r.taskId === want)) return detail
        if (readAsyncTaskIds(rec).includes(want)) return detail
      } catch {
        /* 单条详情失败则跳过 */
      }
    }
    if (list.length < pageSize) break
    skip += pageSize
  }
  return null
}

/**
 * 解析列表卡片对应的表单 config（用于 `buildTestDataFeedFromConfig`）。
 * 顺序：同 id 详情 → 扫描本地配置中的 asyncTaskRefs → 列表字段回退。
 */
export async function resolveFeedConfigForListCard(card: TaskCardModel): Promise<Record<string, unknown>> {
  try {
    const detail = await getFeishuTaskConfig(card.id)
    if (detail.config != null && typeof detail.config === 'object' && !Array.isArray(detail.config)) {
      return narrowFeedConfigToListCard(detail.config as Record<string, unknown>, card)
    }
  } catch {
    /* 列表 id 多为 YDDM task_id */
  }

  const found = await findFeishuConfigContainingAsyncTaskId(card.id)
  if (found?.config != null && typeof found.config === 'object' && !Array.isArray(found.config)) {
    return narrowFeedConfigToListCard(found.config as Record<string, unknown>, card)
  }

  return buildFeedConfigFromListCard(card)
}

/** 多平台共一条 feishu 配置时，列表按 YDDM 子任务拉数只保留当前卡片对应 ref */
export function narrowFeedConfigToListCard(
  config: Record<string, unknown>,
  card: TaskCardModel,
): Record<string, unknown> {
  const want = String(card.id)
  const refs = readAsyncTaskRefs(config).filter((r) => r.taskId === want)
  if (!refs.length) return buildFeedConfigFromListCard(card)
  return { ...config, asyncTaskRefs: refs, asyncTaskIds: [want] }
}

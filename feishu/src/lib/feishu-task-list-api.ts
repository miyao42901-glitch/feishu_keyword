/**

 * 任务列表页：`GET /api/v1/async/tasks`（`data.result.items` + `summary`）。

 */



import type { PlatformKey } from '@/components/PlatformIcon.vue'

import {

  extractAsyncTaskId,

  listAsyncTasks,

  parseAsyncTaskListEnvelope,

  parseAsyncTaskStatusResponse,

  type AsyncTaskLifecycle,

  type AsyncTaskListSummary,

} from '@/lib/async-task-api'

import type { SyncFetchContext } from '@/lib/sync-api-common'

import { platformDisplayNames } from '@/views/TaskCreateForm/constants'

import type { TaskRunStatus } from '@/views/TaskCreateForm/types'

import type { TaskCardModel } from '@/views/tasks/types'

import dayjs from 'dayjs'



const ASYNC_PLATFORM_TO_KEY: Record<string, PlatformKey> = {

  douyin: 'douyin',

  xhs: 'xiaohongshu',

  xiaohongshu: 'xiaohongshu',

  mp: 'gzh',

  gzh: 'gzh',

  wxvideo: 'shipinhao',

  shipinhao: 'shipinhao',

}



function mapAsyncPlatform(raw: unknown): PlatformKey | null {

  const s = String(raw ?? '').trim().toLowerCase()

  return ASYNC_PLATFORM_TO_KEY[s] ?? null

}



export function lifecycleToTaskRunStatus(lifecycle: AsyncTaskLifecycle): TaskRunStatus {

  switch (lifecycle) {

    case 'completed':

      return 'completed'

    case 'failed':

      return 'failed'

    case 'pending':

      return 'pending_run'

    case 'running':

      return 'running'

    default:

      return 'stopped'

  }

}



function asyncRecordToCardStatus(rec: Record<string, unknown>, taskId: string): TaskRunStatus {

  const { lifecycle } = parseAsyncTaskStatusResponse(rec, taskId)

  return lifecycleToTaskRunStatus(lifecycle)

}



function readTimeField(rec: Record<string, unknown>, ...keys: string[]): string | null {

  for (const key of keys) {

    const v = rec[key]

    if (v != null && String(v).trim()) return String(v).trim()

  }

  return null

}



function formatCardDate(raw: string | null): string {

  if (!raw) return '—'

  const d = dayjs(raw)

  return d.isValid() ? d.format('YYYY-MM-DD') : raw.slice(0, 10) || '—'

}



function buildCardName(rec: Record<string, unknown>, platformKey: PlatformKey | null, taskId: string): string {

  const taskName = String(rec.task_name ?? rec.taskName ?? '').trim()

  if (taskName) return taskName

  const action = String(rec.action ?? '').trim()

  const label = platformKey ? platformDisplayNames[platformKey] : String(rec.platform ?? '').trim()

  if (label && action) return `${label} · ${action}`

  if (label) return `${label} #${taskId}`

  return action || `采集任务 #${taskId}`

}



/** 单条 `data.result.items[]` → 列表卡片（`id` 为 YDDM `task_id`） */

export function asyncListItemToTaskCard(rec: Record<string, unknown>): TaskCardModel | null {

  const taskId = extractAsyncTaskId(rec)

  if (!taskId) return null

  const id = Number(taskId)

  if (!Number.isFinite(id) || id <= 0) return null



  const platformKey = mapAsyncPlatform(rec.platform)

  const platformKeys = platformKey ? [platformKey] : []

  const start = readTimeField(rec, 'task_start_time', 'taskStartTime')

  const end = readTimeField(rec, 'task_end_time', 'taskEndTime')

  const hasSchedule = Boolean(start || end || rec.interval_minutes != null)



  return {

    id,

    name: buildCardName(rec, platformKey, taskId),

    platformKeys,

    platformsLabel: platformKey ? platformDisplayNames[platformKey] : String(rec.platform ?? '—'),

    taskTypeLabel: hasSchedule ? '定时任务' : '单次任务',

    dateLabel: hasSchedule ? formatCardDate(start) : '—',

    status: asyncRecordToCardStatus(rec, taskId),

    notificationCount: 0,

    effectiveAtRaw: start,

    expireAtRaw: end,

    nextRunAtRaw: readTimeField(rec, 'next_run_at', 'nextRunAt'),

    stoppedKind: 'neutral',

  }

}



export type TaskListStatCounts = {

  total: number

  running: number

  completed: number

}



/**

 * 顶部统计：优先用接口 `summary` 各字段（有值即用，含 0）；无 `summary` 时按当前卡片计数。

 */

export function taskStatsFromAsyncSummary(
  summary: AsyncTaskListSummary | null,
  cards: TaskCardModel[],
): TaskListStatCounts {
  /** 顶部统计固定用接口 `summary`，勿用当前页/筛选后的 `cards` 计数 */
  if (summary) {
    return {
      total: summary.total,
      running: summary.running,
      completed: summary.success,
    }
  }

  if (cards.length > 0) {
    return {
      total: cards.length,
      running: cards.filter((t) => isAsyncCardRunningStatus(t.status)).length,
      completed: cards.filter((t) => t.status === 'completed').length,
    }
  }

  return { total: 0, running: 0, completed: 0 }
}

/** 列表筛选：与顶部「运行中」统计一致（YDDM `running`，不含 `pending` / `pending_run`） */
export function matchesAsyncListFilter(
  status: TaskRunStatus,
  filter: 'all' | 'running' | 'completed',
): boolean {
  switch (filter) {
    case 'running':
      return isAsyncCardRunningStatus(status)
    case 'completed':
      return status === 'completed'
    default:
      return true
  }
}



/** 列表筛选：运行中（仅 YDDM `running`，不含 `pending` / `pending_run`） */

export function isAsyncCardRunningStatus(status: TaskRunStatus): boolean {
  return status === 'running'
}

/**
 * 是否从任务列表页隐藏该 YDDM 子任务。
 * 曾用于隐藏「测试*」联调数据，会导致顶部统计与下方列表不一致，现恒为不隐藏。
 */
export function shouldHideAsyncListTaskRecord(_rec: Record<string, unknown>): boolean {
  return false
}



export type ListTaskCardsFromAsyncResult = {

  cards: TaskCardModel[]

  summary: AsyncTaskListSummary | null

  page: number

  limit: number

}



/** 任务列表：`GET /api/v1/async/tasks?page=&limit=`（单页，翻页由列表页传入 page/limit） */

export async function listTaskCardsFromAsync(
  ctx: SyncFetchContext,
  options?: { page?: number; limit?: number },
): Promise<ListTaskCardsFromAsyncResult> {
  const pageNum = Math.max(1, Math.floor(options?.page ?? 1))
  const limit = Math.max(1, Math.floor(options?.limit ?? 100))
  const parsed = await listAsyncTasks(ctx, { page: pageNum, limit })
  const batch = parseAsyncTaskListEnvelope(parsed)

  const cards: TaskCardModel[] = []
  for (const rec of batch.items) {
    if (shouldHideAsyncListTaskRecord(rec)) continue
    const card = asyncListItemToTaskCard(rec)
    if (card) cards.push(card)
  }

  cards.sort((a, b) => b.id - a.id)

  return {
    cards,
    summary: batch.summary,
    page: batch.page,
    limit: batch.limit,
  }
}



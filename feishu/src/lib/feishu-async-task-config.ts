/**
 * 任务配置：8765 异步任务 + 浏览器本地快照（不再请求 `server/` 8000）。
 */

import type { FeishuTaskConfigDetail, FeishuTaskConfigWriteResult } from '@/lib/task-config-types'
import {
  configPatchFromAsyncTaskRecord,
  getAsyncTaskStatus,
  readAsyncTaskRefs,
} from '@/lib/async-task-api'
import { lifecycleToTaskRunStatus } from '@/lib/feishu-task-list-api'
import { buildCollectionFetchContext } from '@/lib/collection-context'
import {
  buildFeedConfigFromListCard,
  narrowFeedConfigToListCard,
} from '@/lib/feishu-task-feed-config'
import {
  isLocalDraftTaskId,
  loadLocalTaskConfig,
  mergeLocalTaskConfig,
  removeLocalTaskConfig,
  saveLocalTaskConfig,
} from '@/lib/feishu-task-config-local'
import type { SyncFetchContext } from '@/lib/sync-api-common'
import type { TaskCardModel } from '@/views/tasks/types'
import type { TaskRunStatus } from '@/views/TaskCreateForm/types'

const YDDM_PLATFORM_FROM_CARD: Record<string, string> = {
  douyin: 'douyin',
  xiaohongshu: 'xhs',
  shipinhao: 'wxvideo',
  gzh: 'mp',
}

function displayStatusFromConfig(cfg: Record<string, unknown>): TaskRunStatus {
  if (cfg.taskAbnormal === true || cfg.runStatus === 'failed') return 'failed'
  if (cfg.taskPaused === true) return 'stopped'
  const rs = String(cfg.runStatus ?? '').trim()
  if (rs === 'running' || rs === 'completed' || rs === 'pending_run' || rs === 'stopped') {
    return rs as TaskRunStatus
  }
  const tt = cfg.taskType ?? cfg.task_type
  if (tt === 'realtime') return 'pending_run'
  return 'stopped'
}

function writeResultFromConfig(id: number, cfg: Record<string, unknown>): FeishuTaskConfigWriteResult {
  const display_status = displayStatusFromConfig(cfg)
  return {
    id,
    display_status,
    stopped_kind: display_status === 'stopped' && cfg.taskPaused === true ? 'paused_in_window' : 'neutral',
  }
}

/** 从本地快照拼列表卡片（新建保存后尚未出现在 YDDM 列表时） */
export function taskCardFromLocalConfig(
  taskId: number,
  config: Record<string, unknown>,
): TaskCardModel {
  const name = String(config.planName ?? config.plan_name ?? '未命名任务').trim() || '未命名任务'
  const sources = Array.isArray(config.selectedSources)
    ? (config.selectedSources as unknown[]).filter((x) => typeof x === 'string').map((s) => s.trim())
    : []
  const tt = config.taskType ?? config.task_type
  const isRealtime = tt === 'realtime'
  const eff = config.effectiveAt ?? config.effective_at
  const exp = config.expireAt ?? config.expire_at
  const status = displayStatusFromConfig(config)
  return {
    id: taskId,
    name,
    platformKeys: sources,
    platformsLabel: sources.length ? sources.join('、') : '未选择平台',
    taskTypeLabel: isRealtime ? '单次任务' : '定时任务',
    dateLabel: isRealtime
      ? '—'
      : eff != null && String(eff).trim()
        ? String(eff).slice(0, 10)
        : '—',
    status,
    notificationCount: 0,
    nextRunAtRaw: null,
    effectiveAtRaw: eff != null && String(eff).trim() ? String(eff).trim() : null,
    expireAtRaw: exp != null && String(exp).trim() ? String(exp).trim() : null,
    stoppedKind: status === 'stopped' && config.taskPaused === true ? 'paused_in_window' : 'neutral',
  }
}

async function fetchYddmConfigPatch(
  card: TaskCardModel,
  ctx?: SyncFetchContext,
): Promise<Record<string, unknown>> {
  if (isLocalDraftTaskId(card.id)) {
    throw new Error('local draft task')
  }
  const syncCtx = ctx ?? (await buildCollectionFetchContext())
  const status = await getAsyncTaskStatus(syncCtx, String(card.id))
  return configPatchFromAsyncTaskRecord({
    ...status.data,
    task_name: card.name,
    task_start_time: card.effectiveAtRaw,
    task_end_time: card.expireAtRaw,
    platform: YDDM_PLATFORM_FROM_CARD[card.platformKeys[0] ?? ''] ?? card.platformKeys[0],
  })
}

export type ResolveFeedConfigOptions = {
  /**
   * 列表轮询：不请求 `GET /async/tasks/{id}`，避免多平台任务对每条卡片打详情接口。
   * 优先 localStorage，否则用列表卡片字段拼最小 config。
   */
  pollMode?: boolean
}

/** 列表卡片「单次 / 定时」与本地 `taskType` 对齐（避免 YDDM 补丁把单次误判为定时） */
export function applyTaskTypeFromListCard(
  config: Record<string, unknown>,
  card: TaskCardModel,
): Record<string, unknown> {
  if (card.taskTypeLabel === '单次任务') {
    return { ...config, taskType: 'realtime', task_type: 'realtime' }
  }
  if (card.taskTypeLabel === '定时任务') {
    return { ...config, taskType: 'scheduled', task_type: 'scheduled' }
  }
  return config
}

/**
 * 解析列表卡片 config（采集 / 写表 / 轮询）。
 * 顺序：本地快照 + YDDM 详情补丁 → 仅 YDDM → 列表字段回退。
 */
export async function resolveFeedConfigForListCard(
  card: TaskCardModel,
  ctx?: SyncFetchContext,
  options?: ResolveFeedConfigOptions,
): Promise<Record<string, unknown>> {
  const local = loadLocalTaskConfig(card.id)
  if (options?.pollMode) {
    const base = local
      ? narrowFeedConfigToListCard(local, card)
      : buildFeedConfigFromListCard(card)
    return applyTaskTypeFromListCard(base, card)
  }
  try {
    const yddmPatch = await fetchYddmConfigPatch(card, ctx)
    if (local) {
      const merged = { ...yddmPatch, ...local }
      const localType = local.taskType ?? local.task_type
      if (localType === 'realtime') {
        merged.taskType = 'realtime'
        merged.task_type = 'realtime'
      }
      return applyTaskTypeFromListCard(narrowFeedConfigToListCard(merged, card), card)
    }
    return applyTaskTypeFromListCard(narrowFeedConfigToListCard(yddmPatch, card), card)
  } catch {
    const base = local
      ? narrowFeedConfigToListCard(local, card)
      : buildFeedConfigFromListCard(card)
    return applyTaskTypeFromListCard(base, card)
  }
}

/** 加载详情弹框 / 编辑回显 */
export async function loadTaskConfigDetail(
  card: TaskCardModel,
  ctx?: SyncFetchContext,
): Promise<FeishuTaskConfigDetail> {
  const local = loadLocalTaskConfig(card.id)
  let config: Record<string, unknown>
  let display_status: TaskRunStatus = card.status
  try {
    if (isLocalDraftTaskId(card.id)) {
      throw new Error('local draft task')
    }
    const syncCtx = ctx ?? (await buildCollectionFetchContext())
    const status = await getAsyncTaskStatus(syncCtx, String(card.id))
    display_status = lifecycleToTaskRunStatus(status.lifecycle)
    const yddmPatch = configPatchFromAsyncTaskRecord({
      ...status.data,
      task_name: card.name,
      task_start_time: card.effectiveAtRaw,
      task_end_time: card.expireAtRaw,
    })
    config = local ? { ...local, ...yddmPatch } : yddmPatch
  } catch {
    config = local ?? buildFeedConfigFromListCard(card)
  }
  return {
    id: card.id,
    plan_name: card.name,
    config: narrowFeedConfigToListCard(config, card),
    display_status,
  }
}

/** 合并补丁到本地快照（替代 `updateFeishuTaskConfig`） */
export function saveTaskConfigPatch(
  taskId: number,
  patch: Record<string, unknown>,
): FeishuTaskConfigWriteResult {
  const cfg = mergeLocalTaskConfig(taskId, patch)
  return writeResultFromConfig(taskId, cfg)
}

/** 全量保存表单（新建 / 编辑确认） */
export function saveTaskConfigSnapshot(
  taskId: number,
  config: Record<string, unknown>,
): FeishuTaskConfigWriteResult {
  saveLocalTaskConfig(taskId, config)
  return writeResultFromConfig(taskId, config)
}

/** 执行采集前读取 config */
export async function loadTaskConfigForExecution(
  card: TaskCardModel,
): Promise<Record<string, unknown>> {
  const cfg = await resolveFeedConfigForListCard(card)
  return applyTaskTypeFromListCard(cfg, card)
}

/** 采集提交后把 asyncTaskRefs 写入本地，并迁移草稿 id */
export function persistCollectionRefsToLocal(
  taskId: number,
  config: Record<string, unknown>,
  options?: { draftId?: number },
): void {
  saveLocalTaskConfig(taskId, config)
  const refs = readAsyncTaskRefs(config)
  for (const ref of refs) {
    const id = Number(ref.taskId)
    if (!Number.isFinite(id) || id <= 0 || id === taskId) continue
    saveLocalTaskConfig(id, narrowFeedConfigToListCard(config, taskCardFromRef(id, ref, config)))
  }
  const draftId = options?.draftId
  if (draftId != null && draftId !== taskId) removeLocalTaskConfig(draftId)
}

const REF_PLATFORM_TO_KEY: Record<string, TaskCardModel['platformKeys'][number]> = {
  douyin: 'douyin',
  xhs: 'xiaohongshu',
  xiaohongshu: 'xiaohongshu',
  mp: 'gzh',
  gzh: 'gzh',
  wxvideo: 'shipinhao',
  shipinhao: 'shipinhao',
}

function taskCardFromRef(
  taskId: number,
  ref: { platform: string; keyword: string },
  config: Record<string, unknown>,
): TaskCardModel {
  const planName = String(config.planName ?? config.plan_name ?? '未命名任务').trim()
  const platformKey =
    REF_PLATFORM_TO_KEY[ref.platform.trim().toLowerCase()] ?? 'douyin'
  return {
    id: taskId,
    name: planName || '未命名任务',
    platformKeys: [platformKey],
    platformsLabel: platformKey,
    taskTypeLabel: String(config.taskType) === 'realtime' ? '单次任务' : '定时任务',
    dateLabel: '—',
    status: displayStatusFromConfig(config),
    notificationCount: 0,
    nextRunAtRaw: null,
    effectiveAtRaw: null,
    expireAtRaw: null,
    stoppedKind: 'neutral',
  }
}

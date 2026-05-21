/**
 * 飞书自定义机器人 Webhook 通知（文本消息）。
 * 触发：定时任务按采集频率每轮推送、采集失败、账户积分低于阈值（单次任务不推送任务级通知）。
 */

import type { AsyncTaskRef } from '@/lib/async-task-api'
import { isRealtimeTaskConfig } from '@/lib/async-task-api'
import { parseTaskDateTimeString } from '@/lib/datetime-task-window'
import { platformDisplayNames } from '@/views/TaskCreateForm/constants'

import { rememberGlobalNotifyWebhook, readGlobalNotifyWebhook } from '@/stores/globalSettings'

export const LOW_BALANCE_THRESHOLD_POINTS = 1000

export type WebhookTaskEventType = 'scheduled_round' | 'execution_complete' | 'collection_failed'

const TASK_STATE_PREFIX = 'feishu_keyword_webhook_task_'
const LOW_BALANCE_NOTIFIED_KEY = 'feishu_keyword_low_balance_notified'

type TaskWebhookState = {
  /** 已推送的采集轮次（首轮=开始时间，之后按采集频率） */
  lastRoundNotifyKey?: string
  /** 已推送的失败子任务指纹 */
  lastFailedNotifyKey?: string
  lastCompleteRunKey?: string
}

function readTaskWebhookState(taskId: number): TaskWebhookState {
  try {
    const raw = localStorage.getItem(`${TASK_STATE_PREFIX}${taskId}`)
    if (!raw) return {}
    const parsed = JSON.parse(raw) as TaskWebhookState
    return parsed && typeof parsed === 'object' ? parsed : {}
  } catch {
    return {}
  }
}

function writeTaskWebhookState(taskId: number, state: TaskWebhookState): void {
  try {
    localStorage.setItem(`${TASK_STATE_PREFIX}${taskId}`, JSON.stringify(state))
  } catch {
    /* 忽略 */
  }
}

function patchTaskWebhookState(taskId: number, patch: Partial<TaskWebhookState>): TaskWebhookState {
  const next = { ...readTaskWebhookState(taskId), ...patch }
  writeTaskWebhookState(taskId, next)
  return next
}

/** 新一次提交采集时清除轮次/失败去重 */
export function resetTaskWebhookRoundDedupe(taskId: number): void {
  const state = readTaskWebhookState(taskId)
  if (!state.lastRoundNotifyKey && !state.lastFailedNotifyKey) return
  const { lastRoundNotifyKey: _r, lastFailedNotifyKey: _f, ...rest } = state
  writeTaskWebhookState(taskId, rest)
}

/** 新一次提交采集时清除「已完成」去重，以便本轮结束可再通知 */
export function resetTaskWebhookCompleteDedupe(taskId: number): void {
  const state = readTaskWebhookState(taskId)
  if (!state.lastCompleteRunKey) return
  const { lastCompleteRunKey: _, ...rest } = state
  writeTaskWebhookState(taskId, rest)
}

export function isFeishuNotifyEnabled(config: Record<string, unknown>): boolean {
  const v = config.feishuNotifyEnabled ?? config.feishu_notify_enabled
  return v === true || v === 1 || String(v ?? '').toLowerCase() === 'true'
}

export function readFeishuWebhookUrl(config: Record<string, unknown>): string | null {
  if (!isFeishuNotifyEnabled(config)) return null
  const raw = config.feishuWebhookUrl ?? config.feishu_webhook_url
  const url = typeof raw === 'string' ? raw.trim() : ''
  return url || null
}

/** 保存任务时同步全局 Webhook（供积分不足等账户级通知使用） */
export function syncGlobalNotifyWebhookFromConfig(config: Record<string, unknown>): void {
  const url = readFeishuWebhookUrl(config)
  if (url) rememberGlobalNotifyWebhook(url)
}

/** 表单「采集频率」（分钟）；勿用 YDDM 回写的 `interval_minutes` 作为前端轮询间隔 */
export function readCrawlFrequencyMinutes(config: Record<string, unknown>): number {
  const freqRaw = config.crawlFrequency ?? config.crawl_frequency
  const n = typeof freqRaw === 'number' ? freqRaw : Number(String(freqRaw ?? '').trim())
  return Number.isFinite(n) && n > 0 ? Math.floor(n) : 10
}

/** 采集频率（分钟）：优先表单字段，否则兼容仅含 `interval_minutes` 的旧配置 */
export function readCrawlIntervalMinutes(config: Record<string, unknown>): number {
  const fromForm = config.crawlFrequency ?? config.crawl_frequency
  if (fromForm != null && String(fromForm).trim() !== '') {
    return readCrawlFrequencyMinutes(config)
  }
  const legacy = config.interval_minutes
  const n = typeof legacy === 'number' ? legacy : Number(String(legacy ?? '').trim())
  return Number.isFinite(n) && n > 0 ? Math.floor(n) : 10
}

/** 运行中任务拉取 async 结果/写表的轮询间隔（定时任务=表单采集频率；单次任务用较短回退） */
export function readCrawlPollIntervalMs(
  config: Record<string, unknown>,
  options?: { realtimeFallbackMs?: number },
): number {
  if (isRealtimeTaskConfig(config)) {
    return options?.realtimeFallbackMs ?? 30_000
  }
  return readCrawlFrequencyMinutes(config) * 60_000
}

/**
 * 当前时刻所属的采集轮次键（首轮对齐开始时间，与 `countScheduledExecutionRounds` 一致）。
 * 监控窗口外返回 null。
 */
export function computeScheduledRoundKey(
  config: Record<string, unknown>,
  nowMs = Date.now(),
): string | null {
  const start = parseTaskDateTimeString(config.effectiveAt ?? config.effective_at)
  const end = parseTaskDateTimeString(config.expireAt ?? config.expire_at)
  const intervalMs = readCrawlIntervalMinutes(config) * 60_000

  if (!start) {
    return `t${Math.floor(nowMs / intervalMs)}`
  }

  const startMs = start.valueOf()
  if (nowMs < startMs) return null

  if (end && nowMs > end.valueOf()) return null

  const roundIndex = Math.floor((nowMs - startMs) / intervalMs)
  return `r${roundIndex}`
}

export function buildAsyncRunKey(config: Record<string, unknown>): string {
  const ids = config.asyncTaskIds ?? config.async_task_ids
  if (Array.isArray(ids) && ids.length) {
    return ids
      .map((x) => String(x).trim())
      .filter(Boolean)
      .sort()
      .join(',')
  }
  return 'sync'
}

function buildFailedNotifyKey(roundKey: string | null, failedRefs: AsyncTaskRef[]): string {
  const ids = failedRefs
    .map((r) => r.taskId.trim())
    .filter(Boolean)
    .sort()
    .join(',')
  return `${roundKey ?? 'na'}:${ids}`
}

export function buildTaskWebhookMessage(input: {
  taskName: string
  event: WebhookTaskEventType
  detailLines?: string[]
}): string {
  const titleByEvent: Record<WebhookTaskEventType, string> = {
    scheduled_round: '【关键词监控】定时任务已执行一轮',
    execution_complete: '【关键词监控】任务执行完成',
    collection_failed: '【关键词监控】采集失败',
  }
  const lines = [
    titleByEvent[input.event],
    `任务名称：${input.taskName.trim() || '未命名任务'}`,
    `时间：${new Date().toLocaleString('zh-CN', { hour12: false })}`,
  ]
  if (input.detailLines?.length) lines.push(...input.detailLines)
  return lines.join('\n')
}

export async function sendFeishuWebhookText(webhookUrl: string, text: string): Promise<void> {
  const url = webhookUrl.trim()
  if (!url) return
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      msg_type: 'text',
      content: { text },
    }),
  })
  if (!res.ok) {
    const body = await res.text().catch(() => '')
    throw new Error(body.trim() || `Webhook 请求失败（HTTP ${res.status}）`)
  }
  let payload: unknown
  try {
    payload = await res.json()
  } catch {
    return
  }
  if (payload && typeof payload === 'object') {
    const code = (payload as Record<string, unknown>).code
    if (code != null && Number(code) !== 0) {
      const msg = String((payload as Record<string, unknown>).msg ?? 'Webhook 返回错误')
      throw new Error(msg)
    }
  }
}

async function notifyTaskWebhookIfEnabled(input: {
  taskId: number
  taskName: string
  config: Record<string, unknown>
  event: WebhookTaskEventType
  detailLines?: string[]
}): Promise<boolean> {
  const url = readFeishuWebhookUrl(input.config)
  if (!url) return false
  const text = buildTaskWebhookMessage({
    taskName: input.taskName,
    event: input.event,
    detailLines: input.detailLines,
  })
  try {
    await sendFeishuWebhookText(url, text)
    return true
  } catch (e) {
    if (import.meta.env.DEV) {
      console.warn('[feishu-webhook]', input.event, e)
    }
    return false
  }
}

/** 定时任务：按采集频率每轮推送一次（与监控开始时间 + 频率对齐，非列表轮询间隔） */
export async function maybeNotifyScheduledRoundByFrequency(input: {
  taskId: number
  taskName: string
  config: Record<string, unknown>
  writtenRowCount: number
  totalRowCount: number
}): Promise<void> {
  const url = readFeishuWebhookUrl(input.config)
  if (!url) return
  if (isRealtimeTaskConfig(input.config)) return

  const roundKey = computeScheduledRoundKey(input.config)
  if (!roundKey) return

  const state = readTaskWebhookState(input.taskId)
  if (state.lastRoundNotifyKey === roundKey) return
  patchTaskWebhookState(input.taskId, { lastRoundNotifyKey: roundKey })

  const intervalMin = readCrawlIntervalMinutes(input.config)
  const written = Math.max(0, Math.floor(input.writtenRowCount))
  const total = Math.max(0, Math.floor(input.totalRowCount))

  const detailLines: string[] = [`采集频率：每 ${intervalMin} 分钟`]
  if (written > 0) {
    detailLines.push(`本轮写入飞书表格：${written} 条`)
  } else {
    detailLines.push('本轮无新数据写入飞书表格')
  }
  if (total > 0) {
    detailLines.push(`采集结果累计：${total} 条`)
  }

  await notifyTaskWebhookIfEnabled({
    taskId: input.taskId,
    taskName: input.taskName,
    config: input.config,
    event: 'scheduled_round',
    detailLines,
  })
}

/** 异步子任务或本地执行失败时推送（同一轮次内相同失败集只推一次） */
export async function maybeNotifyCollectionFailed(input: {
  taskId: number
  taskName: string
  config: Record<string, unknown>
  failedRefs?: AsyncTaskRef[]
  detailLines?: string[]
}): Promise<void> {
  const url = readFeishuWebhookUrl(input.config)
  if (!url) return
  if (isRealtimeTaskConfig(input.config)) return

  const failedRefs = input.failedRefs ?? []
  const extraLines = input.detailLines?.filter((s) => String(s).trim()) ?? []
  if (!failedRefs.length && !extraLines.length) {
    const state = readTaskWebhookState(input.taskId)
    if (state.lastFailedNotifyKey) {
      const { lastFailedNotifyKey: _, ...rest } = state
      writeTaskWebhookState(input.taskId, rest)
    }
    return
  }

  const roundKey = computeScheduledRoundKey(input.config)
  const failedKey = failedRefs.length
    ? buildFailedNotifyKey(roundKey, failedRefs)
    : `msg:${roundKey ?? 'na'}:${extraLines.join('|')}`

  const state = readTaskWebhookState(input.taskId)
  if (state.lastFailedNotifyKey === failedKey) return
  patchTaskWebhookState(input.taskId, { lastFailedNotifyKey: failedKey })

  const detailLines = [...extraLines]
  if (failedRefs.length) {
    const parts = failedRefs.map((r) => {
      const label = platformDisplayNames[r.platform] ?? r.platform
      const kw = r.keyword?.trim()
      return kw ? `${label}（关键词：${kw}）` : label
    })
    detailLines.push(`失败子任务：${parts.join('、')}`)
  }

  await notifyTaskWebhookIfEnabled({
    taskId: input.taskId,
    taskName: input.taskName,
    config: input.config,
    event: 'collection_failed',
    detailLines,
  })
}

/** @deprecated 使用 {@link maybeNotifyScheduledRoundByFrequency} */
export async function maybeNotifyScheduledRound(input: {
  taskId: number
  taskName: string
  config: Record<string, unknown>
  writtenRowCount: number
  totalRowCount: number
  maxCollectedAtMs: number
}): Promise<void> {
  await maybeNotifyScheduledRoundByFrequency({
    taskId: input.taskId,
    taskName: input.taskName,
    config: input.config,
    writtenRowCount: input.writtenRowCount,
    totalRowCount: input.totalRowCount,
  })
}

/** 定时任务本轮执行结束（异步子任务全部完成） */
export async function maybeNotifyExecutionComplete(input: {
  taskId: number
  taskName: string
  config: Record<string, unknown>
  runKey?: string
  detailLines?: string[]
}): Promise<void> {
  if (isRealtimeTaskConfig(input.config)) return
  const url = readFeishuWebhookUrl(input.config)
  if (!url) return
  const runKey = input.runKey?.trim() || buildAsyncRunKey(input.config)
  const state = readTaskWebhookState(input.taskId)
  if (state.lastCompleteRunKey === runKey) return
  patchTaskWebhookState(input.taskId, { lastCompleteRunKey: runKey })
  await notifyTaskWebhookIfEnabled({
    taskId: input.taskId,
    taskName: input.taskName,
    config: input.config,
    event: 'execution_complete',
    detailLines: input.detailLines,
  })
}

function isLowBalanceNotifiedFlagSet(): boolean {
  try {
    return localStorage.getItem(LOW_BALANCE_NOTIFIED_KEY) === '1'
  } catch {
    return false
  }
}

function setLowBalanceNotifiedFlag(on: boolean): void {
  try {
    if (on) localStorage.setItem(LOW_BALANCE_NOTIFIED_KEY, '1')
    else localStorage.removeItem(LOW_BALANCE_NOTIFIED_KEY)
  } catch {
    /* 忽略 */
  }
}

/** 积分低于阈值时推送一次；回升到阈值以上后重置，可再次提醒 */
export async function maybeNotifyLowBalance(points: number | null | undefined): Promise<void> {
  if (points == null || !Number.isFinite(points)) return
  const balance = Math.floor(points)
  if (balance >= LOW_BALANCE_THRESHOLD_POINTS) {
    setLowBalanceNotifiedFlag(false)
    return
  }
  if (isLowBalanceNotifiedFlagSet()) return

  const url = readGlobalNotifyWebhook()
  if (!url) return

  const text = [
    '【关键词监控】账户积分不足提醒',
    `当前积分：${balance.toLocaleString('zh-CN')}（低于 ${LOW_BALANCE_THRESHOLD_POINTS.toLocaleString('zh-CN')}）`,
    '请及时充值，避免采集任务中断。',
    `时间：${new Date().toLocaleString('zh-CN', { hour12: false })}`,
  ].join('\n')

  try {
    await sendFeishuWebhookText(url, text)
    setLowBalanceNotifiedFlag(true)
  } catch (e) {
    if (import.meta.env.DEV) {
      console.warn('[feishu-webhook] low-balance', e)
    }
  }
}

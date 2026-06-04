/**
 * 异步采集任务：
 * - `POST /api/v1/async/tasks` 提交
 * - `GET /api/v1/async/tasks` 列表（任务列表页定时轮询，见 `TasksView`：有 pending/running 时约 15s/次，并触发后端调度 tick）
 * - `GET /api/v1/async/tasks/{task_id}` 查看单条任务（Header：`x-api-key`、`X-User-Id`；Query 可选 `X-API-KEY`）
 * - `GET /api/v1/async/tasks/{task_id}/results` 查询采集结果（先 `GET` 状态；`running`/`completed` 或 `pending` 且已过 `next_run_at+3min` 时拉结果；首屏 `total=0` 且 `items=[]` 时最多重试 3 次，仍无数据则不验收、不扣积分）
 * - `POST /api/v1/async/tasks/{task_id}/delete` 删除任务
 * - `POST /api/v1/async/tasks/edit` 编辑任务（调度字段仅 pending 可改）
 * - `POST /api/v1/results/acceptance` 结果验收（`douyin` / `xhs` 异步任务 id 列表）
 */

import type { PlatformKey } from '@/components/PlatformIcon.vue'
import type { TaskRunStatus } from '@/views/TaskCreateForm/types'
import {
  extractAsyncTaskResultsMeta,
  extractSyncResultItems,
  extractSyncResultPageMeta,
  isEmptyAsyncTaskResultsPage,
  type AsyncTaskResultsMeta,
  type SyncFetchContext,
} from '@/lib/sync-api-common'
import { expectedApiPageRows } from '@/lib/sync-platform-page-size'
import { buildDouyinSearchPageBody } from '@/lib/sync-search-page'
import {
  getSyncApiJson,
  postSyncApiJson,
  readDataRange,
  readSearchKeywords,
} from '@/lib/sync-search-shared'
import { fetchDouyinSearchItems } from '@/lib/douyin-sync-api'
import { refreshYddmUserBalance } from '@/lib/refresh-yddm-balance'
import { isTaskWindowExpired } from '@/lib/datetime-task-window'
import { estimatePointsFromItemsByPlatform } from '@/lib/task-estimate-points'
import {
  isSyncCollectionPlatform,
  mapYddmPlatformToSyncId,
  readSyncCollectionPlatforms,
  SYNC_SEARCH_PAGE_BY_PLATFORM,
  type SyncCollectionPlatformId,
} from '@/lib/sync-collection-platforms'
import {
  ensureSyncEndpointDiscountForPlatform,
  resetPlatformSyncBillingSession,
  syncPointsPackageForPlatform,
} from '@/lib/sync-set-discount'
import { isSyncHttpError } from '@/lib/sync-api-common'
import { SYNC_SEARCH_PAGE_MAX_ATTEMPTS } from '@/lib/sync-search-shared'
import { buildGzhSearchPageBody, fetchGzhSearchItems } from '@/lib/gzh-sync-api'
import { fetchWxvideoSearchItems } from '@/lib/wxvideo-sync-api'
import { buildWxvideoSearchPageBody } from '@/lib/wxvideo-sync-api'
import { fetchXhsSearchItems } from '@/lib/xhs-sync-api'
import { buildXhsSearchPageBody } from '@/lib/xhs-sync-api'
import type { SyncItemsByPlatform } from '@/lib/sync-collection-cache'
import { setSyncCollectionCache } from '@/lib/sync-collection-cache'
import {
  DEFAULT_CRAWL_FREQUENCY,
  platformDisplayNames,
  TASK_NAME_MAX_LEN,
} from '@/views/TaskCreateForm/constants'

const ASYNC_TASK_PATH = '/api/v1/async/tasks'
/** `GET /api/v1/async/tasks` 每页条数（列表页轮询默认只拉第 1 页，见 `listTaskCardsFromAsync`） */
const ASYNC_TASK_LIST_PAGE_LIMIT = 100
const RESULTS_ACCEPTANCE_PATH = '/api/v1/results/acceptance'

/** `GET .../results` 首屏为空时最多请求次数（落库延迟场景） */
export const ASYNC_TASK_RESULTS_MAX_ATTEMPTS = 3
const ASYNC_TASK_RESULTS_RETRY_DELAY_MS = 400

function sleepMs(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

/** 定时任务 `POST /api/v1/async/tasks` 的 action（可用环境变量覆盖） */
const ACTION_BY_PLATFORM: Partial<Record<PlatformKey, string>> = {
  douyin:
    (import.meta.env.VITE_ASYNC_TASK_ACTION_DOUYIN as string | undefined)?.trim() ||
    'douyin-search-all',
  xiaohongshu:
    (import.meta.env.VITE_ASYNC_TASK_ACTION_XHS as string | undefined)?.trim() ||
    'xhs-search-all',
  shipinhao:
    (import.meta.env.VITE_ASYNC_TASK_ACTION_WXVIDEO as string | undefined)?.trim() ||
    'wxvideo-search-all',
  gzh:
    (import.meta.env.VITE_ASYNC_TASK_ACTION_GZH as string | undefined)?.trim() ||
    'mp-search-all',
}

/** Apifox：`body` 至少含 `keyword`，其余与 search-page 对齐 */
export type AsyncTaskBody = {
  keyword: string
  [property: string]: unknown
}

/**
 * 定时任务 `POST /api/v1/async/tasks` 入参。
 * `task_start_time` / `task_end_time` 对应表单「开始/结束时间」；
 * `interval_minutes` 对应「采集频率」；`fetch_count` 对应「选择条数」；
 * `task_name` 对应表单「任务名称」（1～30 字符）。
 *
 * 采集节奏由 YDDM 按上述窗口与频率调度：首轮在 `task_start_time`，之后每隔 `interval_minutes`；
 * 前端每平台×关键词提交一条异步任务。预估轮次见 `countScheduledExecutionRounds`
 * （例：14:29~14:41、5 分钟 → 14:29/14:34/14:39/14:41 共 4 轮）。
 */
export type AsyncTaskSubmitRequest = {
  action: string
  body: AsyncTaskBody
  task_name: string
  task_start_time: string
  task_end_time: string
  interval_minutes: number
  fetch_count: number
  [property: string]: unknown
}

/** `POST /api/v1/async/tasks/edit` 请求体（仅 pending 可改调度相关字段） */
export type AsyncTaskEditRequest = {
  task_id: number
  task_name?: string
  interval_minutes?: number
  fetch_count?: number
  task_start_time?: string
  task_end_time?: string
  priority?: number
}

/** 路径参数 `task_id` */
export type AsyncTaskStatusPath = {
  task_id: string
  [property: string]: unknown
}

/** 查询状态解析后的业务态 */
export type AsyncTaskLifecycle = 'pending' | 'running' | 'completed' | 'failed' | 'unknown'

const lastAsyncLifecycleByTaskId = new Map<string, AsyncTaskLifecycle>()

/** 清除生命周期缓存（切换授权码等场景，避免 task_id 复用误判） */
export function resetAsyncTaskLifecycleCache(): void {
  lastAsyncLifecycleByTaskId.clear()
}

/** 记录状态变化；由 `pending` 等变为 `running` 时在控制台打印（非首次见到该 id） */
export function notifyAsyncTaskLifecycleChange(taskId: string, lifecycle: AsyncTaskLifecycle): void {
  const id = taskId.trim()
  if (!id) return
  const prev = lastAsyncLifecycleByTaskId.get(id)
  lastAsyncLifecycleByTaskId.set(id, lifecycle)
  if (lifecycle === 'running' && prev !== undefined && prev !== 'running') {
    console.log('[async-task] 状态变为 running', { taskId: id, prevLifecycle: prev })
  }
}

export type AsyncTaskStatusResult = {
  taskId: string
  lifecycle: AsyncTaskLifecycle
  /** 接口原始 `data`（若有） */
  data: Record<string, unknown>
}

/** 提交后保存的子任务引用（用于结果查询时区分平台） */
export type AsyncTaskRef = {
  taskId: string
  platform: PlatformKey
  keyword: string
}

/** 平台 + 关键词唯一槽位（同一槽位仅保留一个 YDDM `task_id`） */
export function asyncRefSlotKey(platform: PlatformKey, keyword: string): string {
  return `${platform}:${keyword.trim()}`
}

function isReuseableAsyncTaskLifecycle(lifecycle: AsyncTaskLifecycle): boolean {
  return lifecycle === 'pending' || lifecycle === 'running' || lifecycle === 'completed'
}

export type AsyncTaskResultsPayload = {
  taskId: string
  items: Record<string, unknown>[]
  meta?: AsyncTaskResultsMeta
  /** 由 `meta.platform` 解析的表单平台 id（如 `mp` → `gzh`） */
  platform?: SyncCollectionPlatformId | null
}

/** 单条子任务 `GET .../results` 聚合结果（含 `data.meta.platform`） */
export type AsyncTaskResultsBatch = {
  items: Record<string, unknown>[]
  meta: AsyncTaskResultsMeta
  platform: SyncCollectionPlatformId | null
}

/** `GET /api/v1/async/tasks/{task_id}/results` 查询参数（Apifox：`page` 可选） */
export type AsyncTaskResultsQuery = {
  page?: string
  [property: string]: unknown
}

/** `POST /api/v1/results/acceptance` 请求体 */
export type ResultsAcceptanceRequest = {
  douyin: number[]
  xhs: number[]
}

function readSelectedSources(config: Record<string, unknown>): SyncCollectionPlatformId[] {
  return readSyncCollectionPlatforms(config)
}

const PAGINATION_BODY_KEYS = [
  'page',
  'cursor',
  'log_id',
  'logid',
  'offset',
  'cookies_buffer',
  'count',
  'data_range',
] as const

/** 定时任务 body：去掉翻页字段；`sort_type` / `time_range` / `fetch_count` 与 8765 文档对齐 */
function normalizeScheduledAsyncBody(raw: Record<string, unknown>): AsyncTaskBody {
  const body = { ...raw } as AsyncTaskBody
  for (const key of PAGINATION_BODY_KEYS) {
    delete body[key]
  }
  if (body.time_range == null) {
    const tr = body.publish_time ?? body.note_time ?? body.time_range
    if (tr != null && String(tr).trim() !== '') {
      const n = Number(tr)
      body.time_range = Number.isFinite(n) && n >= 1 ? Math.floor(n) : 7
    }
  }
  delete body.publish_time
  delete body.note_time
  if (body.sort_type != null && body.sort_type !== '') {
    const n = Number(body.sort_type)
    if (Number.isFinite(n)) body.sort_type = n
  }
  if (body.fetch_count == null && body.data_range != null) {
    const n = Number(body.data_range)
    if (Number.isFinite(n) && n >= 1) body.fetch_count = Math.min(500, Math.floor(n))
  }
  if (body.fetch_count != null) {
    const fc = Number(body.fetch_count)
    if (Number.isFinite(fc)) body.fetch_count = Math.min(500, Math.max(1, Math.floor(fc)))
  }
  return body
}

function buildDouyinAsyncTaskBody(
  config: Record<string, unknown>,
  keyword: string,
): AsyncTaskBody {
  const full = buildDouyinSearchPageBody(config, keyword)
  const { cursor: _c, log_id: _l, ...rest } = full
  return normalizeScheduledAsyncBody(rest as Record<string, unknown>)
}

function buildXhsAsyncTaskBody(config: Record<string, unknown>, keyword: string): AsyncTaskBody {
  const full = buildXhsSearchPageBody(config, keyword, 1)
  const { page: _p, ...rest } = full
  return normalizeScheduledAsyncBody(rest as Record<string, unknown>)
}

function buildWxvideoAsyncTaskBody(config: Record<string, unknown>, keyword: string): AsyncTaskBody {
  const full = buildWxvideoSearchPageBody(config, keyword, 1)
  const { page: _p, offset: _o, cookies_buffer: _cb, ...rest } = full
  return normalizeScheduledAsyncBody(rest as Record<string, unknown>)
}

function buildGzhAsyncTaskBody(config: Record<string, unknown>, keyword: string): AsyncTaskBody {
  const full = buildGzhSearchPageBody(config, keyword, 1)
  const { page: _p, offset: _o, cookies_buffer: _cb, ...rest } = full
  return normalizeScheduledAsyncBody(rest as Record<string, unknown>)
}

/** 从任务配置读取定时监控窗口与频率（仅定时任务；单次任务勿调用） */
export function readAsyncTaskSchedule(config: Record<string, unknown>): {
  task_start_time: string
  task_end_time: string
  interval_minutes: number
  fetch_count: number
} {
  if (isRealtimeTaskConfig(config)) {
    throw new Error('单次任务无需填写监控开始/结束时间')
  }
  const task_start_time = String(config.effectiveAt ?? config.effective_at ?? '').trim()
  const task_end_time = String(config.expireAt ?? config.expire_at ?? '').trim()
  const freqRaw = config.crawlFrequency ?? config.crawl_frequency ?? DEFAULT_CRAWL_FREQUENCY
  const interval = typeof freqRaw === 'number' ? freqRaw : Number(String(freqRaw).trim())
  const fallbackMins = Number(DEFAULT_CRAWL_FREQUENCY)
  const interval_minutes =
    Number.isFinite(interval) && interval > 0 ? Math.floor(interval) : fallbackMins
  const fetch_count = readDataRange(config)

  if (!task_start_time) {
    throw new Error('请填写监控开始时间')
  }
  if (!task_end_time) {
    throw new Error('请填写监控结束时间')
  }

  return { task_start_time, task_end_time, interval_minutes, fetch_count }
}

/** 表单/配置中的任务名称（提交与编辑接口 `task_name`） */
export function readAsyncTaskName(config: Record<string, unknown>): string {
  const name = String(config.planName ?? config.plan_name ?? config.task_name ?? '').trim()
  if (!name) throw new Error('请填写任务名称')
  if (name.length > TASK_NAME_MAX_LEN) {
    throw new Error(`任务名称不能超过 ${TASK_NAME_MAX_LEN} 个字符`)
  }
  return name
}

export function buildAsyncTaskSubmitRequest(
  platform: SyncCollectionPlatformId,
  config: Record<string, unknown>,
  keyword: string,
): AsyncTaskSubmitRequest {
  const action = ACTION_BY_PLATFORM[platform]?.trim()
  if (!action) throw new Error(`平台 ${platform} 未配置异步 action`)
  const schedule = readAsyncTaskSchedule(config)
  const body = buildAsyncTaskBodyForPlatform(platform, config, keyword)
  const task_name = readAsyncTaskName(config)
  return { action, body, task_name, ...schedule }
}

function buildAsyncTaskBodyForPlatform(
  platform: SyncCollectionPlatformId,
  config: Record<string, unknown>,
  keyword: string,
): AsyncTaskBody {
  switch (platform) {
    case 'douyin':
      return buildDouyinAsyncTaskBody(config, keyword)
    case 'xiaohongshu':
      return buildXhsAsyncTaskBody(config, keyword)
    case 'shipinhao':
      return buildWxvideoAsyncTaskBody(config, keyword)
    case 'gzh':
      return buildGzhAsyncTaskBody(config, keyword)
    default:
      return { keyword: keyword.trim() }
  }
}

/** 从提交/查询响应中提取 `task_id` */
function readTaskIdField(raw: unknown): string | null {
  if (typeof raw === 'string' && raw.trim()) return raw.trim()
  if (typeof raw === 'number' && Number.isFinite(raw)) return String(raw)
  return null
}

/** 从列表条目或状态响应中解析 YDDM 异步任务 id */
export function extractAsyncTaskId(payload: unknown): string | null {
  if (!payload || typeof payload !== 'object') return null
  const visit = (node: unknown, depth: number): string | null => {
    if (depth > 6 || !node || typeof node !== 'object') return null
    const r = node as Record<string, unknown>
    const tid = readTaskIdField(r.task_id ?? r.taskId ?? r.id)
    if (tid) return tid
    for (const key of ['data', 'result']) {
      const found = visit(r[key], depth + 1)
      if (found) return found
    }
    return null
  }
  return visit(payload, 0)
}

const RUNNING_STATUSES = new Set([
  'queued',
  'queue',
  'running',
  'processing',
  'in_progress',
  'in-progress',
  'active',
])
const COMPLETED_STATUSES = new Set(['completed', 'complete', 'success', 'succeeded', 'done', 'finished'])
const FAILED_STATUSES = new Set(['failed', 'error', 'cancelled', 'canceled', 'timeout', 'aborted'])

function normalizeLifecycle(raw: unknown): AsyncTaskLifecycle {
  if (raw == null) return 'unknown'
  const s = String(raw).trim().toLowerCase()
  if (!s) return 'unknown'
  if (RUNNING_STATUSES.has(s)) return 'running'
  if (COMPLETED_STATUSES.has(s)) return 'completed'
  if (FAILED_STATUSES.has(s)) return 'failed'
  if (s === 'pending' || s === 'waiting') return 'pending'
  return 'unknown'
}

function pickStatusField(record: Record<string, unknown>): unknown {
  for (const key of ['status', 'state', 'task_status', 'taskStatus', 'run_status', 'runStatus']) {
    if (record[key] != null) return record[key]
  }
  return null
}

function tryRecordArray(v: unknown): Record<string, unknown>[] {
  if (!Array.isArray(v)) return []
  return v.filter((x): x is Record<string, unknown> => x != null && typeof x === 'object')
}

function unwrapMaybeJsonString(value: unknown): unknown {
  if (typeof value !== 'string') return value
  const s = value.trim()
  if (!s.startsWith('{') && !s.startsWith('[')) return value
  try {
    return JSON.parse(s) as unknown
  } catch {
    return value
  }
}

function readSyncDataObject(payload: Record<string, unknown>): Record<string, unknown> | null {
  const data = unwrapMaybeJsonString(payload.data)
  if (!data || typeof data !== 'object' || Array.isArray(data)) return null
  return data as Record<string, unknown>
}

/** `GET /api/v1/async/tasks` 列表 `data.result.summary` */
export type AsyncTaskListSummary = {
  total: number
  pending: number
  running: number
  success: number
  failed: number
  cancelled: number
  active: number
  total_success_count: number
  total_failed_count: number
}

/** `GET /api/v1/async/tasks` 列表 `data.result` 分页块 */
export type AsyncTaskListPage = {
  page: number
  limit: number
  summary: AsyncTaskListSummary | null
  items: Record<string, unknown>[]
}

function readAsyncTaskListSummary(raw: unknown): AsyncTaskListSummary | null {
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return null
  const s = raw as Record<string, unknown>
  const num = (k: string) => {
    const v = s[k]
    return typeof v === 'number' && Number.isFinite(v) ? v : 0
  }
  return {
    total: num('total'),
    pending: num('pending'),
    running: num('running'),
    success: num('success'),
    failed: num('failed'),
    cancelled: num('cancelled'),
    active: num('active'),
    total_success_count: num('total_success_count'),
    total_failed_count: num('total_failed_count'),
  }
}

/**
 * 解析 `GET /api/v1/async/tasks` 完整列表响应。
 * 标准形态：`{ code, msg, data: { result: { page, limit, summary, items[] }, meta } }`
 */
export function parseAsyncTaskListEnvelope(payload: unknown): AsyncTaskListPage {
  const empty: AsyncTaskListPage = { page: 1, limit: 20, summary: null, items: [] }
  if (!payload || typeof payload !== 'object') return empty
  const data = readSyncDataObject(payload as Record<string, unknown>)
  if (!data) return empty

  const result = unwrapMaybeJsonString(data.result)
  if (result && typeof result === 'object' && !Array.isArray(result)) {
    const r = result as Record<string, unknown>
    const items = tryRecordArray(r.items)
    const page = typeof r.page === 'number' && Number.isFinite(r.page) ? r.page : 1
    const limit = typeof r.limit === 'number' && Number.isFinite(r.limit) ? r.limit : 20
    return {
      page,
      limit,
      summary: readAsyncTaskListSummary(r.summary),
      items,
    }
  }

  for (const key of ['items', 'list', 'tasks', 'records', 'rows']) {
    const hit = tryRecordArray(data[key])
    if (hit.length) return { page: 1, limit: hit.length, summary: null, items: hit }
  }

  const root = payload as Record<string, unknown>
  if (Array.isArray(root.data)) {
    const hit = tryRecordArray(root.data)
    if (hit.length) return { page: 1, limit: hit.length, summary: null, items: hit }
  }
  const legacy = tryRecordArray(root.items ?? root.tasks ?? root.list ?? root.records)
  return { ...empty, items: legacy }
}

/** 解析 `GET /api/v1/async/tasks` 列表响应中的任务条目（`data.result.items`） */
export function extractAsyncTaskListRecords(payload: unknown): Record<string, unknown>[] {
  return parseAsyncTaskListEnvelope(payload).items
}

/** 从列表条目中解析采集结果（列表 `items` 通常无内嵌结果，需另调 `/results`） */
export function extractAsyncTaskResultItemsFromRecord(
  record: Record<string, unknown>,
): Record<string, unknown>[] {
  const direct = extractAsyncTaskResultItems(record)
  if (direct.length) return direct
  for (const key of ['results', 'data', 'items']) {
    const hit = extractAsyncTaskResultItems(record[key])
    if (hit.length) return hit
  }
  return []
}

/** `GET /api/v1/async/tasks` 任务列表（可选 `page` / `limit`） */
export async function listAsyncTasks(
  ctx: SyncFetchContext,
  query?: { page?: number; limit?: number },
): Promise<unknown> {
  const qs = new URLSearchParams()
  if (query?.page != null && Number.isFinite(query.page)) qs.set('page', String(Math.floor(query.page)))
  if (query?.limit != null && Number.isFinite(query.limit)) {
    qs.set('limit', String(Math.floor(query.limit)))
  }
  const path = qs.toString() ? `${ASYNC_TASK_PATH}?${qs.toString()}` : ASYNC_TASK_PATH
  return getSyncApiJson({
    path,
    platformLabel: '异步任务列表',
    ctx,
  })
}

export type ListAllAsyncTaskPagesOptions = {
  /** 每页条数，默认 `ASYNC_TASK_LIST_PAGE_LIMIT` */
  limit?: number
  /** 最多请求页数；列表轮询传 `1` 避免连续 `page=1,2,3…` */
  maxPages?: number
}

/** 拉取分页条目（合并 `items`，保留首页 `summary`） */
export async function listAllAsyncTaskPages(
  ctx: SyncFetchContext,
  options?: ListAllAsyncTaskPagesOptions,
): Promise<AsyncTaskListPage> {
  const limit = options?.limit ?? ASYNC_TASK_LIST_PAGE_LIMIT
  const maxPages = Math.max(1, Math.min(options?.maxPages ?? 50, 50))
  let page = 1
  const items: Record<string, unknown>[] = []
  let summary: AsyncTaskListSummary | null = null

  while (page <= maxPages) {
    const parsed = await listAsyncTasks(ctx, { page, limit })
    const batch = parseAsyncTaskListEnvelope(parsed)
    if (!summary && batch.summary) summary = batch.summary
    items.push(...batch.items)
    if (batch.items.length < limit) break
    if (summary && summary.total > 0 && items.length >= summary.total) break
    page += 1
  }

  return { page: 1, limit: items.length || limit, summary, items }
}

/**
 * 批量查询任务状态：`GET /api/v1/async/tasks/{task_id}`（不拉列表，避免与列表页重复请求）。
 */
/** 根据已拉取的状态 Map 筛选 failed 子任务（避免重复 `GET .../tasks/{id}`） */
export function listFailedAsyncTaskRefsFromStatusMap(
  config: Record<string, unknown>,
  statusMap: Map<string, AsyncTaskStatusResult>,
): AsyncTaskRef[] {
  const refs = readAsyncTaskRefs(config)
  if (refs.length) {
    return refs.filter((r) => statusMap.get(r.taskId)?.lifecycle === 'failed')
  }
  return readAsyncTaskIds(config)
    .filter((id) => statusMap.get(id)?.lifecycle === 'failed')
    .map((taskId) => ({ taskId, platform: 'douyin' as PlatformKey, keyword: '' }))
}

/** 查询配置中状态为 failed 的异步子任务 */
export async function listFailedAsyncTaskRefs(
  config: Record<string, unknown>,
  ctx: SyncFetchContext,
): Promise<AsyncTaskRef[]> {
  const refs = readAsyncTaskRefs(config)
  const ids = refs.length ? refs.map((r) => r.taskId) : readAsyncTaskIds(config)
  if (!ids.length) return []
  const statusMap = await fetchAsyncTaskStatusMap(ctx, ids)
  return listFailedAsyncTaskRefsFromStatusMap(config, statusMap)
}

export async function fetchAsyncTaskStatusMap(
  ctx: SyncFetchContext,
  taskIds: string[],
): Promise<Map<string, AsyncTaskStatusResult>> {
  const wanted = [...new Set(taskIds.map((x) => x.trim()).filter(Boolean))]
  const map = new Map<string, AsyncTaskStatusResult>()
  if (!wanted.length) return map

  await Promise.all(
    wanted.map(async (id) => {
      try {
        map.set(id, await getAsyncTaskStatus(ctx, id))
      } catch {
        map.set(id, { taskId: id, lifecycle: 'unknown', data: {} })
      }
    }),
  )
  return map
}

/**
 * 从 `GET /api/v1/async/tasks/{id}` 响应取出任务条目（兼容 `data` / `data.result` 与列表 `items[]` 同构）。
 */
export function extractAsyncTaskStatusRecord(payload: unknown): Record<string, unknown> {
  if (!payload || typeof payload !== 'object') return {}
  const root = payload as Record<string, unknown>
  const dataRaw = unwrapMaybeJsonString(root.data)
  if (dataRaw && typeof dataRaw === 'object' && !Array.isArray(dataRaw)) {
    const data = dataRaw as Record<string, unknown>
    const result = unwrapMaybeJsonString(data.result)
    if (result && typeof result === 'object' && !Array.isArray(result)) {
      const rec = result as Record<string, unknown>
      if (pickStatusField(rec) != null || readTaskIdField(rec.task_id ?? rec.taskId) != null) {
        return rec
      }
    }
    if (pickStatusField(data) != null || readTaskIdField(data.task_id ?? data.taskId) != null) {
      return data
    }
  }
  if (pickStatusField(root) != null || readTaskIdField(root.task_id ?? root.taskId) != null) {
    return root
  }
  return {}
}

/** 解析 `GET /api/v1/async/tasks/{task_id}` 响应 */
export function parseAsyncTaskStatusResponse(
  payload: unknown,
  taskId: string,
): AsyncTaskStatusResult {
  const data = extractAsyncTaskStatusRecord(payload)
  const id = extractAsyncTaskId(data) ?? extractAsyncTaskId(payload) ?? taskId.trim()
  const lifecycle = normalizeLifecycle(pickStatusField(data))
  notifyAsyncTaskLifecycleChange(id, lifecycle)
  return { taskId: id, lifecycle, data }
}

/** 从 results 响应中提取条目列表（兼容 search-page 与多种 `data` 形态） */
export function extractAsyncTaskResultItems(payload: unknown): Record<string, unknown>[] {
  return extractSyncResultItems(payload)
}

/** 配置中保存的异步任务 id 列表 */
export function readAsyncTaskIds(config: Record<string, unknown>): string[] {
  const refs = readAsyncTaskRefs(config)
  if (refs.length) return refs.map((r) => r.taskId)
  const raw = config.asyncTaskIds ?? config.async_task_ids
  if (!Array.isArray(raw)) return []
  const out: string[] = []
  for (const x of raw) {
    const s = String(x).trim()
    if (s) out.push(s)
  }
  return [...new Set(out)]
}

/** 单次任务不应保留的 YDDM 子任务引用（避免误调 `GET .../results`） */
export function clearRealtimeAsyncBindings(config: Record<string, unknown>): Record<string, unknown> {
  const next = { ...config }
  delete next.asyncTaskRefs
  delete next.async_task_refs
  delete next.asyncTaskIds
  delete next.async_task_ids
  return next
}

/**
 * 用于拉取 `GET .../async/tasks/{id}/results` 的子任务 id。
 * 排除与列表主任务 id 相同且无任何 `asyncTaskRefs` 的脏数据（单次任务误写入的 `asyncTaskIds: [主任务id]`）。
 */
export function readAsyncSubTaskIdsForResults(
  config: Record<string, unknown>,
  parentTaskId?: number,
): string[] {
  const refs = readAsyncTaskRefs(config)
  if (refs.length) return [...new Set(refs.map((r) => r.taskId.trim()).filter(Boolean))]
  const parent = parentTaskId != null ? String(parentTaskId).trim() : ''
  return readAsyncTaskIds(config).filter((id) => id.trim() && id.trim() !== parent)
}

/** 是否走异步 results（单次任务 / 已有 search-page 预加载数据时返回 false） */
export function shouldUseAsyncTaskResultsFeed(
  config: Record<string, unknown>,
  options?: { parentTaskId?: number; hasPreloadedSyncItems?: boolean },
): boolean {
  if (options?.hasPreloadedSyncItems) return false
  if (isRealtimeTaskConfig(config)) return false
  return readAsyncSubTaskIdsForResults(config, options?.parentTaskId).length > 0
}

export function readAsyncTaskRefs(config: Record<string, unknown>): AsyncTaskRef[] {
  const raw = config.asyncTaskRefs ?? config.async_task_refs
  if (!Array.isArray(raw)) return []
  const out: AsyncTaskRef[] = []
  for (const x of raw) {
    if (!x || typeof x !== 'object') continue
    const r = x as Record<string, unknown>
    const taskId = String(r.taskId ?? r.task_id ?? '').trim()
    const platform = String(r.platform ?? '').trim()
    if (!taskId || !isSyncCollectionPlatform(platform)) continue
    out.push({
      taskId,
      platform,
      keyword: String(r.keyword ?? '').trim(),
    })
  }
  const bySlot = new Map<string, AsyncTaskRef>()
  for (const ref of out) {
    bySlot.set(asyncRefSlotKey(ref.platform, ref.keyword), ref)
  }
  return [...bySlot.values()]
}

export function mergeAsyncTaskIds(
  config: Record<string, unknown>,
  incoming: string[],
): string[] {
  return [...new Set([...readAsyncTaskIds(config), ...incoming.map((x) => x.trim()).filter(Boolean)])]
}

export function mergeAsyncTaskRefs(
  config: Record<string, unknown>,
  incoming: AsyncTaskRef[],
): AsyncTaskRef[] {
  const bySlot = new Map<string, AsyncTaskRef>()
  for (const ref of readAsyncTaskRefs(config)) {
    bySlot.set(asyncRefSlotKey(ref.platform, ref.keyword), ref)
  }
  for (const ref of incoming) {
    if (!ref.taskId.trim()) continue
    bySlot.set(asyncRefSlotKey(ref.platform, ref.keyword), ref)
  }
  return [...bySlot.values()]
}

/** 多条异步子任务聚合：任一失败→失败；全部完成→完成；否则运行中 */
export function aggregateAsyncTaskLifecycles(
  items: AsyncTaskStatusResult[],
): AsyncTaskLifecycle {
  if (!items.length) return 'unknown'
  if (items.some((x) => x.lifecycle === 'failed')) return 'failed'
  if (items.every((x) => x.lifecycle === 'completed')) return 'completed'
  if (items.some((x) => x.lifecycle === 'running' || x.lifecycle === 'pending')) return 'running'
  return 'unknown'
}

export async function postAsyncTask(
  ctx: SyncFetchContext,
  req: AsyncTaskSubmitRequest,
): Promise<unknown> {
  return postSyncApiJson({
    path: ASYNC_TASK_PATH,
    platformLabel: '异步任务',
    body: req as unknown as Record<string, unknown>,
    ctx,
  })
}

/**
 * `POST /api/v1/async/tasks/{task_id}/delete` 删除 YDDM 异步任务。
 * Path：`task_id`；Header：`x-api-key`、`X-User-Id`（由 `SyncFetchContext` 注入）。
 */
export async function deleteAsyncTask(
  ctx: SyncFetchContext,
  taskId: string,
): Promise<unknown> {
  const id = taskId.trim()
  if (!id) throw new Error('缺少 task_id')
  return postSyncApiJson({
    path: `${ASYNC_TASK_PATH}/${encodeURIComponent(id)}/delete`,
    platformLabel: '删除异步任务',
    body: {},
    ctx,
  })
}

/** @deprecated 使用 {@link deleteAsyncTask} */
export const cancelAsyncTask = deleteAsyncTask

/**
 * `POST /api/v1/async/tasks/{task_id}/restart` 重启/立即执行异步任务。
 * 适用场景：
 * - 已结束的任务（success/failed/cancelled）重新开始
 * - pending_run 状态的定时任务立即执行（不等到 task_start_time）
 * Path：`task_id`；Header：`x-api-key`、`X-User-Id`（由 `SyncFetchContext` 注入）。
 */
export async function restartAsyncTask(
  ctx: SyncFetchContext,
  taskId: string,
): Promise<unknown> {
  const id = taskId.trim()
  if (!id) throw new Error('缺少 task_id')
  return postSyncApiJson({
    path: `${ASYNC_TASK_PATH}/${encodeURIComponent(id)}/restart`,
    platformLabel: '重启异步任务',
    body: {},
    ctx,
  })
}

/** YDDM `pending` 对应列表 `pending_run`；仅此时可改调度字段 */
export function canEditAsyncScheduleFields(
  status: TaskRunStatus | AsyncTaskLifecycle | null | undefined,
): boolean {
  if (status == null) return false
  if (status === 'pending_run' || status === 'pending') return true
  return false
}

function readPriorityFromConfig(config: Record<string, unknown>): number | undefined {
  const raw = config.priority
  if (raw == null || String(raw).trim() === '') return undefined
  const n = typeof raw === 'number' ? raw : Number(String(raw).trim())
  if (!Number.isFinite(n)) return undefined
  const p = Math.floor(n)
  if (p < 0 || p > 9) return undefined
  return p
}

/**
 * 由表单/配置构造 `POST /api/v1/async/tasks/edit` 请求体。
 * @param allowScheduleFields - 为 false 时不传 interval/fetch/窗口/priority（非 pending）
 */
export function buildAsyncTaskEditRequest(
  taskId: number,
  input: Record<string, unknown>,
  options?: { allowScheduleFields?: boolean },
): AsyncTaskEditRequest {
  const id = Math.floor(taskId)
  if (!Number.isFinite(id) || id <= 0) {
    throw new Error('缺少有效的 task_id')
  }

  const body: AsyncTaskEditRequest = { task_id: id }

  const name = String(input.planName ?? input.plan_name ?? input.task_name ?? '').trim()
  if (name) {
    if (name.length > TASK_NAME_MAX_LEN) {
      throw new Error(`任务名称不能超过 ${TASK_NAME_MAX_LEN} 个字符`)
    }
    body.task_name = name
  }

  if (!options?.allowScheduleFields) {
    return body
  }

  const freqRaw = input.crawlFrequency ?? input.crawl_frequency ?? input.interval_minutes
  const interval =
    typeof freqRaw === 'number' ? freqRaw : Number(String(freqRaw ?? '').trim())
  if (Number.isFinite(interval)) {
    const mins = Math.floor(interval)
    if (mins < 5) throw new Error('采集频率不能小于 5 分钟')
    body.interval_minutes = mins
  }

  const fetch = readDataRange(input)
  if (fetch >= 1 && fetch <= 500) {
    body.fetch_count = fetch
  }

  const start = String(input.effectiveAt ?? input.effective_at ?? input.task_start_time ?? '').trim()
  if (start) body.task_start_time = start

  const end = String(input.expireAt ?? input.expire_at ?? input.task_end_time ?? '').trim()
  if (end) body.task_end_time = end

  const priority = readPriorityFromConfig(input)
  if (priority != null) body.priority = priority

  return body
}

/** 列表/状态接口条目 → 表单 `config` 补丁（无本地 feishu_task_configs 时回显） */
export function configPatchFromAsyncTaskRecord(rec: Record<string, unknown>): Record<string, unknown> {
  const start = String(rec.task_start_time ?? rec.taskStartTime ?? '').trim()
  const end = String(rec.task_end_time ?? rec.taskEndTime ?? '').trim()
  const interval = rec.interval_minutes ?? rec.intervalMinutes
  const fetch = rec.fetch_count ?? rec.fetchCount
  const name = String(rec.task_name ?? rec.taskName ?? '').trim()
  const platform = String(rec.platform ?? '').trim().toLowerCase()
  let keyword = String(rec.keyword ?? '').trim()
  const bodyRaw = rec.body
  if (!keyword && bodyRaw && typeof bodyRaw === 'object' && !Array.isArray(bodyRaw)) {
    keyword = String((bodyRaw as Record<string, unknown>).keyword ?? '').trim()
  }

  const explicitType = rec.task_type ?? rec.taskType
  const taskType =
    explicitType === 'realtime' || explicitType === 'scheduled'
      ? explicitType
      : start || end
        ? 'scheduled'
        : 'realtime'

  const patch: Record<string, unknown> = {
    taskType,
    runStatus: 'pending_run',
  }
  if (name) patch.planName = name
  if (start) patch.effectiveAt = start
  if (end) patch.expireAt = end
  if (interval != null && String(interval).trim() !== '') {
    patch.crawlFrequency = String(Math.floor(Number(interval)))
  }
  if (fetch != null && String(fetch).trim() !== '') {
    const n = Math.floor(Number(fetch))
    if (Number.isFinite(n) && n >= 1) patch.dataRange = Math.min(500, n)
  }
  const platformNorm =
    platform === 'xhs'
      ? 'xiaohongshu'
      : platform === 'mp'
        ? 'gzh'
        : platform === 'wxvideo'
          ? 'shipinhao'
          : platform
  if (platformNorm && isSyncCollectionPlatform(platformNorm)) {
    patch.selectedSources = [platformNorm]
  }
  if (keyword) patch.keywords = [keyword]

  const pri = readPriorityFromConfig(rec)
  if (pri != null) patch.priority = pri

  return patch
}

/** `POST /api/v1/async/tasks/edit` */
export async function editAsyncTask(
  ctx: SyncFetchContext,
  req: AsyncTaskEditRequest,
): Promise<unknown> {
  return postSyncApiJson({
    path: `${ASYNC_TASK_PATH}/edit`,
    platformLabel: '编辑异步任务',
    body: req as unknown as Record<string, unknown>,
    ctx,
  })
}

/**
 * 查看任务：`GET /api/v1/async/tasks/{task_id}`
 * - Header（必需）：`x-api-key`、`X-User-Id`
 * - Query（可选）：`X-API-KEY`（与 Header 同值，兼容 Apifox 文档）
 */
export async function getAsyncTaskStatus(
  ctx: SyncFetchContext,
  taskId: string,
): Promise<AsyncTaskStatusResult> {
  const id = taskId.trim()
  if (!id) throw new Error('缺少 task_id')
  const apiKey = ctx.apiKey?.trim() ?? ''
  const parsed = await getSyncApiJson({
    path: `${ASYNC_TASK_PATH}/${encodeURIComponent(id)}`,
    platformLabel: '查看异步任务',
    ctx,
    query: apiKey ? { 'X-API-KEY': apiKey } : undefined,
  })
  return parseAsyncTaskStatusResponse(parsed, id)
}

/** 待运行定时任务：在 YDDM `next_run_at` 之后约 3 分钟再拉 results（各平台共用） */
export const PENDING_RESULTS_AFTER_NEXT_RUN_MS = 3 * 60_000

/** 是否已到「pending 可拉 results」时刻（`next_run_at` + {@link PENDING_RESULTS_AFTER_NEXT_RUN_MS}） */
export function isPendingAsyncResultsDue(
  nextRunAtRaw: string | null | undefined,
  nowMs = Date.now(),
  expireAtRaw?: string | null,
): boolean {
  if (isTaskWindowExpired(expireAtRaw, nowMs)) return false
  const raw = nextRunAtRaw?.trim()
  if (!raw) return false
  const nextRunAtMs = Date.parse(raw.replace(' ', 'T'))
  if (!Number.isFinite(nextRunAtMs)) return false
  return nowMs >= nextRunAtMs + PENDING_RESULTS_AFTER_NEXT_RUN_MS
}

/**
 * 是否对该 lifecycle 发起 `GET .../results`。
 * - `running`：始终拉取
 * - `pending`：在列表轮询判定 `pendingResultsDue`（next_run_at+3min）时拉取
 * - `completed`、`failed`：不拉取
 */
export function shouldFetchAsyncResultsAfterStatus(
  lifecycle: AsyncTaskLifecycle,
  options?: { pendingResultsDue?: boolean },
): boolean {
  if (lifecycle === 'running') return true
  if (lifecycle === 'pending' && options?.pendingResultsDue) return true
  return false
}

/** `GET /api/v1/async/tasks/{task_id}/results` 单页原始响应（Header：`x-api-key`、`X-User-Id`） */
export async function fetchAsyncTaskResultsPage(
  ctx: SyncFetchContext,
  taskId: string,
  query?: AsyncTaskResultsQuery,
): Promise<unknown> {
  const id = taskId.trim()
  if (!id) throw new Error('缺少 task_id')
  let path = `${ASYNC_TASK_PATH}/${encodeURIComponent(id)}/results`
  const page = query?.page
  if (page != null && String(page).trim()) {
    path += `?${new URLSearchParams({ page: String(page).trim() }).toString()}`
  }
  if (import.meta.env.DEV) {
    console.log('[async-task] GET', path)
  }
  return getSyncApiJson({
    path,
    platformLabel: '异步任务结果',
    ctx,
  })
}

/**
 * 首屏 `total=0` 且 `items=[]` 时连续重试（最多 {@link ASYNC_TASK_RESULTS_MAX_ATTEMPTS} 次）。
 * 翻页（`page>1`）不重试。
 */
async function fetchAsyncTaskResultsPageWithRetry(
  ctx: SyncFetchContext,
  taskId: string,
  query?: AsyncTaskResultsQuery,
): Promise<unknown> {
  const pageNum = query?.page != null ? Number.parseInt(String(query.page).trim(), 10) : 1
  const isFirstPage = !Number.isFinite(pageNum) || pageNum <= 1
  if (!isFirstPage) {
    return fetchAsyncTaskResultsPage(ctx, taskId, query)
  }

  let last: unknown = null
  for (let attempt = 1; attempt <= ASYNC_TASK_RESULTS_MAX_ATTEMPTS; attempt++) {
    const parsed = await fetchAsyncTaskResultsPage(ctx, taskId, query)
    last = parsed
    if (!isEmptyAsyncTaskResultsPage(parsed)) {
      if (attempt > 1 && import.meta.env.DEV) {
        console.log('[async-task] results 重试成功', { taskId, attempt })
      }
      return parsed
    }
    if (attempt < ASYNC_TASK_RESULTS_MAX_ATTEMPTS) {
      if (import.meta.env.DEV) {
        console.warn('[async-task] results 为空，将重试', { taskId, attempt })
      }
      await sleepMs(ASYNC_TASK_RESULTS_RETRY_DELAY_MS * attempt)
    }
  }
  return last!
}

/** @deprecated 使用 `fetchAsyncTaskResultsPage` */
export const postAsyncTaskResults = fetchAsyncTaskResultsPage

function resolvePlatformFromResultsMeta(meta: AsyncTaskResultsMeta): SyncCollectionPlatformId | null {
  return mapYddmPlatformToSyncId(meta.platform ?? meta.source)
}

/** 拉取单任务全部结果页（`GET .../results?page=`）；达到选择条数后不再翻页，末页超出条数不截断 */
export async function fetchAllAsyncTaskResults(
  ctx: SyncFetchContext,
  taskId: string,
  options?: { maxItems?: number },
): Promise<AsyncTaskResultsBatch> {
  const collected: Record<string, unknown>[] = []
  let meta: AsyncTaskResultsMeta = {}
  const maxPages = 50
  const maxItems =
    options?.maxItems != null && options.maxItems > 0 ? Math.floor(options.maxItems) : undefined

  for (let pageNum = 1; pageNum <= maxPages; pageNum++) {
    const parsed = await fetchAsyncTaskResultsPageWithRetry(
      ctx,
      taskId,
      pageNum > 1 ? { page: String(pageNum) } : {},
    )
    if (!meta.platform && !meta.resultTable) {
      meta = extractAsyncTaskResultsMeta(parsed)
    }
    const batch = extractAsyncTaskResultItems(parsed)
    if (batch.length) collected.push(...batch)

    const pageMeta = extractSyncResultPageMeta(parsed)
    if (pageMeta.insufficientBalance) {
      throw new Error('账户积分不足，无法继续采集')
    }
    if (maxItems != null && collected.length >= maxItems) break
    if (!batch.length) break

    const platform = resolvePlatformFromResultsMeta(meta)
    const rowsPerPage = expectedApiPageRows(platform ?? 'douyin')

    /*
     * 结果接口用 `?page=` 翻页（非 cursor）。抖音约 10 条/页：
     * 本页满页则继续请求下一页，直至凑满 maxItems 或遇到不足一页的末页。
     * 不依赖 `has_more`（首屏常误报 false，导致只写入 10 条）。
     */
    const needMore = maxItems == null || collected.length < maxItems
    if (needMore && batch.length >= rowsPerPage) continue
    if (batch.length < rowsPerPage) break
  }

  if (import.meta.env.DEV && maxItems != null && collected.length > 0 && collected.length < maxItems) {
    console.warn('[async-task] results 未凑满选择条数', {
      taskId,
      collected: collected.length,
      maxItems,
      platform: resolvePlatformFromResultsMeta(meta),
    })
  }

  const platform = resolvePlatformFromResultsMeta(meta)
  /* 不按选择条数截断：末页若多于上限则全部保留；翻页仅在 collected.length < maxItems 时继续 */
  return { items: collected, meta, platform }
}

/** @deprecated 使用 `fetchAllAsyncTaskResults` */
export async function fetchAllAsyncTaskResultItems(
  ctx: SyncFetchContext,
  taskId: string,
): Promise<Record<string, unknown>[]> {
  const batch = await fetchAllAsyncTaskResults(ctx, taskId)
  return batch.items
}

/** 批量拉取任务结果（每条先依赖状态接口，再 `GET .../results`） */
export async function fetchAsyncTaskResultsMap(
  ctx: SyncFetchContext,
  taskIds: string[],
  statusMap?: Map<string, AsyncTaskStatusResult>,
  options?: { maxItemsPerTask?: number; pendingResultsDue?: boolean },
): Promise<Map<string, AsyncTaskResultsBatch>> {
  const wanted = [...new Set(taskIds.map((x) => x.trim()).filter(Boolean))]
  const map = new Map<string, AsyncTaskResultsBatch>()
  if (!wanted.length) return map

  const emptyBatch = (): AsyncTaskResultsBatch => ({
    items: [],
    meta: {},
    platform: null,
  })

  await Promise.all(
    wanted.map(async (id) => {
      const lifecycle = statusMap?.get(id)?.lifecycle ?? 'unknown'
      if (!shouldFetchAsyncResultsAfterStatus(lifecycle, { pendingResultsDue: options?.pendingResultsDue })) {
        map.set(id, emptyBatch())
        return
      }
      try {
        map.set(id, await fetchAllAsyncTaskResults(ctx, id, { maxItems: options?.maxItemsPerTask }))
      } catch {
        map.set(id, emptyBatch())
      }
    }),
  )
  return map
}

function parseAsyncTaskIdAsInt(taskId: string): number | null {
  const n = Math.floor(Number(taskId.trim()))
  return Number.isFinite(n) && n > 0 ? n : null
}

/**
 * 由异步子任务引用与 results 映射构造验收 body（仅含已拉到条目的 douyin / 小红书任务 id）。
 */
export function buildResultsAcceptanceBody(
  refs: AsyncTaskRef[],
  resultsMap: Map<string, AsyncTaskResultsBatch>,
): ResultsAcceptanceRequest {
  const douyin: number[] = []
  const xhs: number[] = []
  const seenDouyin = new Set<number>()
  const seenXhs = new Set<number>()

  for (const ref of refs) {
    const id = parseAsyncTaskIdAsInt(ref.taskId)
    if (id == null) continue
    const items = resultsMap.get(ref.taskId)?.items ?? []
    if (!items.length) continue

    if (ref.platform === 'douyin') {
      if (!seenDouyin.has(id)) {
        seenDouyin.add(id)
        douyin.push(id)
      }
    } else if (ref.platform === 'xiaohongshu') {
      if (!seenXhs.has(id)) {
        seenXhs.add(id)
        xhs.push(id)
      }
    }
  }

  return { douyin, xhs }
}

/** `POST /api/v1/results/acceptance`（Header：`x-api-key`、`X-User-Id`） */
export async function postResultsAcceptance(
  ctx: SyncFetchContext,
  body: ResultsAcceptanceRequest,
): Promise<unknown> {
  return postSyncApiJson({
    path: RESULTS_ACCEPTANCE_PATH,
    platformLabel: '采集结果验收',
    body: {
      douyin: body.douyin,
      xhs: body.xhs,
    },
    ctx,
  })
}

/**
 * 各平台 `GET .../results` 完成后调用验收（失败不阻断写表，DEV 下打日志）。
 * 仅含已拉到条目的任务 id；三次重试仍无数据的不进入验收，不扣积分。
 */
export async function postResultsAcceptanceAfterAsyncFetch(
  ctx: SyncFetchContext,
  refs: AsyncTaskRef[],
  resultsMap: Map<string, AsyncTaskResultsBatch>,
): Promise<void> {
  const body = buildResultsAcceptanceBody(refs, resultsMap)
  if (!body.douyin.length && !body.xhs.length) return
  try {
    await postResultsAcceptance(ctx, body)
  } catch (e) {
    if (import.meta.env.DEV) {
      console.warn('[results-acceptance]', e)
    }
  }
}

/**
 * 逐条：`GET` 状态 →（`running`/`completed`，或 `pending` 且 pendingResultsDue）`GET .../results` →（可选）验收。
 */
export async function fetchAsyncTaskStatusAndResultsMaps(
  ctx: SyncFetchContext,
  taskIds: string[],
  options?: {
    refs?: AsyncTaskRef[]
    skipAcceptance?: boolean
    /** 列表已确认为 running 的子任务 id，跳过 `GET .../tasks/{id}` */
    skipStatusFetchForIds?: Iterable<string>
    /** 对应表单「选择条数」，拉 results 时翻页上限 */
    maxItemsPerTask?: number
    /** `pending` 且已过 next_run_at+3min 时拉 results（各平台子任务共用） */
    pendingResultsDue?: boolean
  },
): Promise<{
  statusMap: Map<string, AsyncTaskStatusResult>
  resultsMap: Map<string, AsyncTaskResultsBatch>
}> {
  const skipStatus = new Set(
    [...(options?.skipStatusFetchForIds ?? [])].map((x) => x.trim()).filter(Boolean),
  )
  const wanted = [...new Set(taskIds.map((x) => x.trim()).filter(Boolean))]
  const statusMap = new Map<string, AsyncTaskStatusResult>()
  const needFetch: string[] = []
  for (const id of wanted) {
    if (skipStatus.has(id)) {
      statusMap.set(id, { taskId: id, lifecycle: 'running', data: {} })
    } else {
      needFetch.push(id)
    }
  }
  if (needFetch.length) {
    const fetched = await fetchAsyncTaskStatusMap(ctx, needFetch)
    for (const [id, st] of fetched) statusMap.set(id, st)
  }
  const resultsMap = await fetchAsyncTaskResultsMap(ctx, taskIds, statusMap, {
    maxItemsPerTask: options?.maxItemsPerTask,
    pendingResultsDue: options?.pendingResultsDue,
  })
  if (!options?.skipAcceptance && options?.refs?.length) {
    await postResultsAcceptanceAfterAsyncFetch(ctx, options.refs, resultsMap)
  }
  return { statusMap, resultsMap }
}

/** `GET /api/v1/async/tasks/{task_id}/results` 解析为条目列表 */
export async function getAsyncTaskResults(
  ctx: SyncFetchContext,
  taskId: string,
): Promise<AsyncTaskResultsPayload> {
  const id = taskId.trim()
  if (!id) throw new Error('缺少 task_id')
  const batch = await fetchAllAsyncTaskResults(ctx, id)
  return {
    taskId: id,
    items: batch.items,
    meta: batch.meta,
    platform: batch.platform,
  }
}

export function isRealtimeTaskConfig(config: Record<string, unknown>): boolean {
  const tt = config.taskType ?? config.task_type
  return tt === 'realtime'
}

export type CollectionSubmitResult =
  | { mode: 'async'; refs: AsyncTaskRef[] }
  | {
      mode: 'sync'
      itemCount: number
      itemsByPlatform: SyncItemsByPlatform
      /** 按各平台实采条数折算的积分（展示用；正式扣费以 YDDM 为准） */
      pointsConsumed: number
      /** 某平台接口 200 但列表为空时的提示 */
      emptyPlatformHints?: string[]
    }

export type { SyncItemsByPlatform } from '@/lib/sync-collection-cache'

/** 将采集提交结果写入任务配置快照（保存前调用） */
export function applyCollectionResultToConfig(
  config: Record<string, unknown>,
  collection: CollectionSubmitResult,
): void {
  if (collection.mode === 'async' && collection.refs.length) {
    config.asyncTaskIds = collection.refs.map((r) => r.taskId)
    config.asyncTaskRefs = mergeAsyncTaskRefs(config, collection.refs)
    config.runStatus = 'stopped'
    return
  }
  if (collection.mode === 'sync') {
    config.runStatus = 'completed'
    clearRealtimeAsyncBindings(config)
    return
  }
  if (collection.mode === 'async') {
    config.runStatus = 'stopped'
  }
}

/**
 * 单次任务：直接调用 search-page（抖音 / 小红书同步接口）。
 * 定时任务：提交 `POST /api/v1/async/tasks`。
 */
export async function submitCollectionFromConfig(
  config: Record<string, unknown>,
  ctx: SyncFetchContext,
  options?: { taskId?: number },
): Promise<CollectionSubmitResult> {
  if (isRealtimeTaskConfig(config)) {
    const { itemCount, itemsByPlatform, emptyPlatformHints } = await runRealtimeSyncSearchFromConfig(
      config,
      ctx,
      { taskId: options?.taskId },
    )
    void refreshYddmUserBalance()
    const pointsConsumed = estimatePointsFromItemsByPlatform(itemsByPlatform)
    return { mode: 'sync', itemCount, itemsByPlatform, pointsConsumed, emptyPlatformHints }
  }
  const refs = await submitAsyncTasksFromConfig(config, ctx, {
    feishuTaskConfigId: options?.taskId,
  })
  void refreshYddmUserBalance()
  return { mode: 'async', refs }
}

/** 单次任务：拉取单个平台的 search-page 结果 */
export async function fetchRealtimePlatformSearchItems(
  platform: PlatformKey,
  config: Record<string, unknown>,
  ctx: SyncFetchContext,
): Promise<Record<string, unknown>[]> {
  if (platform === 'douyin') return fetchDouyinSearchItems(config, ctx)
  if (platform === 'xiaohongshu') return fetchXhsSearchItems(config, ctx)
  if (platform === 'shipinhao') return fetchWxvideoSearchItems(config, ctx)
  if (platform === 'gzh') return fetchGzhSearchItems(config, ctx)
  return []
}

export type RealtimePlatformCollectedHandler = (
  platform: PlatformKey,
  items: Record<string, unknown>[],
  itemsByPlatform: SyncItemsByPlatform,
) => void | Promise<void>

/** 单次任务：按勾选平台顺序依次调用对应 `search-page`（抖音 → 小红书 → 视频号 → 公众号） */
export async function runRealtimeSyncSearchFromConfig(
  config: Record<string, unknown>,
  ctx: SyncFetchContext,
  options?: { taskId?: number; onPlatformCollected?: RealtimePlatformCollectedHandler },
): Promise<{
  itemCount: number
  itemsByPlatform: SyncItemsByPlatform
  emptyPlatformHints: string[]
}> {
  const sources = readSelectedSources(config)
  if (!sources.length) {
    throw new Error('请至少选择一个采集平台')
  }

  const itemsByPlatform: SyncItemsByPlatform = {}
  const emptyPlatformHints: string[] = []
  let itemCount = 0

  const trackPlatform = (platform: PlatformKey, items: Record<string, unknown>[]) => {
    if (items.length) return
    const label = platformDisplayNames[platform] ?? platform
    emptyPlatformHints.push(
      `${label}：接口返回 0 条（请检查关键词/排除词是否过严，或账户余额是否充足）`,
    )
  }

  if (import.meta.env.DEV) {
    console.log(
      '[sync-collect] 单次任务 search-page',
      sources.map((p) => ({ platform: p, path: SYNC_SEARCH_PAGE_BY_PLATFORM[p].path })),
    )
  }

  for (const platform of sources) {
    const pathInfo = SYNC_SEARCH_PAGE_BY_PLATFORM[platform]
    if (import.meta.env.DEV) {
      console.log('[sync-collect] search-page 开始', { platform, path: pathInfo.path })
    }

    let items: Record<string, unknown>[] = []
    const platformCtx = resetPlatformSyncBillingSession(ctx)
    try {
      items = await fetchRealtimePlatformSearchItems(platform, config, platformCtx)
    } catch (e) {
      const label = platformDisplayNames[platform] ?? platform
      let msg = e instanceof Error ? e.message : String(e)
      if (isSyncHttpError(e) && e.status >= 500 && e.status < 600) {
        const pkg = syncPointsPackageForPlatform(platform)
        const pkgHint = pkg > 0 ? `，本平台约 ${pkg.toLocaleString('zh-CN')} 积分档位不扣费` : ''
        msg = `${msg}（已重试 ${SYNC_SEARCH_PAGE_MAX_ATTEMPTS} 次仍失败${pkgHint}）`
      }
      emptyPlatformHints.push(`${label}：${msg}`)
      if (import.meta.env.DEV) {
        console.warn('[sync-collect] search-page 失败', { platform, path: pathInfo.path, msg })
      }
    }
    itemsByPlatform[platform] = items
    trackPlatform(platform, items)
    itemCount += items.length

    if (import.meta.env.DEV) {
      console.log('[sync-collect] search-page 完成', {
        platform,
        path: pathInfo.path,
        count: items.length,
      })
    }

    if (options?.onPlatformCollected) {
      try {
        await options.onPlatformCollected(platform, items, itemsByPlatform)
      } catch (e) {
        const label = platformDisplayNames[platform] ?? platform
        const msg = e instanceof Error ? e.message : String(e)
        emptyPlatformHints.push(`${label} 写表：${msg}`)
        if (import.meta.env.DEV) {
          console.warn('[sync-collect] 写表失败', { platform, msg })
        }
      }
    }
  }
  if (import.meta.env.DEV) {
    console.log('[sync-collect]', {
      itemCount,
      byPlatform: {
        douyin: itemsByPlatform.douyin?.length ?? 0,
        xiaohongshu: itemsByPlatform.xiaohongshu?.length ?? 0,
        shipinhao: itemsByPlatform.shipinhao?.length ?? 0,
        gzh: itemsByPlatform.gzh?.length ?? 0,
      },
      samples: {
        douyin: itemsByPlatform.douyin?.[0],
        xiaohongshu: itemsByPlatform.xiaohongshu?.[0],
      },
    })
  }
  if (options?.taskId != null) {
    setSyncCollectionCache(options.taskId, itemsByPlatform)
  }
  return { itemCount, itemsByPlatform, emptyPlatformHints }
}

/** 定时任务：按已选平台 × 关键词各提交一条异步任务 */
export async function submitAsyncTasksFromConfig(
  config: Record<string, unknown>,
  ctx: SyncFetchContext,
  options?: { feishuTaskConfigId?: number },
): Promise<AsyncTaskRef[]> {
  const keywords = readSearchKeywords(config)

  const sources = readSelectedSources(config)
  if (!sources.length) {
    throw new Error('请至少选择一个采集平台')
  }

  const existingBySlot = new Map<string, AsyncTaskRef>()
  for (const ref of readAsyncTaskRefs(config)) {
    existingBySlot.set(asyncRefSlotKey(ref.platform, ref.keyword), ref)
  }

  const bySlot = new Map<string, AsyncTaskRef>()
  for (const platform of sources) {
    for (const keyword of keywords) {
      const slot = asyncRefSlotKey(platform, keyword)
      const existing = existingBySlot.get(slot)

      if (existing?.taskId.trim()) {
        const existingNum = Math.floor(Number(existing.taskId))
        const isDraftRef = !Number.isFinite(existingNum) || existingNum >= 1_000_000_000_000
        if (!isDraftRef) {
          try {
            const status = await getAsyncTaskStatus(ctx, existing.taskId)
            if (isReuseableAsyncTaskLifecycle(status.lifecycle)) {
              bySlot.set(slot, existing)
              if (import.meta.env.DEV) {
                console.log('[async-task] 复用已有子任务', {
                  platform,
                  keyword: keyword || '(空)',
                  taskId: existing.taskId,
                  lifecycle: status.lifecycle,
                })
              }
              continue
            }
          } catch {
            /* 查询失败则重新提交 */
          }
        }
      }

      await ensureSyncEndpointDiscountForPlatform(platform, ctx)
      const req = buildAsyncTaskSubmitRequest(platform, config, keyword)
      if (import.meta.env.DEV) {
        console.log('[async-task] POST /api/v1/async/tasks', {
          platform,
          keyword: keyword || '(空)',
          action: req.action,
          task_name: req.task_name,
          task_start_time: req.task_start_time,
          task_end_time: req.task_end_time,
          interval_minutes: req.interval_minutes,
          fetch_count: req.fetch_count,
          body: req.body,
        })
      }
      const submitBody: AsyncTaskSubmitRequest & Record<string, unknown> = { ...req }
      if (options?.feishuTaskConfigId != null) {
        submitBody.feishu_task_config_id = options.feishuTaskConfigId
      }
      const parsed = await postAsyncTask(ctx, submitBody)
      const tid = extractAsyncTaskId(parsed)?.trim()
      if (!tid) continue

      const ref: AsyncTaskRef = { taskId: tid, platform, keyword }
      if (existing?.taskId.trim() === tid) {
        bySlot.set(slot, existing)
      } else {
        bySlot.set(slot, ref)
      }
    }
  }
  return [...bySlot.values()]
}

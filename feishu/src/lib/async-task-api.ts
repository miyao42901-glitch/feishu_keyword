/**
 * 异步采集任务：
 * - `POST /api/v1/async/tasks` 提交
 * - `GET /api/v1/async/tasks/{task_id}` 查询状态
 * - `GET /api/v1/async/tasks/{task_id}/results` 查询结果
 */

import type { PlatformKey } from '@/components/PlatformIcon.vue'
import { extractSyncResultItems, type SyncFetchContext } from '@/lib/sync-api-common'
import { buildDouyinSearchPageBody } from '@/lib/sync-search-page'
import {
  getSyncApiJson,
  postSyncApiJson,
  readDataRange,
  readSearchKeywords,
} from '@/lib/sync-search-shared'
import { fetchDouyinSearchItems } from '@/lib/douyin-sync-api'
import { refreshYddmUserBalance } from '@/lib/refresh-yddm-balance'
import { ensureSyncEndpointDiscountForPlatform } from '@/lib/sync-set-discount'
import { fetchXhsSearchItems } from '@/lib/xhs-sync-api'
import { buildXhsSearchPageBody } from '@/lib/xhs-sync-api'

const ASYNC_TASK_PATH = '/api/v1/async/tasks'

const ACTION_BY_PLATFORM: Partial<Record<PlatformKey, string>> = {
  douyin:
    (import.meta.env.VITE_ASYNC_TASK_ACTION_DOUYIN as string | undefined)?.trim() ||
    'douyin.search_page',
  xiaohongshu:
    (import.meta.env.VITE_ASYNC_TASK_ACTION_XHS as string | undefined)?.trim() ||
    'xhs.search_page',
}

/** Apifox：`body` 至少含 `keyword`，其余与 search-page 对齐 */
export type AsyncTaskBody = {
  keyword: string
  [property: string]: unknown
}

/** Apifox 提交异步任务入参 */
export type AsyncTaskSubmitRequest = {
  action: string
  body: AsyncTaskBody
  [property: string]: unknown
}

/** 路径参数 `task_id` */
export type AsyncTaskStatusPath = {
  task_id: string
  [property: string]: unknown
}

/** 查询状态解析后的业务态 */
export type AsyncTaskLifecycle = 'pending' | 'running' | 'completed' | 'failed' | 'unknown'

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

export type AsyncTaskResultsPayload = {
  taskId: string
  items: Record<string, unknown>[]
}

function readSelectedSources(config: Record<string, unknown>): PlatformKey[] {
  const raw = config.selectedSources ?? config.selected_sources
  if (!Array.isArray(raw)) return []
  const out: PlatformKey[] = []
  for (const x of raw) {
    if (typeof x !== 'string') continue
    const s = x.trim()
    if (s === 'douyin' || s === 'xiaohongshu') out.push(s)
  }
  return out
}

function withDataRange(body: AsyncTaskBody, config: Record<string, unknown>): AsyncTaskBody {
  const range = readDataRange(config)
  return { ...body, data_range: range, count: range }
}

function buildDouyinAsyncTaskBody(
  config: Record<string, unknown>,
  keyword: string,
): AsyncTaskBody {
  const full = buildDouyinSearchPageBody(config, keyword)
  const { cursor: _c, log_id: _l, ...rest } = full
  return withDataRange(rest as AsyncTaskBody, config)
}

function buildXhsAsyncTaskBody(config: Record<string, unknown>, keyword: string): AsyncTaskBody {
  const full = buildXhsSearchPageBody(config, keyword, 1)
  const { page: _p, ...rest } = full
  return withDataRange(rest as AsyncTaskBody, config)
}

/** 从提交/查询响应中提取 `task_id` */
export function extractAsyncTaskId(payload: unknown): string | null {
  if (!payload || typeof payload !== 'object') return null
  const visit = (node: unknown, depth: number): string | null => {
    if (depth > 6 || !node || typeof node !== 'object') return null
    const r = node as Record<string, unknown>
    const tid = r.task_id ?? r.taskId
    if (typeof tid === 'string' && tid.trim()) return tid.trim()
    if (typeof tid === 'number' && Number.isFinite(tid)) return String(tid)
    for (const key of ['data', 'result']) {
      const found = visit(r[key], depth + 1)
      if (found) return found
    }
    return null
  }
  return visit(payload, 0)
}

const RUNNING_STATUSES = new Set([
  'pending',
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

/** 解析 `GET /api/v1/async/tasks/{task_id}` 响应 */
export function parseAsyncTaskStatusResponse(
  payload: unknown,
  taskId: string,
): AsyncTaskStatusResult {
  const id = extractAsyncTaskId(payload) ?? taskId.trim()
  let data: Record<string, unknown> = {}
  if (payload && typeof payload === 'object') {
    const root = payload as Record<string, unknown>
    const inner = root.data
    if (inner && typeof inner === 'object' && !Array.isArray(inner)) {
      data = inner as Record<string, unknown>
    } else {
      data = root
    }
  }
  const lifecycle = normalizeLifecycle(pickStatusField(data) ?? pickStatusField(payload as Record<string, unknown>))
  return { taskId: id, lifecycle, data }
}

/** 从 results 响应中提取条目列表（兼容 search-page 与多种 `data` 形态） */
export function extractAsyncTaskResultItems(payload: unknown): Record<string, unknown>[] {
  const fromSync = extractSyncResultItems(payload)
  if (fromSync.length) return fromSync
  if (!payload || typeof payload !== 'object') return []

  const tryArray = (v: unknown): Record<string, unknown>[] => {
    if (!Array.isArray(v)) return []
    return v.filter((x): x is Record<string, unknown> => x != null && typeof x === 'object')
  }

  const root = payload as Record<string, unknown>
  const data = root.data
  if (Array.isArray(data)) return tryArray(data)
  if (data && typeof data === 'object' && !Array.isArray(data)) {
    const d = data as Record<string, unknown>
    for (const key of ['items', 'results', 'list', 'records', 'rows']) {
      const hit = tryArray(d[key])
      if (hit.length) return hit
    }
    const result = d.result
    if (result && typeof result === 'object') {
      const hit = tryArray((result as Record<string, unknown>).data)
      if (hit.length) return hit
    }
  }
  return tryArray(root.items ?? root.results ?? root.list)
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

export function readAsyncTaskRefs(config: Record<string, unknown>): AsyncTaskRef[] {
  const raw = config.asyncTaskRefs ?? config.async_task_refs
  if (!Array.isArray(raw)) return []
  const out: AsyncTaskRef[] = []
  for (const x of raw) {
    if (!x || typeof x !== 'object') continue
    const r = x as Record<string, unknown>
    const taskId = String(r.taskId ?? r.task_id ?? '').trim()
    const platform = String(r.platform ?? '').trim()
    if (!taskId || (platform !== 'douyin' && platform !== 'xiaohongshu')) continue
    out.push({
      taskId,
      platform,
      keyword: String(r.keyword ?? '').trim(),
    })
  }
  const byId = new Map<string, AsyncTaskRef>()
  for (const ref of out) byId.set(ref.taskId, ref)
  return [...byId.values()]
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
  const byId = new Map<string, AsyncTaskRef>()
  for (const ref of [...readAsyncTaskRefs(config), ...incoming]) {
    if (ref.taskId.trim()) byId.set(ref.taskId.trim(), ref)
  }
  return [...byId.values()]
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

/** `GET /api/v1/async/tasks/{task_id}`，Header 含 `x-api-key` */
export async function getAsyncTaskStatus(
  ctx: SyncFetchContext,
  taskId: string,
): Promise<AsyncTaskStatusResult> {
  const id = taskId.trim()
  if (!id) throw new Error('缺少 task_id')
  const parsed = await getSyncApiJson({
    path: `${ASYNC_TASK_PATH}/${encodeURIComponent(id)}`,
    platformLabel: '异步任务状态',
    ctx,
  })
  return parseAsyncTaskStatusResponse(parsed, id)
}

/** `GET /api/v1/async/tasks/{task_id}/results` */
export async function getAsyncTaskResults(
  ctx: SyncFetchContext,
  taskId: string,
): Promise<AsyncTaskResultsPayload> {
  const id = taskId.trim()
  if (!id) throw new Error('缺少 task_id')
  const parsed = await getSyncApiJson({
    path: `${ASYNC_TASK_PATH}/${encodeURIComponent(id)}/results`,
    platformLabel: '异步任务结果',
    ctx,
  })
  return {
    taskId: extractAsyncTaskId(parsed) ?? id,
    items: extractAsyncTaskResultItems(parsed),
  }
}

export function isRealtimeTaskConfig(config: Record<string, unknown>): boolean {
  const tt = config.taskType ?? config.task_type
  return tt === 'realtime'
}

export type CollectionSubmitResult =
  | { mode: 'async'; refs: AsyncTaskRef[] }
  | { mode: 'sync'; itemCount: number }

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
    config.asyncTaskIds = []
    config.asyncTaskRefs = []
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
): Promise<CollectionSubmitResult> {
  if (isRealtimeTaskConfig(config)) {
    const itemCount = await runRealtimeSyncSearchFromConfig(config, ctx)
    void refreshYddmUserBalance()
    return { mode: 'sync', itemCount }
  }
  const refs = await submitAsyncTasksFromConfig(config, ctx)
  void refreshYddmUserBalance()
  return { mode: 'async', refs }
}

/** 单次任务：按平台调用 `/api/v1/sync/douyin/search-page`、`/api/v1/sync/xhs/search-page` */
export async function runRealtimeSyncSearchFromConfig(
  config: Record<string, unknown>,
  ctx: SyncFetchContext,
): Promise<number> {
  const sources = readSelectedSources(config)
  if (!sources.length) {
    throw new Error('请至少选择一个采集平台')
  }

  let itemCount = 0
  if (sources.includes('douyin')) {
    itemCount += (await fetchDouyinSearchItems(config, ctx)).length
  }
  if (sources.includes('xiaohongshu')) {
    itemCount += (await fetchXhsSearchItems(config, ctx)).length
  }
  return itemCount
}

/** 定时任务：按已选平台 × 关键词各提交一条异步任务 */
export async function submitAsyncTasksFromConfig(
  config: Record<string, unknown>,
  ctx: SyncFetchContext,
): Promise<AsyncTaskRef[]> {
  const keywords = readSearchKeywords(config)

  const sources = readSelectedSources(config)
  if (!sources.length) {
    throw new Error('请至少选择一个采集平台')
  }

  const refs: AsyncTaskRef[] = []
  for (const platform of sources) {
    const action = ACTION_BY_PLATFORM[platform]?.trim()
    if (!action) continue
    for (const keyword of keywords) {
      await ensureSyncEndpointDiscountForPlatform(
        platform as 'douyin' | 'xiaohongshu',
        ctx,
      )
      const body =
        platform === 'douyin'
          ? buildDouyinAsyncTaskBody(config, keyword)
          : buildXhsAsyncTaskBody(config, keyword)
      const parsed = await postAsyncTask(ctx, { action, body })
      const tid = extractAsyncTaskId(parsed)
      if (tid) refs.push({ taskId: tid, platform, keyword })
    }
  }
  const byId = new Map<string, AsyncTaskRef>()
  for (const ref of refs) byId.set(ref.taskId, ref)
  return [...byId.values()]
}

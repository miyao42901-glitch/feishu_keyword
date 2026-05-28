<script setup lang="ts">
import { ArrowLeft, ArrowRight, Plus } from '@element-plus/icons-vue'
import { computed, onMounted, onScopeDispose, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { storeToRefs } from 'pinia'
import TaskCreateForm from '@/views/TaskCreateForm/index.vue'
import TaskDetailDialog from '@/views/tasks/components/TaskDetailDialog.vue'
import TaskListCard from '@/views/tasks/components/TaskListCard.vue'
import type { TaskCardModel, TaskStoppedKind } from '@/views/tasks/types'
import type { TaskRunStatus } from '@/views/TaskCreateForm/types'
import {
  parseBackendDisplayStatus,
  parseBackendStoppedKind,
  type FeishuTaskConfigDetail,
  type FeishuTaskConfigWriteResult,
} from '@/lib/api'
import {
  applyTaskTypeFromListCard,
  loadTaskConfigDetail,
  loadTaskConfigForExecution,
  persistCollectionRefsToLocal,
  resolveFeedConfigForListCard,
  saveTaskConfigPatch,
} from '@/lib/feishu-async-task-config'
import { isLocalDraftTaskId, loadLocalTaskConfig } from '@/lib/feishu-task-config-local'
import {
  appendTestFeedRowsToBitable,
  clearTestFeedAppendStateForTask,
  countRowsPendingBitableAppend,
  ensureBitableTablesForTask,
  pruneTestFeedAppendState,
} from '@/lib/feishu-bitable-append-feed'
import { createTestFeedBitableDeps, syncTaskCollectionToBitable } from '@/lib/feishu-bitable-task-sync'
import { readSyncCollectionPlatforms } from '@/lib/sync-collection-platforms'
import {
  applyCollectionResultToConfig,
  deleteAsyncTask,
  isPendingAsyncResultsDue,
  isRealtimeTaskConfig,
  resetAsyncTaskLifecycleCache,
  submitCollectionFromConfig,
  type AsyncTaskStatusResult,
} from '@/lib/async-task-api'
import { buildCollectionFetchContext } from '@/lib/collection-context'
import { readCrawlPollIntervalMs } from '@/lib/feishu-webhook-notify'
import {
  isScheduledFeedPollDue,
  msUntilNextScheduledRunPoll,
  scheduledRunPolledMarkThrough,
} from '@/lib/datetime-task-window'
import {
  notifyWebhookAfterScheduledPoll,
  notifyWebhookCollectionRunFailed,
  prepareTaskWebhookForNewRun,
} from '@/lib/feishu-webhook-task-triggers'
import {
  listTaskCardsFromAsync,
  matchesAsyncListFilter,
  taskStatsFromAsyncSummary,
} from '@/lib/feishu-task-list-api'
import type { AsyncTaskListSummary } from '@/lib/async-task-api'
import { refreshYddmUserBalance } from '@/lib/refresh-yddm-balance'
import { buildTestDataFeedFromConfig, taskUsesOnlyTestDataPlatforms, type TestFeedRow } from '@/lib/test-data-feed'
import { useGlobalSettingsStore } from '@/stores/globalSettings'

/** 任务列表空态图（`public/images/task-list/empty.png`） */
const taskListEmptyImgSrc = `${import.meta.env.BASE_URL}images/task-list/empty.png`

const tasks = ref<TaskCardModel[]>([])
/** `GET /api/v1/async/tasks` 的 `data.result.summary`（顶部统计优先用此） */
const asyncListSummary = ref<AsyncTaskListSummary | null>(null)
/** 列表每页条数 */
const pageSize = ref(10)
const listCurrentPage = ref(1)
const screen = ref<'list' | 'create'>('list')
const editingTaskId = ref<number | null>(null)
/** 编辑态 YDDM 任务状态（决定 edit 接口是否可改调度字段） */
const editingTaskStatus = ref<TaskRunStatus | null>(null)
const taskDetail = ref<FeishuTaskConfigDetail | null>(null)

const globalSettings = useGlobalSettingsStore()
const { authCode } = storeToRefs(globalSettings)

/** 运行中且仅抖音/小红书：按 test_data 与任务配置写入飞书表并更新条数统计 */
let testFeedDebounce: ReturnType<typeof setTimeout> | null = null
/** 运行中任务按采集频率调度下一次同步（列表页） */
let testFeedPollTimeout: ReturnType<typeof setTimeout> | null = null
/** 列表 `GET /api/v1/async/tasks` 定时轮询（与后端 `ASYNC_DISPATCH_POLL_SECONDS` 默认 15s 对齐） */
const ASYNC_TASK_LIST_POLL_RUNNING_MS = 30_000
const ASYNC_TASK_LIST_POLL_PENDING_MS = 15_000
const ASYNC_TASK_LIST_POLL_PENDING_MIN_MS = 5_000
/** force 刷新最短间隔；定时轮询走 `listPollIntervalMs()` 不受此限制 */
const ASYNC_TASK_LIST_MIN_FETCH_MS = 15_000
let lastTaskListFetchedAt = 0
let listSyncBlockedUntil = 0
let lastListSyncErrorToastAt = 0
let taskListPollInterval: ReturnType<typeof setInterval> | null = null
/** 当前列表轮询定时器周期（仅当周期变化时才重置定时器） */
let activeListPollIntervalMs = 0
let taskListLoadInFlight: Promise<void> | null = null
let asyncListSyncInFlight: Promise<void> | null = null
/** 列表请求进行中再次要求刷新（如切换统计筛选）时，完成后补拉一次 */
let listRefetchQueued = false
/** 避免同一任务并发执行两次同步 */
const testFeedSyncInFlight = new Set<number>()
/** 单次任务：上次拉取时刻（按采集频率节流） */
const lastRealtimeFeedPollAtByTaskId = new Map<number, number>()
/** 定时任务：已拉取到的最大采集时刻（对齐 14:29 / 14:34 …） */
const lastScheduledRunPolledAtByTaskId = new Map<number, number>()
/** 轮询用任务配置缓存（含开始/结束/频率） */
const feedPollConfigByTaskId = new Map<number, Record<string, unknown>>()

const testFeedBitableDeps = createTestFeedBitableDeps()

/** 仅 `running` 卡片拉 results 的最小间隔 */
const RUNNING_FEED_POLL_MS = 120_000
let syncPollTimerDebounce: ReturnType<typeof setTimeout> | null = null
let refreshTestDataFeedInFlight: Promise<void> | null = null
let runningFeedWatchDebounce: ReturnType<typeof setTimeout> | null = null

/** 定时任务 pending_run：各平台在 next_run_at+3min 拉 `GET .../results` */
function isPendingTaskResultsDue(row: TaskCardModel, now = Date.now()): boolean {
  if (row.status !== 'pending_run' || row.taskTypeLabel === '单次任务') return false
  return isPendingAsyncResultsDue(row.nextRunAtRaw, now)
}

function listRunningFeedTargets(): TaskCardModel[] {
  return tasks.value.filter(
    (t) =>
      (t.status === 'running' || t.status === 'pending_run') &&
      taskUsesOnlyTestDataPlatforms(t.platformKeys),
  )
}

function listActiveRunningFeedTargets(): TaskCardModel[] {
  const now = Date.now()
  return tasks.value.filter(
    (t) =>
      t.taskTypeLabel !== '单次任务' &&
      taskUsesOnlyTestDataPlatforms(t.platformKeys) &&
      (t.status === 'running' || isPendingTaskResultsDue(t, now)),
  )
}

function pruneFeedPollState(runningIds: Set<number>): void {
  for (const id of [...lastRealtimeFeedPollAtByTaskId.keys()]) {
    if (!runningIds.has(id)) lastRealtimeFeedPollAtByTaskId.delete(id)
  }
  for (const id of [...lastScheduledRunPolledAtByTaskId.keys()]) {
    if (!runningIds.has(id)) lastScheduledRunPolledAtByTaskId.delete(id)
  }
  for (const id of [...feedPollConfigByTaskId.keys()]) {
    if (!runningIds.has(id)) feedPollConfigByTaskId.delete(id)
  }
}

function readScheduleFields(cfg: Record<string, unknown>) {
  return {
    effectiveAt: cfg.effectiveAt ?? cfg.effective_at,
    expireAt: cfg.expireAt ?? cfg.expire_at,
    intervalMinutes: cfg.crawlFrequency ?? cfg.crawl_frequency ?? cfg.interval_minutes,
  }
}

function computeMsUntilNextFeedPoll(): number {
  const targets = listActiveRunningFeedTargets()
  if (!targets.length) return 10 * 60_000

  const now = Date.now()
  let minWait = Number.POSITIVE_INFINITY
  for (const t of targets) {
    if (t.status === 'pending_run') {
      minWait = Math.min(minWait, 0)
      continue
    }
    if (t.status === 'running') {
      const last =
        lastRealtimeFeedPollAtByTaskId.get(t.id) ?? lastScheduledRunPolledAtByTaskId.get(t.id)
      if (last == null) minWait = Math.min(minWait, 0)
      else minWait = Math.min(minWait, Math.max(0, RUNNING_FEED_POLL_MS - (now - last)))
    }
    const cfg = feedPollConfigByTaskId.get(t.id)
    if (!cfg) {
      minWait = Math.min(minWait, 0)
      continue
    }
    if (isRealtimeTaskConfig(cfg)) {
      const interval = readCrawlPollIntervalMs(cfg)
      const last = lastRealtimeFeedPollAtByTaskId.get(t.id)
      if (last == null) minWait = Math.min(minWait, 0)
      else minWait = Math.min(minWait, Math.max(0, interval - (now - last)))
      continue
    }
    const { effectiveAt, expireAt, intervalMinutes } = readScheduleFields(cfg)
    const ms = msUntilNextScheduledRunPoll(
      effectiveAt,
      expireAt,
      intervalMinutes,
      lastScheduledRunPolledAtByTaskId.get(t.id),
      now,
    )
    if (ms === 0) minWait = 0
    else if (ms != null) minWait = Math.min(minWait, ms)
    else minWait = Math.min(minWait, 60_000)
  }
  if (!Number.isFinite(minWait)) return 10 * 60_000
  return Math.max(minWait, 1_000)
}

function isFeedPollDueForTask(t: TaskCardModel, cfg: Record<string, unknown>, now: number): boolean {
  if (t.status === 'pending_run') return isPendingTaskResultsDue(t, now)
  if (t.status === 'running') {
    const last =
      lastRealtimeFeedPollAtByTaskId.get(t.id) ?? lastScheduledRunPolledAtByTaskId.get(t.id)
    return last == null || now - last >= RUNNING_FEED_POLL_MS
  }
  if (isRealtimeTaskConfig(cfg)) {
    const interval = readCrawlPollIntervalMs(cfg)
    const last = lastRealtimeFeedPollAtByTaskId.get(t.id)
    return last == null || now - last >= interval
  }
  const { effectiveAt, expireAt, intervalMinutes } = readScheduleFields(cfg)
  return isScheduledFeedPollDue(
    effectiveAt,
    expireAt,
    intervalMinutes,
    lastScheduledRunPolledAtByTaskId.get(t.id),
    now,
  )
}

function markTaskFeedPolled(taskId: number, cfg: Record<string, unknown>, cardStatus?: TaskRunStatus): void {
  const now = Date.now()
  if (cardStatus === 'running') {
    lastRealtimeFeedPollAtByTaskId.set(taskId, now)
    return
  }
  if (isRealtimeTaskConfig(cfg)) {
    lastRealtimeFeedPollAtByTaskId.set(taskId, now)
    return
  }
  const { effectiveAt, expireAt, intervalMinutes } = readScheduleFields(cfg)
  lastScheduledRunPolledAtByTaskId.set(
    taskId,
    scheduledRunPolledMarkThrough(effectiveAt, expireAt, intervalMinutes, now),
  )
}

/** 预读运行中任务配置（不 `GET /async/tasks/{id}`，避免多平台每条卡片打详情） */
async function bootstrapFeedPollConfigForRunningTasks(): Promise<void> {
  const running = listActiveRunningFeedTargets()
  const pending = running.filter((t) => !feedPollConfigByTaskId.has(t.id))
  if (!pending.length) return

  await Promise.all(
    pending.map(async (t) => {
      try {
        const cfg = await resolveFeedConfigForListCard(t, undefined, { pollMode: true })
        feedPollConfigByTaskId.set(t.id, cfg)
      } catch {
        feedPollConfigByTaskId.set(t.id, {})
      }
    }),
  )
}

async function resolveFeedConfigForPoll(t: TaskCardModel): Promise<Record<string, unknown>> {
  const cached = feedPollConfigByTaskId.get(t.id)
  if (cached) return cached
  const cfg = await resolveFeedConfigForListCard(t, undefined, { pollMode: true })
  feedPollConfigByTaskId.set(t.id, cfg)
  return cfg
}

function clearTestFeedPollTimeout(): void {
  if (testFeedPollTimeout != null) {
    clearTimeout(testFeedPollTimeout)
    testFeedPollTimeout = null
  }
}

function scheduleNextTestFeedPoll(): void {
  clearTestFeedPollTimeout()
  const want =
    screen.value === 'list' &&
    authCode.value.trim() &&
    listActiveRunningFeedTargets().length > 0
  if (!want) return

  const delay = computeMsUntilNextFeedPoll()
  testFeedPollTimeout = setTimeout(() => {
    testFeedPollTimeout = null
    void refreshTestDataFeed().finally(() => scheduleNextTestFeedPoll())
  }, delay)
}

/** 存在未结束活动任务时需定时拉列表（含 summary.pending，避免筛选「已完成」后停轮询） */
function shouldPollAsyncTaskList(): boolean {
  const s = asyncListSummary.value
  if (s && (s.pending > 0 || s.running > 0 || s.active > 0)) return true
  return tasks.value.some((t) => t.status === 'running' || t.status === 'pending_run')
}

function listPollIntervalMs(): number {
  if (tasks.value.some((t) => t.status === 'running')) return ASYNC_TASK_LIST_POLL_RUNNING_MS
  const pendingCards = tasks.value.filter((t) => t.status === 'pending_run')
  if (pendingCards.length) {
    const now = Date.now()
    let wait = ASYNC_TASK_LIST_POLL_PENDING_MS
    for (const t of pendingCards) {
      const raw = t.nextRunAtRaw
      if (!raw) continue
      const due = Date.parse(raw.replace(' ', 'T'))
      if (!Number.isFinite(due)) continue
      const delta = due - now
      if (delta <= 0) wait = Math.min(wait, ASYNC_TASK_LIST_POLL_PENDING_MIN_MS)
      else wait = Math.min(wait, Math.max(ASYNC_TASK_LIST_POLL_PENDING_MIN_MS, delta + 2_000))
    }
    return wait
  }
  if ((asyncListSummary.value?.pending ?? 0) > 0) return ASYNC_TASK_LIST_POLL_PENDING_MS
  return ASYNC_TASK_LIST_POLL_PENDING_MS
}

function stopActiveTaskListPolling(): void {
  if (taskListPollInterval != null) {
    clearInterval(taskListPollInterval)
    taskListPollInterval = null
  }
  activeListPollIntervalMs = 0
}

/** 列表页定时拉取任务列表（单定时器；周期不变时不重置，避免连发 `GET /async/tasks`） */
function ensureActiveTaskListPolling(): void {
  if (screen.value !== 'list' || !authCode.value.trim() || !shouldPollAsyncTaskList()) {
    stopActiveTaskListPolling()
    return
  }
  const delay = listPollIntervalMs()
  if (taskListPollInterval != null && activeListPollIntervalMs === delay) return

  stopActiveTaskListPolling()
  activeListPollIntervalMs = delay
  taskListPollInterval = setInterval(() => {
    if (screen.value !== 'list' || !authCode.value.trim() || !shouldPollAsyncTaskList()) {
      stopActiveTaskListPolling()
      return
    }
    void loadTaskList()
  }, delay)
}

function syncTestFeedPollTimerInner() {
  const activeRunning = listActiveRunningFeedTargets()
  const scopeIds = new Set([
    ...activeRunning.map((t) => t.id),
    ...listRunningFeedTargets().map((t) => t.id),
  ])
  pruneFeedPollState(scopeIds)
  ensureActiveTaskListPolling()
  if (screen.value === 'list' && authCode.value.trim() && activeRunning.length) {
    void bootstrapFeedPollConfigForRunningTasks()
    scheduleNextTestFeedPoll()
    return
  }
  clearTestFeedPollTimeout()
}

/** 防抖：避免列表刷新 / watch 连续触发多轮 `GET /async/tasks` 与详情 */
function syncTestFeedPollTimer() {
  if (syncPollTimerDebounce != null) clearTimeout(syncPollTimerDebounce)
  syncPollTimerDebounce = setTimeout(() => {
    syncPollTimerDebounce = null
    syncTestFeedPollTimerInner()
  }, 1500)
}

function syncDetailDialogRowFromList() {
  if (!detailDialogVisible.value || !detailDialogRow.value) return
  const next = tasks.value.find((t) => t.id === detailDialogRow.value!.id)
  if (next) detailDialogRow.value = next
}

type RefreshTestDataFeedOptions = { /** 忽略采集频率节流（保存/执行后立即同步） */ forceAll?: boolean }

async function refreshTestDataFeed(options?: RefreshTestDataFeedOptions) {
  if (screen.value !== 'list') return
  if (refreshTestDataFeedInFlight) return refreshTestDataFeedInFlight

  refreshTestDataFeedInFlight = refreshTestDataFeedInner(options).finally(() => {
    refreshTestDataFeedInFlight = null
  })
  return refreshTestDataFeedInFlight
}

async function refreshTestDataFeedInner(options?: RefreshTestDataFeedOptions) {
  if (screen.value !== 'list') return
  const scopeTargets = listRunningFeedTargets()
  /** `running` 立即拉 results；`pending_run` 在 next_run_at+3min 且 YDDM 为 pending 时拉 results */
  const resultsTargets = listActiveRunningFeedTargets()
  pruneTestFeedAppendState(new Set(scopeTargets.map((t) => t.id)))
  pruneFeedPollState(new Set(scopeTargets.map((t) => t.id)))

  const now = Date.now()
  const targets = options?.forceAll
    ? resultsTargets
    : resultsTargets.filter((t) => {
        const cfg = feedPollConfigByTaskId.get(t.id)
        if (!cfg) return true
        return isFeedPollDueForTask(t, cfg, now)
      })

  if (!scopeTargets.length) {
    if (tasks.value.some((c) => c.status === 'running' && c.notificationCount !== 0)) {
      tasks.value = tasks.value.map((c) =>
        c.status === 'running' && c.notificationCount !== 0 ? { ...c, notificationCount: 0 } : c,
      )
    }
    syncTestFeedPollTimer()
    return
  }

  if (!targets.length) {
    syncTestFeedPollTimer()
    return
  }

  const targetIds = targets.map((t) => t.id)
  if (targetIds.some((id) => testFeedSyncInFlight.has(id))) {
    syncTestFeedPollTimer()
    return
  }
  for (const id of targetIds) testFeedSyncInFlight.add(id)

  const configByTaskId = new Map<number, Record<string, unknown>>()
  try {
    const syncCtx = await buildCollectionFetchContext()
    const counts = new Map<number, number>()
    const feedMetaByTaskId = new Map<
      number,
      {
        taskName: string
        config: Record<string, unknown>
        maxCollectedAtMs: number
        pendingRowCount: number
        asyncStatusMap?: Map<string, AsyncTaskStatusResult>
      }
    >()
    const rows: TestFeedRow[] = []
    for (const t of targets) {
      try {
        const cfg = await resolveFeedConfigForPoll(t)
        if (isRealtimeTaskConfig(cfg)) continue
        configByTaskId.set(t.id, cfg)
        const pendingResultsDue = isPendingTaskResultsDue(t, now)
        const feed = await buildTestDataFeedFromConfig({
          taskId: t.id,
          taskName: t.name,
          config: cfg,
          sync: syncCtx,
          card: t,
          pendingResultsDue,
          skipStatusFetchForTaskIds:
            t.status === 'running' ? [String(t.id)] : undefined,
        })
        counts.set(t.id, feed.rows.length)
        const maxCollected = feed.rows.reduce((m, r) => Math.max(m, r.collectedAtMs), 0)
        const tableMode = cfg.tableMode ?? cfg.table_mode
        const platformsForTables = [
          ...new Set([
            ...readSyncCollectionPlatforms(cfg),
            ...(feed.resultPlatforms ?? []),
          ]),
        ]
        if (tableMode === 'new' && platformsForTables.length) {
          try {
            await ensureBitableTablesForTask(t.id, cfg, testFeedBitableDeps, {
              platforms: platformsForTables,
            })
            configByTaskId.set(t.id, cfg)
          } catch (tableErr) {
            if (import.meta.env.DEV) {
              console.warn('[feed-poll] ensureBitableTablesForTask', tableErr)
            }
          }
        }
        feedMetaByTaskId.set(t.id, {
          taskName: t.name,
          config: cfg,
          maxCollectedAtMs: maxCollected,
          pendingRowCount: countRowsPendingBitableAppend(feed.rows),
          asyncStatusMap: feed.asyncStatusMap,
        })
        rows.push(...feed.rows)
      } catch (feedErr) {
        const failCfg = configByTaskId.get(t.id) ?? {}
        void notifyWebhookCollectionRunFailed({
          taskId: t.id,
          taskName: t.name,
          config: failCfg,
          message: feedErr instanceof Error ? feedErr.message : '拉取采集数据失败',
        })
      }
    }
    const displayRows: TestFeedRow[] = []
    const rowsByTask = new Map<number, TestFeedRow[]>()
    for (const r of rows) {
      const list = rowsByTask.get(r.taskId) ?? []
      list.push(r)
      rowsByTask.set(r.taskId, list)
    }
    for (const list of rowsByTask.values()) {
      list.sort((a, b) => b.publishMs - a.publishMs)
      displayRows.push(...list)
    }

    let writtenByTask = new Map<number, number>()
    try {
      writtenByTask = await appendTestFeedRowsToBitable(
        displayRows,
        configByTaskId,
        testFeedBitableDeps,
      )
    } catch {
      /* 非插件环境或表结构不匹配时静默失败 */
    }

    for (const [taskId, meta] of feedMetaByTaskId) {
      if (isRealtimeTaskConfig(meta.config)) continue
      const totalRowCount = counts.get(taskId) ?? 0
      const writtenRowCount = writtenByTask.get(taskId) ?? 0
      void notifyWebhookAfterScheduledPoll({
        taskId,
        taskName: meta.taskName,
        config: meta.config,
        writtenRowCount: writtenRowCount > 0 ? writtenRowCount : meta.pendingRowCount,
        totalRowCount,
        sync: syncCtx,
        asyncStatusMap: meta.asyncStatusMap,
      })
    }

    tasks.value = tasks.value.map((c) => {
      if (c.status !== 'running') return c
      const written = writtenByTask.get(c.id) ?? 0
      if (written === 0) return c.notificationCount === 0 ? c : { ...c, notificationCount: 0 }
      return { ...c, notificationCount: written }
    })

    let completedAny = false
    for (const t of targets) {
      const cfg = configByTaskId.get(t.id)
      if (!cfg || !isRealtimeTaskConfig(cfg)) continue
      try {
        const wr = await patchTaskConfig(t.id, { runStatus: 'completed' })
        applyDisplayFromWrite(t.id, wr)
        completedAny = true
      } catch {
        /* 标记完成失败时保持运行中，下次轮询可重试 */
      }
    }
    if (completedAny) {
      await loadTaskList({ force: true, bypassMinGap: true })
      syncTestFeedPollTimer()
    }
  } finally {
    for (const id of targetIds) {
      testFeedSyncInFlight.delete(id)
      const cfg = configByTaskId.get(id) ?? feedPollConfigByTaskId.get(id)
      const card = tasks.value.find((t) => t.id === id)
      if (cfg) markTaskFeedPolled(id, cfg, card?.status)
    }
    if (targetIds.length) void refreshYddmUserBalance()
    syncTestFeedPollTimer()
  }
}

function scheduleRefreshTestDataFeed() {
  if (testFeedDebounce != null) clearTimeout(testFeedDebounce)
  testFeedDebounce = setTimeout(() => {
    testFeedDebounce = null
    void refreshTestDataFeed({ forceAll: true })
  }, 350)
}

const detailDialogVisible = ref(false)
const detailDialogLoading = ref(false)
const detailDialogPayload = ref<FeishuTaskConfigDetail | null>(null)
/** 与详情弹框底部操作区对应列表行（随列表刷新同步） */
const detailDialogRow = ref<TaskCardModel | null>(null)

/** 删除确认：不用 ElMessageBox（飞书 iframe 内易出现错位、叠字） */
const deleteDialogVisible = ref(false)
const deleteTarget = ref<TaskCardModel | null>(null)
const deleteSubmitting = ref(false)
const deleteError = ref('')

const listTip = ref<string | null>(null)
let listTipTimer: ReturnType<typeof setTimeout> | null = null

function showListTip(msg: string) {
  if (listTipTimer != null) {
    clearTimeout(listTipTimer)
    listTipTimer = null
  }
  listTip.value = msg
  listTipTimer = setTimeout(() => {
    listTip.value = null
    listTipTimer = null
  }, 3500)
}

onScopeDispose(() => {
  if (listTipTimer != null) clearTimeout(listTipTimer)
  if (testFeedDebounce != null) {
    clearTimeout(testFeedDebounce)
    testFeedDebounce = null
  }
})

const primaryActionRowId = ref<number | null>(null)

function cloneConfigRecord(raw: unknown): Record<string, unknown> {
  if (raw != null && typeof raw === 'object' && !Array.isArray(raw)) {
    return JSON.parse(JSON.stringify(raw)) as Record<string, unknown>
  }
  return {}
}

async function patchTaskConfig(
  id: number,
  patch: Record<string, unknown>,
): Promise<FeishuTaskConfigWriteResult> {
  return saveTaskConfigPatch(id, patch)
}

/** 用 POST/PUT 返回的 `display_status` 覆盖列表行（在 `loadTaskList` 之后调用） */
function applyDisplayFromWrite(id: number, wr: FeishuTaskConfigWriteResult) {
  if (typeof wr.display_status !== 'string' || !wr.display_status.trim()) return
  const idx = tasks.value.findIndex((t) => t.id === id)
  if (idx < 0) return
  const prev = tasks.value[idx]
  const status = parseBackendDisplayStatus(wr)
  const stoppedKind: TaskStoppedKind =
    status === 'stopped' ? parseBackendStoppedKind(wr) : 'neutral'
  tasks.value.splice(idx, 1, { ...prev, status, stoppedKind })
}

function isPrimaryLoadingFor(rowId: number): boolean {
  return primaryActionRowId.value === rowId
}

/** 将任务标为异常（接口失败等），供列表推导为「失败」 */
async function markTaskAbnormal(id: number) {
  try {
    saveTaskConfigPatch(id, { taskAbnormal: true, runStatus: 'failed' })
  } catch {
    /* 忽略二次失败 */
  }
}

/** 任务列表统计：优先 `summary.total` / `summary.running` / `summary.success`（`pending` 不计入运行中） */
const taskStats = computed(() => taskStatsFromAsyncSummary(asyncListSummary.value, tasks.value))

/** 点击统计卡片筛选列表：`all` | `running` | `completed` */
const listFilter = ref<'all' | 'running' | 'completed'>('all')

const displayedTasks = computed(() =>
  tasks.value.filter((t) => matchesAsyncListFilter(t.status, listFilter.value)),
)

/** 当前页条目（接口按 page/limit 返回，筛选在本地做） */
const pagedDisplayedTasks = computed(() => displayedTasks.value)

const paginationTotalPages = computed(() => {
  const total = asyncListSummary.value?.total
  if (typeof total === 'number' && total > 0) {
    return Math.max(1, Math.ceil(total / pageSize.value))
  }
  return Math.max(1, Math.ceil(displayedTasks.value.length / pageSize.value))
})

/** 页码序列：如 1 2 3 … 10 */
function buildPaginationItems(current: number, total: number): Array<number | 'ellipsis'> {
  if (total < 1) return []
  if (total === 1) return [1]
  const edge = new Set<number>([1, total])
  const pad = 2
  for (let i = current - pad; i <= current + pad; i++) {
    if (i >= 1 && i <= total) edge.add(i)
  }
  const sorted = [...edge].sort((a, b) => a - b)
  const out: Array<number | 'ellipsis'> = []
  for (let i = 0; i < sorted.length; i++) {
    const n = sorted[i]!
    if (i > 0 && n - sorted[i - 1]! > 1) out.push('ellipsis')
    out.push(n)
  }
  return out
}

const paginationItems = computed(() =>
  buildPaginationItems(listCurrentPage.value, paginationTotalPages.value),
)

const pageSizeSelectOptions = [5, 10, 20] as const

function onPageSizeChange(s: number) {
  pageSize.value = s
  listCurrentPage.value = 1
  void loadTaskList({ force: true, bypassMinGap: true })
}

/** 翻页：请求 `GET /api/v1/async/tasks?page=&limit=` */
function goToListPage(page: number) {
  const max = paginationTotalPages.value
  const next = Math.max(1, Math.min(Math.floor(page), max))
  if (next === listCurrentPage.value) return
  listCurrentPage.value = next
  void loadTaskList({ force: true, bypassMinGap: true })
}

function goToPrevListPage() {
  goToListPage(listCurrentPage.value - 1)
}

function goToNextListPage() {
  goToListPage(listCurrentPage.value + 1)
}

/** 切换统计维度（重复点击同一项也会刷新列表，触发后端调度补偿） */
function selectListFilter(next: 'all' | 'running' | 'completed') {
  if (listFilter.value !== next) {
    listFilter.value = next
    listCurrentPage.value = 1
  }
  void loadTaskList({ force: true, bypassMinGap: true })
}

function isListSyncAuthError(msg: string): boolean {
  const s = msg.toLowerCase()
  return s.includes('401') || s.includes('403') || s.includes('未授权') || s.includes('鉴权')
}

/** 从 `GET /api/v1/async/tasks` 加载列表与 `summary`（进入列表 / 手动刷新 / 定时轮询） */
async function syncTaskListFromAsyncTasks() {
  if (!authCode.value.trim()) {
    tasks.value = []
    asyncListSummary.value = null
    stopActiveTaskListPolling()
    return
  }
  if (Date.now() < listSyncBlockedUntil) return
  if (asyncListSyncInFlight) return asyncListSyncInFlight

  asyncListSyncInFlight = (async () => {
    try {
      const ctx = await buildCollectionFetchContext()
      const { cards, summary } = await listTaskCardsFromAsync(ctx, {
        page: listCurrentPage.value,
        limit: pageSize.value,
      })
      tasks.value = cards
      asyncListSummary.value = summary
      lastTaskListFetchedAt = Date.now()
      listSyncBlockedUntil = 0
      const total = summary?.total
      const maxPage =
        typeof total === 'number' && total > 0
          ? Math.max(1, Math.ceil(total / pageSize.value))
          : Math.max(1, Math.ceil(cards.filter((t) => matchesAsyncListFilter(t.status, listFilter.value)).length / pageSize.value))
      if (listCurrentPage.value > maxPage) listCurrentPage.value = maxPage
      syncDetailDialogRowFromList()
      syncTestFeedPollTimer()
    } catch (e) {
      const msg = e instanceof Error ? e.message : '加载任务列表失败'
      if (isListSyncAuthError(msg)) {
        listSyncBlockedUntil = Date.now() + 60_000
        stopActiveTaskListPolling()
      }
      const now = Date.now()
      if (now - lastListSyncErrorToastAt > 8_000) {
        lastListSyncErrorToastAt = now
        ElMessage.error(msg)
      }
    } finally {
      asyncListSyncInFlight = null
    }
  })()

  return asyncListSyncInFlight
}

/** 停止/启动后：在 `loadTaskList` 之后用本地快照的 `display_status` 覆盖列表行状态（名称等仍来自接口） */
function mergeTaskCardFromDetail(id: number, wr?: FeishuTaskConfigWriteResult) {
  if (typeof wr?.display_status === 'string' && wr.display_status.trim() !== '') {
    applyDisplayFromWrite(id, wr)
  }
}

type LoadTaskListOptions = { force?: boolean; /** 保存/执行/启停等需立即刷新列表 */ bypassMinGap?: boolean }

function minMsUntilNextListFetch(options?: LoadTaskListOptions): number {
  if (options?.bypassMinGap) return 0
  if (!options?.force) return listPollIntervalMs()
  return ASYNC_TASK_LIST_MIN_FETCH_MS
}

async function loadTaskList(options?: LoadTaskListOptions) {
  if (!authCode.value.trim()) {
    tasks.value = []
    asyncListSummary.value = null
    listCurrentPage.value = 1
    lastTaskListFetchedAt = 0
    return
  }
  const now = Date.now()
  if (now - lastTaskListFetchedAt < minMsUntilNextListFetch(options)) {
    return
  }
  if (taskListLoadInFlight) {
    if (options?.bypassMinGap) listRefetchQueued = true
    return taskListLoadInFlight
  }

  taskListLoadInFlight = syncTaskListFromAsyncTasks().finally(() => {
    taskListLoadInFlight = null
    if (listRefetchQueued) {
      listRefetchQueued = false
      void loadTaskList({ force: true, bypassMinGap: true })
    }
  })

  return taskListLoadInFlight
}

watch(authCode, (code, prev) => {
  const next = code.trim()
  const old = (prev ?? '').trim()
  if (next === old) return
  resetAsyncTaskLifecycleCache()
  listSyncBlockedUntil = 0
  if (!next) {
    tasks.value = []
    asyncListSummary.value = null
    stopActiveTaskListPolling()
    return
  }
  void loadTaskList({ force: true, bypassMinGap: true })
})

watch(
  () =>
    tasks.value
      .map(
        (t) =>
          `${t.id}:${t.status}:${t.taskTypeLabel}:${t.effectiveAtRaw ?? ''}:${t.expireAtRaw ?? ''}`,
      )
      .join('|'),
  () => {
    syncTestFeedPollTimer()
  },
)

/** 子任务变为 `running` 时拉 results（防抖，避免与列表刷新叠成请求风暴） */
watch(
  () =>
    tasks.value
      .filter((t) => t.status === 'running')
      .map((t) => t.id)
      .sort((a, b) => a - b)
      .join(','),
  (ids, prev) => {
    if (!ids || ids === prev) return
    if (screen.value !== 'list' || !authCode.value.trim()) return
    if (runningFeedWatchDebounce != null) clearTimeout(runningFeedWatchDebounce)
    runningFeedWatchDebounce = setTimeout(() => {
      runningFeedWatchDebounce = null
      void refreshTestDataFeed({ forceAll: true })
    }, 1500)
  },
)

watch(
  () =>
    [
      asyncListSummary.value?.pending,
      asyncListSummary.value?.running,
      asyncListSummary.value?.active,
    ].join(','),
  () => {
    if (screen.value === 'list' && authCode.value.trim() && shouldPollAsyncTaskList()) {
      ensureActiveTaskListPolling()
    }
  },
)

watch(screen, (s) => {
  if (s === 'list') {
    void loadTaskList()
    if (listActiveRunningFeedTargets().length) {
      void refreshTestDataFeed({ forceAll: true })
    }
    ensureActiveTaskListPolling()
  } else {
    stopActiveTaskListPolling()
  }
  syncTestFeedPollTimer()
})

onScopeDispose(() => {
  clearTestFeedPollTimeout()
  stopActiveTaskListPolling()
  if (syncPollTimerDebounce != null) clearTimeout(syncPollTimerDebounce)
  if (runningFeedWatchDebounce != null) clearTimeout(runningFeedWatchDebounce)
})

onMounted(() => {
  void loadTaskList({ force: true, bypassMinGap: true })
})

function onCreateTask() {
  editingTaskId.value = null
  editingTaskStatus.value = null
  taskDetail.value = null
  screen.value = 'create'
}

async function onBackFromCreate() {
  screen.value = 'list'
  editingTaskId.value = null
  editingTaskStatus.value = null
  taskDetail.value = null
  await loadTaskList({ force: true, bypassMinGap: true })
}

const emit = defineEmits<{
  createModeChange: [inCreate: boolean]
}>()

watch(
  screen,
  (s) => {
    emit('createModeChange', s === 'create')
  },
  { immediate: true },
)

defineExpose({
  leaveCreateToList: onBackFromCreate,
})

/** 新建保存：单次任务已在确认弹框内 search-page 执行，不刷任务列表；定时任务刷新列表 */
async function onSaved(id: number, isEdit = false, isRealtime = false) {
  screen.value = 'list'
  editingTaskId.value = null
  editingTaskStatus.value = null
  taskDetail.value = null
  if (isRealtime) {
    clearTestFeedAppendStateForTask(id)
    showListTip(isEdit ? '单次任务已更新并执行' : '单次任务已执行完成')
    return
  }
  if (isEdit) {
    await loadTaskList({ force: true, bypassMinGap: true })
    showListTip('任务已更新')
    return
  }
  if (!isLocalDraftTaskId(id)) {
    await loadTaskList({ force: true, bypassMinGap: true })
    showListTip('定时任务已提交监控')
    return
  }
  clearTestFeedAppendStateForTask(id)
  await loadTaskList({ force: true, bypassMinGap: true })
  showListTip('任务已保存')
}

async function openView(row: TaskCardModel) {
  detailDialogRow.value = row
  detailDialogVisible.value = true
  detailDialogLoading.value = true
  detailDialogPayload.value = null
  try {
    const ctx = await buildCollectionFetchContext()
    detailDialogPayload.value = await loadTaskConfigDetail(row, ctx)
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '加载任务详情失败')
    detailDialogVisible.value = false
    detailDialogRow.value = null
    void markTaskAbnormal(row.id)
    await loadTaskList({ force: true, bypassMinGap: true })
  } finally {
    detailDialogLoading.value = false
  }
}

async function openEdit(row: TaskCardModel) {
  detailDialogVisible.value = false
  detailDialogPayload.value = null
  detailDialogRow.value = null
  editingTaskId.value = row.id
  editingTaskStatus.value = row.status
  taskDetail.value = null
  screen.value = 'create'
  try {
    const ctx = await buildCollectionFetchContext()
    taskDetail.value = await loadTaskConfigDetail(row, ctx)
    const st = taskDetail.value.display_status
    if (st === 'pending_run' || st === 'running' || st === 'completed' || st === 'failed' || st === 'stopped') {
      editingTaskStatus.value = st
    }
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '加载配置失败')
    void markTaskAbnormal(row.id)
    await loadTaskList({ force: true, bypassMinGap: true })
    screen.value = 'list'
    editingTaskId.value = null
    editingTaskStatus.value = null
  }
}

async function executeTaskCollectionAndPatch(
  row: TaskCardModel,
  cfg: Record<string, unknown>,
): Promise<{ wr: FeishuTaskConfigWriteResult; collection: Awaited<ReturnType<typeof submitCollectionFromConfig>> }> {
  const execCfg = applyTaskTypeFromListCard(cfg, row)
  prepareTaskWebhookForNewRun(row.id, execCfg)
  const collection = await submitCollectionFromConfig(execCfg, await buildCollectionFetchContext(), {
    taskId: row.id,
  })
  const next: Record<string, unknown> = {
    ...cloneConfigRecord(execCfg),
    taskPaused: false,
    taskAbnormal: false,
  }
  applyCollectionResultToConfig(next, collection)
  const primaryId =
    collection.mode === 'async' && collection.refs.length
      ? Number(collection.refs[0]!.taskId)
      : row.id
  const storeId = Number.isFinite(primaryId) && primaryId > 0 ? primaryId : row.id
  persistCollectionRefsToLocal(storeId, next, {
    draftId: storeId !== row.id ? row.id : undefined,
  })
  const wr = saveTaskConfigPatch(storeId, next)
  return { wr, collection }
}

function showExecutionResultTip(
  wr: FeishuTaskConfigWriteResult,
  cfg: Record<string, unknown>,
  collection: Awaited<ReturnType<typeof submitCollectionFromConfig>>,
) {
  if (collection.mode === 'sync' && collection.emptyPlatformHints?.length) {
    const hint = collection.emptyPlatformHints.join('；')
    if (collection.itemCount === 0) {
      ElMessage.warning(hint)
      return
    }
    ElMessage.warning(`部分平台无数据：${hint}`)
  }
  if (wr.display_status === 'running') {
    showListTip('已提交执行')
  } else if (wr.display_status === 'completed') {
    showListTip(isRealtimeTaskConfig(cfg) ? '已执行完成' : '任务已过期或未在窗口内')
  } else if (wr.display_status === 'pending_run') {
    showListTip('已提交执行，未到生效时间仍为待运行')
  } else if (parseBackendStoppedKind(wr) === 'before_effective') {
    showListTip('已提交执行，未到生效时间仍为已停止')
  } else {
    showListTip('已提交执行')
  }
}

/** 列表页执行采集：search-page / 异步任务、写多维表格、刷新状态 */
async function runTaskExecutionFromList(row: TaskCardModel) {
  if (primaryActionRowId.value != null) return
  primaryActionRowId.value = row.id
  try {
    const cfg = await loadTaskConfigForExecution(row)
    const { wr, collection } = await executeTaskCollectionAndPatch(row, cfg)
    const storeId =
      collection.mode === 'async' && collection.refs.length
        ? Number(collection.refs[0]!.taskId) || row.id
        : wr.id

    if (collection.mode === 'sync' && collection.emptyPlatformHints?.length && collection.itemCount === 0) {
      await loadTaskList({ force: true, bypassMinGap: true })
      await mergeTaskCardFromDetail(storeId, wr)
      return
    }

    const cfgForBitable = loadLocalTaskConfig(storeId) ?? cfg
    const syncCtx = await buildCollectionFetchContext()
    let bitableWritten = 0
    let bitableTotal = 0
    try {
      const bitable = await syncTaskCollectionToBitable({
        taskId: storeId,
        taskName: row.name,
        config: cfgForBitable,
        syncCtx,
        card: row,
        preloadedItems: collection.mode === 'sync' ? collection.itemsByPlatform : undefined,
      })
      bitableWritten = bitable.written
      bitableTotal = bitable.rowCount
      if (bitable.createdTables.length) {
        showListTip(
          `已新建/写入：${bitable.createdTables.join('、')}（共 ${bitable.written} 条）`,
        )
      } else if (bitable.rowCount > 0 && bitable.written === 0) {
        showListTip(
          '采集成功，但未写入多维表格（请确认：①在飞书多维表格内打开插件；②高级配置为「自动新建表格」；③已勾选采集字段）',
        )
      }
    } catch (bitableErr) {
      const msg = bitableErr instanceof Error ? bitableErr.message : '写入飞书表格失败'
      showListTip(`采集完成，但飞书表格失败：${msg}`)
      void notifyWebhookCollectionRunFailed({
        taskId: row.id,
        taskName: row.name,
        config: cfgForBitable,
        message: `飞书表格写入失败：${msg}`,
      })
    }

    if (!isRealtimeTaskConfig(cfgForBitable)) {
      void notifyWebhookAfterScheduledPoll({
        taskId: row.id,
        taskName: row.name,
        config: cfgForBitable,
        writtenRowCount: bitableWritten,
        totalRowCount: bitableTotal,
        sync: syncCtx,
      })
    }

    await loadTaskList({ force: true, bypassMinGap: true })
    await mergeTaskCardFromDetail(storeId, wr)
    clearTestFeedAppendStateForTask(row.id)
    clearTestFeedAppendStateForTask(storeId)
    scheduleRefreshTestDataFeed()
    showExecutionResultTip(wr, cfg, collection)
  } catch (e) {
    const msg = e instanceof Error ? e.message : '执行失败'
    ElMessage.error(msg)
    try {
      const failCfg = (await loadTaskConfigForExecution(row).catch(() => ({}))) as Record<
        string,
        unknown
      >
      void notifyWebhookCollectionRunFailed({
        taskId: row.id,
        taskName: row.name,
        config: failCfg,
        message: msg,
      })
    } catch {
      /* 无法加载配置时跳过 Webhook */
    }
    void markTaskAbnormal(row.id)
    await loadTaskList({ force: true, bypassMinGap: true })
  } finally {
    primaryActionRowId.value = null
    if (detailDialogVisible.value && detailDialogRow.value?.id === row.id) {
      const next = tasks.value.find((t) => t.id === row.id)
      if (next) detailDialogRow.value = next
    }
  }
}

async function onPrimaryAction(row: TaskCardModel) {
  if (row.status === 'failed' || (row.taskTypeLabel === '单次任务' && row.status !== 'running')) {
    await runTaskExecutionFromList(row)
    return
  }
  if (primaryActionRowId.value != null) return
  primaryActionRowId.value = row.id
  try {
    switch (row.status) {
      case 'running': {
        const wr = await patchTaskConfig(row.id, { taskPaused: true })
        await loadTaskList({ force: true, bypassMinGap: true })
        await mergeTaskCardFromDetail(row.id, wr)
        showListTip(parseBackendDisplayStatus(wr) === 'stopped' ? '已停止' : '已保存')
        break
      }
      default:
        break
    }
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '操作失败')
    void markTaskAbnormal(row.id)
    await loadTaskList({ force: true, bypassMinGap: true })
  } finally {
    primaryActionRowId.value = null
    if (detailDialogVisible.value && detailDialogRow.value?.id === row.id) {
      const next = tasks.value.find((t) => t.id === row.id)
      if (next) detailDialogRow.value = next
    }
  }
}

function onDeleteTask(row: TaskCardModel) {
  deleteError.value = ''
  deleteTarget.value = row
  deleteDialogVisible.value = true
}

function onDeleteDialogClosed() {
  deleteTarget.value = null
  deleteError.value = ''
}

async function confirmDeleteTask() {
  const row = deleteTarget.value
  if (!row || deleteSubmitting.value) return
  deleteError.value = ''
  deleteSubmitting.value = true
  try {
    const deletedId = row.id
    const ctx = await buildCollectionFetchContext()
    await deleteAsyncTask(ctx, String(row.id))
    clearTestFeedAppendStateForTask(row.id)
    deleteDialogVisible.value = false
    showListTip('已删除')
    await loadTaskList({ force: true, bypassMinGap: true })
    if (detailDialogVisible.value && detailDialogRow.value?.id === deletedId) {
      detailDialogVisible.value = false
      detailDialogPayload.value = null
      detailDialogRow.value = null
    }
  } catch (e) {
    deleteError.value = e instanceof Error ? e.message : '删除失败'
  } finally {
    deleteSubmitting.value = false
  }
}
</script>

<template>
  <div class="flex min-h-0 w-full min-w-0 flex-col gap-4">
    <TaskDetailDialog
      v-model="detailDialogVisible"
      :detail="detailDialogPayload"
      :loading="detailDialogLoading"
      :row="detailDialogRow"
      :primary-loading="detailDialogRow ? isPrimaryLoadingFor(detailDialogRow.id) : false"
      @primary-action="onPrimaryAction"
      @delete="onDeleteTask"
      @edit="openEdit"
    />

    <el-dialog
      v-model="deleteDialogVisible"
      title="删除任务"
      width="90%"
      align-center
      append-to-body
      destroy-on-close
      :close-on-click-modal="false"
      class="delete-task-dialog"
      @closed="onDeleteDialogClosed"
    >
      <el-alert
        v-if="deleteError"
        type="error"
        :title="deleteError"
        show-icon
        closable
        class="mb-3"
        @close="deleteError = ''"
      />
      <p v-if="deleteTarget" class="m-0 text-sm leading-relaxed text-slate-600">
        确定删除「<strong class="font-medium text-slate-800">{{ deleteTarget.name }}</strong>」？删除后不可恢复。
      </p>
      <template #footer>
        <div class="flex justify-end gap-2">
          <el-button :disabled="deleteSubmitting" @click="deleteDialogVisible = false">取消</el-button>
          <el-button type="danger" :loading="deleteSubmitting" @click="confirmDeleteTask">删除</el-button>
        </div>
      </template>
    </el-dialog>

    <template v-if="screen === 'create'">
      <div
        v-if="editingTaskId !== null && !taskDetail"
        class="py-16 text-center text-sm text-slate-500"
      >
        加载配置…
      </div>
      <TaskCreateForm
        v-else
        :task-config-id="editingTaskId"
        :detail="taskDetail"
        :edit-task-status="editingTaskStatus"
        @back="onBackFromCreate"
        @saved="onSaved"
      />
    </template>

    <template v-else>
      <section class="flex min-h-0 flex-col gap-4">
        <el-alert
          v-if="listTip"
          type="success"
          :title="listTip"
          show-icon
          closable
          class="sticky top-0 z-10 shadow-sm"
          @close="listTip = null"
        />
        <div class="task-stat-row flex w-full min-w-0 gap-2">
          <button
            type="button"
            class="task-stat-card"
            :class="{ 'task-stat-card--active': listFilter === 'all' }"
            @click="selectListFilter('all')"
          >
            <div class="task-stat-num task-stat-num--total">{{ taskStats.total }}</div>
            <div class="task-stat-label">总任务数</div>
          </button>
          <button
            type="button"
            class="task-stat-card"
            :class="{ 'task-stat-card--active': listFilter === 'running' }"
            @click="selectListFilter('running')"
          >
            <div class="task-stat-num task-stat-num--running">{{ taskStats.running }}</div>
            <div class="task-stat-label">运行中</div>
          </button>
          <button
            type="button"
            class="task-stat-card"
            :class="{ 'task-stat-card--active': listFilter === 'completed' }"
            @click="selectListFilter('completed')"
          >
            <div class="task-stat-num task-stat-num--completed">{{ taskStats.completed }}</div>
            <div class="task-stat-label">已完成</div>
          </button>
        </div>

        <button type="button" class="task-create-btn" @click="onCreateTask">
          <el-icon class="task-create-btn__icon" :size="18">
            <Plus />
          </el-icon>
          新建任务
        </button>

        <h2 class="task-list-heading">任务列表</h2>

        <div v-if="displayedTasks.length > 0" class="flex flex-col gap-3">
          <TaskListCard
            v-for="row in pagedDisplayedTasks"
            :key="row.id"
            :row="row"
            :primary-loading="isPrimaryLoadingFor(row.id)"
            @view="openView"
            @edit="openEdit"
            @primary-action="onPrimaryAction"
            @delete="onDeleteTask"
          />
          <div class="task-pagination-bar">
            <button
              type="button"
              class="task-pagination-icon-btn"
              :disabled="listCurrentPage <= 1"
              aria-label="上一页"
              @click="goToPrevListPage"
            >
              <el-icon :size="18">
                <ArrowLeft />
              </el-icon>
            </button>
            <div class="task-pagination-pages">
              <template v-for="(item, idx) in paginationItems" :key="`pg-${idx}-${String(item)}`">
                <span v-if="item === 'ellipsis'" class="task-pagination-ellipsis">...</span>
                <button
                  v-else
                  type="button"
                  class="task-pagination-page-btn"
                  :class="{ 'task-pagination-page-btn--active': item === listCurrentPage }"
                  @click="goToListPage(item)"
                >
                  {{ item }}
                </button>
              </template>
            </div>
            <button
              type="button"
              class="task-pagination-icon-btn"
              :disabled="listCurrentPage >= paginationTotalPages"
              aria-label="下一页"
              @click="goToNextListPage"
            >
              <el-icon :size="18">
                <ArrowRight />
              </el-icon>
            </button>
            <el-select
              :model-value="pageSize"
              class="task-pagination-size-select"
              size="small"
              teleported
              @update:model-value="onPageSizeChange"
            >
              <el-option
                v-for="n in pageSizeSelectOptions"
                :key="n"
                :label="`${n}条/页`"
                :value="n"
              />
            </el-select>
          </div>
        </div>
        <div v-else class="task-list-empty" role="status">
          <img class="task-list-empty__img" :src="taskListEmptyImgSrc" alt="" decoding="async" />
          <p class="task-list-empty__text">
            {{ tasks.length > 0 ? '当前筛选下暂无任务' : '暂无任务' }}
          </p>
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.task-stat-row {
  -webkit-overflow-scrolling: touch;
}

.task-stat-card {
  box-sizing: border-box;
  flex: 1 1 0;
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: auto;
  height: 94px;
  padding: 0 8px;
  margin: 0;
  border: none;
  background: #f8f9fa;
  border-radius: 0;
  cursor: pointer;
  transition: box-shadow 0.15s ease;
}

.task-stat-card:hover:not(:disabled):not(.task-stat-card--active) {
  box-shadow: inset 0 0 0 1px #e1e4e8;
}

.task-stat-card:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.task-stat-card--active {
  box-shadow: inset 0 0 0 2px #3370ff;
}

.task-stat-num {
  font-weight: 600;
  font-size: 24px;
  text-align: center;
  font-style: normal;
  text-transform: none;
  line-height: 1.2;
}

.task-stat-num--total {
  color: #2b2f36;
}

.task-stat-num--running {
  color: #3370ff;
}

.task-stat-num--completed {
  color: #34c724;
}

.task-stat-label {
  margin-top: 6px;
  font-weight: 400;
  font-size: 14px;
  color: #2b2f36;
  text-align: center;
  font-style: normal;
  text-transform: none;
  line-height: 1.2;
  white-space: nowrap;
}

.task-list-heading {
  margin: 0;
  font-weight: 500;
  font-size: 16px;
  color: #0f1114;
  text-align: left;
  font-style: normal;
  text-transform: none;
  line-height: 1.4;
}

.task-list-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem 1rem 2.5rem;
}

.task-list-empty__img {
  display: block;
  width: min(200px, 72vw);
  height: auto;
  margin: 0 auto 0.75rem;
  object-fit: contain;
  user-select: none;
  pointer-events: none;
}

.task-list-empty__text {
  margin: 0;
  font-size: 14px;
  line-height: 1.5;
  color: #8f959e;
  text-align: center;
}

.task-create-btn {
  box-sizing: border-box;
  display: inline-flex;
  width: 100%;
  min-width: 0;
  align-items: center;
  justify-content: center;
  height: 46px;
  padding: 0 16px;
  margin: 0;
  border: none;
  border-radius: 4px;
  background: linear-gradient(90deg, #1456f0 0%, #4014f0 100%);
  color: #ffffff;
  font-weight: 400;
  font-size: 16px;
  text-align: center;
  font-style: normal;
  line-height: 1;
  cursor: pointer;
  transition: filter 0.15s ease, box-shadow 0.15s ease;
}

.task-create-btn:hover {
  filter: brightness(1.06);
}

.task-create-btn:focus-visible {
  outline: 2px solid #4014f0;
  outline-offset: 2px;
}

.task-create-btn:active {
  filter: brightness(0.96);
}

.task-create-btn__icon {
  margin-right: 6px;
  color: #ffffff;
}

.task-pagination-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 10px 12px;
  padding-top: 0.5rem;
}

.task-pagination-icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  padding: 0;
  margin: 0;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: #646a73;
  cursor: pointer;
  transition: color 0.15s ease, background-color 0.15s ease;
}

.task-pagination-icon-btn:hover:not(:disabled) {
  color: #3370ff;
  background: rgba(51, 112, 255, 0.08);
}

.task-pagination-icon-btn:disabled {
  cursor: not-allowed;
  color: #bbbfc4;
  opacity: 0.55;
}

.task-pagination-pages {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.task-pagination-ellipsis {
  display: inline-flex;
  min-width: 1.25rem;
  align-items: center;
  justify-content: center;
  padding: 0 2px;
  font-size: 14px;
  font-weight: 500;
  color: #8f959e;
  user-select: none;
}

.task-pagination-page-btn {
  box-sizing: border-box;
  min-width: 28px;
  height: 28px;
  padding: 0 6px;
  margin: 0;
  border: 1px solid transparent;
  border-radius: 4px;
  background: #ffffff;
  color: #2b2f36;
  font-size: 14px;
  font-weight: 400;
  line-height: 1;
  cursor: pointer;
  transition:
    border-color 0.15s ease,
    color 0.15s ease,
    background-color 0.15s ease;
}

.task-pagination-page-btn:hover:not(.task-pagination-page-btn--active) {
  border-color: #dee0e3;
  background: #f8f9fa;
}

.task-pagination-page-btn--active {
  border-color: #3370ff;
  color: #3370ff;
  font-weight: 500;
}

.task-pagination-size-select {
  width: 108px;
}

.task-pagination-size-select :deep(.el-select__wrapper) {
  border-radius: 4px;
}
</style>

<style>
.delete-task-dialog.el-dialog {
  width: min(420px, calc(100vw - 24px)) !important;
  max-width: calc(100vw - 16px);
}
</style>

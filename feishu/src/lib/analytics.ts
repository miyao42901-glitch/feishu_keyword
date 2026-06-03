/**
 * 飞书插件埋点：批量上报至 POST /api/v1/analytics/events
 */

import { getSyncApiBase } from '@/lib/sync-api-common'
import { useGlobalSettingsStore } from '@/stores/globalSettings'
import { useYddmAuthStore } from '@/stores/yddmAuth'

export type AnalyticsEventName =
  | 'page_view'
  | 'task_create'
  | 'notify_toggle'
  | 'user_profile'

export type AnalyticsProperties = Record<string, unknown>

type QueuedEvent = {
  event: AnalyticsEventName
  user_id?: string
  ts: string
  properties: AnalyticsProperties
}

const QUEUE_KEY = 'feishu_analytics_queue_v1'
const MAX_QUEUE = 100
const FLUSH_INTERVAL_MS = 5000

let queue: QueuedEvent[] = []
let flushTimer: ReturnType<typeof setTimeout> | null = null
let flushing = false

function loadPersistedQueue(): QueuedEvent[] {
  try {
    const raw = localStorage.getItem(QUEUE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw) as QueuedEvent[]
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function persistQueue(): void {
  try {
    localStorage.setItem(QUEUE_KEY, JSON.stringify(queue.slice(-MAX_QUEUE)))
  } catch {
    /* ignore quota */
  }
}

function initQueueFromStorage(): void {
  if (queue.length === 0) {
    queue = loadPersistedQueue()
  }
}

export function detectDeviceType(): '手机' | '桌面' | 'Web' {
  const ua = navigator.userAgent || ''
  if (/Mobile|Android|iPhone|iPad/i.test(ua)) return '手机'
  if (/Feishu|Lark|Electron/i.test(ua)) return '桌面'
  return 'Web'
}

export function getPluginVersion(): string {
  return (import.meta.env.VITE_APP_VERSION as string | undefined)?.trim() || 'dev'
}

function resolveUserId(explicit?: string | number | null): string | undefined {
  if (explicit != null && String(explicit).trim()) return String(explicit).trim()
  const yddm = useYddmAuthStore()
  const id = yddm.me?.id
  return id != null && String(id).trim() ? String(id).trim() : undefined
}

function buildHeaders(): Record<string, string> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  const globalSettings = useGlobalSettingsStore()
  const yddm = useYddmAuthStore()
  const apiKey = String(globalSettings.authCode ?? yddm.me?.api_key ?? '').trim()
  const userId = resolveUserId()
  if (apiKey) headers['X-API-Key'] = apiKey
  if (userId) headers['X-User-Id'] = userId
  return headers
}

function baseProps(extra: AnalyticsProperties = {}): AnalyticsProperties {
  return {
    device_type: detectDeviceType(),
    plugin_version: getPluginVersion(),
    ...extra,
  }
}

export function trackAnalytics(
  event: AnalyticsEventName,
  properties: AnalyticsProperties = {},
  userId?: string | number | null,
): void {
  initQueueFromStorage()
  const item: QueuedEvent = {
    event,
    user_id: resolveUserId(userId),
    ts: new Date().toISOString(),
    properties: baseProps(properties),
  }
  queue.push(item)
  if (queue.length > MAX_QUEUE) {
    queue = queue.slice(-MAX_QUEUE)
  }
  persistQueue()
  scheduleFlush()
}

function scheduleFlush(): void {
  if (flushTimer != null) return
  flushTimer = setTimeout(() => {
    flushTimer = null
    void flushAnalytics()
  }, FLUSH_INTERVAL_MS)
}

export async function flushAnalytics(): Promise<void> {
  initQueueFromStorage()
  if (flushing || queue.length === 0) return
  flushing = true
  const batch = queue.splice(0, 50)
  persistQueue()
  try {
    const base = getSyncApiBase()
    const url = `${base}/api/v1/analytics/events`
    const res = await fetch(url, {
      method: 'POST',
      headers: buildHeaders(),
      body: JSON.stringify({
        events: batch.map((e) => ({
          event: e.event,
          user_id: e.user_id,
          ts: e.ts,
          properties: e.properties,
        })),
      }),
    })
    if (!res.ok) {
      queue = [...batch, ...queue].slice(-MAX_QUEUE)
      persistQueue()
    }
  } catch {
    queue = [...batch, ...queue].slice(-MAX_QUEUE)
    persistQueue()
  } finally {
    flushing = false
    if (queue.length > 0) scheduleFlush()
  }
}

export function trackPageView(pageName: string, source?: string): void {
  trackAnalytics('page_view', { page_name: pageName, source: source ?? 'direct' })
}

export function trackTaskCreate(payload: {
  taskId: string | number
  taskType: string
  keywordCount: number
  platforms: string[]
  notifyEnabled: boolean
  userId?: string | number
}): void {
  trackAnalytics(
    'task_create',
    {
      task_id: String(payload.taskId),
      task_type: payload.taskType,
      keyword_count: payload.keywordCount,
      platforms: payload.platforms,
      notify_enabled: payload.notifyEnabled,
      status: '运行中',
    },
    payload.userId,
  )
}

export function trackNotifyToggle(payload: {
  taskId?: string | number
  enabled: boolean
  userId?: string | number
}): void {
  trackAnalytics(
    'notify_toggle',
    {
      task_id: payload.taskId != null ? String(payload.taskId) : undefined,
      enabled: payload.enabled,
    },
    payload.userId,
  )
}

export function trackUserProfile(payload: {
  userId: string | number
  phone?: string | null
  feishuId?: string | null
}): void {
  trackAnalytics(
    'user_profile',
    {
      phone: payload.phone ?? undefined,
      feishu_id: payload.feishuId ?? undefined,
    },
    payload.userId,
  )
}

if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    void flushAnalytics()
  })
}

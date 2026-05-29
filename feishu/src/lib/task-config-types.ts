/** 飞书任务配置 UI 类型与展示状态解析（本地快照 + 8765 异步任务）。 */

export type FeishuTaskConfigListItem = {
  id: number
  plan_name?: string | null
  updated_at?: string | null
  task_type?: string | null
  platform_keys?: string[] | null
  effective_at?: string | null
  expire_at?: string | null
  task_paused?: boolean | null
  taskPaused?: boolean | null
  task_abnormal?: boolean | null
  taskAbnormal?: boolean | null
  run_status?: string | null
  runStatus?: string | null
  display_status?: string | null
  displayStatus?: string | null
  stopped_kind?: string | null
  stoppedKind?: string | null
}

const BACKEND_DISPLAY = new Set(['running', 'stopped', 'completed', 'failed', 'pending_run'])
const BACKEND_STOPPED_KIND = new Set(['before_effective', 'paused_in_window', 'neutral'])

export function parseBackendDisplayStatus(
  raw: unknown,
): 'running' | 'stopped' | 'completed' | 'failed' | 'pending_run' {
  const o = raw as Record<string, unknown> | null | undefined
  const v = (typeof raw === 'string' ? raw : o?.display_status ?? o?.displayStatus) as string | undefined
  const s = typeof v === 'string' ? v.trim().toLowerCase() : ''
  if (BACKEND_DISPLAY.has(s)) return s as 'running' | 'stopped' | 'completed' | 'failed' | 'pending_run'
  return 'stopped'
}

export function parseBackendStoppedKind(raw: unknown): 'before_effective' | 'paused_in_window' | 'neutral' {
  const o = raw as Record<string, unknown> | null | undefined
  const v = (typeof raw === 'string' ? raw : o?.stopped_kind ?? o?.stoppedKind) as string | undefined
  const s = typeof v === 'string' ? v.trim().toLowerCase() : ''
  if (BACKEND_STOPPED_KIND.has(s)) return s as 'before_effective' | 'paused_in_window' | 'neutral'
  return 'neutral'
}

export function parseListTaskPaused(row: FeishuTaskConfigListItem): boolean {
  const o = row as Record<string, unknown>
  const v = o.task_paused ?? o.taskPaused
  if (v === true) return true
  if (v === false || v == null) return false
  if (typeof v === 'string') {
    const s = v.trim().toLowerCase()
    if (s === 'true' || s === '1' || s === 'yes' || s === 'on') return true
  }
  if (typeof v === 'number' && v === 1) return true
  return false
}

function parseListTruthish(v: unknown): boolean {
  if (v === true) return true
  if (v === false || v == null) return false
  if (typeof v === 'string') {
    const s = v.trim().toLowerCase()
    if (s === 'true' || s === '1' || s === 'yes' || s === 'on') return true
  }
  if (typeof v === 'number' && v === 1) return true
  return false
}

export function parseListTaskAbnormal(row: FeishuTaskConfigListItem): boolean {
  const o = row as Record<string, unknown>
  return parseListTruthish(o.task_abnormal ?? o.taskAbnormal)
}

export function parseListRunStatus(row: FeishuTaskConfigListItem): string | null {
  const o = row as Record<string, unknown>
  const v = o.run_status ?? o.runStatus
  if (typeof v !== 'string') return null
  const s = v.trim()
  return s.length ? s : null
}

export type FeishuTaskConfigWriteResult = {
  id: number
  display_status?: string | null
  stopped_kind?: string | null
}

export type FeishuTaskConfigDetail = {
  id: number
  plan_name?: string | null
  config: Record<string, unknown>
  created_at?: string | null
  updated_at?: string | null
  display_status?: string | null
  stopped_kind?: string | null
}

const LIST_RUN_STATUSES = new Set(['running', 'completed', 'stopped', 'failed'])

export function feishuDetailToListItem(d: FeishuTaskConfigDetail): FeishuTaskConfigListItem {
  const c =
    d.config != null && typeof d.config === 'object' && !Array.isArray(d.config)
      ? (d.config as Record<string, unknown>)
      : {}
  const row = { id: d.id, ...c } as Record<string, unknown>
  const tt = row.task_type ?? row.taskType
  const task_type = tt === 'realtime' || tt === 'scheduled' ? String(tt) : null
  const rawSources = row.selectedSources
  const platform_keys = Array.isArray(rawSources)
    ? (rawSources as unknown[]).filter((x) => x != null).map((x) => String(x))
    : null
  const eff = row.effective_at ?? row.effectiveAt
  const ex = row.expire_at ?? row.expireAt
  const effective_at = eff != null && String(eff).trim() ? String(eff).trim() : null
  const expire_at = ex != null && String(ex).trim() ? String(ex).trim() : null
  const asList = row as unknown as FeishuTaskConfigListItem
  const rs = parseListRunStatus(asList)
  const run_status = rs != null && LIST_RUN_STATUSES.has(rs) ? rs : null
  const disp = parseBackendDisplayStatus(d)
  return {
    id: d.id,
    plan_name: d.plan_name ?? null,
    updated_at: d.updated_at ?? null,
    task_type,
    platform_keys,
    effective_at,
    expire_at,
    task_paused: parseListTaskPaused(asList),
    task_abnormal: parseListTaskAbnormal(asList) || undefined,
    run_status,
    display_status: disp,
    stopped_kind: disp === 'stopped' ? parseBackendStoppedKind(d) : undefined,
  }
}

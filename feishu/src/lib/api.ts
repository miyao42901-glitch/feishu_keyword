/**
 * 浏览器直连 `server/` 提供的 REST API。
 *
 * - Base URL：`VITE_API_BASE_URL`（仓根 `.env` / `.env.local`，见 `.env.example`），**禁止写死生产域名**。
 * - 本地 `npm run dev` 未配置时默认 `http://127.0.0.1:8000`。
 * - 后端统一响应：`{ code, message, data }`；本模块 **`apiFetch` 在 `code === 0` 时只返回 `data`**，
 *   非 0 时抛错（`message` 供 UI 提示）。约定见 `docs/API.md` 第五节。
 * - 任务相关接口携带请求头 **`X-Api-Key`**（与 Pinia `globalSettings.authCode` / localStorage 同步），
 *   供后端按登录账户隔离任务数据。
 */

import { getActivePinia } from 'pinia'

import { GLOBAL_AUTH_CODE_STORAGE_KEY, useGlobalSettingsStore } from '@/stores/globalSettings'

/** 本地后端默认地址（与文档中 uvicorn 示例端口一致） */
const DEFAULT_DEV_API_ROOT = 'http://127.0.0.1:8000'

/** 与后端统一响应外层结构一致（`T` 为成功时 `data` 的类型） */
export type ApiEnvelope<T = unknown> = {
  code: number
  message: string
  data: T | null
}

/** 拼接并校验 `VITE_API_BASE_URL`，生产构建未配置时抛错 */
function getApiRoot(): string {
  const raw = import.meta.env.VITE_API_BASE_URL as string | undefined
  if (raw?.trim()) return raw.replace(/\/$/, '')
  if (import.meta.env.DEV) return DEFAULT_DEV_API_ROOT
  throw new Error(
    '未配置 VITE_API_BASE_URL：请在仓根 .env 中设置（build-public-*.bat 或 cp .env.test .env 后再构建）',
  )
}

/** 从已解析 JSON 中取出业务 `data`；`code !== 0` 时用 `message` 抛错 */
function unwrapEnvelope<T>(body: unknown): T {
  if (!body || typeof body !== 'object' || !('code' in body)) {
    throw new Error('响应格式错误：缺少统一字段 code')
  }
  const o = body as ApiEnvelope<T>
  if (o.code !== 0) {
    const msg =
      typeof o.message === 'string' && o.message.trim()
        ? o.message
        : `业务错误（code=${o.code}）`
    throw new Error(msg)
  }
  return o.data as T
}

/**
 * 发起 `fetch`，期望响应体为统一信封 JSON；成功返回 **`data`**。
 *
 * @param path - 业务路径，如 `/feishu-task-configs` 或 `feishu-task-configs`（自动加 `/api` 前缀）
 * @param init - 标准 `fetch` 选项；默认设置 `Content-Type: application/json`
 * @returns 解析后的 `data` 字段
 * @throws Error - 非信封、业务 `code !== 0`、或非 JSON 错误响应
 */
export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const root = getApiRoot()
  const url = `${root}/api${path.startsWith('/') ? path : `/${path}`}`
  const apiKey = readApiKeyForHeader()
  const baseHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(init?.headers as Record<string, string>),
  }
  if (apiKey) baseHeaders['X-Api-Key'] = apiKey
  const res = await fetch(url, {
    ...init,
    headers: baseHeaders,
  })
  const text = await res.text()
  let parsed: unknown = null
  if (text) {
    try {
      parsed = JSON.parse(text) as unknown
    } catch {
      parsed = text
    }
  }

  if (parsed && typeof parsed === 'object' && parsed !== null && 'code' in parsed) {
    return unwrapEnvelope<T>(parsed)
  }

  if (!res.ok) {
    const detail =
      typeof parsed === 'object' && parsed !== null && 'detail' in parsed
        ? String((parsed as { detail: unknown }).detail)
        : `请求失败 HTTP ${res.status}`
    throw new Error(detail)
  }

  throw new Error('响应格式错误：无法解析为统一 JSON')
}

function readApiKeyForHeader(): string {
  try {
    const pinia = getActivePinia()
    if (pinia) {
      const k = useGlobalSettingsStore(pinia).authCode?.trim()
      if (k) return k
    }
  } catch {
    /* Pinia 未挂载等 */
  }
  try {
    const raw = localStorage.getItem(GLOBAL_AUTH_CODE_STORAGE_KEY)
    return typeof raw === 'string' ? raw.trim() : ''
  } catch {
    return ''
  }
}

/** `GET /api/feishu-task-configs` 列表项（`data` 数组元素） */
export type FeishuTaskConfigListItem = {
  id: number
  plan_name?: string | null
  updated_at?: string | null
  /** 来自表单 `taskType`：`scheduled` | `realtime` */
  task_type?: string | null
  /** 平台 id 列表，来自表单 `selectedSources` */
  platform_keys?: string[] | null
  /** 生效时间字符串，来自表单 `effectiveAt` */
  effective_at?: string | null
  /** 过期时间字符串，来自表单 `expireAt` */
  expire_at?: string | null
  /** 窗口内暂停，来自表单 `taskPaused` */
  task_paused?: boolean | null
  /** 少数代理/运行环境会把列表字段转成 camelCase，与 `task_paused` 等价 */
  taskPaused?: boolean | null
  /** 任务异常（如接口失败），来自表单 `taskAbnormal` */
  task_abnormal?: boolean | null
  taskAbnormal?: boolean | null
  /** 配置中的 `runStatus`；`failed` 与 `task_abnormal` 均视为失败态 */
  run_status?: string | null
  runStatus?: string | null
  /** 服务端计算的卡片状态（唯一可信来源） */
  display_status?: string | null
  displayStatus?: string | null
  stopped_kind?: string | null
  stoppedKind?: string | null
}

const BACKEND_DISPLAY = new Set(['running', 'stopped', 'completed', 'failed', 'pending_run'])
const BACKEND_STOPPED_KIND = new Set(['before_effective', 'paused_in_window', 'neutral'])

/** 列表/详情中的展示状态：仅展示后端返回值，缺省回退 `stopped` */
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

/** 与后端 `task_paused_from_config` 语义一致；勿仅用 `task_paused === true`（易漏 camelCase / 字符串） */
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

/** POST/PUT 保存成功后返回，用于立即刷新卡片状态（不依赖列表是否含 `display_status`） */
export type FeishuTaskConfigWriteResult = {
  id: number
  display_status?: string | null
  stopped_kind?: string | null
}

/** `GET /api/feishu-task-configs/{id}` 详情（`data` 对象） */
export type FeishuTaskConfigDetail = {
  id: number
  plan_name?: string | null
  config: Record<string, unknown>
  created_at?: string | null
  updated_at?: string | null
  /** 服务端计算的卡片状态 */
  display_status?: string | null
  stopped_kind?: string | null
}

const LIST_RUN_STATUSES = new Set(['running', 'completed', 'stopped', 'failed'])

/**
 * 用详情接口的 `config` 拼出与列表项等价的结构，供卡片状态推导。
 * 当列表 GET 缺字段或被网关改写时，仍以详情为准（停止/启动后主操作与列表一致）。
 */
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
  const effective_at =
    eff != null && String(eff).trim() ? String(eff).trim() : null
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

/** 分页拉取本地任务配置列表（`GET /api/feishu-task-configs`）。任务列表页主数据源。 */
export function listFeishuTaskConfigs(skip = 0, limit = 100) {
  return apiFetch<FeishuTaskConfigListItem[]>(`/feishu-task-configs?skip=${skip}&limit=${limit}`)
}

/** 按 id 拉取单条配置（含 `config` 快照，用于表单回显） */
export function getFeishuTaskConfig(id: number) {
  return apiFetch<FeishuTaskConfigDetail>(`/feishu-task-configs/${id}`)
}

/**
 * 新建任务配置。
 * @param config - 与 `TaskCreateForm` 表单结构一致的普通对象，序列化为请求体 `{"config": ...}`
 */
export function createFeishuTaskConfig(config: Record<string, unknown>) {
  return apiFetch<FeishuTaskConfigWriteResult>('/feishu-task-configs', {
    method: 'POST',
    body: JSON.stringify({ config }),
  })
}

/**
 * 全量更新已有任务配置。
 * @param id - `feishu_task_configs` 主键
 * @param config - 完整表单快照
 */
export function updateFeishuTaskConfig(id: number, config: Record<string, unknown>) {
  return apiFetch<FeishuTaskConfigWriteResult>(`/feishu-task-configs/${id}`, {
    method: 'PUT',
    body: JSON.stringify({ config }),
  })
}

/**
 * 删除任务配置。
 * @param id - `feishu_task_configs` 主键
 */
export function deleteFeishuTaskConfig(id: number) {
  return apiFetch<{ id: number }>(`/feishu-task-configs/${id}`, {
    method: 'DELETE',
  })
}

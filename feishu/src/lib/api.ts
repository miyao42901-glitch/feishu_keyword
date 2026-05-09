/**
 * 浏览器直连 `server/` 提供的 REST API。
 *
 * - Base URL：`VITE_API_BASE_URL`（见 `feishu/.env.example`），**禁止写死生产域名**。
 * - 本地 `npm run dev` 未配置时默认 `http://127.0.0.1:8000`。
 * - 后端统一响应：`{ code, message, data }`；本模块 **`apiFetch` 在 `code === 0` 时只返回 `data`**，
 *   非 0 时抛错（`message` 供 UI 提示）。约定见 `docs/API.md` 第五节。
 */

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
    '未配置 VITE_API_BASE_URL：请在 feishu/.env 中设置（构建产物部署时需写入真实后端地址后再 npm run build）',
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
  const res = await fetch(url, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers as Record<string, string>),
    },
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

/** `GET /api/feishu-task-configs` 列表项（`data` 数组元素） */
export type FeishuTaskConfigListItem = {
  id: number
  plan_name?: string | null
  updated_at?: string | null
  /** `scheduled` | `realtime`，来自表单 `taskType` */
  task_type?: string | null
  /** 平台 id 列表，来自表单 `selectedSources` */
  platform_keys?: string[] | null
  /** 生效时间字符串，来自表单 `effectiveAt` */
  effective_at?: string | null
}

/** `GET /api/feishu-task-configs/{id}` 详情（`data` 对象） */
export type FeishuTaskConfigDetail = {
  id: number
  plan_name?: string | null
  config: Record<string, unknown>
  created_at?: string | null
  updated_at?: string | null
}

/**
 * 分页拉取任务配置列表。
 * @param skip - 偏移量，默认 0
 * @param limit - 条数上限，默认 100（服务端仍会裁剪）
 */
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
  return apiFetch<{ id: number }>('/feishu-task-configs', {
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
  return apiFetch<{ id: number }>(`/feishu-task-configs/${id}`, {
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

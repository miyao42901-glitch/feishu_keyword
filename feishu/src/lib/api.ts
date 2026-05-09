/**
 * 浏览器直连 `server/` 提供的 REST API。
 * - 优先使用环境变量 `VITE_API_BASE_URL`（见 `feishu/.env.example`），禁止写死生产域名。
 * - **本地开发未配置时**：默认 `http://127.0.0.1:8000`（与文档示例一致），便于开箱即用。
 *
 * 后端统一响应：`{ code, message, data }`，成功时 `code === 0`，业务数据在 `data`。
 */

/** 本地后端默认地址（与 docs 中 uvicorn 示例端口一致） */
const DEFAULT_DEV_API_ROOT = 'http://127.0.0.1:8000'

export type ApiEnvelope<T = unknown> = {
  code: number
  message: string
  data: T | null
}

function getApiRoot(): string {
  const raw = import.meta.env.VITE_API_BASE_URL as string | undefined
  if (raw?.trim()) return raw.replace(/\/$/, '')
  if (import.meta.env.DEV) return DEFAULT_DEV_API_ROOT
  throw new Error(
    '未配置 VITE_API_BASE_URL：请在 feishu/.env 中设置（构建产物部署时需写入真实后端地址后再 npm run build）',
  )
}

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

export type FeishuTaskConfigListItem = {
  id: number
  plan_name?: string | null
  updated_at?: string | null
}

export type FeishuTaskConfigDetail = {
  id: number
  plan_name?: string | null
  config: Record<string, unknown>
  created_at?: string | null
  updated_at?: string | null
}

export function listFeishuTaskConfigs(skip = 0, limit = 100) {
  return apiFetch<FeishuTaskConfigListItem[]>(`/feishu-task-configs?skip=${skip}&limit=${limit}`)
}

export function getFeishuTaskConfig(id: number) {
  return apiFetch<FeishuTaskConfigDetail>(`/feishu-task-configs/${id}`)
}

export function createFeishuTaskConfig(config: Record<string, unknown>) {
  return apiFetch<{ id: number }>('/feishu-task-configs', {
    method: 'POST',
    body: JSON.stringify({ config }),
  })
}

export function updateFeishuTaskConfig(id: number, config: Record<string, unknown>) {
  return apiFetch<{ id: number }>(`/feishu-task-configs/${id}`, {
    method: 'PUT',
    body: JSON.stringify({ config }),
  })
}

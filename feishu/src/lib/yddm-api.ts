/**
 * 独立计费站（api.yddm.com）HTTP 封装，与 `lib/api.ts`（飞书插件后端）完全分离。
 * 响应体兼容 `message` 或 `msg` 字段。
 */

export const YDDM_API_BASE = 'https://api.yddm.com'

/** 与 `/auth/register` 入参一致 */
export interface YddmRegisterRequest {
  captcha: string
  email?: string
  password: string
  phone_num?: string
  [property: string]: unknown
}

type YddmEnvelope<T> = {
  code: number
  message?: string
  msg?: string
  data: T | null
}

function unwrapYddm<T>(body: unknown): T {
  if (!body || typeof body !== 'object' || !('code' in body)) {
    throw new Error('响应格式错误：缺少 code')
  }
  const o = body as YddmEnvelope<T>
  if (o.code !== 0) {
    const msg =
      (typeof o.message === 'string' && o.message.trim()) ||
      (typeof o.msg === 'string' && o.msg.trim()) ||
      `业务错误（code=${o.code}）`
    throw new Error(msg)
  }
  return o.data as T
}

export async function yddmPostJson<T>(path: string, body: unknown): Promise<T> {
  const url = `${YDDM_API_BASE}${path.startsWith('/') ? path : `/${path}`}`
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
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
    return unwrapYddm<T>(parsed)
  }
  if (!res.ok) {
    const detail = typeof parsed === 'string' ? parsed : JSON.stringify(parsed)
    throw new Error(`HTTP ${res.status}${detail ? `：${detail}` : ''}`)
  }
  return parsed as T
}

/** `POST /auth/register` */
export function yddmRegister(payload: YddmRegisterRequest) {
  return yddmPostJson<unknown>('/auth/register', payload)
}

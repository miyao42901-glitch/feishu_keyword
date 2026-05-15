/**
 * 独立计费站（api.yddm.com）HTTP 封装，与 `lib/api.ts`（飞书插件后端）完全分离。
 * 响应体兼容 `message` 或 `msg` 字段。
 *
 * - **本地 `npm run dev`**：默认请求同源 `/yddm-api`（见 `vite.config.ts` 代理），避免浏览器 CORS。
 * - **生产**：默认直连 `https://api.yddm.com`；若仍有 CORS，请在对方网关配置允许飞书页面 Origin，或设置 `VITE_YDDM_API_BASE` 为你方可控的反代地址。
 */

const YDDM_UPSTREAM = 'https://api.yddm.com'

/** 上游计费域（展示用） */
export const YDDM_UPSTREAM_ORIGIN = YDDM_UPSTREAM

/**
 * 实际发起 fetch 使用的根地址（无末尾 `/`）。
 * 优先级：`VITE_YDDM_API_BASE` → 开发模式为 `/yddm-api` → 否则为上游域名。
 */
export function getYddmApiBase(): string {
  const raw = (import.meta.env.VITE_YDDM_API_BASE as string | undefined)?.trim()
  if (raw) return raw.replace(/\/$/, '')
  if (import.meta.env.DEV) return '/yddm-api'
  return YDDM_UPSTREAM
}

/** 与 `/auth/register` 入参一致 */
export interface YddmRegisterRequest {
  captcha: string
  email?: string
  password: string
  phone_num?: string
  [property: string]: unknown
}

/** `POST /auth/login` — 插件侧仅传手机号与密码 */
export interface YddmLoginRequest {
  phone_num: string
  password: string
  [property: string]: unknown
}

/** `/auth/login` 成功时 `data` 结构（字段以实际接口为准） */
export interface YddmLoginUser {
  id: number
  email?: string
  phone_num?: string
  api_key: string
  balance_cents?: number
}

export interface YddmLoginData {
  access_token: string
  token_type: string
  user: YddmLoginUser
}

/**
 * `GET /users/me` 成功时 `data` 形态（与上游字段对齐；未文档字段可出现在对象上）。
 */
export interface YddmMeUser {
  id: number
  email?: string | null
  phone_num?: string | null
  api_key?: string
  balance_cents?: number
  [key: string]: unknown
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

async function yddmParseJsonResponse<T>(res: Response, parsed: unknown): Promise<T> {
  if (parsed && typeof parsed === 'object' && parsed !== null && 'code' in parsed) {
    return unwrapYddm<T>(parsed)
  }
  if (!res.ok) {
    const detail = typeof parsed === 'string' ? parsed : JSON.stringify(parsed)
    throw new Error(`HTTP ${res.status}${detail ? `：${detail}` : ''}`)
  }
  return parsed as T
}

export async function yddmPostJson<T>(path: string, body: unknown): Promise<T> {
  const url = `${getYddmApiBase()}${path.startsWith('/') ? path : `/${path}`}`
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
  return yddmParseJsonResponse<T>(res, parsed)
}

/** `GET` 请求；需鉴权时传入 `accessToken`（`Authorization: Bearer …`）。 */
export async function yddmGetJson<T>(
  path: string,
  opts?: { accessToken?: string; query?: Record<string, string | undefined> },
): Promise<T> {
  let url = `${getYddmApiBase()}${path.startsWith('/') ? path : `/${path}`}`
  if (opts?.query) {
    const params = new URLSearchParams()
    for (const [key, value] of Object.entries(opts.query)) {
      const v = value?.trim()
      if (v) params.set(key, v)
    }
    const qs = params.toString()
    if (qs) url += (url.includes('?') ? '&' : '?') + qs
  }
  const headers: Record<string, string> = { Accept: 'application/json' }
  const token = opts?.accessToken?.trim()
  if (token) headers.Authorization = `Bearer ${token}`
  const res = await fetch(url, { method: 'GET', headers })
  const text = await res.text()
  let parsed: unknown = null
  if (text) {
    try {
      parsed = JSON.parse(text) as unknown
    } catch {
      parsed = text
    }
  }
  return yddmParseJsonResponse<T>(res, parsed)
}

/** `GET /users/me` — 需登录态 `access_token`。 */
export function yddmFetchMe(accessToken: string) {
  return yddmGetJson<YddmMeUser>('/users/me', { accessToken })
}

/** `GET /auth/get_captcha` — query 入参 */
export interface YddmGetCaptchaRequest {
  /** 手机号 */
  phone_num?: string
  [property: string]: unknown
}

/** `POST /auth/register` */
export function yddmRegister(payload: YddmRegisterRequest) {
  return yddmPostJson<unknown>('/auth/register', payload)
}

/**
 * 图片验证码地址（`GET /auth/get_captcha` 返回图片，供 `<img src>` 使用，非 JSON 信封）。
 * `phone_num` 可选；`t` 防缓存。
 */
export function buildYddmCaptchaImageUrl(phoneNum?: string): string {
  const params = new URLSearchParams()
  const phone = phoneNum?.trim()
  if (phone) params.set('phone_num', phone)
  params.set('t', String(Date.now()))
  return `${getYddmApiBase()}/auth/get_captcha?${params.toString()}`
}

/** `POST /auth/login` */
export function yddmLogin(payload: YddmLoginRequest) {
  return yddmPostJson<YddmLoginData | null>('/auth/login', payload)
}

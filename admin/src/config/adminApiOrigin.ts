/** 管理后台 API 基址；可用 `.env.*` 或 `npm run dev` 的 `VITE_ADMIN_API_ORIGIN` 覆盖。 */
const DEFAULT_ORIGIN = 'https://test-fskw.tbpf.com'

const fromEnv = (() => {
  if (typeof process !== 'undefined' && process.env && typeof process.env.VITE_ADMIN_API_ORIGIN === 'string') {
    const p = process.env.VITE_ADMIN_API_ORIGIN.trim()
    if (p) return p
  }
  return (import.meta.env?.VITE_ADMIN_API_ORIGIN as string | undefined)?.trim()
})()

function resolveAdminApiOrigin(): string {
  const raw = (fromEnv || DEFAULT_ORIGIN).replace(/\/+$/, '')
  if (!raw) {
    return DEFAULT_ORIGIN
  }
  return raw
}

export const ADMIN_API_ORIGIN = resolveAdminApiOrigin() as string

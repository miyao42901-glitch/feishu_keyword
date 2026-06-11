/**
 * YDDM 登录/注册表单校验（与 `/auth/login` 等 body 约定一致）。
 */

export const YDDM_PASSWORD_MAX_LEN = 32

/** 中国大陆手机号：可选 +86 / 86 前缀与空格，主体须为 1[3-9] + 9 位数字 */
export const CN_MOBILE_RE = /^1[3-9]\d{9}$/
export const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export function normalizeCnMobileInput(raw: string): string {
  let t = raw.trim().replace(/\s+/g, '')
  if (t.startsWith('+86')) t = t.slice(3)
  else if (t.startsWith('86') && t.length === 13 && t[2] === '1') t = t.slice(2)
  return t
}

export function validateLoginPhoneOrEmail(
  _rule: unknown,
  value: unknown,
  callback: (e?: Error) => void,
) {
  const raw = typeof value === 'string' ? value : ''
  const s = raw.trim()
  if (!s) {
    callback(new Error('请输入手机号或邮箱'))
    return
  }
  if (s.includes('@')) {
    if (!EMAIL_RE.test(s)) {
      callback(new Error('邮箱格式不正确'))
      return
    }
    callback()
    return
  }
  const mobile = normalizeCnMobileInput(s)
  if (!CN_MOBILE_RE.test(mobile)) {
    callback(new Error('请输入11位中国大陆手机号（或带 @ 的邮箱）'))
    return
  }
  callback()
}

export function validateRegisterPhoneOptional(
  _rule: unknown,
  value: unknown,
  callback: (e?: Error) => void,
) {
  const s = typeof value === 'string' ? value.trim() : ''
  if (!s) {
    callback()
    return
  }
  const mobile = normalizeCnMobileInput(s)
  if (!CN_MOBILE_RE.test(mobile)) {
    callback(new Error('请输入11位中国大陆手机号'))
    return
  }
  callback()
}

/** 注册提交时给邮箱本地部分加 `fs_` 前缀（已有则不再重复添加） */
export function prefixRegisterEmail(raw: string): string {
  const email = raw.trim()
  if (!email) return ''
  const at = email.indexOf('@')
  if (at <= 0) return email
  const localPart = email.slice(0, at)
  const domain = email.slice(at)
  const prefix = 'fs_'
  const normalizedLocal = localPart.startsWith(prefix) ? localPart : `${prefix}${localPart}`
  return `${normalizedLocal}${domain}`
}

/** 选填邮箱：空则通过，否则校验格式 */
export function validateOptionalEmail(_rule: unknown, value: unknown, callback: (e?: Error) => void) {
  const s = typeof value === 'string' ? value.trim() : ''
  if (!s) {
    callback()
    return
  }
  if (!EMAIL_RE.test(s)) {
    callback(new Error('邮箱格式不正确'))
    return
  }
  callback()
}

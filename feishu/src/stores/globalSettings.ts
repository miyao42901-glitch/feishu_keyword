import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

/** 与 `api.ts` 请求头一致：持久化 YDDM API Key（授权码） */
export const GLOBAL_AUTH_CODE_STORAGE_KEY = 'feishu_keyword_global_auth_code'

/** 账户级通知（如积分不足）使用的 Webhook，由最近保存的已开启通知任务同步 */
export const GLOBAL_NOTIFY_WEBHOOK_STORAGE_KEY = 'feishu_keyword_global_notify_webhook'

export function readGlobalNotifyWebhook(): string | null {
  try {
    const raw = localStorage.getItem(GLOBAL_NOTIFY_WEBHOOK_STORAGE_KEY)
    const url = typeof raw === 'string' ? raw.trim() : ''
    return url || null
  } catch {
    return null
  }
}

export function rememberGlobalNotifyWebhook(url: string): void {
  const trimmed = url.trim()
  if (!trimmed) return
  try {
    localStorage.setItem(GLOBAL_NOTIFY_WEBHOOK_STORAGE_KEY, trimmed)
  } catch {
    /* 忽略 */
  }
}

/**
 * 跨任务共享的配置（如 API 授权码），与单条 `config_json` 解耦，仅前端持久化。
 */
export const useGlobalSettingsStore = defineStore('globalSettings', () => {
  const authCode = ref('')

  try {
    const raw = localStorage.getItem(GLOBAL_AUTH_CODE_STORAGE_KEY)
    if (typeof raw === 'string') authCode.value = raw
  } catch {
    /* 忽略无痕模式等 */
  }

  watch(authCode, (v) => {
    try {
      localStorage.setItem(GLOBAL_AUTH_CODE_STORAGE_KEY, v)
    } catch {
      /* 忽略 */
    }
  })

  return { authCode }
})

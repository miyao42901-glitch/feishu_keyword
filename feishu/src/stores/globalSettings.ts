import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

/** 与 `api.ts` 请求头一致：持久化 YDDM API Key（授权码） */
export const GLOBAL_AUTH_CODE_STORAGE_KEY = 'feishu_keyword_global_auth_code'

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

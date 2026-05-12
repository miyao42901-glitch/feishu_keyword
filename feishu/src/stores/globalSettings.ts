import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

const AUTH_CODE_STORAGE_KEY = 'feishu_keyword_global_auth_code'

/**
 * 跨任务共享的配置（如 API 授权码），与单条 `config_json` 解耦，仅前端持久化。
 */
export const useGlobalSettingsStore = defineStore('globalSettings', () => {
  const authCode = ref('')

  try {
    const raw = localStorage.getItem(AUTH_CODE_STORAGE_KEY)
    if (typeof raw === 'string') authCode.value = raw
  } catch {
    /* 忽略无痕模式等 */
  }

  watch(authCode, (v) => {
    try {
      localStorage.setItem(AUTH_CODE_STORAGE_KEY, v)
    } catch {
      /* 忽略 */
    }
  })

  return { authCode }
})

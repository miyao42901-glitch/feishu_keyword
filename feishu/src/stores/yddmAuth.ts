import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { yddmFetchMe, type YddmLoginData, type YddmMeUser } from '@/lib/yddm-api'

const ACCESS_TOKEN_STORAGE_KEY = 'feishu_keyword_yddm_access_token'

/**
 * YDDM 登录态：`access_token` 持久化，个人信息由 `GET /users/me` 刷新。
 */
export const useYddmAuthStore = defineStore('yddmAuth', () => {
  const accessToken = ref('')
  const me = ref<YddmMeUser | null>(null)

  function loadTokenFromStorage() {
    try {
      const raw = localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY)
      if (typeof raw === 'string') accessToken.value = raw
    } catch {
      /* 忽略 */
    }
  }

  loadTokenFromStorage()

  const isLoggedIn = computed(() => Boolean(accessToken.value?.trim()))

  function persistAccessToken(token: string) {
    accessToken.value = token
    try {
      localStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, token)
    } catch {
      /* 忽略 */
    }
  }

  /** 登录接口成功后写入 token，并暂用登录返回的 `user` 填充展示（随后可 `refreshMe`） */
  function setFromLogin(data: YddmLoginData | null | undefined) {
    const tok = data?.access_token?.trim()
    if (!tok) return
    persistAccessToken(tok)
    if (data?.user) {
      me.value = { ...data.user } as YddmMeUser
    }
  }

  function clearSession() {
    accessToken.value = ''
    me.value = null
    try {
      localStorage.removeItem(ACCESS_TOKEN_STORAGE_KEY)
    } catch {
      /* 忽略 */
    }
  }

  /** 调用 `GET /users/me` 更新 `me`；失败时抛出（由调用方决定是否清 session） */
  async function refreshMe() {
    const tok = accessToken.value?.trim()
    if (!tok) {
      me.value = null
      return null
    }
    const u = await yddmFetchMe(tok)
    if (!u || typeof u !== 'object') {
      throw new Error('个人信息为空')
    }
    me.value = u
    return u
  }

  return {
    accessToken,
    me,
    isLoggedIn,
    setFromLogin,
    clearSession,
    refreshMe,
  }
})

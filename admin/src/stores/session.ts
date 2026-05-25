import { defineStore } from 'pinia'
import { ref } from 'vue'

const STORAGE_KEY = 'fkw_admin_token'

export const useSessionStore = defineStore('session', () => {
  const token = ref<string>(localStorage.getItem(STORAGE_KEY) || '')

  function setToken(t: string) {
    token.value = t
    localStorage.setItem(STORAGE_KEY, t)
  }

  function clear() {
    token.value = ''
    localStorage.removeItem(STORAGE_KEY)
  }

  return { token, setToken, clear }
})

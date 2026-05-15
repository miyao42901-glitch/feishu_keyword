import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

const BALANCE_STORAGE_KEY = 'feishu_keyword_account_balance_points'

const DEFAULT_BALANCE = 500

function readBalanceFromStorage(): number {
  try {
    const raw = localStorage.getItem(BALANCE_STORAGE_KEY)
    if (raw == null || raw === '') return DEFAULT_BALANCE
    const n = Number(raw)
    if (!Number.isFinite(n) || n < 0) return DEFAULT_BALANCE
    return Math.floor(n)
  } catch {
    return DEFAULT_BALANCE
  }
}

/**
 * 账户点数余额（前端展示）；默认 500，持久化便于后续对接登录/计费接口后写入。
 */
export const useAccountPointsStore = defineStore('accountPoints', () => {
  const currentBalancePoints = ref(readBalanceFromStorage())

  watch(currentBalancePoints, (v) => {
    try {
      localStorage.setItem(BALANCE_STORAGE_KEY, String(v))
    } catch {
      /* 忽略 */
    }
  })

  function setCurrentBalancePoints(n: number) {
    if (!Number.isFinite(n) || n < 0) return
    currentBalancePoints.value = Math.floor(n)
  }

  /** 退出登录或未接入计费资料时恢复默认展示用余额 */
  function resetToDefaultBalance() {
    setCurrentBalancePoints(DEFAULT_BALANCE)
  }

  return { currentBalancePoints, setCurrentBalancePoints, resetToDefaultBalance }
})

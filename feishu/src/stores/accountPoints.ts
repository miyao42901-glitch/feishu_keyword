import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { parseYddmUserBalancePoints } from '@/lib/account-balance'
import type { YddmLoginUser, YddmMeUser } from '@/lib/yddm-api'

const BALANCE_STORAGE_KEY = 'feishu_keyword_account_balance_points'

function readBalanceFromStorage(): number {
  try {
    const raw = localStorage.getItem(BALANCE_STORAGE_KEY)
    if (raw == null || raw === '') return 0
    const n = Number(raw)
    if (!Number.isFinite(n) || n < 0) return 0
    return Math.floor(n)
  } catch {
    return 0
  }
}

/**
 * 账户积分余额（与 YDDM 登录态同步，用于任务预估对比）。
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

  /** 用登录/个人信息中的积分余额覆盖本地缓存 */
  function syncFromYddmUser(user: YddmMeUser | YddmLoginUser | null | undefined) {
    const pts = parseYddmUserBalancePoints(user)
    if (pts != null) setCurrentBalancePoints(pts)
  }

  /** 退出登录后清空展示用余额 */
  function resetToDefaultBalance() {
    setCurrentBalancePoints(0)
  }

  return { currentBalancePoints, setCurrentBalancePoints, syncFromYddmUser, resetToDefaultBalance }
})

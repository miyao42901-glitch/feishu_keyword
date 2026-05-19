/**
 * 采集等扣费操作后刷新 YDDM 用户信息（含 `balance_cents` / 积分余额）。
 */

import { useAccountPointsStore } from '@/stores/accountPoints'
import { useYddmAuthStore } from '@/stores/yddmAuth'

const MIN_REFRESH_INTERVAL_MS = 1500

let inflight: Promise<void> | null = null
let lastSuccessAt = 0

/** `GET /users/me` 并同步顶部积分展示；未登录或节流窗口内则跳过 */
export function refreshYddmUserBalance(): Promise<void> {
  if (inflight) return inflight

  const yddmAuth = useYddmAuthStore()
  if (!yddmAuth.isLoggedIn) return Promise.resolve()

  const now = Date.now()
  if (now - lastSuccessAt < MIN_REFRESH_INTERVAL_MS) return Promise.resolve()

  inflight = (async () => {
    try {
      const u = await yddmAuth.refreshMe()
      useAccountPointsStore().syncFromYddmUser(u)
      lastSuccessAt = Date.now()
    } catch {
      /* 余额刷新失败不阻断采集主流程 */
    } finally {
      inflight = null
    }
  })()

  return inflight
}

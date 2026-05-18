import type { YddmMeUser } from '@/lib/yddm-api'

/** 每条采集数据消耗的积分（与产品计费口径一致） */
export const POINTS_PER_DATA_ROW = 100

type YddmUserLike = Pick<YddmMeUser, 'balance_cents'> & {
  balance_points?: number
  balancePoints?: number
}

/**
 * 从 YDDM 登录/个人信息解析积分余额（整数）。
 * 优先 `balance_points`；否则将 `balance_cents` 视为积分余额（不做分→元换算）。
 */
export function parseYddmUserBalancePoints(user: YddmUserLike | null | undefined): number | null {
  if (!user || typeof user !== 'object') return null
  const o = user as Record<string, unknown>
  const rawPoints = o.balance_points ?? o.balancePoints
  if (typeof rawPoints === 'number' && Number.isFinite(rawPoints)) {
    return Math.max(0, Math.floor(rawPoints))
  }
  const cents = user.balance_cents
  if (typeof cents === 'number' && Number.isFinite(cents)) {
    return Math.max(0, Math.floor(cents))
  }
  return null
}

export function formatPointsBalance(points: number | null | undefined): string {
  if (points == null || !Number.isFinite(points)) return '—'
  return `${Math.floor(points).toLocaleString('zh-CN')} 积分`
}

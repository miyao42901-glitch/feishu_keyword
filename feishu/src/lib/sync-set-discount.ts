/**
 * 采集前设置用户折扣：`POST /admin/set_discount`（YDDM 域，与登录注册同源）
 */

import type { SyncFetchContext } from '@/lib/sync-api-common'
import { yddmPostJson } from '@/lib/yddm-api'
import { normalizeCnMobileInput } from '@/lib/yddm-auth-validators'
import { useYddmAuthStore } from '@/stores/yddmAuth'

const SET_DISCOUNT_PATH = '/admin/set_discount'

/** YDDM `set_discount` 的 endpoint（与采集 search-page 路径不同） */
export const DOUYIN_DISCOUNT_ENDPOINT = '/douyin/general_search'
export const XHS_DISCOUNT_ENDPOINT = '/xhs/search_note_app'

/** @deprecated 使用 `DOUYIN_DISCOUNT_ENDPOINT` */
export const DOUYIN_SYNC_ENDPOINT = DOUYIN_DISCOUNT_ENDPOINT
/** @deprecated 使用 `XHS_DISCOUNT_ENDPOINT` */
export const XHS_SYNC_ENDPOINT = XHS_DISCOUNT_ENDPOINT

/** 抖音：1000 / 150 */
export const DOUYIN_DISCOUNT_RATE = 1000 / 150
/** 小红书：2000 / 100 */
export const XHS_DISCOUNT_RATE = 2000 / 100

/** 折扣最多保留两位小数（接口要求） */
export function formatDiscountRate(rate: number): number {
  if (!Number.isFinite(rate)) return 0
  return Math.round(rate * 100) / 100
}

export type SetDiscountRequest = {
  discount_rate: number
  endpoint: string
  phone_num: string
  [property: string]: unknown
}

const appliedKeys = new Set<string>()

function resolvePhoneNumFromCtx(ctx: SyncFetchContext): string {
  const raw = ctx.phoneNum
  if (raw == null) return ''
  const s = String(raw).trim()
  if (!s) return ''
  return normalizeCnMobileInput(s)
}

async function resolvePhoneNum(ctx: SyncFetchContext): Promise<string> {
  const direct = resolvePhoneNumFromCtx(ctx)
  if (direct) return direct

  const yddmAuth = useYddmAuthStore()
  const cached = yddmAuth.me?.phone_num
  if (cached != null && String(cached).trim()) {
    return normalizeCnMobileInput(String(cached))
  }
  if (yddmAuth.isLoggedIn) {
    const u = await yddmAuth.refreshMe()
    if (u?.phone_num != null && String(u.phone_num).trim()) {
      return normalizeCnMobileInput(String(u.phone_num))
    }
  }
  return ''
}

export function resolveDiscountForSyncPath(
  path: string,
): { endpoint: string; discount_rate: number } | null {
  const p = path.trim()
  if (p.includes('/douyin/')) {
    return {
      endpoint: DOUYIN_DISCOUNT_ENDPOINT,
      discount_rate: formatDiscountRate(DOUYIN_DISCOUNT_RATE),
    }
  }
  if (p.includes('/xhs/')) {
    return {
      endpoint: XHS_DISCOUNT_ENDPOINT,
      discount_rate: formatDiscountRate(XHS_DISCOUNT_RATE),
    }
  }
  return null
}

async function postSetDiscount(body: SetDiscountRequest): Promise<void> {
  const yddmAuth = useYddmAuthStore()
  const accessToken = yddmAuth.accessToken?.trim()
  await yddmPostJson<unknown>(SET_DISCOUNT_PATH, body, {
    accessToken: accessToken || undefined,
  })
}

/** 按 endpoint 设置折扣（同会话同参数只请求一次；失败不阻断后续采集） */
export async function ensureSyncEndpointDiscount(input: {
  endpoint: string
  discountRate: number
  ctx: SyncFetchContext
}): Promise<void> {
  const phone_num = await resolvePhoneNum(input.ctx)
  if (!phone_num) return

  const endpoint = input.endpoint.trim()
  const discount_rate = formatDiscountRate(input.discountRate)
  const cacheKey = `${phone_num}|${endpoint}|${discount_rate}`
  if (appliedKeys.has(cacheKey)) return

  try {
    await postSetDiscount({ discount_rate, endpoint, phone_num })
    appliedKeys.add(cacheKey)
  } catch {
    /* 折扣设置失败不阻断 search-page / async 采集 */
  }
}

export async function ensureSyncEndpointDiscountForPath(
  path: string,
  ctx: SyncFetchContext,
): Promise<void> {
  const spec = resolveDiscountForSyncPath(path)
  if (!spec) return
  await ensureSyncEndpointDiscount({
    endpoint: spec.endpoint,
    discountRate: spec.discount_rate,
    ctx,
  })
}

export async function ensureSyncEndpointDiscountForPlatform(
  platform: 'douyin' | 'xiaohongshu',
  ctx: SyncFetchContext,
): Promise<void> {
  if (platform === 'douyin') {
    await ensureSyncEndpointDiscount({
      endpoint: DOUYIN_DISCOUNT_ENDPOINT,
      discountRate: DOUYIN_DISCOUNT_RATE,
      ctx,
    })
    return
  }
  await ensureSyncEndpointDiscount({
    endpoint: XHS_DISCOUNT_ENDPOINT,
    discountRate: XHS_DISCOUNT_RATE,
    ctx,
  })
}

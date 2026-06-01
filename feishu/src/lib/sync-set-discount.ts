/**
 * 采集前设置用户折扣：`POST /admin/set_discount`（YDDM 域，与登录注册同源）
 *
 * 计费目标：每条数据 **100 积分**。
 * `discount_rate` = 积分档位 ÷ 100（表示单次 search-page 典型返回条数，传给 YDDM；
 * 与 `sync-platform-page-size` 翻页逻辑一致）。
 */

import type { PlatformKey } from '@/components/PlatformIcon.vue'
import type { SyncFetchContext } from '@/lib/sync-api-common'
import { yddmPostJson } from '@/lib/yddm-api'
import { normalizeCnMobileInput } from '@/lib/yddm-auth-validators'
import { useYddmAuthStore } from '@/stores/yddmAuth'

const SET_DISCOUNT_PATH = '/admin/set_discount'

/** 每条采集数据目标扣费（积分） */
export const TARGET_POINTS_PER_ROW = 100

/** YDDM `set_discount` 的 endpoint（与采集 search-page 路径不同） */
export const DOUYIN_DISCOUNT_ENDPOINT = '/douyin/general_search'
export const XHS_DISCOUNT_ENDPOINT = '/xhs/search_note_app'
/** 视频号 / 公众号（微信搜一搜） */
export const WX_SOUSOU_DISCOUNT_ENDPOINT = '/wx/sousou'

/** @deprecated 使用 `DOUYIN_DISCOUNT_ENDPOINT` */
export const DOUYIN_SYNC_ENDPOINT = DOUYIN_DISCOUNT_ENDPOINT
/** @deprecated 使用 `XHS_DISCOUNT_ENDPOINT` */
export const XHS_SYNC_ENDPOINT = XHS_DISCOUNT_ENDPOINT

/** 抖音积分档位（与后台套餐一致） */
export const DOUYIN_POINTS_PACKAGE = 1000
/** 小红书积分档位 */
export const XHS_POINTS_PACKAGE = 2000
/** 视频号 / 公众号积分档位 */
export const WX_SOUSOU_POINTS_PACKAGE = 1500

/** 折扣最多保留两位小数（接口要求） */
export function formatDiscountRate(rate: number): number {
  if (!Number.isFinite(rate)) return 0
  return Math.round(rate * 100) / 100
}

/**
 * 按「每条 {@link TARGET_POINTS_PER_ROW} 积分」从积分档位推导 `discount_rate`。
 * 例：1000 分档 → rate=10（1000÷100，约 10 条/档）；1500 分档 → rate=15。
 */
export function discountRateForPackage(
  pointsPackage: number,
  pointsPerRow: number = TARGET_POINTS_PER_ROW,
): number {
  if (!Number.isFinite(pointsPackage) || pointsPerRow <= 0) return 0
  return formatDiscountRate(pointsPackage / pointsPerRow)
}

/** 抖音：1000 积分档 → discount_rate 10（每条 100 积分） */
export const DOUYIN_DISCOUNT_RATE = discountRateForPackage(DOUYIN_POINTS_PACKAGE)
/** 小红书：2000 积分档 → discount_rate 20 */
export const XHS_DISCOUNT_RATE = discountRateForPackage(XHS_POINTS_PACKAGE)
/** 视频号 / 公众号：固定 discount_rate 1（按后端要求） */
export const WX_SOUSOU_DISCOUNT_RATE = 1

/** 视频号 / 公众号单次 search-page 典型返回条数（翻页与积分预估；与 {@link WX_SOUSOU_DISCOUNT_RATE} 分离） */
export const WX_SOUSOU_EXPECTED_PAGE_ROWS = 15

/** 按积分档位与 discount_rate，折算每条积分（应等于 {@link TARGET_POINTS_PER_ROW}） */
export function pointsPerRowFromDiscountPackage(
  pointsPackage: number,
  rowsPerPackage: number,
): number {
  if (!Number.isFinite(pointsPackage) || !Number.isFinite(rowsPerPackage) || rowsPerPackage <= 0) {
    return 0
  }
  return pointsPackage / rowsPerPackage
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
      discount_rate: DOUYIN_DISCOUNT_RATE,
    }
  }
  if (p.includes('/xhs/')) {
    return {
      endpoint: XHS_DISCOUNT_ENDPOINT,
      discount_rate: XHS_DISCOUNT_RATE,
    }
  }
  if (p.includes('/wxvideo/') || p.includes('/wx/')) {
    return {
      endpoint: WX_SOUSOU_DISCOUNT_ENDPOINT,
      discount_rate: WX_SOUSOU_DISCOUNT_RATE,
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

/** 该平台一次采集对应的积分档位（展示/预估用，与 `set_discount` 套餐一致） */
export function syncPointsPackageForPlatform(platform: PlatformKey): number {
  switch (platform) {
    case 'douyin':
      return DOUYIN_POINTS_PACKAGE
    case 'xiaohongshu':
      return XHS_POINTS_PACKAGE
    case 'shipinhao':
    case 'gzh':
      return WX_SOUSOU_POINTS_PACKAGE
    default:
      return 0
  }
}

/** 切换平台前重置折扣会话，避免上一平台「已计费」标记影响下一平台 */
export function resetPlatformSyncBillingSession(ctx: SyncFetchContext): SyncFetchContext {
  return { ...ctx, platformDiscountPrimed: false }
}

/** search-page 成功响应后，按路径触发一次 `set_discount`（同平台翻页不重复请求） */
export async function primeSyncEndpointDiscountAfterSuccess(
  path: string,
  ctx: SyncFetchContext,
): Promise<void> {
  if (ctx.skipSetDiscount || ctx.platformDiscountPrimed) return
  await ensureSyncEndpointDiscountForPath(path, ctx)
  ctx.platformDiscountPrimed = true
}

export async function ensureSyncEndpointDiscountForPlatform(
  platform: 'douyin' | 'xiaohongshu' | 'shipinhao' | 'gzh',
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
  if (platform === 'xiaohongshu') {
    await ensureSyncEndpointDiscount({
      endpoint: XHS_DISCOUNT_ENDPOINT,
      discountRate: XHS_DISCOUNT_RATE,
      ctx,
    })
    return
  }
  if (platform === 'shipinhao' || platform === 'gzh') {
    return
  }
}

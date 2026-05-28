/**
 * 各平台 search-page 单次接口典型返回条数（用于翻页与积分预估）。
 * 抖音/小红书与 `set_discount` 的 discount_rate 一致；视频号/公众号 discount_rate 固定为 1，翻页按 {@link WX_SOUSOU_EXPECTED_PAGE_ROWS}。
 */

import type { PlatformKey } from '@/components/PlatformIcon.vue'
import {
  DOUYIN_DISCOUNT_RATE,
  WX_SOUSOU_EXPECTED_PAGE_ROWS,
  XHS_DISCOUNT_RATE,
} from '@/lib/sync-set-discount'

const PAGE_ROWS: Partial<Record<PlatformKey, number>> = {
  douyin: DOUYIN_DISCOUNT_RATE,
  xiaohongshu: XHS_DISCOUNT_RATE,
  shipinhao: WX_SOUSOU_EXPECTED_PAGE_ROWS,
  gzh: WX_SOUSOU_EXPECTED_PAGE_ROWS,
}

/** 单次 search-page 典型返回条数（抖音约 10、小红书约 20、视频号/公众号约 15） */
export function expectedApiPageRows(platform: PlatformKey): number {
  const n = PAGE_ROWS[platform]
  return n != null && n > 0 ? n : 10
}

/** 为凑满 `requestedRows` 条，粗略需要的请求次数（上限估算） */
export function estimatedApiPagesNeeded(requestedRows: number, platform: PlatformKey): number {
  const perPage = expectedApiPageRows(platform)
  if (perPage <= 0) return 1
  return Math.max(1, Math.ceil(Math.max(0, requestedRows) / perPage))
}

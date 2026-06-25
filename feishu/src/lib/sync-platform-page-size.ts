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

/** 表单 `dataRange` 合法页数（与 {@link dataRangeOptions} 一致） */
export function normalizeDataPageCount(raw: unknown): number {
  const n = typeof raw === 'number' ? raw : Number(raw)
  if (!Number.isFinite(n) || n < 1) return 10
  const pages = Math.floor(n)
  const allowed = [1, 2, 5, 10, 20, 50] as const
  if ((allowed as readonly number[]).includes(pages)) return pages
  const legacyRowCounts = [10, 20, 30, 50, 70, 100]
  if (legacyRowCounts.includes(pages)) {
    const est = Math.max(1, Math.ceil(pages / 10))
    let best: number = allowed[0]
    let diff = Math.abs(est - best)
    for (const p of allowed) {
      const d = Math.abs(est - p)
      if (d < diff) {
        best = p
        diff = d
      }
    }
    return best
  }
  return Math.min(50, Math.max(1, pages))
}

/** 页数 × 平台单次典型条数 → 定时任务 `fetch_count` 上限 */
export function fetchCountFromDataPages(pageCount: number, platform: PlatformKey): number {
  const pages = normalizeDataPageCount(pageCount)
  return Math.min(500, Math.max(1, estimatedRowsFromPages(pages, platform)))
}

export function estimatedRowsFromPages(pageCount: number, platform: PlatformKey): number {
  const pages = normalizeDataPageCount(pageCount)
  return pages * expectedApiPageRows(platform)
}

/** 从服务端 `fetch_count` 反推表单页数 */
export function dataPagesFromFetchCount(fetchCount: number, platform: PlatformKey): number {
  const perPage = expectedApiPageRows(platform)
  if (perPage <= 0) return normalizeDataPageCount(1)
  return normalizeDataPageCount(Math.ceil(Math.max(1, fetchCount) / perPage))
}

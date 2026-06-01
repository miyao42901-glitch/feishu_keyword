/**
 * 抖音搜索同步：`POST /api/v1/sync/douyin/search-page`
 *
 * 翻页：单次约 {@link expectedApiPageRows}('douyin') 条；未凑满 `dataRange` 时用
 * `next_cursor` / `next_logid` 继续请求，直至达到上限或无更多数据。
 */

import type { SyncFetchContext } from '@/lib/sync-api-common'
import {
  extractSyncResultItems,
  extractSyncResultPageMeta,
  normalizePaginationToken,
} from '@/lib/sync-api-common'
import { expectedApiPageRows } from '@/lib/sync-platform-page-size'
import {
  assertKeywordLength,
  buildExcludeWords,
  mapNoteTime,
  mapSortType,
  mergeResultItems,
  postSyncSearchPage,
  readDataRange,
  readSearchKeywords,
  type SyncSortType,
} from '@/lib/sync-search-shared'

/** 内容形式：0 不限，1 视频，2 图文 */
export type DouyinContentType = '0' | '1' | '2'

export type DouyinFilterDuration = '0' | '0-1' | '1-5' | '1-10000'

/**
 * 抖音 search-page 请求体。
 * 首屏不传 `cursor` / `log_id`；翻页传上一页返回的 `next_cursor` / `next_logid`。
 */
export type DouyinSearchPageRequestBody = {
  keyword: string
  exclude_words: string
  content_type?: DouyinContentType
  cursor?: string
  log_id?: string
  publish_time?: string
  sort_type?: SyncSortType
  filter_duration?: DouyinFilterDuration
  [property: string]: unknown
}

function mapFilterDuration(videoDuration: string): DouyinFilterDuration {
  switch (videoDuration.trim()) {
    case 'lt1m':
      return '0-1'
    case '1to5m':
      return '1-5'
    case 'gt5m':
      return '1-10000'
    default:
      return '0'
  }
}

export function buildDouyinSearchPageBody(
  config: Record<string, unknown>,
  keyword: string,
  page?: { cursor?: string | number; logId?: string | number },
): DouyinSearchPageRequestBody {
  const body: DouyinSearchPageRequestBody = {
    keyword: assertKeywordLength(keyword),
    exclude_words: buildExcludeWords(config),
    content_type: '0',
    sort_type: mapSortType(String(config.sortOrder ?? config.sort_order ?? 'default')),
    publish_time: mapNoteTime(String(config.publishTime ?? config.publish_time ?? 'unlimited')),
    filter_duration: mapFilterDuration(
      String(config.videoDuration ?? config.video_duration ?? 'all'),
    ),
  }

  const cursor = normalizePaginationToken(page?.cursor)
  if (cursor) body.cursor = cursor

  const logId = normalizePaginationToken(page?.logId)
  if (logId) body.log_id = logId

  return body
}

/** @deprecated 使用 `buildDouyinSearchPageBody` */
export const buildSyncSearchPageBody = buildDouyinSearchPageBody

/** @deprecated 使用 `DouyinSearchPageRequestBody` */
export type SyncSearchPageRequestBody = DouyinSearchPageRequestBody

/** 防止翻页异常时死循环 */
const DOUYIN_MAX_PAGES = 50

export async function fetchDouyinSearchItems(
  config: Record<string, unknown>,
  ctx: SyncFetchContext,
): Promise<Record<string, unknown>[]> {
  const keywords = readSearchKeywords(config)
  const limit = readDataRange(config)
  const rowsPerPage = expectedApiPageRows('douyin')
  const collected: Record<string, unknown>[] = []
  const seenIds = new Set<string>()
  const path = '/api/v1/sync/douyin/search-page'

  for (const keyword of keywords) {
    let cursor: string | undefined
    let logId: string | undefined
    let pageCount = 0

    while (collected.length < limit && pageCount < DOUYIN_MAX_PAGES) {
      pageCount += 1
      const payload = await postSyncSearchPage({
        path,
        platformLabel: '抖音',
        ctx,
        body: buildDouyinSearchPageBody(
          config,
          keyword,
          cursor || logId ? { cursor, logId } : undefined,
        ),
      })
      const batch = extractSyncResultItems(payload)
      const before = collected.length
      if (
        mergeResultItems({
          batch,
          collected,
          seenIds,
          itemIdKeys: ['aweme_id', 'awemeId'],
          limit,
          platformKey: 'douyin',
        })
      ) {
        break
      }
      if (!batch.length) break
      /* 本页有数据但去重后无新增：避免 has_more 导致重复打满 search-page */
      if (collected.length === before) break

      const pageMeta = extractSyncResultPageMeta(payload)
      const nextCursor = pageMeta.nextCursor
      const nextLogId = pageMeta.nextLogid
      const canContinue = pageMeta.hasMore || Boolean(nextCursor || nextLogId)
      const remaining = limit - collected.length

      if (import.meta.env.DEV) {
        console.log('[douyin-search-page]', {
          keyword,
          page: pageCount,
          batch: batch.length,
          added: collected.length - before,
          total: collected.length,
          limit,
          remaining,
          hasMore: pageMeta.hasMore,
          nextCursor,
          nextLogId,
        })
      }

      if (collected.length >= limit) break
      if (remaining <= 0) break
      /* 本页不足一页且无更多 → 不翻页（与小红书/微信逻辑一致） */
      if (batch.length < rowsPerPage && !pageMeta.hasMore) break
      if (!pageMeta.hasMore && batch.length < remaining) break
      if (!canContinue) break

      cursor = nextCursor
      logId = nextLogId
    }

    if (collected.length >= limit) break
  }

  return collected
}

/** @deprecated 使用 `fetchDouyinSearchItems` */
export const fetchSyncSearchItems = fetchDouyinSearchItems

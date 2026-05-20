/**
 * 小红书搜索同步：`POST /api/v1/sync/xhs/search-page`
 *
 * 翻页：单次约 {@link expectedApiPageRows}('xiaohongshu') 条（通常 20）。
 * 选择 20 条且首屏已满 20 条时不再请求第 2 页；不足 20 条且仍有 `has_more` 时翻页。
 */

import { extractSyncResultItems, extractSyncResultPageMeta } from '@/lib/sync-api-common'
import type { SyncFetchContext } from '@/lib/sync-api-common'
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

const XHS_SEARCH_PAGE_PATH = '/api/v1/sync/xhs/search-page'

/** 最大翻页次数，防止异常时死循环 */
const XHS_MAX_PAGES = 50

/**
 * 小红书 search-page 请求体（Apifox）。
 * `content_type`：`0` 不限，`1` 图文，`2` 视频。
 */
export type XhsSearchPageRequestBody = {
  keyword: string
  exclude_words: string
  content_type: string
  note_time: string
  page: number
  sort_type: string
  [property: string]: unknown
}

export function buildXhsSearchPageBody(
  config: Record<string, unknown>,
  keyword: string,
  page: number,
): XhsSearchPageRequestBody {
  return {
    keyword: assertKeywordLength(keyword),
    exclude_words: buildExcludeWords(config),
    content_type: '0',
    note_time: mapNoteTime(String(config.publishTime ?? config.publish_time ?? 'unlimited')),
    page: Math.max(1, Math.floor(page)),
    sort_type: mapSortType(String(config.sortOrder ?? config.sort_order ?? 'default')) as SyncSortType,
  }
}

export async function postXhsSearchPage(input: {
  body: XhsSearchPageRequestBody
  ctx: SyncFetchContext
}): Promise<unknown> {
  return postSyncSearchPage({
    path: XHS_SEARCH_PAGE_PATH,
    platformLabel: '小红书',
    body: input.body,
    ctx: input.ctx,
  })
}

export async function fetchXhsSearchItems(
  config: Record<string, unknown>,
  ctx: SyncFetchContext,
): Promise<Record<string, unknown>[]> {
  const keywords = readSearchKeywords(config)
  const limit = readDataRange(config)
  const rowsPerPage = expectedApiPageRows('xiaohongshu')
  const collected: Record<string, unknown>[] = []
  const seenIds = new Set<string>()

  for (const keyword of keywords) {
    let pageNum = 1

    while (collected.length < limit && pageNum <= XHS_MAX_PAGES) {
      const payload = await postXhsSearchPage({
        ctx,
        body: buildXhsSearchPageBody(config, keyword, pageNum),
      })
      const batch = extractSyncResultItems(payload)
      const before = collected.length
      if (
        mergeResultItems({
          batch,
          collected,
          seenIds,
          itemIdKeys: ['note_id', 'noteId'],
          limit,
        })
      ) {
        break
      }
      if (!batch.length) break

      const pageMeta = extractSyncResultPageMeta(payload)
      const remaining = limit - collected.length

      if (import.meta.env.DEV) {
        console.log('[xhs-search-page]', {
          keyword,
          page: pageNum,
          batch: batch.length,
          added: collected.length - before,
          total: collected.length,
          limit,
          remaining,
          hasMore: pageMeta.hasMore,
        })
      }

      if (collected.length >= limit) break
      /* 已凑满或本页不足一页且无更多 → 不翻页 */
      if (remaining <= 0) break
      if (batch.length < rowsPerPage && !pageMeta.hasMore) break
      if (!pageMeta.hasMore && batch.length < remaining) break

      pageNum += 1
    }

    if (collected.length >= limit) break
  }

  return collected.slice(0, limit)
}

/**
 * 小红书搜索同步：`POST /api/v1/sync/xhs/search-page`
 *
 * 翻页：按表单「作品数据范围」固定请求对应页数（`page` 递增）。
 */

import { extractSyncResultItems, extractSyncResultPageMeta } from '@/lib/sync-api-common'
import type { SyncFetchContext } from '@/lib/sync-api-common'
import {
  assertKeywordLength,
  buildExcludeWords,
  mapNoteTime,
  mapSortType,
  mergeResultItems,
  postSyncSearchPage,
  readConfiguredSearchPageCount,
  readSearchKeywords,
  type SyncSortType,
} from '@/lib/sync-search-shared'

const XHS_SEARCH_PAGE_PATH = '/api/v1/sync/xhs/search-page'

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
  const pageCount = readConfiguredSearchPageCount(config)
  const collected: Record<string, unknown>[] = []
  const seenIds = new Set<string>()

  for (const keyword of keywords) {
    for (let pageNum = 1; pageNum <= pageCount; pageNum++) {
      const payload = await postXhsSearchPage({
        ctx,
        body: buildXhsSearchPageBody(config, keyword, pageNum),
      })
      const batch = extractSyncResultItems(payload)
      const before = collected.length
      mergeResultItems({
        batch,
        collected,
        seenIds,
        itemIdKeys: [
          'post_id',
          'postId',
          'note_id',
          'noteId',
          'noteid',
          'id',
          'note_card_id',
          'noteCardId',
        ],
        platformKey: 'xiaohongshu',
      })

      if (import.meta.env.DEV) {
        console.log('[xhs-search-page]', {
          keyword,
          page: pageNum,
          pageCount,
          batch: batch.length,
          added: collected.length - before,
          total: collected.length,
          hasMore: extractSyncResultPageMeta(payload).hasMore,
        })
      }
    }
  }

  return collected
}

/**
 * `/api/v1/sync/wxvideo/search-page` 共用拉取与翻页（视频号、公众号）。
 */

import { extractSyncResultItems, extractWxSearchPageMeta } from '@/lib/sync-api-common'
import type { SyncFetchContext } from '@/lib/sync-api-common'
import type { PlatformKey } from '@/components/PlatformIcon.vue'
import { expectedApiPageRows } from '@/lib/sync-platform-page-size'
import { mergeResultItems, postSyncSearchPage, readDataRange, readSearchKeywords } from '@/lib/sync-search-shared'

const WX_SEARCH_MAX_PAGES = 50

export type WxSearchPageTurn = {
  offset?: string
  cookiesBuffer?: string
}

export async function fetchWxSearchPageItems(input: {
  path: string
  platformLabel: string
  /** 用于读取该平台单次典型返回条数（视频号/公众号约 15） */
  platform: PlatformKey
  config: Record<string, unknown>
  ctx: SyncFetchContext
  buildBody: (
    config: Record<string, unknown>,
    keyword: string,
    page: number,
    pageTurn?: WxSearchPageTurn,
  ) => Record<string, unknown>
}): Promise<Record<string, unknown>[]> {
  const keywords = readSearchKeywords(input.config)
  const limit = readDataRange(input.config)
  const rowsPerPage = expectedApiPageRows(input.platform)
  const collected: Record<string, unknown>[] = []
  const seenIds = new Set<string>()

  for (const keyword of keywords) {
    let pageNum = 1
    let offset = ''
    let cookiesBuffer = ''

    while (collected.length < limit && pageNum <= WX_SEARCH_MAX_PAGES) {
      const pageForBody = offset || cookiesBuffer ? 1 : pageNum
      const payload = await postSyncSearchPage({
        path: input.path,
        platformLabel: input.platformLabel,
        ctx: input.ctx,
        body: input.buildBody(input.config, keyword, pageForBody, { offset, cookiesBuffer }),
      })
      const batch = extractSyncResultItems(payload)
      const before = collected.length
      if (
        mergeResultItems({
          batch,
          collected,
          seenIds,
          itemIdKeys: ['post_id', 'postId', 'feed_id', 'feedId', 'article_id', 'articleId', 'id'],
          limit,
          platformKey: input.platform,
        })
      ) {
        break
      }
      if (!batch.length) break
      if (collected.length === before) break

      const pageMeta = extractWxSearchPageMeta(payload)
      if (pageMeta.insufficientBalance) {
        throw new Error('账户积分不足，无法继续采集')
      }

      const remaining = limit - collected.length
      if (import.meta.env.DEV) {
        console.log('[wx-search-page]', {
          platform: input.platformLabel,
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
      if (remaining <= 0) break
      if (batch.length < rowsPerPage && !pageMeta.hasMore) break
      if (!pageMeta.hasMore) break

      const nextOffset = pageMeta.offset
      const nextCookies = pageMeta.cookies_buffer
      if (nextOffset || nextCookies) {
        /* 微信搜一搜翻页用 next_offset + cookies_buffer，page 保持 1，勿与 page++ 混用（易 400） */
        offset = nextOffset
        cookiesBuffer = nextCookies
      } else {
        pageNum += 1
      }
    }

    if (collected.length >= limit) break
  }

  return collected
}

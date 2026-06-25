/**
 * `/api/v1/sync/wxvideo/search-page` 与 `/api/v1/sync/mp/search-page` 共用拉取与翻页（视频号、公众号）。
 */

import { extractSyncResultItems, extractWxSearchPageMeta } from '@/lib/sync-api-common'
import type { SyncFetchContext } from '@/lib/sync-api-common'
import type { PlatformKey } from '@/components/PlatformIcon.vue'
import {
  mergeResultItems,
  postSyncSearchPage,
  readConfiguredSearchPageCount,
  readSearchKeywords,
} from '@/lib/sync-search-shared'

export type WxSearchPageTurn = {
  offset?: string
  cookiesBuffer?: string
}

export async function fetchWxSearchPageItems(input: {
  path: string
  platformLabel: string
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
  const pageCount = readConfiguredSearchPageCount(input.config)
  const collected: Record<string, unknown>[] = []
  const seenIds = new Set<string>()

  for (const keyword of keywords) {
    let pageNum = 1
    let offset = ''
    let cookiesBuffer = ''

    for (let apiCall = 1; apiCall <= pageCount; apiCall++) {
      const pageForBody = offset || cookiesBuffer ? 1 : pageNum
      const payload = await postSyncSearchPage({
        path: input.path,
        platformLabel: input.platformLabel,
        ctx: input.ctx,
        body: input.buildBody(input.config, keyword, pageForBody, { offset, cookiesBuffer }),
      })
      const batch = extractSyncResultItems(payload)
      const before = collected.length
      mergeResultItems({
        batch,
        collected,
        seenIds,
        itemIdKeys: ['post_id', 'postId', 'feed_id', 'feedId', 'article_id', 'articleId', 'id'],
        platformKey: input.platform,
      })

      const pageMeta = extractWxSearchPageMeta(payload)
      if (pageMeta.insufficientBalance) {
        throw new Error('账户积分不足，无法继续采集')
      }

      if (import.meta.env.DEV) {
        console.log('[wx-search-page]', {
          platform: input.platformLabel,
          apiCall,
          pageCount,
          batch: batch.length,
          added: collected.length - before,
          total: collected.length,
          hasMore: pageMeta.hasMore,
        })
      }

      const nextOffset = pageMeta.offset
      const nextCookies = pageMeta.cookies_buffer
      if (nextOffset || nextCookies) {
        offset = nextOffset
        cookiesBuffer = nextCookies
      } else {
        pageNum += 1
      }
    }
  }

  return collected
}

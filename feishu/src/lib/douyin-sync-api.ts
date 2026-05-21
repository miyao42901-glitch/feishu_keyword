/**
 * 抖音搜索同步：`POST /api/v1/sync/douyin/search-page`
 */

import type { SyncFetchContext } from '@/lib/sync-api-common'
import { postSyncSearchPage } from '@/lib/sync-search-shared'
import {
  buildDouyinSearchPageBody,
  fetchDouyinSearchItems,
  type DouyinSearchPageRequestBody,
} from '@/lib/sync-search-page'

const DOUYIN_SEARCH_PAGE_PATH = '/api/v1/sync/douyin/search-page'

export type { DouyinSearchPageRequestBody }
export { buildDouyinSearchPageBody, fetchDouyinSearchItems }

export async function postDouyinSearchPage(input: {
  body: DouyinSearchPageRequestBody
  ctx: SyncFetchContext
}): Promise<unknown> {
  return postSyncSearchPage({
    path: DOUYIN_SEARCH_PAGE_PATH,
    platformLabel: '抖音',
    body: input.body,
    ctx: input.ctx,
  })
}

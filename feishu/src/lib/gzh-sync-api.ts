/**
 * 公众号搜索同步：`POST /api/v1/sync/mp/search-page`
 * 请求体无 `note_time`；翻页用 `offset` / `cookies_buffer`。
 */

import type { SyncFetchContext } from '@/lib/sync-api-common'
import {
  assertKeywordLength,
  buildExcludeWords,
  mapSortType,
  type SyncSortType,
} from '@/lib/sync-search-shared'
import { fetchWxSearchPageItems } from '@/lib/wx-search-page-fetch'
import { postSyncSearchPage } from '@/lib/sync-search-shared'

const GZH_SEARCH_PAGE_PATH = '/api/v1/sync/mp/search-page'

export type GzhSearchPageRequestBody = {
  keyword: string
  exclude_words: string
  page: number
  sort_type: SyncSortType
  offset?: string
  cookies_buffer?: string
  [property: string]: unknown
}

export function buildGzhSearchPageBody(
  config: Record<string, unknown>,
  keyword: string,
  page: number,
  pageTurn?: { offset?: string; cookiesBuffer?: string },
): GzhSearchPageRequestBody {
  const body: GzhSearchPageRequestBody = {
    keyword: assertKeywordLength(keyword),
    exclude_words: buildExcludeWords(config),
    page: Math.max(1, Math.floor(page)),
    sort_type: mapSortType(String(config.sortOrder ?? config.sort_order ?? 'default')),
  }
  const offset = pageTurn?.offset != null ? String(pageTurn.offset).trim() : ''
  const cookies = pageTurn?.cookiesBuffer?.trim() ?? ''
  if (offset) body.offset = offset
  if (cookies) body.cookies_buffer = cookies
  return body
}

export async function postGzhSearchPage(input: {
  body: GzhSearchPageRequestBody
  ctx: SyncFetchContext
}): Promise<unknown> {
  return postSyncSearchPage({
    path: GZH_SEARCH_PAGE_PATH,
    platformLabel: '公众号',
    body: input.body,
    ctx: input.ctx,
  })
}

export async function fetchGzhSearchItems(
  config: Record<string, unknown>,
  ctx: SyncFetchContext,
): Promise<Record<string, unknown>[]> {
  return fetchWxSearchPageItems({
    path: GZH_SEARCH_PAGE_PATH,
    platformLabel: '公众号',
    platform: 'gzh',
    config,
    ctx,
    buildBody: (cfg, kw, page, turn) => buildGzhSearchPageBody(cfg, kw, page, turn),
  })
}

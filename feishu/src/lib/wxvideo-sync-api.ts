/**
 * 视频号搜索同步：`POST /api/v1/sync/wxvideo/search-page`
 */

import type { SyncFetchContext } from '@/lib/sync-api-common'
import {
  assertKeywordLength,
  buildExcludeWords,
  mapNoteTime,
  mapSortType,
  readSearchKeywords,
  type SyncSortType,
} from '@/lib/sync-search-shared'
import { fetchWxSearchPageItems } from '@/lib/wx-search-page-fetch'
import { postSyncSearchPage } from '@/lib/sync-search-shared'

const WXVIDEO_SEARCH_PAGE_PATH = '/api/v1/sync/wxvideo/search-page'

/** 视频号 search-page 请求体（Apifox） */
export type WxvideoSearchPageRequestBody = {
  keyword: string
  exclude_words: string
  page: number
  sort_type: SyncSortType
  note_time: string
  offset?: string
  cookies_buffer?: string
  [property: string]: unknown
}

export function buildWxvideoSearchPageBody(
  config: Record<string, unknown>,
  keyword: string,
  page: number,
  pageTurn?: { offset?: string; cookiesBuffer?: string },
): WxvideoSearchPageRequestBody {
  const body: WxvideoSearchPageRequestBody = {
    keyword: assertKeywordLength(keyword),
    exclude_words: buildExcludeWords(config),
    page: Math.max(1, Math.floor(page)),
    sort_type: mapSortType(String(config.sortOrder ?? config.sort_order ?? 'default')),
    note_time: mapNoteTime(String(config.publishTime ?? config.publish_time ?? 'unlimited')),
  }
  const offset = pageTurn?.offset != null ? String(pageTurn.offset).trim() : ''
  const cookies = pageTurn?.cookiesBuffer?.trim() ?? ''
  if (offset) body.offset = offset
  if (cookies) body.cookies_buffer = cookies
  return body
}

export async function postWxvideoSearchPage(input: {
  body: WxvideoSearchPageRequestBody
  ctx: SyncFetchContext
}): Promise<unknown> {
  return postSyncSearchPage({
    path: WXVIDEO_SEARCH_PAGE_PATH,
    platformLabel: '视频号',
    body: input.body,
    ctx: input.ctx,
  })
}

export async function fetchWxvideoSearchItems(
  config: Record<string, unknown>,
  ctx: SyncFetchContext,
): Promise<Record<string, unknown>[]> {
  return fetchWxSearchPageItems({
    path: WXVIDEO_SEARCH_PAGE_PATH,
    platformLabel: '视频号',
    platform: 'shipinhao',
    config,
    ctx,
    buildBody: (cfg, kw, page, turn) => buildWxvideoSearchPageBody(cfg, kw, page, turn),
  })
}

export { readSearchKeywords }

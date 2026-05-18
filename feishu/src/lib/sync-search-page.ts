/**
 * 抖音搜索同步：`POST /api/v1/sync/douyin/search-page`
 */

import type { SyncFetchContext } from '@/lib/sync-api-common'
import {
  assertKeywordLength,
  buildExcludeWords,
  mapNoteTime,
  mapSortType,
  mergeResultItems,
  postSyncSearchPage,
  readConfigArray,
  readDataRange,
  type SyncSortType,
} from '@/lib/sync-search-shared'
import { extractSyncResultItems, extractSyncResultPageMeta } from '@/lib/sync-api-common'

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
  page?: { cursor?: string; logId?: string },
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

  const cursor = page?.cursor?.trim()
  if (cursor) body.cursor = cursor

  const logId = page?.logId?.trim()
  if (logId) body.log_id = logId

  return body
}

/** @deprecated 使用 `buildDouyinSearchPageBody` */
export const buildSyncSearchPageBody = buildDouyinSearchPageBody

/** @deprecated 使用 `DouyinSearchPageRequestBody` */
export type SyncSearchPageRequestBody = DouyinSearchPageRequestBody

export async function fetchDouyinSearchItems(
  config: Record<string, unknown>,
  ctx: SyncFetchContext,
): Promise<Record<string, unknown>[]> {
  const keywords = readConfigArray(config, 'keywords')
  if (!keywords.length) {
    throw new Error('抖音采集需至少配置一个监控关键词')
  }

  const limit = readDataRange(config)
  const collected: Record<string, unknown>[] = []
  const seenIds = new Set<string>()
  const path = '/api/v1/sync/douyin/search-page'

  for (const keyword of keywords) {
    let cursor: string | undefined
    let logId: string | undefined

    while (collected.length < limit) {
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
      if (
        mergeResultItems({
          batch,
          collected,
          seenIds,
          itemIdKeys: ['aweme_id', 'awemeId'],
          limit,
        })
      ) {
        break
      }
      if (!batch.length) break

      const pageMeta = extractSyncResultPageMeta(payload)
      if (!pageMeta.hasMore) break
      const nextCursor =
        pageMeta.nextCursor != null && String(pageMeta.nextCursor).trim()
          ? String(pageMeta.nextCursor).trim()
          : undefined
      const nextLogId = pageMeta.nextLogid?.trim() || undefined
      if (!nextCursor && !nextLogId) break
      cursor = nextCursor
      logId = nextLogId
    }

    if (collected.length >= limit) break
  }

  return collected.slice(0, limit)
}

/** @deprecated 使用 `fetchDouyinSearchItems` */
export const fetchSyncSearchItems = fetchDouyinSearchItems

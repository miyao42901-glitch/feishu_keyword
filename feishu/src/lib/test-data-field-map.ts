/**
 * 将 test_data JSON 原始项按任务 `sourceFieldSelection` 映射为飞书列名 → 字符串值。
 */
import type { PlatformKey } from '@/components/PlatformIcon.vue'
import {
  sourceFieldFlatOptionsByPlatform,
  type SourceFieldFlatOption,
} from '@/views/TaskCreateForm/source-field-catalog'
import type { SourceFieldKey } from '@/views/TaskCreateForm/types'

function str(v: unknown): string {
  if (v == null) return ''
  if (typeof v === 'string') return v.trim()
  if (typeof v === 'number' && Number.isFinite(v)) return String(v)
  if (Array.isArray(v)) return v.map((x) => str(x)).filter(Boolean).join('\n')
  return ''
}

function joinUrlList(v: unknown, separator = '\n'): string {
  if (!Array.isArray(v)) return ''
  return v.map((x) => str(x)).filter(Boolean).join(separator)
}

function extractHashtagsFromText(text: string): string {
  if (!text) return ''
  const m = text.match(/#[^\s#]+/g)
  return m ? m.join(' ') : ''
}

function formatPublish(ms: number): string {
  if (!Number.isFinite(ms)) return ''
  const d = new Date(ms)
  return Number.isNaN(d.getTime()) ? '' : d.toLocaleString('zh-CN', { hour12: false })
}

/** 采集时间展示：本地时间 */
export function formatCollectedAt(ms: number): string {
  if (!Number.isFinite(ms)) return ''
  const d = new Date(ms)
  if (Number.isNaN(d.getTime())) return ''
  return d.toLocaleString('zh-CN', { hour12: false })
}

function readDouyinRaw(item: Record<string, unknown>, key: SourceFieldKey): string {
  const author =
    item.author && typeof item.author === 'object' && !Array.isArray(item.author)
      ? (item.author as Record<string, unknown>)
      : null

  switch (key) {
    case 'videoUniqueId':
      return str(item.aweme_id)
    case 'title':
      return str(item.title) || str(item.desc)
    case 'videoDescription':
      return str(item.desc)
    case 'playPageUrl':
      return str(item.url)
    case 'externalDownloadUrl': {
      const list = item.video_list
      if (Array.isArray(list) && list.length) return str(list[0])
      return ''
    }
    case 'coverUrl':
      return str(item.cover)
    case 'durationSeconds':
      return str(item.duration)
    case 'publishedAt': {
      const pt = item.publish_time
      const ms = typeof pt === 'number' ? pt : Number(pt)
      return formatPublish(ms)
    }
    case 'like':
      return str(item.like_count)
    case 'comment':
      return str(item.comment_count)
    case 'share':
      return str(item.share_count)
    case 'favorite':
      return str(item.collect_count)
    case 'authorNickname':
      return str(item.nickname)
    case 'authorId':
      return str(item.user_id)
    case 'authorAvatar':
      return str(item.avatar) || pickNestedStr(author ?? {}, 'avatar', 'avatar_url')
    case 'authorSignature':
      return (
        str(item.author_signature) ||
        str(item.authorSignature) ||
        pickNestedStr(author ?? {}, 'author_signature', 'signature')
      )
    case 'verifyName':
      return (
        str(item.verify_name) ||
        str(item.verifyName) ||
        pickNestedStr(author ?? {}, 'verify_name', 'verifyName')
      )
    case 'hashtagList':
      return extractHashtagsFromText(str(item.desc) || str(item.title))
    default:
      return ''
  }
}

function readShipinhaoRaw(item: Record<string, unknown>, key: SourceFieldKey): string {
  const author =
    item.author && typeof item.author === 'object' && !Array.isArray(item.author)
      ? (item.author as Record<string, unknown>)
      : null

  switch (key) {
    case 'wxvVideoUniqueId':
      return (
        str(item.post_id) ||
        str(item.postId) ||
        str(item.feed_id) ||
        str(item.feedId) ||
        str(item.object_id) ||
        str(item.objectId) ||
        str(item.video_id) ||
        str(item.videoId) ||
        str(item.id)
      )
    case 'wxvVideoUrl':
      return str(item.video_url) || str(item.videoUrl) || str(item.url) || str(item.link) || str(item.play_url)
    case 'wxvVideoTitle':
      return str(item.title) || str(item.desc)
    case 'wxvVideoDescription':
      return str(item.desc) || str(item.description) || str(item.video_desc)
    case 'wxvAuthorNickname':
      return (
        str(item.nickname) ||
        pickNestedStr(author ?? {}, 'nickname', 'name') ||
        str(item.author_name)
      )
    case 'wxvAuthorAvatar':
      return (
        str(item.avatar_url) ||
        str(item.avatarUrl) ||
        str(item.avatar) ||
        pickNestedStr(author ?? {}, 'avatar', 'head_img', 'headimgurl')
      )
    case 'wxvAuthorBio':
      return (
        str(item.signature) ||
        str(item.author_desc) ||
        str(item.intro) ||
        pickNestedStr(author ?? {}, 'signature', 'desc', 'intro')
      )
    case 'wxvAuthorId':
      return (
        str(item.user_id) ||
        str(item.userid) ||
        str(item.userId) ||
        str(item.finder_uin) ||
        pickNestedStr(author ?? {}, 'id', 'user_id', 'uin')
      )
    case 'publishedAt': {
      const pt = item.publish_time ?? item.create_time
      const ms = typeof pt === 'number' ? pt : Number(pt)
      return formatPublish(ms)
    }
    case 'wxvLikeCount':
      return str(item.like_count) || str(item.liked_num)
    case 'wxvCommentCount':
      return str(item.comment_count) || str(item.comment_num)
    case 'wxvRepostCount':
      return str(item.share_count) || str(item.forward_count) || str(item.repost_count)
    case 'wxvHeartCount':
      return (
        str(item.thumb_count) ||
        str(item.thumbCount) ||
        str(item.heart_count) ||
        str(item.fav_count) ||
        str(item.favorite_count) ||
        str(item.collect_count) ||
        str(item.like_num)
      )
    case 'wxvCoverUrl':
      return str(item.cover_url) || str(item.coverUrl) || str(item.cover) || str(item.thumb_url) || str(item.thumbUrl)
    case 'wxvDuration':
      return str(item.duration) || str(item.video_duration)
    /* 兼容旧配置字段 key */
    case 'videoUniqueId':
      return readShipinhaoRaw(item, 'wxvVideoUniqueId')
    case 'playPageUrl':
      return readShipinhaoRaw(item, 'wxvVideoUrl')
    case 'title':
      return readShipinhaoRaw(item, 'wxvVideoTitle')
    case 'videoDescription':
      return readShipinhaoRaw(item, 'wxvVideoDescription')
    case 'coverUrl':
      return readShipinhaoRaw(item, 'wxvCoverUrl')
    case 'durationSeconds':
      return readShipinhaoRaw(item, 'wxvDuration')
    case 'like':
      return readShipinhaoRaw(item, 'wxvLikeCount')
    case 'comment':
      return readShipinhaoRaw(item, 'wxvCommentCount')
    case 'share':
      return readShipinhaoRaw(item, 'wxvRepostCount')
    case 'favorite':
      return readShipinhaoRaw(item, 'wxvHeartCount')
    case 'authorNickname':
      return readShipinhaoRaw(item, 'wxvAuthorNickname')
    case 'authorId':
      return readShipinhaoRaw(item, 'wxvAuthorId')
    case 'authorAvatar':
      return readShipinhaoRaw(item, 'wxvAuthorAvatar')
    default:
      return ''
  }
}

function pickNestedStr(item: Record<string, unknown>, ...paths: string[]): string {
  for (const path of paths) {
    const parts = path.split('.')
    let cur: unknown = item
    for (const p of parts) {
      if (!cur || typeof cur !== 'object') {
        cur = undefined
        break
      }
      cur = (cur as Record<string, unknown>)[p]
    }
    const s = str(cur)
    if (s) return s
  }
  return ''
}

function readGzhRaw(item: Record<string, unknown>, key: SourceFieldKey): string {
  const account =
    item.account && typeof item.account === 'object' && !Array.isArray(item.account)
      ? (item.account as Record<string, unknown>)
      : item.mp && typeof item.mp === 'object' && !Array.isArray(item.mp)
        ? (item.mp as Record<string, unknown>)
        : item.biz && typeof item.biz === 'object' && !Array.isArray(item.biz)
          ? (item.biz as Record<string, unknown>)
          : null

  switch (key) {
    case 'gzhArticleId':
      return (
        str(item.post_id) ||
        str(item.postId) ||
        str(item.article_id) ||
        str(item.articleId) ||
        str(item.msg_id) ||
        str(item.msgId) ||
        str(item.appmsgid) ||
        str(item.id)
      )
    case 'gzhArticleTitle':
      return str(item.title) || pickNestedStr(item, 'article.title')
    case 'gzhArticleBody':
      return (
        str(item.content) ||
        str(item.article_content) ||
        str(item.desc) ||
        pickNestedStr(item, 'article.content')
      )
    case 'gzhArticleSummary':
      return str(item.digest) || str(item.summary) || str(item.abstract) || str(item.desc_summary)
    case 'gzhArticleUrl':
      return (
        str(item.url) ||
        str(item.link) ||
        str(item.video_url) ||
        str(item.videoUrl) ||
        str(item.source_url) ||
        str(item.content_url)
      )
    case 'gzhArticleType':
      return str(item.article_type) || str(item.type) || str(item.content_type)
    case 'publishedAt': {
      const pt = item.publish_time ?? item.create_time ?? item.send_time
      const ms = typeof pt === 'number' ? pt : Number(pt)
      return formatPublish(ms)
    }
    case 'gzhAccountId':
      return (
        str(item.bizuin) ||
        str(item.gh_id) ||
        str(item.wechat_id) ||
        str(item.account_id) ||
        pickNestedStr(account ?? {}, 'bizuin', 'gh_id', 'wechat_id', 'id')
      )
    case 'gzhAccountNickname':
      return (
        str(item.nickname) ||
        str(item.biz_name) ||
        str(item.account_name) ||
        str(item.author) ||
        pickNestedStr(account ?? {}, 'nickname', 'name', 'biz_name')
      )
    case 'gzhAccountAvatar':
      return (
        str(item.avatar_url) ||
        str(item.avatarUrl) ||
        str(item.avatar) ||
        str(item.head_img) ||
        str(item.headimgurl) ||
        pickNestedStr(account ?? {}, 'avatar', 'head_img', 'headimgurl')
      )
    case 'gzhAccountBio':
      return (
        str(item.signature) ||
        str(item.account_intro) ||
        str(item.description) ||
        pickNestedStr(account ?? {}, 'signature', 'intro', 'description')
      )
    case 'gzhReadCount':
      return str(item.read_count) || str(item.read_num) || str(item.view_count) || str(item.read_num_new)
    case 'gzhLikeCount':
      return str(item.like_count) || str(item.liked_num) || str(item.praise_num)
    case 'gzhRepostCount':
      return str(item.share_count) || str(item.repost_count) || str(item.forward_count)
    case 'gzhCollectCount':
      return str(item.collect_count) || str(item.favorite_count) || str(item.collect_num)
    case 'gzhWowCount':
      return str(item.wow_count) || str(item.show_count) || str(item.like_num) || str(item.view_like_count)
    case 'gzhFeaturedCommentCount':
      return (
        str(item.comment_count) ||
        str(item.commentCount) ||
        str(item.featured_comment_count) ||
        str(item.star_comment_count) ||
        str(item.selected_comment_count)
      )
    /* 兼容旧配置字段 key */
    case 'noteId':
      return readGzhRaw(item, 'gzhArticleId')
    case 'title':
      return readGzhRaw(item, 'gzhArticleTitle')
    case 'noteBody':
      return readGzhRaw(item, 'gzhArticleBody')
    case 'playPageUrl':
      return readGzhRaw(item, 'gzhArticleUrl')
    case 'like':
      return readGzhRaw(item, 'gzhLikeCount')
    case 'share':
      return readGzhRaw(item, 'gzhRepostCount')
    case 'favorite':
      return readGzhRaw(item, 'gzhCollectCount')
    case 'authorNickname':
      return readGzhRaw(item, 'gzhAccountNickname')
    case 'authorId':
      return readGzhRaw(item, 'gzhAccountId')
    case 'authorAvatar':
      return readGzhRaw(item, 'gzhAccountAvatar')
    default:
      return ''
  }
}

/** YDDM `GET .../results` 小红书条目（`post_id` / `page_url` / `publish_time_ms` 等） */
export function readXhsPublishTimeMs(item: Record<string, unknown>): number {
  for (const key of ['publish_time_ms', 'publish_time', 'publishTimeMs', 'publishTime', 'create_time']) {
    const v = item[key]
    const n = typeof v === 'number' ? v : Number(v)
    if (Number.isFinite(n) && n > 0) return n
  }
  return 0
}

function readXhsNoteBody(item: Record<string, unknown>): string {
  return str(item.desc) || str(item.summary) || str(item.note_body) || str(item.noteBody)
}

function readXhsPageUrl(item: Record<string, unknown>): string {
  return str(item.url) || str(item.page_url) || str(item.pageUrl)
}

function readXhsRaw(item: Record<string, unknown>, key: SourceFieldKey): string {
  switch (key) {
    case 'noteId':
      return str(item.post_id ?? item.postId ?? item.note_id ?? item.noteId)
    case 'title':
      return str(item.title) || readXhsNoteBody(item)
    case 'noteBody':
      return readXhsNoteBody(item)
    case 'playPageUrl':
      return readXhsPageUrl(item)
    case 'topicTags':
      return extractHashtagsFromText(readXhsNoteBody(item) || str(item.title))
    case 'noteImages': {
      const list = item.images_list
      if (Array.isArray(list) && list.length) return joinUrlList(list)
      return str(item.primary_image_url) || str(item.cover_url) || str(item.coverUrl)
    }
    case 'videoMedia': {
      const parts: string[] = []
      const videoUrl =
        joinUrlList(item.video_list, ' | ') ||
        str(item.primary_video_url) ||
        str(item.primaryVideoUrl)
      if (videoUrl) parts.push(videoUrl)
      const dur = item.duration_seconds ?? item.duration
      if (dur != null && String(dur).trim() !== '' && String(dur) !== '0') {
        parts.push(`${str(dur)}秒`)
      }
      if (!parts.length) {
        const cover =
          str(item.primary_image_url) ||
          str(item.cover_url) ||
          joinUrlList(item.images_list, ' | ')
        if (cover) parts.push(cover)
      }
      return parts.join(' | ')
    }
    case 'publishedAt':
      return formatPublish(readXhsPublishTimeMs(item))
    case 'like':
      return str(item.like_count)
    case 'comment':
      return str(item.comment_count)
    case 'share':
      return str(item.share_count)
    case 'favorite':
      return str(item.collect_count)
    case 'authorNickname':
      return str(item.nickname)
    case 'authorId':
      return str(item.sec_uid ?? item.userid ?? item.user_id ?? item.userId)
    case 'authorAvatar':
      return str(item.avatar_url) || str(item.avatarUrl) || str(item.avatar)
    case 'noteType': {
      const ct = str(item.content_type).toLowerCase()
      if (ct === 'video') return '视频'
      if (ct === 'normal') return '图文'
      return ct
    }
    default:
      return ''
  }
}

function readSelectedSourceFields(config: Record<string, unknown>, platform: PlatformKey): SourceFieldKey[] {
  const raw = config.sourceFieldSelection ?? config.source_field_selection
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return []
  const plat = (raw as Record<string, unknown>)[platform]
  if (!Array.isArray(plat)) return []
  const opts = sourceFieldFlatOptionsByPlatform[platform] ?? []
  const allowed = new Set(opts.map((o) => o.value))
  return plat.filter((x): x is SourceFieldKey => typeof x === 'string' && allowed.has(x as SourceFieldKey))
}

/** 按任务勾选字段生成「列名 → 单元格文本」 */
export function mapItemToColumnValues(
  item: Record<string, unknown>,
  platform: PlatformKey,
  config: Record<string, unknown>,
  options?: { collectedAtMs?: number },
): Record<string, string> {
  const keys = readSelectedSourceFields(config, platform)
  const opts = sourceFieldFlatOptionsByPlatform[platform] ?? []
  const optByKey = new Map<SourceFieldKey, SourceFieldFlatOption>(opts.map((o) => [o.value, o]))
  const out: Record<string, string> = {}
  for (const key of keys) {
    const opt = optByKey.get(key)
    if (!opt) continue
    if (key === 'collectedAt') {
      const ms = options?.collectedAtMs ?? Date.now()
      out[opt.label] = formatCollectedAt(ms)
      continue
    }
    const raw =
      platform === 'douyin'
        ? readDouyinRaw(item, key)
        : platform === 'xiaohongshu'
          ? readXhsRaw(item, key)
          : platform === 'shipinhao'
            ? readShipinhaoRaw(item, key)
            : platform === 'gzh'
              ? readGzhRaw(item, key)
              : ''
    out[opt.label] = raw
  }
  return out
}

/** 按表单扁平列表顺序返回已勾选字段的列名（用于建表列顺序与主字段） */
export function getOrderedColumnLabelsForPlatform(
  config: Record<string, unknown>,
  platform: PlatformKey,
): string[] {
  const keys = readSelectedSourceFields(config, platform)
  const opts = sourceFieldFlatOptionsByPlatform[platform] ?? []
  const labels: string[] = []
  for (const opt of opts) {
    if (keys.includes(opt.value)) labels.push(opt.label)
  }
  return labels
}

/** 主字段（带锁列）取该平台勾选字段中的第一项 */
export function getPrimaryColumnLabelForPlatform(
  config: Record<string, unknown>,
  platform: PlatformKey,
): string {
  return getOrderedColumnLabelsForPlatform(config, platform)[0] ?? ''
}


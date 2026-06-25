/**
 * 信源采集字段：扁平列表（无分类表头），与 `config_json.sourceFieldSelection` 对齐。
 */
import type { PlatformKey } from '@/components/PlatformIcon.vue'
import { isSyncCollectionPlatform } from '@/lib/sync-collection-platforms'
import type { SourceFieldKey, TaskCreateFormModel } from '@/views/TaskCreateForm/types'

export type SourceFieldFlatOption = {
  value: SourceFieldKey
  label: string
  /** 必选：始终勾选且不可取消 */
  required?: boolean
}

/** 抖音：下拉多选扁平项（顺序即展示顺序） */
export const douyinFlatSourceFields: SourceFieldFlatOption[] = [
  { value: 'videoUniqueId', label: '视频唯一ID', required: true },
  { value: 'title', label: '标题' },
  { value: 'videoDescription', label: '视频描述' },
  { value: 'playPageUrl', label: '视频播放页链接' },
  { value: 'externalDownloadUrl', label: '外链视频下载链接' },
  { value: 'coverUrl', label: '封面图链接' },
  { value: 'durationSeconds', label: '视频时长（秒）' },
  { value: 'publishedAt', label: '发布时间' },
  { value: 'like', label: '点赞数' },
  { value: 'comment', label: '评论数' },
  { value: 'share', label: '分享数' },
  { value: 'favorite', label: '收藏数' },
  { value: 'authorNickname', label: '作者昵称' },
  { value: 'authorId', label: '作者唯一ID' },
  { value: 'authorFollowers', label: '粉丝数' },
  { value: 'authorAvatar', label: '头像链接' },
  { value: 'authorSignature', label: '个人简介' },
  { value: 'verifyName', label: '星标认证' },
  { value: 'hashtagList', label: '话题标签' },
  { value: 'collectedAt', label: '采集时间' },
]

/** 小红书：下拉多选扁平项 */
export const xiaohongshuFlatSourceFields: SourceFieldFlatOption[] = [
  { value: 'noteId', label: '笔记ID', required: true },
  { value: 'title', label: '笔记标题' },
  { value: 'noteBody', label: '笔记正文内容' },
  { value: 'topicTags', label: '话题标签' },
  { value: 'publishedAt', label: '发布时间' },
  { value: 'noteImages', label: '图片URL数组' },
  { value: 'videoMedia', label: '视频多媒体（链接/封面/类型/时长）' },
  { value: 'like', label: '点赞数' },
  { value: 'comment', label: '评论数' },
  { value: 'favorite', label: '收藏数' },
  { value: 'authorId', label: '作者用户ID' },
  { value: 'authorNickname', label: '用户昵称' },
  { value: 'authorAvatar', label: '头像链接' },
  { value: 'noteType', label: '笔记类型（图文/视频）' },
  { value: 'collectedAt', label: '采集时间' },
]

/** 视频号：列名与飞书表头一致 */
export const shipinhaoFlatSourceFields: SourceFieldFlatOption[] = [
  { value: 'wxvVideoUniqueId', label: '视频唯一ID', required: true },
  { value: 'wxvVideoUrl', label: '视频链接' },
  { value: 'wxvVideoTitle', label: '视频标题' },
  { value: 'wxvAuthorNickname', label: '作者昵称' },
  { value: 'wxvAuthorAvatar', label: '作者头像' },
  { value: 'publishedAt', label: '发布时间' },
  { value: 'wxvLikeCount', label: '点赞数' },
  { value: 'wxvCommentCount', label: '评论数' },
  { value: 'wxvRepostCount', label: '转发数' },
  { value: 'wxvHeartCount', label: '小心心数' },
  { value: 'wxvCoverUrl', label: '封面图' },
  { value: 'wxvDuration', label: '视频时长' },
  { value: 'collectedAt', label: '采集时间' },
]

/** 旧版视频号字段 value → 新 value */
const shipinhaoLegacyFieldMap: Partial<Record<SourceFieldKey, SourceFieldKey>> = {
  videoUniqueId: 'wxvVideoUniqueId',
  playPageUrl: 'wxvVideoUrl',
  title: 'wxvVideoTitle',
  videoDescription: 'wxvVideoDescription',
  authorNickname: 'wxvAuthorNickname',
  authorAvatar: 'wxvAuthorAvatar',
  authorId: 'wxvAuthorId',
  like: 'wxvLikeCount',
  comment: 'wxvCommentCount',
  share: 'wxvRepostCount',
  favorite: 'wxvHeartCount',
  coverUrl: 'wxvCoverUrl',
  durationSeconds: 'wxvDuration',
}

/** 公众号：图文文章字段（列名与飞书表头一致） */
export const gzhFlatSourceFields: SourceFieldFlatOption[] = [
  { value: 'gzhArticleId', label: '文章ID', required: true },
  { value: 'gzhArticleTitle', label: '文章标题' },
  { value: 'gzhArticleUrl', label: '文章原始URL' },
  { value: 'publishedAt', label: '发布时间' },
  { value: 'gzhAccountNickname', label: '公众号昵称' },
  { value: 'gzhAccountAvatar', label: '公众号头像链接' },
  { value: 'gzhLikeCount', label: '点赞数' },
  { value: 'gzhRepostCount', label: '转发数' },
  { value: 'gzhFeaturedCommentCount', label: '精选留言数' },
  { value: 'collectedAt', label: '采集时间' },
]

/** 旧版公众号字段 value → 新 value（加载历史任务配置时迁移） */
const gzhLegacyFieldMap: Partial<Record<SourceFieldKey, SourceFieldKey>> = {
  noteId: 'gzhArticleId',
  title: 'gzhArticleTitle',
  noteBody: 'gzhArticleBody',
  playPageUrl: 'gzhArticleUrl',
  coverUrl: 'gzhAccountAvatar',
  like: 'gzhLikeCount',
  comment: 'gzhFeaturedCommentCount',
  share: 'gzhRepostCount',
  favorite: 'gzhCollectCount',
  authorNickname: 'gzhAccountNickname',
  authorId: 'gzhAccountId',
  authorAvatar: 'gzhAccountAvatar',
}

export const sourceFieldFlatOptionsByPlatform: Partial<Record<PlatformKey, SourceFieldFlatOption[]>> = {
  douyin: douyinFlatSourceFields,
  xiaohongshu: xiaohongshuFlatSourceFields,
  shipinhao: shipinhaoFlatSourceFields,
  gzh: gzhFlatSourceFields,
}

/** 当前信源仅开放的平台（与 `sourcePlatforms` 一致） */
export const supportedSourcePlatformIds = [
  'douyin',
  'xiaohongshu',
  'shipinhao',
  'gzh',
] as const satisfies readonly PlatformKey[]

export function isSupportedSourcePlatform(id: PlatformKey): boolean {
  return (supportedSourcePlatformIds as readonly string[]).includes(id)
}

/** 合并旧配置、保存时允许的采集字段 value */
export const allSourceFieldKeys: readonly SourceFieldKey[] = [
  'videoUniqueId',
  'title',
  'videoDescription',
  'playPageUrl',
  'externalDownloadUrl',
  'coverUrl',
  'videoTypeTag',
  'durationSeconds',
  'publishedAt',
  'collectedAt',
  'like',
  'comment',
  'share',
  'favorite',
  'authorNickname',
  'authorId',
  'authorFollowers',
  'authorAvatar',
  'authorSignature',
  'verifyName',
  'hashtagList',
  'city',
  'ipLocation',
  'noteId',
  'noteBody',
  'topicTags',
  'noteImages',
  'videoMedia',
  'location',
  'noteType',
  'mentionedUsers',
  'gzhArticleId',
  'gzhArticleTitle',
  'gzhArticleBody',
  'gzhArticleSummary',
  'gzhArticleUrl',
  'gzhArticleType',
  'gzhAccountId',
  'gzhAccountNickname',
  'gzhAccountAvatar',
  'gzhAccountBio',
  'gzhReadCount',
  'gzhLikeCount',
  'gzhRepostCount',
  'gzhCollectCount',
  'gzhWowCount',
  'gzhFeaturedCommentCount',
  'wxvVideoUniqueId',
  'wxvVideoUrl',
  'wxvVideoTitle',
  'wxvVideoDescription',
  'wxvAuthorNickname',
  'wxvAuthorAvatar',
  'wxvAuthorBio',
  'wxvAuthorId',
  'wxvLikeCount',
  'wxvCommentCount',
  'wxvRepostCount',
  'wxvHeartCount',
  'wxvCoverUrl',
  'wxvDuration',
] as const

export function isSourceFieldKey(x: unknown): x is SourceFieldKey {
  return typeof x === 'string' && (allSourceFieldKeys as readonly string[]).includes(x)
}

export function getRequiredFieldKeys(platform: PlatformKey): SourceFieldKey[] {
  const opts = sourceFieldFlatOptionsByPlatform[platform]
  if (!opts?.length) return []
  return opts.filter((o) => o.required).map((o) => o.value)
}

/** 每个已选信源：合并必选 + 合法旧勾选，顺序与扁平表一致 */
export function ensureSourceFieldSelectionForPlatform(form: TaskCreateFormModel, platform: PlatformKey) {
  const opts = sourceFieldFlatOptionsByPlatform[platform]
  if (!opts?.length) return
  const allowed = new Set(opts.map((o) => o.value))
  const required = opts.filter((o) => o.required).map((o) => o.value)
  let prev = form.sourceFieldSelection[platform] ?? []
  if (platform === 'gzh') {
    prev = prev.map((k) => (isSourceFieldKey(k) ? (gzhLegacyFieldMap[k] ?? k) : k))
  }
  if (platform === 'shipinhao') {
    prev = prev.map((k) => (isSourceFieldKey(k) ? (shipinhaoLegacyFieldMap[k] ?? k) : k))
  }
  const kept = prev.filter((k): k is SourceFieldKey => isSourceFieldKey(k) && allowed.has(k))
  if (!kept.length) {
    form.sourceFieldSelection[platform] = opts.map((o) => o.value)
    return
  }
  const merged = new Set<SourceFieldKey>([...required, ...kept])
  if (allowed.has('collectedAt')) merged.add('collectedAt')
  form.sourceFieldSelection[platform] = opts.map((o) => o.value).filter((v) => merged.has(v))
}

export function ensureSourceFieldSelectionForAllSelected(form: TaskCreateFormModel) {
  for (const p of form.selectedSources) {
    if (isSupportedSourcePlatform(p)) ensureSourceFieldSelectionForPlatform(form, p)
  }
}

function mergePlatformFieldSelection(
  platform: PlatformKey,
  prev: SourceFieldKey[],
): SourceFieldKey[] {
  const opts = sourceFieldFlatOptionsByPlatform[platform]
  if (!opts?.length) return []
  const allowed = new Set(opts.map((o) => o.value))
  const required = opts.filter((o) => o.required).map((o) => o.value)
  let kept = [...prev]
  if (platform === 'gzh') {
    kept = kept.map((k) => (isSourceFieldKey(k) ? (gzhLegacyFieldMap[k] ?? k) : k))
  }
  if (platform === 'shipinhao') {
    kept = kept.map((k) => (isSourceFieldKey(k) ? (shipinhaoLegacyFieldMap[k] ?? k) : k))
  }
  const filtered = kept.filter((k): k is SourceFieldKey => isSourceFieldKey(k) && allowed.has(k))
  // 列表执行 / 未保存过采集字段时 prev 为空：默认勾选该平台全部字段，避免只写入「标题」等少量列
  if (!filtered.length) {
    return opts.map((o) => o.value)
  }
  const merged = new Set<SourceFieldKey>([...required, ...filtered])
  if (allowed.has('collectedAt')) merged.add('collectedAt')
  return opts.map((o) => o.value).filter((v) => merged.has(v))
}

/** 写入多维表格时实际使用的采集字段（空配置 → 全量字段） */
export function getEffectiveSourceFieldKeysForPlatform(
  config: Record<string, unknown>,
  platform: PlatformKey,
): SourceFieldKey[] {
  const raw = config.sourceFieldSelection ?? config.source_field_selection
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) {
    const opts = sourceFieldFlatOptionsByPlatform[platform]
    return opts?.map((o) => o.value) ?? []
  }
  const plat = (raw as Record<string, unknown>)[platform]
  const prev = Array.isArray(plat) ? (plat as SourceFieldKey[]) : []
  return mergePlatformFieldSelection(platform, prev)
}

/**
 * 写入飞书表前补齐 `sourceFieldSelection`（列表执行时 config 可能未带表单里的采集字段）。
 */
export function ensureSourceFieldSelectionInConfig(config: Record<string, unknown>): void {
  const rawSources = config.selectedSources ?? config.selected_sources
  const platforms: PlatformKey[] = Array.isArray(rawSources)
    ? rawSources.filter((x): x is PlatformKey => typeof x === 'string' && isSyncCollectionPlatform(x))
    : []

  const rawSel = config.sourceFieldSelection ?? config.source_field_selection
  const sel: Partial<Record<PlatformKey, SourceFieldKey[]>> =
    rawSel && typeof rawSel === 'object' && !Array.isArray(rawSel)
      ? { ...(rawSel as Partial<Record<PlatformKey, SourceFieldKey[]>>) }
      : {}

  for (const platform of platforms) {
    const opts = sourceFieldFlatOptionsByPlatform[platform]
    if (!opts?.length) continue
    const prev = Array.isArray(sel[platform]) ? sel[platform]! : []
    sel[platform] = mergePlatformFieldSelection(platform, prev)
  }

  config.sourceFieldSelection = sel
}

/**
 * 写入多维表格时使用该平台全部采集字段（search-page 已返回完整条目，应写满各列）。
 */
export function applyFullSourceFieldSelectionForBitableWrite(config: Record<string, unknown>): void {
  const rawSources = config.selectedSources ?? config.selected_sources
  const platforms: PlatformKey[] = Array.isArray(rawSources)
    ? rawSources.filter((x): x is PlatformKey => typeof x === 'string' && isSyncCollectionPlatform(x))
    : []

  const rawSel = config.sourceFieldSelection ?? config.source_field_selection
  const sel: Partial<Record<PlatformKey, SourceFieldKey[]>> =
    rawSel && typeof rawSel === 'object' && !Array.isArray(rawSel)
      ? { ...(rawSel as Partial<Record<PlatformKey, SourceFieldKey[]>>) }
      : {}

  for (const platform of platforms) {
    const opts = sourceFieldFlatOptionsByPlatform[platform]
    if (opts?.length) sel[platform] = opts.map((o) => o.value)
  }

  config.sourceFieldSelection = sel
}

/** 必选字段不计入「额外接口」估算 */
export function countOptionalSelectedSourceFields(form: TaskCreateFormModel, platform: PlatformKey): number {
  const opts = sourceFieldFlatOptionsByPlatform[platform]
  if (!opts?.length) return 0
  const required = new Set(opts.filter((o) => o.required).map((o) => o.value))
  const sel = form.sourceFieldSelection[platform] ?? []
  return sel.filter((k) => !required.has(k)).length
}

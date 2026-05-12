/**
 * 信源采集字段：扁平列表（无分类表头），与 `config_json.sourceFieldSelection` 对齐。
 */
import type { PlatformKey } from '@/components/PlatformIcon.vue'
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
  { value: 'videoTypeTag', label: '视频类型标签' },
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
  { value: 'hashtagList', label: '话题标签' },
  { value: 'city', label: '城市' },
  { value: 'ipLocation', label: 'IP 属地' },
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
  { value: 'share', label: '分享数' },
  { value: 'authorId', label: '作者用户ID' },
  { value: 'authorNickname', label: '用户昵称' },
  { value: 'authorAvatar', label: '头像链接' },
  { value: 'authorFollowers', label: '粉丝数' },
  { value: 'location', label: '地点名称' },
  { value: 'city', label: '城市' },
  { value: 'noteType', label: '笔记类型（图文/视频）' },
  { value: 'ipLocation', label: 'IP 属地' },
  { value: 'mentionedUsers', label: '@用户列表' },
]

export const sourceFieldFlatOptionsByPlatform: Partial<Record<PlatformKey, SourceFieldFlatOption[]>> = {
  douyin: douyinFlatSourceFields,
  xiaohongshu: xiaohongshuFlatSourceFields,
}

/** 当前信源仅开放的平台（与 `sourcePlatforms` 一致） */
export const supportedSourcePlatformIds = ['douyin', 'xiaohongshu'] as const satisfies readonly PlatformKey[]

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
  'like',
  'comment',
  'share',
  'favorite',
  'authorNickname',
  'authorId',
  'authorFollowers',
  'authorAvatar',
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
  const prev = form.sourceFieldSelection[platform] ?? []
  const kept = prev.filter((k): k is SourceFieldKey => isSourceFieldKey(k) && allowed.has(k))
  const merged = new Set<SourceFieldKey>([...required, ...kept])
  form.sourceFieldSelection[platform] = opts.map((o) => o.value).filter((v) => merged.has(v))
}

export function ensureSourceFieldSelectionForAllSelected(form: TaskCreateFormModel) {
  for (const p of form.selectedSources) {
    if (isSupportedSourcePlatform(p)) ensureSourceFieldSelectionForPlatform(form, p)
  }
}

/** 必选字段不计入「额外接口」估算 */
export function countOptionalSelectedSourceFields(form: TaskCreateFormModel, platform: PlatformKey): number {
  const opts = sourceFieldFlatOptionsByPlatform[platform]
  if (!opts?.length) return 0
  const required = new Set(opts.filter((o) => o.required).map((o) => o.value))
  const sel = form.sourceFieldSelection[platform] ?? []
  return sel.filter((k) => !required.has(k)).length
}

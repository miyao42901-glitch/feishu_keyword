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

function formatPublish(ms: number): string {
  if (!Number.isFinite(ms)) return ''
  const d = new Date(ms)
  return Number.isNaN(d.getTime()) ? '' : d.toLocaleString('zh-CN', { hour12: false })
}

function readDouyinRaw(item: Record<string, unknown>, key: SourceFieldKey): string {
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
      return str(item.avatar)
    default:
      return ''
  }
}

function readXhsRaw(item: Record<string, unknown>, key: SourceFieldKey): string {
  switch (key) {
    case 'noteId':
      return str(item.note_id ?? item.id)
    case 'title':
      return str(item.title) || str(item.desc)
    case 'noteBody':
      return str(item.desc)
    case 'playPageUrl':
      return str(item.url)
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
      return str(item.avatar)
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
): Record<string, string> {
  const keys = readSelectedSourceFields(config, platform)
  const opts = sourceFieldFlatOptionsByPlatform[platform] ?? []
  const optByKey = new Map<SourceFieldKey, SourceFieldFlatOption>(opts.map((o) => [o.value, o]))
  const out: Record<string, string> = {}
  for (const key of keys) {
    const opt = optByKey.get(key)
    if (!opt) continue
    const raw =
      platform === 'douyin' ? readDouyinRaw(item, key) : platform === 'xiaohongshu' ? readXhsRaw(item, key) : ''
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


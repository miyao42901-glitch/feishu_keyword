/**
 * 将保存后的 `config_json` 快照转为预览表格行（不含敏感字段原文）。
 */
import type { PlatformKey } from '@/components/PlatformIcon.vue'
import {
  frequencyOptions,
  platformDisplayNames,
  publishTimeOptions,
  sortOrderOptions,
  videoDurationOptions,
} from '@/views/TaskCreateForm/constants'

function optLabel<T extends { label: string; value: string }>(
  options: readonly T[],
  value: unknown,
): string {
  const v = typeof value === 'string' ? value : String(value ?? '')
  const hit = options.find((o) => o.value === v)
  if (hit) return hit.label
  return v.trim() || '—'
}

function joinArr(v: unknown): string {
  if (!Array.isArray(v)) return '—'
  const parts = v
    .filter((x): x is string => typeof x === 'string')
    .map((s) => s.trim())
    .filter((s) => s.length > 0)
  return parts.length ? parts.join('、') : '—'
}

export function buildTaskConfigPreviewRows(cfg: Record<string, unknown>): { label: string; value: string }[] {
  const rows: { label: string; value: string }[] = []
  const planName = typeof cfg.planName === 'string' ? cfg.planName.trim() : ''
  rows.push({ label: '方案名称', value: planName || '—' })

  const taskType = cfg.taskType === 'realtime' ? '实时任务' : '定时任务'
  rows.push({ label: '任务类型', value: taskType })

  if (cfg.taskType !== 'realtime') {
    rows.push({
      label: '采集频率',
      value: optLabel(frequencyOptions, cfg.crawlFrequency),
    })
    const eff = typeof cfg.effectiveAt === 'string' ? cfg.effectiveAt.trim() : ''
    const exp = typeof cfg.expireAt === 'string' ? cfg.expireAt.trim() : ''
    rows.push({ label: '生效时间', value: eff || '—' })
    rows.push({ label: '过期时间', value: exp || '—' })
  }

  rows.push({ label: '监控关键词', value: joinArr(cfg.keywords) })
  rows.push({ label: '排除词', value: joinArr(cfg.excludeKeywords) })
  rows.push({
    label: '互动阈值（赞/评/藏/转）',
    value: `${cfg.heatLikeMin ?? 0} / ${cfg.heatCommentMin ?? 0} / ${cfg.heatFavoriteMin ?? 0} / ${cfg.heatShareMin ?? 0}`,
  })
  rows.push({ label: '排序方式', value: optLabel(sortOrderOptions, cfg.sortOrder) })
  rows.push({ label: '发布时间', value: optLabel(publishTimeOptions, cfg.publishTime) })
  rows.push({ label: '视频时长', value: optLabel(videoDurationOptions, cfg.videoDuration) })
  rows.push({
    label: '单次拉取条数',
    value: typeof cfg.dataRange === 'number' ? String(cfg.dataRange) : '—',
  })

  const src = cfg.selectedSources
  if (Array.isArray(src) && src.length) {
    const labels = src
      .filter((x): x is PlatformKey => typeof x === 'string' && x in platformDisplayNames)
      .map((k) => platformDisplayNames[k])
    rows.push({ label: '信源', value: labels.join('、') })
  } else {
    rows.push({ label: '信源', value: '—' })
  }

  const tm = cfg.tableMode === 'new' ? '新建多维表' : '关联已有表'
  rows.push({ label: '数据沉淀', value: tm })
  const tid = typeof cfg.existingTableId === 'string' ? cfg.existingTableId.trim() : ''
  if (cfg.tableMode === 'existing' && tid) {
    rows.push({ label: '已有表 ID', value: tid })
  }

  const hasAuth = typeof cfg.authCode === 'string' && cfg.authCode.trim().length > 0
  rows.push({ label: 'API-Key', value: hasAuth ? '已填写' : '未填写' })

  return rows
}

/** 用于预览展示：脱敏 `authCode` */
export function snapshotForPreview(raw: Record<string, unknown>): Record<string, unknown> {
  const o = JSON.parse(JSON.stringify(raw)) as Record<string, unknown>
  if (typeof o.authCode === 'string' && o.authCode.trim()) {
    o.authCode = '***'
  }
  return o
}

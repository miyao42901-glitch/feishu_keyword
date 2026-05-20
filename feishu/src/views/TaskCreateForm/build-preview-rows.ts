/**
 * 将保存后的 `config_json` 快照转为预览表格行（不含敏感字段原文）。
 */
import dayjs from 'dayjs'
import customParseFormat from 'dayjs/plugin/customParseFormat'
import type { PlatformKey } from '@/components/PlatformIcon.vue'

dayjs.extend(customParseFormat)
import { countScheduledExecutionRounds } from '@/lib/datetime-task-window'
import {
  DATETIME_FORMAT,
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
  rows.push({ label: '任务名称', value: planName || '—' })

  const taskType = cfg.taskType === 'realtime' ? '单次任务' : '定时任务'
  rows.push({ label: '任务类型', value: taskType })

  if (cfg.taskType !== 'realtime') {
    rows.push({
      label: '采集频率',
      value: optLabel(frequencyOptions, cfg.crawlFrequency),
    })
    const eff = typeof cfg.effectiveAt === 'string' ? cfg.effectiveAt.trim() : ''
    const exp = typeof cfg.expireAt === 'string' ? cfg.expireAt.trim() : ''
    rows.push({ label: '开始时间', value: eff || '—' })
    rows.push({ label: '结束时间', value: exp || '—' })
    const rounds = countScheduledExecutionRounds(eff, exp, cfg.crawlFrequency)
    rows.push({
      label: '预计采集轮次',
      value: rounds > 0 ? `${rounds} 轮（按开始+频率至结束，结束时刻可能补采）` : '—',
    })
  }

  rows.push({ label: '监控关键词', value: joinArr(cfg.keywords) })
  rows.push({ label: '排除词', value: joinArr(cfg.excludeKeywords) })
  rows.push({ label: '排序方式', value: optLabel(sortOrderOptions, cfg.sortOrder) })
  rows.push({ label: '发布时间', value: optLabel(publishTimeOptions, cfg.publishTime) })
  rows.push({ label: '视频时长', value: optLabel(videoDurationOptions, cfg.videoDuration) })
  rows.push({
    label: '选择条数',
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

  const notifyOn =
    cfg.feishuNotifyEnabled === true ||
    cfg.feishuNotifyEnabled === 1 ||
    String(cfg.feishuNotifyEnabled ?? '')
      .trim()
      .toLowerCase() === 'true'
  rows.push({
    label: '飞书通知',
    value: notifyOn ? '开启' : '关闭',
  })
  if (notifyOn) {
    const wh = typeof cfg.feishuWebhookUrl === 'string' ? cfg.feishuWebhookUrl.trim() : ''
    rows.push({ label: 'Webhook', value: wh ? '已填写' : '未填写' })
  }

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

function formatTaskWindowDuration(effectiveAt: string, expireAt: string): string {
  const a = effectiveAt.trim()
  const b = expireAt.trim()
  if (!a || !b) return '—'
  const d1 = dayjs(a, DATETIME_FORMAT, true)
  const d2 = dayjs(b, DATETIME_FORMAT, true)
  if (!d1.isValid() || !d2.isValid()) return '—'
  const diffMs = d2.diff(d1)
  if (diffMs <= 0) return '—'
  const days = Math.floor(diffMs / 86400000)
  const hours = Math.floor((diffMs % 86400000) / 3600000)
  const minutes = Math.floor((diffMs % 3600000) / 60000)
  const parts: string[] = []
  if (days) parts.push(`${days}天`)
  if (hours) parts.push(`${hours}小时`)
  if (!days && !hours && minutes) parts.push(`${minutes}分钟`)
  if (!parts.length && diffMs > 0) parts.push('不足1分钟')
  return parts.length ? parts.join('') : '—'
}

function formatDataRangeLabel(cfg: Record<string, unknown>): string {
  const dr = cfg.dataRange
  const n = typeof dr === 'number' ? dr : Number(dr)
  return Number.isFinite(n) && n > 0 ? `${Math.floor(n)}条` : '—'
}

/** 确认弹框：标签 + 展示值 */
export type TaskConfigConfirmRow = { label: string; value: string }

function formatTargetTable(cfg: Record<string, unknown>): string {
  const src = cfg.selectedSources
  if (!Array.isArray(src) || src.length === 0) return '—'
  const platforms = src.filter(
    (x): x is PlatformKey => typeof x === 'string' && x in platformDisplayNames,
  )
  if (!platforms.length) return '—'

  if (cfg.tableMode === 'new') {
    const names = cfg.platformNewTableNames
    if (names && typeof names === 'object' && !Array.isArray(names)) {
      const parts = platforms
        .map((p) => {
          const n = String((names as Record<string, unknown>)[p] ?? '').trim()
          return n ? `${platformDisplayNames[p]}：${n}` : null
        })
        .filter((x): x is string => !!x)
      if (parts.length) return parts.join('；')
    }
    return '自动新建'
  }

  if (cfg.tableMode === 'existing') {
    const ids = cfg.platformExistingTableIds
    if (ids && typeof ids === 'object' && !Array.isArray(ids)) {
      const parts = platforms.map((p) => {
        const id = String((ids as Record<string, unknown>)[p] ?? '').trim()
        return id
          ? `${platformDisplayNames[p]}：已关联`
          : `${platformDisplayNames[p]}：未选择`
      })
      return parts.join('；')
    }
    return '—'
  }

  return '—'
}

/**
 * 「确认任务配置」弹框：与设计稿一致的字段顺序与展示。
 */
export function buildTaskConfigConfirmRows(cfg: Record<string, unknown>): TaskConfigConfirmRow[] {
  const rows: TaskConfigConfirmRow[] = []
  const isRealtime = cfg.taskType === 'realtime'

  const planName = typeof cfg.planName === 'string' ? cfg.planName.trim() : ''
  rows.push({ label: '任务名称', value: planName || '—' })

  rows.push({ label: '任务类型', value: isRealtime ? '单次任务' : '定时任务' })

  const eff = typeof cfg.effectiveAt === 'string' ? cfg.effectiveAt.trim() : ''
  const exp = typeof cfg.expireAt === 'string' ? cfg.expireAt.trim() : ''
  rows.push({
    label: '任务开始时间',
    value: !isRealtime && eff ? eff : '—',
  })
  rows.push({
    label: '任务结束时间',
    value: !isRealtime && exp ? exp : '—',
  })
  rows.push({
    label: '任务时长',
    value: !isRealtime && eff && exp ? formatTaskWindowDuration(eff, exp) : '—',
  })
  if (!isRealtime && eff && exp) {
    const rounds = countScheduledExecutionRounds(eff, exp, cfg.crawlFrequency)
    rows.push({
      label: '预计采集轮次',
      value: rounds > 0 ? `${rounds} 轮` : '—',
    })
    rows.push({
      label: '采集频率',
      value: optLabel(frequencyOptions, cfg.crawlFrequency),
    })
  }

  rows.push({ label: '监控关键词', value: joinArr(cfg.keywords) })
  rows.push({ label: '排除词', value: joinArr(cfg.excludeKeywords) })
  rows.push({ label: '排序方式', value: optLabel(sortOrderOptions, cfg.sortOrder) })
  rows.push({ label: '发布时间', value: optLabel(publishTimeOptions, cfg.publishTime) })
  rows.push({ label: '视频时长', value: optLabel(videoDurationOptions, cfg.videoDuration) })
  rows.push({ label: '选择条数', value: formatDataRangeLabel(cfg) })

  const src = cfg.selectedSources
  if (Array.isArray(src) && src.length) {
    const labels = src
      .filter((x): x is PlatformKey => typeof x === 'string' && x in platformDisplayNames)
      .map((k) => platformDisplayNames[k])
    rows.push({ label: '采集平台', value: labels.join('、') })
  } else {
    rows.push({ label: '采集平台', value: '—' })
  }

  rows.push({ label: '目标表格', value: formatTargetTable(cfg) })

  const notifyOn =
    cfg.feishuNotifyEnabled === true ||
    cfg.feishuNotifyEnabled === 1 ||
    String(cfg.feishuNotifyEnabled ?? '')
      .trim()
      .toLowerCase() === 'true'
  rows.push({ label: '飞书通知', value: notifyOn ? '开启' : '关闭' })

  const wh = typeof cfg.feishuWebhookUrl === 'string' ? cfg.feishuWebhookUrl.trim() : ''
  rows.push({
    label: 'Webhook地址',
    value: notifyOn && wh ? wh : '—',
  })

  return rows
}

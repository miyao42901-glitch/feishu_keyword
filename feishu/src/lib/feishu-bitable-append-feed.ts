/**
 * 将「运行中」且仅抖音/小红书任务的演示数据写入当前多维表格。
 * 列名与列顺序由任务 `sourceFieldSelection`（采集字段）决定，值来自 test_data 映射。
 */

import { bitable, FieldType, type IAddTableConfig } from '@lark-base-open/js-sdk'
import type { PlatformKey } from '@/components/PlatformIcon.vue'
import { getOrderedColumnLabelsForPlatform } from '@/lib/test-data-field-map'
import type { TestFeedRow } from '@/lib/test-data-feed'

/** 仅当任务未配置任何采集字段时，尝试匹配默认「文本」列做兜底 */
const FALLBACK_TEXT_COLUMN_NAMES = ['文本', '多行文本', '备注', '说明'] as const

export type TestFeedBitableDeps = {
  /** 自动新建表后把 tableId 写入配置；传空字符串表示清除该平台已失效的表 id */
  persistPlatformTableReference: (input: {
    taskId: number
    platform: PlatformKey
    tableId: string
  }) => Promise<void>
}

function readTableMode(cfg: Record<string, unknown>): 'new' | 'existing' {
  const m = cfg.tableMode ?? cfg.table_mode
  return m === 'existing' ? 'existing' : 'new'
}

function readPlatformExistingTableId(cfg: Record<string, unknown>, platform: PlatformKey): string {
  const raw = cfg.platformExistingTableIds ?? cfg.platform_existing_table_ids
  if (!raw || typeof raw !== 'object') return ''
  const v = (raw as Record<string, unknown>)[platform]
  return typeof v === 'string' ? v.trim() : ''
}

function clearPlatformTableIdInCfg(cfg: Record<string, unknown>, platform: PlatformKey): void {
  const rawIds = cfg.platformExistingTableIds ?? cfg.platform_existing_table_ids
  if (!rawIds || typeof rawIds !== 'object' || Array.isArray(rawIds)) return
  const merged = { ...(rawIds as Record<string, unknown>) }
  delete merged[platform]
  cfg.platformExistingTableIds = merged
}

async function isBitableTableReachable(tableId: string): Promise<boolean> {
  if (!tableId.trim()) return false
  try {
    if (typeof bitable.base.isTableExist === 'function') {
      return await bitable.base.isTableExist(tableId)
    }
    await bitable.base.getTable(tableId)
    return true
  } catch {
    return false
  }
}

async function resolveStoredPlatformTableId(
  cfg: Record<string, unknown>,
  platform: PlatformKey,
  taskId: number,
  deps: TestFeedBitableDeps | undefined,
  mutCfg: Map<number, Record<string, unknown>>,
): Promise<string> {
  const tableId = readPlatformExistingTableId(cfg, platform)
  if (!tableId) return ''
  const ok = await isBitableTableReachable(tableId)
  if (ok) return tableId

  const next = { ...cfg }
  clearPlatformTableIdInCfg(next, platform)
  mutCfg.set(taskId, next)
  if (deps && readTableMode(cfg) === 'new') {
    try {
      await deps.persistPlatformTableReference({ taskId, platform, tableId: '' })
    } catch {
      /* */
    }
  }
  return ''
}

function readPlatformNewTableName(cfg: Record<string, unknown>, platform: PlatformKey): string {
  const raw = cfg.platformNewTableNames ?? cfg.platform_new_table_names
  if (raw && typeof raw === 'object') {
    const v = (raw as Record<string, unknown>)[platform]
    if (typeof v === 'string' && v.trim()) return v.trim()
  }
  return platform === 'douyin' ? '抖音数据表' : '小红书数据表'
}

type BitableTable = Awaited<ReturnType<typeof bitable.base.getTable>>
type BitableField = Awaited<ReturnType<BitableTable['getFieldList']>>[number]

async function resolveFirstFieldId(table: BitableTable, names: readonly string[]): Promise<string | null> {
  for (const name of names) {
    try {
      const f = await table.getFieldByName(name)
      const id = f && typeof (f as { id?: unknown }).id === 'string' ? ((f as { id: string }).id as string) : null
      if (id?.trim()) return id.trim()
    } catch {
      /* */
    }
  }
  return null
}

/** 将新建表默认主字段改名为任务配置中的第一列（如「视频唯一 ID」「标题」等） */
async function configurePrimaryColumn(table: BitableTable, primaryLabel: string): Promise<void> {
  if (!primaryLabel.trim()) return

  let primaryField: BitableField | null = null
  try {
    for (const field of await table.getFieldList()) {
      const meta = await field.getMeta()
      if (meta.isPrimary) {
        primaryField = field
        break
      }
    }
  } catch {
    return
  }
  if (!primaryField) return

  let primaryName = ''
  try {
    primaryName = (await primaryField.getName()).trim()
  } catch {
    return
  }
  if (primaryName === primaryLabel) return

  try {
    for (const field of await table.getFieldList()) {
      if (field.id === primaryField.id) continue
      if ((await field.getName()).trim() === primaryLabel) {
        await table.deleteField(field.id)
        break
      }
    }
  } catch {
    /* */
  }

  try {
    await table.setField(primaryField.id, {
      type: FieldType.Text,
      name: primaryLabel,
    })
  } catch {
    /* */
  }
}

/** 按任务采集字段配置补齐列（首列为主字段，其余 addField） */
async function ensureConfiguredColumns(table: BitableTable, orderedLabels: string[]): Promise<void> {
  const labels = orderedLabels.map((s) => s.trim()).filter(Boolean)
  if (!labels.length) return

  try {
    await configurePrimaryColumn(table, labels[0])
  } catch {
    /* */
  }

  const primaryLabel = labels[0]
  for (let i = 1; i < labels.length; i++) {
    const name = labels[i]
    try {
      const existing = await resolveFirstFieldId(table, [name])
      if (existing) continue
      await table.addField({ type: FieldType.Text, name })
    } catch {
      /* */
    }
  }

  if (primaryLabel) {
    try {
      await configurePrimaryColumn(table, primaryLabel)
    } catch {
      /* */
    }
  }
}

async function resolveColumnFieldIds(
  table: BitableTable,
  orderedLabels: string[],
): Promise<Map<string, string>> {
  const map = new Map<string, string>()
  for (const label of orderedLabels) {
    const id = await resolveFirstFieldId(table, [label])
    if (id) map.set(label, id)
  }
  return map
}

function rowFingerprint(row: TestFeedRow): string {
  const id =
    row.fieldColumns['视频唯一ID'] ??
    row.fieldColumns['笔记ID'] ??
    row.fieldColumns['视频播放页链接'] ??
    row.fieldColumns['笔记标题'] ??
    row.url
  return `${row.taskId}:${row.platform}:${id}:${row.publishMs}`
}

const appendedFingerprintsByTask = new Map<number, Set<string>>()

export function pruneTestFeedAppendState(runningTaskIds: Set<number>): void {
  for (const id of [...appendedFingerprintsByTask.keys()]) {
    if (!runningTaskIds.has(id)) appendedFingerprintsByTask.delete(id)
  }
}

export function clearTestFeedAppendStateForTask(taskId: number): void {
  appendedFingerprintsByTask.delete(taskId)
}

function getFpSet(taskId: number): Set<string> {
  let set = appendedFingerprintsByTask.get(taskId)
  if (!set) {
    set = new Set()
    appendedFingerprintsByTask.set(taskId, set)
  }
  return set
}

function filterNotYetAppended(rows: TestFeedRow[]): TestFeedRow[] {
  const seen = new Set<string>()
  const out: TestFeedRow[] = []
  for (const row of rows) {
    const fp = rowFingerprint(row)
    if (getFpSet(row.taskId).has(fp) || seen.has(fp)) continue
    seen.add(fp)
    out.push(row)
  }
  return out
}

function markAppended(rows: TestFeedRow[]): void {
  for (const row of rows) {
    getFpSet(row.taskId).add(rowFingerprint(row))
  }
}

function rowToFields(
  row: TestFeedRow,
  columnIds: Map<string, string>,
  fallbackTextFieldId: string | null,
): Record<string, string> {
  const fields: Record<string, string> = {}
  for (const [label, fieldId] of columnIds) {
    const v = row.fieldColumns[label]
    if (v !== undefined && v !== '') fields[fieldId] = v
  }

  if (Object.keys(fields).length > 0) return fields

  if (fallbackTextFieldId) {
    const lines = Object.entries(row.fieldColumns)
      .filter(([, v]) => v)
      .map(([k, v]) => `${k}：${v}`)
    if (lines.length) fields[fallbackTextFieldId] = lines.join('\n')
  }
  return fields
}

const tableCreateLocks = new Map<string, Promise<string>>()

async function resolveOrCreateTableId(
  taskId: number,
  platform: PlatformKey,
  deps: TestFeedBitableDeps | undefined,
  mutCfg: Map<number, Record<string, unknown>>,
): Promise<string> {
  const cfg0 = mutCfg.get(taskId)
  if (!cfg0) return ''
  const hit = await resolveStoredPlatformTableId(cfg0, platform, taskId, deps, mutCfg)
  if (hit) return hit

  const cfgAfter = mutCfg.get(taskId)
  if (!cfgAfter || readTableMode(cfgAfter) !== 'new' || !deps) return ''

  const lockKey = `${taskId}:${platform}`
  const pending = tableCreateLocks.get(lockKey)
  if (pending) return pending

  const run = (async () => {
    const cfg = mutCfg.get(taskId)
    if (!cfg) return ''
    const again = await resolveStoredPlatformTableId(cfg, platform, taskId, deps, mutCfg)
    if (again) return again

    try {
      if (!(await bitable.base.isEditable())) return ''
    } catch {
      return ''
    }

    const name = readPlatformNewTableName(cfg, platform)
    let tableId = ''
    try {
      const res = await bitable.base.addTable({ name, fields: [] } as IAddTableConfig)
      tableId = typeof res?.tableId === 'string' ? res.tableId.trim() : ''
    } catch {
      return ''
    }
    if (!tableId) return ''

    let table: BitableTable
    try {
      table = await bitable.base.getTable(tableId)
    } catch {
      return ''
    }

    const orderedLabels = getOrderedColumnLabelsForPlatform(cfg, platform)
    try {
      await ensureConfiguredColumns(table, orderedLabels)
    } catch {
      /* */
    }

    const next = { ...cfg }
    const rawIds = next.platformExistingTableIds ?? next.platform_existing_table_ids
    const merged =
      rawIds && typeof rawIds === 'object' && !Array.isArray(rawIds)
        ? { ...(rawIds as Record<string, unknown>) }
        : {}
    merged[platform] = tableId
    next.platformExistingTableIds = merged
    mutCfg.set(taskId, next)

    try {
      await deps.persistPlatformTableReference({ taskId, platform, tableId })
    } catch {
      /* */
    }

    return tableId
  })().finally(() => {
    tableCreateLocks.delete(lockKey)
  })

  tableCreateLocks.set(lockKey, run)
  return run
}

function readTaskPlatformKeys(config: Record<string, unknown>): PlatformKey[] {
  const raw = config.selectedSources ?? config.selected_sources
  if (!Array.isArray(raw)) return []
  const out: PlatformKey[] = []
  for (const x of raw) {
    if (x === 'douyin' || x === 'xiaohongshu') out.push(x)
  }
  return out
}

/**
 * 「自动新建表格」：按 `platformNewTableNames` 预先创建各平台数据表及列（无需等待运行中轮询）。
 */
export async function ensureBitableTablesForTask(
  taskId: number,
  config: Record<string, unknown>,
  deps: TestFeedBitableDeps,
): Promise<void> {
  if (readTableMode(config) !== 'new') return

  const mutCfg = new Map<number, Record<string, unknown>>()
  mutCfg.set(taskId, { ...config })

  for (const platform of readTaskPlatformKeys(config)) {
    await resolveOrCreateTableId(taskId, platform, deps, mutCfg)
  }
}

async function resolveTableIdForRow(
  row: TestFeedRow,
  deps: TestFeedBitableDeps | undefined,
  mutCfg: Map<number, Record<string, unknown>>,
): Promise<string> {
  const cfg = mutCfg.get(row.taskId)
  if (!cfg) return ''
  const mode = readTableMode(cfg)
  let tableId = await resolveStoredPlatformTableId(cfg, row.platform, row.taskId, deps, mutCfg)
  if (!tableId && mode === 'new') {
    tableId = await resolveOrCreateTableId(row.taskId, row.platform, deps, mutCfg)
  } else if (!tableId && mode === 'existing') {
    tableId = readPlatformExistingTableId(cfg, row.platform)
  }
  return tableId
}

/** 各任务本次实际写入飞书的行数 */
export async function appendTestFeedRowsToBitable(
  rows: TestFeedRow[],
  configByTaskId: Map<number, Record<string, unknown>>,
  deps?: TestFeedBitableDeps,
): Promise<Map<number, number>> {
  const writtenByTaskId = new Map<number, number>()
  type Group = { tableId: string; rows: TestFeedRow[]; platform: PlatformKey; taskId: number }
  const byTable = new Map<string, Group>()

  for (const row of rows) {
    const tableId = await resolveTableIdForRow(row, deps, configByTaskId)
    if (!tableId) continue
    let g = byTable.get(tableId)
    if (!g) {
      g = { tableId, rows: [], platform: row.platform, taskId: row.taskId }
      byTable.set(tableId, g)
    }
    g.rows.push(row)
  }

  for (const { tableId, rows: tableRows, platform, taskId } of byTable.values()) {
    if (!tableRows.length) continue
    const fresh = filterNotYetAppended(tableRows)
    if (!fresh.length) continue

    const cfg = configByTaskId.get(taskId)
    const orderedLabels = cfg ? getOrderedColumnLabelsForPlatform(cfg, platform) : []

    let table: BitableTable
    try {
      table = await bitable.base.getTable(tableId)
    } catch {
      continue
    }

    if (orderedLabels.length) {
      try {
        await ensureConfiguredColumns(table, orderedLabels)
      } catch {
        /* */
      }
    }

    const columnIds = await resolveColumnFieldIds(table, orderedLabels)
    const fallbackTextFieldId = await resolveFirstFieldId(table, FALLBACK_TEXT_COLUMN_NAMES)
    if (columnIds.size === 0 && !fallbackTextFieldId) continue

    const BATCH = 80
    try {
      for (let i = 0; i < fresh.length; i += BATCH) {
        const sliceRows = fresh.slice(i, i + BATCH)
        const slice = sliceRows.map((row) => ({
          fields: rowToFields(row, columnIds, fallbackTextFieldId),
        }))
        await table.addRecords(slice as never)
        markAppended(sliceRows)
        for (const row of sliceRows) {
          writtenByTaskId.set(row.taskId, (writtenByTaskId.get(row.taskId) ?? 0) + 1)
        }
      }
    } catch {
      /* */
    }
  }
  return writtenByTaskId
}

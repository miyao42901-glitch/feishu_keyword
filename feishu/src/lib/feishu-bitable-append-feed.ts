/**
 * 将「运行中」且仅抖音/小红书任务的演示数据写入当前多维表格。
 * 列名与列顺序由任务 `sourceFieldSelection`（采集字段）决定，值来自 test_data 映射。
 */

import { bitable, FieldType, type IAddTableConfig } from '@lark-base-open/js-sdk'
import { fetchBitableTableMetaList } from '@/lib/feishu-bitable-tables'
import type { PlatformKey } from '@/components/PlatformIcon.vue'
import { defaultNewTableNameForPlatform, readSyncCollectionPlatforms } from '@/lib/sync-collection-platforms'
import { getOrderedColumnLabelsForPlatform } from '@/lib/test-data-field-map'
import { buildPlatformItemDedupKey, type TestFeedRow } from '@/lib/test-data-feed'

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

export function readPlatformNewTableName(cfg: Record<string, unknown>, platform: PlatformKey): string {
  const raw = cfg.platformNewTableNames ?? cfg.platform_new_table_names
  if (raw && typeof raw === 'object') {
    const v = (raw as Record<string, unknown>)[platform]
    if (typeof v === 'string' && v.trim()) return v.trim()
  }
  if (
    platform === 'douyin' ||
    platform === 'xiaohongshu' ||
    platform === 'shipinhao' ||
    platform === 'gzh'
  ) {
    return defaultNewTableNameForPlatform(platform)
  }
  return '数据表'
}

type BitableTable = Awaited<ReturnType<typeof bitable.base.getTable>>
type BitableField = Awaited<ReturnType<BitableTable['getFieldList']>>[number]

function normalizeColumnLabelForMatch(label: string): string {
  return label
    .trim()
    .replace(/\s+/g, '')
    .replace(/[()（）]/g, '')
    .toLowerCase()
}

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
  const tableFields: { id: string; name: string; norm: string }[] = []
  try {
    for (const field of await table.getFieldList()) {
      const name = (await field.getName()).trim()
      const id =
        field && typeof (field as { id?: unknown }).id === 'string'
          ? ((field as { id: string }).id as string).trim()
          : ''
      if (id && name) {
        tableFields.push({ id, name, norm: normalizeColumnLabelForMatch(name) })
      }
    }
  } catch {
    /* */
  }

  for (const label of orderedLabels) {
    let id = await resolveFirstFieldId(table, [label])
    if (!id && tableFields.length) {
      const norm = normalizeColumnLabelForMatch(label)
      const hit =
        tableFields.find((f) => f.name === label) ??
        tableFields.find((f) => f.norm === norm)
      id = hit?.id ?? null
    }
    if (id) map.set(label, id)
  }
  return map
}

function rowFingerprint(row: TestFeedRow): string {
  const stable = row.itemStableId?.trim()
  if (stable) return buildPlatformItemDedupKey(row.platform, stable)

  const fromColumns =
    row.fieldColumns['视频唯一ID'] ??
    row.fieldColumns['文章ID'] ??
    row.fieldColumns['笔记ID'] ??
    row.fieldColumns['视频链接'] ??
    row.fieldColumns['视频播放页链接']
  const colId = typeof fromColumns === 'string' ? fromColumns.trim() : ''
  if (colId) return `${row.taskId}:${row.platform}:${colId}`

  const url = row.url?.trim()
  if (url && url !== '—') return `${row.taskId}:${row.platform}:${url}`

  const title = row.title?.trim()
  if (title && title !== '—') {
    return `${row.taskId}:${row.platform}:${title}:${row.publishMs}:${row.author}`
  }

  return `${row.taskId}:${row.platform}:${row.publishMs}:${row.collectedAtMs}:${row.author}`
}

/** 已有平台内容 ID 的条目：跨任务、跨次执行均不再写入 */
const appendedPlatformItemKeys = new Set<string>()
/** 无稳定 ID 时的兜底指纹（按任务隔离） */
const appendedFingerprintsByTask = new Map<number, Set<string>>()

function hasStablePlatformItemId(row: TestFeedRow): boolean {
  return Boolean(row.itemStableId?.trim())
}

function isRowAlreadyAppended(row: TestFeedRow, fp: string): boolean {
  if (hasStablePlatformItemId(row)) return appendedPlatformItemKeys.has(fp)
  return getFpSet(row.taskId).has(fp)
}

export function pruneTestFeedAppendState(runningTaskIds: Set<number>): void {
  for (const id of [...appendedFingerprintsByTask.keys()]) {
    if (!runningTaskIds.has(id)) appendedFingerprintsByTask.delete(id)
  }
}

export function clearTestFeedAppendStateForTask(taskId: number): void {
  appendedFingerprintsByTask.delete(taskId)
}

/** 新一轮单次任务执行前清空全局「平台+内容ID」去重（避免上次执行导致本次 0 写入） */
export function clearGlobalBitableAppendDedup(): void {
  appendedPlatformItemKeys.clear()
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
    if (isRowAlreadyAppended(row, fp) || seen.has(fp)) continue
    seen.add(fp)
    out.push(row)
  }
  return out
}

/** 尚未写入飞书表格、且未在本次批次内重复的行数（与 `appendTestFeedRowsToBitable` 去重规则一致） */
export function countRowsPendingBitableAppend(rows: TestFeedRow[]): number {
  return filterNotYetAppended(rows).length
}

function markAppended(rows: TestFeedRow[]): void {
  for (const row of rows) {
    const fp = rowFingerprint(row)
    if (hasStablePlatformItemId(row)) {
      appendedPlatformItemKeys.add(fp)
    } else {
      getFpSet(row.taskId).add(fp)
    }
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

/** 与多维表格标签页展示名对齐，避免首尾空格导致「已存在表」匹配失败 */
function normalizeTableDisplayName(name: string): string {
  return name.trim().replace(/\s+/g, ' ')
}

function tableDisplayNamesMatch(a: string, b: string): boolean {
  const left = normalizeTableDisplayName(a)
  const right = normalizeTableDisplayName(b)
  return left.length > 0 && left === right
}

async function findTableIdByDisplayName(name: string): Promise<string> {
  const want = normalizeTableDisplayName(name)
  if (!want) return ''
  try {
    const list = await fetchBitableTableMetaList()
    const hit = list.find((t) => tableDisplayNamesMatch(t.name, want))
    return hit?.id?.trim() ?? ''
  } catch {
    return ''
  }
}

/** 飞书不支持同名新建；建表失败或空 tableId 时按展示名回查已有表（含短暂重试） */
async function findTableIdByDisplayNameWithRetry(
  name: string,
  options?: { attempts?: number; delayMs?: number },
): Promise<string> {
  const attempts = Math.max(1, options?.attempts ?? 3)
  const delayMs = options?.delayMs ?? 150
  for (let i = 0; i < attempts; i++) {
    const id = await findTableIdByDisplayName(name)
    if (id) return id
    if (i < attempts - 1) {
      await new Promise((r) => setTimeout(r, delayMs))
    }
  }
  return ''
}

async function createOrReuseTableByDisplayName(name: string): Promise<string> {
  const displayName = normalizeTableDisplayName(name)
  if (!displayName) return ''

  let tableId = await findTableIdByDisplayNameWithRetry(displayName, { attempts: 1 })
  if (tableId) return tableId

  try {
    const res = await bitable.base.addTable({ name: displayName } as IAddTableConfig)
    tableId = typeof res?.tableId === 'string' ? res.tableId.trim() : ''
  } catch (e) {
    const detail = e instanceof Error ? e.message : String(e)
    const reused = await findTableIdByDisplayNameWithRetry(displayName)
    if (reused) return reused
    throw new Error(`新建数据表「${displayName}」失败：${detail}`)
  }

  if (!tableId) {
    tableId = await findTableIdByDisplayNameWithRetry(displayName)
  }
  return tableId
}

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

    let editable = false
    try {
      editable = await bitable.base.isEditable()
    } catch {
      editable = false
    }
    if (!editable) {
      throw new Error(
        '当前环境无法新建多维表格：请在飞书多维表格内打开本插件后再执行（浏览器单独打开页面无建表权限）',
      )
    }

    const name = readPlatformNewTableName(cfg, platform)
    const tableId = await createOrReuseTableByDisplayName(name)
    if (!tableId) {
      throw new Error(`新建数据表「${normalizeTableDisplayName(name)}」失败：未找到或创建数据表`)
    }

    let table: BitableTable
    try {
      table = await bitable.base.getTable(tableId)
    } catch (e) {
      const detail = e instanceof Error ? e.message : String(e)
      throw new Error(`无法打开数据表「${name}」：${detail}`)
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
  return readSyncCollectionPlatforms(config)
}

/**
 * 「自动新建表格」：按 `platformNewTableNames` 预先创建各平台数据表及列（无需等待运行中轮询）。
 */
export async function ensureBitableTablesForTask(
  taskId: number,
  config: Record<string, unknown>,
  deps: TestFeedBitableDeps,
  options?: { platforms?: PlatformKey[] },
): Promise<string[]> {
  if (readTableMode(config) !== 'new') return []

  const mutCfg = new Map<number, Record<string, unknown>>()
  mutCfg.set(taskId, { ...config })

  const platforms = options?.platforms?.length
    ? options.platforms
    : readTaskPlatformKeys(config)
  const createdNames: string[] = []

  for (const platform of platforms) {
    const tableId = await resolveOrCreateTableId(taskId, platform, deps, mutCfg)
    if (!tableId) {
      throw new Error(`平台「${platform}」建表失败，请确认在飞书多维表格插件内执行`)
    }
    const cfgNow = mutCfg.get(taskId) ?? config
    createdNames.push(readPlatformNewTableName(cfgNow, platform))
  }

  return createdNames
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

  const skippedNoTable: Partial<Record<PlatformKey, number>> = {}

  for (const row of rows) {
    const tableId = await resolveTableIdForRow(row, deps, configByTaskId)
    if (!tableId) {
      skippedNoTable[row.platform] = (skippedNoTable[row.platform] ?? 0) + 1
      continue
    }
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
    } catch (err) {
      const detail = err instanceof Error ? err.message : String(err)
      console.warn('[bitable-append] addRecords failed', { platform, taskId, tableId, detail })
      throw new Error(`写入「${readPlatformNewTableName(cfg ?? {}, platform)}」失败：${detail}`)
    }
  }

  if (import.meta.env.DEV) {
    const writtenByPlatform: Partial<Record<PlatformKey, number>> = {}
    const freshByPlatform: Partial<Record<PlatformKey, number>> = {}
    for (const { platform, rows: tableRows } of byTable.values()) {
      writtenByPlatform[platform] = tableRows.length
    }
    for (const row of rows) {
      const fp = rowFingerprint(row)
      if (!getFpSet(row.taskId).has(fp)) {
        freshByPlatform[row.platform] = (freshByPlatform[row.platform] ?? 0) + 1
      }
    }
    console.log('[bitable-append]', {
      inputRows: rows.length,
      pendingFreshByPlatform: freshByPlatform,
      skippedNoTable,
      tables: [...byTable.values()].map((g) => ({
        platform: g.platform,
        tableId: g.tableId,
        rows: g.rows.length,
        fresh: filterNotYetAppended(g.rows).length,
      })),
    })
  }

  const skippedTotal = Object.values(skippedNoTable).reduce((a, b) => a + b, 0)
  if (skippedTotal > 0 && import.meta.env.DEV) {
    console.warn('[bitable-append] 未解析到 tableId，已跳过行', skippedNoTable)
  }

  return writtenByTaskId
}

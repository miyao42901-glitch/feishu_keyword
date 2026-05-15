/**
 * 将「运行中」且仅抖音/小红书任务的演示数据写入当前多维表格。
 * - 「使用现有表格」：按 platformExistingTableIds 写入；
 * - 「自动新建表格」：首次写入时 addTable、补列并回写 platformExistingTableIds；
 * - 分列写入：任务 / 平台 / 标题 / 作者 / 时间 / 链接（必要时自动 addField）；
 * - 同一任务运行期间按行指纹去重，避免定时刷新重复追加（仅成功写入后计入指纹）。
 */

import { bitable, FieldType, type IAddTableConfig } from '@lark-base-open/js-sdk'
import type { PlatformKey } from '@/components/PlatformIcon.vue'
import type { TestFeedRow } from '@/lib/test-data-feed'

/** 与表中字段名一致即可匹配；同时用于 ensure 时新建列的默认名 */
const NAME_GROUPS = {
  task: ['任务', '任务名称', '任务名', '计划名称'],
  platform: ['平台', '采集平台', '来源', '来源平台'],
  title: ['标题', '内容标题', '笔记标题', '名称'],
  singleText: ['文本', '多行文本', '备注', '说明'],
  author: ['作者', '昵称', '发布者', '达人'],
  time: ['发布时间', '时间', '发布日期'],
  link: ['链接', '原文链接', 'URL', '地址'],
} as const

/** 主字段（带锁列）目标列名，与 FeishuPlugin `tableHelper` 中 `isPrimary` 字段一致 */
const PRIMARY_COLUMN_NAME = NAME_GROUPS.title[0]

/** ensure 时按此顺序补列（「标题」由主字段承担，不在此重复 addField） */
const STANDARD_COLUMN_NAMES = ['任务', '平台', '作者', '时间', '链接'] as const

type FieldIdMap = {
  task: string | null
  platform: string | null
  title: string | null
  singleText: string | null
  author: string | null
  time: string | null
  link: string | null
}

export type TestFeedBitableDeps = {
  /** 自动新建表后把 tableId 写入配置（合并 platformExistingTableIds） */
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

function readPlatformNewTableName(cfg: Record<string, unknown>, platform: PlatformKey): string {
  const raw = cfg.platformNewTableNames ?? cfg.platform_new_table_names
  if (raw && typeof raw === 'object') {
    const v = (raw as Record<string, unknown>)[platform]
    if (typeof v === 'string' && v.trim()) return v.trim()
  }
  return platform === 'douyin' ? '抖音数据表' : '小红书数据表'
}

async function resolveFirstFieldId(
  table: Awaited<ReturnType<typeof bitable.base.getTable>>,
  names: readonly string[],
): Promise<string | null> {
  for (const name of names) {
    try {
      const f = await table.getFieldByName(name)
      const id = f && typeof (f as { id?: unknown }).id === 'string' ? ((f as { id: string }).id as string) : null
      if (id?.trim()) return id.trim()
    } catch {
      /* 无此字段名 */
    }
  }
  return null
}

async function resolveFieldIdMap(table: Awaited<ReturnType<typeof bitable.base.getTable>>): Promise<FieldIdMap> {
  return {
    task: await resolveFirstFieldId(table, NAME_GROUPS.task),
    platform: await resolveFirstFieldId(table, NAME_GROUPS.platform),
    title: await resolveFirstFieldId(table, NAME_GROUPS.title),
    singleText: await resolveFirstFieldId(table, NAME_GROUPS.singleText),
    author: await resolveFirstFieldId(table, NAME_GROUPS.author),
    time: await resolveFirstFieldId(table, NAME_GROUPS.time),
    link: await resolveFirstFieldId(table, NAME_GROUPS.link),
  }
}

type BitableTable = Awaited<ReturnType<typeof bitable.base.getTable>>
type BitableField = Awaited<ReturnType<BitableTable['getFieldList']>>[number]

/** 将新建表默认带锁主字段改名为「标题」（参考 FeishuPlugin `writeToTable` + `setField`） */
async function configurePrimaryAsTitleColumn(table: BitableTable): Promise<void> {
  let primaryField: BitableField | null = null
  try {
    const fieldList = await table.getFieldList()
    for (const field of fieldList) {
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
  if (primaryName === PRIMARY_COLUMN_NAME) return

  try {
    const fieldList = await table.getFieldList()
    for (const field of fieldList) {
      if (field.id === primaryField.id) continue
      const name = (await field.getName()).trim()
      if (name === PRIMARY_COLUMN_NAME) {
        await table.deleteField(field.id)
        break
      }
    }
  } catch {
    /* 删除与主字段同名的重复列失败时仍尝试 setField */
  }

  try {
    await table.setField(primaryField.id, {
      type: FieldType.Text,
      name: PRIMARY_COLUMN_NAME,
    })
  } catch {
    /* 无编辑权限等 */
  }
}

/** 缺分列时补 Text 列；主字段先设为「标题」，其余列 addField */
async function ensureStandardTextColumns(table: BitableTable): Promise<void> {
  try {
    await configurePrimaryAsTitleColumn(table)
  } catch {
    /* */
  }

  let ids = await resolveFieldIdMap(table)
  if (ids.title && ids.platform && ids.author && ids.time && ids.link && ids.task) return

  for (const name of STANDARD_COLUMN_NAMES) {
    ids = await resolveFieldIdMap(table)
    const need =
      (name === '任务' && !ids.task) ||
      (name === '平台' && !ids.platform) ||
      (name === '作者' && !ids.author) ||
      (name === '时间' && !ids.time) ||
      (name === '链接' && !ids.link)
    if (!need) continue
    try {
      await table.addField({ type: FieldType.Text, name })
    } catch {
      /* 无编辑权限或重名等 */
    }
  }

  ids = await resolveFieldIdMap(table)
  if (!ids.title) {
    try {
      await configurePrimaryAsTitleColumn(table)
    } catch {
      /* */
    }
  }
}

function rowFingerprint(row: TestFeedRow): string {
  return `${row.taskId}:${row.platform}:${row.publishMs}:${row.url}:${row.title}`
}

/** 已成功写入飞书的行指纹（停跑后由 prune 清理） */
const appendedFingerprintsByTask = new Map<number, Set<string>>()

export function pruneTestFeedAppendState(runningTaskIds: Set<number>): void {
  for (const id of [...appendedFingerprintsByTask.keys()]) {
    if (!runningTaskIds.has(id)) appendedFingerprintsByTask.delete(id)
  }
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
  return rows.filter((row) => !getFpSet(row.taskId).has(rowFingerprint(row)))
}

function markAppended(rows: TestFeedRow[]): void {
  for (const row of rows) {
    getFpSet(row.taskId).add(rowFingerprint(row))
  }
}

function rowToFields(row: TestFeedRow, ids: FieldIdMap): Record<string, string> {
  const fields: Record<string, string> = {}
  const split =
    !!(ids.title || ids.task) ||
    !!(ids.platform && ids.author && ids.time && ids.link) ||
    !!(ids.title && ids.platform)

  if (!split && ids.singleText) {
    return {
      [ids.singleText]: [
        `任务：${row.taskName}`,
        `平台：${row.platformLabel}`,
        `标题：${row.title}`,
        `作者：${row.author}`,
        `时间：${row.publishedAt}`,
        `链接：${row.url && row.url !== '—' ? row.url : '—'}`,
      ].join('\n'),
    }
  }

  if (ids.task) fields[ids.task] = row.taskName
  if (ids.platform) fields[ids.platform] = row.platformLabel
  if (ids.title) fields[ids.title] = row.title
  if (ids.author) fields[ids.author] = row.author
  if (ids.time) fields[ids.time] = row.publishedAt
  if (ids.link) fields[ids.link] = row.url && row.url !== '—' ? row.url : ''

  if (Object.keys(fields).length === 0 && ids.singleText) {
    fields[ids.singleText] = [
      `任务：${row.taskName}`,
      `平台：${row.platformLabel}`,
      `标题：${row.title}`,
      `作者：${row.author}`,
      `时间：${row.publishedAt}`,
      `链接：${row.url && row.url !== '—' ? row.url : '—'}`,
    ].join('\n')
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
  const hit = readPlatformExistingTableId(cfg0, platform)
  if (hit) return hit

  if (readTableMode(cfg0) !== 'new' || !deps) return ''

  const lockKey = `${taskId}:${platform}`
  const pending = tableCreateLocks.get(lockKey)
  if (pending) return pending

  const run = (async () => {
    const cfg = mutCfg.get(taskId)
    if (!cfg) return ''
    const again = readPlatformExistingTableId(cfg, platform)
    if (again) return again

    try {
      const editable = await bitable.base.isEditable()
      if (!editable) return ''
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

    let table: Awaited<ReturnType<typeof bitable.base.getTable>>
    try {
      table = await bitable.base.getTable(tableId)
    } catch {
      return ''
    }

    try {
      await ensureStandardTextColumns(table)
    } catch {
      /* 列创建失败仍尝试按已有列写入 */
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
      /* 回写失败不影响本次内存映射 */
    }

    return tableId
  })().finally(() => {
    tableCreateLocks.delete(lockKey)
  })

  tableCreateLocks.set(lockKey, run)
  return run
}

async function resolveTableIdForRow(
  row: TestFeedRow,
  deps: TestFeedBitableDeps | undefined,
  mutCfg: Map<number, Record<string, unknown>>,
): Promise<string> {
  const cfg = mutCfg.get(row.taskId)
  if (!cfg) return ''
  const mode = readTableMode(cfg)
  let tableId = readPlatformExistingTableId(cfg, row.platform)
  if (!tableId && mode === 'new') {
    tableId = await resolveOrCreateTableId(row.taskId, row.platform, deps, mutCfg)
  }
  return tableId
}

/**
 * 将 `rows` 按任务配置写入多维表；自动新建模式会建表并依赖 `deps.persistPlatformTableReference` 回写表 id。
 */
export async function appendTestFeedRowsToBitable(
  rows: TestFeedRow[],
  configByTaskId: Map<number, Record<string, unknown>>,
  deps?: TestFeedBitableDeps,
): Promise<void> {
  type Group = { tableId: string; rows: TestFeedRow[] }
  const byTable = new Map<string, Group>()

  for (const row of rows) {
    const tableId = await resolveTableIdForRow(row, deps, configByTaskId)
    if (!tableId) continue
    let g = byTable.get(tableId)
    if (!g) {
      g = { tableId, rows: [] }
      byTable.set(tableId, g)
    }
    g.rows.push(row)
  }

  for (const { tableId, rows: tableRows } of byTable.values()) {
    if (!tableRows.length) continue
    const fresh = filterNotYetAppended(tableRows)
    if (!fresh.length) continue

    let table: Awaited<ReturnType<typeof bitable.base.getTable>>
    try {
      table = await bitable.base.getTable(tableId)
    } catch {
      continue
    }

    try {
      await ensureStandardTextColumns(table)
    } catch {
      /* */
    }

    const ids = await resolveFieldIdMap(table)
    if (!ids.title && !ids.singleText && !ids.task) continue

    const BATCH = 80
    try {
      for (let i = 0; i < fresh.length; i += BATCH) {
        const sliceRows = fresh.slice(i, i + BATCH)
        const slice = sliceRows.map((row) => ({ fields: rowToFields(row, ids) }))
        await table.addRecords(slice as never)
        markAppended(sliceRows)
      }
    } catch {
      /* 写入失败时静默，不计入指纹以便重试 */
    }
  }
}

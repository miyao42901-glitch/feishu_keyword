/**
 * 任务表单配置本地快照（替代 `server/` 的 `feishu_task_configs`）。
 * 列表与状态以 8765 `GET /api/v1/async/tasks` 为准；扩展字段（关键词、写表 id 等）存 localStorage。
 */

const STORAGE_PREFIX = 'feishu_kw_task_cfg:'

/** 前端草稿 id（`Date.now()` 毫秒时间戳），8765 上无对应任务，禁止 `GET /async/tasks/{id}` */
export function isLocalDraftTaskId(taskId: number | string): boolean {
  const n = Math.floor(Number(taskId))
  if (!Number.isFinite(n) || n <= 0) return true
  return n >= 1_000_000_000_000
}

function storageKey(taskId: number): string {
  return `${STORAGE_PREFIX}${taskId}`
}

function cloneConfig(raw: Record<string, unknown>): Record<string, unknown> {
  return JSON.parse(JSON.stringify(raw)) as Record<string, unknown>
}

/** 读取本地配置快照；不存在返回 `null` */
export function loadLocalTaskConfig(taskId: number): Record<string, unknown> | null {
  try {
    const raw = localStorage.getItem(storageKey(taskId))
    if (!raw) return null
    const parsed = JSON.parse(raw) as unknown
    if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
      return parsed as Record<string, unknown>
    }
  } catch {
    /* */
  }
  return null
}

/** 全量写入本地配置 */
export function saveLocalTaskConfig(taskId: number, config: Record<string, unknown>): void {
  try {
    localStorage.setItem(storageKey(taskId), JSON.stringify(config))
  } catch {
    /* 存储满或隐私模式 */
  }
}

/** 合并补丁并写回；返回合并后的 config */
export function mergeLocalTaskConfig(
  taskId: number,
  patch: Record<string, unknown>,
): Record<string, unknown> {
  const base = loadLocalTaskConfig(taskId) ?? {}
  const next = { ...cloneConfig(base), ...patch }
  saveLocalTaskConfig(taskId, next)
  return next
}

export function removeLocalTaskConfig(taskId: number): void {
  try {
    localStorage.removeItem(storageKey(taskId))
  } catch {
    /* */
  }
}

/** 浏览器内所有本地草稿任务 id（未出现在 YDDM 列表的 `Date.now()` id） */
export function listLocalDraftTaskIds(): number[] {
  const ids: number[] = []
  try {
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i)
      if (!key?.startsWith(STORAGE_PREFIX)) continue
      const id = Math.floor(Number(key.slice(STORAGE_PREFIX.length)))
      if (!Number.isFinite(id) || id <= 0 || !isLocalDraftTaskId(id)) continue
      if (loadLocalTaskConfig(id)) ids.push(id)
    }
  } catch {
    /* */
  }
  ids.sort((a, b) => b - a)
  return ids
}

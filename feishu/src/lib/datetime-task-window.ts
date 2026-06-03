/**
 * 任务生效 / 过期时间：与 `DATETIME_FORMAT` 一致的字符串解析、
 * Element Plus `el-date-picker` 的禁用日期/时间、以及表单校验规则。
 *
 * 新建任务、重启时间弹框等共用，避免多处复制同一套边界逻辑。
 */
import dayjs from 'dayjs'
import type { Dayjs } from 'dayjs'
import type { FormItemRule } from 'element-plus'

/** 解析表单/接口中的日期时间字符串；非法或空串返回 null */
export function parseTaskDateTimeString(value: unknown): Dayjs | null {
  if (value == null) return null
  const s = String(value).trim()
  if (!s) return null
  const d = dayjs(s)
  return d.isValid() ? d : null
}

/** 采集窗口是否已结束（`expireAt` / `task_end_time`）；无结束时间则视为未过期 */
export function isTaskWindowExpired(expireAt: unknown, nowMs = Date.now()): boolean {
  const end = parseTaskDateTimeString(expireAt)
  if (!end) return false
  return nowMs >= end.valueOf()
}

/** 不可选今天之前的日期（与 `el-date-picker` `disabled-date` 签名一致） */
export function disabledPastDateForPicker(time: Date): boolean {
  return dayjs(time).startOf('day').isBefore(dayjs().startOf('day'))
}

export type DatePickerDisabledTime = {
  disabledHours: () => number[]
  disabledMinutes: (hour: number) => number[]
  disabledSeconds: (hour: number, minute: number) => number[]
}

function makeDisabledTimeFromBoundary(date: Date, boundary: Dayjs): DatePickerDisabledTime {
  const cur = dayjs(date)
  if (!cur.isSame(boundary, 'day')) {
    return {
      disabledHours: () => [],
      disabledMinutes: () => [],
      disabledSeconds: () => [],
    }
  }
  const b = boundary
  return {
    disabledHours: () => Array.from({ length: b.hour() }, (_, i) => i),
    disabledMinutes: (hour: number) =>
      hour < b.hour()
        ? Array.from({ length: 60 }, (_, i) => i)
        : hour === b.hour()
          ? Array.from({ length: b.minute() }, (_, i) => i)
          : [],
    disabledSeconds: (hour: number, minute: number) =>
      hour < b.hour() || (hour === b.hour() && minute < b.minute())
        ? Array.from({ length: 60 }, (_, i) => i)
        : hour === b.hour() && minute === b.minute()
          ? Array.from({ length: b.second() }, (_, i) => i)
          : [],
  }
}

/** 生效时间：选「今天」时不可选当前时刻之前 */
export function disabledTimeEffectiveDateTime(date: Date): DatePickerDisabledTime {
  const now = dayjs()
  if (!dayjs(date).isSame(now, 'day')) {
    return {
      disabledHours: () => [],
      disabledMinutes: () => [],
      disabledSeconds: () => [],
    }
  }
  return makeDisabledTimeFromBoundary(date, now)
}

/**
 * 过期时间：不得早于「当前」与「生效」中较晚者（同一天内按边界禁用时分秒）。
 */
export function disabledTimeExpireDateTime(date: Date, effectiveAtStr: string): DatePickerDisabledTime {
  const cur = dayjs(date)
  const now = dayjs()
  const eff = parseTaskDateTimeString(effectiveAtStr)
  const candidates: Dayjs[] = []
  if (cur.isSame(now, 'day')) candidates.push(now)
  if (eff && cur.isSame(eff, 'day')) candidates.push(eff)
  if (candidates.length === 0) {
    return {
      disabledHours: () => [],
      disabledMinutes: () => [],
      disabledSeconds: () => [],
    }
  }
  const boundary = candidates.reduce((a, c) => (a.isAfter(c) ? a : c))
  return makeDisabledTimeFromBoundary(date, boundary)
}

/** 开始时间：`el-form` 规则（必填 + 不早于当前） */
export function effectiveAtFormItemRules(): FormItemRule[] {
  return [
    { required: true, message: '请输入开始时间', trigger: 'change' },
    {
      validator: (_rule, value: string, callback) => {
        const d = parseTaskDateTimeString(value)
        if (!d) {
          callback(new Error('开始时间格式不正确'))
          return
        }
        if (d.valueOf() < Date.now()) {
          callback(new Error('开始时间不能早于当前时间'))
          return
        }
        callback()
      },
      trigger: ['change', 'blur'],
    },
  ]
}

/**
 * 结束时间：`el-form` 规则（必填 + 不早于当前 + 不早于开始时间）。
 * @param getEffectiveAt - 读取当前开始时间字符串（如 `() => form.effectiveAt`）
 */
/**
 * 定时任务各轮采集时刻（毫秒时间戳，与提交 YDDM 的 `task_start_time` / `interval_minutes` 对齐）。
 *
 * 规则：首轮在「开始时间」执行，之后每隔采集频率一轮；若结束时间未落在整点上，结束时刻再补一轮。
 *
 * 例：14:29 开始、14:41 结束、5 分钟 → 14:29、14:34、14:39、14:41，共 4 轮。
 */
export function listScheduledExecutionRunAtMs(
  effectiveAt: unknown,
  expireAt: unknown,
  intervalMinutes: unknown,
): number[] {
  const start = parseTaskDateTimeString(effectiveAt)
  const end = parseTaskDateTimeString(expireAt)
  if (!start || !end) return []

  const startMs = start.valueOf()
  const endMs = end.valueOf()
  if (endMs <= startMs) return []

  const interval =
    typeof intervalMinutes === 'number'
      ? intervalMinutes
      : Number(String(intervalMinutes ?? '').trim())
  const mins = Number.isFinite(interval) && interval > 0 ? Math.floor(interval) : 10
  const intervalMs = mins * 60_000

  const runAtMs: number[] = []
  let t = startMs
  while (t <= endMs) {
    runAtMs.push(t)
    t += intervalMs
  }
  if (runAtMs.length === 0 || runAtMs[runAtMs.length - 1]! < endMs) {
    runAtMs.push(endMs)
  }
  return runAtMs
}

/** 定时任务在监控窗口内的预计采集轮次 */
export function countScheduledExecutionRounds(
  effectiveAt: unknown,
  expireAt: unknown,
  intervalMinutes: unknown,
): number {
  const start = parseTaskDateTimeString(effectiveAt)
  const end = parseTaskDateTimeString(expireAt)
  if (!start || !end) return 1
  return listScheduledExecutionRunAtMs(effectiveAt, expireAt, intervalMinutes).length
}

/**
 * 距离下一次应按采集时刻表刷新接口的毫秒数。
 * - `0`：当前已跨过某一采集点且尚未为该点拉过 results
 * - `> 0`：等到 upcoming 采集时刻（如 14:34）
 * - `null`：窗口内计划轮次均已拉取过
 */
export function msUntilNextScheduledRunPoll(
  effectiveAt: unknown,
  expireAt: unknown,
  intervalMinutes: unknown,
  lastPolledRunAtMs: number | undefined,
  nowMs = Date.now(),
): number | null {
  const runs = listScheduledExecutionRunAtMs(effectiveAt, expireAt, intervalMinutes)
  if (!runs.length) return null

  const startMs = runs[0]!
  if (nowMs < startMs) return startMs - nowMs

  const last = lastPolledRunAtMs ?? 0
  for (const runAt of runs) {
    if (runAt > last) {
      if (runAt > nowMs) return runAt - nowMs
      return 0
    }
  }
  return null
}

/** 本轮刷新完成后，记录已覆盖到的最大采集时刻（用于下一轮对齐 14:29 / 14:34 …） */
export function scheduledRunPolledMarkThrough(
  effectiveAt: unknown,
  expireAt: unknown,
  intervalMinutes: unknown,
  nowMs = Date.now(),
): number {
  const runs = listScheduledExecutionRunAtMs(effectiveAt, expireAt, intervalMinutes)
  let mark = 0
  for (const runAt of runs) {
    if (runAt <= nowMs) mark = Math.max(mark, runAt)
  }
  return mark
}

export function isScheduledFeedPollDue(
  effectiveAt: unknown,
  expireAt: unknown,
  intervalMinutes: unknown,
  lastPolledRunAtMs: number | undefined,
  nowMs = Date.now(),
): boolean {
  return msUntilNextScheduledRunPoll(effectiveAt, expireAt, intervalMinutes, lastPolledRunAtMs, nowMs) === 0
}

export function expireAtFormItemRules(getEffectiveAt: () => string): FormItemRule[] {
  return [
    { required: true, message: '请输入结束时间', trigger: 'change' },
    {
      validator: (_rule, value: string, callback) => {
        const d = parseTaskDateTimeString(value)
        if (!d) {
          callback(new Error('结束时间格式不正确'))
          return
        }
        if (d.valueOf() < Date.now()) {
          callback(new Error('结束时间不能早于当前时间'))
          return
        }
        const eff = parseTaskDateTimeString(getEffectiveAt())
        if (eff && d.isBefore(eff)) {
          callback(new Error('结束时间不能早于开始时间'))
          return
        }
        callback()
      },
      trigger: ['change', 'blur'],
    },
  ]
}

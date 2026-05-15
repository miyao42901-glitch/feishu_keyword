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

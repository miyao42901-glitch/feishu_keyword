/** 监控关键词单条最大字符数（表单输入截断与提交校验一致） */
export const KEYWORD_MAX_LEN = 20

export const KEYWORD_TOO_LONG_HINT = '关键词不能过长'

/** 监控关键词最多条数 */
export const KEYWORD_MAX_COUNT = 20

export const KEYWORD_COUNT_EXCEEDED_HINT = '关键词数量不能超过20个'

export const KEYWORD_DUPLICATE_HINT = '该关键词已添加'

export const EXCLUDE_KEYWORD_CONFLICT_HINT = '排除词不能与关键词重复'

/** 去除首尾空白后截断至 `maxLen`，并标记是否发生过截断 */
export function truncateKeyword(
  raw: string,
  maxLen: number = KEYWORD_MAX_LEN,
): { value: string; truncated: boolean } {
  const trimmed = raw.trim()
  if (!trimmed) return { value: '', truncated: false }
  if (trimmed.length <= maxLen) return { value: trimmed, truncated: false }
  return { value: trimmed.slice(0, maxLen), truncated: true }
}

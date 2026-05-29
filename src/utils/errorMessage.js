const OPERATION_FAILED_PREFIX = '操作失败:'

/**
 * 将技术性错误信息转换为用户可读的中文说明
 * @param {string} raw
 * @returns {string}
 */
export function formatErrorDetail(raw) {
  if (!raw || typeof raw !== 'string') {
    return '未知错误'
  }

  const message = raw.trim()

  if (/Cannot read properties of undefined \(reading 'id'\)/i.test(message)) {
    return '表格缺少必要字段，请确认所选数据表的列名与插件模板一致（如「用户id」「视频id」等）'
  }

  if (/Cannot read properties of undefined \(reading 'text'\)/i.test(message)) {
    return '表格数据不完整，请检查所选记录是否已填写必要内容（如用户id、视频id）'
  }

  if (/Cannot read properties of null \(reading 'id'\)/i.test(message)) {
    return '表格缺少必要字段，请确认所选数据表的列名与插件模板一致'
  }

  if (/Cannot read properties of null \(reading 'text'\)/i.test(message)) {
    return '表格数据不完整，请检查所选记录是否已填写必要内容'
  }

  if (/Cannot read properties of undefined \(reading/i.test(message)) {
    return '表格字段或数据异常，请检查表结构及所选记录是否完整'
  }

  if (/Cannot read properties of null \(reading/i.test(message)) {
    return '表格字段或数据异常，请检查表结构及所选记录是否完整'
  }

  if (/All promises were rejected/i.test(message)) {
    return '操作已取消，请在弹窗中至少选择一条记录后再确认'
  }

  if (/Network Error|网络连接错误|Failed to fetch|timeout/i.test(message)) {
    return '网络连接异常，请检查网络后重试'
  }

  return message
}

/**
 * 格式化完整提示文案（含「操作失败:」前缀）
 * @param {string} message
 * @returns {string}
 */
export function formatFormMessage(message) {
  if (!message || typeof message !== 'string') {
    return message
  }

  if (message.startsWith(OPERATION_FAILED_PREFIX)) {
    const detail = message.slice(OPERATION_FAILED_PREFIX.length)
    return OPERATION_FAILED_PREFIX + formatErrorDetail(detail)
  }

  return formatErrorDetail(message)
}

/**
 * 从 Error 对象生成操作失败提示
 * @param {unknown} error
 * @returns {string}
 */
export function buildOperationFailedMessage(error) {
  const raw =
    (error && typeof error === 'object' && 'message' in error && error.message) ||
    (typeof error === 'string' ? error : '') ||
    '未知错误'
  return OPERATION_FAILED_PREFIX + formatErrorDetail(String(raw))
}

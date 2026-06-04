const OPERATION_FAILED_PREFIX = '操作失败:'

export const INSUFFICIENT_BALANCE_MESSAGE =
  '当前余额不足以完成本次采集，请充值后重试。'

export const NETWORK_ERROR_MESSAGE =
  '网络请求超时，请检查网络连接后重试。本次未扣余额'

export const OPERATION_ERROR_MESSAGE =
  '链接无效，请检查账号链接后重试。本次未扣余额。'

/**
 * 判断是否为余额不足类错误
 * @param {string} message
 * @returns {boolean}
 */
export function isInsufficientBalanceMessage(message) {
  if (!message || typeof message !== 'string') {
    return false
  }

  const text = message.replace(/^操作失败:/, '').trim()
  return /余额不足|余额不够|不足以完成(?:本次)?采集|余额.*不足|insufficient.*balance/i.test(
    text,
  )
}

/**
 * 判断是否为网络或其他可重试类错误
 * @param {string} message
 * @returns {boolean}
 */
export function isNetworkErrorMessage(message) {
  if (!message || typeof message !== 'string') {
    return false
  }

  if (isInsufficientBalanceMessage(message)) {
    return false
  }

  const text = message.replace(/^操作失败:/, '').trim()
  if (text === NETWORK_ERROR_MESSAGE) {
    return true
  }

  return /Network Error|网络连接错误|网络连接异常|网络请求超时|Failed to fetch|timeout|超时|ECONNABORTED|ERR_NETWORK|请求超时|网络异常/i.test(
    text,
  )
}

/**
 * 判断是否为操作问题类错误（如链接无效）
 * @param {string} message
 * @returns {boolean}
 */
export function isOperationErrorMessage(message) {
  if (!message || typeof message !== 'string') {
    return false
  }

  if (isInsufficientBalanceMessage(message) || isNetworkErrorMessage(message)) {
    return false
  }

  const text = message.replace(/^操作失败:/, '').trim()
  if (text === OPERATION_ERROR_MESSAGE) {
    return true
  }

  return /链接无效|视频号id不正确|用户id格式不正确|抖音用户id|sec_uid|secUid|v2_name|check v2_name|账号链接|invalid.*link|格式不正确.*(?:抖音|用户|账号)|没找到有关视频号|Error, please check v2_name/i.test(
    text,
  )
}

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

  if (/Network Error|网络连接错误|Failed to fetch|timeout|超时|网络请求超时|ECONNABORTED|ERR_NETWORK|请求超时/i.test(message)) {
    return NETWORK_ERROR_MESSAGE
  }

  if (/链接无效|视频号id不正确|用户id格式不正确|抖音用户id|sec_uid|v2_name|check v2_name|没找到有关视频号|Error, please check v2_name/i.test(message)) {
    return OPERATION_ERROR_MESSAGE
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

/**
 * 从新增账号成功文案中解析统计数据
 * @param {string} message
 * @returns {{ newAccounts: number|null, cost: number|null }|null}
 */
export function parseAddAccountStatsFromMessage(message) {
  if (!message || typeof message !== 'string') {
    return null
  }

  const text = message.replace(/\n/g, '')
  if (!/新增.+账号完成/.test(text)) {
    return null
  }

  const stats = {
    newAccounts: null,
    cost: null,
  }

  const successMatch = text.match(/成功(\d+)条/)
  if (successMatch) {
    stats.newAccounts = Number(successMatch[1])
  } else {
    stats.newAccounts = 1
  }

  const costMatch = text.match(/消耗[：:]\s*([\d.]+)/)
  if (costMatch) {
    stats.cost = Number(costMatch[1])
  }

  return stats.newAccounts != null || stats.cost != null ? stats : null
}

/**
 * 从更新作品成功文案中解析统计数据
 * @param {string} message
 * @returns {{ updatedWorks: number|null, cost: number|null }|null}
 */
export function parseUpdateWorksStatsFromMessage(message) {
  if (!message || typeof message !== 'string') {
    return null
  }

  const text = message.replace(/\n/g, '')
  if (/新增.+账号完成/.test(text)) {
    return null
  }
  if (text.includes('账号信息') || /更新用户|更新快手账号|更新用户信息/.test(text)) {
    return null
  }
  if (/获取(视频|笔记|文章)|共写入|成功操作\d+个账号/.test(text)) {
    return null
  }

  const isUpdateWorks =
    /更新(?:抖音视频|快手视频|视频号视频|小红书笔记|文章)完成/.test(text) ||
    /批量更新完成/.test(text)

  if (!isUpdateWorks) {
    return null
  }

  const stats = {
    updatedWorks: null,
    cost: null,
  }

  const successUpdateMatch = text.match(/成功更新(\d+)条/)
  const successMatch = text.match(/成功(\d+)条/)
  if (successUpdateMatch) {
    stats.updatedWorks = Number(successUpdateMatch[1])
  } else if (successMatch) {
    stats.updatedWorks = Number(successMatch[1])
  }

  const costMatch = text.match(/共消耗([\d.]+)元?|, 消耗([\d.]+)/)
  if (costMatch) {
    stats.cost = Number(costMatch[1] || costMatch[2])
  }

  return stats.updatedWorks != null || stats.cost != null ? stats : null
}

/**
 * 从更新账号数据成功文案中解析统计数据
 * @param {string} message
 * @returns {{ newAccounts: number|null, updatedAccounts: number|null, cost: number|null }|null}
 */
export function parseUpdateAccountStatsFromMessage(message) {
  if (!message || typeof message !== 'string') {
    return null
  }

  const text = message.replace(/\n/g, '')
  if (/新增.+账号完成/.test(text)) {
    return null
  }

  const isUpdateAccount =
    /更新(?:用户|快手账号)信息完成/.test(text) ||
    (/更新.+完成/.test(text) && text.includes('账号信息'))

  if (!isUpdateAccount) {
    return null
  }

  const stats = {
    newAccounts: 0,
    updatedAccounts: null,
    cost: null,
  }

  const newMatch = text.match(/新增(\d+)(?:个|条)/)
  if (newMatch) {
    stats.newAccounts = Number(newMatch[1])
  }

  const successMatch = text.match(/成功(\d+)条/)
  if (successMatch) {
    stats.updatedAccounts = Number(successMatch[1])
  }

  const costMatch = text.match(/消耗\s*([\d.]+)\s*元|消耗[：:]\s*([\d.]+)/)
  if (costMatch) {
    stats.cost = Number(costMatch[1] || costMatch[2])
  }

  return stats.updatedAccounts != null || stats.cost != null ? stats : null
}

/**
 * 从采集成功文案中解析统计数据
 * @param {string} message
 * @returns {{ successAccounts: number|null, workCount: number|null, cost: number|null }|null}
 */
export function parseCollectStatsFromMessage(message) {
  if (!message || typeof message !== 'string') {
    return null
  }

  const text = message.replace(/\n/g, '')
  if (/新增.+账号完成/.test(text)) {
    return null
  }
  if (parseUpdateWorksStatsFromMessage(message) || parseUpdateAccountStatsFromMessage(message)) {
    return null
  }

  const stats = {
    successAccounts: null,
    workCount: null,
    cost: null,
  }

  const accountOpMatch = text.match(/成功操作(\d+)个账号/)
  if (accountOpMatch) {
    stats.successAccounts = Number(accountOpMatch[1])
  }

  const bloggerDataMatch = text.match(/成功采集(\d+)条(?:博主)?数据/)
  if (bloggerDataMatch) {
    stats.successAccounts = Number(bloggerDataMatch[1])
  }

  const bloggerAttemptMatch = text.match(/尝试采集(\d+)位博主/)
  if (bloggerAttemptMatch && stats.successAccounts == null) {
    stats.successAccounts = Number(bloggerAttemptMatch[1])
  }

  const wxAccountMatch = text.match(/成功(\d+)条(?=.*(?:视频号|微信))/)
  if (wxAccountMatch && stats.successAccounts == null && text.includes('账号')) {
    stats.successAccounts = Number(wxAccountMatch[1])
  }

  const writeMatch = text.match(/共写入\s*(\d+)\s*条/)
  if (writeMatch) {
    stats.workCount = Number(writeMatch[1])
  }

  const postCollectMatch = text.match(/成功采集(\d+)条作品数据/)
  if (postCollectMatch) {
    stats.workCount = Number(postCollectMatch[1])
  }

  const wxAddMatch = text.match(/成功(\d+)条，消耗[：:]\s*([\d.]+)/)
  if (wxAddMatch) {
    if (stats.successAccounts == null) {
      stats.successAccounts = Number(wxAddMatch[1])
    }
    stats.cost = Number(wxAddMatch[2])
  }

  const costMatch = text.match(/共消耗\s*([\d.]+)|消耗[：:]\s*([\d.]+)|消耗\s*([\d.]+)\s*元/)
  if (costMatch && stats.cost == null) {
    stats.cost = Number(costMatch[1] || costMatch[2] || costMatch[3])
  }

  const hasStats =
    stats.successAccounts != null || stats.workCount != null || stats.cost != null
  return hasStats ? stats : null
}

export function formatCollectCount(value, unit) {
  if (value == null || Number.isNaN(value)) {
    return '-'
  }
  return `${value}${unit}`
}

export function formatCollectMoney(value) {
  if (value == null || value === '' || Number.isNaN(Number(value))) {
    return '-'
  }
  return `${Number(value).toFixed(2)}元`
}

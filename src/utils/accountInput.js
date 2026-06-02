/**
 * 单行采集账号是否已填写
 * @param {{ dataType?: string, data?: object }|null|undefined} item
 * @returns {boolean}
 */
export function isAccountRowFilled(item) {
  if (!item) {
    return false
  }
  if (item.dataType === 'input') {
    return !!item.data?.inputValue?.trim()
  }
  if (item.dataType === 'table') {
    return item.data?.recordIdList?.length > 0
  }
  return false
}

/**
 * 所有采集账号输入行均已填写时可采集
 * @param {Record<string, unknown>|object|null|undefined} searchValues
 * @returns {boolean}
 */
export function hasAllAccountInputs(searchValues) {
  const rows = Object.values(searchValues || {})
  if (rows.length === 0) {
    return false
  }
  return rows.every(isAccountRowFilled)
}

/**
 * 新增账号成功后：清空链接输入框，保留表格选择
 * @param {Record<string, { dataType?: string, data?: object }>} searchValues
 * @returns {Record<string, { dataType?: string, data?: object }>}
 */
export function clearInputAccountRowsAfterSuccess(searchValues) {
  const entries = Object.entries(searchValues || {})
  const result = {}

  for (const [key, item] of entries) {
    if (item?.dataType === 'table') {
      result[key] = item
    }
  }

  const hasTable = Object.keys(result).length > 0
  if (!hasTable) {
    return {
      0: {
        dataType: 'input',
        data: { inputValue: '' },
      },
    }
  }

  return result
}

/**
 * @param {{ value: Record<string, unknown> }} searchValuesRef
 */
export function resetAccountInputsAfterSuccess(searchValuesRef) {
  searchValuesRef.value = clearInputAccountRowsAfterSuccess(searchValuesRef.value)
}

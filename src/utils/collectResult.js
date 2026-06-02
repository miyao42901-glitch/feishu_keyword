/**
 * 记录采集成功后可跳转的数据表
 * @param {{ resultTableId?: string|null }} formData
 * @param {string|null|undefined} tableId
 */
export function setCollectResultTable(formData, tableId) {
  formData.resultTableId = tableId || null
}

/**
 * @param {{ userTableId?: string|null, workTableId?: string|null, selectedTableId?: string|null }} paneData
 * @param {'user'|'work'} target
 * @returns {string|null}
 */
export function getCollectResultTableId(paneData, target) {
  if (!paneData) {
    return null
  }
  if (target === 'user') {
    return paneData.userTableId || paneData.selectedTableId || null
  }
  if (target === 'work') {
    return paneData.workTableId || paneData.selectedTableId || null
  }
  return paneData.selectedTableId || paneData.workTableId || paneData.userTableId || null
}

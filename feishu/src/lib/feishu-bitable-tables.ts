/**
 * 当前多维表格（Base）内的数据表列表，供「使用现有表」等下拉使用。
 * 仅在飞书多维表格插件宿主环境内可用；本地页或异常时返回空数组。
 */
import { bitable } from '@lark-base-open/js-sdk'

export type BitableTableOption = {
  id: string
  name: string
}

/**
 * 拉取当前 base 下全部数据表（id + 名称）。
 * 使用各表的 `getName()`，与多维表格顶部标签页展示一致；`getTableMetaList()` 的 `name`
 * 在部分环境下会为默认「数据表」等，与界面不同步。
 */
export async function fetchBitableTableMetaList(): Promise<BitableTableOption[]> {
  const tables = await bitable.base.getTableList()
  const mapped = await Promise.all(
    tables.map(async (table) => {
      const meta = await table.getMeta()
      const displayName = (await table.getName()).trim()
      return {
        id: meta.id,
        name: displayName || meta.name.trim() || meta.id,
      }
    }),
  )
  mapped.sort((a, b) => a.name.localeCompare(b.name, 'zh-Hans-CN'))
  return mapped
}

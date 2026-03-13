import { bitable } from '@lark-base-open/js-sdk';

/**
 * 写入数据到表格
 * @param {string} tableId - 表格ID，如果是新建表格则为null
 * @param {Array} dataList - 数据列表
 * @param {Object} fieldsConfig - 字段配置
 * @param {boolean} isNewTable - 是否为新建表格
 * @param {string} tableName - 新建表格的名称
 * @returns {Promise<{success: boolean, data: {tableId: string, recordIds: Array<string>} | null, error: string | null}>} - 写入结果
 */
export const writeToTable = async (tableId, dataList, fieldsConfig, isNewTable = false, tableName = '新建表格') => {
  try {
    let targetTableId = tableId;
    
    // 如果是新建表格
    if (isNewTable) {
      // 创建新表格
      const newTable = await bitable.base.addTable(tableName);
      targetTableId = newTable.id;
      console.log('新建表格成功，表格ID:', targetTableId);
    }
    
    // 获取表格实例
    const table = await bitable.base.getTable(targetTableId);
    
    // 补全表格字段
    const fieldList = await table.getFieldList();
    const fieldMap = new Map();
    
    for (const field of fieldList) {
      const fieldName = await field.getName();
      fieldMap.set(fieldName, field.id);
    }
    
    // 添加缺失的字段
    for (const field of Object.values(fieldsConfig)) {
      if (!fieldMap.has(field.label)) {
        const newField = await table.addField({
          type: field.fieldType,
          name: field.label,
        });
        fieldMap.set(field.label, newField.id);
      }
    }
    
    // 分批处理数据，每次最多200条
    const batchSize = 200;
    const allRecordIds = [];
    
    for (let i = 0; i < dataList.length; i += batchSize) {
      const batchData = dataList.slice(i, i + batchSize);
      
      // 构建记录数据
      const records = batchData.map(item => {
        const fields = {};
        for (const [key, field] of Object.entries(fieldsConfig)) {
          const fieldId = fieldMap.get(field.label);
          if (fieldId && item[field.value] !== undefined && item[field.value] !== null) {
            fields[fieldId] = item[field.value];
            console.log(`Mapping field: ${field.label} (${fieldId}) with value: ${item[field.value]}`);
          }
        }
        return {
          fields: fields
        };
      });
      
      console.log('准备写入的记录:', records);
      
      // 写入数据
      const batchResult = await table.addRecords(records);
      allRecordIds.push(...batchResult);
      console.log(`批次 ${Math.floor(i / batchSize) + 1} 写入成功，新增记录数: ${batchResult.length}`);
    }
    
    console.log('全部数据写入成功，总记录数:', allRecordIds.length);
    return {
      success: true,
      data: {
        tableId: targetTableId,
        recordIds: allRecordIds
      },
      error: null
    };
  } catch (error) {
    console.error('写入表格失败:', error);
    return {
      success: false,
      data: null,
      error: error.message || '写入失败'
    };
  }
};

export default {
  writeToTable
};
import { bitable, FieldType, IOpenSegmentType } from '@lark-base-open/js-sdk';

/**
 * 写入数据到表格
 * @param {string} tableId - 表格ID，如果是新建表格则为null
 * @param {Array} dataList - 数据列表
 * @param {Object} fieldsConfig - 字段配置
 * @param {boolean} isNewTable - 是否为新建表格
 * @param {string} tableName - 新建表格的名称
 * @returns {Promise<{success: boolean, data: {tableId: string, recordIds: Array<string>} | null, error: string | null}>} - 写入结果
 */
export const writeToTable = async (tableId, dataList, fieldsConfig, isNewTable = false, tableName = null) => {
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
    
    let fieldList = await table.getFieldList();

    // 设置索引字段
    let primaryField = null;
    let primaryFieldConfig = null
    for (const field of fieldList) {
      const fieldMeta = await field.getMeta();
      if (fieldMeta.isPrimary) {
        primaryField = field;
        break;
      }
    }
    for (const fieldConfigValue of Object.values(fieldsConfig)){
      if (fieldConfigValue.isPrimary){
        primaryFieldConfig = fieldConfigValue;
        break;
      }
    }
    
    // 处理索引字段
    if (primaryField && primaryFieldConfig) {
      const primaryFieldName = await primaryField.getName();
      if (primaryFieldName !== primaryFieldConfig.label) {
        // 删除table中与primaryFieldConfig同名的字段（如果有）
        for (const field of fieldList) {
          const fieldName = await field.getName();
          if (fieldName === primaryFieldConfig.label) {
            await table.deleteField(field.id);
            console.log(`删除与索引字段配置同名的字段: ${fieldName}`);
            break;
          }
        }
        
      }
        // 使用setField方法覆盖table中的索引字段设置
        const fieldCell = buildFieldConfig(primaryFieldConfig);
        await table.setField(primaryField.id, fieldCell);
        console.log(`覆盖索引字段设置: ${primaryFieldName} -> ${primaryFieldConfig.label}`);
    }
    
    // 补全表格字段
    fieldList = await table.getFieldList();
    const fieldMap = {};
    
    for (const field of fieldList) {
      const fieldName = await field.getName();
      fieldMap[fieldName] = field;
    }

    // 添加缺失的字段
    for (const fieldConfigValue of Object.values(fieldsConfig)) {
      if (!fieldMap[fieldConfigValue.label]) {
        const fieldCell = buildFieldConfig(fieldConfigValue);
        const newFieldId = await table.addField(fieldCell);
        fieldMap[fieldConfigValue.label] = await table.getField(newFieldId);
      }
    }
    
    // 分批处理数据，每次最多200条
    const batchSize = 200;
    const allRecordIds = [];
    
    for (let i = 0; i < dataList.length; i += batchSize) {
      const batchData = dataList.slice(i, i + batchSize);
      
      // 构建记录数据
      const records = await Promise.all(batchData.map(async item => {
        const fields = {};
        for (const [fieldConfigKey, fieldConfigValue] of Object.entries(fieldsConfig)) {
          const fieldId = fieldMap[fieldConfigValue.label].id;
          if (fieldId) {
            fields[fieldId] = await getCellValue(item[fieldConfigKey], fieldMap[fieldConfigValue.label], fieldConfigValue);
          }
        }
        return {
          fields: fields
        };
      }));
      
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

// 构建字段配置对象
const buildFieldConfig = (fieldConfigValue) => {
  const fieldCell = {
    type: fieldConfigValue.fieldType,
    name: fieldConfigValue.label,
  };
  
  // 如果是单选字段且有选项配置，添加选项
  if (fieldConfigValue.fieldType === FieldType.SingleSelect && fieldConfigValue.options && Object.keys(fieldConfigValue.options).length > 0) {
    fieldCell.property = { options: Object.values(fieldConfigValue.options).map(name => ({ name })) };
  }
  
  return fieldCell;
};

const getCellValue = async (value, field, fieldConfigValue) => {
  const fieldType = await field.getType();
  if (fieldType !== fieldConfigValue.fieldType) {
    return value
  }
  switch (fieldType) {
    case FieldType.SingleSelect:{
      const options = await field.getOptions();
      const option = options.find(opt => opt.name == fieldConfigValue.options[value]);
      return {id: option.id};
    }
    case FieldType.DateTime:
      return value * 1000;
    case FieldType.Url:
      return {
        type: IOpenSegmentType.Url,
        text: value
      };
    default:
      return value;
  }
}

export default {
  writeToTable
};
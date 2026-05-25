import { bitable, FieldType, IOpenSegmentType, FilterOperator, FilterConjunction } from '@lark-base-open/js-sdk';

// 错误消息
const ERROR_MESSAGES = {
  writeFailed: '写入失败',
  updateFailed: '更新失败'
}

/**
 * 写入数据到表格
 * @param {string} tableId - 表格ID，如果是新建表格则为null
 * @param {Array} dataList - 数据列表
 * @param {Object} fieldsConfig - 字段配置
 * @param {string} tableName - 新建表格的名称
 * @returns {Promise<{success: boolean, data: {tableId: string, recordIds: Array<string>} | null, error: string | null}>} - 写入结果
 */
export const writeToTable = async (tableId, dataList, fieldsConfig, tableName = null) => {
  try {
    let targetTableId = tableId;
    
    // 如果是新建表格
    if (tableId === null) {
      // 创建新表格
      const newTable = await bitable.base.addTable({name: tableName});
      targetTableId = newTable.tableId;
      console.log('新建表格成功，表格ID:', targetTableId);
    }
    
    // 获取表格实例
    const table = await bitable.base.getTable(targetTableId);

    let fieldList = await table.getFieldList();

    // 新建表格需要设置索引字段    
    if (tableId === null){
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
          if (fieldId && item[fieldConfigKey] !== undefined) {
            fields[fieldId] = await getCellValue(item[fieldConfigKey], fieldMap[fieldConfigValue.label], fieldConfigValue);
          }
        }
        return {
          fields: fields
        };
      }));
      
      // console.log('准备写入的记录:', records);
      
      // 写入数据
      const batchResult = await table.addRecords(records);
      allRecordIds.push(...batchResult);
      // console.log(`批次 ${Math.floor(i / batchSize) + 1} 写入成功，新增记录数: ${batchResult.length}`);
    }
    
    // console.log('全部数据写入成功，总记录数:', allRecordIds.length);
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
      error: error.message || ERROR_MESSAGES.writeFailed
    };
  }
};

// 构建字段配置对象
export const buildFieldConfig = (fieldConfigValue) => {
  const fieldCell = {
    type: fieldConfigValue.fieldType ? fieldConfigValue.fieldType : FieldType.Text,
    name: fieldConfigValue.label,
  };
  
  switch (fieldConfigValue.fieldType) {
    case FieldType.SingleSelect: {
      if (fieldConfigValue.options && Object.keys(fieldConfigValue.options).length > 0) {
        fieldCell.property = { options: Object.values(fieldConfigValue.options).map(name => ({ name })) };
      }
      break;
    }
    case FieldType.SingleLink: {
      fieldCell.property = fieldConfigValue.property
      break;
    }
    case FieldType.DateTime: {
      fieldCell.property = fieldConfigValue.property
      break;
    }
    case FieldType.Number: {
      fieldCell.property = fieldConfigValue.property
      break;
    }

  }

  return fieldCell;
};

export const getCellValue = async (value, field, fieldConfigValue) => {
  const fieldType = await field.getType();

  if (fieldType !== fieldConfigValue.fieldType) {
    return value
  }

  switch (fieldType) {
    case FieldType.SingleSelect:{
      const options = await field.getOptions();
      const option = options.find(opt => opt.name == fieldConfigValue.options[value]);
      if (!option) {
        return value;
      }
      return {id: option.id};
    }
    case FieldType.Url:
      return {
        type: IOpenSegmentType.Url,
        text: value
      };
    case FieldType.SingleLink:
      return {
        record_ids: value
      };
    default:
      return value;
  }
}

/**
 * 更新表格数据
 * @param {string} tableId - 表格ID
 * @param {Array} dataList - 数据列表，每个元素应包含 recordId 和要更新的字段数据
 * @param {Object} fieldsConfig - 字段配置
 * @returns {Promise<{success: boolean, data: {recordIds: Array<string>} | null, error: string | null}>} - 更新结果
 */
export const updateTable = async (tableId, dataList, fieldsConfig) => {
  try {
    // 获取表格实例
    const table = await bitable.base.getTable(tableId);
    
    // 获取字段列表
    const fieldList = await table.getFieldList();
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

    // 筛选出字段配置中和表格字段均包含的字段
    const commonFields = {};
    for (const [fieldConfigKey, fieldConfigValue] of Object.entries(fieldsConfig)) {
      if (fieldMap[fieldConfigValue.label]) {
        commonFields[fieldConfigKey] = fieldConfigValue;
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
        for (const [fieldConfigKey, fieldConfigValue] of Object.entries(commonFields)) {
          const fieldId = fieldMap[fieldConfigValue.label].id;
          if (fieldId && item.data[fieldConfigKey] !== undefined) {
            fields[fieldId] = await getCellValue(item.data[fieldConfigKey], fieldMap[fieldConfigValue.label], fieldConfigValue);
          }
        }
        return {
          recordId: item.recordId,
          fields: fields
        };
      }));
      
      // console.log('准备更新的记录:', records);
      
      // 更新数据
      await table.setRecords(records);
      allRecordIds.push(...records.map(record => record.recordId));
      // console.log(`批次 ${Math.floor(i / batchSize) + 1} 更新成功，更新记录数: ${records.length}`);
    }
    
    // console.log('全部数据更新成功，总记录数:', allRecordIds.length);
    return {
      success: true,
      data: {
        recordIds: allRecordIds
      },
      error: null
    };
  } catch (error) {
    console.error('更新表格失败:', error);
    return {
      success: false,
      data: null,
      error: error.message || ERROR_MESSAGES.updateFailed
    };
  }
};

/**
 * 获取视频表中指定用户记录的最大create_time
 * @param {string} videoTableId - 视频表格ID
 * @param {string} userRecordId - 用户记录ID
 * @param {Object} fieldsConfig - 字段配置，包含dy_link和create_time字段
 * @param {string} linkField - dy_link字段名称
 * @param {string} timeField - create_time字段名称
 * @param {number} minTime - 最小时间戳，当没有找到记录时使用
 * @returns {Promise<number>} - 最大的create_time时间戳
 */
export const getMaxCreateTimeByUser = async (videoTableId, userRecordId, fieldsConfig, linkField, timeField, minTime) => {
  try {
    // 获取视频表格实例
    const videoTable = await bitable.base.getTable(videoTableId);
    
    // 获取字段列表并构建字段映射
    const fieldList = await videoTable.getFieldList();
    const fieldMap = {};
    for (const field of fieldList) {
      const fieldName = await field.getName();
      fieldMap[fieldName] = field;
    }
    
    // 获取字段ID
    const linkFieldId = fieldMap[fieldsConfig[linkField].label].id;
    const timeFieldId = fieldMap[fieldsConfig[timeField].label].id;
    // console.log(linkFieldId, timeFieldId)
    
    // 使用filter和sort参数直接获取最大的createTime记录
    const records = await videoTable.getRecordsByPage({
      pageSize: 1,
      filter: {
        conditions: [
          {
            fieldId: linkFieldId,
            operator: FilterOperator.Is,
            value: [userRecordId]
          }
        ],
        conjunction: FilterConjunction.And,
      },
      sort: [
        {
          fieldId: timeFieldId,
          desc: true
        }
      ]
    });
    
    // 获取最大的createTime
    // console.log(records)
    
    let maxCreateTime = minTime;
    if (records.records && records.records.length > 0) {
      const createTime = records.records[0].fields[timeFieldId];
      if (createTime) {
        maxCreateTime = Math.max(maxCreateTime, createTime);
      }
    }
    // console.log(maxCreateTime)
    
    return maxCreateTime;
  } catch (error) {
    console.error('获取最大create_time失败:', error);
    return minTime;
  }
};

/**
 * @param {string} tableId - 表格ID
 * @param {string} fieldName - 字段名称
 * @param {object} fieldValue - 字段值
 */
export const getFirstRecordByField = async (tableId, fieldName, fieldValue) => {
  try {
    // 获取表格实例
    const table = await bitable.base.getTable(tableId);
    
    // 获取字段id
    const fieldList = await table.getFieldList();
    const fieldMap = {};
    
    for (const field of fieldList) {
      const fieldName = await field.getName();
      fieldMap[fieldName] = field;
    }
    
    const fieldId = fieldMap[fieldName].id;
    if (!fieldId) {
      console.error('字段不存在:', fieldName);
      return [null, null];
    }
    
    // 使用filter参数直接获取第一个记录
    const records = await table.getRecordsByPage({
      pageSize: 1,
      filter: {
        conditions: [
          {
            fieldId: fieldId,
            operator: FilterOperator.Is,
            value: fieldValue
          }
        ],
        conjunction: FilterConjunction.And,
      }
    });

    if (records.records && records.records.length > 0) {
      if (records.records[0]) {
        return [records.records[0], fieldMap];
      }
    }
    else {
      return [null, null];
    }

  } catch (error) {
    console.error('获取record失败:', error);
    return [null, null];
  }
};

export default {
  writeToTable,
  updateTable,
  buildFieldConfig,
  getCellValue,
  getMaxCreateTimeByUser,
  getFirstRecordByField,
};
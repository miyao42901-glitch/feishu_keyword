<script>
  import { ref, watch } from 'vue';
  import { bitable } from '@lark-base-open/js-sdk';
  import { CircleClose } from '@element-plus/icons-vue';

  export default {
    components: {
      CircleClose
    },
    props: {
      modelValue: {
        type: Object,
        default: () => ({dataType: 'input', data: {inputValue: ''}})
      },
      placeholder: {
        type: String,
        default: '请选择数据表或手动输入'
      }
    },
    emits: ['update:modelValue'],
    setup(props, { emit }) {
      const tableDataList = ref([]);
      const selectedTableId = ref('');
      const inputValue = ref('');
      const isReadOnly = ref(false);

      // 读取数据表列表
      const loadTableList = async () => {
        try {
          const tableList = await bitable.base.getTableList();
          tableDataList.value = [];
          for(const table of tableList) {
            const tableName = await table.getName();
            tableDataList.value.push({tableId: table.id, tableName: tableName});
          }
        } catch (error) {
          console.error('读取表格列表失败:', error);
        }
      };

      const querySearch = async (queryString, callback) => {
        callback(tableDataList.value);
      };

      const handleSelect = async (item, event) => {
        selectedTableId.value = item.tableId;
        const recordIdList = await bitable.ui.selectRecordIdList(item.tableId);
        if (recordIdList.length > 0) {
          isReadOnly.value = true;
          // 手动控制输入框的值
          inputValue.value = '已选' + recordIdList.length + '条记录，选自“' + item.tableName + '”';
          emit('update:modelValue', {dataType: 'table', data:{tableId: item.tableId, recordIdList: recordIdList}});
        }
      }

      const clearSelected = () => {
        selectedTableId.value = '';
        isReadOnly.value = false;
        inputValue.value = '';
      }

      watch(() => inputValue.value, (newVal) => {
        if (!isReadOnly.value) {
          let result = ''
          if(newVal) {
            result = newVal;
          }
          emit('update:modelValue', {dataType: 'input', data: {inputValue: result}});
        }
      });


      return {
        tableDataList,
        inputValue,
        selectedTableId,
        isReadOnly,
        loadTableList,
        querySearch,
        handleSelect,
        clearSelected,
      };
    },
  };
</script>

<template>
  <div class="general-select">
    <el-autocomplete
      v-model="inputValue"
      :fetch-suggestions="querySearch"
      @focus="loadTableList"
      @select="handleSelect"
      :placeholder="placeholder"
      :readonly="isReadOnly"
    >
    <template #suffix>
      <el-icon 
        v-if="inputValue" 
        style="cursor: pointer;"
        @click.stop="clearSelected"
      >
        <CircleClose />
      </el-icon>
    </template>
    <template #default="{ item }">
      <div class="name">{{ item.tableName }}</div>
    </template>
    </el-autocomplete>
  </div>
</template>

<style scoped>
  .general-select {
    width: 100%;
  }
</style>
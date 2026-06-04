<script>
  import { ref, watch } from 'vue';
  import { bitable } from '@lark-base-open/js-sdk';
  import { CircleClose, ArrowDown } from '@element-plus/icons-vue';

  export default {
    components: {
      CircleClose,
      ArrowDown
    },
    props: {
      modelValue: {
        type: Object,
        default: () => ({dataType: 'input', data: {inputValue: ''}})
      },
      placeholder: {
        type: String,
        default: '请选择数据表或手动输入'
      },
      maxlength: {
        type: Number,
        default: undefined
      },
      disabledTableIds: {
        type: Array,
        default: () => []
      }
    },
    emits: ['update:modelValue'],
    setup(props, { emit }) {
      const tableDataList = ref([]);
      const selectedTableId = ref('');
      const inputValue = ref('');
      const isReadOnly = ref(false);

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

      const handleSelect = async (item) => {
        if (props.disabledTableIds.includes(item.tableId)) return;
        selectedTableId.value = item.tableId;
        const recordIdList = await bitable.ui.selectRecordIdList(item.tableId);
        if (recordIdList.length > 0) {
          isReadOnly.value = true;
          inputValue.value = '已选' + recordIdList.length + '条记录，选自"' + item.tableName + '"';
          emit('update:modelValue', {dataType: 'table', data:{tableId: item.tableId, recordIdList: recordIdList}});
        }
      }

      const clearSelected = () => {
        selectedTableId.value = '';
        isReadOnly.value = false;
        inputValue.value = '';
        emit('update:modelValue', {dataType: 'input', data: {inputValue: ''}});
      }

      watch(() => inputValue.value, (newVal) => {
        if (!isReadOnly.value) {
          emit('update:modelValue', {dataType: 'input', data: {inputValue: newVal || ''}});
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
      :maxlength="maxlength"
    >
      <template #suffix>
        <el-icon
          v-if="inputValue"
          style="cursor: pointer;"
          @click.stop="clearSelected"
        >
          <CircleClose />
        </el-icon>
        <el-icon v-else>
          <ArrowDown />
        </el-icon>
      </template>
      <template #default="{ item }">
        <div
          class="name"
          :class="{ 'is-disabled': disabledTableIds.includes(item.tableId) }"
        >{{ item.tableName }}<span v-if="disabledTableIds.includes(item.tableId)" class="disabled-tag">已选</span></div>
      </template>
    </el-autocomplete>
  </div>
</template>

<style scoped>
  .general-select {
    width: 100%;
  }

  .name.is-disabled {
    color: #c0c4cc;
    cursor: not-allowed;
  }

  .disabled-tag {
    margin-left: 6px;
    font-size: 11px;
    color: #c0c4cc;
    background: #f4f4f5;
    border-radius: 3px;
    padding: 0 4px;
  }
</style>

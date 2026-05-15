<script>
  import { ref, watch } from 'vue';
  import { bitable } from '@lark-base-open/js-sdk';
  import { useI18n } from 'vue-i18n';
  import {
    ElSelect,
    ElOption,
  } from 'element-plus';

  export default {
    components: {
      ElSelect,
      ElOption,
    },
    props: {
      modelValue: {
        type: String,
        default: null
      },
      placeholder: {
        type: String,
        default: '请选择数据表'
      }
    },
    emits: ['update:modelValue', 'change'],
    setup(props, { emit }) {
      const tableDataList = ref([]);
      const isLoading = ref(false);
      const selectedTableId = ref(props.modelValue);

      // 同步本地数据到父组件
      const syncData = () => {
        emit('update:modelValue', selectedTableId.value);
      };

      // 监听本地数据变化
      watch(selectedTableId, async (newValue) => {
        syncData();
        emit('change', newValue);
      });

      // 监听父组件数据变化
      watch(() => props.modelValue, async (newValue) => {
        await loadTableList();
        selectedTableId.value = newValue;
      });

      // 读取数据表列表
      const loadTableList = async () => {
        isLoading.value = true;
        try {
          const tableList = await bitable.base.getTableList();
          tableDataList.value = [];
          for(const table of tableList) {
            const tableName = await table.getName();
            tableDataList.value.push({tableId: table.id, tableName: tableName});
          }
        } catch (error) {
          console.error('读取表格列表失败:', error);
        } finally {
          isLoading.value = false;
        }
      };

      return {
        selectedTableId,
        tableDataList,
        isLoading,
        loadTableList,
      };
    },
  };
</script>

<template>
  <div class="table-select">
    <el-select
      v-model="selectedTableId"
      :placeholder="placeholder"
      style="width: 100%;"
      @visible-change="loadTableList"
      :loading="isLoading"
      clearable
    >
      <el-option
        v-for="item in tableDataList"
        :key="item.tableId"
        :label="item.tableName"
        :value="item.tableId"
      >
      </el-option>
    </el-select>
  </div>
</template>

<style scoped>
  .table-select {
    width: 100%;
  }
</style>
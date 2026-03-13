<script>
  import { bitable, FieldType } from '@lark-base-open/js-sdk';
  import { ref, onMounted, computed, watch } from 'vue';
  import {
    ElButton,
    ElForm,
    ElFormItem,
    ElSelect,
    ElOption,
    ElAlert,
    ElCheckboxGroup,
    ElCheckbox,
    ElInput,
    ElRadio,
    ElRadioGroup,
    ElLink,
    ElRow,
    ElCol,
    ElText,
    ElCard,
    ElTabs,
    ElTabPane,
  } from 'element-plus';
  import pluginAPI from '@/utils/request'
  import GhForm from './ghForm.vue'

  export default {
    components: {
      ElButton,
      ElForm,
      ElFormItem,
      ElSelect,
      ElOption,
      ElAlert,
      ElCheckboxGroup,
      ElCheckbox,
      ElInput,
      ElRadio,
      ElRadioGroup,
      ElLink,
      ElRow,
      ElCol,
      ElText,
      ElCard,
      ElTabs,
      ElTabPane,
      GhForm,
    },
    setup() {
      const tableSelectOptions = [
        {newTable: true, label: '新建表格'},
        {newTable: false, label: '使用现有表格'}
      ]
      const formRef = ref(null)
      const formData = ref({
        newTable: true,
        newTableName: null,
        key: '',
        selectedTableId: null,
       });
      const tableDataList = ref([])

      const ghTableFields = {
        appmsgid: {value: 'appmsgid', label: '文章ID', fieldType: FieldType.Number},
        url: {value: 'url', label: '文章链接', fieldType: FieldType.Url},
        post_time: {value: 'post_time', label: '发文时间', fieldType: FieldType.DateTime},
        title: {value: 'title', label: '文章标题', fieldType: FieldType.Text},
        digest: {value: 'digest', label: '文章摘要', fieldType: FieldType.Text},
      }

      // const fetchUrlFields = async() => {
      //   const table = await bitable.base.getTableById(formData.value.tableId)
      //   const fieldList = await table.getFieldList();
      //   tableUrlFields.value = []
      //   for (const field of fieldList) {
      //     const fieldType = await field.getType();
      //     if(fieldType === FieldType.Url){
      //       const fieldName = await field.getName();
      //       tableUrlFields.value.push({
      //           fieldId: field.id,
      //           fieldName: fieldName,
      //           fieldType: fieldType,
      //       })
      //     }
      //   }
      // }

      // const collectData = async() => {
      //   removeListeners()
      //   const table = await bitable.base.getTableById(formData.value.tableId)

      //   const fieldList = await table.getFieldList();
      //   const fieldNameList = []
      //   for (const field of fieldList) {
      //     const fieldName = await field.getName();
      //     fieldNameList.push(fieldName)
      //   }
      //   for (const option of vedioDataOptions.value){
      //     if(formData.value.selectedOptions.includes(option.value)){
      //       if(!fieldNameList.includes(option.label)){
      //         await table.addField({
      //           type: option.fieldType,
      //           name: option.label,
      //         })
      //       }
      //     }
      //   }

        // const res = await pluginAPI.post('/fbmain/monitor/v3/bilibili_search', {
        //   key: "JZL6f0685390502a6b9",
        //   keyword: "特斯拉",
        //   search_type: "VIDEO",
        //   order_type: "TOTALRANK",
        //   order_sort: "0",
        //   page: "1"
        // })

      //   await setupFieldListeners();
      // }

      onMounted(async () => {
        // const selection = await bitable.base.getSelection();
        // formData.value.tableId = selection.tableId;
        // formData.value.viewId = selection.viewId;
      });

      watch(() => formData.value.newTable, async(newValue, oldValue) => {
        if (newValue === false) {
          tableDataList.value = []
          formData.value.selectedTableId = null
          const tableList = await bitable.base.getTableList();
          for(const table of tableList){
            const tableName = await table.getName()
            tableDataList.value.push({tableId: table.id, tableName: tableName})
          }
        }
        if (newValue === true) {
          formData.value.newTableName = null
        }
      })

      const testClick = async() => {
        const response = await pluginAPI.post('/fbmain/monitor/v3/bilibili_search', {
          key: "JZL6f0685390502a6b9",
          keyword: "特斯拉",
          search_type: "VIDEO",
          order_type: "TOTALRANK",
          order_sort: "0",
          page: "1"
        })
        // const table = await bitable.base.getTableById(formData.value.tableId)
        // if (formData.value.collectType === 'total'){
        //   const res = await table.getRecordIdListByPage({viewId: formData.value.viewId})
        //   console.log(res)
        // }
        // else if (formData.value.collectType === 'pick'){
        //   console.log(formData.value.tableId, formData.value.viewId)
        //   const res = await bitable.ui.selectRecordIdList(formData.value.tableId, formData.value.viewId)
        //   console.log(res)
        // }
      }

      return {
        formRef,
        formData,
        tableSelectOptions,
        tableDataList,
        testClick,
        ghTableFields,
      };
      
    },
  };
</script>

<template>
  <el-form ref="formRef" class="form" :model="formData" >
    <div class="title-section">多平台数据采集插件</div>

    <el-card class="card-item" shadow="hover">
      <el-form-item 
        label="API Key"
        label-position="left"
      >
        <el-input
          v-model="formData.key"
          type="password"
          placeholder="请输入API Key"
          show-password
          clearable
          style="flex: 1;"
        />
        <el-link 
          href="https://www.dajiala.com/main/interface" 
          target="_blank"
          :underline="false" 
          type="primary"
          style="padding-left: 16px;">获取key
        </el-link>
      </el-form-item>
    </el-card>

    <el-card class="card-item" shadow="hover">
      <el-form-item 
        label="表格选择"
        label-position="top"
      >
        <el-radio-group v-model="formData.newTable">
          <el-radio 
            v-for="item in tableSelectOptions" 
            :key="item.newTable"
            :label="item.newTable"
          >
            {{ item.label }}
          </el-radio>
        </el-radio-group>
      </el-form-item>
      
      <el-form-item 
        label="数据表名"
        label-position="left"
      >
        <el-select
          v-model="formData.selectedTableId"
          placeholder="请选择表格"
          v-if="!formData.newTable"
        >
          <el-option
            v-for="item in tableDataList"
            :key="item.tableId"
            :label="item.tableName"
            :value="item.tableId"
          >
          </el-option>
        </el-select>
        <el-input
          v-if="formData.newTable"
          v-model="formData.newTableName"
          placeholder="请输入数据表名"
        />
      </el-form-item>
    </el-card>
    
    <el-card class="card-item" shadow="hover">
      <el-tabs >
        <el-tab-pane label="公众号" name="0">
          <GhForm :disabled="!formData.newTable && !formData.selectedTableId" :form-data="formData" />
        </el-tab-pane>
        <el-tab-pane label="平台2" name="1">
          测试
        </el-tab-pane>
        <el-tab-pane label="平台3" name="2">
          测试
        </el-tab-pane>
      </el-tabs>
    </el-card>
    
    <p>{{ formData }}</p>
    <p>{{ tableDataList }}</p>
  </el-form>
</template>

<style scoped>
  .form :deep(.el-form-item__label) {
    font-size: 16px;
    color: var(--el-text-color-primary);
  }
  .form :deep(.el-form-item__content), .form :deep(.el-link), .form :deep(.el-button) {
    font-size: 16px;
  }
  .form :deep(.el-form-item:last-child) {
    margin-bottom: 0;
  }
  .title-section {
    font-size: 20px;
    width: 100%;
    padding-left: 10px;
    border-left: 5px solid rgb(37, 152, 248);
    padding-bottom: 10px;
    margin-bottom: 10px;
    padding-top: 10px;
  }
  .card-item {
    margin: 10px 0px 10px 0px;
  }
</style>

<script>
  import { bitable, FieldType } from '@lark-base-open/js-sdk';
  import { ref, onMounted, computed, watch } from 'vue';
  import {
    ElButton,
    ElForm,
    ElFormItem,
    ElAlert,
    ElCheckboxGroup,
    ElCheckbox,
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
      ElAlert,
      ElCheckboxGroup,
      ElCheckbox,
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
      const formRef = ref(null)
      const formData = ref({
        key: null,
       });

      return {
        formRef,
        formData,
      };
    },
  };
</script>

<template>
  <el-form ref="formRef" class="form" :model="formData" label-position="left">
    <div class="title-section">多平台数据采集插件</div>

    <el-card class="card-item" shadow="hover">
      <el-form-item 
        label="API Key"
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
      <el-tabs >
        <el-tab-pane label="公众号" name="0">
          <GhForm :form-data="formData" />
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

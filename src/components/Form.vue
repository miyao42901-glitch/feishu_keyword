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

      const isLocked = ref(false);

      return {
        formRef,
        formData,
        isLocked,
      };
    },
  };
</script>

<template>
  <div class="form-container">
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
            :disabled="isLocked"
          />
          <el-link 
            href="https://www.dajiala.com/main/interface" 
            target="_blank"
            :underline="false" 
            type="primary"
            style="padding-left: 16px;"
            :disabled="isLocked"
          >获取key
          </el-link>
        </el-form-item>
      </el-card>
      
      <el-card class="card-item" shadow="hover">
        <el-tabs :disabled="isLocked">
          <el-tab-pane label="公众号" name="0">
            <GhForm :form-data="formData" :is-locked="isLocked" @update:is-locked="isLocked = $event" />
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
      <p>{{ isLocked }}</p>
    </el-form>
    
    <!-- 加载遮罩 -->
    <div class="loading-overlay" v-if="isLocked">
      <div class="loading-content">
        <div class="loading-spinner"></div>
        <p>操作进行中，请稍候...</p>
      </div>
    </div>
  </div>
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
  
  /* 加载遮罩样式 */
  .form-container {
    position: relative;
    min-height: 400px;
  }
  
  .loading-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(255, 255, 255, 0.8);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
    backdrop-filter: blur(2px);
  }
  
  .loading-content {
    text-align: center;
    padding: 30px;
    background-color: white;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }
  
  .loading-spinner {
    width: 40px;
    height: 40px;
    border: 4px solid #f3f3f3;
    border-top: 4px solid #3498db;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 16px;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  
  .loading-content p {
    margin: 0;
    font-size: 16px;
    color: #606266;
  }
</style>

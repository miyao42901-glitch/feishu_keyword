<script>
  import { bitable, bridge, FieldType } from '@lark-base-open/js-sdk';
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
    ElMessageBox,
  } from 'element-plus';
  import pluginAPI from '@/utils/request'
  import GhForm from './ghForm.vue'
  import DyForm from './dyForm.vue'
  // import XhsForm from './xhsForm.vue'
  import V2Form from './v2Form.vue'
  import axios from 'axios'

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
      ElMessageBox,
      GhForm,
      DyForm,
      // XhsForm,
      V2Form,
    },
    setup() {
      const formRef = ref(null)
      const formData = ref({
        isLogin: false,
        key: null,
        message: null,
        messageType: 'success',
        remainMoney: null,
        username: null,
      });

      const isLocked = ref(false);

      watch(isLocked, (newVal, oldVal) => {
        if (oldVal === true && newVal === false) {
          if (formData.value.message) {
            console.log(formData.value.message);
            ElMessageBox.confirm(formData.value.message, '提示',{type: formData.value.messageType})
            // 清空提示信息
            formData.value.message = null;
            formData.value.messageType = 'success';
          }
        }
      });

      // 生成指定长度的随机字符串（使用 crypto API，更安全）
      function randomString(length) {
        const array = new Uint8Array(Math.ceil(length / 2));
        window.crypto.getRandomValues(array);
        return Array.from(array, byte => 
          ('0' + (byte & 0xFF).toString(16)).slice(-2)
        ).join('').substring(0, length);
      }

      onMounted(async () => {
        isLocked.value = true;
        try{
          if (localStorage.getItem('isLogin') === 'true') {
            formData.value.isLogin = true;
            formData.value.username = localStorage.getItem('username');
            formData.value.key = localStorage.getItem('key');
            const res = await pluginAPI.get('/fbmain/monitor/v3/get_remain_money', {
              params: {
                key: formData.value.key,
              }
            });
            if (res && res.data && res.data.code === 0) {
              formData.value.remainMoney = res.data.remain_money;
            }
            else {
              formData.value.message = '获取余额失败，请联系管理员';
              formData.value.messageType = 'error';
            }
          }
          // 提取 URL 中的 code 参数
          const urlParams = new URLSearchParams(window.location.search);
          const code = urlParams.get('code');
          const state = urlParams.get('state');
          
          // 提前清理 URL 中的参数
          if (code || state) {
            const newUrl = new URL(window.location.href);
            newUrl.searchParams.delete('code');
            newUrl.searchParams.delete('state');
            window.history.replaceState({}, '', newUrl.toString());
          }
          
          const storedState = sessionStorage.getItem('state');
          // 清空状态参数
          sessionStorage.removeItem('state');

          // console.log(state, storedState, code);

          if (storedState && storedState !== state) {
            ElMessageBox.confirm('授权失败', '提示',{type: 'error'})
            return;
          }
          
          if (code && state) {
            await handleAuthorization(code);
          }
        }
        finally {
          isLocked.value = false;
        }
      });

      async function tenantAuth() {
        isLocked.value = true;
        const app_id = 'cli_a9ad0d32f1b89bdf';
        const redirect_uri = encodeURIComponent(window.location.href);
        const state = randomString(16);
        sessionStorage.setItem('state', state);
        const authUrl = `https://accounts.feishu.cn/open-apis/authen/v1/authorize?client_id=${app_id}&response_type=code&redirect_uri=${redirect_uri}&state=${state}`;
        console.log(authUrl);
        window.location.href = authUrl;
      }

      async function handleAuthorization(code) {
        isLocked.value = true;
        try {
          const res = await axios.post('https://feishu.jzl.com/api/feishu/plugin/login', {
            code: code,
            appID: 'cli_a9ad0d32f1b89bdf',
            redirect_uri: encodeURIComponent(window.location.href),
          })
          formData.value.username = res.data.username;
          formData.value.remainMoney = res.data.remain_money;
          formData.value.key = res.data.key;
          formData.value.isLogin = true;
          localStorage.setItem('isLogin', 'true');
          localStorage.setItem('username', res.data.username);
          localStorage.setItem('key', res.data.key);
        } catch (error) {
          console.error('授权失败:', error);
          formData.value.message = '授权失败，请联系管理员';
          formData.value.messageType = 'error';
        }
        finally {
          isLocked.value = false;
        }
      }

      return {
        formRef,
        formData,
        isLocked,
        tenantAuth,
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
            href="https://www.dajiala.com" 
            target="_blank"
            :underline="false" 
            type="primary"
            style="padding-left: 16px;"
            :disabled="isLocked"
          >获取key
          </el-link>
        </el-form-item>
      </el-card>

      <el-button type="primary" @click="tenantAuth">获取授权</el-button>
      
      <el-card class="card-item" shadow="hover">
        <el-tabs :disabled="isLocked">
          <el-tab-pane label="公众号" name="0">
            <GhForm :form-data="formData" :is-locked="isLocked" @update:is-locked="isLocked = $event" />
          </el-tab-pane>
          <el-tab-pane label="抖音" name="1">
            <DyForm :form-data="formData" :is-locked="isLocked" @update:is-locked="isLocked = $event" />
          </el-tab-pane>
          <el-tab-pane label="视频号" name="2">
            <V2Form :form-data="formData" :is-locked="isLocked" @update:is-locked="isLocked = $event" />
          </el-tab-pane>
        </el-tabs>
      </el-card>
      
      <!-- <p>{{ formData }}</p>
      <p>{{ isLocked }}</p> -->
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

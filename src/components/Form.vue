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
  import SensitiveText from './sensitiveText.vue'
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
      SensitiveText,
    },
    setup() {
      const app_id = 'cli_a9f6a88460f85bc6';
      const formRef = ref(null)
      const formData = ref({
        isLogin: false,
        key: null,
        message: null,
        messageType: 'success',
        remainMoney: null,
      });

      const isLocked = ref(false);

      const isShow = ref(false);

      watch(isLocked, async (newVal, oldVal) => {
        if (newVal === false) {
          await keyAuth(formData.value.key);
          isShow.value = false;
          if (formData.value.message) {
            await ElMessageBox.confirm(formData.value.message, '提示',{type: formData.value.messageType})
            // 清空提示信息
            formData.value.message = null;
            formData.value.messageType = 'success';
          }
        }
        else if (newVal === true) {
          isShow.value = true;
        }
      });

      onMounted(async () => {
        isLocked.value = true;
        try{
          // 从URL中获取state
          const urlParams = new URLSearchParams(window.location.search);
          const callback = urlParams.get('callback');
          
          // 从地址中去除callback
          if (callback) {
            const newUrl = new URL(window.location.href);
            newUrl.searchParams.delete('callback');
            window.history.replaceState({}, '', newUrl.toString());
          }

          const storedState = sessionStorage.getItem('state');
          sessionStorage.removeItem('state');

          if (storedState && callback) {
            if (!(await handleAuthorization(storedState))) {
              formData.value.message = '授权失败，请重试或联系管理员';
              formData.value.messageType = 'error';
            }
          }
          else if (sessionStorage.getItem('jzl_key')) {
            if (!(await keyAuth(sessionStorage.getItem('jzl_key')))) {
              formData.value.message = '授权失败，请重试或联系管理员';
              formData.value.messageType = 'error';
            }
          }
        }
        finally {
          isLocked.value = false;
        }
      });

      async function tenantAuth() {
        isLocked.value = true;
        const redirect_uri = encodeURIComponent("https://feishu.jzl.com/api/v1/auth/feishu/plugin/callback");
        const state = crypto.randomUUID();
        sessionStorage.setItem('state', state);
        try {
          const frontendUrl = new URL(window.location.href);
          frontendUrl.searchParams.append('callback', 1);
          const res = await axios.post('https://feishu.jzl.com/api/v1/auth/feishu/plugin/save_url', {
            state: state,
            frontend_url: frontendUrl.toString(),
          })
          const authUrl = `https://accounts.feishu.cn/open-apis/authen/v1/authorize?client_id=${app_id}&response_type=code&redirect_uri=${redirect_uri}&state=${state}`;
          window.location.href = authUrl;
        } catch (error) {
          console.error('授权失败:', error);
          formData.value.message = '授权失败，请重试或联系管理员';
          formData.value.messageType = 'error';
        }
        finally {
          isLocked.value = false;
        }
      }

      async function handleAuthorization(state) {
        let result = false;
        try {
          const res = await axios.post('https://feishu.jzl.com/api/v1/auth/feishu/plugin/get_key', {
            state: state,
          })
          formData.value.key = res.data.data.key;
          formData.value.isLogin = true;
          sessionStorage.setItem('jzl_key', res.data.data.key);
          result = true;
        } catch (error) {
          console.error('授权失败:', error);
        }
        return result;
      }

      async function keyAuth(jzl_key) {
        let result = false;
        try {
          const res = await pluginAPI.post('/fbmain/monitor/v3/get_remain_money', {
            key: jzl_key,
          });
          if (res && res.data && res.data.code === 0) {
            formData.value.isLogin = true;
            formData.value.key = jzl_key; 
            formData.value.remainMoney = res.data.remain_money;
            sessionStorage.setItem('jzl_key', jzl_key);
            result = true
          }
        }
        catch (error) {
          console.error(error);
        }
        return result;
      }

      function logout() {
        sessionStorage.removeItem('jzl_key');
        formData.value.isLogin = false;
        formData.value.key = null;
        formData.value.remainMoney = null;
      }

      async function inputKey() {
        const typeKey = await ElMessageBox.prompt('', '请输入key', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          inputType: 'password',
          inputPattern: /^[a-zA-Z0-9_]+$/,
          inputErrorMessage: '请输入正确的key格式',
        });
        if (typeKey) {
          isLocked.value = true;
          try {
            const result = await keyAuth(typeKey.value);
            if (!result) {
              formData.value.message = '无效的key';
              formData.value.messageType = 'error';
            }
          }
          finally {
            isLocked.value = false;
          }
        }
      }
      
      
      async function refreshBalance() {
        isLocked.value = true;
        try {
          const result = await keyAuth(formData.value.key);
        }
        finally {
          isLocked.value = false;
        } 
      }

      return {
        formRef,
        formData,
        isLocked,
        isShow,
        refreshBalance,
        tenantAuth,
        keyAuth,
        logout,
        inputKey,
      };
    },
  };
</script>

<template>
  <div class="form-container">
    <el-form ref="formRef" class="form" :model="formData" label-position="left">
      <div class="title-section">极致了数据采集插件</div>

      <el-card class="card-item" shadow="hover">
        <el-form>
          <el-form-item 
            label="余额 :"
            v-if="formData.isLogin"
          >
            <el-text style="flex: 1;">{{ formData.remainMoney }}</el-text>
          </el-form-item>

          <el-form-item 
            label="key :"
            v-if="formData.isLogin"
          >
            <SensitiveText
              :value="formData.key"
              style="flex: 1;"
            />
          </el-form-item>

          <el-form-item 
            label-width="null"
            v-if="formData.isLogin"
          >
            <el-button 
              type="primary" 
              @click="refreshBalance"
              plain
              style="flex: 1;"
            >
              刷新余额
            </el-button>

            <el-button 
              type="danger" 
              @click="logout"
              plain
              style="flex: 1;"
            >
              退出登录
            </el-button>
          </el-form-item>

          <el-form-item 
            label-width="null"
            v-if="!formData.isLogin"
          >
            <el-alert
              title="尚未登录,请选择登录方式"
              type="primary"
              show-icon
              closeable = "false"
            />
          </el-form-item>

          <el-form-item 
            label-width="null"
            v-if="!formData.isLogin"
          >
            <el-button 
              type="primary" 
              @click="tenantAuth"
              plain
              style="flex: 1;"
            >飞书账号授权</el-button>
          </el-form-item>

          <el-form-item 
            label-width="null"
            v-if="!formData.isLogin"
          >
            <el-button 
              type="primary" 
              @click="inputKey"
              plain
              style="flex: 1;"
            >已有账号，使用key</el-button>
          </el-form-item>

          <el-form-item 
            label-width="null"
            v-if="!formData.isLogin"
          >
            <el-button
              tag="a"
              href="https://www.dajiala.com"
              target="_blank"
              type="primary"
              plain
              style="flex: 1;text-decoration: none;"
            >
              前往注册账号
            </el-button>
          </el-form-item>

        </el-form>
      </el-card>
      
      
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
    <div class="loading-overlay" v-if="isShow">
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

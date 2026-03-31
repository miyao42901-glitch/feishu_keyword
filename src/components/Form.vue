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
  import LoginDialog from './LoginDialog.vue'
  import RechargeDialog from './RechargeDialog.vue'
  import WechatLoginDialog from './WechatLoginDialog.vue'
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
      LoginDialog,
      RechargeDialog,
      WechatLoginDialog,
    },
    setup() {
      const app_id = 'cli_a9f6a88460f85bc6';
      const formRef = ref(null)
      const alertList = ref({
        0: {title: '尚未登录,请选择登录方式' },
      })
      const formData = ref({
        username: null,
        isLogin: false,
        key: null,
        message: null,
        messageType: 'success',
        remainMoney: null,
      });

      const isLocked = ref(false);
      const loginDialogVisible = ref(false);
      const rechargeDialogVisible = ref(false)
      const wechatLoginDialogVisible = ref(false);

      const isShow = ref(false);

      watch(isLocked, async (newVal, oldVal) => {
        if (newVal === false) {
          if (formData.value.key) {
            await getRemainMoney();
          }
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
          // // 从URL中获取state
          // const urlParams = new URLSearchParams(window.location.search);
          // const callback = urlParams.get('callback');
          
          // // 从地址中去除callback
          // if (callback) {
          //   const newUrl = new URL(window.location.href);
          //   newUrl.searchParams.delete('callback');
          //   window.history.replaceState({}, '', newUrl.toString());
          // }

          // const storedState = sessionStorage.getItem('state');
          // sessionStorage.removeItem('state');

          // if (storedState && callback) {
          //   if (!(await handleAuthorization(storedState))) {
          //     formData.value.message = '授权失败，请重试或联系管理员';
          //     formData.value.messageType = 'error';
          //   }
          // }
          // else 
          if (sessionStorage.getItem('user_access_token')) {
            if (!(await getUserDetail(sessionStorage.getItem('user_access_token')))) {
              sessionStorage.removeItem('user_access_token');
              formData.value.message = '自动登录失败，请重新登录';
              formData.value.messageType = 'error';
            }
          }
        }
        finally {
          isLocked.value = false;
        }
      });

      // async function tenantAuth() {
      //   isLocked.value = true;
      //   const redirect_uri = encodeURIComponent("https://feishu.jzl.com/api/v1/auth/feishu/plugin/callback");
      //   const state = crypto.randomUUID();
      //   sessionStorage.setItem('state', state);
      //   let authUrl = '';
      //   try {
      //     const frontendUrl = new URL(window.location.href);
      //     frontendUrl.searchParams.append('callback', 1);
      //     const res = await axios.post('https://feishu.jzl.com/api/v1/auth/feishu/plugin/save_url', {
      //       state: state,
      //       frontend_url: frontendUrl.toString(),
      //     })
      //     authUrl = `https://accounts.feishu.cn/open-apis/authen/v1/authorize?client_id=${app_id}&response_type=code&redirect_uri=${redirect_uri}&state=${state}`;
      //   } catch (error) {
      //     console.error('授权失败:', error);
      //     formData.value.message = '授权失败，请重试或联系管理员';
      //     formData.value.messageType = 'error';
      //   }
      //   finally {
      //     if (authUrl) {
      //       window.location.href = authUrl;
      //     }
      //     else{
      //       isLocked.value = false;
      //     }
      //   }
      // }

      // async function handleAuthorization(state) {
      //   let result = false;
      //   try {
      //     const res = await axios.post('https://feishu.jzl.com/api/v1/auth/feishu/plugin/get_key', {
      //       state: state,
      //     })
      //     formData.value.key = res.data.data.key;
      //     formData.value.username = res.data.data.username;
      //     formData.value.isLogin = true;
      //     sessionStorage.setItem('user_access_token', res.data.data.user_access_token);
      //     result = true;
      //   } catch (error) {
      //     console.error('授权失败:', error);
      //   }
      //   return result;
      // }

      async function getUserDetail(user_access_token) {
        let result = false;
        try {
          const res = await pluginAPI.get('/fbmain/monitor/v3/api_user_detail', {
            headers: {
              accesstoken: user_access_token,
            }
          });
          if (res && res.data && res.data.code === 0) {
            formData.value.isLogin = true;
            formData.value.key = res.data.data.key;
            formData.value.username = res.data.data.user_name;
            formData.value.remainMoney = res.data.data.remain_money;
            result = true
          }
        }
        catch (error) {
          console.error(error);
        }
        return result;
      }

      async function getRemainMoney() {
        let result = false;
        try {
          const res = await pluginAPI.post('/fbmain/monitor/v3/get_remain_money', {
            key: formData.value.key,
          });
          if (res && res.data && res.data.code === 0) {
            formData.value.remainMoney = res.data.remain_money;
            result = true
          }
        }
        catch (error) {
          console.error(error);
        }
        return result;
      }

      function logout() {
        sessionStorage.removeItem('user_access_token');
        formData.value.isLogin = false;
        formData.value.key = null;
        formData.value.remainMoney = null;
      }

      function openLoginDialog() {
        loginDialogVisible.value = true;
      }

      async function openRechargeDialog() {
        isLocked.value = true;
        try {
          if (!sessionStorage.getItem('user_access_token')) {
            formData.value.message = '请先登录';
            formData.value.messageType = 'error';
          }
          else {
            rechargeDialogVisible.value = true;
          }
        }
        finally {
          isLocked.value = false;
        }
      }

      function openWechatLoginDialog() {
        wechatLoginDialogVisible.value = true;
      }

      async function handleRecharge(data) {
        isLocked.value = true;
        formData.value.message = `充值${data.amount}元成功，赠送${data.gift}元`;
        formData.value.messageType = 'success';
        await delay(500)
        isLocked.value = false;
      }

      async function handleLoginSuccess(data) {
        isLocked.value = true;
        try {
          if (!data.data.accessToken) {
            formData.value.message = '登录失败，请重试或联系管理员';
            formData.value.messageType = 'error';
          }
          else {
            sessionStorage.setItem('user_access_token', data.data.accessToken);
            const result = await getUserDetail(data.data.accessToken);
            if (!result) {
              formData.value.message = '登录失败，请重试或联系管理员';
              formData.value.messageType = 'error';
            }
          }
        }
        finally {
          isLocked.value = false;
        }
      }
      
      async function refreshBalance() {
        isLocked.value = true;
        try {
          if (formData.value.key) {
            const result = await getRemainMoney();
            await delay(500)
          }
          else {
            formData.value.message = '请先登录';
            formData.value.messageType = 'error';
          }
        }
        finally {
          isLocked.value = false;
        } 
      }

      const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms))

      return {
        formRef,
        alertList,
        formData,
        isLocked,
        isShow,
        rechargeDialogVisible,
        loginDialogVisible,
        wechatLoginDialogVisible,
        refreshBalance,
        // tenantAuth,
        getRemainMoney,
        logout,
        openLoginDialog,
        handleLoginSuccess,
        openRechargeDialog,
        handleRecharge,
        openWechatLoginDialog,
      };
    },
  };
</script>

<template>
  <div class="form-container">
    <el-form ref="formRef" class="form" :model="formData">
      <div class="title-section">极致了数据助手</div>

      <el-card class="card-item" shadow="hover">
        <el-form label-width="60px" label-position="left">
          <el-form-item 
            label="用户名"
            v-if="formData.isLogin"
          >
            <el-text style="flex: 1;">{{ formData.username }}</el-text>
          </el-form-item>

          <el-form-item 
            label="余额"
            v-if="formData.isLogin"
          >
            <el-text style="flex: 1;">{{ formData.remainMoney }}</el-text>
          </el-form-item>

          <!-- <el-form-item 
            label="key :"
            v-if="formData.isLogin"
          >
            <SensitiveText
              :value="formData.key"
              style="flex: 1;"
            />
          </el-form-item> -->

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
            v-if="formData.isLogin"
          >
            <el-button
              type="primary"
              plain
              style="flex: 1;"
              @click="openRechargeDialog"
            >
              余额充值
            </el-button>

            <el-button
              tag="a"
              href="https://www.dajiala.com/main/interface"
              target="_blank"
              type="primary"
              plain
              style="flex: 1;text-decoration: none;"
            >
              了解更多
            </el-button>
          </el-form-item>
          
          <el-form-item v-if="alertList[0] && !formData.isLogin" label-width="null">
            <el-alert
              :title="alertList[0].title"
              type="primary"
              show-icon
              @close="() => alertList[0] = null"
            />
          </el-form-item>

          <!-- <el-form-item 
            label-width="null"
            v-if="!formData.isLogin"
          >
            <el-button 
              type="primary" 
              @click="tenantAuth"
              plain
              style="flex: 1;"
            >飞书账号授权</el-button>
          </el-form-item> -->

          <el-form-item 
            label-width="null"
            v-if="!formData.isLogin"
          >
            <el-button 
              type="primary"
              @click="openWechatLoginDialog"
              plain
              style="flex: 1;"
            >微信扫码注册/登录</el-button>
          </el-form-item>

          <el-form-item 
            label-width="null"
            v-if="!formData.isLogin"
          >
            <el-button 
              type="primary" 
              @click="openLoginDialog"
              plain
              style="flex: 1;"
            >账号密码登录</el-button>
          </el-form-item>

          <el-form-item 
            label-width="null"
            v-if="!formData.isLogin"
          >
            <el-button
              tag="a"
              href="https://www.dajiala.com/main/interface"
              target="_blank"
              type="primary"
              plain
              style="flex: 1;text-decoration: none;"
            >
              了解更多
            </el-button>
          </el-form-item>

        </el-form>
      </el-card>
      
      
      <el-card class="card-item" shadow="hover">
        <el-tabs :disabled="isLocked">
          <el-tab-pane label="抖音">
            <DyForm :form-data="formData" :is-locked="isLocked" @update:is-locked="isLocked = $event" />
          </el-tab-pane>
          <el-tab-pane label="公众号">
            <GhForm :form-data="formData" :is-locked="isLocked" @update:is-locked="isLocked = $event" />
          </el-tab-pane>
          <el-tab-pane label="视频号">
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

    <!-- 登录对话框 -->
    <LoginDialog
      v-model:visible="loginDialogVisible"
      @login-success="handleLoginSuccess"
    />

    <!-- 充值对话框 -->
    <RechargeDialog
      v-model:visible="rechargeDialogVisible"
      @recharge="handleRecharge"
    />

    <!-- 微信登录对话框 -->
    <WechatLoginDialog
      v-model:visible="wechatLoginDialogVisible"
      @login-success="handleLoginSuccess"
    />
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
    padding-left: 45px;
    padding-bottom: 10px;
    margin-bottom: 10px;
    padding-top: 10px;
    background-image: url('/jzl_icon.png');
    background-repeat: no-repeat;
    background-size: 40px;
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

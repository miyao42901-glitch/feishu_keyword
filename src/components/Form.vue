<script>
  import { bitable, bridge, FieldType } from '@lark-base-open/js-sdk';
  import { ref, onMounted, computed, watch } from 'vue';
  import { useI18n } from 'vue-i18n';
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
  import GhForm from './ghForm.vue'
  import DyForm from './dyForm.vue'
  // import XhsForm from './xhsForm.vue'
  import V2Form from './v2Form.vue'
  import KsForm from './ksForm.vue'

  import PDyForm from '@/paneForms/dyForm.vue'
  import PGhForm from '@/paneForms/ghForm.vue'
  import PV2Form from '@/paneForms/v2Form.vue'
  import PKsForm from '@/paneForms/ksForm.vue'
  import PXhsForm from '@/paneForms/xhsForm.vue'

  import SensitiveText from './sensitiveText.vue'
  import LoginDialog from './LoginDialog.vue'
  import RechargeCard from './RechargeCard.vue'
  import WechatLoginDialog from './WechatLoginDialog.vue'
  import axios from 'axios'
  import '@/assets/form-styles.css'

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
      KsForm,

      PDyForm,
      PGhForm,
      PV2Form,
      PKsForm,
      PXhsForm,

      SensitiveText,
      LoginDialog,
      RechargeCard,
      WechatLoginDialog,
    },
    setup() {
      const { t } = useI18n();
      const app_id = 'cli_a9f6a88460f85bc6';
      const formRef = ref(null)
      const alertList = ref({
        0: {title: t('form.alert.guide') },
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
      const showRechargeCard = ref(false)
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
          if (localStorage.getItem('user_access_token')) {
            if (!(await getUserDetail(localStorage.getItem('user_access_token')))) {
              localStorage.removeItem('user_access_token');
              formData.value.message = t('form.messages.autoLoginFailed');
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
      //     localStorage.setItem('user_access_token', res.data.data.user_access_token);
      //     result = true;
      //   } catch (error) {
      //     console.error('授权失败:', error);
      //   }
      //   return result;
      // }

      async function getUserDetail(user_access_token) {
        let result = false;
        try {
          const res = await axios.get('https://www.dajiala.com/fbmain/monitor/v3/api_user_detail', {
            headers: {
              accesstoken: user_access_token,
            }
          });
          if (res && res.data && res.data.code === 0) {
            formData.value.isLogin = true;
            formData.value.key = res.data.data.key;
            // formData.value.key = 'JZL6f0685390502a6b9';
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
          const res = await axios.post('https://www.dajiala.com/fbmain/monitor/v3/get_remain_money', {
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
        localStorage.removeItem('user_access_token');
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
          if (!localStorage.getItem('user_access_token')) {
            formData.value.message = t('form.messages.loginFirst');
            formData.value.messageType = 'error';
          }
          else {
            showRechargeCard.value = true;
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
        formData.value.message = t('form.messages.rechargeSuccess', { amount: data.amount, gift: data.gift });
        formData.value.messageType = 'success';
        await delay(500)
        isLocked.value = false;
      }

      async function handleLoginSuccess(data) {
        isLocked.value = true;
        try {
          const token = data?.data?.accessToken;
          if (!token) {
            formData.value.message = t('form.messages.loginFailed');
            formData.value.messageType = 'error';
          }
          else {
            localStorage.setItem('user_access_token', token);
            const result = await getUserDetail(token);
            if (!result) {
              formData.value.message = t('form.messages.loginFailed');
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
            formData.value.message = t('form.messages.loginFirst');
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
        showRechargeCard,
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
        t,
      };
    },
  };
</script>

<template>
  <div class="form-container">
    <el-form ref="formRef" :model="formData">
      <div class="title-section">{{ t('form.title') }}</div>

      <el-card class="card-item" shadow="hover">
        
        <el-form class="ghForm" label-position="left" label-width="auto">
          
          <el-form-item v-if="alertList[0]" label-width="null">
            <el-alert
              type="primary"
              @close="() => alertList[0] = null"
            >
              {{ t('form.alert.guide.text') }}<a href="https://lcnnrhjmwxym.feishu.cn/wiki/OruzwbB6nigLMek8zxFcbKwmnXg" target="_blank">{{ t('form.alert.guide.urlText') }}</a>
            </el-alert>
          </el-form-item>

          <el-form-item 
            :label="t('form.fields.username')"
            v-if="formData.isLogin"
          >
            <el-text style="flex: 1;">{{ formData.username }}</el-text>
          </el-form-item>

          <el-form-item 
            :label="t('form.fields.balance')"
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
              {{ t('form.buttons.refreshBalance') }}
            </el-button>

            <el-button 
              type="danger" 
              @click="logout"
              plain
              style="flex: 1;"
            >
              {{ t('form.buttons.logout') }}
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
              {{ t('form.buttons.recharge') }}
            </el-button>

            <el-button
              tag="a"
              href="https://www.dajiala.com/main/interface"
              target="_blank"
              type="primary"
              plain
              style="flex: 1;text-decoration: none;"
            >
              {{ t('form.buttons.learnMore') }}
            </el-button>
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
            >{{ t('form.buttons.wechatLogin') }}</el-button>
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
            >{{ t('form.buttons.passwordLogin') }}</el-button>
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
              {{ t('form.buttons.learnMore') }}
            </el-button>
          </el-form-item>

        </el-form>
      </el-card>

    <!-- 充值卡片 -->
    <RechargeCard
      v-if="showRechargeCard"
      @recharge="handleRecharge"
      @close="showRechargeCard = false"
    />

      <!-- <el-card v-show="!showRechargeCard" class="card-item" shadow="hover">
        <el-tabs :disabled="isLocked">
          <el-tab-pane :label="t('form.tabs.douyin')">
            <DyForm :form-data="formData" :is-locked="isLocked" @update:is-locked="isLocked = $event" />
          </el-tab-pane>
          <el-tab-pane :label="t('form.tabs.wechatChannel')">
            <V2Form :form-data="formData" :is-locked="isLocked" @update:is-locked="isLocked = $event" />
          </el-tab-pane>
          <el-tab-pane :label="t('form.tabs.wechat')">
            <GhForm :form-data="formData" :is-locked="isLocked" @update:is-locked="isLocked = $event" />
          </el-tab-pane>
          <el-tab-pane :label="t('form.tabs.kuaishou')">
            <KsForm :form-data="formData" :is-locked="isLocked" @update:is-locked="isLocked = $event" />
          </el-tab-pane>
        </el-tabs>
      </el-card> -->

      <el-card v-show="!showRechargeCard" class="card-item" shadow="hover">
        <el-tabs :disabled="isLocked">
          <el-tab-pane :label="t('form.tabs.douyin')">
            <PDyForm :form-data="formData" :is-locked="isLocked" @update:is-locked="isLocked = $event" />
          </el-tab-pane>
          <el-tab-pane :label="'小红书'">
            <PXhsForm :form-data="formData" :is-locked="isLocked" @update:is-locked="isLocked = $event" />
          </el-tab-pane>
          <el-tab-pane :label="t('form.tabs.wechatChannel')">
            <PV2Form :form-data="formData" :is-locked="isLocked" @update:is-locked="isLocked = $event" />
          </el-tab-pane>
          <el-tab-pane :label="t('form.tabs.wechat')">
            <PGhForm :form-data="formData" :is-locked="isLocked" @update:is-locked="isLocked = $event" />
          </el-tab-pane>
          <el-tab-pane :label="t('form.tabs.kuaishou')">
            <PKsForm :form-data="formData" :is-locked="isLocked" @update:is-locked="isLocked = $event" />
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
        <p>{{ t('form.loading') }}</p>
      </div>
    </div>

    <!-- 登录对话框 -->
    <LoginDialog
      v-model:visible="loginDialogVisible"
      @login-success="handleLoginSuccess"
    />


    <!-- 微信登录对话框 -->
    <WechatLoginDialog
      v-model:visible="wechatLoginDialogVisible"
      @login-success="handleLoginSuccess"
    />
  </div>
</template>

<style scoped>
  .title-section {
    font-size: 20px;
    color: var(--el-text-color-primary);
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
    background-color: var(--el-bg-color);
  }
  
  .loading-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: var(--el-overlay-color);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
    backdrop-filter: blur(2px);
  }
  
  .loading-content {
    text-align: center;
    padding: 30px;
    background-color: var(--el-bg-color);
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    border: 1px solid var(--el-border-color);
  }
  
  .loading-spinner {
    width: 40px;
    height: 40px;
    border: 4px solid var(--el-border-color-lighter);
    border-top: 4px solid var(--el-color-primary);
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
    color: var(--el-text-color-regular);
  }
</style>

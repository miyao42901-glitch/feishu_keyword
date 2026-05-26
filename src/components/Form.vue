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
  import PDyFormNew from '@/paneForms/dyForm_new.vue'

  import SensitiveText from './sensitiveText.vue'
  import LoginDialog from './LoginDialog.vue'
  import RechargeCard from './RechargeCard.vue'
  import RechargeDialog from './RechargeDialog.vue'
  import WechatLoginDialog from './WechatLoginDialog.vue'
  import PostConfirm from '@/tipDialogs/postConfirm.vue'
  import axios from 'axios'
  import { RefreshRight, Switch } from '@element-plus/icons-vue'
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
      PDyFormNew,

      SensitiveText,
      LoginDialog,
      RechargeCard,
      RechargeDialog,
      WechatLoginDialog,

      RefreshRight,
      Switch,

      PostConfirm,
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
      const rechargeDialogVisible = ref(false);
      const showRechargeCard = ref(false);
      const wechatLoginDialogVisible = ref(false);

      const isShow = ref(false);

      const postConfirmVisible = ref(false);

      const postConfirmProps = ref({
        resultTableId: '',
        displayInfo: '',
        resultType: 'success',
      })

      watch(isLocked, async (newVal, oldVal) => {
        if (newVal === false) {
          if (formData.value.key) {
            await getRemainMoney();
          }
          isShow.value = false;
          if (formData.value.message) {
            await ElMessageBox.confirm(formData.value.message, '提示',{type: formData.value.messageType})
            postConfirmProps.value.displayInfo = formData.value.message;
            postConfirmProps.value.resultType = formData.value.messageType;
            postConfirmVisible.value = true;
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

      async function logout() {
        const confirm = await ElMessageBox.confirm('确定退出登录吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        if (!confirm) {
          return;
        }
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
        rechargeDialogVisible,
        postConfirmVisible,
        postConfirmProps,
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
    <div class="container">
        <div class="header">
            <div class="brand-wrapper">
                <div class="title-section">
                    <div class="brand-text">
                        <div class="brand-title">极致了数​​据助手</div>
                        <a  class="brand-sub" href="https://www.dajiala.com/main/interface" target="_blank" style="text-decoration: none;">了解更多 ></a>
                    </div>
                </div>
            </div>
            
            <div class="header-actions">
                <a class="action-btn" href="https://lcnnrhjmwxym.feishu.cn/wiki/OruzwbB6nigLMek8zxFcbKwmnXg" target="_blank" style="text-decoration: none;">使用指南</a>
                <span style="color: #d1d5db; font-size: 12px;">|</span>
                <a class="action-btn" href="https://lcnnrhjmwxym.feishu.cn/wiki/OruzwbB6nigLMek8zxFcbKwmnXg" target="_blank" style="text-decoration: none;">加入交流群</a>
            </div>
        </div>

        <div class="info-panel">
            <div class="info-left" v-if="formData.isLogin">
                <div class="info-row">
                    <span class="info-label">用户:</span>
                    <span class="info-value">{{ formData.username }}</span>
                    <el-tooltip effect="dark" content="退出登录" placement="top" :enterable="false" :hide-after="0">
                        <el-icon class="info-icon" @click="logout"><Switch /></el-icon>
                    </el-tooltip>
                </div>
                <div class="info-row">
                    <span class="info-label">余额:</span>
                    <span class="info-value">{{ formData.remainMoney }}</span>
                    <el-tooltip effect="dark" content="刷新余额" placement="top" :enterable="false" :hide-after="0">
                        <el-icon class="info-icon" @click="refreshBalance"><RefreshRight /></el-icon>
                    </el-tooltip>
                </div>
            </div>

            <button class="info-btn" v-if="formData.isLogin" @click="openRechargeDialog">余额充值</button>
            <button class="info-btn" v-if="!formData.isLogin" @click="openWechatLoginDialog">微信扫码登录/注册</button>
            <button class="info-btn" v-if="!formData.isLogin" @click="openLoginDialog">账号密码登录</button>
        </div>
    </div>

    <div class="container-down">
      <el-tabs :disabled="isLocked" class="my-custom-tabs">
        <el-tab-pane :label="'抖音测试'">
          <PDyFormNew :form-data="formData" :is-locked="isLocked" @update:is-locked="isLocked = $event" />
        </el-tab-pane>
        <el-tab-pane :label="'抖音测试1'">
          <PDyFormNew :form-data="formData" :is-locked="isLocked" @update:is-locked="isLocked = $event" />
        </el-tab-pane>
        <!-- <el-tab-pane :label="t('form.tabs.douyin')">
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
        </el-tab-pane> -->
      </el-tabs>
    </div>
  </div>

  <!-- 加载遮罩 -->
  <div class="loading-overlay" v-if="isShow">
    <div class="loading-content">
      <div class="loading-spinner"></div>
      <p>{{ t('form.loading') }}</p>
    </div>
  </div>

  <LoginDialog
    v-model:visible="loginDialogVisible"
    @login-success="handleLoginSuccess"
  />

  <WechatLoginDialog
    v-model:visible="wechatLoginDialogVisible"
    @login-success="handleLoginSuccess"
  />

  <RechargeDialog
    v-model:visible="rechargeDialogVisible"
    @recharge="handleRecharge"
  />

  <PostConfirm
    v-model:visible="postConfirmVisible"
    :resultTableId="postConfirmProps.resultTableId"
    :displayInfo="postConfirmProps.displayInfo"
    :resultType="postConfirmProps.resultType"
  />

</template>

<style scoped>
  .title-section {
    padding-left: 45px;
    padding-top: 5px;
    padding-bottom: 10px;
    background-image: url('/jzl_icon.png');
    background-repeat: no-repeat;
    background-size: 40px;
  }
  
  /* 加载遮罩样式 */
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

  .my-custom-tabs{
    height: 100%;
  }
  .my-custom-tabs :deep(.el-tabs__item.is-active) {
    color: #1a2a5f;
    font-weight: bold;
  }
  .my-custom-tabs :deep(.el-tabs__active-bar) {
    background-color: #1a2a5f;
  }

  /* 2. 修改鼠标悬停时的颜色 */
  .my-custom-tabs :deep(.el-tabs__item:hover) {
    color: #1a2a5f;
  }
</style>

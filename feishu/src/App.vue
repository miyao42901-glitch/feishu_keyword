<script setup lang="ts">
import { ArrowLeft } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, onMounted, ref, watch } from 'vue'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import GlobalApiKeyBar from '@/components/GlobalApiKeyBar.vue'
import YddmLoginDialog from '@/components/YddmLoginDialog.vue'
import TasksView from '@/views/TasksView.vue'
import YddmAuthView from '@/views/YddmAuthView.vue'
import { formatPointsBadge } from '@/lib/account-balance'
import { getCustomerServiceQrUrl } from '@/lib/insufficient-balance'
import { homeHeroAccountPointsIconImgAttrs, homeHeroBannerBg } from '@/lib/home-hero-media'
import { useAccountPointsStore } from '@/stores/accountPoints'
import { useGlobalSettingsStore } from '@/stores/globalSettings'
import { useYddmAuthStore } from '@/stores/yddmAuth'

const activeTab = ref<'tasks' | 'yddmAuth'>('tasks')
const accountPoints = useAccountPointsStore()
const globalSettings = useGlobalSettingsStore()
const yddmAuth = useYddmAuthStore()

/** 未登录时展示「登录账户」 */
const showLoginAccountBtn = computed(() => !yddmAuth.isLoggedIn)

/** 任务页是否处于新建/编辑配置（由 TasksView 同步） */
const inTaskCreate = ref(false)
const tasksViewRef = ref<{ leaveCreateToList: () => Promise<void> } | null>(null)
const loginDialogVisible = ref(false)

watch(activeTab, (t) => {
  if (t !== 'tasks') inTaskCreate.value = false
})

function onHeaderNavClick() {
  if (activeTab.value !== 'tasks') {
    activeTab.value = 'tasks'
    return
  }
  if (inTaskCreate.value && tasksViewRef.value) {
    void tasksViewRef.value.leaveCreateToList()
    return
  }
}

const heroBannerBgStyle = {
  '--hero-bg-1x': `url(${homeHeroBannerBg['1x']})`,
  '--hero-bg-2x': `url(${homeHeroBannerBg['2x']})`,
} as Record<string, string>
const DEFAULT_OPERATIONS_DOC_URL =
  'https://lcnnrhjmwxym.feishu.cn/wiki/Hnstw1DDgi3sswkMwh6cyn2lnlc'

const operationsDocUrl =
  (import.meta.env.VITE_OPERATIONS_DOC_URL as string | undefined)?.trim() ||
  DEFAULT_OPERATIONS_DOC_URL

/** 首页「加入用户群」默认飞书 applink（可用 `VITE_USER_GROUP_URL` 覆盖） */
const DEFAULT_USER_GROUP_URL =
  'https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=b40ked6d-3390-421e-b94a-446cce2b2271'

const userGroupUrl =
  (import.meta.env.VITE_USER_GROUP_URL as string | undefined)?.trim() || DEFAULT_USER_GROUP_URL
const userGroupQrUrl = (import.meta.env.VITE_CUSTOMER_SERVICE_QR_URL as string | undefined)?.trim()

const userGroupDialogVisible = ref(false)
const balanceDialogVisible = ref(false)
const balanceQrUrl = getCustomerServiceQrUrl()

function openBalanceDialog() {
  balanceDialogVisible.value = true
}

function openOperationsDoc() {
  window.open(operationsDocUrl, '_blank', 'noopener,noreferrer')
}

function openUserGroup() {
  if (userGroupUrl) {
    window.open(userGroupUrl, '_blank', 'noopener,noreferrer')
    return
  }
  if (userGroupQrUrl) {
    userGroupDialogVisible.value = true
    return
  }
  ElMessage.info('请在环境变量 VITE_USER_GROUP_URL 中配置用户群链接')
}

function openLoginDialog() {
  loginDialogVisible.value = true
}

/** 首页横幅右上角：剩余积分（YDDM 登录个人信息） */
const heroBalanceBadgeText = computed(() => {
  if (!yddmAuth.isLoggedIn && !yddmAuth.me) return '—'
  return formatPointsBadge(accountPoints.currentBalancePoints)
})

watch(
  () => yddmAuth.me,
  (m) => {
    accountPoints.syncFromYddmUser(m)
  },
  { deep: true, immediate: true },
)

onMounted(() => {
  const tok = yddmAuth.accessToken?.trim()
  if (!tok) return
  void yddmAuth.refreshMe().then((u) => {
    const key = u?.api_key?.trim()
    if (key) globalSettings.authCode = key
  }).catch(() => {
    /* 保留本地 token，由任务请求或用户手动重试 */
  })
})
</script>

<template>
  <el-config-provider :locale="zhCn">
  <div class="flex h-screen min-h-0 w-full min-w-0 flex-col bg-[#ffffff]">
    <YddmLoginDialog v-model="loginDialogVisible" />
    <el-dialog
      v-model="userGroupDialogVisible"
      title="加入用户群"
      width="min(360px, 92vw)"
      align-center
      append-to-body
      class="user-group-dialog"
    >
      <p class="user-group-dialog__hint">扫码或长按识别二维码加入用户群</p>
      <img
        v-if="userGroupQrUrl"
        class="user-group-dialog__qr"
        :src="userGroupQrUrl"
        alt="用户群二维码"
      />
    </el-dialog>
    <el-dialog
      v-model="balanceDialogVisible"
      width="min(360px, 92vw)"
      align-center
      append-to-body
      :show-header="false"
      class="balance-qr-dialog"
    >
      <img
        class="balance-qr-dialog__qr"
        :src="balanceQrUrl"
        alt="客服二维码"
        loading="lazy"
        decoding="async"
      />
    </el-dialog>
    <div class="home-hero">
      <div class="home-hero__bg" :style="heroBannerBgStyle" aria-hidden="true" />
      <div class="home-hero__inner">
        <div class="home-hero__copy">
          <div class="home-hero__title-row">
            <span class="home-hero__title-accent" aria-hidden="true" />
            <h1 class="home-hero__title">关键词监控</h1>
          </div>
          <div class="home-hero__actions" role="group" aria-label="快捷入口">
            <button type="button" class="home-hero__action" @click="openOperationsDoc">
              <svg class="home-hero__action-icon" viewBox="0 0 24 24" aria-hidden="true">
                <rect x="4" y="5" width="16" height="4.5" rx="1.2" fill="currentColor" opacity="0.88" />
                <rect x="4" y="10.25" width="16" height="4.5" rx="1.2" fill="currentColor" opacity="0.72" />
                <rect x="4" y="15.5" width="11" height="4.5" rx="1.2" fill="currentColor" opacity="0.56" />
              </svg>
              操作文档
            </button>
            <span class="home-hero__action-divider" aria-hidden="true" />
            <button type="button" class="home-hero__action" @click="openUserGroup">
              <svg class="home-hero__action-icon home-hero__action-icon--chat" viewBox="0 0 24 24" aria-hidden="true">
                <path
                  fill="currentColor"
                  d="M6 4h12a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H9l-4 3.5V6a2 2 0 0 1 2-2Z"
                  opacity="0.9"
                />
              </svg>
              加入用户群
            </button>
          </div>
        </div>
        <div class="home-hero__balance-wrap">
          <button
            type="button"
            class="home-hero__balance"
            aria-label="剩余积分，点击查看充值"
            @click="openBalanceDialog"
          >
            <img
              class="home-hero__balance-icon"
              v-bind="homeHeroAccountPointsIconImgAttrs()"
              width="14"
              height="14"
              alt=""
              decoding="async"
            />
            <span class="home-hero__balance-text">{{ heroBalanceBadgeText }}</span>
          </button>
          <p class="home-hero__balance-hint">充值请联系客服</p>
        </div>
      </div>
    </div>

    <div class="app-scroll flex min-h-0 w-full min-w-0 flex-1 flex-col overflow-y-auto bg-[#ffffff]">
      <header
        class="flex shrink-0 items-center justify-between gap-3 bg-[#ffffff] px-4 py-3"
        :class="
          activeTab === 'tasks' && inTaskCreate
            ? 'app-header-return-sticky'
            : 'border-b border-slate-200'
        "
      >
        <button
          type="button"
          class="inline-flex items-center gap-2 text-lg font-bold focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/30"
          :class="activeTab === 'tasks' ? 'text-slate-900' : 'text-slate-500'"
          @click="onHeaderNavClick"
        >
          <template v-if="activeTab === 'tasks' && inTaskCreate">
            <el-icon class="shrink-0" :size="20">
              <ArrowLeft />
            </el-icon>
            <span>返回首页</span>
          </template>
          <template v-else>首页</template>
        </button>
        <div
          v-if="showLoginAccountBtn"
          v-show="!(activeTab === 'tasks' && inTaskCreate)"
          class="flex min-w-0 shrink-0 items-center gap-2 sm:gap-3"
        >
          <button
            type="button"
            class="inline-flex shrink-0 items-center gap-1.5 whitespace-nowrap text-sm font-medium text-slate-700 transition-colors hover:text-blue-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/30"
            @click="openLoginDialog"
          >
            <svg
              class="size-4 shrink-0 text-amber-500"
              viewBox="0 0 24 24"
              fill="currentColor"
              aria-hidden="true"
            >
              <path
                d="M12 2l1.8 4.5h4.7l-3.8 2.8 1.5 4.7L12 12.2 7.8 14l1.5-4.7L5.5 6.5h4.7L12 2zm-8 8.5L2 20h20l-2-9.5-3.5 2.6L14 20H10l-2.5-6.9L4 10.5z"
              />
            </svg>
            <span class="truncate">登录账户</span>
          </button>
        </div>
      </header>
      <div
        class="app-api-key-sticky"
        :class="{ 'app-api-key-sticky--below-return': activeTab === 'tasks' && inTaskCreate }"
      >
        <GlobalApiKeyBar @go-login="openLoginDialog" />
      </div>
      <div class="app-scroll-body min-h-0 w-full min-w-0 flex-1 p-4">
        <TasksView
          v-if="activeTab === 'tasks'"
          ref="tasksViewRef"
          @create-mode-change="inTaskCreate = $event"
        />
        <YddmAuthView v-else />
      </div>
    </div>
  </div>
  </el-config-provider>
</template>

<style scoped>
.home-hero {
  box-sizing: border-box;
  position: relative;
  flex-shrink: 0;
  width: 100%;
  max-width: 100%;
  min-width: 0;
  overflow: hidden;
  padding: 1.5rem 1rem 1.75rem;
  min-height: clamp(5.75rem, 9vw, 8rem);
  background-color: #f0f2f8;
}

.home-hero__bg {
  position: absolute;
  inset: 0;
  z-index: 0;
  background-color: transparent;
  background-image: var(--hero-bg-1x);
  background-repeat: no-repeat;
  background-position: right center;
  background-size: auto 100%;
  pointer-events: none;
}

@media (min-width: 768px) {
  .home-hero__bg {
    background-size: cover;
  }
}

@media (min-resolution: 2dppx) {
  .home-hero__bg {
    background-image: var(--hero-bg-2x);
  }
}

.home-hero__inner {
  box-sizing: border-box;
  position: relative;
  z-index: 1;
  display: flex;
  width: 100%;
  max-width: 100%;
  min-width: 0;
  min-height: 5.75rem;
  flex-direction: row;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
}

.home-hero__balance-wrap {
  display: flex;
  flex-shrink: 0;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.25rem;
  margin-left: auto;
  margin-top: 0.125rem;
}

.home-hero__balance {
  display: inline-flex;
  flex-shrink: 0;
  align-items: center;
  gap: 0.25rem;
  margin-left: 0;
  margin-top: 0;
  padding: 0.375rem 0.625rem;
  border: none;
  border-radius: 0.375rem;
  background: linear-gradient(135deg, #3370ff 0%, #1f22f6 100%);
  color: #ffffff;
  font-size: 0.75rem;
  font-weight: 600;
  line-height: 1.2;
  box-shadow: 0 2px 6px rgba(31, 34, 246, 0.22);
  cursor: pointer;
  transition: filter 0.15s ease, box-shadow 0.15s ease;
}

.home-hero__balance:hover {
  filter: brightness(1.06);
  box-shadow: 0 3px 8px rgba(31, 34, 246, 0.28);
}

.home-hero__balance:focus-visible {
  outline: 2px solid rgba(255, 255, 255, 0.85);
  outline-offset: 2px;
}

.home-hero__balance-icon {
  flex-shrink: 0;
  width: 14px;
  height: 14px;
  object-fit: contain;
}

.home-hero__balance-text {
  white-space: nowrap;
}

.home-hero__balance-hint {
  margin: 0;
  font-size: 0.6875rem;
  line-height: 1.3;
  color: #000000;
  white-space: nowrap;
}

.home-hero__copy {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  flex: 1 1 auto;
  min-width: 0;
  max-width: min(22rem, 58%);
}

.home-hero__title-row {
  display: flex;
  align-items: stretch;
  gap: 0.625rem;
}

.home-hero__title-accent {
  flex-shrink: 0;
  width: 3px;
  border-radius: 2px;
  background: linear-gradient(180deg, #3370ff 0%, #1f22f6 100%);
}

.home-hero__title {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 600;
  line-height: 1.35;
  letter-spacing: -0.01em;
  color: #0f1114;
}

.home-hero__actions {
  box-sizing: border-box;
  display: inline-flex;
  align-items: center;
  margin-top: 0.75rem;
  padding: 0.25rem 0.5rem;
  border: 1px solid #e8eaed;
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 1px 2px rgba(15, 17, 20, 0.04);
}

.home-hero__action {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  margin: 0;
  padding: 0.3125rem 0.625rem;
  border: none;
  border-radius: 9999px;
  background: transparent;
  color: #2b2f36;
  font-size: 0.75rem;
  font-weight: 500;
  line-height: 1.2;
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.home-hero__action:hover {
  background: rgba(51, 112, 255, 0.06);
}

.home-hero__action:focus-visible {
  outline: 2px solid rgba(31, 34, 246, 0.35);
  outline-offset: 1px;
}

.home-hero__action-divider {
  flex-shrink: 0;
  width: 1px;
  height: 14px;
  background: #dee0e3;
}

.home-hero__action-icon {
  flex-shrink: 0;
  width: 14px;
  height: 14px;
  color: #646a73;
}

.home-hero__action-icon--chat {
  color: #3370ff;
}

.user-group-dialog__hint {
  margin: 0 0 12px;
  font-size: 13px;
  line-height: 1.5;
  color: #646a73;
  text-align: center;
}

.user-group-dialog__qr {
  display: block;
  width: min(240px, 100%);
  margin: 0 auto;
  border-radius: 8px;
}

.balance-qr-dialog__qr {
  display: block;
  width: min(240px, 100%);
  margin: 0 auto;
  border-radius: 8px;
}

@media (min-width: 640px) {
  .home-hero {
    padding-left: 1.25rem;
    padding-right: 1.25rem;
  }

  .home-hero__title {
    font-size: 1.25rem;
  }
}

.app-scroll {
  -webkit-overflow-scrolling: touch;
}

.app-header-return-sticky {
  position: sticky;
  top: 0;
  z-index: 30;
}

.app-api-key-sticky {
  position: sticky;
  top: 0;
  z-index: 20;
  flex-shrink: 0;
  border-bottom: 1px solid #e5e7eb;
  background: #ffffff;
  padding: 10px 16px;
}

/* 与吸顶「返回首页」栏高度对齐，避免两条 sticky 叠在同一 top */
.app-api-key-sticky--below-return {
  top: 3.25rem;
}

.app-scroll-body {
  flex: 1 1 auto;
  min-height: 0;
}
</style>

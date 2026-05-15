<script setup lang="ts">
import { ArrowLeft } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, ref, watch } from 'vue'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import { storeToRefs } from 'pinia'
import GlobalApiKeyBar from '@/components/GlobalApiKeyBar.vue'
import YddmLoginDialog from '@/components/YddmLoginDialog.vue'
import TasksView from '@/views/TasksView.vue'
import YddmAuthView from '@/views/YddmAuthView.vue'
import { useAccountPointsStore } from '@/stores/accountPoints'
import { useGlobalSettingsStore } from '@/stores/globalSettings'
import { useYddmAuthStore } from '@/stores/yddmAuth'

const activeTab = ref<'tasks' | 'yddmAuth'>('tasks')
const accountPoints = useAccountPointsStore()
const globalSettings = useGlobalSettingsStore()
const yddmAuth = useYddmAuthStore()
const { authCode } = storeToRefs(globalSettings)

/** 已登录或可调用 API（含仅填写授权码）：展示退出登录 */
const showLogoutBtn = computed(
  () => Boolean(yddmAuth.isLoggedIn) || authCode.value.trim().length > 0,
)

function onLogout() {
  yddmAuth.clearSession()
  globalSettings.authCode = ''
  ElMessage.success('已退出登录')
}
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

const operationsDocUrl = (import.meta.env.VITE_OPERATIONS_DOC_URL as string | undefined)?.trim()

function openOperationsDoc() {
  if (operationsDocUrl) {
    window.open(operationsDocUrl, '_blank', 'noopener,noreferrer')
    return
  }
  ElMessage.info('请在环境变量 VITE_OPERATIONS_DOC_URL 中配置操作文档链接')
}

function openLoginDialog() {
  loginDialogVisible.value = true
}
</script>

<template>
  <el-config-provider :locale="zhCn">
  <div class="flex h-screen min-h-0 w-full min-w-0 flex-col bg-[#ffffff]">
    <YddmLoginDialog v-model="loginDialogVisible" />
    <div class="home-hero">
      <div class="home-hero__bg" aria-hidden="true" />
      <div class="home-hero__inner">
        <div class="home-hero__copy">
          <div class="home-hero__title-row">
            <span class="home-hero__title-accent" aria-hidden="true" />
            <h1 class="home-hero__title">关键词监控</h1>
          </div>
          <button type="button" class="home-hero__doc-btn" @click="openOperationsDoc">
            <svg class="home-hero__doc-icon" viewBox="0 0 24 24" aria-hidden="true">
              <rect x="4" y="5" width="16" height="4.5" rx="1.2" fill="currentColor" opacity="0.88" />
              <rect x="4" y="10.25" width="16" height="4.5" rx="1.2" fill="currentColor" opacity="0.72" />
              <rect x="4" y="15.5" width="11" height="4.5" rx="1.2" fill="currentColor" opacity="0.56" />
            </svg>
            操作文档
          </button>
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
          v-show="!(activeTab === 'tasks' && inTaskCreate)"
          class="flex min-w-0 shrink-0 items-center gap-2 sm:gap-3"
        >
          <span class="max-w-[9rem] truncate text-xs text-slate-500 sm:max-w-none"
            >余额 {{ accountPoints.currentBalancePoints }} 点</span
          >
          <button
            v-if="showLogoutBtn"
            type="button"
            class="inline-flex shrink-0 items-center justify-center whitespace-nowrap rounded-md px-2 py-1.5 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100 hover:text-red-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/30"
            @click="onLogout"
          >
            退出登录
          </button>
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
  background-image: url('/im.png');
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
    background-image: url('/im@2x.png');
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
  align-items: center;
  justify-content: flex-start;
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

.home-hero__doc-btn {
  box-sizing: border-box;
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  margin-top: 0.75rem;
  padding: 0.375rem 0.75rem;
  border: 1px solid #e1e4e8;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.92);
  color: #2b2f36;
  font-size: 0.75rem;
  font-weight: 500;
  line-height: 1.2;
  cursor: pointer;
  transition:
    background-color 0.15s ease,
    border-color 0.15s ease;
}

.home-hero__doc-btn:hover {
  background: #ffffff;
  border-color: #c9cdd4;
}

.home-hero__doc-btn:focus-visible {
  outline: 2px solid rgba(31, 34, 246, 0.35);
  outline-offset: 2px;
}

.home-hero__doc-icon {
  flex-shrink: 0;
  width: 14px;
  height: 14px;
  color: #646a73;
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

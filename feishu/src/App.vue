<script setup lang="ts">
import { ArrowLeft, Document } from '@element-plus/icons-vue'
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
  <div class="flex h-screen min-h-0 flex-col bg-[#ffffff]">
    <YddmLoginDialog v-model="loginDialogVisible" />
    <div class="home-hero min-h-[7.5rem] shrink-0 px-4 pb-8 pt-7">
      <h1 class="text-xl font-bold tracking-tight text-slate-900">关键词监控</h1>
      <button
        type="button"
        class="mt-3 inline-flex items-center gap-1.5 rounded-full border border-white/80 bg-white/95 px-3 py-1.5 text-xs font-medium text-slate-700 shadow-sm backdrop-blur-sm transition-colors hover:bg-white"
        @click="openOperationsDoc"
      >
        <el-icon class="text-slate-500" :size="14">
          <Document />
        </el-icon>
        操作文档
      </button>
    </div>

    <div class="app-scroll flex min-h-0 flex-1 flex-col overflow-y-auto bg-[#ffffff]">
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
      <div class="app-scroll-body min-h-0 flex-1 p-4">
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
  background-color: #ffffff;
  background-image: url('/im.png');
  background-repeat: no-repeat;
  background-position: right center;
  background-size: auto 100%;
}

@media (min-resolution: 2dppx) {
  .home-hero {
    background-image: url('/im@2x.png');
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

<script setup lang="ts">
import { ref } from 'vue'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import GlobalApiKeyBar from '@/components/GlobalApiKeyBar.vue'
import TasksView from '@/views/TasksView.vue'
import YddmAuthView from '@/views/YddmAuthView.vue'
import { useAccountPointsStore } from '@/stores/accountPoints'

const activeTab = ref<'tasks' | 'yddmAuth'>('tasks')
const accountPoints = useAccountPointsStore()
</script>

<template>
  <el-config-provider :locale="zhCn">
  <div class="flex h-screen min-h-0 flex-col bg-slate-50">
    <header
      class="flex shrink-0 items-center justify-between gap-3 border-b border-slate-200 bg-white px-4 py-3"
    >
      <h1 class="truncate text-sm font-semibold text-slate-900">飞书关键词监控插件</h1>
      <span class="shrink-0 text-sm text-slate-700">当前余额: {{ accountPoints.currentBalancePoints }}点</span>
    </header>
    <div class="shrink-0 border-b border-slate-200 bg-white px-4 py-3">
      <GlobalApiKeyBar @go-login="activeTab = 'yddmAuth'" />
    </div>
    <div class="grid shrink-0 grid-cols-2 border-b border-slate-200 bg-white">
      <button
        type="button"
        class="flex justify-center py-3 text-sm font-medium focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/40"
        @click="activeTab = 'tasks'"
      >
        <span
          class="inline-block border-b-[3px] pb-2 transition-colors"
          :class="
            activeTab === 'tasks'
              ? 'border-[#2563eb] font-medium text-[#2563eb]'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          "
        >
          任务配置
        </span>
      </button>
      <button
        type="button"
        class="flex justify-center py-3 text-sm font-medium focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/40"
        @click="activeTab = 'yddmAuth'"
      >
        <span
          class="inline-block border-b-[3px] pb-2 transition-colors"
          :class="
            activeTab === 'yddmAuth'
              ? 'border-[#2563eb] font-medium text-[#2563eb]'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          "
        >
          登录账户
        </span>
      </button>
    </div>
    <main class="min-h-0 flex-1 overflow-auto bg-[#f4f5f7] p-4">
      <TasksView v-if="activeTab === 'tasks'" />
      <YddmAuthView v-else />
    </main>
  </div>
  </el-config-provider>
</template>

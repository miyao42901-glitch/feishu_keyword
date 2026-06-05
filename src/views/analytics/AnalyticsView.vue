<template>
  <div class="analytics-layout">
    <aside class="analytics-sidebar">
      <div class="analytics-sidebar-header">
        <h2>多平台数据采集插件</h2>
      </div>
      <nav class="analytics-menu">
        <div
          v-for="item in menuItems"
          :key="item.key"
          :class="['analytics-menu-item', { active: activeView === item.key }]"
          @click="activeView = item.key"
        >
          <i :class="['menu-icon', item.icon]"></i>
          <span>{{ item.label }}</span>
        </div>
      </nav>
    </aside>

    <main class="analytics-main">
      <header class="analytics-topbar">
        <div class="analytics-topbar-left">
          <h1 class="analytics-topbar-title">{{ currentTitle }}</h1>
        </div>
        <div class="analytics-topbar-right">
          <div class="analytics-topbar-user">
            <el-avatar :size="32" style="background-color: #1a2a5f">J ZL</el-avatar>
          </div>
        </div>
      </header>

      <div class="analytics-content">
        <AnalyticsOverviewView v-if="activeView === 'overview'" />
        <LoginTrackView v-else-if="activeView === 'login'" />
        <CollectTaskView v-else-if="activeView === 'collect'" />
        <HelpGuideView v-else-if="activeView === 'help'" />
        <TaskListView v-else-if="activeView === 'tasks'" />
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import AnalyticsOverviewView from './AnalyticsOverviewView.vue'
import LoginTrackView from './LoginTrackView.vue'
import CollectTaskView from './CollectTaskView.vue'
import HelpGuideView from './HelpGuideView.vue'
import TaskListView from './TaskListView.vue'

const activeView = ref('overview')

const menuItems = [
  { key: 'overview', label: '数据总览', icon: 'el-icon-data-line' },
  { key: 'login', label: '登录与进入', icon: 'el-icon-user' },
  { key: 'collect', label: '采集任务', icon: 'el-icon-document' },
  { key: 'help', label: '帮助与引导', icon: 'el-icon-question' },
  { key: 'tasks', label: '任务列表', icon: 'el-icon-list' },
]

const currentTitle = computed(() => {
  const item = menuItems.find((m) => m.key === activeView.value)
  return item?.label ?? '数据总览'
})
</script>

<style scoped>
.analytics-layout {
  display: flex;
  height: 100vh;
  background: #f5f7fa;
  overflow: hidden;
}

.analytics-sidebar {
  width: 200px;
  background: #2c3e50;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.analytics-sidebar-header {
  padding: 20px 16px;
  background: #1a2a5f;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.analytics-sidebar-header h2 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: #fff;
  line-height: 1.4;
}

.analytics-menu {
  flex: 1;
  padding: 12px 0;
  overflow-y: auto;
}

.analytics-menu-item {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  color: rgba(255, 255, 255, 0.7);
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
  gap: 10px;
}

.analytics-menu-item:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

.analytics-menu-item.active {
  background: #1a2a5f;
  color: #fff;
  border-left: 3px solid #409eff;
}

.menu-icon {
  font-size: 16px;
  width: 16px;
  text-align: center;
}

.analytics-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.analytics-topbar {
  height: 60px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  flex-shrink: 0;
}

.analytics-topbar-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.analytics-topbar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.analytics-topbar-user {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.analytics-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}
</style>

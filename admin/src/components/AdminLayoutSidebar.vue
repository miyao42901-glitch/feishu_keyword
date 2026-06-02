<template>
  <div class="sidebar-root">
    <div class="brand">
      <span class="brand__title">飞书关键词</span>
      <span class="brand__sub">监控管理后台</span>
    </div>
    <div class="sidebar-menu-scroll">
      <el-menu
        ref="sidebarMenuRef"
        class="side-menu"
        router
        unique-opened
        :default-active="menuActive"
        background-color="transparent"
        text-color="#b8c5d6"
        active-text-color="#ffffff"
        @select="onMenuSelect"
      >
        <el-menu-item index="/dashboard">
          <span>工作台</span>
        </el-menu-item>

        <el-sub-menu index="data-root">
          <template #title>
            <span>数据</span>
          </template>
          <el-menu-item index="/data/overview">
            <span>数据概览</span>
          </el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="business-root">
          <template #title>
            <span>业务</span>
          </template>
          <el-menu-item index="/business/tasks">
            <span>任务管理</span>
          </el-menu-item>
          <el-menu-item index="/business/exec-monitor">
            <span>执行监控</span>
          </el-menu-item>
          <el-menu-item index="/business/api-monitor">
            <span>API 监控</span>
          </el-menu-item>
          <el-menu-item index="/business/push-monitor">
            <span>推送监控</span>
          </el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="operation-root">
          <template #title>
            <span>运营</span>
          </template>
          <el-menu-item index="/operation/users">
            <span>用户管理</span>
          </el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="keyword-root">
          <template #title>
            <span>关键词管理</span>
          </template>
          <el-menu-item index="/keyword/list">
            <span>关键词列表</span>
          </el-menu-item>
          <el-menu-item index="/keyword/group">
            <span>关键词分组</span>
          </el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="rule-root">
          <template #title>
            <span>监控规则</span>
          </template>
          <el-menu-item index="/rule/list">
            <span>规则列表</span>
          </el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="hit-root">
          <template #title>
            <span>命中记录</span>
          </template>
          <el-menu-item index="/hit/list">
            <span>命中列表</span>
          </el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="notify-root">
          <template #title>
            <span>通知配置</span>
          </template>
          <el-menu-item index="/notify/bot">
            <span>飞书机器人</span>
          </el-menu-item>
          <el-menu-item index="/notify/template">
            <span>通知模板</span>
          </el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="ops-root">
          <template #title>
            <span>运维</span>
          </template>
          <el-menu-item index="/ops/api-abnormal">
            <span>接口异常</span>
          </el-menu-item>
          <el-menu-item index="/ops/db-backup">
            <span>数据库备份</span>
          </el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="settings-root">
          <template #title>
            <span>系统设置</span>
          </template>
          <el-menu-item index="/settings/overview">
            <span>系统信息</span>
          </el-menu-item>
          <el-menu-item index="/settings/admins">
            <span>管理员账号</span>
          </el-menu-item>
          <el-menu-item index="/settings/logs">
            <span>操作日志</span>
          </el-menu-item>
        </el-sub-menu>
      </el-menu>
    </div>
    <div class="foot">
      <el-button type="danger" link @click="logout">退出</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import http from '@/api/http'
import { useSessionStore } from '@/stores/session'

function submenuRootForPath(path: string): string | null {
  if (path.startsWith('/data/')) return 'data-root'
  if (path.startsWith('/business/')) return 'business-root'
  if (path.startsWith('/operation/')) return 'operation-root'
  if (path.startsWith('/keyword/')) return 'keyword-root'
  if (path.startsWith('/rule/')) return 'rule-root'
  if (path.startsWith('/hit/')) return 'hit-root'
  if (path.startsWith('/notify/')) return 'notify-root'
  if (path.startsWith('/ops/')) return 'ops-root'
  if (path.startsWith('/settings/')) return 'settings-root'
  return null
}

const SUB_MENU_ROOTS = [
  'data-root',
  'business-root',
  'operation-root',
  'keyword-root',
  'rule-root',
  'hit-root',
  'notify-root',
  'ops-root',
  'settings-root',
] as const

type SidebarMenuExpose = { open: (index: string) => void; close: (index: string) => void }

interface Emits {
  (e: 'navigate'): void
}
const emit = defineEmits<Emits>()

const route = useRoute()
const router = useRouter()
const session = useSessionStore()

const sidebarMenuRef = ref<SidebarMenuExpose | null>(null)

function syncSubmenusWithRoute(): void {
  nextTick(() => {
    const m = sidebarMenuRef.value
    if (!m) return
    const keep = submenuRootForPath(route.path)
    for (const id of SUB_MENU_ROOTS) {
      if (id !== keep) {
        try {
          m.close(id)
        } catch {
          /* 子菜单未展开时 close 可能抛错，忽略 */
        }
      }
    }
    if (keep) {
      try {
        m.open(keep)
      } catch {
        /* 同上 */
      }
    }
  })
}

watch(() => route.path, syncSubmenusWithRoute)
onMounted(() => {
  syncSubmenusWithRoute()
})

const menuActive = computed(() => {
  if (route.path.startsWith('/dashboard')) {
    return '/dashboard'
  }
  if (route.path.startsWith('/data/overview')) {
    return '/data/overview'
  }
  if (route.path.startsWith('/business/tasks')) {
    return '/business/tasks'
  }
  if (route.path.startsWith('/business/exec-monitor')) {
    return '/business/exec-monitor'
  }
  if (route.path.startsWith('/business/api-monitor')) {
    return '/business/api-monitor'
  }
  if (route.path.startsWith('/business/push-monitor')) {
    return '/business/push-monitor'
  }
  if (route.path.startsWith('/operation/users')) {
    return '/operation/users'
  }
  if (route.path.startsWith('/keyword/list')) {
    return '/keyword/list'
  }
  if (route.path.startsWith('/keyword/group')) {
    return '/keyword/group'
  }
  if (route.path.startsWith('/rule/edit')) {
    return '/rule/list'
  }
  if (route.path.startsWith('/rule/list')) {
    return '/rule/list'
  }
  if (route.path.startsWith('/hit/') && route.path !== '/hit/list') {
    return '/hit/list'
  }
  if (route.path.startsWith('/hit/list')) {
    return '/hit/list'
  }
  if (route.path.startsWith('/notify/bot')) {
    return '/notify/bot'
  }
  if (route.path.startsWith('/notify/template')) {
    return '/notify/template'
  }
  if (route.path.startsWith('/ops/api-abnormal')) {
    return '/ops/api-abnormal'
  }
  if (route.path.startsWith('/ops/db-backup')) {
    return '/ops/db-backup'
  }
  if (route.path.startsWith('/settings/admins')) {
    return '/settings/admins'
  }
  if (route.path.startsWith('/settings/logs')) {
    return '/settings/logs'
  }
  if (route.path.startsWith('/settings/overview')) {
    return '/settings/overview'
  }
  if (route.path.startsWith('/settings')) {
    return '/settings/overview'
  }
  return route.path
})

function onMenuSelect() {
  emit('navigate')
}

async function logout() {
  try {
    await http.post('/api/admin/v1/system/logout')
  } catch {
    /* ignore */
  }
  session.clear()
  await router.replace('/login')
}
</script>

<style scoped>
.sidebar-root {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}
.brand {
  flex-shrink: 0;
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 8px 10px;
  padding: 20px 16px 18px;
  border-bottom: 1px solid var(--admin-sidebar-border);
  border-left: 3px solid var(--admin-brand);
  margin: 16px 12px 0;
  padding-left: 13px;
  border-radius: 0 8px 8px 0;
  background: rgba(255, 255, 255, 0.04);
}
.brand__title {
  font-size: 18px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 0.02em;
  flex-shrink: 0;
}
.brand__sub {
  font-size: 13px;
  color: #8fa3b8;
  font-weight: 500;
  white-space: nowrap;
}
.sidebar-menu-scroll {
  flex: 1;
  min-height: 0;
  overflow-x: hidden;
  overflow-y: auto;
  scrollbar-width: none;
  scrollbar-color: rgba(148, 163, 184, 0.45) transparent;
}
.sidebar-menu-scroll:hover {
  scrollbar-width: thin;
}
.sidebar-menu-scroll::-webkit-scrollbar {
  width: 0;
  height: 0;
}
.sidebar-menu-scroll:hover::-webkit-scrollbar {
  width: 8px;
  height: 0;
}
.sidebar-menu-scroll::-webkit-scrollbar-track {
  background: rgba(15, 23, 42, 0.2);
  border-radius: 4px;
}
.sidebar-menu-scroll::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.45);
  border-radius: 4px;
}
.sidebar-menu-scroll:hover::-webkit-scrollbar-thumb {
  background: rgba(186, 198, 214, 0.55);
}
.side-menu {
  border: none !important;
  border-right: none !important;
  padding: 12px 8px;
  --el-menu-bg-color: transparent;
  --el-menu-hover-bg-color: rgba(64, 115, 250, 0.12);
}
.side-menu :deep(.el-menu),
.side-menu :deep(.el-menu--vertical),
.side-menu :deep(.el-menu--inline) {
  background: transparent !important;
  border: none !important;
}
.side-menu :deep(.el-menu-item),
.side-menu :deep(.el-sub-menu__title) {
  border: none !important;
  border-radius: 8px;
  margin-bottom: 4px;
  background-color: transparent !important;
  box-shadow: none !important;
}
.side-menu :deep(.el-menu-item:hover) {
  background: rgba(64, 115, 250, 0.12) !important;
  color: #e8eef5 !important;
}
.side-menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(90deg, rgba(64, 115, 250, 0.35), rgba(64, 115, 250, 0.08)) !important;
  color: #fff !important;
  font-weight: 600;
}
.side-menu :deep(.el-sub-menu__title) {
  color: #b8c5d6 !important;
}
.side-menu :deep(.el-sub-menu__title:hover) {
  background: rgba(64, 115, 250, 0.12) !important;
  color: #e8eef5 !important;
}
.side-menu :deep(.el-sub-menu.is-active > .el-sub-menu__title) {
  color: #e8eef5 !important;
}
.side-menu :deep(.el-menu--inline .el-menu-item) {
  padding-left: 44px !important;
  min-width: 0;
}
.foot {
  flex-shrink: 0;
  padding: 12px 16px 16px;
  border-top: 1px solid var(--admin-sidebar-border);
}
.foot :deep(.el-button) {
  color: #b8c5d6;
}
.foot :deep(.el-button:hover) {
  color: #ff6b6b;
}
</style>

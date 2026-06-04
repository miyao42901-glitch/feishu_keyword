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
        <template v-for="group in menuConfig.enabledGroups" :key="group.key">
          <el-sub-menu :index="group.key">
            <template #title>
              <span>{{ group.label }}</span>
            </template>
            <el-menu-item
              v-for="item in group.children"
              :key="item.key"
              :index="item.key"
            >
              <span>{{ item.label }}</span>
            </el-menu-item>
          </el-sub-menu>
        </template>
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
import { useMenuConfigStore } from '@/stores/menuConfig'

type SidebarMenuExpose = { open: (index: string) => void; close: (index: string) => void }

interface Emits {
  (e: 'navigate'): void
}
const emit = defineEmits<Emits>()

const route = useRoute()
const router = useRouter()
const session = useSessionStore()
const menuConfig = useMenuConfigStore()

const sidebarMenuRef = ref<SidebarMenuExpose | null>(null)

function submenuRootForPath(path: string): string | null {
  for (const group of menuConfig.groups) {
    if (group.children.some((c) => path.startsWith(c.key))) {
      return group.key
    }
  }
  return null
}

function syncSubmenusWithRoute(): void {
  nextTick(() => {
    const m = sidebarMenuRef.value
    if (!m) return
    const keep = submenuRootForPath(route.path)
    for (const group of menuConfig.groups) {
      if (group.key !== keep) {
        try {
          m.close(group.key)
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
  for (const group of menuConfig.groups) {
    for (const item of group.children) {
      if (route.path.startsWith(item.key) || route.path === item.key) {
        return item.key
      }
    }
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

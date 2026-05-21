<template>
  <el-container class="layout" :class="{ 'layout--mobile': isMobile }">
    <el-aside v-if="!isMobile" width="220px" class="aside">
      <AdminLayoutSidebar />
    </el-aside>

    <template v-if="isMobile">
      <div
        class="mobile-mask"
        :class="{ 'mobile-mask--visible': mobileMenuOpen }"
        aria-hidden="true"
        @click="mobileMenuOpen = false"
      />
      <div class="aside aside--mobile" :class="{ 'aside--mobile-open': mobileMenuOpen }">
        <AdminLayoutSidebar @navigate="mobileMenuOpen = false" />
      </div>
    </template>

    <el-main class="main">
      <header v-if="isMobile" class="mobile-topbar">
        <button type="button" class="mobile-topbar__menu" aria-label="打开菜单" @click="mobileMenuOpen = true">
          <svg class="mobile-topbar__icon" viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">
            <path fill="currentColor" d="M4 6h16v2H4V6zm0 5h16v2H4v-2zm0 5h16v2H4v-2z" />
          </svg>
        </button>
        <span class="mobile-topbar__title">飞书关键词监控</span>
      </header>
      <div class="main-inner">
        <router-view />
      </div>
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import AdminLayoutSidebar from '@/components/AdminLayoutSidebar.vue'
import { useAdminMobileLayout } from '@/composables/useAdminMobileLayout'

const route = useRoute()
const { isMobile } = useAdminMobileLayout()
const mobileMenuOpen = ref(false)

watch(isMobile, (v) => {
  if (!v) {
    mobileMenuOpen.value = false
  }
})

watch(
  () => route.fullPath,
  () => {
    mobileMenuOpen.value = false
  },
)
</script>

<style scoped>
.layout {
  height: 100vh;
  height: 100dvh;
}
.aside {
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: var(--admin-sidebar-bg);
  border-right: 1px solid var(--admin-sidebar-border);
  box-shadow: 4px 0 24px rgba(15, 23, 42, 0.12);
}
.aside--mobile {
  position: fixed;
  left: 0;
  top: 0;
  z-index: 3000;
  width: min(288px, 88vw);
  height: 100vh;
  height: 100dvh;
  max-height: 100dvh;
  transform: translateX(-100%);
  transition: transform 0.28s ease;
  overflow: hidden;
  -webkit-overflow-scrolling: touch;
}
.aside--mobile.aside--mobile-open {
  transform: translateX(0);
}
.mobile-mask {
  position: fixed;
  inset: 0;
  z-index: 2999;
  background: rgba(15, 23, 42, 0.45);
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.2s ease, visibility 0.2s ease;
}
.mobile-mask--visible {
  opacity: 1;
  visibility: visible;
}
.main {
  background: linear-gradient(180deg, #f0f4f8 0%, #e8eef5 100%);
  padding: 0;
  overflow: auto;
  min-width: 0;
}
.main-inner {
  min-height: 100%;
  padding: 20px 24px 32px;
  box-sizing: border-box;
}
.layout--mobile .main-inner {
  padding: 12px 14px 28px;
}
.mobile-topbar {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 4px 14px;
  margin: 0 0 4px;
  background: linear-gradient(180deg, rgba(240, 244, 248, 0.96) 70%, rgba(240, 244, 248, 0));
  backdrop-filter: blur(8px);
}
.mobile-topbar__menu {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  padding: 0;
  border: 1px solid rgba(26, 35, 50, 0.12);
  border-radius: 10px;
  background: #fff;
  color: #1a2332;
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
}
.mobile-topbar__menu:hover {
  border-color: var(--admin-brand);
  color: var(--admin-brand);
}
.mobile-topbar__icon {
  display: block;
}
.mobile-topbar__title {
  font-size: 16px;
  font-weight: 600;
  color: #1a2332;
  letter-spacing: 0.02em;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>

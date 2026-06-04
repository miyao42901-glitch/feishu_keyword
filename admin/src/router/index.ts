import { createRouter, createWebHistory } from 'vue-router'
import { useSessionStore } from '@/stores/session'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue') },
    {
      path: '/',
      component: () => import('@/views/LayoutView.vue'),
      meta: { requiresAuth: true },
      children: [
        { path: '', redirect: '/data/overview' },
        {
          path: 'data/overview',
          name: 'data-overview',
          component: () => import('@/views/data/DataOverviewView.vue'),
        },
        {
          path: 'business/tasks',
          name: 'business-tasks',
          component: () => import('@/views/business/TaskManageView.vue'),
        },
        {
          path: 'business/exec-monitor',
          name: 'business-exec-monitor',
          component: () => import('@/views/business/ExecMonitorView.vue'),
        },
        {
          path: 'business/api-monitor',
          name: 'business-api-monitor',
          component: () => import('@/views/business/ApiMonitorView.vue'),
        },
        {
          path: 'business/push-monitor',
          name: 'business-push-monitor',
          component: () => import('@/views/business/PushMonitorView.vue'),
        },
        {
          path: 'operation/users',
          name: 'operation-users',
          component: () => import('@/views/operation/UserManageView.vue'),
        },
        {
          path: 'notify/template',
          name: 'notify-template',
          component: () => import('@/views/notify/NotifyTemplateView.vue'),
        },
        {
          path: 'ops/api-abnormal',
          name: 'ops-api-abnormal',
          component: () => import('@/views/ops/ApiAbnormalView.vue'),
        },
        {
          path: 'ops/db-backup',
          name: 'ops-db-backup',
          component: () => import('@/views/ops/DbBackupView.vue'),
        },
        {
          path: 'settings/overview',
          name: 'settings-overview',
          component: () => import('@/views/settings/SettingsOverviewView.vue'),
        },
        {
          path: 'settings/admins',
          name: 'settings-admins',
          component: () => import('@/views/settings/SettingsAdminsView.vue'),
        },
        {
          path: 'settings/logs',
          name: 'settings-logs',
          component: () => import('@/views/settings/SettingsLogsView.vue'),
        },
      ],
    },
  ],
})

router.beforeEach((to) => {
  const s = useSessionStore()
  if (to.meta.requiresAuth && !s.token) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.name === 'login' && s.token) {
    return { path: '/' }
  }
  return true
})

export default router

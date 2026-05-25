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
        { path: '', redirect: '/dashboard' },
        {
          path: 'dashboard',
          name: 'dashboard',
          component: () => import('@/views/DashboardView.vue'),
        },
        {
          path: 'keyword/list',
          name: 'keyword-list',
          component: () => import('@/views/keyword/KeywordListView.vue'),
        },
        {
          path: 'keyword/group',
          name: 'keyword-group',
          component: () => import('@/views/keyword/KeywordGroupView.vue'),
        },
        {
          path: 'rule/list',
          name: 'rule-list',
          component: () => import('@/views/rule/RuleListView.vue'),
        },
        {
          path: 'rule/edit/:id',
          name: 'rule-edit',
          component: () => import('@/views/rule/RuleEditView.vue'),
          props: true,
        },
        {
          path: 'hit/list',
          name: 'hit-list',
          component: () => import('@/views/hit/HitListView.vue'),
        },
        {
          path: 'hit/:id',
          name: 'hit-detail',
          component: () => import('@/views/hit/HitDetailView.vue'),
          props: true,
        },
        {
          path: 'notify/bot',
          name: 'notify-bot',
          component: () => import('@/views/notify/NotifyBotView.vue'),
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

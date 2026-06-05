import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface MenuItemConfig {
  key: string
  label: string
  enabled: boolean
}

export interface MenuGroupConfig {
  key: string
  label: string
  enabled: boolean
  children: MenuItemConfig[]
}

const STORAGE_KEY = 'fkw_admin_menu_config'

const DEFAULT_MENU_GROUPS: MenuGroupConfig[] = [
  {
    key: 'data-root',
    label: '数据',
    enabled: true,
    children: [{ key: '/data/overview', label: '数据概览', enabled: true }],
  },
  {
    key: 'business-root',
    label: '业务',
    enabled: true,
    children: [
      { key: '/business/tasks', label: '任务管理', enabled: true },
      { key: '/business/exec-monitor', label: '执行监控', enabled: true },
      { key: '/business/api-monitor', label: 'API 监控', enabled: true },
      { key: '/business/push-monitor', label: '推送监控', enabled: true },
    ],
  },
  {
    key: 'operation-root',
    label: '运营',
    enabled: true,
    children: [{ key: '/operation/users', label: '用户管理', enabled: true }],
  },
  {
    key: 'notify-root',
    label: '通知配置',
    enabled: true,
    children: [{ key: '/notify/template', label: '通知模板', enabled: true }],
  },
  {
    key: 'ops-root',
    label: '运维',
    enabled: true,
    children: [
      { key: '/ops/api-abnormal', label: '接口异常', enabled: true },
      { key: '/ops/db-backup', label: '数据库备份', enabled: true },
    ],
  },
  {
    key: 'settings-root',
    label: '系统设置',
    enabled: true,
    children: [
      { key: '/settings/overview', label: '系统信息', enabled: true },
      { key: '/settings/admins', label: '管理员账号', enabled: true },
      { key: '/settings/logs', label: '操作日志', enabled: true },
      { key: '/settings/menu', label: '菜单管理', enabled: true },
    ],
  },
]

function loadFromStorage(): MenuGroupConfig[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return structuredClone(DEFAULT_MENU_GROUPS)
    const saved: MenuGroupConfig[] = JSON.parse(raw)
    // merge: keep default structure, overlay saved enabled states
    return DEFAULT_MENU_GROUPS.map((defaultGroup) => {
      const savedGroup = saved.find((g) => g.key === defaultGroup.key)
      return {
        ...defaultGroup,
        enabled: savedGroup ? savedGroup.enabled : defaultGroup.enabled,
        children: defaultGroup.children.map((defaultItem) => {
          const savedItem = savedGroup?.children.find((c) => c.key === defaultItem.key)
          return {
            ...defaultItem,
            enabled: savedItem ? savedItem.enabled : defaultItem.enabled,
          }
        }),
      }
    })
  } catch {
    return structuredClone(DEFAULT_MENU_GROUPS)
  }
}

export const useMenuConfigStore = defineStore('menuConfig', () => {
  const groups = ref<MenuGroupConfig[]>(loadFromStorage())
  
  const LOCKED_GROUPS = new Set(['settings-root'])

  function save() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(groups.value))
  }

  function setGroupEnabled(groupKey: string, enabled: boolean) {
    if (LOCKED_GROUPS.has(groupKey)) return
    const g = groups.value.find((g) => g.key === groupKey)
    if (g) {
      g.enabled = enabled
      save()
    }
  }

  function setItemEnabled(groupKey: string, itemKey: string, enabled: boolean) {
    const g = groups.value.find((g) => g.key === groupKey)
    if (g) {
      const item = g.children.find((c) => c.key === itemKey)
      if (item) {
        item.enabled = enabled
        save()
      }
    }
  }

  function resetToDefault() {
    groups.value = structuredClone(DEFAULT_MENU_GROUPS)
    save()
  }

  const enabledGroups = computed(() =>
    groups.value
      .filter((g) => g.enabled)
      .map((g) => ({
        ...g,
        children: g.children.filter((c) => c.enabled),
      })),
  )

  const LOCKED_ITEMS = new Set(['/settings/menu'])

  function isItemVisible(itemKey: string): boolean {
    if (LOCKED_ITEMS.has(itemKey)) return true
    for (const g of groups.value) {
      if (!g.enabled) continue
      const item = g.children.find((c) => c.key === itemKey)
      if (item) return item.enabled
    }
    return false
  }

  return { groups, enabledGroups, setGroupEnabled, setItemEnabled, resetToDefault, isItemVisible }
})

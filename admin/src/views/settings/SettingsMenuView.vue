<template>
  <div class="settings-menu">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <h3 class="card-title">菜单管理</h3>
          <el-button type="primary" size="small" @click="handleReset">恢复默认</el-button>
        </div>
      </template>

      <div class="menu-config-list">
        <div v-for="group in menuStore.groups" :key="group.key" class="menu-group">
          <div class="group-header">
            <el-switch
              :model-value="group.enabled"
              @change="(val) => menuStore.setGroupEnabled(group.key, val as boolean)"
              class="group-switch"
            />
            <span class="group-label">{{ group.label }}</span>
            <span class="group-count">({{ group.children.length }} 项)</span>
          </div>

          <div v-if="group.enabled" class="group-items">
            <div
              v-for="item in group.children"
              :key="item.key"
              class="menu-item"
              :class="{ disabled: !item.enabled }"
            >
              <el-switch
                :model-value="item.enabled"
                @change="(val) => menuStore.setItemEnabled(group.key, item.key, val as boolean)"
                :disabled="item.key === '/settings/menu'"
                size="small"
              />
              <span class="item-label">{{ item.label }}</span>
              <span v-if="item.key === '/settings/menu'" class="item-lock">
                <el-icon><Lock /></el-icon>
              </span>
            </div>
          </div>
        </div>
      </div>

      <el-alert
        type="info"
        :closable="false"
        show-icon
        class="tips-alert"
        title="提示"
      >
        <p>• 关闭某个菜单分组将隐藏该分组下的所有子菜单</p>
        <p>• 菜单管理页面本身不可被隐藏</p>
        <p>• 配置实时生效，刷新页面后保持</p>
      </el-alert>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ElMessageBox, ElMessage } from 'element-plus'
import { Lock } from '@element-plus/icons-vue'
import { useMenuConfigStore } from '@/stores/menuConfig'

const menuStore = useMenuConfigStore()

async function handleReset() {
  try {
    await ElMessageBox.confirm('确定要恢复到默认菜单配置吗？', '确认操作', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    menuStore.resetToDefault()
    ElMessage.success('已恢复默认配置')
  } catch {
    /* 用户取消 */
  }
}
</script>

<style scoped>
.settings-menu {
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-title {
  margin: 0;
  font-size: 18px;
  color: var(--el-text-color-primary);
}

.menu-config-list {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.menu-group {
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  padding: 16px;
  background: var(--el-fill-color-blank);
  transition: all 0.2s;
}

.menu-group:hover {
  border-color: var(--el-border-color);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.group-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.group-switch {
  flex-shrink: 0;
}

.group-label {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.group-count {
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.group-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-left: 8px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 6px;
  background: var(--el-fill-color-lighter);
  transition: all 0.2s;
}

.menu-item:hover {
  background: var(--el-fill-color-light);
}

.menu-item.disabled {
  opacity: 0.5;
}

.item-label {
  flex: 1;
  font-size: 14px;
  color: var(--el-text-color-regular);
}

.item-lock {
  display: flex;
  align-items: center;
  color: var(--el-color-warning);
  font-size: 14px;
}

.tips-alert {
  margin-top: 24px;
}

.tips-alert :deep(.el-alert__content) p {
  margin: 4px 0;
  line-height: 1.6;
}
</style>

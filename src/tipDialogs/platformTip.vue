<template>
  <el-dialog
    v-model="dialogVisible"
    width="400px"
    :close-on-click-modal="true"
    class="help-dialog"
  >
    <template #header>
      <div class="dialog-header">
        <img src="/icon/help-icon.png" srcset="/icon/help-icon@2x.png 2x" alt="帮助图标" class="header-icon-img" />
        <span class="header-title">如何获取{{ platformName }}"采集账号"?</span>
      </div>
    </template>
    
    <div class="help-content">
      <div class="help-section">
        <p class="help-text">方式一：直接复制并粘贴</p>
        <div class="help-image-placeholder">
          <span class="placeholder-text">(测试版截图真实场景)</span>
        </div>
      </div>
      
      <div class="help-section">
        <p class="help-text">方式二：下拉选择带有"{{ accountFieldName }}"字段的表格，一次性选择多个账号</p>
        <div class="help-image-placeholder">
          <span class="placeholder-text">(测试版截图真实场景)</span>
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'

const emit = defineEmits(['update:visible'])
const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  platformName: {
    type: String,
    default: '抖音'
  },
  accountFieldName: {
    type: String,
    default: '抖音账号ID'
  }
})

const dialogVisible = ref(props.visible)

watch(() => props.visible, (newVal) => {
  dialogVisible.value = newVal
})

watch(dialogVisible, (newVal) => {
  emit('update:visible', newVal)
})
</script>

<style scoped>
.help-dialog :deep(.el-dialog) {
  border-radius: 8px;
}

.help-dialog :deep(.el-dialog__header) {
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
}

.dialog-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-icon-img {
  width: 20px;
  height: 20px;
  object-fit: contain;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.help-dialog :deep(.el-dialog__body) {
  padding: 20px;
}

.help-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.help-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.help-text {
  font-size: 14px;
  color: #374151;
  line-height: 1.6;
  margin: 0;
}

.help-image-placeholder {
  width: 100%;
  height: 180px;
  background-color: #d1d5db;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.placeholder-text {
  font-size: 13px;
  color: #6b7280;
}
</style>

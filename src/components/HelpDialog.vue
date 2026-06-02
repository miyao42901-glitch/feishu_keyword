<template>
  <el-dialog
    v-model="dialogVisible"
    :title="title"
    width="400px"
    :close-on-click-modal="true"
    :close-on-press-escape="true"
    class="help-dialog"
  >
    <div class="help-content">
      <div v-for="(section, index) in sections" :key="index" class="help-section">
        <p class="help-text">{{ section.text }}</p>
        <div v-if="section.image" class="help-image-placeholder">
          <span class="placeholder-text">{{ section.placeholder || '(测试版截图真实场景)' }}</span>
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElDialog } from 'element-plus'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: ''
  },
  sections: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:visible'])

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

.help-dialog :deep(.el-dialog__title) {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  display: flex;
  align-items: center;
}

.help-dialog :deep(.el-dialog__title)::before {
  content: '💡';
  margin-right: 8px;
  font-size: 18px;
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

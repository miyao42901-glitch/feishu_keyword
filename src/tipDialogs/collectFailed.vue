<template>
  <el-dialog
    v-model="dialogVisible"
    width="378px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    class="collect-failed-dialog"
    :show-close="true"
  >
    <div class="dialog-title">
      <img
        src="/icon/collect-failed-icon.png"
        srcset="/icon/collect-failed-icon@2x.png 2x"
        alt="采集失败"
        class="error-icon-img"
      />
      <span class="title-text">采集失败</span>
    </div>

    <p class="dialog-message">{{ networkErrorMessage }}</p>

    <template #footer>
      <span class="dialog-footer">
        <el-button class="close-btn" @click="dialogVisible = false">关闭</el-button>
        <el-button class="retry-btn" @click="handleRetry">重试</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { NETWORK_ERROR_MESSAGE } from '@/utils/errorMessage'

const emit = defineEmits(['update:visible', 'retry'])

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
})

const networkErrorMessage = NETWORK_ERROR_MESSAGE
const dialogVisible = ref(props.visible)

const handleRetry = () => {
  dialogVisible.value = false
  emit('retry')
}

watch(() => props.visible, (newVal) => {
  dialogVisible.value = newVal
})

watch(dialogVisible, (newVal) => {
  emit('update:visible', newVal)
})
</script>

<style scoped>
.collect-failed-dialog :deep(.el-dialog) {
  border-radius: 8px;
  overflow: hidden;
}

.collect-failed-dialog :deep(.el-dialog__header) {
  padding: 0;
  margin: 0;
}

.collect-failed-dialog :deep(.el-dialog__headerbtn) {
  top: 16px;
  right: 16px;
}

.collect-failed-dialog :deep(.el-dialog__body) {
  padding: 20px 32px 0;
}

.collect-failed-dialog :deep(.el-dialog__footer) {
  padding: 0 32px 32px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.dialog-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.error-icon-img {
  width: 24px;
  height: 24px;
  object-fit: contain;
  flex-shrink: 0;
}

.title-text {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.dialog-message {
  margin: 25px 0 32px;
  font-size: 14px;
  line-height: 1.6;
  color: #374151;
}

.close-btn {
  border-radius: 8px;
  border-color: #d1d5db;
  color: #374151;
  background-color: #ffffff;
}

.close-btn:hover {
  border-color: #9ca3af;
  color: #1f2937;
  background-color: #ffffff;
}

.retry-btn {
  border-radius: 8px;
  background-color: #0e1e3d !important;
  border-color: #0e1e3d !important;
  color: #ffffff !important;
}

.retry-btn:hover {
  background-color: #1a2f58 !important;
  border-color: #1a2f58 !important;
}

.retry-btn:active {
  transform: scale(0.97);
}
</style>

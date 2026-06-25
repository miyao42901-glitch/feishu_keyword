<script setup lang="ts">
/**
 * 保存前「确认任务配置」：配置摘要；单次为「立即执行」，定时为「开始执行」。
 */
import { Close } from '@element-plus/icons-vue'
import type { TaskConfigConfirmRow } from '@/views/TaskCreateForm/build-preview-rows'

defineOptions({ name: 'TaskConfigConfirmDialog' })

defineProps<{
  rows: TaskConfigConfirmRow[]
  confirming: boolean
  /** 单次任务：主按钮文案为「立即执行」 */
  isRealtimeTask?: boolean
}>()

const visible = defineModel<boolean>({ required: true })

const emit = defineEmits<{
  confirm: []
}>()

function handleClose() {
  visible.value = false
}
</script>

<template>
  <el-dialog
    v-model="visible"
    width="92%"
    align-center
    append-to-body
    destroy-on-close
    class="task-config-confirm-dialog"
    :close-on-click-modal="false"
    :show-close="false"
  >
    <template #header>
      <div class="task-config-confirm-dialog__header">
        <span class="task-config-confirm-dialog__title">确认任务配置</span>
        <button
          type="button"
          class="task-config-confirm-dialog__close"
          aria-label="关闭"
          :disabled="confirming"
          @click="handleClose"
        >
          <el-icon :size="14"><Close /></el-icon>
        </button>
      </div>
    </template>

    <div class="task-config-confirm-dialog__fields">
      <div
        v-for="(row, idx) in rows"
        :key="idx"
        class="task-config-confirm-dialog__field"
        :class="{
          'task-config-confirm-dialog__field--span':
            row.label === '目标表格' || row.label === 'Webhook地址',
        }"
      >
        <p class="task-config-confirm-dialog__label">{{ row.label }}</p>
        <p class="task-config-confirm-dialog__value">{{ row.value }}</p>
      </div>
    </div>

    <template #footer>
      <div class="task-config-confirm-dialog__footer">
        <button
          type="button"
          class="task-config-confirm-dialog__btn task-config-confirm-dialog__btn--cancel"
          :disabled="confirming"
          @click="handleClose"
        >
          取消
        </button>
        <button
          type="button"
          class="task-config-confirm-dialog__btn task-config-confirm-dialog__btn--primary"
          :disabled="confirming"
          @click="emit('confirm')"
        >
          {{
            confirming ? '提交中…' : isRealtimeTask ? '立即执行' : '开始执行'
          }}
        </button>
      </div>
    </template>
  </el-dialog>
</template>

<style scoped>
.task-config-confirm-dialog__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.task-config-confirm-dialog__title {
  font-size: 16px;
  font-weight: 500;
  line-height: 1.4;
  color: #0f1114;
  text-align: left;
  font-style: normal;
  text-transform: none;
}

.task-config-confirm-dialog__close {
  box-sizing: border-box;
  display: inline-flex;
  width: 24px;
  height: 24px;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  margin: 0;
  padding: 0;
  border: 1px dashed #c9cdd4;
  border-radius: 2px;
  background: transparent;
  color: #8f959e;
  cursor: pointer;
}

.task-config-confirm-dialog__close:hover:not(:disabled) {
  color: #646a73;
  border-color: #bbbfc4;
}

.task-config-confirm-dialog__close:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.task-config-confirm-dialog__fields {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px 20px;
}

.task-config-confirm-dialog__field {
  margin: 0;
  min-width: 0;
}

.task-config-confirm-dialog__field--span {
  grid-column: 1 / -1;
}

.task-config-confirm-dialog__label {
  margin: 0 0 2px;
  font-size: 12px;
  font-weight: 400;
  line-height: 1.4;
  color: #646a73;
  text-align: left;
  font-style: normal;
  text-transform: none;
}

.task-config-confirm-dialog__value {
  margin: 0;
  font-size: 14px;
  font-weight: 400;
  line-height: 1.45;
  color: #0f1114;
  text-align: left;
  font-style: normal;
  text-transform: none;
  word-break: break-word;
  overflow-wrap: anywhere;
}

.task-config-confirm-dialog__footer {
  display: flex;
  width: 100%;
  gap: 12px;
}

.task-config-confirm-dialog__btn {
  box-sizing: border-box;
  display: inline-flex;
  min-width: 0;
  height: 46px;
  flex: 1 1 0;
  align-items: center;
  justify-content: center;
  margin: 0;
  padding: 0 16px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  line-height: 1;
  cursor: pointer;
  transition:
    opacity 0.15s ease,
    border-color 0.15s ease;
}

.task-config-confirm-dialog__btn:disabled {
  cursor: not-allowed;
  opacity: 0.65;
}

.task-config-confirm-dialog__btn--cancel {
  border: 1px solid #dee0e3;
  background: #ffffff;
  color: #0f1114;
}

.task-config-confirm-dialog__btn--cancel:hover:not(:disabled) {
  border-color: #bbbfc4;
}

.task-config-confirm-dialog__btn--primary {
  border: none;
  background-image: linear-gradient(90deg, #1456f0 0%, #4014f0 100%);
  color: #ffffff;
}

.task-config-confirm-dialog__btn--primary:hover:not(:disabled) {
  background-image: linear-gradient(90deg, #1a5df8 0%, #4d22f5 100%);
}
</style>

<style>
.task-config-confirm-dialog.el-dialog {
  width: min(560px, calc(100vw - 24px)) !important;
  max-width: calc(100vw - 16px);
  border-radius: 8px;
  background: #ffffff;
}

.task-config-confirm-dialog .el-dialog__header {
  margin-right: 0;
  padding: 16px 20px 12px;
}

.task-config-confirm-dialog .el-dialog__body {
  padding: 0 20px 4px;
  overflow: visible;
  max-height: none;
}

.task-config-confirm-dialog .el-dialog__footer {
  padding: 12px 20px 16px;
}
</style>

<script setup lang="ts">
/**
 * 保存前「确认任务配置」：配置摘要、预估积分与当前积分；单次为「立即执行」，定时为「开始执行」。
 */
import { Close } from '@element-plus/icons-vue'
import { computed } from 'vue'
import type { TaskConfigConfirmRow } from '@/views/TaskCreateForm/build-preview-rows'

defineOptions({ name: 'TaskConfigConfirmDialog' })

const props = defineProps<{
  rows: TaskConfigConfirmRow[]
  estimatedPoints: number
  balancePoints: number
  /** 定时任务：监控窗口内预计采集轮次 */
  scheduledExecutionRounds?: number
  confirming: boolean
  /** 单次任务：主按钮文案为「立即执行」 */
  isRealtimeTask?: boolean
}>()

/** 当前积分低于预估消耗上限时不允许提交 */
const pointsInsufficient = computed(
  () => props.estimatedPoints > 0 && props.balancePoints < props.estimatedPoints,
)

const visible = defineModel<boolean>({ required: true })

const emit = defineEmits<{
  confirm: []
  /** 积分不足时联系客服充值 */
  recharge: []
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
      <div v-for="(row, idx) in rows" :key="idx" class="task-config-confirm-dialog__field">
        <p class="task-config-confirm-dialog__label">{{ row.label }}</p>
        <p class="task-config-confirm-dialog__value">{{ row.value }}</p>
      </div>
    </div>

    <div class="task-config-confirm-dialog__points">
      <div class="task-config-confirm-dialog__points-row">
        <span class="task-config-confirm-dialog__points-label">预估消耗（上限）</span>
        <span class="task-config-confirm-dialog__points-value">
          <span class="task-config-confirm-dialog__points-num">{{
            estimatedPoints.toLocaleString('zh-CN')
          }}</span>
          <span class="task-config-confirm-dialog__points-unit">积分</span>
        </span>
      </div>
      <p class="task-config-confirm-dialog__points-hint">
        <template v-if="scheduledExecutionRounds != null && scheduledExecutionRounds > 1">
          定时任务预计在监控期内采集 {{ scheduledExecutionRounds }} 轮（自开始后每隔采集频率执行，结束时刻可能补采一轮）；预估积分已按轮次累加。
        </template>
        按各平台、每轮实采条数扣费：未凑满选择条数时会继续翻页；实采不足时按实际返回条数计费。
      </p>
      <div class="task-config-confirm-dialog__points-row">
        <span class="task-config-confirm-dialog__points-label">当前积分</span>
        <span class="task-config-confirm-dialog__points-value">
          <span
            class="task-config-confirm-dialog__points-num"
            :class="{ 'task-config-confirm-dialog__points-num--warn': pointsInsufficient }"
          >{{
            balancePoints.toLocaleString('zh-CN')
          }}</span>
          <span class="task-config-confirm-dialog__points-unit">积分</span>
        </span>
      </div>
      <div v-if="pointsInsufficient" class="task-config-confirm-dialog__insufficient">
        <p class="task-config-confirm-dialog__points-warn" role="alert">点数不足，请先充值</p>
        <button
          type="button"
          class="task-config-confirm-dialog__recharge-link"
          @click="emit('recharge')"
        >
          联系客服充值
        </button>
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
          :disabled="confirming || pointsInsufficient"
          :title="pointsInsufficient ? '点数不足，请先充值' : undefined"
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
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.task-config-confirm-dialog__field {
  margin: 0;
}

.task-config-confirm-dialog__label {
  margin: 0 0 4px;
  font-size: 12px;
  font-weight: 400;
  line-height: 1.5;
  color: #646a73;
  text-align: left;
  font-style: normal;
  text-transform: none;
}

.task-config-confirm-dialog__value {
  margin: 0;
  font-size: 14px;
  font-weight: 400;
  line-height: 1.5;
  color: #0f1114;
  text-align: left;
  font-style: normal;
  text-transform: none;
  word-break: break-all;
}

.task-config-confirm-dialog__points {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 24px;
  padding: 14px 16px;
  border-radius: 8px;
  background: #f8f9fa;
}

.task-config-confirm-dialog__points-hint {
  margin: 0;
  font-size: 12px;
  line-height: 1.5;
  color: #646a73;
}

.task-config-confirm-dialog__points-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.task-config-confirm-dialog__points-label {
  font-size: 14px;
  font-weight: 400;
  line-height: 1.5;
  color: #0f1114;
}

.task-config-confirm-dialog__points-value {
  display: inline-flex;
  align-items: baseline;
  gap: 2px;
}

.task-config-confirm-dialog__points-num {
  font-size: 14px;
  font-weight: 500;
  line-height: 1.5;
  color: #1f22f6;
}

.task-config-confirm-dialog__points-num--warn {
  color: #d83931;
}

.task-config-confirm-dialog__insufficient {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
}

.task-config-confirm-dialog__points-warn {
  margin: 0;
  font-size: 12px;
  line-height: 1.5;
  color: #d83931;
}

.task-config-confirm-dialog__recharge-link {
  margin: 0;
  padding: 0;
  border: none;
  background: transparent;
  font-size: 12px;
  font-weight: 500;
  line-height: 1.5;
  color: #1f22f6;
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 2px;
}

.task-config-confirm-dialog__recharge-link:hover {
  color: #1456f0;
}

.task-config-confirm-dialog__points-unit {
  font-size: 14px;
  font-weight: 400;
  line-height: 1.5;
  color: #0f1114;
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
  width: min(520px, calc(100vw - 24px)) !important;
  max-width: calc(100vw - 16px);
  border-radius: 8px;
  background: #ffffff;
}

.task-config-confirm-dialog .el-dialog__header {
  margin-right: 0;
  padding: 20px 20px 16px;
}

.task-config-confirm-dialog .el-dialog__body {
  padding: 0 20px 4px;
}

.task-config-confirm-dialog .el-dialog__footer {
  padding: 16px 20px 20px;
}
</style>

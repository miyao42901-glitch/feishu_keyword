<script setup lang="ts">
/**
 * 单次采集完成：展示采集条数、本次消耗与剩余余额（定时任务不弹出）。
 */
import { Close } from '@element-plus/icons-vue'
import type { CollectionSuccessSummary } from '@/lib/task-estimate-points'
import { formatPointsBalance } from '@/lib/account-balance'
import { collectionSuccessIconSrc } from '@/views/tasks/task-status-media'

defineOptions({ name: 'CollectionSuccessDialog' })

defineProps<{
  summary: CollectionSuccessSummary | null
}>()

const visible = defineModel<boolean>({ required: true })

const emit = defineEmits<{
  viewCollection: []
}>()

function handleClose() {
  visible.value = false
}

function handleViewCollection() {
  visible.value = false
  emit('viewCollection')
}
</script>

<template>
  <el-dialog
    v-model="visible"
    width="min(400px, 92vw)"
    align-center
    append-to-body
    destroy-on-close
    class="collection-success-dialog"
    :show-close="false"
    :close-on-click-modal="false"
  >
    <template #header>
      <div class="collection-success-dialog__header">
        <div class="collection-success-dialog__title-wrap">
          <span class="collection-success-dialog__icon" aria-hidden="true">
            <img
              class="collection-success-dialog__icon-img"
              :src="collectionSuccessIconSrc"
              alt=""
              decoding="async"
            />
          </span>
          <span class="collection-success-dialog__title">采集成功</span>
        </div>
        <button
          type="button"
          class="collection-success-dialog__close"
          aria-label="关闭"
          @click="handleClose"
        >
          <el-icon :size="14"><Close /></el-icon>
        </button>
      </div>
    </template>

    <div v-if="summary" class="collection-success-dialog__panel">
      <div class="collection-success-dialog__row">
        <span class="collection-success-dialog__label">采集文章</span>
        <span class="collection-success-dialog__value">{{ summary.articleCount }}条</span>
      </div>
      <div class="collection-success-dialog__row">
        <span class="collection-success-dialog__label">本次消耗</span>
        <span class="collection-success-dialog__value"
          >{{ formatPointsBalance(summary.consumptionPoints) }}</span
        >
      </div>
      <div class="collection-success-dialog__row">
        <span class="collection-success-dialog__label">剩余余额</span>
        <span class="collection-success-dialog__value"
          >{{ formatPointsBalance(summary.balancePoints) }}</span
        >
      </div>
    </div>

    <template #footer>
      <div class="collection-success-dialog__footer">
        <button
          type="button"
          class="collection-success-dialog__btn collection-success-dialog__btn--ghost"
          @click="handleClose"
        >
          关闭
        </button>
        <button
          type="button"
          class="collection-success-dialog__btn collection-success-dialog__btn--primary"
          @click="handleViewCollection"
        >
          查看采集
        </button>
      </div>
    </template>
  </el-dialog>
</template>

<style scoped>
.collection-success-dialog__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.collection-success-dialog__title-wrap {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.collection-success-dialog__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  flex-shrink: 0;
}

.collection-success-dialog__icon-img {
  display: block;
  width: 28px;
  height: 28px;
  object-fit: contain;
}

.collection-success-dialog__title {
  font-size: 16px;
  font-weight: 500;
  line-height: 1.4;
  color: #0f1114;
}

.collection-success-dialog__close {
  display: inline-flex;
  width: 24px;
  height: 24px;
  align-items: center;
  justify-content: center;
  margin: 0;
  padding: 0;
  border: none;
  background: transparent;
  color: #8f959e;
  cursor: pointer;
}

.collection-success-dialog__close:hover {
  color: #646a73;
}

.collection-success-dialog__panel {
  display: flex;
  flex-direction: column;
  gap: 0;
  padding: 4px 0;
  border-radius: 8px;
  background: #f5f6f7;
}

.collection-success-dialog__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
}

.collection-success-dialog__label {
  font-size: 14px;
  line-height: 1.5;
  color: #646a73;
}

.collection-success-dialog__value {
  font-size: 14px;
  font-weight: 500;
  line-height: 1.5;
  color: #0f1114;
}

.collection-success-dialog__footer {
  display: flex;
  gap: 12px;
}

.collection-success-dialog__btn {
  box-sizing: border-box;
  display: inline-flex;
  min-width: 0;
  height: 40px;
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
}

.collection-success-dialog__btn--ghost {
  border: 1px solid #dee0e3;
  background: #ffffff;
  color: #0f1114;
}

.collection-success-dialog__btn--ghost:hover {
  border-color: #bbbfc4;
}

.collection-success-dialog__btn--primary {
  border: none;
  background: #1f2329;
  color: #ffffff;
}

.collection-success-dialog__btn--primary:hover {
  background: #2b2f36;
}
</style>

<style>
.collection-success-dialog.el-dialog {
  border-radius: 8px;
}

.collection-success-dialog .el-dialog__header {
  margin-right: 0;
  padding: 20px 20px 12px;
}

.collection-success-dialog .el-dialog__body {
  padding: 0 20px 8px;
}

.collection-success-dialog .el-dialog__footer {
  padding: 12px 20px 20px;
}
</style>

<script setup lang="ts">
/**
 * 折叠块「数据沉淀配置」：新建表 / 使用现有表 + 表格下拉（选项待接口）。
 */
import type { TaskCreateFormModel } from '@/views/TaskCreateForm/types'

defineOptions({ name: 'DataRetentionSection' })

const props = defineProps<{ form: TaskCreateFormModel }>()

/** 选择「新建」时清空已选表 id */
function onPickNew() {
  props.form.tableMode = 'new'
  props.form.existingTableId = ''
}

/** 选择「使用现有」时保留或后续由用户选表 */
function onPickExisting() {
  props.form.tableMode = 'existing'
}
</script>

<template>
  <div class="retention-panel">
    <p class="retention-panel-label">选择多维表格</p>
    <div class="retention-cards">
      <button
        type="button"
        class="retention-card"
        :class="form.tableMode === 'new' ? 'retention-card--active' : 'retention-card--muted'"
        @click="onPickNew"
      >
        <span class="retention-card-plus" aria-hidden="true">+</span>
        <span class="retention-card-title">新建表格</span>
        <span class="retention-card-desc">创建新的多维表格</span>
      </button>
      <button
        type="button"
        class="retention-card"
        :class="form.tableMode === 'existing' ? 'retention-card--active' : 'retention-card--muted'"
        @click="onPickExisting"
      >
        <span class="retention-card-icon" aria-hidden="true">
          <svg viewBox="0 0 48 48" class="size-12" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="10" y="8" width="28" height="32" rx="2" stroke="currentColor" stroke-width="2" />
            <path d="M16 14h16M16 20h12" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
          </svg>
        </span>
        <span class="retention-card-title">使用现有</span>
        <span class="retention-card-desc">关联已有表格</span>
      </button>
    </div>

    <el-select
      v-show="form.tableMode === 'existing'"
      v-model="form.existingTableId"
      class="retention-table-select mt-4 w-full"
      placeholder="请选择表格..."
      clearable
      filterable
    >
      <!-- 选项由多维表格列表接口后续接入 -->
    </el-select>
  </div>
</template>

<style scoped>
.retention-panel-label {
  margin-bottom: 0.75rem;
  font-size: 0.875rem;
  color: rgb(51 65 85);
}

.retention-cards {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}

.retention-card {
  flex: 1 1 0;
  min-width: 10rem;
  min-height: 9.5rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
  padding: 1.25rem 1rem;
  border-radius: 0.75rem;
  cursor: pointer;
  text-align: center;
  transition:
    border-color 0.15s ease,
    background-color 0.15s ease,
    box-shadow 0.15s ease;
}

.retention-card--muted {
  border: 2px dashed rgb(203 213 225);
  background: #fff;
  color: rgb(51 65 85);
}

.retention-card--muted:hover {
  border-color: rgb(148 163 184);
}

.retention-card--active {
  border: 2px solid rgb(37 99 235);
  background: rgb(239 246 255);
  color: rgb(30 64 175);
  box-shadow: 0 0 0 1px rgb(191 219 254);
}

.retention-card-plus {
  font-size: 2.75rem;
  font-weight: 300;
  line-height: 1;
  color: rgb(15 23 42);
}

.retention-card--active .retention-card-plus {
  color: rgb(29 78 216);
}

.retention-card-icon {
  color: rgb(71 85 105);
}

.retention-card--active .retention-card-icon {
  color: rgb(37 99 235);
}

.retention-card-title {
  font-size: 0.9375rem;
  font-weight: 600;
  color: rgb(30 41 59);
}

.retention-card--active .retention-card-title {
  color: rgb(30 64 175);
}

.retention-card-desc {
  font-size: 0.75rem;
  color: rgb(100 116 139);
  max-width: 11rem;
  line-height: 1.35;
}

.retention-card--active .retention-card-desc {
  color: rgb(59 130 246);
}

.retention-table-select :deep(.el-select__wrapper) {
  border-radius: 0.5rem;
  box-shadow: 0 0 0 1px rgb(37 99 235) inset;
}

.retention-table-select :deep(.el-select__wrapper.is-hovering:not(.is-focused)) {
  box-shadow: 0 0 0 1px rgb(59 130 246) inset;
}
</style>

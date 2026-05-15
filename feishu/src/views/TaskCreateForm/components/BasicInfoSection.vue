<script setup lang="ts">
/**
 * 「基础设置」步骤：任务名称、任务类型（定时 / 单次横向切换，与设计稿一致）。
 */
import { AlarmClock, Lightning, QuestionFilled } from '@element-plus/icons-vue'
import type { TaskCreateFormModel } from '@/views/TaskCreateForm/types'

defineOptions({ name: 'BasicInfoSection' })

defineProps<{ form: TaskCreateFormModel }>()
</script>

<template>
  <div>
    <el-form-item label="任务名称" prop="planName">
      <el-input v-model="form.planName" class="w-full" placeholder="请输入任务名称" clearable />
    </el-form-item>
    <el-form-item prop="taskType" class="task-type-form-item">
      <template #label>
        <span class="task-type-label-wrap">
          <span class="task-form-field-title">任务类型</span>
          <el-tooltip
            placement="top"
            content="定时任务：按采集频率在生效时间窗口内持续拉取；单次任务：保存后按关键词执行一次采集。"
          >
            <span class="task-type-help" tabindex="0" role="button" aria-label="任务类型说明">
              <el-icon :size="14"><QuestionFilled /></el-icon>
            </span>
          </el-tooltip>
        </span>
      </template>
      <div class="task-type-segmented" role="tablist" aria-label="任务类型">
        <button
          type="button"
          role="tab"
          :aria-selected="form.taskType === 'scheduled'"
          class="task-type-segment"
          :class="{ 'task-type-segment--active': form.taskType === 'scheduled' }"
          @click="form.taskType = 'scheduled'"
        >
          <el-icon class="task-type-segment__icon shrink-0" :size="18">
            <AlarmClock />
          </el-icon>
          <span class="task-type-segment__label whitespace-nowrap">定时任务</span>
        </button>
        <button
          type="button"
          role="tab"
          :aria-selected="form.taskType === 'realtime'"
          class="task-type-segment"
          :class="{ 'task-type-segment--active': form.taskType === 'realtime' }"
          @click="form.taskType = 'realtime'"
        >
          <el-icon class="task-type-segment__icon shrink-0" :size="18">
            <Lightning />
          </el-icon>
          <span class="task-type-segment__label whitespace-nowrap">单次任务</span>
        </button>
      </div>
    </el-form-item>
  </div>
</template>

<style scoped>
.task-type-form-item :deep(.el-form-item__content) {
  line-height: 1.3;
}

.task-type-label-wrap {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.task-type-help {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 1px solid #c9cdd4;
  color: #8f959e;
  cursor: default;
  line-height: 1;
}

.task-type-help:hover {
  color: #1f22f6;
  border-color: #1f22f6;
}

.task-type-segmented {
  box-sizing: border-box;
  display: flex;
  width: 100%;
  max-width: 378px;
  flex-direction: row;
  flex-wrap: nowrap;
  align-items: stretch;
  gap: 6px;
  padding: 4px;
  background: #f8f9fa;
  border-radius: 6px;
}

.task-type-segment {
  box-sizing: border-box;
  display: inline-flex;
  min-width: 0;
  height: 40px;
  flex: 1 1 0;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin: 0;
  padding: 0 8px;
  border: 1px solid #dee0e3;
  border-radius: 4px;
  background: #ffffff;
  font-size: 14px;
  font-weight: 500;
  line-height: 1;
  color: #0f1114;
  cursor: pointer;
  transition:
    background-color 0.15s ease,
    border-color 0.15s ease,
    color 0.15s ease;
}

.task-type-segment:hover:not(.task-type-segment--active) {
  border-color: #bbbfc4;
}

.task-type-segment__icon {
  color: #646a73;
}

.task-type-segment--active {
  background: #ededfe;
  border-color: #1f22f6;
  color: #1f22f6;
}

.task-type-segment--active .task-type-segment__icon {
  color: #1f22f6;
}

.task-type-segment--active .task-type-segment__label {
  color: #1f22f6;
}
</style>

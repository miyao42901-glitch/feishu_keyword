<script setup lang="ts">
/**
 * 「基础设置」步骤：方案名称、任务类型（分段控件：定时 / 单次）。
 */
import { AlarmClock, Lightning } from '@element-plus/icons-vue'
import type { TaskCreateFormModel } from '@/views/TaskCreateForm/types'

defineOptions({ name: 'BasicInfoSection' })

defineProps<{ form: TaskCreateFormModel }>()
</script>

<template>
  <div>
    <el-form-item label="方案名称" prop="planName">
      <el-input v-model="form.planName" placeholder="请输入方案名称" clearable />
    </el-form-item>
    <el-form-item label="任务类型" prop="taskType" class="task-type-form-item">
      <div
        class="task-type-segmented inline-flex w-full max-w-md rounded-[10px] bg-[#f0f2f5] p-[3px]"
        role="tablist"
        aria-label="任务类型"
      >
        <button
          type="button"
          role="tab"
          :aria-selected="form.taskType === 'scheduled'"
          class="task-type-segment flex min-w-0 flex-1 items-center justify-center gap-1.5 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200 sm:px-4"
          :class="
            form.taskType === 'scheduled'
              ? 'task-type-segment--active text-slate-800'
              : 'text-slate-600 hover:text-slate-800'
          "
          @click="form.taskType = 'scheduled'"
        >
          <el-icon class="shrink-0 text-[#a65d48]" :size="18">
            <AlarmClock />
          </el-icon>
          <span class="whitespace-nowrap">定时任务</span>
        </button>
        <button
          type="button"
          role="tab"
          :aria-selected="form.taskType === 'realtime'"
          class="task-type-segment flex min-w-0 flex-1 items-center justify-center gap-1.5 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200 sm:px-4"
          :class="
            form.taskType === 'realtime'
              ? 'task-type-segment--active text-slate-800'
              : 'text-slate-600 hover:text-slate-800'
          "
          @click="form.taskType = 'realtime'"
        >
          <el-icon class="shrink-0 text-[#d4a017]" :size="18">
            <Lightning />
          </el-icon>
          <span class="whitespace-nowrap">单次任务</span>
        </button>
      </div>
    </el-form-item>
  </div>
</template>

<style scoped>
.task-type-form-item :deep(.el-form-item__content) {
  line-height: 1.3;
}

.task-type-segment--active {
  background-color: #fff;
  box-shadow: 0 1px 3px rgb(0 0 0 / 0.08), 0 1px 2px rgb(0 0 0 / 0.06);
}
</style>

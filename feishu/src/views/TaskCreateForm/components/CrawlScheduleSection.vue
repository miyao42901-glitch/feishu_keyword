<script setup lang="ts">
/**
 * 「采集配置」步骤内：定时任务的采集频率、开始时间、结束时间。
 */
import type { TaskCreateFormModel } from '@/views/TaskCreateForm/types'
import { DATETIME_FORMAT, frequencyOptions } from '@/views/TaskCreateForm/constants'
import {
  disabledPastDateForPicker,
  disabledTimeEffectiveDateTime,
  disabledTimeExpireDateTime,
} from '@/lib/datetime-task-window'

defineOptions({ name: 'CrawlScheduleSection' })

const props = defineProps<{ form: TaskCreateFormModel }>()

function onExpireDisabledTime(date: Date) {
  return disabledTimeExpireDateTime(date, props.form.effectiveAt)
}
</script>

<template>
  <div v-if="form.taskType === 'scheduled'">
    <el-form-item label="采集频率" prop="crawlFrequency">
      <el-select v-model="form.crawlFrequency" placeholder="请选择采集频率" class="max-w-xs">
        <el-option v-for="opt in frequencyOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
      </el-select>
    </el-form-item>
    <div class="schedule-datetime-row flex flex-col gap-4 sm:flex-row sm:items-start sm:gap-4">
      <el-form-item label="开始时间" prop="effectiveAt" class="schedule-datetime-item min-w-0 flex-1">
        <el-date-picker
          v-model="form.effectiveAt"
          type="datetime"
          :format="DATETIME_FORMAT"
          :value-format="DATETIME_FORMAT"
          placeholder="选择年月日时分秒"
          class="w-full"
          :disabled-date="disabledPastDateForPicker"
          :disabled-time="disabledTimeEffectiveDateTime"
        />
      </el-form-item>
      <el-form-item label="结束时间" prop="expireAt" class="schedule-datetime-item min-w-0 flex-1">
        <el-date-picker
          v-model="form.expireAt"
          type="datetime"
          :format="DATETIME_FORMAT"
          :value-format="DATETIME_FORMAT"
          placeholder="选择年月日时分秒"
          class="w-full"
          :disabled-date="disabledPastDateForPicker"
          :disabled-time="onExpireDisabledTime"
        />
      </el-form-item>
    </div>
  </div>
  <p v-else class="mb-4 text-sm text-slate-500">单词任务按单次关键词执行，无需配置采集频率与时间窗口。</p>
</template>

<style scoped>
/* 同一行并排；极窄屏纵向堆叠 */
@media (min-width: 640px) {
  .schedule-datetime-row :deep(.schedule-datetime-item) {
    margin-bottom: 0;
  }
}
</style>

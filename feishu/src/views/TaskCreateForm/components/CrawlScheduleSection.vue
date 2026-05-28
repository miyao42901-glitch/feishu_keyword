<script setup lang="ts">
/**
 * 定时任务：采集频率、开始时间、结束时间；单次任务：说明文案。置于任务类型下方，控件样式与设计稿一致。
 */
import type { TaskCreateFormModel } from '@/views/TaskCreateForm/types'
import { DATETIME_FORMAT, frequencyOptions } from '@/views/TaskCreateForm/constants'
import {
  disabledPastDateForPicker,
  disabledTimeEffectiveDateTime,
  disabledTimeExpireDateTime,
} from '@/lib/datetime-task-window'

defineOptions({ name: 'CrawlScheduleSection' })

const props = defineProps<{
  form: TaskCreateFormModel
  /** 非 pending 编辑态：采集频率与起止时间不可改 */
  scheduleLocked?: boolean
}>()

function onExpireDisabledTime(date: Date) {
  return disabledTimeExpireDateTime(date, props.form.effectiveAt)
}
</script>

<template>
  <div v-if="form.taskType === 'scheduled'">
    <p v-if="scheduleLocked" class="schedule-locked-hint m-0 mb-3 text-xs text-amber-700">
      任务已非待运行状态，采集频率与起止时间不可修改；仍可修改任务名称。
    </p>
    <el-form-item prop="crawlFrequency" class="crawl-frequency-form-item">
      <template #label>
        <div class="crawl-frequency-label-row">
          <span class="task-form-field-title">采集频率</span>
          <span class="crawl-frequency-hint">*采集频率越高，消耗积分越多</span>
        </div>
      </template>
      <el-select
        v-model="form.crawlFrequency"
        placeholder="请选择采集频率"
        class="w-full crawl-schedule-control"
        :disabled="scheduleLocked"
      >
        <el-option v-for="opt in frequencyOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
      </el-select>
    </el-form-item>
    <div class="schedule-datetime-col flex flex-col gap-4">
      <el-form-item label="开始时间" prop="effectiveAt" class="schedule-datetime-item min-w-0 w-full">
        <el-date-picker
          v-model="form.effectiveAt"
          type="datetime"
          :format="DATETIME_FORMAT"
          :value-format="DATETIME_FORMAT"
          placeholder="请输入开始时间"
          class="w-full crawl-schedule-control"
          :disabled="scheduleLocked"
          :disabled-date="disabledPastDateForPicker"
          :disabled-time="disabledTimeEffectiveDateTime"
        />
      </el-form-item>
      <el-form-item label="结束时间" prop="expireAt" class="schedule-datetime-item min-w-0 w-full">
        <el-date-picker
          v-model="form.expireAt"
          type="datetime"
          :format="DATETIME_FORMAT"
          :value-format="DATETIME_FORMAT"
          placeholder="请输入结束时间"
          class="w-full crawl-schedule-control"
          :disabled="scheduleLocked"
          :disabled-date="disabledPastDateForPicker"
          :disabled-time="onExpireDisabledTime"
        />
      </el-form-item>
    </div>
  </div>
</template>

<style scoped>
.crawl-frequency-label-row {
  display: flex;
  max-width: 100%;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0.375rem 0.75rem;
}

.crawl-frequency-hint {
  font-size: 12px;
  font-weight: 400;
  line-height: 1.35;
  color: #f54a45;
}

.crawl-frequency-form-item :deep(.el-form-item__label) {
  width: 100% !important;
  justify-content: flex-start;
}

.crawl-schedule-control :deep(.el-select__wrapper),
.crawl-schedule-control :deep(.el-input__wrapper) {
  min-height: 36px;
  border-radius: 4px;
  border: 1px solid #dee0e3;
  box-shadow: none !important;
  background-color: #ffffff;
}

.crawl-schedule-control :deep(.el-select__wrapper.is-hovering),
.crawl-schedule-control :deep(.el-select__wrapper.is-focused),
.crawl-schedule-control :deep(.el-input__wrapper.is-hovering),
.crawl-schedule-control :deep(.el-input__wrapper.is-focused) {
  box-shadow: none !important;
}

.crawl-schedule-control :deep(.el-select__wrapper.is-focused),
.crawl-schedule-control :deep(.el-input__wrapper.is-focused) {
  border-color: #1f22f6;
}

.schedule-datetime-col :deep(.schedule-datetime-item) {
  margin-bottom: 0;
}
</style>

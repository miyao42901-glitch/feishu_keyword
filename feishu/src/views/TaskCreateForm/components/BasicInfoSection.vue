<script setup lang="ts">
/**
 * 折叠块「基础信息」：方案名、任务类型、采集频率（仅定时）、时间（仅定时）、授权码。
 */
import type { TaskCreateFormModel } from '@/views/TaskCreateForm/types'
import { DATETIME_FORMAT, frequencyOptions } from '@/views/TaskCreateForm/constants'
import {
  disabledPastDateForPicker,
  disabledTimeEffectiveDateTime,
  disabledTimeExpireDateTime,
} from '@/lib/datetime-task-window'

defineOptions({ name: 'BasicInfoSection' })

const props = defineProps<{ form: TaskCreateFormModel }>()

function onExpireDisabledTime(date: Date) {
  return disabledTimeExpireDateTime(date, props.form.effectiveAt)
}
</script>

<template>
  <div>
    <el-form-item label="方案名称" prop="planName">
      <el-input v-model="form.planName" placeholder="请输入方案名称" clearable />
    </el-form-item>
    <el-form-item label="任务类型" prop="taskType">
      <el-radio-group v-model="form.taskType">
        <el-radio value="scheduled">定时任务</el-radio>
        <el-radio value="realtime">实时任务</el-radio>
      </el-radio-group>
    </el-form-item>
    <template v-if="form.taskType === 'scheduled'">
      <el-form-item label="采集频率" prop="crawlFrequency">
        <el-select v-model="form.crawlFrequency" placeholder="请选择采集频率" class="max-w-xs">
          <el-option
            v-for="opt in frequencyOptions"
            :key="opt.value"
            :label="opt.label"
            :value="opt.value"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="生效时间" prop="effectiveAt">
        <el-date-picker
          v-model="form.effectiveAt"
          type="datetime"
          :format="DATETIME_FORMAT"
          :value-format="DATETIME_FORMAT"
          placeholder="选择年月日时分秒"
          class="w-full max-w-md"
          :disabled-date="disabledPastDateForPicker"
          :disabled-time="disabledTimeEffectiveDateTime"
        />
      </el-form-item>
      <el-form-item label="过期时间" prop="expireAt">
        <el-date-picker
          v-model="form.expireAt"
          type="datetime"
          :format="DATETIME_FORMAT"
          :value-format="DATETIME_FORMAT"
          placeholder="选择年月日时分秒"
          class="w-full max-w-md"
          :disabled-date="disabledPastDateForPicker"
          :disabled-time="onExpireDisabledTime"
        />
      </el-form-item>
    </template>
    <el-form-item label="授权码" prop="authCode">
      <el-input v-model="form.authCode" type="password" show-password placeholder="请输入授权码" clearable />
      <p class="mt-1.5 text-xs text-slate-500">授权码用于API接口调用认证</p>
    </el-form-item>
  </div>
</template>

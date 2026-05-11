<script setup lang="ts">
/**
 * 折叠块「基础信息」：方案名、定时任务、采集频率、时间、授权码。
 */
import dayjs from 'dayjs'
import type { TaskCreateFormModel } from '@/views/TaskCreateForm/types'
import { DATETIME_FORMAT, frequencyOptions } from '@/views/TaskCreateForm/constants'

defineOptions({ name: 'BasicInfoSection' })

const props = defineProps<{ form: TaskCreateFormModel }>()

/** 不可选今天之前的日期 */
function disabledPastDate(time: Date) {
  return dayjs(time).startOf('day').isBefore(dayjs().startOf('day'))
}

function makeDisabledTimeFromBoundary(date: Date, boundary: dayjs.Dayjs) {
  const cur = dayjs(date)
  if (!cur.isSame(boundary, 'day')) return {}
  const b = boundary
  return {
    disabledHours: () => Array.from({ length: b.hour() }, (_, i) => i),
    disabledMinutes: (hour: number) =>
      hour < b.hour()
        ? Array.from({ length: 60 }, (_, i) => i)
        : hour === b.hour()
          ? Array.from({ length: b.minute() }, (_, i) => i)
          : [],
    disabledSeconds: (hour: number, minute: number) =>
      hour < b.hour() || (hour === b.hour() && minute < b.minute())
        ? Array.from({ length: 60 }, (_, i) => i)
        : hour === b.hour() && minute === b.minute()
          ? Array.from({ length: b.second() }, (_, i) => i)
          : [],
  }
}

/** 生效时间：若选「今天」，不可选当前时刻之前 */
function disabledTimeEffective(date: Date) {
  const now = dayjs()
  if (!dayjs(date).isSame(now, 'day')) return {}
  return makeDisabledTimeFromBoundary(date, now)
}

/** 过期时间：不得早于当前时刻；若与生效同一天，不得早于生效时刻 */
function disabledTimeExpire(date: Date) {
  const cur = dayjs(date)
  const now = dayjs()
  const effRaw = props.form.effectiveAt?.trim()
  const eff = effRaw ? dayjs(effRaw) : null
  const candidates: dayjs.Dayjs[] = []
  if (cur.isSame(now, 'day')) candidates.push(now)
  if (eff && eff.isValid() && cur.isSame(eff, 'day')) candidates.push(eff)
  if (candidates.length === 0) return {}
  const boundary = candidates.reduce((a, c) => (a.isAfter(c) ? a : c))
  return makeDisabledTimeFromBoundary(date, boundary)
}
</script>

<template>
  <div>
    <el-form-item label="方案名称" prop="planName">
      <el-input v-model="form.planName" placeholder="请输入方案名称" clearable />
    </el-form-item>
    <el-form-item label="任务类型">
      <span class="text-sm text-slate-700">定时任务</span>
    </el-form-item>
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
        :disabled-date="disabledPastDate"
        :disabled-time="disabledTimeEffective"
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
        :disabled-date="disabledPastDate"
        :disabled-time="disabledTimeExpire"
      />
    </el-form-item>
    <el-form-item label="授权码" prop="authCode">
      <el-input v-model="form.authCode" type="password" show-password placeholder="请输入授权码" clearable />
      <p class="mt-1.5 text-xs text-slate-500">授权码用于API接口调用认证</p>
    </el-form-item>
  </div>
</template>

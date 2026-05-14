<script setup lang="ts">
/**
 * 「基础设置」步骤：方案名称、任务类型（单词任务 / 定时任务）。
 */
import type { TaskCreateFormModel } from '@/views/TaskCreateForm/types'

defineOptions({ name: 'BasicInfoSection' })

defineProps<{ form: TaskCreateFormModel }>()
</script>

<template>
  <div>
    <el-form-item label="方案名称" prop="planName">
      <el-input v-model="form.planName" placeholder="请输入方案名称" clearable />
    </el-form-item>
    <el-form-item label="任务类型" prop="taskType">
      <el-radio-group v-model="form.taskType">
        <el-radio value="scheduled">定时任务</el-radio>
        <el-radio value="realtime">单词任务</el-radio>
      </el-radio-group>
    </el-form-item>
  </div>
</template>

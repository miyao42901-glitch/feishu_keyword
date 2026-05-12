<script setup lang="ts">
/**
 * 任务页外层「任务配置」：与单任务表单解耦，可扩展多项；当前含全局授权码。
 */
import { useGlobalSettingsStore } from '@/stores/globalSettings'

defineOptions({ name: 'TaskGlobalConfigBar' })

const globalSettings = useGlobalSettingsStore()
</script>

<template>
  <section class="max-w-3xl" aria-labelledby="task-global-config-heading">
    <h2 id="task-global-config-heading" class="mb-3 text-base font-semibold text-slate-800">
      任务配置
    </h2>
    <el-form :model="globalSettings" label-position="top">
      <el-form-item label="授权码" required>
        <el-input
          v-model="globalSettings.authCode"
          type="text"
          placeholder="请输入授权码"
          clearable
          autocomplete="off"
        />
        <p class="mt-1.5 text-xs text-slate-500">授权码用于API接口调用认证</p>
      </el-form-item>
    </el-form>
  </section>
</template>

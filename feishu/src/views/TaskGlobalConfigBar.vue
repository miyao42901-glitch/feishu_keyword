<script setup lang="ts">
/**
 * 任务页外层「任务配置」：与单任务表单解耦，可扩展多项；当前含全局授权码。
 */
import { ref } from 'vue'
import { useGlobalSettingsStore } from '@/stores/globalSettings'

defineOptions({ name: 'TaskGlobalConfigBar' })

const globalSettings = useGlobalSettingsStore()

const authHelpVisible = ref(false)

/** 飞书开放平台扩展托管的教程图（图内已含步骤说明与标题文案） */
const authCodeHelpImageUrl =
  'https://ext.baseopendev.com/ext/k741350093_keyword-search-fe_1777360332062_924/1777360354886/image.png'
</script>

<template>
  <section class="max-w-3xl" aria-labelledby="task-global-config-heading">
    <h2 id="task-global-config-heading" class="mb-3 text-base font-semibold text-slate-800">
      任务配置
    </h2>
    <el-form :model="globalSettings" label-position="top">
      <el-form-item required>
        <template #label>
          <span class="inline-flex items-center gap-1.5">
            <span>授权码</span>
            <el-tooltip content="点击查看如何获取授权码" placement="top">
              <button
                type="button"
                class="inline-flex size-5 shrink-0 items-center justify-center rounded-full border border-slate-300 bg-white text-xs font-semibold text-slate-500 transition-colors hover:border-indigo-400 hover:text-indigo-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/40"
                aria-label="如何获取授权码"
                @click="authHelpVisible = true"
              >
                ?
              </button>
            </el-tooltip>
          </span>
        </template>
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

    <el-dialog
      v-model="authHelpVisible"
      title="如何获取授权码"
      width="520px"
      append-to-body
      destroy-on-close
      class="auth-code-help-dialog"
      align-center
    >
      <div class="max-h-[min(85vh,800px)] overflow-y-auto">
        <img
          :src="authCodeHelpImageUrl"
          alt="如何获取授权码"
          class="w-full rounded border border-slate-100"
          loading="lazy"
          decoding="async"
          referrerpolicy="no-referrer-when-downgrade"
        />
      </div>
    </el-dialog>
  </section>
</template>

<style>
.auth-code-help-dialog.el-dialog {
  max-width: calc(100vw - 24px);
}

.auth-code-help-dialog .el-dialog__body {
  padding-top: 0.5rem;
  padding-bottom: 1rem;
}
</style>

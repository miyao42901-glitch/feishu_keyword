<script setup lang="ts">
/**
 * 全局 API-Key（授权码）；「获取 API-Key」跳转登录页以拉取 api_key。
 */
import { ref } from 'vue'
import { useGlobalSettingsStore } from '@/stores/globalSettings'

defineOptions({ name: 'GlobalApiKeyBar' })

const emit = defineEmits<{
  goLogin: []
}>()

const globalSettings = useGlobalSettingsStore()
const authHelpVisible = ref(false)

const authCodeHelpImageUrl =
  'https://ext.baseopendev.com/ext/k741350093_keyword-search-fe_1777360332062_924/1777360354886/image.png'
</script>

<template>
  <section class="w-full space-y-4" aria-labelledby="global-api-key-heading">
    <div class="flex flex-col gap-2 sm:flex-row sm:items-end sm:gap-3">
      <div class="min-w-0 flex-1">
        <div class="mb-1 flex items-center gap-1.5">
          <span id="global-api-key-heading" class="text-xs font-medium text-slate-700">API-Key</span>
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
        </div>
        <el-input
          v-model="globalSettings.authCode"
          type="password"
          show-password
          placeholder="请输入 API-Key"
          clearable
          autocomplete="off"
          class="w-full"
        />
      </div>
      <el-button type="primary" class="w-full shrink-0 sm:w-auto" @click="emit('goLogin')">
        获取API-Key
      </el-button>
    </div>
    <p class="text-xs text-slate-500">授权码用于 API 接口调用认证</p>

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

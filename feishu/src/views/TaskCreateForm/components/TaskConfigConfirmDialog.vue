<script setup lang="ts">
/**
 * 保存前「确认任务配置」：配置摘要、预估点数与余额、取消 / 开始执行（落库）。
 */
import { DocumentCopy, Histogram } from '@element-plus/icons-vue'
import type { TaskConfigConfirmRow } from '@/views/TaskCreateForm/build-preview-rows'

defineOptions({ name: 'TaskConfigConfirmDialog' })

defineProps<{
  rows: TaskConfigConfirmRow[]
  estimatedPoints: number
  balancePoints: number
  confirming: boolean
}>()

const visible = defineModel<boolean>({ required: true })

const emit = defineEmits<{
  confirm: []
}>()

function handleClose() {
  visible.value = false
}
</script>

<template>
  <el-dialog
    v-model="visible"
    width="480px"
    align-center
    append-to-body
    destroy-on-close
    class="task-config-confirm-dialog"
    :close-on-click-modal="false"
    :show-close="false"
  >
    <template #header>
      <div class="flex items-center justify-between border-b border-slate-200 pb-3">
        <div class="flex items-center gap-2 text-slate-900">
          <el-icon class="text-[#3355FF]" :size="18">
            <DocumentCopy />
          </el-icon>
          <span class="text-base font-semibold">确认任务配置</span>
        </div>
        <el-button
          text
          circle
          class="!ml-0 !h-8 !w-8"
          aria-label="关闭"
          :disabled="confirming"
          @click="handleClose"
        >
          <span class="text-lg leading-none text-slate-400 hover:text-slate-600">×</span>
        </el-button>
      </div>
    </template>

    <div class="pt-1">
      <div class="mb-3 flex items-center gap-2 text-sm font-medium text-slate-800">
        <el-icon class="text-[#3355FF]" :size="16">
          <Histogram />
        </el-icon>
        <span>配置详情</span>
      </div>

      <div class="rounded-lg border border-slate-100 bg-slate-50 px-4 py-3">
        <div
          v-for="(row, idx) in rows"
          :key="idx"
          class="flex gap-3 border-b border-slate-100 py-2.5 text-sm last:border-b-0"
          :class="row.kind === 'tags' ? 'items-start' : 'items-center'"
        >
          <span class="w-24 shrink-0 text-slate-500">{{ row.label }}</span>
          <div class="min-w-0 flex-1 text-right text-slate-900">
            <template v-if="row.kind === 'text'">{{ row.value }}</template>
            <template v-else>
              <div v-if="row.tags.length" class="flex flex-wrap justify-end gap-1.5">
                <el-tag
                  v-for="(t, i) in row.tags"
                  :key="`${t}-${i}`"
                  type="primary"
                  effect="plain"
                  size="small"
                  class="!border-[#CCD6FF] !bg-[#EEF1FF] !text-[#3355FF]"
                >
                  {{ t }}
                </el-tag>
              </div>
              <span v-else>—</span>
            </template>
          </div>
        </div>
      </div>

      <div
        class="mt-4 flex items-center justify-between rounded-lg border border-[#CCD6FF] bg-[#EEF4FF] px-4 py-3 text-sm"
      >
        <span class="text-slate-700">
          预估消耗：<span class="font-semibold text-[#3355FF]">~{{ estimatedPoints }}点</span>
        </span>
        <span class="text-slate-700">
          当前余额：<span class="font-semibold text-[#3355FF]">{{ balancePoints }}点</span>
        </span>
      </div>
    </div>

    <template #footer>
      <div class="flex w-full gap-3 border-t border-slate-100 pt-4">
        <el-button class="flex-1" :disabled="confirming" @click="handleClose">取消</el-button>
        <el-button type="primary" class="flex-1" :loading="confirming" @click="emit('confirm')">
          开始执行
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<style scoped>
.task-config-confirm-dialog :deep(.el-dialog__header) {
  margin-right: 0;
  padding-bottom: 0;
}
.task-config-confirm-dialog :deep(.el-dialog__body) {
  padding-top: 0.75rem;
}
.task-config-confirm-dialog :deep(.el-dialog__footer) {
  padding-top: 0;
}
</style>

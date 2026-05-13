<script setup lang="ts">
/**
 * 保存成功后的配置预览；确认后「立即执行」启动任务分配。
 */
defineOptions({ name: 'TaskConfigPreviewDialog' })

defineProps<{
  rows: { label: string; value: string }[]
  executing: boolean
}>()

const visible = defineModel<boolean>({ required: true })

const emit = defineEmits<{
  execute: []
  leave: []
}>()
</script>

<template>
  <el-dialog
    v-model="visible"
    title="配置预览"
    width="520px"
    align-center
    append-to-body
    destroy-on-close
    class="task-config-preview-dialog"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    :show-close="false"
  >
    <p class="mb-3 text-sm text-slate-600">请核对以下配置。确认无误后可立即开始分配任务。</p>
    <el-table :data="rows" border size="small" class="preview-table">
      <el-table-column prop="label" label="项" width="140" />
      <el-table-column prop="value" label="内容" min-width="200" show-overflow-tooltip />
    </el-table>
    <template #footer>
      <div class="flex flex-wrap justify-end gap-2">
        <el-button :disabled="executing" @click="emit('leave')">返回列表</el-button>
        <el-button type="primary" :loading="executing" @click="emit('execute')">立即执行</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<style scoped>
.preview-table :deep(.el-table__cell) {
  font-size: 0.8125rem;
}
</style>

<script setup lang="ts">
/**
 * 飞书 Webhook 通知（置于关键词下方）：开关、Webhook 输入与获取说明折叠区。
 */
import type { TaskCreateFormModel } from '@/views/TaskCreateForm/types'

defineOptions({ name: 'FeishuNotifySection' })

defineProps<{ form: TaskCreateFormModel }>()
</script>

<template>
  <div class="mt-6">
    <div
      class="mb-4 flex flex-col gap-3 rounded-lg border border-slate-100 bg-slate-50/80 px-4 py-3 sm:flex-row sm:items-center sm:justify-between sm:gap-4"
    >
      <div class="flex min-w-0 flex-1 flex-col gap-1 sm:flex-row sm:items-center sm:gap-3">
        <span class="shrink-0 text-sm font-medium text-slate-800">飞书通知</span>
        <span class="text-xs leading-relaxed text-slate-500">
          开启后任务执行完毕将推送飞书消息
        </span>
      </div>
      <el-switch v-model="form.feishuNotifyEnabled" class="shrink-0 self-end sm:self-auto" />
    </div>

    <template v-if="form.feishuNotifyEnabled">
      <el-form-item label="Webhook地址" prop="feishuWebhookUrl" required>
        <el-input
          v-model="form.feishuWebhookUrl"
          placeholder="请输入飞书机器人Webhook地址"
          clearable
        />
      </el-form-item>

      <el-collapse class="webhook-help-collapse mb-2 border-0 shadow-none">
        <el-collapse-item name="webhook-help" title="如何获取Webhook地址？">
          <ol class="m-0 list-decimal space-y-2 pl-5 text-sm leading-relaxed text-slate-600">
            <li>在飞书群聊中点击「设置」→「群机器人」</li>
            <li>点击「添加机器人」→ 选择「自定义机器人」</li>
            <li>设置机器人名称（如：关键词监控通知）</li>
            <li>复制生成的 Webhook 地址</li>
            <li>粘贴到上方输入框</li>
          </ol>
        </el-collapse-item>
      </el-collapse>
    </template>
  </div>
</template>

<style scoped>
.webhook-help-collapse :deep(.el-collapse-item__header) {
  font-size: 0.8125rem;
  font-weight: 500;
  color: rgb(51 65 85);
  background: rgb(248 250 252);
  border-radius: 0.5rem;
  padding: 0.5rem 0.75rem;
  height: auto;
  line-height: 1.4;
}

.webhook-help-collapse :deep(.el-collapse-item__wrap) {
  border-bottom: none;
}

.webhook-help-collapse :deep(.el-collapse-item__content) {
  padding-bottom: 0.5rem;
  padding-top: 0.25rem;
}
</style>

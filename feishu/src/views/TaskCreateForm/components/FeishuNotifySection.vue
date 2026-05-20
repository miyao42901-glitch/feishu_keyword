<script setup lang="ts">
/**
 * 飞书 Webhook 通知（第三步）：开关行 + Webhook 地址输入 + 获取说明弹框。
 */
import { Close, InfoFilled, QuestionFilled } from '@element-plus/icons-vue'
import { ref } from 'vue'
import type { TaskCreateFormModel } from '@/views/TaskCreateForm/types'

defineOptions({ name: 'FeishuNotifySection' })

defineProps<{ form: TaskCreateFormModel }>()

const webhookHelpVisible = ref(false)

function openWebhookHelp() {
  webhookHelpVisible.value = true
}
</script>

<template>
  <div class="feishu-notify-section">
    <div class="feishu-notify-toggle-row">
      <span class="task-form-field-title feishu-notify-toggle-row__label">飞书通知</span>
      <el-switch v-model="form.feishuNotifyEnabled" class="feishu-notify-switch" />
      <span class="feishu-notify-hint">*开启后按采集频率推送每轮结果；采集失败、积分低于1000时也会推送（单次任务不推送）</span>
    </div>

    <template v-if="form.feishuNotifyEnabled">
      <el-form-item prop="feishuWebhookUrl" class="feishu-webhook-form-item">
        <template #label>
          <span class="feishu-webhook-label-wrap">
            <span class="task-form-field-title">Webhook地址</span>
            <span class="feishu-webhook-required" aria-hidden="true">*</span>
            <button
              type="button"
              class="feishu-webhook-help"
              aria-label="如何获取 Webhook 地址"
              @click="openWebhookHelp"
            >
              <el-icon :size="12"><QuestionFilled /></el-icon>
            </button>
          </span>
        </template>
        <el-input
          v-model="form.feishuWebhookUrl"
          class="feishu-webhook-input w-full"
          placeholder="请输入飞书机器人Webhook地址"
          clearable
        />
      </el-form-item>
    </template>

    <el-dialog
      v-model="webhookHelpVisible"
      width="400px"
      align-center
      append-to-body
      destroy-on-close
      class="webhook-help-dialog"
      :show-close="false"
    >
      <template #header>
        <div class="webhook-help-dialog__header">
          <div class="webhook-help-dialog__title-wrap">
            <span class="webhook-help-dialog__info-icon" aria-hidden="true">
              <el-icon :size="14"><InfoFilled /></el-icon>
            </span>
            <span class="webhook-help-dialog__title">如何获取Webhook地址？</span>
          </div>
          <button
            type="button"
            class="webhook-help-dialog__close"
            aria-label="关闭"
            @click="webhookHelpVisible = false"
          >
            <el-icon :size="14"><Close /></el-icon>
          </button>
        </div>
      </template>

      <ol class="webhook-help-dialog__steps">
        <li>
          在飞书群聊中点击<span class="webhook-help-dialog__term">「设置」</span>→<span
            class="webhook-help-dialog__term"
            >「群机器人」</span
          >
        </li>
        <li>
          点击<span class="webhook-help-dialog__term">「添加机器人」</span>→选择<span
            class="webhook-help-dialog__term"
            >「自定义机器人」</span
          >
        </li>
        <li>设置机器人名称（如:关键词监控通知）</li>
        <li>复制生成的 Webhook 地址，粘贴进来即可</li>
      </ol>
    </el-dialog>
  </div>
</template>

<style scoped>
.feishu-notify-section {
  width: 100%;
}

.feishu-notify-toggle-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 12px;
}

.feishu-notify-toggle-row__label {
  flex-shrink: 0;
}

.feishu-notify-switch {
  flex-shrink: 0;
}

.feishu-notify-hint {
  min-width: 0;
  flex: 1 1 auto;
  font-size: 12px;
  font-weight: 400;
  line-height: 1.5;
  color: #8f959e;
}

.feishu-webhook-form-item {
  margin-top: 16px;
  margin-bottom: 0;
}

.feishu-webhook-form-item :deep(.el-form-item__label) {
  padding-bottom: 8px;
  line-height: 1.4;
}

.feishu-webhook-label-wrap {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.feishu-webhook-required {
  font-size: 12px;
  font-weight: 500;
  line-height: 1;
  color: #f54a45;
}

.feishu-webhook-help {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  margin: 0;
  padding: 0;
  border: 1px solid #c9cdd4;
  border-radius: 50%;
  background: transparent;
  color: #8f959e;
  cursor: pointer;
  line-height: 1;
}

.feishu-webhook-help:hover {
  color: #1f22f6;
  border-color: #1f22f6;
}

.feishu-webhook-input :deep(.el-input__wrapper) {
  min-height: 36px;
  border-radius: 4px;
  box-shadow: 0 0 0 1px #dee0e3 inset !important;
  background: #ffffff;
}

.feishu-webhook-input :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #1f22f6 inset !important;
}

.webhook-help-dialog__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.webhook-help-dialog__title-wrap {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 8px;
}

.webhook-help-dialog__info-icon {
  display: inline-flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #1f22f6;
  color: #ffffff;
}

.webhook-help-dialog__title {
  font-size: 16px;
  font-weight: 500;
  line-height: 1.4;
  color: #0f1114;
  text-align: left;
}

.webhook-help-dialog__close {
  box-sizing: border-box;
  display: inline-flex;
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  align-items: center;
  justify-content: center;
  margin: 0;
  padding: 0;
  border: 1px dashed #c9cdd4;
  border-radius: 2px;
  background: transparent;
  color: #8f959e;
  cursor: pointer;
}

.webhook-help-dialog__close:hover {
  color: #646a73;
  border-color: #bbbfc4;
}

.webhook-help-dialog__steps {
  margin: 0;
  padding: 0;
  list-style: none;
  counter-reset: webhook-step;
}

.webhook-help-dialog__steps li {
  position: relative;
  margin: 0;
  padding: 0 0 12px 1.5rem;
  font-size: 14px;
  font-weight: 400;
  line-height: 1.6;
  color: #0f1114;
  text-align: left;
}

.webhook-help-dialog__steps li:last-child {
  padding-bottom: 0;
}

.webhook-help-dialog__steps li::before {
  position: absolute;
  left: 0;
  font-size: 14px;
  font-weight: 400;
  line-height: 1.6;
  color: #0f1114;
  content: counter(webhook-step) '.';
  counter-increment: webhook-step;
}

.webhook-help-dialog__term {
  color: #000000;
}
</style>

<style>
.webhook-help-dialog.el-dialog {
  border-radius: 8px;
  background: #ffffff;
}

.webhook-help-dialog .el-dialog__header {
  margin-right: 0;
  padding: 20px 20px 12px;
}

.webhook-help-dialog .el-dialog__body {
  padding: 0 20px 20px;
}
</style>

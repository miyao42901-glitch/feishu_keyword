<script setup lang="ts">
/**
 * 积分不足等场景：展示提示文案与客服二维码。
 */
import { getCustomerServiceQrUrl, POINTS_INSUFFICIENT_MSG } from '@/lib/insufficient-balance'

defineOptions({ name: 'CustomerServiceQrDialog' })

withDefaults(
  defineProps<{
    message?: string
  }>(),
  { message: POINTS_INSUFFICIENT_MSG },
)

const visible = defineModel<boolean>({ required: true })

const supportQrUrl = getCustomerServiceQrUrl()
</script>

<template>
  <el-dialog
    v-model="visible"
    title="联系客服"
    width="min(360px, 92vw)"
    align-center
    append-to-body
    class="customer-service-qr-dialog"
  >
    <p class="customer-service-qr-dialog__message" role="alert">{{ message }}</p>
    <div class="customer-service-qr-dialog__qr-wrap">
      <img
        :src="supportQrUrl"
        alt="客服二维码"
        class="customer-service-qr-dialog__qr"
        loading="lazy"
        decoding="async"
      />
    </div>
    <p class="customer-service-qr-dialog__hint">扫码添加客服，获取专属支持</p>
  </el-dialog>
</template>

<style scoped>
.customer-service-qr-dialog__message {
  margin: 0 0 16px;
  font-size: 14px;
  font-weight: 500;
  line-height: 1.5;
  color: #d83931;
  text-align: center;
}

.customer-service-qr-dialog__qr-wrap {
  display: flex;
  justify-content: center;
  margin: 0 auto;
}

.customer-service-qr-dialog__qr {
  display: block;
  width: min(220px, 72vw);
  height: auto;
  border-radius: 8px;
}

.customer-service-qr-dialog__hint {
  margin: 14px 0 0;
  font-size: 13px;
  line-height: 1.5;
  color: #646a73;
  text-align: center;
}
</style>

<script setup lang="ts">
/**
 * 首页「关键词监控」下 API-Key：无授权码时引导获取；有授权码时完整展示（过长省略）并可跳转重新登陆。
 */
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useGlobalSettingsStore } from '@/stores/globalSettings'

defineOptions({ name: 'GlobalApiKeyBar' })

const emit = defineEmits<{
  goLogin: []
}>()

const globalSettings = useGlobalSettingsStore()
const { authCode } = storeToRefs(globalSettings)

const hasAuthCode = computed(() => authCode.value.trim().length > 0)

const authCodeDisplay = computed(() => authCode.value.trim())
</script>

<template>
  <section
    v-if="hasAuthCode"
    class="auth-code-card"
    aria-label="授权码"
  >
    <div class="auth-code-row">
      <span class="auth-code-label">授权码：</span>
      <span class="auth-code-value">{{ authCodeDisplay }}</span>
      <button type="button" class="auth-code-relogin" @click="emit('goLogin')">重新登陆</button>
    </div>
  </section>

  <section
    v-else
    class="api-key-promo"
    aria-labelledby="api-key-promo-heading"
  >
    <h2 id="api-key-promo-heading" class="sr-only">API-Key</h2>
    <button type="button" class="api-key-promo__btn" @click="emit('goLogin')">获取API-Key</button>
    <p class="api-key-promo__hint">请先登录，以获取API接口调用资格</p>
  </section>
</template>

<style scoped>
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.auth-code-card {
  box-sizing: border-box;
  width: 100%;
  max-width: 100%;
  margin-right: 0;
  margin-left: 0;
  padding: 10px 12px;
  background: #eff0f1;
  border-radius: 4px;
}

.auth-code-row {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  min-width: 0;
}

.auth-code-label {
  flex-shrink: 0;
  font-weight: 500;
  font-size: 12px;
  line-height: 1.35;
  color: #646a73;
  text-align: left;
}

.auth-code-value {
  flex: 1 1 auto;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 500;
  font-size: 12px;
  line-height: 1.35;
  color: #2b2f36;
  text-align: left;
}

.auth-code-relogin {
  flex-shrink: 0;
  margin: 0;
  padding: 0;
  border: none;
  background: transparent;
  cursor: pointer;
  font-weight: 500;
  font-size: 12px;
  line-height: 1.35;
  color: #1f22f6;
  text-align: right;
}

.auth-code-relogin:hover {
  text-decoration: underline;
}

.auth-code-relogin:focus-visible {
  outline: 2px solid rgba(31, 34, 246, 0.35);
  outline-offset: 2px;
}

.api-key-promo {
  box-sizing: border-box;
  display: flex;
  width: 100%;
  max-width: 100%;
  height: 92px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin-top: 0;
  margin-right: 0;
  margin-left: 0;
  padding: 0 12px;
  background: #ededfe;
  border-radius: 0;
}

.api-key-promo__btn {
  box-sizing: border-box;
  display: inline-flex;
  width: 135px;
  height: 38px;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  padding: 0;
  margin: 0;
  border: none;
  border-radius: 4px;
  background: linear-gradient(90deg, #1456f0 0%, #4014f0 100%);
  color: #ffffff;
  font-weight: 400;
  font-size: 16px;
  text-align: center;
  font-style: normal;
  text-transform: none;
  line-height: 1;
  cursor: pointer;
  transition: filter 0.15s ease;
}

.api-key-promo__btn:hover {
  filter: brightness(1.05);
}

.api-key-promo__btn:active {
  filter: brightness(0.96);
}

.api-key-promo__hint {
  margin: 8px 0 0;
  max-width: 100%;
  padding: 0 4px;
  font-size: 10px;
  color: #646a73;
  text-align: center;
  font-style: normal;
  line-height: 1.4;
}
</style>

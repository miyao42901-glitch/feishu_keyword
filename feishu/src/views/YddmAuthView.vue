<script setup lang="ts">
import { CircleCheck } from '@element-plus/icons-vue'
import { onMounted, reactive, ref } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import {
  EMAIL_RE,
  normalizeCnMobileInput,
  validateLoginPhoneOrEmail,
  validateRegisterPhoneOptional,
  YDDM_PASSWORD_MAX_LEN,
} from '@/lib/yddm-auth-validators'
import { yddmLogin, yddmRegister, type YddmLoginRequest, type YddmRegisterRequest } from '@/lib/yddm-api'
import { useGlobalSettingsStore } from '@/stores/globalSettings'
import { useYddmAuthStore } from '@/stores/yddmAuth'

defineOptions({ name: 'YddmAuthView' })

const globalSettings = useGlobalSettingsStore()
const yddmAuth = useYddmAuthStore()

const panel = ref<'login' | 'register'>('login')
const loginSubmitting = ref(false)
const registerSubmitting = ref(false)
const meLoading = ref(false)

const loginFormRef = ref<FormInstance>()
const loginForm = reactive({
  phone_num: '',
  password: '',
})
const loginRules: FormRules = {
  phone_num: [{ validator: validateLoginPhoneOrEmail, trigger: ['blur', 'change'] }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        const s = typeof value === 'string' ? value : ''
        if (s.length > YDDM_PASSWORD_MAX_LEN) {
          callback(
            new Error(
              `密码最多 ${YDDM_PASSWORD_MAX_LEN} 个字符；若误将 API Key 粘到密码框，请改填到顶部「API-Key」`,
            ),
          )
          return
        }
        callback()
      },
      trigger: ['blur', 'change'],
    },
  ],
}

const registerFormRef = ref<FormInstance>()
const registerForm = reactive({
  captcha: '',
  email: '',
  password: '',
  phone_num: '',
})

const registerRules: FormRules = {
  phone_num: [{ validator: validateRegisterPhoneOptional, trigger: ['blur', 'change'] }],
  captcha: [{ required: true, message: '请输入验证码', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        const s = typeof value === 'string' ? value : ''
        if (s.length > YDDM_PASSWORD_MAX_LEN) {
          callback(new Error(`密码最多 ${YDDM_PASSWORD_MAX_LEN} 个字符`))
          return
        }
        callback()
      },
      trigger: ['blur', 'change'],
    },
  ],
}

/** 替换为二维码图片 URL 后，「联系客服」区域将显示图片 */
const customerServiceQrUrl = ''

function maskApiKey(key: string): string {
  const t = key.trim()
  if (!t) return '—'
  if (t.length <= 10) return `${t.slice(0, 2)}…${t.slice(-2)}`
  return `${t.slice(0, 3)}****${t.slice(-4)}`
}

function formatBalanceCents(cents: unknown): string {
  if (typeof cents !== 'number' || !Number.isFinite(cents)) return '—'
  return `${(cents / 100).toFixed(2)} 元`
}

async function tryRefreshMe(clearSessionOnError = true) {
  if (!yddmAuth.isLoggedIn) return
  meLoading.value = true
  try {
    const u = await yddmAuth.refreshMe()
    const key = u?.api_key?.trim()
    if (key) globalSettings.authCode = key
  } catch (e) {
    const msg = e instanceof Error ? e.message : '加载个人信息失败'
    if (clearSessionOnError) {
      yddmAuth.clearSession()
      globalSettings.authCode = ''
      ElMessage.warning(`${msg}，请重新登录`)
    } else {
      ElMessage.error(`${msg}，已保留登录态与登录接口返回的资料`)
    }
  } finally {
    meLoading.value = false
  }
}

onMounted(() => {
  void tryRefreshMe(true)
})

async function onLogin() {
  loginSubmitting.value = true
  try {
    await loginFormRef.value?.validate().catch(() => Promise.reject())
    const account = loginForm.phone_num.trim()
    const phoneForApi = account.includes('@') ? account : normalizeCnMobileInput(account)
    const payload: YddmLoginRequest = {
      phone_num: phoneForApi,
      password: loginForm.password,
    }
    const data = await yddmLogin(payload)
    if (!data?.access_token?.trim()) {
      const apiKeyOnly = data?.user?.api_key?.trim()
      if (apiKeyOnly) globalSettings.authCode = apiKeyOnly
      ElMessage.success('登录成功（响应中未包含 access_token，无法拉取 /users/me）')
    } else {
      yddmAuth.setFromLogin(data)
      await tryRefreshMe(false)
      const apiKey = data?.user?.api_key?.trim() || yddmAuth.me?.api_key?.trim()
      if (apiKey) globalSettings.authCode = apiKey
      ElMessage.success('登录成功，已写入顶部 API-Key')
    }
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '登录失败')
  } finally {
    loginSubmitting.value = false
  }
}

function onLogout() {
  yddmAuth.clearSession()
  globalSettings.authCode = ''
  panel.value = 'login'
  ElMessage.success('已退出登录')
}

async function onRegister() {
  registerSubmitting.value = true
  try {
    await registerFormRef.value?.validate().catch(() => Promise.reject())
    const email = registerForm.email.trim()
    const phone = registerForm.phone_num.trim()
    if (!email && !phone) {
      ElMessage.warning('请至少填写邮箱或手机号之一')
      return
    }
    if (email && !EMAIL_RE.test(email)) {
      ElMessage.warning('邮箱格式不正确')
      return
    }
    const payload: YddmRegisterRequest = {
      captcha: registerForm.captcha.trim(),
      password: registerForm.password,
    }
    if (email) payload.email = email
    if (phone) payload.phone_num = normalizeCnMobileInput(phone)
    await yddmRegister(payload)
    ElMessage.success('注册成功')
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '注册失败')
  } finally {
    registerSubmitting.value = false
  }
}
</script>

<template>
  <div class="mx-auto flex w-full min-w-0 max-w-full flex-col gap-5 px-1 sm:px-0">
    <section class="auth-card rounded-xl border border-slate-200/80 bg-white p-6 shadow-sm">
      <template v-if="yddmAuth.isLoggedIn">
        <div class="flex flex-col items-center text-center">
          <el-icon :size="52" class="text-emerald-500" aria-hidden="true">
            <CircleCheck />
          </el-icon>
          <p class="mt-4 text-base font-semibold text-slate-900">已登录成功</p>
          <p class="mt-1 w-full max-w-full text-sm text-slate-500">
            API Key 已自动填入顶部授权码字段；下方为
            <span class="whitespace-nowrap">GET /users/me</span>
            同步的账户信息。
          </p>

          <div
            v-if="meLoading"
            class="mt-5 w-full rounded-lg border border-slate-100 bg-slate-50 py-6 text-sm text-slate-500"
          >
            正在加载个人信息…
          </div>
          <dl
            v-else-if="yddmAuth.me"
            class="mt-5 w-full space-y-2.5 rounded-lg border border-slate-100 bg-slate-50/80 px-4 py-3 text-left text-sm"
          >
            <div class="flex justify-between gap-3">
              <dt class="shrink-0 text-slate-500">用户 ID</dt>
              <dd class="truncate font-medium text-slate-800">{{ yddmAuth.me.id }}</dd>
            </div>
            <div v-if="yddmAuth.me.email" class="flex justify-between gap-3">
              <dt class="shrink-0 text-slate-500">邮箱</dt>
              <dd class="truncate text-slate-800">{{ yddmAuth.me.email }}</dd>
            </div>
            <div v-if="yddmAuth.me.phone_num" class="flex justify-between gap-3">
              <dt class="shrink-0 text-slate-500">手机</dt>
              <dd class="truncate text-slate-800">{{ yddmAuth.me.phone_num }}</dd>
            </div>
            <div class="flex justify-between gap-3">
              <dt class="shrink-0 text-slate-500">API Key</dt>
              <dd class="truncate font-mono text-xs text-slate-700">
                {{ maskApiKey(String(yddmAuth.me.api_key ?? '')) }}
              </dd>
            </div>
            <div class="flex justify-between gap-3">
              <dt class="shrink-0 text-slate-500">账户余额</dt>
              <dd class="text-slate-800">{{ formatBalanceCents(yddmAuth.me.balance_cents) }}</dd>
            </div>
          </dl>

          <el-button class="mt-6 w-full" size="large" @click="onLogout">退出登录</el-button>
        </div>
      </template>

      <template v-else-if="panel === 'login'">
        <h2 class="mb-6 flex items-center justify-center gap-2 text-base font-semibold text-slate-900">
          <span class="text-lg leading-none" aria-hidden="true">🔑</span>
          登录账户获取API-Key
        </h2>

        <el-form
          ref="loginFormRef"
          :model="loginForm"
          :rules="loginRules"
          class="auth-form"
          label-position="top"
          @submit.prevent
        >
          <el-form-item prop="phone_num">
            <el-input
              v-model="loginForm.phone_num"
              size="large"
              placeholder="手机号/邮箱"
              clearable
              class="auth-input"
              maxlength="128"
            />
          </el-form-item>
          <el-form-item prop="password">
            <el-input
              v-model="loginForm.password"
              type="password"
              show-password
              size="large"
              placeholder="密码"
              clearable
              class="auth-input"
              :maxlength="YDDM_PASSWORD_MAX_LEN"
            />
          </el-form-item>
          <el-button
            type="primary"
            size="large"
            class="auth-submit mt-1 w-full"
            :loading="loginSubmitting"
            @click="onLogin"
          >
            登录
          </el-button>
        </el-form>

        <p class="mt-4 text-center text-sm text-slate-600">
          还没有账户？
          <button
            type="button"
            class="font-medium text-[#2563eb] hover:text-[#1d4ed8] focus:outline-none focus-visible:underline"
            @click="panel = 'register'"
          >
            立即注册
          </button>
        </p>
      </template>

      <template v-else>
        <h2 class="mb-6 flex items-center justify-center gap-2 text-base font-semibold text-slate-900">
          <span class="text-lg leading-none" aria-hidden="true">✉️</span>
          注册账户
        </h2>

        <el-form
          ref="registerFormRef"
          :model="registerForm"
          :rules="registerRules"
          class="auth-form"
          label-position="top"
          @submit.prevent
        >
          <el-form-item prop="captcha">
            <el-input v-model="registerForm.captcha" size="large" placeholder="验证码" clearable class="auth-input" />
          </el-form-item>
          <el-form-item prop="email">
            <el-input v-model="registerForm.email" size="large" placeholder="邮箱（可选）" clearable class="auth-input" />
          </el-form-item>
          <el-form-item prop="phone_num">
            <el-input
              v-model="registerForm.phone_num"
              size="large"
              placeholder="11位手机号（可选）"
              clearable
              class="auth-input"
              maxlength="20"
            />
          </el-form-item>
          <el-form-item prop="password">
            <el-input
              v-model="registerForm.password"
              type="password"
              show-password
              size="large"
              placeholder="密码（最多32位）"
              clearable
              class="auth-input"
              :maxlength="YDDM_PASSWORD_MAX_LEN"
            />
          </el-form-item>
          <el-button
            type="primary"
            size="large"
            class="auth-submit mt-1 w-full"
            :loading="registerSubmitting"
            @click="onRegister"
          >
            注册
          </el-button>
        </el-form>

        <p class="mt-4 text-center text-sm text-slate-600">
          已有账户？
          <button
            type="button"
            class="font-medium text-[#2563eb] hover:text-[#1d4ed8] focus:outline-none focus-visible:underline"
            @click="panel = 'login'"
          >
            返回登录
          </button>
        </p>
      </template>
    </section>

    <section
      class="auth-card rounded-xl border border-slate-200/80 bg-white p-6 shadow-sm"
      aria-labelledby="yddm-customer-service-heading"
    >
      <h3
        id="yddm-customer-service-heading"
        class="mb-5 flex items-center justify-center gap-2 text-base font-semibold text-slate-900"
      >
        <span class="text-lg leading-none text-red-500" aria-hidden="true">📞</span>
        联系客服
      </h3>

      <div
        class="mx-auto flex aspect-square max-w-[200px] items-center justify-center rounded-lg border-2 border-dashed border-slate-200 bg-slate-50"
      >
        <img
          v-if="customerServiceQrUrl"
          :src="customerServiceQrUrl"
          alt="客服二维码"
          class="max-h-full max-w-full object-contain p-3"
          loading="lazy"
          decoding="async"
        />
        <span v-else class="text-sm text-slate-400">客服二维码</span>
      </div>

      <p class="mt-4 text-center text-sm text-slate-500">扫码添加客服，获取专属支持</p>
    </section>
  </div>
</template>

<style scoped>
.auth-form :deep(.el-form-item__label) {
  display: none;
}

.auth-form :deep(.el-form-item) {
  margin-bottom: 1rem;
}

.auth-input :deep(.el-input__wrapper) {
  border-radius: 0.5rem;
  box-shadow: 0 0 0 1px rgb(226 232 240) inset;
}

.auth-input :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px rgb(203 213 225) inset;
}

.auth-input :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #2563eb inset;
}

.auth-submit {
  --el-button-bg-color: #2563eb;
  --el-button-border-color: #2563eb;
  --el-button-hover-bg-color: #1d4ed8;
  --el-button-hover-border-color: #1d4ed8;
  --el-button-active-bg-color: #1e40af;
  --el-button-active-border-color: #1e40af;
  border-radius: 0.5rem;
  font-weight: 500;
}
</style>

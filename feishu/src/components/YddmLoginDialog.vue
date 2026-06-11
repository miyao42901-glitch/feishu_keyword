<script setup lang="ts">
/**
 * 首页登录 / 注册：与设计稿一致的弹框（含客服二维码区）。
 */
import { Close } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, nextTick, onScopeDispose, reactive, ref, watch } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import {
  CN_MOBILE_RE,
  EMAIL_RE,
  normalizeCnMobileInput,
  prefixRegisterEmail,
  validateLoginPhoneOrEmail,
  YDDM_PASSWORD_MAX_LEN,
} from '@/lib/yddm-auth-validators'
import {
  buildYddmCaptchaImageUrl,
  yddmLogin,
  yddmRegister,
  type YddmLoginRequest,
  type YddmRegisterRequest,
} from '@/lib/yddm-api'
import { useAccountPointsStore } from '@/stores/accountPoints'
import { useGlobalSettingsStore } from '@/stores/globalSettings'
import { flushAnalytics, trackPageView, trackUserProfile } from '@/lib/analytics'
import { useYddmAuthStore } from '@/stores/yddmAuth'

defineOptions({ name: 'YddmLoginDialog' })

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [v: boolean]
}>()

const globalSettings = useGlobalSettingsStore()
const yddmAuth = useYddmAuthStore()
const accountPoints = useAccountPointsStore()

type AuthPanel = 'login' | 'register'
const panel = ref<AuthPanel>('login')

const loginFormRef = ref<FormInstance>()
const loginSubmitting = ref(false)
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
const registerSubmitting = ref(false)
const registerForm = reactive({
  phone_num: '',
  email: '',
  captcha: '',
  password: '',
  confirmPassword: '',
})

/** 合法 11 位国内手机号时展示并校验图片验证码 */
const registerCaptchaVisible = computed(() =>
  CN_MOBILE_RE.test(normalizeCnMobileInput(registerForm.phone_num.trim())),
)

function validateRegisterPhone(_rule: unknown, value: unknown, callback: (e?: Error) => void) {
  const raw = typeof value === 'string' ? value : ''
  const s = raw.trim()
  if (!s) {
    callback(new Error('请输入手机号'))
    return
  }
  const m = normalizeCnMobileInput(s)
  if (!CN_MOBILE_RE.test(m)) {
    callback(new Error('请输入11位中国大陆手机号'))
    return
  }
  callback()
}

const registerRules = computed<FormRules>(() => {
  const rules: FormRules = {
    phone_num: [{ validator: validateRegisterPhone, trigger: 'blur' }],
    email: [
      { required: true, message: '请输入邮箱', trigger: 'blur' },
      {
        validator: (_rule, value, callback) => {
          const s = typeof value === 'string' ? value.trim() : ''
          if (!EMAIL_RE.test(s)) {
            callback(new Error('邮箱格式不正确'))
            return
          }
          callback()
        },
        trigger: 'blur',
      },
    ],
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
        trigger: 'blur',
      },
    ],
    confirmPassword: [
      { required: true, message: '请再次输入密码', trigger: 'blur' },
      {
        validator: (_rule, value, callback) => {
          const s = typeof value === 'string' ? value : ''
          if (s !== registerForm.password) {
            callback(new Error('两次输入的密码不一致'))
            return
          }
          callback()
        },
        trigger: 'blur',
      },
    ],
  }
  if (registerCaptchaVisible.value) {
    rules.captcha = [{ required: true, message: '请输入图中的验证码', trigger: 'blur' }]
  }
  return rules
})

/** 登录弹框底部客服二维码：默认 `public/custom.png`，可由环境变量覆盖 */
const supportQrUrl =
  (import.meta.env.VITE_CUSTOMER_SERVICE_QR_URL as string | undefined)?.trim() ||
  `${import.meta.env.BASE_URL}custom.png`

/** 验证码 `<img src>`：优先 blob URL（fetch 拉图，避免直连被拦）；失败时回退为接口 URL */
const captchaImage = ref('')

let captchaBlobRevoke: (() => void) | null = null

function revokeCaptchaBlobUrl() {
  if (captchaBlobRevoke) {
    captchaBlobRevoke()
    captchaBlobRevoke = null
  }
}

function clearCaptchaState() {
  revokeCaptchaBlobUrl()
  captchaImage.value = ''
}

function captchaFetchHref(built: string): string {
  if (built.startsWith('http://') || built.startsWith('https://')) return built
  return new URL(built, window.location.origin).href
}

/** 刷新图片验证码；合法手机号时附带 phone_num */
async function refreshCaptcha() {
  revokeCaptchaBlobUrl()
  captchaImage.value = ''
  const m = normalizeCnMobileInput(registerForm.phone_num.trim())
  const built = CN_MOBILE_RE.test(m) ? buildYddmCaptchaImageUrl(m) : buildYddmCaptchaImageUrl()
  const fetchUrl = captchaFetchHref(built)

  try {
    const res = await fetch(fetchUrl, { method: 'GET', credentials: 'omit', cache: 'no-store' })
    if (!res.ok) throw new Error(String(res.status))
    const blob = await res.blob()
    if (blob.size < 16) throw new Error('empty')
    const ct = (blob.type || res.headers.get('content-type') || '').toLowerCase()
    if (ct.includes('json') || ct.includes('text/html')) {
      const t = await blob.text()
      throw new Error(t.slice(0, 120) || 'unexpected')
    }
    const objectUrl = URL.createObjectURL(blob)
    captchaBlobRevoke = () => URL.revokeObjectURL(objectUrl)
    captchaImage.value = objectUrl
  } catch {
    captchaImage.value = fetchUrl
  }
}

onScopeDispose(() => {
  clearCaptchaState()
})

async function tryRefreshMe(clearSessionOnError: boolean) {
  if (!yddmAuth.isLoggedIn) return
  try {
    const u = await yddmAuth.refreshMe()
    accountPoints.syncFromYddmUser(u)
    const key = u?.api_key?.trim()
    if (key) globalSettings.authCode = key
    if (u?.id != null) {
      trackUserProfile({ userId: u.id, phone: u.phone_num })
      void flushAnalytics()
    }
  } catch (e) {
    const msg = e instanceof Error ? e.message : '加载个人信息失败'
    if (clearSessionOnError) {
      yddmAuth.clearSession()
      globalSettings.authCode = ''
      accountPoints.resetToDefaultBalance()
      ElMessage.warning(`${msg}，请重新登录`)
    } else {
      ElMessage.error(`${msg}，已保留登录态与登录接口返回的资料`)
    }
  }
}

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
      accountPoints.syncFromYddmUser(data.user)
      await tryRefreshMe(false)
      const apiKey = data?.user?.api_key?.trim() || yddmAuth.me?.api_key?.trim()
      if (apiKey) globalSettings.authCode = apiKey
      ElMessage.success('登录成功，已写入顶部 API-Key')
    }
    emit('update:modelValue', false)
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '登录失败')
  } finally {
    loginSubmitting.value = false
  }
}

function buildRegisterPayload(): YddmRegisterRequest {
  return {
    captcha: registerForm.captcha.trim(),
    password: registerForm.password,
    phone_num: normalizeCnMobileInput(registerForm.phone_num.trim()),
    email: prefixRegisterEmail(registerForm.email),
  }
}

async function onRegisterAndLogin() {
  registerSubmitting.value = true
  try {
    await registerFormRef.value?.validate().catch(() => Promise.reject())
    const payload = buildRegisterPayload()
    await yddmRegister(payload)
    ElMessage.success('注册成功')

    const phoneForApi = normalizeCnMobileInput(registerForm.phone_num.trim())
    const loginPayload: YddmLoginRequest = {
      phone_num: phoneForApi,
      password: registerForm.password,
    }
    const data = await yddmLogin(loginPayload)
    if (!data?.access_token?.trim()) {
      const apiKeyOnly = data?.user?.api_key?.trim()
      if (apiKeyOnly) globalSettings.authCode = apiKeyOnly
      ElMessage.success('已自动登录（响应中未包含 access_token）')
    } else {
      yddmAuth.setFromLogin(data)
      accountPoints.syncFromYddmUser(data.user)
      await tryRefreshMe(false)
      const apiKey = data?.user?.api_key?.trim() || yddmAuth.me?.api_key?.trim()
      if (apiKey) globalSettings.authCode = apiKey
      ElMessage.success('已自动登录，已写入顶部 API-Key')
    }
    emit('update:modelValue', false)
  } catch (e) {
    registerForm.captcha = ''
    void refreshCaptcha()
    ElMessage.error(e instanceof Error ? e.message : '注册或登录失败')
  } finally {
    registerSubmitting.value = false
  }
}

function close() {
  emit('update:modelValue', false)
}

function onLogoutFromDialog() {
  yddmAuth.clearSession()
  globalSettings.authCode = ''
  accountPoints.resetToDefaultBalance()
  ElMessage.success('已退出登录')
  close()
}

function onRegisterClick() {
  panel.value = 'register'
  void nextTick(() => registerFormRef.value?.clearValidate())
}

function onBackToLogin() {
  panel.value = 'login'
  void nextTick(() => loginFormRef.value?.clearValidate())
}

watch(registerCaptchaVisible, (v) => {
  if (v) {
    void nextTick(() => void refreshCaptcha())
  } else {
    clearCaptchaState()
    registerForm.captcha = ''
  }
})

watch(
  () => props.modelValue,
  (open) => {
    if (open) {
      trackPageView('登录', 'dialog')
      panel.value = 'login'
      Object.assign(loginForm, { phone_num: '', password: '' })
      Object.assign(registerForm, {
        phone_num: '',
        email: '',
        captcha: '',
        password: '',
        confirmPassword: '',
      })
      clearCaptchaState()
      void nextTick(() => {
        loginFormRef.value?.clearValidate()
        registerFormRef.value?.clearValidate()
      })
    } else {
      clearCaptchaState()
    }
  },
)
</script>

<template>
  <el-dialog
    :model-value="modelValue"
    width="92%"
    :class="'yddm-login-dialog'"
    align-center
    append-to-body
    :show-close="false"
    destroy-on-close
    @update:model-value="emit('update:modelValue', $event)"
  >
    <template #header>
      <div class="yddm-login-dialog__header">
        <div class="yddm-login-dialog__title-row">
          <template v-if="panel === 'login'">
            <span class="yddm-login-dialog__key-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                <path
                  d="M14.5 2a4.5 4.5 0 0 0-4.42 5.33L3 14.41V19h4v-2h2v-2h2.17l3.09-3.09A4.5 4.5 0 1 0 14.5 2Zm0 2a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5Z"
                />
              </svg>
            </span>
            <span class="yddm-login-dialog__title">登录账户获取API-Key</span>
          </template>
          <template v-else>
            <span class="yddm-login-dialog__key-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                <path
                  d="M14.5 2a4.5 4.5 0 0 0-4.42 5.33L3 14.41V19h4v-2h2v-2h2.17l3.09-3.09A4.5 4.5 0 1 0 14.5 2Zm0 2a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5Z"
                />
              </svg>
            </span>
            <span class="yddm-login-dialog__title">注册新账户</span>
          </template>
        </div>
        <button type="button" class="yddm-login-dialog__close" aria-label="关闭" @click="close">
          <el-icon :size="18"><Close /></el-icon>
        </button>
      </div>
    </template>

    <div v-if="yddmAuth.isLoggedIn" class="yddm-login-dialog__logged-in">
      <p class="yddm-login-dialog__logged-in-text">当前已登录，API-Key 已同步到顶部授权码。</p>
      <div class="yddm-login-dialog__logged-in-actions">
        <button type="button" class="yddm-login-dialog__logout-btn" @click="onLogoutFromDialog">
          退出登录
        </button>
        <button type="button" class="yddm-login-dialog__primary-btn yddm-login-dialog__logged-in-primary" @click="close">
          知道了
        </button>
      </div>
    </div>

    <template v-else-if="panel === 'login'">
      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        class="yddm-login-dialog__form"
        label-position="top"
        @submit.prevent="onLogin"
      >
        <el-form-item prop="phone_num">
          <el-input
            v-model="loginForm.phone_num"
            size="large"
            placeholder="手机号/邮箱"
            clearable
            maxlength="128"
            class="yddm-login-dialog__input"
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
            class="yddm-login-dialog__input"
            :maxlength="YDDM_PASSWORD_MAX_LEN"
          />
        </el-form-item>
        <button
          type="button"
          class="yddm-login-dialog__primary-btn"
          :disabled="loginSubmitting"
          @click="onLogin"
        >
          <span v-if="loginSubmitting" class="yddm-login-dialog__btn-loading">登录中…</span>
          <span v-else>登录</span>
        </button>
      </el-form>

      <p class="yddm-login-dialog__register-line">
        还没有账户？
        <button type="button" class="yddm-login-dialog__link" @click="onRegisterClick">立即注册</button>
      </p>
    </template>

    <template v-else>
      <el-form
        ref="registerFormRef"
        :model="registerForm"
        :rules="registerRules"
        class="yddm-login-dialog__form"
        label-position="top"
        @submit.prevent="onRegisterAndLogin"
      >
        <el-form-item prop="phone_num">
          <el-input
            v-model="registerForm.phone_num"
            size="large"
            placeholder="手机号"
            clearable
            maxlength="20"
            class="yddm-login-dialog__input"
          />
        </el-form-item>
        <el-form-item prop="email">
          <el-input
            v-model="registerForm.email"
            size="large"
            placeholder="邮箱"
            clearable
            maxlength="128"
            class="yddm-login-dialog__input"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="registerForm.password"
            type="password"
            show-password
            size="large"
            placeholder="密码"
            clearable
            class="yddm-login-dialog__input"
            :maxlength="YDDM_PASSWORD_MAX_LEN"
          />
        </el-form-item>
        <el-form-item prop="confirmPassword">
          <el-input
            v-model="registerForm.confirmPassword"
            type="password"
            show-password
            size="large"
            placeholder="确认密码"
            clearable
            class="yddm-login-dialog__input"
            :maxlength="YDDM_PASSWORD_MAX_LEN"
          />
        </el-form-item>
        <el-form-item v-if="registerCaptchaVisible" prop="captcha" class="yddm-login-dialog__captcha-item">
          <div class="yddm-login-dialog__captcha-row">
            <el-input
              v-model="registerForm.captcha"
              size="large"
              placeholder="请输入图中字符"
              clearable
              maxlength="32"
              class="yddm-login-dialog__input yddm-login-dialog__captcha-input-el"
            />
            <button
              type="button"
              class="yddm-login-dialog__captcha-thumb"
              title="点击刷新验证码"
              aria-label="点击刷新图片验证码"
              @click="void refreshCaptcha()"
            >
              <img
                v-if="captchaImage"
                :key="captchaImage"
                :src="captchaImage"
                class="yddm-login-dialog__captcha-img"
                alt=""
                referrerpolicy="no-referrer"
                decoding="async"
              />
            </button>
          </div>
        </el-form-item>
        <button
          type="button"
          class="yddm-login-dialog__primary-btn"
          :disabled="registerSubmitting"
          @click="onRegisterAndLogin"
        >
          <span v-if="registerSubmitting" class="yddm-login-dialog__btn-loading">提交中…</span>
          <span v-else>注册并登录</span>
        </button>
      </el-form>

      <p class="yddm-login-dialog__register-line">
        已有账户？
        <button type="button" class="yddm-login-dialog__link" @click="onBackToLogin">返回登录</button>
      </p>
    </template>

    <div class="yddm-login-dialog__support">
      <div class="yddm-login-dialog__support-inner">
        <div class="yddm-login-dialog__qr-wrap">
          <img
            :src="supportQrUrl"
            alt="客服二维码"
            class="yddm-login-dialog__qr-img"
            loading="lazy"
            decoding="async"
          />
        </div>
        <p class="yddm-login-dialog__support-text">扫码添加客服，获取专属支持</p>
      </div>
    </div>
  </el-dialog>
</template>

<style scoped>
.yddm-login-dialog__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding-right: 0;
}

.yddm-login-dialog__title-row {
  display: flex;
  min-width: 0;
  flex: 1;
  align-items: center;
  gap: 8px;
}

.yddm-login-dialog__key-icon {
  display: flex;
  flex-shrink: 0;
  width: 22px;
  height: 22px;
  align-items: center;
  justify-content: center;
  color: #1456f0;
}

.yddm-login-dialog__key-icon svg {
  display: block;
  width: 20px;
  height: 20px;
}

.yddm-login-dialog__title {
  font-size: 16px;
  font-weight: 600;
  line-height: 1.35;
  color: #1f2329;
}

.yddm-login-dialog__close {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  padding: 4px;
  margin: -4px -4px 0 0;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: #8f959e;
  cursor: pointer;
  transition:
    color 0.15s ease,
    background 0.15s ease;
}

.yddm-login-dialog__close:hover {
  background: #f2f3f5;
  color: #646a73;
}

.yddm-login-dialog__form :deep(.el-form-item) {
  margin-bottom: 14px;
}

.yddm-login-dialog__form :deep(.el-form-item__label) {
  display: none;
}

.yddm-login-dialog__input :deep(.el-input__wrapper) {
  border-radius: 4px;
  box-shadow: 0 0 0 1px #dee0e3 inset;
}

.yddm-login-dialog__input :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #c3c6cb inset;
}

.yddm-login-dialog__input :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #1456f0 inset;
}

.yddm-login-dialog__captcha-item :deep(.el-form-item__content) {
  line-height: 0;
}

.yddm-login-dialog__captcha-row {
  display: flex;
  gap: 10px;
  align-items: stretch;
  width: 100%;
}

.yddm-login-dialog__captcha-input-el {
  flex: 1;
  min-width: 0;
}

.yddm-login-dialog__captcha-thumb {
  box-sizing: border-box;
  display: flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  align-self: center;
  min-width: 120px;
  min-height: 40px;
  padding: 0;
  margin: 0;
  border: none;
  border-radius: 0;
  background: transparent;
  cursor: pointer;
  line-height: 0;
  transition: opacity 0.15s ease;
}

.yddm-login-dialog__captcha-thumb:hover {
  opacity: 0.88;
}

.yddm-login-dialog__captcha-thumb:focus-visible {
  outline: 2px solid #1456f0;
  outline-offset: 2px;
}

.yddm-login-dialog__captcha-thumb img,
.yddm-login-dialog__captcha-img {
  display: block;
  height: 40px;
  width: auto;
  max-width: 160px;
  object-fit: contain;
}

.yddm-login-dialog__primary-btn {
  box-sizing: border-box;
  display: flex;
  width: 100%;
  height: 44px;
  align-items: center;
  justify-content: center;
  padding: 0 16px;
  margin-top: 4px;
  border: none;
  border-radius: 4px;
  background: linear-gradient(90deg, #1456f0 0%, #4014f0 100%);
  color: #ffffff;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition:
    filter 0.15s ease,
    opacity 0.15s ease;
}


.yddm-login-dialog__primary-btn:hover:not(:disabled) {
  filter: brightness(1.06);
}

.yddm-login-dialog__primary-btn:active:not(:disabled) {
  filter: brightness(0.96);
}

.yddm-login-dialog__primary-btn:disabled {
  cursor: not-allowed;
  opacity: 0.75;
}

.yddm-login-dialog__btn-loading {
  font-size: 15px;
}

.yddm-login-dialog__register-line {
  margin: 16px 0 0;
  font-size: 14px;
  line-height: 1.5;
  color: #646a73;
  text-align: center;
}

.yddm-login-dialog__link {
  padding: 0;
  border: none;
  background: none;
  color: #1456f0;
  font-size: inherit;
  font-weight: 500;
  cursor: pointer;
}

.yddm-login-dialog__link:hover {
  text-decoration: underline;
}

.yddm-login-dialog__support {
  margin-top: 20px;
}

.yddm-login-dialog__support-inner {
  padding: 16px 14px 14px;
  background: #ededfe;
  border-radius: 8px;
}

.yddm-login-dialog__qr-wrap {
  display: flex;
  width: 140px;
  height: 140px;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
  overflow: hidden;
  background: #ffffff;
  border-radius: 8px;
}

.yddm-login-dialog__qr-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.yddm-login-dialog__qr-placeholder {
  font-size: 13px;
  color: #8f959e;
}

.yddm-login-dialog__support-text {
  margin: 12px 0 0;
  font-size: 13px;
  line-height: 1.45;
  color: #646a73;
  text-align: center;
}

.yddm-login-dialog__logged-in {
  padding: 8px 0 4px;
}

.yddm-login-dialog__logged-in-text {
  margin: 0 0 16px;
  font-size: 14px;
  line-height: 1.55;
  color: #646a73;
  text-align: center;
}

.yddm-login-dialog__logged-in-actions {
  display: flex;
  gap: 10px;
  align-items: stretch;
}

.yddm-login-dialog__logged-in-actions .yddm-login-dialog__primary-btn {
  margin-top: 0;
}

.yddm-login-dialog__logout-btn {
  box-sizing: border-box;
  display: inline-flex;
  flex: 1;
  min-height: 44px;
  align-items: center;
  justify-content: center;
  padding: 0 12px;
  border: 1px solid #dee0e3;
  border-radius: 8px;
  background: #ffffff;
  color: #646a73;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition:
    border-color 0.15s ease,
    background 0.15s ease,
    color 0.15s ease;
}

.yddm-login-dialog__logout-btn:hover {
  border-color: #f54a45;
  background: rgba(245, 74, 69, 0.06);
  color: #f54a45;
}

.yddm-login-dialog__logged-in-primary {
  flex: 1;
}
</style>

<style>
.yddm-login-dialog.el-dialog {
  width: min(420px, calc(100vw - 24px)) !important;
  max-width: calc(100vw - 16px);
  padding: 20px 20px 22px;
  border-radius: 12px;
}

.yddm-login-dialog .el-dialog__header {
  margin-right: 0;
  margin-bottom: 18px;
  padding: 0;
}

.yddm-login-dialog .el-dialog__body {
  padding: 0;
}
</style>

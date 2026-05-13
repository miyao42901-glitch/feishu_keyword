<script setup lang="ts">
import { reactive, ref } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import {
  getYddmApiBase,
  yddmLogin,
  yddmRegister,
  type YddmLoginRequest,
  type YddmRegisterRequest,
} from '@/lib/yddm-api'
import { useGlobalSettingsStore } from '@/stores/globalSettings'

defineOptions({ name: 'YddmAuthView' })

const globalSettings = useGlobalSettingsStore()

const active = ref<'login' | 'register'>('login')
const loginSubmitting = ref(false)
const registerSubmitting = ref(false)

const loginFormRef = ref<FormInstance>()
const loginForm = reactive({
  phone_num: '',
  password: '',
})
const loginRules: FormRules = {
  phone_num: [{ required: true, message: '请输入手机号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const registerFormRef = ref<FormInstance>()
const registerForm = reactive({
  captcha: '',
  email: '',
  password: '',
  phone_num: '',
})

const registerRules: FormRules = {
  captcha: [{ required: true, message: '请输入验证码', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

/** 替换为二维码图片 URL 后，「联系客服」区域将显示图片 */
const customerServiceQrUrl = ''

async function onLogin() {
  loginSubmitting.value = true
  try {
    await loginFormRef.value?.validate().catch(() => Promise.reject())
    const payload: YddmLoginRequest = {
      phone_num: loginForm.phone_num.trim(),
      password: loginForm.password,
    }
    const data = await yddmLogin(payload)
    const apiKey = data?.user?.api_key?.trim()
    if (apiKey) {
      globalSettings.authCode = apiKey
      ElMessage.success('登录成功，已写入顶部 API-Key')
    } else {
      ElMessage.success('登录成功（响应中未包含 api_key，未更新授权码）')
    }
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '登录失败')
  } finally {
    loginSubmitting.value = false
  }
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
    if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      ElMessage.warning('邮箱格式不正确')
      return
    }
    const payload: YddmRegisterRequest = {
      captcha: registerForm.captcha.trim(),
      password: registerForm.password,
    }
    if (email) payload.email = email
    if (phone) payload.phone_num = phone
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
  <div class="mx-auto flex w-full max-w-md flex-col gap-4">
    <div class="rounded-lg border border-slate-200 bg-slate-50/80 p-4 shadow-sm">
      <h2 class="mb-0.5 text-center text-base font-semibold text-slate-900">登录账户</h2>
      <p class="mb-4 text-center text-xs text-slate-500">
        请求根：{{ getYddmApiBase() }}（与飞书任务后端无关；开发环境经 Vite 代理转发至 yddm）
      </p>

      <el-tabs v-model="active" class="yddm-auth-tabs">
        <el-tab-pane label="登录" name="login">
          <el-form
            ref="loginFormRef"
            :model="loginForm"
            :rules="loginRules"
            label-position="top"
            class="mt-2"
            @submit.prevent
          >
            <el-form-item label="手机号" prop="phone_num">
              <el-input v-model="loginForm.phone_num" placeholder="手机号" clearable />
            </el-form-item>
            <el-form-item label="密码" prop="password">
              <el-input
                v-model="loginForm.password"
                type="password"
                show-password
                placeholder="密码"
                clearable
              />
            </el-form-item>
            <el-button type="primary" class="mt-1 w-full" :loading="loginSubmitting" @click="onLogin">
              登录
            </el-button>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="注册" name="register">
          <el-form
            ref="registerFormRef"
            :model="registerForm"
            :rules="registerRules"
            label-position="top"
            class="mt-2"
            @submit.prevent
          >
            <el-form-item label="验证码" prop="captcha">
              <el-input v-model="registerForm.captcha" placeholder="captcha" clearable />
            </el-form-item>
            <el-form-item label="邮箱（可选）" prop="email">
              <el-input v-model="registerForm.email" placeholder="email" clearable />
            </el-form-item>
            <el-form-item label="手机号（可选）" prop="phone_num">
              <el-input v-model="registerForm.phone_num" placeholder="phone_num" clearable />
            </el-form-item>
            <el-form-item label="密码" prop="password">
              <el-input
                v-model="registerForm.password"
                type="password"
                show-password
                placeholder="password"
                clearable
              />
            </el-form-item>
            <el-button
              type="primary"
              class="mt-1 w-full"
              :loading="registerSubmitting"
              @click="onRegister"
            >
              注册（POST /auth/register）
            </el-button>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </div>

    <section
      class="rounded-lg border border-slate-200 bg-white p-4 shadow-sm"
      aria-labelledby="yddm-customer-service-heading"
    >
      <h3 id="yddm-customer-service-heading" class="text-sm font-semibold text-slate-900">联系客服</h3>
      <div class="mt-3 overflow-hidden rounded-lg border border-dashed border-slate-300 bg-slate-50">
        <img
          v-if="customerServiceQrUrl"
          :src="customerServiceQrUrl"
          alt="客服二维码"
          class="mx-auto block max-h-44 w-full max-w-[11rem] object-contain p-2"
          loading="lazy"
          decoding="async"
        />
        <div
          v-else
          class="flex min-h-[10rem] flex-col items-center justify-center px-4 py-8 text-center"
        >
          <span class="text-xs text-slate-500">客服二维码</span>
        </div>
      </div>
      <p class="mt-3 text-center text-xs leading-relaxed text-slate-500">扫码添加客服，获取专属支持</p>
    </section>
  </div>
</template>

<style scoped>
.yddm-auth-tabs :deep(.el-tabs__header) {
  margin-bottom: 0;
}
</style>

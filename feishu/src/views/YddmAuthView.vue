<script setup lang="ts">
import { reactive, ref } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { yddmRegister, type YddmRegisterRequest } from '@/lib/yddm-api'

defineOptions({ name: 'YddmAuthView' })

const active = ref<'login' | 'register'>('login')
const loginSubmitting = ref(false)
const registerSubmitting = ref(false)

const loginFormRef = ref<FormInstance>()
const loginForm = reactive({
  account: '',
  password: '',
})
const loginRules: FormRules = {
  account: [{ required: true, message: '请输入邮箱或手机号', trigger: 'blur' }],
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

async function onLogin() {
  loginSubmitting.value = true
  try {
    await loginFormRef.value?.validate().catch(() => Promise.reject())
    ElMessage.info('登录接口路径与入参待你提供后再对接，当前为占位。')
  } catch {
    // 校验失败
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
  <div class="mx-auto w-full max-w-md">
    <div class="rounded-lg border border-slate-200 bg-slate-50/80 p-4 shadow-sm">
      <h2 class="mb-0.5 text-center text-base font-semibold text-slate-900">yddm 账号</h2>
      <p class="mb-4 text-center text-xs text-slate-500">接口前缀 https://api.yddm.com（与飞书任务后端无关）</p>

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
            <el-form-item label="邮箱或手机号" prop="account">
              <el-input v-model="loginForm.account" placeholder="占位，待登录接口" clearable />
            </el-form-item>
            <el-form-item label="密码" prop="password">
              <el-input
                v-model="loginForm.password"
                type="password"
                show-password
                placeholder="占位，待登录接口"
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
  </div>
</template>

<style scoped>
.yddm-auth-tabs :deep(.el-tabs__header) {
  margin-bottom: 0;
}
</style>

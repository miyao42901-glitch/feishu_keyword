<template>
  <div class="wrap">
    <el-card class="card" shadow="hover">
      <h2 class="title">飞书关键词监控管理后台</h2>
      <el-form :model="form" label-width="72px" @submit.prevent="onSubmit">
        <el-form-item label="用户名">
          <el-input v-model="form.username" autocomplete="username" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" autocomplete="current-password" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" native-type="submit" :loading="loading" style="width: 100%">登录</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import http, { unwrap } from '@/api/http'
import { useSessionStore } from '@/stores/session'

const route = useRoute()
const router = useRouter()
const session = useSessionStore()

const loading = ref(false)
const form = reactive({ username: '', password: '' })

async function onSubmit() {
  if (!form.username || !form.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    const res = await http.post('/api/admin/v1/system/login', {
      username: form.username,
      password: form.password,
    })
    const data = unwrap<{ token: string; admin: unknown }>(res)
    session.setToken(data.token)
    const redir = (route.query.redirect as string) || '/dashboard'
    await router.replace(redir)
  } catch {
    /* ElMessage 已在拦截器 */
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.wrap {
  min-height: 100vh;
  min-height: 100dvh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px 16px;
  box-sizing: border-box;
  background: linear-gradient(165deg, #e8efff 0%, #f5f8ff 45%, #ffffff 100%);
}
.card {
  width: 100%;
  max-width: 400px;
  border-radius: 12px;
  border: 1px solid rgba(64, 115, 250, 0.12);
  box-shadow: 0 12px 40px rgba(26, 35, 50, 0.08), 0 0 0 1px rgba(255, 255, 255, 0.8) inset;
}
.title {
  margin: 0 0 20px;
  text-align: center;
  font-weight: 700;
  font-size: 20px;
  color: #1a2332;
  letter-spacing: 0.03em;
}
</style>

<template>
  <el-dialog
    v-model="dialogVisible"
    title="账号登录"
    width="90%"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
  >
    <el-form :model="loginForm" :rules="rules" ref="loginFormRef" label-width="80px">
      <el-alert
        v-if="errorMessage"
        :title="errorMessage"
        type="error"
        show-icon
        :closable="false"
        style="margin-bottom: 16px;"
      />
      <el-form-item label="用户名" prop="username">
        <el-input v-model="loginForm.username" placeholder="请输入用户名" @input="clearError" />
      </el-form-item>
      <el-form-item label="密码" prop="password">
        <el-input v-model="loginForm.password" type="password" placeholder="请输入密码" @input="clearError" />
      </el-form-item>
    </el-form>
    <div class="protocol-section">
      <el-checkbox v-model="agreeProtocol" label="agree" @click="clearError">
        我已阅读并同意
        <el-link type="primary" href="https://static.dajiala.com:9224/static/HTMLPage/UserAgreement.html" target="_blank">《用户协议》</el-link>
        和
        <el-link type="primary" href="https://static.dajiala.com:9224/static/HTMLPage/ProtectionInform.html" target="_blank" @click="clearError">《个人信息保护政策》</el-link>
      </el-checkbox>
    </div>
    
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleLogin" :loading="loading">登录</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:visible', 'login-success'])

const dialogVisible = ref(props.visible)
const loginForm = ref({
  username: '',
  password: '',
})
const loading = ref(false)
const loginFormRef = ref(null)
const errorMessage = ref('')
const agreeProtocol = ref(true)

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ],
}

const clearError = () => {
  errorMessage.value = ''
}

const handleLogin = async () => {
  // 清除之前的错误信息
  errorMessage.value = ''
  
  if (!loginFormRef.value) return
  
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        if (!agreeProtocol.value) {
          errorMessage.value = '请先阅读并同意协议'
        }
        else{
        // 以form形式传参数
          const formData = new FormData();
          formData.append('username', loginForm.value.username);
          formData.append('password', loginForm.value.password);
          formData.append('agree_protocol', agreeProtocol.value ? 1 : 0);
          
          const res = await axios.post('https://www.dajiala.com/fbmain/account/v1/login', formData, {
            headers: {
              'Content-Type': 'multipart/form-data'
            }
          })
          
          if (res.data && res.data.error_code === 0) {
            emit('login-success', res.data)
            dialogVisible.value = false
          } else {
            errorMessage.value = res.data?.msg || '登录失败'
          }
        }
      } catch (error) {
        console.error('登录失败:', error)
        errorMessage.value = '网络错误，请稍后重试'
      } finally {
        loading.value = false
      }
    }
  })
}

// 监听visible变化
import { watch } from 'vue'
watch(() => props.visible, (newVal) => {
  dialogVisible.value = newVal
  // 当对话框关闭时重置表单
  if (!newVal && loginFormRef.value) {
    loginFormRef.value.resetFields()
    errorMessage.value = ''
  }
})

// 当对话框关闭时通知父组件
watch(dialogVisible, (newVal) => {
  emit('update:visible', newVal)
  // 当对话框关闭时重置表单
  if (!newVal && loginFormRef.value) {
    loginFormRef.value.resetFields()
    errorMessage.value = ''
  }
})
</script>

<style scoped>
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}


.protocol-section {
  margin-top: 16px;
  padding: 0 20px;
}

.protocol-section .el-checkbox {
  font-size: 12px;
  color: #666;
}

.protocol-section .el-link {
  font-size: 12px;
}
</style>
<template>
  <el-dialog
    v-model="dialogVisible"
    :title="t('loginDialog.title')"
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
      <el-form-item :label="t('loginDialog.fields.username')" prop="username">
        <el-input v-model="loginForm.username" :placeholder="t('loginDialog.placeholders.username')" @input="clearError" />
      </el-form-item>
      <el-form-item :label="t('loginDialog.fields.password')" prop="password">
        <el-input v-model="loginForm.password" type="password" :placeholder="t('loginDialog.placeholders.password')" @input="clearError" />
      </el-form-item>
    </el-form>
    <div class="protocol-section">
      <el-checkbox v-model="agreeProtocol" label="agree" @click="clearError">
        {{ t('loginDialog.protocol') }}
        <el-link type="primary" href="https://static.dajiala.com:9224/static/HTMLPage/UserAgreement.html" target="_blank">{{ t('loginDialog.agreement.userAgreement') }}</el-link>
        {{ '&' }}
        <el-link type="primary" href="https://static.dajiala.com:9224/static/HTMLPage/ProtectionInform.html" target="_blank">{{ t('loginDialog.agreement.privacyPolicy') }}</el-link>
      </el-checkbox>
    </div>
    
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="dialogVisible = false">{{ t('loginDialog.buttons.cancel') }}</el-button>
        <el-button type="primary" @click="handleLogin" :loading="loading">{{ t('loginDialog.buttons.login') }}</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { useI18n } from 'vue-i18n'

const { t } = useI18n();

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
    { required: true, message: t('loginDialog.messages.requiredUsername'), trigger: 'blur' }
  ],
  password: [
    { required: true, message: t('loginDialog.messages.requiredPassword'), trigger: 'blur' }
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
          errorMessage.value = t('loginDialog.messages.agreeProtocol')
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
            errorMessage.value = res.data?.msg || t('loginDialog.messages.loginFailed')
          }
        }
      } catch (error) {
        console.error('登录失败:', error)
        errorMessage.value = t('loginDialog.messages.networkError')
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
}

.protocol-section .el-checkbox {
  font-size: 12px;
  color: #666;
}

.protocol-section .el-link {
  font-size: 12px;
}
</style>
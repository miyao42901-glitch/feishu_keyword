<template>
  <el-dialog
    v-model="dialogVisible"
    :title="t('wechatLoginDialog.title')"
    width="90%"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
  >
    <div class="wechat-login-container">
      <!-- 二维码登录部分 -->
      <div class="qrcode-section" v-if="qrcodeImage && !showRegisterForm">
        <div :class="['qrcode-wrapper', { 'blur': !agreeProtocol }]">
          <img :src="qrcodeImage" alt="微信登录二维码" class="qrcode-image" />
          <div v-if="!agreeProtocol" class="blur-overlay">
            <p>{{ t('wechatLoginDialog.agreeProtocol') }}</p>
          </div>
        </div>
        <p class="qrcode-tip">{{ t('wechatLoginDialog.tip') }}</p>
        <div class="protocol-section">
          <el-checkbox v-model="agreeProtocol" label="agree">
            {{ t('wechatLoginDialog.protocol') }}
            <el-link type="primary" href="https://static.dajiala.com:9224/static/HTMLPage/UserAgreement.html" target="_blank">{{ t('wechatLoginDialog.agreement.userAgreement') }}</el-link>
            {{ '&' }}
            <el-link type="primary" href="https://static.dajiala.com:9224/static/HTMLPage/ProtectionInform.html" target="_blank">{{ t('wechatLoginDialog.agreement.privacyPolicy') }}</el-link>
          </el-checkbox>
        </div>
      </div>
      <!-- 注册表单部分 -->
      <div class="register-section" v-if="showRegisterForm">
        <el-form :model="registerForm" :rules="registerRules" ref="registerFormRef" label-width="80px">
          <el-form-item label="手机号" prop="phone">
            <el-input v-model="registerForm.phone" placeholder="请输入手机号" />
          </el-form-item>
          <el-form-item label="密码" prop="password">
            <el-input v-model="registerForm.password" type="password" placeholder="请输入密码" />
          </el-form-item>
          <el-form-item label="确认密码" prop="confirmPassword">
            <el-input v-model="registerForm.confirmPassword" type="password" placeholder="请确认密码" />
          </el-form-item>
        </el-form>
      </div>
      <!-- 加载部分 -->
      <div class="loading-section" v-else-if="!qrcodeImage && !showRegisterForm">
        <el-icon class="loading-icon"><i-ep-loading /></el-icon>
        <p>{{ t('wechatLoginDialog.loading') }}</p>
      </div>
    </div>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleCancel">{{ t('wechatLoginDialog.buttons.cancel') }}</el-button>
        <el-button type="primary" @click="handleRegister" v-if="showRegisterForm">注册</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElForm, ElFormItem, ElInput } from 'element-plus'
import axios from 'axios'
import pluginAPI from '@/utils/request'
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
const qrcodeImage = ref('')
const checkInterval = ref(null)
const agreeProtocol = ref(true)
const showRegisterForm = ref(false)
const registerFormRef = ref(null)
const loginForm = ref({
  token: ''
})
const registerForm = ref({
  phone: '',
  password: '',
  confirmPassword: '',
  token: ''
})
const registerRules = ref({
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于8位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== registerForm.value.password) {
          callback(new Error('两次输入密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
})

// 生成二维码
const generateQrcode = async () => {
  try {
    console.log('获取微信登录二维码...')

    const res = await axios.get('https://www.dajiala.com/fbmain/account/v1/qrcode')
    if (res.data && res.data.error_code === 0) {
      const img = res.data.data.img;
      loginForm.value.token = res.data.data.qrcode;
      qrcodeImage.value = img;
      startCheckLoginStatus()
    }
    // 开始检测登录状态
  } catch (error) {
    console.error('生成二维码失败:', error)
    ElMessage.error(t('wechatLoginDialog.messages.qrcodeFailed'))
    dialogVisible.value = false
  }
}

// 开始检测登录状态
const startCheckLoginStatus = () => {
  let count = 0
  const maxChecks = 100 // 最多检测次数
  
  checkInterval.value = setInterval(async () => {
    count++
    
    try {
      // 这里将来会调用检测登录状态的接口
      console.log('检测登录状态...')
      
      const formData = new FormData();
      formData.append('token', loginForm.value.token);
      formData.append('agree_protocol', agreeProtocol.value ? 1 : 0);
      
      const res = await axios.post('https://www.dajiala.com/fbmain/account/v1/login', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      
      if (res.data && res.data.error_code === 0) {
        if (res.data.data.type === 0) {
          // 需要注册
          clearInterval(checkInterval.value)
          showRegisterForm.value = true
          registerForm.value.token = res.data.data.accessToken
        } else {
          // 登录成功
          clearInterval(checkInterval.value)
          ElMessage.success(t('wechatLoginDialog.messages.loginSuccess'))
          emit('login-success', res.data)
          dialogVisible.value = false
        }
      }
    } catch (error) {
      console.error('检测登录状态失败:', error)
    }
    
    // 超时处理
  if (count >= maxChecks) {
    clearInterval(checkInterval.value)
    ElMessage.error(t('wechatLoginDialog.messages.loginTimeout'))
    dialogVisible.value = false
  }
  }, 2000) // 每2秒检测一次
}

// 处理注册
const handleRegister = async () => {
  if (!registerFormRef.value) return
  
  try {
    await registerFormRef.value.validate()
    
    // const res = await axios.post('https://www.dajiala.com/fbmain/account/v1/register', {
    //   accessToken: registerForm.value.token,
    //   phone: registerForm.value.phone,
    //   password: registerForm.value.password,
    //   confirm: registerForm.value.confirmPassword,
    //   bd_vid: '',
    //   code: ''
    // })

    const res = await pluginAPI.post('/plugin_register_forward', {
      accessToken: registerForm.value.token,
      phone: registerForm.value.phone,
      password: registerForm.value.password,
      confirm: registerForm.value.confirmPassword,
      bd_vid: '',
      code: ''
    })
    
    if (res.data && res.data.error_code === 0) {
      ElMessage.success('注册成功')
      ElMessage.success(t('wechatLoginDialog.messages.loginSuccess'))
      emit('login-success', {data: {accessToken: registerForm.value.token}})
      dialogVisible.value = false
    } else {
      ElMessage.error(res.data.error_msg || '注册失败')
    }
  } catch (error) {
    console.error('注册失败:', error)
    ElMessage.error('注册失败，请稍后重试')
  }
}

// 取消登录
const handleCancel = () => {
  if (checkInterval.value) {
    clearInterval(checkInterval.value)
  }
  dialogVisible.value = false
}

// 监听visible变化
import { watch } from 'vue'
watch(() => props.visible, (newVal) => {
  dialogVisible.value = newVal
  if (newVal) {
    showRegisterForm.value = false
    registerForm.value = {
      phone: '',
      password: '',
      confirmPassword: '',
      token: ''
    }
    generateQrcode()
  } else {
    // 对话框关闭时清理
    qrcodeImage.value = ''
    showRegisterForm.value = false
    if (checkInterval.value) {
      clearInterval(checkInterval.value)
    }
  }
})

// 当对话框关闭时通知父组件
watch(dialogVisible, (newVal) => {
  emit('update:visible', newVal)
})
</script>

<style scoped>
.wechat-login-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 0;
}

.qrcode-section {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.qrcode-wrapper {
  position: relative;
  width: 200px;
  height: 200px;
  margin-bottom: 16px;
  overflow: hidden;
}

.qrcode-image {
  width: 100%;
  height: 100%;
  transition: filter 0.3s ease;
}

.qrcode-wrapper.blur .qrcode-image {
  filter: blur(5px);
}

.blur-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: var(--el-overlay-color);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10;
}

.blur-overlay p {
  color: var(--el-text-color-regular);
  font-size: 14px;
  text-align: center;
  margin: 0;
  padding: 0 20px;
}

.qrcode-tip {
  font-size: 14px;
  color: var(--el-text-color-regular);
  margin: 0 0 16px 0;
}

.protocol-section {
  margin-top: 16px;
}

.protocol-section .el-checkbox {
  font-size: 12px;
  color: var(--el-text-color-regular);
}

.protocol-section .el-link {
  font-size: 12px;
}

.loading-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 0;
}

.loading-icon {
  font-size: 48px;
  color: var(--el-color-primary);
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
}

.register-section {
  width: 100%;
  max-width: 400px;
  padding: 20px 0;
}

.register-section .el-form {
  width: 100%;
}

.register-section .el-form-item {
  margin-bottom: 16px;
}
</style>
<template>
  <el-dialog
    v-model="dialogVisible"
    title="微信扫码登录"
    width="90%"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
  >
    <div class="wechat-login-container">
      <div class="qrcode-section" v-if="qrcodeImage">
        <div :class="['qrcode-wrapper', { 'blur': !agreeProtocol }]">
          <img :src="qrcodeImage" alt="微信登录二维码" class="qrcode-image" />
          <div v-if="!agreeProtocol" class="blur-overlay">
            <p>请先阅读并同意协议</p>
          </div>
        </div>
        <p class="qrcode-tip">请使用微信扫码登录</p>
        <div class="protocol-section">
          <el-checkbox v-model="agreeProtocol" label="agree">
            我已阅读并同意
            <el-link type="primary" href="https://static.dajiala.com:9224/static/HTMLPage/UserAgreement.html" target="_blank">《用户协议》</el-link>
            和
            <el-link type="primary" href="https://static.dajiala.com:9224/static/HTMLPage/ProtectionInform.html" target="_blank">《个人信息保护政策》</el-link>
          </el-checkbox>
        </div>
      </div>
      <div class="loading-section" v-else>
        <el-icon class="loading-icon"><i-ep-loading /></el-icon>
        <p>正在生成二维码...</p>
      </div>
    </div>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleCancel">取消</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

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
const loginForm = ref({
  token: ''
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
    ElMessage.error('生成二维码失败，请稍后重试')
    dialogVisible.value = false
  }
}

// 开始检测登录状态
const startCheckLoginStatus = () => {
  let count = 0
  const maxChecks = 100 // 最多检测300次
  
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
        clearInterval(checkInterval.value)
        ElMessage.success('登录成功')
        emit('login-success', res.data)
        dialogVisible.value = false
      }
    } catch (error) {
      console.error('检测登录状态失败:', error)
    }
    
    // 超时处理
    if (count >= maxChecks) {
      clearInterval(checkInterval.value)
      ElMessage.error('登录超时，请重新扫码')
      dialogVisible.value = false
    }
  }, 2000) // 每2秒检测一次
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
    generateQrcode()
  } else {
    // 对话框关闭时清理
    qrcodeImage.value = ''
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
  background-color: rgba(255, 255, 255, 0.8);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10;
}

.blur-overlay p {
  color: #666;
  font-size: 14px;
  text-align: center;
  margin: 0;
  padding: 0 20px;
}

.qrcode-tip {
  font-size: 14px;
  color: #666;
  margin: 0 0 16px 0;
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

.loading-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 0;
}

.loading-icon {
  font-size: 48px;
  color: #409EFF;
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
</style>
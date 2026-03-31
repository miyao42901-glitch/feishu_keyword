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
        <img :src="qrcodeImage" alt="微信登录二维码" class="qrcode-image" />
        <p class="qrcode-tip">请使用微信扫码登录</p>
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
import { ref, defineProps, defineEmits, onMounted } from 'vue'
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
  const maxChecks = 100 // 最多检测100次（5分钟）
  
  checkInterval.value = setInterval(async () => {
    count++
    
    try {
      // 这里将来会调用检测登录状态的接口
      console.log('检测登录状态...')
      
      const formData = new FormData();
      formData.append('token', loginForm.value.token);
      formData.append('agree_protocol', 1);
      
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

.qrcode-image {
  width: 200px;
  height: 200px;
  margin-bottom: 16px;
}

.qrcode-tip {
  font-size: 14px;
  color: #666;
  margin: 0;
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
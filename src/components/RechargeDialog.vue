<template>
  <el-dialog
    v-model="dialogVisible"
    title="充值"
    width="90%"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
  >
    <el-form :model="rechargeForm" :rules="rules" ref="rechargeFormRef">
      <el-alert
        v-if="errorMessage"
        :title="errorMessage"
        type="error"
        show-icon
        :closable="false"
        style="margin-bottom: 16px;"
      />
      
      <el-form-item label="充值金额" prop="amount">
        <el-input
          v-model.number="rechargeForm.amount"
          type="number"
          placeholder="请输入充值金额"
          min="5"
          step="1"
          @input="handleAmountInput"
        />
        <div class="gift-info"">
          额外赠送：￥{{ giftAmount }}
        </div>
      </el-form-item>
      
      <el-form-item>
        <div class="preset-amounts">
          <el-button
            v-for="item in presetAmounts"
            :key="item.amount"
            :type="rechargeForm.amount === item.amount ? 'primary' : 'default'"
            @click="selectPresetAmount(item.amount)"
          >
            <div class="button-content">
              <div class="amount">￥{{ item.amount }}</div>
              <div class="desc">{{ item.gift ? `送￥${item.gift}` : '无赠送' }}</div>
            </div>
          </el-button>
        </div>
      </el-form-item>
    </el-form>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleRecharge" :loading="loading">充值</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, defineProps, defineEmits, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:visible', 'recharge'])

const dialogVisible = ref(props.visible)
const rechargeForm = ref({
  amount: 5
})
const loading = ref(false)
const rechargeFormRef = ref(null)
const errorMessage = ref('')
const presetAmounts = [
  { amount: 5, gift: 0 },
  { amount: 30, gift: 0 },
  { amount: 50, gift: 0 },
  { amount: 100, gift: 4 },
  { amount: 200, gift: 10 },
  { amount: 500, gift: 30 },
  { amount: 1000, gift: 80 },
  { amount: 2000, gift: 200 },
  { amount: 5000, gift: 600 },
  { amount: 10000, gift: 2000 },
  { amount: 30000, gift: 7500 },
  { amount: 100000, gift: 30000 }
]

const rules = {
  amount: [
    { required: true, message: '请输入充值金额', trigger: 'blur' },
    { type: 'number', min: 5, message: '充值金额不能小于5元', trigger: 'blur' }
  ]
}

const clearError = () => {
  errorMessage.value = ''
}

const handleAmountInput = () => {
  // 确保金额为整数
  if (rechargeForm.value.amount) {
    rechargeForm.value.amount = Math.floor(rechargeForm.value.amount)
  }
  clearError()
}

const selectPresetAmount = (amount) => {
  rechargeForm.value.amount = amount
  clearError()
  // 清除表单验证状态
  if (rechargeFormRef.value) {
    rechargeFormRef.value.clearValidate(['amount'])
  }
}

// 计算赠送金额（使用computed）
const giftAmount = computed(() => {
  const amount = rechargeForm.value.amount
  if (!amount) return 0
  
  for (let i = presetAmounts.length - 1; i >= 0; i--) {
    const preset = presetAmounts[i]
    if (amount >= preset.amount && preset.gift > 0) {
      // 计算赠送金额：(充值金额 * 该档位赠送金额) / 该档位金额，取整数部分
      return Math.floor((amount * preset.gift) / preset.amount)
    }
  }
  return 0
})

const checkPaymentStatus = async(order_no, accessToken) => {
  let count = 0
  while(count < 100 && dialogVisible.value){
    count++
    await new Promise(resolve => setTimeout(resolve, 3000)) // 每3秒检测一次
    try {
      const res = await axios.get('https://www.dajiala.com/fbmain/account/v1/api_check_order_status', {
        headers: {
          accesstoken: accessToken,
        },
        params: {
          order_no: order_no
        }
      })
      if (res.data && res.data.error_code === 0 && res.data.data.status === 1){
        return true
      }
    } catch (error) {
      console.error('支付检测失败:', error)
    }
  }
  if(dialogVisible.value){
    ElMessage.error('已超时')
  }
  return false
}

const handleRecharge = async () => {
  if (!rechargeFormRef.value) return
  
  clearError()
  
  await rechargeFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        // 显示确认对话框
        await ElMessageBox.confirm(
          `确认充值 ${rechargeForm.value.amount} 元吗？`,
          '充值确认',
          {
            confirmButtonText: '确认',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        
        loading.value = true
        const accessToken = sessionStorage.getItem('user_access_token');
        if (accessToken) {
          const formData = new FormData();
          formData.append('money', rechargeForm.value.amount);
          const res = await axios.post('https://www.dajiala.com/fbmain/account/v1/api_create_order', formData, {
            headers: {
              'Content-Type': 'multipart/form-data',
              accesstoken: accessToken,
            }
          })
          if (res.data && res.data.error_code === 0){
            const order_no = res.data.data.order_no
            const res_info = await axios.get('https://www.dajiala.com/fbmain/account/v1/api_pay_info', {
              headers: {
                accesstoken: accessToken,
              },
              params: {
                order_no: order_no
              }
            })
            if (res_info.data && res_info.data.error_code === 0){
              const pay_url = res_info.data.data.pay_url
              window.open(pay_url, '_blank')
              const isPaid = await checkPaymentStatus(order_no, accessToken)
              if(isPaid){
                emit('recharge', { amount: rechargeForm.value.amount, gift: giftAmount.value })
                dialogVisible.value = false
              }
            }else{
              errorMessage.value = res_info.data.msg
            }
          }else{
            errorMessage.value = res.data.msg
          }
        } else {
          errorMessage.value = '请先登录'
        }
      } catch (error) {
        // 如果是用户取消确认，不显示错误信息
        if (error !== 'cancel') {
          console.error('充值失败:', error)
          errorMessage.value = '充值失败，请稍后重试'
        }
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
  if (!newVal && rechargeFormRef.value) {
    rechargeFormRef.value.resetFields()
    errorMessage.value = ''
  }
})

// 当对话框关闭时通知父组件
watch(dialogVisible, (newVal) => {
  emit('update:visible', newVal)
  // 当对话框关闭时重置表单
  if (!newVal && rechargeFormRef.value) {
    rechargeFormRef.value.resetFields()
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

.preset-amounts {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding-left: 0;
  margin: 0;
  list-style: none;
}

.preset-amounts .el-button {
  flex: 1;
  min-width: 80px;
  padding: 30px 8px;
  text-align: center;
  display: flex;
  justify-content: center;
  align-items: center;
  border-radius: 6px;
}

.button-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 8px 0;
}

.amount {
  font-size: 16px;
  font-weight: bold;
}

.desc {
  font-size: 12px;
  color: #666;
}

.gift-info {
  margin-top: 8px;
  font-size: 14px;
  color: #f56c6c;
  font-weight: 500;
}

/* 为所有按钮添加左侧内边距，确保排列整齐 */
.preset-amounts .el-button {
  margin-left: 0;
}
</style>
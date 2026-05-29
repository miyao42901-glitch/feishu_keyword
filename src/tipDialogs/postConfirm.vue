<template>
  <el-dialog
    v-model="dialogVisible"
    width="90%"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
  >
  <div class="dialog-title">
    <el-icon v-if="props.resultType === 'success'" style="color: green;">
      <SuccessFilled />
    </el-icon>
    <el-icon v-else-if="props.resultType === 'warning'" style="color: orange;">
      <WarningFilled />
    </el-icon>
    <el-icon v-else-if="props.resultType === 'error'" style="color: red;">
      <CircleCheckFilled />
    </el-icon>
    <el-icon v-else style="color: gray;">
      <InfoFilled />
    </el-icon>
    <div>{{ props.title }}</div>
  </div>
  <div class="dialog-content">
    {{ props.displayInfo }}  
  </div>
  <template #footer>
    <span class="dialog-footer">
      <el-button @click="dialogVisible = false">{{ '关闭' }}</el-button>
      <el-button @click="handleJump" class="jump-btn" v-if="props.resultTableId">{{ '查看结果' }}</el-button>
    </span>
  </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { bitable } from '@lark-base-open/js-sdk'
import { SuccessFilled, WarningFilled, CircleCheckFilled, InfoFilled } from '@element-plus/icons-vue'
const emit = defineEmits(['update:visible'])
const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  resultTableId: {
    type: String,
    default: ''
  },
  displayInfo: {
    type: String,
    default: ''
  },
  title: {
    type: String,
    default: '提示'
  },
  resultType: {
    type: String,
    default: 'success'
  }
})
const dialogVisible = ref(props.visible)

const handleJump = async () => {
  if (props.resultTableId) {
    await bitable.ui.switchToTable(props.resultTableId);
    dialogVisible.value = false
  }
}

watch(() => props.visible, (newVal) => {
  dialogVisible.value = newVal
})

// 当对话框关闭时通知父组件
watch(dialogVisible, (newVal) => {
  emit('update:visible', newVal)
})
</script>

<style scoped>
.dialog-footer {
  display: flex;
  justify-content: flex-end;
}
.dialog-title {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 30px;
  display: flex;
  flex-direction: row;
  gap: 4px;
  color: #1890ff;
}
.dialog-content {
  font-size: 14px;
  margin-bottom: 30px;
  /* background-color: #eeeeee;
  padding: 12px; */
}
.jump-btn {
  background-color: #0e1e3d !important;
  color: #ffffff !important;
}
.jump-btn:hover {
  background-color: #1a2f58 !important;
}
.jump-btn:active {
  transform: scale(0.97);
}
</style>
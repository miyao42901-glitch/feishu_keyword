<template>
  <el-dialog
    v-model="dialogVisible"
    width="90%"
  >
  <div class="dialog-title">
    如何获取抖音"采集账号"
  </div>
  <div class="dialog-content">
    方式一、在浏览器打开抖音博主主页，复制链接。
  </div>
  <div class="dialog-content">
    方式二、下拉选择带有"抖音账号ID"字段的表格，一次性选择多个账号。
  </div>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
const emit = defineEmits(['update:visible'])
const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  }
})
const dialogVisible = ref(props.visible)

watch(() => props.visible, (newVal) => {
  dialogVisible.value = newVal
})

// 当对话框关闭时通知父组件
watch(dialogVisible, (newVal) => {
  emit('update:visible', newVal)
})
</script>

<style scoped>
.dialog-title {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 30px;
}
.dialog-content {
  font-size: 14px;
  margin-bottom: 30px;
}
</style>
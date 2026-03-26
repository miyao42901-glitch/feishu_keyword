<template>
  <div class="sensitive-text">
    <el-text>{{ displayText }}</el-text>
    <el-button
      :icon="visible ? View : Hide"
      link
      @click="toggleVisibility"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { View, Hide } from '@element-plus/icons-vue'

const props = defineProps({
  value: {
    type: String,
    required: true
  },
  // 掩码字符，默认为
  maskChar: {
    type: String,
    default: '..'
  }
})

const visible = ref(false)

const displayText = computed(() => {
  if (visible.value) return props.value
  // 掩码：替换为相同长度的掩码字符
  return props.value.replace(/./g, props.maskChar)
})

const toggleVisibility = () => {
  visible.value = !visible.value
}
</script>

<style scoped>
.sensitive-text {
  display: inline-flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  gap: 8px;
  padding: 4px 0;
  font-size: 14px;
  line-height: 1.5;
  background: transparent;
  border: none;
}

</style>
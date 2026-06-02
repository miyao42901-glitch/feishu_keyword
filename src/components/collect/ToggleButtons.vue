<template>
  <div class="toggle-wrapper">
    <el-button
      v-for="option in options"
      :key="option.value"
      type="info"
      class="toggle-btn"
      :class="{ active: modelValue === option.value }"
      @click="handleClick(option.value)"
    >
      {{ option.label }}
    </el-button>
  </div>
</template>

<script setup>
import { ElButton } from 'element-plus'

const props = defineProps({
  modelValue: {
    type: [String, Number],
    required: true
  },
  options: {
    type: Array,
    required: true,
    validator: (value) => {
      return value.every(item => item.value !== undefined && item.label !== undefined)
    }
  }
})

const emit = defineEmits(['update:modelValue'])

const handleClick = (value) => {
  emit('update:modelValue', value)
}
</script>

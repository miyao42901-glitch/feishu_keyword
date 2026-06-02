<template>
  <div class="collect-btn-item">
    <el-button
      :class="buttonClass"
      :disabled="disabled"
      :loading="loading"
      @click="handleClick"
    >
      <slot>{{ text }}</slot>
    </el-button>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { ElButton } from 'element-plus'

const props = defineProps({
  type: {
    type: String,
    default: 'primary',
    validator: (value) => ['primary', 'secondary'].includes(value)
  },
  disabled: {
    type: Boolean,
    default: false
  },
  loading: {
    type: Boolean,
    default: false
  },
  text: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['click'])

const buttonClass = computed(() => {
  return props.type === 'primary' ? 'collect-btn' : 'update-btn'
})

const handleClick = () => {
  if (!props.disabled && !props.loading) {
    emit('click')
  }
}
</script>

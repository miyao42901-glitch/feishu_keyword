<template>
  <div class="section-title">
    {{ title }}
    <el-icon v-if="showHelp" class="icon-hint" @click="handleHelpClick">
      <QuestionFilled />
    </el-icon>
  </div>
</template>

<script setup>
import { ElIcon } from 'element-plus'
import { QuestionFilled } from '@element-plus/icons-vue'

defineProps({
  title: {
    type: String,
    required: true
  },
  showHelp: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['help-click'])

const handleHelpClick = () => {
  emit('help-click')
}
</script>

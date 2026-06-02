<template>
  <div class="collect-sub-panel">
    <div v-if="title" class="section-block">
      <div class="field-label">{{ title }}</div>
    </div>
    <slot></slot>
  </div>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    default: ''
  }
})
</script>

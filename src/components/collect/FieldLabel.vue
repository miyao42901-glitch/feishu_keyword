<template>
  <div class="field-label">{{ label }}</div>
</template>

<script setup>
defineProps({
  label: {
    type: String,
    required: true
  }
})
</script>

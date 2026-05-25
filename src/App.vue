<script setup>
import Form from './components/Form.vue'
import { useTheme } from './utils/theme'

// 使用主题钩子
useTheme()
</script>

<template>
  <main>
    <!-- <h4>编辑 <code>src/App.vue</code> 并保存以重新加载</h4> -->
    <Form />
  </main>
</template>

<style scoped>
  /* main {
    min-height: 100vh
  } */
</style>

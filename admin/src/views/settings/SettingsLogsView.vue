<template>
  <div class="page-empty">
    <el-card shadow="hover" class="page-empty__card">
      <h3 class="page-empty__title">{{ title }}</h3>
      <p class="page-empty__hint">该页面正在建设中。</p>
    </el-card>
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ title?: string }>(), { title: '操作日志' })
</script>

<style scoped>
.page-empty {
  max-width: 1200px;
  margin: 0 auto;
}
.page-empty__card {
  min-height: 200px;
}
.page-empty__title {
  margin: 0 0 8px;
  font-size: 18px;
  color: var(--el-text-color-primary);
}
.page-empty__hint {
  margin: 0;
  color: var(--el-text-color-secondary);
}
</style>

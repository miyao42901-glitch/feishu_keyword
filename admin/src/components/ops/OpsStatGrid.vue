<template>
  <el-row :gutter="16" class="ops-stat-row">
    <el-col v-for="item in stats" :key="item.label" :xs="24" :sm="colSm">
      <el-card shadow="hover" class="ops-stat-card">
        <div class="ops-stat-label">{{ item.label }}</div>
        <div class="ops-stat-value">{{ item.value }}</div>
        <div class="ops-stat-sub" :class="item.tone">{{ item.sub }}</div>
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    stats: Array<{ label: string; value: string | number; sub: string; tone?: 'up' | 'down' | 'muted' | 'neutral' }>
    colSm?: number
  }>(),
  { colSm: 8 },
)
</script>

<template>
  <el-card shadow="never" class="ops-chart-card">
    <template #header>
      <div class="ops-chart-header">
        <span class="ops-chart-title">{{ title }}</span>
        <slot name="actions" />
      </div>
    </template>
    <VChart class="ops-chart" :option="option" autoresize />
  </el-card>
</template>

<script setup lang="ts">
import type { OpsChartOption } from '@/types/opsCharts'
import VChart from 'vue-echarts'
import { useOpsEcharts } from '@/composables/useOpsEcharts'

useOpsEcharts()

defineProps<{
  title: string
  option: OpsChartOption
}>()
</script>

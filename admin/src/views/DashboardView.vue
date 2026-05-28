<template>
  <div class="dashboard" :class="{ 'dashboard--mobile': isMobile }">
    <div class="dashboard-top">
      <div class="toolbar">
        <span class="toolbar-label">概览</span>
        <span class="toolbar-hint">以下为占位数据，接入接口后可替换</span>
      </div>
    </div>

    <el-row :gutter="16" class="kpi-row">
      <el-col :xs="24" :sm="8">
        <el-card shadow="hover" class="kpi-card">
          <div class="kpi-label">关键词总数</div>
          <div class="kpi-num">{{ kpi.keywords }}</div>
          <div class="kpi-sub">占位</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card shadow="hover" class="kpi-card">
          <div class="kpi-label">今日命中</div>
          <div class="kpi-num">{{ kpi.hitsToday }}</div>
          <div class="kpi-sub">占位</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card shadow="hover" class="kpi-card">
          <div class="kpi-label">启用规则</div>
          <div class="kpi-num">{{ kpi.rulesActive }}</div>
          <div class="kpi-sub">占位</div>
        </el-card>
      </el-col>
    </el-row>

    <div class="dashboard-charts">
      <el-card shadow="never" class="chart-card">
        <template #header>
          <span class="chart-title">近 7 日趋势（占位）</span>
        </template>
        <VChart class="chart" :option="chartOption" autoresize />
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import type { ComposeOption } from 'echarts/core'
import type { LineSeriesOption } from 'echarts/charts'
import type { GridComponentOption, TooltipComponentOption } from 'echarts/components'
import VChart from 'vue-echarts'
import { useAdminMobileLayout } from '@/composables/useAdminMobileLayout'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent])

type LineOpt = ComposeOption<LineSeriesOption | GridComponentOption | TooltipComponentOption>

const { isMobile } = useAdminMobileLayout()

const kpi = ref({ keywords: 0, hitsToday: 0, rulesActive: 0 })

const stubLabels = ['D-6', 'D-5', 'D-4', 'D-3', 'D-2', 'D-1', '今天']
const stubSeries = [0, 0, 0, 0, 0, 0, 0]

const chartOption = computed(
  (): LineOpt => ({
    tooltip: { trigger: 'axis' },
    grid: { left: 48, right: 24, top: 32, bottom: 40 },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: stubLabels,
    },
    yAxis: {
      type: 'value',
      name: '次',
      minInterval: 1,
    },
    series: [
      {
        name: '命中次数',
        type: 'line',
        smooth: true,
        showSymbol: true,
        symbolSize: 6,
        lineStyle: { width: 2, color: '#4073fa' },
        itemStyle: { color: '#4073fa' },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: '#4073fa40' },
              { offset: 1, color: '#4073fa08' },
            ],
          },
        },
        data: stubSeries,
      },
    ],
  }),
)
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
  margin: 0 auto;
}
.dashboard-top {
  margin-bottom: 16px;
}
.toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}
.toolbar-label {
  font-size: 14px;
  color: var(--el-text-color-secondary);
}
.toolbar-hint {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}
.kpi-row {
  margin-bottom: 16px;
}
.kpi-card {
  min-height: 120px;
}
.kpi-label {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  margin-bottom: 8px;
}
.kpi-num {
  font-size: 28px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  line-height: 1.2;
}
.kpi-sub {
  margin-top: 8px;
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}
.dashboard-charts {
  margin-top: 8px;
}
.chart-card {
  width: 100%;
}
.chart-title {
  font-weight: 600;
}
.chart {
  height: 280px;
  width: 100%;
}

@media (max-width: 899px) {
  .toolbar {
    align-items: flex-start;
  }

  .kpi-row {
    margin-bottom: 20px;
  }

  .kpi-row :deep(.el-col) {
    margin-bottom: 12px;
  }

  .kpi-row :deep(.el-col:last-child) {
    margin-bottom: 0;
  }

  .chart {
    height: 220px;
  }
}
</style>

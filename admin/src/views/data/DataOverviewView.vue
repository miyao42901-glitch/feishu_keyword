<template>
  <div class="ops-page">
    <div class="ops-section-head">
      <span class="ops-section-title">核心指标</span>
      <el-radio-group v-model="kpiRange" size="small">
        <el-radio-button value="day">今日</el-radio-button>
        <el-radio-button value="week">本周</el-radio-button>
        <el-radio-button value="month">本月</el-radio-button>
      </el-radio-group>
    </div>

    <el-row :gutter="16" class="ops-kpi-row">
      <el-col v-for="card in kpiCards" :key="card.key" :xs="24" :sm="12" :lg="6">
        <el-card
          shadow="hover"
          class="ops-kpi-card"
          :class="`ops-kpi-card--${card.tone}`"
          @click="drillKpi(card.drill)"
        >
          <span class="ops-kpi-drill">查看详情 →</span>
          <div class="ops-kpi-label">{{ card.label }}</div>
          <div class="ops-kpi-value">{{ card.value }}</div>
          <div class="ops-kpi-sub"><span class="up">↑</span>{{ card.compareHint }}</div>
          <div class="ops-kpi-target">{{ card.target }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="ops-chart-row">
      <el-col :xs="24" :lg="12">
        <OpsChartCard title="用户与业务趋势（近30天）" :option="trendOption" />
      </el-col>
      <el-col :xs="24" :lg="12">
        <OpsChartCard title="本月新增任务的状态分布" :option="statusOption" />
      </el-col>
    </el-row>

    <el-row :gutter="16" class="ops-chart-row">
      <el-col :xs="24" :lg="12">
        <OpsChartCard title="平台 API 调用分布（近30天）" :option="platformOption" />
      </el-col>
      <el-col :xs="24" :lg="12">
        <OpsChartCard title="点数消耗 Top 用户（本月）" :option="topUserOption" />
      </el-col>
    </el-row>

    <el-card shadow="never" class="ops-funnel-card">
      <template #header>
        <span class="ops-section-title">页面触达流程 · 未登录用户转化漏斗</span>
      </template>
      <div class="ops-funnel-layout">
        <div class="ops-funnel-main">
          <template v-for="(step, index) in funnelSteps" :key="step.label">
            <div class="ops-funnel-step">
              <div class="ops-funnel-step__head" :style="{ background: funnelColors[index] || '#4073fa' }">
                <div style="font-size: 12px; opacity: 0.85; margin-bottom: 4px">{{ step.label }}</div>
                <div class="ops-funnel-step__value">{{ Number(step.value).toLocaleString() }}</div>
              </div>
              <div class="ops-funnel-step__foot">
                <div>{{ step.note }}</div>
                <div v-if="step.loss" style="color: #f53f3f">{{ step.loss }}</div>
              </div>
            </div>
            <div v-if="index < funnelSteps.length - 1 && funnelRates[index]" class="ops-funnel-arrow">
              <span>{{ funnelRates[index] }}</span>
            </div>
          </template>
        </div>
        <div class="ops-funnel-side">
          <div class="ops-section-title" style="margin-bottom: 12px">流失分析</div>
          <div v-if="funnelLosses.length === 0" style="font-size: 12px; color: var(--el-text-color-secondary)">
            暂无足够埋点数据
          </div>
          <div v-for="item in funnelLosses" :key="item.title" class="ops-funnel-loss">
            <div style="display: flex; justify-content: space-between; margin-bottom: 6px">
              <span style="font-size: 12px">{{ item.title }}</span>
              <span style="font-size: 12px; font-weight: 600; color: #f53f3f">{{ item.count }}</span>
            </div>
            <div style="font-size: 11px; color: var(--el-text-color-secondary)">{{ item.desc }}</div>
          </div>
          <div class="ops-funnel-summary">
            <div style="font-size: 11px; color: var(--el-color-primary); margin-bottom: 4px">全链路转化率</div>
            <div style="font-size: 32px; font-weight: 700; color: var(--el-color-primary)">{{ funnelConversion }}</div>
            <div style="font-size: 11px; color: var(--el-text-color-secondary); margin-top: 4px">{{ funnelRangeLabel }}</div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import type { OpsChartOption } from '@/types/opsCharts'
import OpsChartCard from '@/components/ops/OpsChartCard.vue'
import { useOpsEcharts } from '@/composables/useOpsEcharts'
import { fetchAnalyticsOverview, type AnalyticsOverviewData } from '@/api/analytics'
import { FUNNEL_LOSSES, FUNNEL_STEPS, KPI_DATA, type KpiRange } from '@/mock/opsMockData'

useOpsEcharts()

const router = useRouter()
const kpiRange = ref<KpiRange>('month')
const overview = ref<AnalyticsOverviewData | null>(null)
const useMockFallback = ref(false)

const funnelColors = ['#4073fa', '#ff7d00', '#00b42a', '#00b42a']

async function loadOverview() {
  try {
    overview.value = await fetchAnalyticsOverview(kpiRange.value)
    useMockFallback.value = Boolean(overview.value?.empty)
  } catch {
    overview.value = null
    useMockFallback.value = true
  }
}

watch(kpiRange, () => {
  void loadOverview()
}, { immediate: true })

const kpi = computed(() => {
  if (!useMockFallback.value && overview.value?.kpis) return overview.value.kpis
  return KPI_DATA[kpiRange.value]
})

const kpiCards = computed(() => {
  const d = kpi.value as Record<string, string | number>
  const compare = String(d.compare ?? KPI_DATA[kpiRange.value].compare)
  return [
    { key: 'tasks', label: '活跃任务数', value: d.activeTasks, compareHint: compare, target: '目标: ≥500', tone: 'blue', drill: '/business/tasks' },
    { key: 'exec', label: '任务执行成功率', value: d.execRate, compareHint: compare, target: '目标: ≥95%', tone: 'green', drill: '/business/exec-monitor' },
    { key: 'api', label: 'API 调用成功率', value: d.apiRate, compareHint: compare, target: '目标: ≥98%', tone: 'green', drill: '/business/api-monitor' },
    { key: 'points', label: '点数消耗量', value: d.points, compareHint: compare, target: '目标: ≥10,000', tone: 'orange', drill: '/operation/users' },
    { key: 'retention', label: '用户月留存率', value: d.retention, compareHint: compare, target: '目标: ≥60%', tone: 'blue', drill: '/operation/users' },
    { key: 'avg', label: '人均任务数', value: d.avgTasks, compareHint: compare, target: '目标: ≥3', tone: 'green', drill: '/business/tasks' },
    { key: 'push', label: '预警推送触达率', value: d.pushRate, compareHint: compare, target: '目标: ≥90%', tone: 'green', drill: '/business/push-monitor' },
    { key: 'users', label: '活跃用户数', value: d.activeUsers, compareHint: compare, target: String(d.newUsers ?? ''), tone: 'blue', drill: '/operation/users' },
  ]
})

function drillKpi(path: string) {
  router.push(path)
}

const funnelSteps = computed(() => {
  if (!useMockFallback.value && overview.value?.funnel?.steps?.length) {
    return overview.value.funnel.steps
  }
  return FUNNEL_STEPS.map((s) => ({ label: s.label, value: s.value, note: s.note, loss: s.loss }))
})

const funnelLosses = computed(() => {
  if (!useMockFallback.value && overview.value?.funnel?.losses?.length) {
    return overview.value.funnel.losses
  }
  return useMockFallback.value ? FUNNEL_LOSSES : []
})

const funnelConversion = computed(() => {
  if (!useMockFallback.value && overview.value?.funnel?.conversionRate) {
    return overview.value.funnel.conversionRate
  }
  return '15.0%'
})

const funnelRangeLabel = computed(() => {
  if (!useMockFallback.value && overview.value?.funnel?.rangeLabel) {
    return overview.value.funnel.rangeLabel
  }
  return '1,240 → 186'
})

const funnelRates = computed(() => {
  const steps = funnelSteps.value
  const rates: string[] = []
  for (let i = 0; i < steps.length - 1; i += 1) {
    const cur = Number(steps[i]?.value ?? 0)
    const next = Number(steps[i + 1]?.value ?? 0)
    rates.push(cur > 0 ? `${Math.round((next / cur) * 100)}%` : '-')
  }
  return rates
})

const trendOption = computed((): OpsChartOption => {
  const trend = overview.value?.charts?.trend
  const labels = trend?.labels?.length ? trend.labels : ['5/1', '5/5', '5/9', '5/13', '5/17', '5/21', '5/25', '5/28']
  const activeUsers = trend?.activeUsers?.length ? trend.activeUsers : [42, 58, 63, 71, 82, 95, 108, 126]
  const execCounts = trend?.execCounts?.length ? trend.execCounts : [420, 512, 548, 596, 635, 682, 725, 784]
  return {
    tooltip: { trigger: 'axis' },
    legend: { top: 0 },
    grid: { left: 48, right: 48, top: 40, bottom: 32 },
    xAxis: { type: 'category', data: labels },
    yAxis: [
      { type: 'value', name: '任务创建' },
      { type: 'value', name: '活跃用户', position: 'right', splitLine: { show: false } },
    ],
    series: [
      {
        name: '任务创建数',
        type: 'line',
        smooth: true,
        data: execCounts,
        itemStyle: { color: '#00b42a' },
        areaStyle: { color: 'rgba(0,180,42,0.08)' },
      },
      {
        name: '活跃用户数',
        type: 'line',
        smooth: true,
        yAxisIndex: 1,
        data: activeUsers,
        itemStyle: { color: '#4073fa' },
        areaStyle: { color: 'rgba(64,115,250,0.08)' },
      },
    ],
  }
})

const statusOption = computed((): OpsChartOption => {
  const rows = overview.value?.charts?.taskStatus
  const data = rows?.length
    ? rows
    : [
        { name: '运行中', value: 89 },
        { name: '已停止', value: 58 },
        { name: '已完成', value: 39 },
      ]
  return {
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [{ type: 'pie', radius: ['45%', '70%'], data, color: ['#00b42a', '#e8eaed', '#4073fa'] }],
  }
})

const platformOption = computed((): OpsChartOption => {
  const plat = overview.value?.charts?.platformApi
  const labels = plat?.labels?.length
    ? plat.labels
    : ['微博', '抖音', '百度', '知乎', '小红书', '微信公众号', '政府网']
  const values = plat?.values?.length ? plat.values : [3200, 2800, 2100, 1500, 1200, 980, 706]
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 48, right: 24, top: 24, bottom: 40 },
    xAxis: { type: 'category', data: labels },
    yAxis: { type: 'value' },
    series: [{ type: 'bar', data: values, itemStyle: { color: '#4073fa', borderRadius: [4, 4, 0, 0] }, barMaxWidth: 28 }],
  }
})

const topUserOption = computed((): OpsChartOption => {
  const top = overview.value?.charts?.topUsers
  const labels = top?.labels?.length ? top.labels : ['赵雪', '张明', '吴强', '李婷', '刘芳']
  const values = top?.values?.length ? top.values : [4100, 2340, 1980, 1820, 1560]
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 72, right: 24, top: 24, bottom: 32 },
    xAxis: { type: 'value' },
    yAxis: { type: 'category', data: labels },
    series: [{ type: 'bar', data: values, itemStyle: { color: '#4073fa', borderRadius: [0, 4, 4, 0] }, barMaxWidth: 20 }],
  }
})
</script>

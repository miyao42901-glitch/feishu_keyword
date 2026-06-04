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

    <el-empty v-if="!loading && !hasData" description="暂无数据" />

    <template v-else>
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
          <OpsChartCard v-if="trendOption" title="用户与业务趋势（近30天）" :option="trendOption" />
          <el-card v-else shadow="never">
            <template #header>用户与业务趋势（近30天）</template>
            <el-empty description="暂无数据" />
          </el-card>
        </el-col>
        <el-col :xs="24" :lg="12">
          <OpsChartCard v-if="statusOption" title="本月新增任务的状态分布" :option="statusOption" />
          <el-card v-else shadow="never">
            <template #header>本月新增任务的状态分布</template>
            <el-empty description="暂无数据" />
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="16" class="ops-chart-row">
        <el-col :xs="24" :lg="12">
          <OpsChartCard v-if="platformOption" title="平台 API 调用分布（近30天）" :option="platformOption" />
          <el-card v-else shadow="never">
            <template #header>平台 API 调用分布（近30天）</template>
            <el-empty description="暂无数据" />
          </el-card>
        </el-col>
        <el-col :xs="24" :lg="12">
          <OpsChartCard v-if="topUserOption" title="点数消耗 Top 用户（本月）" :option="topUserOption" />
          <el-card v-else shadow="never">
            <template #header>点数消耗 Top 用户（本月）</template>
            <el-empty description="暂无数据" />
          </el-card>
        </el-col>
      </el-row>

      <el-card shadow="never" class="ops-funnel-card">
        <template #header>
          <span class="ops-section-title">页面触达流程 · 未登录用户转化漏斗</span>
        </template>
        <el-empty v-if="funnelSteps.length === 0" description="暂无数据" />
        <div v-else class="ops-funnel-layout">
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
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import type { OpsChartOption } from '@/types/opsCharts'
import OpsChartCard from '@/components/ops/OpsChartCard.vue'
import { useOpsEcharts } from '@/composables/useOpsEcharts'
import { fetchAnalyticsOverview, type AnalyticsOverviewData, type AnalyticsRange } from '@/api/analytics'

useOpsEcharts()

const router = useRouter()
const kpiRange = ref<AnalyticsRange>('month')
const overview = ref<AnalyticsOverviewData | null>(null)
const loading = ref(false)
const hasData = computed(() => !overview.value?.empty && overview.value !== null)

const funnelColors = ['#4073fa', '#ff7d00', '#00b42a', '#00b42a']

async function loadOverview() {
  loading.value = true
  try {
    overview.value = await fetchAnalyticsOverview(kpiRange.value)
  } catch {
    overview.value = null
  } finally {
    loading.value = false
  }
}

watch(kpiRange, () => {
  void loadOverview()
}, { immediate: true })

const kpiCards = computed(() => {
  const d = overview.value?.kpis
  if (!hasData.value || !d) return []
  return [
    { key: 'tasks', label: '活跃任务数', value: d.activeTasks, compareHint: d.compare, target: '目标: ≥500', tone: 'blue', drill: '/business/tasks' },
    { key: 'exec', label: '任务执行成功率', value: d.execRate, compareHint: d.compare, target: '目标: ≥95%', tone: 'green', drill: '/business/exec-monitor' },
    { key: 'api', label: 'API 调用成功率', value: d.apiRate, compareHint: d.compare, target: '目标: ≥98%', tone: 'green', drill: '/business/api-monitor' },
    { key: 'points', label: '点数消耗量', value: d.points, compareHint: d.compare, target: '目标: ≥10,000', tone: 'orange', drill: '/operation/users' },
    { key: 'retention', label: '用户月留存率', value: d.retention, compareHint: d.compare, target: '目标: ≥60%', tone: 'blue', drill: '/operation/users' },
    { key: 'avg', label: '人均任务数', value: d.avgTasks, compareHint: d.compare, target: '目标: ≥3', tone: 'green', drill: '/business/tasks' },
    { key: 'push', label: '预警推送触达率', value: d.pushRate, compareHint: d.compare, target: '目标: ≥90%', tone: 'green', drill: '/business/push-monitor' },
    { key: 'users', label: '活跃用户数', value: d.activeUsers, compareHint: d.compare, target: String(d.newUsers ?? ''), tone: 'blue', drill: '/operation/users' },
  ]
})

function drillKpi(path: string) {
  router.push(path)
}

const funnelSteps = computed(() => {
  if (!hasData.value) return []
  return overview.value?.funnel?.steps ?? []
})

const funnelLosses = computed(() => {
  if (!hasData.value) return []
  return overview.value?.funnel?.losses ?? []
})

const funnelConversion = computed(() => {
  if (!hasData.value) return '-'
  return overview.value?.funnel?.conversionRate ?? '-'
})

const funnelRangeLabel = computed(() => {
  if (!hasData.value) return ''
  return overview.value?.funnel?.rangeLabel ?? ''
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

const trendOption = computed((): OpsChartOption | null => {
  const trend = overview.value?.charts?.trend
  if (!hasData.value || !trend?.labels?.length) return null
  return {
    tooltip: { trigger: 'axis' },
    legend: { top: 0 },
    grid: { left: 48, right: 48, top: 40, bottom: 32 },
    xAxis: { type: 'category', data: trend.labels },
    yAxis: [
      { type: 'value', name: '任务创建' },
      { type: 'value', name: '活跃用户', position: 'right', splitLine: { show: false } },
    ],
    series: [
      {
        name: '任务创建数',
        type: 'line',
        smooth: true,
        data: trend.execCounts,
        itemStyle: { color: '#00b42a' },
        areaStyle: { color: 'rgba(0,180,42,0.08)' },
      },
      {
        name: '活跃用户数',
        type: 'line',
        smooth: true,
        yAxisIndex: 1,
        data: trend.activeUsers,
        itemStyle: { color: '#4073fa' },
        areaStyle: { color: 'rgba(64,115,250,0.08)' },
      },
    ],
  }
})

const statusOption = computed((): OpsChartOption | null => {
  const rows = overview.value?.charts?.taskStatus
  if (!hasData.value || !rows?.length) return null
  return {
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [{ type: 'pie', radius: ['45%', '70%'], data: rows, color: ['#00b42a', '#e8eaed', '#4073fa'] }],
  }
})

const platformOption = computed((): OpsChartOption | null => {
  const plat = overview.value?.charts?.platformApi
  if (!hasData.value || !plat?.labels?.length) return null
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 48, right: 24, top: 24, bottom: 40 },
    xAxis: { type: 'category', data: plat.labels },
    yAxis: { type: 'value' },
    series: [{ type: 'bar', data: plat.values, itemStyle: { color: '#4073fa', borderRadius: [4, 4, 0, 0] }, barMaxWidth: 28 }],
  }
})

const topUserOption = computed((): OpsChartOption | null => {
  const top = overview.value?.charts?.topUsers
  if (!hasData.value || !top?.labels?.length) return null
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 130, right: 24, top: 24, bottom: 32 },
    xAxis: { type: 'value' },
    yAxis: { type: 'category', data: top.labels },
    series: [{ type: 'bar', data: top.values, itemStyle: { color: '#4073fa', borderRadius: [0, 4, 4, 0] }, barMaxWidth: 20 }],
  }
})
</script>

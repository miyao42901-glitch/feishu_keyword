<template>
  <div class="overview-page">
    <div class="overview-header">
      <el-button-group>
        <el-button :type="timeRange === 'day' ? 'primary' : ''" @click="timeRange = 'day'">今日</el-button>
        <el-button :type="timeRange === 'week' ? 'primary' : ''" @click="timeRange = 'week'">本周</el-button>
        <el-button :type="timeRange === 'month' ? 'primary' : ''" @click="timeRange = 'month'">本月</el-button>
      </el-button-group>
    </div>

    <div v-loading="loading">
      <!-- KPI Cards -->
      <div class="kpi-grid">
        <div v-for="kpi in kpiCards" :key="kpi.key" class="kpi-card">
          <div class="kpi-label">{{ kpi.label }}</div>
          <div class="kpi-value">{{ kpi.value }}</div>
          <div class="kpi-change" :class="kpi.changeType">{{ kpi.change }}</div>
        </div>
      </div>

      <!-- Platform + Failure Row -->
      <div class="charts-row">
        <el-card shadow="never" class="chart-card">
          <template #header><span class="chart-title">各平台数据采集分布</span></template>
          <div ref="platformEl" class="chart-body" />
        </el-card>
        <el-card shadow="never" class="chart-card">
          <template #header><span class="chart-title">采集失败原因分布</span></template>
          <div ref="failureEl" class="chart-body" />
        </el-card>
      </div>

      <!-- Funnel Row -->
      <el-card shadow="never" class="funnel-card">
        <template #header>
          <div class="funnel-card-header">
            <span class="chart-title">任务漏斗-从打开插件到采集成功</span>
            <el-link type="primary" style="font-size: 13px">查看详细漏斗 &gt;</el-link>
          </div>
        </template>
        <div class="funnel-body">
          <!-- Custom horizontal funnel matching the screenshot -->
          <div class="funnel-steps">
            <template v-for="(step, idx) in funnelSteps" :key="step.label">
              <div class="funnel-step">
                <div class="funnel-step-label">{{ step.label }}</div>
                <div class="funnel-bar-row">
                  <div
                    class="funnel-bar"
                    :style="{
                      width: funnelBarWidth(step.value) + '%',
                      background: funnelBarColors[idx],
                    }"
                  />
                  <span class="funnel-bar-value">{{ Number(step.value).toLocaleString() }}</span>
                  <span class="funnel-bar-pct">{{ funnelPct(step.value) }}</span>
                </div>
              </div>
              <div v-if="idx < funnelSteps.length - 1" class="funnel-drop">
                <span class="funnel-drop-text">
                  {{ funnelDropLabels[idx] }}
                  <span class="funnel-drop-pct">{{ funnelDropPcts[idx] }}</span>
                </span>
              </div>
            </template>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { fetchAnalyticsOverview } from '@/api/analytics'

const timeRange = ref('month')
const loading = ref(false)
const overview = ref(null)

const platformEl = ref(null)
const failureEl = ref(null)

let platformChart = null
let failureChart = null

const funnelBarColors = ['#4e7bef', '#4e7bef', '#4e7bef', '#34c759']

async function loadData() {
  loading.value = true
  try {
    overview.value = await fetchAnalyticsOverview(timeRange.value)
    await nextTick()
    renderCharts()
  } finally {
    loading.value = false
  }
}

// ── KPI cards (range-aware) ──────────────────────────────────────────────────
const KPI_BY_RANGE = {
  day: [
    { key: 'users',  label: '有效用户',       value: '312',    change: '+8 较昨日',     changeType: 'up' },
    { key: 'calls',  label: '调用次数',       value: '428',    change: '+32 较昨日',    changeType: 'up' },
    { key: 'points', label: '消耗金额',       value: '1,204',  change: '+98 较昨日',    changeType: 'up' },
    { key: 'rate',   label: '采集任务成功率', value: '91.2%',  change: '+0.8% 较昨日',  changeType: 'up' },
    { key: 'time',   label: '平均全流程时长', value: '3m 58s', change: '-5% 较昨日',    changeType: 'up' },
  ],
  week: [
    { key: 'users',  label: '有效用户',       value: '876',    change: '+42 较上周',    changeType: 'up' },
    { key: 'calls',  label: '调用次数',       value: '3,024',  change: '+215 较上周',   changeType: 'up' },
    { key: 'points', label: '消耗金额',       value: '8,340',  change: '+620 较上周',   changeType: 'up' },
    { key: 'rate',   label: '采集任务成功率', value: '89.5%',  change: '+0.5% 较上周',  changeType: 'up' },
    { key: 'time',   label: '平均全流程时长', value: '4m 05s', change: '-2% 较上周',    changeType: 'up' },
  ],
  month: [
    { key: 'users',  label: '有效用户',       value: '1,231',  change: '+113 较上月',   changeType: 'up' },
    { key: 'calls',  label: '调用次数',       value: '14,528', change: '+1,123 较上月', changeType: 'up' },
    { key: 'points', label: '消耗金额',       value: '14,528', change: '+1,123 较上月', changeType: 'up' },
    { key: 'rate',   label: '采集任务成功率', value: '88.8%',  change: '+1.2% 较上月',  changeType: 'up' },
    { key: 'time',   label: '平均全流程时长', value: '4m 23s', change: '-2% 较上月',    changeType: 'up' },
  ],
}

const kpiCards = computed(() => KPI_BY_RANGE[timeRange.value] ?? KPI_BY_RANGE.month)

// ── Funnel helpers ────────────────────────────────────────────────────────────
const FUNNEL_BY_RANGE = {
  day: [
    { label: '打开插件', value: 1840, dropLabel: '▼ 未登录流失', dropPct: '8%' },
    { label: '完成登录', value: 1693, dropLabel: '▼ 配置时放弃', dropPct: '45%' },
    { label: '采集执行', value: 931,  dropLabel: '▼ 执行失败',   dropPct: '25%' },
    { label: '采集成功', value: 698,  dropLabel: null,            dropPct: null  },
  ],
  week: [
    { label: '打开插件', value: 9240, dropLabel: '▼ 未登录流失', dropPct: '9%' },
    { label: '完成登录', value: 8408, dropLabel: '▼ 配置时放弃', dropPct: '42%' },
    { label: '采集执行', value: 4877, dropLabel: '▼ 执行失败',   dropPct: '26%' },
    { label: '采集成功', value: 3609, dropLabel: null,            dropPct: null  },
  ],
  month: [
    { label: '打开插件', value: 12840, dropLabel: '▼ 未登录流失', dropPct: '8%' },
    { label: '完成登录', value: 11813, dropLabel: '▼ 配置时放弃', dropPct: '45%' },
    { label: '采集执行', value: 6497,  dropLabel: '▼ 执行失败',   dropPct: '25%' },
    { label: '采集成功', value: 4873,  dropLabel: null,            dropPct: null  },
  ],
}

const funnelSteps = computed(() => FUNNEL_BY_RANGE[timeRange.value] ?? FUNNEL_BY_RANGE.month)

const funnelDropLabels = computed(() =>
  funnelSteps.value.slice(0, -1).map((s) => s.dropLabel ?? ''),
)
const funnelDropPcts = computed(() =>
  funnelSteps.value.slice(0, -1).map((s) => s.dropPct ?? ''),
)

function funnelBarWidth(value) {
  const max = funnelSteps.value[0]?.value ?? 1
  return Math.round((value / max) * 100)
}

function funnelPct(value) {
  const max = funnelSteps.value[0]?.value ?? 1
  return Math.round((value / max) * 100) + '%'
}

// ── Chart renderers ───────────────────────────────────────────────────────────
const PLATFORM_BY_RANGE = {
  day:   [52, 23, 13, 8, 4],
  week:  [49, 25, 14, 7, 5],
  month: [52, 23, 13, 8, 4],
}

const FAILURE_BY_RANGE = {
  day:   [85, 18, 12, 8],
  week:  [86, 16, 13, 7],
  month: [88, 15, 11, 6],
}

const PLATFORM_COLORS = ['#a78bfa', '#fb7185', '#4ade80', '#38bdf8', '#fb923c']
const FAILURE_COLORS  = ['#ef4444', '#fb923c', '#fbbf24', '#a3b899']

function buildHBarOption(labels, values, colors) {
  const maxVal = Math.max(...values)
  return {
    grid: { left: 110, right: 80, top: 10, bottom: 10, containLabel: false },
    xAxis: { type: 'value', show: false, max: maxVal * 1.3 },
    yAxis: {
      type: 'category',
      data: labels,
      inverse: true,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { fontSize: 13, color: '#374151' },
    },
    series: [
      {
        type: 'bar',
        data: values.map((v, i) => ({
          value: v,
          itemStyle: { color: colors[i], borderRadius: [0, 4, 4, 0] },
        })),
        barWidth: 20,
        label: {
          show: true,
          position: 'right',
          formatter: (p) => `${p.value}%`,
          fontSize: 12,
          color: '#6b7280',
          distance: 8,
        },
        showBackground: true,
        backgroundStyle: { color: '#f3f4f6', borderRadius: [0, 4, 4, 0] },
      },
    ],
  }
}

function renderCharts() {
  if (!window.echarts) return

  const platformVals = PLATFORM_BY_RANGE[timeRange.value] ?? PLATFORM_BY_RANGE.month
  const failureVals  = FAILURE_BY_RANGE[timeRange.value]  ?? FAILURE_BY_RANGE.month

  if (platformEl.value) {
    if (!platformChart) platformChart = window.echarts.init(platformEl.value)
    platformChart.setOption(buildHBarOption(
      ['抖音', '小红书', '公众号', '视频号', '快手'],
      platformVals,
      PLATFORM_COLORS,
    ))
  }

  if (failureEl.value) {
    if (!failureChart) failureChart = window.echarts.init(failureEl.value)
    failureChart.setOption(buildHBarOption(
      ['账号ID错误', '余额不足', '网络超时', '其他原因'],
      failureVals,
      FAILURE_COLORS,
    ))
  }
}

watch(timeRange, async () => {
  await loadData()
})

onMounted(() => {
  loadData()
})

onBeforeUnmount(() => {
  platformChart?.dispose()
  failureChart?.dispose()
})
</script>

<style scoped>
.overview-page {
  padding: 0;
}

/* ── Header ── */
.overview-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 20px;
}

/* ── KPI Grid ── */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 14px;
  margin-bottom: 20px;
}

@media (max-width: 1300px) {
  .kpi-grid { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 768px) {
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
}

.kpi-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 20px 18px 16px;
}

.kpi-label {
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 8px;
}

.kpi-value {
  font-size: 30px;
  font-weight: 700;
  color: #111827;
  line-height: 1.15;
  margin-bottom: 6px;
  letter-spacing: -0.5px;
}

.kpi-change {
  font-size: 12px;
}

.kpi-change.up   { color: #10b981; }
.kpi-change.down { color: #ef4444; }

/* ── Charts Row ── */
.charts-row {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.chart-card {
  flex: 1;
  min-width: 0;
}

.chart-title {
  font-size: 14px;
  font-weight: 600;
  color: #111827;
}

.chart-body {
  height: 230px;
}

/* ── Funnel Card ── */
.funnel-card {
  margin-bottom: 20px;
}

.funnel-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.funnel-body {
  padding: 8px 0;
}

.funnel-steps {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.funnel-step {
  padding: 10px 0;
}

.funnel-step-label {
  font-size: 13px;
  color: #374151;
  margin-bottom: 8px;
  font-weight: 500;
}

.funnel-bar-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.funnel-bar {
  height: 32px;
  border-radius: 0 4px 4px 0;
  transition: width 0.5s ease;
  min-width: 4px;
}

.funnel-bar-value {
  font-size: 14px;
  font-weight: 600;
  color: #111827;
  min-width: 54px;
}

.funnel-bar-pct {
  font-size: 13px;
  color: #6b7280;
}

.funnel-drop {
  padding: 6px 0 6px 16px;
  font-size: 12px;
  color: #6b7280;
}

.funnel-drop-pct {
  color: #f59e0b;
  font-weight: 600;
  margin-left: 4px;
}
</style>

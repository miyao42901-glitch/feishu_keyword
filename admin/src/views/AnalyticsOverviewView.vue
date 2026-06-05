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
      <div class="kpi-grid">
        <div v-for="kpi in kpiCards" :key="kpi.key" class="kpi-card">
          <div class="kpi-label">{{ kpi.label }}</div>
          <div class="kpi-value">{{ kpi.value }}</div>
          <div class="kpi-change" :class="kpi.changeType">{{ kpi.change }}</div>
        </div>
      </div>
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
      <el-card shadow="never" class="funnel-card">
        <template #header>
          <div class="funnel-card-header">
            <span class="chart-title">任务漏斗-从打开插件到采集成功</span>
            <el-link type="primary" style="font-size:13px">&lt; 返回精简版漏斗</el-link>
          </div>
        </template>
        <div class="funnel-body">
          <div class="funnel-common">
            <template v-for="(step, idx) in funnelCommon" :key="step.label">
              <div class="funnel-step">
                <div class="funnel-bar-row">
                  <div class="funnel-step-label">{{ step.label }}</div>
                  <div class="funnel-bar-wrap">
                    <div class="funnel-bar" :style="{ width: pct(step.value, funnelCommon[0].value) + '%' }" />
                  </div>
                  <span class="funnel-bar-value">{{ Number(step.value).toLocaleString() }}</span>
                  <span class="funnel-bar-pct">{{ pct(step.value, funnelCommon[0].value) }}%</span>
                </div>
              </div>
              <div v-if="idx < funnelCommon.length - 1" class="funnel-drop-row">
                <span class="funnel-drop-label">{{ step.dropLabel }}</span>
                <span class="funnel-drop-pct">{{ step.dropPct }}</span>
              </div>
            </template>
          </div>
          <div class="funnel-divider">
            <span class="funnel-divider-text">根据任务类型 进行漏斗分支</span>
          </div>
          <div class="funnel-branches">
            <div class="funnel-branch">
              <div class="funnel-branch-title">采集账号数据（包括更新）</div>
              <template v-for="step in funnelAccount" :key="step.label">
                <div v-if="step.dropLabel" class="funnel-drop-row">
                  <span class="funnel-drop-label">{{ step.dropLabel }}</span>
                  <span class="funnel-drop-pct">{{ step.dropPct }}</span>
                </div>
                <div class="funnel-step">
                  <div class="funnel-bar-row">
                    <div class="funnel-step-label">{{ step.label }}</div>
                    <div class="funnel-bar-wrap">
                      <div class="funnel-bar" :class="{ 'funnel-bar--success': step.isSuccess }" :style="{ width: pct(step.value, funnelCommon[0].value) + '%' }" />
                    </div>
                    <span class="funnel-bar-value">{{ step.value != null ? Number(step.value).toLocaleString() : 'xxx' }}</span>
                    <span class="funnel-bar-pct">{{ step.value != null ? pct(step.value, funnelCommon[0].value) + '%' : 'xx%' }}</span>
                  </div>
                </div>
              </template>
            </div>
            <div class="funnel-branch">
              <div class="funnel-branch-title">采集视频数据（包括更新）</div>
              <template v-for="step in funnelVideo" :key="step.label + '_v'">
                <div v-if="step.dropLabel" class="funnel-drop-row">
                  <span class="funnel-drop-label">{{ step.dropLabel }}</span>
                  <span class="funnel-drop-pct">{{ step.dropPct }}</span>
                </div>
                <div class="funnel-step">
                  <div class="funnel-bar-row">
                    <div class="funnel-step-label">{{ step.label }}</div>
                    <div class="funnel-bar-wrap">
                      <div class="funnel-bar" :class="{ 'funnel-bar--success': step.isSuccess }" :style="{ width: pct(step.value, funnelCommon[0].value) + '%' }" />
                    </div>
                    <span class="funnel-bar-value">{{ step.value != null ? Number(step.value).toLocaleString() : 'xxx' }}</span>
                    <span class="funnel-bar-pct">{{ step.value != null ? pct(step.value, funnelCommon[0].value) + '%' : 'xx%' }}</span>
                  </div>
                </div>
              </template>
            </div>
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

const KPI_BY_RANGE = {
  day: [
    { key: 'users',  label: '有效用户',      value: '312',    change: '+8 较昨日',    changeType: 'up' },
    { key: 'calls',  label: '调用次数',      value: '428',    change: '+32 较昨日',   changeType: 'up' },
    { key: 'points', label: '消耗积分',      value: '1,204',  change: '+98 较昨日',   changeType: 'up' },
    { key: 'rate',   label: '采集任务成功率', value: '91.2%',  change: '+0.8% 较昨日', changeType: 'up' },
    { key: 'time',   label: '平均全链路时长', value: '3m 58s', change: '-5% 较昨日',   changeType: 'up' },
  ],
  week: [
    { key: 'users',  label: '有效用户',      value: '876',    change: '+42 较上周',   changeType: 'up' },
    { key: 'calls',  label: '调用次数',      value: '3,024',  change: '+215 较上周',  changeType: 'up' },
    { key: 'points', label: '消耗积分',      value: '8,340',  change: '+620 较上周',  changeType: 'up' },
    { key: 'rate',   label: '采集任务成功率', value: '89.5%',  change: '+0.5% 较上周', changeType: 'up' },
    { key: 'time',   label: '平均全链路时长', value: '4m 05s', change: '-2% 较上周',   changeType: 'up' },
  ],
  month: [
    { key: 'users',  label: '有效用户',      value: '1,231',  change: '+113 较上月',   changeType: 'up' },
    { key: 'calls',  label: '调用次数',      value: '14,528', change: '+1,123 较上月', changeType: 'up' },
    { key: 'points', label: '消耗积分',      value: '14,528', change: '+1,123 较上月', changeType: 'up' },
    { key: 'rate',   label: '采集任务成功率', value: '88.8%',  change: '+1.2% 较上月',  changeType: 'up' },
    { key: 'time',   label: '平均全链路时长', value: '4m 23s', change: '-2% 较上月',    changeType: 'up' },
  ],
}

const FUNNEL_COMMON = {
  day: [
    { label: '打开插件',     value: 1840,  dropLabel: '↓ 未登录流失',        dropPct: '8%' },
    { label: '完成登录',     value: 1693,  dropLabel: '↓ 选择任务类型时流失', dropPct: '0%' },
    { label: '选择任务类型', value: 1693,  dropLabel: null, dropPct: null },
  ],
  week: [
    { label: '打开插件',     value: 9240,  dropLabel: '↓ 未登录流失',        dropPct: '9%' },
    { label: '完成登录',     value: 8408,  dropLabel: '↓ 选择任务类型时流失', dropPct: '0%' },
    { label: '选择任务类型', value: 8408,  dropLabel: null, dropPct: null },
  ],
  month: [
    { label: '打开插件',     value: 12840, dropLabel: '↓ 未登录流失',        dropPct: '8%' },
    { label: '完成登录',     value: 11813, dropLabel: '↓ 选择任务类型时流失', dropPct: '0%' },
    { label: '选择任务类型', value: 11813, dropLabel: null, dropPct: null },
  ],
}

const FUNNEL_ACCOUNT = {
  day: [
    { label: '写入关键词', value: null, dropLabel: '↓ 选择平台时流失', dropPct: '16%' },
    { label: '采集账号',  value: null, dropLabel: '↓ 填写账号时流失', dropPct: '17%' },
    { label: '开始采集',  value: null, dropLabel: '↓ 采集完成后流失', dropPct: '2%'  },
    { label: '采集成功',  value: 384,  dropLabel: '↓ 执行失败',      dropPct: '5%', isSuccess: true },
  ],
  week: [
    { label: '写入关键词', value: null, dropLabel: '↓ 选择平台时流失', dropPct: '16%' },
    { label: '采集账号',  value: null, dropLabel: '↓ 填写账号时流失', dropPct: '17%' },
    { label: '开始采集',  value: null, dropLabel: '↓ 采集完成后流失', dropPct: '2%'  },
    { label: '采集成功',  value: 2053, dropLabel: '↓ 执行失败',      dropPct: '5%', isSuccess: true },
  ],
  month: [
    { label: '写入关键词', value: null, dropLabel: '↓ 选择平台时流失', dropPct: '16%' },
    { label: '采集账号',  value: null, dropLabel: '↓ 填写账号时流失', dropPct: '17%' },
    { label: '开始采集',  value: null, dropLabel: '↓ 采集完成后流失', dropPct: '2%'  },
    { label: '采集成功',  value: 4542, dropLabel: '↓ 执行失败',      dropPct: '5%', isSuccess: true },
  ],
}

const FUNNEL_VIDEO = {
  day: [
    { label: '写入关键词', value: null, dropLabel: '↓ 选择平台时流失', dropPct: '16%' },
    { label: '采集账号',  value: null, dropLabel: '↓ 填写账号时流失', dropPct: '34%' },
    { label: '数据范围',  value: null, dropLabel: '↓ 选择范围时流失', dropPct: '0%'  },
    { label: '开始采集',  value: null, dropLabel: '↓ 采集完成后流失', dropPct: '2%'  },
    { label: '采集成功',  value: 384,  dropLabel: '↓ 执行失败',      dropPct: '5%', isSuccess: true },
  ],
  week: [
    { label: '写入关键词', value: null, dropLabel: '↓ 选择平台时流失', dropPct: '16%' },
    { label: '采集账号',  value: null, dropLabel: '↓ 填写账号时流失', dropPct: '34%' },
    { label: '数据范围',  value: null, dropLabel: '↓ 选择范围时流失', dropPct: '0%'  },
    { label: '开始采集',  value: null, dropLabel: '↓ 采集完成后流失', dropPct: '2%'  },
    { label: '采集成功',  value: 2053, dropLabel: '↓ 执行失败',      dropPct: '5%', isSuccess: true },
  ],
  month: [
    { label: '写入关键词', value: null, dropLabel: '↓ 选择平台时流失', dropPct: '16%' },
    { label: '采集账号',  value: null, dropLabel: '↓ 填写账号时流失', dropPct: '34%' },
    { label: '数据范围',  value: null, dropLabel: '↓ 选择范围时流失', dropPct: '0%'  },
    { label: '开始采集',  value: null, dropLabel: '↓ 采集完成后流失', dropPct: '2%'  },
    { label: '采集成功',  value: 4542, dropLabel: '↓ 执行失败',      dropPct: '5%', isSuccess: true },
  ],
}

const kpiCards      = computed(() => KPI_BY_RANGE[timeRange.value]   ?? KPI_BY_RANGE.month)
const funnelCommon  = computed(() => FUNNEL_COMMON[timeRange.value]  ?? FUNNEL_COMMON.month)
const funnelAccount = computed(() => FUNNEL_ACCOUNT[timeRange.value] ?? FUNNEL_ACCOUNT.month)
const funnelVideo   = computed(() => FUNNEL_VIDEO[timeRange.value]   ?? FUNNEL_VIDEO.month)

function pct(value, base) {
  if (!value || !base) return 0
  return Math.round((value / base) * 100)
}

const PLATFORM_BY_RANGE = { day: [52,23,13,8,4], week: [49,25,14,7,5], month: [52,23,13,8,4] }
const FAILURE_BY_RANGE  = { day: [85,18,12,8],   week: [86,16,13,7],   month: [88,15,11,6]  }
const PLATFORM_COLORS   = ['#a78bfa','#fb7185','#4ade80','#38bdf8','#fb923c']
const FAILURE_COLORS    = ['#ef4444','#fb923c','#fbbf24','#a3b899']

function buildHBarOption(labels, values, colors) {
  const maxVal = Math.max(...values)
  return {
    grid: { left: 110, right: 80, top: 10, bottom: 10, containLabel: false },
    xAxis: { type: 'value', show: false, max: maxVal * 1.3 },
    yAxis: {
      type: 'category', data: labels, inverse: true,
      axisLine: { show: false }, axisTick: { show: false },
      axisLabel: { fontSize: 13, color: '#374151' },
    },
    series: [{
      type: 'bar',
      data: values.map((v, i) => ({ value: v, itemStyle: { color: colors[i], borderRadius: [0,4,4,0] } })),
      barWidth: 20,
      label: { show: true, position: 'right', formatter: (p) => `${p.value}%`, fontSize: 12, color: '#6b7280', distance: 8 },
      showBackground: true,
      backgroundStyle: { color: '#f3f4f6', borderRadius: [0,4,4,0] },
    }],
  }
}

function renderCharts() {
  if (!window.echarts) return
  const pv = PLATFORM_BY_RANGE[timeRange.value] ?? PLATFORM_BY_RANGE.month
  const fv = FAILURE_BY_RANGE[timeRange.value]  ?? FAILURE_BY_RANGE.month
  if (platformEl.value) {
    if (!platformChart) platformChart = window.echarts.init(platformEl.value)
    platformChart.setOption(buildHBarOption(['抖音', '小红书', '视频号', '公众号', '快手'], pv, PLATFORM_COLORS))
  }
  if (failureEl.value) {
    if (!failureChart) failureChart = window.echarts.init(failureEl.value)
    failureChart.setOption(buildHBarOption(['账号ID失效', '限流', '请求超时', '其他原因'], fv, FAILURE_COLORS))
  }
}

watch(timeRange, () => loadData())
onMounted(() => loadData())
onBeforeUnmount(() => { platformChart?.dispose(); failureChart?.dispose() })
</script>
<style scoped>
.overview-page { padding: 0; }
.overview-header { display: flex; justify-content: flex-end; margin-bottom: 20px; }
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 14px;
  margin-bottom: 20px;
}
@media (max-width: 1300px) { .kpi-grid { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 768px)  { .kpi-grid { grid-template-columns: repeat(2, 1fr); } }
.kpi-card { background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px 18px 16px; }
.kpi-label { font-size: 13px; color: #6b7280; margin-bottom: 8px; }
.kpi-value { font-size: 30px; font-weight: 700; color: #111827; line-height: 1.15; margin-bottom: 6px; letter-spacing: -0.5px; }
.kpi-change { font-size: 12px; }
.kpi-change.up   { color: #10b981; }
.kpi-change.down { color: #ef4444; }
.charts-row { display: flex; gap: 16px; margin-bottom: 20px; }
.chart-card { flex: 1; min-width: 0; }
.chart-title { font-size: 14px; font-weight: 600; color: #111827; }
.chart-body { height: 230px; }
.funnel-card { margin-bottom: 20px; }
.funnel-card-header { display: flex; justify-content: space-between; align-items: center; width: 100%; }
.funnel-body { padding: 16px 0; }
.funnel-common { margin-bottom: 0; }
.funnel-step { padding: 8px 0; }
.funnel-bar-row { display: flex; align-items: center; gap: 12px; }
.funnel-step-label { font-size: 13px; color: #374151; font-weight: 500; min-width: 90px; flex-shrink: 0; }
.funnel-bar-wrap { flex: 1; height: 32px; background: #f3f4f6; border-radius: 0 4px 4px 0; overflow: hidden; }
.funnel-bar { height: 100%; background: #4e7bef; border-radius: 0 4px 4px 0; transition: width 0.5s ease; min-width: 2px; }
.funnel-bar--success { background: #34c759; }
.funnel-bar-value { font-size: 14px; font-weight: 600; color: #111827; min-width: 60px; text-align: right; flex-shrink: 0; }
.funnel-bar-pct   { font-size: 13px; color: #6b7280; min-width: 40px; flex-shrink: 0; }
.funnel-drop-row { padding: 4px 0 4px 102px; font-size: 12px; color: #6b7280; }
.funnel-drop-label { margin-right: 6px; }
.funnel-drop-pct   { color: #f59e0b; font-weight: 600; }
.funnel-divider {
  border-top: 1px solid #e5e7eb;
  border-bottom: 1px solid #e5e7eb;
  padding: 10px 0;
  margin: 20px 0;
  text-align: center;
  background: #fafafa;
}
.funnel-divider-text { font-size: 13px; font-weight: 600; color: #6b7280; }
.funnel-branches { display: grid; grid-template-columns: 1fr 1fr; gap: 32px; }
@media (max-width: 1100px) { .funnel-branches { grid-template-columns: 1fr; gap: 20px; } }
.funnel-branch { min-width: 0; }
.funnel-branch-title {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  text-align: center;
  background: #f3f4f6;
  border-radius: 6px;
  padding: 8px 12px;
  margin-bottom: 4px;
}
</style>

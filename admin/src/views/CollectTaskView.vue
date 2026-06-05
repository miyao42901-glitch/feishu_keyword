<template>
  <div class="collect-page">
    <div class="page-header">
      <el-button-group>
        <el-button :type="range === 'day' ? 'primary' : ''" @click="range = 'day'">今日</el-button>
        <el-button :type="range === 'week' ? 'primary' : ''" @click="range = 'week'">本周</el-button>
        <el-button :type="range === 'month' ? 'primary' : ''" @click="range = 'month'">本月</el-button>
      </el-button-group>
    </div>

    <div class="kpi-row">
      <el-card shadow="never" class="kpi-card">
        <div class="kpi-label">采集任务发起数</div>
        <div class="kpi-value">{{ current.taskCount }}</div>
        <div class="kpi-change up">{{ current.taskChange }}</div>
      </el-card>
      <el-card shadow="never" class="kpi-card">
        <div class="kpi-label">采集任务成功率</div>
        <div class="kpi-value">{{ current.successRate }}</div>
        <div class="kpi-change up">{{ current.successChange }}</div>
      </el-card>
      <el-card shadow="never" class="kpi-card">
        <div class="kpi-label">平均采集耗时</div>
        <div class="kpi-value">{{ current.avgTime }}</div>
        <div class="kpi-change up">{{ current.timeChange }}</div>
      </el-card>
    </div>

    <el-card shadow="never" class="source-card">
      <template #header>
        <div class="source-header">
          <span class="chart-title">采集来源分布（V1.1.0）</span>
          <el-button-group size="small">
            <el-button v-for="p in platforms" :key="p" :type="activePlatform === p ? 'primary' : ''" @click="activePlatform = p">{{ p }}</el-button>
          </el-button-group>
        </div>
      </template>
      <div class="source-bar-wrap">
        <div class="source-bar">
          <div v-for="seg in sourceSegments" :key="seg.label" class="source-seg" :style="{ width: seg.pct + '%', background: seg.color }">
            <span class="source-seg-label">{{ seg.label }} {{ seg.pct }}%</span>
          </div>
        </div>
      </div>
    </el-card>

    <div class="charts-row">
      <el-card shadow="never" class="chart-card">
        <template #header><span class="chart-title">采集失败原因明细</span></template>
        <div class="failure-body">
          <div class="failure-donut-wrap">
            <div ref="donutEl" class="failure-donut" />
          </div>
          <div class="failure-legend">
            <div v-for="item in failureItems" :key="item.name" class="failure-legend-item">
              <span class="legend-dot" :style="{ background: item.color }" />
              <span class="legend-name">{{ item.name }}</span>
              <span class="legend-pct">{{ item.pct }}</span>
              <span class="legend-cnt">{{ item.count }}</span>
            </div>
          </div>
        </div>
      </el-card>

      <el-card shadow="never" class="chart-card">
        <template #header><span class="chart-title">采集数据范围分布</span></template>
        <div ref="rangeBarEl" class="range-bar-chart" />
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const range = ref('month')
const activePlatform = ref('抖音')
const donutEl = ref(null)
const rangeBarEl = ref(null)
let donutChart = null
let rangeBarChart = null

const platforms = ['抖音', '小红书', '视频号', '公众号', '快手']

const KPI_DATA = {
  day:   { taskCount: '428',   taskChange: '+32 较昨日',  successRate: '90.1%', successChange: '+0.8% 较昨日', avgTime: '11s', timeChange: '-1s 较昨日' },
  week:  { taskCount: '876',   taskChange: '+56 较上周',  successRate: '89.3%', successChange: '+0.5% 较上周', avgTime: '12s', timeChange: '-1s 较上周' },
  month: { taskCount: '1,528', taskChange: '+113 较上月', successRate: '88.8%', successChange: '+1.2% 较上月', avgTime: '13s', timeChange: '-2s 较上月' },
}

const SOURCE_DATA = {
  抖音:   [{ label: '账号分享链接', pct: 58, color: '#1a2a5f' }, { label: '账号表', pct: 28, color: '#4e7bef' }, { label: '账号ID', pct: 14, color: '#38bdf8' }],
  小红书: [{ label: '账号分享链接', pct: 50, color: '#1a2a5f' }, { label: '账号表', pct: 32, color: '#4e7bef' }, { label: '账号ID', pct: 18, color: '#38bdf8' }],
  视频号: [{ label: '账号分享链接', pct: 62, color: '#1a2a5f' }, { label: '账号表', pct: 25, color: '#4e7bef' }, { label: '账号ID', pct: 13, color: '#38bdf8' }],
  公众号: [{ label: '账号分享链接', pct: 45, color: '#1a2a5f' }, { label: '账号表', pct: 35, color: '#4e7bef' }, { label: '账号ID', pct: 20, color: '#38bdf8' }],
  快手:   [{ label: '账号分享链接', pct: 55, color: '#1a2a5f' }, { label: '账号表', pct: 30, color: '#4e7bef' }, { label: '账号ID', pct: 15, color: '#38bdf8' }],
}

const FAILURE_DATA = {
  month: [
    { name: '账号ID格式错误',   pct: '43%', count: '1,432', color: '#fb7185', value: 43 },
    { name: '账号链接读取失败', pct: '25%', count: 'xxx',   color: '#fb923c', value: 25 },
    { name: '账号表格字段有误', pct: 'xx%', count: 'xxx',   color: '#fbbf24', value: 12 },
    { name: '余额不足',         pct: 'xx%', count: 'xxx',   color: '#a78bfa', value: 10 },
    { name: '网络超时',         pct: 'xx%', count: 'xxx',   color: '#38bdf8', value: 6 },
    { name: '其他',             pct: 'xx%', count: 'xxx',   color: '#86efac', value: 4 },
  ],
}

const RANGE_DATA = { day: [62, 48, 30, 18, 12, 8], week: [60, 50, 28, 20, 14, 7], month: [58, 45, 25, 18, 12, 6] }

const current = computed(() => KPI_DATA[range.value] ?? KPI_DATA.month)
const sourceSegments = computed(() => SOURCE_DATA[activePlatform.value] ?? SOURCE_DATA['抖音'])
const failureItems = computed(() => FAILURE_DATA[range.value] ?? FAILURE_DATA.month)

const FAILURE_CENTER = { day: '1,680次', week: '2,140次', month: '3,330次' }

function renderDonut() {
  const items = failureItems.value
  if (!donutEl.value || !window.echarts) return
  if (!donutChart) donutChart = window.echarts.init(donutEl.value)
  const centerText = FAILURE_CENTER[range.value] ?? FAILURE_CENTER.month
  donutChart.setOption({
    series: [{
      type: 'pie',
      radius: ['48%', '72%'],
      center: ['40%', '50%'],
      data: items.map((it) => ({ name: it.name, value: it.value, itemStyle: { color: it.color } })),
      label: { show: false },
      emphasis: { scale: false },
    }],
    graphic: [
      { type: 'text', bounding: 'raw', left: '40%', top: '40%', style: { text: centerText, font: 'bold 16px sans-serif', fill: '#111827', textAlign: 'center' } },
      { type: 'text', bounding: 'raw', left: '40%', top: '57%', style: { text: '采集失败', font: '12px sans-serif', fill: '#6b7280', textAlign: 'center' } },
    ],
  })
}

function renderRangeBar() {
  const vals = RANGE_DATA[range.value] ?? RANGE_DATA.month
  const labels = ['7天内', '当天', '1页（默认）', '3天内', '30天内', '其他']
  if (!rangeBarEl.value || !window.echarts) return
  if (!rangeBarChart) rangeBarChart = window.echarts.init(rangeBarEl.value)
  rangeBarChart.setOption({
    grid: { left: 90, right: 80, top: 10, bottom: 10, containLabel: false },
    xAxis: { type: 'value', show: false, max: Math.max(...vals) * 1.35 },
    yAxis: { type: 'category', data: labels, inverse: true, axisLine: { show: false }, axisTick: { show: false }, axisLabel: { fontSize: 13, color: '#374151' } },
    series: [{
      type: 'bar',
      data: vals.map((v) => ({ value: v, itemStyle: { color: '#38bdf8', borderRadius: [0, 4, 4, 0] } })),
      barWidth: 18,
      label: { show: true, position: 'right', formatter: 'xx%', fontSize: 12, color: '#6b7280', distance: 8 },
      showBackground: true,
      backgroundStyle: { color: '#f3f4f6', borderRadius: [0, 4, 4, 0] },
    }],
  })
}

watch(range, async () => { await nextTick(); renderDonut(); renderRangeBar() })
onMounted(async () => { await nextTick(); renderDonut(); renderRangeBar() })
onBeforeUnmount(() => { donutChart?.dispose(); rangeBarChart?.dispose() })
</script>

<style scoped>
.collect-page { padding: 0; }
.page-header { display: flex; justify-content: flex-end; margin-bottom: 20px; }

.kpi-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 20px; }
@media (max-width: 900px) { .kpi-row { grid-template-columns: 1fr; } }

.kpi-card { padding: 4px 0; }
.kpi-label { font-size: 13px; color: #6b7280; margin-bottom: 10px; }
.kpi-value { font-size: 36px; font-weight: 700; color: #111827; line-height: 1.1; margin-bottom: 8px; letter-spacing: -0.5px; }
.kpi-change { font-size: 12px; }
.kpi-change.up { color: #10b981; }

.source-card { margin-bottom: 20px; }
.source-header { display: flex; justify-content: space-between; align-items: center; width: 100%; }
.chart-title { font-size: 14px; font-weight: 600; color: #111827; }

.source-bar-wrap { padding: 8px 0 4px; }
.source-bar { display: flex; height: 44px; border-radius: 6px; overflow: hidden; width: 100%; }
.source-seg { display: flex; align-items: center; justify-content: center; transition: width 0.4s ease; min-width: 0; overflow: hidden; }
.source-seg-label { font-size: 13px; font-weight: 600; color: #fff; white-space: nowrap; padding: 0 12px; overflow: hidden; text-overflow: ellipsis; }

.charts-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
@media (max-width: 1000px) { .charts-row { grid-template-columns: 1fr; } }

.failure-body { display: flex; align-items: center; gap: 16px; padding: 8px 0; }
.failure-donut-wrap { flex-shrink: 0; }
.failure-donut { width: 200px; height: 220px; }

.failure-legend { flex: 1; display: flex; flex-direction: column; gap: 10px; }
.failure-legend-item { display: grid; grid-template-columns: 12px 1fr 36px 48px; align-items: center; gap: 8px; font-size: 13px; }
.legend-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.legend-name { color: #374151; }
.legend-pct { color: #111827; font-weight: 600; text-align: right; }
.legend-cnt { color: #6b7280; text-align: right; }

.range-bar-chart { height: 260px; }
</style>

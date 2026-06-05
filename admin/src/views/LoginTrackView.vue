<template>
  <div class="login-page">
    <div class="page-header">
      <el-button-group>
        <el-button :type="range === 'day' ? 'primary' : ''" @click="range = 'day'">今日</el-button>
        <el-button :type="range === 'week' ? 'primary' : ''" @click="range = 'week'">本周</el-button>
        <el-button :type="range === 'month' ? 'primary' : ''" @click="range = 'month'">本月</el-button>
      </el-button-group>
    </div>

    <div class="kpi-row">
      <el-card shadow="never" class="kpi-card">
        <div class="kpi-label">插件打开次数（日均）</div>
        <div class="kpi-value">{{ current.openCount }}</div>
        <div class="kpi-change up">{{ current.openChange }}</div>
      </el-card>
      <el-card shadow="never" class="kpi-card">
        <div class="kpi-label">登录成功率</div>
        <div class="kpi-value">{{ current.loginRate }}</div>
        <div class="kpi-change up">{{ current.loginRateChange }}</div>
      </el-card>
    </div>

    <div class="charts-row">
      <el-card shadow="never" class="chart-card">
        <template #header><span class="chart-title">登录方式选择分布</span></template>
        <div class="donut-wrapper">
          <div ref="donutEl" class="donut-chart" />
          <div class="donut-legend">
            <div v-for="item in loginMethods" :key="item.name" class="legend-item">
              <span class="legend-dot" :style="{ background: item.color }" />
              <span class="legend-name">{{ item.name }}</span>
              <span class="legend-pct">{{ item.value }}%</span>
            </div>
          </div>
        </div>
      </el-card>

      <el-card shadow="never" class="chart-card">
        <template #header><span class="chart-title">未登录停留时长</span></template>
        <div ref="barEl" class="bar-chart" />
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const range = ref('month')
const donutEl = ref(null)
const barEl = ref(null)
let donutChart = null
let barChart = null

const KPI_DATA = {
  day:   { openCount: '412',   openChange: '+18 较昨日',  loginRate: '81%', loginRateChange: '+2% 较昨日' },
  week:  { openCount: '876',   openChange: '+56 较上周',  loginRate: '80%', loginRateChange: '+1% 较上周' },
  month: { openCount: '1,231', openChange: '+113 较上月', loginRate: '79%', loginRateChange: '+4% 较上月' },
}

const LOGIN_METHODS = {
  day:   [{ name: '微信扫码', value: 90, color: '#7c5cfc' }, { name: '账号密码', value: 10, color: '#fbbf24' }],
  week:  [{ name: '微信扫码', value: 91, color: '#7c5cfc' }, { name: '账号密码', value: 9,  color: '#fbbf24' }],
  month: [{ name: '微信扫码', value: 92, color: '#7c5cfc' }, { name: '账号密码', value: 8,  color: '#fbbf24' }],
}

const DWELL_DATA = {
  day:   [82, 16, 12, 7],
  week:  [85, 15, 11, 6],
  month: [88, 15, 11, 6],
}

const current = computed(() => KPI_DATA[range.value] ?? KPI_DATA.month)
const loginMethods = computed(() => LOGIN_METHODS[range.value] ?? LOGIN_METHODS.month)

function renderDonut() {
  const methods = loginMethods.value
  if (!donutEl.value) return
  if (!donutChart) donutChart = window.echarts.init(donutEl.value)
  const main = methods[0]
  donutChart.setOption({
    series: [{
      type: 'pie',
      radius: ['55%', '78%'],
      center: ['38%', '50%'],
      data: methods.map((m) => ({ name: m.name, value: m.value, itemStyle: { color: m.color } })),
      label: { show: false },
      emphasis: { scale: false },
    }],
    graphic: [
      { type: 'text', bounding: 'raw', left: '38%', top: '38%', style: { text: `${main.value}%`, font: 'bold 22px sans-serif', fill: '#111827', textAlign: 'center' } },
      { type: 'text', bounding: 'raw', left: '38%', top: '55%', style: { text: main.name, font: '12px sans-serif', fill: '#6b7280', textAlign: 'center' } },
    ],
  })
}

function renderBar() {
  const vals = DWELL_DATA[range.value] ?? DWELL_DATA.month
  const labels = ['0~5秒', '5~15秒', '15~60秒', '60秒以上']
  const colors = ['#ef4444', '#fb923c', '#fbbf24', '#a3b899']
  if (!barEl.value) return
  if (!barChart) barChart = window.echarts.init(barEl.value)
  barChart.setOption({
    grid: { left: 80, right: 80, top: 10, bottom: 10, containLabel: false },
    xAxis: { type: 'value', show: false, max: Math.max(...vals) * 1.3 },
    yAxis: { type: 'category', data: labels, inverse: true, axisLine: { show: false }, axisTick: { show: false }, axisLabel: { fontSize: 13, color: '#374151' } },
    series: [{
      type: 'bar',
      data: vals.map((v, i) => ({ value: v, itemStyle: { color: colors[i], borderRadius: [0, 4, 4, 0] } })),
      barWidth: 20,
      label: { show: true, position: 'right', formatter: (p) => `${p.value}%`, fontSize: 12, color: '#6b7280', distance: 8 },
      showBackground: true,
      backgroundStyle: { color: '#f3f4f6', borderRadius: [0, 4, 4, 0] },
    }],
  })
}

watch(range, async () => { await nextTick(); renderDonut(); renderBar() })
onMounted(async () => { await nextTick(); renderDonut(); renderBar() })
onBeforeUnmount(() => { donutChart?.dispose(); barChart?.dispose() })
</script>

<style scoped>
.login-page { padding: 0; }
.page-header { display: flex; justify-content: flex-end; margin-bottom: 20px; }

.kpi-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px; }
@media (max-width: 768px) { .kpi-row { grid-template-columns: 1fr; } }

.kpi-card { padding: 4px 0; }
.kpi-label { font-size: 13px; color: #6b7280; margin-bottom: 10px; }
.kpi-value { font-size: 36px; font-weight: 700; color: #111827; line-height: 1.1; margin-bottom: 8px; letter-spacing: -0.5px; }
.kpi-change { font-size: 12px; }
.kpi-change.up { color: #10b981; }

.charts-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
@media (max-width: 900px) { .charts-row { grid-template-columns: 1fr; } }

.chart-title { font-size: 14px; font-weight: 600; color: #111827; }

.donut-wrapper { display: flex; align-items: center; gap: 32px; padding: 12px 0; }
.donut-chart { width: 200px; height: 200px; flex-shrink: 0; }
.donut-legend { display: flex; flex-direction: column; gap: 20px; }
.legend-item { display: flex; align-items: center; gap: 10px; font-size: 13px; }
.legend-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.legend-name { color: #374151; min-width: 60px; }
.legend-pct { font-weight: 600; color: #111827; }

.bar-chart { height: 220px; }
</style>
